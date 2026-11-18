-- calyxculture database schema (exported from the live project wxroneyxnidxluxtxsdq on 2026-11-15)
-- Run once in a fresh Supabase project: SQL Editor > New query > paste > Run.
-- Order: tables, constraints, indexes, functions, row-level security, policies, triggers, grants.

create table public.admin_emails (email text not null);
create table public.audit_log (id bigint generated always as identity not null, actor text, action text not null, detail jsonb, created_at timestamp with time zone default now());
create table public.banners (id bigint generated always as identity not null, eyebrow text, headline text not null, image_url text, cta_label text, cta_cat text, active boolean default true, sort integer default 0);
create table public.blocklist (id bigint generated always as identity not null, kind text not null default 'phone'::text, value text not null, reason text, created_at timestamp with time zone not null default now());
create table public.contact_messages (id bigint generated always as identity not null, name text not null, phone text, message text not null, created_at timestamp with time zone default now(), handled boolean not null default false);
create table public.coupons (code text not null, percent integer not null, min_cart integer default 0, max_uses integer, uses integer default 0, active boolean default true, is_demo boolean default false, expires_at timestamp with time zone);
create table public.faq (id bigint generated always as identity not null, question text not null, answer text not null, keywords text not null default ''::text, active boolean not null default true, sort integer default 0);
create table public.orders (id bigint generated always as identity not null, code text, user_id uuid, name text not null, phone text not null, address text not null, pincode text not null, payment text not null, items jsonb not null, subtotal integer not null, discount integer not null default 0, shipping integer not null default 0, total integer not null, coupon text, status text not null default 'placed'::text, courier text, tracking_id text, notes text, idem text, created_at timestamp with time zone default now(), risk_score integer not null default 0, risk_flags jsonb not null default '[]'::jsonb, policy_version text, policy_accepted_at timestamp with time zone, verified_at timestamp with time zone, verified_by text);
create table public.order_events (id bigint generated always as identity not null, order_id bigint not null, status text not null, note text, created_at timestamp with time zone default now());
create table public.products (id bigint generated always as identity not null, slug text not null, name text not null, category text not null, kind text not null default 'tee'::text, price integer not null, compare_at integer, badge text, colors text[] not null default '{}'::text[], image_url text, stock integer, status text not null default 'published'::text, is_demo boolean not null default false, sort integer default 0, created_at timestamp with time zone default now(), description text);
create table public.profiles (id uuid not null, email text, name text, created_at timestamp with time zone default now());
create table public.reviews (id bigint generated always as identity not null, product_id bigint not null, order_id bigint not null, name text not null, rating integer not null, body text not null, image_url text, status text not null default 'pending'::text, created_at timestamp with time zone not null default now());
create table public.store_settings (key text not null, value jsonb not null);

