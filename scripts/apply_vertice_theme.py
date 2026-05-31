"""
apply_vertice_theme.py
======================
Aplica el design system VERTICE-family a FARO dashboard:
  - Tokens CSS (cream/gold palette, Barlow Semi Condensed + Mulish + IBM Plex Mono)
  - Logo SVG con 4 opciones de marca
  - Modal de bienvenida (onboarding)
  - Letterhead PDF rediseñado
"""

import re, os

SRC  = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dashboard.html')
DEST = SRC
DOCS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'index.html')

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. FONTS ──────────────────────────────────────────────────────────────────
OLD_FONT = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap'
NEW_FONT = 'https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@400;500;600;700&family=Mulish:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap'

html = html.replace(OLD_FONT, NEW_FONT)
print('[OK] Fonts -> Barlow Semi Condensed + Mulish + IBM Plex Mono')

# ── 2. CSS ROOT TOKENS ────────────────────────────────────────────────────────
OLD_ROOT = """:root {
  /* FARO — AirDNA Light Mode */
  --bg:         oklch(98.2% 0.007 264);
  --surface:    oklch(99.8% 0.003 264);
  --surface2:   oklch(94.8% 0.013 264);
  --border:     oklch(87.5% 0.015 264);
  --text:       oklch(14.0% 0.015 264);
  --muted:      oklch(50.0% 0.018 264);
  --accent:     oklch(30.0% 0.270 264);
  --accent-dim: oklch(93.5% 0.032 264);
  --accent2:    oklch(46.0% 0.220 264);
  --accent3:    oklch(51.0% 0.220  25);
  --success:    oklch(50.0% 0.170 142);
  --warning:    oklch(65.0% 0.160  65);
  --font:       'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --mono:       'DM Mono', 'Cascadia Code', monospace;
  --radius:     8px;
  --radius-sm:  5px;
  --shadow-sm:  0 1px 3px oklch(14% 0.015 264 / 0.08), 0 1px 2px oklch(14% 0.015 264 / 0.04);
  --shadow:     0 4px 16px oklch(14% 0.015 264 / 0.10);
}"""

NEW_ROOT = """:root {
  /* FARO — VERTICE Family · Cream / Gold */
  --bg:         oklch(97.5% 0.008 72);
  --surface:    oklch(99.0% 0.004 72);
  --surface2:   oklch(93.8% 0.016 68);
  --border:     oklch(87.0% 0.018 68);
  --text:       oklch(12.5% 0.018 72);
  --muted:      oklch(52.0% 0.015 70);
  --accent:     #C8A24B;
  --accent-dim: oklch(94.0% 0.038 73);
  --accent2:    oklch(58.0% 0.110 73);
  --accent3:    oklch(51.0% 0.220  25);
  --success:    oklch(50.0% 0.170 142);
  --warning:    oklch(65.0% 0.160  65);
  --font:         'Mulish', system-ui, sans-serif;
  --font-display: 'Barlow Semi Condensed', system-ui, sans-serif;
  --mono:         'IBM Plex Mono', ui-monospace, monospace;
  --radius:     8px;
  --radius-sm:  5px;
  --shadow-sm:  0 1px 3px oklch(12% 0.018 72 / 0.07), 0 1px 2px oklch(12% 0.018 72 / 0.04);
  --shadow:     0 4px 16px oklch(12% 0.018 72 / 0.09);
}"""

html = html.replace(OLD_ROOT, NEW_ROOT)
print('[OK] CSS tokens -> cream/gold palette')

# ── 3. STATS BAR: add font-display to stat-value ─────────────────────────────
html = html.replace(
    '.stat-value{font-size:22px;font-weight:700;font-family:var(--mono);color:var(--text);letter-spacing:-.02em;font-variant-numeric:tabular-nums}',
    '.stat-value{font-size:22px;font-weight:700;font-family:var(--mono);color:var(--text);letter-spacing:-.02em;font-variant-numeric:tabular-nums;font-feature-settings:"tnum"}'
)

# ── 4. HEADER LOGO — 4 opciones de marca SVG ─────────────────────────────────
# Agrega .logo-mark SVG + picker de logos (almacenado en localStorage)
LOGO_OLD = '  <div class="logo">FARO <em>· Torreón</em></div>'
LOGO_NEW = """  <div class="logo" id="faro-logo" onclick="if(event.altKey)toggleLogoPicker()" title="Alt+clic para cambiar logo">
    <span class="logo-mark" id="logo-svg-container"></span>
    <span class="logo-word"><b>FARO</b> <em>· Torreón</em></span>
  </div>"""
