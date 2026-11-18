(()=>{'use strict';
// Everything here is progressive enhancement: the four pages are complete HTML without it.
// Page content is built with createElement and textContent only, so database text can never run as code.
const SB='https://wxroneyxnidxluxtxsdq.supabase.co',KEY='sb_publishable_2hc-tOo_hNpjD8psyQZw8Q_cF4ECWeP',CLD='https://res.cloudinary.com/soa4brgh/image/upload/';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const api=(p,o={})=>fetch(SB+'/rest/v1/'+p,{...o,headers:{apikey:KEY,'Content-Type':'application/json'},signal:typeof AbortSignal!=='undefined'&&AbortSignal.timeout?AbortSignal.timeout(9000):undefined});
const inr=n=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(n);
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
const imgu=(id,w)=>CLD+'f_auto,q_auto,w_'+w+'/'+String(id).replace(/[^\w\/.-]/g,'');
const WA='https://wa.me/918899190631?text=';

// menu: close with Escape and give focus back to the button
const mn=$('#mn');if(mn)addEventListener('keydown',e=>{if(e.key==='Escape'&&mn.open){mn.open=false;$('summary',mn).focus()}});

// live store settings (owner edits these in the admin panel)
async function settings(){
  try{
    const r=await api('store_settings?select=key,value&key=in.(seller,stores,free_ship_threshold)');if(!r.ok)return;
    const m={};(await r.json()).forEach(x=>{m[x.key]=x.value});
    const f=+m.free_ship_threshold;if(f>0)$$('[data-fs]').forEach(n=>{n.textContent=inr(f)});
    const s=m.seller&&typeof m.seller==='object'?m.seller:{};
    if(typeof s.support_hours==='string'&&s.support_hours.trim())$$('[data-hours]').forEach(n=>{n.textContent='Support hours: '+s.support_hours.trim().slice(0,120)});
    if(typeof s.support_email==='string'&&/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(s.support_email.trim()))$$('[data-email]').forEach(n=>{n.textContent='Email: '+s.support_email.trim()});
    if(Array.isArray(m.stores)&&m.stores.length)renderStores(m.stores.slice(0,10));
  }catch{}
}
function renderStores(list){
  const box=$('#stores-list');if(!box)return;box.replaceChildren();
  list.forEach(s=>{
    if(!s||typeof s.name!=='string')return;
    const a=el('article','sc');a.append(el('h2',null,s.name.slice(0,80)));
    const addr=String(s.address||'').slice(0,200);if(addr)a.append(el('address',null,addr));
    const tel=String(s.phone||'').replace(/[^\d+]/g,'').slice(0,16);
    if(tel){const p=el('p','ph2','Phone: '),l=el('a',null,String(s.phone).slice(0,24));l.href='tel:'+tel;p.append(l);a.append(p)}
    const row=el('div','row'),d=el('a','btn p','Get directions');
    d.href='https://www.google.com/maps/search/?api=1&query='+encodeURIComponent((s.name+' '+addr).slice(0,200));d.target='_blank';d.rel='noopener';row.append(d);
    if(tel){const c=el('a','btn o','Call the store');c.href='tel:'+tel;row.append(c)}
    const w=el('a','btn o','Check timings');w.href=WA+encodeURIComponent('Hi calyxculture, I would like to visit '+s.name.slice(0,80)+'. What are your timings today?');w.target='_blank';w.rel='noopener';row.append(w);
    a.append(row);box.append(a);
  });
  if(list.length>1){const h=$('#st-h');if(h)h.textContent='Our stores'}
}

// FAQ managed in the admin panel replaces the built-in answers
async function faq(){
  const box=$('#faq-list');if(!box)return;
  try{
    const r=await api('faq?select=question,answer&order=sort.asc');if(!r.ok)return;const l=await r.json();
    if(!Array.isArray(l)||!l.length)return;box.replaceChildren();
    l.slice(0,60).forEach(f=>{if(!f||!f.question||!f.answer)return;const d=el('details','fq'),s=el('summary',null,String(f.question).slice(0,200));d.append(s,el('p',null,String(f.answer).slice(0,1500)));box.append(d)});
  }catch{}
}

// newest real products (never the sample ones)
async function arrivals(){
  const sec=$('#pop');if(!sec)return;
  try{
    const r=await api('products?status=eq.published&is_demo=eq.false&select=id,name,price,compare_at,image_url&order=created_at.desc,id.desc&limit=4');if(!r.ok)return;
    const l=await r.json();if(!Array.isArray(l)||!l.length)return;const g=$('#pop-g');g.replaceChildren();
    l.forEach(p=>{
      const id=parseInt(p.id,10),pr=+p.price;if(!id||!(pr>=0))return;
      const a=el('a','pc');a.href='/product/'+id;const ph=el('div','ph');
      if(p.image_url){const i=new Image();i.alt=String(p.name||'').slice(0,100);i.width=400;i.height=500;i.loading='lazy';i.decoding='async';i.src=imgu(p.image_url,400);i.srcset=imgu(p.image_url,240)+' 240w, '+imgu(p.image_url,400)+' 400w, '+imgu(p.image_url,736)+' 736w';i.sizes='(min-width:640px) 23vw, 46vw';ph.append(i)}
      const price=el('span',null,inr(pr));if(+p.compare_at>pr){price.append(el('s',null,inr(+p.compare_at)))}
      a.append(ph,el('b',null,String(p.name||'').slice(0,80)),price);g.append(a);
    });
    if(g.children.length)sec.hidden=false;
  }catch{}
}

// contact form (same rules as the storefront chat and the database)
const fm=$('#cff');
if(fm)fm.addEventListener('submit',async ev=>{
  ev.preventDefault();const out=$('#cfo'),btn=$('button[type=submit]',fm);out.className='out';
  if(fm.elements.hp.value)return;
  const n=fm.elements.n.value.trim(),ph=fm.elements.p.value.replace(/\D/g,'').slice(-10),m=fm.elements.m.value.trim();
  if(n.length<2){out.textContent='Please enter your name.';fm.elements.n.focus();return}
  if(!/^[6-9]\d{9}$/.test(ph)){out.textContent='Please enter a valid 10-digit phone number.';fm.elements.p.focus();return}
  if(m.length<10){out.textContent='Please write at least 10 characters.';fm.elements.m.focus();return}
  btn.disabled=true;out.textContent='Sending…';
  try{
    const x=await api('contact_messages',{method:'POST',body:JSON.stringify({name:n,phone:ph,message:m})});
    if(x.ok){fm.reset();out.className='out ok';out.textContent='Thank you. Your message has reached our team and we will reply on WhatsApp.'}
    else{const e=await x.json().catch(()=>({}));out.textContent=/rate_limited/.test(e.message||'')?'You have sent a few messages already. Please try again later or use WhatsApp.':'Could not send right now. Please use WhatsApp instead.'}
  }catch{out.textContent='No connection. Please check your internet or use WhatsApp.'}
  btn.disabled=false;
});

settings();faq();arrivals();
})();
