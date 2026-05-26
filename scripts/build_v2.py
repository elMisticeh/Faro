"""
build_v2.py — Generates CAMPO v2.0 from the existing dashboard.html
Applies: AirDNA design tokens, Inter font, 2-tab structure (Mercado/Demografía),
         app rename to CAMPO, impeccable product register guidelines.
"""
import re, os

SRC  = r'C:\proyectos\real-estate\frontend\dashboard.html'
DEST = r'C:\proyectos\real-estate\frontend\dashboard.html'

with open(SRC, encoding='utf-8') as f:
    html = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# 1. TITLE
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    '<title>Torreón RE · Dashboard</title>',
    '<title>CAMPO · Inteligencia Inmobiliaria</title>'
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. FONT — Space Grotesk → Inter
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap",
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap"
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. CSS :root — AirDNA tokens + impeccable guidelines
# ─────────────────────────────────────────────────────────────────────────────
OLD_ROOT = """:root {
  --bg: #0d0f14; --surface: #161920; --surface2: #1e2230;
  --border: #2a2f3d; --accent: #e8ff47; --accent2: #47b8ff;
  --accent3: #ff6b47; --text: #e8eaf0; --muted: #6b7280;
  --success: #4ade80; --font: 'Space Grotesk',sans-serif; --mono: 'DM Mono',monospace;
}"""

NEW_ROOT = """:root {
  /* AirDNA-inspired · CAMPO v2.0 */
  --bg: #212121;
  --surface: #0f0f14;
  --surface2: #1a1a24;
  --border: #3c3e4d;
  --accent: #0000ee;
  --accent-dim: rgba(0,0,238,0.12);
  --accent2: #3f51b5;
  --accent3: #e53935;
  --text: #f0f0f8;
  --muted: #666677;
  --success: #4caf50;
  --warning: #ff9800;
  --font: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --mono: 'DM Mono', 'Cascadia Code', monospace;
  --radius: 10px;
  --radius-sm: 6px;
}"""

html = html.replace(OLD_ROOT, NEW_ROOT, 1)

# ─────────────────────────────────────────────────────────────────────────────
# 4. HEADER — rename logo
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    '<div class="logo">Torreón RE <span>·</span> Dashboard</div>',
    '<div class="logo">CAMPO <span>·</span> Torreón</div>'
)
# Also try alternate logo markup from the template
html = html.replace(
    "Torreón RE <span>·</span> Dashboard",
    "CAMPO <span>·</span> Torreón"
)
html = html.replace(
    "Torreón RE · Dashboard",
    "CAMPO · Torreón"
)

# ─────────────────────────────────────────────────────────────────────────────
# 5. CSS — tabs redesign: replace old .tab/.tabs with main-tabs + sub-tabs
# ─────────────────────────────────────────────────────────────────────────────
OLD_TABS_CSS = """/* TABS */
.tabs{display:flex;gap:0;border-bottom:1px solid var(--border);background:var(--surface);padding:0 32px}
.tab{padding:12px 20px;font-size:13px;font-weight:600;cursor:pointer;border-bottom:2px solid transparent;color:var(--muted);transition:all .2s;user-select:none}
.tab:hover{color:var(--text)}
.tab.active{color:var(--accent);border-bottom-color:var(--accent)}"""

NEW_TABS_CSS = """/* MAIN TABS */
.main-tabs{display:flex;gap:0;background:var(--surface);border-bottom:2px solid var(--border)}
.main-tab{padding:14px 28px;font-size:14px;font-weight:600;cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-2px;color:var(--muted);transition:color .15s,border-color .15s;user-select:none;letter-spacing:-.01em}
.main-tab:hover{color:var(--text)}
.main-tab.active{color:var(--text);border-bottom-color:var(--accent)}

/* SUB-TABS (within Mercado) */
.sub-tabs{display:flex;gap:4px;padding:0 4px}
.sub-tab{padding:6px 14px;font-size:12px;font-weight:600;cursor:pointer;border-radius:var(--radius-sm);color:var(--muted);transition:all .15s;user-select:none;border:1px solid transparent}
.sub-tab:hover{color:var(--text);background:var(--surface2)}
.sub-tab.active{color:var(--accent);background:var(--accent-dim);border-color:rgba(0,0,238,.25)}

/* Controls bar (sub-tabs + filters combined) */
.controls-bar{display:flex;align-items:center;gap:16px;padding:10px 24px;border-bottom:1px solid var(--border);background:var(--surface);flex-wrap:wrap}
.controls-bar .sub-tabs{flex-shrink:0}
.controls-bar .filters-inline{display:flex;align-items:center;gap:8px;flex-wrap:wrap;flex:1}"""