html = html.replace(LOGO_OLD, LOGO_NEW)
print('[OK] Logo -> SVG mark + wordmark')

# ── 5. CSS: logo + eyebrow + onboarding + logo picker ────────────────────────
CSS_INSERT_AFTER = '.version-tag{background:var(--accent-dim);color:var(--accent);border:1px solid oklch(85% 0.055 264);padding:2px 7px;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:.04em;font-family:var(--mono)}'
CSS_NEW = CSS_INSERT_AFTER + """
/* Logo */
.logo{font-size:15px;font-weight:600;letter-spacing:-.01em;color:var(--text);display:flex;align-items:center;gap:10px;cursor:default}
.logo-mark{display:flex;align-items:center;color:var(--accent);flex-shrink:0;width:26px;height:26px}
.logo-word b{font-family:var(--font-display);font-weight:700;font-size:1.1rem;letter-spacing:.02em}
.logo-word em{font-style:normal;color:var(--muted);font-weight:400;font-size:12px;margin-left:2px}
/* Eyebrow utility */
.eyebrow{font-family:var(--mono);font-size:10px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:var(--accent)}
/* Logo picker */
.logo-picker{display:none;position:absolute;top:58px;left:16px;z-index:200;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;box-shadow:var(--shadow);gap:12px;flex-direction:column}
.logo-picker.open{display:flex}
.logo-picker-title{font-family:var(--mono);font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted)}
.logo-options{display:flex;gap:10px}
.logo-opt{width:52px;height:52px;border:1.5px solid var(--border);border-radius:8px;display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--muted);transition:border-color .15s,color .15s}
.logo-opt:hover,.logo-opt.active{border-color:var(--accent);color:var(--accent)}
.logo-opt svg{width:28px;height:28px}
/* Onboarding modal */
.onboarding-overlay{display:none;position:fixed;inset:0;background:oklch(12% 0.018 72 / 0.6);z-index:500;align-items:center;justify-content:center;backdrop-filter:blur(4px)}
.onboarding-overlay.open{display:flex}
.onboarding-box{background:var(--surface);border:1px solid var(--border);border-radius:14px;width:600px;max-width:92vw;max-height:88vh;overflow:hidden;box-shadow:0 24px 64px oklch(12% 0.018 72 / 0.18);display:flex;flex-direction:column}
.ob-header{padding:28px 32px 0;border-bottom:none}
.ob-eyebrow{font-family:var(--mono);font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:var(--accent);margin-bottom:10px}
.ob-title{font-family:var(--font-display);font-size:1.9rem;font-weight:700;letter-spacing:.01em;color:var(--text);line-height:1.05;margin-bottom:6px}
.ob-subtitle{font-size:13px;color:var(--muted);line-height:1.5}
.ob-rule{height:1px;background:linear-gradient(90deg,var(--accent) 0%,transparent 100%);opacity:.4;margin:20px 32px 0}
.ob-steps{padding:20px 32px;display:grid;grid-template-columns:1fr 1fr;gap:14px;flex:1}
.ob-step{display:flex;gap:12px;align-items:flex-start}
.ob-step-num{font-family:var(--mono);font-size:11px;color:var(--accent);font-weight:500;letter-spacing:.05em;flex-shrink:0;padding-top:1px}
.ob-step-title{font-family:var(--font-display);font-size:.95rem;font-weight:600;color:var(--text);margin-bottom:3px}
.ob-step-desc{font-size:12px;color:var(--muted);line-height:1.5}
.ob-footer{padding:16px 32px 24px;display:flex;align-items:center;justify-content:space-between;border-top:1px solid var(--border)}
.ob-footer-note{font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:.05em}
.ob-btn{background:var(--accent);color:#1a1000;border:none;padding:10px 28px;border-radius:7px;font-family:var(--font-display);font-size:.95rem;font-weight:700;letter-spacing:.04em;cursor:pointer;transition:opacity .15s}
.ob-btn:hover{opacity:.85}"""

html = html.replace(CSS_INSERT_AFTER, CSS_NEW)
print('[OK] CSS: logo styles + eyebrow + onboarding + logo picker')

# Remove old .logo rule that now duplicates
html = html.replace(
    '\n.logo{font-size:15px;font-weight:700;letter-spacing:-.03em;color:var(--text);display:flex;align-items:center;gap:8px}\n.logo em{font-style:normal;color:var(--muted);font-weight:400;font-size:13px}',
    ''
)

