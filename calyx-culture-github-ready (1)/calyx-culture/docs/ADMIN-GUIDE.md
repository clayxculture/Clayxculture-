# Admin guide

## Log in
1. Open `https://YOUR-SITE/admin/` (nobody links to it).
2. Tap **Continue with Google** and use an approved Google account.
3. You are signed out after 15 minutes without activity. Sign in again.

## Who can log in, and how many
Only Google accounts listed in the `admin_emails` table (Supabase > Table Editor > admin_emails > Insert row). There is no limit on how many. Today there is one: the owner. Everyone else, including other Google users, is refused by the database itself.
Add a staff member: insert their Gmail address. Remove: delete the row. Every admin has full admin powers (roles are on the roadmap).

## Why strangers cannot change prices
The admin page only holds a public key. Every change is checked by the database: a request is accepted only if it carries a real Google login whose email is in `admin_emails`. Prices, stock, orders and settings are protected by that check, not by hiding the page. Order status changes also follow fixed steps, cannot be edited after the fact, and are logged with the signed-in email.

## Daily work
- **Orders:** tap an order, set the next status, add courier and tracking ID, optional message to the customer (shown in tracking). To cancel or return you must give a reason; stock goes back automatically. Orders marked **Needs verification** wait for the customer to message you on WhatsApp from the same number; then tap **Verified on WhatsApp**.
- **Products:** Add product, fill name, category (type a new one to create a category page), price, old price, stock (blank = not tracked), colours, description, photo. Status Draft hides it; Archived retires it.
- **Samples clear themselves:** each real product you add hides one sample; with 10 real products all samples are gone. You can also use Settings > Delete sample products.
- **Offers:** delay notice, welcome pop-up, coupons, reviews to approve, Instagram reels, hero photo and video, chat answers, customer messages.
- **Settings:** shipping fee and free-shipping amount, stores, seller details (fill every box), order safety levels, blocked numbers, backup and orders export.

## Capacity
Comfortable up to about 500 live products and tens of thousands of orders on the free plans. Images: Cloudinary free plan has 25 credits a month shared by storage and visitor downloads; check the dashboard monthly.
