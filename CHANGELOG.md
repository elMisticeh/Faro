# FARO - Changelog

> Convencion de versiones "MK": cada ola de cambios se etiqueta MK1, MK2, etc.
> Antes de empezar una MK se guarda un snapshot del build estable anterior en
> `archive/versions/faro-MKn-FECHA.html` (+ su commit baseline). Si algo se rompe,
> ese snapshot es la version de respaldo funcional.

## v3.0.0 "MK2" - 2026-06-04 (en progreso)

Baseline: MK1 = commit c82394e (`archive/versions/faro-MK1-2026-06-04.html`).
Objetivo MK2: oportunidades de desarrollo (uso de suelo, contraste de mapa,
valor de construccion real). Entrega por piezas con checkpoint.

### Pieza 1 - Contraste y usabilidad del mapa
- Heatmap: nuevo ramp legible sobre fondo claro (sin amarillos/cianes washed-out).
- Bandera de precio: estilo glass oscuro (`.flag-tip`) -> texto legible sobre mapa claro;
  ahora sigue el cursor (sticky) y se limpia el "trail" al panear/zoom (`cerrarBanderasMapa`).
- Colonias: linea punteada visible en fondo claro (emerald `#047857`) + tooltip legible.
- Recoloreados los `#e8ff47`/`#4ade80` ilegibles en popups y sidebar de hexagono
  a emerald `#059669` / amber `#d97706`.

### Pendiente MK2
- Pieza 2: sidebar de uso de suelo al click en mapa (zonificacion IMPLAN on-demand) + uso de suelo en la bandera.
- Pieza 3: columna $/m2 construido real (resta valor de terreno por colonia) + score de oportunidad (flipping).
- MK3: persistir `uso_suelo` en Supabase (point-in-polygon batch) para filtrar en la lista.

### Nota sobre el "Score" actual
`score_calidad_anuncio` (columna Score de la lista) NO es score de oportunidad:
es una calificacion 0-100 generada por IA de que tan COMPLETO esta el anuncio
(RE/MAX lo fija en 70). El score de oportunidad (flipping) sera una metrica nueva e independiente (Pieza 3).

---

## v2.2.0 "MK1" - 2026-06-04

### Added
- **Reporte Consolidado (1 click)**: demografia + mercado en un documento de 7 paginas
  (Portada/Indice/Recomendacion/Demografia/Mercado/Fuentes/Glosario) con recomendacion
  explicita: que / a quien / a cuantos / a que precio / por que.
- Sistema de marca unificado para reportes (logo Pin verde, membrete FARO, paleta esmeralda).

### Changed
- Reporte de mercado migrado de dorado (beacon) a verde + Pin (consistencia de marca).

### Fixed
- Repintado iOS Safari/WebKit: filtros y popups ahora actualizan al instante (`forceRepaint`).

---

## v2.1.0 — 2026-05-30

### Changed
- App renamed from **CAMPO** to **FARO**

---

## v2.0.0 — 2026-05-26

### Breaking changes
- App renamed from "Torreón RE Dashboard" to **CAMPO** (ahora FARO)
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
- Logo: "FARO · Torreón" con separador en muted

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
