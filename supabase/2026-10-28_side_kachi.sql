-- 까치 감성 쇼츠 방향 개편 (2026-10-28)
-- 1) 반려 = '수정 요청'(rework): 코멘트를 feedback 기록에 남기고, 고친 뒤 다시 검수로 올린다
-- 2) 트렌드: 감성 쇼츠 실제 조회수 수집(sc_hot_*) + 까치 소재·시즌 일정(sc_trends 확장)
-- 3) 이전 방향(롱폼·네티즌 반응) 데이터는 보관(archived/legacy)

-- ---------- 수정 요청 흐름 ----------
do $$ declare c record; begin
  for c in select conname, conrelid::regclass t from pg_constraint
    where conrelid::regclass::text in ('sc_videos','sc_plans','sc_trends') and contype = 'c' and pg_get_constraintdef(oid) ilike '%status%'
  loop execute format('alter table %s drop constraint %I', c.t, c.conname); end loop;
end $$;

alter table sc_videos add column if not exists feedback jsonb not null default '[]';
alter table sc_videos add constraint sc_videos_status_check
  check (status in ('review','rework','approved','uploaded','rejected','archived'));

alter table sc_plans add column if not exists feedback jsonb not null default '[]';
alter table sc_plans add column if not exists emotion text;
alter table sc_plans add column if not exists korea text;
alter table sc_plans add column if not exists spec jsonb not null default '{}';   -- music, pinned, description, tags
alter table sc_plans add constraint sc_plans_status_check
  check (status in ('requested','pending','rework','approved','producing','made','rejected'));

-- ---------- 트렌드: 소재·시즌 ----------
alter table sc_trends add column if not exists kind text not null default 'idea';   -- idea | season | legacy
alter table sc_trends add column if not exists emotion text;                         -- mom, grand, animal, kind, korea, underdog
alter table sc_trends add column if not exists korea text;                           -- 화면에 보일 한국 장면
alter table sc_trends add column if not exists apply text;                           -- 까치 버전 줄거리
alter table sc_trends add column if not exists evidence jsonb not null default '[]'; -- [{video_id,title,views,channel}]
alter table sc_trends add column if not exists day date;                             -- 시즌 날짜
alter table sc_trends add column if not exists upload_by date;                       -- 늦어도 이날까지 올리기
alter table sc_trends add constraint sc_trends_status_check check (status in ('new','picked','skipped'));

update sc_trends set kind = 'legacy', status = 'skipped' where kind = 'idea' and line in ('sports','kpop','drama','news','story','life');

-- ---------- 감성 쇼츠 조회수 수집 ----------
create table if not exists sc_hot_queries (
  q text primary key, cat text not null, lang text not null default 'en', active boolean not null default true);
create table if not exists sc_hot_videos (
  video_id text primary key, title text, channel text, channel_id text, cats text[] not null default '{}', queries text[] not null default '{}',
  lang text, length_sec int, published_est timestamptz, first_seen timestamptz not null default now(), last_seen timestamptz not null default now());
create table if not exists sc_hot_snaps (
  video_id text not null references sc_hot_videos(video_id) on delete cascade, day date not null, views bigint not null,
  taken_at timestamptz not null default now(), primary key (video_id, day));

alter table sc_hot_queries enable row level security;
alter table sc_hot_videos enable row level security;
alter table sc_hot_snaps enable row level security;
drop policy if exists sc_hot_queries_admin on sc_hot_queries;
drop policy if exists sc_hot_videos_admin on sc_hot_videos;
drop policy if exists sc_hot_snaps_admin on sc_hot_snaps;
create policy sc_hot_queries_admin on sc_hot_queries for all to authenticated using (is_admin()) with check (is_admin());
create policy sc_hot_videos_admin on sc_hot_videos for all to authenticated using (is_admin()) with check (is_admin());
create policy sc_hot_snaps_admin on sc_hot_snaps for all to authenticated using (is_admin()) with check (is_admin());

-- 영상별 최신 조회수, 하루 증가량(전날 스냅샷이 있으면 그 차이, 없으면 올린 뒤 하루 평균), 올린 지 며칠
create or replace view sc_hot with (security_invoker = true) as
with s as (
  select video_id, day, views, taken_at,
    lag(views) over w pv, lag(taken_at) over w pt, row_number() over (partition by video_id order by day desc) rn
  from sc_hot_snaps window w as (partition by video_id order by day)
)
select v.video_id, v.title, v.channel, v.cats, v.queries, v.lang, v.length_sec, v.published_est, v.first_seen,
  s.views, s.day,
  round(extract(epoch from (now() - coalesce(v.published_est, v.first_seen))) / 86400.0, 1) as age_days,
  case when s.pv is not null then round(greatest(s.views - s.pv, 0) / greatest(extract(epoch from (s.taken_at - s.pt)) / 86400.0, 0.25))
       else round(s.views / greatest(extract(epoch from (now() - coalesce(v.published_est, v.first_seen))) / 86400.0, 1)) end as per_day,
  (s.pv is not null) as measured
