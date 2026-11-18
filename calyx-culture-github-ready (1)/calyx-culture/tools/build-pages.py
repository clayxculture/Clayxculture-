#!/usr/bin/env python3
"""Writes site/about.html, stores.html, contact.html and faq.html.

The four pages share one header, footer and icon sprite, so they are generated from this one file.
Run from the repo root:  python3 tools/build-pages.py && python3 tools/stamp.py
The generated .html files are what gets deployed; nothing here runs on the server.
"""
import glob, html, os, re, urllib.parse

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
DOMAIN = 'https://clayxculture.in'
WA = 'https://wa.me/918899190631?text='
PHONE_TXT, PHONE_TEL = '+91 88991 90631', '+918899190631'
IG = 'https://www.instagram.com/calyxculture_/'
ADDR = 'Housing Colony, Jamia Market, Near Jamia Ahli-Hadees, Bemina, Srinagar, Jammu & Kashmir, India'
FONTS = 'https://fonts.googleapis.com/css2?family=Archivo:ital,wdth,wght@1,125,900&family=Inter:wght@400;600;700&display=swap'
OG = '/img/og.5af23071.jpg'
e = html.escape


def img(base, w):
    m = glob.glob(os.path.join(ROOT, 'img', f'{base}-{w}.*.webp'))
    assert m, f'missing image {base}-{w}'
    return '/img/' + os.path.basename(m[0])


def pic(base, alt, sizes, lazy=True, ws=(240, 400, 736), dims=(736, 981), extra=''):
    ss = ', '.join(f'{img(base, w)} {w}w' for w in ws)
    return (f'<img src="{img(base, ws[-1])}" srcset="{ss}" sizes="{sizes}" alt="{e(alt)}" width="{dims[0]}" height="{dims[1]}"'
            f'{" loading=lazy" if lazy else ""} decoding="async"{extra}>')


def wa(text):
    return WA + urllib.parse.quote(text, safe='')


SPRITE = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'
          '<symbol id="i-menu" viewBox="0 0 24 24"><path d="M4 8h16M4 16h10"/></symbol>'
          '<symbol id="i-x" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></symbol>'
          '<symbol id="i-chat" viewBox="0 0 24 24"><path d="M5 5h14v10H10l-5 4z"/></symbol>'
          '<symbol id="i-cod" viewBox="0 0 24 24"><rect x="3" y="6" width="18" height="13" rx="3"/><path d="M16 12h5v3h-5a1.5 1.5 0 0 1 0-3z"/></symbol>'
          '<symbol id="i-ship" viewBox="0 0 24 24"><path d="M3 7h11v9H3zM14 10h4l3 3v3h-7z"/><circle cx="7" cy="18" r="1.6"/><circle cx="17" cy="18" r="1.6"/></symbol>'
          '<symbol id="i-pin" viewBox="0 0 24 24"><path d="M12 21s6-5.5 6-10a6 6 0 0 0-12 0c0 4.5 6 10 6 10z"/><circle cx="12" cy="11" r="2.2"/></symbol>'
          '<symbol id="i-wa" viewBox="0 0 24 24"><path d="M4 20l1.3-4A8 8 0 1 1 8 18.7z"/><path d="M9 9.5c.5 2.5 2.5 4.5 5 5l1.2-1.3-1.8-.9-.8.7c-.9-.4-1.6-1.1-2-2l.7-.8-.9-1.8z"/></symbol>'
          '<symbol id="i-ig" viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="5"/><circle cx="12" cy="12" r="3.8"/><path d="M17 7h.01"/></symbol>'
          '<symbol id="i-ph" viewBox="0 0 24 24"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a1 1 0 0 1-1 1A15 15 0 0 1 4 5a1 1 0 0 1 1-1z"/></symbol>'
          '</defs></svg>')
STAR = '<svg viewBox="0 0 20 36" aria-hidden="true"><path d="M10 0 12 15 20 18 12 21 10 36 8 21 0 18 8 15z"/></svg>'


def ic(n):
    return f'<svg class="i" aria-hidden="true"><use href="#i-{n}"/></svg>'


NAV = [('/shop', 'Shop'), ('/about', 'About'), ('/stores', 'Our store'), ('/contact', 'Contact'), ('/faq', 'FAQ')]