# ── 6. ONBOARDING MODAL HTML ──────────────────────────────────────────────────
ONBOARD_HTML = """
<!-- ONBOARDING MODAL -->
<div class="onboarding-overlay" id="onboarding-overlay">
  <div class="onboarding-box">
    <div class="ob-header">
      <div class="ob-eyebrow">Bienvenido a FARO</div>
      <div class="ob-title">Inteligencia de mercado<br>para decisiones de tierra</div>
      <div class="ob-subtitle">Plataforma de analítica inmobiliaria para Torreón &mdash; scraping semanal, demographics INEGI y reportes de zona.</div>
    </div>
    <div class="ob-rule"></div>
    <div class="ob-steps">
      <div class="ob-step">
        <div class="ob-step-num">01</div>
        <div><div class="ob-step-title">Tab Mercado &rarr; Lista</div><div class="ob-step-desc">Todos los listings activos con filtros por tipo, operación, colonia y precio. Exporta CSV o ve el resumen por colonia.</div></div>
      </div>
      <div class="ob-step">
        <div class="ob-step-num">02</div>
        <div><div class="ob-step-title">Tab Mercado &rarr; Mapa</div><div class="ob-step-desc">Hexágonos H3 con precio mediano por zona. Detecta colonias premium vs emergentes visualmente.</div></div>
      </div>
      <div class="ob-step">
        <div class="ob-step-num">03</div>
        <div><div class="ob-step-title">Tab Mercado &rarr; Validación</div><div class="ob-step-desc">Listings con anomalías detectadas automáticamente. Aprueba, marca error, edita precio o reubica el pin GPS.</div></div>
      </div>
      <div class="ob-step">
        <div class="ob-step-num">04</div>
        <div><div class="ob-step-title">Tab Demografía</div><div class="ob-step-desc">Clic en el mapa para analizar una zona de influencia: score 1-10, NSE AMAI, crecimiento 2010-2020, buyer persona y reporte PDF.</div></div>
      </div>
    </div>
    <div class="ob-footer">
      <span class="ob-footer-note">FARO &middot; COEZA Consulting &middot; Datos: INEGI 2020 &middot; Scrape semanal</span>
      <button class="ob-btn" onclick="cerrarOnboarding()">Comenzar &rarr;</button>
    </div>
  </div>
</div>

"""

# Insert before <div id="app">
html = html.replace('<div id="app">', ONBOARD_HTML + '<div id="app">')
print('[OK] Onboarding modal HTML insertado')

# ── 7. ONBOARDING + LOGO JS ───────────────────────────────────────────────────
LOGO_SVGS = {
    'sector': '<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M7 25 L7 9 A16 16 0 0 1 23 25 Z"/></svg>',
    'meridian': '<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><line x1="16" y1="3" x2="16" y2="12"/><line x1="16" y1="20" x2="16" y2="29"/><line x1="3" y1="16" x2="12" y2="16"/><line x1="20" y1="16" x2="29" y2="16"/><circle cx="16" cy="16" r="3.5" fill="currentColor" stroke="none"/></svg>',
    'beacon': '<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-linecap="round"><circle cx="16" cy="7" r="3" fill="currentColor" stroke="none"/><line x1="16" y1="10" x2="16" y2="28" stroke-width="1.8"/><line x1="16" y1="17" x2="7" y2="28" stroke-width="1.2" opacity="0.45"/><line x1="16" y1="17" x2="25" y2="28" stroke-width="1.2" opacity="0.45"/></svg>',
    'pivot': '<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="9.5" y="9.5" width="13" height="13" transform="rotate(45 16 16)"/><circle cx="16" cy="16" r="2.2" fill="currentColor" stroke="none"/></svg>',
}

