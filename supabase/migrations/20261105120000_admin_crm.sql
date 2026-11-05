-- 회원 CRM (2026-11-05 대표 요청: 회원 활동 추적·활성 유저·소통 관리)
-- 활동 = 그 회원의 앱 접속·화면 보기 기록(events, 로그인 전 같은 기기 기록 포함) + 종목·일지·설정 저장(docs)
-- 운영·체험 계정은 뺀다

create table if not exists public.crm_members (
  uid uuid primary key references auth.users(id) on delete cascade,
  tags text[] not null default '{}',
  memo text,
  updated_at timestamptz not null default now()
);
create table if not exists public.crm_log (
  id bigserial primary key,
  uid uuid not null references auth.users(id) on delete cascade,
  kind text not null,               -- 'msg' 앱 메시지 · 'note' 메모 기록
  title text,
  body text,
  alert_id text,
  at timestamptz not null default now()
);
create index if not exists crm_log_uid_at on public.crm_log(uid, at desc);
alter table public.crm_members enable row level security;
alter table public.crm_log enable row level security;
revoke all on public.crm_members, public.crm_log from anon, authenticated;

/* 회원 하루 단위 활동 (최근 60일): 회원 id · 날짜 · 화면 수 · 저장 수 */
create or replace function public._crm_activity(p_days int)
returns table(uid uuid, d date, views int, saves int, last_at timestamptz)
language sql stable security definer set search_path = public, auth as $$
  with excl as (select array_remove(array[public.publisher_id(), public.demo_id()], null) a),
       mem as (select id from auth.users, excl where not (id = any(excl.a))),
       vmap as (select distinct e.vk, e.uid from events e join mem on mem.id = e.uid where e.vk is not null),
       ev as (select coalesce(e.uid, vmap.uid) uid, e.at, e.kind from events e left join vmap on e.uid is null and vmap.vk = e.vk
               where e.at > now() - make_interval(days => p_days) and e.kind in ('visit','view','engage','login','onboard')),
       evm as (select ev.* from ev join mem on mem.id = ev.uid),
       -- 시세 갱신 같은 시스템 일괄 작업: 같은 분에 회원 3명 이상의 문서가 함께 바뀐 시각(앞뒤 1분 포함)은 회원 활동에서 뺀다
       bm as (select date_trunc('minute', updated_at) m from docs
               where updated_at > now() - make_interval(days => p_days) and owner in (select id from mem)
               group by 1 having count(distinct owner) > 2),
       dc as (select owner uid, updated_at at from docs join mem on mem.id = docs.owner
               where updated_at > now() - make_interval(days => p_days)
                 and collection in ('holdings','journal','settings','companies','interests','push_prefs')
                 and not exists (select 1 from bm where abs(extract(epoch from date_trunc('minute', docs.updated_at) - bm.m)) <= 60))
  select uid, d, sum(v)::int, sum(s)::int, max(at) from (
    select uid, (at at time zone 'Asia/Seoul')::date d, (kind in ('visit','view'))::int v, 0 s, at from evm
    union all
    select uid, (at at time zone 'Asia/Seoul')::date, 0, 1, at from dc) x
  group by uid, d $$;
revoke all on function public._crm_activity(int) from public, anon, authenticated;

