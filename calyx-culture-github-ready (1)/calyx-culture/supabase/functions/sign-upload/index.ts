// Staff-only signed Cloudinary upload (product photos, hero video).
// Needs permission 'uploads.product' (checked in the database by has_perm(), not in the browser).
// Secrets (Supabase > Edge Functions > Secrets): CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET,
//   CLOUDINARY_CLOUD_NAME (optional), ALLOWED_ORIGINS (optional, comma separated; defaults to the production domain).
// Each signature is bound to ONE server-chosen public_id with overwrite=false, so replaying a stolen
// signature cannot create a second asset or replace an existing one. Cloudinary itself rejects
// signatures older than one hour.
const ORIGINS = (Deno.env.get('ALLOWED_ORIGINS') || 'https://clayxculture.in,https://www.clayxculture.in').split(',').map(s => s.trim()).filter(Boolean);
const FORMATS: Record<string, string> = { image: 'jpg,jpeg,png,webp,avif', video: 'mp4,webm' };
const hex = (b: ArrayBuffer) => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
Deno.serve(async (req: Request) => {
  const o = req.headers.get('origin') || '';
  const h = { 'Access-Control-Allow-Origin': ORIGINS.includes(o) ? o : ORIGINS[0], 'Access-Control-Allow-Headers': 'authorization,content-type,apikey', 'Access-Control-Allow-Methods': 'POST,OPTIONS', 'Vary': 'Origin', 'Content-Type': 'application/json' };
  const out = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: h });
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: h });
  if (req.method !== 'POST' || !ORIGINS.includes(o)) return out({ error: 'forbidden' }, 403);
  const auth = req.headers.get('authorization') || '';
  if (!auth.startsWith('Bearer ')) return out({ error: 'forbidden' }, 403);
  let b: any = {}; try { b = await req.json() } catch { /* empty body means image */ }
  const kind = b && b.kind === 'video' ? 'video' : 'image';
  const r = await fetch(Deno.env.get('SUPABASE_URL') + '/rest/v1/rpc/has_perm', { method: 'POST', headers: { apikey: Deno.env.get('SUPABASE_ANON_KEY') || '', Authorization: auth, 'Content-Type': 'application/json' }, body: JSON.stringify({ p: 'uploads.product' }) });
  if (!r.ok || (await r.json()) !== true) return out({ error: 'forbidden' }, 403);
  const secret = Deno.env.get('CLOUDINARY_API_SECRET'), apiKey = Deno.env.get('CLOUDINARY_API_KEY'), cloud = Deno.env.get('CLOUDINARY_CLOUD_NAME') || 'soa4brgh';
  if (!secret || !apiKey) return out({ error: 'not_configured' }, 500);
  const ts = Math.floor(Date.now() / 1000), public_id = 'calyx/p/' + crypto.randomUUID().replace(/-/g, ''), allowed_formats = FORMATS[kind];
  // parameters in alphabetical order, exactly as Cloudinary verifies them
  const p: Record<string, string> = { allowed_formats, overwrite: 'false', public_id, timestamp: String(ts) };
  if (kind === 'image') p.transformation = 'c_limit,h_2400,w_2400'; // incoming transformation caps dimensions
  const toSign = Object.keys(p).sort().map(k => k + '=' + p[k]).join('&');
  const signature = hex(await crypto.subtle.digest('SHA-1', new TextEncoder().encode(toSign + secret)));
  return out({ signature, timestamp: ts, api_key: apiKey, cloud_name: cloud, ...p });
});
