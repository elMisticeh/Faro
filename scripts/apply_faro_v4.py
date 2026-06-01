"""
apply_faro_v4.py — FARO v4
  1. Acento azul navy (reemplaza gold)
  2. 4 logos nuevos completamente diferentes
  3. Reporte de Mercado: modal de filtros + fetch directo a Supabase
"""
import os, re

SRC  = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dashboard.html')
DOCS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'index.html')

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# 1. ACENTO: gold → blue navy
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    """  --accent:     #C8A24B;
  --accent-dim: oklch(94.0% 0.038 73);
  --accent2:    oklch(58.0% 0.110 73);""",
    """  --accent:     oklch(33% 0.21 243);
  --accent-dim: oklch(94% 0.022 243);
  --accent2:    oklch(48% 0.18 243);"""
)
# Corregir version-tag border que tenia el color azul hardcodeado del tema viejo
html = html.replace(
    'border:1px solid oklch(85% 0.055 264)',
    'border:1px solid oklch(88% 0.035 243)'
)
# Boton mercado: quitar color gold hardcodeado
html = html.replace(
    'style="margin-top:6px;background:oklch(67% .12 73);color:#1a1000"',
    'style="margin-top:6px"'
)
print('[OK] Acento: gold -> blue navy oklch(33% 0.21 243)')

# ─────────────────────────────────────────────────────────────────────────────
# 2. LOGOS — 4 conceptos nuevos
# ─────────────────────────────────────────────────────────────────────────────
OLD_LOGOS = """const LOGO_SVGS = {
  sector:   `<svg viewBox='0 0 32 32' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round'><path d='M7 25 L7 9 A16 16 0 0 1 23 25 Z'/></svg>`,
  meridian: `<svg viewBox='0 0 32 32' fill='none' stroke='currentColor' stroke-width='1.6' stroke-linecap='round'><line x1='16' y1='3' x2='16' y2='12'/><line x1='16' y1='20' x2='16' y2='29'/><line x1='3' y1='16' x2='12' y2='16'/><line x1='20' y1='16' x2='29' y2='16'/><circle cx='16' cy='16' r='3.5' fill='currentColor' stroke='none'/></svg>`,
  beacon:   `<svg viewBox='0 0 32 32' fill='none' stroke='currentColor' stroke-linecap='round'><circle cx='16' cy='7' r='3' fill='currentColor' stroke='none'/><line x1='16' y1='10' x2='16' y2='28' stroke-width='1.8'/><line x1='16' y1='17' x2='7' y2='28' stroke-width='1.2' opacity='0.45'/><line x1='16' y1='17' x2='25' y2='28' stroke-width='1.2' opacity='0.45'/></svg>`,
  pivot:    `<svg viewBox='0 0 32 32' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><rect x='9.5' y='9.5' width='13' height='13' transform='rotate(45 16 16)'/><circle cx='16' cy='16' r='2.2' fill='currentColor' stroke='none'/></svg>`,
};"""

NEW_LOGOS = """const LOGO_SVGS = {
  bars:     `<svg viewBox='0 0 32 32' fill='currentColor'><rect x='4'  y='18' width='6' height='10' rx='1'/><rect x='13' y='10' width='6' height='18' rx='1'/><rect x='22' y='4'  width='6' height='24' rx='1'/></svg>`,
  reticle:  `<svg viewBox='0 0 32 32' fill='none' stroke='currentColor' stroke-width='1.6' stroke-linecap='round'><rect x='8' y='8' width='16' height='16' rx='1'/><line x1='16' y1='3' x2='16' y2='7'/><line x1='16' y1='25' x2='16' y2='29'/><line x1='3' y1='16' x2='7' y2='16'/><line x1='25' y1='16' x2='29' y2='16'/><circle cx='16' cy='16' r='2' fill='currentColor' stroke='none'/></svg>`,
  fmark:    `<svg viewBox='0 0 32 32' fill='currentColor'><rect x='6' y='5' width='20' height='4' rx='1'/><rect x='6' y='5' width='4' height='22' rx='1'/><rect x='6' y='15' width='14' height='3.5' rx='1'/></svg>`,
  wave:     `<svg viewBox='0 0 32 32' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='3,22 9,10 15,18 21,8 27,14'/><circle cx='27' cy='14' r='2' fill='currentColor' stroke='none'/></svg>`,
};"""

