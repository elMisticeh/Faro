#!/usr/bin/env python3
"""
add_report_generator.py
Inserts generateReporte() function + button into dashboard.html.
Adds DATERRA-style PDF zone report generation via browser print.
"""

import re, sys, os

SRC = r'C:\proyectos\real-estate\frontend\dashboard.html'
DST_DOCS = r'C:\proyectos\real-estate\docs\index.html'

BUTTON_CSS = """
  .btn-reporte {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    width: 100%; margin-top: 14px; padding: 10px 16px;
    background: var(--accent); color: oklch(99% 0.003 264);
    border: none; border-radius: 8px; cursor: pointer;
    font-size: 13px; font-weight: 700; letter-spacing: 0.02em;
    transition: background 0.18s, box-shadow 0.18s;
    box-shadow: var(--shadow-sm);
  }
  .btn-reporte:hover { background: var(--accent2); box-shadow: var(--shadow); }
"""

REPORT_JS = r'''
function generateReporte() {
  const s = window._lastDemoStats;
  const title = window._lastDemoTitle || 'Zona de Influencia';
  const subtitle = window._lastDemoSubtitle || '';
  if (!s) { alert('Selecciona una zona primero.'); return; }

  const b = {"pob_total":700595,"hog_total":209771,"viv_habitadas":209864,"viv_total":254420,
    "pea":348898,"escolaridad":11.12,"densidad_pob":4472.2,"pct_pea":49.8,"pct_viv_des":14.6,
    "pct_0_14":24.6,"pct_15_24":16.8,"pct_25_59":46.5,"pct_60mas":12.2,"crec_pob":13.2,
    "crec_hog":29.0,"crec_viv":-3.3,"prom_hnv":1.93};

  const fmt = (n, d) => isNaN(n) ? '—' : (+n).toLocaleString('es-MX', {maximumFractionDigits:d||0, minimumFractionDigits:d||0});
  const sign = n => (n >= 0 ? '+' : '') + fmt(n, 1) + '%';
  const score = calcScore(s);
  const [slbl] = scoreLabel(score);

  // Score colors (inline, no CSS vars)
  const scoreColor = score >= 8 ? '#22863a' : score >= 6 ? '#1a6ab2' : score >= 4 ? '#1c2878' : '#b43a2a';
  const scoreBg = score >= 8 ? '#e6f4ea' : score >= 6 ? '#ddeeff' : score >= 4 ? '#eaeeff' : '#fdecea';

  // NSE helpers
  const pct_alto = s.nse_total ? (s.nse_ab + s.nse_cmas) / s.nse_total * 100 : 0;
  const pct_c    = s.nse_total ? s.nse_c / s.nse_total * 100 : 0;
  const pct_bajo = s.nse_total ? (s.nse_cmenos + s.nse_dmas + s.nse_d + s.nse_e) / s.nse_total * 100 : 0;

  // Buyer persona logic
  let nseLabel, ingresoRange, precioRange, productType, habitType;
  if (pct_alto >= 30) {
    nseLabel='A/B + C+'; ingresoRange='$35,000–$85,000+/mes'; precioRange='$3.5M–$7M+';
    productType='Residencial Plus / Premium'; habitType='Departamento o casa de lujo, amenidades completas';
  } else if (pct_alto >= 15) {
    nseLabel='C+ dominante'; ingresoRange='$35,000–$85,000/mes'; precioRange='$2.5M–$5M';
    productType='Residencial / Residencial Plus'; habitType='Departamento 2-3 rec, fraccionamiento cerrado';
  } else if (pct_c >= 30) {
    nseLabel='C predominante'; ingresoRange='$11,600–$35,000/mes'; precioRange='$1M–$2.5M';
    productType='Vivienda Media'; habitType='Casa o depto accesible, crédito hipotecario viable';
  } else {
    nseLabel='C− / D+'; ingresoRange='$6,800–$11,600/mes'; precioRange='$500K–$1.2M';
    productType='Vivienda Popular / Interés Social'; habitType='Vivienda mínima, subsidio/Infonavit';
  }

  let agePerfil;
  if (s.pct_60 >= 20) agePerfil = 'Población envejecida (60+: ' + fmt(s.pct_60,1) + '%). Producto accesible, planta baja, servicios de salud cercanos.';
  else if (s.pct_25_59 >= 46) agePerfil = 'Adultos activos 25–59 años dominantes (' + fmt(s.pct_25_59,1) + '%). Compradores con ingreso y familia en formación.';
  else agePerfil = 'Cohorte joven 15–24 años relevante (' + fmt(s.pct_15_24,1) + '%). Mercado de renta y primera vivienda en próximos 5–10 años.';

  // Narrative bullets for dinámica territorial
  const bullets = [];
  if (s.crec_pob < 0)
    bullets.push({type:'warn', text:'La población registró una <strong>contracción de ' + fmt(Math.abs(s.crec_pob),1) + '%</strong> entre 2010–2020 (municipio: ' + sign(b.crec_pob) + '). Puede indicar migración hacia zonas periféricas o deterioro del parque habitacional.'});
  else if (s.crec_pob > 30)
    bullets.push({type:'ok', text:'La zona registró un <strong>crecimiento acelerado de +' + fmt(s.crec_pob,1) + '%</strong> en población (municipio: ' + sign(b.crec_pob) + '). Mercado en expansión activa.'});
  else
    bullets.push({type:'info', text:'Crecimiento de población <strong>' + sign(s.crec_pob) + '</strong> entre 2010–2020 (municipio: ' + sign(b.crec_pob) + '). Dinámica comparable al promedio municipal.'});

  if (s.pct_viv_des > 20)
    bullets.push({type:'warn', text:'Vacancia alta: <strong>' + fmt(s.pct_viv_des,1) + '%</strong> de viviendas deshabitadas (umbral referencia: 12%). Evaluar demanda real antes de agregar oferta nueva.'});
  else if (s.pct_viv_des > 12)
    bullets.push({type:'info', text:'Vacancia moderada: <strong>' + fmt(s.pct_viv_des,1) + '%</strong> de viviendas deshabitadas. Monitorear absorción antes de desarrollar nueva oferta.'});
  else
    bullets.push({type:'ok', text:'Vacancia saludable: <strong>' + fmt(s.pct_viv_des,1) + '%</strong> de viviendas deshabitadas. El parque habitacional está siendo utilizado activamente.'});

  if (s.pct_60 > 20)
    bullets.push({type:'warn', text:'Zona con <strong>población envejecida</strong>: ' + fmt(s.pct_60,1) + '% mayores de 60 años (vs ' + fmt(b.pct_60mas,1) + '% municipal). Demanda de unidades compactas en planta baja y proximidad a servicios de salud.'});

  if (s.pct_viv_tmp > 5)
    bullets.push({type:'info', text:'Viviendas de uso temporal: <strong>' + fmt(s.pct_viv_tmp,1) + '%</strong> del parque. Señal de mercado vacacional o segunda residencia. Evaluar impacto en disponibilidad de vivienda permanente.'});

  if (pct_alto >= 30)
    bullets.push({type:'ok', text:'Concentración NSE alto (A/B + C+): <strong>' + fmt(pct_alto,1) + '%</strong> de viviendas clasificadas. Capacidad de pago sólida para vivienda residencial media-alta.'});

  // Score breakdown
  const scoreItems = [];
  const crec_pts = s.crec_pob > 0 ? 2 : s.crec_pob > -10 ? 1 : 0;
  scoreItems.push({label:'Crecimiento Poblacional', pts:crec_pts, max:2,
    detail: crec_pts===2?'Crecimiento positivo': crec_pts===1?'Contracción leve (<10%)':'Contracción significativa'});
  const age_pts = s.pct_25_59 >= 44 ? 2 : s.pct_25_59 >= 35 ? 1 : 0;
  scoreItems.push({label:'Cohorte Compradora 25–59', pts:age_pts, max:2,
    detail: age_pts===2?fmt(s.pct_25_59,1)+'% (umbral: 44%+)': age_pts===1?fmt(s.pct_25_59,1)+'% (umbral: 35%+)':fmt(s.pct_25_59,1)+'% (bajo umbral mínimo)'});
  const viv_pts = s.pct_viv_h >= 80 ? 2 : s.pct_viv_h >= 65 ? 1 : 0;
  scoreItems.push({label:'Ocupación Habitacional', pts:viv_pts, max:2,
    detail: viv_pts===2?fmt(s.pct_viv_h,1)+'% habitadas (umbral: 80%+)': viv_pts===1?fmt(s.pct_viv_h,1)+'% habitadas (umbral: 65%+)':fmt(s.pct_viv_h,1)+'% habitadas (baja ocupación)'});
  const pea_pts = s.pct_pea >= 50 ? 2 : s.pct_pea >= 40 ? 1 : 0;
  scoreItems.push({label:'Actividad Económica (PEA)', pts:pea_pts, max:2,
    detail: pea_pts===2?fmt(s.pct_pea,1)+'% PEA activa (umbral: 50%+)': pea_pts===1?fmt(s.pct_pea,1)+'% PEA activa (umbral: 40%+)':fmt(s.pct_pea,1)+'% PEA (baja actividad)'});
  const nse_pts = pct_alto >= 30 ? 2 : pct_alto >= 15 ? 1 : 0;
  scoreItems.push({label:'NSE Medio-Alto (A/B + C+)', pts:nse_pts, max:2,
    detail: nse_pts===2?fmt(pct_alto,1)+'% de viviendas (umbral: 30%+)': nse_pts===1?fmt(pct_alto,1)+'% de viviendas (umbral: 15%+)':fmt(pct_alto,1)+'% (concentración baja)'});

  // Recommendations
  const recs = [];
  if (pct_alto >= 30) {
    recs.push({icon:'🏢', text:'<strong>Vivienda Residencial Plus o Premium:</strong> La capacidad de pago NSE A/B+C+ sustenta precios ' + precioRange + '. Producto con amenidades diferenciadas (lobby, gym, área pet-friendly).'});
    recs.push({icon:'📐', text:'<strong>Departamentos 60–90m²:</strong> Cohorte 25–59 años dominante con familias en formación. Priorizar 2–3 recámaras, bodega y 1.5+ cajones.'});
  } else if (pct_alto >= 15) {
    recs.push({icon:'🏠', text:'<strong>Vivienda Residencial Accesible:</strong> Rango sugerido ' + precioRange + '. Evitar lujo excesivo; enfocarse en funcionalidad y ubicación.'});
  } else {
    recs.push({icon:'🏘️', text:'<strong>Vivienda Media o Interés Social:</strong> NSE C/C− dominante. Precio techo ' + precioRange + '. Viable con esquemas Infonavit o subsidio.'});
  }

  if (s.pct_60 >= 20)
    recs.push({icon:'♿', text:'<strong>Accesibilidad Universal:</strong> Alta población 60+ demanda plantas bajas, rampas, sin escaleras, proximidad a servicios de salud y transporte.'});

  if (s.pct_viv_des > 20)
    recs.push({icon:'⚠️', text:'<strong>Precaución en oferta nueva:</strong> Vacancia ' + fmt(s.pct_viv_des,1) + '% supera umbral de alerta (12%). Validar absorción del mercado antes de comprometer desarrollo.'});

  if (s.pct_viv_tmp > 5)
    recs.push({icon:'🏖️', text:'<strong>Oportunidad de renta corta:</strong> ' + fmt(s.pct_viv_tmp,1) + '% de uso temporal puede indicar demanda de Airbnb o segunda residencia. Validar con datos AIRDNA.'});

  recs.push({icon:'📊', text:'<strong>Benchmark de competencia:</strong> Complementar este análisis sociodemográfico con levantamiento de proyectos activos en la zona (absorción, precios/m², vacío de mercado).'});

  // ---- Build SVG helpers ----
  function hBar(pct, color, maxW) {
    const w = Math.min(Math.max(pct, 0), 100) / 100 * (maxW || 200);
    return '<rect x="0" y="0" width="' + w.toFixed(1) + '" height="12" rx="3" fill="' + color + '"/>';
  }

  function nseDonut(items, total) {
    if (!total) return '<circle cx="60" cy="60" r="50" fill="#eee"/>';
    let angle = -Math.PI / 2;
    const R = 50, cx = 60, cy = 60;
    const colors = {'A/B':'#8b5cf6','C+':'#3b82f6','C':'#22d3ee','C-':'#4ade80','D+':'#a3e635','D':'#facc15','E':'#f97316'};
    let paths = '';
    items.forEach(item => {
      if (!item.count) return;
      const sweep = (item.count / total) * 2 * Math.PI;
      const x1 = cx + R * Math.cos(angle);
      const y1 = cy + R * Math.sin(angle);
      const x2 = cx + R * Math.cos(angle + sweep);
      const y2 = cy + R * Math.sin(angle + sweep);
      const large = sweep > Math.PI ? 1 : 0;
      paths += '<path d="M' + cx + ' ' + cy + ' L' + x1.toFixed(1) + ' ' + y1.toFixed(1) +
        ' A' + R + ' ' + R + ' 0 ' + large + ' 1 ' + x2.toFixed(1) + ' ' + y2.toFixed(1) + ' Z"' +
        ' fill="' + (colors[item.label] || '#ccc') + '" stroke="white" stroke-width="1.5"/>';
      angle += sweep;
    });
    return paths + '<circle cx="' + cx + '" cy="' + cy + '" r="28" fill="white"/>';
  }

  const nseItems = [
    {label:'A/B', count:s.nse_ab, color:'#8b5cf6'},
    {label:'C+',  count:s.nse_cmas, color:'#3b82f6'},
    {label:'C',   count:s.nse_c, color:'#22d3ee'},
    {label:'C-',  count:s.nse_cmenos, color:'#4ade80'},
    {label:'D+',  count:s.nse_dmas, color:'#a3e635'},
    {label:'D',   count:s.nse_d, color:'#facc15'},
    {label:'E',   count:s.nse_e, color:'#f97316'},
  ].filter(x => x.count > 0);

  const today = new Date().toLocaleDateString('es-MX', {day:'2-digit', month:'long', year:'numeric'});

  const html = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Reporte CAMPO — ${title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', system-ui, sans-serif; background: #fff; color: #1a1a2e; font-size: 10pt; line-height: 1.5; }

  /* PAGE STRUCTURE */
  .page { width: 210mm; min-height: 297mm; padding: 14mm 16mm; position: relative;
    page-break-after: always; display: flex; flex-direction: column; }
  .page:last-child { page-break-after: auto; }

  /* HEADER BAND */
  .page-header { display: flex; justify-content: space-between; align-items: flex-start;
    margin-bottom: 10mm; border-bottom: 2px solid #1c2878; padding-bottom: 4mm; }
  .logo-mark { font-size: 18pt; font-weight: 900; color: #1c2878; letter-spacing: -0.5px; }
  .logo-mark em { font-style: normal; color: #1a6ab2; font-weight: 600; }
  .report-meta { text-align: right; font-size: 7.5pt; color: #666; line-height: 1.6; }
  .report-meta strong { color: #1c2878; font-size: 8.5pt; }

  /* SECTION LABEL */
  .section-label { font-size: 7pt; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase;
    color: #1a6ab2; margin-bottom: 1.5mm; }
  .section-title { font-size: 15pt; font-weight: 800; color: #1a1a2e; margin-bottom: 5mm; }
  .section-sub   { font-size: 10pt; font-weight: 400; color: #555; margin-top: -3mm; margin-bottom: 5mm; }

  /* SCORE BADGE */
  .score-badge { display: inline-flex; align-items: center; gap: 10px;
    padding: 6px 16px 6px 12px; border-radius: 10px; margin-bottom: 6mm; }
  .score-num { font-size: 36pt; font-weight: 900; line-height: 1; }
  .score-denom { font-size: 16pt; font-weight: 500; opacity: 0.6; }
  .score-label { font-size: 12pt; font-weight: 800; letter-spacing: 0.05em; }
  .score-source { font-size: 7.5pt; color: #888; margin-top: 1px; }

  /* KPI GRID */
  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3mm; margin-bottom: 6mm; }
  .kpi-card { background: #f4f7ff; border: 1px solid #dde4f5; border-radius: 8px; padding: 3mm 4mm; }
  .kpi-val  { font-size: 14pt; font-weight: 800; color: #1c2878; display: block; }
  .kpi-lbl  { font-size: 7pt; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }

  /* COMPARISON BARS */
  .cmp-section { margin-bottom: 5mm; }
  .cmp-title { font-size: 8.5pt; font-weight: 700; color: #1a1a2e; margin-bottom: 3mm;
    text-transform: uppercase; letter-spacing: 0.08em; }
  .cmp-row { margin-bottom: 3.5mm; }
  .cmp-name { font-size: 9pt; font-weight: 600; color: #1a1a2e; margin-bottom: 1.5mm;
    display: flex; justify-content: space-between; }
  .cmp-name span { font-weight: 400; font-size: 8.5pt; }
  .bar-track { background: #eaeff8; border-radius: 4px; height: 7px; margin-bottom: 2px; position: relative; }
  .bar-fill  { height: 7px; border-radius: 4px; transition: width 0s; }
  .bar-lbl   { font-size: 7pt; color: #888; margin-bottom: 1px; }
  .neg-bar   { background: #e55; }
  .zona-bar  { background: #1c2878; }
  .mun-bar   { background: #a0aec0; }

  /* BULLETS / ALERTS */
  .bullet { display: flex; gap: 7px; margin-bottom: 3.5mm; padding: 3.5mm 4mm;
    border-radius: 7px; font-size: 9pt; line-height: 1.55; }
  .bullet.warn { background: #fff8e6; border-left: 3px solid #e8a000; }
  .bullet.ok   { background: #e9f7ef; border-left: 3px solid #27ae60; }
  .bullet.info { background: #eef3ff; border-left: 3px solid #1a6ab2; }
  .bullet-icon { font-size: 11pt; flex-shrink: 0; margin-top: 1px; }

  /* NSE BAR */
  .nse-bar-wrap { display: flex; height: 14px; border-radius: 6px; overflow: hidden; margin: 3mm 0; }
  .nse-seg { height: 100%; }
  .nse-legend { display: flex; flex-wrap: wrap; gap: 6px; }
  .nse-pill { display: flex; align-items: center; gap: 4px; font-size: 8pt; }
  .nse-dot  { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

  /* AGE PYRAMID */
  .pyramid-wrap { margin: 3mm 0; }
  .age-row  { display: flex; align-items: center; gap: 4mm; margin-bottom: 1.5mm; }
  .age-lbl  { font-size: 8pt; font-weight: 600; width: 28mm; text-align: right; color: #333; }
  .age-bars { display: flex; gap: 2mm; align-items: center; }
  .age-bar  { height: 10px; border-radius: 3px; }
  .age-val  { font-size: 7.5pt; color: #666; width: 22px; }
  .age-legend { display: flex; gap: 10mm; margin-top: 3mm; font-size: 8pt; color: #666; }
  .age-legend span { display: flex; align-items: center; gap: 4px; }
  .age-legend .dot { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }

  /* FAMILY STATUS */
  .family-row { display: flex; align-items: center; gap: 3mm; margin-bottom: 2.5mm; }
  .family-lbl { font-size: 9pt; font-weight: 600; width: 32mm; }
  .family-track { flex: 1; background: #eaeff8; border-radius: 4px; height: 8px; }
  .family-fill  { height: 8px; border-radius: 4px; background: #1c2878; }
  .family-pct   { font-size: 9pt; font-family: monospace; width: 20mm; text-align: right; color: #1c2878; font-weight: 700; }

  /* SCORE BREAKDOWN TABLE */
  .score-table { width: 100%; border-collapse: collapse; margin: 4mm 0; }
  .score-table th { background: #1c2878; color: white; padding: 3mm 4mm; font-size: 8.5pt;
    text-align: left; font-weight: 700; }
  .score-table td { padding: 2.5mm 4mm; font-size: 9pt; border-bottom: 1px solid #eaeff8; }
  .score-table tr:last-child td { border-bottom: none; }
  .score-table .pts { font-family: monospace; font-weight: 700; font-size: 10pt; text-align: center; }
  .pts-full { color: #27ae60; }
  .pts-half { color: #e8a000; }
  .pts-zero { color: #e55; }

  /* BUYER PERSONA CARD */
  .persona-card { background: #f4f7ff; border: 1.5px solid #c7d4f5; border-radius: 10px;
    padding: 5mm 6mm; margin-bottom: 5mm; }
  .persona-title { font-size: 11pt; font-weight: 800; color: #1c2878; margin-bottom: 3mm; }
  .persona-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 3mm; }
  .persona-item label { font-size: 7pt; text-transform: uppercase; letter-spacing: 0.1em;
    color: #888; display: block; margin-bottom: 1px; }
  .persona-item span { font-size: 9.5pt; font-weight: 600; color: #1a1a2e; }

  /* REC ITEMS */
  .rec-item { display: flex; gap: 7px; margin-bottom: 3.5mm; font-size: 9pt; line-height: 1.5; }
  .rec-icon { font-size: 13pt; flex-shrink: 0; }

  /* SEMAPHORE */
  .semaforo { display: flex; gap: 4mm; margin: 3mm 0; }
  .sem-circle { width: 18mm; height: 18mm; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-size: 8pt; font-weight: 700; text-align: center; flex-direction: column; }

  /* FOOTER */
  .page-footer { margin-top: auto; padding-top: 4mm; border-top: 1px solid #e0e8f5;
    font-size: 7pt; color: #aaa; display: flex; justify-content: space-between; }

  /* COVER PAGE SPECIFIC */
  .cover-hero { flex: 1; display: flex; flex-direction: column; justify-content: center; }
  .cover-subtitle { font-size: 11pt; color: #1a6ab2; font-weight: 600; margin-bottom: 2mm; }
  .cover-title { font-size: 22pt; font-weight: 900; color: #1a1a2e; margin-bottom: 1mm; line-height: 1.15; }
  .cover-meta  { font-size: 9pt; color: #777; margin-bottom: 8mm; }
  .cover-kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4mm; margin-bottom: 6mm; }
  .cover-kpi { background: #f4f7ff; border: 1px solid #dde4f5; border-radius: 10px; padding: 4mm 5mm; }
  .cover-kpi-val { font-size: 18pt; font-weight: 900; color: #1c2878; display: block; line-height: 1; }
  .cover-kpi-lbl { font-size: 8pt; color: #666; font-weight: 600; margin-top: 1mm; }
  .cover-score-wrap { display: inline-flex; align-items: center; gap: 8mm; padding: 4mm 6mm;
    border-radius: 10px; margin-bottom: 4mm; }

  /* TWO COLUMN */
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; }

  /* PRINT */
  @media print {
    body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
    .no-print { display: none; }
    .page { width: 100%; min-height: 0; page-break-after: always; }
  }
  .print-btn {
    position: fixed; bottom: 20px; right: 20px; padding: 10px 20px;
    background: #1c2878; color: white; border: none; border-radius: 8px;
    font-size: 13px; font-weight: 700; cursor: pointer; z-index: 999;
    box-shadow: 0 4px 16px rgba(28,40,120,0.35);
  }
  .print-btn:hover { background: #1a6ab2; }
</style>
</head>
<body>

<button class="print-btn no-print" onclick="window.print()">🖨️ Imprimir / Guardar PDF</button>

<!-- ===== PAGE 1: COVER ===== -->
<div class="page">
  <div class="page-header">
    <div>
      <div class="logo-mark">CAMPO <em>· COEZA</em></div>
      <div style="font-size:7.5pt;color:#888;margin-top:2px">Inteligencia Inmobiliaria</div>
    </div>
    <div class="report-meta">
      <strong>Reporte de Zona de Influencia</strong><br>
      Censo de Población y Vivienda 2020 · INEGI<br>
      Clasificación NSE AMAI 2018<br>
      ${today}
    </div>
  </div>

  <div class="cover-hero">
    <div class="cover-subtitle">CAMPO · Análisis Sociodemográfico</div>
    <div class="cover-title">${title}</div>
    <div class="cover-meta">${subtitle} · Generado ${today}</div>

    <div class="cover-score-wrap" style="background:${scoreBg}">
      <div>
        <span style="font-size:42pt;font-weight:900;color:${scoreColor};line-height:1">${score}</span>
        <span style="font-size:18pt;font-weight:500;color:${scoreColor};opacity:0.6">/10</span>
      </div>
      <div>
        <div style="font-size:16pt;font-weight:900;color:${scoreColor}">${slbl}</div>
        <div style="font-size:8.5pt;color:#888">Score de Zona · Análisis Sociodemográfico INEGI 2020</div>
      </div>
    </div>

    <div class="cover-kpi-grid">
      <div class="cover-kpi">
        <span class="cover-kpi-val">${fmt(s.pob)}</span>
        <div class="cover-kpi-lbl">Población total</div>
      </div>
      <div class="cover-kpi">
        <span class="cover-kpi-val">${fmt(s.hog)}</span>
        <div class="cover-kpi-lbl">Hogares</div>
      </div>
      <div class="cover-kpi">
        <span class="cover-kpi-val">${fmt(s.densidad,0)}</span>
        <div class="cover-kpi-lbl">Hab/km²</div>
      </div>
      <div class="cover-kpi">
        <span class="cover-kpi-val">${fmt(s.escolaridad,1)}</span>
        <div class="cover-kpi-lbl">Escolaridad (años)</div>
      </div>
      <div class="cover-kpi">
        <span class="cover-kpi-val">${fmt(s.pct_pea,1)}%</span>
        <div class="cover-kpi-lbl">PEA Activa</div>
      </div>
      <div class="cover-kpi">
        <span class="cover-kpi-val">${fmt(s.prom_hnv,2)}</span>
        <div class="cover-kpi-lbl">Hijos/mujer</div>
      </div>
    </div>

    <div style="font-size:9pt;color:#888;margin-top:4mm">
      <strong style="color:#1c2878">Fuentes:</strong> Censo de Población y Vivienda 2020 · INEGI · Clasificación NSE AMAI 2018 · Proyecciones CONAPO
    </div>
  </div>

  <div class="page-footer">
    <span>CAMPO · COEZA Consulting</span>
    <span>Pág. 1</span>
  </div>
</div>

<!-- ===== PAGE 2: PANORAMA DE ZONA ===== -->
<div class="page">
  <div class="page-header">
    <div class="logo-mark">CAMPO <em>· COEZA</em></div>
    <div class="report-meta">
      <strong>${title}</strong><br>
      CAMPO · Análisis de Zona · ${today}
    </div>
  </div>

  <div class="section-label">Análisis de Mercado</div>
  <div class="section-title">Panorama de Zona</div>
  <div class="section-sub">${subtitle}</div>

  <div class="cover-score-wrap" style="background:${scoreBg};margin-bottom:5mm">
    <div>
      <span style="font-size:36pt;font-weight:900;color:${scoreColor};line-height:1">${score}</span>
      <span style="font-size:16pt;font-weight:500;color:${scoreColor};opacity:0.6">/10</span>
    </div>
    <div>
      <div style="font-size:14pt;font-weight:900;color:${scoreColor}">${slbl}</div>
      <div style="font-size:7.5pt;color:#888">Índice de atractivo sociodemográfico para inversión inmobiliaria</div>
    </div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card">
      <span class="kpi-val">${fmt(s.pob)}</span>
      <span class="kpi-lbl">Población</span>
    </div>
    <div class="kpi-card">
      <span class="kpi-val">${fmt(s.hog)}</span>
      <span class="kpi-lbl">Hogares</span>
    </div>
    <div class="kpi-card">
      <span class="kpi-val">${fmt(s.pea)}</span>
      <span class="kpi-lbl">PEA Activa</span>
    </div>
    <div class="kpi-card">
      <span class="kpi-val">${fmt(s.escolaridad,1)}</span>
      <span class="kpi-lbl">Escolaridad (años)</span>
    </div>
  </div>

  <div class="persona-card">
    <div class="persona-title">Buyer Persona · Perfil de Demanda</div>
    <div class="persona-grid">
      <div class="persona-item">
        <label>NSE Dominante</label>
        <span>${nseLabel}</span>
      </div>
      <div class="persona-item">
        <label>Ingreso Familiar Estimado</label>
        <span>${ingresoRange}</span>
      </div>
      <div class="persona-item">
        <label>Rango de Precio Viable</label>
        <span>${precioRange}</span>
      </div>
      <div class="persona-item">
        <label>Tipo de Producto Sugerido</label>
        <span>${productType}</span>
      </div>
      <div class="persona-item" style="grid-column:1/-1">
        <label>Perfil Demográfico</label>
        <span>${agePerfil}</span>
      </div>
      <div class="persona-item" style="grid-column:1/-1">
        <label>Tipología Recomendada</label>
        <span>${habitType}</span>
      </div>
    </div>
  </div>

  ${bullets.map(b => `<div class="bullet ${b.type}">
    <span class="bullet-icon">${b.type==='warn'?'⚠':'b.type==='ok'?'✓':'→'}</span>
    <span>${b.text}</span>
  </div>`).join('')}

  <div class="page-footer">
    <span>CAMPO · COEZA Consulting · Censo 2020 · INEGI</span>
    <span>Pág. 2</span>
  </div>
</div>

<!-- ===== PAGE 3: CRECIMIENTO COMPARATIVO ===== -->
<div class="page">
  <div class="page-header">
    <div class="logo-mark">CAMPO <em>· COEZA</em></div>
    <div class="report-meta">
      <strong>${title}</strong><br>
      CAMPO · Análisis de Zona · ${today}
    </div>
  </div>

  <div class="section-label">Demografía y Habitacional</div>
  <div class="section-title">Crecimiento Comparativo 2010–2020</div>
  <div class="section-sub">Zona vs Torreón (municipio) · Fuente: Censo 2010 y 2020, INEGI</div>

  <div class="two-col">
    <div>
      <div class="cmp-title">Indicadores de Crecimiento (%)</div>

      ${(function(){
        const rows = [
          {name:'Población',    zona:s.crec_pob, mun:b.crec_pob},
          {name:'Viviendas hab.',zona:s.crec_viv, mun:b.crec_viv},
          {name:'Hogares',      zona:s.crec_hog, mun:b.crec_hog},
          {name:'Viv. temporal',zona:s.pct_viv_tmp, mun:b.pct_viv_des},
        ];
        return rows.map(r => {
          const absMax = Math.max(Math.abs(r.zona), Math.abs(r.mun), 0.1) * 1.25;
          const zW = Math.min(Math.abs(r.zona)/absMax*100, 100).toFixed(0);
          const mW = Math.min(Math.abs(r.mun)/absMax*100, 100).toFixed(0);
          const zCls = r.zona < 0 ? 'neg-bar' : 'zona-bar';
          const diff = r.zona - r.mun;
          const diffCol = diff >= 0 ? '#27ae60' : '#c0392b';
          return `<div class="cmp-row">
            <div class="cmp-name">${r.name} <span style="color:${diffCol}">${sign(r.zona)}</span></div>
            <div class="bar-lbl">Zona</div>
            <div class="bar-track"><div class="bar-fill ${zCls}" style="width:${zW}%"></div></div>
            <div class="bar-lbl">Municipio ${sign(r.mun)}</div>
            <div class="bar-track"><div class="bar-fill mun-bar" style="width:${mW}%"></div></div>
          </div>`;
        }).join('');
      })()}
    </div>

    <div>
      <div class="cmp-title">Indicadores Promedio</div>
      ${(function(){
        const rows = [
          {name:'Densidad (hab/km²)', zona:fmt(s.densidad,0), mun:fmt(b.densidad_pob,0), diff:((s.densidad-b.densidad_pob)/Math.max(b.densidad_pob,1)*100).toFixed(1)},
          {name:'Escolaridad (años)',  zona:fmt(s.escolaridad,1), mun:fmt(b.escolaridad,1), diff:((s.escolaridad-b.escolaridad)/Math.max(b.escolaridad,1)*100).toFixed(1)},
          {name:'Hab. por vivienda',   zona:fmt(s.viv_h?s.pob/s.viv_h:0,2), mun:fmt(b.pob_total/b.viv_habitadas,2), diff:0},
          {name:'% PEA Activa',       zona:fmt(s.pct_pea,1)+'%', mun:fmt(b.pct_pea,1)+'%', diff:((s.pct_pea-b.pct_pea)).toFixed(1)},
        ];
        return `<table style="width:100%;font-size:9pt;border-collapse:collapse">
          <tr style="background:#1c2878;color:white">
            <th style="padding:2.5mm 3mm;text-align:left;font-size:8pt">Indicador</th>
            <th style="padding:2.5mm 3mm;text-align:center;font-size:8pt">Zona</th>
            <th style="padding:2.5mm 3mm;text-align:center;font-size:8pt">Mun.</th>
            <th style="padding:2.5mm 3mm;text-align:center;font-size:8pt">Δ</th>
          </tr>
          ${rows.map((r,i) => `<tr style="background:${i%2?'#f4f7ff':'#fff'}">
            <td style="padding:2mm 3mm;font-weight:600">${r.name}</td>
            <td style="padding:2mm 3mm;text-align:center;font-family:monospace;color:#1c2878;font-weight:700">${r.zona}</td>
            <td style="padding:2mm 3mm;text-align:center;font-family:monospace;color:#666">${r.mun}</td>
            <td style="padding:2mm 3mm;text-align:center;font-size:8pt;color:${parseFloat(r.diff)>=0?'#27ae60':'#c0392b'}">${r.diff!=0?(parseFloat(r.diff)>=0?'+':'')+r.diff+'pp':'—'}</td>
          </tr>`).join('')}
        </table>`;
      })()}
    </div>
  </div>

  <div style="margin-top:5mm">
    <div class="cmp-title">Análisis de Dinámica Territorial 2010–2020</div>
    ${bullets.map(b => `<div class="bullet ${b.type}">
      <span class="bullet-icon">${b.type==='warn'?'▲':b.type==='ok'?'✓':'→'}</span>
      <span>${b.text}</span>
    </div>`).join('')}
  </div>

  <div class="page-footer">
    <span>CAMPO · COEZA Consulting · Censo 2020 · INEGI</span>
    <span>Pág. 3</span>
  </div>
</div>

<!-- ===== PAGE 4: ESTRUCTURA DE EDAD + HABITACIONAL ===== -->
<div class="page">
  <div class="page-header">
    <div class="logo-mark">CAMPO <em>· COEZA</em></div>
    <div class="report-meta">
      <strong>${title}</strong><br>
      CAMPO · Análisis de Zona · ${today}
    </div>
  </div>

  <div class="two-col">
    <div>
      <div class="section-label">Demografía</div>
      <div style="font-size:13pt;font-weight:800;margin-bottom:4mm">Estructura de Edad</div>
      <div style="font-size:8.5pt;color:#666;margin-bottom:3mm">Zona vs Torreón (municipio)</div>

      ${(function(){
        const ages = [
          {lbl:'0–14 años',  zona:s.pct_0_14,  mun:b.pct_0_14},
          {lbl:'15–24 años', zona:s.pct_15_24, mun:b.pct_15_24},
          {lbl:'25–59 años', zona:s.pct_25_59, mun:b.pct_25_59},
          {lbl:'60+ años',   zona:s.pct_60,    mun:b.pct_60mas},
        ];
        const maxVal = Math.max(...ages.map(a => Math.max(a.zona, a.mun))) * 1.2;
        return `<div class="pyramid-wrap">
          ${ages.map(a => {
            const zW = (a.zona/maxVal*90).toFixed(0);
            const mW = (a.mun/maxVal*90).toFixed(0);
            return `<div class="age-row">
              <div class="age-lbl">${a.lbl}</div>
              <div style="flex:1">
                <div style="display:flex;align-items:center;gap:3px;margin-bottom:2px">
                  <div class="age-bar" style="width:${zW}%;background:#1c2878;min-width:2px;height:9px;border-radius:3px"></div>
                  <span style="font-size:7.5pt;color:#1c2878;font-weight:700">${fmt(a.zona,1)}%</span>
                </div>
                <div style="display:flex;align-items:center;gap:3px">
                  <div class="age-bar" style="width:${mW}%;background:#a0aec0;min-width:2px;height:9px;border-radius:3px"></div>
                  <span style="font-size:7.5pt;color:#a0aec0">${fmt(a.mun,1)}%</span>
                </div>
              </div>
            </div>`;
          }).join('')}
          <div style="display:flex;gap:8mm;margin-top:3mm;font-size:7.5pt;color:#666">
            <span><span style="display:inline-block;width:10px;height:10px;background:#1c2878;border-radius:2px;margin-right:3px;vertical-align:middle"></span>Zona</span>
            <span><span style="display:inline-block;width:10px;height:10px;background:#a0aec0;border-radius:2px;margin-right:3px;vertical-align:middle"></span>Municipio</span>
          </div>
        </div>`;
      })()}

      ${s.pct_60 > 20 ? `<div class="bullet warn" style="margin-top:3mm">
        <span class="bullet-icon">⚠</span>
        <span>Población envejecida. El mercado tiende a unidades compactas en planta baja y accesibilidad universal. La demanda de nueva vivienda familiar será limitada en el corto plazo.</span>
      </div>` : s.pct_25_59 >= 46 ? `<div class="bullet ok" style="margin-top:3mm">
        <span class="bullet-icon">✓</span>
        <span>Cohorte compradora activa (25–59 años) es dominante. Mercado accesible para vivienda familiar y primera compra. Demanda sostenida proyectada.</span>
      </div>` : `<div class="bullet info" style="margin-top:3mm">
        <span class="bullet-icon">→</span>
        <span>Estructura de edad equilibrada. Validar buyer persona con datos complementarios de portales e investigación primaria.</span>
      </div>`}
    </div>

    <div>
      <div class="section-label">Habitacional</div>
      <div style="font-size:13pt;font-weight:800;margin-bottom:4mm">Composición del Parque</div>
      <div style="font-size:8.5pt;color:#666;margin-bottom:3mm">${fmt(s.viv_t)} unidades totales</div>

      ${(function(){
        const items = [
          {lbl:'Habitadas',    pct:s.pct_viv_h,   color:'#1c2878'},
          {lbl:'Deshabitadas', pct:s.pct_viv_des,  color:'#e55'},
          {lbl:'Uso temporal', pct:s.pct_viv_tmp,  color:'#e8a000'},
          {lbl:'2+ dormitorios',pct:s.pct_2dor,    color:'#1a6ab2'},
        ];
        return items.map(i => `<div class="family-row">
          <div class="family-lbl">${i.lbl}</div>
          <div class="family-track">
            <div class="family-fill" style="width:${Math.min(i.pct,100).toFixed(0)}%;background:${i.color}"></div>
          </div>
          <div class="family-pct" style="color:${i.color}">${fmt(i.pct,1)}%</div>
        </div>`).join('');
      })()}

      <div style="font-size:8pt;color:#666;margin-top:3mm;padding:2mm 0;border-top:1px solid #eaeff8">
        Ocupación promedio: <strong style="color:#1c2878">${s.viv_h ? fmt(s.pob/s.viv_h,2) : '—'}</strong> hab/viv
        (municipio: <span style="font-family:monospace">${fmt(b.pob_total/b.viv_habitadas,2)}</span>)
      </div>

      ${s.pct_viv_des > 20 ? `<div class="bullet warn" style="margin-top:3mm">
        <span class="bullet-icon">⚠</span>
        <span><strong>Vacancia alta: ${fmt(s.pct_viv_des,1)}%</strong> de viviendas deshabitadas (umbral referencia: 12%). Riesgo de mercado saturado. Evaluar demanda antes de agregar oferta.</span>
      </div>` : ''}

      ${s.pct_viv_tmp > 5 ? `<div class="bullet info" style="margin-top:3mm">
        <span class="bullet-icon">→</span>
        <span><strong>Señal turística detectada:</strong> ${fmt(s.pct_viv_tmp,1)}% de uso temporal. Posible mercado de segunda residencia o renta corta (Airbnb). Evaluar con datos AIRDNA.</span>
      </div>` : ''}

      <div style="font-size:13pt;font-weight:800;margin:5mm 0 3mm">Estructura Familiar</div>
      ${(function(){
        const items = [
          {lbl:'Solteros',       pct:s.fam_total?s.sol/s.fam_total*100:0},
          {lbl:'Casados / Unión',pct:s.fam_total?s.cas/s.fam_total*100:0},
          {lbl:'Separados / Div.',pct:s.fam_total?s.sep/s.fam_total*100:0},
        ];
        return items.map(i => `<div class="family-row">
          <div class="family-lbl">${i.lbl}</div>
          <div class="family-track">
            <div class="family-fill" style="width:${Math.min(i.pct,100).toFixed(0)}%"></div>
          </div>
          <div class="family-pct">${fmt(i.pct,1)}%</div>
        </div>`).join('');
      })()}
      <div style="font-size:8pt;color:#666;margin-top:2mm">
        Fertilidad: <strong style="color:#1c2878">${fmt(s.prom_hnv,2)}</strong> hijos/mujer
        (municipio: <span style="font-family:monospace">${fmt(b.prom_hnv,2)}</span>)
        · Demanda ${s.fam_total && s.cas/s.fam_total > 0.5 ? 'de vivienda familiar' : 'mixta (unitarias + familiares)'}
      </div>
    </div>
  </div>

  <div class="page-footer">
    <span>CAMPO · COEZA Consulting · Censo 2020 · INEGI</span>
    <span>Pág. 4</span>
  </div>
</div>

<!-- ===== PAGE 5: ACTIVIDAD ECONÓMICA + NSE ===== -->
<div class="page">
  <div class="page-header">
    <div class="logo-mark">CAMPO <em>· COEZA</em></div>
    <div class="report-meta">
      <strong>${title}</strong><br>
      CAMPO · Análisis de Zona · ${today}
    </div>
  </div>

  <div class="section-label">Economía y Nivel Socioeconómico</div>
  <div class="section-title">Actividad Económica + NSE</div>

  <div class="two-col">
    <div>
      <div class="cmp-title">Indicadores Económicos</div>
      <div class="kpi-grid" style="grid-template-columns:1fr 1fr;margin-bottom:4mm">
        <div class="kpi-card">
          <span class="kpi-val">${fmt(s.pea)}</span>
          <span class="kpi-lbl">PEA Total</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-val">${fmt(s.pct_pea,1)}%</span>
          <span class="kpi-lbl">% PEA Activa</span>
        </div>
      </div>

      ${(function(){
        const items = [
          {lbl:'% PEA (Zona)',    zona:s.pct_pea,    mun:b.pct_pea},
          {lbl:'Escolaridad (años)', zona:s.escolaridad, mun:b.escolaridad},
        ];
        const maxVal = Math.max(...items.map(i => Math.max(i.zona, i.mun))) * 1.2;
        return items.map(i => `<div style="margin-bottom:3mm">
          <div style="display:flex;justify-content:space-between;font-size:8.5pt;font-weight:600;margin-bottom:1.5mm">
            <span>${i.lbl}</span>
            <span style="color:${i.zona >= i.mun ? '#27ae60' : '#c0392b'}">${fmt(i.zona,1)} vs ${fmt(i.mun,1)} mun</span>
          </div>
          <div class="bar-lbl">Zona</div>
          <div class="bar-track"><div class="bar-fill zona-bar" style="width:${(i.zona/maxVal*100).toFixed(0)}%"></div></div>
          <div class="bar-lbl">Municipio</div>
          <div class="bar-track"><div class="bar-fill mun-bar" style="width:${(i.mun/maxVal*100).toFixed(0)}%"></div></div>
        </div>`).join('');
      })()}

      ${(function(){
        const anal = [];
        if (s.pct_pea >= 50) anal.push({type:'ok', text:'PEA activa <strong>' + fmt(s.pct_pea,1) + '%</strong> — superior al promedio municipal (' + fmt(b.pct_pea,1) + '%). Indica empleo formal estable y capacidad de pago.'});
        else if (s.pct_pea >= 40) anal.push({type:'info', text:'PEA activa <strong>' + fmt(s.pct_pea,1) + '%</strong> — dentro del rango aceptable. Validar con datos IMSS de empleo formal en la zona.'});
        else anal.push({type:'warn', text:'PEA activa <strong>' + fmt(s.pct_pea,1) + '%</strong> — por debajo del promedio municipal (' + fmt(b.pct_pea,1) + '%). Puede indicar alto desempleo o economía informal.'});

        if (s.escolaridad >= 12) anal.push({type:'ok', text:'Escolaridad promedio <strong>' + fmt(s.escolaridad,1) + ' años</strong> — nivel preparatoria o más. Asociado a mayor capacidad adquisitiva y acceso a crédito hipotecario.'});
        else if (s.escolaridad >= b.escolaridad) anal.push({type:'info', text:'Escolaridad <strong>' + fmt(s.escolaridad,1) + ' años</strong> — comparable al promedio municipal (' + fmt(b.escolaridad,1) + ' años).'});
        else anal.push({type:'warn', text:'Escolaridad <strong>' + fmt(s.escolaridad,1) + ' años</strong> — por debajo del promedio municipal (' + fmt(b.escolaridad,1) + ' años). Correlaciona con menor capacidad de pago.'});

        return anal.map(a => `<div class="bullet ${a.type}">
          <span class="bullet-icon">${a.type==='warn'?'⚠':a.type==='ok'?'✓':'→'}</span>
          <span>${a.text}</span>
        </div>`).join('');
      })()}
    </div>

    <div>
      <div class="cmp-title">Distribución NSE · AMAI 2018</div>
      <div style="margin-bottom:2mm;font-size:8pt;color:#666">${fmt(s.nse_total)} viviendas clasificadas</div>

      <!-- NSE horizontal stacked bar -->
      <div class="nse-bar-wrap" style="margin-bottom:4mm">
        ${nseItems.map(x => {
          const pct = s.nse_total ? (x.count/s.nse_total*100).toFixed(1) : 0;
          return `<div class="nse-seg" title="${x.label}: ${pct}%" style="width:${pct}%;background:${x.color};min-width:${x.count?2:0}px"></div>`;
        }).join('')}
      </div>

      <div class="nse-legend">
        ${nseItems.map(x => {
          const pct = s.nse_total ? (x.count/s.nse_total*100).toFixed(0) : 0;
          return `<div class="nse-pill">
            <div class="nse-dot" style="background:${x.color}"></div>
            <strong>${x.label}</strong>
            <span style="color:#666">${pct}%</span>
            <span style="font-size:7.5pt;color:#999">(${fmt(x.count)})</span>
          </div>`;
        }).join('')}
      </div>

      <div style="margin-top:4mm;border-top:1px solid #eaeff8;padding-top:3mm">
        <div style="font-size:8.5pt;font-weight:700;margin-bottom:2mm">Segmentos Clave</div>
        <div style="font-size:8.5pt;margin-bottom:1.5mm">
          <span style="color:#1c2878;font-weight:700">Alto (A/B + C+):</span>
          <strong>${fmt(pct_alto,1)}%</strong>
          <span style="color:#666">— ${pct_alto >= 30 ? 'Concentración alta. Mercado para residencial plus.' : pct_alto >= 15 ? 'Concentración media. Validar con benchmark.' : 'Concentración baja. Orientar a vivienda media.'}</span>
        </div>
        <div style="font-size:8.5pt;margin-bottom:1.5mm">
          <span style="color:#22d3ee;font-weight:700">Medio (C):</span>
          <strong>${fmt(pct_c,1)}%</strong>
          <span style="color:#666">— Ingreso $11,600–$35,000/mes</span>
        </div>
        <div style="font-size:8.5pt">
          <span style="color:#f97316;font-weight:700">Bajo (C− / D+ / D / E):</span>
          <strong>${fmt(pct_bajo,1)}%</strong>
          <span style="color:#666">— Interés social / popular</span>
        </div>
      </div>

      <div class="bullet ${pct_alto >= 30 ? 'ok' : pct_alto >= 15 ? 'info' : 'warn'}" style="margin-top:3mm">
        <span class="bullet-icon">${pct_alto >= 30 ? '✓' : pct_alto >= 15 ? '→' : '⚠'}</span>
        <span>${pct_alto >= 30
          ? 'NSE alto dominante (' + fmt(pct_alto,1) + '%). Zona con capacidad de pago sólida para vivienda residencial media-alta a premium.'
          : pct_alto >= 15
          ? 'NSE alto presente (' + fmt(pct_alto,1) + '%). Mercado mixto — producto entre $2M y $4M con amenidades moderadas.'
          : 'NSE bajo dominante. Mercado principal: vivienda interés social o media. Precio techo aproximado: ' + precioRange + '.'}</span>
      </div>
    </div>
  </div>

  <div style="margin-top:3mm;font-size:7.5pt;color:#aaa">
    * Los promedios estatales y del municipio corresponden exclusivamente a AGEBs urbanos con datos censales disponibles.<br>
    Fuente: INEGI Censo de Población y Vivienda 2020 · Clasificación NSE: AMAI 2018.
  </div>

  <div class="page-footer">
    <span>CAMPO · COEZA Consulting · Censo 2020 · INEGI · AMAI 2018</span>
    <span>Pág. 5</span>
  </div>
</div>

<!-- ===== PAGE 6: CONCLUSIONES ===== -->
<div class="page">
  <div class="page-header">
    <div class="logo-mark">CAMPO <em>· COEZA</em></div>
    <div class="report-meta">
      <strong>${title}</strong><br>
      CAMPO · Análisis de Zona · ${today}
    </div>
  </div>

  <div class="section-label">Estrategia</div>
  <div class="section-title">Conclusiones · Estrategia de Mercado</div>

  <div style="display:flex;align-items:center;gap:6mm;margin-bottom:6mm">
    <div style="background:${scoreBg};border-radius:10px;padding:4mm 6mm;display:inline-flex;align-items:center;gap:5mm">
      <span style="font-size:32pt;font-weight:900;color:${scoreColor};line-height:1">${score}</span>
      <div>
        <div style="font-size:11pt;font-weight:900;color:${scoreColor}">${slbl}</div>
        <div style="font-size:7.5pt;color:#888">Entorno socioeconómico</div>
      </div>
    </div>
    <div style="flex:1;font-size:9.5pt;color:#444;line-height:1.6">
      Score calculado sobre 5 dimensiones: crecimiento demográfico, cohorte compradora, ocupación habitacional, actividad económica y concentración NSE. Rango: 0–10.
    </div>
  </div>

  <div style="margin-bottom:5mm">
    <div class="cmp-title">Desglose del Score · Dimensión por Dimensión</div>
    <table class="score-table">
      <tr>
        <th>Dimensión</th>
        <th style="text-align:center;width:20mm">Puntos</th>
        <th>Detalle</th>
      </tr>
      ${scoreItems.map(item => {
        const cls = item.pts === item.max ? 'pts-full' : item.pts > 0 ? 'pts-half' : 'pts-zero';
        return `<tr>
          <td><strong>${item.label}</strong></td>
          <td class="pts ${cls}">${item.pts}/${item.max}</td>
          <td style="font-size:8.5pt;color:#555">${item.detail}</td>
        </tr>`;
      }).join('')}
      <tr style="background:#1c2878;color:white">
        <td style="padding:2.5mm 4mm;font-weight:800">TOTAL</td>
        <td style="padding:2.5mm 4mm;text-align:center;font-weight:800;font-family:monospace;font-size:11pt">${score}/10</td>
        <td style="padding:2.5mm 4mm;font-size:8.5pt">${slbl}</td>
      </tr>
    </table>
  </div>

  <div style="margin-bottom:5mm">
    <div class="cmp-title">Semáforo de Mercado</div>
    <div class="semaforo">
      <div class="sem-circle" style="background:${score>=6?'#27ae60':'#eee'};color:${score>=6?'white':'#999'}">
        ALTO<br>${score>=6?'✓':''}
      </div>
      <div class="sem-circle" style="background:${score>=4&&score<6?'#e8a000':'#eee'};color:${score>=4&&score<6?'white':'#999'}">
        MOD<br>${score>=4&&score<6?'→':''}
      </div>
      <div class="sem-circle" style="background:${score<4?'#c0392b':'#eee'};color:${score<4?'white':'#999'}">
        BAJO<br>${score<4?'!':''}
      </div>
      <div style="flex:1;font-size:9pt;color:#444;align-self:center;line-height:1.55">
        <strong>Entorno socioeconómico ${slbl.toLowerCase()}.</strong>
        ${score >= 8 ? 'Zona con condiciones demográficas y económicas muy favorables para inversión inmobiliaria. Proceder con análisis de oferta.' :
          score >= 6 ? 'Condiciones favorables. Recomendado continuar con benchmark de competencia y análisis de precio.' :
          score >= 4 ? 'Condiciones moderadas. Identificar factores de riesgo específicos antes de comprometer capital.' :
          'Entorno con señales de alerta. Validar factores adicionales antes de proceder. Considerar otras zonas.'}
      </div>
    </div>
  </div>

  <div>
    <div class="cmp-title">Resumen de Hallazgos Territoriales</div>
    ${bullets.map(b => `<div class="bullet ${b.type}">
      <span class="bullet-icon">${b.type==='warn'?'▲':b.type==='ok'?'✓':'→'}</span>
      <span>${b.text}</span>
    </div>`).join('')}
  </div>

  <div class="page-footer">
    <span>CAMPO · COEZA Consulting · Censo 2020 · INEGI</span>
    <span>Pág. 6</span>
  </div>
</div>

<!-- ===== PAGE 7: RECOMENDACIONES ===== -->
<div class="page">
  <div class="page-header">
    <div class="logo-mark">CAMPO <em>· COEZA</em></div>
    <div class="report-meta">
      <strong>${title}</strong><br>
      CAMPO · Análisis de Zona · ${today}
    </div>
  </div>

  <div class="section-label">Estrategia</div>
  <div class="section-title">Recomendaciones Estratégicas</div>
  <div class="section-sub">Basadas en análisis INEGI 2020 · AMAI 2018 · Metodología CAMPO</div>

  <div class="persona-card" style="margin-bottom:5mm">
    <div class="persona-title">Buyer Persona · Perfil Definitivo</div>
    <div class="persona-grid">
      <div class="persona-item">
        <label>NSE Dominante</label>
        <span>${nseLabel}</span>
      </div>
      <div class="persona-item">
        <label>Ingreso Familiar Mensual</label>
        <span>${ingresoRange}</span>
      </div>
      <div class="persona-item">
        <label>Precio Máximo Viable</label>
        <span>${precioRange}</span>
      </div>
      <div class="persona-item">
        <label>Tipo de Producto</label>
        <span>${productType}</span>
      </div>
      <div class="persona-item" style="grid-column:1/-1">
        <label>Perfil Demográfico</label>
        <span>${agePerfil}</span>
      </div>
      <div class="persona-item" style="grid-column:1/-1">
        <label>Tipología Habitacional Sugerida</label>
        <span>${habitType}</span>
      </div>
    </div>
  </div>

  <div style="margin-bottom:5mm">
    <div class="cmp-title">Recomendaciones de Producto · Soluciones COEZA</div>
    ${recs.map(r => `<div class="rec-item">
      <span class="rec-icon">${r.icon}</span>
      <div>${r.text}</div>
    </div>`).join('')}
  </div>

  <div style="background:#eef3ff;border-left:3px solid #1a6ab2;padding:3.5mm 4mm;border-radius:0 6px 6px 0;font-size:8.5pt;line-height:1.6;margin-top:4mm">
    <strong>Nota Metodológica:</strong> Este reporte utiliza datos del Censo de Población y Vivienda 2020 (INEGI), clasificación NSE AMAI 2018, y proyecciones de crecimiento CONAPO. Los indicadores son de naturaleza sociodemográfica y deben complementarse con datos de oferta activa (portales, SOFTEC), análisis de absorción y benchmark de competencia para un estudio de mercado completo (proceso DIVI COEZA, 4 semanas).
  </div>

  <div style="background:#fff8e6;border-left:3px solid #e8a000;padding:3.5mm 4mm;border-radius:0 6px 6px 0;font-size:8.5pt;line-height:1.6;margin-top:3mm">
    <strong>Siguientes Pasos Recomendados:</strong> (1) Benchmark de oferta activa en Inmuebles24 / propiedades.com para la zona. (2) Validar absorción mensual del mercado (SOFTEC si disponible, levantamiento manual si no). (3) Identificar vacío de precio con eje de precios de competidores. (4) Preventa simulada o investigación primaria con buyer persona identificado.
  </div>

  <div style="margin-top:auto;padding-top:5mm;border-top:1px solid #eaeff8;font-size:7.5pt;color:#aaa;line-height:1.7">
    <strong>Fuentes de Datos:</strong> Censo de Población y Vivienda 2020, INEGI · Clasificación NSE AMAI 2018 · Proyecciones de Crecimiento CONAPO · Análisis CAMPO, COEZA Consulting.<br>
    <strong>Metodología:</strong> Score de Zona calculado con 5 dimensiones ponderadas: crecimiento poblacional, cohorte compradora 25–59 años, ocupación habitacional, actividad económica (PEA) y concentración NSE medio-alto. Máximo 10 puntos. Ver Mind de Mercado COEZA v2.2 para metodología completa.
  </div>

  <div class="page-footer">
    <span>CAMPO · COEZA Consulting · Inteligencia Inmobiliaria</span>
    <span>Pág. 7 de 7</span>
  </div>
</div>

</body>
</html>`;

  // Open in new window and auto-print
  const w = window.open('', '_blank', 'width=900,height=700');
  w.document.write(html);
  w.document.close();
  // Short delay for fonts/styles to load before auto-print
  // (user can also click the print button manually)
}
'''

