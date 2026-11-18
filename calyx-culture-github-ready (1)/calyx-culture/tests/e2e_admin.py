import json,base64,time
from playwright.sync_api import sync_playwright
def b64(o): return base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip('=')
tok=b64({'alg':'none'})+'.'+b64({'email':'clayxculture@gmail.com'})+'.x'
calls=[];errs=[]
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},service_workers='block')
    ctx.add_init_script(f"sessionStorage.setItem('cc_at','{tok}');sessionStorage.setItem('cc_exp',String(Date.now()+3600000))")
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    def route(r):
        u=r.request.url;m=r.request.method;calls.append((m,u.split('supabase.co')[-1][:80]))
        def ok(b): r.fulfill(status=200,content_type='application/json',body=json.dumps(b))
        if 'rpc/is_admin' in u: ok(True)
        elif 'rpc/set_order_status' in u: r.fulfill(status=204,body='')
        elif '/rest/v1/orders' in u: ok([{'id':1,'code':'CC-10482','name':'Test User','phone':'9876543210','address':'House 1 Test Road','pincode':'190001','payment':'Cash on Delivery','items':[{'id':1,'name':'Item 1','color':'Black','size':'M','qty':1,'price':900}],'subtotal':900,'discount':0,'shipping':99,'total':999,'status':'placed','risk_score':25,'risk_flags':['new_phone','cod'],'courier':None,'tracking_id':None,'created_at':'2026-11-12T05:00:00Z'}])
        elif '/rest/v1/products' in u: ok([{'id':1,'name':'Item 1','category':'Hoodies','kind':'hood','price':900,'compare_at':None,'badge':None,'colors':['Black'],'image_url':None,'stock':2,'status':'published','is_demo':True,'description':None}])
        elif 'store_settings' in u and m=='GET': ok([{'key':'shipping_fee','value':99},{'key':'free_ship_threshold','value':1999},{'key':'announcement','value':'Hi'}])
        elif 'store_settings' in u: r.fulfill(status=201,body='')
        elif '/rest/v1/reviews' in u: ok([{'id':1,'product_id':1,'name':'Asif K.','rating':5,'body':'Great hoodie, true to size','image_url':None,'status':'pending','created_at':'2026-11-12T06:00:00Z','products':{'name':'Item 1'}}]) if m=='GET' else r.fulfill(status=204,body='')
        elif '/rest/v1/blocklist' in u: ok([])
        elif '/rest/v1/coupons' in u: ok([{'code':'CALYX10','percent':10,'min_cart':0,'uses':0,'max_uses':None,'active':True,'is_demo':True}])
        elif '/rest/v1/faq' in u: ok([{'id':1,'question':'Q','answer':'A','keywords':'k','active':True}])
        elif '/rest/v1/contact_messages' in u: ok([{'id':5,'name':'Asif','phone':'9876500000','message':'Is the hoodie in stock?','created_at':'2026-11-12T06:00:00Z'}]) if m=='GET' else r.fulfill(status=204,body='')
        elif u.startswith('http://localhost'): r.continue_()
        else: r.abort()
    ctx.route('**/*',route)
    pg.goto('http://localhost:8077/admin/');pg.wait_for_timeout(800)
    assert 'Setup guide' in pg.inner_text('main'),'guide'
    assert pg.locator('.kp').count()==1,'stats'
    pg.click('[data-o="1"]');pg.wait_for_timeout(300);pg.fill('#o-m','Delayed by snow');pg.select_option('#o-s','confirmed');pg.click('[data-so]');pg.wait_for_timeout(400)
    assert any('rpc/set_order_status' in c[1] for c in calls),'status rpc'
    pg.click('.tabs [data-v=products]');pg.wait_for_timeout(300);assert 'Only 2 left' in pg.inner_text('main')
    pg.click('[data-p="new"]');pg.wait_for_timeout(200);assert pg.locator('#p-c[list]').count()==1 and pg.locator('#p-f').count()==1,'product form'
    pg.keyboard.press('Escape')
    pg.click('.tabs [data-v=offers]');pg.wait_for_timeout(400);t=pg.inner_text('main');assert 'Asif' in t and 'Instagram reels' in t and 'Welcome pop-up' in t and 'Customer reviews' in t and 'Hero video' in t,'offers'
    pg.click('[data-rl="new"]');pg.fill('#r-u','https://example.com/x');pg.click('[data-rs2]');pg.wait_for_timeout(200);assert 'Instagram' in pg.inner_text('#toast'),'reel validation'
    pg.keyboard.press('Escape')
    pg.click('.tabs [data-v=settings]');pg.wait_for_timeout(400)
    pg.click('[data-st="new"]');pg.fill('#s-n','calyxculture Lal Chowk');pg.fill('#s-ad','Lal Chowk, Srinagar, J&K');pg.click('[data-ss2]');pg.wait_for_timeout(500)
    assert any(c[0]=='POST' and 'store_settings' in c[1] for c in calls),'store saved'
    pg.screenshot(path='out/admin390.png')
    print('admin ok','errors',errs)
    b.close()
