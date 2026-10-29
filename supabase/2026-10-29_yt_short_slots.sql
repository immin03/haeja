-- 2026-10-29 유튜브 쇼츠 슬롯 규칙 (대표님 결정)
-- "슬롯을 3개일 때와 4~5개일 때를 각각 두고, 하나가 추가되면 남는 칸에, 우선순위면 기존 칸에 넣고 원래 거는 뒤로.
--  쇼츠는 11시(23시) 전에 다 끝내고, 하루 3개 많게는 5개. 벤치마킹 승인분은 렌더 끝나는 시간 계산해서 최대한 빨리."
--
-- 슬롯(KST): 기본 07:40 · 12:10 · 19:40 / 추가 17:40 · 21:40 / 하루 최대 5편 / 22:59 이후 금지
-- 우선순위: 2 = 벤치마킹 승인 반영(노트에 '벤치마킹'), 1 = 급변·실적(id 끝 u·q 또는 노트 '급변'·'실적'), 0 = 일반
--   우선순위 편: 렌더 끝난 시각 + 30분 이후의 가장 빠른 칸(기본·추가 구분 없이). 아직 스튜디오에 안 올라간 일반 편이 있던 칸이면 그 칸을 차지하고 일반 편은 뒤로 밀림.
--   일반 편: 원래 날짜의 기본 칸 먼저 → 그날 추가 칸 → 다음 날.
-- 이미 스튜디오에 올라간 편(youtube_id 있음 또는 status uploaded)은 움직이지 않고, 그 앞뒤 90분 안의 칸을 막는다.

alter table public.youtube_posts add column if not exists priority smallint;

insert into public.app_config (key, value) values ('yt_short_slots',
  '{"base":["07:40","12:10","19:40"],"extra":["17:40","21:40"],"max_per_day":5,"latest":"22:59","lead_min":30,"block_min":90}'::jsonb)
on conflict (key) do update set value = excluded.value;

create or replace function public.yt_short_prio(p public.youtube_posts) returns int
language sql stable as $$
  select coalesce(p.priority::int,
    case when coalesce(p.note,'') like '%벤치마킹%' then 2
         when p.id ~ '[uq]$' or coalesce(p.note,'') ~ '(급변|실적)' then 1
         else 0 end)
$$;

create or replace function public.yt_short_reslot(dry boolean default false) returns jsonb
language plpgsql security definer set search_path to 'public' as $$
declare
  cfg jsonb; lead interval; blk interval; mx int; tz text := 'Asia/Seoul';
  d0 date; d int; t text; s timestamptz; earliest timestamptz;
  fixed timestamptz[] := '{}'; r record; pick timestamptz; moved jsonb := '[]'::jsonb;
begin
  select value into cfg from app_config where key = 'yt_short_slots';
  lead := make_interval(mins => coalesce((cfg->>'lead_min')::int, 30));
  blk  := make_interval(mins => coalesce((cfg->>'block_min')::int, 90));
  mx   := coalesce((cfg->>'max_per_day')::int, 5);
  d0   := (now() at time zone tz)::date;

  -- 후보 칸 (오늘~8일 뒤)
  create temp table if not exists _slots (at timestamptz, day date, extra boolean) on commit drop;
  truncate _slots;
  for d in 0..8 loop
    for t in select jsonb_array_elements_text(cfg->'base') loop
      insert into _slots values (((d0 + d)::text || ' ' || t)::timestamp at time zone tz, d0 + d, false);
    end loop;
    for t in select jsonb_array_elements_text(cfg->'extra') loop
      insert into _slots values (((d0 + d)::text || ' ' || t)::timestamp at time zone tz, d0 + d, true);
    end loop;
  end loop;

  -- 움직이지 않는 편 (스튜디오에 이미 있음)
  select coalesce(array_agg(scheduled_at), '{}') into fixed from youtube_posts
   where kind = 'short' and scheduled_at > now() - interval '1 day'
     and (status = 'uploaded' or youtube_id is not null) and status not in ('hold','deleted','stale');

  for r in
    select p.id, p.scheduled_at, p.rendered_at, public.yt_short_prio(p) pr
      from youtube_posts p
     where p.kind = 'short' and p.status in ('review','approved') and p.youtube_id is null
       and p.scheduled_at > now() - interval '3 days'
     order by public.yt_short_prio(p) desc, p.scheduled_at, p.id
  loop
    earliest := greatest(now() + lead, coalesce(r.rendered_at, now()) + lead);
    if r.pr = 0 then
      earliest := greatest(earliest, ((r.scheduled_at at time zone tz)::date)::timestamp at time zone tz);
    end if;
    select x.at into pick from _slots x
     where x.at >= earliest
       and not exists (select 1 from unnest(fixed) f where abs(extract(epoch from f - x.at)) < extract(epoch from blk))
       and (select count(*) from unnest(fixed) f where (f at time zone tz)::date = x.day) < mx
     order by case when r.pr = 0 then x.day end, case when r.pr = 0 then x.extra end, x.at
     limit 1;
    if pick is null then continue; end if;
    fixed := fixed || pick;
    if pick is distinct from r.scheduled_at then
      moved := moved || jsonb_build_object('id', r.id, 'from', to_char(r.scheduled_at at time zone tz, 'MM-DD HH24:MI'),
                                           'to', to_char(pick at time zone tz, 'MM-DD HH24:MI'), 'prio', r.pr);
      if not dry then
        update youtube_posts set scheduled_at = pick, updated_at = now(),
          events = coalesce(events,'[]'::jsonb) || jsonb_build_array(jsonb_build_object('at', now(), 'by', 'slot',
            'what', '쇼츠 슬롯 배정 ' || to_char(pick at time zone tz, 'MM-DD HH24:MI') || case when r.pr > 0 then ' (우선순위 ' || r.pr || ')' else '' end))
         where id = r.id;
      end if;
    end if;
  end loop;
  return moved;
