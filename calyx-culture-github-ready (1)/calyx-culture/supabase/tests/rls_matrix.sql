-- STAGING ONLY. NOT YET EXECUTED (no Postgres was available when written).
-- Run in the Supabase SQL editor of a STAGING project after schema.sql + seed.sql + the migration.
-- Each block impersonates a role/JWT, attempts something, and raises if the outcome is wrong.
-- Replace the emails below with real rows in admin_emails (one per role) before running.
create or replace function pg_temp.as_user(em text, prov text default 'google') returns void language plpgsql as $$
begin
  perform set_config('request.jwt.claims', json_build_object('email', em, 'app_metadata', json_build_object('provider', prov))::text, true);
  perform set_config('request.headers', '{"cf-connecting-ip":"203.0.113.9"}', true);
end $$;
create or replace function pg_temp.expect_fail(q text, label text) returns void language plpgsql as $$
begin execute q; raise exception 'SECURITY FAILURE (allowed): %', label;
exception when raise_exception then raise; when others then raise notice 'ok (rejected): %', label; end $$;
create or replace function pg_temp.expect_rows(q text, want int, label text) returns void language plpgsql as $$
declare n int; begin execute 'select count(*) from (' || q || ') t' into n;
  if n <> want then raise exception 'WRONG ROWS for %: got %, want %', label, n, want; end if; raise notice 'ok: %', label; end $$;

begin;
-- ===== anonymous =====
set local role anon;
select pg_temp.expect_fail($$select * from public.orders$$, 'anon reads orders');
select pg_temp.expect_fail($$select * from public.coupons$$, 'anon reads coupons');
select pg_temp.expect_fail($$select * from public.audit_log$$, 'anon reads audit_log');
select pg_temp.expect_fail($$select * from public.admin_emails$$, 'anon reads admin_emails');
select pg_temp.expect_fail($$select * from public.rate_events$$, 'anon reads rate_events');
select pg_temp.expect_fail($$select * from public.upload_tokens$$, 'anon reads upload_tokens');
select pg_temp.expect_fail($$insert into public.products(slug,name,category,price) values('x','x','x',1)$$, 'anon writes products');
select pg_temp.expect_fail($$insert into public.contact_messages(name,message,handled) values('a','hello',true)$$, 'anon sets handled');
select pg_temp.expect_fail($$select public.set_order_status(1,'cancelled',null,null,'x')$$, 'anon calls set_order_status');
select pg_temp.expect_fail($$select public.issue_review_upload('CC-10001','9876543210',1,'1.1.1.1')$$, 'anon calls issue_review_upload');
select pg_temp.expect_fail($$select public.rate_hit('a','b')$$, 'anon calls rate_hit');
select pg_temp.expect_rows($$select 1 from public.store_settings where key in ('risk_review','risk_reject','cod_cap_first')$$, 0, 'anon cannot see fraud thresholds');
select pg_temp.expect_rows($$select 1 from public.products where status <> 'published'$$, 0, 'anon sees only published products');
-- tracking lockout: 21st wrong attempt must raise rate_limited
do $$ declare i int; begin
  for i in 1..20 loop perform public.track_order('CC-99999','9000000000'); end loop;
  begin perform public.track_order('CC-99999','9000000000'); raise exception 'SECURITY FAILURE: no lockout';
  exception when others then if sqlerrm <> 'rate_limited' then raise; end if; end;
  raise notice 'ok: tracking locks out after 20 failures'; end $$;
rollback;

-- ===== ordinary customer (signed in with Google but NOT in admin_emails) =====
begin;
select pg_temp.as_user('random.customer@example.com');
set local role authenticated;
select pg_temp.expect_rows($$select 1 from public.orders$$, 0, 'customer sees no orders via REST');
select pg_temp.expect_fail($$update public.products set price=1$$, 'customer updates products');
select pg_temp.expect_fail($$insert into public.admin_emails(email) values('random.customer@example.com')$$, 'customer self-promotes');
select pg_temp.expect_fail($$select public.set_order_status(1,'cancelled',null,null,'x')$$, 'customer cancels via RPC');
rollback;

-- ===== email-provider account with an admin email must NOT be admin =====
begin;
select pg_temp.as_user('clayxculture@gmail.com', 'email');
set local role authenticated;
select pg_temp.expect_rows($$select 1 where public.is_admin()$$, 0, 'non-google provider is not admin');
rollback;

-- ===== role matrix (edit emails first) =====
-- product_manager must: write products (ok), read orders (0 rows), call set_order_status (fail), edit admin_emails (fail)
-- order_manager must: set_order_status (ok), write products (fail), edit coupons (fail)
-- customer_support must: read orders (ok), set_order_status (fail), read audit_log (0 rows)
-- content_manager must: write banners/faq (ok), write products (fail), write store_settings key 'risk_review' (fail)
-- owner must: do everything incl. admin_emails
-- Copy the pattern above for each role: pg_temp.as_user('<email>'); set local role authenticated; expect_* ...
