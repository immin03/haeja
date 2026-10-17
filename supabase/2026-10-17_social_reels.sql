-- 릴스(영상) 게시 지원 + social/reels/queue.json 1시간마다 가져오기 (2026-10-17 적용 완료)
alter table public.social_posts add column if not exists kind text not null default 'carousel';
alter table public.social_posts add column if not exists video text;
alter table public.social_posts add column if not exists cover text;
alter table public.social_posts add column if not exists ig_container text;
alter table public.social_posts add column if not exists th_container text;
alter table public.social_posts alter column images set default '{}';
-- social_reels_fetch / social_reels_import 함수와 cron(haeja-reels-fetch 매시 15분, haeja-reels-import 매시 18분)은
-- Supabase에 직접 적용했다. 정의는 DB의 public.social_reels_import 를 참고.
-- 편성 재정리: 기존 카드뉴스 대기열은 멈춤(paused), 핵심 카드 4편(30·26·07·23)만 월·수·금·일 12:30에 게시.
