# -*- coding: utf-8 -*-
"""
scrapers/instagram.py — Scraper inmobiliario de Instagram (perfiles + posts sueltos)
====================================================================================
Reusa la sesion logueada de Chrome (copia cookies; Chrome debe estar CERRADO),
parsea el caption con Haiku y hace upsert a Supabase (fuente=instagram).

Uso:
    py scrapers/instagram.py --perfil suah_linkbienesraices            # un perfil
    py scrapers/instagram.py --perfil suah_linkbienesraices --max 80
    py scrapers/instagram.py --posts URL1 URL2                          # posts sueltos
    py scrapers/instagram.py --posts links.txt                         # archivo con URLs
    py scrapers/instagram.py --posts-dump                              # lee los .txt del Dump del vault
    py scrapers/instagram.py --perfil suah_linkbienesraices --posts-dump --dry-run

Requisito: Chrome cerrado al correr (las cookies estan bloqueadas si Chrome corre).
Portado de scraper_instagram.py (pre-reestructura) a core/db + data/.
"""

import asyncio
import argparse
import json
import re
import os
import sys
import glob
from datetime import datetime

import anthropic
from playwright.async_api import async_playwright

# Permite importar core/ cuando se ejecuta como script standalone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from core.db import upsert_listings_batch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEOJSON_PATH = os.path.join(ROOT, "data", "colonias_torreon.geojson")
DUMP_IG_DIR = (r"C:/Users/rogel/iCloudDrive/iCloud~md~obsidian/Second brain/"
               r"00 - Entrada/Dump/https_/www.instagram.com")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_USER_DATA = r"C:\Users\rogel\AppData\Local\Google\Chrome\User Data"
TMP_PROFILE = r"C:\Users\rogel\AppData\Local\Temp\chrome_ig_tmp"

# ---------------------------------------------------------------------------
# Geocoding por colonia usando GeoJSON de IMPLAN
# ---------------------------------------------------------------------------

_colonias_index = None


def _load_colonias():
    global _colonias_index
    if _colonias_index is not None:
        return _colonias_index
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        gj = json.load(f)
    index = {}
    for feat in gj["features"]:
        name = feat["properties"].get("colonia", "").upper().strip()
        coords = feat["geometry"]["coordinates"]
        geom_type = feat["geometry"]["type"]
        if geom_type == "Polygon":
            ring = coords[0]
        elif geom_type == "MultiPolygon":
            ring = coords[0][0]
        else:
            continue
        lngs = [c[0] for c in ring]
        lats = [c[1] for c in ring]
        index[name] = (sum(lats) / len(lats), sum(lngs) / len(lngs))
    _colonias_index = index
    return index


def _normalize(s):
    import unicodedata
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.upper().strip()


# Ruido a quitar para puentear fragmentacion del IMPLAN (etapas, ordinales,
# tipo de asentamiento). Misma filosofia que devColoniaMatcher del dashboard.
_GEO_STOP = re.compile(
    r"\b(RESIDENCIAL|FRACCIONAMIENTO|FRACC|FRAC|COLONIA|COL|PRIVADA|PRIVADAS|PRIV|"
    r"CERRADA|CERRADAS|SECTOR|ETAPA|ETEPA|SECCION|SECC|AMPLIACION|AMPL|CONJUNTO|"
    r"PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|SEPTIMA|OCTAVA|1RA|2DA|3RA|4TA|5TA)\b")
_GEO_ROM = re.compile(r"\b([IVX]+|[0-9]+A?)\b\.?\s*$")


def _clean_col(s):
    t = _GEO_STOP.sub(" ", _normalize(s))
    t = re.sub(r"\s+", " ", t).strip()
    for _ in range(3):
        t = _GEO_ROM.sub("", t).strip()
    return t


