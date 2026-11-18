# Launch checklist

## A. Make the admin work (one time)
1. Google Cloud Console > APIs & Services > Credentials > Create OAuth client ID > Web application. Authorised redirect URI: `https://wxroneyxnidxluxtxsdq.supabase.co/auth/v1/callback`.
2. Supabase > Authentication > Providers > Google: paste the client ID and secret, enable.
3. Supabase > Authentication > URL Configuration: Site URL = your live site; Redirect URLs: add BOTH `https://YOUR-SITE/admin/` (owner login) and `https://YOUR-SITE/` (customer login), for the Netlify address and the final domain.
4. Supabase > Authentication > Providers: turn **off** email sign-ups so only Google works.
5. Supabase > Edge Functions > Secrets: add CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET (from the Cloudinary dashboard).
6. Open /admin/, sign in, check Orders, Products, Offers, Settings load.

## A2. Customer Google login
The account icon at the top uses the same Google provider as the admin. Once step A3 includes `https://YOUR-SITE/`, customers can sign in, see their orders, and orders they place while signed in are saved to their account. Test: sign in on a phone, place a COD order, open the account icon and check it is listed.

## A3. Reviews
The "What customers say" block on the home page shows only real, verified reviews (it stays hidden until at least 3 exist). Nothing is typed in by hand. Reviews appear after a customer with a delivered order submits one.

## B. Fill the legal details
Admin > Settings > Seller and policy details (14 boxes). Open /policies.html and check no yellow [FILL] remains. Have an accountant or lawyer review the Policies page, and answer the GST, registration and labelling questions. Confirm the domain spelling.

## C. Add real content
Add products with photos and stock. The samples disappear as you add them. Set shipping fee and free-shipping amount. Add stores. Upload a hero photo or video (optional). Add Instagram reels (optional).

## D. Test with real money-free orders
Place a COD order on a phone, see it in admin, move it through the statuses, track it on the site, cancel one (stock returns), place a high-value first COD order (it should say Needs verification), leave a review after marking an order delivered.

## E. Domain
Add `clayxculture.in` in Netlify (or Cloudflare Pages) and follow its DNS steps. Update the Supabase URL settings in A3. Submit `/sitemap.xml` in Google Search Console. Run pagespeed.web.dev and fix anything it flags.

## F. Keep it alive
Free Supabase projects pause after about a week with no activity; real traffic prevents this. Download a backup from Admin > Settings > Tools every week.
