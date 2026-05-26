"""
apply_light_theme.py — CAMPO light mode (AirDNA-inspired)
Replaces the entire <style> block and fixes dark-mode hard-codes.
"""
import re, sys, pathlib

SRC  = pathlib.Path(__file__).parent.parent / "frontend" / "dashboard.html"
DEST = SRC

NEW_CSS = """\
<style>
:root {
  /* CAMPO — AirDNA Light Mode */
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
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh}

/* HEADER */
header{
  padding:0 32px;height:54px;
  border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;
  background:var(--surface);z-index:100;position:sticky;top:0;
  box-shadow:var(--shadow-sm);
}
.logo{font-size:15px;font-weight:700;letter-spacing:-.03em;color:var(--text);display:flex;align-items:center;gap:8px}
.logo em{font-style:normal;color:var(--muted);font-weight:400;font-size:13px}
.version-tag{background:var(--accent-dim);color:var(--accent);border:1px solid oklch(85% 0.055 264);padding:2px 7px;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:.04em;font-family:var(--mono)}
.header-meta{font-family:var(--mono);font-size:11px;color:var(--muted);display:flex;align-items:center;gap:14px}
#last-update{color:var(--accent2);font-weight:500}

/* STATS BAR */
.stats-bar{display:grid;grid-template-columns:repeat(6,1fr);background:var(--surface);border-bottom:1px solid var(--border)}
.stat{padding:13px 20px 15px;display:flex;flex-direction:column;gap:4px;border-right:1px solid var(--border)}
.stat:last-child{border-right:none}
.stat-label{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:600}
.stat-value{font-size:22px;font-weight:700;font-family:var(--mono);color:var(--text);letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat-value.green{color:var(--success)}
.stat-value.blue{color:var(--accent2)}
.stat-value.accent{color:var(--accent)}
.stat-value.yellow{color:var(--warning)}

/* MAIN TABS */
.main-tabs{display:flex;background:var(--surface);border-bottom:1px solid var(--border)}
.main-tab{padding:13px 24px;font-size:13px;font-weight:600;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;color:var(--muted);transition:color .15s,border-color .15s;user-select:none;letter-spacing:-.01em}
.main-tab:hover{color:var(--text)}
.main-tab.active{color:var(--accent);border-bottom-color:var(--accent)}

/* SUB-TABS */
.sub-tabs{display:flex;gap:2px;padding:0 2px}
.sub-tab{padding:5px 12px;font-size:12px;font-weight:600;cursor:pointer;border-radius:var(--radius-sm);color:var(--muted);transition:all .12s;user-select:none;border:1px solid transparent}
.sub-tab:hover{color:var(--text);background:var(--bg)}
.sub-tab.active{color:var(--accent);background:var(--accent-dim);border-color:oklch(85% 0.055 264)}

/* CONTROLS BAR */
.controls-bar{display:flex;align-items:center;gap:12px;padding:8px 20px;border-bottom:1px solid var(--border);background:var(--surface2);flex-wrap:wrap}
.controls-bar .sub-tabs{flex-shrink:0}
.controls-bar .filters-inline{display:flex;align-items:center;gap:8px;flex-wrap:wrap;flex:1}

/* FILTERS */
.filters-wrap{display:flex;gap:6px;flex-wrap:wrap;align-items:center;flex:1}
.filter-group{display:flex;align-items:center;gap:5px}
.filter-group label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600;white-space:nowrap}
select,input[type=text],input[type=number]{background:var(--surface);border:1px solid var(--border);color:var(--text);padding:5px 9px;border-radius:var(--radius-sm);font-family:var(--font);font-size:12px;outline:none;cursor:pointer;transition:border-color .15s,box-shadow .15s}
select:hover,input:hover{border-color:var(--muted)}
select:focus,input:focus{border-color:var(--accent);box-shadow:0 0 0 3px oklch(93% 0.04 264)}
.btn{background:var(--accent);color:oklch(99% 0.003 264);border:none;padding:5px 14px;border-radius:var(--radius-sm);font-family:var(--font);font-size:12px;font-weight:600;cursor:pointer;transition:background .15s;letter-spacing:.01em}
.btn:hover{background:var(--accent2)}
.btn.secondary{background:var(--surface);color:var(--muted);border:1px solid var(--border);transition:border-color .15s,color .15s}
.btn.secondary:hover{color:var(--text);border-color:var(--muted)}

/* TABLE VIEW */
#view-table{display:block}
#view-map{display:none}
#view-mercado{display:block}
.table-wrap{padding:0 28px 32px;overflow-x:auto}
.table-meta{padding:12px 0 8px;display:flex;justify-content:space-between;align-items:center}
.table-meta span{font-size:12px;color:var(--muted);font-family:var(--mono)}
table{width:100%;border-collapse:collapse;font-size:13px}
thead tr{border-bottom:1px solid var(--border)}
th{padding:8px 12px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:700;white-space:nowrap;cursor:pointer;user-select:none;background:var(--surface)}
th:hover{color:var(--text)}
th.sorted{color:var(--accent)}
th.sorted::after{content:' ↓'}
th.sorted.asc::after{content:' ↑'}
tbody tr{border-bottom:1px solid var(--border);transition:background .1s}
tbody tr:hover{background:var(--accent-dim)}
td{padding:10px 12px;vertical-align:middle}
.badge{display:inline-block;padding:2px 7px;border-radius:3px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;font-family:var(--mono)}
.badge-venta{background:oklch(94% 0.04 264);color:var(--accent)}
.badge-renta{background:oklch(94% 0.03 220);color:var(--accent2)}
.badge-preventa{background:oklch(96% 0.04 50);color:var(--warning)}
.tipo-badge{display:inline-block;padding:2px 6px;border-radius:3px;font-size:10px;background:var(--surface2);color:var(--muted);border:1px solid var(--border)}
.precio{font-family:var(--mono);font-weight:700;color:var(--success);white-space:nowrap;font-variant-numeric:tabular-nums}
.precio-m2{font-family:var(--mono);font-size:11px;color:var(--muted)}
.colonia{font-weight:600;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.desc{color:var(--muted);max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px}
.score.high{color:var(--success)}.score.mid{color:var(--warning)}.score.low{color:var(--accent3)}
a.link-ext{color:var(--accent2);text-decoration:none;font-size:12px}
a.link-ext:hover{text-decoration:underline}

/* MAP VIEW */
#map-container{height:calc(100vh - 280px);min-height:500px;position:relative}
#map{width:100%;height:100%}
.leaflet-container{background:oklch(92% 0.008 240)!important}

/* Map overlays (float over varied tile content — purposeful translucency) */
.map-legend{position:absolute;bottom:20px;left:20px;z-index:1000;background:oklch(99.5% 0.003 264 / 0.95);border:1px solid var(--border);border-radius:8px;padding:12px 14px;font-size:12px;backdrop-filter:blur(6px);box-shadow:var(--shadow)}
.map-legend-title{font-weight:700;margin-bottom:8px;color:var(--text);font-size:11px}
.legend-item{display:flex;align-items:center;gap:7px;margin-bottom:4px;color:var(--muted);font-size:11px}
.legend-dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.map-stats{position:absolute;top:14px;right:14px;z-index:1000;background:oklch(99.5% 0.003 264 / 0.95);border:1px solid var(--border);border-radius:8px;padding:8px 13px;font-family:var(--mono);font-size:11px;color:var(--muted);backdrop-filter:blur(6px);box-shadow:var(--shadow)}
#map-count{color:var(--accent);font-weight:700}

/* Leaflet popups */
.leaflet-popup-content-wrapper{background:var(--surface)!important;color:var(--text)!important;border:1px solid var(--border)!important;border-radius:var(--radius)!important;box-shadow:var(--shadow)!important}
.leaflet-popup-tip{background:var(--surface)!important}
.leaflet-popup-content{margin:12px 14px!important;font-family:var(--font)!important;font-size:13px!important;line-height:1.5!important}
.popup-precio{font-family:var(--mono);font-weight:700;color:var(--success);font-size:15px;margin-bottom:3px;font-variant-numeric:tabular-nums}
.popup-colonia{font-weight:600;margin-bottom:5px}
.popup-meta{color:var(--muted);font-size:12px;margin-bottom:7px}
.popup-badge{display:inline-block;padding:2px 6px;border-radius:3px;font-size:10px;font-weight:700;text-transform:uppercase;margin-right:4px}
.popup-link{display:inline-block;margin-top:7px;color:var(--accent2);text-decoration:none;font-size:12px}
.popup-link:hover{text-decoration:underline}
.popup-oportunidad{color:var(--success);font-weight:600;font-size:12px;margin-top:4px}

/* HEATMAP TOOLBAR */
.heat-toolbar{display:flex;align-items:center;gap:10px;padding:9px 14px;background:oklch(99.5% 0.003 264 / 0.95);border:1px solid var(--border);border-radius:8px;position:absolute;top:14px;left:14px;z-index:1000;backdrop-filter:blur(6px);box-shadow:var(--shadow);flex-wrap:wrap}
.heat-toolbar label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;white-space:nowrap;font-weight:600}
.heat-toolbar select{padding:4px 7px;font-size:11px}
.heat-toggle{display:flex;align-items:center;gap:6px;padding:4px 10px;background:var(--surface2);border:1px solid var(--border);border-radius:5px;cursor:pointer;font-size:11px;font-weight:600;transition:all .15s;user-select:none;color:var(--muted)}
.heat-toggle:hover{border-color:var(--muted);color:var(--text)}
.heat-toggle.on{background:var(--accent-dim);border-color:oklch(82% 0.06 264);color:var(--accent)}
.heat-toggle-dot{width:7px;height:7px;border-radius:50%;background:var(--border);transition:background .15s}
.heat-toggle.on .heat-toggle-dot{background:var(--accent)}
.heat-sep{width:1px;height:20px;background:var(--border)}

/* HEATMAP LEGEND */
.heat-legend{position:absolute;bottom:20px;right:20px;z-index:1000;background:oklch(99.5% 0.003 264 / 0.95);border:1px solid var(--border);border-radius:8px;padding:12px 14px;min-width:190px;backdrop-filter:blur(6px);box-shadow:var(--shadow)}
.heat-legend-title{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:7px;font-weight:600}
.heat-legend-bar{height:6px;border-radius:3px;background:linear-gradient(to right,#0d47a1,#42a5f5,#80deea,#a5d6a7,#ffeb3b,#ff9800,#f44336);margin-bottom:5px}
.heat-legend-labels{display:flex;justify-content:space-between;font-family:var(--mono);font-size:10px;color:var(--muted)}
.heat-legend-stats{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-top:9px}
.heat-stat{background:var(--surface2);border-radius:4px;padding:5px 8px;border:1px solid var(--border)}
.heat-stat-label{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;font-weight:600}
.heat-stat-val{font-family:var(--mono);font-size:12px;font-weight:700;color:var(--text);margin-top:2px;font-variant-numeric:tabular-nums}

/* Leaflet tooltip */
.leaflet-tooltip{background:var(--surface)!important;border:1px solid var(--border)!important;color:var(--text)!important;border-radius:5px!important;box-shadow:var(--shadow-sm)!important;font-size:11px!important}
.leaflet-tooltip::before{display:none!important}

/* Basemap selector */
.basemap-selector{position:absolute;bottom:20px;left:20px;z-index:1000;display:flex;gap:3px}
.basemap-btn{padding:4px 9px;background:oklch(99.5% 0.003 264 / 0.95);border:1px solid var(--border);color:var(--muted);border-radius:5px;cursor:pointer;font-family:var(--mono);font-size:10px;transition:all .12s;backdrop-filter:blur(6px);box-shadow:var(--shadow-sm)}
.basemap-btn:hover{color:var(--text)}
.basemap-btn.active{background:var(--accent-dim);border-color:oklch(82% 0.06 264);color:var(--accent)}

/* Hex sidebar */
#hex-sidebar{position:absolute;top:0;right:0;bottom:0;width:300px;background:var(--surface);border-left:1px solid var(--border);z-index:1000;display:flex;flex-direction:column;transform:translateX(100%);transition:transform .22s cubic-bezier(.16,1,.3,1);overflow:hidden;box-shadow:var(--shadow)}
#hex-sidebar.open{transform:translateX(0)}
.hex-sidebar-header{padding:14px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.hex-sidebar-title{font-size:13px;font-weight:700;color:var(--text)}
.hex-sidebar-sub{font-family:var(--mono);font-size:10px;color:var(--muted);margin-top:2px}
.hex-close{background:none;border:none;color:var(--muted);font-size:16px;cursor:pointer;padding:2px 5px;border-radius:4px;transition:background .12s}
.hex-close:hover{background:var(--surface2);color:var(--text)}
.hex-popup .leaflet-popup-content-wrapper{background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:8px!important}
.hex-popup .leaflet-popup-tip{background:var(--surface)!important}
.hex-sidebar-body{overflow-y:auto;flex:1;padding:10px;display:flex;flex-direction:column;gap:6px}
.hex-card{background:var(--surface2);border:1px solid var(--border);border-radius:7px;padding:11px;transition:border-color .12s}
.hex-card:hover{border-color:var(--accent2)}
.hex-card-precio{font-family:var(--mono);font-weight:700;color:var(--success);font-size:14px;font-variant-numeric:tabular-nums}
.hex-card-pm2{font-family:var(--mono);font-size:10px;color:var(--muted);margin-top:1px}
.hex-card-meta{font-size:11px;color:var(--muted);margin-top:5px;line-height:1.5}
.hex-card-badges{display:flex;gap:3px;margin-top:5px;flex-wrap:wrap}
.hex-card-badge{padding:2px 5px;border-radius:3px;font-size:9px;font-weight:700;font-family:var(--mono);text-transform:uppercase}
.hex-card-link{display:inline-block;margin-top:7px;color:var(--accent2);text-decoration:none;font-size:10px}
.hex-card-link:hover{text-decoration:underline}
.hex-opor{color:var(--success);font-size:10px;margin-top:4px;font-weight:600}

/* Loading / empty */
.loading{display:flex;align-items:center;justify-content:center;gap:10px;padding:80px;color:var(--muted);font-family:var(--mono);font-size:13px}
.spinner{width:18px;height:18px;border:2px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .75s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.empty{padding:60px;text-align:center;color:var(--muted);font-family:var(--mono)}

/* PAGINATION */
.pagination{display:flex;gap:4px;padding:12px 28px;align-items:center}
.page-btn{padding:4px 10px;background:var(--surface);border:1px solid var(--border);color:var(--text);border-radius:5px;cursor:pointer;font-family:var(--mono);font-size:12px;transition:all .12s}
.page-btn:hover{border-color:var(--muted)}
.page-btn.active{background:var(--accent);color:oklch(99% 0.003 264);border-color:var(--accent);font-weight:700}
.page-info{font-family:var(--mono);font-size:11px;color:var(--muted);margin-left:auto}

/* VALIDATION VIEW */
#view-validacion{display:none;padding:24px 28px}
.val-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}
.val-header h2{font-size:17px;font-weight:700}
.val-header p{font-size:12px;color:var(--muted);margin-top:2px}
.val-stats{display:flex;gap:12px;margin-bottom:20px}
.val-stat{background:var(--surface);border:1px solid var(--border);border-radius:7px;padding:12px 18px;min-width:110px}
.val-stat-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600}
.val-stat-val{font-size:22px;font-weight:700;font-family:var(--mono);margin-top:3px;font-variant-numeric:tabular-nums}
.val-stat-val.yellow{color:var(--warning)}.val-stat-val.green{color:var(--success)}
.val-cards{display:flex;flex-direction:column;gap:8px}
.val-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 18px;display:grid;grid-template-columns:1fr auto;gap:12px;align-items:start;transition:border-color .12s}
.val-card:hover{border-color:var(--muted)}
.val-card.aprobado{border-color:var(--success);opacity:.65}
.val-card.error{border-color:var(--accent3);opacity:.65}
.val-card-precio{font-family:var(--mono);font-size:15px;font-weight:700;color:var(--success);font-variant-numeric:tabular-nums}
.val-card-meta{font-size:12px;color:var(--muted);margin-top:4px;line-height:1.6}
.val-card-sospecha{display:inline-flex;align-items:center;gap:5px;margin-top:7px;padding:3px 9px;background:oklch(96% 0.04 25);border:1px solid oklch(88% 0.08 25);border-radius:5px;font-size:11px;color:var(--accent3);font-family:var(--mono)}
.val-card-actions{display:flex;flex-direction:column;gap:5px;flex-shrink:0}
.val-btn{padding:5px 12px;border-radius:5px;font-size:11px;font-weight:600;cursor:pointer;border:none;font-family:var(--font);transition:opacity .12s;white-space:nowrap}
.val-btn:hover{opacity:.8}
.val-btn-ok{background:oklch(95% 0.05 142);color:var(--success);border:1px solid oklch(88% 0.08 142)}
.val-btn-err{background:oklch(96% 0.04 25);color:var(--accent3);border:1px solid oklch(88% 0.08 25)}
.val-btn-link{background:var(--surface2);color:var(--accent2);border:1px solid var(--border)}
.val-empty{padding:60px;text-align:center;color:var(--muted);font-family:var(--mono)}

/* CONFIG MODAL */
.config-overlay{display:none;position:fixed;inset:0;background:oklch(14% 0.015 264 / 0.45);z-index:200;align-items:center;justify-content:center}
.config-overlay.open{display:flex}
.config-box{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:28px 32px;width:460px;max-width:90vw;box-shadow:var(--shadow)}
.config-box h2{font-size:16px;margin-bottom:6px}
.config-box p{font-size:12px;color:var(--muted);margin-bottom:20px;line-height:1.6}
.config-field{margin-bottom:12px}
.config-field label{display:block;font-size:10px;color:var(--muted);margin-bottom:4px;text-transform:uppercase;letter-spacing:.06em;font-weight:600}
.config-field input{width:100%}
.config-actions{display:flex;gap:8px;margin-top:18px}

/* FUENTE BADGES */
.fuente-badge{display:inline-block;padding:2px 5px;border-radius:3px;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;font-family:var(--mono)}
.fuente-remax{background:oklch(95% 0.04 25);color:oklch(45% 0.22 25)}
.fuente-i24{background:oklch(94% 0.03 220);color:var(--accent2)}
.fuente-propcom{background:oklch(94% 0.05 142);color:var(--success)}
.fuente-ml{background:oklch(96% 0.07 80);color:oklch(45% 0.16 80)}
.fuente-otro{background:var(--surface2);color:var(--muted)}

/* MULTI-SELECT COLONIAS */
.ms-wrap{position:relative;min-width:190px}
.ms-trigger{background:var(--surface);border:1px solid var(--border);color:var(--text);padding:5px 9px;border-radius:var(--radius-sm);font-family:var(--font);font-size:12px;cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:5px;transition:border-color .15s;user-select:none;white-space:nowrap;overflow:hidden;max-width:200px}
.ms-trigger:hover{border-color:var(--muted)}
.ms-trigger.active{border-color:var(--accent)}
.ms-arrow{font-size:9px;color:var(--muted);flex-shrink:0}
.ms-panel{position:absolute;top:calc(100% + 3px);left:0;z-index:500;background:var(--surface);border:1px solid var(--border);border-radius:7px;padding:7px;min-width:220px;box-shadow:var(--shadow);display:none}
.ms-panel.open{display:block}
.ms-search{width:100%;background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:5px 8px;border-radius:4px;font-size:11px;font-family:var(--font);outline:none;margin-bottom:5px}
.ms-list{max-height:200px;overflow-y:auto;display:flex;flex-direction:column;gap:1px}
.ms-opt{display:flex;align-items:center;gap:6px;padding:4px 5px;border-radius:3px;cursor:pointer;font-size:11px;transition:background .1s}
.ms-opt:hover{background:var(--surface2)}
.ms-opt input[type=checkbox]{accent-color:var(--accent);width:12px;height:12px;flex-shrink:0}
.ms-clear{font-size:11px;color:var(--accent);cursor:pointer;text-align:right;padding-top:5px;margin-top:4px;border-top:1px solid var(--border)}
.ms-clear:hover{text-decoration:underline}

/* ══════════════ DEMOGRAFÍA ══════════════ */
#view-demografia{display:none}
#demo-map-container{height:calc(100vh - 204px);min-height:500px;position:relative}
#demo-map{width:100%;height:100%}
.demo-toolbar{position:absolute;top:12px;left:12px;z-index:1000;display:flex;align-items:center;gap:8px;flex-wrap:wrap;background:oklch(99.5% 0.003 264 / 0.95);border:1px solid var(--border);border-radius:8px;padding:8px 12px;backdrop-filter:blur(6px);font-size:11px;max-width:calc(100% - 420px);box-shadow:var(--shadow)}
.demo-toolbar label{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;white-space:nowrap;font-weight:600}
.demo-mode-btn{padding:4px 9px;background:var(--surface2);border:1px solid var(--border);border-radius:5px;cursor:pointer;font-size:11px;font-weight:600;color:var(--muted);transition:all .15s;user-select:none;white-space:nowrap}
.demo-mode-btn:hover{color:var(--text)}
.demo-mode-btn.active{background:var(--accent-dim);border-color:oklch(82% 0.06 264);color:var(--accent)}
.demo-toolbar select{padding:3px 7px;font-size:11px}
#demo-status{font-size:10px;color:var(--muted);font-family:var(--mono);white-space:nowrap}
#demo-sidebar{width:390px}
.demo-sidebar-loading{display:flex;flex-direction:column;align-items:center;justify-content:center;height:180px;gap:10px;color:var(--muted);font-size:12px}
.demo-sidebar-loading .spinner{width:22px;height:22px;border:2px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .75s linear infinite}
.demo-kpi-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;background:var(--border);border-radius:7px;overflow:hidden;margin-bottom:4px}
.demo-kpi{background:var(--surface2);padding:10px 10px 8px;display:flex;flex-direction:column;gap:2px}
.demo-kpi-val{font-family:var(--mono);font-size:17px;font-weight:700;color:var(--text);line-height:1;font-variant-numeric:tabular-nums}
.demo-kpi-lbl{font-size:9px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600}
.demo-score-wrap{display:flex;align-items:center;gap:16px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px 16px;margin-bottom:4px}
.demo-score-num{font-family:var(--mono);font-size:38px;font-weight:700;line-height:1;color:var(--text)}
.demo-score-denom{font-family:var(--mono);font-size:16px;color:var(--muted);margin-top:6px}
.demo-score-label{font-size:12px;font-weight:700;margin-bottom:3px}
.demo-score-sub{font-size:11px;color:var(--muted);line-height:1.4}
.demo-section{background:var(--surface2);border:1px solid var(--border);border-radius:7px;padding:11px;display:flex;flex-direction:column;gap:7px}
.demo-section-title{font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:700;border-bottom:1px solid var(--border);padding-bottom:5px;margin-bottom:1px}
.demo-cmp-row{display:flex;flex-direction:column;gap:3px;margin-bottom:3px}
.demo-cmp-label{display:flex;justify-content:space-between;align-items:baseline}
.demo-cmp-name{font-size:11px;color:var(--text);font-weight:500}
.demo-cmp-vals{font-family:var(--mono);font-size:10px;color:var(--muted)}
.demo-bars-wrap{display:flex;flex-direction:column;gap:3px}
.demo-bar-row{display:flex;align-items:center;gap:6px}
.demo-bar-lbl{font-family:var(--mono);font-size:9px;color:var(--muted);width:28px;text-align:right;flex-shrink:0}
.demo-bar-track{flex:1;height:5px;background:var(--border);border-radius:3px;overflow:hidden}
.demo-bar-fill{height:100%;border-radius:3px;transition:width .4s cubic-bezier(.16,1,.3,1);min-width:2px}
.demo-bar-fill.zona{background:var(--accent)}
.demo-bar-fill.mun{background:var(--accent2)}
.demo-bar-fill.neg{background:var(--accent3)}
.demo-nse-grid{display:flex;flex-wrap:wrap;gap:4px}
.demo-nse-pill{display:flex;align-items:center;gap:5px;padding:3px 7px;border-radius:20px;font-size:11px;font-weight:600;border:1px solid var(--border);background:var(--surface)}
.demo-nse-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.demo-age-row{display:flex;align-items:center;gap:7px;margin-bottom:3px}
.demo-age-lbl{font-size:10px;color:var(--muted);width:44px;flex-shrink:0}
.demo-age-bars{flex:1;display:flex;flex-direction:column;gap:2px}
.demo-viv-row{display:flex;align-items:center;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border)}
.demo-viv-row:last-child{border-bottom:none}
.demo-viv-name{font-size:11px;color:var(--text)}
.demo-alert{display:flex;align-items:flex-start;gap:7px;padding:7px 9px;border-radius:5px;font-size:11px;line-height:1.45;margin-top:3px}
.demo-alert.warn{background:oklch(96% 0.04 25);border:1px solid oklch(88% 0.08 25);color:var(--accent3)}
.demo-alert.ok{background:oklch(95% 0.05 142);border:1px solid oklch(87% 0.09 142);color:var(--success)}
.demo-alert.info{background:oklch(95% 0.03 220);border:1px solid oklch(87% 0.06 220);color:var(--accent2)}
.demo-alert-icon{font-size:12px;flex-shrink:0}
#demo-heatmap-legend{position:absolute;bottom:20px;right:20px;z-index:1000;background:oklch(99.5% 0.003 264 / 0.95);border:1px solid var(--border);border-radius:8px;padding:11px 14px;min-width:170px;backdrop-filter:blur(6px);box-shadow:var(--shadow);display:none}
.demo-legend-title{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;font-weight:700}
.demo-legend-bar{height:6px;border-radius:3px;margin-bottom:5px}
.demo-legend-labels{display:flex;justify-content:space-between;font-family:var(--mono);font-size:9px;color:var(--muted)}
.demo-nse-legend{display:flex;flex-direction:column;gap:4px}
.demo-nse-legend-item{display:flex;align-items:center;gap:6px;font-size:10px;color:var(--muted)}
.demo-nse-legend-dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}

/* View transitions */
#view-mercado, #view-demografia { animation:fadeIn .12s ease-out }
@keyframes fadeIn { from{opacity:.8;transform:translateY(1px)} to{opacity:1;transform:translateY(0)} }

/* Scrollbar */
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--muted)}
</style>"""