def header(cur):
    links = lambda: ''.join(f'<a href="{h}"{" aria-current=page" if h == cur else ""}>{t}</a>' for h, t in NAV)
    return (f'<header class="top"><div class="in"><a class="wm" href="/" aria-label="calyxculture home">calyxculture{STAR}</a>'
            f'<nav class="nv" aria-label="Main">{links()}</nav><span class="sp"></span>'
            f'<a class="btn p s" href="/shop">Shop now</a>'
            f'<details class="mn" id="mn"><summary aria-label="Menu"><svg class="i i-o" aria-hidden="true"><use href="#i-menu"/></svg>'
            f'<svg class="i i-c" aria-hidden="true"><use href="#i-x"/></svg></summary><nav aria-label="Menu">{links()}'
            f'<a href="/policies.html">Policies</a></nav></details></div></header>')


def footer():
    return (f'<footer class="ft dk"><div class="in"><div><a class="wm" href="/" aria-label="calyxculture home">calyxculture{STAR}</a>'
            f'<p style="margin-top:14px">Streetwear from Srinagar, Kashmir. {e(ADDR)}.</p></div>'
            f'<nav aria-label="Footer"><a href="/shop">Shop</a><a href="/about">About</a><a href="/stores">Our store</a><a href="/contact">Contact</a>'
            f'<a href="/faq">FAQ</a><a href="/policies.html">Policies</a><a href="/policies.html#privacy">Privacy</a>'
            f'<a href="{IG}" rel="noopener" target="_blank">Instagram</a></nav>'
            f'<p class="cr">&copy; 2026 calyxculture. Cash on Delivery available. Prices in Indian rupees.</p></div></footer>'
            f'<div class="dock"><a class="btn p" href="/shop">Shop now</a>'
            f'<a class="btn o" href="{wa("Hi calyxculture")}" rel="noopener" target="_blank">{ic("wa")}WhatsApp</a></div>')


SM = {'margin-top:8px': 'm8', 'margin-top:10px': 'm10', 'margin-top:14px': 'm14', 'margin-top:16px': 'm16', 'margin-top:18px': 'm18',
      'margin-top:20px': 'm20', 'margin-top:22px': 'm22', 'font-size:14px': 'f14', 'padding-top:8px': 't8', 'padding-top:20px': 't20',
      'max-width:820px': 'w820', 'position:absolute': 'spr'}


def nostyle(h):
    def sub(m):
        tag, pre, st, post = m.group(1), m.group(2), m.group(3), m.group(4)
        cls = ' '.join(SM[d.strip()] for d in st.split(';') if d.strip())
        both = pre + post
        if 'class="' in both:
            pre = pre.replace('class="', f'class="{cls} ', 1) if 'class="' in pre else pre
            post = post.replace('class="', f'class="{cls} ', 1) if 'class="' in post and 'class="' not in pre else post
            return f'<{tag}{pre}{post}>'
        return f'<{tag}{pre} class="{cls}"{post}>'
    return re.sub(r'<(\w+)([^>]*?)\sstyle="([^"]*)"([^>]*)>', sub, h)


def page(path, title, desc, cur, body, preload='', ld='', og=OG):
    url = DOMAIN + path
    crumbs = ('{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
              f'{{"@type":"ListItem","position":1,"name":"Home","item":"{DOMAIN}/"}},'
              f'{{"@type":"ListItem","position":2,"name":"{e(title.split(" | ")[0].split(":")[0])}","item":"{url}"}}]}}')
    out = f'''<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#ffffff">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="calyxculture"><meta property="og:locale" content="en_IN">
<meta property="og:url" content="{url}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{DOMAIN}{og}"><meta property="og:image:width" content="736"><meta property="og:image:height" content="736"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="/icon-192.png"><link rel="apple-touch-icon" href="/icon-192.png"><link rel="manifest" href="/manifest.webmanifest">
{preload}<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}" media="print" data-fonts><noscript><link rel="stylesheet" href="{FONTS}"></noscript>
<script src="/assets/boot.js?v=0" async></script>
<link rel="stylesheet" href="/assets/pages.css?v=0">
<script type="application/ld+json">{crumbs}</script>
{ld}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{SPRITE}
{header(cur)}
<main id="main" tabindex="-1">
{body}
</main>
{footer()}
<script src="/assets/pages.js?v=0" defer></script>
</body>
</html>
'''
    return nostyle(out)


def new_arrivals(heading='New arrivals'):
    return (f'<section class="sec" id="pop" hidden aria-labelledby="pop-h"><h2 class="h" id="pop-h">{heading}</h2>'
            f'<div class="pg" id="pop-g"></div><p class="more"><a class="btn o" href="/shop">See the full collection</a></p></section>')


