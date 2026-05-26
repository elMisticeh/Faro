# CAMPO — Changelog

## v2.0.0 — 2026-05-26

### Breaking changes
- App renamed from "Torreón RE Dashboard" to **CAMPO**
- Tab structure reorganized: 4 flat tabs → 2 main tabs (Mercado / Demografía)

### Added
- **Tab Demografía**: análisis sociodemográfico INEGI 2020 por zona de influencia
  - 332 AGEBs urbanos de Torreón embebidos (datos DATERRA/INEGI)
  - Modos: Radio (click + km configurables) y selección manual de AGEBs
  - Score de zona 1–10 con 5 indicadores (crecimiento, edad activa, ocupación, PEA, NSE)
  - Heatmaps: hogares totales, crecimiento 2010–20, NSE predominante
  - Benchmarks municipales automáticos para comparativas
- **GitHub Pages**: hosting gratuito en `docs/index.html`
- `serve.bat`: servidor local para desarrollo

### Changed
- Design system: AirDNA tokens — `bg #212121`, `accent #0000ee`, `border #3c3e4d`
- Fuente: Space Grotesk → **Inter** (más legible en datos densos)
- Tab Mercado agrupa Lista + Mapa + Validación como sub-tabs
- Botones: fondo accent ahora texto blanco (AirDNA spec)
- Scrollbars: estilo custom sutil
- Logo: "CAMPO · Torreón" con separador en muted

### Fixed
- IMPLAN: `inSR=4326` obligatorio para queries lat/lng (devolvía 0 features sin él)
- IMPLAN: campo correcto es `SIMBOLOGIA` (no `DESCRIPCIO` — no existe en este layer)

---

## v1.0.0 — 2026-05-25

- Dashboard inicial: tabs Lista / Mapa / Validación
- Hexágonos H3 con precio mediano por zona
- Conexión Supabase (~2,370 listings activos)
- Filtros: operación, tipo, fuente, precio, m², colonia (multi-select)
- Detección de oportunidades automática
- Exportación CSV y resumen por colonia
- Archivo: `archive/v1.0-torreon-re-dashboard-2026-05-25.html`
