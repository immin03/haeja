// 기업 목록(스크리너) 대량 수집 — 5개 시장 시가총액 상위 약 600개
// - {action:"start"}  : 네이버 증권 시가총액 순위로 대상 목록을 만들고 작업을 시작한다 (기존 목록 종목도 포함)
// - {action:"step"}   : 다음 묶음(최대 ~40종목, 100초)을 Yahoo 연간 재무로 계산해 임시 저장. 끝나면 목록(screen/chunk-*)을 새로 쓴다
// - {action:"status"} : 진행 상황
// 계산식은 analyze(목록에 없는 종목 분석)·screener.py와 같다. pg_cron이 매주 토요일 새벽에 start, 그 뒤 1분마다 step을 부른다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const UA = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36" };
const kst = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
const rnd = (x: number | null | undefined, d = 2) => (x === null || x === undefined || !isFinite(x)) ? null : Math.round(x * 10 ** d) / 10 ** d;
const TARGET = { KOSPI: 100, KOSDAQ: 50, US: 200, JP: 100, CN: 100, HK: 50 };
const BUDGET_MS = 100_000, CONC = 6, CHUNK = 120;

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
  // 주식 수는 한 가지 기준으로만 비교한다 (발행주식·유통주식이 해마다 섞이면 희석률이 틀어진다)
  const nOrd = Object.keys(by.OrdinarySharesNumber || {}).length, nIss = Object.keys(by.ShareIssued || {}).length;
  const shares = nOrd >= 2 || nOrd >= nIss ? series("OrdinarySharesNumber") : series("ShareIssued");
  const invcap = series("InvestedCapital"), cfo = series("OperatingCashFlow"), capex = series("CapitalExpenditure");
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


/* ---------- 대상 목록: 네이버 증권 시가총액 순위 (한글 이름 포함) ---------- */
type U = { t: string; code: string; n: string; en?: string; m: string; ind?: string; mv: number };
const num = (v: unknown) => { const x = parseFloat(String(v ?? "").replace(/,/g, "")); return isFinite(x) ? x : 0; };
async function naverKR(cat: "KOSPI" | "KOSDAQ", want: number): Promise<U[]> {
  const out: U[] = [];
  for (let page = 1; out.length < want && page <= 6; page++) {
    const j = await (await fetch(`https://m.stock.naver.com/api/stocks/marketValue/${cat}?page=${page}&pageSize=100`, { headers: UA })).json();
    for (const s of j.stocks || []) {
      if (s.stockEndType !== "stock") continue;
      const code = String(s.itemCode || ""), nm = String(s.stockName || "");
      if (!/^\d{6}$/.test(code)) continue;                       // 우선주 신형 코드(0043B0 등) 제외
      if (/(우|우B|우C|\(전환\))$/.test(nm) || /스팩|리츠|REIT/i.test(nm)) continue; // 우선주·스팩·리츠 제외
      out.push({ t: code + (cat === "KOSDAQ" ? ".KQ" : ".KS"), code, n: nm, m: "KR", mv: num(s.marketValueRaw ?? s.marketValue) });
      if (out.length >= want) break;
    }
    if (!(j.stocks || []).length) break;
  }
  return out;
}
async function naverWorld(ex: string, pages: number): Promise<any[]> {
  const all: any[] = [];
  for (let page = 1; page <= pages; page++) {
    const j = await (await fetch(`https://api.stock.naver.com/stock/exchange/${ex}/marketValue?page=${page}&pageSize=100`, { headers: UA })).json();
    const st = j.stocks || []; all.push(...st.filter((s: any) => s.stockEndType === "stock")); if (st.length < 100) break;
  }
  return all;
}
const baseName = (s: string) => String(s || "").toLowerCase().replace(/\b(class [a-z]|adr|ads|ord(inary)?|shares?|co\.?|ltd\.?|limited|inc\.?|corp(oration)?\.?|holdings?|group|plc|the|sa|ag|nv|se)\b/g, "").replace(/[^a-z0-9]/g, "");
async function universe(): Promise<U[]> {
  const [kospi, kosdaq, nyse, nasdaq, tyo, shh, shz, hkg] = await Promise.all([
    naverKR("KOSPI", TARGET.KOSPI), naverKR("KOSDAQ", TARGET.KOSDAQ),
    naverWorld("NYSE", 2), naverWorld("NASDAQ", 2), naverWorld("TOKYO", 2), naverWorld("SHANGHAI", 1), naverWorld("SHENZHEN", 1), naverWorld("HONG_KONG", 2)]);
  const w = (s: any, m: string, t: string, code: string): U => ({ t, code, n: String(s.stockName || code).trim(), en: String(s.stockNameEng || "").replace(/\s{2,}/g, " ").trim(), m, ind: s.industryCodeType?.industryGroupKor || "", mv: num(s.marketValueRaw ?? s.marketValue) });
  const top = (xs: U[], n: number) => xs.sort((a, b) => b.mv - a.mv).slice(0, n);
  const jp = top(tyo.filter((s) => /^\d{3}[0-9A-Z]\.T$/.test(s.reutersCode)).map((s) => w(s, "JP", s.reutersCode, s.reutersCode.replace(".T", ""))), TARGET.JP);
  const cn = top([...shh, ...shz].filter((s) => /^\d{6}\.(SS|SZ)$/.test(s.reutersCode)).map((s) => w(s, "CN", s.reutersCode, s.reutersCode.slice(0, 6))), TARGET.CN);
  // 미국: 우선주·워런트 제외, 같은 회사의 여러 주식(GOOG/GOOGL)은 하나만
  const usAll = [...nyse, ...nasdaq].filter((s) => /^[A-Z]{1,5}(\.[A-Z])?$/.test(String(s.symbolCode || ""))).map((s) => w(s, "US", String(s.symbolCode).replace(".", "-"), String(s.symbolCode).replace(".", "-")));
  // 다른 시장에 본주가 있는 ADR은 본주로 본다 (토요타 TM → 7203.T)
  const homeNames = new Set([...jp, ...cn].map((x) => baseName(x.en || "")).filter(Boolean));
  const seen = new Set<string>(); const us: U[] = [];
  for (const x of top(usAll, 400)) { const b = baseName(x.en || x.n); if (!b || seen.has(b) || (/ADR/i.test(x.n + " " + x.en) && homeNames.has(b))) continue; seen.add(b); us.push(x); if (us.length >= TARGET.US) break; }
  // 홍콩: 해외 기업 예탁증서(마이크로소프트 4338 등)와 본토 A주와 같은 회사의 H주는 제외
  const usNames = new Set(us.map((x) => baseName(x.en || "")));
  const cnNames = new Set(cn.map((x) => baseName(x.en || "")));
  const hk = top(hkg.filter((s) => /^\d{4}\.HK$/.test(s.reutersCode)).map((s) => w(s, "HK", s.reutersCode, s.reutersCode.replace(".HK", "")))
    .filter((x) => { const b = baseName(x.en || ""); return !usNames.has(b) && !cnNames.has(b); }), TARGET.HK);
  return [...kospi, ...kosdaq, ...us, ...jp, ...cn, ...hk];
}