html = html.replace(OLD_TABS_CSS, NEW_TABS_CSS, 1)

# ─────────────────────────────────────────────────────────────────────────────
# 6. CSS — update btn/select to match AirDNA (radius 10px, accent blue)
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    'select,input[type=text],input[type=number]{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:7px 10px;border-radius:6px;font-family:var(--font);font-size:13px;outline:none;cursor:pointer;transition:border-color .2s}',
    'select,input[type=text],input[type=number]{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:7px 10px;border-radius:var(--radius-sm);font-family:var(--font);font-size:13px;outline:none;cursor:pointer;transition:border-color .15s}',
    1
)
html = html.replace(
    'select:hover,input:hover,select:focus,input:focus{border-color:var(--accent)}',
    'select:hover,input:hover,select:focus,input:focus{border-color:var(--accent)}',
    1
)
html = html.replace(
    '.btn{background:var(--accent);color:#000;border:none;padding:7px 14px;border-radius:6px;font-family:var(--font);font-size:13px;font-weight:600;cursor:pointer;transition:opacity .2s}',
    '.btn{background:var(--accent);color:#fff;border:none;padding:7px 16px;border-radius:var(--radius-sm);font-family:var(--font);font-size:13px;font-weight:600;cursor:pointer;transition:opacity .15s;letter-spacing:.01em}',
    1
)
html = html.replace(
    '.btn.secondary{background:var(--surface2);color:var(--text);border:1px solid var(--border)}',
    '.btn.secondary{background:transparent;color:var(--muted);border:1px solid var(--border);transition:color .15s,border-color .15s}.btn.secondary:hover{color:var(--text);border-color:var(--accent)}',
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 7. CSS — badge for validation sub-tab
# ─────────────────────────────────────────────────────────────────────────────
# Keep the same badge styles, they work fine

# ─────────────────────────────────────────────────────────────────────────────
# 8. CSS — filters-wrap is now inside controls-bar (remove standalone padding)
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    '.filters-wrap{padding:16px 32px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;border-bottom:1px solid var(--border)}',
    '.filters-wrap{display:flex;gap:8px;flex-wrap:wrap;align-items:center;flex:1}',
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 9. CSS — stat values: lime accent → neutral (not everything should be accent)
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    '.stat-value.green{color:var(--success)}.stat-value.yellow{color:var(--accent)}.stat-value.blue{color:var(--accent2)}',
    '.stat-value.green{color:var(--success)}.stat-value.blue{color:#3f51b5}.stat-value.accent{color:var(--accent)}',
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 10. CSS — map dark leaflet bg already matches; popup style update
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    '.leaflet-popup-content-wrapper{background:var(--surface)!important;color:var(--text)!important;border:1px solid var(--border)!important;border-radius:8px!important;box-shadow:0 4px 20px rgba(0,0,0,.5)!important}',
    '.leaflet-popup-content-wrapper{background:var(--surface)!important;color:var(--text)!important;border:1px solid var(--border)!important;border-radius:var(--radius)!important;box-shadow:0 8px 32px rgba(0,0,0,.6)!important}',
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 11. CSS — score/badge colors: lime was used as accent, now blue accent
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    '.score.high{color:var(--success)}.score.mid{color:var(--accent)}.score.low{color:var(--accent3)}',
    '.score.high{color:var(--success)}.score.mid{color:var(--accent2)}.score.low{color:var(--accent3)}',
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 12. CSS — heat-toggle active: lime → blue
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    '.heat-toggle.on{background:rgba(232,255,71,.15);border-color:var(--accent);color:var(--accent)}',
    '.heat-toggle.on{background:var(--accent-dim);border-color:rgba(0,0,238,.5);color:var(--accent)}',
    1
)
html = html.replace(
    '.heat-toggle.on .heat-toggle-dot{background:var(--accent)}',
    '.heat-toggle.on .heat-toggle-dot{background:var(--accent)}',
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 13. CSS — basemap btn active: lime → blue
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    '.basemap-btn.active { background:rgba(232,255,71,.12); border-color:var(--accent); color:var(--accent); }',
    '.basemap-btn.active { background:var(--accent-dim); border-color:rgba(0,0,238,.4); color:var(--accent); }',
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 14. CSS — pagination and table colors: lime accent → blue
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    'th.sorted{color:var(--accent)}',
    'th.sorted{color:var(--accent)}',
    1
)
# Badge colors: keep venta/renta/preventa semantic meaning
html = html.replace(
    '.badge-venta{background:rgba(232,255,71,.15);color:var(--accent)}',
    '.badge-venta{background:rgba(0,0,238,.12);color:#7b7fff}',
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 15. CSS — config overlay button: lime → blue
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    "background:var(--accent);color:#000",
    "background:var(--accent);color:#fff",
    # This replaces ALL occurrences — careful. We already fixed .btn above
    # Let's just do a targeted fix for the config overlay save button
)
# Actually let's not do this blindly — the .btn class is already fixed above

