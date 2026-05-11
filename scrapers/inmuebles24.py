"""
inmuebles24.py — Scraper para inmuebles24.com
============================================
- Paginación corregida con URLs directas (/pagina-N.html)
- Colonia extraída de ubicación; si es genérica, IA la saca de descripción
- m² y recámaras desde features HTML; si faltan, IA los extrae de descripción
- Solo listings de Torreón (la URL ya filtra por ciudad)
"""
import asyncio, re
from playwright.async_api import Page
from .base import limpiar_precio, parsear_features, enriquecer_con_ia, guardar_listing

NOMBRE = "inmuebles24"
BASE   = "https://www.inmuebles24.com"

# URL base → (url_pag1, tipo_operacion, tipo_inmueble_hint)
URLS = [
    # VENTA — URLs confirmadas desde HTML real de i24
    (f"{BASE}/casas-en-venta-en-torreon.html",               "venta", "casa"),
    (f"{BASE}/departamentos-en-venta-en-torreon.html",       "venta", "departamento"),
    (f"{BASE}/terrenos-en-venta-en-torreon.html",            "venta", "terreno"),
    (f"{BASE}/terreno-comercial-en-venta-en-torreon.html",   "venta", "terreno"),
    (f"{BASE}/locales-comerciales-en-venta-en-torreon.html", "venta", "local_comercial"),
    # RENTA — URLs confirmadas desde HTML real de i24
    (f"{BASE}/casas-en-renta-en-torreon.html",               "renta", "casa"),
    (f"{BASE}/departamentos-en-renta-en-torreon.html",       "renta", "departamento"),
    (f"{BASE}/locales-comerciales-en-renta-en-torreon.html", "renta", "local_comercial"),
    (f"{BASE}/bodegas-comerciales-en-renta-en-torreon.html", "renta", "bodega"),
    (f"{BASE}/oficinas-en-renta-en-torreon.html",            "renta", "oficina"),
    # POR COLONIA — máxima cobertura de colonias populares
    (f"{BASE}/casas-en-venta-en-fraccionamiento-las-trojes-ciudad-de-torreon.html",    "venta", "casa"),
    (f"{BASE}/casas-en-venta-en-fraccionamiento-monterreal-ciudad-de-torreon.html",    "venta", "casa"),
    (f"{BASE}/casas-en-venta-en-san-isidro-ciudad-de-torreon.html",                    "venta", "casa"),
    (f"{BASE}/casas-en-venta-en-el-castano-ciudad-de-torreon.html",                    "venta", "casa"),
    (f"{BASE}/inmuebles-en-venta-en-san-isidro-ciudad-de-torreon.html",                "venta", "casa"),
    (f"{BASE}/inmuebles-en-renta-en-ciudad-industrial-ciudad-de-torreon.html",         "renta", "local_comercial"),
    # INMOBILIARIAS — listings de agencias locales de Torreón
    (f"{BASE}/inmobiliarias/re-max-laguna_5022",                                       "venta", "casa"),
]

SEL_LISTINGS  = '[data-qa="posting PROPERTY"]'
SEL_PRECIO    = '[data-qa="POSTING_CARD_PRICE"]'
SEL_UBICACION = '[data-qa="POSTING_CARD_LOCATION"]'
SEL_FEATURES  = '[data-qa="POSTING_CARD_FEATURES"]'
SEL_DESC      = '[data-qa="POSTING_CARD_DESCRIPTION"]'
SEL_SIGUIENTE = '[data-qa="PAGING_NEXT"]'

COLONIAS_GENERICAS = {"torreón","torreon","torreón, coahuila","torreón coahuila",
                       "coahuila","coahuila de zaragoza",""}

def url_pagina(url_base: str, n: int) -> str:
    """Construye URL de página N a partir de la URL base."""
    if n == 1:
        return url_base
    # /casas-en-venta-en-torreon.html → /casas-en-venta-en-torreon-pagina-2.html
    return re.sub(r'\.html$', f'-pagina-{n}.html', url_base)

async def scrapear_url_pagina(url: str) -> list:
    """Abre browser fresco y extrae listings de una URL. Evita detección anti-bot."""
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="es-MX",
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3500)
            try:
                await page.wait_for_selector(SEL_LISTINGS, timeout=8000)
            except:
                pass
            listings = await page.query_selector_all(SEL_LISTINGS)
            # Extraer datos mientras el page está abierto
            resultados = []
            for listing in listings:
                try:
                    precio_el = await listing.query_selector(SEL_PRECIO)
                    precio_txt = (await precio_el.inner_text()).strip() if precio_el else ""

                    ubic_el = await listing.query_selector(SEL_UBICACION)
                    ubic_txt = (await ubic_el.inner_text()).strip() if ubic_el else ""

                    desc_el = await listing.query_selector(SEL_DESC)
                    desc = (await desc_el.inner_text()).strip() if desc_el else ""

                    tag = await (await listing.get_property("tagName")).json_value()
                    if tag.lower() == "a":
                        href = await listing.get_attribute("href")
                    else:
                        a = await listing.query_selector("a[href]")
                        href = await a.get_attribute("href") if a else None
                    if href and not href.startswith("http"):
                        href = "https://www.inmuebles24.com" + href

                    feat_el = await listing.query_selector(SEL_FEATURES)
                    feat_textos = []
                    if feat_el:
                        spans = await feat_el.query_selector_all("span")
                        feat_textos = [(await s.inner_text()).strip() for s in spans]

                    resultados.append({
                        "precio_txt": precio_txt,
                        "ubic_txt": ubic_txt,
                        "desc": desc,
                        "href": href,
                        "feat_textos": feat_textos,
                    })
                except:
                    pass
            return resultados
        except Exception as e:
            print(f"    Error en {url}: {e}")
            return []
        finally:
            await browser.close()


