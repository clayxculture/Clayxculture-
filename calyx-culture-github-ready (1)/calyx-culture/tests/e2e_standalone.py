"""The four standalone pages (about, stores, contact, faq): real HTML files, strict CSP, live data, contact form.
Runs against tests/serve.py, which applies site/_headers and _redirects like Netlify does."""
import json
from playwright.sync_api import sync_playwright
BASE = 'http://localhost:8077'
bad = []
def ok(x): return dict(status=200, content_type='application/json', body=json.dumps(x))
PRODUCTS = [{'id': i, 'name': f'Hoodie {i}', 'price': 1200 + i, 'compare_at': 1800 if i == 1 else None, 'image_url': 'calyx/p/x%d' % i} for i in range(1, 5)]
posts = []
def mock(r):
    u, m = r.request.url, r.request.method
    if u.startswith(BASE): return r.continue_()
    if m == 'POST' and 'contact_messages' in u: posts.append(json.loads(r.request.post_data)); return r.fulfill(status=201, body='')
    if 'store_settings' in u: return r.fulfill(**ok([
        {'key': 'stores', 'value': [{'name': 'calyxculture Bemina', 'address': 'Bemina, Srinagar', 'phone': '+91 8899190631'}, {'name': 'calyxculture Lal Chowk', 'address': 'Lal Chowk, Srinagar'}]},
        {'key': 'seller', 'value': {'support_hours': 'Mon-Sat 10am to 8pm', 'support_email': 'hello@example.com'}},
        {'key': 'free_ship_threshold', 'value': 2499}]))
    if '/rest/v1/faq' in u: return r.fulfill(**ok([{'question': 'Mock question?', 'answer': 'Mock answer <img src=x onerror=alert(1)>'}]))
    if '/rest/v1/products' in u: return r.fulfill(**ok(PRODUCTS))
    if 'supabase' in u: return r.fulfill(**ok([]))
    r.abort()
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, vp in (('mobile', {'width': 390, 'height': 844}), ('desktop', {'width': 1280, 'height': 800})):
        ctx = b.new_context(viewport=vp, service_workers='block'); ctx.route('**/*', mock)
        for path, h1, extra in (('/about', 'Rooted in Srinagar', 'New arrivals'), ('/stores', 'Our stores', 'calyxculture Lal Chowk'), ('/contact', 'Talk to us', 'Send us a message'), ('/faq', 'Questions, answered', 'Mock question?')):
            pg = ctx.new_page(); msgs = []
            pg.on('console', lambda m: msgs.append(m.text) if m.type in ('error', 'warning') and 'Failed to load resource' not in m.text else None)
            pg.on('pageerror', lambda e: msgs.append(str(e)))
            pg.on('dialog', lambda d: (bad.append('alert fired: ' + d.message), d.dismiss()))
            resp = pg.goto(BASE + path); pg.wait_for_timeout(700)
            assert resp.status == 200, (path, resp.status)
            assert 'script-src \'self\';' in resp.headers['content-security-policy'] and 'unsafe-inline' not in resp.headers['content-security-policy'].split('style-src')[0], path
            assert h1.lower() in pg.inner_text('h1').lower(), (path, pg.inner_text('h1'))
            assert extra.lower() in pg.inner_text('main').lower(), (path, extra)
            assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), f'{name} {path}: horizontal scroll'
            assert not msgs, (name, path, msgs)
            assert pg.title() and pg.locator('link[rel=canonical]').count() == 1 and pg.locator('meta[name=description]').count() == 1
            assert pg.locator('h1').count() == 1
            # live data
            if path == '/about' or path == '/stores':
                assert pg.locator('#pop:not([hidden]) .pc').count() == 4, 'new arrivals'
                assert pg.locator('#pop .pc a, a.pc').first.get_attribute('href').startswith('/product/')
                assert '₹2,499' in pg.inner_text('[data-fs]') if pg.locator('[data-fs]').count() else True
            if path == '/stores': assert pg.locator('.sc').count() == 2 and 'Mon-Sat' in pg.inner_text('[data-hours]')
            if path == '/faq': assert pg.locator('#faq-list img').count() == 0 and 'onerror' in pg.text_content('#faq-list')  # database text stays text
            # sticky order bar only on small screens
            assert pg.locator('.dock').is_visible() == (name == 'mobile'), 'dock'
            if name == 'mobile':
                pg.click('#mn summary'); assert pg.locator('#mn nav a[href="/stores"]').is_visible(); pg.keyboard.press('Escape'); assert not pg.locator('#mn nav').is_visible()
            if name == 'mobile': pg.screenshot(path=f'out/{path[1:]}-mobile.png', full_page=True)
            else: pg.screenshot(path=f'out/{path[1:]}-desktop.png', full_page=True)
            # every internal link on the page resolves
            for href in set(pg.eval_on_selector_all('a[href^="/"]', 'els=>els.map(e=>e.getAttribute("href"))')):
                if href.startswith('/product/'): continue
                st = pg.evaluate('h=>fetch(h).then(r=>r.status)', href.split('#')[0]); assert st == 200, (path, href, st)
            if path == '/contact' and name == 'mobile':
                pg.fill('#c-n', 'Asif'); pg.fill('#c-p', '12345'); pg.fill('#c-m', 'Is the hoodie in XL?'); pg.click('#cff button[type=submit]')
                assert 'valid 10-digit' in pg.inner_text('#cfo') and not posts
                pg.fill('#c-p', '98765 00000'); pg.click('#cff button[type=submit]'); pg.wait_for_timeout(500)
                assert posts == [{'name': 'Asif', 'phone': '9876500000', 'message': 'Is the hoodie in XL?'}], posts
                assert 'reached our team' in pg.inner_text('#cfo')
            pg.close()
        ctx.close()
    # the shop app itself must run under the strict CSP (no inline script)
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, service_workers='block'); ctx.route('**/*', mock); ctx.add_init_script("localStorage.setItem('cc_wel',String(Date.now()))")
    pg = ctx.new_page(); msgs = []; pg.on('console', lambda m: msgs.append(m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None); pg.on('pageerror', lambda e: msgs.append(str(e)))
    pg.goto(BASE + '/'); pg.wait_for_timeout(800)
    assert not msgs, msgs
    pg.click('[data-open=menu]'); pg.wait_for_timeout(300)
    with pg.expect_navigation(): pg.click('#menu a[href="/about"]')
    assert pg.url.endswith('/about') and 'rooted in srinagar' in pg.inner_text('h1').lower(), pg.url   # a real page load, not the shop app
    r404 = pg.goto(BASE + '/definitely-missing'); assert r404.status == 404 and 'wrong turn' in pg.inner_text('body').lower()
    b.close()
assert not bad, bad
print('standalone pages ok')
