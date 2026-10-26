-- 트렌드 주제 순위 → 선택 → 롱폼 기획안 (2026-10-26 운영자):
-- "트렌드 흐름, 주제 흐름 등 다 고려해서 가장 추천하는 주제를 선정하고, 최근 급등량·조회수 모든 걸 고려해야 하고,
--  그 주제의 예상 시간 효력도 적어줘. 내가 선택하면 바로 기획안 작성, 기획안 통과하면 렌더링까지."
-- 저장: docs collection 'yt_topics', owner = publisher. 주제(묶음)와 판단 값(적합도·효력)은 Claude가 매일 아침 쓰고,
-- 점수의 숫자 부분(관심 크기·가속·이슈 근접)은 이 함수가 trend_hot 최신 값으로 매번 다시 계산한다.
--
-- 점수 100점 = 관심 크기 35 + 가속(최근 급등) 30 + 이슈 근접 15 + 밸류노트 적합 20
--   관심 크기: 주제에 걸린 영상들의 하루 조회 증가 합(pd). 10만 회 = 0점, 270만 회 이상 = 35점 (로그 눈금)
--   가속: 그중 최근 3일 안에 올라온 영상 몫(60%) + 급등·새 영상 급성장 판정 영상 수(8개면 만점, 40%)
--   이슈 근접: 연결된 실적·행사 날까지 7일 이내 15 · 14일 이내 10 · 30일 이내 5
--   적합: 워렌 버핏·기업 돈 버는 구조 이야기로 풀 수 있는가 (Claude 판단 0~20, 근거 문장 함께 저장)
-- 상태: candidate → picked(기획안 요청됨) → planned(기획안 연결) / skipped. 효력일(valid_until)이 지나면 '만료'로 보인다.

create or replace function public.trend_topic_signals(p_queries text[], p_match text default null)
returns jsonb language sql stable security definer set search_path to 'public' as $f$
  with m as (
    select distinct on (h.video_id) h.video_id, h.title, h.channel, h.per_day, h.flag, h.spike, h.published_est, h.published_text
    from public.trend_hot h
    where h.day = (select max(day) from public.trend_hot)
      and (h.queries && coalesce(p_queries, '{}'::text[]) or (coalesce(p_match, '') <> '' and h.title ~* p_match))
  )
  select jsonb_build_object(
    'pd', coalesce(round(sum(per_day)), 0),
    'pd_new', coalesce(round(sum(per_day) filter (where published_est > now() - interval '3 days')), 0),
    'videos', count(*),
    'hot', count(*) filter (where flag in ('spike', 'fast_new')),
    'spikes', count(*) filter (where flag = 'spike'),
    'max_spike', max(spike),
    'top', coalesce((select jsonb_agg(jsonb_build_object('id', video_id, 'title', title, 'channel', channel, 'pd', round(per_day), 'when', published_text, 'flag', flag) order by per_day desc)
                     from (select * from m order by per_day desc limit 3) t), '[]'::jsonb))
  from m;
$f$;