html = html.replace(OLD_LOGOS, NEW_LOGOS)
# Update LOGO_NAMES
html = html.replace(
    "const LOGO_NAMES = { sector: 'Sector', meridian: 'Meridian', beacon: 'Beacon', pivot: 'Pivot' };",
    "const LOGO_NAMES = { bars: 'Barras', reticle: 'Reticula', fmark: 'F-Mark', wave: 'Onda' };"
)
# Default logo
html = html.replace(
    "return localStorage.getItem('faro_logo') || 'beacon';",
    "return localStorage.getItem('faro_logo') || 'bars';"
)
# Update PDF letterhead SVG (keep inline beacon but update color)
print('[OK] Logos: bars / reticula / F-mark / onda')

# ─────────────────────────────────────────────────────────────────────────────
# 3. MARKET REPORT — modal de filtros + fetch directo Supabase
# ─────────────────────────────────────────────────────────────────────────────

# 3a. Cambiar botón Mercado → abrirFiltrosMercado()
html = html.replace(
    'onclick="generateReporteMercado()" title="Reporte de mercado inmobiliario PDF"',
    'onclick="abrirFiltrosMercado()" title="Reporte de mercado inmobiliario PDF"'
)

# 3b. Agregar CSS del modal de filtros (después del CSS de onboarding)
FILTER_CSS = """
/* Market filter modal */
.mf-overlay{display:none;position:fixed;inset:0;background:oklch(12% 0.018 72 / 0.55);z-index:400;align-items:center;justify-content:center;backdrop-filter:blur(3px)}
.mf-overlay.open{display:flex}
.mf-box{background:var(--surface);border:1px solid var(--border);border-radius:12px;width:480px;max-width:92vw;box-shadow:var(--shadow);overflow:hidden}
.mf-header{padding:20px 24px 16px;border-bottom:1px solid var(--border)}
.mf-title{font-family:var(--font-display);font-size:1.15rem;font-weight:700;color:var(--text);margin-bottom:3px}
.mf-sub{font-size:12px;color:var(--muted)}
.mf-body{padding:20px 24px}
.mf-label{font-family:var(--mono);font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin-bottom:10px;display:block}
.mf-chips{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:18px}
.mf-chip{padding:5px 13px;border:1.5px solid var(--border);border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;color:var(--muted);transition:all .12s;background:var(--surface2);font-family:var(--font)}
.mf-chip.active{border-color:var(--accent);color:var(--accent);background:var(--accent-dim)}
.mf-radio{display:flex;gap:8px;margin-bottom:18px}
.mf-footer{padding:14px 24px;border-top:1px solid var(--border);display:flex;gap:10px;justify-content:flex-end}
#mf-status{font-family:var(--mono);font-size:11px;color:var(--muted);align-self:center;flex:1}"""

html = html.replace('.ob-btn:hover{opacity:.85}', '.ob-btn:hover{opacity:.85}' + FILTER_CSS)
print('[OK] CSS: modal de filtros de mercado')

# 3c. HTML del modal de filtros (antes del PIN MODAL)
FILTER_MODAL_HTML = """
<!-- MARKET FILTER MODAL -->
<div class="mf-overlay" id="mf-overlay">
  <div class="mf-box">
    <div class="mf-header">
      <div class="mf-title">Reporte de Mercado</div>
      <div class="mf-sub" id="mf-zone-desc">Zona seleccionada en Demografía</div>
    </div>
    <div class="mf-body">
      <span class="mf-label">Tipo de inmueble</span>
      <div class="mf-chips" id="mf-tipos">
        <div class="mf-chip active" data-val="todos">Todos</div>
        <div class="mf-chip" data-val="terreno_habitacional">Terreno Hab.</div>
        <div class="mf-chip" data-val="terreno_comercial">Terreno Com.</div>
        <div class="mf-chip" data-val="casa">Casa</div>
        <div class="mf-chip" data-val="departamento">Depto</div>
        <div class="mf-chip" data-val="local_comercial">Local Com.</div>
      </div>
      <span class="mf-label">Tipo de operación</span>
      <div class="mf-radio" id="mf-ops">
        <div class="mf-chip active" data-val="todos">Venta y Renta</div>
        <div class="mf-chip" data-val="venta">Solo Venta</div>
        <div class="mf-chip" data-val="renta">Solo Renta</div>
      </div>
    </div>
    <div class="mf-footer">
      <span id="mf-status"></span>
      <button class="btn secondary" onclick="cerrarFiltrosMercado()">Cancelar</button>
      <button class="btn" id="mf-btn-gen" onclick="fetchYGenerarReporte()">Generar Reporte</button>
    </div>
  </div>
</div>

"""

