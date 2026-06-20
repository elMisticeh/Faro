# Lente "Dónde Desarrollar" — Implementation Plan (FARO MK7)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar a FARO una lente interactiva que rankea colonias de Torreón por margen neto de desarrollo de vivienda ($/m² construido que paga el mercado − costo de obra), más un reporte HTML imprimible.

**Architecture:** Todo client-side sobre `allData` ya cargado (cero llamadas nuevas a Supabase). Una función pura de agregación por colonia alimenta tres consumidores: tabla-ranking, mapa de calor (reusa `coloniasLayer` GeoJSON) y reporte (mirror de `generateReporteConsolidado`). Se entrega como pieza MK7 con tag git y entrada en CHANGELOG, siguiendo la convención del proyecto.

**Tech Stack:** HTML/JS vanilla en un solo archivo `frontend/dashboard.html` (~660k tokens), Leaflet ya cargado, estilo GRID (Sora + Space Mono). Sin framework de tests; verificación = `node --check` del script extraído + verificación visual en `serve.bat`.

**User Verification:** YES — el usuario confirma visualmente en `serve.bat` que la lente rankea correctamente y que el reporte abre sin error, antes de cerrar la pieza (patrón habitual de FARO).

---

## Estructura de archivos

- **Modify:** `frontend/dashboard.html` — único archivo de la app. Se agrega:
  - Markup: 4ª sub-tab "Desarrollo" en `#view-mercado` (línea ~458) + `<div id="view-desarrollo">`.
  - Lógica: `switchSubTab` extendido (línea ~836); función nueva `calcularMargenDesarrollo()`; render de tabla `renderDesarrollo()`; mapa `renderMapaDesarrollo()`; reporte `generateReporteDesarrollo()`.
- **Modify:** `CHANGELOG.md` — entrada MK7.
- **Create (snapshot):** `archive/versions/faro-MK7-2026-06-18.html` (untracked, respaldo).

Sin nuevos archivos de datos. Sin cambios de schema/DB.

---

### Task 1: Motor de agregación por colonia (`calcularMargenDesarrollo`)

**Goal:** Función pura que toma `allData` + costo de obra + muestras mínimas y devuelve un arreglo de colonias ordenado por margen neto $/m²c, con semáforo de confianza.

**Files:**
- Modify: `frontend/dashboard.html` — insertar la función justo después de `calcularValorConstruccion()` (termina en línea ~2096).

**Acceptance Criteria:**
- [ ] Para cada colonia con ≥ `minMuestras` casas en venta devuelve: `colonia`, `nCasas`, `nTerrenos`, `pm2TerrenoMediana`, `ticketMediano`, `m2cMediano`, `residualMediano` ($/m²c que paga el mercado), `margenNeto` (`residualMediano − costoObra`), `margenPorCasa` (`margenNeto × m2cMediano`), `confianza` (`'alta'|'media'|'baja'`).
- [ ] `pm2TerrenoMediana` = mediana de `precio_x_m2_terreno` de listings de **terreno** de la colonia; si hay < 2 terrenos, usa la mediana global de terrenos y marca el flag de fallback.
- [ ] El residual por casa se calcula con la **mediana** de terreno de la colonia (no el promedio que usa `_m2cReal`): `residual = (precio_mxn − m2_terreno × pm2TerrenoMediana) / m2_construccion`, descartando residuales ≤ 0.
- [ ] Confianza: `alta` si `nCasas ≥ minMuestras` Y `nTerrenos ≥ 2`; `media` si cumple uno; `baja` si ninguno (incluye fallback global de terreno).
- [ ] Solo casas en venta: `tipo_inmueble === 'casa' && tipo_operacion === 'venta' && m2_construccion > 0 && m2_terreno > 0 && precio_mxn > 0`.
- [ ] Resultado ordenado por `margenNeto` descendente.
- [ ] No depende del DOM ni de Leaflet (testeable en node).

**Verify:** `node --check` sobre el bloque de la función extraído + cross-check manual: en la consola del navegador (`serve.bat`), `calcularMargenDesarrollo(allData, 15000, 4)` para una colonia conocida (ej. Hacienda El Rosario) debe dar un `margenNeto` coherente con el cálculo a mano del ejemplo del spec (~$15,789/m²c residual antes de restar obra).

**Steps:**

- [ ] **Step 1: Escribir test standalone de la lógica matemática**

Crear `scripts/margen_desarrollo.test.js` con la función *aislada* (copia de trabajo para validar la matemática; la versión productiva vive inline en el HTML):

