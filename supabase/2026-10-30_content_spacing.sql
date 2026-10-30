-- 2026-10-30 대표님 결정 (채팅 10:27):
-- "릴스의 경우 18:00에 두 개가 올라가는데 그렇게 하지 말고, 오전부터 나눠서 밤까지 고루고루 배포되게 해 줘.
--  모든 콘텐츠는 최소 1시간 간격은 둬야 할 것 같아."
--
-- 인스타(릴스·카드뉴스)와 유튜브(롱폼·쇼츠)는 각 채널 안에서 서로 60분 이상 떨어뜨린다.
--   인스타 칸(KST): 카드뉴스 08:30 · 15:30 · 19:30 / 릴스 09:30 · 13:00 · 21:00 (추가 17:30 · 22:00)
--     → 하루가 08:30 카드 → 09:30 릴스 → 13:00 릴스 → 15:30 카드 → (17:30 릴스) → 19:30 카드 → 21:00 릴스 순으로 고르게 퍼진다.
--   유튜브 칸(KST): 롱폼 11:30 / 쇼츠 07:45 · 13:15 · 19:45 (추가 17:45 · 21:45) — 12:15 칸은 11:30 롱폼과 45분뿐이라 13:15로 옮김.
-- 급변(U·E)·실적(Q) 편과 이미 올라간 편, 20분 안에 올라갈 편은 움직이지 않고 그 앞뒤 60분을 막는다.
-- 제작 작업이 옛 시각(12:30·18:00 등)으로 넣어도 아래 트리거가 바로 새 칸으로 옮긴다.

-- ① 유튜브 쇼츠 칸
update public.app_config set value = value || '{"base":["07:45","13:15","19:45"],"extra":["17:45","21:45"]}'::jsonb where key = 'yt_short_slots';

-- 쇼츠 칸을 고를 때 롱폼 앞뒤도 막는다 (롱폼은 하루 편수에는 세지 않음)
create or replace function public.yt_short_reslot(dry boolean default false) returns jsonb
language plpgsql security definer set search_path to 'public' as $$
declare
  cfg jsonb; lead interval; blk interval; mx int; tz text := 'Asia/Seoul';
  d0 date; d int; t text; earliest timestamptz;
  fixed timestamptz[] := '{}'; longs timestamptz[] := '{}'; r record; pick timestamptz; moved jsonb := '[]'::jsonb;
begin
  select value into cfg from app_config where key = 'yt_short_slots';
  lead := make_interval(mins => coalesce((cfg->>'lead_min')::int, 30));
  blk  := make_interval(mins => coalesce((cfg->>'block_min')::int, 90));
  mx   := coalesce((cfg->>'max_per_day')::int, 5);
  d0   := (now() at time zone tz)::date;

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

  select coalesce(array_agg(scheduled_at), '{}') into fixed from youtube_posts
   where kind = 'short' and scheduled_at > now() - interval '1 day'
     and (status = 'uploaded' or youtube_id is not null) and status not in ('hold','deleted','stale');
  select coalesce(array_agg(scheduled_at), '{}') into longs from youtube_posts
   where kind = 'long' and scheduled_at > now() - interval '1 day' and status in ('review','approved','uploaded');

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
       and not exists (select 1 from unnest(longs) f where abs(extract(epoch from f - x.at)) < 3600)
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

-- ② 인스타 칸
insert into public.app_config (key, value) values ('ig_slots',
  '{"card":["08:30","15:30","19:30"],"reel":["09:30","13:00","21:00"],"reel_extra":["17:30","22:00"],"gap_min":60,"lock_min":20}'::jsonb)
on conflict (key) do update set value = excluded.value;

create or replace function public.ig_reslot(dry boolean default false) returns jsonb
language plpgsql security definer set search_path to 'public' as $$
declare
  cfg jsonb; tz text := 'Asia/Seoul'; gap interval; lockw interval; d0 date; d int; t text;
  fixed timestamptz[] := '{}'; r record; pick timestamptz; moved jsonb := '[]'::jsonb; ok boolean;
