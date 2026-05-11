"""
validators/colonias_ai.py — Corrige colonias mal asignadas usando IA
=====================================================================
Problema: muchos listings tienen el campo 'colonia' incorrecto porque el scraper
tomó el nombre de la ciudad/zona genérica. Sin embargo, la descripción del anuncio
suele mencionar explícitamente el fraccionamiento o colonia real.

Estrategia:
  1. Detectar listings donde el GPS cae en un polígono IMPLAN diferente al 'colonia' guardado
  2. Enviar descripción a Claude Haiku para extraer la colonia mencionada
  3. Si Haiku la encuentra con alta confianza → actualizar colonia en Supabase

Solo modifica listings con editado_manualmente = false.

Uso:
    py validators/colonias_ai.py               # corrige automáticamente (preview primero)
    py validators/colonias_ai.py --reporte     # solo muestra, sin modificar DB
    py validators/colonias_ai.py --limite 100  # procesar solo N listings
    py validators/colonias_ai.py --fuente i24  # filtrar por fuente
"""

import os, re, json, unicodedata, argparse, sys, time
import anthropic
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
ai = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def _sanitizar_para_prompt(texto: str, max_chars: int = 800) -> str:
    """Elimina secuencias de prompt injection antes de enviar a Claude."""
    if not texto:
        return ""
    sanitizado = re.sub(
        r'(?i)(ignora|ignore|forget|olvida|instrucciones|instructions)\s*(las\s*)?(anteriores?|previous|above|previas?)',
        '[REDACTED]', texto
    )
    return sanitizado[:max_chars]

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# ── Geometría IMPLAN ──────────────────────────────────────────────────────────
_colonias_features = None

def _cargar_colonias():
    global _colonias_features
    if _colonias_features is not None:
        return
    geojson_path = os.path.join(_DATA_DIR, 'colonias_torreon.geojson')
    with open(geojson_path, encoding='utf-8') as f:
        data = json.load(f)
    _colonias_features = data.get('features', [])
    print(f"  [geo] {len(_colonias_features)} polígonos IMPLAN cargados")

def _punto_en_poligono(lat, lng, coords):
    inside = False
    n = len(coords)
    j = n - 1
    for i in range(n):
        xi, yi = coords[i][0], coords[i][1]
        xj, yj = coords[j][0], coords[j][1]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def get_colonia_implan(lat, lng) -> str | None:
    """Devuelve el nombre canónico IMPLAN para (lat, lng), o None."""
    if not lat or not lng:
        return None
    _cargar_colonias()
    for feat in _colonias_features:
        geom  = feat.get('geometry', {})
        props = feat.get('properties', {})
        nombre = props.get('colonia') or props.get('COLONIA') or props.get('nom_col') or ''
        if geom.get('type') == 'Polygon':
            if _punto_en_poligono(lat, lng, geom['coordinates'][0]):
                return nombre.strip()
        elif geom.get('type') == 'MultiPolygon':
            for poly in geom['coordinates']:
                if _punto_en_poligono(lat, lng, poly[0]):
                    return nombre.strip()
    return None

def _normalizar(txt):
    if not txt:
        return ''
    t = unicodedata.normalize('NFD', txt.upper().strip())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9 ]', ' ', t)).strip()

_STOPWORDS = {
    'DE', 'DEL', 'LA', 'LAS', 'LOS', 'EL', 'EN', 'Y', 'A', 'AL',
    'SAN', 'SANTA', 'SANTO', 'RESIDENCIAL', 'JARDIN', 'JARDINES',
    'VILLAS', 'VILLA', 'FRACCIONAMIENTO', 'COLONIA', 'ETAPA',
    'NUEVA', 'NUEVO', 'TORREON', 'SECCION',
}

def _tokens(nombre):
    return {p for p in _normalizar(nombre).split() if len(p) >= 3 and p not in _STOPWORDS}

def colonias_coinciden(col_a: str, col_b: str) -> bool:
    """True si los nombres parecen referirse al mismo lugar (por overlap de tokens)."""
    if not col_a or not col_b:
        return False
    if _normalizar(col_a) == _normalizar(col_b):
        return True
    ta = _tokens(col_a)
    tb = _tokens(col_b)
    if not ta or not tb:
        return False
    return bool(ta & tb)

# ── Extracción con IA ─────────────────────────────────────────────────────────