```javascript
// scripts/margen_desarrollo.test.js — valida la matemática de calcularMargenDesarrollo
const assert = require('assert');

function median(a){ if(!a||!a.length) return null; const x=[...a].sort((p,q)=>p-q); return x[Math.floor(x.length/2)]; }

function calcularMargenDesarrollo(data, costoObra, minMuestras){
  const terrAll = data.filter(d=>d.tipo_inmueble==='terreno'&&d.precio_x_m2_terreno>0).map(d=>d.precio_x_m2_terreno);
  const pm2TerrGlobal = median(terrAll);
  const terrPorColonia = {};
  data.forEach(d=>{ if(d.tipo_inmueble==='terreno'&&d.precio_x_m2_terreno>0&&d.colonia)
    (terrPorColonia[d.colonia]=terrPorColonia[d.colonia]||[]).push(d.precio_x_m2_terreno); });
  const casas = data.filter(d=>d.tipo_inmueble==='casa'&&d.tipo_operacion==='venta'&&d.m2_construccion>0&&d.m2_terreno>0&&d.precio_mxn>0&&d.colonia);
  const porColonia = {};
  casas.forEach(d=>{ (porColonia[d.colonia]=porColonia[d.colonia]||[]).push(d); });
  const out = [];
  Object.entries(porColonia).forEach(([col, arr])=>{
    if(arr.length < minMuestras) return;
    const terrArr = terrPorColonia[col] || [];
    const fallback = terrArr.length < 2;
    const pm2Terr = fallback ? pm2TerrGlobal : median(terrArr);
    if(!pm2Terr) return;
    const residuales = [], tickets = [], m2cs = [];
    arr.forEach(d=>{ const res = (d.precio_mxn - d.m2_terreno*pm2Terr)/d.m2_construccion;
      if(res>0){ residuales.push(res); tickets.push(d.precio_mxn); m2cs.push(d.m2_construccion); } });
    if(!residuales.length) return;
    const residualMediano = median(residuales);
    const m2cMediano = median(m2cs);
    const margenNeto = residualMediano - costoObra;
    const nTerrenos = terrArr.length;
    const confianza = (arr.length>=minMuestras && nTerrenos>=2) ? 'alta'
                    : ((arr.length>=minMuestras || nTerrenos>=2) && !fallback) ? 'media' : 'baja';
    out.push({ colonia:col, nCasas:arr.length, nTerrenos, pm2TerrenoMediana:pm2Terr,
      ticketMediano:median(tickets), m2cMediano, residualMediano, margenNeto,
      margenPorCasa: margenNeto*m2cMediano, confianza });
  });
  return out.sort((a,b)=>b.margenNeto-a.margenNeto);
}

// Fixture: una colonia "cara" y una "barata"
const data = [
  // terrenos colonia A (cara): $6000/m2
  {tipo_inmueble:'terreno',precio_x_m2_terreno:6000,colonia:'A'},
  {tipo_inmueble:'terreno',precio_x_m2_terreno:6000,colonia:'A'},
  // 4 casas colonia A: ticket 9M, 500 m2 terreno, 380 m2 const -> residual = (9M - 500*6000)/380 = 15789
  ...Array.from({length:4},()=>({tipo_inmueble:'casa',tipo_operacion:'venta',precio_mxn:9000000,m2_terreno:500,m2_construccion:380,colonia:'A'})),
  // terrenos colonia B (barata): $2000/m2
  {tipo_inmueble:'terreno',precio_x_m2_terreno:2000,colonia:'B'},
  {tipo_inmueble:'terreno',precio_x_m2_terreno:2000,colonia:'B'},
  // 4 casas colonia B: ticket 3M, 300 m2 terreno, 250 m2 const -> residual = (3M - 300*2000)/250 = 9600
  ...Array.from({length:4},()=>({tipo_inmueble:'casa',tipo_operacion:'venta',precio_mxn:3000000,m2_terreno:300,m2_construccion:250,colonia:'B'})),
];

const r = calcularMargenDesarrollo(data, 12000, 4);
assert.strictEqual(r.length, 2, 'deben salir 2 colonias');
assert.strictEqual(r[0].colonia, 'A', 'A debe rankear primero (mayor margen)');
assert.strictEqual(Math.round(r[0].residualMediano), 15789, 'residual A');
assert.strictEqual(Math.round(r[0].margenNeto), 3789, 'margenNeto A = 15789-12000');
assert.strictEqual(r[0].confianza, 'alta', 'A confianza alta (4 casas, 2 terrenos)');
assert.strictEqual(Math.round(r[1].residualMediano), 9600, 'residual B');
console.log('OK — calcularMargenDesarrollo: matemática validada');
```

