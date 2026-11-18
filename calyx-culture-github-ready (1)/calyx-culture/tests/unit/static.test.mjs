// Static checks on configuration and SQL. These are lint-level guards, NOT database tests.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import fsCrypto from 'node:crypto';
const R = path.resolve(import.meta.dirname, '../..'), rd = p => fs.readFileSync(path.join(R, p), 'utf8');

test('migration: every SECURITY DEFINER function pins an empty search_path', () => {
  const sql = rd('supabase/migrations/20261116_01_security_hardening.sql');
  const fns = sql.split(/create or replace function/i).slice(1);
  assert.ok(fns.length >= 10);
  for (const f of fns) {
    const head = f.split(/\$\$/)[0];
    if (/security definer/i.test(head)) assert.match(head, /set search_path = ''/i, 'missing empty search_path: ' + head.slice(0, 60));
  }
});
test('migration: store_settings is no longer world-readable and risk keys are not public', () => {
  const sql = rd('supabase/migrations/20261116_01_security_hardening.sql');
  const pol = sql.match(/create policy settings_public_read[\s\S]*?;/)[0];
  assert.ok(!/using\s*\(\s*true\s*\)/i.test(pol));
  for (const k of ['risk_review', 'risk_reject', 'cod_cap_first', 'review_photo_limit']) assert.ok(!pol.includes("'" + k + "'"), k + ' must stay private');
});
test('migration: customers cannot read orders; privileged functions are not callable by anon', () => {
  const sql = rd('supabase/migrations/20261116_01_security_hardening.sql');
  assert.ok(!/orders_read[^;]*auth\.uid/i.test(sql));
  const toAnon = sql.split('\n').filter(l => /^grant execute/i.test(l) && /anon/.test(l)).join(' ');
  for (const f of ['set_order_status', 'issue_review_upload', 'rate_hit', 'rate_count', '_review_eligibility']) assert.ok(!toAnon.includes(f), f);
});
test('storefront uses only settings keys that the public policy allows', () => {
  const sql = rd('supabase/migrations/20261116_01_security_hardening.sql');
  const pol = sql.match(/create policy settings_public_read[\s\S]*?;/)[0];
  const idx = rd('site/assets/app.js');
  const used = [...new Set([...idx.matchAll(/\bm\.([a-z_]+)/g)].map(m => m[1]))].filter(k => k.includes('_') || ['announcement', 'notice', 'welcome', 'reels', 'seller', 'stores', 'delivery'].includes(k));
  for (const k of used) assert.ok(pol.includes("'" + k + "'"), 'storefront reads setting "' + k + '" but the policy hides it');
});
test('no secrets in site/ or functions', () => {
  for (const f of ['site/index.html', 'site/assets/app.js', 'site/assets/pages.js', 'site/admin/admin.js', 'site/policies.html', 'supabase/functions/sign-upload/index.ts', 'supabase/functions/sign-review-upload/index.ts']) {
    const t = rd(f);
    assert.ok(!/sb_secret_|BEGIN (RSA )?PRIVATE KEY|eyJ[A-Za-z0-9_-]{30,}\.[A-Za-z0-9_-]{30,}/.test(t), f);
    assert.ok(!/service_role['"]?\s*[:=]\s*['"][^'"]+/.test(t), f);
  }
});
test('_headers: admin CSP forbids inline script; every CSP names the real Supabase host; one domain in SEO files', () => {
  const h = rd('site/_headers');
  const admin = h.match(/\/admin\/\*[\s\S]*?Content-Security-Policy: ([^\n]+)/)[1];
  assert.match(admin, /script-src 'self'(;| )/); assert.ok(!/script-src[^;]*unsafe-inline/.test(admin));
  const hosts = new Set([...h.matchAll(/https:\/\/([a-z0-9]+)\.supabase\.co/g)].map(m => m[1]));
  assert.equal(hosts.size, 1);
  assert.ok(rd('site/assets/app.js').includes([...hosts][0] + '.supabase.co'));
  assert.ok(rd('site/assets/pages.js').includes([...hosts][0] + '.supabase.co'));
  const dom = new Set(['site/sitemap.xml', 'site/robots.txt'].flatMap(f => [...rd(f).matchAll(/https:\/\/([a-z.]+)\//g)].map(m => m[1])));
  assert.equal(dom.size, 1);
});

const HTML = ['index', 'about', 'stores', 'contact', 'faq', 'policies', '404', 'offline'].map(n => 'site/' + n + '.html');
test('no page has an inline script, inline event handler or javascript: link (strict CSP depends on it)', () => {
  for (const f of HTML) {
    const t = rd(f);
    assert.ok(![...t.matchAll(/<script(?![^>]*\bsrc=)[^>]*>/g)].some(m => !/application\/ld\+json/.test(m[0])), f + ': inline script');
    assert.ok(!/\son[a-z]+\s*=\s*["']/i.test(t), f + ': inline handler');
    assert.ok(!/javascript:/i.test(t), f + ': javascript: URL');
  }
});
test('_headers: every page path has exactly one CSP; none allows inline or eval script', () => {
  const blocks = rd('site/_headers').split(/\n\s*\n/).filter(b => /Content-Security-Policy/.test(b));
  assert.ok(blocks.length >= 15);
  for (const b of blocks) {
    const n = (b.match(/Content-Security-Policy:/g) || []).length; assert.equal(n, 1, b.split('\n')[0]);
    const sc = b.match(/script-src ([^;]+)/)[1]; assert.equal(sc.trim(), "'self'", b.split('\n')[0]);
  }
  const paths = blocks.map(b => b.split('\n')[0].trim());
  for (const p of ['/', '/shop/*', '/product/*', '/about', '/stores', '/contact', '/faq', '/about.html', '/admin/*', '/policies.html']) assert.ok(paths.includes(p), 'no CSP rule for ' + p);
});
test('about, stores, contact and faq are real files, not rewrites to the shop app', () => {
  const red = rd('site/_redirects');
  for (const p of ['about', 'stores', 'contact', 'faq']) {
    assert.match(red, new RegExp('^/' + p + '\\s+/' + p + '\\.html\\s+200', 'm'));
    const t = rd('site/' + p + '.html');
    assert.equal((t.match(/<h1[ >]/g) || []).length, 1, p + ': one h1');
    assert.match(t, /<link rel="canonical" href="https:\/\/clayxculture\.in\/[a-z]+">/);
    assert.match(t, /<meta name="description" content="[^"]{40,}/);
    assert.ok(!/\sstyle\s*=/.test(t), p + ': inline style (these pages run without unsafe-inline styles)');
  }
});
test('asset links carry the current content hash and the files exist', () => {
  const crypto = await_import();
  for (const f of HTML) for (const m of rd(f).matchAll(/\/assets\/([\w.-]+)\?v=(\w+)/g)) {
    const h = crypto.createHash('sha256').update(fs.readFileSync(path.join(R, 'site/assets', m[1]))).digest('hex').slice(0, 8);
    assert.equal(m[2], h, f + ' -> ' + m[1] + ' is stale: run python3 tools/stamp.py');
  }
});
function await_import() { return { createHash: (a) => fsCrypto.createHash(a) }; }
test('pages.js builds DOM safely (no innerHTML / eval)', () => {
  for (const f of ['site/assets/pages.js']) assert.ok(!/innerHTML|outerHTML|insertAdjacentHTML|eval\(|new Function|document\.write/.test(rd(f)), f);
});
