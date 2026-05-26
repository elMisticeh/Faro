"""
add_demo_tab.py — Injects Demographics tab into dashboard.html
"""
import json, os, re

DASHBOARD = r'C:\proyectos\real-estate\frontend\dashboard.html'
B64_PATH   = r'C:\proyectos\real-estate\data\ageb_data.b64'
BM_PATH    = r'C:\proyectos\real-estate\data\torreon_benchmarks.json'
GEOJSON    = r'C:\proyectos\real-estate\data\torreon_agebs.geojson'

# ── Load assets ───────────────────────────────────────────────────────────────
with open(DASHBOARD, encoding='utf-8') as f:
    html = f.read()

with open(B64_PATH) as f:
    ageb_b64 = f.read().strip()

# Compute municipal growth benchmarks
with open(GEOJSON, encoding='utf-8') as f:
    tdata = json.load(f)

features = tdata['features']
pob_2020 = sum(f['properties']['pob_total'] for f in features)
pob_2010 = sum(f['properties']['pob_2010'] for f in features)
hog_2020 = sum(f['properties']['hog_total'] for f in features)
hog_2010 = sum(f['properties']['hog_2010'] for f in features)
viv_2020 = sum(f['properties']['viv_habitadas'] for f in features)
viv_2010 = sum(f['properties']['viv_2010'] for f in features)

with open(BM_PATH) as f:
    bm = json.load(f)

bm['crec_pob'] = round((pob_2020 - pob_2010) / pob_2010 * 100, 1) if pob_2010 else 0
bm['crec_hog'] = round((hog_2020 - hog_2010) / hog_2010 * 100, 1) if hog_2010 else 0
bm['crec_viv'] = round((viv_2020 - viv_2010) / viv_2010 * 100, 1) if viv_2010 else 0
bm['prom_hnv'] = round(
    sum(f['properties'].get('prom_hnv', 0) * f['properties'].get('pob_total', 0) for f in features) / pob_2020, 2
)

with open(BM_PATH, 'w') as f:
    json.dump(bm, f, indent=2)

bm_js = json.dumps(bm)
print('Municipal growth benchmarks:', bm['crec_pob'], '/', bm['crec_hog'], '/', bm['crec_viv'])

