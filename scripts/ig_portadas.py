# -*- coding: utf-8 -*-
"""
Genera las portadas (foto de cabecera) de los TERRENOS de Instagram para las
tarjetas de recomendacion del reporte "Donde Desarrollar".

Baja el og:image de cada post IG (via Playwright), lo comprime (Pillow, ~360px
JPEG) y lo embebe como data URI en `frontend/dashboard.html` entre los marcadores
__IG_PORTADAS_START__ / __IG_PORTADAS_END__ -> window.IG_PORTADAS = {link: dataURI}.

Las URLs del CDN de Instagram caducan; por eso se embebe el binario, no la URL.

    py scripts/ig_portadas.py
"""
import os, sys, re, io, json, base64, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, 'frontend', 'dashboard.html')


def env():
    e = {}
    for line in open(os.path.join(ROOT, '.env'), encoding='utf-8'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1); e[k] = v.strip()
    return e


def terrenos_ig():
    e = env(); base = e['SUPABASE_URL'].rstrip('/'); key = e['SUPABASE_KEY']
    u = (base + '/rest/v1/listings?select=link_publicacion,pagina_fuente,colonia'
         '&tipo_inmueble=eq.terreno&activo=eq.true&pagina_fuente=like.instagram*')
    req = urllib.request.Request(u, headers={'apikey': key, 'Authorization': 'Bearer ' + key})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def comprimir(data):
    im = Image.open(io.BytesIO(data)).convert('RGB')
    w = 360
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)))
    out = io.BytesIO(); im.save(out, 'JPEG', quality=72, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(out.getvalue()).decode()


def main():
    rows = terrenos_ig()
    print(f'Terrenos IG activos: {len(rows)}')
    portadas = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(); ctx = b.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36')
        page = ctx.new_page()
        for r in rows:
            link = r['link_publicacion']
            try:
                page.goto(link, timeout=25000); time.sleep(2)
                img = page.get_attribute('meta[property="og:image"]', 'content')
                if not img:
                    print('  sin og:image:', link); continue
                data = urllib.request.urlopen(
                    urllib.request.Request(img, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).read()
                portadas[link] = comprimir(data)
                print(f"  OK {r['colonia']:28} {round(len(portadas[link])/1024)}KB  {link[-14:]}")
            except Exception as ex:
                print('  ERR', link[-14:], str(ex)[:60])
        b.close()

    blob = 'window.IG_PORTADAS=' + json.dumps(portadas, ensure_ascii=False) + ';'
    html = open(HTML, encoding='utf-8').read()
    html2 = re.sub(r'/\*__IG_PORTADAS_START__\*/.*?/\*__IG_PORTADAS_END__\*/',
                   '/*__IG_PORTADAS_START__*/' + blob + '/*__IG_PORTADAS_END__*/',
                   html, count=1, flags=re.S)
    if html2 == html:
        print('AVISO: no se encontraron los marcadores __IG_PORTADAS__ en el HTML.')
    else:
        open(HTML, 'w', encoding='utf-8', newline='').write(html2)
        tot = sum(len(v) for v in portadas.values())
        print(f'\nEmbebidas {len(portadas)} portadas en dashboard.html (~{round(tot/1024)}KB).')


if __name__ == '__main__':
    main()