alter table public.admin_emails add constraint admin_emails_pkey PRIMARY KEY (email);
alter table public.audit_log add constraint audit_log_pkey PRIMARY KEY (id);
alter table public.banners add constraint banners_pkey PRIMARY KEY (id);
alter table public.blocklist add constraint blocklist_pkey PRIMARY KEY (id);
alter table public.contact_messages add constraint contact_messages_pkey PRIMARY KEY (id);
alter table public.coupons add constraint coupons_pkey PRIMARY KEY (code);
alter table public.faq add constraint faq_pkey PRIMARY KEY (id);
alter table public.order_events add constraint order_events_pkey PRIMARY KEY (id);
alter table public.orders add constraint orders_pkey PRIMARY KEY (id);
alter table public.products add constraint products_pkey PRIMARY KEY (id);
alter table public.profiles add constraint profiles_pkey PRIMARY KEY (id);
alter table public.reviews add constraint reviews_pkey PRIMARY KEY (id);
alter table public.store_settings add constraint store_settings_pkey PRIMARY KEY (key);
alter table public.blocklist add constraint blocklist_value_key UNIQUE (value);
alter table public.orders add constraint orders_code_key UNIQUE (code);
alter table public.orders add constraint orders_idem_key UNIQUE (idem);
alter table public.products add constraint products_slug_key UNIQUE (slug);
alter table public.reviews add constraint reviews_order_id_product_id_key UNIQUE (order_id, product_id);
alter table public.blocklist add constraint blocklist_kind_check CHECK ((kind = 'phone'::text));
alter table public.contact_messages add constraint contact_messages_message_check CHECK (((length(message) >= 2) AND (length(message) <= 1000)));
alter table public.contact_messages add constraint contact_messages_name_check CHECK ((length(name) <= 100));
alter table public.contact_messages add constraint contact_messages_phone_check CHECK ((length(phone) <= 20));
alter table public.contact_messages add constraint contact_phone_chk CHECK (((phone IS NULL) OR (phone ~ '^[6-9][0-9]{9}$'::text)));
alter table public.coupons add constraint coupons_percent_check CHECK (((percent >= 1) AND (percent <= 90)));
alter table public.orders add constraint orders_status_check CHECK ((status = ANY (ARRAY['placed'::text, 'needs_verification'::text, 'confirmed'::text, 'packed'::text, 'shipped'::text, 'out_for_delivery'::text, 'delivered'::text, 'cancelled'::text, 'returned'::text])));
alter table public.products add constraint products_price_check CHECK ((price >= 0));
alter table public.products add constraint products_status_check CHECK ((status = ANY (ARRAY['published'::text, 'draft'::text, 'archived'::text])));
alter table public.reviews add constraint reviews_body_check CHECK (((length(body) >= 10) AND (length(body) <= 600)));
alter table public.reviews add constraint reviews_image_url_check CHECK (((image_url IS NULL) OR (image_url ~ '^calyx/r/[A-Za-z0-9_-]+$'::text)));
alter table public.reviews add constraint reviews_rating_check CHECK (((rating >= 1) AND (rating <= 5)));
alter table public.reviews add constraint reviews_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text])));
alter table public.order_events add constraint order_events_order_id_fkey FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
alter table public.orders add constraint orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE SET NULL;
alter table public.profiles add constraint profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;
alter table public.reviews add constraint reviews_order_id_fkey FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
alter table public.reviews add constraint reviews_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;

CREATE INDEX orders_user_id_idx ON public.orders USING btree (user_id);
CREATE INDEX orders_phone_idx ON public.orders USING btree (phone);
CREATE INDEX order_events_order_id_idx ON public.order_events USING btree (order_id);
CREATE INDEX products_status_sort_idx ON public.products USING btree (status, sort);
CREATE INDEX reviews_product_id_status_idx ON public.reviews USING btree (product_id, status);
CREATE INDEX reviews_order_id_idx ON public.reviews USING btree (order_id);

-- ===== functions =====
CREATE OR REPLACE FUNCTION public.is_admin() RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO '' AS $function$
 select exists(select 1 from public.admin_emails where lower(email)=lower(coalesce(auth.jwt()->>'email',''))) and coalesce(auth.jwt()->'app_metadata'->>'provider','')='google' $function$;

CREATE OR REPLACE FUNCTION public.handle_new_user() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path TO '' AS $function$
begin insert into public.profiles(id,email,name) values(new.id,new.email,coalesce(new.raw_user_meta_data->>'full_name',new.raw_user_meta_data->>'name')) on conflict do nothing; return new; end $function$;

CREATE OR REPLACE FUNCTION public.block_mutation() RETURNS trigger LANGUAGE plpgsql SET search_path TO 'public' AS $function$ begin raise exception 'append_only'; end $function$;

CREATE OR REPLACE FUNCTION public.audit_actor() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public' AS $function$ begin new.actor:=coalesce(auth.jwt()->>'email',current_user); new.created_at:=now(); return new; end $function$;

CREATE OR REPLACE FUNCTION public.check_coupon(c text) RETURNS integer LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public' AS $function$
 select percent from public.coupons where code=upper(trim(c)) and active and (max_uses is null or uses<max_uses) $function$;

CREATE OR REPLACE FUNCTION public.contact_rate_limit() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public' AS $function$
begin
 if (select count(*) from public.contact_messages where phone is not distinct from new.phone and created_at>now()-interval '1 hour')>=3
  or (select count(*) from public.contact_messages where created_at>now()-interval '1 hour')>=200 then raise exception 'rate_limited'; end if;
 return new; end $function$;

CREATE OR REPLACE FUNCTION public.orders_rate_limit() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public' AS $function$
begin if (select count(*) from public.orders where phone=new.phone and created_at>now()-interval '1 hour')>=5 then raise exception 'rate_limited'; end if; return new; end $function$;

