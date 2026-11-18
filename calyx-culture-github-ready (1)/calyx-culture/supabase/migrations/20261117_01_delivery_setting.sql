-- Run this ONLY if you already ran 20261116_01_security_hardening.sql before this file existed.
-- It lets the storefront read the new "delivery" setting (expected delivery dates). Safe to run twice.
drop policy if exists settings_public_read on public.store_settings;
create policy settings_public_read   on public.store_settings   for select to anon, authenticated
  using (key in ('brand','whatsapp','phone','address','instagram','announcement','notice','welcome','free_ship_threshold','shipping_fee','sizes',
                 'policy_version','seller','stores','reels','hero_video','ig_gallery','site_images','delivery'));
insert into public.store_settings(key,value) values
('delivery','{"dispatch_days":1,"skip_sunday":true,"valley":[1,3],"jk":[2,4],"india":[4,7]}')
on conflict (key) do nothing;