html = html.replace('<!-- PIN RELOCATION MODAL -->', FILTER_MODAL_HTML + '<!-- PIN RELOCATION MODAL -->')
print('[OK] HTML: modal de filtros')

# 3d. JS: abrirFiltrosMercado + fetchYGenerarReporte
# Inserta ANTES de "function generateReporteMercado"
FILTER_JS = """
// ── MARKET REPORT FILTERS ─────────────────────────────────────────────────────
function abrirFiltrosMercado() {
  const CENTER = window._lastDemoCenter;
  const RAD    = window._lastDemoRadius || 2;
  const title  = window._lastDemoTitle  || 'Zona';
  if (!CENTER) { alert('Primero selecciona una zona en la tab Demografía.'); return; }
  document.getElementById('mf-zone-desc').textContent = title + ' · Radio ' + RAD + ' km';
  document.getElementById('mf-status').textContent = '';
  document.getElementById('mf-btn-gen').disabled = false;
  document.getElementById('mf-btn-gen').textContent = 'Generar Reporte';
  document.getElementById('mf-overlay').classList.add('open');
}

function cerrarFiltrosMercado() {
  document.getElementById('mf-overlay').classList.remove('open');
}

// Chip toggle — solo un active por grupo (excepto tipos que puede ser multi)
document.addEventListener('click', e => {
  const chip = e.target.closest('.mf-chip');
  if (!chip) return;
  const group = chip.parentElement;
  if (group.id === 'mf-tipos') {
    if (chip.dataset.val === 'todos') {
      group.querySelectorAll('.mf-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
    } else {
      group.querySelector('[data-val="todos"]').classList.remove('active');
      chip.classList.toggle('active');
      if (!group.querySelector('.mf-chip.active')) chip.classList.add('active');
    }
  } else {
    group.querySelectorAll('.mf-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
  }
});

async function fetchYGenerarReporte() {
  const CENTER = window._lastDemoCenter;
  const RAD    = window._lastDemoRadius || 2;
  const title  = window._lastDemoTitle  || 'Zona de Influencia';
  const sub    = window._lastDemoSubtitle || '';
  const btn    = document.getElementById('mf-btn-gen');
  const status = document.getElementById('mf-status');

  // Leer filtros
  const tiposActivos = [...document.querySelectorAll('#mf-tipos .mf-chip.active')].map(c => c.dataset.val);
  const opActiva     = document.querySelector('#mf-ops .mf-chip.active')?.dataset.val || 'todos';
  const todostipos   = tiposActivos.includes('todos');

  if (!SUPABASE_URL || !SUPABASE_KEY) {
    status.textContent = 'Configura credenciales Supabase primero (boton Config).';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Cargando...';
  status.textContent = 'Consultando Supabase...';

  try {
    // Bbox ligeramente mayor al radio para reducir registros a filtrar
    const delta = (RAD + 1) / 111;
    let url = `${SUPABASE_URL}/rest/v1/listings?select=id,precio_mxn,m2_terreno,m2_construccion,precio_x_m2_terreno,precio_x_m2_construccion,tipo_inmueble,tipo_operacion,pagina_fuente,colonia,lat,lng,historial_precio,es_oportunidad,pct_vs_colonia,descripcion,link_publicacion&activo=eq.true&lat=gte.${CENTER.lat - delta}&lat=lte.${CENTER.lat + delta}&lng=gte.${CENTER.lng - delta}&lng=lte.${CENTER.lng + delta}&limit=1000`;
    const r = await fetch(url, { headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}` }});
    if (!r.ok) throw new Error('Error Supabase: ' + r.status);
    let data = await r.json();

    // Filtrar por radio exacto
    function distKm(la1,lo1,la2,lo2){const R=6371,dLa=(la2-la1)*Math.PI/180,dLo=(lo2-lo1)*Math.PI/180;const a=Math.sin(dLa/2)**2+Math.cos(la1*Math.PI/180)*Math.cos(la2*Math.PI/180)*Math.sin(dLo/2)**2;return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));}
    data = data.filter(d => d.lat && d.lng && distKm(CENTER.lat, CENTER.lng, +d.lat, +d.lng) <= RAD);

    // Filtrar por tipo
    if (!todostipos) {
      data = data.filter(d => tiposActivos.some(t => (d.tipo_inmueble || '').startsWith(t.replace('_habitacional','').replace('_comercial','')) || d.tipo_inmueble === t));
    }
    // Filtrar por operación
    if (opActiva !== 'todos') data = data.filter(d => d.tipo_operacion === opActiva);

    if (data.length < 2) {
      status.textContent = `Solo ${data.length} listing(s) con esos filtros. Amplía el radio o cambia los filtros.`;
      btn.disabled = false; btn.textContent = 'Generar Reporte';
      return;
    }

    status.textContent = `${data.length} listings encontrados.`;
    cerrarFiltrosMercado();
    // Guardar en allData para que esté disponible si el usuario va a Mercado
    if (!window.allData || !allData.length) window.allData = data;
    generateReporteMercado(data, title, sub + ' · Radio ' + RAD + 'km');

  } catch(e) {
    status.textContent = 'Error: ' + e.message;
    btn.disabled = false; btn.textContent = 'Generar Reporte';
  }
}

"""