CREATE OR REPLACE FUNCTION public.get_reviews(pid bigint) RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public' AS $function$
 select jsonb_build_object('avg',coalesce((select round(avg(rating)::numeric,1) from public.reviews where product_id=pid and status='approved'),0),'count',(select count(*) from public.reviews where product_id=pid and status='approved'),'items',coalesce((select jsonb_agg(to_jsonb(x)) from (select name,rating,body,image_url,created_at from public.reviews where product_id=pid and status='approved' order by (image_url is not null) desc,created_at desc limit 12) x),'[]'::jsonb)) $function$;

CREATE OR REPLACE FUNCTION public.home_extras() RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public' AS $function$
select jsonb_build_object(
 'stats',(select coalesce(jsonb_object_agg(product_id::text,jsonb_build_object('a',a,'c',c)),'{}'::jsonb) from (select product_id,round(avg(rating)::numeric,1) a,count(*) c from public.reviews where status='approved' group by product_id) t),
 'best',(select coalesce(jsonb_agg(pid order by q desc),'[]'::jsonb) from (select (i->>'id')::bigint pid,sum((i->>'qty')::int) q from public.orders o,jsonb_array_elements(o.items) i where o.status not in('cancelled','returned') and o.created_at>now()-interval '90 days' group by 1 order by q desc limit 8) t),
 'latest',(select coalesce(jsonb_agg(to_jsonb(x)),'[]'::jsonb) from (select r.name,r.rating,r.body,r.image_url,r.product_id,p.name as product from public.reviews r join public.products p on p.id=r.product_id where r.status='approved' and p.status='published' order by (r.image_url is not null) desc,r.created_at desc limit 6) x)) $function$;

