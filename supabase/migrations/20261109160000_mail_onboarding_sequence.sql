-- 2026-11-10 가입 뒤 D+1·D+3·D+7 안내 메일: 보낼 시각(not_before)과 가입 트리거 확장 (Supabase에 적용 완료)
alter table public.mail_queue add column if not exists not_before timestamptz not null default now();
create index if not exists mail_queue_due_idx on public.mail_queue (status, not_before);

-- 가입 뒤 N일째 아침 8:30(KST)
create or replace function public._mail_morning(p_from timestamptz, p_days int)
returns timestamptz language sql immutable as $$
  select ((date_trunc('day', p_from at time zone 'Asia/Seoul') + make_interval(days => p_days, hours => 8, mins => 30)) at time zone 'Asia/Seoul')
$$;

create or replace function public._mail_on_signup()
returns trigger language plpgsql security definer set search_path to 'public','auth' as $$
declare u record; mk boolean;
begin
  if new.kind <> 'signup' or new.uid is null then return new; end if;
  if new.uid = any(array_remove(array[public.publisher_id(), public.demo_id()], null)) then return new; end if;
  select id, email, raw_user_meta_data m, created_at into u from auth.users where id = new.uid;
  if u.email is null then return new; end if;
  mk := coalesce((u.m ->> 'mail_ok')::boolean, false);
  insert into mail_prefs(uid, email, ok, source, consent_at, revoked_at)
  values (u.id, u.email, mk, case when (u.m ->> 'iss') like '%kakao%' then 'kakao' else 'signup' end, case when mk then now() end, case when not mk then now() end)
  on conflict (uid) do nothing;
  insert into mail_queue(uid, email, kind, ref) values (u.id, u.email, 'welcome', 'welcome') on conflict do nothing;
  -- 첫 주 안내 메일 세 통 (서비스 안내)
  insert into mail_queue(uid, email, kind, ref, not_before) values
    (u.id, u.email, 'd1', 'onb', public._mail_morning(now(), 1)),
    (u.id, u.email, 'd3', 'onb', public._mail_morning(now(), 3)),
    (u.id, u.email, 'd7', 'onb', public._mail_morning(now(), 7))
  on conflict do nothing;
  return new;
end $$;

-- 이미 가입한 회원(14일 안)에게도 아직 지나지 않은 안내 메일만 넣는다. 전부 지났으면 D+7만 내일 아침에
with u as (
  select id, email, created_at from auth.users
  where email is not null and created_at > now() - interval '14 days'
    and not (id = any(array_remove(array[public.publisher_id(), public.demo_id()], null)))
), plan as (
  select u.id, u.email, k.kind, public._mail_morning(u.created_at, k.d) nb
  from u cross join (values ('d1',1),('d3',3),('d7',7)) k(kind, d)
), due as (
  select id, email, kind, nb from plan where nb > now()
  union all
  select id, email, 'd7', public._mail_morning(now(), 1) from u where not exists (select 1 from plan p where p.id = u.id and p.nb > now())
)
insert into mail_queue(uid, email, kind, ref, not_before)
select id, email, kind, 'onb', nb from due
on conflict do nothing;
