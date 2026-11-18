# Audit report, tranche 1 (2026-11-16)

**Verdict: NOT approved for production.** This tranche fixes the highest-risk database and upload issues in code, but the
database changes have never been run, several mandated areas are untouched, and owner-supplied items are missing.

## How to read "status"
- **Verified**: a test was executed here and passed (command shown).
- **Written, unverified**: code exists but could not be executed here (no Postgres, no Cloudinary, no Supabase access).
- **Open**: not started.

## Findings (from reading the code in the uploaded zip)
| # | Sev | Finding | Fix | Status |
|---|-----|---------|-----|--------|
| 1 | High | `store_settings` readable by everyone (`using (true)`), exposing `risk_review`, `risk_reject`, `cod_cap_first` | Public allowlist policy | Written, unverified; allowlist lint passes |
| 2 | High | Customers could read their own `orders` rows over REST, including `risk_score`, `risk_flags`, `notes`, `verified_by` (admin email). Storefront never reads that table directly | Orders/events readable only with `orders.read` | Written, unverified |
| 3 | High | Coupon `max_uses` race: check and increment were separate, so concurrent orders could exceed the limit | Limit enforced inside the `UPDATE` | Written, unverified (no concurrency test possible here) |
| 4 | High | Any admin could add admins; all admins had all powers (no roles) | `admin_emails.role`, `role_permissions`, `has_perm()`; policies and `set_order_status` use it. Existing admins become `owner` | Written, unverified. Admin UI does not yet hide tabs per role |
| 5 | High | `submit_review` accepted any `calyx/r/...` image id: a reviewer could attach another customer's photo or an arbitrary file | Single-use `upload_tokens` bound to order+product, issued only by service-role RPC | Edge side **verified** (tests 5-7); SQL written, unverified |
| 6 | Medium | `track_order`, `review_check`, `check_coupon` had no attempt limits | `rate_events`, per-IP and per-code limits, lockout, `track_lockout` audit entry | Written, unverified |
| 7 | Medium | Admin upload signature: any file type/size/dimension via client-chosen resource type, replayable, no `public_id` binding | Server `public_id`, `overwrite=false`, `allowed_formats`, dimension cap, `uploads.product` permission | **Verified** by tests 1-4 (signature recomputed). Cloudinary acceptance not tested |
| 8 | Medium | Customer review signing had no quota; origin allowlist accepted every `*.netlify.app` / `*.pages.dev` | 3 tokens per order per 24h; origins from `ALLOWED_ORIGINS` secret | Tests 5-7 **verified** |
| 9 | Medium | `place_order`: missing `color` bypassed the colour check (NULL logic); lock order could deadlock | Fixed; locks in id order | Written, unverified |
| 10 | Medium | Cancelling an order never returned the coupon use | Restored on cancel (not on return) | Written, unverified |
| 11 | Medium | Contact form: anon could set `handled`/`created_at` | Column-level INSERT grant | Written, unverified |
| 12 | Medium | No least-privilege table grants (RLS was the only lock); several SECURITY DEFINER functions had `search_path=public` | Revoke-all then minimal grants; empty search_path | Pin check **verified** by lint; grants unverified |
| 13 | Medium | `check_coupon` ignored `expires_at` (UI promised a discount `place_order` then refused) | Expiry honoured | Written, unverified |
| 14 | Low | Audit insert lets any admin write arbitrary `detail` (actor is forced by trigger) | Not fixed | Open |
| 15 | Low | `script-src 'unsafe-inline'` on storefront (inline script block) | Not fixed. Needs the script moved to a file; that breaks the documented `file://` preview mode, so it needs your decision | Open |
| 16 | Info | Domain `clayxculture.in` is used consistently, but brand is "Calyx", wordmark "calyxculture", Instagram "thecalyxwear". I cannot tell if the spelling is intentional | Not changed | **Owner must confirm** |
| 17 | Info | Order codes stay sequential (`CC-10482`) because the UI and chat parser depend on it; the phone is the second factor and attempts are now limited | Deliberate | Documented |

## Tests actually executed
- `node --test tests/unit/*.test.mjs`: **13 passed, 0 failed** (7 edge-function tests against the real source with stubbed runtime; 6 config/SQL lint tests).
- `tests/run-all.sh`: all 7 browser scripts passed before and after my edits. They use a mocked backend, so they prove the UI still works, not that the database is secure.
- CI secret scan pattern run locally: clean.

## NOT done / NOT verified (do not assume)
- Migration never executed; `supabase/tests/rls_matrix.sql` never executed. Role matrix blocks are a template, not finished tests.
- Open and untouched: online payments (stays disabled, correct), Turnstile, per-role admin UI, audit coverage for login/price/stock changes, backup/restore system and restore test, variants and per-size stock, draft/archive UI checks, SEO prerendering and product sitemap, Lighthouse and Core Web Vitals measurements, WCAG testing, visual redesign, code splitting, legal placeholders (owner data), monitoring.
- No Lighthouse, penetration test, concurrency or production results exist.

