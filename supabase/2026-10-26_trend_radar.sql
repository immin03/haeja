-- 트렌드 레이더 (2026-10-26 운영자): "플랫폼·카테고리·채널 트래픽을 고려해서 지금 가장 핫한 주식·금융 이야기,
-- 유튜브에서 많이 올리는 주제의 통계 대시보드가 필요하고, 이걸로 상위 몇 개만 기획안에 올라오게."
-- + "과거 트래픽을 고려해서 빼빼로데이 전에 미리 콘텐츠를 만든다든지."
-- 참고: 주언규 '핫비디오' — 검색어 여러 개로 영상을 모아 일간 조회수 증가량을 추적하고,
--       평소보다 갑자기 튀는 영상의 '구조'(제목·썸네일·전개)를 모아 다른 카테고리에서 가져온다.
--
-- 1) issue_events   : 연간 이슈 캘린더. 날짜 - lead_days(기본 14일)가 되면 대기열 작업(Claude)이 시즌 기획안을 미리 만든다.
-- 2) trend_queries  : 핫비디오 검색어 (금융 + 인접 카테고리, 한국·영어)
-- 3) trend_videos / trend_snaps : 검색에서 찾은 영상과 하루 1번 조회수 스냅샷 → 증가량·급등 배수
-- 4) trend_stocks   : 네이버 금융 검색 상위·야후 트렌딩 종목 (하루 1번)
-- 수집은 edge function trend-collect 가 매일 07:25 KST (pg_cron) 에 한다. 구조 태그는 대기열 작업(Claude)이 붙인다.