JS_LOGO_ONBOARD = """
// ── LOGO SELECTOR ─────────────────────────────────────────────────────────────
const LOGO_SVGS = """ + str(LOGO_SVGS).replace("'", '"') + """;
const LOGO_NAMES = { sector: 'Sector', meridian: 'Meridian', beacon: 'Beacon', pivot: 'Pivot' };

function getActiveLogo() {
  return localStorage.getItem('faro_logo') || 'beacon';
}

function setLogo(key) {
  localStorage.setItem('faro_logo', key);
  document.getElementById('logo-svg-container').innerHTML = LOGO_SVGS[key];
  document.querySelectorAll('.logo-opt').forEach(el => {
    el.classList.toggle('active', el.dataset.logo === key);
  });
}

function toggleLogoPicker() {
  const picker = document.getElementById('logo-picker');
  if (!picker) return;
  picker.classList.toggle('open');
}

function renderLogoPicker() {
  const current = getActiveLogo();
  const pickerHTML = `<div class="logo-picker" id="logo-picker">
    <div class="logo-picker-title">Marca FARO</div>
    <div class="logo-options">
      ${Object.entries(LOGO_SVGS).map(([k,svg]) =>
        `<div class="logo-opt ${k===current?'active':''}" data-logo="${k}" title="${LOGO_NAMES[k]||k}" onclick="setLogo('${k}');toggleLogoPicker()">${svg}</div>`
      ).join('')}
    </div>
    <div style="font-size:10px;color:var(--muted);font-family:var(--mono);margin-top:2px">Alt+clic en el logo para cambiar</div>
  </div>`;
  document.querySelector('header').insertAdjacentHTML('beforeend', pickerHTML);
}

// ── ONBOARDING ─────────────────────────────────────────────────────────────────
function cerrarOnboarding() {
  document.getElementById('onboarding-overlay').classList.remove('open');
  localStorage.setItem('faro_onboarding_done', '1');
}

function initOnboarding() {
  const done = localStorage.getItem('faro_onboarding_done');
  if (!done) {
    document.getElementById('onboarding-overlay').classList.add('open');
  }
}

// Init logo + onboarding
document.addEventListener('DOMContentLoaded', () => {
  renderLogoPicker();
  setLogo(getActiveLogo());
  initOnboarding();
  // Close picker on outside click
  document.addEventListener('click', e => {
    const picker = document.getElementById('logo-picker');
    if (picker && !picker.contains(e.target) && !document.getElementById('faro-logo').contains(e.target)) {
      picker.classList.remove('open');
    }
  });
});
"""

# Insert before the closing </script> of the main script block
# Find a safe anchor near the end of the JS
ANCHOR_JS = '// Init\nif (SUPABASE_URL && SUPABASE_KEY) {'
html = html.replace(ANCHOR_JS, JS_LOGO_ONBOARD + '\n' + ANCHOR_JS)
print('[OK] JS: logo selector + onboarding logic')

# ── 8. PDF REPORT LETTERHEAD ──────────────────────────────────────────────────
# Replace the logo-mark in the PDF report pages
OLD_PDF_LOGO = '      <div class="logo-mark">FARO <em>&middot; COEZA</em></div>'
NEW_PDF_LOGO = """      <div class="logo-mark" style="display:flex;align-items:center;gap:10px">
        <svg viewBox="0 0 32 32" width="22" height="22" fill="none" stroke="#C8A24B" stroke-linecap="round" style="flex-shrink:0">
          <circle cx="16" cy="7" r="3" fill="#C8A24B" stroke="none"/>
          <line x1="16" y1="10" x2="16" y2="28" stroke-width="1.8"/>
          <line x1="16" y1="17" x2="7" y2="28" stroke-width="1.2" opacity="0.5"/>
          <line x1="16" y1="17" x2="25" y2="28" stroke-width="1.2" opacity="0.5"/>
        </svg>
        <span style="font-family:'Barlow Semi Condensed',system-ui,sans-serif;font-weight:700;font-size:.95rem;letter-spacing:.04em;color:#1a1000">FARO <span style="color:#C8A24B;font-weight:400;font-size:.72rem;letter-spacing:.18em;font-family:'IBM Plex Mono',monospace;vertical-align:middle">&middot; COEZA</span></span>
      </div>"""

html = html.replace(OLD_PDF_LOGO, NEW_PDF_LOGO)
count_pdf = html.count('logo-mark')
print(f'[OK] PDF letterhead: beacon SVG + VERTICE typography ({count_pdf} ocurrencias)')

# ── 9. PDF report cover title font ────────────────────────────────────────────
# Update PDF <style> font stack to include Barlow Semi Condensed
OLD_PDF_FONT = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');"
NEW_PDF_FONT = "@import url('https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@400;600;700&family=Mulish:wght@300;400;600&family=IBM+Plex+Mono:wght@400;500&display=swap');"

if OLD_PDF_FONT in html:
    html = html.replace(OLD_PDF_FONT, NEW_PDF_FONT)
    print('[OK] PDF font import -> VERTICE fonts')
else:
    print('[SKIP] PDF font import not found (puede que ya este actualizado)')

# ── 10. WRITE OUTPUT ──────────────────────────────────────────────────────────
for path in [DEST, DOCS]:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    size_kb = os.path.getsize(path) / 1024
    print(f'[OK] Written: {os.path.basename(path)} ({size_kb:.0f} KB)')

print('\nDone. Tokens CSS, logo SVG, onboarding y PDF letterhead aplicados.')
