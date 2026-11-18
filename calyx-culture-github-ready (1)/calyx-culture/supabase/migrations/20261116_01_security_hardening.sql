-- =====================================================================================
-- Calyx Culture: security hardening migration 20261116_01
-- STATUS: WRITTEN BUT NOT EXECUTED. No Postgres was available when this was authored, so
--         it has never been run. Apply ONLY to a staging Supabase project first, run
--         supabase/tests/rls_matrix.sql, then promote. Never run on production unreviewed.
-- Designed to be re-runnable (drop ... if exists / create or replace / if not exists).
-- Rollback: see docs/ROLLBACK.md (restore the pre-migration pg_dump; this file drops policies).
-- =====================================================================================
begin;

-- ---------- 1. Roles and permission matrix (server-side RBAC) ----------
alter table public.admin_emails add column if not exists role text not null default 'owner';
alter table public.admin_emails drop constraint if exists admin_emails_role_check;
alter table public.admin_emails add constraint admin_emails_role_check
  check (role in ('owner','super_admin','product_manager','order_manager','customer_support','content_manager'));
-- Existing rows become 'owner' (column default), so nobody loses access.

create table if not exists public.role_permissions (role text not null, perm text not null, primary key (role, perm));
insert into public.role_permissions(role, perm) values
 ('owner','*'),
 ('super_admin','products.read'),('super_admin','products.write'),('super_admin','orders.read'),('super_admin','orders.write'),
 ('super_admin','coupons.write'),('super_admin','content.write'),('super_admin','settings.write'),('super_admin','reviews.moderate'),
 ('super_admin','contacts.read'),('super_admin','contacts.write'),('super_admin','blocklist.write'),('super_admin','audit.read'),('super_admin','uploads.product'),
 ('product_manager','products.read'),('product_manager','products.write'),('product_manager','uploads.product'),
 ('order_manager','orders.read'),('order_manager','orders.write'),('order_manager','products.read'),('order_manager','blocklist.write'),
 ('customer_support','orders.read'),('customer_support','contacts.read'),('customer_support','contacts.write'),
 ('content_manager','content.write'),('content_manager','settings.content'),('content_manager','uploads.product')
on conflict do nothing;

create or replace function public.admin_role() returns text language sql stable security definer set search_path = '' as $$
  select a.role from public.admin_emails a
   where lower(a.email) = lower(coalesce(auth.jwt()->>'email',''))
     and coalesce(auth.jwt()->'app_metadata'->>'provider','') = 'google' $$;

create or replace function public.has_perm(p text) returns boolean language sql stable security definer set search_path = '' as $$
  select exists(select 1 from public.role_permissions rp
                 where rp.role = public.admin_role() and rp.perm in ('*', p)) $$;

-- ---------- 2. Rate-limit infrastructure (internal only) ----------
create table if not exists public.rate_events (
  id bigint generated always as identity primary key,
  bucket text not null, k text not null, created_at timestamptz not null default now());
create index if not exists rate_events_lookup_idx on public.rate_events(bucket, k, created_at);

create or replace function public.client_ip() returns text language sql stable set search_path = '' as $$
  select coalesce(
    nullif(current_setting('request.headers', true), '')::jsonb ->> 'cf-connecting-ip',
    nullif(split_part(coalesce(nullif(current_setting('request.headers', true), '')::jsonb ->> 'x-forwarded-for', ''), ',', 1), ''),
    'unknown') $$;

create or replace function public.rate_count(b text, key text, win interval) returns integer
language sql stable security definer set search_path = '' as $$
  select count(*)::int from public.rate_events where bucket = b and k = key and created_at > now() - win $$;

