# -*- coding: utf-8 -*-
"""
core/duplicados.py — Deteccion de duplicados por PROPIEDAD (no por URL).

Un agente puede republicar la MISMA propiedad con shortcodes distintos (a veces
bajando el precio). El dedup por link no los detecta. Aqui la huella es la
propiedad fisica: colonia + tipo + m2 terreno + m2 construccion. Dentro de un
grupo con misma huella se conserva el anuncio MAS RECIENTE (precio vigente) y
los demas se marcan activo=false con nota (no se borran; se respeta edicion
manual).

Funciones puras (fingerprint, elegir_vigente, detectar_duplicados) testeables
en aislamiento; marcar_duplicados_db hace el I/O contra Supabase.
"""
import re
import unicodedata


def _norm(s):
    s = unicodedata.normalize('NFKD', (s or '').lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def fingerprint(d):
    """Huella de propiedad o None si no hay datos suficientes para deduplicar.

    - Requiere colonia + tipo_inmueble.
    - terreno: colonia + m2_terreno (redondeado).
    - casa/depto/otros: colonia + m2_construccion (terreno opcional).
    Si falta el m2 clave, devuelve None (no se arriesga un merge ciego)."""
    col = _norm(d.get('colonia'))
    tipo = (d.get('tipo_inmueble') or '').strip().lower()
    if not col or not tipo:
        return None
    t = d.get('m2_terreno')
    c = d.get('m2_construccion')
    try:
        t = round(float(t)) if t else None
        c = round(float(c)) if c else None
    except (TypeError, ValueError):
        return None
    if tipo == 'terreno':
        if not t:
            return None
        return f'terreno|{col}|t{t}'
    if not c:
        return None
    return f'{tipo}|{col}|t{t if t else "-"}|c{c}'


def _fecha(d):
    return (d.get('fecha_publicacion') or d.get('fecha_primer_scrape') or '')


def elegir_vigente(grupo):
    """El anuncio mas reciente del grupo (precio actual). Desempata por id mayor."""
    return max(grupo, key=lambda d: (_fecha(d), d.get('id') or 0))


def detectar_duplicados(listings):
    """Agrupa por huella; retorna [(vigente, [obsoletos])] para grupos con >1.
    Listings sin huella (datos incompletos) nunca se marcan duplicados."""
    grupos = {}
    for d in listings:
        fp = fingerprint(d)
        if fp:
            grupos.setdefault(fp, []).append(d)
    out = []
    for fp, g in grupos.items():
        if len(g) > 1:
            vig = elegir_vigente(g)
            obs = [d for d in g if d is not vig]
            out.append((vig, obs))
    return out


# ---------------------------------------------------------------------------
# Pase contra Supabase
# ---------------------------------------------------------------------------

def marcar_duplicados_db(fuente_prefix='instagram', dry_run=False):
    """Recorre los listings activos cuya pagina_fuente empieza con fuente_prefix,
    agrupa por huella de propiedad y desactiva los duplicados mas viejos.

    Respeta editado_manualmente (no toca anuncios editados a mano).
    Retorna stats. fuente_prefix='' procesa TODA la tabla."""
    from core.db import get_sb
    sb = get_sb()

    cols = ('id, link_publicacion, pagina_fuente, colonia, tipo_inmueble, '
            'm2_terreno, m2_construccion, precio_mxn, fecha_publicacion, '
            'fecha_primer_scrape, editado_manualmente, activo')
    q = sb.table('listings').select(cols).eq('activo', True)
    if fuente_prefix:
        q = q.like('pagina_fuente', f'{fuente_prefix}%')
    rows = q.execute().data or []

    grupos = detectar_duplicados(rows)
    stats = {'activos': len(rows), 'grupos_dup': len(grupos),
             'desactivados': 0, 'protegidos': 0, 'detalle': []}

    for vig, obs in grupos:
        for d in obs:
            if d.get('editado_manualmente'):
                stats['protegidos'] += 1
                continue
            nota = (f"Duplicado de propiedad (misma colonia+m2); vigente: "
                    f"{vig.get('link_publicacion')}")
            stats['detalle'].append({
                'desactivado': d.get('link_publicacion'),
                'precio': d.get('precio_mxn'),
                'vigente': vig.get('link_publicacion'),
                'precio_vigente': vig.get('precio_mxn'),
                'colonia': d.get('colonia'),
            })
            if not dry_run:
                sb.table('listings').update({
                    'activo': False,
                    'notas_editor': nota,
                }).eq('id', d['id']).execute()
            stats['desactivados'] += 1

    return stats


if __name__ == '__main__':
    import sys, json
    sys.path.insert(0, __file__.rsplit('core', 1)[0])
    dry = '--dry-run' in sys.argv
    pref = 'instagram'
    for a in sys.argv[1:]:
        if a.startswith('--fuente='):
            pref = a.split('=', 1)[1]
    st = marcar_duplicados_db(pref, dry_run=dry)
    print(json.dumps({k: v for k, v in st.items() if k != 'detalle'}, ensure_ascii=False))
    for d in st['detalle']:
        print(f"  - {d['colonia']}: {d['desactivado']} (${d['precio']}) -> vigente "
              f"{d['vigente']} (${d['precio_vigente']})")