# Cambiar firma de generateReporteMercado para aceptar datos como parámetro
html = html.replace(
    'function generateReporteMercado() {\n  const CENTER = window._lastDemoCenter;\n  const RAD    = window._lastDemoRadius || 2;\n  const title  = window._lastDemoTitle  || \'Zona de Influencia\';\n  const sub    = window._lastDemoSubtitle || \'\';\n\n  if (!CENTER) { alert(\'Selecciona una zona en Demografía primero.\'); return; }\n  if (!(window.allData && allData.length)) { alert(\'Datos de mercado no cargados. Ve a la tab Mercado primero.\'); return; }\n\n  // ── Helpers ────────────────────────────────────────────────────────────────\n  function distKm(la1,lo1,la2,lo2){\n    const R=6371,dLa=(la2-la1)*Math.PI/180,dLo=(lo2-lo1)*Math.PI/180;\n    const a=Math.sin(dLa/2)**2+Math.cos(la1*Math.PI/180)*Math.cos(la2*Math.PI/180)*Math.sin(dLo/2)**2;\n    return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));\n  }\n  const fmt  = (n,d=0) => isNaN(n)||n===null ? \'—\' : (+n).toLocaleString(\'es-MX\',{maximumFractionDigits:d,minimumFractionDigits:d});\n  const fmtP = n => isNaN(n)||n===null ? \'—\' : \'$\'+fmt(n)+\' MXN\';\n  const sign = n => (n>=0?\'+\':\'\')+fmt(n,1)+\'%\';\n  const mediana = arr => { if(!arr.length) return null; const s=[...arr].sort((a,b)=>a-b); return s[Math.floor(s.length/2)]; };\n  const pct  = (arr,p) => { if(!arr.length) return null; const s=[...arr].sort((a,b)=>a-b); return s[Math.max(0,Math.floor(s.length*p)-1)]; };\n  const today = new Date().toLocaleDateString(\'es-MX\',{year:\'numeric\',month:\'long\',day:\'numeric\'});\n\n  // ── Filter listings in zone ────────────────────────────────────────────────\n  const zona = allData.filter(d => d.activo && d.lat && d.lng &&\n    distKm(CENTER.lat, CENTER.lng, +d.lat, +d.lng) <= RAD);\n\n  if (zona.length < 3) {\n    alert(\'Pocos listings en esta zona (\' + zona.length + \'). Amplia el radio o selecciona otra area.\');\n    return;\n  }',
    'function generateReporteMercado(zona, title, sub) {\n  // zona, title, sub vienen de fetchYGenerarReporte()\n  if (!zona || zona.length < 2) { alert(\'Sin datos suficientes para el reporte.\'); return; }\n  title = title || window._lastDemoTitle || \'Zona de Influencia\';\n  sub   = sub   || window._lastDemoSubtitle || \'\';\n\n  // ── Helpers ────────────────────────────────────────────────────────────────\n  const fmt  = (n,d=0) => isNaN(n)||n===null ? \'—\' : (+n).toLocaleString(\'es-MX\',{maximumFractionDigits:d,minimumFractionDigits:d});\n  const fmtP = n => isNaN(n)||n===null ? \'—\' : \'$\'+fmt(n)+\' MXN\';\n  const sign = n => (n>=0?\'+\':\'\')+fmt(n,1)+\'%\';\n  const mediana = arr => { if(!arr.length) return null; const s=[...arr].sort((a,b)=>a-b); return s[Math.floor(s.length/2)]; };\n  const pct  = (arr,p) => { if(!arr.length) return null; const s=[...arr].sort((a,b)=>a-b); return s[Math.max(0,Math.floor(s.length*p)-1)]; };\n  const today = new Date().toLocaleDateString(\'es-MX\',{year:\'numeric\',month:\'long\',day:\'numeric\'});'
)

