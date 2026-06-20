# -*- coding: utf-8 -*-
"""
Sube a Supabase listings de Instagram YA parseados a mano (workaround cuando la
API de Haiku no tiene creditos). Lee scripts/_ig_parsed.json, geocodifica la
colonia con el GeoJSON IMPLAN y hace upsert via core.db (dedup por link).

    py scripts/ig_upsert_parsed.py --dry-run   # previsualiza
    py scripts/ig_upsert_parsed.py             # guarda
"""
import os, sys, json, argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.instagram import geocode_colonia, _clean_url, _score, upsert_listings_batch

PARSED = os.path.join(os.path.dirname(__file__), "_ig_parsed.json")


def build(p):
    colonia = p.get("colonia")
    lat, lng = geocode_colonia(colonia)
    return {
        "link_publicacion": _clean_url(p["url"]),
        "pagina_fuente": p["fuente"],
        "tipo_operacion": p.get("tipo_operacion"),
        "tipo_inmueble": p.get("tipo_inmueble"),
        "precio_mxn": p.get("precio_mxn"),
        "m2_terreno": p.get("m2_terreno"),
        "m2_construccion": p.get("m2_construccion"),
        "recamaras": p.get("recamaras"),
        "banos": p.get("banos"),
        "colonia": colonia,
        "direccion": p.get("direccion"),
        "descripcion": (p.get("descripcion") or "")[:2000],
        "fecha_publicacion": p.get("fecha"),
        "activo": True,
        "lat": lat, "lng": lng,
        "estado_inmueble": "usado",
        "score_calidad_anuncio": _score(p),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    parsed = json.load(open(PARSED, encoding="utf-8"))
    listings = [build(p) for p in parsed]

    print(f"{len(listings)} listings parseados:\n")
    geo = 0
    for l in listings:
        coords = "geo OK" if l["lat"] else "sin coords"
        if l["lat"]:
            geo += 1
        precio = f"${l['precio_mxn']:,.0f}" if l["precio_mxn"] else "sin precio"
        print(f"  [{l['pagina_fuente'].replace('instagram_','')}] {l['tipo_operacion']}/{l['tipo_inmueble']} "
              f"| {precio} | {l['colonia'] or '(sin colonia)'} | {coords} | score {l['score_calidad_anuncio']}")
    print(f"\nCon coordenadas: {geo}/{len(listings)}")

    if args.dry_run:
        print("\nDRY RUN — no se guardo nada.")
        return
    print("\nGuardando en Supabase...")
    stats = upsert_listings_batch(listings, link_field="link_publicacion")
    print("Resultado:", stats)


if __name__ == "__main__":
    main()
