"""
validators/anomalias.py — Detecta y marca listings con datos sospechosos
========================================================================
Fase 1: Reglas automáticas (gratis, instantáneo)
Fase 2: Validación con Claude Haiku para casos dudosos

Uso:
    py validators/anomalias.py              # solo reglas automáticas
    py validators/anomalias.py --ia         # + validación IA en casos dudosos
    py validators/anomalias.py --reporte    # solo muestra, no modifica DB
"""

import os, re, json, unicodedata, argparse, time, sys
import anthropic
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
ai = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def _sanitizar_para_prompt(texto: str, max_chars: int = 500) -> str:
    """Elimina secuencias de prompt injection antes de enviar a Claude."""
    if not texto:
        return ""
    sanitizado = re.sub(
        r'(?i)(ignora|ignore|forget|olvida|instrucciones|instructions)\s*(las\s*)?(anteriores?|previous|above|previas?)',
        '[REDACTED]', texto
    )
    return sanitizado[:max_chars]

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# ── COLONIAS IMPLAN ───────────────────────────────────────────────────────────
_colonias_features = None

def _cargar_colonias():
    global _colonias_features
    if _colonias_features is not None:
        return
    geojson_path = os.path.join(_DATA_DIR, 'colonias_torreon.geojson')
    with open(geojson_path, encoding='utf-8') as f:
        data = json.load(f)
    _colonias_features = data.get('features', [])
    print(f"  [colonias] {len(_colonias_features)} polígonos IMPLAN cargados")

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

def _get_colonia_implan(lat, lng):
    if not lat or not lng:
        return None
    _cargar_colonias()
    for feat in _colonias_features:
        geom  = feat.get('geometry', {})
        props = feat.get('properties', {})
        nombre = props.get('colonia') or props.get('COLONIA') or props.get('nom_col') or ''
        if geom.get('type') == 'Polygon':
            if _punto_en_poligono(lat, lng, geom['coordinates'][0]):
                return nombre.upper().strip()
        elif geom.get('type') == 'MultiPolygon':
            for poly in geom['coordinates']:
                if _punto_en_poligono(lat, lng, poly[0]):
                    return nombre.upper().strip()
    return None

def _normalizar(texto):
    if not texto:
        return ''
    txt = unicodedata.normalize('NFD', texto.upper().strip())
    txt = ''.join(c for c in txt if unicodedata.category(c) != 'Mn')
    txt = re.sub(r'[^A-Z0-9 ]', ' ', txt)
    return re.sub(r'\s+', ' ', txt).strip()

_STOPWORDS = {
    'DE', 'DEL', 'LA', 'LAS', 'LOS', 'EL', 'EN', 'Y', 'A', 'AL', 'UN', 'UNA',
    'SAN', 'SANTA', 'SANTO',
    'RESIDENCIAL', 'JARDIN', 'JARDINES', 'VILLAS', 'VILLA',
    'FRACCIONAMIENTO', 'COLONIA', 'ETAPA', 'AMPLIACION', 'PROLONGACION',
    'NUEVA', 'NUEVO', 'SEGUNDA', 'TERCERA', 'CUARTA', 'QUINTA', 'SECCION',
    'TORREON', 'EX', 'CERRADA',
    'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
}

def _tokens(nombre):
    palabras = _normalizar(nombre).split()
    return {p for p in palabras if len(p) >= 3 and p not in _STOPWORDS}

def _colonias_coinciden(col_db, col_implan):
    if not col_db or not col_implan:
        return True
    if _normalizar(col_db) == _normalizar(col_implan):
        return True
    ta = _tokens(col_db)
    tb = _tokens(col_implan)
    if not ta or not tb:
        return True
    return bool(ta & tb)

# ── REGLAS ────────────────────────────────────────────────────────────────────

def _es_terreno(d):
    return (d.get('tipo_inmueble') or '').startswith('terreno')