def extraer_colonia_de_descripcion(descripcion: str, colonia_actual: str, colonia_implan: str) -> dict:
    """
    Pide a Haiku que lea la descripción y determine la colonia real del listing.

    Retorna:
        {
          "colonia_encontrada": "Nombre colonia" | null,
          "confianza": "alta" | "media" | "baja",
          "razon": "texto corto"
        }
    """
    prompt = f"""Eres un experto en bienes raíces en Torreón, Coahuila, México.

El siguiente anuncio tiene estas colonias registradas:
- Colonia en el anuncio: "{colonia_actual}"
- Colonia según GPS (IMPLAN): "{colonia_implan}"

Estas no coinciden, lo que indica que una está mal. Lee la descripción y determina
cuál es la colonia, fraccionamiento o zona REAL donde se ubica la propiedad.

DESCRIPCIÓN DEL ANUNCIO:
{_sanitizar_para_prompt(descripcion)}

INSTRUCCIONES:
- Si la descripción menciona explícitamente un fraccionamiento, colonia o zona de Torreón, extráela.
- Si no hay mención clara, devuelve null.
- La colonia debe ser un lugar real de Torreón (ej: "Las Trojes", "Montecarlo", "Ampliación La Rosita").
- NO inventes colonias que no estén en la descripción.

Responde SOLO con JSON, sin texto extra:
{{"colonia_encontrada": "Nombre real" o null, "confianza": "alta|media|baja", "razon": "por qué"}}"""

    try:
        resp = ai.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=150,
            messages=[{'role': 'user', 'content': prompt}]
        )
        txt = resp.content[0].text.strip()
        m = re.search(r'\{.*\}', txt, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        print(f"    [IA error] {e}")
    return {'colonia_encontrada': None, 'confianza': 'baja', 'razon': 'error al consultar IA'}

# ── Pipeline principal ────────────────────────────────────────────────────────

def detectar_mismatches(fuente: str | None = None, limite: int = 0) -> list:
    """
    Trae listings donde el GPS contradice la colonia guardada.
    Solo incluye listings con editado_manualmente = false y con coordenadas.
    """
    _cargar_colonias()

    all_listings = []
    offset = 0
    while True:
        q = sb.table('listings')\
            .select('id, colonia, lat, lng, descripcion, pagina_fuente, link_publicacion')\
            .eq('activo', True)\
            .eq('editado_manualmente', False)\
            .not_.is_('lat', 'null')\
            .not_.is_('lng', 'null')\
            .limit(500).offset(offset)
        if fuente:
            q = q.eq('pagina_fuente', fuente)
        res = q.execute()
        batch = res.data or []
        all_listings.extend(batch)
        if len(batch) < 500:
            break
        offset += 500

    print(f"  [geo] Analizando {len(all_listings)} listings con coordenadas...")

    mismatches = []
    for listing in all_listings:
        lat = listing.get('lat')
        lng = listing.get('lng')
        col_guardada = listing.get('colonia') or ''
        if not col_guardada:
            continue

        col_implan = get_colonia_implan(lat, lng)
        if col_implan is None:
            continue

        if not colonias_coinciden(col_guardada, col_implan):
            mismatches.append({
                **listing,
                'colonia_implan': col_implan,
            })

        if limite and len(mismatches) >= limite:
            break

    print(f"  [geo] {len(mismatches)} listings con colonia GPS ≠ colonia guardada")
    return mismatches


def corregir_colonias(reporte_solo: bool = False, fuente: str | None = None, limite: int = 0):
    """
    Pipeline completo: detecta mismatches → extrae colonia de descripción → actualiza DB.
    """
    print(f"\n{'='*65}")
    print(f"  VALIDADOR DE COLONIAS — IA")
    print(f"  Modo: {'reporte' if reporte_solo else 'corrección'}")
    if fuente:
        print(f"  Fuente: {fuente}")
    if limite:
        print(f"  Límite: {limite} listings")
    print(f"{'='*65}\n")

    mismatches = detectar_mismatches(fuente=fuente, limite=limite)

    if not mismatches:
        print("  No hay mismatches que corregir.")
        return

    corregidos   = 0
    sin_dato_ia  = 0
    baja_confianza = 0
    errores      = 0

    print(f"\n  {'─'*65}")
    print(f"  {'ID':>6}  {'COLONIA ACTUAL':<25}  {'IMPLAN GPS':<25}  {'CORRECCIÓN IA'}")
    print(f"  {'─'*65}")

    for listing in mismatches:
        id_l         = listing['id']
        col_actual   = listing['colonia'] or ''
        col_implan   = listing['colonia_implan']
        descripcion  = listing.get('descripcion') or ''

        if not descripcion.strip():
            sin_dato_ia += 1
            print(f"  {id_l:>6}  {col_actual:<25}  {col_implan:<25}  (sin descripción)")
            continue

        resultado = extraer_colonia_de_descripcion(descripcion, col_actual, col_implan)
        time.sleep(0.2)

        colonia_ia  = resultado.get('colonia_encontrada')
        confianza   = resultado.get('confianza', 'baja')
        razon       = resultado.get('razon', '')

        if not colonia_ia:
            sin_dato_ia += 1
            print(f"  {id_l:>6}  {col_actual:<25}  {col_implan:<25}  (IA no encontró)")
            continue

        if confianza == 'baja':
            baja_confianza += 1
            print(f"  {id_l:>6}  {col_actual:<25}  {col_implan:<25}  baja confianza: {colonia_ia}")
            continue

        print(f"  {id_l:>6}  {col_actual:<25}  {col_implan:<25}  → {colonia_ia} [{confianza}]")

        if not reporte_solo:
            try:
                sb.table('listings').update({
                    'colonia':       colonia_ia,
                    'notas_editor':  f'[auto] Colonia corregida: "{col_actual}" → "{colonia_ia}" (IMPLAN: {col_implan}). {razon}'[:500],
                    'fecha_edicion': __import__('datetime').datetime.now().isoformat(),
                }).eq('id', id_l).execute()
                corregidos += 1
            except Exception as e:
                print(f"    [DB error] {e}")
                errores += 1

    print(f"\n  {'─'*65}")
    print(f"  RESUMEN")
    print(f"  {'─'*65}")
    print(f"  Mismatches encontrados: {len(mismatches)}")
    print(f"  Corregidos (alta/media): {corregidos}")
    print(f"  Sin descripción o IA vacía: {sin_dato_ia}")
    print(f"  Baja confianza (no modificados): {baja_confianza}")
    if errores:
        print(f"  Errores DB: {errores}")
    print(f"  {'─'*65}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Validador IA de colonias")
    parser.add_argument('--reporte',  action='store_true', help='Solo reporte, no modifica DB')
    parser.add_argument('--limite',   type=int, default=0, help='Máximo de listings a procesar')
    parser.add_argument('--fuente',   type=str, default=None, help='Filtrar por pagina_fuente')
    args = parser.parse_args()

    corregir_colonias(
        reporte_solo=args.reporte,
        fuente=args.fuente,
        limite=args.limite,
    )
