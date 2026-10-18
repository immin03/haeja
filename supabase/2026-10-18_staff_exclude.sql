-- 운영자 본인 방문을 통계에서 더 확실히 뺀다 (2026-10-18)
-- 기존: 운영자 계정 로그인 기록, 운영자가 쓴 IP
-- 추가: 운영자 계정으로 한 번이라도 기록된 기기(sid)는 로그아웃 상태·휴대폰 IP가 바뀌어도 제외
-- 고침: 체험 계정(demo)을 써 본 방문자의 IP·기기까지 운영자로 보고 빼던 문제를 바로잡음
-- 브라우저 쪽: 관리자 로그인 기기, ?staff=1로 한 번 연 브라우저는 아예 기록하지 않음 (index.html)

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
  /* 운영자 기기(sid): 한 번이라도 운영자 계정으로 기록된 기기는 로그아웃 상태·다른 IP에서 들어와도 뺀다 */
  with ss as (select distinct sid from events where sid is not null and sid <> 'nosid' and uid = any(staff) and uid is distinct from public.demo_id()),
       sv as (select distinct vk from events where vk is not null and uid = any(staff) and uid is distinct from public.demo_id() and at > now() - interval '31 days'),
       e0 as (select *, coalesce(vk, 's:' || sid) k, (at at time zone 'Asia/Seoul')::date d from events
             where kind in ('visit','view') and at > now() - interval '31 days' and (uid is null or not (uid = any(staff)))
               and (vk is null or vk not in (select vk from sv))
               and (sid is null or sid not in (select sid from ss))),
       /* 로봇 패턴: 같은 IP가 하루에 기기 번호(sid)를 4개 이상 만들거나, 기기를 알 수 없는데 화면 이동이 하나도 없는 경우 */
       bots as (select k, d from e0 group by k, d
                having count(distinct sid) >= 4
                    or (bool_and(device like '% 기타') and count(*) filter (where kind = 'view') = 0)),
       pv as (select e0.* from e0 left join bots b on b.k = e0.k and b.d = e0.d where b.k is null),
       v as (select * from pv where kind = 'visit'),
       u as (select id, email, created_at, last_sign_in_at, (created_at at time zone 'Asia/Seoul')::date d from auth.users where not (id = any(excl))),
       st as (select owner, data -> 'investor' inv from docs where collection = 'settings' and id = 'main'),
       hc as (select owner, count(*) n from docs where collection = 'holdings' group by owner),
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
