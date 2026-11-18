// Customer review photo signing. A customer gets a signature only if the database (issue_review_upload,
// callable by the service role only) confirms: delivered order, matching phone, product in the order,
// photo limit not reached, and fewer than 3 tokens in 24h for that order. The token is single-use and
// is checked again by submit_review, so a photo cannot be attached to someone else's order or product.
// Secrets: CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET, CLOUDINARY_CLOUD_NAME (optional), ALLOWED_ORIGINS (optional).
// SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are injected by Supabase. The service-role key never leaves this function.
const ORIGINS = (Deno.env.get('ALLOWED_ORIGINS') || 'https://clayxculture.in,https://www.clayxculture.in').split(',').map(s => s.trim()).filter(Boolean);
const hex = (b: ArrayBuffer) => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
Deno.serve(async (req: Request) => {
  const o = req.headers.get('origin') || '';
  const h = { 'Access-Control-Allow-Origin': ORIGINS.includes(o) ? o : ORIGINS[0], 'Access-Control-Allow-Headers': 'content-type,apikey', 'Access-Control-Allow-Methods': 'POST,OPTIONS', 'Vary': 'Origin', 'Content-Type': 'application/json' };
  const out = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: h });
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: h });
  if (req.method !== 'POST' || !ORIGINS.includes(o)) return out({ error: 'forbidden' }, 403);
  let b: any; try { b = await req.json() } catch { return out({ error: 'bad_request' }, 400) }
  const c = String(b.c || '').slice(0, 20), ph = String(b.ph || '').replace(/\D/g, '').slice(-10), pid = Number(b.pid);
  if (!c || ph.length !== 10 || !Number.isInteger(pid)) return out({ error: 'bad_request' }, 400);
  const secret = Deno.env.get('CLOUDINARY_API_SECRET'), apiKey = Deno.env.get('CLOUDINARY_API_KEY'), cloud = Deno.env.get('CLOUDINARY_CLOUD_NAME') || 'soa4brgh';
  const svc = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || '';
  if (!secret || !apiKey || !svc) return out({ error: 'not_configured' }, 500);
  const ip = (req.headers.get('cf-connecting-ip') || (req.headers.get('x-forwarded-for') || '').split(',')[0] || 'unknown').trim();
  const r = await fetch(Deno.env.get('SUPABASE_URL') + '/rest/v1/rpc/issue_review_upload', { method: 'POST', headers: { apikey: svc, Authorization: 'Bearer ' + svc, 'Content-Type': 'application/json' }, body: JSON.stringify({ c, ph, pid, ip }) });
  if (!r.ok) { const t = await r.text(); return out({ error: /rate_limited/.test(t) ? 'rate_limited' : 'not_allowed' }, /rate_limited/.test(t) ? 429 : 403); }
  const tok = await r.json(); const public_id = tok && tok.public_id;
  if (typeof public_id !== 'string' || !/^calyx\/r\/[A-Za-z0-9_-]+$/.test(public_id)) return out({ error: 'not_allowed' }, 403);
  const ts = Math.floor(Date.now() / 1000), allowed_formats = 'jpg,jpeg,png,webp';
  const p: Record<string, string> = { allowed_formats, overwrite: 'false', public_id, timestamp: String(ts), transformation: 'c_limit,h_1600,w_1600' };
  const toSign = Object.keys(p).sort().map(k => k + '=' + p[k]).join('&');
  const signature = hex(await crypto.subtle.digest('SHA-1', new TextEncoder().encode(toSign + secret)));
  return out({ signature, timestamp: ts, api_key: apiKey, cloud_name: cloud, ...p });
});