begin
  select value into cfg from app_config where key = 'ig_slots';
  if cfg is null then return moved; end if;
  gap   := make_interval(mins => coalesce((cfg->>'gap_min')::int, 60));
  lockw := make_interval(mins => coalesce((cfg->>'lock_min')::int, 20));
  d0    := (now() at time zone tz)::date;

  create temp table if not exists _igs (at timestamptz, day date, kind text, rank int) on commit drop;
  truncate _igs;
  for d in 0..8 loop
    for t in select jsonb_array_elements_text(cfg->'card') loop insert into _igs values (((d0+d)::text||' '||t)::timestamp at time zone tz, d0+d, 'carousel', 0); end loop;
    for t in select jsonb_array_elements_text(cfg->'reel') loop insert into _igs values (((d0+d)::text||' '||t)::timestamp at time zone tz, d0+d, 'reel', 0); end loop;
    for t in select jsonb_array_elements_text(cfg->'reel_extra') loop insert into _igs values (((d0+d)::text||' '||t)::timestamp at time zone tz, d0+d, 'reel', 1); end loop;
  end loop;

  -- 움직이지 않는 편: 올라간 편 · 곧 올라갈 편 · 급변/실적 편
  select coalesce(array_agg(coalesce(ig_at, scheduled_at)), '{}') into fixed from social_posts
   where coalesce(ig_status,'') <> 'deleted' and not coalesce(paused,false) and to_ig is not false and approved is not false
     and coalesce(ig_at, scheduled_at) > now() - interval '1 day'
     and (ig_status = 'posted' or scheduled_at < now() + lockw or id ~ '^(U|E|Q|H)');

  -- 1차: 이미 자기 종류 칸에 있고 간격도 맞는 편은 그대로
  -- 2차: 나머지는 같은 날 기본 칸 → 추가 칸 → 다음 날 순으로
  for r in
    select p.id, p.kind, p.scheduled_at,
           exists (select 1 from _igs x where x.at = p.scheduled_at and x.kind = p.kind) on_slot
      from social_posts p
     where p.ig_status = 'pending' and not coalesce(p.paused,false) and p.to_ig is not false and p.approved is not false
       and p.kind in ('reel','carousel') and p.id !~ '^(U|E|Q|H)'
       and p.scheduled_at >= now() + lockw and p.scheduled_at < now() + interval '8 days'
     order by 4 desc, p.scheduled_at, p.id
  loop
    ok := r.on_slot and not exists (select 1 from unnest(fixed) f where abs(extract(epoch from f - r.scheduled_at)) < extract(epoch from gap));
    if ok then fixed := fixed || r.scheduled_at; continue; end if;
    select x.at into pick from _igs x
     where x.kind = r.kind and x.at >= now() + lockw
       and x.day >= (r.scheduled_at at time zone tz)::date
       and not exists (select 1 from unnest(fixed) f where abs(extract(epoch from f - x.at)) < extract(epoch from gap))
     order by x.day, x.rank, x.at limit 1;
    if pick is null then continue; end if;
    fixed := fixed || pick;
    if pick is distinct from r.scheduled_at then
      moved := moved || jsonb_build_object('id', r.id, 'from', to_char(r.scheduled_at at time zone tz, 'MM-DD HH24:MI'), 'to', to_char(pick at time zone tz, 'MM-DD HH24:MI'));
      if not dry then update social_posts set scheduled_at = pick where id = r.id; end if;
    end if;
  end loop;
  return moved;
end $$;
grant execute on function public.ig_reslot(boolean) to authenticated, service_role;

create or replace function public.ig_reslot_trg() returns trigger
language plpgsql security definer set search_path to 'public' as $$
begin
  -- ig_reslot 안의 update 가 이 트리거를 다시 부르지 않게 막는다 (직접 부를 때도 set_config('vn.igr','1',true) 먼저)
  if coalesce(current_setting('vn.igr', true), '') = '1' then return null; end if;
  perform set_config('vn.igr', '1', true);
  perform public.ig_reslot();
  perform set_config('vn.igr', '', true);
  return null;
end $$;

drop trigger if exists ig_reslot_after on public.social_posts;
create trigger ig_reslot_after after insert or update of scheduled_at, paused, ig_status on public.social_posts
  for each statement execute function public.ig_reslot_trg();

-- ③ 2026-10-30 12:05 대표님: "수정 요청 올렸는데 기획안이 다시 떴고, 수정 요청이 어떻게 되고 있는지 안 나와"
-- 원인: yt_import 가 새 렌더를 들일 때 status 를 무조건 'review' 로 바꿔, 대표 수정 요청(changes)이 지워졌다.
-- 고침: changes 인 편은 새 렌더가 들어와도 changes 유지(고친 작업이 확인 뒤 approved), events 는 덮지 않고 이어 붙인다.
-- (적용한 함수 본문은 DB의 public.yt_import 와 같다 — 위 2026-10-29_yt_short_slots.sql 의 yt_import 에서 status·events 두 줄만 바뀜)
--   events = coalesce(youtube_posts.events,'[]') || [{by:'import', what:'새 렌더 들어옴 MM-DD HH:MI'}]
--   status = case when youtube_posts.status = 'changes' then 'changes' else 'review' end
