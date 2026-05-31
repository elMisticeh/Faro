"""
add_market_report.py
====================
Inserta generateReporteMercado() en dashboard.html:
  - Botón "Reporte de Mercado" en sidebar Demografía
  - Almacena window._lastDemoCenter / _lastDemoRadius
  - 5 páginas A4: Portada KPIs / Oferta / Precios / Presión / Oportunidades
  - Paleta VERTICE-family: cream #faf7f0 + gold #C8A24B
"""
import os, re

SRC  = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dashboard.html')
DOCS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'index.html')

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. Store center + radius when zone is selected ────────────────────────────
OLD_RENDER = """  window._lastDemoStats = s;
  window._lastDemoTitle = title || 'Zona de Influencia';
  window._lastDemoSubtitle = subtitle || '';"""

NEW_RENDER = """  window._lastDemoStats = s;
  window._lastDemoTitle = title || 'Zona de Influencia';
  window._lastDemoSubtitle = subtitle || '';
  // Persiste centro/radio para Reporte de Mercado
  const _rc = document.getElementById('demo-radius');
  if (_rc) window._lastDemoRadius = parseFloat(_rc.value) || 2;"""

html = html.replace(OLD_RENDER, NEW_RENDER)

OLD_ANALYZE = """  renderDemoPanel(stats, nearby.length,
    nearby.length + ' AGEBs · Radio ' + radiusKm + 'km', 'Radio de Influencia');"""
NEW_ANALYZE = """  window._lastDemoCenter = { lat, lng };
  renderDemoPanel(stats, nearby.length,
    nearby.length + ' AGEBs · Radio ' + radiusKm + 'km', 'Radio de Influencia');"""
html = html.replace(OLD_ANALYZE, NEW_ANALYZE)
print('[OK] Centro/radio almacenados en window._lastDemoCenter/_lastDemoRadius')

# ── 2. Add "Reporte de Mercado" button beside demographics PDF button ─────────
OLD_BTN = """    <button class="btn-reporte" onclick="generateReporte()" title="Generar reporte PDF de la zona seleccionada">
      ⬇ Generar Reporte PDF
    </button>`;"""

NEW_BTN = """    <button class="btn-reporte" onclick="generateReporte()" title="Reporte sociodemografico PDF">
      ⬇ Demografico
    </button>
    <button class="btn-reporte" onclick="generateReporteMercado()" title="Reporte de mercado inmobiliario PDF" style="margin-top:6px;background:oklch(67% .12 73);color:#1a1000">
      ⬇ Mercado
    </button>`;"""

html = html.replace(OLD_BTN, NEW_BTN)
print('[OK] Boton Reporte de Mercado agregado al sidebar')

# ── 3. Insert generateReporteMercado() after generateReporte() ends ───────────
ANCHOR = '\nfunction generateReporte() {'