html = SRC.read_text(encoding="utf-8")

# 1. Replace the entire <style> block
html = re.sub(r"<style>.*?</style>", NEW_CSS, html, flags=re.DOTALL)

# 2. Fix logo: "Torreón RE · Dashboard" -> "CAMPO <em>· Torreón</em>"
html = html.replace(
    '<div class="logo">Torreón <span>RE</span> · Dashboard</div>',
    '<div class="logo">CAMPO <em>· Torreón</em></div>'
)

# 3. Fix version tag in header (inline style -> class)
html = html.replace(
    '<span style="font-family:var(--mono);font-size:10px;color:var(--border);background:var(--surface2);padding:2px 8px;border-radius:4px;border:1px solid var(--border)">v2.0</span>',
    '<span class="version-tag">v2.0</span>'
)

# 4. Default basemap: dark -> light
html = html.replace("setBasemap('dark');", "setBasemap('light');")
html = html.replace(
    'onclick="setBasemap(\'dark\')" id="bm-dark">Oscuro</div>',
    'onclick="setBasemap(\'dark\')" id="bm-dark">Oscuro</div>'
)
# Fix the active state to start on 'light' not 'dark'
html = html.replace(
    '<div class="basemap-btn active" onclick="setBasemap(\'dark\')" id="bm-dark">Oscuro</div>\n      <div class="basemap-btn" onclick="setBasemap(\'light\')" id="bm-light">Claro</div>',
    '<div class="basemap-btn" onclick="setBasemap(\'dark\')" id="bm-dark">Oscuro</div>\n      <div class="basemap-btn active" onclick="setBasemap(\'light\')" id="bm-light">Claro</div>'
)

# 5. Demo map: dark tiles -> light (Positron)
html = html.replace(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
)

DEST.write_text(html, encoding="utf-8")
print(f"[OK] {DEST} — {len(html):,} chars")
print(f"[OK] Light mode aplicado")
print(f"[OK] Logo -> CAMPO")
print(f"[OK] Basemap default -> light (CartoDB Positron)")
print(f"[OK] Demo map -> light tiles")
