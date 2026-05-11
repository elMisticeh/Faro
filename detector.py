"""
detector.py — Detector de oportunidades inmobiliarias
Compara precio/m² de cada listing contra el promedio de su colonia.

Uso:
    py detector.py                    # terrenos por defecto
    py detector.py --tipo casa
    py detector.py --umbral 0.20
"""

import argparse
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

DEFAULTS = {
    "tipo_inmueble":        "terreno",
    "tipo_operacion":       "venta",
    "umbral":               0.15,
    "min_listings_colonia": 3,
}

def calcular_promedios_colonia(tipo_inmueble: str, tipo_operacion: str) -> dict:
    """
    Calcula precio/m² mediana por colonia.
    Usa precio_x_m2_terreno (columna generada en Supabase).
    """
    print(f"\n  Calculando promedios por colonia ({tipo_inmueble} en {tipo_operacion})...")

    # precio_x_m2_terreno es la columna generada: precio_mxn / m2_terreno
    res = supabase.table("listings").select(
        "colonia, precio_x_m2_terreno, precio_x_m2_construccion"
    ).eq("tipo_inmueble", tipo_inmueble)\
     .eq("tipo_operacion", tipo_operacion)\
     .eq("activo", True)\
     .execute()

    if not res.data:
        print("  Sin datos.")
        return {}

    por_colonia = {}
    for row in res.data:
        colonia = (row.get("colonia") or "").strip()
        # Usar construccion si existe, sino terreno
        pm2 = row.get("precio_x_m2_construccion") or row.get("precio_x_m2_terreno")
        if colonia and pm2 and float(pm2) > 0:
            por_colonia.setdefault(colonia, []).append(float(pm2))

    stats = {}
    for colonia, valores in por_colonia.items():
        if len(valores) < DEFAULTS["min_listings_colonia"]:
            continue
        valores_sorted = sorted(valores)
        n = len(valores_sorted)
        stats[colonia] = {
            "pm2_mediana": valores_sorted[n // 2],
            "pm2_promedio": sum(valores) / n,
            "total": n,
        }

    print(f"  Colonias con datos (>={DEFAULTS['min_listings_colonia']} listings): {len(stats)}")
    return stats


def detectar_oportunidades(tipo_inmueble: str, tipo_operacion: str, umbral: float) -> list:
    stats_colonia = calcular_promedios_colonia(tipo_inmueble, tipo_operacion)
    if not stats_colonia:
        return []

    res = supabase.table("listings").select(
        "id, colonia, precio_mxn, precio_x_m2_terreno, precio_x_m2_construccion, link_publicacion, descripcion, m2_terreno"
    ).eq("tipo_inmueble", tipo_inmueble)\
     .eq("tipo_operacion", tipo_operacion)\
     .eq("activo", True)\
     .execute()

    listings = res.data or []
    print(f"\n  Analizando {len(listings)} listings...")

    oportunidades = []
    actualizados = 0

    for listing in listings:
        colonia = (listing.get("colonia") or "").strip()
        pm2 = (listing.get("precio_x_m2_construccion") or
               listing.get("precio_x_m2_terreno"))

        if not pm2 or colonia not in stats_colonia:
            supabase.table("listings").update({
                "es_oportunidad": False,
                "pct_vs_colonia": None,
                "pm2_promedio_colonia": None,
            }).eq("id", listing["id"]).execute()
            continue

        pm2 = float(pm2)
        pm2_ref = stats_colonia[colonia]["pm2_mediana"]
        pct_diff = round(((pm2 - pm2_ref) / pm2_ref) * 100, 1)
        es_oportunidad = pct_diff <= -(umbral * 100)

        supabase.table("listings").update({
            "es_oportunidad":        es_oportunidad,
            "pct_vs_colonia":        pct_diff,
            "pm2_promedio_colonia":  round(pm2_ref, 0),
        }).eq("id", listing["id"]).execute()
        actualizados += 1

        if es_oportunidad:
            oportunidades.append({**listing, "pct_vs_colonia": pct_diff,
                                   "pm2_promedio_colonia": round(pm2_ref, 0)})

    print(f"  Actualizados: {actualizados}")
    return sorted(oportunidades, key=lambda x: x["pct_vs_colonia"])


def imprimir_reporte(oportunidades: list, tipo_inmueble: str, umbral: float):
    print(f"\n{'='*65}")
    print(f"  OPORTUNIDADES — {tipo_inmueble.upper()} EN VENTA")
    print(f"  Umbral: {umbral*100:.0f}% bajo la mediana de la colonia")
    print(f"  Total: {len(oportunidades)}")
    print(f"{'='*65}\n")

    if not oportunidades:
        print("  Sin oportunidades. Necesitas más datos — corre scraper_master.py primero.\n")
        return

    for i, op in enumerate(oportunidades[:20], 1):
        precio = op.get("precio_mxn")
        pm2    = op.get("precio_x_m2_construccion") or op.get("precio_x_m2_terreno")
        pm2_c  = op.get("pm2_promedio_colonia")
        pct    = op.get("pct_vs_colonia")
        m2     = op.get("m2_terreno")
        link   = op.get("link_publicacion", "")
        desc   = (op.get("descripcion") or "")[:60]

        print(f"  #{i:02d} {'🟢' if pct < -25 else '🟡'} {op['colonia']}")
        if precio: print(f"       Precio:  ${precio:>12,.0f}")
        if pm2 and pm2_c: print(f"       $/m²:    ${float(pm2):>10,.0f}  vs colonia ${pm2_c:,.0f}  ({pct:+.1f}%)")
        if m2:    print(f"       Terreno: {m2:,.0f} m²")
        print(f"       {desc}...")
        print(f"       {link}\n")

    if len(oportunidades) > 20:
        print(f"  ... y {len(oportunidades)-20} más en el dashboard.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tipo",      default=DEFAULTS["tipo_inmueble"])
    parser.add_argument("--operacion", default=DEFAULTS["tipo_operacion"])
    parser.add_argument("--umbral",    default=DEFAULTS["umbral"], type=float)
    args = parser.parse_args()

    print(f"\n{'='*65}")
    print(f"  DETECTOR DE OPORTUNIDADES — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Segmento: {args.tipo} en {args.operacion} | Umbral: {args.umbral*100:.0f}%")
    print(f"{'='*65}")

    oportunidades = detectar_oportunidades(args.tipo, args.operacion, args.umbral)
    imprimir_reporte(oportunidades, args.tipo, args.umbral)

    total = supabase.table("listings").select("id", count="exact")\
        .eq("es_oportunidad", True).eq("activo", True).execute()
    print(f"  Total oportunidades activas en DB: {total.count}\n")


if __name__ == "__main__":
    main()
