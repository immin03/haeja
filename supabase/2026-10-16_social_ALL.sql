-- ValueNote SNS 자동 게시: Supabase SQL Editor에 통째로 붙여 넣고 Run
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
insert into public.app_config(key,value) values ('social_paused','true'::jsonb) on conflict (key) do nothing;

-- 카드뉴스 30편 게시 대기열 (1일차 = 2026-10-16)
insert into public.social_posts (id, seq, title, scheduled_at, caption, hashtags, threads_tag, images, to_ig, to_threads) values
('01',1,'ValueNote 소개','2026-10-16T12:30:00+09:00','ValueNote는 그레이엄·버핏·멍거의 투자 기준을 숫자로 옮긴 가치투자 노트다. 한국·미국·일본·중국·홍콩 5개 시장 620개 기업을 매주 자동으로 채점하고, 회사마다 적정 매수가를 계산해 그 가격에 오면 알려 준다. 공식은 버크셔 해서웨이의 실제 매수 62건으로 사후 검증했다. 내일 오를 종목을 맞히는 앱은 아니다. 좋은 회사를 적정 가격에 사서 오래 들고 가려는 사람을 위한 도구다. 이 계정에서는 검증 과정에서 나온 발견과 투자 함정을 매일 정리한다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['가치투자','워렌버핏','주식공부','장기투자','밸류노트']::text[],'가치투자',array['/social/01/01.jpg','/social/01/02.jpg','/social/01/03.jpg','/social/01/04.jpg','/social/01/05.jpg','/social/01/06.jpg','/social/01/07.jpg','/social/01/08.jpg'],true,true),
('02',2,'세 거인의 질문','2026-10-16T18:00:00+09:00','가치투자의 세 대가는 서로 다른 질문을 던졌다. 그레이엄은 얼마에 사는가를 물었고, 답은 내재가치보다 충분히 싸게 사는 안전마진이었다. 버핏은 무엇을 사는가를 물었고, 10년 뒤에도 더 커질 해자 있는 사업을 골랐다. 멍거는 무엇을 피할지를 먼저 물었다. 모르는 사업과 믿기 어려운 경영진, 빚에 기댄 성장을 지우는 것이다. ValueNote의 기업 점수는 이 세 질문을 저평가·품질·감점으로 나눠 합친 것이다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['가치투자','벤저민그레이엄','워렌버핏','찰리멍거','주식공부']::text[],'주식공부',array['/social/02/01.jpg','/social/02/02.jpg','/social/02/03.jpg','/social/02/04.jpg','/social/02/05.jpg','/social/02/06.jpg'],false,true),
('03',3,'폭락장 투자자 5유형','2026-10-16T21:00:00+09:00','같은 20% 하락을 보고도 투자자는 다섯 가지로 갈린다. 계산기를 꺼내는 바겐 헌터, 좋은 회사면 그냥 두는 장기 보유자, 안 될 이유부터 찾는 실수 회피자, 유행을 갈아타는 테마 서퍼, 오르면 사고 떨어지면 파는 롤러코스터 탑승자다. 유형보다 중요한 것은 내 습관을 알고 규칙을 세우는 것이다. ValueNote의 5문항 테스트로 내 유형을 확인하고 결과 카드를 공유할 수 있다. 나는 몇 번인지 댓글로 남겨 달라. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['투자성향테스트','주식','재테크','가치투자','밸류노트']::text[],'투자성향테스트',array['/social/03/01.jpg','/social/03/02.jpg','/social/03/03.jpg','/social/03/04.jpg','/social/03/05.jpg','/social/03/06.jpg'],false,true),
('04',4,'품질 점수의 반전','2026-10-17T08:00:00+09:00','버크셔 해서웨이가 실제로 산 회사들을 매수 당시의 재무와 가격으로 다시 채점했다. 1차 표본 24건에서 성공한 투자의 품질 점수 평균은 56점, 실패한 투자는 69점이었다. 좋은 회사 점수가 오히려 실패 쪽에서 높았다. 반대로 저평가 점수는 성공 50점, 실패 37점이었다. 버크셔는 원래 좋은 회사만 고르기 때문에, 그 안에서 결과를 가른 것은 산 가격이었다. 이 결과로 ValueNote 공식은 품질 40, 저평가 60으로 바뀌었다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['워렌버핏','버크셔해서웨이','가치투자','주식공부','백테스트']::text[],'워렌버핏',array['/social/04/01.jpg','/social/04/02.jpg','/social/04/03.jpg','/social/04/04.jpg','/social/04/05.jpg','/social/04/06.jpg'],false,true),
('05',5,'코카콜라 1988','2026-10-17T12:30:00+09:00','1988년 버핏이 코카콜라를 살 때 코카콜라의 이익수익률은 5.8%, 미국 국채 금리는 8.9%였다. 이익수익률이 국채 금리보다 높아야 싸다고 보는 흔한 공식으로는 탈락이었다. 버핏은 지금의 이익이 아니라 앞으로 커질 이익을 봤다. ValueNote가 PER 하나로 판단하지 않고 역DCF를 쓰는 이유다. 지금 주가가 가정한 성장률과 회사가 실제로 보여 준 성장률을 비교한다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['코카콜라','워렌버핏','가치투자','PER','주식공부']::text[],'워렌버핏',array['/social/05/01.jpg','/social/05/02.jpg','/social/05/03.jpg','/social/05/04.jpg','/social/05/05.jpg','/social/05/06.jpg'],false,true),
('06',6,'버크셔 62건 전수 채점','2026-10-17T21:00:00+09:00','버크셔 해서웨이가 실제로 산 62건을 매수 당시의 재무와 주가로 다시 채점했다. 결론부터 말하면 점수로 버핏의 성공작을 골라낼 수는 없었다. 대신 실패를 피하는 데는 효과가 있었다. 매수 시점 점수가 60점 이상이었던 27건의 실패율은 15%, 60점 미만 35건의 실패율은 37%였다. 경기 바닥의 에너지주나 일본 종합상사처럼 숫자 밖에서 나온 성공도 많았다. 그래서 ValueNote는 점수를 고르는 도구가 아니라 거르는 도구로 쓴다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['버크셔해서웨이','워렌버핏','가치투자','백테스트','주식공부']::text[],'버크셔해서웨이',array['/social/06/01.jpg','/social/06/02.jpg','/social/06/03.jpg','/social/06/04.jpg','/social/06/05.jpg','/social/06/06.jpg','/social/06/07.jpg','/social/06/08.jpg','/social/06/09.jpg'],true,true),
('07',7,'버핏의 2004년 한국 주식','2026-10-18T08:00:00+09:00','2004년 버핏은 버크셔가 아닌 개인 계좌로 한국 주식 약 20개를 샀다. 한국 상장사 자료집을 넘기며 이익에 비해 주가가 지나치게 싼 회사를 골랐다. 버크셔가 한국 주식을 잘 사지 않는 이유는 실력이 아니라 규모다. 한 번에 수조 원을 넣을 곳이 필요하기 때문이다. 개인 투자자에게는 이 제약이 없다. 그래서 ValueNote는 버크셔가 살 수 있는 규모인지와 버핏의 기준을 통과하는지를 나눠 보여 준다. 코스피 100, 코스닥 50 종목도 같은 기준으로 채점한다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['워렌버핏','한국주식','가치투자','코스피','주식공부']::text[],'한국주식',array['/social/07/01.jpg','/social/07/02.jpg','/social/07/03.jpg','/social/07/04.jpg','/social/07/05.jpg','/social/07/06.jpg'],false,true),
('08',8,'좋은 회사 ≠ 좋은 주식','2026-10-18T12:30:00+09:00','버크셔 해서웨이의 상위 보유 종목을 오늘 숫자로 채점하면 품질 점수는 최상위인데 종합 75점을 넘는 종목이 없다. 좋은 회사라는 사실이 이미 주가에 반영돼 안전마진이 사라졌기 때문이다. 버크셔도 2024년 애플 지분의 상당 부분을 팔았다. ValueNote는 품질 80점 이상이고 위험 신호가 없는 회사를 탈락시키지 않고 가격 대기 목록에 둔다. 적정 매수가에 오면 알림이 간다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['버크셔해서웨이','가치투자','안전마진','주식공부','장기투자']::text[],'가치투자',array['/social/08/01.jpg','/social/08/02.jpg','/social/08/03.jpg','/social/08/04.jpg','/social/08/05.jpg','/social/08/06.jpg'],false,true),
('09',9,'숫자는 완벽했는데 버핏도 졌다','2026-10-18T21:00:00+09:00','버크셔 해서웨이의 실패 사례 중에는 숫자가 훌륭했던 회사가 많다. IBM은 클라우드 전환에 밀렸고, 크래프트하인즈는 브랜드의 힘이 약해져 2019년 대규모 손상 처리를 했으며, 덱스터 슈는 값싼 해외 생산에 산업 자체가 넘어갔다. 세 회사 모두 10년 뒤에도 이 사업이 지금보다 클 것인가라는 질문에서 틀렸다. ValueNote는 숫자 점수 다음에 10년 보유 테스트, 회사를 망가뜨릴 시나리오, 매도 조건 3가지를 회사마다 자동으로 정리한다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['워렌버핏','투자실패','가치투자','주식공부','장기투자']::text[],'워렌버핏',array['/social/09/01.jpg','/social/09/02.jpg','/social/09/03.jpg','/social/09/04.jpg','/social/09/05.jpg','/social/09/06.jpg','/social/09/07.jpg','/social/09/08.jpg'],true,true),
('10',10,'적정 매수가 = 내재가치 70%','2026-10-19T08:00:00+09:00','내재가치 계산은 가정 하나만 바뀌어도 크게 흔들린다. 그레이엄은 계산이 틀려도 손해 보지 않을 만큼 싸게 사라고 했고, 이 여유를 안전마진이라 불렀다. ValueNote는 회사마다 내재가치를 계산하고 그 70%를 적정 매수가로 잡는다. 30%의 안전마진이다. 할인율을 1%p 올리고 내렸을 때의 가격 범위도 함께 보여 준다. 관심 종목이 그 가격에 오면 알림이 간다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['안전마진','벤저민그레이엄','내재가치','가치투자','주식공부']::text[],'가치투자',array['/social/10/01.jpg','/social/10/02.jpg','/social/10/03.jpg','/social/10/04.jpg','/social/10/05.jpg','/social/10/06.jpg'],false,true),
('11',11,'역DCF','2026-10-19T12:30:00+09:00','보통의 가치 계산은 성장률을 먼저 가정한다. 가정이 낙관적이면 결과도 낙관적이다. 역DCF는 반대로 지금 주가가 정당하려면 앞으로 몇 % 성장해야 하는지를 구한다. 예를 들어 가상의 홍길동전자 주가가 연 12% 성장을 가정하는데 지난 5년 실제 성장률이 연 5%라면, 시장은 회사의 실력보다 두 배 넘게 기대하고 있는 것이다. ValueNote는 모든 기업에 이 비교를 자동으로 붙인다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['DCF','가치투자','주식공부','밸류에이션','재무제표']::text[],'주식공부',array['/social/11/01.jpg','/social/11/02.jpg','/social/11/03.jpg','/social/11/04.jpg','/social/11/05.jpg','/social/11/06.jpg'],false,true),
('12',12,'점수 공식 공개','2026-10-19T21:00:00+09:00','ValueNote의 기업 점수는 100점 만점이다. 품질 40%와 저평가 60%로 나뉜다. 품질은 ROE, ROIC, 이익률, 현금흐름 전환율, 부채, 주식 수 증가 등 13개 지표로 보고, 저평가는 역DCF로 본 기대 성장률과 30% 안전마진으로 본다. 잦은 적자, 과도한 빚, 잦은 증자, 이익 정점, 성장 둔화는 감점하되 한도를 둔다. 가격 비중이 더 큰 이유는 버크셔 62건 검증에서 결과를 가른 것이 산 가격이었기 때문이다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['가치투자','ROE','재무제표','주식공부','밸류노트']::text[],'가치투자',array['/social/12/01.jpg','/social/12/02.jpg','/social/12/03.jpg','/social/12/04.jpg','/social/12/05.jpg','/social/12/06.jpg','/social/12/07.jpg','/social/12/08.jpg','/social/12/09.jpg'],true,true),
('13',13,'3배 레버리지의 함정','2026-10-20T08:00:00+09:00','지수가 하루 10% 오르고 다음 날 10% 빠지면 100은 99가 된다. 같은 이틀 동안 3배 레버리지 상품은 130을 찍고 91로 내려온다. 지수는 1% 빠졌는데 3배 상품은 9%를 잃는다. 레버리지 상품은 매일 하루 수익률의 3배를 따라가도록 다시 맞추기 때문에, 오르내림이 반복될수록 손실이 쌓인다. 몇 달 이상 들고 가는 용도로는 맞지 않는다. ValueNote는 보유 중인 레버리지 상품에 장기 보유 경고를 붙인다. 이 글은 투자 교육용 정보이며 특정 상품의 매수·매도 권유가 아니다.',array['레버리지ETF','ETF','주식공부','재테크','투자공부']::text[],'ETF',array['/social/13/01.jpg','/social/13/02.jpg','/social/13/03.jpg','/social/13/04.jpg','/social/13/05.jpg','/social/13/06.jpg'],false,true),
('14',14,'배당률의 착각','2026-10-20T12:30:00+09:00','배당은 공짜 돈이 아니다. 회사 이익에서 나가고, 배당락일에는 대체로 배당만큼 주가가 내려간다. 그래서 배당주에서 볼 것은 배당률이 아니라 불황에도 그 배당을 유지할 수 있느냐다. 번 현금으로 배당을 감당하는지, 과거 불황 때 배당을 깎았는지, 빚을 내서 배당하지는 않는지를 본다. 주가가 반토막 나면 배당률은 두 배로 보인다는 점도 기억해야 한다. ValueNote는 배당 성향 투자자에게 배당 적합 종목을 따로 표시한다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['배당주','배당투자','가치투자','주식공부','재테크']::text[],'배당주',array['/social/14/01.jpg','/social/14/02.jpg','/social/14/03.jpg','/social/14/04.jpg','/social/14/05.jpg','/social/14/06.jpg'],false,true),
('15',15,'PER 5배의 함정','2026-10-20T21:00:00+09:00','PER은 주가를 올해 이익으로 나눈 값이라, 업황이 최고일 때 가장 낮아 보인다. 경기 고점의 낮은 PER은 싸다는 신호가 아니라 꼭지 신호일 수 있다. ValueNote는 최근 주당순이익이 5년 평균의 1.5배를 넘는데 매출 성장이 10% 이하인 회사를 이익 정점 가능으로 표시하고 감점한다. 1차 채점 221개 기업 중 19개에 이 경고가 붙었다. 여러 해 평균 이익으로 계산한 PER도 함께 보여 준다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['PER','가치함정','가치투자','주식공부','재무제표']::text[],'주식공부',array['/social/15/01.jpg','/social/15/02.jpg','/social/15/03.jpg','/social/15/04.jpg','/social/15/05.jpg','/social/15/06.jpg','/social/15/07.jpg','/social/15/08.jpg'],true,true),
('16',16,'매수 전 3가지 질문','2026-10-21T08:00:00+09:00','매수 버튼을 누르기 전에 세 가지만 묻자. 첫째, 기사나 영상 요약이 아니라 회사가 낸 공시 원문을 직접 확인했는가. 둘째, 언제 팔지 매도 조건 3가지를 미리 적었는가. 사는 순간이 가장 냉정할 때다. 셋째, 주식시장이 10년 문을 닫아도 마음 편히 들고 있을 회사인가. ValueNote는 이 세 가지에 체크해야 매수 기록이 저장되도록 만들었다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['주식공부','투자원칙','가치투자','재테크','워렌버핏']::text[],'투자원칙',array['/social/16/01.jpg','/social/16/02.jpg','/social/16/03.jpg','/social/16/04.jpg','/social/16/05.jpg'],false,true),
('17',17,'투자자 레벨 5단계','2026-10-21T12:30:00+09:00','ValueNote의 투자자 레벨은 5단계다. 뉴스와 감으로 사는 1단계 투기꾼에서 시작해, 가격과 가치를 구분하고 기다릴 줄 아는 5단계 현명한 투자자로 올라간다. 마지막 단계의 이름은 그레이엄의 책 제목에서 따왔다. 레벨은 수익률이 아니라 원칙대로 행동했는지로 오른다. 그레이엄·버핏·멍거·습관 네 갈래의 미션 18개가 있다. 지금 몇 단계인지 댓글로 남겨 달라. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['현명한투자자','가치투자','주식공부','투자습관','밸류노트']::text[],'가치투자',array['/social/17/01.jpg','/social/17/02.jpg','/social/17/03.jpg','/social/17/04.jpg','/social/17/05.jpg','/social/17/06.jpg'],false,true),
('18',18,'폭락장 투자자 테스트(미니)','2026-10-21T21:00:00+09:00','보유 종목이 하루에 15% 빠지면 어떻게 하는가. 친구가 무조건 오른다고 하면, 수익이 30% 나면 어떻게 하는가. 네 문항에 답하고 가장 많이 고른 알파벳을 세면 된다. A는 바겐 헌터 그레이엄형, B는 장기 보유자 버핏형, C는 실수 회피자 멍거형, D는 테마 서퍼, E는 롤러코스터 탑승자다. D나 E가 나왔다면 테마 투자를 전체의 10% 안에 가두는 규칙부터 세워 보자. 결과를 댓글로 남기고 친구에게도 보내 보자. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['투자성향테스트','심리테스트','주식','재테크','가치투자']::text[],'투자성향테스트',array['/social/18/01.jpg','/social/18/02.jpg','/social/18/03.jpg','/social/18/04.jpg','/social/18/05.jpg','/social/18/06.jpg','/social/18/07.jpg','/social/18/08.jpg'],true,true),
('19',19,'집중인가 몰빵인가','2026-10-22T08:00:00+09:00','멍거는 제대로 아는 좋은 회사가 많지 않으니 몇 개에 집중하는 것이 합리적이라고 봤다. 다만 집중은 잘 아는 회사와 충분한 안전마진이 있을 때만 성립한다. 둘 다 없다면 그것은 집중이 아니라 몰빵이다. 버핏도 대부분의 사람에게는 인덱스 펀드를 권했다. ValueNote는 상위 종목 비중과 업종·시장 쏠림, 현금 비중을 보고 집중의 균형을 점검한다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['포트폴리오','분산투자','찰리멍거','가치투자','주식공부']::text[],'포트폴리오',array['/social/19/01.jpg','/social/19/02.jpg','/social/19/03.jpg','/social/19/04.jpg','/social/19/05.jpg','/social/19/06.jpg'],false,true),
('20',20,'핵심 90 · 탐험 10','2026-10-22T12:30:00+09:00','코인이나 테마주를 끊지 못하겠다면 끊는 대신 가두는 방법이 있다. 포트폴리오를 원칙을 통과한 회사만 담는 핵심 칸 90%와 마음 가는 대로 하는 탐험 칸 10%로 나눈다. 탐험 칸에는 세 가지 규칙을 건다. 전체의 10%를 넘기지 않고, 레버리지를 쓰지 않으며, 0원이 돼도 생활이 흔들리지 않을 돈만 넣는다. ValueNote는 탐험 칸이 10%를 넘으면 알려 준다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['포트폴리오','코인','테마주','가치투자','재테크']::text[],'재테크',array['/social/20/01.jpg','/social/20/02.jpg','/social/20/03.jpg','/social/20/04.jpg','/social/20/05.jpg','/social/20/06.jpg'],false,true),
('21',21,'버핏과 기술주','2026-10-22T21:00:00+09:00','버핏이 기술주를 안 산다는 말은 반만 맞다. 버핏이 피한 것은 기술이 아니라 예측이었다. 2016년 애플을 살 때는 잘 떠나지 않는 고객과 이미 쌓인 현금흐름을 근거로 소비자 브랜드처럼 봤다. 2022년 TSMC는 몇 달 만에 팔았는데, 이유로 든 것은 기술이 아니라 지정학적 위험이었다. ValueNote는 기술주를 볼 때 주식보상비용을 뺀 현금흐름, 안정적인 매출총이익률, 순현금 여부를 함께 점검한다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['기술주','워렌버핏','가치투자','주식공부','장기투자']::text[],'기술주',array['/social/21/01.jpg','/social/21/02.jpg','/social/21/03.jpg','/social/21/04.jpg','/social/21/05.jpg','/social/21/06.jpg','/social/21/07.jpg','/social/21/08.jpg'],true,true),
('22',22,'알림','2026-10-23T08:00:00+09:00','ValueNote에서는 가격을 시스템이 지켜본다. 관심 종목이 적정 매수가에 닿으면 휴대폰이나 PC 브라우저로 알림이 온다. 알림은 무엇이 일어났는지와 내재가치까지 남은 거리만 한 줄로 보여 준다. 시장이 크게 빠진 날에는 기회 점검 카드가 떠서, 공포 대신 기준을 통과한 회사 목록을 보게 된다. 알림만 켜 두고 일상으로 돌아가면 된다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['주식알림','가치투자','장기투자','재테크','밸류노트']::text[],'장기투자',array['/social/22/01.jpg','/social/22/02.jpg','/social/22/03.jpg','/social/22/04.jpg','/social/22/05.jpg'],false,true),
('23',23,'10대 메가트렌드','2026-10-23T12:30:00+09:00','ValueNote는 AI 컴퓨트, 전력 인프라, 메모리와 HBM, 방산, 조선, 우주, 로봇, 비만치료제, 코리아 밸류업, 중국 테크 10개 흐름을 추적한다. 테마를 쫓으려는 것이 아니라 어떤 흐름이 과열인지 알고 비싸게 올라타는 실수를 피하려는 것이다. 각 흐름을 초기·성장·과열·성숙 4단계로 나누고, 바스켓 지수를 3개월부터 5년까지 차트로 비교한다. 매주 월요일 다시 정리한다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['메가트렌드','AI주식','테마주','주식공부','가치투자']::text[],'메가트렌드',array['/social/23/01.jpg','/social/23/02.jpg','/social/23/03.jpg','/social/23/04.jpg','/social/23/05.jpg','/social/23/06.jpg'],false,true),
('24',24,'아침 브리핑','2026-10-23T21:00:00+09:00','뉴스는 넘치지만 내 종목의 판단을 바꿔야 할 뉴스는 드물다. ValueNote 아침 브리핑은 매일 아침 8시 전에 보유 종목과 관심 종목의 뉴스와 종가를 모아 한 줄 요약부터 보여 준다. 실적 쇼크나 대규모 증자처럼 투자 논리를 흔드는 악재는 따로 표시하고, 실적 발표가 나오면 그 회사의 점수를 다시 매긴다. 매주 한 편은 시장과 금리, 환율, 투자 대가의 이야기를 칼럼으로 정리해 이메일로도 보낸다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['아침브리핑','주식뉴스','가치투자','재테크','밸류노트']::text[],'주식뉴스',array['/social/24/01.jpg','/social/24/02.jpg','/social/24/03.jpg','/social/24/04.jpg','/social/24/05.jpg','/social/24/06.jpg','/social/24/07.jpg','/social/24/08.jpg'],true,true),
('25',25,'경기순환주 감점 실험','2026-10-24T08:00:00+09:00','경기를 타는 철강이나 상사 업종은 위험하니 점수를 깎자는 규칙을 넣고 버크셔 해서웨이 매수 사례로 시험했다. 깎인 것은 실패작이 아니라 철강사 뉴코어와 일본 종합상사 같은 성공작이었다. 경기순환주는 업종이 문제가 아니라 사는 시점이 문제였다. 업황 바닥에서 사면 성공하고 고점에서 사면 실패한다. 그래서 감점 대신 경고만 표시하고, 고점 매수는 이익 정점 판별로 거른다. 그럴듯한 규칙도 검증 전에는 넣지 않는다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['경기순환주','버크셔해서웨이','가치투자','백테스트','주식공부']::text[],'가치투자',array['/social/25/01.jpg','/social/25/02.jpg','/social/25/03.jpg','/social/25/04.jpg','/social/25/05.jpg','/social/25/06.jpg'],false,true),
('26',26,'체험 계정','2026-10-24T12:30:00+09:00','ValueNote는 가입 전에 체험 계정으로 모든 화면을 써 볼 수 있다. 홍길동이라는 예시 투자자의 포트폴리오에는 눈에 잘 띄지 않던 저평가 우량주와 유행을 따라 산 종목이 섞여 있어, 둘이 점수와 수익에서 어떻게 갈리는지 보인다. 포트폴리오, 아침 브리핑, 기업 점수, 알림까지 그대로 써 볼 수 있다. 기업 점수와 트렌드는 로그인 없이도 볼 수 있고, 내 종목을 관리하려면 이메일로 가입하면 된다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['주식앱','가치투자','포트폴리오','재테크','밸류노트']::text[],'주식앱',array['/social/26/01.jpg','/social/26/02.jpg','/social/26/03.jpg','/social/26/04.jpg','/social/26/05.jpg','/social/26/06.jpg'],false,true),
('27',27,'공개 검증 예약','2026-10-24T21:00:00+09:00','과거 데이터에 맞춘 공식은 언제나 그럴듯해 보인다. 그래서 ValueNote는 2026년 10월 12일 기준 221개 기업의 점수를 그대로 얼려 두었다. 75점 이상이 19개, 60~74점이 23개였다. 2027년 4월 12일에 6개월 성적을, 10월 12일에 1년 성적을 시장 지수와 비교해 점수대별로 공개한다. 결과가 나쁘면 공식을 고치고 그 과정도 이 계정에 올린다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['가치투자','백테스트','주식공부','투자기록','밸류노트']::text[],'가치투자',array['/social/27/01.jpg','/social/27/02.jpg','/social/27/03.jpg','/social/27/04.jpg','/social/27/05.jpg','/social/27/06.jpg','/social/27/07.jpg','/social/27/08.jpg'],true,true),
('28',28,'금융주 읽는 법','2026-10-25T08:00:00+09:00','은행과 보험은 예금과 보험료가 곧 원재료라서 부채비율이나 현금흐름으로 보면 숫자가 왜곡된다. 대신 ROE와 PBR을 함께 본다. ROE는 자본으로 얼마나 버는지, PBR은 자본 대비 주가가 몇 배인지다. ROE가 꾸준히 높은데 PBR이 1배 아래라면 버는 힘에 비해 싸게 거래되는 것일 수 있다. 버크셔 해서웨이의 뿌리도 보험이다. ValueNote는 은행과 보험에 이 전용 잣대를 따로 적용한다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['은행주','보험주','PBR','가치투자','주식공부']::text[],'주식공부',array['/social/28/01.jpg','/social/28/02.jpg','/social/28/03.jpg','/social/28/04.jpg','/social/28/05.jpg','/social/28/06.jpg'],false,true),
('29',29,'투자 결정 일지','2026-10-25T12:30:00+09:00','3개월만 지나도 왜 샀는지 기억하지 못한다. 그래서 오르면 운을 실력으로, 내리면 실력을 운으로 착각한다. 결정 일지에는 왜 샀는지, 무엇을 보면 팔지, 그때 시스템 판정이 무엇이었는지 세 가지만 적으면 된다. ValueNote는 일지를 쓸 때 그 시점의 점수와 판정을 함께 얼려 두고, 기준대로 산 비율과 기준을 어기고 산 결과를 나란히 보여 준다. 직접 쓰는 칸은 메모 하나뿐이다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['투자일지','투자습관','가치투자','재테크','밸류노트']::text[],'투자습관',array['/social/29/01.jpg','/social/29/02.jpg','/social/29/03.jpg','/social/29/04.jpg','/social/29/05.jpg','/social/29/06.jpg'],false,true),
('30',30,'ValueNote 한눈에','2026-10-25T21:00:00+09:00','ValueNote는 한국 150개, 미국 200개, 일본 100개, 중국 A주 100개, 홍콩 50개 등 5개 시장 620개 기업을 매주 월요일 같은 공식으로 다시 채점한다. 70점 이상이면서 감점이 없는 관심 후보를 시장당 최대 6개씩 자동으로 고르고, 투자 성향에 따라 배당 적합과 상승 여력 아이콘을 붙인다. 목록에 없는 종목은 3회까지 직접 분석할 수 있고 친구를 초대하면 1회씩 늘어난다. 좋은 회사를 적정 가격에 사서 오래 들고 가려는 사람을 위한 노트다. 이 글은 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아니다.',array['가치투자','주식앱','워렌버핏','장기투자','밸류노트']::text[],'가치투자',array['/social/30/01.jpg','/social/30/02.jpg','/social/30/03.jpg','/social/30/04.jpg','/social/30/05.jpg','/social/30/06.jpg','/social/30/07.jpg','/social/30/08.jpg'],true,true)
on conflict (id) do update set title=excluded.title, scheduled_at=excluded.scheduled_at, caption=excluded.caption, hashtags=excluded.hashtags,
  threads_tag=excluded.threads_tag, images=excluded.images, to_ig=excluded.to_ig, to_threads=excluded.to_threads
  where social_posts.ig_status <> 'posted' and social_posts.th_status <> 'posted';
select count(*) as 등록된_카드뉴스 from public.social_posts;