def cta(h='Wear the culture.', p=None):
    p = p or 'Pay when it arrives with Cash on Delivery. Free shipping over <span data-fs>₹1,999</span>.'
    return (f'<section class="cta dk" aria-label="Order"><div class="in"><h2 class="h">{h}</h2><p>{p}</p>'
            f'<div class="row"><a class="btn w" href="/shop">Shop the collection</a>'
            f'<a class="btn g" href="{wa("Hi calyxculture")}" rel="noopener" target="_blank">{ic("wa")}Order on WhatsApp</a></div></div></section>')


def trust():
    return ('<ul class="trust">'
            f'<li>{ic("cod")}<b>Cash on Delivery</b><small>Pay when it arrives</small></li>'
            f'<li>{ic("ship")}<b>Free shipping</b><small>Over <span data-fs>₹1,999</span></small></li>'
            f'<li>{ic("pin")}<b>Order tracking</b><small>With your order ID</small></li>'
            f'<li>{ic("chat")}<b>Real support</b><small>Chat or WhatsApp</small></li></ul>')


# ---------------------------------------------------------------- ABOUT
hero_pre = ('<link rel="preload" as="image" type="image/webp" href="' + img('hero', 736) + '" imagesrcset="' + img('hero', 480) + ' 480w, ' + img('hero', 736) + ' 736w" imagesizes="(min-width:900px) 46vw, 100vw">\n')
about = f'''<section class="hero dk" aria-labelledby="h1"><figure><img src="{img('hero', 736)}" srcset="{img('hero', 480)} 480w, {img('hero', 736)} 736w" sizes="(min-width:900px) 46vw, 100vw" alt="Black shearling jacket and sunglasses on a snowy meadow in Gulmarg" width="736" height="981" fetchpriority="high" decoding="async"></figure>
<div class="tx"><h1 id="h1">Rooted in Srinagar. Made to move with you.</h1>
<p class="lead">Streetwear from the valley: oversized fits, baggy denim, heavy hoodies and winter layers, cut for comfort and made to be seen.</p>
<div class="row"><a class="btn p" href="/shop">Shop the collection</a><a class="btn g" href="{wa("Hi calyxculture")}" rel="noopener" target="_blank">{ic("wa")}Order on WhatsApp</a></div>
<p class="proof">Cash on Delivery. Free shipping over <span data-fs>₹1,999</span>.</p></div></section>
<p class="intro">Streetwear from the valley: oversized fits, baggy denim, heavy hoodies and winter layers, cut for comfort and made to be seen.</p>

<section class="sec" aria-labelledby="mk"><h2 class="h" id="mk">What we make</h2>
<div class="tiles">
<a class="tile" href="/shop/denim">{pic('denim', 'Baggy blue jeans, white sneakers and an olive jacket on a hillside wall', '(min-width:640px) 30vw, 76vw')}<b>Baggy denim<small>Shop denim</small></b></a>
<a class="tile" href="/shop/winter">{pic('knit', 'Dark oversized sweatshirt against a window', '(min-width:640px) 30vw, 76vw')}<b>Winter layers<small>Shop winter</small></b></a>
<a class="tile" href="/shop">{pic('linen', 'White linen shirt and trousers on a misty green hill', '(min-width:640px) 30vw, 76vw')}<b>Light linen<small>See the collection</small></b></a>
</div></section>

<div class="band"><section class="sec split" aria-labelledby="st">
<figure>{pic('back', 'Man in a white shirt standing by a carved wooden pillar with green hills behind', '(min-width:900px) 45vw, 100vw')}</figure>
<div><h2 class="h" id="st">Clothes that feel good and look sharp</h2>
<p style="margin-top:16px">calyxculture is a streetwear label from Srinagar, Kashmir. We make oversized tees, baggy denim, hoodies and winter layers with one idea: clothes that feel good, look sharp and are easy to wear every day.</p>
<p class="mut">We are building a fashion and streetwear brand that stands for individuality, comfort and quality, and keeps great style within everyone’s reach.</p>
<div class="row" style="margin-top:22px"><a class="btn p" href="/shop">Shop the collection</a><a class="btn o" href="/stores">Visit our store</a></div></div>
</section></div>

<section class="sec" aria-labelledby="tr"><h2 class="h" id="tr">Order with confidence</h2>{trust()}
<p class="mut" style="margin-top:16px;font-size:14px">We exchange verified defects, wrong items and transit damage reported within 3 days of delivery. Read the full <a href="/policies.html#returns">exchange policy</a> and <a href="/policies.html#shipping">shipping policy</a>.</p></section>

{new_arrivals()}
{cta()}'''

