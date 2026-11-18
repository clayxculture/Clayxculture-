-- Rename the brand to "calyxculture" and the Instagram username to calyxculture_ on the LIVE store.
-- Run once in Supabase > SQL Editor. Safe to run again.
-- Changes only display text (brand name, Instagram link, FAQ and store text). Image folders (calyx/p, calyx/r),
-- the domain and the support email are not touched.

update public.store_settings set value = '"calyxculture"' where key = 'brand';
update public.store_settings set value = '"https://www.instagram.com/calyxculture_/"' where key = 'instagram';

-- Store names, welcome pop-up, notices and any other saved text that still says "Calyx Culture" or the old handle.
update public.store_settings
   set value = replace(replace(replace(value::text, 'Calyx Culture', 'calyxculture'), 'instagram.com/clayxculture_', 'instagram.com/calyxculture_'), '@clayxculture_', '@calyxculture_')::jsonb
 where key not in ('brand', 'instagram')
   and (value::text like '%Calyx Culture%' or value::text like '%clayxculture\_%');

-- Chat answers (FAQ).
update public.faq
   set question = replace(question, 'Calyx Culture', 'calyxculture'),
       answer   = replace(replace(replace(answer, 'Calyx Culture', 'calyxculture'), 'instagram.com/clayxculture_', 'instagram.com/calyxculture_'), 'instagram.com/thecalyxwear', 'instagram.com/calyxculture_')
 where question like '%Calyx Culture%' or answer like '%Calyx Culture%' or answer like '%clayxculture\_%' or answer like '%instagram.com/thecalyxwear%';

-- Let customers find the "what is this brand" answer by typing the new name too.
update public.faq set keywords = keywords || ',calyxculture' where keywords ~ '(^|,)calyx(,|$)' and keywords !~ 'calyxculture';
