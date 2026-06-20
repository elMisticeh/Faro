# -*- coding: utf-8 -*-
"""Anclas del costo de obra proporcional. Lee las colonias Residencial Plus +
Residencial de la Guia PMX (Torreon) con su valor de terreno (punto medio),
recorta outliers por IQR y deja LAND_LO/LAND_HI -> [14000, 19000].
Datos leidos visualmente del PDF (pag.1, clases Torreon)."""
import json, statistics, os

OBRA_LO, OBRA_HI = 14000, 19000

# (clase, colonia, pm2_terreno_min, pm2_terreno_max) — Guia PMX ene-mar 2026, Torreon
TOP2 = [
    ("R+","Cumbres",8500,11000),("R+","Granjas San Isidro",6900,8500),
    ("R+","Hacienda Del Rosario",4900,5900),("R+","La Barranca",4500,6000),
    ("R+","La Rua",5600,7000),("R+","La Vinicola Residencial",9500,11500),
    ("R+","Las Acacias",8100,8500),("R+","Las Trojes",4100,5000),
    ("R+","Las Villas",8500,10000),("R+","Las Villas del Cardenchal",6900,8150),
    ("R+","Los Angeles",6000,8000),("R+","Los Azulejos",1000,2800),
    ("R+","Montebello",4000,5500),("R+","Real Del Nogalar",4650,5500),
    ("R+","Residencial Campestre La Rosita",6500,12000),("R+","Residencial El Fresno",6800,8500),
    ("R+","Residencial Galerias",8500,9000),("R+","Residencial Las Isabeles",6000,7150),
    ("R+","Residencial Los Fresnos",7000,8000),("R+","Rincon San Angel",5000,5500),
    ("R+","San Isidro",6000,8500),("R+","San Luciano",6000,7000),
    ("R+","Torreon Jardin",7000,8000),
    ("R","Almeras Residencial",4500,5950),("R","Ampliacion Los Angeles",4600,6000),
    ("R","Estrella",5000,6000),("R","Hacienda San Jose",5800,6300),
    ("R","Las Margaritas",4600,6000),("R","Las Quintas",4100,5500),
    ("R","Las Vinas",5500,6000),("R","Los Vinedos",5500,6000),
    ("R","Navarro",5000,6000),("R","Nueva Los Angeles",4600,6000),
    ("R","Quintas San Isidro",4800,5350),("R","San Armando",2900,3550),
    ("R","Santa Barbara",4500,5000),("R","Villas de la Ibero",4200,4500),
]

rows = [{"clase": c, "colonia": col, "pm2_min": lo, "pm2_max": hi,
         "pm2_mid": (lo + hi) / 2} for (c, col, lo, hi) in TOP2]
mids = sorted(r["pm2_mid"] for r in rows)

# Recorte de outliers por percentil P10-P90 (IQR no marcaba Los Azulejos por
# la distribucion ancha). P10/P90 saca las colas de ambos lados.
deciles = statistics.quantiles(mids, n=10)  # 9 cortes P10..P90
LAND_LO = round(deciles[0])   # P10 -> $14k
LAND_HI = round(deciles[8])   # P90 -> $19k
outliers = [round(m) for m in mids if m < LAND_LO or m > LAND_HI]

def costo(pm2):
    if pm2 <= LAND_LO: return OBRA_LO
    if pm2 >= LAND_HI: return OBRA_HI
    return round(OBRA_LO + (pm2 - LAND_LO) / (LAND_HI - LAND_LO) * (OBRA_HI - OBRA_LO))

print(f"Colonias top-2: {len(rows)} | recorte P10-P90")
print(f"Fuera de [P10,P90] (clamp a 14k/19k): {outliers}")
print(f"ANCLAS -> LAND_LO=${LAND_LO:,.0f} (->$14k)  LAND_HI=${LAND_HI:,.0f} (->$19k)\n")
for r in sorted(rows, key=lambda x: x["pm2_mid"]):
    print(f"  {r['colonia'][:30]:30} terreno ${r['pm2_mid']:>7,.0f} -> obra ${costo(r['pm2_mid']):>6,.0f}")

os.makedirs("data", exist_ok=True)
json.dump({"fuente": "Guia PMX Laguna ene-mar 2026 (Torreon, clases R+ y R)",
           "OBRA_LO": OBRA_LO, "OBRA_HI": OBRA_HI,
           "LAND_LO": LAND_LO, "LAND_HI": LAND_HI, "colonias": rows},
          open("data/guia_clases_torreon.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\n-> data/guia_clases_torreon.json")