def geocode_colonia(colonia_raw):
    """Devuelve (lat, lng) del centroide de la colonia, o (None, None).

    Hibrido: exacto -> clave-limpia igual -> query como sub-cadena de palabras.
    Si varios poligonos (etapas) corresponden, promedia sus centroides para un
    centro representativo. NO usa match difuso por palabra suelta (falsos +)."""
    if not colonia_raw:
        return None, None
    index = _load_colonias()
    norm_index = {_normalize(k): v for k, v in index.items() if k.strip()}

    query = _normalize(colonia_raw)
    if query in norm_index:
        return norm_index[query]

    clean_q = _clean_col(colonia_raw)
    if len(clean_q) < 4:
        return None, None

    # Clave "suelta": sin articulos, puentea "del" vs "el" (Hacienda del/EL Rosario).
    # Solo se usa cuando deja >=2 tokens (no colapsa nombres de una palabra).
    _ART = {"DE", "DEL", "LA", "EL", "LOS", "LAS"}
    loose = lambda k: " ".join(t for t in k.split() if t not in _ART)
    loose_q = loose(clean_q)
    usar_loose = len(loose_q.split()) >= 2

    iguales, contenidos, sueltos = [], [], []
    for name, coords in norm_index.items():
        clean_n = _clean_col(name)
        if clean_n == clean_q:
            iguales.append(coords)
        elif (" " + clean_n + " ").find(" " + clean_q + " ") >= 0:
            contenidos.append(coords)
        elif usar_loose:
            loose_n = loose(clean_n)
            if loose_n == loose_q or (" " + loose_n + " ").find(" " + loose_q + " ") >= 0:
                sueltos.append(coords)

    grupo = iguales or contenidos or sueltos
    if not grupo:
        return None, None
    lat = sum(c[0] for c in grupo) / len(grupo)
    lng = sum(c[1] for c in grupo) / len(grupo)
    return lat, lng


# ---------------------------------------------------------------------------
# Auth: copiar perfil de Chrome (cookies de sesion)
# ---------------------------------------------------------------------------

def copy_chrome_profile():
    import shutil
    cookies_src = os.path.join(CHROME_USER_DATA, "Default", "Network", "Cookies")
    try:
        with open(cookies_src, "rb"):
            pass
    except PermissionError:
        raise RuntimeError(
            "Chrome esta abierto — cierralo antes de correr el scraper de Instagram.")
    print("  Copiando perfil de Chrome...")
    if os.path.exists(TMP_PROFILE):
        shutil.rmtree(TMP_PROFILE, ignore_errors=True)
    os.makedirs(TMP_PROFILE)
    shutil.copy2(os.path.join(CHROME_USER_DATA, "Local State"), TMP_PROFILE)

    def copy_ignore_locked(src, dst):
        try:
            shutil.copy2(src, dst)
        except (PermissionError, OSError):
            pass

    SKIP_DIRS = {"Cache", "Code Cache", "GPUCache", "Service Worker", "CacheStorage", "Sessions"}

    def copytree_resilient(src_dir, dst_dir):
        os.makedirs(dst_dir, exist_ok=True)
        for entry in os.scandir(src_dir):
            dst_path = os.path.join(dst_dir, entry.name)
            if entry.is_dir(follow_symlinks=False):
                if entry.name not in SKIP_DIRS:
                    copytree_resilient(entry.path, dst_path)
            else:
                copy_ignore_locked(entry.path, dst_path)

    copytree_resilient(os.path.join(CHROME_USER_DATA, "Default"),
                       os.path.join(TMP_PROFILE, "Default"))
    print("  Perfil copiado OK")


# ---------------------------------------------------------------------------
# Haiku: parsear caption -> datos estructurados
# ---------------------------------------------------------------------------

HAIKU_SYSTEM = """Eres un extractor de datos inmobiliarios.
Dado el caption de un post de Instagram de una agencia inmobiliaria en Torreon, Coahuila,
extrae los datos estructurados del listing.

Responde SOLO con un JSON valido con estas claves (usa null si no se encuentra):
{
  "es_listing": true/false,
  "tipo_operacion": "venta"|"renta"|null,
  "tipo_inmueble": "casa"|"departamento"|"terreno"|"local"|"bodega"|"oficina"|null,
  "precio_mxn": number|null,
  "m2_terreno": number|null,
  "m2_construccion": number|null,
  "recamaras": number|null,
  "banos": number|null,
  "colonia": "string"|null,
  "direccion": "string"|null,
  "telefono": "string"|null,
  "descripcion": "string"|null
}"""


def _sanitizar(caption):
    """Mitiga prompt injection en captions (mismo espiritu que scrapers/base)."""
    c = re.sub(r"(?i)\b(ignora|olvida|disregard|ignore|system prompt|instrucciones?)\b",
               "[x]", caption or "")
    return c[:2000]


def parse_caption_with_haiku(caption):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=HAIKU_SYSTEM,
            messages=[{"role": "user", "content": _sanitizar(caption)}],
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        print(f"  [Haiku error] {e}")
        return None


# ---------------------------------------------------------------------------
# Instagram: extraccion de caption
# ---------------------------------------------------------------------------

