"""
historico.py — Módulo de detección de cambios entre scrapes
============================================================
Compara el estado actual de la DB contra lo que acaba de scrapearse
y detecta: nuevos, bajados, cambios de precio, sin cambio.

Uso standalone:
    py historico.py --fuente propiedades_com
    py historico.py --fuente inmuebles24
    py historico.py --fuente todas

Se integra automáticamente al scheduler.py
"""

import os, json, argparse
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def log(msg, nivel='INFO'):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    icons = {'INFO':'  ','OK':'✓ ','ERR':'✗ ','WARN':'⚠ ','HEAD':'══'}
    print(f"[{ts}] {icons.get(nivel,'  ')}{msg}")

# ── Traer listings de DB ──────────────────────────────────────────────────────
def fetch_listings_db(fuente=None):
    """Trae todos los listings activos (o de una fuente específica)."""
    all_data = []
    offset = 0
    while True:
        q = sb.table('listings')\
            .select('id, link_publicacion, precio_mxn, activo, '
                    'fecha_primer_scrape, fecha_ultimo_scrape, '
                    'historial_precio, scrape_id, colonia, '
                    'tipo_inmueble, tipo_operacion, pagina_fuente')\
            .limit(1000).offset(offset)
        if fuente and fuente != 'todas':
            q = q.eq('pagina_fuente', fuente)
        res = q.execute()
        batch = res.data or []
        all_data.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return all_data

# ── Crear sesión de scrape ────────────────────────────────────────────────────
def crear_sesion(fuente):
    res = sb.table('scrape_sessions').insert({
        'fecha': datetime.now().isoformat(),
        'fuente': fuente,
    }).execute()
    sesion_id = res.data[0]['id']
    log(f"Sesión #{sesion_id} creada para {fuente}")
    return sesion_id

def actualizar_sesion(sesion_id, activos, nuevos, bajados, precio_cambio, notas=''):
    sb.table('scrape_sessions').update({
        'listings_activos':      activos,
        'listings_nuevos':       nuevos,
        'listings_bajados':      bajados,
        'listings_precio_cambio':precio_cambio,
        'notas':                 notas[:500],
    }).eq('id', sesion_id).execute()

