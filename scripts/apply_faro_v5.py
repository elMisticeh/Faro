"""
apply_faro_v5.py — FARO v5
  Palette 03 GRID: white #f0f2f5 + emerald #10b981 + near-black #0d1117
  Logo B: Pin (circle + nucleus)
  Typography: Sora + Space Mono
"""
import os, re

SRC  = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dashboard.html')
DOCS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'index.html')

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. FONTS ──────────────────────────────────────────────────────────────────
OLD_FONT = 'https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@400;500;600;700&family=Mulish:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap'
NEW_FONT = 'https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap'
html = html.replace(OLD_FONT, NEW_FONT)
print('[OK] Fonts -> Sora + Space Mono')

# ── 2. CSS ROOT TOKENS ────────────────────────────────────────────────────────
OLD_ROOT = """:root {
  /* FARO — VERTICE Family · Cream / Gold */
  --bg:         oklch(97.5% 0.008 72);
  --surface:    oklch(99.0% 0.004 72);
  --surface2:   oklch(93.8% 0.016 68);
  --border:     oklch(87.0% 0.018 68);
  --text:       oklch(12.5% 0.018 72);
  --muted:      oklch(52.0% 0.015 70);
  --accent:     oklch(33% 0.21 243);
  --accent-dim: oklch(94% 0.022 243);
  --accent2:    oklch(48% 0.18 243);
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

NEW_ROOT = """:root {
  /* FARO v5 — GRID: White + Emerald + Near-Black */
  --bg:         #f0f2f5;
  --surface:    #ffffff;
  --surface2:   #f5f6f8;
  --border:     #e2e4e8;
  --text:       #0d1117;
  --muted:      #6b7280;
  --accent:     #10b981;
  --accent-dim: #ecfdf5;
  --accent2:    #059669;
  --accent3:    #ef4444;
  --success:    #10b981;
  --warning:    #f59e0b;
  --font:         'Sora', system-ui, sans-serif;
  --font-display: 'Sora', system-ui, sans-serif;
  --mono:         'Space Mono', ui-monospace, monospace;
  --radius:     8px;
  --radius-sm:  5px;
  --shadow-sm:  0 1px 3px rgba(13,17,23,.06), 0 1px 2px rgba(13,17,23,.04);
  --shadow:     0 4px 16px rgba(13,17,23,.08);
}"""

html = html.replace(OLD_ROOT, NEW_ROOT)
print('[OK] CSS tokens -> GRID palette')

# Fix version-tag border leftover
html = html.replace(
    'border:1px solid oklch(88% 0.035 243)',
    'border:1px solid #a7f3d0'
)

# ── 3. LOGO SVGs — add 'pin', set as default ─────────────────────────────────
OLD_LOGOS = """const LOGO_SVGS = {
  bars:     `<svg viewBox='0 0 32 32' fill='currentColor'><rect x='4'  y='18' width='6' height='10' rx='1'/><rect x='13' y='10' width='6' height='18' rx='1'/><rect x='22' y='4'  width='6' height='24' rx='1'/></svg>`,
  reticle:  `<svg viewBox='0 0 32 32' fill='none' stroke='currentColor' stroke-width='1.6' stroke-linecap='round'><rect x='8' y='8' width='16' height='16' rx='1'/><line x1='16' y1='3' x2='16' y2='7'/><line x1='16' y1='25' x2='16' y2='29'/><line x1='3' y1='16' x2='7' y2='16'/><line x1='25' y1='16' x2='29' y2='16'/><circle cx='16' cy='16' r='2' fill='currentColor' stroke='none'/></svg>`,
  fmark:    `<svg viewBox='0 0 32 32' fill='currentColor'><rect x='6' y='5' width='20' height='4' rx='1'/><rect x='6' y='5' width='4' height='22' rx='1'/><rect x='6' y='15' width='14' height='3.5' rx='1'/></svg>`,
  wave:     `<svg viewBox='0 0 32 32' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='3,22 9,10 15,18 21,8 27,14'/><circle cx='27' cy='14' r='2' fill='currentColor' stroke='none'/></svg>`,
};"""

NEW_LOGOS = """const LOGO_SVGS = {
  pin:      `<svg viewBox='0 0 22 22' fill='none' stroke='currentColor' stroke-width='1.6'><circle cx='11' cy='11' r='9.5'/><circle cx='11' cy='11' r='3.8' fill='currentColor' stroke='none'/></svg>`,
  signal:   `<svg viewBox='0 0 32 32' fill='currentColor'><rect x='3'  y='19' width='7' height='10' rx='1.5'/><rect x='12.5' y='11' width='7' height='18' rx='1.5'/><rect x='22' y='3'  width='7' height='26' rx='1.5'/></svg>`,
  frame:    `<svg viewBox='0 0 32 32' fill='none' stroke='currentColor' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'><path d='M10 4 L4 4 L4 28 L10 28'/><path d='M22 4 L28 4 L28 28 L22 28'/></svg>`,
  slash:    `<svg viewBox='0 0 32 32' fill='none' stroke='currentColor' stroke-linecap='round'><line x1='22' y1='4' x2='10' y2='28' stroke-width='3'/><circle cx='10' cy='28' r='3.5' fill='currentColor' stroke='none'/></svg>`,
};"""

html = html.replace(OLD_LOGOS, NEW_LOGOS)
html = html.replace(
    "const LOGO_NAMES = { bars: 'Barras', reticle: 'Reticula', fmark: 'F-Mark', wave: 'Onda' };",
    "const LOGO_NAMES = { pin: 'Pin', signal: 'Signal', frame: 'Frame', slash: 'Slash' };"
)
html = html.replace(
    "return localStorage.getItem('faro_logo') || 'bars';",
    "return localStorage.getItem('faro_logo') || 'pin';"
)
print('[OK] Logos -> pin (default) / signal / frame / slash')

# ── 4. Logo mark in PDF (update inline SVG beacon → pin) ─────────────────────
OLD_PDF_SVG = """<svg viewBox='0 0 32 32' width='22' height='22' fill='none' stroke='#3c78d2' stroke-linecap='round' style='flex-shrink:0'>
          <circle cx='16' cy='7' r='3' fill='#3c78d2' stroke='none'/>
          <line x1='16' y1='10' x2='16' y2='28' stroke-width='1.8'/>
          <line x1='16' y1='17' x2='7' y2='28' stroke-width='1.2' opacity='0.5'/>
          <line x1='16' y1='17' x2='25' y2='28' stroke-width='1.2' opacity='0.5'/>
        </svg>"""
NEW_PDF_SVG = """<svg viewBox='0 0 22 22' width='22' height='22' fill='none' stroke='#10b981' stroke-width='1.6' style='flex-shrink:0'>
          <circle cx='11' cy='11' r='9.5'/>
          <circle cx='11' cy='11' r='3.8' fill='#10b981' stroke='none'/>
        </svg>"""
html = html.replace(OLD_PDF_SVG, NEW_PDF_SVG)
print('[OK] PDF logo -> Pin SVG en emerald')

# ── 5. PDF report colors: blue → emerald, dark covers → light ────────────────
# Cover dark bg → emerald dark
html = html.replace(
    "background:linear-gradient(135deg,#0a0f1e 0%,#0d1830 60%,#112040 100%)",
    "background:linear-gradient(135deg,#064e3b 0%,#065f46 55%,#047857 100%)"
)
html = html.replace("border:1px solid rgba(60,120,210,.18)", "border:1px solid rgba(16,185,129,.18)")
html = html.replace("border:1px solid rgba(60,120,210,.12)", "border:1px solid rgba(16,185,129,.12)")

# Blue accents in PDF → emerald
html = html.replace("color:#3c78d2;letter-spacing:.22em;text-transform:uppercase", "color:#10b981;letter-spacing:.22em;text-transform:uppercase")
html = html.replace("--accent:#2857b8", "--accent:#10b981")
html = html.replace("stroke='#3c78d2'", "stroke='#10b981'")
html = html.replace("fill='#3c78d2'", "fill='#10b981'")
html = html.replace("color:#3c78d2", "color:#10b981")
html = html.replace("background:#3c78d2", "background:#10b981")
html = html.replace("border-left:3px solid #3c78d2", "border-left:3px solid #10b981")
html = html.replace("border-left:2px solid #3c78d2", "border-left:2px solid #10b981")
html = html.replace("background:linear-gradient(90deg,#3c78d2 0%", "background:linear-gradient(90deg,#10b981 0%")
html = html.replace("color:#8a96b0", "color:#9ca3af")
html = html.replace("#dce3f0", "#e5e7eb")
html = html.replace("#f4f6fb", "#f9fafb")
html = html.replace("#e8edf8", "#f0fdf4")
html = html.replace("#f8faff", "#ffffff")
html = html.replace("background:#f4f6fb", "background:#f9fafb")
html = html.replace("font-size:.9rem;font-weight:700;color:#0a1628", "font-size:.9rem;font-weight:700;color:#0d1117")

# PDF wordmark color
html = html.replace(
    "font-family:'Barlow Semi Condensed',system-ui,sans-serif;font-weight:700;font-size:.95rem;letter-spacing:.04em;color:#1a1000",
    "font-family:'Sora',system-ui,sans-serif;font-weight:700;font-size:.9rem;letter-spacing:.02em;color:#0d1117"
)
# PDF sub color in wordmark
html = html.replace(
    "color:#C8A24B;font-weight:400;font-size:.72rem;letter-spacing:.18em;font-family:'IBM Plex Mono',monospace;vertical-align:middle",
    "color:#10b981;font-weight:400;font-size:.72rem;letter-spacing:.18em;font-family:'Space Mono',monospace;vertical-align:middle"
)

# PDF fonts import
html = html.replace(
    "@import url('https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@400;600;700&family=Mulish:wght@300;400;600&family=IBM+Plex+Mono:wght@400;500&display=swap');",
    "@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=Space+Mono:wght@400;700&display=swap');"
)

# PDF display font references
html = html.replace("font-family:'Barlow Semi Condensed',sans-serif", "font-family:'Sora',sans-serif")
html = html.replace("font-family:'IBM Plex Mono',monospace", "font-family:'Space Mono',monospace")
html = html.replace("font-family:'Mulish',sans-serif", "font-family:'Sora',sans-serif")

print('[OK] PDF report -> emerald palette + Sora/Space Mono')

# ── 6. Onboarding button color ────────────────────────────────────────────────
html = html.replace(
    '.ob-btn{background:var(--accent);color:#1a1000;',
    '.ob-btn{background:var(--accent);color:#ffffff;'
)

# ── 7. Market filter modal btn-reporte override ───────────────────────────────
# The emerald btn-reporte second button
html = html.replace(
    '<button class="btn-reporte" onclick="abrirFiltrosMercado()" title="Reporte de mercado inmobiliario PDF" style="margin-top:6px">',
    '<button class="btn-reporte" onclick="abrirFiltrosMercado()" title="Reporte de mercado inmobiliario PDF" style="margin-top:6px;background:#059669">'
)

# ── 8. WRITE ──────────────────────────────────────────────────────────────────
for path, name in [(SRC, 'dashboard.html'), (DOCS, 'index.html')]:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    kb = os.path.getsize(path) / 1024
    print(f'[OK] Written: {name} ({kb:.0f} KB)')

print('\nFARO v5 listo — GRID + Pin + Sora/Space Mono.')