MARKET_FN = r"""
function generateReporteMercado() {
  const CENTER = window._lastDemoCenter;
  const RAD    = window._lastDemoRadius || 2;
  const title  = window._lastDemoTitle  || 'Zona de Influencia';
  const sub    = window._lastDemoSubtitle || '';

  if (!CENTER) { alert('Selecciona una zona en Demografía primero.'); return; }
  if (!(window.allData && allData.length)) { alert('Datos de mercado no cargados. Ve a la tab Mercado primero.'); return; }

  // ── Helpers ────────────────────────────────────────────────────────────────
  function distKm(la1,lo1,la2,lo2){
    const R=6371,dLa=(la2-la1)*Math.PI/180,dLo=(lo2-lo1)*Math.PI/180;
    const a=Math.sin(dLa/2)**2+Math.cos(la1*Math.PI/180)*Math.cos(la2*Math.PI/180)*Math.sin(dLo/2)**2;
    return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
  }
  const fmt  = (n,d=0) => isNaN(n)||n===null ? '—' : (+n).toLocaleString('es-MX',{maximumFractionDigits:d,minimumFractionDigits:d});
  const fmtP = n => isNaN(n)||n===null ? '—' : '$'+fmt(n)+' MXN';
  const sign = n => (n>=0?'+':'')+fmt(n,1)+'%';
  const mediana = arr => { if(!arr.length) return null; const s=[...arr].sort((a,b)=>a-b); return s[Math.floor(s.length/2)]; };
  const pct  = (arr,p) => { if(!arr.length) return null; const s=[...arr].sort((a,b)=>a-b); return s[Math.max(0,Math.floor(s.length*p)-1)]; };
  const today = new Date().toLocaleDateString('es-MX',{year:'numeric',month:'long',day:'numeric'});

  // ── Filter listings in zone ────────────────────────────────────────────────
  const zona = allData.filter(d => d.activo && d.lat && d.lng &&
    distKm(CENTER.lat, CENTER.lng, +d.lat, +d.lng) <= RAD);

  if (zona.length < 3) {
    alert('Pocos listings en esta zona (' + zona.length + '). Amplia el radio o selecciona otra area.');
    return;
  }

  // ── Offer breakdown ────────────────────────────────────────────────────────
  const byTipo = {}, byOp = {}, byPortal = {};
  zona.forEach(d => {
    const t = (d.tipo_inmueble||'otro').replace(/_/g,' ');
    byTipo[t]   = (byTipo[t]   || 0) + 1;
    const o = d.tipo_operacion || 'otro';
    byOp[o]     = (byOp[o]     || 0) + 1;
    const p = (d.pagina_fuente || 'otro').replace('inmuebles24','i24').replace('propiedades','prop.com').replace('mercadolibre','ML');
    byPortal[p] = (byPortal[p] || 0) + 1;
  });
  const sortObj = obj => Object.entries(obj).sort((a,b)=>b[1]-a[1]);
  const total = zona.length;

  // ── Price analysis ─────────────────────────────────────────────────────────
  const ventas    = zona.filter(d => d.tipo_operacion === 'venta' && d.precio_mxn > 0);
  const precios   = ventas.map(d => d.precio_mxn).sort((a,b)=>a-b);
  const medP      = mediana(precios);
  const p25P      = pct(precios,.25);
  const p75P      = pct(precios,.75);
  const p90P      = pct(precios,.90);

  const terrenos  = zona.filter(d => (d.tipo_inmueble||'').startsWith('terreno') && d.precio_x_m2_terreno > 0);
  const pm2s      = terrenos.map(d => d.precio_x_m2_terreno).sort((a,b)=>a-b);
  const medPm2    = mediana(pm2s);
  const BENCH_PM2 = 4850; // benchmark municipal terreno Torreon

  // ── Price pressure (historial_precio) ─────────────────────────────────────
  let conHist=0, bajaron=0, subieron=0, estables=0, sumRed=0;
  zona.forEach(d => {
    let h = d.historial_precio;
    if (typeof h === 'string') { try { h = JSON.parse(h); } catch(e){ h=null; } }
    if (!Array.isArray(h) || h.length < 2) return;
    conHist++;
    const first = h[0].precio || h[0].price || 0;
    const last  = h[h.length-1].precio || h[h.length-1].price || 0;
    if (!first || !last) return;
    if (last < first*0.99)       { bajaron++;  sumRed += ((first-last)/first)*100; }
    else if (last > first*1.005) { subieron++; }
    else                          { estables++; }
  });
  const pctBajaron = conHist ? Math.round(bajaron/conHist*100) : 0;
  const avgRed = bajaron ? sumRed/bajaron : 0;
  const presion = pctBajaron >= 35 ? 'ALTA' : pctBajaron >= 20 ? 'MEDIA' : 'BAJA';
  const presionColor = presion==='ALTA'?'#c0392b': presion==='MEDIA'?'#d68910':'#1e8449';
  const presionBg    = presion==='ALTA'?'#fdecea': presion==='MEDIA'?'#fef9e7':'#eafaf1';

  // ── Opportunities ──────────────────────────────────────────────────────────
  const opps = zona.filter(d => d.es_oportunidad && d.pct_vs_colonia < 0)
    .sort((a,b)=>(a.pct_vs_colonia||0)-(b.pct_vs_colonia||0)).slice(0,6);

  // ── Synthesis bullets ──────────────────────────────────────────────────────
  const benchDiff = medPm2 && BENCH_PM2 ? ((medPm2-BENCH_PM2)/BENCH_PM2)*100 : null;
  const mktPos = benchDiff === null ? 'Sin datos suficientes de terrenos' :
    benchDiff > 15 ? `Zona PREMIUM: pm2 ${sign(benchDiff)} vs benchmark municipal` :
    benchDiff < -15 ? `Zona DESCUENTO: pm2 ${sign(benchDiff)} vs benchmark — posible oportunidad de entrada` :
    `Zona EN MERCADO: pm2 alineado al benchmark municipal (${sign(benchDiff)})`;

  const presionTxt = conHist < 3 ? 'Historial de precios insuficiente para determinar tendencia.' :
    presion==='ALTA' ? `${pctBajaron}% de los listings bajaron precio (prom. ${fmt(avgRed,1)}% de reduccion) — mercado con exceso de oferta.` :
    presion==='MEDIA' ? `${pctBajaron}% de los listings han ajustado precio a la baja — mercado con leve presion vendedora.` :
    `Solo ${pctBajaron}% con reduccion de precio — oferta firme, sin presion de venta.`;

  const opTxt = opps.length
    ? `${opps.length} listado${opps.length>1?'s':''} detectado${opps.length>1?'s':''} por debajo del promedio de su colonia. El mas agresivo: ${fmt(Math.abs(opps[0].pct_vs_colonia),1)}% bajo mercado.`
    : 'No se detectaron oportunidades de precio en esta zona con los datos actuales.';

  // ── Helper: horizontal bar ─────────────────────────────────────────────────
  function hbar(label, val, max, color='#C8A24B') {
    const w = max ? Math.max(2, Math.round(val/max*100)) : 2;
    return `<div style="margin-bottom:7px">
      <div style="display:flex;justify-content:space-between;margin-bottom:3px">
        <span style="font-family:'Mulish',sans-serif;font-size:11px;color:#7a6e5a">${label}</span>
        <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#1a1000;font-weight:500">${val}</span>
      </div>
      <div style="height:5px;background:#e8dfc8;border-radius:3px">
        <div style="height:5px;background:${color};border-radius:3px;width:${w}%;transition:width .3s"></div>
      </div></div>`;
  }

  // ── Percentile row ─────────────────────────────────────────────────────────
  function percRow(label, val, note='') {
    return `<tr>
      <td style="padding:7px 12px;font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.12em;color:#a0936a;text-transform:uppercase">${label}</td>
      <td style="padding:7px 12px;font-family:'IBM Plex Mono',monospace;font-size:13px;color:#1a1000;font-weight:500;text-align:right">${val===null?'—':fmtP(val)}</td>
      <td style="padding:7px 12px;font-family:'Mulish',sans-serif;font-size:11px;color:#7a6e5a">${note}</td>
    </tr>`;
  }

  // ── Logo SVG (inline) ──────────────────────────────────────────────────────
  const logoSVG = `<svg viewBox="0 0 32 32" width="22" height="22" fill="none" stroke="#C8A24B" stroke-linecap="round">
    <circle cx="16" cy="7" r="3" fill="#C8A24B" stroke="none"/>
    <line x1="16" y1="10" x2="16" y2="28" stroke-width="1.8"/>
    <line x1="16" y1="17" x2="7" y2="28" stroke-width="1.2" opacity="0.5"/>
    <line x1="16" y1="17" x2="25" y2="28" stroke-width="1.2" opacity="0.5"/>
  </svg>`;

  const pageStyle = `
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@400;600;700&family=Mulish:wght@300;400;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Mulish',sans-serif;background:#faf7f0;color:#1a1000;-webkit-print-color-adjust:exact;print-color-adjust:exact}
    @page{size:A4 portrait;margin:0}
    .page{width:210mm;min-height:297mm;background:#fff9f2;position:relative;page-break-after:always;display:flex;flex-direction:column;overflow:hidden}
    .page:last-child{page-break-after:auto}
    .ruled{height:1px;background:linear-gradient(90deg,#C8A24B 0%,rgba(200,162,75,.15) 100%)}
    .eyebrow{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:#C8A24B}
    .kpi-val{font-family:'Barlow Semi Condensed',sans-serif;font-size:2.4rem;font-weight:700;color:#1a1000;letter-spacing:-.01em;line-height:1}
    .kpi-label{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:#a0936a;margin-top:4px}
    .section-title{font-family:'Barlow Semi Condensed',sans-serif;font-size:1.15rem;font-weight:700;letter-spacing:.02em;color:#1a1000;margin-bottom:14px}
    .letterhead{padding:18px 28px 14px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e8dfc8}
    .lh-brand{display:flex;align-items:center;gap:9px}
    .lh-wordmark{font-family:'Barlow Semi Condensed',sans-serif;font-weight:700;font-size:1.05rem;letter-spacing:.04em;color:#1a1000}
    .lh-sub{font-family:'IBM Plex Mono',monospace;font-size:8px;letter-spacing:.18em;text-transform:uppercase;color:#C8A24B;margin-left:3px;vertical-align:middle}
    .lh-meta{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#a0936a;text-align:right;line-height:1.6}
    .footer{margin-top:auto;padding:10px 28px;border-top:1px solid #e8dfc8;display:flex;align-items:center;justify-content:space-between}
    .footer-l{font-family:'IBM Plex Mono',monospace;font-size:8px;color:#a0936a;letter-spacing:.06em}
    table{width:100%;border-collapse:collapse}
    tr:nth-child(even){background:#faf7f0}
    th{background:#f0e8d4;font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:#a0936a;padding:7px 12px;text-align:left}
  `;

  function letterhead(pageNum, pageTitle) {
    return `<div class="letterhead">
      <div class="lh-brand">${logoSVG}
        <span class="lh-wordmark">FARO <span class="lh-sub">&middot; COEZA</span></span>
      </div>
      <div class="lh-meta">
        Reporte de Mercado &middot; ${title}<br>
        ${sub} &middot; ${today}
      </div>
    </div>
    <div style="padding:10px 28px 0;display:flex;align-items:baseline;justify-content:space-between">
      <div class="eyebrow">${pageTitle}</div>
      <div style="font-family:'IBM Plex Mono',monospace;font-size:8px;color:#c8b88a">${pageNum}/5</div>
    </div>
    <div style="margin:6px 28px 0"><div class="ruled"></div></div>`;
  }

  function footer(note) {
    return `<div class="footer">
      <span class="footer-l">${note || 'FARO &middot; COEZA Consulting &middot; Datos scraping semanal + INEGI 2020'}</span>
      <span style="font-family:'IBM Plex Mono',monospace;font-size:8px;color:#C8A24B;letter-spacing:.06em">FARO</span>
    </div>`;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PAGE 1 — PORTADA
  // ═══════════════════════════════════════════════════════════════════════════
  const PAGE1 = `<div class="page">
    <div style="flex:1;display:flex;flex-direction:column;padding:0">
      <!-- COVER HEADER -->
      <div style="background:linear-gradient(135deg,#1a1000 0%,#2d2010 60%,#3d2e14 100%);padding:44px 44px 36px;position:relative;overflow:hidden">
        <div style="position:absolute;top:-30px;right:-30px;width:220px;height:220px;border-radius:50%;border:1px solid rgba(200,162,75,.18)"></div>
        <div style="position:absolute;top:20px;right:20px;width:120px;height:120px;border-radius:50%;border:1px solid rgba(200,162,75,.12)"></div>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:28px">
          ${logoSVG}
          <span style="font-family:'Barlow Semi Condensed',sans-serif;font-weight:700;font-size:1.1rem;letter-spacing:.06em;color:#fff9f2">FARO</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-size:8px;letter-spacing:.2em;text-transform:uppercase;color:#C8A24B">&middot; COEZA Consulting</span>
        </div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:#C8A24B;margin-bottom:10px">Reporte de Mercado Inmobiliario</div>
        <div style="font-family:'Barlow Semi Condensed',sans-serif;font-size:2.4rem;font-weight:700;color:#fff9f2;letter-spacing:.01em;line-height:1.05;margin-bottom:6px">${title}</div>
        <div style="font-family:'Mulish',sans-serif;font-size:13px;color:rgba(255,249,242,.6)">${sub} &mdash; ${today}</div>
      </div>
      <!-- 4 KPIs -->
      <div style="padding:28px 44px 0;display:grid;grid-template-columns:repeat(4,1fr);gap:20px">
        ${[
          ['Oferta Activa',  fmt(total),         'listings en zona'],
          ['Precio Mediano', medP ? '$'+fmt(medP/1000000,2)+'M' : '—', 'MXN venta'],
          ['Pres. Mercado',  presion,             pctBajaron+'% bajaron precio'],
          ['Oportunidades',  fmt(opps.length),    'bajo precio de mercado'],
        ].map(([lbl,val,note]) => `
          <div style="background:#fff9f2;border:1px solid #e8dfc8;border-radius:8px;padding:16px 18px">
            <div class="kpi-val">${val}</div>
            <div class="kpi-label">${lbl}</div>
            <div style="font-family:'Mulish',sans-serif;font-size:10px;color:#a0936a;margin-top:3px">${note}</div>
          </div>`).join('')}
      </div>
      <!-- Divider -->
      <div style="margin:22px 44px 0"><div class="ruled"></div></div>
      <!-- Resumen tipología -->
      <div style="padding:18px 44px 0;display:grid;grid-template-columns:1fr 1fr;gap:24px">
        <div>
          <div class="eyebrow" style="margin-bottom:10px">Por tipo de inmueble</div>
          ${sortObj(byTipo).slice(0,5).map(([k,v])=>hbar(k.replace(/\b\w/g,c=>c.toUpperCase()),v,total)).join('')}
        </div>
        <div>
          <div class="eyebrow" style="margin-bottom:10px">Por portal</div>
          ${sortObj(byPortal).slice(0,5).map(([k,v])=>hbar(k,v,total,'#a0936a')).join('')}
        </div>
      </div>
    </div>
    ${footer('FARO &middot; COEZA Consulting &middot; Fuente: scraping semanal portales inmobiliarios')}
  </div>`;

  // ═══════════════════════════════════════════════════════════════════════════
  // PAGE 2 — OFERTA DETALLADA
  // ═══════════════════════════════════════════════════════════════════════════
  const rentasZona = zona.filter(d=>d.tipo_operacion==='renta');
  const ventasZona = zona.filter(d=>d.tipo_operacion==='venta');

  const PAGE2 = `<div class="page">
    ${letterhead('2','Pulso de Oferta')}
    <div style="padding:20px 28px;flex:1;display:grid;grid-template-columns:1fr 1fr;gap:24px;align-content:start">
      <!-- Col izq -->
      <div>
        <div class="section-title">Inventario por tipo</div>
        ${sortObj(byTipo).map(([k,v])=>hbar(k.replace(/\b\w/g,c=>c.toUpperCase()),v,total)).join('')}
        <div style="margin-top:18px"><div class="ruled"></div></div>
        <div style="margin-top:14px">
          <div class="section-title">Venta vs Renta</div>
          ${hbar('Venta', ventasZona.length, total, '#C8A24B')}
          ${hbar('Renta', rentasZona.length, total, '#d4a96a')}
          <div style="margin-top:10px;font-family:'Mulish',sans-serif;font-size:11px;color:#7a6e5a">
            ${Math.round(ventasZona.length/total*100)}% de la oferta es venta. ${ventasZona.length >= rentasZona.length*3 ? 'Mercado orientado a venta.' : 'Mix equilibrado venta/renta.'}
          </div>
        </div>
      </div>
      <!-- Col der -->
      <div>
        <div class="section-title">Fuentes de oferta</div>
        ${sortObj(byPortal).map(([k,v])=>hbar(k,v,total,'#a0936a')).join('')}
        <div style="margin-top:8px;font-family:'Mulish',sans-serif;font-size:11px;color:#7a6e5a;line-height:1.5">
          ${sortObj(byPortal)[0] ? `<b>${sortObj(byPortal)[0][0]}</b> lidera con ${Math.round(sortObj(byPortal)[0][1]/total*100)}% de la oferta en esta zona.` : ''} ${sortObj(byPortal).length >= 3 ? 'Mercado multi-portal: datos representativos.' : 'Oferta concentrada en pocos portales.'}
        </div>
        <div style="margin-top:18px"><div class="ruled"></div></div>
        <div style="margin-top:14px">
          <div class="section-title">Indicadores clave</div>
          ${[
            ['Listings activos en zona', fmt(total)],
            ['En venta', fmt(ventasZona.length)],
            ['En renta', fmt(rentasZona.length)],
            ['Terrenos', fmt(terrenos.length)],
            ['Con historial de precio', fmt(conHist)],
          ].map(([l,v])=>`<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f0e8d4">
            <span style="font-family:'Mulish',sans-serif;font-size:11px;color:#7a6e5a">${l}</span>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:500;color:#1a1000">${v}</span>
          </div>`).join('')}
        </div>
      </div>
    </div>
    ${footer()}
  </div>`;

  // ═══════════════════════════════════════════════════════════════════════════
  // PAGE 3 — ANÁLISIS DE PRECIOS
  // ═══════════════════════════════════════════════════════════════════════════
  const benchDiffTxt = benchDiff !== null
    ? (benchDiff>0?'<span style="color:#c0392b">+'+fmt(benchDiff,1)+'%</span> sobre benchmark':'<span style="color:#1e8449">'+fmt(benchDiff,1)+'%</span> bajo benchmark')
    : '—';

  const PAGE3 = `<div class="page">
    ${letterhead('3','Analisis de Precios')}
    <div style="padding:20px 28px;flex:1;display:grid;grid-template-columns:1fr 1fr;gap:24px;align-content:start">
      <div>
        <div class="section-title">Precio de venta — distribución</div>
        <table>
          <thead><tr><th>Percentil</th><th style="text-align:right">Precio</th><th>Interpretación</th></tr></thead>
          <tbody>
            ${percRow('P25 — 25%', p25P, 'Cuartil inferior del mercado')}
            ${percRow('P50 — Mediana', medP, 'Precio típico de la zona')}
            ${percRow('P75 — 75%', p75P, 'Segmento premium')}
            ${percRow('P90 — Tope', p90P, 'Límite superior del mercado')}
          </tbody>
        </table>
        <div style="margin-top:10px;font-family:'Mulish',sans-serif;font-size:11px;color:#7a6e5a;line-height:1.5">
          Rango intercuartil (P25–P75): ${p25P&&p75P ? fmtP(p25P)+' — '+fmtP(p75P) : '—'}. El 50% de la oferta se concentra en esta banda de precios.
        </div>
      </div>
      <div>
        <div class="section-title">Precio por m² terreno</div>
        <div style="background:#fff9f2;border:1px solid #e8dfc8;border-radius:8px;padding:18px;margin-bottom:14px">
          <div class="kpi-val">${medPm2 ? '$'+fmt(medPm2) : '—'}</div>
          <div class="kpi-label">Mediana pm² terreno</div>
          <div style="font-family:'Mulish',sans-serif;font-size:11px;color:#a0936a;margin-top:6px">
            Benchmark municipal: $${fmt(BENCH_PM2)} &mdash; esta zona: ${benchDiffTxt}
          </div>
        </div>
        ${medPm2 ? `
        <div style="margin-top:4px">
          ${[
            ['Benchmark municipal', BENCH_PM2, '#e8dfc8'],
            ['Esta zona (mediana)', medPm2, '#C8A24B'],
          ].map(([l,v,c])=>`<div style="margin-bottom:8px">
            <div style="display:flex;justify-content:space-between;margin-bottom:3px">
              <span style="font-family:'Mulish',sans-serif;font-size:10px;color:#7a6e5a">${l}</span>
              <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#1a1000">$${fmt(v)}/m²</span>
            </div>
            <div style="height:6px;background:#f0e8d4;border-radius:3px">
              <div style="height:6px;background:${c};border-radius:3px;width:${Math.min(100,Math.round(v/Math.max(medPm2,BENCH_PM2)*90))}%"></div>
            </div></div>`).join('')}
        </div>` : '<div style="font-family:\'Mulish\',sans-serif;font-size:11px;color:#a0936a">Insuficientes terrenos con datos de pm² en esta zona.</div>'}
        <div style="margin-top:16px"><div class="ruled"></div></div>
        <div style="margin-top:12px;padding:12px;background:${benchDiff&&benchDiff<-15?'#eafaf1':benchDiff&&benchDiff>15?'#fdecea':'#faf7f0'};border-radius:6px;border-left:3px solid ${benchDiff&&benchDiff<-15?'#1e8449':benchDiff&&benchDiff>15?'#c0392b':'#C8A24B'}">
          <div style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:#a0936a;margin-bottom:4px">Posición de mercado</div>
          <div style="font-family:'Mulish',sans-serif;font-size:12px;color:#1a1000;line-height:1.5">${mktPos}</div>
        </div>
      </div>
    </div>
    ${footer('Precios en MXN. Benchmark municipal basado en datos DATERRA/INEGI 2020. N=' + fmt(ventas.length) + ' ventas.')}
  </div>`;

  // ═══════════════════════════════════════════════════════════════════════════
  // PAGE 4 — PRESIÓN DE MERCADO
  // ═══════════════════════════════════════════════════════════════════════════
  const PAGE4 = `<div class="page">
    ${letterhead('4','Presion de Mercado')}
    <div style="padding:20px 28px;flex:1">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:20px">
        <!-- Semáforo presión -->
        <div style="background:#fff9f2;border:1px solid #e8dfc8;border-radius:8px;padding:20px;text-align:center">
          <div style="font-family:'Barlow Semi Condensed',sans-serif;font-size:3rem;font-weight:700;color:${presionColor};letter-spacing:.04em">${presion}</div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:#a0936a;margin-top:4px">Presión de mercado</div>
          <div style="margin-top:12px;font-family:'Mulish',sans-serif;font-size:12px;color:#7a6e5a;line-height:1.5">${presionTxt}</div>
        </div>
        <!-- Stats de historial -->
        <div>
          <div class="section-title">Análisis de historial de precios</div>
          ${conHist < 3 ? '<div style="font-family:\'Mulish\',sans-serif;font-size:12px;color:#a0936a;padding:16px 0">Historial insuficiente para análisis estadístico.<br>Se requieren al menos 3 semanas de datos.</div>' :
          [
            ['Listings con historial', fmt(conHist), '100%'],
            ['Bajaron precio', fmt(bajaron), fmt(pctBajaron)+'%'],
            ['Subieron precio', fmt(subieron), fmt(conHist?Math.round(subieron/conHist*100):0)+'%'],
            ['Sin cambios', fmt(estables), fmt(conHist?Math.round(estables/conHist*100):0)+'%'],
          ].map(([l,v,p])=>`<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f0e8d4">
            <span style="font-family:'Mulish',sans-serif;font-size:11px;color:#7a6e5a">${l}</span>
            <div style="display:flex;gap:14px">
              <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#1a1000;font-weight:500">${v}</span>
              <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#a0936a;width:36px;text-align:right">${p}</span>
            </div></div>`).join('')}
          ${bajaron>0?`<div style="margin-top:10px;padding:8px 10px;background:#faf7f0;border-radius:5px;font-family:'Mulish',sans-serif;font-size:11px;color:#7a6e5a">Reducción promedio: <b style="color:#1a1000">${fmt(avgRed,1)}%</b> del precio original</div>`:''}
        </div>
      </div>
      <div><div class="ruled"></div></div>
      <!-- Interpretación -->
      <div style="margin-top:16px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
        ${[
          ['Presión baja (< 20%)', 'Oferta firme. Vendedores no ceden precio. Puede indicar escasez real o sobrevaluación sostenida.', '#1e8449'],
          ['Presión media (20-35%)', 'Ajuste normal de mercado. Algunos vendedores flexibles. Buen momento para negociar.', '#d68910'],
          ['Presión alta (> 35%)', 'Exceso de oferta o urgencia de venta. Oportunidad para compradores con capital listo.', '#c0392b'],
        ].map(([t,d,c])=>`<div style="background:#fff9f2;border-top:3px solid ${c};border-radius:0 0 7px 7px;padding:12px">
          <div style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.1em;color:${c};text-transform:uppercase;margin-bottom:5px">${t}</div>
          <div style="font-family:'Mulish',sans-serif;font-size:11px;color:#7a6e5a;line-height:1.5">${d}</div>
        </div>`).join('')}
      </div>
    </div>
    ${footer('Basado en historial_precio scrapeado semanalmente. N=' + fmt(conHist) + ' listings con historial.')}
  </div>`;

  // ═══════════════════════════════════════════════════════════════════════════
  // PAGE 5 — OPORTUNIDADES + SÍNTESIS
  // ═══════════════════════════════════════════════════════════════════════════
  const PAGE5 = `<div class="page">
    ${letterhead('5','Oportunidades y Sintesis')}
    <div style="padding:16px 28px;flex:1">
      <div class="section-title">Oportunidades detectadas &mdash; precio bajo mercado</div>
      ${opps.length === 0
        ? `<div style="padding:20px;text-align:center;font-family:'Mulish',sans-serif;font-size:13px;color:#a0936a">No se detectaron oportunidades en esta zona con los datos actuales.</div>`
        : `<table style="margin-bottom:16px">
          <thead><tr>
            <th>Colonia</th><th>Tipo</th><th>Precio</th><th>vs Colonia</th><th>Portal</th>
          </tr></thead>
          <tbody>
          ${opps.map(d=>`<tr>
            <td style="padding:7px 12px;font-family:'Mulish',sans-serif;font-size:11px;color:#1a1000">${d.colonia||'—'}</td>
            <td style="padding:7px 12px;font-family:'Mulish',sans-serif;font-size:11px;color:#7a6e5a">${(d.tipo_inmueble||'').replace(/_/g,' ')}</td>
            <td style="padding:7px 12px;font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:500;color:#1a1000">$${fmt(d.precio_mxn)}</td>
            <td style="padding:7px 12px;font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:600;color:#1e8449">${fmt(d.pct_vs_colonia,1)}%</td>
            <td style="padding:7px 12px;font-family:'IBM Plex Mono',monospace;font-size:10px;color:#a0936a">${d.pagina_fuente||'—'}</td>
          </tr>`).join('')}
          </tbody>
        </table>`}
      <div><div class="ruled"></div></div>
      <!-- Síntesis ejecutiva -->
      <div style="margin-top:14px">
        <div class="eyebrow" style="margin-bottom:10px">Síntesis ejecutiva</div>
        <div style="display:flex;flex-direction:column;gap:8px">
          ${[
            ['01', 'Posición de precios', mktPos],
            ['02', 'Dinámica de mercado', presionTxt],
            ['03', 'Oportunidades', opTxt],
          ].map(([n,t,d])=>`<div style="display:flex;gap:12px;padding:10px 14px;background:#fff9f2;border-radius:7px;border-left:2px solid #C8A24B">
            <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#C8A24B;font-weight:500;flex-shrink:0;padding-top:1px">${n}</div>
            <div>
              <div style="font-family:'Barlow Semi Condensed',sans-serif;font-size:.92rem;font-weight:600;color:#1a1000;margin-bottom:2px">${t}</div>
              <div style="font-family:'Mulish',sans-serif;font-size:11px;color:#7a6e5a;line-height:1.5">${d}</div>
            </div></div>`).join('')}
        </div>
      </div>
    </div>
    ${footer('FARO &middot; COEZA Consulting &middot; Inteligencia Inmobiliaria Torreón &middot; ' + today)}
  </div>`;

  // ── Assemble & Open ────────────────────────────────────────────────────────
  const fullHTML = `<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
  <title>Reporte de Mercado FARO — ${title}</title>
  <style>${pageStyle}</style></head><body>
  ${PAGE1}${PAGE2}${PAGE3}${PAGE4}${PAGE5}
  <script>window.onload=()=>window.print();<\/script>
  </body></html>`;

  const w = window.open('', '_blank', 'width=900,height=700');
  if (!w) { alert('El navegador bloqueó el popup. Permite popups para este sitio.'); return; }
  w.document.write(fullHTML);
  w.document.close();
}

"""

html = html.replace(ANCHOR, MARKET_FN + ANCHOR)
print('[OK] generateReporteMercado() insertado')

# ── Write output ──────────────────────────────────────────────────────────────
for path, name in [(SRC, 'dashboard.html'), (DOCS, 'index.html')]:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    size_kb = os.path.getsize(path) / 1024
    print(f'[OK] Written: {name} ({size_kb:.0f} KB)')

print('\nDone. Reporte de Mercado listo.')
