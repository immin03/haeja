-- 밸류노트 비서 (2026-10-20)
-- 눈: perf-collect 함수가 3시간마다 릴스 성과를 받아 social_posts.ig_insights 에 저장 (토큰 0)
-- 요약: agent_snapshot(일수) 한 번이면 릴스·블로그·랜딩(/start)·가입·잔존을 숫자 한 묶음으로 돌려준다
--       비서 예약 작업(매일 저녁)과 릴스 품질 점검·주간 대본 작업이 이 숫자를 읽고 판단한다
-- 운영자·체험 계정과 그 기기·IP 방문은 admin_stats 와 같은 기준으로 뺀다

alter table public.social_posts add column if not exists ig_insights jsonb;
alter table public.social_posts add column if not exists ig_insights_at timestamptz;

create table if not exists public.metrics_daily (
  day date not null, k text not null, v jsonb not null, primary key (day, k)
);
alter table public.metrics_daily enable row level security;  -- 정책 없음: 서비스 키·보안 함수만 읽고 쓴다

create or replace function public.agent_snapshot(days int default 7) returns jsonb
language plpgsql stable security definer set search_path = public, auth as
$$
declare
  t1 timestamptz := now();
  t0 timestamptz := now() - make_interval(days => days);
  tp timestamptz := now() - make_interval(days => days * 2);
  staff uuid[];
  res jsonb;
