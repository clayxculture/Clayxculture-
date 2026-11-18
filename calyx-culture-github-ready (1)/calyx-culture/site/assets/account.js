(function(){
var SB='https://wxroneyxnidxluxtxsdq.supabase.co',KEY='sb_publishable_2hc-tOo_hNpjD8psyQZw8Q_cF4ECWeP',tok=null,user=null;
var $=function(s){return document.querySelector(s)};
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function store(k,v){try{v==null?sessionStorage.removeItem(k):sessionStorage.setItem(k,v)}catch(e){}}
function get(k){try{return sessionStorage.getItem(k)}catch(e){return null}}
(function(){var h=new URLSearchParams(location.hash.slice(1));if(h.get('access_token')&&get('cc_login')){store('cu_at',h.get('access_token'));store('cu_exp',String(Date.now()+(+h.get('expires_in')||3600)*1000));store('cc_login',null);history.replaceState(null,'',location.pathname+location.search);setTimeout(function(){open()},400)}})();
tok=get('cu_at');if(tok&&Date.now()>+get('cu_exp'))tok=null,store('cu_at',null);
function api(p){return fetch(SB+p,{headers:{apikey:KEY,Authorization:'Bearer '+tok}}).then(function(r){if(r.status===401){out();throw 0}return r.ok?r.json():Promise.reject()})}
function out(){tok=null;user=null;store('cu_at',null);store('cu_exp',null);paint()}
function login(){store('cc_login','1');location.href=SB+'/auth/v1/authorize?provider=google&redirect_to='+encodeURIComponent(location.origin+'/')}
var G='<svg width="20" height="20" viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.800 2.400 30.300 0 24 0 14.600 0 6.500 5.400 2.600 13.200l7.900 6.100C12.400 13.600 17.700 9.500 24 9.500z"/><path fill="#4285F4" d="M46.500 24.500c0-1.600-.1-3.100-.4-4.500H24v9h12.700c-.6 3-2.300 5.500-4.800 7.200l7.700 6c4.500-4.200 6.900-10.300 6.900-17.700z"/><path fill="#FBBC05" d="M10.500 28.700A14.500 14.500 0 0 1 9.500 24c0-1.600.3-3.200.9-4.700l-7.900-6.100A24 24 0 0 0 0 24c0 3.900.9 7.500 2.600 10.800l7.900-6.100z"/><path fill="#34A853" d="M24 48c6.500 0 11.900-2.100 15.900-5.800l-7.700-6c-2.200 1.400-4.900 2.300-8.200 2.300-6.300 0-11.600-4.100-13.500-9.800l-7.900 6.100C6.500 42.600 14.600 48 24 48z"/></svg>';
var ST={placed:'Placed',needs_verification:'Verifying',confirmed:'Confirmed',packed:'Packed',shipped:'Shipped',out_for_delivery:'Out for delivery',delivered:'Delivered',cancelled:'Cancelled',returned:'Returned'};
function paint(){
var b=$('#acb'),body=$('#acbody');if(!b||!body)return;
var i=user&&(user.n||user.e||'?').trim().charAt(0).toUpperCase();
b.innerHTML=user?'<span class="av">'+esc(i)+'</span>':'<svg class="i"><use href="#i-user"/></svg>';
b.setAttribute('aria-label',user?'Your account':'Sign in');
if(!tok){body.innerHTML='<div class="ac-hero"><div class="ac-logo"><svg viewBox="0 0 20 36" width="22" height="40" aria-hidden="true"><path fill="#fff" d="M10 0 12 15 20 18 12 21 10 36 8 21 0 18 8 15z"/></svg></div><h2>Welcome to calyxculture</h2><p>Sign in to track your orders, save your details and check out faster.</p><button class="ac-g" id="acg" type="button">'+G+'<span>Continue with Google</span></button><ul class="ac-pts"><li>Track every order in one place</li><li>Leave reviews on delivered items</li><li>No password to remember</li></ul><p class="ac-fine">By continuing you agree to our <a href="/policies.html#terms">Terms</a> and <a href="/policies.html#privacy">Privacy Policy</a>.</p></div>';return}
body.innerHTML='<div class="ac-me"><span class="av lg">'+esc(i||'?')+'</span><div><b>'+esc(user?user.n||'Your account':'Loading…')+'</b><span>'+esc(user?user.e:'')+'</span></div></div><div class="ac-q"><a href="/shop" data-nav data-x><svg class="i"><use href="#i-grid"/></svg>Shop</a><button type="button" data-open="wl"><svg class="i"><use href="#i-heart"/></svg>Wishlist</button><a href="https://wa.me/918899190631" rel="noopener"><svg class="i"><use href="#i-wa"/></svg>Support</a></div><h3 class="ac-h">My orders</h3><div id="aco"><p class="ac-fine">Loading orders…</p></div><button class="ac-so" id="aco2" type="button">Sign out</button>'}
function orders(){
api('/rest/v1/orders?select=code,status,total,created_at,items,tracking_id,courier&order=created_at.desc&limit=20').then(function(d){
var el=$('#aco');if(!el)return;
if(!d.length){el.innerHTML='<div class="ac-empty"><p>No orders yet.</p><a class="btn" href="/shop" data-nav data-x>Start shopping</a></div>';return}
el.innerHTML=d.map(function(o){var n=Array.isArray(o.items)?o.items.reduce(function(a,x){return a+(+x.qty||1)},0):0,dt=new Date(o.created_at).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'});
return '<div class="ac-o"><div><b>#'+esc(o.code)+'</b><span>'+dt+' · '+n+' item'+(n===1?'':'s')+'</span>'+(o.tracking_id?'<span>'+esc(o.courier||'Courier')+': '+esc(o.tracking_id)+'</span>':'')+'</div><div class="r"><b>₹'+esc(o.total)+'</b><i class="st s-'+esc(o.status)+'">'+esc(ST[o.status]||o.status)+'</i></div></div>'}).join('')}).catch(function(){var el=$('#aco');if(el)el.innerHTML='<p class="ac-fine">Couldn’t load orders. Try again later.</p>'})}
function load(){if(!tok){paint();return}
fetch(SB+'/auth/v1/user',{headers:{apikey:KEY,Authorization:'Bearer '+tok}}).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(u){var m=u.user_metadata||{};user={n:m.full_name||m.name||'',e:u.email||''};paint();if($('#acd')&&$('#acd').open)orders()}).catch(function(){out()})}
function open(){var d=$('#acd');if(!d)return;document.querySelectorAll('dialog[open]').forEach(function(x){x.close()});paint();d.showModal();if(tok&&user)orders()}
document.addEventListener('click',function(e){
var t=e.target.closest('#acb,#acg,#aco2,[data-acct]');if(!t)return;
if(t.id==='acg')login();else if(t.id==='aco2'){out();$('#acd').close()}else open()});
var d=$('#acd');if(d)d.addEventListener('click',function(e){if(e.target===d)d.close()});
load();
})();
