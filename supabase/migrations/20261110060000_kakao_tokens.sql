-- 2026-11-10 카카오 "나에게 보내기" 연동: 카카오 로그인 회원이 talk_message 에 동의하면 토큰을 보관하고 알림을 본인 카톡으로도 보낸다
create table if not exists public.kakao_tokens (
  uid uuid primary key references auth.users(id) on delete cascade,
  refresh_token text,
  access_token text,
  access_expires_at timestamptz,
  refresh_expires_at timestamptz,
  scopes text[],
  linked_at timestamptz not null default now(),
  last_sent_at timestamptz,
  fail_count int not null default 0,
  last_error text
);
alter table public.kakao_tokens enable row level security;  -- 정책 없음: service role(Edge 함수)만 읽고 쓴다

-- 카카오 개발자 콘솔에서 '카카오톡 메시지 전송' 동의 항목을 켜기 전까지는 끔. 켜지면 true 로 바꾼다
insert into public.app_config(key, value) values ('kakao_msg', 'false'::jsonb) on conflict (key) do nothing;

-- 화면이 scope 요청 여부를 정할 때 읽는 스위치 (app_config 는 클라이언트가 못 읽으므로 이 키 하나만 함수로)
create or replace function public.kakao_msg_on()
returns boolean language sql stable security definer set search_path to 'public' as $$
  select coalesce((select (value #>> '{}')::boolean from app_config where key = 'kakao_msg'), false)
$$;
grant execute on function public.kakao_msg_on() to anon, authenticated;
