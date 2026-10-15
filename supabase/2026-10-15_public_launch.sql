-- ValueNote 공개 준비 (2026-10-15) — Supabase → SQL Editor에 통째로 붙여넣고 Run 한 번
-- 1) 여러 사용자용 구조  2) 방문·가입 기록과 관리자 집계  3) 마케팅용 체험 계정(예시 데이터)
-- 기존 데이터는 지우지 않는다. 시작 전에 docs 표 전체를 docs_backup_20261015로 복사해 둔다.

-- ============ 0) 백업 ============
create table if not exists public.docs_backup_20261015 as select * from public.docs;
alter table public.docs_backup_20261015 enable row level security;

-- ============ 1) 여러 사용자용 구조 ============
-- 사용자마다 같은 문서 id(예: settings/main)를 가질 수 있게 기본 키에 owner 포함
do $$ begin
  if (select string_agg(a.attname, ',' order by a.attname) from pg_index i join pg_attribute a on a.attrelid = i.indrelid and a.attnum = any(i.indkey)
      where i.indrelid = 'public.docs'::regclass and i.indisprimary) = 'collection,id' then
    alter table public.docs drop constraint docs_pkey;
    alter table public.docs add primary key (owner, collection, id);
  end if;
end $$;

-- 앱 설정: 운영자(공용 데이터 주인), 관리자, 체험 계정
create table if not exists public.app_config (key text primary key, value jsonb not null);
alter table public.app_config enable row level security;
insert into public.app_config(key, value) values
  ('publisher', to_jsonb('e33646e9-502a-4967-8330-a4818c7f0fff'::text)),
  ('admins',    '["immin03@gmail.com"]'::jsonb),
  ('demo',      to_jsonb('dec0de00-0000-4000-8000-000000000001'::text))
on conflict (key) do nothing;

