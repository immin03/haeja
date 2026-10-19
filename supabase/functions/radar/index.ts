// 경제 레이더: 위기 신호 지표를 모아 신호등(0 안정 ~ 4 위험)으로 바꾼다. 매일 아침 pg_cron이 호출한다.
// 자료: 미국 연준 경제자료(FRED) 공개 CSV. 결과는 fx/radar 문서에 저장한다.
// 주간 칼럼 작업이 쓰는 해설(events, upcoming, outlook)은 건드리지 않고 그대로 둔다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
type Pt = [string, number];
const r2 = (v: number) => Math.round(v * 100) / 100;

async function fred(id: string, from: string): Promise<Pt[] | null> {
  try {
    const r = await fetch(`https://fred.stlouisfed.org/graph/fredgraph.csv?id=${id}&cosd=${from}`, { headers: { "User-Agent": "Mozilla/5.0 (valuenote)" } });
    if (!r.ok) return null;
    const rows = (await r.text()).trim().split("\n").slice(1);
    const pts = rows.map((l) => l.trim().split(",")).filter(([d, v]) => /^\d{4}-\d\d-\d\d$/.test(d) && /^-?\d+(\.\d+)?$/.test((v || "").trim())).map(([d, v]) => [d, Number(v)] as Pt);
    return pts.length ? pts : null;
  } catch (_) { return null; }
}
/* 지수 일간 종가 (야후) */
async function yahoo(sym: string, range = "2y", interval = "1d"): Promise<Pt[] | null> {
  try {
    const r = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=${range}&interval=${interval}`, { headers: { "User-Agent": "Mozilla/5.0 (valuenote)" } });
    const res = (await r.json())?.chart?.result?.[0];
    const ts: number[] = res?.timestamp || [], cl: (number | null)[] = res?.indicators?.quote?.[0]?.close || [];
    const off = (res?.meta?.gmtoffset ?? 0) * 1000;
    const pts = ts.map((t, i) => [new Date(t * 1000 + off).toISOString().slice(0, 10), cl[i]] as [string, number | null]).filter((p): p is Pt => typeof p[1] === "number" && isFinite(p[1]) && p[1] > 0);
    return pts.length > 30 ? pts : null;
  } catch (_) { return null; }
}
/* multpl.com 월별 표 (Shiller PER, S&P 500 배당수익률): 최신이 앞 */
async function multpl(path: string): Promise<Pt[] | null> {
  try {
    const r = await fetch(`https://www.multpl.com/${path}/table/by-month`, { headers: { "User-Agent": "Mozilla/5.0 (valuenote)" } });
    if (!r.ok) return null;
    const html = await r.text(); const out: Pt[] = [];
    for (const m of html.matchAll(/<tr[^>]*>([\s\S]*?)<\/tr>/g)) {
      const tds = [...m[1].matchAll(/<td[^>]*>([\s\S]*?)<\/td>/g)].map((x) => x[1].replace(/<[^>]+>/g, "").replace(/&[#\w]+;/g, " ").trim());
      if (tds.length < 2) continue;
      const t = Date.parse(tds[0]); const v = Number((tds[1].match(/-?\d+(\.\d+)?/) || [])[0]);
      if (isFinite(t) && isFinite(v)) out.push([new Date(t).toISOString().slice(0, 10), v]);
    }
    return out.length > 24 ? out : null;
  } catch (_) { return null; }
}
/* ============ 시장 국면 ============
 * 그레이엄 『현명한 투자자』 8장의 강세장 공통 특성(높은 주가·높은 PER·채권보다 낮은 배당·신용 투기·부실 상장)을
 * 출발점으로 삼되, 지금 쓰는 지표로 바꿨다.
 * 1) 국면(추세): 52주 고점 대비 낙폭, 200일 이동평균 위/아래와 기울기, 직전 약세장 바닥 이후 경과
 * 2) 과열도(0~100): 밸류에이션·투기·쏠림 신호 평균. 강세장에서 65 이상이면 "후기·과열"
 */
const lin = (v: number, cold: number, hot: number) => Math.max(0, Math.min(100, Math.round((v - cold) / (hot - cold) * 100)));
function trend(daily: Pt[] | null, weekly10: Pt[] | null) {
  if (!daily || daily.length < 220) return null;
  const last = daily.at(-1)!, ma = (n: number, end = daily.length) => daily.slice(end - n, end).reduce((a, p) => a + p[1], 0) / n;
  const ma200 = ma(200), ma200m = ma(200, daily.length - 21);
  const yr = daily.filter((x) => Date.parse(x[0]) >= Date.parse(last[0]) - 365 * 864e5), hi = Math.max(...yr.map((x) => x[1]));
  const dd = r2((last[1] / hi - 1) * 100), above = last[1] >= ma200, slope = r2((ma200 / ma200m - 1) * 100);
  // 가장 최근 약세장(직전 고점 대비 −20% 이상 하락)의 바닥
  let trough: Pt | null = null;
  const W = weekly10 && weekly10.length > 50 ? weekly10 : daily;
  { let pk = W[0][1], cur: Pt | null = null;
    for (const p of W) { if (p[1] > pk) { pk = p[1]; if (cur) { trough = cur; cur = null; } } else if (p[1] / pk - 1 <= -0.2 && (!cur || p[1] < cur[1])) cur = p; }
    if (cur) trough = cur; }
  const sinceM = trough ? Math.round((Date.parse(last[0]) - Date.parse(trough[0])) / (30.4 * 864e5)) : null;
  const rise = trough ? r2((last[1] / trough[1] - 1) * 100) : null;
  return { px: r2(last[1]), date: last[0], dd, ma200: r2(ma200), gap200: r2((last[1] / ma200 - 1) * 100), above, slope, trough: trough ? { d: trough[0], v: r2(trough[1]) } : null, sinceM, rise };
}
function phaseOf(t: any, heat: number | null, vix: number | null) {
  if (!t) return null;
  if (t.dd <= -20) return heat !== null && heat <= 35 && vix !== null && vix >= 30 ? "panic" : "bear";
  if (t.dd <= -10 || (!t.above && t.slope < 0)) return "correction";
  if (t.trough && t.sinceM !== null && t.sinceM <= 15 && t.above) return "early";
  if (heat !== null && heat >= 65) return "late";
  return "bull";
}
async function market(ind: Record<string, any>) {
  const [spxD, spxW, ksD, ksW, cape, pe, tips, mg, ipo, spy, rsp] = await Promise.all([
    yahoo("^GSPC", "2y"), yahoo("^GSPC", "10y", "1wk"), yahoo("^KS11", "2y"), yahoo("^KS11", "10y", "1wk"),
    multpl("shiller-pe"), multpl("s-p-500-pe-ratio"), fred("DFII10", "2003-01-01"),
    fred("BOGZ1FL663067003Q", "1990-01-01"), yahoo("IPO", "2y"), yahoo("SPY", "2y"), yahoo("RSP", "2y"),
  ]);
  const us = trend(spxD, spxW), kr = trend(ksD, ksW);
  const sig: any[] = [];
  const add = (k: string, g: string, gr: boolean, v: number | null, heat: number | null, why: string, date?: string) => sig.push({ k, g, gr, v, heat, why, date: date || null });
  const r1 = (p: Pt[] | null) => { if (!p) return null; const b = before(p, 365); return b ? (p.at(-1)![1] / b[1] - 1) * 100 : null; };
  // 밸류에이션
  if (cape) { const v = cape[0][1], pc = Math.round(cape.filter((p) => p[1] <= v).length / cape.length * 100); add("cape", "val", true, r2(v), pc, `경기 조정 PER ${r2(v)}배. 1871년 이후 ${pc}% 시점보다 비쌉니다`, cape[0][0]); }
  else add("cape", "val", true, null, null, "");
  if (pe && tips) { const ey = 100 / pe[0][1], ry = tips.at(-1)![1], erp = r2(ey - ry); add("erp", "val", true, erp, lin(erp, 5, 1), `이익수익률 ${r2(ey)}% − 물가연동 국채 실질금리 ${r2(ry)}% = ${erp}%p. 주식을 들고 더 받는 몫이 ${erp < 2 ? "얇습니다" : "남아 있습니다"}`, pe[0][0]); }
  else add("erp", "val", true, null, null, "");
  if (us) { const g = us.gap200; add("stretch", "val", true, g, lin(g, 0, 20), `S&P 500이 200일 평균선보다 ${g}% ${g >= 0 ? "위" : "아래"}에 있습니다`, us.date); }
  // 투기
  if (mg && mg.length > 5) { const l = mg.at(-1)!, b = before(mg, 360), y = b ? r2((l[1] / b[1] - 1) * 100) : null; add("margin", "spec", true, y, y === null ? null : lin(y, 0, 40), y === null ? "" : `빚내서 하는 주식 투자(증권사 신용 대출)가 1년 새 ${y}% ${y >= 0 ? "늘었습니다" : "줄었습니다"} (분기 자료)`, l[0]); }
  else add("margin", "spec", true, null, null, "");
  { const a = r1(ipo), c = r1(spy); const ex = a !== null && c !== null ? r2(a - c) : null; add("ipo", "spec", true, ex, ex === null ? null : lin(ex, -10, 40), ex === null ? "" : `최근 상장한 기업 주가가 S&P 500보다 1년간 ${Math.abs(ex)}%p ${ex >= 0 ? "더 올랐습니다" : "덜 올랐습니다"}`, ipo?.at(-1)?.[0]); }
  if (typeof ind.hy?.v === "number") { const v = ind.hy.v; add("credit", "spec", false, v, lin(v, 6, 3), `하이일드 스프레드 ${v}%. ${v < 3.5 ? "신용이 낮은 회사에도 돈이 싸게 풀리고 있습니다" : "위험에 값을 매기고 있습니다"}`, ind.hy.date); }
  if (typeof ind.vix?.v === "number") { const v = ind.vix.v; add("calm", "spec", false, v, lin(v, 25, 12), `공포지수 ${v}. ${v < 14 ? "시장이 위험을 거의 걱정하지 않습니다" : v < 20 ? "평온한 편입니다" : "불안이 남아 있습니다"}`, ind.vix.date); }
  // 쏠림
  { const a = r1(spy), b = r1(rsp); const ex = a !== null && b !== null ? r2(a - b) : null; add("conc", "conc", false, ex, ex === null ? null : lin(ex, 0, 15), ex === null ? "" : `시가총액 가중 S&P 500이 동일 가중보다 1년간 ${Math.abs(ex)}%p ${ex >= 0 ? "더 올랐습니다" : "덜 올랐습니다"}. ${ex >= 5 ? "소수 대형주가 지수를 끌고 있습니다" : "상승이 여러 종목에 고르게 퍼져 있습니다"}`, spy?.at(-1)?.[0]); }
  const hs = sig.map((x) => x.heat).filter((h) => typeof h === "number") as number[];
  const heat = hs.length >= 4 ? Math.round(hs.reduce((a, b) => a + b, 0) / hs.length) : null;
  const vix = typeof ind.vix?.v === "number" ? ind.vix.v : null;
  return { us: us ? { ...us, phase: phaseOf(us, heat, vix), heat } : null, kr: kr ? { ...kr, phase: phaseOf(kr, null, null) } : null, sig, heat, at: new Date().toISOString() };
}
const monthly = (pts: Pt[]) => { const m = new Map<string, Pt>(); for (const p of pts) m.set(p[0].slice(0, 7), [p[0], r2(p[1])]); return [...m.values()]; };
const weekly = (pts: Pt[]) => { const m = new Map<string, Pt>(); for (const p of pts) { const d = new Date(p[0]); const k = new Date(d.getTime() - ((d.getUTCDay() + 6) % 7) * 864e5).toISOString().slice(0, 10); m.set(k, [p[0], r2(p[1])]); } return [...m.values()]; };
const before = (pts: Pt[], days: number) => { const t = Date.parse(pts.at(-1)![0]) - days * 864e5; let b: Pt | null = null; for (const p of pts) { if (Date.parse(p[0]) <= t) b = p; else break; } return b; };
const CRISES: [string, string, string][] = [["dotcom", "2000-03-01", "2002-12-31"], ["gfc", "2007-07-01", "2009-06-30"], ["euro", "2011-07-01", "2012-06-30"], ["covid", "2020-02-15", "2020-06-30"], ["hike", "2022-01-01", "2022-12-31"]];
function peaks(pts: Pt[], high = true) {
  const o: Record<string, number> = {};
  for (const [k, a, b] of CRISES) { const xs = pts.filter((p) => p[0] >= a && p[0] <= b).map((p) => p[1]); if (xs.length) o[k] = r2(high ? Math.max(...xs) : Math.min(...xs)); }
  return o;
}
const pctile = (pts: Pt[], v: number) => Math.round(pts.filter((p) => p[1] <= v).length / pts.length * 100);
const lvl = (v: number, cuts: number[]) => cuts.filter((c) => v >= c).length; // cuts 오름차순 4개 → 0~4

// 지표 정의: id, 가중치, 수준 판정
const DEF: { k: string; id: string; from: string; w: number; level: (p: Pt[]) => { lv: number; why: string } }[] = [
  { k: "hy", id: "BAMLH0A0HYM2", from: "1997-01-01", w: 2, level: (p) => { const v = p.at(-1)![1]; return { lv: lvl(v, [4, 5, 6.5, 8]), why: v < 4 ? "회사채 시장이 위험을 낮게 보고 있습니다" : v < 6.5 ? "돈 빌리기가 조금씩 어려워지고 있습니다" : "회사채 시장에 스트레스가 커졌습니다" }; } },
  { k: "stress", id: "STLFSI4", from: "1997-01-01", w: 2, level: (p) => { const v = p.at(-1)![1]; return { lv: lvl(v, [-0.5, 0, 1, 2]), why: v < 0 ? "금융 스트레스가 평균보다 낮습니다" : v < 1 ? "금융 스트레스가 평균보다 높습니다" : "금융 시스템 전반에 긴장이 커졌습니다" }; } },
  { k: "vix", id: "VIXCLS", from: "1997-01-01", w: 1, level: (p) => { const v = p.at(-1)![1]; return { lv: lvl(v, [15, 20, 25, 35]), why: v < 20 ? "시장이 차분합니다" : v < 30 ? "시장의 불안이 커졌습니다" : "공포 구간입니다" }; } },
  { k: "curve", id: "T10Y3M", from: "1982-01-01", w: 1.5, level: (p) => {
      const v = p.at(-1)![1]; const recent = p.filter((x) => Date.parse(x[0]) > Date.parse(p.at(-1)![0]) - 548 * 864e5);
      const wasInv = recent.some((x) => x[1] < 0);
      if (v < 0) return { lv: 2, why: "장단기 금리가 역전돼 있습니다. 과거 경기 침체 1~2년 전에 나타났습니다" };
      if (wasInv) return { lv: 3, why: "역전됐던 금리차가 다시 벌어지는 중입니다. 과거에는 이때 침체가 시작된 경우가 많았습니다" };
      return { lv: v < 0.5 ? 1 : 0, why: "장단기 금리 구조가 정상입니다" };
    } },
  { k: "rate", id: "DGS10", from: "1990-01-01", w: 1.5, level: (p) => {
      const v = p.at(-1)![1], b = before(p, 365); const ch = b ? v - b[1] : 0;
      let lv = ch > 1.5 ? 3 : ch > 1 ? 2 : ch > 0.5 ? 1 : 0; if (v >= 5) lv = Math.min(4, lv + 1);
      return { lv, why: ch > 0.5 ? `1년 새 ${r2(ch)}%p 올랐습니다. 금리가 빠르게 오른 뒤에는 약한 고리가 먼저 끊어졌습니다` : "금리 상승 속도가 완만합니다" };
    } },
  { k: "sahm", id: "SAHMREALTIME", from: "1990-01-01", w: 1.5, level: (p) => { const v = p.at(-1)![1]; return { lv: v >= 0.5 ? 4 : v >= 0.3 ? 2 : v >= 0.15 ? 1 : 0, why: v >= 0.5 ? "실업률이 침체 신호 기준(0.5%p)을 넘었습니다" : "고용은 아직 침체 신호가 아닙니다" }; } },
  { k: "dollar", id: "DTWEXBGS", from: "2006-01-01", w: 1, level: (p) => {
      const v = p.at(-1)![1], b = before(p, 365); const ch = b ? (v / b[1] - 1) * 100 : 0;
      return { lv: ch > 8 ? 3 : ch > 5 ? 2 : ch > 2 ? 1 : 0, why: ch > 5 ? "달러가 1년 새 크게 강해졌습니다. 신흥국과 달러 빚이 많은 곳이 먼저 힘들어집니다" : "달러 흐름은 큰 부담이 아닙니다" };
    } },
];

Deno.serve(async (_req: Request) => {
  try {
    const { data: cfg } = await sb.from("app_config").select("value").eq("key", "publisher").maybeSingle();
    const owner = cfg?.value as string; if (!owner) return Response.json({ error: "no publisher" }, { status: 500 });
    const ind: Record<string, unknown> = {}; const fails: string[] = [];
    let sw = 0, sl = 0;
    await Promise.all(DEF.map(async (d) => {
      const p = await fred(d.id, d.from); if (!p || p.length < 30) { fails.push(d.k); return; }
      const { lv, why } = d.level(p); const last = p.at(-1)!;
      const b1 = before(p, 30), b12 = before(p, 365);
      ind[d.k] = { v: r2(last[1]), date: last[0], lv, why, chg1m: b1 ? r2(last[1] - b1[1]) : null, chg1y: b12 ? r2(last[1] - b12[1]) : null,
        pct: pctile(p, last[1]), peaks: peaks(p, d.k !== "curve"), w5: weekly(p.filter((x) => x[0] >= new Date(Date.now() - 5.2 * 365 * 864e5).toISOString().slice(0, 10))), m: monthly(p) };
      sw += d.w; sl += d.w * lv;
    }));
    // 주가지수 낙폭: 52주 최고가 대비 (코스피, S&P 500)
    await Promise.all([["kospi", "^KS11", 1.5], ["spx", "^GSPC", 1]].map(async ([k, sym, w]) => {
      const p = await yahoo(sym as string); if (!p) { fails.push(k as string); return; }
      const last = p.at(-1)!, yr = p.filter((x) => Date.parse(x[0]) >= Date.parse(last[0]) - 365 * 864e5);
      const hi = Math.max(...yr.map((x) => x[1])), dd = r2((last[1] / hi - 1) * 100), b1 = before(p, 7);
      const lv = lvl(-dd, [10, 15, 20, 30]);
      ind[k as string] = { v: dd, px: r2(last[1]), hi: r2(hi), date: last[0], lv, chg1w: b1 ? r2((last[1] / b1[1] - 1) * 100) : null,
        why: -dd < 10 ? "고점 근처에서 움직이고 있습니다" : -dd < 20 ? "고점에서 의미 있게 내려왔습니다. 조정 구간입니다" : "고점 대비 20% 넘게 빠진 약세장 구간입니다",
        w5: weekly(p.filter((x) => Date.parse(x[0]) >= Date.parse(last[0]) - 400 * 864e5)) };
      sw += w as number; sl += (w as number) * lv;
    }));
    // 프랑스-독일 금리차는 fx/rates 에서 가져온다 (주간 작업의 최신값 우선)
    const { data: rd } = await sb.from("docs").select("data").eq("owner", owner).eq("collection", "fx").eq("id", "rates").maybeSingle();
    const R: any = rd?.data || {}; const fr = R.manual?.FR10Y, de = R.manual?.DE10Y;
    const frde = fr && de ? { v: r2(fr.v - de.v), date: fr.date } : R.auto?.FR_DE ? { v: R.auto.FR_DE.v, date: R.auto.FR_DE.date } : null;
    if (frde) { const lv = lvl(frde.v, [0.5, 0.8, 1.2, 1.8]); ind.euro = { ...frde, lv, why: frde.v < 0.8 ? "유럽 재정 불안은 크지 않습니다" : "프랑스 국채에 위험 프리미엄이 붙고 있습니다", peaks: { euro: 1.9 }, m: R.series?.FR_DE?.monthly || [] }; sw += 0.5; sl += 0.5 * lv; }
    const score = sw ? r2(sl / sw) : null;
    let overall = score === null ? null : score < 0.8 ? 0 : score < 1.6 ? 1 : score < 2.3 ? 2 : score < 3 ? 3 : 4;
    // 보수적 바닥: 한 지표라도 위험(4)이면 최소 경계(3), 경계 이상이 2개 넘으면 최소 유의(2)
    const lvs = Object.values(ind).map((o: any) => o.lv as number);
    if (overall !== null) { if (lvs.some((v) => v >= 4)) overall = Math.max(overall, 3); if (lvs.filter((v) => v >= 3).length >= 2) overall = Math.max(overall, 2); }
    const { data: old } = await sb.from("docs").select("data").eq("owner", owner).eq("collection", "fx").eq("id", "radar").maybeSingle();
    const hist = [...(((old?.data as any)?.hist) || []).filter((h: any) => h.d !== new Date().toISOString().slice(0, 10)), { d: new Date().toISOString().slice(0, 10), s: score, o: overall }].slice(-400);
    const ffp = await fred("FEDFUNDS", "1990-01-01"); // 과거 위기 비교용 미국 기준금리(월평균)
    let mk: any = null; try { mk = await market(ind as any); } catch (_) { fails.push("market"); } // 시장 국면(강세장·약세장)
    const data = { ...(old?.data || {}), ind, score, overall, hist, ...(ffp ? { ff: monthly(ffp) } : {}), ...(mk ? { mkt: mk } : {}), graham: undefined, autoAt: new Date().toISOString(), fails };
    const { error } = await sb.from("docs").upsert({ owner, collection: "fx", id: "radar", data, updated_at: new Date().toISOString() }, { onConflict: "owner,collection,id" });
    if (error) throw error;
    return Response.json({ ok: true, score, overall, got: Object.keys(ind), fails, mkt: mk ? { us: mk.us && [mk.us.phase, mk.us.dd, mk.us.gap200, mk.us.slope, mk.us.sinceM, mk.us.rise], kr: mk.kr && [mk.kr.phase, mk.kr.dd, mk.kr.gap200, mk.kr.slope, mk.kr.sinceM, mk.kr.rise], heat: mk.heat, sig: mk.sig.map((x: any) => [x.k, x.v, x.heat]) } : null });
  } catch (e) {
    return Response.json({ error: String((e as Error)?.message || e) }, { status: 500 });
  }
});