# ---------------------------------------------------------------- STORES
store_card = (f'<article class="sc"><h2>calyxculture, Bemina</h2><address>{e(ADDR)}</address>'
              f'<p class="ph2">Phone: <a href="tel:{PHONE_TEL}">{PHONE_TXT}</a></p>'
              f'<div class="row"><a class="btn p" href="https://www.google.com/maps/search/?api=1&amp;query=calyxculture%20Housing%20Colony%20Jamia%20Market%20Bemina%20Srinagar" rel="noopener" target="_blank">{ic("pin")}Get directions</a>'
              f'<a class="btn o" href="tel:{PHONE_TEL}">{ic("ph")}Call the store</a>'
              f'<a class="btn o" href="{wa("Hi calyxculture, I would like to visit the store. What are your timings today?")}" rel="noopener" target="_blank">{ic("wa")}Check timings</a></div></article>')
stores = f'''<div class="ph1"><h1 id="st-h">Our store</h1><p class="lead">Come see the range in person, or order from home and we deliver.</p></div>
<section class="sec" style="padding-top:8px" aria-labelledby="st-h"><div class="st"><div id="stores-list">{store_card}</div>
<div class="sph">{pic('navy', 'Man in a navy sweater leaning on an orange railing with mountains behind', '(min-width:900px) 40vw, 100vw', dims=(736, 1308))}</div></div>
<p class="mut" style="margin-top:14px" data-hours>Message us on WhatsApp before you visit to check today’s timings.</p></section>

<section class="sec" aria-labelledby="away"><h2 class="h" id="away">Can’t make it to Bemina?</h2>
<div class="three"><div><b>Order on WhatsApp</b><p>Send us the style and size. We confirm the delivery time and shipping charge for your pincode.</p></div>
<div><b>Pay when it arrives</b><p>Cash on Delivery is available. Online payment options are coming soon.</p></div>
<div><b>Not sure of your size?</b><p>We stock S, M, L and XL. Send your height and weight on WhatsApp and we will recommend a size.</p></div></div>
<div class="row" style="margin-top:20px"><a class="btn p" href="/shop">Shop the collection</a><a class="btn o" href="{wa("Hi calyxculture")}" rel="noopener" target="_blank">{ic("wa")}Order on WhatsApp</a></div></section>
{new_arrivals()}
{cta('See you soon.', 'Visit the store in Bemina, or order from home with Cash on Delivery.')}'''
stores_ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"ClothingStore","name":"calyxculture","url":"' + DOMAIN + '/","image":"' + DOMAIN + OG + '","telephone":"' + PHONE_TEL +
             '","sameAs":["' + IG + '"],"address":{"@type":"PostalAddress","streetAddress":"Housing Colony, Jamia Market, Near Jamia Ahli-Hadees, Bemina","addressLocality":"Srinagar","addressRegion":"Jammu & Kashmir","addressCountry":"IN"}}</script>\n')

# ---------------------------------------------------------------- CONTACT
contact = f'''<div class="ph1"><h1 id="ct-h">Talk to us</h1><p class="lead">The fastest way to reach us is WhatsApp. We reply on the number you message from.</p></div>
<section class="sec" style="padding-top:8px" aria-label="Contact options"><div class="acts">
<a class="act p" href="{wa("Hi calyxculture")}" rel="noopener" target="_blank">{ic("wa")}<span><b>WhatsApp us</b><small>Fastest reply</small></span></a>
<a class="act" href="tel:{PHONE_TEL}">{ic("ph")}<span><b>Call {PHONE_TXT}</b><small>Call the store</small></span></a>
<a class="act" href="{IG}" rel="noopener" target="_blank">{ic("ig")}<span><b>Instagram</b><small>@calyxculture_</small></span></a></div></section>
<section class="sec cols" aria-labelledby="msg"><div><h2 class="h" id="msg">Send us a message</h2>
<form class="cf" id="cff" novalidate>
<div class="fld"><label for="c-n">Your name</label><input class="fi" id="c-n" name="n" autocomplete="name" maxlength="60" required></div>
<div class="fld"><label for="c-p">Phone number</label><input class="fi" id="c-p" name="p" type="tel" inputmode="numeric" autocomplete="tel-national" maxlength="14" required></div>
<div class="fld"><label for="c-m">Message</label><textarea class="fi" id="c-m" name="m" maxlength="500" required></textarea></div>
<input class="hp" name="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<button class="btn p" type="submit">Send message</button>
<p class="out" id="cfo" role="status" aria-live="polite"></p>
<noscript><p>The form needs JavaScript. Please <a href="{wa("Hi calyxculture")}">message us on WhatsApp</a> instead.</p></noscript></form>
<p class="mut" style="font-size:14px;margin-top:8px">We use your details only to reply to you. See our <a href="/policies.html#privacy">Privacy Policy</a>.</p></div>
<div><h2 class="h" id="vis">Visit or look up</h2>
<p style="margin-top:16px"><b>calyxculture, Bemina</b><br>{e(ADDR)}</p>
<p class="mut" style="margin-top:10px" data-email></p><p class="mut" data-hours></p>
<div class="row" style="margin-top:18px"><a class="btn o" href="/stores">Store details</a><a class="btn o" href="/faq">Read the FAQ</a></div>
<p class="mut" style="margin-top:18px;font-size:14px">Delivery, exchanges and payments are covered in our <a href="/policies.html#shipping">shipping policy</a> and <a href="/policies.html#returns">exchange policy</a>.</p></div></section>'''