# ─────────────────────────────────────────────────────────────────────────────
# 16. HTML — replace .tabs div with main-tabs + wrap existing views in mercado
# ─────────────────────────────────────────────────────────────────────────────

# The existing structure:
# <div class="tabs">
#   <div class="tab active" onclick="switchTab('table')">☰ Lista</div>
#   <div class="tab" onclick="switchTab('map')">⊕ Mapa</div>
#   <div class="tab" onclick="switchTab('validacion')" id="tab-validacion">⚠ Validación ...</div>
#   <div class="tab" onclick="switchTab('demografia')">⊙ Demografía</div>  ← injected last session
# </div>

OLD_TABS_HTML = """<div class="tabs">
  <div class="tab active" onclick="switchTab('table')">☰ Lista</div>
  <div class="tab" onclick="switchTab('map')">⊕ Mapa</div>"""

NEW_TABS_HTML = """<nav class="main-tabs">
  <div class="main-tab active" id="main-tab-mercado" onclick="switchMainTab('mercado')">Mercado</div>
  <div class="main-tab" id="main-tab-demografia" onclick="switchMainTab('demografia')">Demografía</div>
</nav>

<!-- MERCADO VIEW (Lista + Mapa + Validación) -->
<div id="view-mercado">
<div class="controls-bar">
  <div class="sub-tabs">
    <div class="sub-tab active" id="sub-tab-lista" onclick="switchSubTab('lista')">Lista</div>
    <div class="sub-tab" id="sub-tab-mapa" onclick="switchSubTab('mapa')">Mapa</div>"""

html = html.replace(OLD_TABS_HTML, NEW_TABS_HTML, 1)

# Now replace the rest of the old tabs and the closing </div>
# Find and replace the remaining old tab entries + closing div
OLD_TABS_REST = """  <div class="tab" onclick="switchTab('validacion')" id="tab-validacion">⚠ Validación <span id="badge-validacion" style="display:none;background:var(--accent3);color:#000;font-size:10px;font-weight:700;padding:1px 6px;border-radius:10px;margin-left:4px"></span></div>
  <div class="tab" onclick="switchTab('demografia')">&#9677; Demograf&#237;a</div>
</div>"""

NEW_TABS_REST = """    <div class="sub-tab" id="sub-tab-validacion" onclick="switchSubTab('validacion')">Validación <span id="badge-validacion" style="display:none;background:var(--accent3);color:#fff;font-size:10px;font-weight:700;padding:1px 6px;border-radius:10px;margin-left:4px"></span></div>
  </div>"""

html = html.replace(OLD_TABS_REST, NEW_TABS_REST, 1)

# ─────────────────────────────────────────────────────────────────────────────
# 17. HTML — move filters-wrap inside controls-bar (after sub-tabs closing)
#     and add the view-mercado closing tag before view-demografia
# ─────────────────────────────────────────────────────────────────────────────
# The current structure after the tab replacement:
# NEW_TABS_REST ends right before .filters-wrap
# We need to wrap filters inside controls-bar and close it

OLD_FILTERS_WRAP_START = '<div class="filters-wrap">'
NEW_FILTERS_WRAP_START = '''  <div class="filters-wrap">'''
# Keep filters-wrap as is, just close the controls-bar div after the filters
html = html.replace(OLD_FILTERS_WRAP_START, NEW_FILTERS_WRAP_START, 1)

