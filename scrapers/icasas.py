"""icasas.py — Scraper para icasas.mx"""
import asyncio
from playwright.async_api import Page
from .base import (limpiar_precio, parsear_features, calcular_precio_x_m2,
                   enriquecer_con_ia, guardar_listing)
import re

NOMBRE = "icasas"
BASE   = "https://www.icasas.mx"

URLS = [
    (f"{BASE}/casas-en-venta-en-torreon-coahuila",         "venta"),
    (f"{BASE}/departamentos-en-venta-en-torreon-coahuila", "venta"),
    (f"{BASE}/terrenos-en-venta-en-torreon-coahuila",      "venta"),
    (f"{BASE}/locales-en-venta-en-torreon-coahuila",       "venta"),
    (f"{BASE}/casas-en-renta-en-torreon-coahuila",         "renta"),
    (f"{BASE}/departamentos-en-renta-en-torreon-coahuila", "renta"),
]

async def scrapear_pagina(page: Page, url: str, tipo_op: str, max_pags: int) -> dict:
    stats = {"nuevo": 0, "actualizado": 0, "error": 0, "paginas": 0}
    url_actual = url

    for pag in range(1, max_pags + 1):
        try:
            await page.goto(url_actual, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"    Error p{pag}: {e}")
            break

        listings = await page.query_selector_all(
            ".propiedades article, .listing-item, article.property, [class*='listing-card']"
        )
        if not listings:
            break

        stats["paginas"] += 1
        print(f"    Pág {pag}: {len(listings)} listings", end="", flush=True)

        for listing in listings:
            try:
                precio_el = await listing.query_selector("[class*='price'], .precio, h3.price")
                precio = limpiar_precio((await precio_el.inner_text()).strip() if precio_el else "")

                titulo_el = await listing.query_selector("h2, h3, [class*='title']")
                desc = (await titulo_el.inner_text()).strip() if titulo_el else ""

                loc_el = await listing.query_selector("[class*='location'], [class*='address'], .ubicacion")
                ubic_txt = (await loc_el.inner_text()).strip() if loc_el else ""
                colonia = ubic_txt.split(",")[0].strip()

                a_el = await listing.query_selector("a[href]")
                href = await a_el.get_attribute("href") if a_el else None
                if href and not href.startswith("http"):
                    href = BASE + href

                feat_spans = await listing.query_selector_all("[class*='feature'] span, [class*='amenity'], li")
                textos = [(await s.inner_text()).strip() for s in feat_spans]
                feats = parsear_features([t for t in textos if t])

                m2_ref = feats.get("m2_construccion") or feats.get("m2_terreno")
                pm2 = calcular_precio_x_m2(precio, m2_ref)
                datos_ia = enriquecer_con_ia(desc, precio or 0, colonia, tipo_op) if (desc or colonia) else {}

                resultado = guardar_listing({
                    "link_publicacion":   href,
                    "pagina_fuente":      NOMBRE,
                    "descripcion":        desc,
                    "colonia":            colonia,
                    "precio_mxn":         precio,
                    "precio_x_m2":        pm2,
                    "tipo_operacion":     datos_ia.get("tipo_operacion", tipo_op),
                    "tipo_inmueble":      datos_ia.get("tipo_inmueble"),
                    "recamaras":          feats.get("recamaras") or datos_ia.get("recamaras"),
                    "banos":              feats.get("banos") or datos_ia.get("banos"),
                    "m2_terreno":         feats.get("m2_terreno"),
                    "m2_construccion":    feats.get("m2_construccion"),
                    "estado_inmueble":    datos_ia.get("estado_inmueble"),
                    "nivel_premium":      datos_ia.get("nivel_premium"),
                    "amenidades":         datos_ia.get("amenidades", []),
                    "score_calidad_anuncio": datos_ia.get("score_calidad_anuncio"),
                })
                stats[resultado] = stats.get(resultado, 0) + 1
                await asyncio.sleep(0.2)

            except Exception as e:
                stats["error"] += 1

        print(f" ✓")

        # Paginación iCasas: /pagina-2
        if pag < max_pags:
            base_url = re.sub(r"/pagina-\d+$", "", url_actual.rstrip("/"))
            url_actual = f"{base_url}/pagina-{pag+1}"
            await asyncio.sleep(2)
        else:
            break

    return stats
