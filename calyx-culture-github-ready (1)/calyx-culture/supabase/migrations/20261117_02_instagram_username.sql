-- Point the live store at the new Instagram page (clayxculture_).
-- Run once in Supabase > SQL Editor. Safe to run again.
update public.store_settings set value = '"https://www.instagram.com/clayxculture_/"' where key = 'instagram';
update public.faq set answer = 'Follow us on Instagram at instagram.com/clayxculture_.' where answer like '%instagram.com/thecalyxwear%';
