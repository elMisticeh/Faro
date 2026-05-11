"""lamudi.py — Scraper para lamudi.com.mx"""
import asyncio
from playwright.async_api import Page
from .base import (limpiar_precio, limpiar_m2, calcular_precio_x_m2,
                   enriquecer_con_ia, guardar_listing)
import re

NOMBRE = "lamudi"
BASE   = "https://www.lamudi.com.mx"

URLS = [
    (f"{BASE}/coahuila/torreon/casas/venta/",        "venta"),
    (f"{BASE}/coahuila/torreon/departamentos/venta/","venta"),
    (f"{BASE}/coahuila/torreon/terrenos/venta/",     "venta"),
    (f"{BASE}/coahuila/torreon/locales/venta/",      "venta"),
    (f"{BASE}/coahuila/torreon/casas/renta/",        "renta"),
    (f"{BASE}/coahuila/torreon/departamentos/renta/","renta"),
    (f"{BASE}/coahuila/torreon/locales/renta/",      "renta"),
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
            ".js-listing-link, .ListingCell-content, article[class*='listing'], .property-listing"
        )
        if not listings:
            # Intentar con JSON-LD embebido como fallback
            scripts = await page.query_selector_all("script[type='application/ld+json']")
            break

        stats["paginas"] += 1
        print(f"    Pág {pag}: {len(listings)} listings", end="", flush=True)

        for listing in listings:
            try:
                precio_el = await listing.query_selector(
                    ".price, .listing-price, [class*='price'], h3"
                )
                precio = limpiar_precio((await precio_el.inner_text()).strip() if precio_el else "")

                titulo_el = await listing.query_selector("h2, h3, .listing-title, [class*='title']")
                desc = (await titulo_el.inner_text()).strip() if titulo_el else ""

                loc_el = await listing.query_selector("[class*='location'], [class*='address'], address")
                ubic_txt = (await loc_el.inner_text()).strip() if loc_el else ""
                colonia = ubic_txt.split(",")[0].strip()

                a_el = await listing.query_selector("a[href]")
                href = await a_el.get_attribute("href") if a_el else None
                if href and not href.startswith("http"):
                    href = BASE + href

                # m² desde atributos o texto
                m2_terreno = None
                m2_constr = None
                m2_el = await listing.query_selector("[class*='size'], [class*='area'], [data-stat='surface']")
                if m2_el:
                    m2_txt = (await m2_el.inner_text()).strip()
                    m2_terreno = limpiar_m2(m2_txt)

                pm2 = calcular_precio_x_m2(precio, m2_constr or m2_terreno)
                datos_ia = enriquecer_con_ia(desc, precio or 0, colonia, tipo_op) if (desc or colonia) else {}

                resultado = guardar_listing({
                    "link_publicacion":  href,
                    "pagina_fuente":     NOMBRE,
                    "descripcion":       desc,
                    "colonia":           colonia,
                    "precio_mxn":        precio,
                    "precio_x_m2":       pm2,
                    "tipo_operacion":    datos_ia.get("tipo_operacion", tipo_op),
                    "tipo_inmueble":     datos_ia.get("tipo_inmueble"),
                    "m2_terreno":        m2_terreno,
                    "estado_inmueble":   datos_ia.get("estado_inmueble"),
                    "nivel_premium":     datos_ia.get("nivel_premium"),
                    "amenidades":        datos_ia.get("amenidades", []),
                    "score_calidad_anuncio": datos_ia.get("score_calidad_anuncio"),
                })
                stats[resultado] = stats.get(resultado, 0) + 1
                await asyncio.sleep(0.2)

            except Exception as e:
                stats["error"] += 1

        print(f" ✓")

        # Paginación Lamudi: ?page=2
        if pag < max_pags:
            next_url = re.sub(r"[?&]page=\d+", "", url_actual)
            sep = "&" if "?" in next_url else "?"
            url_actual = f"{next_url}{sep}page={pag+1}"
            await asyncio.sleep(2)
        else:
            break

    return stats
