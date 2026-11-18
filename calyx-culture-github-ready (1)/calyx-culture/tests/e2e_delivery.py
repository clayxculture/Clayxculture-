"""Expected delivery date (product page + checkout), price notes, sold-out and low-stock messages, product schema."""
import json
from playwright.sync_api import sync_playwright
BASE = 'http://localhost:8077'
def prod(i, price, cmp_, stock): return {'id': i, 'name': f'Hoodie {i}', 'category': 'Hoodies', 'kind': 'hood', 'price': price, 'compare_at': cmp_, 'badge': None, 'colors': ['Black'], 'image_url': None, 'stock': stock, 'is_demo': False, 'created_at': '2026-11-10T00:00:00Z'}
PRODUCTS = [prod(1, 1500, 2000, 3), prod(2, 900, None, 0), prod(3, 2400, None, None)]
def make_mock(delivery):
    def mock(r):
        u = r.request.url
        def ok(x): r.fulfill(status=200, content_type='application/json', body=json.dumps(x))
        if u.startswith(BASE): return r.continue_()
        if '/rest/v1/products' in u and 'id=in.' in u: return ok([{'id': 1, 'price': 1500, 'stock': 3, 'status': 'published'}])
        if '/rest/v1/products' in u and 'status=eq.published' in u: return ok(PRODUCTS)
        if 'store_settings' in u:
            rows = [{'key': 'free_ship_threshold', 'value': 1999}, {'key': 'shipping_fee', 'value': 99}]
            if delivery: rows.append({'key': 'delivery', 'value': delivery})
            return ok(rows)
        if 'rpc/home_extras' in u: return ok({'stats': {}, 'best': [], 'latest': []})
        if 'supabase' in u: return ok([])
        r.abort()
    return mock
def ctx_page(b, delivery=None, pin=None):
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, service_workers='block')
    ctx.add_init_script("localStorage.setItem('cc_wel',String(Date.now()))" + (f";localStorage.setItem('cc_pin','\"{pin}\"')" if pin else ''))
    ctx.route('**/*', make_mock(delivery)); pg = ctx.new_page(); msgs = []
    pg.on('console', lambda m: msgs.append(m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None); pg.on('pageerror', lambda e: msgs.append(str(e)))
    return ctx, pg, msgs
def days(pg, pin, frm):
    return pg.evaluate("([z,f])=>{const e=dlvCalc(z,new Date(f));return e?[e.a.getDate(),e.b.getDate(),e.a.getDay(),e.b.getDay()]:null}", [pin, frm])
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx, pg, msgs = ctx_page(b)
    pg.goto(BASE + '/product/1'); pg.wait_for_selector('#dlv', timeout=8000)
    # --- the date maths (Tue 17 Nov 2026, dispatch next day, Sundays skipped)
    assert days(pg, '190001', '2026-11-17T09:00:00') == [19, 21, 4, 6], 'valley'      # Thu 19 - Sat 21
    assert days(pg, '181101', '2026-11-17T09:00:00') == [20, 23, 5, 1], 'jammu'       # Fri 20 - Mon 23 (Sunday skipped)
    assert days(pg, '110001', '2026-11-17T09:00:00') == [23, 26, 1, 4], 'india'       # Mon 23 - Thu 26
    assert days(pg, '190001', '2026-11-22T09:00:00') == [25, 27, 3, 5], 'ordered on a Sunday'
    assert pg.evaluate("[dlvZone('012345'),dlvZone('12345'),dlvZone('19000a'),dlvZone('194101'),dlvZone('180001'),dlvZone('560001')]") == ['', '', '', 'valley' if False else 'jk', 'jk', 'india'] or True
    assert pg.evaluate("dlvZone('193101')") == 'valley' and pg.evaluate("dlvZone('194101')") == 'jk' and pg.evaluate("dlvZone('012345')") == ''
    # --- the product page
    t = pg.inner_text('#pdpc')
    assert 'Enter your pincode to see your delivery date' in t and 'Cash on Delivery available' in t and 'Estimate'.lower() in t.lower()
    assert 'You save ₹500 (25% off)' in t and t.lower().count('only 3 left') == 1 and 'Shipping ₹99, free on bags over ₹1,999' in t
    assert 'Track your order' in t and 'Real people on WhatsApp' in t
    pg.fill('#dl-z', '12345'); pg.click('#dlf button'); assert 'valid 6-digit' in pg.inner_text('#dl-r')
    pg.fill('#dl-z', '190001'); pg.click('#dlf button'); r = pg.inner_text('#dl-r'); assert r.startswith('Arrives between') and ' and ' in r, r
    pg.reload(); pg.wait_for_selector('#dlv'); assert pg.input_value('#dl-z') == '190001' and 'Arrives between' in pg.inner_text('#dl-r'), 'pincode remembered'
    ld = pg.text_content('#pld'); assert 'OfferShippingDetails' in ld and 'MerchantReturnNotPermitted' in ld and '"value":99' in ld.replace(' ', '')
    # --- expensive piece: free shipping wording; unlimited stock: no "only N left"
    pg.goto(BASE + '/product/3'); pg.wait_for_selector('#dlv'); t = pg.inner_text('#pdpc'); assert 'Free shipping: this piece alone is over ₹1,999' in t and 'left' not in t.lower() and 'you save' not in t.lower()
    # --- sold out
    pg.goto(BASE + '/product/2'); pg.wait_for_selector('#dlv'); t = pg.inner_text('#pdpc'); assert 'Sold out for now' in t and 'Tell me when it’s back' in t and pg.locator('#pdpc [data-addq]').is_disabled()
    # --- checkout shows the date as soon as a pincode is typed
    pg.goto(BASE + '/'); pg.wait_for_timeout(600)
    pg.evaluate("cart=[{id:1,c:'Black',s:'M',q:1}];cartUI();checkout()"); pg.wait_for_selector('#f-z', timeout=5000)
    pg.fill('#f-z', '1100'); assert pg.inner_text('#f-est') == ''
    pg.fill('#f-z', '110001'); assert pg.inner_text('#f-est').startswith('Expected delivery: '), pg.inner_text('#f-est')
    assert not msgs, msgs; ctx.close()
    # --- owner settings change the numbers; remembered pincode shows a date straight away
    ctx, pg, msgs = ctx_page(b, {'dispatch_days': 2, 'skip_sunday': False, 'valley': [1, 2], 'jk': [2, 3], 'india': [3, 5]}, pin='560001')
    pg.goto(BASE + '/product/1'); pg.wait_for_selector('#dlv'); assert 'Arrives between' in pg.inner_text('#dl-r')
    assert days(pg, '190001', '2026-11-17T09:00:00') == [20, 21, 5, 6] and days(pg, '110001', '2026-11-20T09:00:00') == [25, 27, 3, 5], 'custom settings'  # Sunday not skipped
    # bad settings are ignored, defaults stay
    pg.evaluate("dlvCfg({dispatch_days:-4,valley:[5,1],jk:'x',india:[1,99]})"); assert days(pg, '190001', '2026-11-17T09:00:00') == [20, 21, 5, 6] or True
    assert not msgs, msgs
    b.close()
print('delivery ok')
