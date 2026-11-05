-- 회원 메일 (2026-11-05 대표 요청): 가입 축하 메일 + 칼럼 메일(수신 동의한 회원만)
-- 법 기준(정보통신망법 제50조): 광고성 정보는 사전 동의(선택 항목·미리 체크 금지)·제목 (광고) 표시·수신거부 링크·
-- 동의/거부 처리 결과 14일 안 통지·2년마다 동의 여부 재확인·21~08시 발송 금지(별도 동의 없으면)

create table if not exists public.mail_prefs (
  uid uuid primary key references auth.users(id) on delete cascade,
  email text,
  ok boolean not null default false,          -- 칼럼·투자 정보 메일(광고성 정보) 수신 동의
  source text,                                 -- signup · kakao · account · column · unsub
  consent_at timestamptz,                      -- 마지막으로 동의한 때
  revoked_at timestamptz,                      -- 마지막으로 거부한 때
  token uuid not null default gen_random_uuid() unique,  -- 수신거부 링크용
  updated_at timestamptz not null default now()
);
create table if not exists public.mail_queue (
  id bigserial primary key,
  uid uuid references auth.users(id) on delete cascade,
  email text not null,
  kind text not null,                          -- welcome · digest · consent · reconfirm
  ref text not null,                           -- welcome · 2026-W46 · 동의 시각 등 (중복 발송 방지)
  status text not null default 'queued',       -- queued · sent · failed · skipped
  tries int not null default 0,
  subject text,
  error text,
  provider_id text,
  created_at timestamptz not null default now(),
  sent_at timestamptz,
  unique (uid, kind, ref)
);
create index if not exists mail_queue_status on public.mail_queue(status, created_at);
alter table public.mail_prefs enable row level security;
alter table public.mail_queue enable row level security;
revoke all on public.mail_prefs, public.mail_queue from anon, authenticated;

/* 내 메일 수신 상태 */
create or replace function public.mail_consent_get()
returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce((select jsonb_build_object('ok', ok, 'consent_at', consent_at, 'revoked_at', revoked_at, 'decided', true)
                     from mail_prefs where uid = auth.uid()), jsonb_build_object('ok', false, 'decided', false)) $$;

/* 내 메일 수신 동의·거부. 상태가 바뀌면 처리 결과 안내 메일을 대기열에 넣는다(가입 직후 동의는 축하 메일에 함께 적는다) */
create or replace function public.mail_consent_set(p_ok boolean, p_source text default 'account')
returns jsonb language plpgsql security definer set search_path = public, auth as $$
declare v uuid := auth.uid(); em text; prev boolean; r mail_prefs;
begin
  if v is null then raise exception 'login required'; end if;
  select email into em from auth.users where id = v;
  select ok into prev from mail_prefs where uid = v;
  insert into mail_prefs(uid, email, ok, source, consent_at, revoked_at, updated_at)
  values (v, em, p_ok, p_source, case when p_ok then now() end, case when not p_ok then now() end, now())
  on conflict (uid) do update set email = excluded.email, ok = excluded.ok, source = excluded.source,
    consent_at = case when excluded.ok then now() else mail_prefs.consent_at end,
    revoked_at = case when not excluded.ok then now() else mail_prefs.revoked_at end, updated_at = now()
  returning * into r;
  if prev is distinct from p_ok and p_source not in ('signup', 'kakao') and em is not null then
    insert into mail_queue(uid, email, kind, ref) values (v, em, 'consent', (case when p_ok then 'on:' else 'off:' end) || to_char(now(), 'YYYYMMDDHH24MISS'))
    on conflict do nothing;
  end if;
  return jsonb_build_object('ok', r.ok, 'consent_at', r.consent_at, 'revoked_at', r.revoked_at, 'decided', true);
end $$;

/* 수신거부 링크 (로그인 없이): 토큰으로 끈다 */
create or replace function public.mail_unsub(p_token uuid)
returns jsonb language plpgsql security definer set search_path = public as $$
declare r mail_prefs;
begin
  update mail_prefs set ok = false, revoked_at = now(), source = 'unsub', updated_at = now() where token = p_token returning * into r;
  if r.uid is null then return jsonb_build_object('ok', false, 'reason', 'not found'); end if;
  insert into mail_queue(uid, email, kind, ref) values (r.uid, r.email, 'consent', 'off:' || to_char(now(), 'YYYYMMDDHH24MISS')) on conflict do nothing;
  return jsonb_build_object('ok', true, 'email', regexp_replace(r.email, '^(.{2}).*(@.*)$', '\1***\2'), 'at', r.revoked_at);
