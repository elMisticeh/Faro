"""
mercadolibre.py — Scraper via API oficial de Mercado Libre
=========================================================
Usa la API pública gratuita (sin creds para búsqueda básica).
Docs: https://developers.mercadolibre.com.mx/es_ar/items-y-busquedas

No requiere Playwright — es REST puro, más rápido y confiable.
"""
import asyncio
import aiohttp
from .base import (limpiar_precio, calcular_precio_x_m2,
                   enriquecer_con_ia, guardar_listing)

NOMBRE = "mercadolibre"
BASE_API = "https://api.mercadolibre.com"

# Torreón, Coahuila en ML = TM1652 (Torreón)
# Categoría inmuebles en México = MLM1459
SITE = "MLM"
CIUDAD = "TM1652"

BUSQUEDAS = [
    # (categoría ML, tipo_operacion)
    ("MLM1459",  "venta"),   # Inmuebles (todas las subcategorías)
]

# Subcategorías específicas por si acaso
SUBCATEGORIAS_VENTA = [
    "MLM1472",  # Casas en venta
    "MLM1474",  # Departamentos en venta
    "MLM1468",  # Terrenos en venta
    "MLM1500",  # Locales comerciales
    "MLM1502",  # Bodegas
]

async def fetch_items(session: aiohttp.ClientSession, categoria: str, offset: int = 0) -> dict:
    url = (
        f"{BASE_API}/sites/{SITE}/search"
        f"?category={categoria}"
        f"&state=TUxNUENPQTM5NTU"   # Coahuila
        f"&city={CIUDAD}"
        f"&limit=50&offset={offset}"
    )
    async with session.get(url) as r:
        if r.status != 200:
            return {"results": [], "paging": {"total": 0}}
        return await r.json()

async def fetch_detalle(session: aiohttp.ClientSession, item_id: str) -> dict:
    """Detalles adicionales del listing (descripción, m², etc.)"""
    url = f"{BASE_API}/items/{item_id}"
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
        if r.status != 200:
            return {}
        return await r.json()

def extraer_atributo(atributos: list, nombre: str) -> str | None:
    """Extrae valor de atributos ML por nombre."""
    for attr in atributos:
        if attr.get("name", "").lower() == nombre.lower():
            return attr.get("value_name") or attr.get("value_struct", {}).get("number")
    return None

async def scrapear(max_por_categoria: int = 500) -> dict:
    stats = {"nuevo": 0, "actualizado": 0, "error": 0, "total_api": 0}

    async with aiohttp.ClientSession() as session:
        for categoria in SUBCATEGORIAS_VENTA:
            offset = 0
            cat_total = 0
            print(f"\n  ML categoría {categoria}:", end="", flush=True)

            while offset < max_por_categoria:
                try:
                    data = await fetch_items(session, categoria, offset)
                    items = data.get("results", [])
                    total_disponible = data.get("paging", {}).get("total", 0)

                    if not items:
                        break

                    for item in items:
                        try:
                            stats["total_api"] += 1
                            item_id   = item.get("id")
                            titulo    = item.get("title", "")
                            precio    = float(item.get("price", 0)) or None
                            link      = item.get("permalink", "")
                            moneda    = item.get("currency_id", "MXN")

                            # Convertir USD a MXN aproximado si aplica
                            if moneda == "USD" and precio:
                                precio = precio * 17.5  # tipo de cambio aproximado

                            # Ubicación
                            loc = item.get("location", {})
                            colonia = (
                                loc.get("neighborhood", {}).get("name") or
                                loc.get("city", {}).get("name") or
                                "Torreón"
                            )

                            # Atributos (m², recámaras, etc.)
                            atributos = item.get("attributes", [])
                            m2_total    = extraer_atributo(atributos, "Metros cuadrados totales")
                            m2_terreno  = extraer_atributo(atributos, "Metros cuadrados del terreno")
                            m2_constr   = extraer_atributo(atributos, "Metros cuadrados construidos")
                            recamaras   = extraer_atributo(atributos, "Recámaras")
                            banos       = extraer_atributo(atributos, "Baños")
                            tipo_inm    = extraer_atributo(atributos, "Tipo de propiedad")
                            operacion   = extraer_atributo(atributos, "Tipo de operación")

                            # Normalizar tipo operación
                            tipo_op = "renta" if operacion and "renta" in operacion.lower() else "venta"

                            m2_num_constr  = float(m2_constr) if m2_constr else None
                            m2_num_terreno = float(m2_terreno or m2_total or 0) or None
                            m2_ref         = m2_num_constr or m2_num_terreno
                            pm2            = calcular_precio_x_m2(precio, m2_ref)

                            # IA solo si falta tipo inmueble
                            datos_ia = {}
                            if not tipo_inm and titulo:
                                datos_ia = enriquecer_con_ia(titulo, precio or 0, colonia, tipo_op)

                            resultado = guardar_listing({
                                "link_publicacion":   link,
                                "pagina_fuente":      NOMBRE,
                                "descripcion":        titulo,
                                "colonia":            colonia,
                                "precio_mxn":         precio,
                                "precio_x_m2":        pm2,
                                "tipo_operacion":     tipo_op,
                                "tipo_inmueble":      (tipo_inm or datos_ia.get("tipo_inmueble", "")).lower().replace(" ", "_") or None,
                                "recamaras":          int(recamaras) if recamaras else datos_ia.get("recamaras"),
                                "banos":              float(banos) if banos else datos_ia.get("banos"),
                                "m2_terreno":         m2_num_terreno,
                                "m2_construccion":    m2_num_constr,
                                "estado_inmueble":    datos_ia.get("estado_inmueble"),
                                "nivel_premium":      datos_ia.get("nivel_premium"),
                                "amenidades":         datos_ia.get("amenidades", []),
                                "score_calidad_anuncio": datos_ia.get("score_calidad_anuncio"),
                            })
                            stats[resultado] = stats.get(resultado, 0) + 1
                            cat_total += 1
                            await asyncio.sleep(0.1)

                        except Exception as e:
                            stats["error"] += 1

                    print(f" {cat_total}", end="", flush=True)
                    offset += 50
                    if offset >= total_disponible:
                        break
                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"\n    Error API ML: {e}")
                    break

            print(f" ({cat_total} procesados)")

    return stats