def _pm2_terreno(d):
    pm2 = d.get('precio_x_m2_terreno')
    if pm2:
        return pm2
    precio = d.get('precio_mxn') or 0
    m2     = d.get('m2_terreno') or 0
    return (precio / m2) if m2 > 0 else None

def _colonia_fuera_de_pin(d):
    lat = d.get('lat')
    lng = d.get('lng')
    col_db = d.get('colonia') or ''
    if not lat or not lng or not col_db:
        return False
    col_implan = _get_colonia_implan(lat, lng)
    if col_implan is None:
        return False
    return not _colonias_coinciden(col_db, col_implan)

REGLAS = {
    'terreno_pm2_muy_bajo':   lambda d: _es_terreno(d) and _pm2_terreno(d) and _pm2_terreno(d) < 500,
    'terreno_pm2_muy_alto':   lambda d: _es_terreno(d) and _pm2_terreno(d) and _pm2_terreno(d) > 15000,
    'terreno_pm2_extremo':    lambda d: _es_terreno(d) and _pm2_terreno(d) and _pm2_terreno(d) > 30000,
    'precio_venta_muy_bajo':  lambda d: d['tipo_operacion'] == 'venta' and d.get('precio_mxn') and d['precio_mxn'] < 200000,
    'precio_venta_muy_alto':  lambda d: d['tipo_operacion'] == 'venta' and d.get('precio_mxn') and d['precio_mxn'] > 500_000_000,
    'precio_venta_extremo':   lambda d: d.get('precio_mxn') and d['precio_mxn'] > 1_000_000_000,
    'posible_renta_en_venta': lambda d: d['tipo_operacion'] == 'venta' and d.get('precio_mxn') and d['precio_mxn'] < 50000,
    'colonia_pin_mismatch':   lambda d: _colonia_fuera_de_pin(d),
}

MOTIVOS = {
    'terreno_pm2_muy_bajo':   'pm2 < $500 — posible terreno rural/ejidal',
    'terreno_pm2_muy_alto':   'pm2 > $15,000 — outlier muy alto',
    'terreno_pm2_extremo':    'pm2 > $30,000 — error de captura evidente',
    'precio_venta_muy_bajo':  'precio venta < $200K — posible error',
    'precio_venta_muy_alto':  'precio venta > $500M — posible error captura',
    'precio_venta_extremo':   'precio > $1,000M — error de captura evidente',
    'posible_renta_en_venta': 'precio < $50K catalogado como venta — posible renta',
    'colonia_pin_mismatch':   'pin fuera del polígono de la colonia registrada',
}

# Reglas tan extremas que se desactivan sin necesidad de confirmación IA
REGLAS_AUTO_DESACTIVAR = {'terreno_pm2_extremo', 'precio_venta_extremo'}

def evaluar_reglas(listing):
    violadas = []
    for nombre, regla in REGLAS.items():
        try:
            if regla(listing):
                violadas.append(nombre)
        except Exception:
            pass
    return violadas