async def scrapear_url(page, url_base: str, tipo_op: str,
                       tipo_inm_hint: str, max_pags: int) -> dict:
    stats = {"nuevo": 0, "actualizado": 0, "error": 0,
             "fuera_de_torreon": 0, "precio_invalido": 0, "paginas": 0}

    for pag in range(1, max_pags + 1):
        url_actual = url_pagina(url_base, pag)

        # Browser fresco por página — evita detección anti-bot de i24
        resultados = await scrapear_url_pagina(url_actual)

        if not resultados:
            print(f"    Pág {pag}: sin listings — fin.")
            break

        stats["paginas"] += 1
        print(f"    Pág {pag}/{max_pags}: {len(resultados)} listings", end="", flush=True)

        nuevos_esta_pag = 0
        for r in resultados:
            try:
                precio_txt = r["precio_txt"]
                precio     = limpiar_precio(precio_txt)
                ubic_txt   = r["ubic_txt"]
                desc       = r["desc"]
                href       = r["href"]

                partes = [p.strip() for p in ubic_txt.split(",")]
                colonia_raw = partes[0] if partes else ""
                colonia_es_generica = colonia_raw.lower() in COLONIAS_GENERICAS

                feats = parsear_features([t for t in r["feat_textos"] if t])

                # ── IA: colonia desde descripción + m² faltantes ─────
                # Llamar IA si: colonia es genérica O faltan m²
                necesita_ia = (colonia_es_generica or
                               ("m2_terreno" not in feats and "m2_construccion" not in feats))

                datos_ia = {}
                if necesita_ia and (desc or colonia_raw):
                    datos_ia = enriquecer_con_ia(
                        descripcion=desc,
                        precio=precio or 0,
                        colonia=colonia_raw,
                        tipo_op=tipo_op,
                    )

                # Colonia final: usar la de IA si la original es genérica
                colonia_final = colonia_raw
                if colonia_es_generica:
                    colonia_ia = datos_ia.get("colonia") or datos_ia.get("colonia_extraida")
                    if colonia_ia and isinstance(colonia_ia, str):
                        colonia_final = colonia_ia.strip()

                # m² finales: HTML tiene prioridad, IA complementa
                m2_terreno   = feats.get("m2_terreno")   or datos_ia.get("m2_terreno")
                m2_constr    = feats.get("m2_construccion") or datos_ia.get("m2_construccion")
                recamaras    = feats.get("recamaras")     or datos_ia.get("recamaras")
                banos        = feats.get("banos")         or datos_ia.get("banos")

                resultado = guardar_listing({
                    "link_publicacion":      href,
                    "pagina_fuente":         NOMBRE,
                    "descripcion":           desc,
                    "colonia":               colonia_final or None,
                    "precio_mxn":            precio,
                    "tipo_operacion":        datos_ia.get("tipo_operacion", tipo_op),
                    "tipo_inmueble":         datos_ia.get("tipo_inmueble", tipo_inm_hint),
                    "recamaras":             recamaras,
                    "banos":                 banos,
                    "m2_terreno":            m2_terreno,
                    "m2_construccion":       m2_constr,
                    "estado_inmueble":       datos_ia.get("estado_inmueble"),
                    "nivel_premium":         datos_ia.get("nivel_premium"),
                    "amenidades":            datos_ia.get("amenidades", []),
                    "uso_suelo_inferido":    datos_ia.get("uso_suelo_inferido"),
                    "score_calidad_anuncio": datos_ia.get("score_calidad_anuncio"),
                })
                stats[resultado] = stats.get(resultado, 0) + 1
                if resultado == "nuevo":
                    nuevos_esta_pag += 1
                await asyncio.sleep(0.2)

            except Exception as e:
                stats["error"] += 1

        print(f" | +{nuevos_esta_pag} nuevos")

        # Si toda la página son actualizaciones (ya los tenemos), parar
        if pag > 2 and nuevos_esta_pag == 0:
            print(f"    Pág {pag}: todos ya existían — parando.")
            break

        await asyncio.sleep(1.5)

    return stats


async def scrapear_pagina(page: Page, url: str, tipo_op: str, max_pags: int) -> dict:
    """Interfaz compatible con scraper_master.py"""
    # Detectar tipo de inmueble desde la URL
    tipo_hint = "casa"
    if "terreno" in url: tipo_hint = "terreno"
    elif "departamento" in url: tipo_hint = "departamento"
    elif "local" in url: tipo_hint = "local_comercial"
    elif "bodega" in url: tipo_hint = "bodega"
    elif "oficina" in url: tipo_hint = "oficina"

    return await scrapear_url(page, url, tipo_op, tipo_hint, max_pags)