create or replace function public.publisher_id() returns uuid
language sql stable security definer set search_path = public as
$$ select (value #>> '{}')::uuid from public.app_config where key = 'publisher' $$;
create or replace function public.demo_id() returns uuid
language sql stable security definer set search_path = public as
$$ select (value #>> '{}')::uuid from public.app_config where key = 'demo' $$;

-- 공용 데이터(기업 목록·재무 프로필·트렌드·가격 기록·환율)는 로그인한 모든 사용자가 읽기만 가능
drop policy if exists "shared read" on public.docs;
create policy "shared read" on public.docs for select to authenticated
  using (collection in ('screen','profiles','trends','prices','fx') and owner = public.publisher_id());

-- 체험 계정은 읽기 전용 (누가 로그인해도 예시 데이터가 바뀌지 않게)
drop policy if exists "owner insert" on public.docs;
drop policy if exists "owner update" on public.docs;
drop policy if exists "owner delete" on public.docs;
create policy "owner insert" on public.docs for insert with check (owner = auth.uid() and auth.uid() is distinct from public.demo_id());
create policy "owner update" on public.docs for update using (owner = auth.uid() and auth.uid() is distinct from public.demo_id()) with check (owner = auth.uid());
create policy "owner delete" on public.docs for delete using (owner = auth.uid() and auth.uid() is distinct from public.demo_id());

-- ============ 2) 방문·가입 기록과 관리자 집계 ============
create table if not exists public.events (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  kind text not null check (kind in ('visit','signup','login','onboard')),
  sid text check (length(sid) <= 64),
  uid uuid default auth.uid(),
  path text check (length(path) <= 200),
  ref text check (length(ref) <= 300),
  device text check (length(device) <= 40)
);
create index if not exists events_at on public.events (at);
alter table public.events enable row level security;
drop policy if exists "anyone insert" on public.events;
create policy "anyone insert" on public.events for insert to anon, authenticated
  with check (uid is null or uid = auth.uid());
grant insert on public.events to anon, authenticated;

create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = public as
$$ select coalesce((auth.jwt() ->> 'email') in (select jsonb_array_elements_text(value) from public.app_config where key = 'admins'), false) $$;

create or replace function public.admin_stats() returns jsonb
language plpgsql stable security definer set search_path = public, auth as
$$
declare
  d0 date := (now() at time zone 'Asia/Seoul')::date;
  excl uuid[];
  res jsonb;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  excl := array_remove(array[public.publisher_id(), public.demo_id()], null);

  with v as (select *, (at at time zone 'Asia/Seoul')::date d from events
             where kind = 'visit' and at > now() - interval '31 days' and (uid is null or not (uid = any(excl)))),
       u as (select id, email, created_at, last_sign_in_at, (created_at at time zone 'Asia/Seoul')::date d from auth.users where not (id = any(excl))),
       st as (select owner, data -> 'investor' inv from docs where collection = 'settings' and id = 'main'),
       hc as (select owner, count(*) n from docs where collection = 'holdings' group by owner),
       days as (select generate_series(d0 - 29, d0, interval '1 day')::date d)
  select jsonb_build_object(
    'asOf', now(),
    'visitors', jsonb_build_object(
       'today', (select count(distinct sid) from v where d = d0),
       'd7',    (select count(distinct sid) from v where d > d0 - 7),
       'd30',   (select count(distinct sid) from v where d > d0 - 30)),
    'pageviews', jsonb_build_object(
       'today', (select count(*) from v where d = d0),
       'd30',   (select count(*) from v where d > d0 - 30)),
    'signups', jsonb_build_object(
       'total', (select count(*) from u),
       'today', (select count(*) from u where d = d0),
       'd7',    (select count(*) from u where d > d0 - 7),
       'd30',   (select count(*) from u where d > d0 - 30)),
    'funnel', jsonb_build_object(
       'visitors30',   (select count(distinct sid) from v where d > d0 - 30),
       'signups30',    (select count(*) from u where d > d0 - 30),
       'onboarded',    (select count(*) from u join st on st.owner = u.id where st.inv ? 'done'),
       'withHoldings', (select count(*) from u join hc on hc.owner = u.id),
       'pushOn',       (select count(distinct owner) from docs where collection = 'push_subs' and not (owner = any(excl)))),
    'active7', (select count(distinct owner) from docs where updated_at > now() - interval '7 days' and not (owner = any(excl))
                and collection in ('holdings','journal','settings','companies')),
    'demoVisits7', (select count(*) from events where kind = 'login' and uid = public.demo_id() and at > now() - interval '7 days'),
    'daily', (select jsonb_agg(jsonb_build_object('d', days.d,
                'v', (select count(distinct sid) from v where v.d = days.d),
                's', (select count(*) from u where u.d = days.d)) order by days.d) from days),
    'devices', (select coalesce(jsonb_object_agg(device, n), '{}') from
                (select coalesce(device,'기타') device, count(distinct sid) n from v where d > d0 - 30 group by 1) x),
    'refs', (select coalesce(jsonb_agg(jsonb_build_object('r', r, 'n', n) order by n desc), '[]') from
             (select coalesce(nullif(ref,''),'직접 방문') r, count(distinct sid) n from v where d > d0 - 30 group by 1 order by 2 desc limit 8) x),
    'expect', (select coalesce(jsonb_object_agg(e, n), '{}') from
               (select jsonb_array_elements_text(st.inv -> 'expect') e, count(*) n from st join u on u.id = st.owner
                where jsonb_typeof(st.inv -> 'expect') = 'array' group by 1) x),
    'style', (select coalesce(jsonb_object_agg(s, n), '{}') from
              (select st.inv ->> 'style' s, count(*) n from st join u on u.id = st.owner where st.inv ->> 'style' is not null group by 1) x),
    'size', (select coalesce(jsonb_object_agg(s, n), '{}') from
             (select st.inv ->> 'size' s, count(*) n from st join u on u.id = st.owner where st.inv ->> 'size' is not null group by 1) x),
    'users', (select coalesce(jsonb_agg(x order by x.created_at desc), '[]') from (
       select u.email, u.created_at, u.last_sign_in_at, coalesce(hc.n, 0) holdings,
              st.inv ->> 'style' style, st.inv ->> 'size' size, st.inv ->> 'exp' exp, st.inv -> 'expect' expect, st.inv ->> 'expectNote' note
       from u left join st on st.owner = u.id left join hc on hc.owner = u.id order by u.created_at desc limit 100) x)
  ) into res;
  return res;
end $$;
revoke all on function public.admin_stats() from public, anon;
grant execute on function public.admin_stats() to authenticated;
grant execute on function public.is_admin() to authenticated;

-- ============ 3) 마케팅용 체험 계정 (예시 데이터) ============
-- 아이디 demo@valuenote.app / 비밀번호 valuenote
do $$
declare
  did uuid := 'dec0de00-0000-4000-8000-000000000001';