html = html.replace('\nfunction generateReporteMercado(zona, title, sub) {', FILTER_JS + '\nfunction generateReporteMercado(zona, title, sub) {')
print('[OK] JS: abrirFiltrosMercado + fetchYGenerarReporte + firma nueva')

# ─────────────────────────────────────────────────────────────────────────────
# 4. PDF report: actualizar colores gold → blue
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace("background:linear-gradient(135deg,#1a1000 0%,#2d2010 60%,#3d2e14 100%)", "background:linear-gradient(135deg,#0a0f1e 0%,#0d1830 60%,#112040 100%)")
html = html.replace("border:1px solid rgba(200,162,75,.18)", "border:1px solid rgba(60,120,210,.18)")
html = html.replace("border:1px solid rgba(200,162,75,.12)", "border:1px solid rgba(60,120,210,.12)")
# Gold accent en PDF → blue
html = html.replace("color:#C8A24B;letter-spacing:.22em;text-transform:uppercase", "color:#3c78d2;letter-spacing:.22em;text-transform:uppercase")
html = html.replace("--accent:#C8A24B", "--accent:#2857b8")
html = html.replace("stroke='#C8A24B'", "stroke='#3c78d2'")
html = html.replace("fill='#C8A24B'", "fill='#3c78d2'")
html = html.replace("color:#C8A24B", "color:#3c78d2")
html = html.replace("background:#C8A24B", "background:#3c78d2")
html = html.replace("border-left:3px solid #C8A24B", "border-left:3px solid #3c78d2")
html = html.replace("border-left:2px solid #C8A24B", "border-left:2px solid #3c78d2")
html = html.replace("background:linear-gradient(90deg,#C8A24B 0%", "background:linear-gradient(90deg,#3c78d2 0%")
html = html.replace("color:#a0936a", "color:#8a96b0")
html = html.replace("#e8dfc8", "#dce3f0")
html = html.replace("#faf7f0", "#f4f6fb")
html = html.replace("#f0e8d4", "#e8edf8")
html = html.replace("#fff9f2", "#f8faff")
html = html.replace("background:#faf7f0", "background:#f4f6fb")
html = html.replace("font-size:.9rem;font-weight:700;color:#1a1000", "font-size:.9rem;font-weight:700;color:#0a1628")
print('[OK] PDF report: palette cream/gold -> cream/blue')

# ─────────────────────────────────────────────────────────────────────────────
# 5. WRITE
# ─────────────────────────────────────────────────────────────────────────────
for path, name in [(SRC, 'dashboard.html'), (DOCS, 'index.html')]:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    size_kb = os.path.getsize(path) / 1024
    print(f'[OK] Written: {name} ({size_kb:.0f} KB)')

print('\nFARO v4 listo.')