/* ---------- 한 종목 계산 → 목록 행 ---------- */
const fxCache: Record<string, number> = {};
async function fxC(src: string, dst: string) { const k = src + dst; if (!(k in fxCache)) fxCache[k] = await fx(src, dst); return fxCache[k]; }
const marketOf = (t: string) => /\.(KS|KQ)$/.test(t) ? "KR" : /\.T$/.test(t) ? "JP" : /\.HK$/.test(t) ? "HK" : /\.(SS|SZ)$/.test(t) ? "CN" : "US";
async function rowFor(u: U): Promise<any | null> {
  let meta = await chartMeta(u.t);
  if ((!meta || !meta.regularMarketPrice) && /\.KS$/.test(u.t)) { u = { ...u, t: u.t.replace(".KS", ".KQ") }; meta = await chartMeta(u.t); }
  if (!meta || !meta.regularMarketPrice) return null;
  if (meta.instrumentType && meta.instrumentType !== "EQUITY") return null;
  const st = await statements(u.t);
  if (!st || !Object.keys(st.by).length) return null;
  let sector = "", industry = "";
  try { const j = await (await fetch(`https://query2.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(u.t)}&quotesCount=3&newsCount=0`, { headers: UA })).json();
    const q = (j.quotes || []).find((x: any) => x.symbol === u.t) || {}; sector = q.sectorDisp || q.sector || ""; industry = q.industryDisp || q.industry || ""; } catch (_) { /* */ }
  const finSector = sector.toLowerCase().includes("financ") || /^(banks|insurance)/i.test(industry) || /^(은행|보험|투자 은행)/.test(u.ind || "");
  const c = compute(st, finSector);
  const px = meta.regularMarketPrice as number, cur = meta.currency || "USD";
  const k = await fxC(st.fcur || cur, cur);
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
  for (const key of Object.keys(val)) if (val[key] === null || val[key] === undefined) delete val[key];
  const nFin = Object.keys(c.f).length;
  const dataConf = c.years < 3 || nFin < 6 || val.oeps === undefined ? "low" : "medium";
  return { t: u.t, code: u.code, n: u.n, en: u.en || meta.longName || meta.shortName || "", m: u.m || marketOf(u.t), s: sector, ind: u.ind || industry, cur, fcur: st.fcur || cur,
    px: rnd(px, 4), mcap: mcap ? Math.round(mcap / 1e6) : null, fin: c.f, val, fin_sector: finSector, fy: c.fy, yrs: c.years, dataConf, tags: [], auto: kst() };
}
async function pool<T>(xs: T[], n: number, f: (x: T) => Promise<void>) { let i = 0; await Promise.all(Array.from({ length: Math.min(n, xs.length) }, async () => { while (i < xs.length) { const x = xs[i++]; await f(x); } })); }

