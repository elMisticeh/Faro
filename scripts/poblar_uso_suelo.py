# -*- coding: utf-8 -*-
"""
MK3 - Pobla listings.uso_suelo / uso_suelo_cat por point-in-polygon contra la
zonificacion IMPLAN. Correr DESPUES de scripts/mk3_uso_suelo.sql.

    py scripts/poblar_uso_suelo.py

Lee credenciales de .env (SUPABASE_URL, SUPABASE_KEY). No toca filas que no
caen en ninguna zona (quedan NULL). Idempotente: re-correrlo recalcula todo.
"""
import os, json, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEOJSON = os.path.join(ROOT, 'frontend', 'data', 'zonificacion_torreon_slim.geojson')

def load_env():
    env = {}
    with open(os.path.join(ROOT, '.env'), encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k] = v.strip()
    return env

def categoria(s):
    s = (s or '').lower()
    if 'mixto' in s: return 'Mixto'
    if 'corredor' in s: return 'Corredor urbano'
    if 'habitacional' in s or 'ejidal' in s: return 'Habitacional'
    if 'industria' in s: return 'Industrial'
    if any(k in s for k in ['equipamiento', 'administraci', 'asistencia', 'salud',
                            'educac', 'cultural', 'recreac', 'comunicac', 'verdes', 'espacios']):
        return 'Equipamiento'
    if 'servicios' in s: return 'Servicios'
    if 'agr' in s: return 'Agricola'
    if 'conserv' in s: return 'Conservacion'
    return 'Otro'

def pip(lat, lng, ring):
    inside = False; n = len(ring); j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def build_index(gj):
    idx = []
    for f in gj['features']:
        sim = f['properties']['SIMBOLOGIA']
        geom = f['geometry']
        polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        for poly in polys:
            outer = poly[0]
            if not outer or len(outer) < 4:
                continue
            xs = [p[0] for p in outer]; ys = [p[1] for p in outer]
            idx.append((min(xs), min(ys), max(xs), max(ys), outer, poly[1:], sim))
    return idx

def uso_en_punto(idx, lat, lng):
    for (mnx, mny, mxx, mxy, outer, holes, sim) in idx:
        if lng < mnx or lng > mxx or lat < mny or lat > mxy:
            continue
        if pip(lat, lng, outer):
            in_hole = any(pip(lat, lng, h) for h in holes)
            if not in_hole:
                return sim
    return None

def http(method, url, key, body=None):
    data = json.dumps(body).encode('utf-8') if body is not None else None
    headers = {'apikey': key, 'Authorization': 'Bearer ' + key,
               'Content-Type': 'application/json', 'Prefer': 'return=minimal'}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read().decode()

def main():
    env = load_env()
    base = env['SUPABASE_URL'].rstrip('/'); key = env['SUPABASE_KEY']

    print('Cargando zonificacion...', end=' ', flush=True)
    gj = json.load(open(GEOJSON, encoding='utf-8'))
    idx = build_index(gj)
    print('%d poligonos.' % len(idx))

    # Verifica que exista la columna
    try:
        http('GET', base + '/rest/v1/listings?select=uso_suelo&limit=1', key)
    except urllib.error.HTTPError as e:
        if e.code == 400 and 'uso_suelo' in e.read().decode():
            print('\nERROR: la columna uso_suelo no existe. Corre primero scripts/mk3_uso_suelo.sql en Supabase.')
            sys.exit(1)
        raise

    # Trae listings con coordenadas
    print('Trayendo listings...', end=' ', flush=True)
    rows = []; offset = 0
    while True:
        u = (base + '/rest/v1/listings?select=id,lat,lng&lat=not.is.null&lng=not.is.null'
             '&order=id&limit=1000&offset=%d' % offset)
        _, body = http('GET', u, key)
        batch = json.loads(body)
        rows += batch
        if len(batch) < 1000:
            break
        offset += 1000
    print('%d con lat/lng.' % len(rows))

    # Calcula uso de suelo
    grupos = {}; con_zona = 0
    for r in rows:
        try:
            lat = float(r['lat']); lng = float(r['lng'])
        except (TypeError, ValueError):
            continue
        sim = uso_en_punto(idx, lat, lng)
        if not sim:
            continue
        con_zona += 1
        cat = categoria(sim)
        grupos.setdefault((sim, cat), []).append(r['id'])
    print('Con zona: %d / %d (%.0f%%). Categorias distintas: %d'
          % (con_zona, len(rows), 100.0 * con_zona / max(len(rows), 1), len(set(c for _, c in grupos))))

    # Actualiza agrupado por valor, en lotes de ids
    print('Actualizando Supabase...')
    total = 0
    for (sim, cat), ids in grupos.items():
        for i in range(0, len(ids), 150):
            chunk = ids[i:i + 150]
            inlist = '(' + ','.join(str(x) for x in chunk) + ')'
            u = base + '/rest/v1/listings?id=in.' + inlist
            http('PATCH', u, key, {'uso_suelo': sim, 'uso_suelo_cat': cat})
            total += len(chunk)
    print('Listo. %d listings actualizados con uso de suelo.' % total)

    # Resumen por categoria
    print('\nResumen por categoria:')
    porcat = {}
    for (sim, cat), ids in grupos.items():
        porcat[cat] = porcat.get(cat, 0) + len(ids)
    for cat, n in sorted(porcat.items(), key=lambda kv: -kv[1]):
        print('  %-16s %d' % (cat, n))

if __name__ == '__main__':
    main()
