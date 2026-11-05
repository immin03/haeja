-- 2026-11-05 12:47 대표: 가입 축하 메일에서 칼럼 구독 바로 유도 · 기존 회원은 자연스럽게 · 보내기 전 대표 검수
-- (실제 DB에 적용됨: mail_sub, mail_consent_set 수정, admin_mail_live, admin_mail에 live 추가)
-- ① mail_sub(token): 가입 축하 메일 '칼럼 메일 받기' → /mail?s=토큰 화면에서 한 번 더 눌러 동의 (source = mail-welcome)
-- ② mail_consent_set: 처리 결과 안내는 켰을 때, 또는 받던 사람이 껐을 때만 (기존 회원이 앱 안내에서 '괜찮아요'를 누른 건 안내 안 함)
-- ③ app_config.mail_live: 관리자 메일 탭 '검수 완료 · 발송 시작'을 눌러야 true → 그 전까지 mail 함수는 보내지 않음
create or replace function public.mail_sub(p_token uuid)
returns jsonb language plpgsql security definer set search_path = public as $$
declare r mail_prefs; prev boolean;
begin
  select ok into prev from mail_prefs where token = p_token;
  update mail_prefs set ok = true, consent_at = now(), source = 'mail-welcome', updated_at = now() where token = p_token returning * into r;
  if r.uid is null then return jsonb_build_object('ok', false, 'reason', 'not found'); end if;
  if prev is distinct from true then
    insert into mail_queue(uid, email, kind, ref) values (r.uid, r.email, 'consent', 'on:' || to_char(now(), 'YYYYMMDDHH24MISS')) on conflict do nothing;
  end if;
  return jsonb_build_object('ok', true, 'email', regexp_replace(r.email, '^(.{2}).*(@.*)$', '\1***\2'), 'at', r.consent_at);
end $$;
grant execute on function public.mail_sub(uuid) to anon, authenticated;
insert into app_config(key, value) values ('mail_live', 'false'::jsonb) on conflict (key) do nothing;
create or replace function public.admin_mail_live(p_on boolean)
returns jsonb language plpgsql security definer set search_path = public as $$
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  insert into app_config(key, value) values ('mail_live', to_jsonb(p_on)) on conflict (key) do update set value = excluded.value;
  insert into app_config(key, value) values ('mail_live_at', to_jsonb(now())) on conflict (key) do update set value = excluded.value;
  return jsonb_build_object('ok', true, 'live', p_on);
end $$;
revoke all on function public.admin_mail_live(boolean) from public, anon;
grant execute on function public.admin_mail_live(boolean) to authenticated;