begin
  if not exists (select 1 from auth.users where id = did) then
    insert into auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
      raw_app_meta_data, raw_user_meta_data, created_at, updated_at, confirmation_token, recovery_token, email_change_token_new, email_change)
    values ('00000000-0000-0000-0000-000000000000', did, 'authenticated', 'authenticated', 'demo@valuenote.app',
      extensions.crypt('valuenote', extensions.gen_salt('bf')), now(),
      '{"provider":"email","providers":["email"]}', '{"name":"체험 투자자"}', now(), now(), '', '', '', '');
    insert into auth.identities (id, user_id, provider_id, identity_data, provider, last_sign_in_at, created_at, updated_at)
    values (gen_random_uuid(), did, did::text,
      jsonb_build_object('sub', did::text, 'email', 'demo@valuenote.app', 'email_verified', true), 'email', now(), now(), now());
  end if;
end $$;

-- 예시 데이터를 새로 채운다 (다시 실행해도 같은 상태로 돌아감)
delete from public.docs where owner = 'dec0de00-0000-4000-8000-000000000001';

with pub as (select public.publisher_id() id),
rows as (
  select r from public.docs d, pub, jsonb_array_elements(d.data -> 'rows') r
  where d.owner = pub.id and d.collection = 'screen' and d.id like 'chunk-%'
),
pick(t, cid, pinned, created, qual, thesis) as (values
  ('005930.KS', 'dc-samsung', false, '2025-04-08',
   '{"circle":true,"moats":["scale","cost"],"hold10":true,"inversion":"메모리 가격이 2년 넘게 바닥에 머무는 경우"}'::jsonb,
   '{"why":"메모리 업황 바닥에서 PBR 1배 미만, 순현금 보유. 사이클이 돌아오면 이익이 크게 회복된다고 봤다.","edge":"업황 바닥에서 사고 정점에서 비중을 줄이는 원칙","sell1":"영업이익률이 사이클 정점 수준(30% 이상)에서 꺾이기 시작하면 절반 매도","sell2":"주가가 적정 가격을 20% 넘게 웃돌면 비중 축소","sell3":"HBM 경쟁력 상실이 확인되면 전량 매도","target":null,"conviction":4,"reviewDate":"2026-12-31","status":"유효"}'::jsonb),
  ('105560.KS', 'dc-kb', false, '2025-03-12',
   '{"circle":true,"moats":["scale","switch"],"hold10":true,"inversion":"부동산 PF 부실이 자본비율을 깎는 경우"}'::jsonb,
   '{"why":"PBR 0.4배, 배당과 자사주 소각을 늘리는 주주환원 정책. 은행업은 이해하기 쉽다.","edge":"남들이 지루하다고 외면할 때 산 저평가 금융주","sell1":"자사주 소각·배당 확대 정책이 후퇴하면 비중 축소","sell2":"PBR 1배를 넘으면 절반 매도","sell3":"연체율이 2배 넘게 오르면 재점검","target":null,"conviction":4,"reviewDate":"2026-12-31","status":"유효"}'::jsonb),
  ('BRK-B', 'dc-brk', false, '2025-06-20',
   '{"circle":true,"moats":["brand","scale","cost"],"hold10":true,"inversion":"후계 체제에서 자본 배분 원칙이 흔들리는 경우"}'::jsonb,
   '{"why":"버핏 이후에도 보험 플로트와 자회사 현금흐름이 이어진다. 현금이 많아 하락장에서 기회를 산다.","edge":"10년 이상 들고 갈 기본 축","sell1":"보험 손해율이 3년 연속 업계 평균보다 나빠지면 재점검","sell2":"주가가 장부가 2배를 크게 넘으면 비중 축소","sell3":"","target":null,"conviction":5,"reviewDate":"2027-06-30","status":"유효"}'::jsonb),
  ('035720.KS', 'dc-kakao', false, '2024-11-04',
   '{"circle":false,"moats":["network"],"hold10":null,"inversion":"광고·커머스 성장이 멈추고 AI 투자비만 늘어나는 경우"}'::jsonb,
   '{"why":"AI 테마와 반등 기대. 숫자를 확인하지 않고 샀다.","edge":"","sell1":"","sell2":"","sell3":"","target":null,"conviction":2,"reviewDate":"2026-11-30","status":"점검 필요","memo":"매도 조건 없이 산 종목. 이익 대비 비싸게 샀다."}'::jsonb),
  ('LULU', 'dc-lulu', false, '2024-12-10',
   '{"circle":true,"moats":["brand"],"hold10":false,"inversion":"유행이 바뀌어 브랜드 프리미엄이 사라지는 경우"}'::jsonb,
   '{"why":"브랜드가 좋아 보였고 성장률이 높았다. PER 30배를 감수했다.","edge":"","sell1":"매출 성장률이 5% 아래로 떨어지면 매도","sell2":"","sell3":"","target":null,"conviction":2,"reviewDate":"2026-10-31","status":"점검 필요","memo":"매도 조건(성장률 5% 미만)에 닿았는데 지키지 못했다."}'::jsonb),
  ('KO', 'dc-ko', false, '2025-01-15',
   '{"circle":true,"moats":["brand","scale"],"hold10":true,"inversion":"설탕세 확대로 판매량이 구조적으로 줄어드는 경우"}'::jsonb,
   '{"why":"60년 넘게 배당을 늘린 회사. 경기와 상관없이 팔린다.","edge":"배당 재투자용 방어 종목","sell1":"배당 증가가 멈추면 재점검","sell2":"","sell3":"","target":null,"conviction":4,"reviewDate":"2027-01-31","status":"유효"}'::jsonb),
  ('TSLA', 'dc-tsla', false, '2026-02-18',
   '{"circle":false,"moats":["brand"],"hold10":null,"inversion":"자율주행·로봇 기대가 실적으로 이어지지 않는 경우"}'::jsonb,
   '{"why":"도전 칸(포트폴리오 5% 이하)에서 로봇·자율주행 성장에 작게 베팅.","edge":"","sell1":"도전 칸 비중이 10%를 넘으면 줄인다","sell2":"-30%면 손절","sell3":"","target":null,"conviction":2,"reviewDate":"2026-12-31","status":"유효"}'::jsonb),
  ('005830.KS', 'dc-dbins', true, '2026-09-02',
   '{"circle":true,"moats":["scale"],"hold10":true,"inversion":""}'::jsonb,
   '{"why":"ROE 17%에 PER 6배. 적정 매수가 아래로 오면 주력으로 편입할 후보.","edge":"","sell1":"","sell2":"","sell3":"","target":null,"conviction":3,"reviewDate":"","status":"유효"}'::jsonb),
  ('9433.T', 'dc-kddi', true, '2026-09-10',
   '{"circle":true,"moats":["scale","switch"],"hold10":true,"inversion":""}'::jsonb,
   '{"why":"일본 통신 2위, 자사주 매입이 꾸준하다. 엔저 구간에 지켜보는 후보.","edge":"","sell1":"","sell2":"","sell3":"","target":null,"conviction":3,"reviewDate":"","status":"유효"}'::jsonb),
  ('V', 'dc-visa', true, '2026-08-21',
   '{"circle":true,"moats":["network","switch"],"hold10":true,"inversion":""}'::jsonb,
   '{"why":"세계 결제망 독점에 가까운 해자. 좋은 회사지만 지금 가격은 비싸다.","edge":"","sell1":"","sell2":"","sell3":"","target":null,"conviction":4,"reviewDate":"","status":"유효"}'::jsonb)
)
insert into public.docs (owner, collection, id, data, updated_at)
select 'dec0de00-0000-4000-8000-000000000001', 'companies', p.cid,
  jsonb_build_object(
    'name', r ->> 'n', 'ticker', coalesce(r ->> 'code', r ->> 't'), 'yf', r ->> 't', 'market', r ->> 'm', 'kind', 'stock',
    'sector', coalesce(r ->> 'ind', r ->> 's', ''), 'price', r -> 'px', 'example', false,
    'fin', coalesce(r -> 'fin', '{}'), 'val', coalesce(r -> 'val', '{}'), 'qual', p.qual, 'fscore', coalesce(r -> 'fsd', '[]'), 'special', '[]'::jsonb,
    'thesis', p.thesis,
    'ai', jsonb_build_object('fillNote', '', 'review', '', 'reviewAt', '',
            'filled', (select coalesce(jsonb_agg(k), '[]') from (select jsonb_object_keys(coalesce(r -> 'fin', '{}')) k union all select jsonb_object_keys(coalesce(r -> 'val', '{}'))) kk)),
    'createdAt', p.created, 'pinned', p.pinned, 'starAt', case when p.pinned then p.created end,
    'finSector', coalesce((r ->> 'fin_sector')::boolean, false), 'mf', r -> 'mf', 'holdco', coalesce((r ->> 'holdco')::boolean, false),
    'dataConf', r -> 'dataConf', 'source', '스크리너 자동 수집 (체험 계정 예시)'),
  now()