create or replace function public.rate_hit(b text, key text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.rate_events(bucket, k) values (b, key);
  if random() < 0.01 then delete from public.rate_events where created_at < now() - interval '3 days'; end if;
end $$;

-- ---------- 3. Review photo tokens (single-use, bound to order + product) ----------
create table if not exists public.upload_tokens (
  public_id text primary key check (public_id ~ '^calyx/r/[A-Za-z0-9_-]+$'),
  order_id bigint not null references public.orders(id) on delete cascade,
  product_id bigint not null references public.products(id) on delete cascade,
  created_at timestamptz not null default now(), used boolean not null default false);
create index if not exists upload_tokens_order_idx on public.upload_tokens(order_id, created_at);

-- Eligibility without any rate limiting; internal helper, not callable by clients.
create or replace function public._review_eligibility(c text, ph text, pid bigint) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare o public.orders%rowtype; lim int; ph_ok boolean;
begin
  select * into o from public.orders where code = upper(trim(c)) and phone = trim(ph) and status = 'delivered';
  if not found then return jsonb_build_object('ok', false, 'photo', false); end if;
  if not exists(select 1 from jsonb_array_elements(o.items) i where (i->>'id')::bigint = pid)
     or exists(select 1 from public.reviews where order_id = o.id and product_id = pid)
  then return jsonb_build_object('ok', false, 'photo', false); end if;
  select (value #>> '{}')::int into lim from public.store_settings where key = 'review_photo_limit';
  lim := coalesce(lim, 20);
  ph_ok := (select count(*) from public.reviews where product_id = pid and image_url is not null and status <> 'rejected') < lim;
  return jsonb_build_object('ok', true, 'photo', ph_ok);
end $$;

create or replace function public.review_check(c text, ph text, pid bigint) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare ip text := public.client_ip(); cc text := upper(left(trim(coalesce(c,'')), 20)); r jsonb;
begin
  if public.rate_count('rev_fail_ip', ip, interval '1 hour') >= 20 or public.rate_count('rev_fail_code', cc, interval '1 hour') >= 40
  then raise exception 'rate_limited'; end if;
  r := public._review_eligibility(c, ph, pid);
  if (r->>'ok')::boolean is not true then perform public.rate_hit('rev_fail_ip', ip); perform public.rate_hit('rev_fail_code', cc); end if;
  return r;
end $$;

-- Called ONLY by the sign-review-upload edge function with the service role.
create or replace function public.issue_review_upload(c text, ph text, pid bigint, ip text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare cc text := upper(left(trim(coalesce(c,'')), 20)); r jsonb; o public.orders%rowtype; pub text;
begin
  ip := left(coalesce(nullif(ip,''), 'unknown'), 64);
  if public.rate_count('rev_fail_ip', ip, interval '1 hour') >= 20 or public.rate_count('rev_fail_code', cc, interval '1 hour') >= 40
  then raise exception 'rate_limited'; end if;
  r := public._review_eligibility(c, ph, pid);
  if (r->>'ok')::boolean is not true or (r->>'photo')::boolean is not true then
    perform public.rate_hit('rev_fail_ip', ip); perform public.rate_hit('rev_fail_code', cc);
    raise exception 'not_allowed';
  end if;
  select * into o from public.orders where code = cc and phone = trim(ph);
  if (select count(*) from public.upload_tokens where order_id = o.id and created_at > now() - interval '24 hours') >= 3
  then raise exception 'rate_limited'; end if;
  pub := 'calyx/r/' || replace(gen_random_uuid()::text, '-', '');
  insert into public.upload_tokens(public_id, order_id, product_id) values (pub, o.id, pid);
  return jsonb_build_object('public_id', pub);
end $$;

create or replace function public.submit_review(c text, ph text, pid bigint, rt integer, bd text, img text default null)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare o public.orders%rowtype; chk jsonb; nm text; ip text := public.client_ip(); cc text := upper(left(trim(coalesce(c,'')), 20));
begin
  if public.rate_count('rev_fail_ip', ip, interval '1 hour') >= 20 or public.rate_count('rev_fail_code', cc, interval '1 hour') >= 40
  then raise exception 'rate_limited'; end if;
  chk := public._review_eligibility(c, ph, pid);
  if (chk->>'ok')::boolean is not true then
    perform public.rate_hit('rev_fail_ip', ip); perform public.rate_hit('rev_fail_code', cc); raise exception 'not_eligible'; end if;
  select * into o from public.orders where code = cc and phone = trim(ph);
  img := nullif(img, '');
  if img is not null then
    if (chk->>'photo')::boolean is not true then raise exception 'photo_limit'; end if;
    -- the photo must be one this customer was issued for THIS order and product, and only once
    update public.upload_tokens set used = true
     where public_id = img and order_id = o.id and product_id = pid and not used and created_at > now() - interval '1 day';
    if not found then raise exception 'invalid_photo'; end if;
  end if;
  nm := split_part(trim(o.name), ' ', 1);
  if split_part(trim(o.name), ' ', 2) <> '' then nm := nm || ' ' || left(split_part(trim(o.name), ' ', 2), 1) || '.'; end if;
  insert into public.reviews(product_id, order_id, name, rating, body, image_url) values (pid, o.id, left(nm, 40), rt, trim(bd), img);
  return jsonb_build_object('ok', true);
end $$;

-- ---------- 4. Order tracking: failed-attempt limits, lockout, suspicious-activity log ----------
-- Order codes (CC-10482) stay sequential on purpose: the storefront, chat helper and printed
-- customer messages depend on that format. The phone number is the second factor, so
-- brute force is blocked by limits. A wrong code and a wrong phone behave identically.
create or replace function public.track_order(c text, ph text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare o public.orders%rowtype; ip text := public.client_ip(); cc text := upper(left(trim(coalesce(c,'')), 20)); n int;
begin
  if public.rate_count('trk_fail_ip', ip, interval '1 hour') >= 20 or public.rate_count('trk_fail_code', cc, interval '1 hour') >= 40
  then raise exception 'rate_limited'; end if;
  select * into o from public.orders where code = cc and phone = trim(ph);
  if not found then
    perform public.rate_hit('trk_fail_ip', ip); perform public.rate_hit('trk_fail_code', cc);
    n := public.rate_count('trk_fail_ip', ip, interval '1 hour');
    if n = 20 then insert into public.audit_log(actor, action, detail) values (null, 'track_lockout', jsonb_build_object('ip', ip, 'last_code', cc)); end if;
    return null;
  end if;
  return jsonb_build_object('code', o.code, 'status', o.status, 'courier', o.courier, 'tracking_id', o.tracking_id,
    'events', (select coalesce(jsonb_agg(jsonb_build_object('status', e.status, 'at', e.created_at, 'note', e.note) order by e.created_at), '[]'::jsonb)
                 from public.order_events e where e.order_id = o.id));
end $$;

-- ---------- 5. Coupons: honour expiry, rate limit the oracle ----------
create or replace function public.check_coupon(c text) returns integer language plpgsql security definer set search_path = '' as $$
declare ip text := public.client_ip(); r integer;
begin
  if public.rate_count('cpn_ip', ip, interval '10 minutes') >= 30 then raise exception 'rate_limited'; end if;
  perform public.rate_hit('cpn_ip', ip);
  select percent into r from public.coupons
   where code = upper(trim(c)) and active and (max_uses is null or uses < max_uses) and (expires_at is null or expires_at > now());
  return r;
end $$;

-- ---------- 6. place_order: atomic coupon use, null-colour bug, deterministic lock order ----------
create or replace function public.place_order(p jsonb) returns jsonb language plpgsql security definer set search_path = '' as $$
declare it jsonb; pr public.products%rowtype; sub int := 0; disc int := 0; sh int := 0; fee int := 0; thr int; tot int; lines jsonb := '[]'; q int;
 cp public.coupons%rowtype; oid bigint; ex public.orders%rowtype; cn text; nm text; ph text; ad text; pay text; pin text; totq int := 0; ver text;
 rs int := 0; flags jsonb := '[]'; stt text := 'placed'; rev int; rej int; capc int; prior int; bad int; delivered int; bulk boolean := false; fv boolean := false; cpok boolean := false;
begin
  if p->>'idem' is not null then select * into ex from public.orders where idem = p->>'idem'; if found then return jsonb_build_object('code', ex.code, 'total', ex.total, 'status', ex.status); end if; end if;
  nm := trim(coalesce(p->>'name','')); ph := coalesce(p->>'phone',''); ad := trim(coalesce(p->>'address','')); pin := coalesce(p->>'pincode',''); pay := coalesce(p->>'payment','');
  if length(nm) not between 2 and 60 or ph !~ '^[6-9][0-9]{9}$' or length(ad) not between 15 and 250 or pin !~ '^[1-9][0-9]{5}$' or pay not in ('Cash on Delivery','Order via WhatsApp') then raise exception 'invalid_details'; end if;
  select value #>> '{}' into ver from public.store_settings where key = 'policy_version'; ver := coalesce(ver, '2026-11-14.1');
  if coalesce(p->>'policy','') <> ver then raise exception 'consent_required'; end if;
  if jsonb_typeof(p->'items') <> 'array' or jsonb_array_length(p->'items') not between 1 and 20 then raise exception 'invalid_items'; end if;
  if (select count(*) from public.orders where phone = ph and created_at > now() - interval '1 hour') >= 3 or (select count(*) from public.orders where phone = ph and created_at > now() - interval '24 hours') >= 8 then raise exception 'rate_limited'; end if;
  if public.rate_count('ord_ip', public.client_ip(), interval '1 hour') >= 15 then raise exception 'rate_limited'; end if;
  perform public.rate_hit('ord_ip', public.client_ip());
  -- lock products in id order so two concurrent checkouts cannot deadlock
  for it in select value from jsonb_array_elements(p->'items') order by (value->>'id')::bigint loop
    q := coalesce((it->>'qty')::int, 0); if q < 1 or q > 10 then raise exception 'invalid_qty'; end if;
    totq := totq + q; if totq > 20 then raise exception 'invalid_qty'; end if; if q >= 4 then bulk := true; end if;
    if coalesce(it->>'size','') not in ('S','M','L','XL') then raise exception 'invalid_size'; end if;
    select * into pr from public.products where id = (it->>'id')::bigint and status = 'published' for update;
    if not found then raise exception 'unavailable'; end if;
    if it->>'color' is null or not ((it->>'color') = any(pr.colors)) then raise exception 'invalid_color'; end if;   -- null colour used to slip through
    sub := sub + pr.price * q;
    lines := lines || jsonb_build_object('id', pr.id, 'name', pr.name, 'color', left(it->>'color', 30), 'size', it->>'size', 'qty', q, 'price', pr.price);
  end loop;
  select * into ex from public.orders where phone = ph and address = ad and items = lines and status <> 'cancelled' and created_at > now() - interval '10 minutes' order by id desc limit 1;
  if found then return jsonb_build_object('code', ex.code, 'total', ex.total, 'status', ex.status); end if;
  for it in select value from jsonb_array_elements(lines) order by (value->>'id')::bigint loop
    q := (it->>'qty')::int;
    update public.products set stock = stock - q where id = (it->>'id')::bigint and stock is not null and stock >= q;
    if not found and exists(select 1 from public.products where id = (it->>'id')::bigint and stock is not null) then raise exception 'out_of_stock'; end if;
  end loop;
  if nullif(p->>'coupon','') is not null then
    select * into cp from public.coupons where code = upper(trim(p->>'coupon')) and active and sub >= coalesce(min_cart, 0) and (expires_at is null or expires_at > now());
    if found and not exists(select 1 from public.orders where phone = ph and coupon = cp.code and status not in ('cancelled')) then
      -- atomic: the limit is checked inside the UPDATE, so concurrent orders cannot exceed max_uses
      update public.coupons set uses = uses + 1 where code = cp.code and (max_uses is null or uses < max_uses);
      cpok := found;
      if cpok then disc := round(sub * cp.percent / 100.0); end if;
    end if;
  end if;
  select coalesce((value #>> '{}')::int, 1999) into thr from public.store_settings where key = 'free_ship_threshold';
  select coalesce((value #>> '{}')::int, 99) into fee from public.store_settings where key = 'shipping_fee';
  if sub - disc < coalesce(thr, 1999) then sh := coalesce(fee, 99); end if;
  tot := sub - disc + sh;
  select count(*) into prior from public.orders where phone = ph and status <> 'cancelled';
  select count(*) into delivered from public.orders where phone = ph and status = 'delivered';
  select count(*) into bad from public.orders where phone = ph and status in ('cancelled','returned');
  if prior = 0 then rs := rs + 15; flags := flags || '"new_phone"'; end if;
  if pay = 'Cash on Delivery' then rs := rs + 10; flags := flags || '"cod"'; end if;
  if tot > 3000 then rs := rs + 15; flags := flags || '"high_value"'; end if;
  if bulk then rs := rs + 10; flags := flags || '"bulk_size"'; end if;
  if ph ~ '^([0-9])\1{9}$' or ph ~ '(0123456789|1234567890|9876543210)$' then rs := rs + 30; flags := flags || '"fake_phone"'; end if;
  if ad ~* '(.)\1{4,}' or ad ~* '\m(test|asdf|qwerty|dummy|fake)\M' or ad !~* '[aeiou]' then rs := rs + 30; flags := flags || '"bad_address"'; end if;
  if nm ~* '(.)\1{3,}' or nm ~* '^(test|asdf|qwerty|abc|xyz)\M' then rs := rs + 30; flags := flags || '"bad_name"'; end if;
  if bad > 0 then rs := rs + least(60, 20 * bad); flags := flags || '"past_cancel_return"'; end if;
  select coalesce((value #>> '{}')::int, 2500) into capc from public.store_settings where key = 'cod_cap_first';
  if pay = 'Cash on Delivery' and tot > coalesce(capc, 2500) and delivered = 0 then fv := true; flags := flags || '"cod_cap"'; end if;
  if exists(select 1 from public.blocklist where kind = 'phone' and value = ph) then rs := rs + 100; flags := flags || '"blocklist"'; end if;
  select coalesce((value #>> '{}')::int, 30) into rev from public.store_settings where key = 'risk_review';
  select coalesce((value #>> '{}')::int, 60) into rej from public.store_settings where key = 'risk_reject';
  if rs > coalesce(rej, 60) then raise exception 'order_rejected'; elsif rs >= coalesce(rev, 30) or fv then stt := 'needs_verification'; end if;
  insert into public.orders(user_id, name, phone, address, pincode, payment, items, subtotal, discount, shipping, total, coupon, idem, status, risk_score, risk_flags, policy_version, policy_accepted_at)
  values (auth.uid(), left(nm, 60), ph, left(ad, 250), pin, pay, lines, sub, disc, sh, tot, case when disc > 0 then cp.code end, p->>'idem', stt, rs, flags, ver, now()) returning id into oid;
  cn := 'CC-' || (10000 + oid); update public.orders set code = cn where id = oid;
  insert into public.order_events(order_id, status, note) values (oid, stt, case when stt = 'placed' then 'Order placed' else 'Order placed. We will verify it on WhatsApp before dispatch.' end);
  return jsonb_build_object('code', cn, 'total', tot, 'subtotal', sub, 'discount', disc, 'shipping', sh, 'status', stt);
end $$;

-- ---------- 7. set_order_status: permission check, coupon restored on cancel ----------
create or replace function public.set_order_status(oid bigint, st text, cr text default null, trk text default null, nt text default null)
returns void language plpgsql security definer set search_path = '' as $$
declare o public.orders%rowtype; it jsonb; nxt text[];
begin
  if not public.has_perm('orders.write') then raise exception 'forbidden'; end if;
  select * into o from public.orders where id = oid for update; if not found then raise exception 'not_found'; end if;
  nxt := case o.status when 'placed' then array['needs_verification','confirmed','cancelled'] when 'needs_verification' then array['confirmed','cancelled'] when 'confirmed' then array['packed','cancelled'] when 'packed' then array['shipped','cancelled'] when 'shipped' then array['out_for_delivery','delivered','returned'] when 'out_for_delivery' then array['delivered','returned'] when 'delivered' then array['returned'] else array[]::text[] end;
  if st <> o.status and not (st = any(nxt)) then raise exception 'invalid_transition'; end if;
  if st in ('cancelled','returned') and st <> o.status and coalesce(trim(nt),'') = '' then raise exception 'reason_required'; end if;
  if st in ('cancelled','returned') and o.status not in ('cancelled','returned') then
    for it in select value from jsonb_array_elements(o.items) loop
      update public.products set stock = stock + (it->>'qty')::int where id = (it->>'id')::bigint and stock is not null; end loop;
    if st = 'cancelled' and o.coupon is not null then update public.coupons set uses = greatest(uses - 1, 0) where code = o.coupon; end if;
  end if;
  update public.orders set status = st, courier = coalesce(cr, courier), tracking_id = coalesce(trk, tracking_id),
    verified_at = case when o.status = 'needs_verification' and st = 'confirmed' then now() else verified_at end,
    verified_by = case when o.status = 'needs_verification' and st = 'confirmed' then auth.jwt()->>'email' else verified_by end where id = oid;
  if st <> o.status or nt is not null then insert into public.order_events(order_id, status, note) values (oid, st, nt); end if;
  insert into public.audit_log(actor, action, detail) values (null, 'order_status', jsonb_build_object('order', o.code, 'from', o.status, 'to', st, 'role', public.admin_role()));
end $$;

-- ---------- 8. Empty search_path on every remaining SECURITY DEFINER / trigger function ----------
alter function public.is_admin() set search_path = '';
alter function public.block_mutation() set search_path = '';
alter function public.audit_actor() set search_path = '';
alter function public.contact_rate_limit() set search_path = '';
alter function public.orders_rate_limit() set search_path = '';
alter function public.get_reviews(bigint) set search_path = '';
alter function public.home_extras() set search_path = '';

-- ---------- 9. Row level security: policies rewritten around has_perm() ----------
alter table public.role_permissions enable row level security;
alter table public.rate_events enable row level security;      -- no policies: unreadable by clients
alter table public.upload_tokens enable row level security;    -- no policies: unreadable by clients

do $$ declare r record; begin
  for r in select schemaname, tablename, policyname from pg_policies where schemaname = 'public'
    and tablename in ('admin_emails','audit_log','banners','blocklist','contact_messages','coupons','faq','orders','order_events','products','profiles','reviews','store_settings','role_permissions')
  loop execute format('drop policy %I on %I.%I', r.policyname, r.schemaname, r.tablename); end loop;
end $$;

create policy admin_emails_owner     on public.admin_emails     for all    to authenticated using (public.has_perm('admins.manage')) with check (public.has_perm('admins.manage'));
create policy role_perm_read         on public.role_permissions for select to authenticated using (public.is_admin());
create policy audit_read             on public.audit_log        for select to authenticated using (public.has_perm('audit.read'));
create policy audit_insert           on public.audit_log        for insert to authenticated with check (public.is_admin());
create policy banners_read           on public.banners          for select to anon, authenticated using (active or public.has_perm('content.write'));
create policy banners_write          on public.banners          for all    to authenticated using (public.has_perm('content.write')) with check (public.has_perm('content.write'));
create policy faq_read               on public.faq              for select to anon, authenticated using (active or public.has_perm('content.write'));
create policy faq_write              on public.faq              for all    to authenticated using (public.has_perm('content.write')) with check (public.has_perm('content.write'));
create policy blocklist_all          on public.blocklist        for all    to authenticated using (public.has_perm('blocklist.write')) with check (public.has_perm('blocklist.write'));
create policy contact_insert         on public.contact_messages for insert to anon, authenticated with check (true);
create policy contact_read           on public.contact_messages for select to authenticated using (public.has_perm('contacts.read'));
create policy contact_update         on public.contact_messages for update to authenticated using (public.has_perm('contacts.write')) with check (public.has_perm('contacts.write'));
create policy contact_delete         on public.contact_messages for delete to authenticated using (public.has_perm('contacts.write'));
create policy coupons_all            on public.coupons          for all    to authenticated using (public.has_perm('coupons.write')) with check (public.has_perm('coupons.write'));
-- Customers can no longer read orders/events through the REST API (they track via track_order).
-- This also stops them seeing risk_score, risk_flags, notes and the verifying admin's email.
create policy orders_read            on public.orders           for select to authenticated using (public.has_perm('orders.read'));
create policy events_read            on public.order_events     for select to authenticated using (public.has_perm('orders.read'));
create policy products_read          on public.products         for select to anon, authenticated using (status = 'published' or public.has_perm('products.read'));
create policy products_write         on public.products         for all    to authenticated using (public.has_perm('products.write')) with check (public.has_perm('products.write'));
create policy profile_own            on public.profiles         for select to authenticated using (id = (select auth.uid()) or public.has_perm('orders.read'));
create policy profile_update_own     on public.profiles         for update to authenticated using (id = (select auth.uid())) with check (id = (select auth.uid()));
create policy reviews_all            on public.reviews          for all    to authenticated using (public.has_perm('reviews.moderate')) with check (public.has_perm('reviews.moderate'));
-- Settings: anonymous visitors see ONLY the keys the storefront needs. Fraud thresholds stay private.
create policy settings_public_read   on public.store_settings   for select to anon, authenticated
  using (key in ('brand','whatsapp','phone','address','instagram','announcement','notice','welcome','free_ship_threshold','shipping_fee','sizes',
                 'policy_version','seller','stores','reels','hero_video','ig_gallery','site_images','delivery'));
create policy settings_admin_read    on public.store_settings   for select to authenticated using (public.has_perm('settings.write') or public.has_perm('settings.content'));
create policy settings_write         on public.store_settings   for all    to authenticated
  using (public.has_perm('settings.write') or (public.has_perm('settings.content') and key in ('announcement','notice','welcome','hero_video','ig_gallery','reels','site_images')))
  with check (public.has_perm('settings.write') or (public.has_perm('settings.content') and key in ('announcement','notice','welcome','hero_video','ig_gallery','reels','site_images')));

-- ---------- 10. Table privileges: least privilege (RLS is the second lock, not the only one) ----------
revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
alter default privileges in schema public revoke all on tables from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;

grant select on public.banners, public.faq, public.products, public.store_settings to anon, authenticated;
grant insert (name, phone, message) on public.contact_messages to anon, authenticated;   -- cannot set 'handled' or 'created_at'
grant select, insert, update, delete on public.banners, public.faq, public.blocklist, public.coupons, public.products, public.reviews, public.store_settings to authenticated;
grant select, update, delete on public.contact_messages to authenticated;
grant select on public.orders, public.order_events, public.admin_emails, public.role_permissions to authenticated;
grant insert, update, delete on public.admin_emails to authenticated;
grant select, insert on public.audit_log to authenticated;
grant select on public.profiles to authenticated;
grant update (name) on public.profiles to authenticated;
grant usage on all sequences in schema public to authenticated;
grant usage on sequence public.contact_messages_id_seq to anon;

-- ---------- 11. Function execute grants ----------
revoke execute on all functions in schema public from public, anon, authenticated;
grant execute on function public.is_admin(), public.has_perm(text), public.admin_role() to anon, authenticated;
grant execute on function public.place_order(jsonb), public.track_order(text,text), public.check_coupon(text), public.get_reviews(bigint),
  public.review_check(text,text,bigint), public.submit_review(text,text,bigint,integer,text,text), public.home_extras() to anon, authenticated;
grant execute on function public.set_order_status(bigint,text,text,text,text) to authenticated;
grant execute on function public.issue_review_upload(text,text,bigint,text) to service_role;

commit;