def _find_caption_in_json(obj, best=""):
    """Busca recursivamente el texto de caption mas largo en un payload JSON."""
    if isinstance(obj, dict):
        cap = obj.get("caption")
        if isinstance(cap, dict) and isinstance(cap.get("text"), str):
            if len(cap["text"]) > len(best):
                best = cap["text"]
        emc = obj.get("edge_media_to_caption")
        if isinstance(emc, dict):
            for e in emc.get("edges", []):
                t = e.get("node", {}).get("text", "")
                if len(t) > len(best):
                    best = t
        for v in obj.values():
            best = _find_caption_in_json(v, best)
    elif isinstance(obj, list):
        for v in obj:
            best = _find_caption_in_json(v, best)
    return best


def _shortcode(url):
    m = re.search(r"/p/([^/?]+)", url) or re.search(r"/reel/([^/?]+)", url)
    return m.group(1) if m else ""


def _clean_url(url):
    sc = _shortcode(url)
    return f"https://www.instagram.com/p/{sc}/" if sc else url.split("?")[0]


async def extract_post(page, url):
    """Abre un post individual y devuelve (caption, username, fecha_iso)."""
    grabbed = {"caption": "", "username": "", "ts": 0}

    async def on_resp(response):
        u = response.url
        if any(k in u for k in ("/api/v1/media/", "graphql", "web_info", "PolarisPost")):
            try:
                j = await response.json()
            except Exception:
                return
            t = _find_caption_in_json(j)
            if len(t) > len(grabbed["caption"]):
                grabbed["caption"] = t

    page.on("response", on_resp)
    try:
        await page.goto(_clean_url(url), timeout=25000)
        await page.wait_for_timeout(3800)
    except Exception as e:
        print(f"  [goto error] {e}")
    page.remove_listener("response", on_resp)

    # og:title trae "{Cuenta} on Instagram: \"{caption}\"" — publico aunque haya
    # login wall. De ahi sacamos cuenta y, si la API no dio caption, el caption.
    og_title = ""
    try:
        og_title = await page.get_attribute('meta[property="og:title"]', "content") or ""
    except Exception:
        pass
    if og_title:
        mh = re.search(r"@([A-Za-z0-9._]+)", og_title)
        if mh:
            grabbed["username"] = mh.group(1)
        elif " on Instagram" in og_title:
            disp = og_title.split(" on Instagram")[0].strip()
            grabbed["username"] = re.sub(r"[^a-z0-9]+", "_", disp.lower()).strip("_")
        if not grabbed["caption"]:
            mc = re.search(r'on Instagram[^"“]*["“](.+)["”]\s*$', og_title, re.S)
            if mc:
                grabbed["caption"] = mc.group(1).strip()

    # Fallback: og:description
    if not grabbed["caption"]:
        try:
            meta = await page.get_attribute('meta[property="og:description"]', "content") or ""
            m = re.search(r':\s*["“](.+)["”]\s*$', meta, re.S)
            if m:
                grabbed["caption"] = m.group(1).strip()
        except Exception:
            pass

    # Ultimo recurso: span mas largo del DOM, descartando el menu de idiomas de IG
    if not grabbed["caption"]:
        try:
            els = await page.query_selector_all("h1, span")
            best = ""
            for el in els[:500]:
                try:
                    t = await el.inner_text()
                    if 25 < len(t) < 3000 and len(t) > len(best) and "Afrikaans" not in t:
                        best = t
                except Exception:
                    pass
            grabbed["caption"] = best
        except Exception:
            pass

    fecha = datetime.fromtimestamp(grabbed["ts"]).isoformat() if grabbed["ts"] else datetime.now().isoformat()
    return grabbed["caption"], grabbed["username"], fecha


# --- Perfil completo (portado del scraper viejo) ---------------------------

def _parse_edges(edges):
    posts = []
    for edge in edges:
        node = edge.get("node", {})
        cap_edges = node.get("edge_media_to_caption", {}).get("edges", [])
        caption = cap_edges[0]["node"]["text"] if cap_edges else ""
        ts = node.get("taken_at_timestamp", 0)
        sc = node.get("shortcode", "")
        posts.append({
            "shortcode": sc, "caption": caption,
            "fecha": datetime.fromtimestamp(ts).isoformat() if ts else datetime.now().isoformat(),
            "url": f"https://www.instagram.com/p/{sc}/",
        })
    return posts


