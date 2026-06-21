# -*- coding: utf-8 -*-
"""Descarga las imagenes del carrusel de un post de Instagram para leerlas
(precio/specs quemados en la imagen). Uso: py scripts/ig_carousel.py <shortcode>"""
import sys, os, time, re, urllib.request

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ocr')


def main(sc):
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    url = f'https://www.instagram.com/p/{sc}/'
    srcs = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(viewport={'width': 1200, 'height': 1000},
                            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36')
        page = ctx.new_page()
        page.goto(url, timeout=30000); time.sleep(3)
        def grab():
            imgs = page.eval_on_selector_all(
                'article img, img',
                "els => els.map(e=>({s:e.src,w:e.naturalWidth||0})).filter(x=>/cdninstagram|fbcdn/.test(x.s))")
            for it in imgs:
                if it['s'] not in srcs and (it['w'] >= 320 or 'e35' in it['s']):
                    srcs.append(it['s'])
        grab()
        for _ in range(9):
            nxt = page.query_selector('button[aria-label="Next"], button[aria-label="Siguiente"], [aria-label="Next"]')
            if not nxt:
                break
            try:
                nxt.click(); time.sleep(1.2); grab()
            except Exception:
                break
        b.close()
    print(f'{len(srcs)} imagenes encontradas')
    saved = []
    for i, s in enumerate(srcs):
        try:
            data = urllib.request.urlopen(
                urllib.request.Request(s, headers={'User-Agent': 'Mozilla/5.0'}), timeout=25).read()
            p = os.path.join(OUT, f'{sc}_{i}.jpg')
            open(p, 'wb').write(data); saved.append(p)
            print('  guardada', p, f'{round(len(data)/1024)}KB')
        except Exception as e:
            print('  err', str(e)[:50])
    return saved


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'DZKCNNNlRtf')