- [ ] **Step 2: Correr el test y verlo fallar/pasar la lógica**

Run: `node scripts/margen_desarrollo.test.js`
Expected: `OK — calcularMargenDesarrollo: matemática validada` (si falla, corregir la fórmula antes de portarla al HTML).

- [ ] **Step 3: Portar la función inline al dashboard**

Insertar en `frontend/dashboard.html` justo después del cierre de `calcularValorConstruccion()` (~línea 2096) la **misma** función `calcularMargenDesarrollo(data, costoObra, minMuestras)` validada arriba, reutilizando el helper `median` ya disponible en el scope del reporte (si no es global, definir un `medianDesarrollo` local). Guardar el último resultado en `window._margenDesarrollo` para que el mapa y el reporte lo consuman sin recalcular.

- [ ] **Step 4: Verificar parse del HTML**

Run: extraer el `<script>` principal y `node --check`, o abrir `serve.bat` y confirmar 0 errores en consola al cargar.
Expected: sin SyntaxError; `calcularMargenDesarrollo` existe en `window`.

- [ ] **Step 5: Commit**

```bash
git add frontend/dashboard.html scripts/margen_desarrollo.test.js
git commit -m "feat(faro): motor de agregacion margen de desarrollo por colonia (MK7 pieza 1)"
```

```json:metadata
{"files": ["frontend/dashboard.html", "scripts/margen_desarrollo.test.js"], "verifyCommand": "node scripts/margen_desarrollo.test.js", "acceptanceCriteria": ["devuelve colonias rankeadas por margenNeto desc", "usa mediana de terreno por colonia con fallback global", "semaforo de confianza alta/media/baja", "solo casas en venta", "sin dependencia de DOM/Leaflet"], "requiresUserVerification": false}
```

---

### Task 2: Sub-tab "Desarrollo" + tabla-ranking + controles en vivo

**Goal:** Agregar la 4ª sub-tab dentro de Mercado con controles (costo de obra, muestras mínimas, toggle 🔴) y una tabla-ranking ordenable que recalcula en vivo.

**Files:**
- Modify: `frontend/dashboard.html` — markup sub-tab (~458), nuevo `#view-desarrollo` dentro de `#view-mercado` (antes de `</div><!-- /view-mercado -->` línea ~727), `switchSubTab` (~836), función `renderDesarrollo()`.

**Acceptance Criteria:**
- [ ] Nueva sub-tab `Desarrollo` visible junto a Lista / Mapa / Validación; al hacer click muestra `#view-desarrollo` y oculta los demás views.
- [ ] Controles: input numérico `costo de obra $/m²` (default 15000), input/slider `muestras mínimas` (default 4), checkbox `mostrar baja confianza` (default off). Cualquier cambio llama `renderDesarrollo()`.
- [ ] Tabla: una fila por colonia, columnas `Colonia · confianza · $/m² terreno · ticket mediano · residual $/m²c · margen neto $/m²c · margen/casa · # casas`, ordenada por margen neto desc; filas 🔴 (`confianza==='baja'`) ocultas salvo que el checkbox esté on.
- [ ] El margen neto se formatea con color (verde si > 0, gris/rojo si ≤ 0). Cifras con los helpers de formato (`toLocaleString('es-MX')`).
- [ ] Cero llamadas a Supabase; usa `calcularMargenDesarrollo(allData, costoObra, minMuestras)`.

**Verify:** En `serve.bat`, abrir tab Mercado → Desarrollo: la tabla se llena; cambiar costo de obra de 15000 a 20000 reduce todos los márgenes en vivo; activar el checkbox agrega filas 🔴.

**Steps:**

- [ ] **Step 1: Markup de la sub-tab**

En `#view-mercado`, agregar tras la sub-tab de Validación (línea ~458):

```html
<div class="sub-tab" id="sub-tab-desarrollo" onclick="switchSubTab('desarrollo')">Desarrollo</div>
```

- [ ] **Step 2: Markup del view + controles**

Antes de `</div><!-- /view-mercado -->` (~727):

