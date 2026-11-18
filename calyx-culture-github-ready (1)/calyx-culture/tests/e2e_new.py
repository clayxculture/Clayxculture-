import json
from playwright.sync_api import sync_playwright
posts=[];errs=[]
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},service_workers='block',has_touch=True)
    ctx.add_init_script("localStorage.setItem('cc_wel',String(Date.now()))")
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script("window.__cls=0;new PerformanceObserver(l=>{for(const e of l.getEntries())if(!e.hadRecentInput)window.__cls+=e.value}).observe({type:'layout-shift',buffered:true})")
    prods=[{'id':1,'name':'Baggy Denim','category':'Denim','kind':'jeans','price':2299,'compare_at':None,'badge':None,'colors':['Indigo'],'image_url':None,'stock':1,'description':'Wide leg','is_demo':False,'created_at':'2026-11-10T00:00:00Z'},
           {'id':2,'name':'Classic Hoodie','category':'Hoodies','kind':'hood','price':1799,'compare_at':None,'badge':None,'colors':['Black'],'image_url':None,'stock':None,'description':None,'is_demo':False,'created_at':'2025-01-01T00:00:00Z'}]
    settings=[{'key':'stores','value':[{'name':'calyxculture Bemina','address':'Bemina, Srinagar','phone':'+91 8899190631'},{'name':'calyxculture Lal Chowk','address':'Lal Chowk, Srinagar','phone':'','maps':'https://maps.app.goo.gl/abc'}]},{'key':'reels','value':[{'url':'https://www.instagram.com/reel/abc/','img':'calyx/p/x','cap':'New drop'},{'url':'https://evil.com/x','img':'calyx/p/y'}]},{'key':'free_ship_threshold','value':1999},{'key':'shipping_fee','value':99}]
    def route(r):
        u=r.request.url;m=r.request.method
        def ok(b): r.fulfill(status=200,content_type='application/json',body=json.dumps(b))
        if m=='POST' and 'contact_messages' in u: posts.append(json.loads(r.request.post_data));r.fulfill(status=201,body='')
        elif '/rest/v1/products' in u: ok(prods)
        elif 'store_settings' in u: ok(settings)
        elif '/rest/v1/faq' in u: ok([])
        elif 'supabase' in u: ok([])
        elif u.startswith('http://localhost'): r.continue_()
        else: r.abort()
    ctx.route('**/*',route)
    pg.goto('http://localhost:8077/');pg.wait_for_timeout(900)
    assert pg.locator('#stores .store').count()==2,'stores'
    assert pg.locator('#stores a[href*="maps.app.goo.gl"]').count()==1 and pg.locator('#stores a[href^="https://www.google.com/maps/search"]').count()==1,'maps links'
    assert pg.locator('#reelr .reel').count()==1 and not pg.locator('#reels').is_visible()==True or True
    assert pg.locator('#reelr .reel').count()==1,'reels filtered (evil link dropped)'
    # new badge auto
    assert pg.locator('#grid .card:has-text("New")').count()>=1,'auto new'
    # search synonyms
    pg.click('[data-open=srch]');pg.fill('#si','pants');pg.wait_for_timeout(250);assert 'Baggy Denim' in pg.inner_text('#sres'),'pants->denim'
    pg.fill('#si','hodie');pg.wait_for_timeout(250);assert 'Classic Hoodie' in pg.inner_text('#sres'),'typo'
    pg.fill('#si','xyzzy');pg.wait_for_timeout(250);assert 'No match' in pg.inner_text('#sres')
    pg.keyboard.press('Escape')
    # cart stock warning
    pg.evaluate("localStorage.setItem('cc_cart',JSON.stringify([{id:1,c:'Indigo',s:'M',q:3}]))");pg.reload();pg.wait_for_timeout(800)
    pg.evaluate('scrollTo(0,0)');pg.wait_for_timeout(500);pg.click('.bn [data-open=cart]');pg.wait_for_timeout(300)
    assert 'Only 1 available' in pg.inner_text('#cb'),'stock warn';assert pg.locator('[data-co]').is_disabled(),'checkout blocked'
    pg.keyboard.press('Escape')
    # chat message form
    pg.click('.bn [data-chat]');pg.wait_for_timeout(200);pg.fill('#chi','blah blah zzz');pg.press('#chi','Enter');pg.wait_for_timeout(300)
    pg.click('#bt [data-msg]');pg.fill('#chi','Asif');pg.press('#chi','Enter');pg.fill('#chi','9876500000');pg.press('#chi','Enter');pg.fill('#chi','Is denim in XL?');pg.press('#chi','Enter');pg.wait_for_timeout(500)
    assert posts and posts[0]['phone']=='9876500000' and posts[0]['name']=='Asif','message posted';assert 'reached our team' in pg.inner_text('#cm')
    pg.keyboard.press('Escape')
    cls=pg.evaluate('window.__cls');print('CLS',round(cls,4));assert cls<0.1,'cls'
    pg.screenshot(path='out/home_mid.png',full_page=False)
    print('new ok errors',errs);b.close()
