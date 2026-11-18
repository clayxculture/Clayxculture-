(function(){
var SB='https://wxroneyxnidxluxtxsdq.supabase.co',KEY='sb_publishable_2hc-tOo_hNpjD8psyQZw8Q_cF4ECWeP',H={apikey:KEY,'Content-Type':'application/json'};
var sec=document.getElementById('fr'),rail=document.getElementById('frr');if(!sec||!rail||!window.fetch)return;
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
function stars(n){n=Math.max(0,Math.min(5,Math.round(n)));return '★★★★★'.slice(0,n)+'☆☆☆☆☆'.slice(0,5-n)}
fetch(SB+'/rest/v1/products?select=id&status=eq.published&order=id.desc&limit=10',{headers:H}).then(function(r){return r.ok?r.json():[]}).then(function(ps){
return Promise.all(ps.map(function(p){return fetch(SB+'/rest/v1/rpc/get_reviews',{method:'POST',headers:H,body:JSON.stringify({pid:p.id})}).then(function(r){return r.ok?r.json():null}).catch(function(){return null})}))}).then(function(all){
var items=[],sum=0;all.forEach(function(d){if(d&&Array.isArray(d.items))d.items.forEach(function(x){if(x&&x.body&&x.rating){items.push(x);sum+=+x.rating}})});
if(items.length<3)return;
items.sort(function(a,b){return String(b.created_at||'').localeCompare(String(a.created_at||''))});
var avg=(sum/items.length).toFixed(1);
document.getElementById('fr-avg').textContent=avg;document.getElementById('fr-cnt').textContent='from '+items.length+' verified review'+(items.length===1?'':'s');
var st=document.getElementById('fr-st');st.textContent=stars(avg);st.setAttribute('aria-label',avg+' out of 5');
items.slice(0,12).forEach(function(x){var f=el('figure','fri'),n=el('div','st',stars(x.rating));n.setAttribute('role','img');n.setAttribute('aria-label',x.rating+' out of 5');
f.appendChild(el('figcaption',null,(x.name||'Customer')+' · Verified buyer'));f.appendChild(n);f.appendChild(el('blockquote',null,x.body));rail.appendChild(f)});
sec.hidden=false}).catch(function(){});
})();
