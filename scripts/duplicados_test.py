# -*- coding: utf-8 -*-
"""Test de core/duplicados (funciones puras, sin DB)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.duplicados import fingerprint, elegir_vigente, detectar_duplicados

# --- fingerprint ---
casa_a = {'colonia': 'Los Ángeles', 'tipo_inmueble': 'casa', 'm2_terreno': 700, 'm2_construccion': 950}
casa_a2 = {'colonia': 'Los Angeles', 'tipo_inmueble': 'Casa', 'm2_terreno': 700.4, 'm2_construccion': 950}
casa_b = {'colonia': 'Los Ángeles', 'tipo_inmueble': 'casa', 'm2_terreno': 700, 'm2_construccion': 951}
terr_a = {'colonia': 'Las Villas', 'tipo_inmueble': 'terreno', 'm2_terreno': 400}
terr_a2 = {'colonia': 'las villas', 'tipo_inmueble': 'terreno', 'm2_terreno': 400}
sin_col = {'colonia': None, 'tipo_inmueble': 'casa', 'm2_construccion': 200}
sin_m2 = {'colonia': 'Centro', 'tipo_inmueble': 'casa'}

assert fingerprint(casa_a) == fingerprint(casa_a2), 'acentos/case/redondeo -> misma huella'
assert fingerprint(casa_a) != fingerprint(casa_b), 'm2 construccion distinto -> distinta'
assert fingerprint(terr_a) == fingerprint(terr_a2), 'terreno misma colonia+m2'
assert fingerprint(sin_col) is None, 'sin colonia -> None'
assert fingerprint(sin_m2) is None, 'casa sin construccion -> None'
print('OK — fingerprint')

# --- elegir_vigente: el mas reciente ---
g = [
    {'id': 1, 'fecha_publicacion': '2026-03-28T00:00:00', 'precio_mxn': 17500000},
    {'id': 2, 'fecha_publicacion': '2026-05-24T00:00:00', 'precio_mxn': 15250000},
    {'id': 3, 'fecha_publicacion': '2026-04-14T00:00:00', 'precio_mxn': 17500000},
]
assert elegir_vigente(g)['id'] == 2, 'gana el mas reciente (mayo)'
print('OK — elegir_vigente')

# --- detectar_duplicados (caso Los Angeles repetido 3 veces + 1 unico) ---
listings = [
    {'id': 1, 'colonia': 'Los Ángeles', 'tipo_inmueble': 'casa', 'm2_terreno': 700, 'm2_construccion': 950,
     'fecha_publicacion': '2026-03-28', 'precio_mxn': 17500000},
    {'id': 2, 'colonia': 'Los Angeles', 'tipo_inmueble': 'casa', 'm2_terreno': 700, 'm2_construccion': 950,
     'fecha_publicacion': '2026-05-24', 'precio_mxn': 15250000},
    {'id': 3, 'colonia': 'Los Ángeles', 'tipo_inmueble': 'casa', 'm2_terreno': 700, 'm2_construccion': 950,
     'fecha_publicacion': '2026-04-14', 'precio_mxn': 17500000},
    {'id': 4, 'colonia': 'Las Trojes', 'tipo_inmueble': 'casa', 'm2_terreno': 245, 'm2_construccion': 337,
     'fecha_publicacion': '2026-06-17', 'precio_mxn': 5300000},
]
dups = detectar_duplicados(listings)
assert len(dups) == 1, 'un grupo duplicado'
vig, obs = dups[0]
assert vig['id'] == 2, 'vigente = el de mayo ($15.25M)'
assert sorted(d['id'] for d in obs) == [1, 3], 'obsoletos = marzo y abril'
print('OK — detectar_duplicados')

print('\nTODO OK — core/duplicados validado')
