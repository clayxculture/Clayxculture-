# Razorpay readiness

**Status: NOT enabled.** The store takes Cash on Delivery and WhatsApp orders only. Nothing in `site/` talks to Razorpay yet, and the security headers deliberately do not allow it. Turning payments on is a server-side job, not a switch: do not paste Razorpay's sample code into the site.

## What must be built (in this order, test mode first)
1. **Create the order on the server** (a Supabase edge function). The amount in paise is computed there from database prices, coupon and shipping. Never take an amount from the browser. Store the Razorpay `order_id` on your order row.
2. **Open Checkout in the browser** with only the public `key_id` and that `order_id`.
3. **Verify on the server**: HMAC-SHA256 of `order_id|payment_id` with the key secret must equal the signature (constant-time compare).
4. **Webhook as the source of truth** (`payment.captured`, `payment.failed`, refunds): verify `X-Razorpay-Signature` against the raw body with the webhook secret; be idempotent (same event twice changes nothing); mark an order paid only if amount, currency and status match the order.
5. **Unpaid orders expire** and release stock; **refunds** only from the admin panel with a permission check.
6. **Secrets** (`key_secret`, webhook secret) only as Supabase function secrets, never in `site/`. Start with `rzp_test_` keys; live keys need Razorpay account activation (KYC).

## Header changes to make only when step 2 exists
Edit `site/_headers` (every page block, and update `tests/unit/static.test.mjs` to match). Confirm hosts against Razorpay's current docs, they change:
- `script-src` add `https://checkout.razorpay.com`
- `frame-src` add `https://api.razorpay.com` (and `https://checkout.razorpay.com` if the docs ask)
- `connect-src` add `https://api.razorpay.com` and `https://lumberjack.razorpay.com`
- `img-src` add the Razorpay image host named in the docs
- `Permissions-Policy: payment=()` blocks the browser payment API; delegate it to the Razorpay origins if Google Pay or UPI buttons fail
- `Cross-Origin-Opener-Policy: same-origin` can break popup-based bank pages; change to `same-origin-allow-popups` only if test mode shows that failure

## Must pass before real money
Wrong signature rejected; tampered amount rejected; webhook replay changes nothing; payment after the order was cancelled is refunded or flagged; double-click on Pay creates one order; test-mode run with UPI, card and netbanking, success and failure; `supabase/tests/rls_matrix.sql` run on staging (still never executed, see AUDIT-REPORT.md).