# ── CSS ───────────────────────────────────────────────────────────────────────
DEMO_CSS = """
/* ═══════════════════════════════ DEMOGRAFÍA TAB ═══════════════════════════ */
#view-demografia{display:none}
#demo-map-container{height:calc(100vh - 204px);min-height:500px;position:relative}
#demo-map{width:100%;height:100%}
.demo-toolbar{position:absolute;top:12px;left:12px;z-index:1000;display:flex;align-items:center;gap:8px;flex-wrap:wrap;background:rgba(13,15,20,.93);border:1px solid var(--border);border-radius:8px;padding:9px 14px;backdrop-filter:blur(8px);font-size:12px;max-width:calc(100% - 420px)}
.demo-toolbar label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;white-space:nowrap}
.demo-mode-btn{padding:5px 10px;background:var(--surface2);border:1px solid var(--border);border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;color:var(--muted);transition:all .2s;user-select:none;white-space:nowrap}
.demo-mode-btn:hover{color:var(--text)}
.demo-mode-btn.active{background:rgba(232,255,71,.12);border-color:var(--accent);color:var(--accent)}
.demo-toolbar select{padding:4px 8px;font-size:12px}
#demo-status{font-size:11px;color:var(--muted);font-family:var(--mono);white-space:nowrap}
#demo-sidebar{width:400px}
.demo-sidebar-loading{display:flex;flex-direction:column;align-items:center;justify-content:center;height:200px;gap:12px;color:var(--muted);font-size:13px}
.demo-sidebar-loading .spinner{width:24px;height:24px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite}
.demo-kpi-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;background:var(--border);border-radius:8px;overflow:hidden;margin-bottom:4px}
.demo-kpi{background:var(--surface2);padding:10px 10px 8px;display:flex;flex-direction:column;gap:2px}
.demo-kpi-val{font-family:var(--mono);font-size:18px;font-weight:700;color:var(--text);line-height:1}
.demo-kpi-lbl{font-size:9px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted)}
.demo-score-wrap{display:flex;align-items:center;gap:16px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px 16px;margin-bottom:4px}
.demo-score-num{font-family:var(--mono);font-size:40px;font-weight:700;line-height:1}
.demo-score-denom{font-family:var(--mono);font-size:18px;color:var(--muted);margin-top:6px}
.demo-score-label{font-size:13px;font-weight:600;margin-bottom:4px}
.demo-score-sub{font-size:11px;color:var(--muted);line-height:1.4}
.demo-section{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px;display:flex;flex-direction:column;gap:8px}
.demo-section-title{font-size:10px;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);font-weight:600;border-bottom:1px solid var(--border);padding-bottom:6px;margin-bottom:2px}
.demo-cmp-row{display:flex;flex-direction:column;gap:4px;margin-bottom:4px}
.demo-cmp-label{display:flex;justify-content:space-between;align-items:baseline}
.demo-cmp-name{font-size:11px;color:var(--text);font-weight:500}
.demo-cmp-vals{font-family:var(--mono);font-size:10px}
.demo-bars-wrap{display:flex;flex-direction:column;gap:3px}
.demo-bar-row{display:flex;align-items:center;gap:6px}
.demo-bar-lbl{font-family:var(--mono);font-size:9px;color:var(--muted);width:28px;text-align:right;flex-shrink:0}
.demo-bar-track{flex:1;height:6px;background:var(--border);border-radius:3px;overflow:hidden}
.demo-bar-fill{height:100%;border-radius:3px;transition:width .4s ease;min-width:2px}
.demo-bar-fill.zona{background:var(--accent)}
.demo-bar-fill.mun{background:var(--accent2)}
.demo-bar-fill.neg{background:var(--accent3)}
.demo-nse-grid{display:flex;flex-wrap:wrap;gap:5px}
.demo-nse-pill{display:flex;align-items:center;gap:5px;padding:4px 8px;border-radius:20px;font-size:11px;font-weight:600;border:1px solid transparent}
.demo-nse-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.demo-age-row{display:flex;align-items:center;gap:8px;margin-bottom:3px}
.demo-age-lbl{font-size:10px;color:var(--muted);width:46px;flex-shrink:0}
.demo-age-bars{flex:1;display:flex;flex-direction:column;gap:2px}
.demo-viv-row{display:flex;align-items:center;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border)}
.demo-viv-row:last-child{border-bottom:none}
.demo-viv-name{font-size:11px;color:var(--text)}
.demo-alert{display:flex;align-items:flex-start;gap:8px;padding:8px 10px;border-radius:6px;font-size:11px;line-height:1.45;margin-top:4px}
.demo-alert.warn{background:rgba(255,107,71,.08);border:1px solid rgba(255,107,71,.3);color:var(--accent3)}
.demo-alert.ok{background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.3);color:var(--success)}
.demo-alert.info{background:rgba(71,184,255,.08);border:1px solid rgba(71,184,255,.3);color:var(--accent2)}
.demo-alert-icon{font-size:13px;flex-shrink:0}
#demo-heatmap-legend{position:absolute;bottom:24px;right:24px;z-index:1000;background:rgba(13,15,20,.93);border:1px solid var(--border);border-radius:8px;padding:12px 16px;min-width:180px;backdrop-filter:blur(8px);display:none}
.demo-legend-title{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:7px}
.demo-legend-bar{height:7px;border-radius:4px;margin-bottom:5px}
.demo-legend-labels{display:flex;justify-content:space-between;font-family:var(--mono);font-size:10px;color:var(--muted)}
.demo-nse-legend{display:flex;flex-direction:column;gap:4px}
.demo-nse-legend-item{display:flex;align-items:center;gap:7px;font-size:11px;color:var(--muted)}
.demo-nse-legend-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
/* ═══════════════════════════════════════════════════════════════════════════ */
"""

# ── HTML ──────────────────────────────────────────────────────────────────────
DEMO_HTML = """
<!-- DEMOGRAFÍA VIEW ─────────────────────────────────────────── -->
<div id="view-demografia">
  <div id="demo-map-container">
    <div id="demo-map"></div>
    <div class="demo-toolbar">
      <label>Modo</label>
      <div class="demo-mode-btn active" id="btn-radio" onclick="setDemoMode('radio')">&#128205; Radio</div>
      <div class="demo-mode-btn" id="btn-ageb" onclick="setDemoMode('ageb')">&#9638; AGEB</div>
      <div class="heat-sep"></div>
      <label>Radio</label>
      <select id="demo-radius">
        <option value="1">1 km</option>
        <option value="2" selected>2 km</option>
        <option value="3">3 km</option>
        <option value="5">5 km</option>
      </select>
      <div class="heat-sep"></div>
      <label>Mapa AGEB</label>
      <select id="demo-heatmap-select" onchange="setAgebHeatmap(this.value)">
        <option value="none">Sin capa</option>
        <option value="hogares">Hogares 2020</option>
        <option value="crecimiento">Crecimiento 10-20</option>
        <option value="nse">NSE Predominante</option>
      </select>
      <div class="heat-sep"></div>
      <span id="demo-status">Haz clic en el mapa para analizar una zona</span>
    </div>
    <div id="demo-sidebar" class="hex-sidebar">
      <div class="hex-sidebar-header">
        <div>
          <div class="hex-sidebar-title" id="demo-title">Zona de Influencia</div>
          <div class="hex-sidebar-sub" id="demo-sub">Selecciona un punto en el mapa</div>
        </div>
        <button class="hex-close" onclick="document.getElementById('demo-sidebar').classList.remove('open')">&#x2715;</button>
      </div>
      <div class="hex-sidebar-body" id="demo-body">
        <div class="demo-sidebar-loading">
          <div class="spinner"></div>Cargando datos INEGI...
        </div>
      </div>
    </div>
    <div id="demo-heatmap-legend">
      <div class="demo-legend-title" id="demo-leg-title">&#8212;</div>
      <div id="demo-leg-content"></div>
    </div>
  </div>
</div>
<!-- /DEMOGRAFÍA ─────────────────────────────────────────────── -->
"""