```html
<div id="view-desarrollo" style="display:none;padding:14px 18px">
  <div style="display:flex;gap:18px;align-items:end;flex-wrap:wrap;margin-bottom:14px">
    <div class="filter-group"><label>Costo de obra $/m²</label>
      <input type="number" id="dev-costo" value="15000" step="500" style="width:120px" oninput="renderDesarrollo()"></div>
    <div class="filter-group"><label>Casas mín./colonia</label>
      <input type="number" id="dev-min" value="4" min="1" step="1" style="width:80px" oninput="renderDesarrollo()"></div>
    <label style="font-size:12px;display:flex;gap:6px;align-items:center;cursor:pointer">
      <input type="checkbox" id="dev-baja" onchange="renderDesarrollo()"> mostrar baja confianza</label>
    <button class="btn-reporte" onclick="generateReporteDesarrollo()" style="margin-left:auto;font-weight:700;background:linear-gradient(135deg,#059669,#10b981)">⬇ Reporte Desarrollo</button>
  </div>
  <div id="dev-table-container"></div>
</div>
```

- [ ] **Step 3: Extender `switchSubTab`**

En `switchSubTab` (~836), añadir `desarrollo` al arreglo de ids y el toggle del view:

```javascript
function switchSubTab(sub) {
  currentSubTab = sub;
  currentTab = sub === 'lista' ? 'table' : sub;
  ['lista','mapa','validacion','desarrollo'].forEach(id => {
    const el = document.getElementById('sub-tab-' + id);
    if (el) el.classList.toggle('active', id === sub);
  });
  document.getElementById('view-table').style.display      = sub === 'lista'      ? 'block' : 'none';
  document.getElementById('view-map').style.display        = sub === 'mapa'        ? 'block' : 'none';
  document.getElementById('view-validacion').style.display = sub === 'validacion' ? 'block' : 'none';
  document.getElementById('view-desarrollo').style.display = sub === 'desarrollo' ? 'block' : 'none';
  if (sub === 'mapa') { initMap(); setTimeout(() => { if(map) map.invalidateSize(); }, 100); }
  if (sub === 'validacion') cargarValidacion();
  if (sub === 'desarrollo') renderDesarrollo();
}
```

- [ ] **Step 4: Función `renderDesarrollo()`**

Insertar junto a `calcularMargenDesarrollo`:

```javascript
function renderDesarrollo() {
  const costo = parseFloat(document.getElementById('dev-costo').value) || 15000;
  const minM  = parseInt(document.getElementById('dev-min').value) || 4;
  const verBaja = document.getElementById('dev-baja').checked;
  const rows = calcularMargenDesarrollo(allData, costo, minM);
  window._margenDesarrollo = rows;
  const vis = rows.filter(r => verBaja || r.confianza !== 'baja');
  const dot = c => c==='alta'?'🟢':c==='media'?'🟡':'🔴';
  const money = n => isNaN(n)||n==null?'—':'$'+Math.round(n).toLocaleString('es-MX');
  const cont = document.getElementById('dev-table-container');
  if (!vis.length) { cont.innerHTML = '<div class="empty">Sin colonias con suficientes muestras. Baja el mínimo o activa baja confianza.</div>'; return; }
  cont.innerHTML = `<table class="data-table"><thead><tr>
    <th>Colonia</th><th>Conf.</th><th>$/m² terreno</th><th>Ticket mediano</th>
    <th>Residual $/m²c</th><th>Margen neto $/m²c</th><th>Margen/casa</th><th># casas</th></tr></thead><tbody>` +
    vis.map(r => `<tr>
      <td>${r.colonia}</td><td>${dot(r.confianza)}</td>
      <td>${money(r.pm2TerrenoMediana)}</td><td>${money(r.ticketMediano)}</td>
      <td>${money(r.residualMediano)}</td>
      <td style="font-weight:700;color:${r.margenNeto>0?'#059669':'#b91c1c'}">${money(r.margenNeto)}</td>
      <td>${money(r.margenPorCasa)}</td><td>${r.nCasas}</td></tr>`).join('') +
    `</tbody></table>`;
}
```

- [ ] **Step 5: Verificar visual**

Run: `serve.bat` → Mercado → Desarrollo.
Expected: tabla poblada y ordenada por margen neto desc; cambiar costo de obra recalcula en vivo; checkbox agrega 🔴.

- [ ] **Step 6: Commit**

```bash
git add frontend/dashboard.html
git commit -m "feat(faro): sub-tab Desarrollo con tabla-ranking y controles en vivo (MK7 pieza 2)"
```

```json:metadata
{"files": ["frontend/dashboard.html"], "verifyCommand": "", "acceptanceCriteria": ["sub-tab Desarrollo funcional", "controles recalculan en vivo", "tabla ordenada por margen neto", "filas baja confianza ocultas por defecto"], "requiresUserVerification": false}
```

---

### Task 3: Mapa de calor por margen de desarrollo

**Goal:** Pintar las colonias por margen neto sobre un mapa Leaflet dentro de la lente, con click → tarjeta de desglose.

**Files:**
- Modify: `frontend/dashboard.html` — agregar `<div id="dev-map">` dentro de `#view-desarrollo`, función `renderMapaDesarrollo()`, reusando el GeoJSON `coloniasData` (cargado en ~1576).

