-- ⚠ 2026-11-19 작성 · DB에 아직 적용하지 않음 (자동 작업에서 기존 함수 교체가 권한 확인에 걸림 — 대표 승인 후 적용)
-- 적용 방법: Supabase SQL 편집기에 이 파일 내용을 붙여 실행
-- 4) yt_import: 제목·썸네일은 이미 있으면 유지 (대표 승인·데스크 지정 제목/썸네일 보호). 같은 기본 썸네일 파일의 새 버전(?v=)만 갱신.
create or replace function public.yt_import()
 returns integer language plpgsql security definer set search_path to 'public'
as $function$
declare rid bigint; body jsonb; x jsonb; n int := 0;
begin
  select (value #>> '{}')::bigint into rid from app_config where key = 'yt_req';
  if rid is null then return 0; end if;
  select content::jsonb into body from net._http_response where id = rid and status_code = 200;
  if body is null or jsonb_typeof(body) <> 'array' then return 0; end if;
  for x in select * from jsonb_array_elements(body) loop
    continue when exists (select 1 from yt_removed where id = x->>'id');
    insert into youtube_posts (id, kind, title, description, tags, scheduled_at, duration, video_url, thumb, data, data_asof, events, company, rendered_at, pinned_comment, status, subs, title_en, description_en)
    values (x->>'id', coalesce(x->>'kind','long'), x->>'title', x->>'description', array(select jsonb_array_elements_text(coalesce(x->'tags','[]'))),
      (x->>'scheduled_at')::timestamptz, (x->>'duration')::numeric, x->>'video_url', x->>'thumb', x->'data', (x->>'data_asof')::timestamptz,
      coalesce(x->'events','[]'), x->>'company', (x->>'rendered_at')::timestamptz, x->>'pinned_comment', 'review',
      case when jsonb_typeof(x->'subs') = 'object' then x->'subs' end, x->>'title_en', x->>'description_en')
    on conflict (id) do update set
      -- 2026-11-19 대표: 자동 등록이 승인·지정된 제목을 덮어쓰지 않는다 (렌더 제목이 다르면 events 에 남김)
      title = coalesce(nullif(youtube_posts.title, ''), excluded.title),
      description = excluded.description, tags = excluded.tags,
      scheduled_at = case when youtube_posts.kind = 'short' then youtube_posts.scheduled_at else excluded.scheduled_at end,
      duration = excluded.duration, video_url = excluded.video_url,
      thumb = case when coalesce(youtube_posts.thumb, '') = '' then excluded.thumb
                   when split_part(youtube_posts.thumb, '?', 1) = split_part(excluded.thumb, '?', 1) then excluded.thumb
                   else youtube_posts.thumb end,
      data = excluded.data, data_asof = excluded.data_asof,
      events = coalesce(youtube_posts.events,'[]'::jsonb) || jsonb_build_array(jsonb_build_object('at', now(), 'by', 'import', 'what', '새 렌더 들어옴 ' || to_char((excluded.rendered_at) at time zone 'Asia/Seoul', 'MM-DD HH24:MI')))
        || case when coalesce(youtube_posts.title, '') <> '' and youtube_posts.title is distinct from excluded.title
                then jsonb_build_array(jsonb_build_object('at', now(), 'by', 'import', 'what', '렌더 제목이 달라 기존 제목 유지', 'render_title', excluded.title))
                else '[]'::jsonb end,
      rendered_at = excluded.rendered_at,
      pinned_comment = excluded.pinned_comment,
      status = case when youtube_posts.status = 'changes' then 'changes' else 'review' end,
      stale_reason = null, updated_at = now(),
      subs = coalesce(youtube_posts.subs, '{}'::jsonb) || coalesce(excluded.subs, '{}'::jsonb),
      title_en = coalesce(excluded.title_en, youtube_posts.title_en),
      description_en = coalesce(excluded.description_en, youtube_posts.description_en)
      where youtube_posts.status not in ('uploaded', 'hold') and youtube_posts.rendered_at is distinct from excluded.rendered_at;
    if found then n := n + 1; end if;
  end loop;
  perform public.yt_check_stale();
  perform public.yt_short_reslot();
  return n;
end $function$;
