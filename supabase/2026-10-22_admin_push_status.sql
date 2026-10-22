-- 2026-10-22 관리자 가입자 목록에 알림 설정 상태 표시
-- users[]에 유입(src)·30일 방문일(days30)·최근 방문(last_seen)·홈화면앱(pwa)·
-- 알림 기기 수(push)·알림 종류(push_prefs)·기기별 알림 권한 상태(push_status)·"나중에" 누름(pn_no)을 더한다.
-- retention.push / retention.pwa 도 채운다 (요약 화면 KPI).
-- 클라이언트(index.html)는 기기마다 push_status 컬렉션에 { state, device, at } 를 남긴다.

create or replace function public.admin_stats()
 returns jsonb
 language plpgsql
 stable security definer
 set search_path to 'public', 'auth'
as $function$
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
  with ss as (select distinct sid from events where sid is not null and sid <> 'nosid' and uid = any(staff) and uid is distinct from public.demo_id()),
       sv as (select distinct vk from events where vk is not null and uid = any(staff) and uid is distinct from public.demo_id() and at > now() - interval '31 days'),
       e0 as (select *, coalesce(vk, 's:' || sid) k, (at at time zone 'Asia/Seoul')::date d from events
             where kind in ('visit','view') and at > now() - interval '31 days' and (uid is null or not (uid = any(staff)))
               and (vk is null or vk not in (select vk from sv))
               and (sid is null or sid not in (select sid from ss))),
       bots as (select k, d from e0 group by k, d
                having count(distinct sid) >= 4
                    or (bool_and(device like '% 기타') and count(*) filter (where kind = 'view') = 0)),
       pv as (select e0.* from e0 left join bots b on b.k = e0.k and b.d = e0.d where b.k is null),
       v as (select * from pv where kind = 'visit'),
       u as (select id, email, created_at, last_sign_in_at, (created_at at time zone 'Asia/Seoul')::date d from auth.users where not (id = any(excl))),
       st as (select owner, data -> 'investor' inv from docs where collection = 'settings' and id = 'main'),
       hc as (select owner, count(*) n from docs where collection = 'holdings' group by owner),
       ps as (select owner, count(*) n, max(data ->> 'at') last_at,
                     jsonb_agg(coalesce(data ->> 'device', '기기') order by data ->> 'at' desc) devices
                from docs where collection = 'push_subs' group by owner),
       pp as (select owner, data prefs from docs where collection = 'push_prefs' and id = 'main'),
       pst as (select owner, jsonb_agg(jsonb_build_object('state', data ->> 'state', 'device', data ->> 'device', 'at', data ->> 'at')
                                       order by data ->> 'at' desc) list
                 from docs where collection = 'push_status' group by owner),
       ue as (select uid, max(at) last_seen,
                     count(distinct (at at time zone 'Asia/Seoul')::date) filter (where at > now() - interval '30 days') days30,
                     bool_or(device like '%홈화면앱%') pwa,
                     bool_or(kind = 'view' and path = 'pn-no') pn_no
                from events where uid is not null and not (uid = any(excl)) group by uid),
       usrc as (select distinct on (uid) uid,
                       case when ref like 'ig%' then 'ig' when ref like 'ad-%' then 'ad'
                            when ref like '%threads%' then 'threads' when ref like '%facebook%' then 'facebook'
                            when ref like '%naver%' then 'naver' when ref like '%youtube%' then 'youtube'
                            when ref like 'kakaotalk%' then 'kakaotalk'
                            when ref = '' or ref like '%kauth.kakao.com%' or ref like '%valuenote%' then null
                            else ref end s
                  from events where kind = 'signup' and uid is not null order by uid, at),
       days as (select generate_series(d0 - 29, d0, interval '1 day')::date d)
  select jsonb_build_object(
    'asOf', now(),
    'bots', jsonb_build_object(
       'today', (select count(*) from bots where d = d0),
       'd30',   (select count(*) from bots)),
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
       'pushOn',       (select count(*) from u join ps on ps.owner = u.id)),
    'retention', jsonb_build_object(
       'push', (select count(*) from u join ps on ps.owner = u.id),
       'pwa',  (select count(*) from u join ue on ue.uid = u.id where ue.pwa)),
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
              case jsonb_typeof(st.inv -> 'style') when 'array' then (select string_agg(x, ', ') from jsonb_array_elements_text(st.inv -> 'style') x) else st.inv ->> 'style' end style, st.inv -> 'goal' goal, st.inv ->> 'size' size, st.inv ->> 'exp' exp, st.inv -> 'expect' expect, st.inv ->> 'expectNote' note,
              usrc.s src, ue.last_seen, coalesce(ue.days30, 0) days30, coalesce(ue.pwa, false) pwa, coalesce(ue.pn_no, false) pn_no,
              coalesce(ps.n, 0) push, ps.last_at push_at, ps.devices push_devices, pp.prefs push_prefs, pst.list push_status
       from u left join st on st.owner = u.id left join hc on hc.owner = u.id
              left join ue on ue.uid = u.id left join usrc on usrc.uid = u.id
              left join ps on ps.owner = u.id left join pp on pp.owner = u.id left join pst on pst.owner = u.id
       order by u.created_at desc limit 100) x)
  ) into res;
  return res;
end $function$;