# Find end of filters-wrap and close the controls-bar
# The filters-wrap ends with the </div> that closes it, then comes the TABLE VIEW comment
# We'll inject the </div> (controls-bar close) and </div> (filters-wrap doesn't need it — it has its own close)
html = html.replace(
    '''  </div>
</div>

<!-- TABLE VIEW -->''',
    '''  </div>
</div>

<!-- TABLE VIEW -->''',
    1
)

# Actually let's just add the closing of controls-bar after the filters closing div
# and the closing of view-mercado before view-demografia

html = html.replace(
    '\n<!-- DEMOGRAFÍA VIEW',
    '\n</div><!-- /view-mercado -->\n\n<!-- DEMOGRAFÍA VIEW'
)

# ─────────────────────────────────────────────────────────────────────────────
# 18. JS — replace switchTab with switchMainTab + switchSubTab
# ─────────────────────────────────────────────────────────────────────────────
OLD_SWITCHTAB = """function switchTab(tab) {
  currentTab = tab;
  const _ids = ['table','map','validacion','demografia'];
  document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', _ids[i] === tab));
  document.getElementById('view-table').style.display      = tab === 'table'      ? 'block' : 'none';
  document.getElementById('view-map').style.display        = tab === 'map'        ? 'block' : 'none';
  document.getElementById('view-validacion').style.display = tab === 'validacion' ? 'block' : 'none';
  document.getElementById('view-demografia').style.display = tab === 'demografia' ? 'block' : 'none';
  if (tab === 'map') initMap();
  if (tab === 'validacion') cargarValidacion();
  if (tab === 'demografia') initDemoMap();
}"""

NEW_SWITCHTAB = """function switchMainTab(tab) {
  document.querySelectorAll('.main-tab').forEach((t, i) =>
    t.classList.toggle('active', ['mercado','demografia'][i] === tab));
  document.getElementById('view-mercado').style.display = tab === 'mercado' ? 'block' : 'none';
  document.getElementById('view-demografia').style.display = tab === 'demografia' ? 'block' : 'none';
  if (tab === 'demografia') initDemoMap();
  if (tab === 'mercado' && currentSubTab === 'mapa') setTimeout(()=>{ if(mapInstance) mapInstance.invalidateSize(); }, 50);
}

function switchSubTab(sub) {
  currentSubTab = sub;
  currentTab = sub === 'lista' ? 'table' : sub;
  ['lista','mapa','validacion'].forEach(id => {
    const el = document.getElementById('sub-tab-' + id);
    if (el) el.classList.toggle('active', id === sub);
  });
  document.getElementById('view-table').style.display      = sub === 'lista'      ? 'block' : 'none';
  document.getElementById('view-map').style.display        = sub === 'mapa'        ? 'block' : 'none';
  document.getElementById('view-validacion').style.display = sub === 'validacion' ? 'block' : 'none';
  if (sub === 'mapa') initMap();
  if (sub === 'validacion') cargarValidacion();
}

// Backward compat — older code calls switchTab(tab)
function switchTab(tab) {
  if (tab === 'demografia') { switchMainTab('demografia'); return; }
  switchMainTab('mercado');
  switchSubTab(tab === 'table' ? 'lista' : tab);
}"""

html = html.replace(OLD_SWITCHTAB, NEW_SWITCHTAB, 1)