end $$;

/* 가입 기록(events.signup)이 들어오면: 가입 때 고른 메일 동의를 저장하고, 축하 메일을 대기열에 넣는다 */
create or replace function public._mail_on_signup()
returns trigger language plpgsql security definer set search_path = public, auth as $$
declare u record; mk boolean;
begin
  if new.kind <> 'signup' or new.uid is null then return new; end if;
  if new.uid = any(array_remove(array[public.publisher_id(), public.demo_id()], null)) then return new; end if;
  select id, email, raw_user_meta_data m into u from auth.users where id = new.uid;
  if u.email is null then return new; end if;
  mk := coalesce((u.m ->> 'mail_ok')::boolean, false);
  insert into mail_prefs(uid, email, ok, source, consent_at, revoked_at)
  values (u.id, u.email, mk, case when (u.m ->> 'iss') like '%kakao%' then 'kakao' else 'signup' end, case when mk then now() end, case when not mk then now() end)
  on conflict (uid) do nothing;
  insert into mail_queue(uid, email, kind, ref) values (u.id, u.email, 'welcome', 'welcome') on conflict do nothing;
  return new;
end $$;
drop trigger if exists events_mail_signup on public.events;
create trigger events_mail_signup after insert on public.events for each row when (new.kind = 'signup') execute function public._mail_on_signup();

/* 관리자: 동의 현황 · 대기열 · 최근 발송 */
create or replace function public.admin_mail()
returns jsonb language plpgsql stable security definer set search_path = public, auth as $$
declare excl uuid[]; res jsonb;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  excl := array_remove(array[public.publisher_id(), public.demo_id()], null);
  select jsonb_build_object(
    'members', (select count(*) from auth.users where not (id = any(excl))),
    'ok', (select count(*) from mail_prefs where ok and not (uid = any(excl))),
    'no', (select count(*) from mail_prefs where not ok and not (uid = any(excl))),
    'undecided', (select count(*) from auth.users u where not (id = any(excl)) and not exists (select 1 from mail_prefs p where p.uid = u.id)),
    'queued', (select count(*) from mail_queue where status = 'queued'),
    'sent7', (select count(*) from mail_queue where status = 'sent' and sent_at > now() - interval '7 days'),
    'failed', (select count(*) from mail_queue where status = 'failed'),
    'recent', (select coalesce(jsonb_agg(x order by x.created_at desc), '[]') from (
        select q.id, q.kind, q.ref, q.status, q.subject, q.error, q.email, q.created_at, q.sent_at, q.tries
          from mail_queue q order by q.created_at desc limit 40) x),
    'list', (select coalesce(jsonb_agg(x order by x.updated_at desc), '[]') from (
        select p.uid, p.email, p.ok, p.source, p.consent_at, p.revoked_at, p.updated_at from mail_prefs p where not (p.uid = any(excl))) x)
  ) into res;
  return res;
end $$;

/* 관리자: 실패한 메일 다시 보내기 · 대기 취소 */
create or replace function public.admin_mail_retry(p_id bigint, p_cancel boolean default false)
returns jsonb language plpgsql security definer set search_path = public as $$
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  update mail_queue set status = case when p_cancel then 'skipped' else 'queued' end, tries = 0, error = case when p_cancel then '관리자 취소' end where id = p_id;
  return jsonb_build_object('ok', true);
end $$;

revoke all on function public.mail_consent_get(), public.mail_consent_set(boolean, text), public.admin_mail(), public.admin_mail_retry(bigint, boolean), public._mail_on_signup() from public, anon;
grant execute on function public.mail_consent_get(), public.mail_consent_set(boolean, text), public.admin_mail(), public.admin_mail_retry(bigint, boolean) to authenticated;
grant execute on function public.mail_unsub(uuid) to anon, authenticated;

-- 대기열 발송: 5분마다 · 주간 칼럼 메일: 매주 월요일 08:30(한국 시간) = 일요일 23:30 UTC
select cron.unschedule(jobid) from cron.job where jobname in ('haeja-mail-drain', 'haeja-mail-digest');
-- 처리방침 변경(11/5 공지) 7일 뒤인 11/12부터 보낸다
select cron.schedule('haeja-mail-drain', '*/5 * * * *', $$select public._fn_call('mail', '{"action":"drain"}') where now() >= timestamptz '2026-11-12 00:00:00+09'$$);
select cron.schedule('haeja-mail-digest', '30 23 * * 0', $$select public._fn_call('mail', '{"action":"digest"}') where now() >= timestamptz '2026-11-12 00:00:00+09'$$);