create or replace function public.yt_topic_list()
returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare today date := (now() at time zone 'Asia/Seoul')::date;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  return coalesce((
    select jsonb_agg(x order by (x->>'live')::int desc, (x->>'score')::numeric desc)
    from (
      select t.data || jsonb_build_object('id', t.id, 'updated_at', t.updated_at, 'signals', s.sig,
               'parts', jsonb_build_object('interest', s.i, 'accel', s.a, 'issue', s.iss, 'fit', s.fit),
               'score', round(s.i + s.a + s.iss + s.fit),
               'live', case when (t.data->>'valid_until')::date >= today then 1 else 0 end,
               'days_left', (t.data->>'valid_until')::date - today,
               'plan_status', p.data->>'status', 'plan_title', p.data->>'title', 'plan_target', p.data->>'target_at') as x
      from docs t
      cross join lateral (select public.trend_topic_signals(array(select jsonb_array_elements_text(coalesce(t.data->'queries', '[]'::jsonb))), t.data->>'match') as sig) g
      cross join lateral (select g.sig as sig,
          round(35 * least(1, greatest(0, ln(greatest((g.sig->>'pd')::numeric, 1) / 1e5) / ln(27.0))), 1) as i,
          round(30 * least(1, 0.6 * coalesce((g.sig->>'pd_new')::numeric / nullif((g.sig->>'pd')::numeric, 0), 0) + 0.4 * least(1, (g.sig->>'hot')::numeric / 8)), 1) as a,
          case when t.data->>'issue_day' is null then 0
               when (t.data->>'issue_day')::date - today between 0 and 7 then 15
               when (t.data->>'issue_day')::date - today between 8 and 14 then 10
               when (t.data->>'issue_day')::date - today between 15 and 30 then 5 else 0 end as iss,
          least(20, greatest(0, coalesce((t.data->>'fit')::numeric, 10))) as fit) s
      left join docs p on p.collection = 'yt_plans' and p.owner = t.owner and p.id = t.data->>'plan_id'
      where t.collection = 'yt_topics' and t.owner = public.publisher_id()
        and (t.data->>'status' in ('candidate', 'picked', 'planned') or t.updated_at > now() - interval '3 days')
        and ((t.data->>'valid_until')::date >= today - 3 or t.data->>'status' in ('picked', 'planned'))
    ) q(x)), '[]'::jsonb);
end $f$;

-- 주제 선택: 기획안 요청(대기열 작업이 다음 실행 때 이 주제로 기획안 1편을 쓴다)
create or replace function public.yt_topic_pick(p_id text, p_note text default null)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare t jsonb; rid text := 'R' || to_char(now() at time zone 'Asia/Seoul', 'YYMMDDHH24MISS') || substr(md5(random()::text), 1, 4);
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  select data into t from docs where collection = 'yt_topics' and owner = public.publisher_id() and id = p_id;
  if t is null then raise exception 'not found'; end if;
  if t->>'status' in ('picked', 'planned') then return jsonb_build_object('ok', false, 'reason', '이미 기획안을 요청한 주제입니다'); end if;
  insert into docs (owner, collection, id, data, updated_at) values (public.publisher_id(), 'yt_plan_requests', rid,
    jsonb_build_object('kind', 'more', 'count', 1, 'status', 'pending', 'at', now(), 'topic_id', p_id,
      'note', '트렌드 주제 선택: ' || coalesce(t->>'title', p_id) || ' · 각도: ' || coalesce(t->>'angle', '') || ' · 효력 ' || coalesce(t->>'valid_until', '?') || '까지'
              || case when coalesce(btrim(p_note), '') <> '' then ' · ' || btrim(p_note) else '' end), now());
  update docs set data = data || jsonb_build_object('status', 'picked', 'picked_at', now(), 'req_id', rid, 'owner_note', nullif(btrim(coalesce(p_note, '')), '')), updated_at = now()
    where collection = 'yt_topics' and owner = public.publisher_id() and id = p_id;
  return jsonb_build_object('ok', true, 'req', rid);
end $f$;

create or replace function public.yt_topic_skip(p_id text)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  update docs set data = data || jsonb_build_object('status', 'skipped', 'skipped_at', now()), updated_at = now()
    where collection = 'yt_topics' and owner = public.publisher_id() and id = p_id and data->>'status' = 'candidate';
  return jsonb_build_object('ok', found);
end $f$;

revoke all on function public.trend_topic_signals(text[], text) from public, anon;
revoke all on function public.yt_topic_list() from public, anon;
revoke all on function public.yt_topic_pick(text, text) from public, anon;
revoke all on function public.yt_topic_skip(text) from public, anon;
grant execute on function public.trend_topic_signals(text[], text) to authenticated, service_role;
grant execute on function public.yt_topic_list() to authenticated;
grant execute on function public.yt_topic_pick(text, text) to authenticated;
grant execute on function public.yt_topic_skip(text) to authenticated;
