// 목록에 없는 종목 검색·즉시 분석
// - {action:"search", q}      : 종목 검색 (한글은 네이버 자동완성, 영문·티커는 Yahoo 검색)
// - {action:"quota"}          : 남은 무료 분석 횟수
// - {action:"run", symbol, name?} : Yahoo 연간 재무로 품질·저평가 입력값(fin, val)을 계산해 companies 문서로 저장
// 계산식은 스크리너(screener.py compute_metrics / fetch_one)와 같다. 정성 평가는 다음 날 아침 자동 분석이 채운다.
// 무료 한도: 사용자당 서로 다른 종목 3개 (같은 종목 다시 분석은 무료). usage/analyze 문서의 limit으로 조정.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...cors, "Content-Type": "application/json" } });
const UA = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36" };
const FREE = 3;
const kst = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
const rnd = (x: number | null | undefined, d = 2) => (x === null || x === undefined || !isFinite(x)) ? null : Math.round(x * 10 ** d) / 10 ** d;

/* ---------- 심볼 ---------- */
function marketOf(sym: string) {
  if (/\.KS$/.test(sym)) return "KR"; if (/\.KQ$/.test(sym)) return "KOSDAQ"; if (/\.T$/.test(sym)) return "JP";
  if (/\.HK$/.test(sym)) return "HK"; if (/\.(SS|SZ)$/.test(sym)) return "CN";
  if (/^[A-Z][A-Z0-9]{0,5}(-[A-Z])?$/.test(sym)) return "US";
  return null;
}
const tickerOf = (sym: string) => sym.replace(/\.(KS|KQ|T|HK|SS|SZ)$/, "");
function fromNaver(it: any): { symbol: string; name: string; exch: string } | null {
  const code = String(it.code || ""), rc = String(it.reutersCode || ""), tc = String(it.typeCode || "");
  if (it.nationCode === "KOR" && /^\d{6}$/.test(code)) return { symbol: code + (tc === "KOSDAQ" ? ".KQ" : ".KS"), name: it.name, exch: it.typeName || tc };
  if (it.nationCode === "USA") return { symbol: code.toUpperCase(), name: it.name, exch: it.typeName || tc };
  if (it.nationCode === "JPN" && /^\d{4}/.test(code)) return { symbol: code.slice(0, 4) + ".T", name: it.name, exch: "도쿄" };
  if (it.nationCode === "HKG") { const c = code.replace(/\D/g, ""); if (c) return { symbol: c.padStart(4, "0").slice(-4) + ".HK", name: it.name, exch: "홍콩" }; }
  if (it.nationCode === "CHN" && /^\d{6}/.test(code)) return { symbol: code.slice(0, 6) + (code.startsWith("6") ? ".SS" : ".SZ"), name: it.name, exch: code.startsWith("6") ? "상하이" : "선전" };
  if (/\.(T|HK|SS|SZ)$/.test(rc)) return { symbol: rc, name: it.name, exch: it.typeName || "" };
  return null;
}
async function search(q: string) {
  const out: { symbol: string; name: string; exch: string; market: string }[] = [];
  const push = (x: { symbol: string; name: string; exch: string } | null) => { if (!x) return; const m = marketOf(x.symbol); if (m && !out.some((o) => o.symbol === x.symbol)) out.push({ ...x, market: m }); };
  const tasks: Promise<void>[] = [];
  tasks.push((async () => { try {
    const r = await fetch(`https://ac.stock.naver.com/ac?q=${encodeURIComponent(q)}&target=stock`, { headers: UA });
    const j = await r.json(); for (const it of j.items || []) if (it.category === "stock") push(fromNaver(it));
  } catch (_) { /* 네이버 실패는 무시 */ } })());
  if (/^[\x20-\x7E]+$/.test(q)) tasks.push((async () => { try {
    const r = await fetch(`https://query2.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(q)}&quotesCount=8&newsCount=0`, { headers: UA });
    const j = await r.json(); for (const it of j.quotes || []) if (it.quoteType === "EQUITY") push({ symbol: it.symbol, name: it.longname || it.shortname || it.symbol, exch: it.exchDisp || it.exchange || "" });
  } catch (_) { /* */ } })());
  await Promise.all(tasks);
  if (/^\d{6}$/.test(q) && !out.length) push({ symbol: q + ".KS", name: q, exch: "코스피" });
  return out.slice(0, 10);
}

