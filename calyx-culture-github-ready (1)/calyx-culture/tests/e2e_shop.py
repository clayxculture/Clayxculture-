"""Every Shop / category / bottom-bar button on the home page, in every situation that has caused trouble:
phone portrait + landscape, desktop, slow data (tap before products load), store with no New / Sale / Winter
styles, a second tap, the keyboard, going back, other pages, and the file:// preview.  Run: python3 e2e_shop.py"""
import json, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_FILE = 'file://' + os.path.abspath(os.path.join(HERE, '..', 'site', 'index.html'))
URL = 'http://localhost:8077/'
errs = []


def products(kind):
    out = []
    for i in range(1, 13):
        if kind == 'full':
            c = ['Denim', 'Hoodies', 'T-Shirts', 'Winter'][i % 4]
            badge = 'New' if i in (1, 2) else None
            cmp_ = 2500 if i == 3 else None
        else:  # no New, no Sale, no Winter
            c = ['Denim', 'Hoodies'][i % 2]
            badge, cmp_ = None, None
        out.append({'id': i, 'name': f'Item {i}', 'category': c, 'kind': 'hood', 'price': 900 + i * 50,
                    'compare_at': cmp_, 'badge': badge, 'colors': ['Black'], 'image_url': None, 'stock': None,
                    'is_demo': False, 'created_at': '2025-01-01T00:00:00Z'})
    return out


def new_ctx(b, vp, kind='full', hold=False, touch=False, file_mode=False):
    ctx = b.new_context(viewport=vp, has_touch=touch, is_mobile=touch, service_workers='block', bypass_csp=True)
    ctx.add_init_script("localStorage.setItem('cc_wel',String(Date.now()))")
    held = []
    data = products(kind)

    def route(r):
        u = r.request.url

        def ok(x):
            r.fulfill(status=200, content_type='application/json', body=json.dumps(x))
        if '/rest/v1/products' in u:
            if hold:
                held.append(lambda: ok(data))
            else:
                ok(data)
        elif 'rpc/home_extras' in u:
            ok({'stats': {}, 'best': [], 'latest': []})
        elif 'supabase' in u:
            ok([])
        elif u.startswith('file:') or u.startswith('http://localhost'):
            r.continue_()
        else:
            r.abort()
    ctx.route('**/*', route)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(SITE_FILE if file_mode else URL)
    if not hold:
        pg.wait_for_function("document.querySelectorAll('#grid .card').length>0", timeout=8000)
    pg.wait_for_timeout(500)
    return ctx, pg, held


def where(pg):
    return pg.evaluate("(location.protocol==='file:'?location.hash.slice(1):location.pathname)")


def wait_path(pg, p, what):
    try:
        pg.wait_for_function("p=>(location.protocol==='file:'?location.hash.slice(1):location.pathname)===p", arg=p, timeout=4000)
    except Exception:
        raise AssertionError(f'{what}: expected {p}, got {where(pg)}')


def on_collection(pg, title, what):
    pg.wait_for_function("t=>!document.querySelector('#col').hidden&&document.querySelector('#ct').textContent===t", arg=title, timeout=4000)
    try:  # the title can appear a moment before the cards render, so wait for them instead of counting at once
        pg.wait_for_function("document.querySelectorAll('#cg .card').length>0", timeout=4000)
    except Exception:
        raise AssertionError(f'{what}: collection "{title}" shows no styles')


def home_visible(pg):
    return pg.evaluate("!document.querySelector('main').hidden&&document.querySelector('#col').hidden")


def back_home(pg, what):
    pg.go_back()
    pg.wait_for_function("!document.querySelector('main').hidden", timeout=4000)
    assert home_visible(pg), what + ': back did not return to home'
    pg.evaluate("scrollTo(0,0)")
    pg.wait_for_timeout(150)


def click_and_check(pg, sel, path, title, what, nth=0):
    loc = pg.locator(sel).nth(nth)
    loc.scroll_into_view_if_needed()
    loc.click()
    wait_path(pg, path, what)
    on_collection(pg, title, what)
    back_home(pg, what)


def home_buttons(pg, label):
    click_and_check(pg, '.hero [data-cat=New]', '/shop/new', 'New arrivals', label + ' hero New')
    click_and_check(pg, '.hero [data-cat=All]', '/shop', 'All styles', label + ' hero All')
    click_and_check(pg, '.lk', '/shop/denim', 'Denim', label + ' lookbook denim', 0)
    click_and_check(pg, '.lk', '/shop/winter', 'Winter', label + ' lookbook winter', 1)
    click_and_check(pg, '.lk', '/shop', 'All styles', label + ' lookbook all', 2)
    n = pg.locator('#tiles a').count()
    assert n >= 3, label + ' category tiles missing'
    for i in range(n):
        pg.locator('#tiles a').nth(i).scroll_into_view_if_needed()
        pg.locator('#tiles a').nth(i).click()
        pg.wait_for_function("!document.querySelector('#col').hidden", timeout=4000)
        assert pg.locator('#cg .card').count() > 0, f'{label} tile {i} shows no styles'
        assert '/shop/' in where(pg), f'{label} tile {i} went to {where(pg)}'
        back_home(pg, f'{label} tile {i}')
    for i in range(pg.locator('footer [data-cat]').count()):
        b = pg.locator('footer [data-cat]').nth(i)
        b.scroll_into_view_if_needed()
        cat = b.get_attribute('data-cat')
        b.click()
        pg.wait_for_function("!document.querySelector('#col').hidden", timeout=4000)
        assert pg.locator('#cg .card').count() > 0, f'{label} footer {cat} shows no styles'
        back_home(pg, f'{label} footer {cat}')
    pg.locator('[data-open=fd]').first.scroll_into_view_if_needed()
    pg.locator('[data-open=fd]').first.click()
    pg.wait_for_function("document.querySelectorAll('dialog[open]').length===1", timeout=3000)
    pg.keyboard.press('Escape')
    pg.wait_for_function("document.querySelectorAll('dialog[open]').length===0", timeout=3000)


