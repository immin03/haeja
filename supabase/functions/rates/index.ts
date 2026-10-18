// 금리 자료 수집 (매일, trend-series 끝에서 호출)
// 미국 연준 경제자료(FRED)의 공개 CSV에서 주요 금리를 받아 fx/rates 문서에 저장한다.
// - 일간: 미국 10년·2년 국채, 미국 기준금리 상단, 유로 예금금리
// - 월간(OECD): 한국·일본·독일·프랑스·이탈리아·영국 10년 국채, 한국 기준금리
// - 월간: 미국 소비자물가 지수(CPIAUCSL) → data.cpi (이슈 릴스용)
// 주간 칼럼 작업이 쓰는 해설(headline, issues, impact, manual 최신값)은 건드리지 않고 그대로 둔다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
type Pt = [string, number];
const r2 = (v: number) => Math.round(v * 100) / 100;

const DAILY: Record<string, string> = { US10Y: "DGS10", US2Y: "DGS2", USPOL: "DFEDTARU", EUPOL: "ECBDFR" };
const MONTHLY: Record<string, string> = {
  KR10Y: "IRLTLT01KRM156N", JP10Y: "IRLTLT01JPM156N", DE10Y: "IRLTLT01DEM156N", FR10Y: "IRLTLT01FRM156N",
  IT10Y: "IRLTLT01ITM156N", GB10Y: "IRLTLT01GBM156N", KRPOL: "IRSTCB01KRM156N",
};

async function fred(id: string, from: string): Promise<Pt[] | null> {
  try {
    const r = await fetch(`https://fred.stlouisfed.org/graph/fredgraph.csv?id=${id}&cosd=${from}`, { headers: { "User-Agent": "Mozilla/5.0 (valuenote)" } });
    if (!r.ok) return null;
    const rows = (await r.text()).trim().split("\n").slice(1);
    const pts = rows.map((l) => l.trim().split(",")).filter(([d, v]) => /^\d{4}-\d\d-\d\d$/.test(d) && /^-?\d+(\.\d+)?$/.test((v || "").trim())).map(([d, v]) => [d, r2(Number(v))] as Pt);
    return pts.length ? pts : null;
  } catch (_) { return null; }
}
/* 미국 10년물 최신값 보강: 야후 ^TNX (단위가 % 그대로) */
async function yahooTNX(): Promise<Pt[] | null> {
  try {
    const r = await fetch("https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX?range=1mo&interval=1d", { headers: { "User-Agent": "Mozilla/5.0 (valuenote)" } });
    const res = (await r.json())?.chart?.result?.[0];
    const ts: number[] = res?.timestamp || [], cl: (number | null)[] = res?.indicators?.quote?.[0]?.close || [];
    return ts.map((t, i) => [new Date(t * 1000).toISOString().slice(0, 10), cl[i]] as [string, number | null])
      .filter((p): p is Pt => typeof p[1] === "number" && isFinite(p[1]));
  } catch (_) { return null; }
}
const weekly = (pts: Pt[]) => { const m = new Map<string, Pt>(); for (const p of pts) { const d = new Date(p[0]); const k = new Date(d.getTime() - ((d.getUTCDay() + 6) % 7) * 864e5).toISOString().slice(0, 10); m.set(k, p); } return [...m.values()]; };
const monthly = (pts: Pt[]) => { const m = new Map<string, Pt>(); for (const p of pts) m.set(p[0].slice(0, 7), p); return [...m.values()]; };
function chg(pts: Pt[], days: number) {
  if (pts.length < 2) return null; const last = pts.at(-1)!; const t = Date.parse(last[0]) - days * 864e5;
  let base: Pt | null = null; for (const p of pts) { if (Date.parse(p[0]) <= t) base = p; else break; }
  return base ? r2(last[1] - base[1]) : null; // %p 변화
}