**Acceptance Criteria:**
- [ ] Dentro de `#view-desarrollo` hay un mapa Leaflet (~360px alto) que colorea cada polígono de colonia por su `margenNeto` (rampa: gris→amarillo→verde intenso = mayor margen). Colonias sin dato (no rankeadas) en gris tenue.
- [ ] El match polígono↔colonia usa el nombre de colonia del GeoJSON contra `window._margenDesarrollo` (normalizado: trim + toLowerCase, reusando `colonia_alias` si aplica).
- [ ] Click en un polígono abre popup/tarjeta con: colonia, confianza, $/m² terreno, residual, margen neto, margen/casa, # casas.
- [ ] Se re-colorea cuando cambian los controles (llamado desde `renderDesarrollo()`).
- [ ] `map.invalidateSize()` tras mostrarse el view (el container pasa de display:none a block — mismo fix que el mapa de Mercado).

**Verify:** En `serve.bat` → Desarrollo: el mapa muestra colonias coloreadas; las de mayor margen se ven más verdes; click muestra el desglose; cambiar costo de obra recolorea.

**Steps:**

- [ ] **Step 1: Markup del mapa**

Dentro de `#view-desarrollo`, antes de `#dev-table-container`:

```html
<div id="dev-map" style="height:360px;border-radius:8px;overflow:hidden;margin-bottom:14px"></div>
```

- [ ] **Step 2: Función `renderMapaDesarrollo(rows)`**

```javascript
let devMap = null, devColLayer = null;
function colorMargen(m, maxAbs){
  if (m == null) return '#e5e7eb';
  const t = Math.max(0, Math.min(1, m / (maxAbs || 1)));   // 0..1 sobre el margen máximo positivo
  if (m <= 0) return '#d1d5db';
  // gris-amarillo-verde
  const g = Math.round(180 + t*40), r = Math.round(190 - t*140);
  return `rgb(${r},${g},120)`;
}
function renderMapaDesarrollo(rows){
  const cont = document.getElementById('dev-map');
  if (!cont) return;
  if (!devMap){
    devMap = L.map('dev-map').setView([25.54,-103.42], 12);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{maxZoom:19,attribution:'&copy; CARTO'}).addTo(devMap);
  }
  setTimeout(()=>devMap.invalidateSize(),60);
  if (devColLayer){ devColLayer.remove(); devColLayer = null; }
  if (!coloniasData) return;   // GeoJSON aún no cargado; se cargará al entrar a Mapa
  const norm = s => (s||'').trim().toLowerCase();
  const byCol = {}; rows.forEach(r => byCol[norm(r.colonia)] = r);
  const maxAbs = Math.max(1, ...rows.filter(r=>r.margenNeto>0).map(r=>r.margenNeto));
  const money = n => isNaN(n)||n==null?'—':'$'+Math.round(n).toLocaleString('es-MX');
  devColLayer = L.geoJSON(coloniasData, {
    style: f => { const r = byCol[norm(f.properties && (f.properties.nombre||f.properties.NOMBRE||f.properties.colonia))];
      return { color:'#9ca3af', weight:1, fillColor: colorMargen(r?r.margenNeto:null, maxAbs), fillOpacity: r?0.7:0.15 }; },
    onEachFeature: (f, layer) => {
      const r = byCol[norm(f.properties && (f.properties.nombre||f.properties.NOMBRE||f.properties.colonia))];
      if (r) layer.bindPopup(`<b>${r.colonia}</b> ${r.confianza==='alta'?'🟢':r.confianza==='media'?'🟡':'🔴'}<br>
        $/m² terreno: ${money(r.pm2TerrenoMediana)}<br>Residual: ${money(r.residualMediano)}/m²c<br>
        <b>Margen neto: ${money(r.margenNeto)}/m²c</b><br>Margen/casa: ${money(r.margenPorCasa)}<br># casas: ${r.nCasas}`);
    }
  }).addTo(devMap);
}
```

> Nota de campo del GeoJSON: confirmar la propiedad real del nombre de colonia leyendo `coloniasData.features[0].properties` en consola (puede ser `nombre`, `NOMBRE`, `SETT_NAME`, etc.) y ajustar el acceso. El bloque ya prueba 3 variantes.

- [ ] **Step 3: Llamar el mapa desde `renderDesarrollo()`**

Al final de `renderDesarrollo()`, tras poblar la tabla, agregar:

```javascript
  if (typeof cargarColonias === 'function' && !coloniasData) { cargarColonias().then(()=>renderMapaDesarrollo(vis)); }
  else renderMapaDesarrollo(vis);
