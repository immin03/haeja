-- 2026-11-15 대표 "댓글 몇 번째 반복 … 다시는 안 생기게" (DB에 직접 적용함 — 기록용)
-- 원인: vn-yt-auto(썸네일 재설정)와 vn-yt-comment가 같은 5분 cron에서 youtube_posts.data 를 통째로 덮어써 comment_id 가 지워짐 → 다음 회차에 고정 댓글을 또 게시
-- 조치: ① public.yp_merge(id, patch, event) — data·events 부분 병합만(두 함수 모두 이것만 사용)
--       ② vn-yt-comment v2: 게시 전에 유튜브 commentThreads 로 밸류노트 채널 댓글이 이미 있는지 확인 → 있으면 기록만, 같은 문구가 2개 이상이면 가장 오래된 1개만 남기고 자동 삭제
create or replace function public.yp_merge(p_id text, p_patch jsonb default '{}'::jsonb, p_event jsonb default null)
returns void language sql security definer set search_path=public as $$
  update youtube_posts set data = coalesce(data,'{}'::jsonb) || coalesce(p_patch,'{}'::jsonb),
    events = case when p_event is null then events else coalesce(events,'[]'::jsonb) || jsonb_build_array(p_event) end, updated_at = now()
  where id = p_id;
$$;