/* ---------- Yahoo 데이터 ---------- */
async function chartMeta(sym: string) {
  const r = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=5d&interval=1d`, { headers: UA });
  if (!r.ok) return null; const m = (await r.json())?.chart?.result?.[0]?.meta; return m || null;
}
async function fx(src: string, dst: string) {
  if (!src || !dst || src === dst) return 1;
  try { const m = await chartMeta(`${src}${dst}=X`); return m?.regularMarketPrice || 1; } catch (_) { return 1; }
}
const TYPES = ["TotalRevenue", "OperatingRevenue", "GrossProfit", "EBIT", "OperatingIncome", "InterestExpense", "InterestExpenseNonOperating", "NetIncomeCommonStockholders", "NetIncome",
  "DilutedEPS", "BasicEPS", "TaxRateForCalcs", "StockholdersEquity", "CommonStockEquity", "LongTermDebt", "LongTermDebtAndCapitalLeaseObligation", "TotalDebt", "CurrentAssets",
  "CurrentLiabilities", "TotalLiabilitiesNetMinorityInterest", "TotalAssets", "CashAndCashEquivalents", "CashCashEquivalentsAndShortTermInvestments", "CurrentDebt", "NetPPE",
  "InvestedCapital", "OrdinarySharesNumber", "DilutedAverageShares", "ShareIssued", "OperatingCashFlow", "CapitalExpenditure", "FreeCashFlow", "StockBasedCompensation"];
async function statements(sym: string) {
  const types = [...TYPES.map((t) => "annual" + t), "trailingNetIncome", "trailingNetIncomeCommonStockholders"].join(",");
  const r = await fetch(`https://query2.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/${encodeURIComponent(sym)}?type=${types}&period1=1300000000&period2=${Math.floor(Date.now() / 1000) + 86400}`, { headers: UA });
  if (!r.ok) return null;
  const j = await r.json();
  const by: Record<string, Record<string, number>> = {}; let fcur = ""; const ttm: Record<string, number> = {};
  for (const res of j?.timeseries?.result || []) {
    const k = res.meta?.type?.[0]; const arr = res[k]; if (!k || !arr) continue;
    for (const x of arr) { if (!x || !x.reportedValue) continue; const v = x.reportedValue.raw; if (typeof v !== "number") continue;
      if (k.startsWith("trailing")) { ttm[k.replace("trailing", "")] = v; continue; }
      (by[k.replace("annual", "")] ||= {})[x.asOfDate] = v; if (x.currencyCode && !fcur && k !== "annualOrdinarySharesNumber" && k !== "annualShareIssued") fcur = x.currencyCode; }
  }
  return { by, fcur, ttm };
}