CREATE OR REPLACE FUNCTION public.review_check(c text, ph text, pid bigint) RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path TO 'public' AS $function$
declare o public.orders%rowtype; lim int; ph_ok boolean;
begin
 select * into o from public.orders where code=upper(trim(c)) and phone=trim(ph) and status='delivered';
 if not found then return jsonb_build_object('ok',false,'photo',false); end if;
 if not exists(select 1 from jsonb_array_elements(o.items) i where (i->>'id')::bigint=pid) or exists(select 1 from public.reviews where order_id=o.id and product_id=pid) then return jsonb_build_object('ok',false,'photo',false); end if;
 select (value#>>'{}')::int into lim from public.store_settings where key='review_photo_limit';
 lim:=coalesce(lim,20);
 ph_ok:=(select count(*) from public.reviews where product_id=pid and image_url is not null and status<>'rejected')<lim;
 return jsonb_build_object('ok',true,'photo',ph_ok);
end $function$;

CREATE OR REPLACE FUNCTION public.submit_review(c text, ph text, pid bigint, rt integer, bd text, img text DEFAULT NULL::text) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public' AS $function$
declare o public.orders%rowtype; chk jsonb; nm text;
begin
 chk:=public.review_check(c,ph,pid);
 if (chk->>'ok')::boolean is not true then raise exception 'not_eligible'; end if;
 if img is not null and (chk->>'photo')::boolean is not true then raise exception 'photo_limit'; end if;
 select * into o from public.orders where code=upper(trim(c)) and phone=trim(ph);
 nm:=split_part(trim(o.name),' ',1); if split_part(trim(o.name),' ',2)<>'' then nm:=nm||' '||left(split_part(trim(o.name),' ',2),1)||'.'; end if;
 insert into public.reviews(product_id,order_id,name,rating,body,image_url) values(pid,o.id,left(nm,40),rt,trim(bd),nullif(img,''));
 return jsonb_build_object('ok',true);
end $function$;

CREATE OR REPLACE FUNCTION public.track_order(c text, ph text) RETURNS jsonb LANGUAGE sql SECURITY DEFINER SET search_path TO 'public' AS $function$
 select jsonb_build_object('code',o.code,'status',o.status,'courier',o.courier,'tracking_id',o.tracking_id,'events',(select coalesce(jsonb_agg(jsonb_build_object('status',e.status,'at',e.created_at,'note',e.note) order by e.created_at),'[]') from public.order_events e where e.order_id=o.id)) from public.orders o where o.code=upper(trim(c)) and o.phone=trim(ph) $function$;

CREATE OR REPLACE FUNCTION public.set_order_status(oid bigint, st text, cr text DEFAULT NULL::text, trk text DEFAULT NULL::text, nt text DEFAULT NULL::text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public' AS $function$
declare o public.orders%rowtype; it jsonb; nxt text[];
begin
 if not public.is_admin() then raise exception 'forbidden'; end if;
 select * into o from public.orders where id=oid for update; if not found then raise exception 'not_found'; end if;
 nxt:=case o.status when 'placed' then array['needs_verification','confirmed','cancelled'] when 'needs_verification' then array['confirmed','cancelled'] when 'confirmed' then array['packed','cancelled'] when 'packed' then array['shipped','cancelled'] when 'shipped' then array['out_for_delivery','delivered','returned'] when 'out_for_delivery' then array['delivered','returned'] when 'delivered' then array['returned'] else array[]::text[] end;
 if st<>o.status and not (st=any(nxt)) then raise exception 'invalid_transition'; end if;
 if st in('cancelled','returned') and st<>o.status and coalesce(trim(nt),'')='' then raise exception 'reason_required'; end if;
 if st in('cancelled','returned') and o.status not in('cancelled','returned') then
  for it in select value from jsonb_array_elements(o.items) loop update public.products set stock=stock+(it->>'qty')::int where id=(it->>'id')::bigint and stock is not null; end loop; end if;
 update public.orders set status=st, courier=coalesce(cr,courier), tracking_id=coalesce(trk,tracking_id), verified_at=case when o.status='needs_verification' and st='confirmed' then now() else verified_at end, verified_by=case when o.status='needs_verification' and st='confirmed' then auth.jwt()->>'email' else verified_by end where id=oid;
 if st<>o.status or nt is not null then insert into public.order_events(order_id,status,note) values(oid,st,nt); end if;
 insert into public.audit_log(actor,action,detail) values(null,'order_status',jsonb_build_object('order',o.code,'from',o.status,'to',st));
end $function$;

CREATE OR REPLACE FUNCTION public.place_order(p jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public' AS $function$
declare it jsonb; pr public.products%rowtype; sub int:=0; disc int:=0; sh int:=0; fee int:=0; thr int; tot int; lines jsonb:='[]'; q int; cp public.coupons%rowtype; oid bigint; ex public.orders%rowtype; cn text;
 nm text; ph text; ad text; pay text; pin text; totq int:=0; ver text; rs int:=0; flags jsonb:='[]'; stt text:='placed'; rev int; rej int; capc int; prior int; bad int; delivered int; bulk boolean:=false; fv boolean:=false;
begin
 if p->>'idem' is not null then select * into ex from public.orders where idem=p->>'idem'; if found then return jsonb_build_object('code',ex.code,'total',ex.total,'status',ex.status); end if; end if;
 nm:=trim(coalesce(p->>'name','')); ph:=coalesce(p->>'phone',''); ad:=trim(coalesce(p->>'address','')); pin:=coalesce(p->>'pincode',''); pay:=coalesce(p->>'payment','');
 if length(nm) not between 2 and 60 or ph !~ '^[6-9][0-9]{9}$' or length(ad) not between 15 and 250 or pin !~ '^[1-9][0-9]{5}$' or pay not in('Cash on Delivery','Order via WhatsApp') then raise exception 'invalid_details'; end if;
 select value#>>'{}' into ver from public.store_settings where key='policy_version'; ver:=coalesce(ver,'2026-11-14.1');
 if coalesce(p->>'policy','')<>ver then raise exception 'consent_required'; end if;
 if jsonb_typeof(p->'items')<>'array' or jsonb_array_length(p->'items') not between 1 and 20 then raise exception 'invalid_items'; end if;
 if (select count(*) from public.orders where phone=ph and created_at>now()-interval '1 hour')>=3 or (select count(*) from public.orders where phone=ph and created_at>now()-interval '24 hours')>=8 then raise exception 'rate_limited'; end if;
 for it in select value from jsonb_array_elements(p->'items') loop
  q:=coalesce((it->>'qty')::int,0); if q<1 or q>10 then raise exception 'invalid_qty'; end if;
  totq:=totq+q; if totq>20 then raise exception 'invalid_qty'; end if; if q>=4 then bulk:=true; end if;
  if coalesce(it->>'size','') not in('S','M','L','XL') then raise exception 'invalid_size'; end if;
  select * into pr from public.products where id=(it->>'id')::bigint and status='published' for update;
  if not found then raise exception 'unavailable'; end if;
  if not ((it->>'color') = any(pr.colors)) then raise exception 'invalid_color'; end if;
  sub:=sub+pr.price*q; lines:=lines||jsonb_build_object('id',pr.id,'name',pr.name,'color',left(it->>'color',30),'size',it->>'size','qty',q,'price',pr.price);
 end loop;
 select * into ex from public.orders where phone=ph and address=ad and items=lines and status<>'cancelled' and created_at>now()-interval '10 minutes' order by id desc limit 1;
 if found then return jsonb_build_object('code',ex.code,'total',ex.total,'status',ex.status); end if;
 for it in select value from jsonb_array_elements(lines) loop
  q:=(it->>'qty')::int;
  update public.products set stock=stock-q where id=(it->>'id')::bigint and stock is not null and stock>=q;
  if not found and exists(select 1 from public.products where id=(it->>'id')::bigint and stock is not null) then raise exception 'out_of_stock'; end if;
 end loop;
 if nullif(p->>'coupon','') is not null then
  select * into cp from public.coupons where code=upper(p->>'coupon') and active and (max_uses is null or uses<max_uses) and sub>=coalesce(min_cart,0) and (expires_at is null or expires_at>now());
  if found and not exists(select 1 from public.orders where phone=ph and coupon=cp.code and status<>'cancelled') then disc:=round(sub*cp.percent/100.0); update public.coupons set uses=uses+1 where code=cp.code; end if;
 end if;
 select coalesce((value#>>'{}')::int,1999) into thr from public.store_settings where key='free_ship_threshold';
 select coalesce((value#>>'{}')::int,99) into fee from public.store_settings where key='shipping_fee';
 if sub-disc<coalesce(thr,1999) then sh:=coalesce(fee,99); end if;
 tot:=sub-disc+sh;
 select count(*) into prior from public.orders where phone=ph and status<>'cancelled';
 select count(*) into delivered from public.orders where phone=ph and status='delivered';
 select count(*) into bad from public.orders where phone=ph and status in('cancelled','returned');
 if prior=0 then rs:=rs+15; flags:=flags||'"new_phone"'; end if;
 if pay='Cash on Delivery' then rs:=rs+10; flags:=flags||'"cod"'; end if;
 if tot>3000 then rs:=rs+15; flags:=flags||'"high_value"'; end if;
 if bulk then rs:=rs+10; flags:=flags||'"bulk_size"'; end if;
 if ph ~ '^([0-9])\1{9}$' or ph ~ '(0123456789|1234567890|9876543210)$' then rs:=rs+30; flags:=flags||'"fake_phone"'; end if;
 if ad ~* '(.)\1{4,}' or ad ~* '\m(test|asdf|qwerty|dummy|fake)\M' or ad !~* '[aeiou]' then rs:=rs+30; flags:=flags||'"bad_address"'; end if;
 if nm ~* '(.)\1{3,}' or nm ~* '^(test|asdf|qwerty|abc|xyz)\M' then rs:=rs+30; flags:=flags||'"bad_name"'; end if;
 if bad>0 then rs:=rs+least(60,20*bad); flags:=flags||'"past_cancel_return"'; end if;
 select coalesce((value#>>'{}')::int,2500) into capc from public.store_settings where key='cod_cap_first';
 if pay='Cash on Delivery' and tot>coalesce(capc,2500) and delivered=0 then fv:=true; flags:=flags||'"cod_cap"'; end if;
 if exists(select 1 from public.blocklist where kind='phone' and value=ph) then rs:=rs+100; flags:=flags||'"blocklist"'; end if;
 select coalesce((value#>>'{}')::int,30) into rev from public.store_settings where key='risk_review';
 select coalesce((value#>>'{}')::int,60) into rej from public.store_settings where key='risk_reject';
 if rs>coalesce(rej,60) then raise exception 'order_rejected'; elsif rs>=coalesce(rev,30) or fv then stt:='needs_verification'; end if;
 insert into public.orders(user_id,name,phone,address,pincode,payment,items,subtotal,discount,shipping,total,coupon,idem,status,risk_score,risk_flags,policy_version,policy_accepted_at) values(auth.uid(),left(nm,60),ph,left(ad,250),pin,pay,lines,sub,disc,sh,tot,case when disc>0 then cp.code end,p->>'idem',stt,rs,flags,ver,now()) returning id into oid;
 cn:='CC-'||(10000+oid); update public.orders set code=cn where id=oid;
 insert into public.order_events(order_id,status,note) values(oid,stt,case when stt='placed' then 'Order placed' else 'Order placed. We will verify it on WhatsApp before dispatch.' end);
 return jsonb_build_object('code',cn,'total',tot,'subtotal',sub,'discount',disc,'shipping',sh,'status',stt);
end $function$;

-- ===== row level security =====
alter table public.admin_emails enable row level security;
alter table public.store_settings enable row level security;
alter table public.profiles enable row level security;
alter table public.banners enable row level security;
alter table public.order_events enable row level security;
alter table public.contact_messages enable row level security;
alter table public.products enable row level security;
alter table public.faq enable row level security;
alter table public.reviews enable row level security;
alter table public.orders enable row level security;
alter table public.coupons enable row level security;
alter table public.blocklist enable row level security;
alter table public.audit_log enable row level security;

create policy "admin_emails admin" on public.admin_emails for ALL to public using (is_admin()) with check (is_admin());
create policy "audit admin" on public.audit_log for SELECT to public using (is_admin());
create policy "audit insert admin" on public.audit_log for INSERT to public with check (is_admin());
create policy "banners admin" on public.banners for ALL to public using (is_admin()) with check (is_admin());
create policy "banners read" on public.banners for SELECT to public using ((active OR is_admin()));
create policy "blocklist admin" on public.blocklist for ALL to public using (is_admin()) with check (is_admin());
create policy "contact admin" on public.contact_messages for SELECT to public using (is_admin());
create policy "contact admin delete" on public.contact_messages for DELETE to public using (is_admin());
create policy "contact admin update" on public.contact_messages for UPDATE to public using (is_admin()) with check (is_admin());
create policy "contact insert" on public.contact_messages for INSERT to anon, authenticated with check (true);
create policy "coupons admin" on public.coupons for ALL to public using (is_admin()) with check (is_admin());
create policy "faq admin" on public.faq for ALL to public using (is_admin()) with check (is_admin());
create policy "faq read" on public.faq for SELECT to public using ((active OR is_admin()));
create policy "events own" on public.order_events for SELECT to public using ((is_admin() OR (EXISTS (SELECT 1 FROM orders o WHERE ((o.id = order_events.order_id) AND (o.user_id = (SELECT auth.uid() AS uid)))))));
create policy "orders own" on public.orders for SELECT to public using (((user_id = (SELECT auth.uid() AS uid)) OR is_admin()));
create policy "products admin" on public.products for ALL to public using (is_admin()) with check (is_admin());
create policy "products read" on public.products for SELECT to public using (((status = 'published'::text) OR is_admin()));
create policy "profile own" on public.profiles for SELECT to public using (((id = (SELECT auth.uid() AS uid)) OR is_admin()));
create policy "profile update own" on public.profiles for UPDATE to public using ((id = (SELECT auth.uid() AS uid))) with check ((id = (SELECT auth.uid() AS uid)));
create policy "reviews admin" on public.reviews for ALL to public using (is_admin()) with check (is_admin());
create policy "settings admin" on public.store_settings for ALL to public using (is_admin()) with check (is_admin());
create policy "settings read" on public.store_settings for SELECT to public using (true);

-- ===== triggers =====
CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
CREATE TRIGGER orders_rate_limit_trg BEFORE INSERT ON public.orders FOR EACH ROW EXECUTE FUNCTION public.orders_rate_limit();
CREATE TRIGGER contact_rate_limit_trg BEFORE INSERT ON public.contact_messages FOR EACH ROW EXECUTE FUNCTION public.contact_rate_limit();
CREATE TRIGGER order_events_ro BEFORE DELETE OR UPDATE ON public.order_events FOR EACH ROW EXECUTE FUNCTION public.block_mutation();
CREATE TRIGGER audit_log_ro BEFORE DELETE OR UPDATE ON public.audit_log FOR EACH ROW EXECUTE FUNCTION public.block_mutation();
CREATE TRIGGER audit_actor_trg BEFORE INSERT ON public.audit_log FOR EACH ROW EXECUTE FUNCTION public.audit_actor();

-- ===== function permissions (only the public API is callable) =====
revoke execute on all functions in schema public from public, anon, authenticated;
grant execute on function public.is_admin() to anon, authenticated;
grant execute on function public.place_order(jsonb), public.track_order(text,text), public.check_coupon(text), public.get_reviews(bigint), public.review_check(text,text,bigint), public.submit_review(text,text,bigint,integer,text,text), public.home_extras() to anon, authenticated;
grant execute on function public.set_order_status(bigint,text,text,text,text) to authenticated;