from pick p join rows on rows.r ->> 't' = p.t;

-- 보유 종목: 약 5,600만 원 + 현금 1,000만 원 = 약 6,600만 원. 잘한 투자와 못한 투자를 섞었다.
with px as (select id cid, (data ->> 'price')::numeric price from public.docs where owner = 'dec0de00-0000-4000-8000-000000000001' and collection = 'companies'),
h(hid, cid, name, ticker, market, currency, qty, avg) as (values
  ('dh-samsung', 'dc-samsung', '삼성전자', '005930', 'KR', 'KRW', 90, 158000),
  ('dh-kb',      'dc-kb',      'KB금융',   '105560', 'KR', 'KRW', 80, 98500),
  ('dh-brk',     'dc-brk',     '버크셔 해서웨이', 'BRK-B', 'US', 'USD', 12, 470),
  ('dh-kakao',   'dc-kakao',   '카카오',   '035720', 'KR', 'KRW', 150, 52800),
  ('dh-lulu',    'dc-lulu',    '룰루레몬', 'LULU',   'US', 'USD', 25, 312),
  ('dh-ko',      'dc-ko',      '코카콜라', 'KO',     'US', 'USD', 30, 62.5),
  ('dh-tsla',    'dc-tsla',    '테슬라',   'TSLA',   'US', 'USD', 5, 410)
)
insert into public.docs (owner, collection, id, data, updated_at)
select 'dec0de00-0000-4000-8000-000000000001', 'holdings', h.hid,
  jsonb_build_object('name', h.name, 'ticker', h.ticker, 'market', h.market, 'currency', h.currency, 'kind', 'stock', 'role', 'none',
    'qty', h.qty, 'avg', h.avg, 'price', px.price, 'prevClose', px.price, 'priceAt', to_char(now() at time zone 'Asia/Seoul', 'YYYY-MM-DD'),
    'companyId', h.cid, 'updatedAt', to_char(now() at time zone 'Asia/Seoul', 'YYYY-MM-DD')),
  now()
