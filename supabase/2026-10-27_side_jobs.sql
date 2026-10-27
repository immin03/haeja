-- 사이드 채널 작업 현황 (렌더·이미지 생성 진행률) — 2026-10-27
-- Supabase SQL Editor 에 통째로 붙여 넣고 Run
create table if not exists public.sc_jobs (
  id text primary key,
  kind text not null default 'render',
  label text,
  status text not null default 'running',
  pct numeric,
  detail text,
  cost numeric,
  run_url text,
  started_at timestamptz default now(),
  updated_at timestamptz default now()
);
alter table public.sc_jobs enable row level security;
drop policy if exists sc_jobs_admin on public.sc_jobs;
create policy sc_jobs_admin on public.sc_jobs for all using (public.is_admin()) with check (public.is_admin());

create table if not exists public.sc_secrets (k text primary key, v text not null);
alter table public.sc_secrets enable row level security;   -- 정책 없음 = 화면·외부에서 못 읽음
insert into public.sc_secrets(k, v) values ('progress_token', '27c7b3f57250c6142046400d2e14e6e337325abdef2302fb')
  on conflict (k) do update set v = excluded.v;

create or replace function public.sc_job_report(p_token text, p_id text, p_kind text, p_label text, p_status text, p_pct numeric, p_detail text, p_cost numeric, p_run_url text)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_token is null or p_token <> (select v from sc_secrets where k = 'progress_token') then raise exception 'bad token'; end if;
  insert into sc_jobs(id, kind, label, status, pct, detail, cost, run_url, started_at, updated_at)
  values (p_id, coalesce(p_kind, 'render'), p_label, coalesce(p_status, 'running'), p_pct, p_detail, p_cost, p_run_url, now(), now())
  on conflict (id) do update set label = coalesce(excluded.label, sc_jobs.label), status = excluded.status, pct = coalesce(excluded.pct, sc_jobs.pct),
    detail = coalesce(excluded.detail, sc_jobs.detail), cost = coalesce(excluded.cost, sc_jobs.cost), run_url = coalesce(excluded.run_url, sc_jobs.run_url), updated_at = now();
end $$;
revoke all on function public.sc_job_report(text, text, text, text, text, numeric, text, numeric, text) from public;
grant execute on function public.sc_job_report(text, text, text, text, text, numeric, text, numeric, text) to anon, authenticated;
