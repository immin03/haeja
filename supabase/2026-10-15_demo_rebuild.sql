-- 체험 계정(demo@valuenote.app) 예시 데이터 교체 — Supabase → SQL Editor에 붙여넣고 Run 한 번
-- 구성: 남들이 외면하던 저평가 회사(잘한 투자) vs 유행 따라 산 회사(못한 투자). 튜토리얼 예시와 같은 구성.
-- 체험 계정의 설정(동의·튜토리얼 완료)은 유지하고, 종목·일지·알림만 새로 채운다.

delete from public.docs where owner = public.demo_id() and collection in ('companies','holdings','journal','alerts');

with rows as (
  select r from public.docs d, jsonb_array_elements(d.data -> 'rows') r
  where d.owner = public.publisher_id() and d.collection = 'screen' and d.id like 'chunk-%'
),
pick(t, cid, pinned, created, qual, thesis) as (values
  ('005830.KS', 'dc-dbins', false, '2025-03-12',
   '{"circle":true,"moats":["scale"],"hold10":true,"inversion":"자동차보험 손해율이 구조적으로 악화되는 경우"}'::jsonb,
   '{"why":"보험주가 외면받던 때 PER 4배, ROE 17%에서 매수","edge":"지루한 업종일수록 가격이 싸다","sell1":"합산비율이 3년 연속 100%를 넘으면 재점검","sell2":"PBR 1.2배를 넘으면 비중 축소","sell3":"","target":null,"conviction":4,"reviewDate":"2026-12-31","status":"유효"}'::jsonb),
  ('175330.KS', 'dc-jb', false, '2025-02-20',
   '{"circle":true,"moats":["scale","switch"],"hold10":true,"inversion":"지역 경기 침체로 연체율이 급등하는 경우"}'::jsonb,
   '{"why":"지방은행이라 관심 밖. PBR 0.4배, 배당과 자사주 소각 확대","edge":"주주환원 확대에 따른 재평가","sell1":"연체율이 2배로 오르면 재점검","sell2":"PBR 1배를 넘으면 절반 매도","sell3":"","target":null,"conviction":4,"reviewDate":"2026-12-31","status":"유효"}'::jsonb),
  ('086280.KS', 'dc-glovis', false, '2025-05-07',
   '{"circle":true,"moats":["scale","switch"],"hold10":true,"inversion":"계열사 물량이 줄고 외부 화주 확보에 실패하는 경우"}'::jsonb,
   '{"why":"물류라 지루한 업종. 순현금, ROE 15%, PER 6배","edge":"","sell1":"계열사 물량 의존도가 크게 늘면 재점검","sell2":"","sell3":"","target":null,"conviction":4,"reviewDate":"2026-12-31","status":"유효"}'::jsonb),
  ('111770.KS', 'dc-youngone', false, '2025-01-22',
   '{"circle":true,"moats":["cost","switch"],"hold10":true,"inversion":"주요 고객사 주문이 장기간 끊기는 경우"}'::jsonb,
   '{"why":"의류 OEM이라 인기 없음. 순유동자산만 주가의 70%","edge":"","sell1":"영업이익률 10% 미만이 2년 이어지면 재점검","sell2":"","sell3":"","target":null,"conviction":3,"reviewDate":"2026-12-31","status":"유효"}'::jsonb),
  ('CB', 'dc-chubb', false, '2025-06-18',
   '{"circle":true,"moats":["scale","brand"],"hold10":true,"inversion":"대형 재해 손실이 구조적으로 커지는 경우"}'::jsonb,
   '{"why":"버크셔가 사들인 보험사. 손해율 관리가 업계 최상위","edge":"","sell1":"손해율이 업계 평균보다 3년 연속 나쁘면 재점검","sell2":"","sell3":"","target":null,"conviction":4,"reviewDate":"2027-06-30","status":"유효"}'::jsonb),
  ('9433.T', 'dc-kddi', false, '2025-08-05',
   '{"circle":true,"moats":["scale","switch"],"hold10":true,"inversion":"통신요금 인하 규제가 강해지는 경우"}'::jsonb,
   '{"why":"일본 통신 2위. 자사주 매입이 꾸준하고 배당 증가","edge":"","sell1":"배당 증가가 멈추면 재점검","sell2":"","sell3":"","target":null,"conviction":3,"reviewDate":"2027-03-31","status":"유효"}'::jsonb),
  ('035720.KS', 'dc-kakao', false, '2024-11-04',
   '{"circle":false,"moats":["network"],"hold10":null,"inversion":"광고·커머스 성장이 멈추고 AI 투자비만 늘어나는 경우"}'::jsonb,
   '{"why":"AI 테마 기대. 숫자를 확인하지 않고 샀다.","edge":"","sell1":"","sell2":"","sell3":"","target":null,"conviction":2,"reviewDate":"2026-11-30","status":"점검 필요","memo":"매도 조건 없이 산 종목. 이익 대비 비싸게 샀다."}'::jsonb),
  ('TSLA', 'dc-tsla', false, '2026-02-18',
   '{"circle":false,"moats":["brand"],"hold10":null,"inversion":"자율주행·로봇 기대가 실적으로 이어지지 않는 경우"}'::jsonb,
   '{"why":"로봇·자율주행 기대감에 신고가 추격","edge":"","sell1":"-30%면 손절","sell2":"","sell3":"","target":null,"conviction":2,"reviewDate":"2026-12-31","status":"점검 필요","memo":"적정 가격 확인 없이 매수"}'::jsonb),
  ('LULU', 'dc-lulu', false, '2024-12-10',
   '{"circle":true,"moats":["brand"],"hold10":false,"inversion":"유행이 바뀌어 브랜드 프리미엄이 사라지는 경우"}'::jsonb,
   '{"why":"유행하는 브랜드, PER 40배를 감수했다.","edge":"","sell1":"매출 성장률이 5% 아래로 떨어지면 매도","sell2":"","sell3":"","target":null,"conviction":2,"reviewDate":"2026-10-31","status":"점검 필요","memo":"회사는 여전히 우량(ROE 36%)하지만 PER 40배에 샀다. 성장 둔화로 배수가 10배로 내려오며 −75%. 좋은 회사도 비싸게 사면 크게 잃는다."}'::jsonb),
  ('071050.KS', 'dc-kih', true, '2026-09-02',
   '{"circle":true,"moats":["scale"],"hold10":true,"inversion":""}'::jsonb,
   '{"why":"증권업 이익 급증, PBR 0.6배. 적정 매수가 대기","edge":"","sell1":"","sell2":"","sell3":"","target":null,"conviction":3,"reviewDate":"","status":"유효"}'::jsonb),
  ('SNY', 'dc-sanofi', true, '2026-09-10',
   '{"circle":true,"moats":["brand","scale"],"hold10":true,"inversion":""}'::jsonb,
   '{"why":"제약업 비관론으로 PER 11배. 가격 대기","edge":"","sell1":"","sell2":"","sell3":"","target":null,"conviction":3,"reviewDate":"","status":"유효"}'::jsonb)
)
insert into public.docs (owner, collection, id, data, updated_at)
select public.demo_id(), 'companies', p.cid,
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