async def get_all_posts(page, username, max_posts=100):
    posts = []
    profile_payload = {}

    async def handle_response(response):
        if "web_profile_info" in response.url:
            try:
                profile_payload["data"] = await response.json()
            except Exception:
                pass

    page.on("response", handle_response)
    print(f"  Cargando perfil @{username}...")
    await page.goto(f"https://www.instagram.com/{username}/", timeout=25000)
    await page.wait_for_timeout(3500)

    if not profile_payload:
        body_text = await page.inner_text("body")
        if "Log in" in body_text or "Log Into" in body_text:
            print("  SESION INVALIDA: Instagram pide login.")
            print("  Solucion: abre Chrome, entra a instagram.com, cierra Chrome y reintenta.")
        else:
            print("  No se capturo web_profile_info — sin datos")
        return posts

    user = profile_payload["data"].get("data", {}).get("user", {})
    user_id = user.get("id", "")
    media = user.get("edge_owner_to_timeline_media", {})
    posts.extend(_parse_edges(media.get("edges", [])))
    print(f"  Pagina 1: {len(posts)} posts")

    cookies = await page.context.cookies()
    session = {c["name"]: c["value"] for c in cookies if "instagram.com" in c.get("domain", "")}
    import httpx
    headers = {
        "x-csrftoken": session.get("csrftoken", ""),
        "x-ig-app-id": "936619743392459",
        "user-agent": "Instagram 275.0.0.27.98 Android",
        "cookie": "; ".join(f"{k}={v}" for k, v in session.items()),
    }
    max_id, page_num = "", 2
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        while len(posts) < max_posts:
            await asyncio.sleep(1.5)
            try:
                params = {"count": 12}
                if max_id:
                    params["max_id"] = max_id
                resp = await client.get(
                    f"https://www.instagram.com/api/v1/feed/user/{user_id}/",
                    params=params, headers=headers)
                if resp.status_code != 200:
                    print(f"  [paginacion] HTTP {resp.status_code}")
                    break
                data = resp.json()
                items = data.get("items", [])
                if not items:
                    break
                for item in items:
                    cap = item.get("caption") or {}
                    caption = cap.get("text", "") if isinstance(cap, dict) else ""
                    ts = item.get("taken_at", 0)
                    sc = item.get("code", item.get("pk", ""))
                    posts.append({
                        "shortcode": sc, "caption": caption,
                        "fecha": datetime.fromtimestamp(ts).isoformat() if ts else datetime.now().isoformat(),
                        "url": f"https://www.instagram.com/p/{sc}/",
                    })
                max_id = data.get("next_max_id", "")
                print(f"  Pagina {page_num}: {len(posts)} posts acumulados")
                page_num += 1
                if not data.get("more_available", False) or not max_id:
                    break
            except Exception as e:
                print(f"  [paginacion] {e}")
                break

    posts = posts[:max_posts]
    print(f"  Total posts: {len(posts)}")
    # completar captions faltantes visitando el post
    for post in posts:
        if post["caption"]:
            continue
        cap, _, _ = await extract_post(page, post["url"])
        post["caption"] = cap
    return posts


# ---------------------------------------------------------------------------
# Mapeo a listing + guardado
# ---------------------------------------------------------------------------

def _score(parsed):
    campos = ["precio_mxn", "tipo_inmueble", "tipo_operacion", "colonia",
              "m2_terreno", "m2_construccion", "recamaras", "banos"]
    llenos = sum(1 for c in campos if parsed.get(c) not in (None, "", 0))
    return round(40 + 60 * llenos / len(campos))  # 40-100


def construir_listing(url, caption, fecha, fuente):
    parsed = parse_caption_with_haiku(caption)
    if not parsed:
        return None, "error"
    if not parsed.get("es_listing"):
        return None, "no_listing"
    colonia = parsed.get("colonia")
    lat, lng = geocode_colonia(colonia)
    precio = parsed.get("precio_mxn")
    print(f"  {parsed.get('tipo_operacion','?')} | {parsed.get('tipo_inmueble','?')} | "
          + (f"${precio:,.0f}" if precio else "sin precio")
          + f" | {colonia or '?'} | coords={'si' if lat else 'no'}")
    listing = {
        "link_publicacion": _clean_url(url),
        "pagina_fuente": fuente,
        "tipo_operacion": parsed.get("tipo_operacion"),
        "tipo_inmueble": parsed.get("tipo_inmueble"),
        "precio_mxn": precio,
        "m2_terreno": parsed.get("m2_terreno"),
        "m2_construccion": parsed.get("m2_construccion"),
        "recamaras": parsed.get("recamaras"),
        "banos": parsed.get("banos"),
        "colonia": colonia,
        "direccion": parsed.get("direccion"),
        "descripcion": (parsed.get("descripcion") or caption)[:2000],
        "fecha_publicacion": fecha,
        "activo": True,
        "lat": lat, "lng": lng,
        "estado_inmueble": "usado",
        "score_calidad_anuncio": _score(parsed),
    }
    return listing, "ok"