end $$;

grant execute on function public.yt_short_reslot(boolean) to authenticated, service_role;

-- 재렌더·새 편이 들어올 때마다 자동으로 칸을 다시 맞춘다
create or replace function public.yt_import()
 returns integer language plpgsql security definer set search_path to 'public' as $function$
declare rid bigint; body jsonb; x jsonb; n int := 0;
begin
  select (value #>> '{}')::bigint into rid from app_config where key = 'yt_req';
  if rid is null then return 0; end if;
  select content::jsonb into body from net._http_response where id = rid and status_code = 200;
  if body is null or jsonb_typeof(body) <> 'array' then return 0; end if;
  for x in select * from jsonb_array_elements(body) loop
    insert into youtube_posts (id, kind, title, description, tags, scheduled_at, duration, video_url, thumb, data, data_asof, events, company, rendered_at, pinned_comment, status, subs, title_en, description_en)
    values (x->>'id', coalesce(x->>'kind','long'), x->>'title', x->>'description', array(select jsonb_array_elements_text(coalesce(x->'tags','[]'))),
      (x->>'scheduled_at')::timestamptz, (x->>'duration')::numeric, x->>'video_url', x->>'thumb', x->'data', (x->>'data_asof')::timestamptz,
      coalesce(x->'events','[]'), x->>'company', (x->>'rendered_at')::timestamptz, x->>'pinned_comment', 'review',
      case when jsonb_typeof(x->'subs') = 'object' then x->'subs' end, x->>'title_en', x->>'description_en')
    on conflict (id) do update set title = excluded.title, description = excluded.description, tags = excluded.tags,
      -- 쇼츠는 슬롯 배정이 정한 시각을 유지한다 (대본의 scheduled_at 은 희망 날짜일 뿐)
      scheduled_at = case when youtube_posts.kind = 'short' then youtube_posts.scheduled_at else excluded.scheduled_at end,
      duration = excluded.duration, video_url = excluded.video_url, thumb = excluded.thumb,
      data = excluded.data, data_asof = excluded.data_asof, events = excluded.events, rendered_at = excluded.rendered_at,
      pinned_comment = excluded.pinned_comment, status = 'review', stale_reason = null, updated_at = now(),
      subs = coalesce(youtube_posts.subs, '{}'::jsonb) || coalesce(excluded.subs, '{}'::jsonb),
      title_en = coalesce(excluded.title_en, youtube_posts.title_en),
      description_en = coalesce(excluded.description_en, youtube_posts.description_en)
      where youtube_posts.status <> 'uploaded' and youtube_posts.rendered_at is distinct from excluded.rendered_at;
    if found then n := n + 1; end if;
  end loop;
  perform public.yt_check_stale();
  perform public.yt_short_reslot();
  return n;
end $function$;