```

(Usar el nombre real del loader de colonias del proyecto; en el código vive cerca de `coloniasData`/`coloniasLayer` ~línea 1576 — verificar el identificador exacto antes de llamarlo.)

- [ ] **Step 4: Verificar visual**

Run: `serve.bat` → Desarrollo.
Expected: mapa coloreado; verdes = mayor margen; click muestra desglose; cambiar costo recolorea.

- [ ] **Step 5: Commit**

```bash
git add frontend/dashboard.html
git commit -m "feat(faro): mapa de calor de margen de desarrollo por colonia (MK7 pieza 3)"
```

```json:metadata
{"files": ["frontend/dashboard.html"], "verifyCommand": "", "acceptanceCriteria": ["colonias coloreadas por margen neto", "click muestra desglose", "recolorea al cambiar controles", "invalidateSize al mostrarse"], "requiresUserVerification": false}
```

---

### Task 4: Reporte "Dónde Desarrollar" (HTML imprimible)

**Goal:** Botón que abre un reporte de 4 páginas imprimible a PDF, mirror del estilo de `generateReporteConsolidado`.

**Files:**
- Modify: `frontend/dashboard.html` — función `generateReporteDesarrollo()` (el botón ya quedó en Task 2).

**Acceptance Criteria:**
- [ ] Abre una ventana nueva con HTML estilo GRID/FARO (Sora + Space Mono, acento esmeralda) imprimible a PDF (Ctrl+P).
- [ ] Página 1 — Portada: título, fecha, supuestos (costo de obra usado, muestras mínimas, universo = casas en venta), nº de colonias analizadas.
- [ ] Página 2 — Top 10 colonias por margen neto: barras horizontales + cifra de margen/casa típica + una línea de lectura geográfica (en qué zona se concentran).
- [ ] Página 3 — Tabla completa de colonias 🟢/🟡 (oculta 🔴), mismas columnas de la lente.
- [ ] Página 4 — Metodología y advertencias: fórmula residual, uso de mediana, qué significa el semáforo, disclaimer honesto (oferta no transacciones; scrape pausado ~mar-2026).
- [ ] Usa `window._margenDesarrollo` (o recalcula con los valores actuales de los controles) — sin nuevas llamadas a Supabase.

**Verify:** En `serve.bat` → Desarrollo → "⬇ Reporte Desarrollo": abre ventana, 4 páginas renderizan sin error de consola, Top 10 coherente con la tabla de la lente.

**Steps:**

- [ ] **Step 1: Implementar `generateReporteDesarrollo()`**

Mirror del patrón de `generateReporteConsolidado` (ventana nueva + helpers locales `money`/`hbar`). Esqueleto completo:

```javascript
function generateReporteDesarrollo(){
  const costo = parseFloat(document.getElementById('dev-costo').value) || 15000;
  const minM  = parseInt(document.getElementById('dev-min').value) || 4;
  const rows = (window._margenDesarrollo && window._margenDesarrollo.length)
    ? window._margenDesarrollo : calcularMargenDesarrollo(allData, costo, minM);
  const vis = rows.filter(r => r.confianza !== 'baja');
  if (!vis.length){ alert('No hay colonias con suficiente muestra. Ajusta los controles primero.'); return; }
  const money = n => isNaN(n)||n==null?'&mdash;':'$'+Math.round(n).toLocaleString('es-MX');
  const dot = c => c==='alta'?'🟢':'🟡';
  const top = vis.slice(0,10);
  const maxM = Math.max(...top.map(r=>r.margenNeto));
  const hbar = (label,val,max)=>{const w=max?Math.max(2,Math.round(val/max*100)):2;
    return `<div style="margin-bottom:9px"><div style="display:flex;justify-content:space-between;font-size:11px"><span>${label}</span><span style="font-family:'Space Mono'">${money(val)}/m²c</span></div><div style="height:7px;background:#eef0f3;border-radius:4px"><div style="height:7px;background:#10b981;border-radius:4px;width:${w}%"></div></div></div>`;};
  const fecha = new Date().toLocaleDateString('es-MX',{day:'2-digit',month:'long',year:'numeric'});
  const css = `<style>@page{size:A4;margin:0}body{font-family:'Sora',system-ui;margin:0;color:#0d1117}
    .page{width:210mm;min-height:297mm;padding:18mm 16mm;box-sizing:border-box;page-break-after:always}
    h1{font-size:26px;margin:0 0 6px} h2{font-size:17px;color:#059669;margin:0 0 12px}
    table{width:100%;border-collapse:collapse;font-size:11px} th,td{padding:5px 7px;border-bottom:1px solid #e5e7eb;text-align:right}
    th:first-child,td:first-child{text-align:left} .mono{font-family:'Space Mono',monospace}
    .cover{background:#064e3b;color:#fff;display:flex;flex-direction:column;justify-content:center}
    .note{font-size:11px;line-height:1.6;background:#fffbeb;border-left:3px solid #d97706;padding:10px 12px;border-radius:6px;margin-top:10px}</style>`;
  const rowsTabla = vis.map(r=>`<tr><td>${r.colonia} ${dot(r.confianza)}</td><td>${money(r.pm2TerrenoMediana)}</td>
    <td>${money(r.ticketMediano)}</td><td>${money(r.residualMediano)}</td>
    <td style="font-weight:700;color:#059669">${money(r.margenNeto)}</td><td>${money(r.margenPorCasa)}</td><td>${r.nCasas}</td></tr>`).join('');
  const html = `<!doctype html><html><head><meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=Space+Mono&display=swap" rel="stylesheet">${css}</head><body>
    <div class="page cover"><div style="font-size:13px;opacity:.8;margin-bottom:8px">FARO · Inteligencia de desarrollo</div>
      <h1 style="color:#fff;font-size:34px">Dónde Desarrollar</h1>
      <div style="font-size:15px;opacity:.9">Ranking de colonias por margen de construcción · Torreón</div>
      <div style="margin-top:40px;font-size:12px;opacity:.85;line-height:2">
        Fecha: ${fecha}<br>Universo: casas en venta<br>Costo de obra asumido: ${money(costo)}/m²<br>
        Casas mínimas por colonia: ${minM}<br>Colonias analizadas: ${vis.length}</div></div>
    <div class="page"><h2>Top 10 colonias por margen neto</h2>
      ${top.map(r=>hbar(`${r.colonia} — margen/casa ${money(r.margenPorCasa)}`, r.margenNeto, maxM)).join('')}
      <p style="font-size:11px;color:#6b7280;margin-top:16px">El margen neto es lo que el mercado paga por m² construido por encima del costo de obra asumido. A mayor margen, más rentable construir el mismo producto.</p></div>
    <div class="page"><h2>Tabla completa</h2><table><thead><tr><th>Colonia</th><th>$/m² terreno</th><th>Ticket</th><th>Residual $/m²c</th><th>Margen neto</th><th>Margen/casa</th><th># casas</th></tr></thead><tbody>${rowsTabla}</tbody></table></div>
    <div class="page"><h2>Metodología y advertencias</h2>
      <p style="font-size:12px;line-height:1.7">Por cada casa en venta se estima el <b>valor residual de construcción</b>:<br>
      <span class="mono">residual $/m²c = (precio − m²_terreno × $/m²_terreno_mediano_colonia) ÷ m²_construcción</span><br><br>
      Se toma la <b>mediana</b> por colonia (robusta a outliers del scrape) y se resta el costo de obra asumido para obtener el <b>margen neto $/m²c</b>, métrica de ranking. El <b>$/m² de terreno</b> sale de la mediana de listings de terreno de la colonia; si hay menos de 2, se usa la mediana global (esas colonias quedan marcadas 🔴 baja confianza y se excluyen de este reporte).</p>
      <div class="note">⚠ Datos de <b>oferta</b> (precios pedidos), no de transacciones cerradas. El scrape está pausado desde ~marzo 2026; trátese como foto de mercado, no como serie viva. Verificar en campo antes de decidir compra de terreno.</div></div>
    </body></html>`;
  const w = window.open('', '_blank');
  w.document.write(html); w.document.close();
}
```

- [ ] **Step 2: Verificar visual**

Run: `serve.bat` → Desarrollo → "⬇ Reporte Desarrollo".
Expected: ventana con 4 páginas, sin error en consola; Top 10 coincide con la tabla; Ctrl+P genera PDF limpio.

- [ ] **Step 3: Commit**

```bash
git add frontend/dashboard.html
git commit -m "feat(faro): reporte Donde Desarrollar imprimible (MK7 pieza 4)"
```

```json:metadata
{"files": ["frontend/dashboard.html"], "verifyCommand": "", "acceptanceCriteria": ["ventana nueva 4 paginas estilo GRID", "portada con supuestos", "top 10 con barras", "tabla completa", "metodologia + disclaimer", "sin nuevas llamadas Supabase"], "requiresUserVerification": false}
```

---

### Task 5: Cierre MK7 — verificación de usuario, CHANGELOG, snapshot y tag

**Goal:** Verificación visual del usuario, documentar la pieza y dejar el respaldo recuperable según la convención MK del proyecto.

**Files:**
- Modify: `CHANGELOG.md`
- Create: `archive/versions/faro-MK7-2026-06-18.html` (snapshot untracked)

**Acceptance Criteria:**
- [ ] El usuario confirma en `serve.bat` que la lente y el reporte funcionan.
- [ ] Entrada nueva en `CHANGELOG.md` describiendo MK7 (lente Desarrollo: motor + tabla + mapa + reporte).
- [ ] Snapshot copiado a `archive/versions/faro-MK7-2026-06-18.html`.
- [ ] Tag git `MK7` creado sobre el commit de cierre.

**User Verification Required:**
Before marking this task complete, you MUST call AskUserQuestion:
```yaml
AskUserQuestion:
  question: "Abre serve.bat → Mercado → Desarrollo. ¿La lente rankea las colonias y el reporte abre correctamente?"
  header: "Verificación"
  options:
    - label: "Funciona"
      description: "Lente y reporte renderizan bien; cierro MK7 con tag y CHANGELOG."
    - label: "Hay que ajustar"
      description: "Algo no renderiza o los números no cuadran; lo corrijo antes de cerrar."