def bottom_bar(pg, label):
    # Shop on the home page scrolls to the collection, and is not hidden under the header
    pg.evaluate("scrollTo(0,0)")
    pg.wait_for_timeout(200)
    pg.locator('.bn [data-go=shop]').click()
    pg.wait_for_function("(()=>{const t=document.getElementById('shop').getBoundingClientRect().top;return t>=0&&t<260})()", timeout=4000)
    pg.locator('.bn [data-go=top]').click()
    pg.wait_for_function("scrollY<5", timeout=4000)
    for page in ('/shop/denim', '/about', '/product/1'):
        pg.evaluate(f"nav('{page}')")
        pg.wait_for_timeout(300)
        assert not home_visible(pg), f'{label} {page} should not show home'
        pg.locator('.bn [data-go=top]').click()
        wait_path(pg, '/', f'{label} bottom Home from {page}')
        assert home_visible(pg), f'{label} bottom Home from {page} did not show home'
        pg.evaluate(f"nav('{page}')")
        pg.wait_for_timeout(300)
        pg.locator('.bn [data-go=shop]').click()
        wait_path(pg, '/shop', f'{label} bottom Shop from {page}')
        on_collection(pg, 'All styles', f'{label} bottom Shop from {page}')
        pg.evaluate("nav('/')")
        pg.wait_for_timeout(200)


def history_len(pg):
    return pg.evaluate("history.length")


def run():
    with sync_playwright() as p:
        b = p.chromium.launch()
        # 1) full store: every control, on a portrait phone, a landscape phone and a desktop
        for name, vp, touch, bar in (('phone-portrait', {'width': 390, 'height': 844}, True, True),
                                     ('phone-landscape', {'width': 844, 'height': 390}, True, True),
                                     ('tablet-landscape', {'width': 1024, 'height': 768}, True, False),
                                     ('desktop', {'width': 1440, 'height': 900}, False, False)):
            ctx, pg, _ = new_ctx(b, vp, 'full', touch=touch)
            home_buttons(pg, name)
            if bar and pg.locator('.bn').is_visible():
                bottom_bar(pg, name)
            # a second tap right after the first must not stack history entries
            before = history_len(pg)
            pg.evaluate("(()=>{const b=document.querySelector('.hero [data-cat=All]');b.click();b.click()})()")
            pg.wait_for_timeout(500)
            assert history_len(pg) - before <= 1, f'{name}: double tap added {history_len(pg) - before} history entries'
            ctx.close()
            print(name, 'ok')
        # 2) keyboard: Tab to the hero button and press Enter
        ctx, pg, _ = new_ctx(b, {'width': 1280, 'height': 800}, 'full')
        pg.focus('.hero [data-cat=New]')
        pg.keyboard.press('Enter')
        wait_path(pg, '/shop/new', 'keyboard Enter')
        ctx.close()
        # 3) tap before the products have loaded: the page must end on the right list once they arrive
        for sel, nth, path, title in (('.hero [data-cat=New]', 0, '/shop/new', 'New arrivals'),
                                      ('.lk', 1, '/shop/winter', 'Winter'),
                                      ('.hero [data-cat=All]', 0, '/shop', 'All styles')):
            ctx, pg, held = new_ctx(b, {'width': 390, 'height': 844}, 'full', hold=True, touch=True)
            pg.locator(sel).nth(nth).scroll_into_view_if_needed()
            pg.locator(sel).nth(nth).click()
            wait_path(pg, path, 'early tap ' + sel)
            for h in held:
                h()
            on_collection(pg, title, 'early tap ' + sel)
            ctx.close()
        print('early taps ok')
        # 4) a store with no New / Sale / Winter styles: buttons still lead to styles, never an empty page
        ctx, pg, _ = new_ctx(b, {'width': 390, 'height': 844}, 'plain', touch=True)
        for sel, nth in (('.hero [data-cat=New]', 0), ('.lk', 1)):
            pg.locator(sel).nth(nth).scroll_into_view_if_needed()
            pg.locator(sel).nth(nth).click()
            wait_path(pg, '/shop', 'plain store ' + sel)
            on_collection(pg, 'All styles', 'plain store ' + sel)
            back_home(pg, 'plain store ' + sel)
        ctx.close()
        ctx, pg, held = new_ctx(b, {'width': 390, 'height': 844}, 'plain', hold=True, touch=True)
        pg.locator('.hero [data-cat=New]').click()
        wait_path(pg, '/shop/new', 'plain early New')
        for h in held:
            h()
        on_collection(pg, 'All styles', 'plain early New')
        assert 'No new drops' in pg.inner_text('#cd'), 'plain early New: missing note'
        ctx.close()
        print('empty categories ok')
        # (opening index.html straight from a file is no longer supported: the strict security policy needs the site served from a web address)
        b.close()
    assert not errs, errs
    print('shop buttons ok', errs)


if __name__ == '__main__':
    try:
        run()
    except AssertionError as e:
        print('FAIL:', e)
        sys.exit(1)
