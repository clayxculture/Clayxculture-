import json
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844},service_workers='block')
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    def route(r):
        u=r.request.url
        if '/rest/v1/products' in u: r.fulfill(status=200,content_type='application/json',body='[]')
        elif 'supabase' in u: r.fulfill(status=200,content_type='application/json',body='[]')
        elif u.startswith('http://localhost'): r.continue_()
        else: r.abort()
    pg.route('**/*',route);pg.goto('http://localhost:8077/');pg.wait_for_timeout(800)
    txt=pg.inner_text('#grid');print('home grid:',txt[:60].replace('\n',' '));assert 'launching soon' in txt.lower() and pg.locator('#grid .card').count()==0
    pg.evaluate("nav('/shop/hoodies')");pg.wait_for_timeout(300);print('col:',pg.inner_text('#cg')[:50].replace('\n',' '))
    print('errors',errs);b.close()
