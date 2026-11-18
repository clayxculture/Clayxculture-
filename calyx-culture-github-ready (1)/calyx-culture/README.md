# calyxculture store

Streetwear store for calyxculture, Srinagar. Static website (no build step) + Supabase database + Cloudinary images.

```
site/        <- the website. Upload THIS folder to Netlify.
  index.html          storefront shell (home, shop, categories, search, product pages, bag, checkout, chat)
  about.html stores.html contact.html faq.html   real standalone pages (own HTML, own address, work without JavaScript)
  assets/             app.js (shop), pages.js + pages.css (the four pages), boot.js, account.js (customer Google login), home-reviews.js (real reviews on home), policies.js, notfound.js
  admin/              owner panel (index.html + admin.js)  ->  yourdomain/admin/
  policies.html offline.html 404.html sw.js manifest.webmanifest icons
  img/                optimised photos (WebP), see docs/IMAGES.md
  _headers _redirects security headers (generated) and page rewrites
supabase/    schema.sql, seed.sql, migrations/, functions/ (secure Cloudinary uploads)
tools/       build-pages.py (writes the 4 pages), build-headers.py (writes _headers), stamp.py (cache hashes)
docs/        ADMIN-GUIDE, SECURITY, LAUNCH-CHECKLIST, AUDIT-REPORT, ROADMAP, IMAGES
tests/       ./tests/run-all.sh (browser tests, strict security headers on) and node --test tests/unit/*.test.mjs
```

After editing anything in `site/assets/` run `python3 tools/stamp.py`; after editing `tools/build-pages.py` run it first, then stamp.

## Fastest way to try it (2 minutes)
1. Go to app.netlify.com, **Add new site, Deploy manually**, and drag the **`site`** folder in.
2. Open the link. The store works right away with your existing Supabase project (Cash on Delivery and WhatsApp orders).
3. To put it on GitHub first: push this whole folder, then in Netlify choose **Import from Git**. `netlify.toml` already points to `site/`.

Netlify is the tested host. Cloudflare Pages should work (it serves `about.html` at `/about` itself) but has not been tested. GitHub Pages is **not** suitable: it cannot do the page rewrites or security headers.

## Preview before hosting
The strict security policy (no inline scripts) means the site must be served from a web address, so double-clicking `index.html` no longer works. Run `python3 tests/serve.py` and open http://localhost:8077 . It applies the same headers and rewrites as Netlify. Google sign-in for the admin only works on the real hosted address.

## Before real customers
Follow `docs/LAUNCH-CHECKLIST.md`. The three must-do items: Google sign-in for the admin, the Cloudinary secrets for photo upload, and the seller details for the Policies page.

## Using a different Supabase project
Edit the two values near the top of `site/index.html` (`SB` and `KEY`), `site/admin/admin.js` (`SB` and `KEY`) and `site/policies.html`, run `supabase/schema.sql` then `supabase/seed.sql`, deploy the two functions in `supabase/functions/`, and update the URLs in `site/_headers`. The Supabase URL and publishable key are meant to be public. Never put a secret key in `site/`.