def main():
    with open(SRC, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1) Add button CSS to the existing <style> block
    # Find the last occurrence of .btn-reporte (to avoid re-adding)
    if '.btn-reporte' not in html:
        # Insert before the closing </style> of the LAST style tag that contains the main styles
        # Find the </style> that comes after :root {
        root_idx = html.find(':root {')
        close_style = html.find('</style>', root_idx)
        if close_style == -1:
            print('ERROR: Could not find </style> after :root')
            return
        html = html[:close_style] + BUTTON_CSS + '\n' + html[close_style:]
        print('OK Added .btn-reporte CSS')
    else:
        print('  .btn-reporte CSS already present, skipping')

    # 2) Add generateReporte() function and button in the sidebar
    # Find the footer line at the end of renderDemoPanel's innerHTML
    FOOTER_OLD = 'Censo Población y Vivienda 2020 · INEGI · AMAI 2018<br>Datos DATERRA Consulting — COEZA Suite\n    </div>`;\n}'
    FOOTER_NEW = '''Censo Población y Vivienda 2020 · INEGI · AMAI 2018<br>Datos DATERRA Consulting — COEZA Suite
    </div>
    <button class="btn-reporte" onclick="generateReporte()" title="Generar reporte PDF de la zona seleccionada">
      ⬇ Generar Reporte PDF
    </button>`;
  window._lastDemoStats = s;
  window._lastDemoTitle = title || 'Zona de Influencia';
  window._lastDemoSubtitle = subtitle || '';
}
''' + REPORT_JS

    if 'generateReporte' not in html:
        if FOOTER_OLD in html:
            html = html.replace(FOOTER_OLD, FOOTER_NEW)
            print('OK Added generateReporte() function and button')
        else:
            print('ERROR: Could not find insertion anchor.')
            print('Searching for partial match...')
            anchor = 'Datos DATERRA Consulting'
            idx = html.find(anchor)
            if idx >= 0:
                print(f'  Found partial match at idx={idx}')
                print(f'  Context: {repr(html[idx-100:idx+200])}')
            return
    else:
        print('  generateReporte() already present, skipping')

    # 3) Write dashboard
    with open(SRC, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'OK Written: {SRC}')

    # 4) Copy to docs/index.html
    with open(DST_DOCS, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'OK Copied: {DST_DOCS}')

if __name__ == '__main__':
    main()