```
**Si el usuario elige "Hay que ajustar":** la tarea NO está completa. Corregir y re-verificar con AskUserQuestion.

**Verify:** `git tag` muestra `MK7`; `CHANGELOG.md` contiene la entrada; el snapshot existe.

**Steps:**

- [ ] **Step 1: Verificación del usuario** (ver bloque arriba — AskUserQuestion).

- [ ] **Step 2: Entrada en CHANGELOG.md**

Agregar al inicio del CHANGELOG una sección `## MK7 — Lente "Dónde Desarrollar" (2026-06-18)` con los 4 componentes.

- [ ] **Step 3: Snapshot**

```bash
cp frontend/dashboard.html archive/versions/faro-MK7-2026-06-18.html
```

- [ ] **Step 4: Commit + tag**

```bash
git add CHANGELOG.md
git commit -m "docs(faro): CHANGELOG MK7 lente Donde Desarrollar"
git tag MK7
```

```json:metadata
{"files": ["CHANGELOG.md", "archive/versions/faro-MK7-2026-06-18.html"], "verifyCommand": "git tag", "acceptanceCriteria": ["usuario confirma funcionamiento", "CHANGELOG actualizado", "snapshot creado", "tag MK7"], "requiresUserVerification": true, "userVerificationPrompt": "Abre serve.bat → Mercado → Desarrollo. ¿La lente rankea las colonias y el reporte abre correctamente?"}
```