# ── JavaScript ────────────────────────────────────────────────────────────────
DEMO_JS_TEMPLATE = r"""
// ═══════════════════════════════════════════════════ DEMOGRAFÍA ══════════════

const AGEB_B64 = 'AGEB_B64_PLACEHOLDER';
const MUN_BENCH = BM_JS_PLACEHOLDER;

let agebGeoJSON = null;
let demoMap = null;
let agebLayer = null;
let demoMode = 'radio';
let selectedAgebs = [];
let demoCircle = null;
let demoInitDone = false;

async function loadAgebData() {
  if (agebGeoJSON) return agebGeoJSON;
  const binary = atob(AGEB_B64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  const ds = new DecompressionStream('gzip');
  const writer = ds.writable.getWriter();
  writer.write(bytes);
  writer.close();
  const reader = ds.readable.getReader();
  const chunks = [];
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }
  const blob = new Blob(chunks);
  agebGeoJSON = JSON.parse(await blob.text());
  return agebGeoJSON;
}

async function initDemoMap() {
  if (demoInitDone) return;
  demoInitDone = true;
  demoMap = L.map('demo-map', { center: [25.5428, -103.4068], zoom: 12, preferCanvas: true });
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO', subdomains: 'abcd', maxZoom: 19
  }).addTo(demoMap);

  document.getElementById('demo-status').textContent = 'Cargando datos INEGI (332 AGEBs)...';
  const data = await loadAgebData();
  document.getElementById('demo-status').textContent = 'Haz clic en el mapa para analizar una zona';

  agebLayer = L.geoJSON(data, {
    style: agebDefaultStyle,
    onEachFeature: (feature, layer) => {
      layer.on('click', (e) => {
        if (demoMode === 'ageb') toggleAgebSelection(feature, layer);
        else analyzePoint(e.latlng.lat, e.latlng.lng);
        L.DomEvent.stopPropagation(e);
      });
      layer.on('mouseover', () => {
        if (demoMode === 'ageb' && !selectedAgebs.includes(feature))
          layer.setStyle({ fillOpacity: 0.6 });
      });
      layer.on('mouseout', () => {
        if (!selectedAgebs.includes(feature))
          layer.setStyle(agebDefaultStyle(feature));
      });
    }
  }).addTo(demoMap);

  demoMap.on('click', (e) => {
    if (demoMode === 'radio') analyzePoint(e.latlng.lat, e.latlng.lng);
  });
}

function agebDefaultStyle() {
  return { color: '#2a2f3d', weight: 0.5, fillColor: '#1e2230', fillOpacity: 0.35 };
}

function setDemoMode(mode) {
  demoMode = mode;
  document.getElementById('btn-radio').classList.toggle('active', mode === 'radio');
  document.getElementById('btn-ageb').classList.toggle('active', mode === 'ageb');
  if (mode === 'radio') {
    document.getElementById('demo-status').textContent = 'Haz clic en el mapa para analizar una zona';
    clearAgebSelection();
  } else {
    document.getElementById('demo-status').textContent = 'Haz clic en los AGEBs para seleccionarlos';
    if (demoCircle) { demoMap.removeLayer(demoCircle); demoCircle = null; }
  }
}

function toggleAgebSelection(feature, layer) {
  const idx = selectedAgebs.indexOf(feature);
  if (idx >= 0) {
    selectedAgebs.splice(idx, 1);
    layer.setStyle(agebDefaultStyle());
  } else {
    selectedAgebs.push(feature);
    layer.setStyle({ color: '#e8ff47', weight: 1.5, fillColor: '#e8ff47', fillOpacity: 0.45 });
  }
  if (selectedAgebs.length > 0) {
    const stats = computeStats(selectedAgebs);
    const n = selectedAgebs.length;
    renderDemoPanel(stats, n, n + ' AGEB' + (n > 1 ? 's' : '') + ' seleccionados', 'Seleccion manual');
    document.getElementById('demo-sidebar').classList.add('open');
  } else {
    document.getElementById('demo-sidebar').classList.remove('open');
  }
}

function clearAgebSelection() {
  selectedAgebs = [];
  if (agebLayer) agebLayer.eachLayer(l => l.setStyle(agebDefaultStyle()));
}

function haversine(lat1, lng1, lat2, lng2) {
  const R = 6371, toRad = x => x * Math.PI / 180;
  const dLat = toRad(lat2 - lat1), dLng = toRad(lng2 - lng1);
  const a = Math.sin(dLat/2)**2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function getAgebCentroid(feature) {
  const coords = feature.geometry.coordinates;
  const type = feature.geometry.type;
  let pts = type === 'Polygon' ? coords[0] : (type === 'MultiPolygon' ? coords[0][0] : []);
  if (!pts.length) return [25.54, -103.41];
  return [
    pts.reduce((s, c) => s + c[1], 0) / pts.length,
    pts.reduce((s, c) => s + c[0], 0) / pts.length
  ];
}

function analyzePoint(lat, lng) {
  if (!agebGeoJSON) return;
  const radiusKm = parseFloat(document.getElementById('demo-radius').value);
  if (demoCircle) demoMap.removeLayer(demoCircle);
  demoCircle = L.circle([lat, lng], {
    radius: radiusKm * 1000,
    color: '#e8ff47', weight: 1.5, fillColor: '#e8ff47', fillOpacity: 0.05, dashArray: '6 4'
  }).addTo(demoMap);

  const nearby = agebGeoJSON.features.filter(f => {
    const [cLat, cLng] = getAgebCentroid(f);
    return haversine(lat, lng, cLat, cLng) <= radiusKm;
  });

  clearAgebSelection();
  if (agebLayer) {
    agebLayer.eachLayer(layer => {
      if (nearby.includes(layer.feature)) {
        layer.setStyle({ color: '#e8ff47', weight: 1, fillColor: '#e8ff47', fillOpacity: 0.35 });
        selectedAgebs.push(layer.feature);
      }
    });
  }

  if (nearby.length === 0) {
    document.getElementById('demo-status').textContent = 'Sin AGEBs en ' + radiusKm + 'km';
    return;
  }

  const stats = computeStats(nearby);
  renderDemoPanel(stats, nearby.length,
    nearby.length + ' AGEBs · Radio ' + radiusKm + 'km', 'Radio de Influencia');
  document.getElementById('demo-sidebar').classList.add('open');
  document.getElementById('demo-status').textContent = nearby.length + ' AGEBs analizados';
}

function computeStats(features) {
  const s = field => features.reduce((a, f) => a + (f.properties[field] || 0), 0);
  const wavg = (field, weight) => {
    const tw = s(weight);
    return tw ? features.reduce((a, f) => a + (f.properties[field] || 0) * (f.properties[weight] || 0), 0) / tw : 0;
  };
  const avg = field => {
    const vals = features.filter(f => f.properties[field] != null).map(f => f.properties[field]);
    return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
  };

  const pob = s('pob_total'), hog = s('hog_total');
  const viv_h = s('viv_habitadas'), viv_t = s('viv_total');
  const viv_des = s('viv_deshabitadas'), viv_tmp = s('viv_temporal');
  const area = s('area_km2'), pea = s('pea');
  const pob_0_14 = s('pob_0_14'), pob_15_24 = s('pob_15_24');
  const pob_25_59 = s('pob_25_59'), pob_60 = s('pob_60mas');
  const nse_ab = s('nse_ab'), nse_cmas = s('nse_cmas'), nse_c = s('nse_c');
  const nse_cmenos = s('nse_cmenos'), nse_dmas = s('nse_dmas'), nse_d = s('nse_d'), nse_e = s('nse_e');
  const sol = s('solteros'), cas = s('casados'), sep = s('separados');
  const pob_2010 = s('pob_2010'), hog_2010 = s('hog_2010'), viv_2010 = s('viv_2010');
  const vph_2 = s('vph_2mas_dor');

  return {
    pob, hog, viv_h, viv_t, viv_des, viv_tmp, area, pea,
    densidad: area ? pob / area : 0,
    escolaridad: wavg('escolaridad', 'pob_total'),
    pct_pea: pob ? pea / pob * 100 : 0,
    pob_0_14, pob_15_24, pob_25_59, pob_60,
    pct_0_14: pob ? pob_0_14/pob*100 : 0,
    pct_15_24: pob ? pob_15_24/pob*100 : 0,
    pct_25_59: pob ? pob_25_59/pob*100 : 0,
    pct_60: pob ? pob_60/pob*100 : 0,
    pct_viv_h: viv_t ? viv_h/viv_t*100 : 0,
    pct_viv_des: viv_t ? viv_des/viv_t*100 : 0,
    pct_viv_tmp: viv_t ? viv_tmp/viv_t*100 : 0,
    pct_2dor: viv_h ? vph_2/viv_h*100 : 0,
    nse_ab, nse_cmas, nse_c, nse_cmenos, nse_dmas, nse_d, nse_e,
    nse_total: nse_ab + nse_cmas + nse_c + nse_cmenos + nse_dmas + nse_d + nse_e,
    sol, cas, sep, fam_total: sol + cas + sep,
    prom_hnv: avg('prom_hnv'),
    crec_pob: pob_2010 ? (pob - pob_2010) / pob_2010 * 100 : 0,
    crec_hog: hog_2010 ? (hog - hog_2010) / hog_2010 * 100 : 0,
    crec_viv: viv_2010 ? (viv_h - viv_2010) / viv_2010 * 100 : 0,
  };
}

function calcScore(s) {
  let pts = 0;
  if (s.crec_pob > 0) pts += 2; else if (s.crec_pob > -10) pts += 1;
  if (s.pct_25_59 >= 44) pts += 2; else if (s.pct_25_59 >= 35) pts += 1;
  if (s.pct_viv_h >= 80) pts += 2; else if (s.pct_viv_h >= 65) pts += 1;
  if (s.pct_pea >= 50) pts += 2; else if (s.pct_pea >= 40) pts += 1;
  const pct_alto = s.nse_total ? (s.nse_ab + s.nse_cmas) / s.nse_total * 100 : 0;
  if (pct_alto >= 30) pts += 2; else if (pct_alto >= 15) pts += 1;
  return pts;
}

function scoreLabel(n) {
  if (n >= 8) return ['MUY ALTO', 'var(--success)'];
  if (n >= 6) return ['ALTO', 'var(--accent2)'];
  if (n >= 4) return ['MODERADO', 'var(--accent)'];
  return ['BAJO', 'var(--accent3)'];
}

function renderDemoPanel(s, count, subtitle, title) {
  document.getElementById('demo-title').textContent = title || 'Zona de Influencia';
  document.getElementById('demo-sub').textContent = subtitle || '';
  const b = MUN_BENCH;
  const fmt = (n, dec) => isNaN(n) ? '—' : (+n).toLocaleString('es-MX', {maximumFractionDigits: dec||0, minimumFractionDigits: dec||0});
  const sign = n => (n >= 0 ? '+' : '') + fmt(n, 1) + '%';

  const score = calcScore(s);
  const [slbl, scol] = scoreLabel(score);

  const alerts = [];
  if (s.pct_60 > 20) alerts.push({t:'warn',i:'⚠',txt:'Población envejecida (' + fmt(s.pct_60,1) + '% ≥60 años vs ' + fmt(b.pct_60mas,1) + '% municipal). Demanda de productos accesibles y planta baja.'});
  if (s.pct_viv_des > 20) alerts.push({t:'warn',i:'⚠',txt:'Vacancia alta (' + fmt(s.pct_viv_des,1) + '%). Evaluar demanda real antes de agregar oferta nueva.'});
  if (s.crec_pob > 5) alerts.push({t:'ok',i:'✓',txt:'Zona en crecimiento (' + sign(s.crec_pob) + '). Mercado activo con demanda sostenida.'});
  if (s.nse_total && (s.nse_ab + s.nse_cmas) / s.nse_total > 0.3) alerts.push({t:'info',i:'↑',txt:'Concentración NSE Alto (AB+C+). Demanda de vivienda media-alta y residencial.'});
  const alertsHtml = alerts.map(a => `<div class="demo-alert ${a.t}"><span class="demo-alert-icon">${a.i}</span>${a.txt}</div>`).join('');

  const nseItems = [
    {label:'A/B',count:s.nse_ab,color:'#8b5cf6'},
    {label:'C+',count:s.nse_cmas,color:'#3b82f6'},
    {label:'C',count:s.nse_c,color:'#22d3ee'},
    {label:'C−',count:s.nse_cmenos,color:'#4ade80'},
    {label:'D+',count:s.nse_dmas,color:'#a3e635'},
    {label:'D',count:s.nse_d,color:'#facc15'},
    {label:'E',count:s.nse_e,color:'#f97316'},
  ].filter(x => x.count > 0);
  const nsePills = nseItems.map(x => {
    const pct = s.nse_total ? x.count / s.nse_total * 100 : 0;
    return `<div class="demo-nse-pill" style="background:${x.color}22;border-color:${x.color}55"><span class="demo-nse-dot" style="background:${x.color}"></span><span style="font-size:10px;font-weight:700">${x.label}</span><span style="font-size:10px;color:var(--muted)">${fmt(pct,0)}%</span></div>`;
  }).join('');

  function cmpBar(name, zona, mun, higherBetter) {
    const absMax = Math.max(Math.abs(zona), Math.abs(mun), 0.1) * 1.2;
    const zW = Math.min(Math.abs(zona) / absMax * 100, 100);
    const mW = Math.min(Math.abs(mun) / absMax * 100, 100);
    const zClass = zona < 0 ? 'neg' : 'zona';
    const diff = zona - mun;
    const diffColor = (diff > 0) === higherBetter ? 'var(--success)' : 'var(--accent3)';
    return `<div class="demo-cmp-row"><div class="demo-cmp-label"><span class="demo-cmp-name">${name}</span><span class="demo-cmp-vals" style="color:${diffColor}">${fmt(zona,1)}% <span style="color:var(--muted)">vs ${fmt(mun,1)}%</span></span></div><div class="demo-bars-wrap"><div class="demo-bar-row"><span class="demo-bar-lbl">Zona</span><div class="demo-bar-track"><div class="demo-bar-fill ${zClass}" style="width:${zW}%"></div></div></div><div class="demo-bar-row"><span class="demo-bar-lbl">Mun</span><div class="demo-bar-track"><div class="demo-bar-fill mun" style="width:${mW}%"></div></div></div></div></div>`;
  }

  function ageBar(label, zona, mun) {
    const max = Math.max(zona, mun, 0.1) * 1.2;
    const zW = Math.min(zona / max * 100, 100);
    const mW = Math.min(mun / max * 100, 100);
    return `<div class="demo-age-row"><span class="demo-age-lbl">${label}</span><div class="demo-age-bars"><div class="demo-bar-row"><span class="demo-bar-lbl">Zona</span><div class="demo-bar-track"><div class="demo-bar-fill zona" style="width:${zW}%"></div></div><span style="font-family:var(--mono);font-size:9px;color:var(--muted);margin-left:4px">${fmt(zona,1)}%</span></div><div class="demo-bar-row"><span class="demo-bar-lbl">Mun</span><div class="demo-bar-track"><div class="demo-bar-fill mun" style="width:${mW}%"></div></div><span style="font-family:var(--mono);font-size:9px;color:var(--muted);margin-left:4px">${fmt(mun,1)}%</span></div></div></div>`;
  }

  function famBar(label, pct) {
    return `<div class="demo-viv-row"><span class="demo-viv-name">${label}</span><div style="flex:1;margin:0 10px"><div class="demo-bar-track" style="height:5px"><div class="demo-bar-fill zona" style="width:${Math.min(pct,100).toFixed(0)}%"></div></div></div><span style="font-family:var(--mono);font-size:12px">${fmt(pct,1)}%</span></div>`;
  }

  const vivPct = s.fam_total > 0;
  document.getElementById('demo-body').innerHTML = `
    <div class="demo-score-wrap">
      <div><div style="display:flex;align-items:baseline;gap:4px"><span class="demo-score-num" style="color:${scol}">${score}</span><span class="demo-score-denom">/10</span></div></div>
      <div><div class="demo-score-label" style="color:${scol}">${slbl}</div><div class="demo-score-sub">Score de zona · Análisis sociodemográfico INEGI 2020</div></div>
    </div>
    <div class="demo-kpi-grid">
      <div class="demo-kpi"><span class="demo-kpi-val">${fmt(s.pob)}</span><span class="demo-kpi-lbl">Población</span></div>
      <div class="demo-kpi"><span class="demo-kpi-val">${fmt(s.hog)}</span><span class="demo-kpi-lbl">Hogares</span></div>
      <div class="demo-kpi"><span class="demo-kpi-val">${fmt(s.densidad,0)}</span><span class="demo-kpi-lbl">Hab/km²</span></div>
      <div class="demo-kpi"><span class="demo-kpi-val">${fmt(s.escolaridad,1)}</span><span class="demo-kpi-lbl">Escolaridad (años)</span></div>
      <div class="demo-kpi"><span class="demo-kpi-val">${fmt(s.pct_pea,1)}%</span><span class="demo-kpi-lbl">PEA Activa</span></div>
      <div class="demo-kpi"><span class="demo-kpi-val">${fmt(s.prom_hnv,2)}</span><span class="demo-kpi-lbl">Hijos/mujer</span></div>
    </div>
    <div class="demo-section">
      <div class="demo-section-title">Crecimiento 2010–2020</div>
      ${cmpBar('Población', s.crec_pob, b.crec_pob, true)}
      ${cmpBar('Hogares', s.crec_hog, b.crec_hog, true)}
      ${cmpBar('Viv. habitadas', s.crec_viv, b.crec_viv, true)}
    </div>
    <div class="demo-section">
      <div class="demo-section-title">Estructura de Edad</div>
      ${ageBar('0–14', s.pct_0_14, b.pct_0_14)}
      ${ageBar('15–24', s.pct_15_24, b.pct_15_24)}
      ${ageBar('25–59', s.pct_25_59, b.pct_25_59)}
      ${ageBar('60+', s.pct_60, b.pct_60mas)}
    </div>
    <div class="demo-section">
      <div class="demo-section-title">Parque Habitacional · ${fmt(s.viv_t)} unidades</div>
      ${famBar('Habitadas', s.pct_viv_h)}
      ${famBar('Deshabitadas', s.pct_viv_des)}
      ${famBar('Uso temporal', s.pct_viv_tmp)}
      <div style="font-size:11px;color:var(--muted);margin-top:4px">Ocupación prom: <span style="color:var(--text);font-family:var(--mono)">${s.viv_h ? fmt(s.pob/s.viv_h,2) : '—'}</span> hab/viv · 2+ dorm: <span style="color:var(--text);font-family:var(--mono)">${fmt(s.pct_2dor,0)}%</span></div>
    </div>
    <div class="demo-section">
      <div class="demo-section-title">NSE · ${fmt(s.nse_total)} viviendas clasificadas</div>
      <div class="demo-nse-grid">${nsePills}</div>
      <div style="font-size:10px;color:var(--muted);margin-top:4px">Fuente: AMAI 2018 · Clasificación por AGEB</div>
    </div>
    <div class="demo-section">
      <div class="demo-section-title">Estructura Familiar</div>
      ${famBar('Solteros', s.fam_total ? s.sol/s.fam_total*100 : 0)}
      ${famBar('Casados / Unión', s.fam_total ? s.cas/s.fam_total*100 : 0)}
      ${famBar('Separados / Div.', s.fam_total ? s.sep/s.fam_total*100 : 0)}
      <div style="font-size:11px;color:var(--muted);margin-top:4px">Fertilidad: <span style="color:var(--text);font-family:var(--mono)">${fmt(s.prom_hnv,2)}</span> vs mun <span style="font-family:var(--mono)">${fmt(b.prom_hnv,2)}</span></div>
    </div>
    ${alertsHtml ? '<div>' + alertsHtml + '</div>' : ''}
    <div style="font-size:9px;color:var(--muted);text-align:center;padding:6px 0;border-top:1px solid var(--border)">
      Censo Población y Vivienda 2020 · INEGI · AMAI 2018<br>Datos DATERRA Consulting — COEZA Suite
    </div>`;
}

const _NSE_COLORS = {'A/B':'#8b5cf6','C+':'#3b82f6','C':'#22d3ee','C-':'#4ade80','D+':'#a3e635','D':'#facc15','E':'#f97316'};

function _numToColor(t) {
  const stops=['#0d47a1','#1976d2','#42a5f5','#80deea','#a5d6a7','#ffeb3b','#ff9800','#f44336'];
  const i=Math.min(Math.floor(t*(stops.length-1)),stops.length-2);
  const frac=t*(stops.length-1)-i;
  const p=c=>[parseInt(c.slice(1,3),16),parseInt(c.slice(3,5),16),parseInt(c.slice(5,7),16)];
  const [r1,g1,b1]=p(stops[i]),[r2,g2,b2]=p(stops[i+1]);
  return `rgb(${Math.round(r1+(r2-r1)*frac)},${Math.round(g1+(g2-g1)*frac)},${Math.round(b1+(b2-b1)*frac)})`;
}

function setAgebHeatmap(mode) {
  if (!agebLayer) return;
  const legend=document.getElementById('demo-heatmap-legend');
  if (mode==='none'){agebLayer.eachLayer(l=>l.setStyle(agebDefaultStyle()));legend.style.display='none';return;}
  if (mode==='nse'){
    agebLayer.eachLayer(l=>{const n=l.feature.properties.nse_predominante||'';l.setStyle({color:'#1a1f2e',weight:0.4,fillColor:_NSE_COLORS[n]||'#374151',fillOpacity:0.8});});
    legend.style.display='block';
    document.getElementById('demo-leg-title').textContent='NSE Predominante (AMAI)';
    document.getElementById('demo-leg-content').innerHTML='<div class="demo-nse-legend">'+Object.entries(_NSE_COLORS).map(([k,c])=>`<div class="demo-nse-legend-item"><span class="demo-nse-legend-dot" style="background:${c}"></span>${k}</div>`).join('')+'</div>';
    return;
  }
  const vals=[];
  agebLayer.eachLayer(l=>{const p=l.feature.properties;vals.push(mode==='hogares'?(p.hog_total||0):(p.crec_pct_hog||0));});
  const minV=Math.min(...vals),maxV=Math.max(...vals),range=maxV-minV||1;
  agebLayer.eachLayer(l=>{
    const p=l.feature.properties;
    const v=mode==='hogares'?(p.hog_total||0):(p.crec_pct_hog||0);
    l.setStyle({color:'#1a1f2e',weight:0.3,fillColor:_numToColor((v-minV)/range),fillOpacity:0.85});
  });
  const fmt2=n=>Math.round(n).toLocaleString('es-MX');
  legend.style.display='block';
  document.getElementById('demo-leg-title').textContent=mode==='hogares'?'Hogares Totales 2020':'Crecimiento Neto Hogares 2010-20';
  document.getElementById('demo-leg-content').innerHTML=`<div class="demo-legend-bar" style="background:linear-gradient(to right,#0d47a1,#42a5f5,#80deea,#ffeb3b,#f44336)"></div><div class="demo-legend-labels"><span>${fmt2(minV)}</span><span>${fmt2(maxV)}</span></div>`;
}
// ═══════════════════════════════════════════════════════════════════════════════
"""