/* ---------- 지표 계산 (screener.py와 같은 식) ---------- */
function compute(st: { by: Record<string, Record<string, number>>; ttm: Record<string, number> }, finSector: boolean) {
  const by = st.by;
  const dates = [...new Set([...Object.keys(by.TotalRevenue || {}), ...Object.keys(by.NetIncome || {}), ...Object.keys(by.NetIncomeCommonStockholders || {})])].sort();
  const series = (...names: string[]) => dates.map((d) => { for (const n of names) { const v = by[n]?.[d]; if (v !== undefined) return v; } return null; });
  const dated = (...names: string[]) => { const o: Record<string, number> = {}; for (const n of names) for (const [d, v] of Object.entries(by[n] || {})) if (!(d in o)) o[d] = v; return o; };
  const nz = (xs: (number | null)[]) => xs.filter((x): x is number => x !== null);
  const last = (xs: (number | null)[]) => { for (let i = xs.length - 1; i >= 0; i--) if (xs[i] !== null) return xs[i]; return null; };
  const cagr = (a: number | null, b: number | null, y: number) => (a === null || b === null || a <= 0 || b <= 0 || y <= 0) ? null : (Math.pow(b / a, 1 / y) - 1) * 100;

  const ni = series("NetIncomeCommonStockholders", "NetIncome"), rev = series("TotalRevenue", "OperatingRevenue"), gp = series("GrossProfit");
  const ebit = series("EBIT", "OperatingIncome"), intexp = series("InterestExpense", "InterestExpenseNonOperating"), epsS = series("DilutedEPS", "BasicEPS");
  const taxr = series("TaxRateForCalcs"), eq = series("StockholdersEquity", "CommonStockEquity"), ltd = series("LongTermDebt", "LongTermDebtAndCapitalLeaseObligation");
  const tdebt = series("TotalDebt"), ca = series("CurrentAssets"), cl = series("CurrentLiabilities"), tl = series("TotalLiabilitiesNetMinorityInterest");
  const cash = series("CashAndCashEquivalents", "CashCashEquivalentsAndShortTermInvestments"), cdebt = series("CurrentDebt"), ppe = series("NetPPE");
  const invcap = series("InvestedCapital"), shares = series("OrdinarySharesNumber", "ShareIssued"), cfo = series("OperatingCashFlow"), capex = series("CapitalExpenditure");
  const fcf = series("FreeCashFlow"), sbc = series("StockBasedCompensation"), dsh = series("DilutedAverageShares");

  const f: Record<string, number | null> = {};
  const niBy = dated("NetIncomeCommonStockholders", "NetIncome"), eqBy = dated("StockholdersEquity", "CommonStockEquity"); const eqD = Object.keys(eqBy).sort();
  const roes: number[] = [];
  for (const [d, v] of Object.entries(niBy).sort()) { const now = eqBy[d]; if (now === undefined) continue; const prev = eqD.filter((x) => x < d).at(-1); const base = prev ? (now + eqBy[prev]) / 2 : now; if (base > 0) roes.push(v / base * 100); }
  if (roes.length) { f.roeAvg = rnd(roes.reduce((a, b) => a + b, 0) / roes.length); f.roeMin = rnd(Math.min(...roes)); }
  const eLast = last(ebit), icLast = last(invcap); let t = last(taxr); t = t !== null && t >= 0 && t <= 0.5 ? t : 0.22;
  if (eLast !== null && icLast && icLast > 0) f.roic = rnd(eLast * (1 - t) / icLast * 100);
  if (!finSector && last(gp) !== null && last(rev)) f.gpm = rnd((last(gp) as number) / (last(rev) as number) * 100);
  if (last(ni) !== null && last(rev)) f.npm = rnd((last(ni) as number) / (last(rev) as number) * 100);
  const epsN = nz(epsS); if (epsN.length >= 3) f.epsCagr = rnd(cagr(epsN[0], epsN.at(-1)!, epsN.length - 1));
  const revN = nz(rev); const revCagr = revN.length >= 3 ? cagr(revN[0], revN.at(-1)!, revN.length - 1) : null;
  const niN = nz(ni); if (niN.length) f.lossYears = niN.filter((x) => x < 0).length;
  let fcfN = nz(fcf); if (!fcfN.length) fcfN = cfo.map((a, i) => a !== null && capex[i] !== null ? a + (capex[i] as number) : null).filter((x): x is number => x !== null);
  const sumNi = fcfN.length && niN.length ? niN.slice(-fcfN.length).reduce((a, b) => a + b, 0) : null;
  if (!finSector && fcfN.length && sumNi && sumNi > 0) {
    f.fcfConv = rnd(fcfN.reduce((a, b) => a + b, 0) / sumNi * 100);
    const capN = nz(capex); if (capN.length) f.capexNi = rnd(Math.abs(capN.slice(-fcfN.length).reduce((a, b) => a + b, 0)) / sumNi * 100);
  }
  const niLast = last(ni);
  if (!finSector) {
    let l = last(ltd); if (l === null && tdebt.some((x) => x !== null)) l = last(tdebt);
    if (l !== null && niLast !== null) f.ltdNi = niLast > 0 ? rnd(l / niLast) : (l <= 0 ? 0 : 99);
    else if (l === null) f.ltdNi = 0;
    const ie = last(intexp);
    if (eLast !== null) f.icr = eLast <= 0 ? (ie ? rnd(eLast / Math.abs(ie)) : null) : (!ie ? 99 : rnd(Math.min(eLast / Math.abs(ie), 99)));
    if (last(ca) && last(cl)) f.currentRatio = rnd((last(ca) as number) / (last(cl) as number));
  }
  const shN = nz(shares); if (shN.length >= 2 && shN[0] > 0) f.shareChg = rnd((shN.at(-1)! / shN[0] - 1) * 100);
  const f3 = fcfN.slice(-3), s3 = nz(sbc).slice(-3);
  const revYoY = revN.length >= 2 ? revN.slice(1).map((v, i) => rnd((v / revN[i] - 1) * 100, 1)).slice(-3) : null;
  const epsYears = dates.map((d, i) => epsS[i] ?? (ni[i] !== null && dsh[i] ? (ni[i] as number) / (dsh[i] as number) : null)).filter((x): x is number => x !== null);
  for (const k of Object.keys(f)) if (f[k] === null || f[k] === undefined) delete f[k];
  return {
    f, years: niN.length, fy: dates.at(-1) || null,
    raw: { ni: niLast, niTTM: st.ttm.NetIncomeCommonStockholders ?? st.ttm.NetIncome ?? null, eq: last(eq), ebit: eLast, tdebt: last(tdebt) ?? last(ltd) ?? 0, cash: last(cash) ?? 0, ca: last(ca), cl: last(cl), tl: last(tl),
      cdebt: last(cdebt) ?? 0, rev: last(rev), ppe: last(ppe), fcf3: f3.length ? f3.reduce((a, b) => a + b, 0) / f3.length : null,
      sbc3: s3.length ? s3.reduce((a, b) => a + b, 0) / s3.length : null, shares: last(shares), revCagr, revYoY, epsYears },
  };
}

