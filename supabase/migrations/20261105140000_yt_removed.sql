-- 2026-11-05 대표: "몇 번 없애라고 했는데 왜 아직도" — 지운 롱폼(10/24 삼성·10/25 테슬라)이 다시 나타나던 문제
-- 원인: 11/4 22:11 대기열 파일(social/youtube/queue.json)에서 뺐지만, 22:16 가져오기(yt_import)가 아직 배포 전인 옛 파일을 읽어 다시 넣었다.
-- 가져오기는 행을 지우지 않으므로 그 뒤로 계속 남아 '렌더 24시간 지남 · 다시 만드는 중'으로 보였다.
-- 고친 것: ① youtube_posts에서 지운 id는 yt_removed에 자동으로 남는다(삭제 트리거)
--          ② yt_import는 yt_removed에 있는 id를 다시 넣지 않는다
--          ③ 반려(hold)한 편은 새 렌더가 들어와도 '검수 대기'로 되돌리지 않는다
create table if not exists public.yt_removed (id text primary key, at timestamptz not null default now(), why text);
alter table public.yt_removed enable row level security;
revoke all on public.yt_removed from anon, authenticated;
create or replace function public._yt_tombstone() returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into yt_removed(id, why) values (old.id, coalesce(current_setting('vn.yt_why', true), '삭제')) on conflict (id) do nothing;
  return old;
end $$;
drop trigger if exists youtube_posts_tombstone on public.youtube_posts;
create trigger youtube_posts_tombstone after delete on public.youtube_posts for each row execute function public._yt_tombstone();
-- yt_import: 루프 첫 줄에 `continue when exists (select 1 from yt_removed where id = x->>'id');`
--            on conflict 갱신 조건을 `youtube_posts.status not in ('uploaded', 'hold')` 로 (실제 DB에 적용됨)
