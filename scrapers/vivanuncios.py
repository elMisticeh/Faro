"""vivanuncios.py — Scraper para vivanuncios.com.mx (plataforma Navent, similar a i24)"""
import asyncio
from playwright.async_api import Page
from .base import (limpiar_precio, parsear_features, calcular_precio_x_m2,
                   enriquecer_con_ia, guardar_listing)

NOMBRE = "vivanuncios"
BASE   = "https://www.vivanuncios.com.mx"

URLS = [
    (f"{BASE}/s-venta-inmuebles/torreon/v1c1098l10578p1", "venta"),
    (f"{BASE}/s-renta-inmuebles/torreon/v1c1097l10578p1", "renta"),
]

SEL = {
    "listings":  "article.listing-card, [data-qa='posting PROPERTY'], li.listing",
    "precio":    "[data-qa='POSTING_CARD_PRICE'], .price-value, .listing-card__price",
    "ubicacion": "[data-qa='POSTING_CARD_LOCATION'], .listing-card__location",
    "features":  "[data-qa='POSTING_CARD_FEATURES'], .listing-main-features",
    "desc":      "[data-qa='POSTING_CARD_DESCRIPTION'], .listing-card__title",
    "siguiente": "[data-qa='PAGING_NEXT'], a[rel='next'], .pagination__next",
}

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

        # Vivanuncios puede usar estructura Navent igual que i24
        listings = await page.query_selector_all("[data-qa='posting PROPERTY']")
        if not listings:
            # Fallback a selectores alternativos
            listings = await page.query_selector_all("article.listing-card")
        if not listings:
            break

        stats["paginas"] += 1
        print(f"    Pág {pag}: {len(listings)} listings", end="", flush=True)

        for listing in listings:
            try:
                precio_el = await listing.query_selector(SEL["precio"])
                precio = limpiar_precio((await precio_el.inner_text()).strip() if precio_el else "")

                ubic_el = await listing.query_selector(SEL["ubicacion"])
                ubic_txt = (await ubic_el.inner_text()).strip() if ubic_el else ""
                colonia = ubic_txt.split(",")[0].strip()

                desc_el = await listing.query_selector(SEL["desc"])
                desc = (await desc_el.inner_text()).strip() if desc_el else ""

                tag = await (await listing.get_property("tagName")).json_value()
                if tag.lower() == "a":
                    href = await listing.get_attribute("href")
                else:
                    a = await listing.query_selector("a[href]")
                    href = await a.get_attribute("href") if a else None
                if href and not href.startswith("http"):
                    href = BASE + href

                feat_el = await listing.query_selector(SEL["features"])
                feats = {}
                if feat_el:
                    spans = await feat_el.query_selector_all("span, li")
                    textos = [(await s.inner_text()).strip() for s in spans]
                    feats = parsear_features([t for t in textos if t])

                m2_ref = feats.get("m2_construccion") or feats.get("m2_terreno")
                pm2 = calcular_precio_x_m2(precio, m2_ref)
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
                    "recamaras":         feats.get("recamaras") or datos_ia.get("recamaras"),
                    "banos":             feats.get("banos") or datos_ia.get("banos"),
                    "m2_terreno":        feats.get("m2_terreno"),
                    "m2_construccion":   feats.get("m2_construccion"),
                    "estado_inmueble":   datos_ia.get("estado_inmueble"),
                    "nivel_premium":     datos_ia.get("nivel_premium"),
                    "amenidades":        datos_ia.get("amenidades", []),
                    "uso_suelo_inferido":datos_ia.get("uso_suelo_inferido"),
                    "score_calidad_anuncio": datos_ia.get("score_calidad_anuncio"),
                })
                stats[resultado] = stats.get(resultado, 0) + 1
                await asyncio.sleep(0.2)

            except Exception as e:
                stats["error"] += 1

        print(f" ✓")

        # Siguiente página — Vivanuncios usa paginación en URL (/p2, /p3...)
        sig = await page.query_selector("[data-qa='PAGING_NEXT'], a[rel='next']")
        if sig:
            next_href = await sig.get_attribute("href")
            if next_href:
                url_actual = BASE + next_href if not next_href.startswith("http") else next_href
                await asyncio.sleep(2)
                continue
        break

    return stats
