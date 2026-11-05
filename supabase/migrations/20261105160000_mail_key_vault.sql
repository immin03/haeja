-- 2026-11-05: Resend 키는 함수 비밀값 대신 DB 암호화 금고(vault, 이름 resend_api_key)에 둔다.
-- 키 값은 저장소에 적지 않는다. 바꿀 때: select vault.update_secret((select id from vault.secrets where name='resend_api_key'), '새 키');
create or replace function public._mail_key() returns text language sql stable security definer set search_path = public, vault as $$
  select decrypted_secret from vault.decrypted_secrets where name = 'resend_api_key' order by created_at desc limit 1 $$;
revoke all on function public._mail_key() from public, anon, authenticated;
grant execute on function public._mail_key() to service_role;