begin
  if not (current_user in ('postgres', 'service_role', 'supabase_admin') or public.is_admin()) then
    raise exception 'not admin';
  end if;
  staff := array(select id from auth.users where id in (public.publisher_id(), public.demo_id())
                  or email in (select jsonb_array_elements_text(value) from app_config where key = 'admins'));

  with ss as (select distinct sid from events where sid is not null and sid <> 'nosid' and uid = any(staff)),
       sv as (select distinct vk from events where vk is not null and uid = any(staff)),
       e as (select *, coalesce(vk, 's:' || sid) who, at >= t0 cur from events
             where at >= tp and (uid is null or not (uid = any(staff)))
               and (vk is null or vk not in (select vk from sv))
               and (sid is null or sid not in (select sid from ss))),
       src as (select who, cur, min(case when ref like 'ad-%' then 'ad' when ref like 'ig%' then 'instagram(프로필 링크·광고)' when ref like '%facebook%' then 'facebook(링크 공유)'
                                      when ref like 'naver%' then 'naver-blog' when ref like 'c%' then 'company-page'
                                      when coalesce(ref, '') = '' then '(직접)' else 'other' end) s
               from e where kind = 'visit' group by who, cur),
       st as (select path, count(distinct who) u from e where cur and path like '/start%' group by path),
       su as (select distinct on (s.who) s.who, s.at, s.uid from e s where s.kind = 'signup' order by s.who, s.at),
       sus as (select su.*, (select src.s from src where src.who = su.who order by src.cur desc limit 1) s,
                      exists(select 1 from e x where x.who = su.who and x.path like '/start%') via_start from su),
       adv as (select who, min(ref) ad from e where cur and kind = 'visit' and ref like 'ad-%' group by who),
       nu as (select id, created_at from auth.users where not (id = any(staff))),
       act as (select uid, (at at time zone 'Asia/Seoul')::date d from events where uid is not null and not (uid = any(staff)) group by 1, 2),
       rp as (select p.id, p.title, p.scheduled_at, p.ig_at, p.ig_insights i from social_posts p
              where p.kind = 'reel' and p.ig_status = 'posted' and p.ig_at >= t0)
  select jsonb_build_object(
    'asOf', to_char(t1 at time zone 'Asia/Seoul', 'YYYY-MM-DD HH24:MI') || ' KST', 'days', days,
    -- 1) 릴스: 성과 순. avgWatchS = 평균 시청 초, shareRate·saveRate = 도달 대비 %
    'reels', coalesce((select jsonb_agg(r order by (r->>'views')::numeric desc nulls last, (r->>'likes')::numeric desc nulls last) from (
        select jsonb_build_object('id', id, 'title', title,
          'posted', to_char(ig_at at time zone 'Asia/Seoul', 'MM-DD HH24:MI'), 'hours', (i->>'hours')::int,
          'views', (i->>'views')::numeric, 'reach', (i->>'reach')::numeric,
          'avgWatchS', round(coalesce((i->>'ig_reels_avg_watch_time')::numeric, 0) / 1000, 1),
          'saved', (i->>'saved')::numeric, 'shares', (i->>'shares')::numeric, 'likes', (i->>'likes')::numeric, 'comments', (i->>'comments')::numeric, 'insights', not (i ? 'noInsights'),
          'saveRate', round(100 * (i->>'saved')::numeric / nullif((i->>'reach')::numeric, 0), 2),
          'shareRate', round(100 * (i->>'shares')::numeric / nullif((i->>'reach')::numeric, 0), 2)) r from rp) x), '[]'::jsonb),
    'reelsNoData', (select count(*) from rp where i is null),
    'reelsFailed', coalesce((select jsonb_agg(jsonb_build_object('id', id, 'title', title, 'err', left(ig_error, 120)))
        from social_posts where kind = 'reel' and ig_status in ('error', 'failed') and scheduled_at >= t0), '[]'::jsonb),
    'reelsNext24h', (select count(*) from social_posts where kind = 'reel' and ig_status = 'pending' and approved and not coalesce(paused, false)
        and scheduled_at between t1 and t1 + interval '24 hours'),
    'followers', (select jsonb_agg(jsonb_build_object('day', day, 'n', v->'followers') order by day)
        from metrics_daily where k = 'ig_account' and day >= (t0 at time zone 'Asia/Seoul')::date - 1),
    -- 2) 유입: 사람 수(같은 IP·기기는 1명), 이번 기간 vs 직전 같은 기간
    'visitors', jsonb_build_object('cur', (select count(distinct who) from src where cur), 'prev', (select count(distinct who) from src where not cur)),
    'bySource', coalesce((select jsonb_object_agg(s, jsonb_build_object('cur', c, 'prev', p)) from (
        select s, count(*) filter (where cur) c, count(*) filter (where not cur) p from src group by s) x), '{}'::jsonb),
    -- 3) 랜딩 페이지(/start) 단계별 도달 사람 수: s0 첫 화면 … s8 끝, t15·t60 = 15초·60초 머묾, cta-* = 가입 버튼
    'start', coalesce((select jsonb_object_agg(replace(path, '/start:', ''), u) from st), '{}'::jsonb),
    -- 4) 가입: 경로별, /start 를 거쳤는지
    'signups', jsonb_build_object('cur', (select count(*) from sus where at >= t0), 'prev', (select count(*) from sus where at < t0),
        'viaStart', (select count(*) from sus where at >= t0 and via_start),
        'bySource', coalesce((select jsonb_object_agg(coalesce(s, '?'), n) from (select s, count(*) n from sus where at >= t0 group by s) x), '{}'::jsonb)),
    -- 5) 잔존: 가입 다음 날 이후 다시 온 사람 비율, 최근 이용자
    'retention', jsonb_build_object(
        'users', (select count(*) from nu),
        'returnedAfterDay1', (select count(*) from nu where exists (select 1 from act a where a.uid = nu.id and a.d > (nu.created_at at time zone 'Asia/Seoul')::date)),
        'eligible', (select count(*) from nu where created_at < now() - interval '1 day'),
        'active7d', (select count(distinct uid) from act where d >= (now() at time zone 'Asia/Seoul')::date - 6),
        'pushOn', (select count(distinct owner) from docs where collection = 'push_subs' and not (owner = any(staff))),
        'withHoldings', (select count(distinct owner) from docs where collection = 'holdings' and not (owner = any(staff)))),
    -- 6) 앱 안에서 많이 본 화면(이번 기간)
    'topViews', coalesce((select jsonb_object_agg(path, u) from (select path, count(distinct who) u from e
        where cur and kind = 'view' and path not like '/start%' group by path order by 2 desc limit 8) x), '{}'::jsonb),
    -- 7) 블로그: 네이버 블로그에서 들어온 사람과 올린 글 수
    -- 8) 광고: 홍보 링크 ?ref=ad-<릴스 id> 별로 방문 → 랜딩 다음 단계(s1) → 가입. spend = 사장님이 알려 준 광고비(원)
    'ads', jsonb_build_object(
        'byAd', coalesce((select jsonb_object_agg(ad, jsonb_build_object('visitors', v, 'reachedS1', s1, 'signups', sg,
                   'spendKrw', (select sum((x->>'krw')::numeric) from docs d, jsonb_array_elements(d.data -> 'entries') x
                                where d.collection = 'agent' and d.id = 'ad-spend' and d.owner = public.publisher_id()
                                  and x->>'ref' = ad and (x->>'date')::date >= (t0 at time zone 'Asia/Seoul')::date))) from (
            select a.ad, count(*) v,
                   count(*) filter (where exists (select 1 from e x where x.who = a.who and x.path = '/start:s1')) s1,
                   count(*) filter (where exists (select 1 from sus where sus.who = a.who and sus.at >= t0)) sg
            from adv a group by a.ad) q), '{}'::jsonb),
        'untaggedFacebook', (select count(*) from src where cur and s = 'facebook(링크 공유)'),
        'spendTotalKrw', (select sum((x->>'krw')::numeric) from docs d, jsonb_array_elements(d.data -> 'entries') x
                          where d.collection = 'agent' and d.id = 'ad-spend' and d.owner = public.publisher_id()
                            and (x->>'date')::date >= (t0 at time zone 'Asia/Seoul')::date)),
    'blog', jsonb_build_object('visitors', (select count(*) from src where cur and s = 'naver-blog'),
        'posted', (select count(*) from docs, jsonb_each_text(data -> 'posted') p where collection = 'naver' and p.value::date >= (t0 at time zone 'Asia/Seoul')::date))
  ) into res;
  return res;
end $$;

revoke all on function public.agent_snapshot(int) from public, anon;
grant execute on function public.agent_snapshot(int) to authenticated, service_role;

-- 3시간마다 성과 수집 (KST 00:20, 03:20 …)
select cron.unschedule(jobid) from cron.job where jobname = 'haeja-perf';
select cron.schedule('haeja-perf', '20 */3 * * *', $$select public._fn_call('perf-collect', '{}')$$);