# ── Detección de cambios ──────────────────────────────────────────────────────
def detectar_cambios(fuente='todas'):
    """
    Compara listings actuales con lo que había antes y registra cambios.
    
    Lógica:
    - Listings vistos en este scrape → fecha_ultimo_scrape = ahora, scrape_id = sesion actual
    - Listings NO vistos en N días   → marcar activo=false, fecha_baja = ahora
    - Precio cambió                  → guardar en historial_precio
    """
    log(f"DETECCIÓN DE CAMBIOS — fuente: {fuente}", 'HEAD')
    
    sesion_id = crear_sesion(fuente)
    ahora = datetime.now()
    
    # Traer todos los listings de esta fuente
    listings = fetch_listings_db(fuente)
    log(f"  Listings en DB: {len(listings)}")

    # Separar activos e inactivos
    activos   = [l for l in listings if l['activo']]
    inactivos = [l for l in listings if not l['activo']]

    # ── Detectar bajados ──────────────────────────────────────────────────────
    # Un listing se considera "bajado" si no fue visto en el scrape actual
    # Lo identificamos porque su fecha_ultimo_scrape NO se actualizó hoy
    hoy = ahora.date().isoformat()
    
    bajados = []
    for l in activos:
        ultimo = (l.get('fecha_ultimo_scrape') or '')[:10]
        # Si no fue actualizado hoy Y lleva más de 3 días sin verse → bajado
        if ultimo < hoy:
            from datetime import timedelta
            try:
                fecha_ult = datetime.fromisoformat(l['fecha_ultimo_scrape'].replace('Z',''))
                dias_sin_ver = (ahora - fecha_ult).days
                if dias_sin_ver >= 3:
                    bajados.append(l)
            except:
                pass

    log(f"  Activos: {len(activos)} | Bajados detectados: {len(bajados)}")

    # Marcar bajados
    if bajados:
        ids_bajados = [l['id'] for l in bajados]
        for i in range(0, len(ids_bajados), 50):
            sb.table('listings').update({
                'activo':     False,
                'fecha_baja': ahora.isoformat(),
                'scrape_id':  sesion_id,
            }).in_('id', ids_bajados[i:i+50]).execute()
        log(f"  Marcados como bajados: {len(bajados)}", 'WARN')

        # Log detalle de bajados
        for l in bajados[:5]:
            log(f"    ↓ {l['colonia']} | {l['tipo_inmueble']} | "
                f"${l['precio_mxn']:,.0f}" if l['precio_mxn'] else f"    ↓ {l['colonia']}")

    # ── Detectar cambios de precio ────────────────────────────────────────────
    # Los listings que sí fueron vistos hoy — comparar precio anterior
    vistos_hoy = [l for l in activos if (l.get('fecha_ultimo_scrape') or '')[:10] == hoy]
    
    precio_cambios = 0
    for l in vistos_hoy:
        historial = l.get('historial_precio')
        if isinstance(historial, str):
            try: historial = json.loads(historial)
            except: historial = []
        historial = historial or []

        precio_actual = l.get('precio_mxn')
        if not precio_actual:
            continue

        # Comparar con último precio registrado
        if historial:
            ultimo_precio = historial[-1].get('precio')
            if ultimo_precio and abs(precio_actual - ultimo_precio) / ultimo_precio > 0.01:
                # Cambio mayor al 1% — registrar
                cambio_pct = round((precio_actual - ultimo_precio) / ultimo_precio * 100, 1)
                historial.append({
                    'fecha':     ahora.isoformat()[:10],
                    'precio':    precio_actual,
                    'cambio_pct': cambio_pct,
                    'scrape_id': sesion_id,
                })
                sb.table('listings').update({
                    'historial_precio': json.dumps(historial),
                    'scrape_id': sesion_id,
                }).eq('id', l['id']).execute()
                precio_cambios += 1
                signo = '↑' if cambio_pct > 0 else '↓'
                log(f"  {signo} Precio: {l['colonia']} | "
                    f"${ultimo_precio:,.0f} → ${precio_actual:,.0f} ({cambio_pct:+.1f}%)")
        else:
            # Primera vez que lo vemos — inicializar historial
            historial = [{
                'fecha':     (l.get('fecha_primer_scrape') or ahora.isoformat())[:10],
                'precio':    precio_actual,
                'cambio_pct': 0,
                'scrape_id': sesion_id,
            }]
            sb.table('listings').update({
                'historial_precio': json.dumps(historial),
                'scrape_id': sesion_id,
            }).eq('id', l['id']).execute()

    # ── Detectar nuevos (vistos hoy, sin historial previo) ────────────────────
    nuevos = [l for l in vistos_hoy
              if not l.get('historial_precio') or l.get('historial_precio') == '[]']

    log(f"  Nuevos hoy: {len(nuevos)} | Cambios precio: {precio_cambios}", 'OK')

    # ── Actualizar sesión con resumen ─────────────────────────────────────────
    activos_final = sb.table('listings').select('id', count='exact')\
        .eq('activo', True).execute()

    actualizar_sesion(
        sesion_id,
        activos    = activos_final.count,
        nuevos     = len(nuevos),
        bajados    = len(bajados),
        precio_cambio = precio_cambios,
        notas      = f"Fuente: {fuente} | Vistos hoy: {len(vistos_hoy)}"
    )

    # ── Reporte ───────────────────────────────────────────────────────────────
    print(f"\n  {'─'*50}")
    print(f"  RESUMEN SESIÓN #{sesion_id}")
    print(f"  {'─'*50}")
    print(f"  Activos en DB:     {activos_final.count:,}")
    print(f"  Nuevos:            {len(nuevos):,}  ← entraron al mercado")
    print(f"  Bajados:           {len(bajados):,}  ← salieron del mercado")
    print(f"  Cambios de precio: {precio_cambios:,}")
    print(f"  Sin cambio:        {len(vistos_hoy)-len(nuevos)-precio_cambios:,}")
    print(f"  {'─'*50}\n")

    return {
        'sesion_id':    sesion_id,
        'activos':      activos_final.count,
        'nuevos':       len(nuevos),
        'bajados':      len(bajados),
        'precio_cambio':precio_cambios,
    }

# ── Historial de sesiones ─────────────────────────────────────────────────────
def ver_historial(n=10):
    """Muestra las últimas N sesiones de scrape."""
    res = sb.table('scrape_sessions')\
        .select('*')\
        .order('fecha', desc=True)\
        .limit(n)\
        .execute()

    print(f"\n  {'─'*65}")
    print(f"  {'FECHA':<22} {'FUENTE':<20} {'ACT':>6} {'NEW':>5} {'BAJ':>5} {'PRC':>5}")
    print(f"  {'─'*65}")
    for s in (res.data or []):
        fecha = s.get('fecha','')[:16].replace('T',' ')
        print(f"  {fecha:<22} {s.get('fuente',''):<20} "
              f"{s.get('listings_activos',0):>6,} "
              f"{s.get('listings_nuevos',0):>5,} "
              f"{s.get('listings_bajados',0):>5,} "
              f"{s.get('listings_precio_cambio',0):>5,}")
    print(f"  {'─'*65}\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fuente', default='todas',
                        choices=['todas','propiedades_com','inmuebles24'])
    parser.add_argument('--historial', action='store_true',
                        help='Ver historial de sesiones')
    parser.add_argument('--n', type=int, default=10,
                        help='Número de sesiones a mostrar')
    args = parser.parse_args()

    if args.historial:
        ver_historial(args.n)
    else:
        detectar_cambios(args.fuente)
