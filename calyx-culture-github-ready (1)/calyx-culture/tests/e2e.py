import json,sys
from playwright.sync_api import sync_playwright
errs=[]
def run(w,h,shots=False):
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if w<500 else 1,has_touch=w<500,service_workers='block')
    ctx.add_init_script("if(!localStorage.getItem('test_popup'))localStorage.setItem('cc_wel',String(Date.now()))")
    pg=ctx.new_page()
    pg.on('console',lambda m:errs.append((w,'console',m.text)) if m.type=='error' else None)
    pg.on('pageerror',lambda e:errs.append((w,'pageerror',str(e))))
    def route(r):
      u=r.request.url
      if 'rpc/place_order' in u: r.fulfill(status=200,content_type='application/json',body=json.dumps({'code':'CC-10482','total':1798,'subtotal':1799,'discount':0,'shipping':99}))
      elif 'rpc/track_order' in u: r.fulfill(status=200,content_type='application/json',body=json.dumps({'code':'CC-10482','status':'shipped','courier':'DTDC','tracking_id':'D123','events':[{'status':'placed','at':'2026-11-11T05:00:00Z'},{'status':'shipped','at':'2026-11-11T09:00:00Z'}]}))
      elif 'rpc/check_coupon' in u: r.fulfill(status=200,content_type='application/json',body='10')
      elif 'store_settings' in u: r.fulfill(status=200,content_type='application/json',body='[{"key":"announcement","value":"Test announcement"},{"key":"free_ship_threshold","value":1999},{"key":"shipping_fee","value":99}]')
      elif '/rest/v1/products' in u: r.fulfill(status=200,content_type='application/json',body=json.dumps([{'id':i,'name':f'Item {i}','category':['T-Shirts','Hoodies','Denim'][i%3],'kind':['tee','hood','jeans'][i%3],'price':900+i*100,'compare_at':(1500 if i==2 else None),'badge':('New' if i%4==0 else None),'colors':['Black','Olive'],'image_url':f'calyx/p/x{i}','stock':(0 if i==3 else None)} for i in range(1,9)]))
      elif 'supabase' in u: r.fulfill(status=200,body='[]',content_type='application/json')
      elif u.startswith('http://localhost'): r.continue_()
      else: r.abort()
    ctx.route('**/*',route)
    pg.goto('http://localhost:8077/',wait_until='load');pg.wait_for_timeout(600)
    ov=pg.evaluate('document.documentElement.scrollWidth-innerWidth');print(w,'overflow px:',ov)
    assert pg.locator('#grid .card').count()==8,'cards'
    assert 'Test announcement' in pg.inner_text('.bar'),'announce'
    if shots: pg.screenshot(path=f'out/s{w}_top.png')
    pg.click('button[data-open=fd]');pg.wait_for_timeout(300);assert pg.locator('#fd .lk').count()>=1,'finder';pg.click('#fd [data-fd="c|Hoodies"]');pg.wait_for_timeout(100);assert pg.locator('#fd .lk').count()>=1;pg.keyboard.press('Escape')
    # quick view + add
    pg.locator('#grid .card .add').first.click();pg.wait_for_timeout(300)
    pg.click('#qv [data-addq]');assert 'Pick a size' in pg.inner_text('#ze')
    pg.click('#qv .sz[data-z=M]');pg.click('#qv [data-addq]');pg.wait_for_timeout(300)
    assert pg.inner_text('#cc')=='1','cart count'
    # sold out card
    assert pg.locator('#grid .card:has-text("Sold out")').count()==1,'soldout'
    # wishlist
    pg.locator('#grid .hrt').nth(1).click();assert pg.inner_text('#wc')=='1'
    # category pages
    pg.evaluate('scrollTo(0,0)');pg.wait_for_timeout(400)
    pg.click('#chips a[href="/shop/sale"]');pg.wait_for_timeout(300)
    assert pg.url.endswith('/shop/sale') and not pg.locator('#col').is_hidden(),'col view'
    assert pg.locator('#cg .card').count()==1,'sale count';assert 'sale' in pg.inner_text('#ct').lower()
    pg.go_back();pg.wait_for_timeout(300);assert pg.locator('#col').is_hidden(),'back to home'
    pg.evaluate('scrollTo(0,0)');pg.wait_for_timeout(400)
    pg.click('#tiles a[href="/shop/hoodies"]');pg.wait_for_timeout(300);assert pg.locator('#cg .card').count()>=1,'hoodies';assert 'Hoodies' in pg.title(),'title'
    pg.select_option('#sort2','h');pg.wait_for_timeout(200)
    pg.click('#cchips a[href="/shop"]');pg.wait_for_timeout(200);assert pg.locator('#cg .card').count()==8
    pg.evaluate("nav('/shop/nope')");pg.wait_for_timeout(200);assert 'not found' in pg.inner_text('#ct').lower()
    pg.evaluate("nav('/')");pg.wait_for_timeout(300)
    # search
    pg.evaluate('scrollTo(0,0)');pg.wait_for_timeout(700);pg.click('[data-open=srch]');pg.fill('#si','item 5');pg.wait_for_timeout(200);assert pg.locator('#sres .ci').count()>=1,'search';pg.keyboard.press('Enter');pg.wait_for_timeout(300);assert '/search' in pg.url and pg.locator('#cg .card').count()==1,'search page';pg.evaluate("nav('/')");pg.wait_for_timeout(300)
    # cart + coupon + checkout
    pg.evaluate('scrollTo(0,0)');pg.wait_for_timeout(700);pg.click('[data-open=cart]');pg.wait_for_timeout(300)
    if shots: pg.screenshot(path=f'out/s{w}_cart.png')
    pg.fill('#cpi','SAVE');pg.click('#cpf button');pg.wait_for_timeout(300);assert 'applied' in pg.inner_text('#cpe').lower(),'coupon'
    pg.click('[data-co]');pg.wait_for_timeout(500)
    pg.click('#cof button[type=submit]');assert pg.locator('[data-e=n]').inner_text()!='','validation'
    pg.fill('#f-n','Test User');pg.fill('#f-p','9876543210');pg.fill('#f-a','House 1, Test Road, Srinagar');pg.fill('#f-z','190001');pg.click('#cof button[type=submit]');assert pg.locator('[data-e=agree]').inner_text()!='','consent required';pg.check('#f-g');pg.wait_for_timeout(3200)
    pg.click('#cof button[type=submit]');pg.wait_for_timeout(500)
    assert 'CC-10482' in pg.inner_text('#co'),'order confirm'
    assert pg.locator('#co a[href*="wa.me"]').count()==1
    if shots: pg.screenshot(path=f'out/s{w}_order.png')
    pg.click('#co [data-x]');assert pg.inner_text('#cc')=='','cart cleared'
    # track
    pg.evaluate('scrollTo(0,0)');pg.wait_for_timeout(500);pg.click('[data-open=menu]');pg.click('#menu [data-trk]');pg.wait_for_timeout(200)
    assert pg.input_value('#t-c')=='CC-10482','track prefill'
    pg.click('#trf button[type=submit]');pg.wait_for_timeout(400);assert 'Shipped' in pg.inner_text('#tro'),'track'
    pg.keyboard.press('Escape')
    pg.click('.bn [data-chat]') if w<900 else pg.click('.chatfab');pg.wait_for_timeout(300)
    pg.click('#bt [data-cq="Where is my order?"]');pg.wait_for_timeout(800);assert 'shipped' in pg.inner_text('#cm').lower(),'chat order'
    pg.fill('#chi','how long is delivery');pg.press('#chi','Enter');pg.wait_for_timeout(300);assert 'WhatsApp' in pg.inner_text('#cm') or 'delivery' in pg.inner_text('#cm').lower()
    pg.keyboard.press('Escape')
    if w<900: assert pg.locator('.bn').is_visible(),'bottom nav'
    pg.evaluate("nav('/product/1-item-1')");pg.wait_for_timeout(400);assert not pg.locator('#pdp').is_hidden() and pg.locator('#pdpc .sz').count()==4,'product page';pg.evaluate("nav('/')");pg.wait_for_timeout(300)
    # recently viewed
    assert not pg.locator('#rvs').is_hidden(),'recent'
    # scroll nav hide/show
    pg.evaluate('scrollTo(0,1500)');pg.wait_for_timeout(500);pg.evaluate('scrollTo(0,1200)');pg.wait_for_timeout(400)
    if shots: pg.screenshot(path=f'out/s{w}_mid.png')
    if w==390:
      pg.evaluate("localStorage.setItem('test_popup','1');localStorage.removeItem('cc_wel')");pg.reload();pg.wait_for_timeout(6800);assert pg.locator('#wp[open]').count()==1,'welcome popup';pg.screenshot(path='out/s390_popup.png')
    print(w,'ok');b.close()
for w,h in [(360,740),(390,844),(768,1024),(1440,900)]:
  try: run(w,h,shots=(w in(390,1440)))
  except Exception as e: print(w,'FAIL',str(e)[:300])
print('errors:',errs)