# ---------------------------------------------------------------- FAQ
FAQS = [
    ('Is Cash on Delivery available?', 'Yes. You can pay Cash on Delivery, or send your order on WhatsApp and pay when it arrives.'),
    ('How long does delivery take?', 'Our team confirms the delivery time and shipping charge for your pincode on WhatsApp. Shipping is free once your bag crosses the free-shipping amount shown in the bag.'),
    ('What is the return or exchange policy?', 'We do not accept returns. We exchange only verified defects, wrong items, transit damage or missing items reported within 3 days of delivery with an unboxing video. See the Policies page for details.'),
    ('Which size should I pick?', 'We stock S, M, L and XL. Most styles are relaxed or oversized. Send your height and weight on WhatsApp and we will recommend a size.'),
    ('Where is your store?', ADDR + '.'),
    ('How can I contact you?', 'WhatsApp or call us on ' + PHONE_TXT + '.'),
    ('Can I pay online with UPI or card?', 'Online payments are not live yet. For now you can pay Cash on Delivery, and online payment options are coming soon.'),
    ('Where can I follow you?', 'Follow us on Instagram at instagram.com/calyxculture_.'),
    ('What is calyxculture?', 'calyxculture is a modern streetwear brand from Srinagar, Kashmir, making stylish, comfortable, quality clothing.'),
]
faq_items = ''.join(f'<details class="fq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in FAQS)
faq = f'''<div class="ph1"><h1 id="fq-h">Questions, answered</h1><p class="lead">Delivery, Cash on Delivery, sizes and exchanges.</p></div>
<section class="sec" style="padding-top:20px;max-width:820px" aria-labelledby="fq-h"><div id="faq-list">{faq_items}</div>
<p style="margin-top:22px">Read the full <a href="/policies.html#returns">exchange policy</a>, <a href="/policies.html#shipping">shipping policy</a> and <a href="/policies.html#privacy">privacy policy</a>.</p>
<div class="row" style="margin-top:20px"><a class="btn p" href="{wa("Hi calyxculture, I have a question")}" rel="noopener" target="_blank">{ic("wa")}Ask on WhatsApp</a><a class="btn o" href="/shop">Shop the collection</a></div></section>
{cta('Still deciding?', 'Message us your height, weight and the style you like. We will suggest a size.')}'''

PAGES = {
    'about.html': ('/about', 'About calyxculture | Streetwear from Srinagar, Kashmir',
                   'calyxculture is a streetwear label from Srinagar, Kashmir. Oversized tees, baggy denim, heavy hoodies and winter layers, cut for comfort and made to be seen.', '/about', about, hero_pre, ''),
    'stores.html': ('/stores', 'Our store in Bemina, Srinagar | calyxculture',
                    'Visit calyxculture in Bemina, Srinagar. Address, directions, phone and WhatsApp. Or order from home with Cash on Delivery.', '/stores', stores, '', stores_ld),
    'contact.html': ('/contact', 'Contact calyxculture | WhatsApp, call or message',
                     'Message, call or WhatsApp calyxculture in Srinagar. Fastest replies on WhatsApp.', '/contact', contact, '', ''),
    'faq.html': ('/faq', 'FAQ: delivery, Cash on Delivery, sizes and exchanges | calyxculture',
                 'Answers about orders, delivery, Cash on Delivery, sizes and exchanges at calyxculture.', '/faq', faq, '', ''),
}
for fn, (path, title, desc, cur, body, pre, ld) in PAGES.items():
    out = page(path, title, desc, cur, body, pre, ld)
    with open(os.path.join(ROOT, fn), 'w', encoding='utf-8') as f:
        f.write(out)
    print('wrote', fn, len(out), 'bytes')