create or replace function public.admin_crm()
returns jsonb language plpgsql stable security definer set search_path = public, auth as $$
declare d0 date := (now() at time zone 'Asia/Seoul')::date; excl uuid[]; res jsonb;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  excl := array_remove(array[public.publisher_id(), public.demo_id()], null);
  with _a as materialized (select * from public._crm_activity(60)),
       u as (select id, email, created_at, (created_at at time zone 'Asia/Seoul')::date sd from auth.users where not (id = any(excl))),
       days as (select generate_series(d0 - 29, d0, interval '1 day')::date d),
       per as (select uid,
                 count(*) filter (where d > d0 - 7) a7, count(*) filter (where d > d0 - 30) a30,
                 sum(views) filter (where d > d0 - 30) v30, sum(saves) filter (where d > d0 - 30) s30,
                 max(last_at) last_at, max(d) last_d,
                 jsonb_agg(d order by d) filter (where d > d0 - 30) dl
               from _a group by uid),
       cnt as (select owner, count(*) filter (where collection = 'holdings') h, count(*) filter (where collection = 'journal') j,
                      count(*) filter (where collection = 'interests') i, count(*) filter (where collection = 'companies') c,
                      count(*) filter (where collection = 'push_subs') p
                 from docs where collection in ('holdings','journal','interests','companies','push_subs') group by owner),
       st as (select owner, data -> 'investor' inv from docs where collection = 'settings' and id = 'main'),
       src as (select distinct on (uid) uid,
                       case when ref like 'ig%' then '인스타' when ref like 'ad-%' then '광고'
                            when ref like '%threads%' then '쓰레드' when ref like '%facebook%' then '페이스북'
                            when ref like '%naver%' then '네이버' when ref like '%youtube%' then '유튜브'
                            when ref like 'kakaotalk%' then '카톡' when ref like '%google%' then '구글 검색'
                            else '직접' end s
                  from events where kind = 'signup' and uid is not null order by uid, at),
       msg as (select l.uid, count(*) n, max(l.at) last_at,
                      count(*) filter (where coalesce((a.data->>'read')::boolean, false)) rd
                 from crm_log l left join docs a on a.collection = 'alerts' and a.owner = l.uid and a.id = l.alert_id
                where l.kind = 'msg' group by l.uid)
  select jsonb_build_object(
    'asOf', now(),
    'total', (select count(*) from u),
    'dau', (select count(distinct uid) from _a where d = d0),
    'wau', (select count(distinct uid) from _a where d > d0 - 7),
    'mau', (select count(distinct uid) from _a where d > d0 - 30),
    'wauPrev', (select count(distinct uid) from _a where d <= d0 - 7 and d > d0 - 14),
    'daily', (select jsonb_agg(jsonb_build_object('d', days.d,
                 'a', (select count(distinct uid) from _a where _a.d = days.d),
                 'w', (select count(distinct uid) from _a where _a.d > days.d - 7 and _a.d <= days.d),
                 's', (select count(*) from u where u.sd = days.d)) order by days.d) from days),
    'tags', (select coalesce(jsonb_agg(distinct t), '[]') from crm_members, unnest(tags) t),
    'members', (select coalesce(jsonb_agg(m order by m.created_at desc), '[]') from (
       select u.id uid, u.email, u.created_at, coalesce(src.s, '직접') src,
              coalesce(per.a7, 0) a7, coalesce(per.a30, 0) a30, coalesce(per.v30, 0) v30, coalesce(per.s30, 0) s30,
              per.last_at, per.dl, coalesce(cnt.h, 0) holdings, coalesce(cnt.j, 0) journal, coalesce(cnt.i, 0) interests, coalesce(cnt.c, 0) analyzed, coalesce(cnt.p, 0) push,
              coalesce(st.inv ? 'done', false) surveyed,
              case jsonb_typeof(st.inv -> 'style') when 'array' then (select string_agg(x, ', ') from jsonb_array_elements_text(st.inv -> 'style') x) else st.inv ->> 'style' end style,
              st.inv -> 'goal' goal, st.inv ->> 'size' size, st.inv ->> 'exp' exp, st.inv -> 'expect' expect, st.inv -> 'markets' markets, st.inv ->> 'expectNote' note,
              coalesce(cm.tags, '{}') tags, cm.memo, coalesce(msg.n, 0) msgs, coalesce(msg.rd, 0) msgs_read, msg.last_at msg_at
       from u left join per on per.uid = u.id left join cnt on cnt.owner = u.id left join st on st.owner = u.id
              left join src on src.uid = u.id left join crm_members cm on cm.uid = u.id left join msg on msg.uid = u.id) m)
  ) into res;
  return res;
end $$;

