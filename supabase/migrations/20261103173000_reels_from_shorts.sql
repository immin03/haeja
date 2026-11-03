-- 2026-11-03 대표 지시: 쇼츠=릴스 같은 영상, 누락 없이 (DB에 직접 적용함 — 기록용)
-- 1) social_posts.evergreen: 「3가지만/이것만 보면 된다」 등 시기를 타지 않는 편은 social-publish의 '날짜 경과' 보류에서 제외
alter table public.social_posts add column if not exists evergreen boolean not null default false;
-- 2) public.reels_from_shorts(): 승인·업로드된 유튜브 쇼츠(최근 12시간~앞으로)를 같은 영상으로 릴스 대기열에 넣음 (id 'S'||쇼츠 id, 제목·영상 중복이면 건너뜀)
--    pg_cron 'reels-from-shorts' 15분마다 실행. 시각은 ig_reslot이 릴스 슬롯(09:30·13:00·21:00 + 17:30·22:00)에 배치
-- 3) social_posts_dedupe 트리거: 같은 영상·제목의 릴스가 다른 id로 또 들어오면 무시 (레포 queue 가져오기와 겹침 방지)
-- 전체 본문은 Supabase 함수 정의(reels_from_shorts, social_posts_dedupe_trg) 참고
