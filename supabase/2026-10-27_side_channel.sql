-- 사이드 채널 전용 (2026-10-27)
-- 밸류노트 테이블과 섞이지 않게 sc_ 접두사로 분리한다.
-- 나중에 다른 프로젝트로 옮기거나 접을 때는 sc_ 테이블 4개와 side.html만 다루면 된다.
-- 실행: Supabase 대시보드 → SQL Editor → 이 파일 내용 전체 붙여 넣기 → Run (여러 번 실행해도 안전)

-- 1) 트렌드: 아웃라이어 소재 후보 (채널 평균 대비 몇 배 터졌나 + 댓글 반응 포인트)
create table if not exists public.sc_trends (
  id bigint generated always as identity primary key,
  line text not null default 'news',            -- sports / kpop / drama / news / life
  keyword text not null,                        -- 소재 키워드
  ref_url text,                                 -- 근거 영상
  ref_title text,
  ref_channel text,
  ref_subs bigint,                              -- 근거 채널 구독자 수
  ref_views bigint,                             -- 근거 영상 조회수
  ref_channel_avg bigint,                       -- 근거 채널 최근 영상 평균 조회수
  ratio numeric generated always as (case when coalesce(ref_channel_avg,0) > 0 then round(ref_views::numeric / ref_channel_avg, 1) end) stored,
  reactions jsonb not null default '[]'::jsonb, -- 댓글에서 뽑은 반응 포인트
  score numeric,                                -- 종합 점수 (배수·최근성·경쟁도)
  fresh_until date,                             -- 예상 유효 기간
  status text not null default 'new' check (status in ('new','picked','skipped')),
  collected_at timestamptz not null default now()
);
create index if not exists sc_trends_status_score on public.sc_trends (status, score desc);

-- 2) 기획안
create table if not exists public.sc_plans (
  id text primary key default 'p' || to_char(now() at time zone 'Asia/Seoul','YYMMDDHH24MISS'),
  trend_id bigint references public.sc_trends(id) on delete set null,
  line text not null default 'news',
  title text not null,                          -- 영어 제목
  title_ko text,                                -- 운영자용 한국어 요약
  hook text,                                    -- 첫 10초
  outline jsonb not null default '[]'::jsonb,   -- 장면 목록
  signal jsonb not null default '{}'::jsonb,    -- 근거 요약
  status text not null default 'pending' check (status in ('pending','approved','rejected','made')),
  note text,                                    -- 운영자 의견
  publish_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 3) 영상 (롱폼 + 롱폼에서 자른 쇼츠)
create table if not exists public.sc_videos (
  id text primary key,
  plan_id text references public.sc_plans(id) on delete set null,
  parent_id text references public.sc_videos(id) on delete set null,  -- 쇼츠면 원본 롱폼
  kind text not null default 'long' check (kind in ('long','short')),
  title text not null,
  description text,
  tags text[] default '{}',
  loc jsonb not null default '{}'::jsonb,       -- 언어별 제목·설명 {"es":{"title":"..","description":".."}}
  video_url text,
  thumb text,
  duration numeric,
  status text not null default 'review' check (status in ('review','approved','uploaded','rejected')),
  note text,
  scheduled_at timestamptz,
  youtube_id text,
  stats jsonb not null default '{}'::jsonb,     -- {"h24":{"views":0,"ctr":0,"avg_sec":0},"h48":{...},"d7":{...}}
  reviewed_at timestamptz,
  uploaded_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 4) 설정 (채널명·언어 목록)
create table if not exists public.sc_settings (
  id int primary key default 1 check (id = 1),
  value jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);
insert into public.sc_settings (id, value) values (1,
  '{"channel_name":"","handle":"","auto_dub":true,"langs":["es","pt","id","hi","ja","fr","de","vi","th","ar","tr","it","pl","zh-TW","ru"]}'::jsonb)
on conflict (id) do nothing;

-- 관리자만 읽고 쓴다 (밸류노트 관리자와 같은 계정)
alter table public.sc_trends enable row level security;
alter table public.sc_plans enable row level security;
alter table public.sc_videos enable row level security;
alter table public.sc_settings enable row level security;
drop policy if exists sc_trends_admin on public.sc_trends;
drop policy if exists sc_plans_admin on public.sc_plans;
drop policy if exists sc_videos_admin on public.sc_videos;
drop policy if exists sc_settings_admin on public.sc_settings;
create policy sc_trends_admin on public.sc_trends for all to authenticated using (public.is_admin()) with check (public.is_admin());
create policy sc_plans_admin on public.sc_plans for all to authenticated using (public.is_admin()) with check (public.is_admin());
create policy sc_videos_admin on public.sc_videos for all to authenticated using (public.is_admin()) with check (public.is_admin());
create policy sc_settings_admin on public.sc_settings for all to authenticated using (public.is_admin()) with check (public.is_admin());

create or replace function public.sc_touch() returns trigger language plpgsql set search_path = public as $$ begin new.updated_at = now(); return new; end $$;
drop trigger if exists sc_plans_touch on public.sc_plans;
drop trigger if exists sc_videos_touch on public.sc_videos;
drop trigger if exists sc_settings_touch on public.sc_settings;
create trigger sc_plans_touch before update on public.sc_plans for each row execute function public.sc_touch();
create trigger sc_videos_touch before update on public.sc_videos for each row execute function public.sc_touch();
create trigger sc_settings_touch before update on public.sc_settings for each row execute function public.sc_touch();