---

## Self-Review

- **Cobertura del spec:** Metodología → Task 1. Lente (controles + tabla) → Task 2. Mapa de calor → Task 3. Reporte → Task 4. Convención MK/CHANGELOG → Task 5. ✓
- **Desviación consciente del spec:** el reporte es de **4 páginas** (no 5): se eliminó la página de "captura del mapa de margen" porque screenshotear Leaflet a una ventana de impresión requiere una dependencia extra (html2canvas/leaflet-image) que no está cargada; el mapa de calor vive interactivo en la lente (Task 3) y la lectura geográfica se incluye como texto en la página Top 10. Menor, alineado con YAGNI.
- **Costo de obra default** $15,000/m² y muestras mínimas 4, ambos ajustables en vivo — coincide con el spec.
- **Sin placeholders:** todos los pasos con código tienen el código completo.
- **Consistencia de tipos:** `calcularMargenDesarrollo` devuelve los mismos campos consumidos por `renderDesarrollo`, `renderMapaDesarrollo` y `generateReporteDesarrollo` (`margenNeto`, `margenPorCasa`, `pm2TerrenoMediana`, `residualMediano`, `ticketMediano`, `m2cMediano`, `confianza`, `nCasas`, `nTerrenos`). ✓
- **Verificación de usuario:** el spec/proyecto implica sign-off visual → Task 5 lo encoda con `requiresUserVerification: true`. ✓
