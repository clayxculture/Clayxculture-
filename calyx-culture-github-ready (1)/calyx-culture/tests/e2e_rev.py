import json
from playwright.sync_api import sync_playwright
errs=[];subs=[]
prods=[{'id':i,'name':f'Item {i}','category':['Hoodies','Denim'][i%2],'kind':'hood','price':900+i*100,'compare_at':None,'badge':None,'colors':['Black'],'image_url':f'calyx/p/x{i}','stock':None,'description':'Soft','is_demo':False,'created_at':'2026-11-10T00:00:00Z'} for i in range(1,7)]
extras={'stats':{'1':{'a':4.5,'c':2}},'best':[1,2,3,4],'latest':[{'name':'Asif K.','rating':5,'body':'Great hoodie, true to size and warm','image_url':'calyx/r/abc','product_id':1,'product':'Item 1'}]}
settings=[{'key':'hero_video','value':{'id':'calyx/p/clip','start':2,'len':6,'on':True}},{'key':'free_ship_threshold','value':1999}]
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},service_workers='block')
    ctx.add_init_script("localStorage.setItem('cc_wel',String(Date.now()));localStorage.setItem('cc_ord',JSON.stringify([{c:'CC-10482',p:'9876543210'}]))")
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    def route(r):
        u=r.request.url
        def ok(x): r.fulfill(status=200,content_type='application/json',body=json.dumps(x))
        if 'rpc/home_extras' in u: ok(extras)
        elif 'rpc/get_reviews' in u: ok({'avg':4.5,'count':2,'items':[{'name':'Asif K.','rating':5,'body':'Great hoodie, true to size','image_url':'calyx/r/abc','created_at':'2026-11-12'}]})
        elif 'rpc/review_check' in u: ok({'ok':True,'photo':True})
        elif 'rpc/submit_review' in u: subs.append(json.loads(r.request.post_data));ok({'ok':True})
        elif 'res.cloudinary.com' in u: r.fulfill(status=200,content_type='image/jpeg',body=open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'ph.jpg'),'rb').read()) if 'video' not in u else r.abort()
        elif '/rest/v1/products' in u: ok(prods)
        elif 'store_settings' in u: ok(settings)
        elif 'supabase' in u: ok([])
        elif u.startswith('http://localhost'): r.continue_()
        else: r.abort()
    ctx.route('**/*',route);pg.goto('http://localhost:8077/');pg.wait_for_timeout(1800)
    assert pg.locator('#best .card').count()==4,'best sellers';assert pg.locator('#revr .rvc').count()==1,'review strip'
    assert pg.locator('.hero>video').count()==1 and 'so_2,du_6' in pg.get_attribute('.hero>video','src'),'hero video'
    assert pg.locator('#grid .card .rtg').count()==1,'rating on card'
    assert 'Over ₹1,999' in pg.inner_text('.trust').replace('\xa0',' ') or '1,999' in pg.inner_text('.trust'),'trust fsv'
    pg.locator('#grid .card .open').first.click();pg.wait_for_timeout(500)
    assert 'Verified buyer' in pg.inner_text('#rvw'),'reviews in qv';pg.click('[data-wr]');pg.wait_for_timeout(300)
    assert pg.input_value('#rw-c')=='CC-10482','prefill'
    pg.click('#rwf button[type=submit]');assert 'rating' in pg.inner_text('#rwo').lower() or 'order' in pg.inner_text('#rwo').lower()
    pg.click('label[for=rt4]');pg.fill('#rw-b','Really nice fit and quality');pg.click('#rwf button[type=submit]');pg.wait_for_timeout(700)
    assert subs and subs[0]['rt']==4 and subs[0]['pid']==1 and subs[0]['c']=='CC-10482','submit';assert 'thank you' in pg.inner_text('#rw').lower()
    print('reviews ok',errs);b.close()