from h join px on px.cid = h.cid;

-- 결정 일지: 왜 샀는지, 지나고 보니 어땠는지
insert into public.docs (owner, collection, id, data, updated_at)
select 'dec0de00-0000-4000-8000-000000000001', 'journal', j.id,
  jsonb_build_object('date', j.d, 'ticker', j.t, 'action', j.a, 'mind', j.m, 'reason', j.r, 'review', j.rv, 'companyId', j.cid,
    'checklist', case when j.a in ('신규 매수','추가 매수') then jsonb_build_object('filing', j.ck, 'sell', j.ck, 'hold10', j.ck) end),
  now()
from (values
  ('dj-1', '2024-11-04', '카카오', '신규 매수', '남들 따라', 'AI 테마로 오른다는 이야기를 듣고 150주 매수 (평균 52,800원). 이익과 적정 가격은 확인하지 않았다.', '-40%. 이익 대비 비싼 가격에 테마만 보고 샀다. 매도 조건도 정하지 않았다. 다시는 숫자 없이 사지 않는다.', 'dc-kakao', false),
  ('dj-2', '2024-12-10', '룰루레몬', '신규 매수', '확신', '브랜드와 성장률이 좋아 PER 30배를 감수하고 25주 매수 (평균 $312). 매도 조건: 매출 성장률 5% 미만.', '-70%. 10년 보유 테스트를 통과하지 못하는 유행 업종을 비싸게 샀다. 매도 조건에 닿았을 때 팔지 못한 것이 더 큰 실수.', 'dc-lulu', true),
  ('dj-3', '2025-01-15', '코카콜라', '신규 매수', '근거 기반', '배당 60년 이상 증가, 적정 가격 대비 25% 할인. 30주 매수 (평균 $62.5).', '+47%. 지루하지만 원칙대로 산 종목이 꾸준히 올랐다.', 'dc-ko', true),
  ('dj-4', '2025-03-12', 'KB금융', '신규 매수', '근거 기반', 'PBR 0.4배, 주주환원 확대. 안전마진 40%에서 80주 매수 (평균 98,500원).', '+62%. 가장 잘한 투자. 아무도 관심 없을 때 숫자를 보고 샀다.', 'dc-kb', true),
  ('dj-5', '2025-04-08', '삼성전자', '신규 매수', '근거 기반', '메모리 업황 바닥, PBR 1배 미만. 적정 매수가 아래에서 90주 매수 (평균 158,000원).', '+47%. 업황이 돌아오며 크게 올랐다. 사이클 정점 신호가 보이면 매도 조건대로 절반 정리할 계획.', 'dc-samsung', true),
  ('dj-6', '2025-06-20', '버크셔 해서웨이', '신규 매수', '근거 기반', '포트폴리오의 기본 축. 12주 매수 (평균 $470).', '+12%. 큰 수익은 아니지만 하락장에서도 흔들리지 않았다.', 'dc-brk', true),
  ('dj-7', '2026-02-18', '테슬라', '신규 매수', '조급함', '도전 칸(5% 이하)에서 5주 매수 (평균 $410). 손절선 -30%.', '-10%. 비중을 작게 지켜서 손실이 전체에 주는 영향은 작다.', 'dc-tsla', true),
  ('dj-8', '2026-08-28', '룰루레몬', '보류', '손실 회피', '매출 성장률이 4%로 매도 조건에 닿았지만 본전 생각에 팔지 못했다.', '손실을 확정하기 싫은 마음(손실 회피)이 원칙을 이겼다. 이번 분기 안에 정리한다.', 'dc-lulu', false)
) j(id, d, t, a, m, r, rv, cid, ck);