-- 보유 종목: 주식 약 4,600만 원 + 현금 700만 원
with px as (select id cid, (data ->> 'price')::numeric price, data ->> 'market' market from public.docs where owner = public.demo_id() and collection = 'companies'),
h(hid, cid, name, ticker, qty, avg) as (values
  ('dh-dbins',   'dc-dbins',    'DB손해보험',  '005830', 70, 98000),
  ('dh-jb',      'dc-jb',       'JB금융지주',  '175330', 300, 14800),
  ('dh-glovis',  'dc-glovis',   '현대글로비스', '086280', 40, 118000),
  ('dh-youngone','dc-youngone', '영원무역',    '111770', 60, 41500),
  ('dh-chubb',   'dc-chubb',    '처브',        'CB',     8, 268),
  ('dh-kddi',    'dc-kddi',     'KDDI',        '9433',   100, 2420),
  ('dh-kakao',   'dc-kakao',    '카카오',      '035720', 100, 54000),
  ('dh-tsla',    'dc-tsla',     '테슬라',      'TSLA',   5, 470),
  ('dh-lulu',    'dc-lulu',     '룰루레몬',    'LULU',   8, 380)
)
insert into public.docs (owner, collection, id, data, updated_at)
select public.demo_id(), 'holdings', h.hid,
  jsonb_build_object('name', h.name, 'ticker', h.ticker, 'market', px.market,
    'currency', case px.market when 'US' then 'USD' when 'JP' then 'JPY' when 'HK' then 'HKD' when 'CN' then 'CNY' else 'KRW' end,
    'kind', 'stock', 'role', 'none', 'qty', h.qty, 'avg', h.avg, 'price', px.price, 'prevClose', px.price,
    'priceAt', to_char(now() at time zone 'Asia/Seoul', 'YYYY-MM-DD'), 'companyId', h.cid, 'updatedAt', to_char(now() at time zone 'Asia/Seoul', 'YYYY-MM-DD')),
  now()