async function runOne(symbol: string, nameHint: string | undefined) {
  const meta = await chartMeta(symbol);
  if (!meta || !meta.regularMarketPrice) return { error: "가격을 찾지 못했습니다. 티커를 확인하세요." };
  if (meta.instrumentType && meta.instrumentType !== "EQUITY") return { error: "ETF·펀드는 회사가 아니라서 분석 대상이 아닙니다.", etf: true };
  const st = await statements(symbol);
  if (!st || !Object.keys(st.by).length) return { error: "재무제표를 찾지 못했습니다. 상장한 지 얼마 안 됐거나 자료가 없는 종목입니다." };
  // 업종: Yahoo 검색 결과의 sector/industry
  let sector = "", industry = "";
  try { const j = await (await fetch(`https://query2.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(symbol)}&quotesCount=3&newsCount=0`, { headers: UA })).json();
    const q = (j.quotes || []).find((x: any) => x.symbol === symbol) || {}; sector = q.sectorDisp || q.sector || ""; industry = q.industryDisp || q.industry || ""; } catch (_) { /* */ }
  const finSector = sector.toLowerCase().includes("financ") || /^(banks|insurance)/i.test(industry);
  const c = compute(st, finSector);
  const px = meta.regularMarketPrice as number, cur = meta.currency || "USD";
  const k = await fx(st.fcur || cur, cur);
  const raw = c.raw; const shares = raw.shares;
  const val: Record<string, unknown> = {};
  let mcap: number | null = null;
  if (shares && shares > 0) {
    mcap = px * shares;
    const niE = raw.niTTM ?? raw.ni;
    if (niE !== null) val.eps = rnd(niE * k / shares, 4);
    if (raw.eq) val.bps = rnd(raw.eq * k / shares, 4);
    if (raw.fcf3 !== null) val.oeps = rnd(raw.fcf3 * k / shares, 4);
    if (raw.ca !== null && raw.tl !== null) val.ncavps = rnd((raw.ca - raw.tl) * k / shares, 4);
    if (raw.rev) val.sps = rnd(raw.rev * k / shares, 4);
    if (raw.sbc3 !== null && raw.fcf3 && raw.fcf3 > 0 && (val.oeps as number) > 0) val.sbcps = rnd((val.oeps as number) * (raw.sbc3 / raw.fcf3), 4);
  }
  if (raw.revCagr !== null) val.revCagr = rnd(raw.revCagr, 1);
  const gs = [c.f.epsCagr, raw.revCagr].filter((g): g is number => g !== null && g !== undefined);
  val.growth = rnd(gs.length ? Math.max(0, Math.min(Math.min(...gs) * 0.5, 8)) : 2, 1);
  if (raw.epsYears.length >= 3) val.epsAvg = rnd(raw.epsYears.reduce((a, b) => a + b, 0) / raw.epsYears.length * k, 4);
  if (raw.revYoY && raw.revYoY.length) val.revYoY = raw.revYoY;
  if (raw.ebit && raw.ebit > 0 && mcap && !finSector) {
    const ev = mcap + (raw.tdebt - raw.cash) * k; if (ev > 0) val.mfEY = rnd(raw.ebit * k / ev * 100);
    if (raw.ca !== null && raw.cl !== null && raw.ppe !== null) { const nwc = Math.max((raw.ca - raw.cash) - (raw.cl - raw.cdebt), 0); const cap = nwc + raw.ppe; if (cap > 0) val.mfROC = rnd(raw.ebit / cap * 100); }
  }
  const nFin = Object.keys(c.f).length;
  const dataConf = c.years < 3 || nFin < 6 || val.oeps === undefined ? "low" : "medium";
  const dataConfWhy = dataConf === "low" ? `Yahoo Finance 연간 재무 ${c.years}개년·지표 ${nFin}개만 확보돼 판단 근거가 부족하다.` : `Yahoo Finance 연간 재무 ${c.years}개년으로 자동 계산했다. 매수 전 공시 원문 대조가 필요하다.`;
  const market = marketOf(symbol)!;
  return { doc: {
    name: nameHint || meta.longName || meta.shortName || symbol, ticker: tickerOf(symbol), yf: symbol, market, kind: "stock", price: px, sector: industry || sector,
    fin: c.f, val, finSector, holdco: false, dataConf, dataConfWhy, fy: c.fy, yrs: c.years, mcap, cur, fcur: st.fcur || cur,
    qual: {}, thesis: { memo: "" }, pinned: true, searched: { at: kst(), by: "검색 분석" },
    source: `Yahoo Finance 연간 재무 ${c.years}개년 자동 계산 ${kst()} (정성 평가는 다음 아침 자동 분석)`, createdAt: kst(), updatedAt: new Date().toISOString(),
  } };
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const body = await req.json().catch(() => ({}));
  try {
    const token = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
    const { data: ud } = await sb.auth.getUser(token);
    const uid = ud?.user?.id;
    if (!uid) return json({ error: "로그인이 필요합니다." }, 401);
    const { data: urow } = await sb.from("docs").select("data").eq("collection", "usage").eq("id", "analyze").eq("owner", uid).maybeSingle();
    const usage = { used: [] as { sym: string; at: string }[], limit: FREE, ...(urow?.data || {}) };
    const quota = () => ({ used: usage.used.length, limit: usage.limit, left: Math.max(0, usage.limit - usage.used.length) });

    if (body.action === "quota") return json(quota());
    if (body.action === "search") { const q = String(body.q || "").trim(); if (q.length < 1) return json({ items: [] }); return json({ items: await search(q), ...quota() }); }
    if (body.action === "run") {
      const symbol = String(body.symbol || "").trim().toUpperCase();
      if (!marketOf(symbol)) return json({ error: "지원하지 않는 시장입니다 (한국·미국·일본·중국·홍콩만)." }, 400);
      const again = usage.used.some((u: any) => u.sym === symbol);
      if (!again && usage.used.length >= usage.limit) return json({ error: "무료 분석 3회를 모두 썼습니다.", quota: true, ...quota() }, 402);
      const r = await runOne(symbol, body.name ? String(body.name).slice(0, 60) : undefined);
      if ("error" in r) return json({ ...r, ...quota() }, 422);
      const id = "a-" + symbol.replace(/[^A-Z0-9]/g, "");
      const { data: old } = await sb.from("docs").select("data").eq("collection", "companies").eq("id", id).eq("owner", uid).maybeSingle();
      const prev = old?.data || {};
      const doc = { ...prev, ...r.doc, qual: prev.qual && Object.keys(prev.qual).length ? prev.qual : {}, thesis: prev.thesis || r.doc.thesis, createdAt: prev.createdAt || r.doc.createdAt };
      for (const k of ["auto", "berkshire", "profile", "hist", "trendLinks", "industry", "risksText"]) if (prev[k]) (doc as any)[k] = prev[k];
      const { error } = await sb.from("docs").upsert({ collection: "companies", id, owner: uid, data: doc, updated_at: new Date().toISOString() });
      if (error) throw error;
      if (!again) { usage.used.push({ sym: symbol, at: kst() }); await sb.from("docs").upsert({ collection: "usage", id: "analyze", owner: uid, data: usage, updated_at: new Date().toISOString() }); }
      return json({ ok: true, id, again, ...quota() });
    }
    return json({ error: "알 수 없는 요청" }, 400);
  } catch (e) {
    return json({ error: String((e as Error)?.message || e) }, 500);
  }
});