create table if not exists public.issue_events (
  id text primary key,
  day date not null,
  title text not null,
  kind text not null default 'season',      -- season | macro | earnings | event
  cat text,                                  -- 소비·유통 / 반도체 / 매크로 …
  angle text,                                -- 밸류노트식 각도 힌트 (돈 버는 구조·숫자)
  companies text[] default '{}',
  lead_days int not null default 14,
  est boolean not null default false,        -- 날짜가 추정치인지
  source text,
  plan_id text,                              -- 이 이슈로 만든 기획안 id
  auto boolean not null default false,       -- trend-collect 가 넣은 실적 일정
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists issue_events_day on public.issue_events(day);

create table if not exists public.trend_queries (
  q text primary key,
  cat text not null,          -- 금융 | 인접:여행 …
  lang text not null default 'ko',
  active boolean not null default true
);

create table if not exists public.trend_videos (
  video_id text primary key,
  title text not null,
  channel text,
  channel_id text,
  length_text text,
  published_text text,
  published_est timestamptz,
  lang text,
  cats text[] default '{}',
  queries text[] default '{}',
  first_seen timestamptz not null default now(),
  last_seen timestamptz not null default now(),
  structure jsonb,             -- Claude 태그 {title_pattern, thumb_pattern, story_pattern, value, topic, transfer}
  tagged_at timestamptz
);

create table if not exists public.trend_snaps (
  video_id text not null references public.trend_videos(video_id) on delete cascade,
  day date not null,
  views bigint not null,
  taken_at timestamptz not null default now(),
  primary key (video_id, day)
);

create table if not exists public.trend_stocks (
  day date not null,
  src text not null,          -- naver_search | yahoo_us
  rank int not null,
  name text not null,
  code text,
  price text,
  change text,
  primary key (day, src, rank)
);

alter table public.issue_events enable row level security;
alter table public.trend_queries enable row level security;
alter table public.trend_videos enable row level security;
alter table public.trend_snaps enable row level security;
alter table public.trend_stocks enable row level security;
-- 정책 없음: 서비스 키(edge function)와 아래 security definer 함수로만 읽고 쓴다.

-- 급등 계산: 최신 스냅샷의 하루 증가량 vs 그 전 증가량 평균.
-- 처음 본 영상은 (조회수 ÷ 올린 지 며칠)로 속도를 추정한다.
create or replace view public.trend_hot with (security_invoker = true) as
with s as (
  select video_id, day, views, taken_at,
         lag(views) over w as pv, lag(taken_at) over w as pt,
         row_number() over (partition by video_id order by day desc) as rn
  from public.trend_snaps window w as (partition by video_id order by day)
), d as (
  select video_id, day, views, rn,
         case when pv is null then null
              else greatest(views - pv, 0) / greatest(extract(epoch from taken_at - pt) / 86400.0, 0.25) end as per_day
  from s
), agg as (
  select video_id,
         max(views) filter (where rn = 1) as views,
         max(day) filter (where rn = 1) as day,
         max(per_day) filter (where rn = 1) as delta,
         avg(per_day) filter (where rn > 1 and per_day is not null) as base,
         count(*) as snaps
  from d group by video_id
)
select v.video_id, v.title, v.channel, v.cats, v.queries, v.lang, v.length_text, v.published_text, v.published_est,
       v.structure, v.tagged_at, a.views, a.day, a.snaps,
       coalesce(a.delta, a.views / greatest(extract(epoch from now() - coalesce(v.published_est, v.first_seen)) / 86400.0, 1)) as per_day,
       a.base,
       case when a.base is not null and a.base > 0 then round((a.delta / a.base)::numeric, 1) end as spike,
       case
         when a.base is not null and a.delta >= 3000 and a.delta >= a.base * 2 then 'spike'          -- 평소보다 2배 넘게 튐
         when a.delta is null and v.published_est > now() - interval '4 days'
              and a.views / greatest(extract(epoch from now() - v.published_est) / 86400.0, 0.5) >= 20000 then 'fast_new'  -- 새 영상이 빠르게 큼
         when coalesce(a.delta, 0) >= 20000 then 'steady'                                              -- 꾸준히 많이 봄
         else null end as flag
from public.trend_videos v join agg a using (video_id)
where a.day >= (now() at time zone 'Asia/Seoul')::date - 1
  -- 90초 미만(쇼츠)은 롱폼 기획에 잡음이라 뺀다 (적용본은 이 정의를 한 번 더 감싼 형태로 들어가 있음, 결과 동일)
  and not (v.length_text ~ '^\d{1,2}:\d\d$' and split_part(v.length_text, ':', 1)::int * 60 + split_part(v.length_text, ':', 2)::int < 90);

-- 관리자 트렌드 탭 + 기획안 작업이 읽는 한 덩어리
create or replace function public.trend_admin(p_days int default 45)
returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare today date := (now() at time zone 'Asia/Seoul')::date;
begin
  if not (public.is_admin() or session_user = 'postgres') then raise exception 'not admin'; end if;
  return jsonb_build_object(
    'today', today,
    'last_run', (select max(taken_at) from trend_snaps),
    'counts', jsonb_build_object('videos', (select count(*) from trend_videos), 'queries', (select count(*) from trend_queries where active),
                                 'tagged', (select count(*) from trend_videos where structure is not null)),
    'hot', coalesce((select jsonb_agg(to_jsonb(h) - 'queries' order by (h.flag = 'spike') desc, h.per_day desc)
                     from (select * from trend_hot where flag is not null order by (flag = 'spike') desc, per_day desc limit 60) h), '[]'),
    'structures', coalesce((select jsonb_agg(x order by (x->>'n')::int desc) from (
        select jsonb_build_object('pattern', structure->>'title_pattern', 'n', count(distinct video_id), 'cats', array_agg(distinct c),
               'best', (array_agg(distinct title))[1:3], 'transfer', (array_agg(structure->>'transfer' order by per_day desc))[1]) x
        from trend_hot, unnest(cats) c where structure ? 'title_pattern' and structure->>'title_pattern' <> ''
        group by structure->>'title_pattern' order by count(distinct video_id) desc limit 20) t), '[]'),
    'issues', coalesce((select jsonb_agg(to_jsonb(e) || jsonb_build_object('d_minus', e.day - today,
                          'plan_status', (select p.data->>'status' from docs p where p.collection = 'yt_plans' and p.owner = public.publisher_id() and p.id = e.plan_id))
                        order by e.day)
                       from issue_events e where e.day between today and today + p_days), '[]'),
    'due', coalesce((select jsonb_agg(e.id order by e.day) from issue_events e
                     where e.day > today and e.day - e.lead_days <= today and e.plan_id is null and e.kind in ('season', 'event')), '[]'),
    'stocks', coalesce((select jsonb_agg(to_jsonb(s) order by s.src, s.rank) from trend_stocks s
                        where s.day = (select max(day) from trend_stocks)), '[]')
  );
end $f$;

create or replace function public.issue_upsert(p jsonb)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare nid text := coalesce(nullif(p->>'id', ''), 'I' || to_char(now(), 'YYMMDDHH24MISS'));
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  if p ? 'delete' then delete from issue_events where id = p->>'id' and not auto; return jsonb_build_object('ok', true); end if;
  insert into issue_events (id, day, title, kind, cat, angle, lead_days, source)
  values (nid, (p->>'day')::date, p->>'title', coalesce(p->>'kind', 'season'), p->>'cat', p->>'angle', coalesce((p->>'lead_days')::int, 14), '관리자 입력')
  on conflict (id) do update set day = excluded.day, title = excluded.title, kind = excluded.kind, cat = excluded.cat,
     angle = excluded.angle, lead_days = excluded.lead_days, updated_at = now();
  return jsonb_build_object('ok', true, 'id', nid);
end $f$;

revoke all on function public.trend_admin(int) from public, anon;
revoke all on function public.issue_upsert(jsonb) from public, anon;
grant execute on function public.trend_admin(int) to authenticated;
grant execute on function public.issue_upsert(jsonb) to authenticated;
revoke all on public.trend_hot from public, anon, authenticated;

-- 매일 07:25 KST (UTC 22:25 전날) 수집
select cron.unschedule('haeja-trend-collect') where exists (select 1 from cron.job where jobname = 'haeja-trend-collect');
select cron.schedule('haeja-trend-collect', '25 22 * * *', $$select public._fn_call('trend-collect', '{}')$$);
-- 오래된 스냅샷 정리 (90일)
select cron.unschedule('haeja-trend-prune') where exists (select 1 from cron.job where jobname = 'haeja-trend-prune');
select cron.schedule('haeja-trend-prune', '50 22 * * 0', $$delete from public.trend_videos where last_seen < now() - interval '90 days' and structure is null$$);