/* ---------- 저장 ---------- */
async function ownerId() { const { data } = await sb.from("docs").select("owner").eq("collection", "screen").eq("id", "meta").maybeSingle(); return data?.owner as string | undefined; }
async function getDoc(col: string, id: string) { const { data } = await sb.from("docs").select("data").eq("collection", col).eq("id", id).maybeSingle(); return data?.data; }
async function putDocs(owner: string, rows: { collection: string; id: string; data: unknown }[]) {
  for (let i = 0; i < rows.length; i += 20) { const { error } = await sb.from("docs").upsert(rows.slice(i, i + 20).map((r) => ({ ...r, owner, updated_at: new Date().toISOString() }))); if (error) throw error; }
}
async function oldRows(): Promise<any[]> {
  const { data } = await sb.from("docs").select("id,data").eq("collection", "screen").like("id", "chunk-%");
  return (data || []).sort((a: any, b: any) => a.id.localeCompare(b.id)).flatMap((d: any) => d.data?.rows || []);
}

async function start(owner: string, force = false) {
  const job = await getDoc("screen_job", "job");
  if (job?.state === "run" && !force && Date.now() - new Date(job.touchedAt || job.startedAt).getTime() < 30 * 60e3) return { ok: false, msg: "이미 진행 중", i: job.i, n: job.list.length };
  const u = await universe();
  const have = new Set(u.map((x) => x.t));
  // 기존 목록에만 있는 종목(예: 웹 조사로 넣은 회사)도 계속 갱신한다
  for (const r of await oldRows()) if (r.t && !have.has(r.t)) { have.add(r.t); u.push({ t: r.t, code: r.code || r.t, n: r.n, en: r.en, m: r.m, ind: r.ind, mv: 0 }); }
  const counts: Record<string, number> = {}; for (const x of u) counts[x.m] = (counts[x.m] || 0) + 1;
  await sb.from("docs").delete().eq("collection", "screen_tmp");
  await putDocs(owner, [{ collection: "screen_job", id: "job", data: { state: "run", list: u, i: 0, part: 0, ok: 0, fail: [], retried: false, startedAt: new Date().toISOString(), touchedAt: new Date().toISOString(), counts } }]);
  return { ok: true, n: u.length, counts };
}

async function step(owner: string) {
  const t0 = Date.now();
  const job = await getDoc("screen_job", "job");
  if (!job || job.state !== "run") return { ok: true, idle: true };
  const list: U[] = job.list; const out: any[] = []; const fail: string[] = [];
  while (job.i < list.length && Date.now() - t0 < BUDGET_MS - 25_000) {
    const batch = list.slice(job.i, job.i + 12); job.i += batch.length;
    await pool(batch, CONC, async (u) => { try { const r = await rowFor(u); if (r) out.push(r); else fail.push(u.t); } catch (_) { fail.push(u.t); } });
  }
  job.ok += out.length; job.fail = [...job.fail, ...fail]; job.touchedAt = new Date().toISOString();
  const writes: { collection: string; id: string; data: unknown }[] = [];
  if (out.length) writes.push({ collection: "screen_tmp", id: "p-" + String(job.part++).padStart(4, "0"), data: { rows: out } });
  // 한 바퀴가 끝나면 실패한 종목을 한 번만 다시 시도한다 (Yahoo 일시 제한 대비)
  if (job.i >= list.length && !job.retried && job.fail.length) {
    const failSet = new Set(job.fail); job.list = [...list, ...list.filter((x) => failSet.has(x.t))]; job.fail = []; job.retried = true;
  }
  if (job.i >= job.list.length) { writes.push({ collection: "screen_job", id: "job", data: { ...job, state: "merge" } }); await putDocs(owner, writes); return await finish(owner); }
  writes.push({ collection: "screen_job", id: "job", data: job });
  await putDocs(owner, writes);
  return { ok: true, i: job.i, n: job.list.length, got: out.length, failed: fail.length, ms: Date.now() - t0 };
}