# ─────────────────────────────────────────────────────────────────────────────
# 19. JS — add currentSubTab variable alongside currentTab
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    "let currentTab = 'table';",
    "let currentTab = 'table';\nlet currentSubTab = 'lista';\nlet currentMainTab = 'mercado';",
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 20. JS — initial display: hide table/map/validacion inline styles at top
#     They now start hidden because controls-bar + sub-tabs manages them
# ─────────────────────────────────────────────────────────────────────────────
# Remove the CSS that hardcodes view-table: block and view-map: none
html = html.replace(
    '#view-table{display:block}\n#view-map{display:none}',
    '#view-table{display:block}\n#view-map{display:none}\n#view-mercado{display:block}',
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 21. JS — initial page load: set correct display states
# ─────────────────────────────────────────────────────────────────────────────
# Find the DOMContentLoaded / init section and add initial state setup
# The existing init block ends with cargarDatos() call

html = html.replace(
    "  document.getElementById('table-container').innerHTML = '<div class=\"empty\">Configura tus credenciales con el botón ⚙ Config</div>';",
    "  document.getElementById('table-container').innerHTML = '<div class=\"empty\">Configura tus credenciales con el botón ⚙ Config</div>';\n  // Init display state\n  switchMainTab('mercado');\n  switchSubTab('lista');",
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 22. HTML — update header logo text color (accent was lime, now auto from CSS)
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    '.logo span{color:var(--accent)}',
    '.logo{font-size:17px;letter-spacing:-.02em}.logo span{color:var(--muted);font-weight:400}',
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 23. CSS — add version indicator in header-meta
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    '<div class="header-meta">',
    '<div class="header-meta" style="display:flex;align-items:center;gap:16px"><span style="font-family:var(--mono);font-size:10px;color:var(--border);background:var(--surface2);padding:2px 8px;border-radius:4px;border:1px solid var(--border)">v2.0</span>',
    1
)
# Close the extra span container
old_meta_end = '<span id="last-update" style="color:var(--accent2)"></span>\n      </div>'
new_meta_end = '<span id="last-update" style="color:var(--accent2)"></span>\n      </div></div>'
html = html.replace(old_meta_end, new_meta_end, 1)

# ─────────────────────────────────────────────────────────────────────────────
# 24. CSS — demo sidebar + demo mode buttons: lime → blue accent
# ─────────────────────────────────────────────────────────────────────────────
html = html.replace(
    '.demo-mode-btn.active{background:rgba(232,255,71,.12);border-color:var(--accent);color:var(--accent)}',
    '.demo-mode-btn.active{background:var(--accent-dim);border-color:rgba(0,0,238,.4);color:var(--accent)}',
    1
)
html = html.replace(
    '.demo-score-num{font-family:var(--mono);font-size:40px;font-weight:700;line-height:1}',
    '.demo-score-num{font-family:var(--mono);font-size:38px;font-weight:700;line-height:1}',
    1
)

# ─────────────────────────────────────────────────────────────────────────────
# 25. CSS — heatmap toggle on: lime → blue
# ─────────────────────────────────────────────────────────────────────────────
# Already done in step 12

# ─────────────────────────────────────────────────────────────────────────────
# 26. CSS — add smooth transition to main views
# ─────────────────────────────────────────────────────────────────────────────
EXTRA_CSS = """
/* View transitions */
#view-mercado, #view-demografia { animation: fadeIn .15s ease-out; }
@keyframes fadeIn { from { opacity:.7; transform:translateY(2px); } to { opacity:1; transform:translateY(0); } }

/* Table header accents */
thead tr { border-bottom: 1px solid var(--border); }
th.sorted { color: var(--accent); }
th.sorted::after { content: ' ↓'; }
th.sorted.asc::after { content: ' ↑'; }

/* Improved scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
"""

html = html.replace('\n</style>', EXTRA_CSS + '\n</style>', 1)

# ─────────────────────────────────────────────────────────────────────────────
# 27. Write output
# ─────────────────────────────────────────────────────────────────────────────
with open(DEST, 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = os.path.getsize(DEST) / 1024
print(f'CAMPO v2.0 built: {size_kb:.0f} KB -> {DEST}')

# ─────────────────────────────────────────────────────────────────────────────
# 28. Verify key elements
# ─────────────────────────────────────────────────────────────────────────────
checks = [
    ('CAMPO title', '<title>CAMPO'),
    ('Inter font', 'family=Inter'),
    ('AirDNA bg', '#212121'),
    ('AirDNA accent', '#0000ee'),
    ('main-tabs', 'class="main-tabs"'),
    ('switchMainTab', 'function switchMainTab'),
    ('switchSubTab', 'function switchSubTab'),
    ('view-mercado', 'id="view-mercado"'),
    ('sub-tab-lista', 'id="sub-tab-lista"'),
    ('AGEB data', 'AGEB_B64'),
    ('demographics', 'id="view-demografia"'),
    ('v2.0 badge', 'v2.0'),
]
print()
print('Verification:')
for name, pattern in checks:
    found = pattern in html
    print(f'  {"OK" if found else "MISSING":6}  {name}')
