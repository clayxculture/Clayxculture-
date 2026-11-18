// Runs the REAL edge function source with a stubbed Deno runtime and stubbed network.
// Run: node --test tests/unit
import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import path from 'node:path';
import fs from 'node:fs';
import os from 'node:os';
import { pathToFileURL } from 'node:url';

const ROOT = path.resolve(import.meta.dirname, '../../supabase/functions');
const SECRET = 'test-secret', ORIGIN = 'https://clayxculture.in';
let n = 0;

async function load(name, env = {}, fetchImpl) {
  const e = { SUPABASE_URL: 'https://x.supabase.co', SUPABASE_ANON_KEY: 'anon', SUPABASE_SERVICE_ROLE_KEY: 'SERVICEKEY',
    CLOUDINARY_API_KEY: 'k', CLOUDINARY_API_SECRET: SECRET, ...env };
  let handler;
  globalThis.Deno = { env: { get: k => e[k] }, serve: h => { handler = h; } };
  globalThis.fetch = fetchImpl;
  // copy to a unique file: Node caches .ts modules by path and ignores query strings
  const tmp = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'edge-')), name + '-' + (++n) + '.ts');
  fs.copyFileSync(path.join(ROOT, name, 'index.ts'), tmp);
  await import(pathToFileURL(tmp).href);
  return handler;
}
const req = (body, headers = {}, method = 'POST') => new Request('https://f/x', { method, headers: { origin: ORIGIN, 'content-type': 'application/json', ...headers }, body: method === 'POST' ? JSON.stringify(body) : undefined });
const sha1 = s => crypto.createHash('sha1').update(s).digest('hex');
const recompute = (j, keys) => sha1(keys.sort().map(k => k + '=' + j[k]).join('&') + SECRET);
const json = (b, ok = true, status = 200) => ({ ok, status, json: async () => b, text: async () => JSON.stringify(b) });

test('sign-upload: rejects missing bearer, wrong origin and non-staff', async () => {
  const calls = [];
  const h = await load('sign-upload', {}, async (u, o) => { calls.push([u, o]); return json(false); });
  assert.equal((await h(req({}))).status, 403);
  assert.equal((await h(req({}, { authorization: 'Bearer t', origin: 'https://evil.example' }))).status, 403);
  assert.equal((await h(req({}, { authorization: 'Bearer t' }))).status, 403);
  assert.equal(JSON.parse(calls[0][1].body).p, 'uploads.product', 'must check the uploads.product permission');
});

test('sign-upload: image signature is valid, single-asset and size-capped', async () => {
  const h = await load('sign-upload', {}, async () => json(true));
  const r = await h(req({}, { authorization: 'Bearer t' })); const j = await r.json();
  assert.equal(r.status, 200);
  assert.match(j.public_id, /^calyx\/p\/[a-f0-9]{32}$/);
  assert.equal(j.overwrite, 'false');
  assert.equal(j.allowed_formats, 'jpg,jpeg,png,webp,avif');
  assert.equal(j.transformation, 'c_limit,h_2400,w_2400');
  assert.equal(j.signature, recompute(j, ['allowed_formats', 'overwrite', 'public_id', 'timestamp', 'transformation']));
  assert.ok(!JSON.stringify(j).includes(SECRET));
  const j2 = await (await h(req({}, { authorization: 'Bearer t' }))).json();
  assert.notEqual(j.public_id, j2.public_id, 'every signature gets a fresh public_id');
});

test('sign-upload: video only allows mp4/webm', async () => {
  const h = await load('sign-upload', {}, async () => json(true));
  const j = await (await h(req({ kind: 'video' }, { authorization: 'Bearer t' }))).json();
  assert.equal(j.allowed_formats, 'mp4,webm'); assert.equal(j.transformation, undefined);
  assert.equal(j.signature, recompute(j, ['allowed_formats', 'overwrite', 'public_id', 'timestamp']));
});

test('sign-upload: not configured and ALLOWED_ORIGINS override', async () => {
  let h = await load('sign-upload', { CLOUDINARY_API_SECRET: '' }, async () => json(true));
  assert.equal((await h(req({}, { authorization: 'Bearer t' }))).status, 500);
  h = await load('sign-upload', { ALLOWED_ORIGINS: 'https://staging.example' }, async () => json(true));
  assert.equal((await h(req({}, { authorization: 'Bearer t' }))).status, 403);
});

const good = { c: 'CC-10482', ph: '9876543210', pid: 7 };
test('sign-review-upload: uses service role server-side, forwards client IP, signs DB-issued id', async () => {
  let call;
  const h = await load('sign-review-upload', {}, async (u, o) => { call = [u, o]; return json({ public_id: 'calyx/r/abc123' }); });
  const r = await h(req(good, { 'cf-connecting-ip': '1.2.3.4' })); const j = await r.json();
  assert.equal(r.status, 200);
  assert.ok(call[0].endsWith('/rpc/issue_review_upload'));
  assert.equal(call[1].headers.Authorization, 'Bearer SERVICEKEY');
  assert.equal(JSON.parse(call[1].body).ip, '1.2.3.4');
  assert.equal(j.public_id, 'calyx/r/abc123');
  assert.equal(j.signature, recompute(j, ['allowed_formats', 'overwrite', 'public_id', 'timestamp', 'transformation']));
  assert.ok(!JSON.stringify(j).includes('SERVICEKEY') && !JSON.stringify(j).includes(SECRET));
});

test('sign-review-upload: maps DB refusals and rejects malformed ids', async () => {
  let h = await load('sign-review-upload', {}, async () => json('{"message":"rate_limited"}', false, 400));
  assert.equal((await h(req(good))).status, 429);
  h = await load('sign-review-upload', {}, async () => json('{"message":"not_allowed"}', false, 400));
  assert.equal((await h(req(good))).status, 403);
  h = await load('sign-review-upload', {}, async () => json({ public_id: 'calyx/p/steal' }));
  assert.equal((await h(req(good))).status, 403, 'a product-folder id must never be signed for a customer');
  h = await load('sign-review-upload', {}, async () => json({ public_id: 'calyx/r/../p/x' }));
  assert.equal((await h(req(good))).status, 403);
});

test('sign-review-upload: input validation and origin', async () => {
  let called = false;
  const h = await load('sign-review-upload', {}, async () => { called = true; return json({}); });
  assert.equal((await h(req({ c: '', ph: '1', pid: 'x' }))).status, 400);
  assert.equal((await h(req(good, { origin: 'https://evil.netlify.app' }))).status, 403);
  assert.equal(called, false);
});
