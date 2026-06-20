# Diseño — Lente "Dónde Desarrollar" + Reporte (FARO)

**Fecha:** 2026-06-18
**Proyecto:** FARO (real-estate-torreon)
**Autor:** Rogelio + Claude
**Estado:** aprobado, pendiente plan de implementación

## Problema

Encontrar la mejor colonia de Torreón para **desarrollar vivienda nueva**: dónde
el mercado paga más caro el m² construido relativo al costo del terreno. Como el
costo de obra es ~constante en cualquier colonia, vender más caro = más margen.

Es el inverso de la lógica de *flipping* ya existente (`calcularValorConstruccion`):
flipping busca el residual de construcción **más barato** (para comprar barato);
desarrollo busca el residual **más caro** (para construir y vender con margen),
agregado por colonia.

## Decisiones tomadas (brainstorming)

1. **Entregable:** nueva lente interactiva dentro de FARO + botón que exporta un
   reporte HTML imprimible.
2. **Métrica de ranking:** margen neto real = residual $/m²c del mercado − costo
   de obra fijo (ajustable).
3. **Universo:** solo **casas en venta** (el producto que se desarrollaría), con
   mínimo de muestras por colonia.

## Metodología — Índice de Margen de Desarrollo

Por cada casa en venta (ya calculado en `calcularValorConstruccion`):

```
valor_terreno    = m2_terreno × ($/m² terreno promedio/mediana de la colonia)
valor_construido = precio_venta − valor_terreno
residual_$/m²c   = valor_construido ÷ m2_construccion   # lo que el mercado paga por m² edificado
```

Agregación nueva, **por colonia**:

| Campo | Cálculo |
|---|---|
| `$/m² terreno` (costo) | mediana de listings de **terreno** de la colonia |
| `ticket mediano` | mediana de precio de venta de casas |
| `residual $/m²c mercado` | **mediana** del residual de las casas |
| `margen neto $/m²c` | `residual $/m²c − costo_obra` ← **métrica de ranking** |
| `margen por casa típica` | `margen neto × m² const. mediano` (cifra tangible en pesos) |
| `confianza` | 🟢/🟡/🔴 por nº muestras de casa Y si el $/m² terreno es real vs fallback global |

### Decisiones de método

- **Mediana, no promedio** — robusto a outliers y precios sucios del scrape.
- **Costo de obra ajustable**, default **$15,000/m²** (residencial Torreón gama
  media-alta). Recalcula todo en vivo desde un input en la lente.
- **Semáforo de confianza** — una colonia con margen alto pero sin listings de
  terreno reales (usa promedio global) es ruido. Por defecto la lente esconde 🔴.
  - 🟢 ≥ N casas Y $/m² terreno real (≥2 terrenos en la colonia)
  - 🟡 cumple uno de los dos
  - 🔴 pocas muestras y/o $/m² terreno por fallback global

## Componente 1 — Lente "Dónde Desarrollar" (frontend, client-side)

Nuevo modo dentro del tab **Mercado** (junto a Lista / Mapa / Validación).

- **Controles:** input *costo de obra $/m²* (default $15,000, recalcula en vivo) ·
  slider *muestras mínimas* por colonia (default 4) · toggle *mostrar 🔴*.
- **Tabla-ranking** ordenable, una fila por colonia, orden por margen neto desc:
  `Colonia · confianza · $/m² terreno · ticket mediano · residual $/m²c · margen neto $/m²c · margen/casa típica · nº casas`.
- **Mapa de calor:** colonias pintadas por margen neto (verde intenso = mejor).
  Reusa polígonos de colonia/IMPLAN del mapa existente. Click → tarjeta de desglose.
- **Botón "⬇ Reporte Desarrollo"** dispara el Componente 2.

Restricciones:
- 100% client-side sobre `allData` ya cargado. No toca Supabase ni la DB. Cero costo.
- Reusa el **patrón** de residual de `calcularValorConstruccion`, pero la lente
  calcula su propio residual por-listing usando la **mediana** de $/m² terreno de
  la colonia (no el promedio que usa `_m2cReal` del flip). Es una función nueva de
  agregación que no pisa la lógica de flipping existente.

## Componente 2 — Reporte "Dónde Desarrollar" (HTML imprimible → PDF)

Mismo patrón que `generateReporteConsolidado`: ventana nueva, estilo GRID/FARO,
Ctrl+P → PDF.

1. **Portada** — supuestos (costo obra usado, fecha, nº colonias, universo = casas venta).
2. **Top 10 colonias** — ranking de margen neto con barras + margen/casa típica.
3. **Tabla completa** — colonias 🟢/🟡, columnas de la lente.
4. **Mapa de calor** — captura del mapa de margen + lectura geográfica.
5. **Metodología y advertencias** — fórmula residual, mediana, semáforo, disclaimer
   honesto (oferta no transacciones; scrape pausado ~mar-2026).

## Fuera de alcance (YAGNI / iteración 2)

- **Capacidad normativa (COS/CUS de MK5)** — "¿cuántos m² puedo construir aquí?"
  no entra en el ranking v1. El reporte puede mencionar la clave/coeficientes por
  colonia como dato, pero el ranking es puro margen de mercado.
- **Capa de departamentos / vertical.**
- **Segmentación por gama** (media/residencial/premium) — posible iteración si el
  ranking mezcla productos demasiado distintos.

## Criterios de aceptación

- [ ] La lente lista colonias ordenadas por margen neto $/m²c, recalculando en vivo
      al cambiar costo de obra.
- [ ] Cada colonia muestra confianza 🟢/🟡/🔴; 🔴 oculto por defecto.
- [ ] El mapa pinta colonias por margen neto y el click muestra desglose.
- [ ] El botón genera un reporte HTML de 5 páginas imprimible a PDF.
- [ ] Cero llamadas nuevas a Supabase; todo sobre `allData`.
- [ ] Validación: JS parse OK, reporte abre sin error, números cuadran contra un
      cálculo manual de 1–2 colonias.

## Convención de entrega

Estilo MK (como el resto de FARO): piezas con checkpoint + git tag. Snapshot del
build estable en `archive/versions/`. Documentar en CHANGELOG.md.