from h join px on px.cid = h.cid;

update public.docs set data = jsonb_set(data, '{cashKRW}', '7000000') where owner = public.demo_id() and collection = 'settings' and id = 'main';

-- 결정 일지
insert into public.docs (owner, collection, id, data, updated_at)
select public.demo_id(), 'journal', j.id,
  jsonb_build_object('date', j.d, 'ticker', j.t, 'action', j.a, 'mind', j.m, 'reason', j.r, 'review', j.rv, 'companyId', j.cid,
    'checklist', case when j.a in ('신규 매수','추가 매수') then jsonb_build_object('filing', j.ck, 'sell', j.ck, 'hold10', j.ck) end),
  now()
from (values
  ('dj-1', '2024-11-04', '카카오', '신규 매수', '남들 따라', 'AI 테마로 오른다는 소식에 100주 매수 (평균 54,000원). 이익과 적정 가격은 확인하지 않았다.', '-43%. 이익 대비 비싼 가격에 테마만 보고 샀다. 매도 조건도 없었다.', 'dc-kakao', false),
  ('dj-2', '2024-12-10', '룰루레몬', '신규 매수', '확신', '유행 브랜드라 PER 40배를 감수하고 8주 매수 (평균 $380). 매도 조건: 매출 성장률 5% 미만.', '-75%. 회사는 지금도 돈을 잘 벌지만 성장 기대가 꺼지며 PER이 40배에서 10배로 내려왔다. 좋은 회사를 너무 비싸게 산 실수.', 'dc-lulu', true),
  ('dj-3', '2025-01-22', '영원무역', '신규 매수', '근거 기반', '의류 OEM이라 아무도 관심 없을 때, 순유동자산만 주가의 70%인 가격에 60주 매수 (평균 41,500원).', '+82%. 숫자가 싼 회사는 관심이 돌아오면 크게 오른다.', 'dc-youngone', true),
  ('dj-4', '2025-02-20', 'JB금융지주', '신규 매수', '근거 기반', '지방은행이라 관심 밖일 때 PBR 0.4배에서 300주 매수 (평균 14,800원).', '+79%. 주주환원이 늘면서 시장이 재평가했다.', 'dc-jb', true),
  ('dj-5', '2025-03-12', 'DB손해보험', '신규 매수', '근거 기반', '보험주 소외 구간, PER 4배·ROE 17%에서 70주 매수 (평균 98,000원).', '+90%. 지루한 업종일수록 가격이 싸다는 걸 확인했다.', 'dc-dbins', true),
  ('dj-6', '2025-05-07', '현대글로비스', '신규 매수', '근거 기반', '순현금 물류 회사를 PER 6배에 40주 매수 (평균 118,000원).', '+51%. 꾸준히 돈 버는 회사를 싸게 산 결과.', 'dc-glovis', true),
  ('dj-7', '2026-02-18', '테슬라', '신규 매수', '조급함', '로봇 기대감에 신고가 추격 매수 5주 (평균 $470).', '-22%. 적정 가격을 보지 않고 분위기에 산 매수.', 'dc-tsla', false),
  ('dj-8', '2026-08-28', '룰루레몬', '보류', '손실 회피', '매출 성장률이 4%로 매도 조건에 닿았지만 본전 생각에 팔지 못했다.', '손실을 확정하기 싫은 마음이 원칙을 이겼다. 이번 분기 안에 정리한다.', 'dc-lulu', false)
) j(id, d, t, a, m, r, rv, cid, ck);

-- 예시 알림 (푸시는 보내지 않음)
insert into public.docs (owner, collection, id, data, updated_at) values
  (public.demo_id(), 'alerts', 'buy-dc-kih-2026-10',
   jsonb_build_object('at', now() - interval '3 hours', 'level', 'good', 'title', '한국금융지주 적정 매수가 도달', 'body', '', 'link', jsonb_build_object('co', 'dc-kih'), 'read', false, 'push', false, 'source', '장부 판정'), now()),
  (public.demo_id(), 'alerts', 'sell-dh-lulu-2026-10',
   jsonb_build_object('at', now() - interval '1 day', 'level', 'warn', 'title', '룰루레몬 매도 조건 도달', 'body', '매출 성장률이 정해 둔 매도 조건(5% 미만)에 닿았습니다. 결정 일지를 확인하세요.', 'link', jsonb_build_object('co', 'dc-lulu'), 'read', false, 'push', false, 'source', '장부 판정'), now());

-- 결과 확인: holdings 9, companies 11, journal 8, alerts 2
select collection, count(*) from public.docs where owner = public.demo_id() group by 1 order by 1;
