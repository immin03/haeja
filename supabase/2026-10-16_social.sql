-- 인스타·쓰레드 카드뉴스 자동 게시
create table if not exists public.social_posts (
  id text primary key,
  seq int not null,
  title text not null,
  scheduled_at timestamptz not null,
  caption text not null,
  hashtags text[] not null default '{}',
  threads_tag text,
  images text[] not null,
  to_ig boolean not null default false,
  to_threads boolean not null default true,
  approved boolean not null default true,
  paused boolean not null default false,
  ig_status text not null default 'pending',
  ig_media_id text, ig_permalink text, ig_error text, ig_at timestamptz,
  th_status text not null default 'pending',
  th_media_id text, th_permalink text, th_error text, th_at timestamptz,
  created_at timestamptz not null default now()
);
alter table public.social_posts enable row level security;
drop policy if exists "admin read" on public.social_posts;
create policy "admin read" on public.social_posts for select to authenticated using (public.is_admin());
drop policy if exists "admin write" on public.social_posts;
create policy "admin write" on public.social_posts for update to authenticated using (public.is_admin()) with check (public.is_admin());
grant select, update on public.social_posts to authenticated;

-- 토큰은 서버 전용 (정책 없음 = service role만 접근)
create table if not exists public.social_accounts (
  platform text primary key check (platform in ('instagram','threads')),
  account_id text not null,
  username text,
  access_token text not null,
  expires_at timestamptz,
  updated_at timestamptz not null default now()
);
alter table public.social_accounts enable row level security;
revoke all on public.social_accounts from anon, authenticated;

create table if not exists public.social_oauth_state (
  nonce text primary key,
  platform text not null,
  ret text not null,
  created_at timestamptz not null default now()
);
alter table public.social_oauth_state enable row level security;
revoke all on public.social_oauth_state from anon, authenticated;

-- 관리자 화면용: 토큰 없이 연결 상태만
create or replace function public.social_status() returns jsonb
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  return jsonb_build_object(
    'accounts', coalesce((select jsonb_agg(jsonb_build_object('platform',platform,'username',username,'expires_at',expires_at,'updated_at',updated_at)) from social_accounts), '[]'::jsonb),
    'paused', coalesce((select value from app_config where key='social_paused'), 'false'::jsonb),
    'site', (select value #>> '{}' from app_config where key='site_url'));
end $$;
revoke all on function public.social_status() from public, anon;
grant execute on function public.social_status() to authenticated;

create or replace function public.social_admin_set(p_key text, p_value jsonb) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  if p_key not in ('social_paused','site_url') then raise exception 'bad key'; end if;
  insert into app_config(key, value) values (p_key, p_value) on conflict (key) do update set value = excluded.value;
end $$;
revoke all on function public.social_admin_set(text, jsonb) from public, anon;
grant execute on function public.social_admin_set(text, jsonb) to authenticated;

-- 5분마다 게시 함수 실행
select cron.unschedule('haeja-social') where exists (select 1 from cron.job where jobname = 'haeja-social');
select cron.schedule('haeja-social', '*/5 * * * *', $$select public._fn_call('social-publish', '{}')$$);
