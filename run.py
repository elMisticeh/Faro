"""
run.py — Orquestador principal del pipeline Real Estate Torreón
===============================================================
Reemplaza scraper_master.py + scheduler.py en un único CLI.

Comandos:
    py run.py scrape                        # todos los portales
    py run.py scrape --portal i24           # solo inmuebles24
    py run.py scrape --portal remax         # solo RE/MAX
    py run.py scrape --portal ml            # solo Mercado Libre
    py run.py scrape --max-pags 5 --skip-ia # limitar páginas, sin IA

    py run.py historico                     # detectar cambios de precio/bajados
    py run.py historico --historial         # ver sesiones anteriores

    py run.py validar-colonias              # corregir colonias con IA
    py run.py validar-colonias --reporte    # solo ver, sin modificar
    py run.py validar-colonias --limite 50  # limitar a 50 listings

    py run.py anomalias                     # detector de anomalías (reglas)
    py run.py anomalias --ia                # + validación Haiku

    py run.py full                          # pipeline completo (scrape + historico + colonias + anomalias)
    py run.py full --skip-ia                # pipeline completo sin llamadas a IA
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from playwright.async_api import async_playwright
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers import inmuebles24, vivanuncios, lamudi, icasas
from scrapers import metroscubicos, propiedades, trovit
from scrapers import mercadolibre

MAX_PAGINAS_DEFAULT = 15

PORTALES_PLAYWRIGHT = [
    (inmuebles24,   "i24"),
    (vivanuncios,   "viva"),
    (lamudi,        "lamudi"),
    (icasas,        "icasas"),
    (metroscubicos, "mc"),
    (propiedades,   "prop"),
    (trovit,        "trovit"),
]

# ── Runner Playwright ─────────────────────────────────────────────────────────

async def correr_portal_playwright(modulo, max_pags: int) -> dict:
    stats_total = {"nuevo": 0, "actualizado": 0, "error": 0, "paginas": 0, "urls": 0}

    for entry in modulo.URLS:
        url, tipo_op = entry[0], entry[1]
        print(f"\n  URL: {url.split('/')[-1]}")

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

        await asyncio.sleep(3)

    return stats_total

# ── Comando: scrape ───────────────────────────────────────────────────────────

async def cmd_scrape(portal: str, max_pags: int, skip_ia: bool):
    inicio = datetime.now()
    print(f"\n{'='*65}")
    print(f"  SCRAPER MULTI-PORTAL — TORREÓN")
    print(f"  {inicio.strftime('%Y-%m-%d %H:%M:%S')} | Portal: {portal} | Págs: {max_pags}")
    print(f"{'='*65}")

    resumen = {}

    # Portales Playwright
    for modulo, alias in PORTALES_PLAYWRIGHT:
        if portal not in ("todos", alias):
            continue
        print(f"\n{'─'*65}")
        print(f"  [{alias.upper()}] {modulo.NOMBRE}")
        print(f"{'─'*65}")
        try:
            stats = await correr_portal_playwright(modulo, max_pags)
            resumen[alias] = stats
            print(f"\n  [{alias.upper()}] nuevo:{stats['nuevo']} act:{stats['actualizado']} err:{stats['error']}")
        except Exception as e:
            print(f"\n  [{alias.upper()}] ERROR: {e}")
            resumen[alias] = {"error": str(e)}

    # RE/MAX
    if portal in ("todos", "remax"):
        print(f"\n{'─'*65}")
        print(f"  [REMAX] RE/MAX Laguna")
        print(f"{'─'*65}")
        try:
            from scrapers import remax as remax_scraper
            stats = await remax_scraper.main(dry_run=False)
            resumen["remax"] = stats
            print(f"\n  [REMAX] nuevo:{stats.get('nuevo',0)} act:{stats.get('actualizado',0)}")
        except Exception as e:
            print(f"\n  [REMAX] ERROR: {e}")
            resumen["remax"] = {"error": str(e)}

    # Mercado Libre (API)
    if portal in ("todos", "ml"):
        print(f"\n{'─'*65}")
        print(f"  [ML] Mercado Libre (API)")
        print(f"{'─'*65}")
        try:
            stats = await mercadolibre.scrapear(max_por_categoria=500)
            resumen["ml"] = stats
            print(f"\n  [ML] nuevo:{stats['nuevo']} act:{stats['actualizado']}")
        except Exception as e:
            print(f"\n  [ML] ERROR: {e}")
            resumen["ml"] = {"error": str(e)}

    # Resumen
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
            print(f"  {alias:<10} nuevo:{s['nuevo']:>4}  act:{s['actualizado']:>4}  err:{s.get('error',0):>3}")
    print(f"{'─'*65}")
    print(f"  {'TOTAL':<10} nuevo:{total_nuevo:>4}  act:{total_act:>4}  err:{total_err:>3}")
    total_db = supabase.table("listings").select("id", count="exact").execute()
    activos  = supabase.table("listings").select("id", count="exact").eq("activo", True).execute()
    print(f"\n  DB total: {total_db.count:,} | Activos: {activos.count:,}")
    print(f"{'='*65}")

# ── Comando: historico ────────────────────────────────────────────────────────

def cmd_historico(fuente: str, ver_historial: bool, n: int):
    from core.historico import detectar_cambios, ver_historial as _ver_historial
    if ver_historial:
        _ver_historial(n)
    else:
        detectar_cambios(fuente)

# ── Comando: validar-colonias ─────────────────────────────────────────────────

def cmd_validar_colonias(reporte: bool, limite: int, fuente: str | None):
    from validators.colonias_ai import corregir_colonias
    corregir_colonias(reporte_solo=reporte, fuente=fuente, limite=limite)

# ── Comando: anomalias ────────────────────────────────────────────────────────

def cmd_anomalias(usar_ia: bool, reporte: bool):
    from validators.anomalias import main as anomalias_main
    import sys as _sys
    old_argv = _sys.argv
    args = []
    if usar_ia:
        args.append('--ia')
    if reporte:
        args.append('--reporte')
    _sys.argv = ['anomalias'] + args
    anomalias_main()
    _sys.argv = old_argv

# ── Comando: instagram ────────────────────────────────────────────────────────

def cmd_instagram(perfiles, posts, posts_dump, max_posts, dry_run, captions_out):
    from scrapers.instagram import run as ig_run, recolectar_urls
    urls = recolectar_urls(posts, posts_dump)
    if not perfiles and not urls:
        print("[instagram] Da --perfil y/o --posts/--posts-dump (no encontre URLs).")
        return
    if urls:
        print(f"[instagram] {len(urls)} posts sueltos a procesar")
    asyncio.run(ig_run(perfiles, urls, max_posts, dry_run, captions_out))

# ── Comando: dedup (duplicados por propiedad) ────────────────────────────────

def cmd_dedup(fuente, dry_run):
    from core.duplicados import marcar_duplicados_db
    st = marcar_duplicados_db(fuente, dry_run=dry_run)
    print(f"Activos: {st['activos']} | grupos duplicados: {st['grupos_dup']} | "
          f"desactivados: {st['desactivados']} | protegidos: {st['protegidos']}"
          + ("  (DRY RUN)" if dry_run else ""))
    for d in st['detalle']:
        print(f"  - {d['colonia']}: {d['desactivado']} (${d['precio']}) -> "
              f"vigente {d['vigente']} (${d['precio_vigente']})")

# ── Comando: full (pipeline completo) ────────────────────────────────────────

async def cmd_full(max_pags: int, skip_ia: bool):
    print(f"\n{'#'*65}")
    print(f"  PIPELINE COMPLETO — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*65}")

    # 1. Scrape todos los portales
    await cmd_scrape("todos", max_pags, skip_ia)

    # 2. Detectar cambios históricos
    print(f"\n{'#'*65}")
    print(f"  PASO 2: HISTÓRICO DE CAMBIOS")
    print(f"{'#'*65}")
    cmd_historico("todas", False, 10)

    # 3. Validar colonias con IA
    if not skip_ia:
        print(f"\n{'#'*65}")
        print(f"  PASO 3: CORRECCIÓN DE COLONIAS (IA)")
        print(f"{'#'*65}")
        cmd_validar_colonias(reporte=False, limite=200, fuente=None)

    # 4. Detector de anomalías
    print(f"\n{'#'*65}")
    print(f"  PASO 4: DETECTOR DE ANOMALÍAS")
    print(f"{'#'*65}")
    cmd_anomalias(usar_ia=not skip_ia, reporte=False)

    # 5. Oportunidades
    print(f"\n{'#'*65}")
    print(f"  PASO 5: DETECTOR DE OPORTUNIDADES")
    print(f"{'#'*65}")
    import subprocess
    subprocess.run([sys.executable, "detector.py"], cwd=os.path.dirname(os.path.abspath(__file__)))

    print(f"\n{'#'*65}")
    print(f"  PIPELINE COMPLETO TERMINADO — {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'#'*65}\n")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Real Estate Torreón — Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    # scrape
    p_scrape = subparsers.add_parser("scrape", help="Correr scrapers")
    p_scrape.add_argument("--portal", default="todos",
                          help="Portal: todos|i24|viva|lamudi|icasas|mc|prop|trovit|ml|remax")
    p_scrape.add_argument("--max-pags", type=int, default=MAX_PAGINAS_DEFAULT)
    p_scrape.add_argument("--skip-ia", action="store_true")

    # historico
    p_hist = subparsers.add_parser("historico", help="Detectar cambios históricos")
    p_hist.add_argument("--fuente", default="todas")
    p_hist.add_argument("--historial", action="store_true", help="Ver sesiones anteriores")
    p_hist.add_argument("--n", type=int, default=10)

    # validar-colonias
    p_col = subparsers.add_parser("validar-colonias", help="Corregir colonias con IA")
    p_col.add_argument("--reporte", action="store_true")
    p_col.add_argument("--limite", type=int, default=0)
    p_col.add_argument("--fuente", type=str, default=None)

    # anomalias
    p_anom = subparsers.add_parser("anomalias", help="Detector de anomalías")
    p_anom.add_argument("--ia", action="store_true")
    p_anom.add_argument("--reporte", action="store_true")

    # full
    p_full = subparsers.add_parser("full", help="Pipeline completo")
    p_full.add_argument("--max-pags", type=int, default=MAX_PAGINAS_DEFAULT)
    p_full.add_argument("--skip-ia", action="store_true")

    # instagram
    p_ig = subparsers.add_parser("instagram", help="Scraper de Instagram (perfiles + posts)")
    p_ig.add_argument("--perfil", nargs="+", help="Username(s) sin @")
    p_ig.add_argument("--posts", nargs="+", help="URLs de posts o archivos .txt con URLs")
    p_ig.add_argument("--posts-dump", action="store_true", help="Lee los .txt del Dump del vault")
    p_ig.add_argument("--max", type=int, default=50, help="Max posts por perfil")
    p_ig.add_argument("--dry-run", action="store_true")
    p_ig.add_argument("--captions-out", metavar="PATH", help="Solo vuelca captions crudos (sin Haiku)")

    # dedup
    p_dedup = subparsers.add_parser("dedup", help="Desactiva duplicados por propiedad (mismo colonia+m2)")
    p_dedup.add_argument("--fuente", default="instagram",
                         help="Prefijo de pagina_fuente (default 'instagram'; vacio = toda la tabla)")
    p_dedup.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.comando == "scrape":
        asyncio.run(cmd_scrape(args.portal, args.max_pags, args.skip_ia))

    elif args.comando == "historico":
        cmd_historico(args.fuente, args.historial, args.n)

    elif args.comando == "validar-colonias":
        cmd_validar_colonias(args.reporte, args.limite, args.fuente)

    elif args.comando == "anomalias":
        cmd_anomalias(args.ia, args.reporte)

    elif args.comando == "full":
        asyncio.run(cmd_full(args.max_pags, args.skip_ia))

    elif args.comando == "instagram":
        cmd_instagram(args.perfil, args.posts, args.posts_dump,
                      args.max, args.dry_run, args.captions_out)

    elif args.comando == "dedup":
        cmd_dedup(args.fuente, args.dry_run)


if __name__ == "__main__":
    main()
