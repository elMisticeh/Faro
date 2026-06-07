"""
db_utils.py — Utilidades de DB que respetan ediciones manuales
==============================================================
Importar en scraper_master.py y cargar_propcom.py:
    from db_utils import upsert_listing, upsert_listings_batch
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
_sb = None

def get_sb():
    global _sb
    if not _sb:
        _sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    return _sb

# Campos que el scraper NUNCA sobreescribe si editado_manualmente = true
CAMPOS_PROTEGIDOS = {
    'colonia', 'lat', 'lng', 'precio_mxn',
    'tipo_inmueble', 'tipo_operacion', 'descripcion',
    'm2_terreno', 'm2_construccion', 'recamaras', 'banos'
}

# Campos que SIEMPRE se actualizan (incluso en listings editados manualmente)
CAMPOS_SIEMPRE = {
    'fecha_ultimo_scrape', 'activo'
}

# Si ubicacion_manual = true, el scraper NO toca estos campos (pero SI actualiza
# precio/descripcion/etc). Editar el pin en el mapa protege solo la ubicacion.
CAMPOS_UBICACION = {'lat', 'lng', 'uso_suelo', 'uso_suelo_clave', 'uso_suelo_cat'}

def upsert_listing(listing: dict, link_field='link_publicacion') -> dict:
    """
    Inserta o actualiza un listing respetando ediciones manuales.
    
    Retorna: {'accion': 'insertado'|'actualizado'|'protegido'|'sin_cambio', 'id': int}
    """
    sb = get_sb()
    link = listing.get(link_field)
    if not link:
        return {'accion': 'error', 'motivo': 'sin link'}

    # Verificar si ya existe
    res = sb.table('listings').select(
        'id, editado_manualmente, ubicacion_manual, fecha_ultimo_scrape, activo'
    ).eq(link_field, link).limit(1).execute()

    ahora = datetime.now().isoformat()

    if not res.data:
        # --- NUEVO: insertar completo ---
        payload = {**listing, 'fecha_primer_scrape': ahora, 'fecha_ultimo_scrape': ahora}
        # Quitar columnas generadas automáticamente
        for col in ['precio_x_m2_terreno', 'precio_x_m2_construccion']:
            payload.pop(col, None)
        sb.table('listings').insert(payload).execute()
        return {'accion': 'insertado'}

    existente = res.data[0]
    id_existente = existente['id']

    if existente.get('editado_manualmente'):
        # --- PROTEGIDO: solo actualizar timestamp y activo ---
        sb.table('listings').update({
            'fecha_ultimo_scrape': ahora,
            'activo': listing.get('activo', True),
        }).eq('id', id_existente).execute()
        return {'accion': 'protegido', 'id': id_existente}

    # --- ACTUALIZAR: todos los campos excepto los generados ---
    payload = {**listing, 'fecha_ultimo_scrape': ahora}
    for col in ['precio_x_m2_terreno', 'precio_x_m2_construccion',
                'fecha_primer_scrape', 'editado_manualmente',
                'notas_editor', 'fecha_edicion']:
        payload.pop(col, None)

    # Ubicacion protegida: si el pin fue editado en el mapa, no mover lat/lng ni uso de suelo
    if existente.get('ubicacion_manual'):
        for col in CAMPOS_UBICACION:
            payload.pop(col, None)

    sb.table('listings').update(payload).eq('id', id_existente).execute()
    return {'accion': 'actualizado', 'id': id_existente}


def upsert_listings_batch(listings: list, link_field='link_publicacion') -> dict:
    """
    Procesa una lista de listings eficientemente.
    Primero verifica cuáles existen y cuáles están protegidos.
    
    Retorna stats: {'insertados': N, 'actualizados': N, 'protegidos': N}
    """
    sb = get_sb()
    if not listings:
        return {'insertados': 0, 'actualizados': 0, 'protegidos': 0}

    stats = {'insertados': 0, 'actualizados': 0, 'protegidos': 0}
    ahora = datetime.now().isoformat()

    # Obtener estado actual de todos los links en lote
    links = [l[link_field] for l in listings if l.get(link_field)]
    existentes = {}  # link → {id, editado_manualmente}

    for i in range(0, len(links), 50):
        res = sb.table('listings').select(
            f'id, {link_field}, editado_manualmente, ubicacion_manual'
        ).in_(link_field, links[i:i+50]).execute()
        for row in (res.data or []):
            existentes[row[link_field]] = row

    # Separar en grupos
    a_insertar = []
    a_actualizar = []
    a_proteger = []

    for listing in listings:
        link = listing.get(link_field)
        if not link:
            continue
        if link not in existentes:
            a_insertar.append(listing)
        elif existentes[link].get('editado_manualmente'):
            a_proteger.append(existentes[link]['id'])
        else:
            a_actualizar.append((existentes[link]['id'], listing, existentes[link].get('ubicacion_manual')))

    # --- Insertar nuevos en lote ---
    if a_insertar:
        lote = []
        for listing in a_insertar:
            p = {**listing, 'fecha_primer_scrape': ahora, 'fecha_ultimo_scrape': ahora}
            for col in ['precio_x_m2_terreno', 'precio_x_m2_construccion']:
                p.pop(col, None)
            lote.append(p)
        for i in range(0, len(lote), 50):
            sb.table('listings').insert(lote[i:i+50]).execute()
        stats['insertados'] = len(a_insertar)

    # --- Actualizar existentes en lote (de a uno por limitación de Supabase) ---
    for (id_ex, listing, ubic_man) in a_actualizar:
        payload = {**listing, 'fecha_ultimo_scrape': ahora}
        for col in ['precio_x_m2_terreno', 'precio_x_m2_construccion',
                    'fecha_primer_scrape', 'editado_manualmente',
                    'notas_editor', 'fecha_edicion']:
            payload.pop(col, None)
        if ubic_man:
            for col in CAMPOS_UBICACION:
                payload.pop(col, None)
        sb.table('listings').update(payload).eq('id', id_ex).execute()
    stats['actualizados'] = len(a_actualizar)

    # --- Solo timestamp para protegidos ---
    if a_proteger:
        for i in range(0, len(a_proteger), 50):
            sb.table('listings').update({
                'fecha_ultimo_scrape': ahora,
                'activo': True,
            }).in_('id', a_proteger[i:i+50]).execute()
    stats['protegidos'] = len(a_proteger)

    return stats


def editar_listing(id_listing: int, cambios: dict, nota: str = '') -> bool:
    """
    Edita manualmente un listing y lo marca como protegido.
    Usar desde scripts de corrección manual.
    
    Ejemplo:
        editar_listing(1234, {'colonia': 'Torreón Jardín', 'lat': 25.548, 'lng': -103.412},
                       nota='Colonia corregida manualmente — estaba mal catalogada')
    """
    sb = get_sb()
    cambios_seguros = {k: v for k, v in cambios.items()
                       if k not in ['precio_x_m2_terreno', 'precio_x_m2_construccion',
                                    'fecha_primer_scrape', 'id']}
    cambios_seguros.update({
        'editado_manualmente': True,
        'notas_editor': nota[:500] if nota else '',
        'fecha_edicion': datetime.now().isoformat(),
    })
    res = sb.table('listings').update(cambios_seguros).eq('id', id_listing).execute()
    return bool(res.data)


def listar_editados() -> list:
    """Retorna todos los listings editados manualmente."""
    sb = get_sb()
    res = sb.table('listings').select(
        'id, colonia, tipo_inmueble, tipo_operacion, precio_mxn, '
        'notas_editor, fecha_edicion, link_publicacion'
    ).eq('editado_manualmente', True).order('fecha_edicion', desc=True).execute()
    return res.data or []


if __name__ == '__main__':
    # Demo: listar editados
    editados = listar_editados()
    if editados:
        print(f"\nListings editados manualmente: {len(editados)}")
        for e in editados:
            print(f"  #{e['id']} {e['colonia']} | {e['tipo_inmueble']} | "
                  f"${e['precio_mxn']:,.0f}" if e.get('precio_mxn') else f"  #{e['id']}")
            if e.get('notas_editor'):
                print(f"    → {e['notas_editor']}")
    else:
        print("No hay listings editados manualmente aún.")
        print("\nEjemplo de uso:")
        print("  from db_utils import editar_listing")
        print("  editar_listing(1234, {'colonia': 'Torreón Jardín'}, 'Corregido manualmente')")
