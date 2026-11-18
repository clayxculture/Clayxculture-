# Security notes

## What is public on purpose
The Supabase project URL and the `sb_publishable_...` key in `site/` are public by design (every Supabase website exposes them). They give no power by themselves; the database rules decide what each visitor may do.

## What protects the data
- Row level security on every table. Visitors can read only published products, active FAQ, store settings and approved reviews. Orders, customers' messages, coupons, the audit log and unapproved reviews cannot be read.
- Visitors cannot write directly. They can only call a few functions: place_order, track_order, check_coupon, get_reviews, review_check, submit_review, home_extras.
- `place_order` recomputes price, shipping, coupon and stock on the server, validates every field, requires policy consent, blocks duplicates, rate-limits per phone, scores risk, and either places, holds for verification, or refuses.
- Admin = Google login + email on the `admin_emails` list. 15-minute idle sign-out. The audit log records the signed-in email; the browser cannot forge it. Order history and the audit log cannot be edited or deleted.
- Headers (`site/_headers`): strict Content-Security-Policy per page, HSTS, no framing, nosniff, same-origin policies. The admin page has no inline scripts.
- Uploads are signed by edge functions that check the caller first (admin, or a delivered order for a review photo).

## Secrets (never commit)
Supabase secrets: CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET. Nothing else secret exists in this repo. Turn on 2-step verification on the admin Google account, Supabase, Netlify/Cloudflare, Cloudinary and the domain registrar.

## Known limits
No bot challenge yet, no per-IP limits, no online payments, admin roles are all-or-nothing. See ROADMAP.md.