/* 새 계산값 + 기존 행의 사람이 넣은 정보(한글 이름·국유기업·지배주주 등)를 합쳐 목록을 다시 쓴다 */
async function finish(owner: string) {
  const job = await getDoc("screen_job", "job");
  const { data: parts } = await sb.from("docs").select("data").eq("collection", "screen_tmp");
  const fresh: Record<string, any> = {};
  for (const p of parts || []) for (const r of p.data?.rows || []) fresh[r.t] = r;
  const old = await oldRows(); const oldBy: Record<string, any> = Object.fromEntries(old.map((r) => [r.t, r]));
  const STRAT = new Set(["품질 상위 10%", "마법공식 상위 10%", "F≥8 저PBR", "넷넷", "안전마진 30%+"]);
  const rows: any[] = [];
  const ts = new Set([...Object.keys(fresh), ...Object.keys(oldBy)]);
  for (const t of ts) {
    const f = fresh[t], o = oldBy[t];
    if (f && o) {
      // 웹 조사로 직접 확인한 기존 행(auto 표시 없음)은 재무를 유지하고 가격만 갱신. 자동 행은 새 값으로 교체하되 새 자료가 빈약하면 유지
      const keepOld = !o.auto || (f.dataConf === "low" && o.dataConf && o.dataConf !== "low");
      rows.push({ ...o, ...(keepOld ? { px: f.px } : f), n: o.n || f.n, en: o.en || f.en, s: o.s || f.s, ind: o.ind || f.ind,
        tags: (o.tags || []).filter((x: string) => !STRAT.has(x)), so: o.so, ctrl: o.ctrl, conf: o.conf, holdco: o.holdco,
        dataConf: keepOld ? o.dataConf : (o.dataConf === "high" && f.dataConf === "medium" ? "high" : f.dataConf), fs: o.fs, fsd: o.fsd });
    } else if (f) rows.push(f);
    else if (o) rows.push(o); // 이번에 못 받은 기존 종목은 지난 값 유지
  }
  const order = ["KR", "US", "JP", "CN", "HK"];
  rows.sort((a, b) => order.indexOf(a.m) - order.indexOf(b.m) || (b.mcap || 0) - (a.mcap || 0));
  const counts: Record<string, number> = {}; for (const r of rows) counts[r.m] = (counts[r.m] || 0) + 1;
  const nCh = Math.ceil(rows.length / CHUNK);
  const writes: { collection: string; id: string; data: unknown }[] = [];
  for (let i = 0; i < nCh; i++) writes.push({ collection: "screen", id: "chunk-" + String(i).padStart(2, "0"), data: { part: i, rows: rows.slice(i * CHUNK, (i + 1) * CHUNK), pxAt: kst() } });
  writes.push({ collection: "screen", id: "meta", data: { total: rows.length, chunks: nCh, counts, source: "네이버 증권 시가총액 순위 + Yahoo Finance 연간 재무 자동 계산", generatedAt: kst(), fresh: Object.keys(fresh).length, failed: (job?.fail || []).length } });
  await putDocs(owner, writes);
  // 남는 옛 chunk 삭제
  const { data: ex } = await sb.from("docs").select("id").eq("collection", "screen").like("id", "chunk-%");
  const stale = (ex || []).map((d: any) => d.id).filter((id: string) => +id.slice(6) >= nCh);
  if (stale.length) await sb.from("docs").delete().eq("collection", "screen").in("id", stale);
  await sb.from("docs").delete().eq("collection", "screen_tmp");
  await putDocs(owner, [{ collection: "screen_job", id: "job", data: { state: "done", doneAt: new Date().toISOString(), total: rows.length, fresh: Object.keys(fresh).length, fail: job?.fail || [], counts } }]);
  return { ok: true, done: true, total: rows.length, fresh: Object.keys(fresh).length, counts };
}

Deno.serve(async (req: Request) => {
  const body = await req.json().catch(() => ({}));
  try {
    const owner = await ownerId(); if (!owner) return Response.json({ ok: false, msg: "screen/meta 없음" });
    if (body.action === "start") return Response.json(await start(owner, !!body.force));
    if (body.action === "step") return Response.json(await step(owner));
    if (body.action === "finish") return Response.json(await finish(owner));
    if (body.action === "universe") { const u = await universe(); const c: Record<string, number> = {}; for (const x of u) c[x.m] = (c[x.m] || 0) + 1; return Response.json({ n: u.length, c, sample: u.filter((_, i) => i % 97 === 0).map((x) => [x.t, x.n, x.en]) }); }
    if (body.action === "one") return Response.json(await rowFor({ t: body.t, code: body.t, n: body.t, m: marketOf(body.t), mv: 0 }));
    const job = await getDoc("screen_job", "job");
    return Response.json(job ? { state: job.state, i: job.i, n: job.list?.length, ok: job.ok, fail: (job.fail || []).length, startedAt: job.startedAt, doneAt: job.doneAt, counts: job.counts } : { state: "none" });
  } catch (e) {
    return Response.json({ ok: false, error: String((e as Error)?.message || e) }, { status: 500 });
  }
});
