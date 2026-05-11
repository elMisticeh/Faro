"""
scraper_master.py — Orquestador multi-portal
============================================
Corre todos los scrapers en secuencia, con reintentos y reporte final.

Uso:
    py scraper_master.py                    # todos los portales
    py scraper_master.py --portal i24       # solo inmuebles24
    py scraper_master.py --portal ml        # solo mercado libre (API)
    py scraper_master.py --max-pags 5       # limitar páginas por portal
    py scraper_master.py --skip-ia          # sin enriquecimiento IA (más rápido)

Al terminar corre automáticamente el detector de oportunidades.
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from supabase import create_client

# Agregar directorio al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# ─── Importar módulos de scrapers ─────────────────────────────────────────────
from scrapers import inmuebles24, vivanuncios, lamudi, icasas
from scrapers import metroscubicos, propiedades, trovit
from scrapers import mercadolibre

# ─── Configuración global ─────────────────────────────────────────────────────

MAX_PAGINAS_DEFAULT = 15  # ~420 listings por URL por portal

PORTALES_PLAYWRIGHT = [
    # (módulo, alias_corto)
    (inmuebles24,   "i24"),
    (vivanuncios,   "viva"),
    (lamudi,        "lamudi"),
    (icasas,        "icasas"),
    (metroscubicos, "mc"),
    (propiedades,   "prop"),
    (trovit,        "trovit"),
]

# ─── Runner genérico Playwright ───────────────────────────────────────────────

async def correr_portal_playwright(modulo, max_pags: int) -> dict:
    """
    Corre un scraper basado en Playwright.
    Reinicia contexto entre URLs para evitar detección anti-bot.
    """
    stats_total = {"nuevo": 0, "actualizado": 0, "error": 0, "paginas": 0, "urls": 0}

    for entry in modulo.URLS:
        url, tipo_op = entry[0], entry[1]
        print(f"\n  URL: {url.split('/')[-1]}")

        # Contexto fresco por URL — evita que i24 detecte sesión larga
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                locale="es-MX",
            )
            page = await context.new_page()
            try:
                stats = await modulo.scrapear_pagina(page, url, tipo_op, max_pags)
                for k, v in stats.items():
                    stats_total[k] = stats_total.get(k, 0) + v
                stats_total["urls"] += 1
                print(f"    → nuevo:{stats.get('nuevo',0)} act:{stats.get('actualizado',0)} err:{stats.get('error',0)}")
            except Exception as e:
                print(f"  ✗ Error en URL: {e}")
            finally:
                await browser.close()

        # Pausa entre URLs para no levantar flags anti-bot
        await asyncio.sleep(3)

    return stats_total

# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Scraper multi-portal Torreón RE")
    parser.add_argument("--portal",   default="todos", help="Portal a scrapear: todos|i24|viva|lamudi|icasas|mc|prop|trovit|ml|remax")
    parser.add_argument("--max-pags", default=MAX_PAGINAS_DEFAULT, type=int, help="Máximo de páginas por URL")
    parser.add_argument("--skip-detector", action="store_true", help="No correr detector al terminar")
    args = parser.parse_args()

    inicio = datetime.now()
    print(f"\n{'='*65}")
    print(f"  SCRAPER MULTI-PORTAL — TORREÓN REAL ESTATE")
    print(f"  {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Portal: {args.portal} | Máx páginas: {args.max_pags}")
    print(f"{'='*65}")

    resumen = {}

    # ── Portales Playwright ─────────────────────────────────────────────────
    for modulo, alias in PORTALES_PLAYWRIGHT:
        if args.portal not in ("todos", alias):
            continue

        print(f"\n{'─'*65}")
        print(f"  [{alias.upper()}] {modulo.NOMBRE}")
        print(f"{'─'*65}")

        try:
            stats = await correr_portal_playwright(modulo, args.max_pags)
            resumen[alias] = stats
            print(f"\n  [{alias.upper()}] Completado — "
                  f"nuevo:{stats['nuevo']} act:{stats['actualizado']} "
                  f"err:{stats['error']} págs:{stats['paginas']}")
        except Exception as e:
            print(f"\n  [{alias.upper()}] ERROR FATAL: {e}")
            resumen[alias] = {"error": str(e)}

    # ── RE/MAX Laguna ────────────────────────────────────────────────────────
    if args.portal in ("todos", "remax"):
        print(f"\n{'-'*65}")
        print(f"  [REMAX] RE/MAX Laguna (oficina_id=26)")
        print(f"{'-'*65}")
        try:
            import scraper_remax
            import importlib
            importlib.reload(scraper_remax)  # evitar estado cacheado
            await scraper_remax.main(dry_run=False)
            # scraper_remax ya imprime su propio resultado
            resumen["remax"] = {"nuevo": 0, "actualizado": 0, "error": 0}  # stats internos
        except Exception as e:
            print(f"\n  [REMAX] ERROR: {e}")
            resumen["remax"] = {"error": str(e)}

    # ── Mercado Libre (API) ─────────────────────────────────────────────────
    if args.portal in ("todos", "ml"):
        print(f"\n{'─'*65}")
        print(f"  [ML] Mercado Libre (API oficial)")
        print(f"{'─'*65}")
        try:
            stats = await mercadolibre.scrapear(max_por_categoria=500)
            resumen["ml"] = stats
            print(f"\n  [ML] Completado — nuevo:{stats['nuevo']} act:{stats['actualizado']} err:{stats['error']}")
        except Exception as e:
            print(f"\n  [ML] ERROR: {e}")
            resumen["ml"] = {"error": str(e)}

    # ── Resumen final ────────────────────────────────────────────────────────
    duracion = int((datetime.now() - inicio).total_seconds() // 60)

    print(f"\n{'='*65}")
    print(f"  RESUMEN FINAL  ({duracion} min)")
    print(f"{'='*65}")

    total_nuevo = total_act = total_err = 0
    for alias, s in resumen.items():
        if isinstance(s, dict) and "nuevo" in s:
            total_nuevo += s.get("nuevo", 0)
            total_act   += s.get("actualizado", 0)
            total_err   += s.get("error", 0)
            print(f"  {alias:<10} nuevo:{s['nuevo']:>4}  act:{s['actualizado']:>4}  err:{s['error']:>3}")

    print(f"{'─'*65}")
    print(f"  {'TOTAL':<10} nuevo:{total_nuevo:>4}  act:{total_act:>4}  err:{total_err:>3}")

    # Conteo en DB
    total_db  = supabase.table("listings").select("id", count="exact").execute()
    activos   = supabase.table("listings").select("id", count="exact").eq("activo", True).execute()
    print(f"\n  DB total: {total_db.count:,} listings | Activos: {activos.count:,}")
    print(f"{'='*65}")

    # ── Detector automático ──────────────────────────────────────────────────
    if not args.skip_detector:
        print("\n  Corriendo detector de oportunidades...")
        import subprocess
        subprocess.run([sys.executable, "detector.py"], cwd=os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    asyncio.run(main())