from sc_hot_videos v join s on s.video_id = v.video_id and s.rn = 1;

-- 검색어 (영어 위주, 한국어 일부). cat = 감정 유형
insert into sc_hot_queries (q, cat, lang) values
 ('mom sacrifice story animation','mom','en'), ('mother love short film','mom','en'), ('mom packed lunch story','mom','en'), ('single mom emotional story','mom','en'),
 ('grandma love animation','grand','en'), ('grandpa emotional story','grand','en'), ('grandmother cooking memory','grand','en'),
 ('mother cat kitten story','animal','en'), ('mother bird protects babies','animal','en'), ('dog mom puppies emotional','animal','en'), ('animal mother love','animal','en'),
 ('kindness story animation','kind','en'), ('stray kitten rescue rain','kind','en'), ('small act of kindness short film','kind','en'), ('helping old man story','kind','en'),
 ('korean mom','korea','en'), ('korean grandma','korea','en'), ('korean culture story','korea','en'), ('korea miniature','korea','en'), ('kimchi grandma','korea','en'),
 ('poor cat story ai','underdog','en'), ('sad cat story ai','underdog','en'), ('ai cat family story','underdog','en'),
 ('miniature animation story','style','en'), ('clay animation emotional','style','en'), ('pixar style sad short','style','en'),
 ('엄마 감동','mom','ko'), ('할머니 감동','grand','ko'), ('고양이 감동 실화','animal','ko'), ('감동 애니메이션','style','ko')
on conflict (q) do nothing;

-- ---------- 이전 방향 보관 ----------
update sc_videos set status = 'archived',
  feedback = feedback || jsonb_build_array(jsonb_build_object('at', now(), 'by', 'claude', 'type', 'archive', 'text', '감성 쇼츠로 방향을 바꾸며 보관함으로 옮겼습니다. 보관함에서 다시 검수로 되돌릴 수 있습니다.'))
where status in ('review','approved') and (kind = 'long' or parent_id is not null);
update sc_plans set status = 'rejected' where status = 'pending' and coalesce(emotion, '') = '';

-- 채널 이름
insert into sc_settings (id, value) values (1, '{}'::jsonb) on conflict (id) do nothing;
update sc_settings set value = value || '{"channel_name":"From Korea, With Love"}'::jsonb where id = 1;

-- 업로드일을 모르는 영상은 하루 증가량을 비워 둔다 (같은 날 2차 적용)
create or replace view sc_hot with (security_invoker = true) as
with s as (
  select video_id, day, views, taken_at,
    lag(views) over w pv, lag(taken_at) over w pt, row_number() over (partition by video_id order by day desc) rn
  from sc_hot_snaps window w as (partition by video_id order by day)
)
select v.video_id, v.title, v.channel, v.cats, v.queries, v.lang, v.length_sec, v.published_est, v.first_seen,
  s.views, s.day,
  case when v.published_est is not null then round(extract(epoch from (now() - v.published_est)) / 86400.0, 1) end as age_days,
  case when s.pv is not null then round(greatest(s.views - s.pv, 0) / greatest(extract(epoch from (s.taken_at - s.pt)) / 86400.0, 0.25))
       when v.published_est is not null then round(s.views / greatest(extract(epoch from (now() - v.published_est)) / 86400.0, 1)) end as per_day,
  (s.pv is not null) as measured
from sc_hot_videos v join s on s.video_id = v.video_id and s.rn = 1;

-- 매일 07:40 KST 수집
-- select cron.schedule('side-hot-collect', '40 22 * * *', $$select public._fn_call('sc-trend-collect', '{}')$$);

-- ===== 2026-10-28 13시: 완전 자동 · 하루 3편 =====
-- sc_settings: {"auto": true, "per_day": 3, "slots": ["03:00","08:00","22:00"], "auto_plan": true}
-- sc_import(): 자동 모드면 단독 쇼츠를 'approved'(업로드 대기)로 바로 넣는다. 본문은 Supabase 마이그레이션 side_auto_mode_3_per_day 참고

-- ===== 2026-10-28 13시 반: 하루 4편 · 3일 비축 · 반응 학습 =====
-- update sc_settings set value = value || '{"per_day": 4, "slots": ["03:00","08:00","13:00","22:00"], "buffer_days": 3, "learn": []}'::jsonb where id = 1;
-- select cron.schedule('side-mine-views', '15 */3 * * *', $$select public._fn_call('sc-trend-collect', '{"only":"mine"}')$$);
-- sc_settings.value.learn = [{at, text}] : 작업자가 반응을 보고 정리한 교훈 (관리자 성과 탭에 보임)
