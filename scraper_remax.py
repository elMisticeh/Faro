"""
scraper_remax.py — Scraper RE/MAX Laguna (oficina_id=26)
=========================================================
Estrategia:
  1. Playwright: carga la página de la oficina → extrae IDs de propiedades
  2. aiohttp: llama FetchPropiedadFlyerData/{id} en paralelo (20 concurrentes)
  3. Mapea al schema de listings y hace upsert en Supabase

Uso:
    py scraper_remax.py              # corre completo
    py scraper_remax.py --dry-run    # solo muestra cuántos, no inserta
"""

import asyncio
import argparse
import os
import sys
from html import unescape
import re

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()
from db_utils import upsert_listings_batch

# ─── Config ───────────────────────────────────────────────────────────────────

OFICINA_URL   = 'https://remax.com.mx/propiedades/venta?oficina_id=26'
FLYER_API     = 'https://remax.com.mx/ajax/FetchPropiedadFlyerData/{id}'
PAGINA_FUENTE = 'remax_laguna'
CONCURRENCIA  = 20  # requests simultáneos

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://remax.com.mx/',
    'X-Requested-With': 'XMLHttpRequest',
}

# ─── Paso 1: Obtener IDs de propiedades ───────────────────────────────────────

async def obtener_ids_propiedades() -> list:
    """Carga la página de la oficina y extrae los IDs de los propCards."""
    print(f'[remax] Cargando pagina de oficina...')
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=HEADERS['User-Agent'],
            viewport={'width': 1280, 'height': 800},
            locale='es-MX',
        )
        page = await context.new_page()
        await page.goto(OFICINA_URL, wait_until='networkidle', timeout=45000)
        await page.wait_for_timeout(2000)
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.propCard')
    ids = [c['id'] for c in cards if c.get('id') and c['id'].isdigit()]
    print(f'[remax] {len(ids)} propiedades encontradas')
    return ids

# ─── Paso 2: Obtener detalles en paralelo ─────────────────────────────────────

async def obtener_detalle_async(session, prop_id: str) -> dict:
    """Llama FetchPropiedadFlyerData y retorna los datos crudos."""
    url = FLYER_API.format(id=prop_id)
    try:
        async with session.get(url, headers=HEADERS, timeout=15) as resp:
            if resp.status != 200:
                return None
            data = await resp.json(content_type=None)
            return data.get('data', {}).get('propiedad')
    except Exception as e:
        print(f'  [warn] ID {prop_id}: {e}')
        return None

async def obtener_todos_detalles(ids: list) -> list:
    """Descarga detalles de todas las propiedades con concurrencia limitada."""
    try:
        import aiohttp
    except ImportError:
        print('[error] Instala aiohttp: pip install aiohttp')
        return []

    semaforo = asyncio.Semaphore(CONCURRENCIA)
    resultados = []

    async def fetch_con_limite(session, prop_id):
        async with semaforo:
            prop = await obtener_detalle_async(session, prop_id)
            return prop

    print(f'[remax] Descargando detalles ({CONCURRENCIA} concurrentes)...')
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_con_limite(session, pid) for pid in ids]
        props = await asyncio.gather(*tasks)

    for p in props:
        if p is not None:
            resultados.append(p)

    print(f'[remax] {len(resultados)}/{len(ids)} detalles obtenidos')
    return resultados

# ─── Paso 3: Mapear a schema de listings ──────────────────────────────────────

TIPO_INMUEBLE_MAP = {
    'Casa': 'casa',
    'Departamento': 'departamento',
    'Terreno': 'terreno',
    'Terreno - Comercial': 'terreno_comercial',
    'Terreno - Industrial': 'terreno_industrial',
    'Local - Comercial': 'local_comercial',
    'Bodega - Comercial': 'bodega_comercial',
    'Edificio - Comercial': 'edificio_comercial',
    'Casa - Comercial': 'casa_comercial',
    'Consultorio - Comercial': 'consultorio_comercial',
    'Finca/Rancho': 'rancho',
    'Oficina - Comercial': 'oficina_comercial',
}

TIPO_OP_MAP = {
    '1': 'venta', '2': 'renta', '3': 'venta',
    1: 'venta', 2: 'renta', 3: 'venta',
}

