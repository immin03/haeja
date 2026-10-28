-- 까치 채널 벤치마킹 (2026-10-29, Supabase에 이미 적용됨 — 기록용)
-- sc_hot_channels: 터진 쇼츠 채널의 구독자·영상 수·쇼츠 조회수 (sc-trend-collect 의 chan 단계가 채움)
-- sc_improve: 매일 11시 벤치마킹 작업이 쓰는 개선 제안. proposed → (관리자 승인) approved → (작업자 적용) applied / hold / rejected
-- sc_breakout: 구독자 10만 이하 & (조회수 ≥ 구독자×5 또는 영상 ≤ 60개)인 10만 회 이상 쇼츠
create table if not exists sc_hot_channels (channel_id text primary key, name text, handle text, subs bigint, video_count int,
  shorts jsonb default '[]'::jsonb, shorts_n int, shorts_median bigint, shorts_max bigint, checked_at timestamptz default now());
create table if not exists sc_improve (id bigserial primary key, day date not null default (now() at time zone 'Asia/Seoul')::date,
  area text not null default 'story', title text not null, finding text, ours text, apply text, evidence jsonb default '[]'::jsonb,
  impact int default 3, cost text, status text not null default 'proposed', applied_to jsonb default '[]'::jsonb, feedback jsonb default '[]'::jsonb,
  created_at timestamptz default now(), updated_at timestamptz default now());
create or replace view sc_breakout with (security_invoker = on) as
with last as (select distinct on (video_id) * from sc_hot order by video_id, day desc)
select l.video_id, l.title, l.channel, v.channel_id, l.cats, l.length_sec, l.views, l.per_day, l.age_days, l.published_est,
       c.subs, c.video_count, c.shorts_median, c.shorts_n, round(l.views::numeric / greatest(coalesce(c.subs,0),1000), 1) as ratio
from last l join sc_hot_videos v using (video_id) join sc_hot_channels c on c.channel_id = v.channel_id
where c.subs is not null and c.subs <= 100000 and l.views >= 100000
  and (l.views >= 5 * greatest(c.subs,1000) or coalesce(c.video_count,999) <= 60);
alter table sc_hot_channels enable row level security; alter table sc_improve enable row level security;
create policy sc_plans_admin on sc_improve for all to authenticated using (is_admin());
create policy sc_plans_admin on sc_hot_channels for all to authenticated using (is_admin());
