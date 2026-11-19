-- 2026-11-19 대표 18:07 "렌더 전에 기획 단계 검수를 촘촘하게 — 렌더는 한 번에" (docs agent 'todo-prerender-gate')
-- 1) 한 영상 한 작업 잠금: docs locks 'render-<id>'  (render_lock / render_unlock)
-- 2) 렌더 전 관문 결과 기록: 기획 progress + alerts 'prerender-gate-<spec id>'  (prerender_gate_report)
-- 3) 관문이 기획 확정 제목·썸네일을 읽는 함수 (prerender_plan)
-- 4) yt_import 수정은 별도 파일 20261119120100_yt_import_keep_title.sql (DB 미적용 — 대표 승인 필요)

create or replace function public.render_lock(p_id text, p_holder text, p_minutes int default 240)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare cur jsonb; k text := 'render-' || left(coalesce(p_id, ''), 80);
begin
  if coalesce(p_id, '') !~ '^[A-Za-z0-9_-]{3,80}$' then return jsonb_build_object('ok', false, 'why', 'bad id'); end if;
  select data into cur from docs where owner = publisher_id() and collection = 'locks' and id = k for update;
  if cur is not null and cur->>'holder' is distinct from p_holder
     and (cur->>'until')::timestamptz > now() then
    return jsonb_build_object('ok', false, 'why', '다른 작업이 렌더 중', 'holder', cur->>'holder', 'since', cur->>'at', 'until', cur->>'until');
  end if;
  insert into docs (owner, collection, id, data, updated_at)
  values (publisher_id(), 'locks', k, jsonb_build_object('holder', left(p_holder, 120), 'at', now(),
          'until', now() + make_interval(mins => least(greatest(coalesce(p_minutes, 240), 10), 360))), now())
  on conflict (owner, collection, id) do update set data = excluded.data, updated_at = now();
  return jsonb_build_object('ok', true);
end $$;

create or replace function public.render_unlock(p_id text, p_holder text)
returns boolean language plpgsql security definer set search_path to 'public' as $$
begin
  delete from docs where owner = publisher_id() and collection = 'locks' and id = 'render-' || p_id
    and data->>'holder' = p_holder;
  return found;
end $$;

create or replace function public.prerender_plan(p_id text)
returns jsonb language sql security definer set search_path to 'public' stable as $$
  select jsonb_build_object('id', id, 'title', data->'title', 'thumb', data->'thumb', 'ab_sets', data->'ab_sets',
                            'target_at', data->'target_at', 'title_fixed_by_owner', data->'title_fixed_by_owner',
                            'title_rule', data->'title_rule', 'status', data->'status', 'type', data->'type')
  from docs where owner = publisher_id() and collection = 'yt_plans' and id = p_id;
$$;

create or replace function public.prerender_gate_report(p_spec text, p_plan text, p_ok boolean, p_summary text)
returns boolean language plpgsql security definer set search_path to 'public' as $$
declare s text := left(coalesce(p_summary, ''), 1500);
begin
  if coalesce(p_spec, '') !~ '^[A-Za-z0-9_-]{3,80}$' then return false; end if;
  if coalesce(p_plan, '') <> '' then
    update docs set data = data || jsonb_build_object('prerender_gate', jsonb_build_object('ok', p_ok, 'at', now(), 'spec', p_spec, 'summary', s))
      || case when p_ok then '{}'::jsonb else jsonb_build_object('progress', jsonb_build_object('pct', 70,
           'step', '렌더 전 검수 실패 — 렌더 안 함: ' || left(s, 300), 'at', now())) end,
      updated_at = now()
    where owner = publisher_id() and collection = 'yt_plans' and id = p_plan;
  end if;
  if not p_ok then
    insert into docs (owner, collection, id, data, updated_at)
    values (publisher_id(), 'alerts', 'prerender-gate-' || p_spec, jsonb_build_object('at', now(), 'level', 'warn',
            'title', '렌더 전 검수 실패 · ' || p_spec, 'body', s, 'read', false, 'push', false, 'source', '렌더 전 관문'), now())
    on conflict (owner, collection, id) do update set data = excluded.data, updated_at = now();
  end if;
  return true;
end $$;

grant execute on function public.render_lock(text, text, int), public.render_unlock(text, text),
  public.prerender_plan(text), public.prerender_gate_report(text, text, boolean, text) to anon, authenticated;

