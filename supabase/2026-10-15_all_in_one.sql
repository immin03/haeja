-- 한 번에 실행: 방문자 중복 제거 + 로그인 없이 둘러보기(기업·트렌드 공개) + 친구 초대 집계
-- Supabase → SQL Editor → New query → 전체 붙여넣기 → Run

-- 방문자 중복 제거(같은 IP는 하루 한 명) + 화면 조회수 집계 — Supabase → SQL Editor에 붙여넣고 Run 한 번
-- IP 원본은 저장하지 않고, 비밀값을 섞은 해시(vk)만 남긴다.

-- 1) 방문 기록에 '방문자 키'와 화면 조회(view) 종류 추가
alter table public.events add column if not exists vk text;
alter table public.events drop constraint if exists events_kind_check;
alter table public.events add constraint events_kind_check check (kind in ('visit','view','signup','login','onboard'));
create index if not exists events_vk on public.events (vk);

-- 2) 해시용 비밀값 (app_config 는 외부에서 읽을 수 없음)
insert into public.app_config(key, value) values ('ipsalt', to_jsonb(md5(random()::text || clock_timestamp()::text)))
on conflict (key) do nothing;

-- 3) 기록이 들어올 때 서버가 접속 IP를 보고 키를 붙인다 (브라우저가 값을 꾸밀 수 없음)
create or replace function public.events_set_vk() returns trigger
language plpgsql security definer set search_path = public as
$$
declare h json; ip text;
begin
  begin h := current_setting('request.headers', true)::json; exception when others then h := null; end;
  ip := coalesce(h ->> 'cf-connecting-ip', h ->> 'x-real-ip', trim(split_part(h ->> 'x-forwarded-for', ',', 1)));
  new.vk := case when coalesce(ip, '') = '' then null
                 else md5(ip || (select value #>> '{}' from public.app_config where key = 'ipsalt')) end;
  return new;
end $$;
revoke all on function public.events_set_vk() from public, anon, authenticated;
drop trigger if exists events_vk on public.events;
create trigger events_vk before insert on public.events for each row execute function public.events_set_vk();

-- 4) 관리자 통계: 방문자 = 같은 IP 하루 1명, 페이지뷰 = 첫 방문 + 화면 이동 전부
create or replace function public.admin_stats() returns jsonb
language plpgsql stable security definer set search_path = public, auth as
$$
declare
  d0 date := (now() at time zone 'Asia/Seoul')::date;
  excl uuid[];
  staff uuid[];
  res jsonb;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  excl := array_remove(array[public.publisher_id(), public.demo_id()], null);

  staff := array(select id from auth.users where id = any(excl)
                  or email in (select jsonb_array_elements_text(value) from public.app_config where key = 'admins'));
  /* 같은 곳(IP)에서 들어온 방문은 하루 한 명으로 센다. 운영자가 쓴 IP의 방문은 로그인 전이라도 뺀다 */
  with sv as (select distinct vk from events where vk is not null and uid = any(staff) and at > now() - interval '31 days'),
       pv as (select *, coalesce(vk, 's:' || sid) k, (at at time zone 'Asia/Seoul')::date d from events
             where kind in ('visit','view') and at > now() - interval '31 days' and (uid is null or not (uid = any(staff)))
               and (vk is null or vk not in (select vk from sv))),
       v as (select * from pv where kind = 'visit'),
       u as (select id, email, created_at, last_sign_in_at, (created_at at time zone 'Asia/Seoul')::date d from auth.users where not (id = any(excl))),
       st as (select owner, data -> 'investor' inv from docs where collection = 'settings' and id = 'main'),
       hc as (select owner, count(*) n from docs where collection = 'holdings' group by owner),
       days as (select generate_series(d0 - 29, d0, interval '1 day')::date d)
  select jsonb_build_object(
    'asOf', now(),
    'visitors', jsonb_build_object(
       'today', (select count(distinct k) from v where d = d0),
       'd7',    (select count(distinct k) from v where d > d0 - 7),
       'd30',   (select count(distinct k) from v where d > d0 - 30)),
    'pageviews', jsonb_build_object(
       'today', (select count(*) from pv where d = d0),
       'd30',   (select count(*) from pv where d > d0 - 30)),
    'pages', (select coalesce(jsonb_object_agg(p, n), '{}') from
              (select coalesce(nullif(ltrim(path, '/'), ''), '첫 화면') p, count(*) n from pv where d > d0 - 30 group by 1 order by 2 desc limit 12) x),
    'signups', jsonb_build_object(
       'total', (select count(*) from u),
       'today', (select count(*) from u where d = d0),
       'd7',    (select count(*) from u where d > d0 - 7),
       'd30',   (select count(*) from u where d > d0 - 30)),
    'funnel', jsonb_build_object(
       'visitors30',   (select count(distinct k) from v where d > d0 - 30),
       'signups30',    (select count(*) from u where d > d0 - 30),
       'onboarded',    (select count(*) from u join st on st.owner = u.id where st.inv ? 'done'),
       'withHoldings', (select count(*) from u join hc on hc.owner = u.id),
       'pushOn',       (select count(distinct owner) from docs where collection = 'push_subs' and not (owner = any(excl)))),
    'active7', (select count(distinct owner) from docs where updated_at > now() - interval '7 days' and not (owner = any(excl))
                and collection in ('holdings','journal','settings','companies')),
    'demoVisits7', (select count(*) from events where kind = 'login' and uid = public.demo_id() and at > now() - interval '7 days'),
    'daily', (select jsonb_agg(jsonb_build_object('d', days.d,
                'v', (select count(distinct k) from v where v.d = days.d),
                'p', (select count(*) from pv where pv.d = days.d),
                's', (select count(*) from u where u.d = days.d)) order by days.d) from days),
    'devices', (select coalesce(jsonb_object_agg(device, n), '{}') from
                (select coalesce(device,'기타') device, count(distinct k) n from v where d > d0 - 30 group by 1) x),
    'refs', (select coalesce(jsonb_agg(jsonb_build_object('r', r, 'n', n) order by n desc), '[]') from
             (select coalesce(nullif(ref,''),'직접 방문') r, count(distinct k) n from v where d > d0 - 30 group by 1 order by 2 desc limit 8) x),
    'refSignups', (select coalesce(jsonb_object_agg(r, n), '{}') from
             (select coalesce(nullif(ref,''),'직접 방문') r, count(*) n from events where kind = 'signup' and at > now() - interval '31 days' group by 1) x),
    'expect', (select coalesce(jsonb_object_agg(e, n), '{}') from
               (select jsonb_array_elements_text(st.inv -> 'expect') e, count(*) n from st join u on u.id = st.owner
                where jsonb_typeof(st.inv -> 'expect') = 'array' group by 1) x),
    'style', (select coalesce(jsonb_object_agg(s, n), '{}') from
              (select s, count(*) n from st join u on u.id = st.owner,
                 lateral (select jsonb_array_elements_text(case jsonb_typeof(st.inv -> 'style') when 'array' then st.inv -> 'style' when 'string' then jsonb_build_array(st.inv -> 'style') else '[]'::jsonb end) s) z group by 1) x),
    'goal', (select coalesce(jsonb_object_agg(s, n), '{}') from
              (select jsonb_array_elements_text(st.inv -> 'goal') s, count(*) n from st join u on u.id = st.owner where jsonb_typeof(st.inv -> 'goal') = 'array' group by 1) x),
    'markets', (select coalesce(jsonb_object_agg(s, n), '{}') from
              (select jsonb_array_elements_text(st.inv -> 'markets') s, count(*) n from st join u on u.id = st.owner where jsonb_typeof(st.inv -> 'markets') = 'array' group by 1) x),
    'size', (select coalesce(jsonb_object_agg(s, n), '{}') from
             (select st.inv ->> 'size' s, count(*) n from st join u on u.id = st.owner where st.inv ->> 'size' is not null group by 1) x),
    'users', (select coalesce(jsonb_agg(x order by x.created_at desc), '[]') from (
       select u.email, u.created_at, u.last_sign_in_at, coalesce(hc.n, 0) holdings,
              case jsonb_typeof(st.inv -> 'style') when 'array' then (select string_agg(x, ', ') from jsonb_array_elements_text(st.inv -> 'style') x) else st.inv ->> 'style' end style, st.inv -> 'goal' goal, st.inv ->> 'size' size, st.inv ->> 'exp' exp, st.inv -> 'expect' expect, st.inv ->> 'expectNote' note
       from u left join st on st.owner = u.id left join hc on hc.owner = u.id order by u.created_at desc limit 100) x)
  ) into res;
  return res;
end $$;


-- 로그인 없이 둘러보기 — Supabase → SQL Editor에 붙여넣고 Run 한 번
-- 비회원(anon)은 운영 계정이 공개하는 공용 자료(기업 점수·개요·트렌드·주가·환율)만 읽을 수 있다.
-- 회원 개인 기록(보유 종목·일지·설정 등)은 지금처럼 본인만 읽는다.

-- 정책 안에서 운영 계정 번호를 확인하는 함수 (운영 계정 번호만 돌려주며 개인 정보는 없음)
grant execute on function public.publisher_id() to anon;

drop policy if exists "guest read" on public.docs;
create policy "guest read" on public.docs for select to anon
  using (collection = any (array['screen','profiles','trends','prices','fx']) and owner = public.publisher_id());

-- 확인: 마지막 줄에 guest read 정책이 보이면 성공

-- 친구 초대 집계 — Supabase → SQL Editor에 붙여넣고 Run 한 번
-- 초대 링크는 /?ref=inv-<회원번호 앞 8자리>. 그 링크로 처음 들어와 가입한 계정 수를 센다.

-- 서버(분석 함수)가 쓰는 집계: 특정 회원의 초대 가입 수
create or replace function public.invite_count(p_uid uuid) returns integer
language sql stable security definer set search_path = public as
$$
  select count(distinct e.uid)::int from public.events e
  where e.kind = 'signup' and e.uid is not null and e.uid <> p_uid
    and e.ref = 'inv-' || left(replace(p_uid::text, '-', ''), 8)
$$;
revoke all on function public.invite_count(uuid) from public, anon, authenticated;
grant execute on function public.invite_count(uuid) to service_role;

-- 앱 화면용: 로그인한 본인의 초대 가입 수만
create or replace function public.my_invites() returns integer
language sql stable security definer set search_path = public as
$$ select case when auth.uid() is null then 0 else public.invite_count(auth.uid()) end $$;
revoke all on function public.my_invites() from public, anon;
grant execute on function public.my_invites() to authenticated;

-- 확인: 두 함수가 보이면 성공

-- 확인: 아래 세 줄이 모두 true 면 성공
select (select count(*) from pg_policies where tablename = 'docs' and policyname = 'guest read') = 1 as guest_ok,
       (select count(*) from pg_trigger where tgname = 'events_vk') = 1 as visitor_ok,
       (select count(*) from pg_proc where proname in ('invite_count','my_invites')) = 2 as invite_ok;