def guardar(listings, dry_run):
    print(f"\n{'='*56}\nListings validos: {len(listings)}")
    if not listings:
        return
    if dry_run:
        print("DRY RUN — no se guarda. Muestra:")
        print(json.dumps(listings[:3], indent=2, ensure_ascii=False, default=str))
        return
    stats = upsert_listings_batch(listings, link_field="link_publicacion")
    print(f"Supabase -> {stats}")


# ---------------------------------------------------------------------------
# Lectura de URLs de posts (args / archivos / Dump del vault)
# ---------------------------------------------------------------------------

def recolectar_urls(args_posts, usar_dump):
    urls = []
    for a in (args_posts or []):
        if os.path.isfile(a):
            with open(a, encoding="utf-8") as f:
                urls += re.findall(r"https?://[^\s]+instagram\.com/[^\s]+", f.read())
        elif "instagram.com" in a:
            urls.append(a.strip())
    if usar_dump:
        for txt in glob.glob(os.path.join(DUMP_IG_DIR, "p", "*", "*.txt")):
            with open(txt, encoding="utf-8") as f:
                urls += re.findall(r"https?://[^\s]+instagram\.com/[^\s]+", f.read())
    # dedup por shortcode
    seen, out = set(), []
    for u in urls:
        sc = _shortcode(u)
        if sc and sc not in seen:
            seen.add(sc)
            out.append(u)
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run(perfiles, post_urls, max_posts, dry_run, captions_out=None):
    copy_chrome_profile()
    todos = []
    crudos = []   # para --captions-out: {url, fuente, fecha, caption} sin Haiku
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=TMP_PROFILE, executable_path=CHROME_PATH,
            headless=True, args=["--profile-directory=Default"], timeout=30000)
        page = await context.new_page()

        for username in perfiles or []:
            print(f"\n{'='*56}\nPERFIL @{username} (max {max_posts})")
            posts = await get_all_posts(page, username, max_posts)
            for i, post in enumerate(posts):
                print(f"[{i+1}/{len(posts)}] {post['url']}")
                if not (post["caption"] or "").strip():
                    print("  sin caption — skip")
                    continue
                if captions_out:
                    crudos.append({"url": _clean_url(post["url"]), "fuente": f"instagram_{username}",
                                   "fecha": post["fecha"], "caption": post["caption"]})
                    continue
                listing, estado = construir_listing(
                    post["url"], post["caption"], post["fecha"], f"instagram_{username}")
                if listing:
                    todos.append(listing)

        if post_urls:
            print(f"\n{'='*56}\nPOSTS SUELTOS ({len(post_urls)})")
            for i, url in enumerate(post_urls):
                print(f"[{i+1}/{len(post_urls)}] {url}")
                caption, username, fecha = await extract_post(page, url)
                if not (caption or "").strip():
                    print("  sin caption — skip (posible login wall o post no publico)")
                    continue
                fuente = f"instagram_{username}" if username else "instagram_post"
                if captions_out:
                    crudos.append({"url": _clean_url(url), "fuente": fuente,
                                   "fecha": fecha, "caption": caption})
                    continue
                listing, estado = construir_listing(url, caption, fecha, fuente)
                if listing:
                    todos.append(listing)

        await context.close()

    if captions_out:
        with open(captions_out, "w", encoding="utf-8") as f:
            json.dump(crudos, f, ensure_ascii=False, indent=2)
        print(f"\nCaptions crudos -> {captions_out} ({len(crudos)} posts, sin Haiku)")
        return
    guardar(todos, dry_run)


def main():
    ap = argparse.ArgumentParser(description="Scraper Instagram inmobiliario (perfiles + posts)")
    ap.add_argument("--perfil", nargs="+", help="Username(s) sin @")
    ap.add_argument("--posts", nargs="+", help="URLs de posts o archivos .txt con URLs")
    ap.add_argument("--posts-dump", action="store_true",
                    help="Lee los .txt de posts guardados en el Dump del vault")
    ap.add_argument("--max", type=int, default=50, help="Max posts por perfil (default 50)")
    ap.add_argument("--dry-run", action="store_true", help="No guarda, solo muestra")
    ap.add_argument("--captions-out", metavar="PATH",
                    help="Solo extrae captions crudos a un JSON (sin Haiku ni upsert)")
    args = ap.parse_args()

    post_urls = recolectar_urls(args.posts, args.posts_dump)
    if not args.perfil and not post_urls:
        ap.error("Da --perfil y/o --posts/--posts-dump (no encontre URLs).")
    if post_urls:
        print(f"URLs de posts a procesar: {len(post_urls)}")
        for u in post_urls:
            print("  -", u)
    asyncio.run(run(args.perfil, post_urls, args.max, args.dry_run, args.captions_out))


if __name__ == "__main__":
    main()