def mapear_listing(prop: dict) -> dict:
    """Convierte datos crudos de RE/MAX al schema de listings."""
    prop_id = prop.get('propiedad_id')
    if not prop_id:
        return None

    if str(prop.get('archivado', '0')) == '1':
        return None
    if str(prop.get('publicar', '1')) == '0':
        return None

    link = f'https://remax.com.mx/propiedad/{prop_id}'

    # Precio
    # Si el listing está en USD, mxn_original es una conversión interna de ReMax
    # que puede usar un tipo de cambio desactualizado — usar usd_original para
    # detectar y saltar estos casos hasta tener conversión confiable.
    moneda = (prop.get('moneda') or 'MXN').strip().upper()
    try:
        precio = float(prop.get('mxn_original') or 0)
    except (ValueError, TypeError):
        precio = 0.0
    if precio <= 0:
        return None
    if moneda == 'USD':
        print(f'  [skip] ID {prop_id}: precio en USD (mxn_original={precio:,.0f}) — omitiendo')
        return None

    # Coordenadas
    def safe_float(v, default=None):
        try:
            f = float(v or 0)
            return f if f != 0 else default
        except (ValueError, TypeError):
            return default

    lat = safe_float(prop.get('latitud'))
    lng = safe_float(prop.get('longitud'))
    m2_construccion = safe_float(prop.get('m2_construccion'))
    m2_terreno      = safe_float(prop.get('m2_terreno'))

    def safe_int(v):
        try:
            f = float(v or 0)
            return int(f) if f > 0 else None
        except (ValueError, TypeError):
            return None

    recamaras = safe_int(prop.get('cuartos'))
    banos = safe_float(prop.get('banos'))

    tipo_operacion = TIPO_OP_MAP.get(prop.get('operacion', '1'), 'venta')
    tipo_raw = prop.get('tipo_nombre') or 'Casa'
    tipo_inmueble = TIPO_INMUEBLE_MAP.get(tipo_raw, tipo_raw.lower().replace(' ', '_').replace('/', '_').replace('-', '').strip('_'))

    colonia_nombre = prop.get('colonia_nombre') or prop.get('colonia') or ''
    calle    = prop.get('calle') or ''
    num_ext  = str(prop.get('numero_exterior') or '')
    ciudad   = prop.get('ciudad_nombre') or ''
    postal   = str(prop.get('postal') or '')
    direccion = f'{calle} {num_ext}, {colonia_nombre}, {ciudad} {postal}'.strip(', ')

    desc_raw = prop.get('descripcion') or ''
    descripcion = re.sub(r'<[^>]+>', ' ', desc_raw)
    descripcion = re.sub(r'\s+', ' ', unescape(descripcion)).strip()

    nivel = 'destacado' if str(prop.get('destacado', '')) == 'si' else 'normal'

    return {
        'link_publicacion': link,
        'pagina_fuente': PAGINA_FUENTE,
        'tipo_inmueble': tipo_inmueble,
        'tipo_operacion': tipo_operacion,
        'precio_mxn': precio,
        'colonia': colonia_nombre,
        'direccion': direccion,
        'lat': lat,
        'lng': lng,
        'm2_construccion': m2_construccion,
        'm2_terreno': m2_terreno,
        'recamaras': recamaras,
        'banos': banos,
        'descripcion': descripcion[:2000] if descripcion else None,
        'activo': True,
        'estado_inmueble': 'usado',
        'nivel_premium': nivel,
        'score_calidad_anuncio': 70,
    }

# ─── Main ─────────────────────────────────────────────────────────────────────

async def main(dry_run=False):
    # 1. IDs
    ids = await obtener_ids_propiedades()
    if not ids:
        print('[remax] No se encontraron propiedades.')
        return

    # 2. Detalles en paralelo
    props = await obtener_todos_detalles(ids)

    # 3. Mapear
    listings = []
    for prop in props:
        l = mapear_listing(prop)
        if l:
            listings.append(l)

    print(f'[remax] {len(listings)} listings válidos (de {len(props)} con datos)')

    if dry_run:
        print('[remax] DRY RUN - no se inserta en Supabase')
        con_coords = sum(1 for l in listings if l['lat'] and l['lng'])
        tipos = {}
        for l in listings:
            t = l['tipo_inmueble']
            tipos[t] = tipos.get(t, 0) + 1
        print(f'  Con coordenadas: {con_coords}/{len(listings)}')
        print(f'  Tipos: {tipos}')
        for l in listings[:3]:
            print(f'  {l["link_publicacion"]} | {l["tipo_inmueble"]} | '
                  f'${l["precio_mxn"]:,.0f} | {l["colonia"]} | lat={l["lat"]}')
        return

    # 4. Upsert
    print('[remax] Insertando en Supabase...')
    stats = upsert_listings_batch(listings, link_field='link_publicacion')
    print(f'[remax] Listo: {stats}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
