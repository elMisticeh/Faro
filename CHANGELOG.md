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

### Pieza 1b - Fix bandera (click + trail)
- Bandera pinneada (click) ahora glass oscuro igual que la del cursor (`.hex-popup`).
- `cerrarBanderasMapa` elimina nodos `.flag-tip` huerfanos + bind a `dragstart`;
  el click hace sweep previo (ya no quedan varias banderas pegadas al panear).

### Pieza 2 - Uso de suelo (zonificacion IMPLAN, on-demand)
- Toggle "Uso de suelo" en la toolbar del mapa: carga `data/zonificacion_torreon_slim.geojson`
  (32 zonas, 0.83MB, simplificado RDP ~44m desde los 20MB originales del IMPLAN).
- Capa coloreada por SIMBOLOGIA (getZoneColor) + leyenda por categoria.
- Click en zona -> sidebar con SIMBOLOGIA, codigo, categoria y nota orientada a desarrollo.
- La bandera del heatmap muestra el uso de suelo del punto (point-in-polygon, ~0.16ms/lookup).
- Datos en `frontend/data/` y `docs/data/` (fetch on-demand; no infla el HTML).

### Pieza 3 - Valor de construccion por residual + score de oportunidad (flipping)
- Nuevas columnas en la lista: **$/m2 const. real** y **Flip** (0-100, ordenable).
- $/m2 const real = (precio_total - m2_terreno * promedio($/m2 terreno de la colonia)) / m2_construccion.
  Corrige el calculo anterior (precio/m2c) que ignoraba el valor del suelo.
- Score flip por percentil invertido: construccion mas barata vs mercado = mayor oportunidad.
- Caso "terreno >= precio": construccion practicamente gratis -> flip 99 (revisar: oportunidad o dato sucio).
- Filtro "Oportunidad flip (>=70)" en el dropdown "Solo".
- 100% client-side (usa promedios de colonia ya disponibles); no toca la DB.

### Pieza 2b - Fix sobre-simplificacion del uso de suelo
- La zonificacion son ~23,451 poligonos chicos (1 por manzana) dentro de 32 features.
  El RDP a ~44m los colapsaba a triangulos y borraba muchos -> huecos donde los pins no caian.
- Re-simplificado a ~3m (eps 0.00003) con fallback que NO borra poligonos: 4.05MB (~1MB gzip),
  los 23,451 poligonos preservados.
- Render en canvas (`L.canvas`) para ~23k poligonos sin lag (SVG era inviable).
- Point-in-polygon ahora con indice plano por-poligono + bbox: 0.077ms/lookup.

### MK2 completo.

## v3.1.0 "MK3" - 2026-06-06

Objetivo: uso de suelo persistido en Supabase para filtrar en la lista sin cargar el geojson por sesion.

### Listo (codigo)
- `scripts/mk3_uso_suelo.sql`: agrega columnas `uso_suelo` + `uso_suelo_cat` (aditivo, IF NOT EXISTS).
- `scripts/poblar_uso_suelo.py`: batch point-in-polygon (indice plano por-poligono) que
  pobla los listings con coordenadas; agrupa updates por valor (PATCH en lotes de 150 ids).
- Frontend: columna "Uso suelo" en la lista (con swatch de color) + filtro "Uso de suelo"
  (categorias presentes) + ordenable. Lee `uso_suelo_cat` directo de Supabase.
- Fix categoria: EAP (Administracion Publica y Servicios Urbanos) -> Equipamiento (antes Servicios).

### Ejecutado (2026-06-06)
- DDL corrido en Supabase SQL Editor (columnas + indice creados).
- `poblar_uso_suelo.py` corrido: **848 / 1,869 listings con uso de suelo** (45%).
  El resto cae fuera de la mancha urbana del IMPLAN (ejidos/periferia/otros municipios) -> NULL (esperado).
- Distribucion: Habitacional 555, Corredor urbano 124, Equipamiento 97, Mixto 47, Industrial 24, Agricola 1.
- Idempotente: re-correr el batch recalcula todo (util al agregar listings o mejorar la zonificacion).

### MK3 completo.

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