## Owner must supply or do
1. Confirm the domain spelling (finding 16).
2. Seller details for `/policies.html` (the 14 `seller` fields); no placeholder may ship.
3. Create a staging Supabase project; run migration, then `rls_matrix.sql`; send me the output.
4. Set secrets: `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `ALLOWED_ORIGINS` (add any preview URL you test on). `SUPABASE_SERVICE_ROLE_KEY` is injected by Supabase; never put it in `site/`.
5. Deploy order: migration, edge functions, then site (see `docs/ROLLBACK.md`).
6. Turn on 2-step verification for the Google admin account (the database cannot enforce MFA for Google OAuth).

---
# Tranche 2 (2026-11-17): standalone pages, strict script policy, speed

**Verdict: still NOT approved for production.** The website side is much stronger, but the items below that only you can do are still open, and the database migration has still never been run.

| # | Change | Status |
|---|---|---|
| 18 | `/about`, `/stores`, `/contact`, `/faq` are now real HTML files (own title, canonical, description, one h1, content readable without JavaScript) instead of `_redirects` rewrites to the shop app. FAQ, extra stores, support hours, email, free-shipping amount and newest products still update live from the admin panel | **Verified**: `tests/e2e_standalone.py` (phone and desktop widths, no horizontal scroll, every link resolves, contact form payload, database text cannot inject HTML) |
| 19 | Finding 15 closed: all inline scripts moved to `site/assets/*.js`; every page now has `script-src 'self'` with no `unsafe-inline`; the four new pages also have no inline styles. Addresses Lighthouse "CSP effective against XSS" | **Verified** by running every browser test with the real `_headers` enforced (`tests/serve.py`) and by 6 new unit checks |
| 20 | `_headers` is generated (`tools/build-headers.py`): exactly one policy per page path; added `upgrade-insecure-requests` | **Verified** (unit test) |
| 21 | Service worker: pages cached per address (the old one stored every page as the home page, which would have broken the new pages offline); app files cached | Written; offline behaviour **not tested** |
| 22 | Speed: storefront HTML 125 KB to 55 KB; scripts cached for a year; touch targets in the footer raised to 44 px; favicon added | Local throttled-phone test (mock backend, no fonts): LCP about 1.08 s to 0.83 s, FCP not improved (noise-level). **Real Lighthouse not re-run: do it after deploying** |
| 23 | Opening `index.html` straight from a file no longer works (strict policy). Use `python3 tests/serve.py` | Deliberate trade-off |

## Still NOT done (do not assume)
- Trusted Types (Lighthouse's second CSP item) needs the storefront's `innerHTML` rendering rewritten; not done. `style-src 'unsafe-inline'` remains on the shop app, admin and policies page.
- Everything under "NOT done / NOT verified" in tranche 1: migration never executed, RLS matrix never executed, no per-role admin UI, no Turnstile, no backups, no penetration test. **No site can be promised "hack proof"**; this one has not been security-tested against a real database.
- Admin panel was not redesigned in this tranche. It already signs out after 15 minutes idle, keeps its token in session storage only, and has a strict policy.
- Owner items from tranche 1 are unchanged: seller details for policies, Cloudinary secrets, Google 2-step verification, domain spelling (clayxculture.in vs calyxculture), and **photo rights** (docs/IMAGES.md): the new pages reuse the same photos.
- Contrast and "identical links" items in the Lighthouse accessibility report were not individually located; the four new pages were built to 4.5:1 text contrast and 44 px targets but not audited with a tool.

---
# Tranche 3 (2026-11-17): expected delivery date and small details

| # | Change | Status |
|---|---|---|
| 24 | **Expected delivery date** on every product page (customer enters a pincode, sees "Arrives between Thu, 19 Nov and Sat, 21 Nov") and live at checkout as soon as the pincode is typed. The pincode is remembered on that device. Owner edits the days in **Admin > Settings > Expected delivery dates** (days to dispatch, skip Sundays, three zones: Kashmir valley 190 to 193, rest of J&K and Ladakh, rest of India) | **Verified**: `tests/e2e_delivery.py` (date maths incl. Sunday cases, bad pincodes, remembered pincode, custom settings, checkout) |
| 25 | Product page: "You save ₹X (Y% off)", "Sold out for now" with a "Tell me when it's back" WhatsApp button, shipping fee and free-shipping line, three trust lines (Cash on Delivery, order tracking, real people on WhatsApp) | **Verified** (same test) |
| 26 | Google product data now includes shipping cost, delivery time and "returns not permitted" | Written; not checked in Google's Rich Results Test |
| 27 | Branded 404 and offline pages, app-install shortcuts (Shop, Our store, Contact), `/.well-known/security.txt`, iPhone home-screen title | 404 **verified**; others written |

**The delivery days are my starting assumptions, not your courier's real times:** dispatch 1 day, Kashmir valley 1 to 3 days, rest of J&K and Ladakh 2 to 4, rest of India 4 to 7, Sundays skipped. Check them in Admin > Settings before launch. The estimate says "our team confirms the exact time on WhatsApp", matching your FAQ. It does not check whether a pincode is serviceable.

**Database:** if you have not run `20261116_01_security_hardening.sql` yet, nothing extra is needed (it now allows the `delivery` setting). If you already ran it, also run `supabase/migrations/20261117_01_delivery_setting.sql`. Until then the site simply uses the starting values above.

---
# Update 2026-11-17: name changed to calyxculture

The owner confirmed the name and username: the brand is written **calyxculture** everywhere (page titles, wordmark, footers, WhatsApp messages, policies, admin, structured data) and the Instagram username is **calyxculture_** (instagram.com/calyxculture_). This settles item 16 for the brand and the Instagram name.

- Live database: run `supabase/migrations/20261117_03_brand_calyxculture.sql` once in Supabase > SQL Editor. Until then the shop reads the old brand and Instagram link from the database.
- Deliberately unchanged: the domain `clayxculture.in` and the support email (real addresses you own), the image folders `calyx/p` and `calyx/r` (changing them would break every photo already uploaded), and the sample coupon `CALYX10`.
- `archive/v1-first-preview.html` is the frozen first preview and was not edited.

