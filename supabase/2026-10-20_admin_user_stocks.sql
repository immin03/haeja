-- 관리자: 회원이 등록한 종목 보기 (2026-10-20)
-- 보유 종목(holdings)과 직접 분석한 종목(companies)을 회원별로 모아 돌려준다.
-- 운영 계정(publisher)·체험 계정(demo)은 제외. 관리자만 호출 가능.
-- 2026-10-20 보강: 현재가(px)를 회원 입력값 → 스크리너 시세 순으로 붙여 평가금액을 볼 수 있게 함

create or replace function public.admin_user_stocks() returns jsonb
language plpgsql stable security definer set search_path = public, auth as
$$
declare
  excl uuid[];
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  excl := array_remove(array[public.publisher_id(), public.demo_id()], null);

  return (
    with h as (
      select d.owner, d.id, 'hold'::text kind, d.data ->> 'name' name, nullif(d.data ->> 'ticker', '') ticker,
             d.data ->> 'market' market, d.data ->> 'currency' cur,
             case when jsonb_typeof(d.data -> 'qty') = 'number' then (d.data ->> 'qty')::numeric end qty,
             case when jsonb_typeof(d.data -> 'avg') = 'number' then (d.data ->> 'avg')::numeric end avg,
             case when jsonb_typeof(d.data -> 'price') = 'number' then (d.data ->> 'price')::numeric end px,
             d.data ->> 'companyId' cid, d.updated_at
        from docs d
       where d.collection = 'holdings' and not (d.owner = any(excl))
    ), c as (
      select d.owner, d.id, 'analysis'::text kind, d.data ->> 'name' name, coalesce(nullif(d.data ->> 'ticker', ''), nullif(d.data ->> 'yf', '')) ticker,
             d.data ->> 'market' market, null::text cur, null::numeric qty, null::numeric avg,
             case when jsonb_typeof(d.data -> 'price') = 'number' then (d.data ->> 'price')::numeric end px,
             d.id cid, d.updated_at
        from docs d
       where d.collection = 'companies' and not (d.owner = any(excl))
         and coalesce((d.data ->> 'example')::boolean, false) = false
    ), sr as (
      select r ->> 't' t, r ->> 'code' code, lower(regexp_replace(r ->> 'n', '\s', '', 'g')) nk, lower(regexp_replace(coalesce(r ->> 'en', ''), '\s', '', 'g')) ek,
             case when jsonb_typeof(r -> 'px') = 'number' then (r ->> 'px')::numeric end px
        from docs d, jsonb_array_elements(d.data -> 'rows') r
       where d.collection = 'screen' and d.id like 'chunk-%'
    ), a0 as (select * from h union all select * from c),
    a as (
      select a0.owner, a0.id, a0.kind, a0.name, a0.ticker, a0.market, a0.cur, a0.qty, a0.avg, a0.cid, a0.updated_at,
             coalesce(a0.px, (select sr.px from sr
                               where (a0.ticker is not null and (upper(sr.t) = upper(a0.ticker) or upper(sr.code) = upper(a0.ticker)))
                                  or (a0.ticker is null and lower(regexp_replace(coalesce(a0.name, ''), '\s', '', 'g')) in (sr.nk, sr.ek))
                               limit 1)) px
        from a0
    )
    select coalesce(jsonb_agg(jsonb_build_object(
             'owner', a.owner, 'email', u.email, 'id', a.id, 'kind', a.kind,
             'name', a.name, 'ticker', a.ticker, 'market', a.market, 'cur', a.cur,
             'qty', a.qty, 'avg', a.avg, 'px', a.px, 'cid', a.cid,
             'analyzed', a.kind = 'analysis' or exists (select 1 from c where c.owner = a.owner and c.id = a.cid),
             'at', a.updated_at)
           order by a.updated_at desc), '[]')
      from a left join auth.users u on u.id = a.owner
  );
end $$;
revoke all on function public.admin_user_stocks() from public, anon;
grant execute on function public.admin_user_stocks() to authenticated;