DEMO_JS = DEMO_JS_TEMPLATE.replace('AGEB_B64_PLACEHOLDER', ageb_b64).replace('BM_JS_PLACEHOLDER', bm_js)

# ── Patch switchTab ───────────────────────────────────────────────────────────
OLD_ST = ("function switchTab(tab) {\n"
          "  currentTab = tab;\n"
          "  document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', ['table','map','validacion'][i] === tab));\n"
          "  document.getElementById('view-table').style.display      = tab === 'table'      ? 'block' : 'none';\n"
          "  document.getElementById('view-map').style.display        = tab === 'map'        ? 'block' : 'none';\n"
          "  document.getElementById('view-validacion').style.display = tab === 'validacion' ? 'block' : 'none';\n"
          "  if (tab === 'map') initMap();\n"
          "  if (tab === 'validacion') cargarValidacion();\n"
          "}")

NEW_ST = ("function switchTab(tab) {\n"
          "  currentTab = tab;\n"
          "  const _ids = ['table','map','validacion','demografia'];\n"
          "  document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', _ids[i] === tab));\n"
          "  document.getElementById('view-table').style.display      = tab === 'table'      ? 'block' : 'none';\n"
          "  document.getElementById('view-map').style.display        = tab === 'map'        ? 'block' : 'none';\n"
          "  document.getElementById('view-validacion').style.display = tab === 'validacion' ? 'block' : 'none';\n"
          "  document.getElementById('view-demografia').style.display = tab === 'demografia' ? 'block' : 'none';\n"
          "  if (tab === 'map') initMap();\n"
          "  if (tab === 'validacion') cargarValidacion();\n"
          "  if (tab === 'demografia') initDemoMap();\n"
          "}")

