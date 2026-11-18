import json
from playwright.sync_api import sync_playwright
errs=[];posts=[]
def mk(i,demo): return {'id':i,'name':f'{"Sample" if demo else "Real"} {i}','category':'Hoodies','kind':'hood','price':900+i,'compare_at':None,'badge':None,'colors':['Black'],'image_url':None,'stock':None,'is_demo':demo,'created_at':f'2026-11-{10+(i%9):02d}T00:00:00Z'}
def run(real):
    prods=[mk(i,True) for i in range(1,13)]+[mk(100+i,False) for i in range(real)]
    with sync_playwright() as p:
        b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},service_workers='block');ctx.add_init_script("localStorage.setItem('cc_wel',String(Date.now()))")
        pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
        def route(r):
            u=r.request.url;m=r.request.method
            def ok(x): r.fulfill(status=200,content_type='application/json',body=json.dumps(x))
            if m=='POST' and 'contact_messages' in u: posts.append(json.loads(r.request.post_data));r.fulfill(status=201,body='')
            elif '/rest/v1/products' in u: ok(prods if 'offset=0' in u or 'offset' not in u else [])
            elif 'rpc/home_extras' in u: ok({'stats':{},'best':[],'latest':[]})
            elif 'store_settings' in u: ok([{'key':'stores','value':[{'name':'calyxculture Bemina','address':'Bemina, Srinagar','phone':'+91 8899190631'},{'name':'calyxculture Lal Chowk','address':'Lal Chowk, Srinagar'}]},{'key':'seller','value':{'support_email':'help@x.in','support_hours':'10am to 8pm'}}])
            elif '/rest/v1/faq' in u: ok([{'question':'Is COD available?','answer':'Yes.','keywords':'cod'}])
            elif 'supabase' in u: ok([])
            elif u.startswith('http://localhost'): r.continue_()
            else: r.abort()
        ctx.route('**/*',route);pg.goto('http://localhost:8077/');pg.wait_for_timeout(1000)
        demo=pg.evaluate("P.filter(p=>p.dm).length");n=pg.evaluate("P.length");print('real',real,'-> demo visible',demo,'total',n)
        if real==2:
            for path,txt in [('/about','Rooted in Srinagar'),('/stores','Lal Chowk'),('/contact','Send us a message'),('/faq','Is COD available')]:
                pg.evaluate(f"nav('{path}')");pg.wait_for_timeout(300);assert not pg.locator('#pg').is_hidden() and txt in pg.inner_text('#pgc'),path;assert pg.locator('main').is_hidden()
            pg.evaluate("nav('/contact')");pg.wait_for_timeout(300);pg.fill('#c-n','Asif');pg.fill('#c-p','9876500000');pg.fill('#c-m','Is the hoodie available in XL?');pg.click('#cff button[type=submit]');pg.wait_for_timeout(500);assert posts and posts[0]['phone']=='9876500000','contact post'
            pg.evaluate("nav('/nothing-here')");pg.wait_for_timeout(300);assert 'not found' in pg.inner_text('#pdpc').lower()
            pg.evaluate("nav('/product/abc')");pg.wait_for_timeout(300);assert 'not available' in pg.inner_text('#pdpc').lower()
            pg.evaluate("nav('/')");pg.click('[data-open=menu]');pg.wait_for_timeout(300);assert pg.locator('#menu a[href="/about"]').count()==1
        b.close();return demo
assert run(0)==12 and run(2)==10 and run(5)==7 and run(10)==0 and run(15)==0
print('pages+samples ok',errs)
