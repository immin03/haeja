-- 홈 화면 앱 로그인 이어받기(pwa-handoff 함수용 표)와 관리자 '알림·홈 화면 전환' 집계
create table if not exists public.pwa_handoff (h text primary key, pin text not null, user_id uuid not null, email text not null, created_at timestamptz not null default now(), used_at timestamptz);
create index if not exists pwa_handoff_pin on public.pwa_handoff(pin, created_at desc);
alter table public.pwa_handoff enable row level security;
create table if not exists public.pwa_handoff_fail (id bigserial primary key, at timestamptz not null default now());
alter table public.pwa_handoff_fail enable row level security;

create or replace function public.is_admin_uid(p uuid) returns boolean language sql stable security definer set search_path to 'public','auth' as $$
  select coalesce((select u.email from auth.users u where u.id = p) in (select jsonb_array_elements_text(value) from public.app_config where key = 'admins'), false)
$$;
revoke execute on function public.is_admin_uid(uuid) from anon;

create or replace function public.admin_push_funnel(p_days int default 14)
returns jsonb language plpgsql stable security definer set search_path to 'public','auth' as $$
declare since timestamptz := now() - make_interval(days => greatest(1, least(coalesce(p_days,14), 90)));
begin
  if not public.is_admin() and current_user not in ('postgres','service_role') then raise exception 'not admin'; end if;
  return jsonb_build_object(
    'days', p_days,
    'steps', coalesce((select jsonb_object_agg(p, n) from (
        select substr(split_part(path,'?',1),2) p, count(distinct coalesce(vk,sid)) n
        from events where at >= since and (path like '/px-%' or path like '/pn-%' or path like '/setup-%')
          and (uid is null or not public.is_admin_uid(uid))
        group by 1) x), '{}'::jsonb),
    'states', coalesce((select jsonb_object_agg(st, n) from (
        select data->>'state' st, count(distinct owner) n from docs d
        where collection = 'push_status' and not public.is_admin_uid(owner) and owner <> 'dec0de00-0000-4000-8000-000000000001'
        group by 1) y), '{}'::jsonb),
    'pwa', (select count(distinct uid) from events where uid is not null and device like '%홈화면앱%' and not public.is_admin_uid(uid))
  );
end $$;
grant execute on function public.admin_push_funnel(int) to authenticated;