# ── Apply all patches ─────────────────────────────────────────────────────────
# 1. CSS
assert '</style>' in html
html = html.replace('</style>', DEMO_CSS + '\n</style>', 1)
print('CSS injected.')

# 2. Tab button
OLD_TAB_LINE = "  <div class=\"tab\" onclick=\"switchTab('validacion')\" id=\"tab-validacion\">&#9888; Validaci&#243;n <span id=\"badge-validacion\""
# Try as-is in file
if "switchTab('validacion')" not in html:
    print('ERROR: validacion tab not found')
else:
    TAB_MARKER = "switchTab('validacion')"
    idx = html.find(TAB_MARKER)
    # Find end of that div
    end = html.find('</div>', idx) + 6
    insert_after = html[idx - 50:end]
    replacement = insert_after + "\n  <div class=\"tab\" onclick=\"switchTab('demografia')\">&#9677; Demograf&#237;a</div>"
    html = html[:idx-50] + replacement + html[end:]
    print('Tab button injected.')

# 3. View div — insert before first <script>
assert '<script>' in html
html = html.replace('<script>', DEMO_HTML + '\n\n<script>', 1)
print('View HTML injected.')

# 4. switchTab patch
if OLD_ST in html:
    html = html.replace(OLD_ST, NEW_ST, 1)
    print('switchTab patched.')
else:
    print('WARNING: switchTab pattern not found, skipping patch')

# 5. Demo JS before last </script>
last = html.rfind('</script>')
html = html[:last] + DEMO_JS + '\n</script>' + html[last+9:]
print('Demo JS injected.')

# ── Write output ──────────────────────────────────────────────────────────────
with open(DASHBOARD, 'w', encoding='utf-8') as f:
    f.write(html)

final_kb = os.path.getsize(DASHBOARD) / 1024
print(f'\ndashboard.html updated: {final_kb:.0f} KB')