/* 회원 한 명: 날짜별 본 화면 · 등록 종목 · 메시지·메모 기록 */
create or replace function public.admin_crm_member(p_uid uuid)
returns jsonb language plpgsql stable security definer set search_path = public, auth as $$
declare res jsonb;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  with vk as (select distinct vk from events where uid = p_uid and vk is not null),
       ev as (select at, kind, path, device, ref from events
               where (uid = p_uid or (uid is null and vk in (select vk from vk)))
                 and kind in ('visit','view','signup','onboard','login') and at > now() - interval '60 days'),
       byday as (select (at at time zone 'Asia/Seoul')::date d, count(*) filter (where kind in ('visit','view')) n,
                        jsonb_agg(distinct coalesce(nullif(ltrim(path, '/'), ''), '첫 화면')) filter (where kind = 'view') pages,
                        jsonb_agg(distinct kind) filter (where kind in ('signup','onboard')) marks,
                        min(at) first_at, max(at) last_at
                   from ev group by 1)
  select jsonb_build_object(
    'days', (select coalesce(jsonb_agg(b order by b.d desc), '[]') from byday b),
    'devices', (select coalesce(jsonb_agg(distinct device), '[]') from ev where device is not null),
    'saves', (select coalesce(jsonb_agg(x order by x.at desc), '[]') from (
        select collection c, coalesce(data->>'name', data->>'title', data->>'ticker', id) name, updated_at at
          from docs where owner = p_uid and collection in ('holdings','journal','interests','companies')
         order by updated_at desc limit 40) x),
    'log', (select coalesce(jsonb_agg(x order by x.at desc), '[]') from (
        select l.id, l.kind, l.title, l.body, l.at, coalesce((a.data->>'read')::boolean, false) read
          from crm_log l left join docs a on a.collection = 'alerts' and a.owner = l.uid and a.id = l.alert_id
         where l.uid = p_uid order by l.at desc limit 50) x)
  ) into res;
  return res;
end $$;

create or replace function public.admin_crm_set(p_uid uuid, p_tags text[], p_memo text)
returns jsonb language plpgsql security definer set search_path = public as $$
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  insert into crm_members(uid, tags, memo, updated_at)
  values (p_uid, coalesce((select array_agg(distinct btrim(t)) from unnest(p_tags) t where btrim(t) <> ''), '{}'), nullif(btrim(p_memo), ''), now())
  on conflict (uid) do update set tags = excluded.tags, memo = excluded.memo, updated_at = now();
  return jsonb_build_object('ok', true);
end $$;

/* 회원에게 앱 메시지: 앱 알림함에 남고, 알림을 켠 기기에는 푸시로 간다 */
create or replace function public.admin_crm_send(p_uids uuid[], p_title text, p_body text, p_tab text default null)
returns jsonb language plpgsql security definer set search_path = public, auth as $$
declare v uuid; aid text; n int := 0; np int := 0; excl uuid[];
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  if coalesce(btrim(p_title), '') = '' or coalesce(btrim(p_body), '') = '' then raise exception '제목과 내용이 필요합니다'; end if;
  excl := array_remove(array[public.publisher_id(), public.demo_id()], null);
  foreach v in array p_uids loop
    continue when v = any(excl) or not exists(select 1 from auth.users where id = v);
    aid := 'crm-' || to_char(now(), 'YYYYMMDDHH24MISSMS') || '-' || n;
    insert into docs(collection, id, owner, data, updated_at) values ('alerts', aid, v,
      jsonb_build_object('at', now(), 'level', 'good', 'title', btrim(p_title), 'body', btrim(p_body),
                         'link', case when nullif(p_tab, '') is null then '{}'::jsonb else jsonb_build_object('tab', p_tab) end,
                         'url', case when nullif(p_tab, '') is null then '/#alerts' else '/#' || p_tab end,
                         'read', false, 'push', true, 'source', '밸류노트'), now());
    insert into crm_log(uid, kind, title, body, alert_id) values (v, 'msg', btrim(p_title), btrim(p_body), aid);
    n := n + 1;
    if exists(select 1 from docs where collection = 'push_subs' and owner = v) then np := np + 1; end if;
  end loop;
  return jsonb_build_object('ok', true, 'sent', n, 'push', np);
end $$;

revoke all on function public.admin_crm(), public.admin_crm_member(uuid), public.admin_crm_set(uuid, text[], text), public.admin_crm_send(uuid[], text, text, text) from public, anon;
grant execute on function public.admin_crm(), public.admin_crm_member(uuid), public.admin_crm_set(uuid, text[], text), public.admin_crm_send(uuid[], text, text, text) to authenticated;