Deno.serve(async (_req: Request) => {
  try {
    const { data: cfg } = await sb.from("app_config").select("value").eq("key", "publisher").maybeSingle();
    const owner = cfg?.value as string; if (!owner) return new Response(JSON.stringify({ error: "no publisher" }), { status: 500 });
    const from5 = new Date(Date.now() - 5.2 * 365 * 864e5).toISOString().slice(0, 10), from10 = new Date(Date.now() - 10.2 * 365 * 864e5).toISOString().slice(0, 10);
    const series: Record<string, { daily: Pt[]; points: Pt[]; monthly: Pt[] }> = {};
    const auto: Record<string, { v: number; date: string; chg1m: number | null; chg1y: number | null; freq: string }> = {};
    const fails: string[] = [];
    await Promise.all(Object.entries(DAILY).map(async ([k, id]) => {
      let p = await fred(id, from5);
      if (k === "US10Y") { const y = await yahooTNX(); if (y && y.length) { const m = new Map((p || []).map((x) => [x[0], x[1]])); y.forEach(([d, v]) => m.set(d, r2(v > 20 ? v / 10 : v))); p = [...m.entries()].sort((a, b) => a[0] < b[0] ? -1 : 1) as Pt[]; } }
      if (!p) { fails.push(k); return; }
      series[k] = { daily: p.slice(-70), points: weekly(p), monthly: monthly(p) };
      auto[k] = { v: p.at(-1)![1], date: p.at(-1)![0], chg1m: chg(p, 30), chg1y: chg(p, 365), freq: "일간" };
    }));
    await Promise.all(Object.entries(MONTHLY).map(async ([k, id]) => {
      const p = await fred(id, from10); if (!p) { fails.push(k); return; }
      series[k] = { daily: [], points: [], monthly: p };
      auto[k] = { v: p.at(-1)![1], date: p.at(-1)![0], chg1m: chg(p, 31), chg1y: chg(p, 366), freq: "월간" };
    }));
    // 미국 소비자물가 지수(월간, 계절조정). 화면의 금리 목록에는 넣지 않고 이슈 릴스(events.py)가 1년 전 대비 상승률을 계산하는 데만 쓴다
    const cpiPts = await fred("CPIAUCSL", from5);
    const cpi = cpiPts ? { monthly: cpiPts.slice(-30), at: new Date().toISOString() } : null; if (!cpiPts) fails.push("USCPI");
    if (series.US10Y && series.US2Y) { // 장단기 금리차 (10년 − 2년)
      const m2 = new Map(series.US2Y.daily.concat(series.US2Y.points).map((p) => [p[0], p[1]]));
      const sp = (arr: Pt[]) => arr.filter((p) => m2.has(p[0])).map((p) => [p[0], r2(p[1] - m2.get(p[0])!)] as Pt);
      series.US10_2 = { daily: sp(series.US10Y.daily), points: sp(series.US10Y.points), monthly: sp(series.US10Y.monthly) };
      const d = series.US10_2.daily.at(-1); if (d) auto.US10_2 = { v: d[1], date: d[0], chg1m: chg(series.US10_2.daily, 30), chg1y: chg(series.US10_2.points, 365), freq: "일간" };
    }
    if (series.FR10Y && series.DE10Y) { // 프랑스 − 독일 10년 금리차
      const md = new Map(series.DE10Y.monthly.map((p) => [p[0], p[1]]));
      const sp = series.FR10Y.monthly.filter((p) => md.has(p[0])).map((p) => [p[0], r2(p[1] - md.get(p[0])!)] as Pt);
      series.FR_DE = { daily: [], points: [], monthly: sp };
      const d = sp.at(-1); if (d) auto.FR_DE = { v: d[1], date: d[0], chg1m: chg(sp, 31), chg1y: chg(sp, 366), freq: "월간" };
    }
    const { data: old } = await sb.from("docs").select("data").eq("owner", owner).eq("collection", "fx").eq("id", "rates").maybeSingle();
    const data = { ...(old?.data || {}), ...(cpi ? { cpi } : {}), series: { ...((old?.data as any)?.series || {}), ...series }, auto: { ...((old?.data as any)?.auto || {}), ...auto }, autoAt: new Date().toISOString(), fails };
    const { error } = await sb.from("docs").upsert({ owner, collection: "fx", id: "rates", data, updated_at: new Date().toISOString() }, { onConflict: "owner,collection,id" });
    if (error) throw error;
    return new Response(JSON.stringify({ ok: true, got: Object.keys(auto), fails }), { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    return new Response(JSON.stringify({ error: String((e as Error)?.message || e) }), { status: 500, headers: { "Content-Type": "application/json" } });
  }
});
