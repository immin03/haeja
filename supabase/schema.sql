-- 해자 장부 데이터베이스 (Supabase SQL Editor에 통째로 붙여넣고 Run)
-- 표 하나에 모든 데이터를 문서(JSON) 형태로 저장한다: holdings, companies, journal, settings, screen, news, briefing, trends, prices, fx, profiles, snapshots

create table if not exists public.docs (
  collection  text        not null,
  id          text        not null,
  data        jsonb       not null default '{}'::jsonb,
  owner       uuid        not null default auth.uid() references auth.users(id) on delete cascade,
  updated_at  timestamptz not null default now(),
  primary key (owner, collection, id)
);

create index if not exists docs_owner_collection on public.docs (owner, collection);

-- 행 수준 보안: 로그인한 본인 행만 읽고 쓴다
alter table public.docs enable row level security;

drop policy if exists "owner read"   on public.docs;
drop policy if exists "owner insert" on public.docs;
drop policy if exists "owner update" on public.docs;
drop policy if exists "owner delete" on public.docs;

create policy "owner read"   on public.docs for select using (owner = auth.uid());
create policy "owner insert" on public.docs for insert with check (owner = auth.uid());
create policy "owner update" on public.docs for update using (owner = auth.uid()) with check (owner = auth.uid());
create policy "owner delete" on public.docs for delete using (owner = auth.uid());

-- 실시간 반영 (다른 기기·아침 자동 분석이 쓴 내용이 화면에 바로 뜨게)
do $$ begin
  alter publication supabase_realtime add table public.docs;
exception when duplicate_object then null; end $$;
