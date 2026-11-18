const V='cc-shell-v8',A='cc-assets-v1',OWN=['/about','/stores','/contact','/faq','/policies.html'];
self.addEventListener('install',e=>{e.waitUntil((async()=>{const c=await caches.open(V);await c.addAll(['/','/offline.html']);
try{const t=await(await fetch('/')).text();await Promise.all([...new Set([...t.matchAll(/\/assets\/[\w.-]+\.(?:js|css)\?v=\w+/g)].map(m=>m[0]))].map(x=>c.add(x)))}catch{}
await self.skipWaiting()})())});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V&&x!==A).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{const r=e.request,u=new URL(r.url);if(r.method!=='GET'||u.pathname.startsWith('/admin'))return;
if(r.mode==='navigate'){const own=OWN.includes(u.pathname);e.respondWith(fetch(r).then(x=>{if(x.ok){const c=x.clone();caches.open(V).then(h=>h.put(own?r:'/',c))}return x}).catch(()=>caches.match(own?r:'/').then(x=>x||caches.match('/offline.html'))));return}
if(u.origin===location.origin&&(u.pathname.startsWith('/img/')||u.pathname.startsWith('/assets/'))){e.respondWith(caches.match(r).then(m=>m||fetch(r).then(x=>{if(x.ok){const c=x.clone();caches.open(A).then(h=>h.put(r,c))}return x})));return}
if(u.hostname==='fonts.gstatic.com'||u.hostname==='fonts.googleapis.com'){e.respondWith(caches.open(A).then(c=>c.match(r).then(m=>{const f=fetch(r).then(x=>{if(x.ok)c.put(r,x.clone());return x}).catch(()=>m);return m||f})))}});
