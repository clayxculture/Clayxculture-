#!/usr/bin/env python3
"""Writes site/_headers (security headers + one Content-Security-Policy per kind of page).

Why it is generated: Netlify merges every matching rule, so a single '/*' CSP would also apply to /admin and
the two policies would both be enforced. Instead each page path gets exactly one policy, written once here.
Run from the repo root:  python3 tools/build-headers.py
"""
import os
SUPA = 'https://wxroneyxnidxluxtxsdq.supabase.co'   # keep in sync with SB in site/assets/*.js and site/admin/admin.js
COMMON = ["Strict-Transport-Security: max-age=31536000; includeSubDomains",
          "X-Content-Type-Options: nosniff",
          "Referrer-Policy: strict-origin-when-cross-origin",
          "Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), browsing-topics=()",
          "X-Frame-Options: DENY",
          "Cross-Origin-Opener-Policy: same-origin",
          "Cross-Origin-Resource-Policy: same-origin"]
# Storefront (the shop app): scripts only from our own files. Inline styles are still allowed because the app sets style attributes.
APP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
       f"img-src 'self' data: https://res.cloudinary.com; connect-src 'self' {SUPA} https://api.cloudinary.com; media-src https://res.cloudinary.com; "
       "manifest-src 'self'; worker-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'; upgrade-insecure-requests")
# Standalone pages: no inline script and no inline styles at all.
STATIC = ("default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
          f"img-src 'self' data: https://res.cloudinary.com; connect-src 'self' {SUPA}; manifest-src 'self'; "
          "frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'; upgrade-insecure-requests")
# Legacy pages that still carry a <style> block.
LEGACY = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
          f"img-src 'self' data:; connect-src 'self' {SUPA}; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'; upgrade-insecure-requests")
ADMIN = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://res.cloudinary.com; "
         f"connect-src 'self' {SUPA} https://api.cloudinary.com; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'; upgrade-insecure-requests")
SWR = "Cache-Control: public, max-age=60, stale-while-revalidate=600"
out = ['/*'] + ['  ' + h for h in COMMON] + ['']
def block(paths, csp, extra=()):
    for p in paths:
        out.extend([p, f'  Content-Security-Policy: {csp}', *['  ' + x for x in extra], ''])
block(['/', '/index.html', '/shop', '/shop/*', '/search', '/product/*'], APP, [SWR])
block(['/about', '/about.html', '/stores', '/stores.html', '/contact', '/contact.html', '/faq', '/faq.html'], STATIC, [SWR])
block(['/policies.html', '/offline.html', '/404.html'], LEGACY)
block(['/admin/*'], ADMIN, ['X-Robots-Tag: noindex, nofollow', 'Cache-Control: no-store'])
out += ['/assets/*', '  Cache-Control: public, max-age=31536000, immutable', '',
        '/.well-known/security.txt', '  Content-Type: text/plain; charset=utf-8', '  Cache-Control: public, max-age=86400', '',
        '/sw.js', '  Cache-Control: no-cache', '',
        '/manifest.webmanifest', '  Cache-Control: public, max-age=86400', '',
        '/icon-*.png', '  Cache-Control: public, max-age=2592000', '',
        '/img/*', '  Cache-Control: public, max-age=31536000, immutable', '']
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site', '_headers'), 'w').write('\n'.join(out))
print('wrote site/_headers')
