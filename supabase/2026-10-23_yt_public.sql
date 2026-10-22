-- 2026-10-23 사이트 곳곳(칼럼·랜딩·앱·기업 페이지)에 유튜브 영상을 붙이기 위한 공개 목록 (/yt.js 가 읽는다)
-- 공개 시각이 지난 업로드 영상만 내보내고, 토큰 등 계정 정보는 노출하지 않는다. (이미 적용됨)
create or replace function public.yt_public()
returns jsonb language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'channel', (select jsonb_build_object('title', channel_title, 'handle', handle, 'id', channel_id) from youtube_account where id = 1),
    'videos', coalesce((select jsonb_agg(jsonb_build_object(
        'yid', y.youtube_id, 'kind', y.kind, 'title', regexp_replace(y.title, '\s*#shorts\s*$', ''),
        'company', y.company, 'at', y.scheduled_at, 'dur', y.duration) order by y.scheduled_at desc)
      from youtube_posts y
      where y.status = 'uploaded' and y.youtube_id is not null and y.scheduled_at <= now()), '[]'::jsonb));
$$;
revoke all on function public.yt_public() from public;
grant execute on function public.yt_public() to anon, authenticated;