def validar_con_ia(listing):
    desc    = listing.get('descripcion', '') or ''
    colonia = listing.get('colonia', '') or ''
    precio  = listing.get('precio_mxn', 0) or 0
    m2      = listing.get('m2_terreno', 0) or 0
    pm2     = _pm2_terreno(listing) or 0
    op      = listing.get('tipo_operacion', '')
    tipo    = listing.get('tipo_inmueble', '')
    fuente  = listing.get('pagina_fuente', '')
    col_implan = _get_colonia_implan(listing.get('lat'), listing.get('lng')) or '(fuera de cobertura)'

    prompt = f"""Analiza este listing inmobiliario de Torreón, Coahuila, México y determina si tiene errores de datos.

DATOS DEL LISTING:
- Tipo: {tipo} en {op}
- Fuente: {fuente}
- Precio total listado: ${precio:,.0f} MXN
- Superficie: {m2:,.0f} m²
- Precio/m²: ${pm2:,.0f} MXN/m²
- Colonia registrada: {colonia}
- Colonia IMPLAN según GPS: {col_implan}
- Descripción: {_sanitizar_para_prompt(desc, 800)}

CONTEXTO MERCADO TORREÓN 2024:
- Terrenos residenciales: $2,000–$12,000/m²
- Terrenos comerciales: $3,000–$15,000/m²
- Terrenos rurales/ejidales: $100–$500/m²
- Casas venta: $800,000–$8,000,000 MXN típico
- Renta mensual casa: $8,000–$25,000 MXN
- Precios en USD frecuentes en portales (1 USD ≈ 17 MXN)

VERIFICA:
1. ¿El precio tiene dígitos de más? (ej: 45645645 en lugar de 4564564)
2. ¿Está en USD pero registrado como MXN sin conversión?
3. ¿Es renta catalogada como venta?
4. ¿La descripción menciona un precio diferente al registrado?
5. ¿La colonia del anuncio coincide con GPS?

Si detectas error de precio, intenta inferir el precio correcto desde la descripción.

Responde SOLO en JSON:
{{"es_error": true/false, "tipo_error": "digitos_extra|precio_usd_sin_convertir|renta_como_venta|colonia_incorrecta|precio_anomalo|ninguno", "motivo": "explicacion breve max 80 chars", "confianza": "alta|media|baja", "precio_corregido": null_o_numero_entero}}"""

    try:
        resp = ai.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=300,
            messages=[{'role': 'user', 'content': prompt}]
        )
        txt = resp.content[0].text.strip()
        m = re.search(r'\{.*\}', txt, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        print(f"    IA error: {e}")
    return {'es_error': False, 'tipo_error': 'ninguno', 'motivo': 'error al consultar IA', 'confianza': 'baja', 'precio_corregido': None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ia', action='store_true', help='Validar con IA los casos dudosos')
    parser.add_argument('--reporte', action='store_true', help='Solo reportar, no modificar DB')
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  DETECTOR DE ANOMALÍAS")
    print(f"  Modo: {'reporte' if args.reporte else 'activo'} | IA: {'sí' if args.ia else 'no'}")
    print(f"{'='*60}\n")

    _cargar_colonias()

    listings, offset = [], 0
    while True:
        res = sb.table('listings')\
            .select('id, tipo_inmueble, tipo_operacion, precio_mxn, m2_terreno, '
                    'precio_x_m2_terreno, colonia, descripcion, link_publicacion, '
                    'pagina_fuente, alerta_precio_anomalo, lat, lng')\
            .eq('activo', True)\
            .limit(1000).offset(offset)\
            .execute()
        batch = res.data or []
        listings.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000

    N, S, E, W = 25.75, 25.40, -103.15, -103.65
    def en_zml(d):
        lat, lng = d.get('lat'), d.get('lng')
        if not lat or not lng:
            return True
        return S < lat < N and W < lng < E
    listings = [d for d in listings if en_zml(d)]
    print(f"  Listings a analizar: {len(listings)}")

    sospechosos = []
    for listing in listings:
        violadas = evaluar_reglas(listing)
        if violadas:
            sospechosos.append({'listing': listing, 'reglas': violadas})

    print(f"  Sospechosos: {len(sospechosos)} | Sin anomalías: {len(listings) - len(sospechosos)}\n")

    from collections import Counter
    conteo = Counter()
    for s in sospechosos:
        for r in s['reglas']:
            conteo[r] += 1
    print("  Resumen por regla:")
    for regla, count in conteo.most_common():
        print(f"    {MOTIVOS[regla]}: {count}")

    confirmados_error = []
    falsos_positivos  = []

    for s in sospechosos:
        listing = s['listing']
        reglas  = s['reglas']
        motivo_auto = ' | '.join(MOTIVOS[r] for r in reglas)
        precio_actual = listing.get('precio_mxn', 0) or 0

        # Outliers tan extremos que se desactivan sin IA
        if any(r in REGLAS_AUTO_DESACTIVAR for r in reglas):
            confirmados_error.append({
                'id': listing['id'], 'motivo': motivo_auto,
                'confianza': 'alta', 'fuente': 'regla_extrema',
                'precio_corregido': None, 'desactivar': True
            })
            print(f"  x EXTREMO [{listing.get('colonia','')}] ${precio_actual:,.0f} — {motivo_auto[:70]}")
            continue

        if 'terreno_pm2_muy_bajo' in reglas:
            confirmados_error.append({
                'id': listing['id'], 'motivo': motivo_auto,
                'confianza': 'alta', 'fuente': 'regla',
                'precio_corregido': None, 'desactivar': True
            })
            print(f"  x AUTO [{listing.get('colonia','')}] ${precio_actual:,.0f} — {motivo_auto[:60]}")
            continue

        if 'colonia_pin_mismatch' in reglas:
            col_implan = _get_colonia_implan(listing.get('lat'), listing.get('lng')) or '?'
            print(f"  ! COLONIA [{listing.get('colonia','')}] -> IMPLAN: [{col_implan}]")

        if args.ia:
            print(f"  ? IA [{listing.get('colonia','')}] ${precio_actual:,.0f}")
            resultado = validar_con_ia(listing)
            time.sleep(0.3)
            precio_corregido = resultado.get('precio_corregido')
            if resultado.get('es_error') and resultado.get('confianza') in ('alta', 'media'):
                confirmados_error.append({
                    'id': listing['id'],
                    'motivo': resultado.get('motivo', motivo_auto),
                    'confianza': resultado.get('confianza', 'media'),
                    'fuente': 'ia',
                    'precio_corregido': precio_corregido,
                    'desactivar': resultado.get('confianza') == 'alta' and not precio_corregido,
                })
                corr_txt = f" → precio corregido: ${precio_corregido:,.0f}" if precio_corregido else ""
                print(f"    → ERROR {resultado.get('confianza','')}: {resultado.get('motivo','')[:60]}{corr_txt}")
            else:
                falsos_positivos.append(listing['id'])
                print(f"    → OK: {resultado.get('motivo','')[:60]}")
        else:
            confirmados_error.append({
                'id': listing['id'], 'motivo': motivo_auto,
                'confianza': 'pendiente_revision', 'fuente': 'regla',
                'precio_corregido': None, 'desactivar': False
            })

    corregidos = [e for e in confirmados_error if e.get('precio_corregido')]
    desactivados = [e for e in confirmados_error if e.get('desactivar')]
    print(f"\n  Errores confirmados: {len(confirmados_error)} | Precios corregidos: {len(corregidos)} | Desactivados: {len(desactivados)} | Falsos positivos: {len(falsos_positivos)}")

    if not args.reporte and confirmados_error:
        print(f"\n  Actualizando DB...")
        for item in confirmados_error:
            update = {'alerta_precio_anomalo': True}
            if item.get('desactivar'):
                update['activo'] = False
            if item.get('precio_corregido'):
                update['precio_mxn'] = item['precio_corregido']
                update['editado_manualmente'] = True
                update['notas_editor'] = f"Precio corregido por auditoria IA ({item['fuente']}): {item['motivo'][:120]}"
                import datetime
                update['fecha_edicion'] = datetime.datetime.utcnow().isoformat()
            sb.table('listings').update(update).eq('id', item['id']).execute()
        for lid in falsos_positivos:
            sb.table('listings').update({'alerta_precio_anomalo': False}).eq('id', lid).execute()

    print(f"\n{'='*60}")
    total_activos = sb.table('listings').select('id', count='exact').eq('activo', True).execute()
    total_alerta  = sb.table('listings').select('id', count='exact').eq('alerta_precio_anomalo', True).execute()
    print(f"  Listings activos: {total_activos.count} | Con alerta: {total_alerta.count}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