-- 설정: 운영자 계정의 할인율·국채금리 등 기준값을 그대로 쓰고, 현금 1,000만 원, 처음 안내·동의·기본 정보는 완료 상태
insert into public.docs (owner, collection, id, data, updated_at)
select 'dec0de00-0000-4000-8000-000000000001', 'settings', 'main',
  (s.data - 'prog' - 'investor') || jsonb_build_object(
    'cashKRW', 10000000,
    'prog', jsonb_build_object('consentV1', now(), 'introV3', '2026-10-15', 'introV2', '2026-10-15', 'introDone', '2026-10-15', 'lastLevel', 3),
    'investor', jsonb_build_object('done', '2026-10-15', 'at', '2026-10-15', 'size', '5천만~2억 원', 'count', '4~7개',
      'markets', '["한국 주식","미국 주식"]'::jsonb, 'horizon', '1~3년', 'style', '균형형', 'exp', '1~5년',
      'expect', '["좋은 회사 고르는 기준","적정 매수가·매수 시점 알림","내 포트폴리오 점검"]'::jsonb)),
  now()
from public.docs s where s.owner = public.publisher_id() and s.collection = 'settings' and s.id = 'main';

-- 예시 알림 (푸시는 보내지 않음)
insert into public.docs (owner, collection, id, data, updated_at) values
  ('dec0de00-0000-4000-8000-000000000001', 'alerts', 'buy-dc-dbins-2026-10',
   jsonb_build_object('at', now() - interval '3 hours', 'level', 'good', 'title', 'DB손해보험 적정 매수가 도달', 'body', '', 'link', jsonb_build_object('co', 'dc-dbins'), 'read', false, 'push', false, 'source', '장부 판정'), now()),
  ('dec0de00-0000-4000-8000-000000000001', 'alerts', 'sell-dh-lulu-2026-10',
   jsonb_build_object('at', now() - interval '1 day', 'level', 'warn', 'title', '룰루레몬 매도 조건 도달', 'body', '매출 성장률이 정해 둔 매도 조건(5% 미만)에 닿았습니다. 결정 일지를 확인하세요.', 'link', jsonb_build_object('co', 'dc-lulu'), 'read', false, 'push', false, 'source', '장부 판정'), now());

-- 결과 확인
select collection, count(*) from public.docs where owner = 'dec0de00-0000-4000-8000-000000000001' group by 1 order by 1;
