// semi-backtest (2026-11-24 대표: "과거 바닥에서 그래프가 어땠는지 — 금하고 반도체 둘 다 서비스 계기판에")
// 금(gold-backtest)과 같은 모양으로, 과거 4번의 반도체 하락장 바닥에서 신호가 몇 개 켜져 있었는지 계산한다.
// 4번 = SOXL 3편이 쓴 뱅크오브아메리카 보고서의 2011·2015·2018·2022 하락장 (평균 253일·-32%)
// POST(x-cron) 로 계산해 app_config.semi_backtest 에 저장, GET 은 저장된 결과(공개)
// 신호 5개 (지금 계기판 semi-gauge 와 같은 기준)
//  ① 실적: 고점 대비 -20% 이하이면서 최근 3개월(63거래일) 저점에서 15% 이상 반등
//  ② 가격(예상 PER): 과거 일별 예상 PER 자료가 없어 계산하지 않는다(null)
//  ③ 기간: 고점 대비 -20% 이하이면서 고점 뒤 253일(달력일) 이상
//  ④ 공포(VIX): 최근 1개월(21거래일)에 30 이상 치솟았다가 30 아래
//  ⑤ 금리(10년물): 지금은 연준 확인으로 수동이지만, 과거는 '6개월 최고보다 0.5%p 이상 내려옴'으로 대신 계산
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";
const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
type Pt = [string, number];
async function yahoo(sym: string): Promise<Pt[]> {
  const r = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?period1=1104537600&period2=${Math.floor(Date.now() / 1000)}&interval=1d`, { headers: { "User-Agent": "Mozilla/5.0" } });
  const res = (await r.json())?.chart?.result?.[0]; const ts: number[] = res?.timestamp || [], cl = res?.indicators?.quote?.[0]?.close || []; const p: Pt[] = [];
  ts.forEach((t, i) => { const v = cl[i]; if (typeof v === "number" && isFinite(v)) p.push([new Date(t * 1000).toISOString().slice(0, 10), v]); }); return p;
}
const back = (d: string, days: number) => new Date(Date.parse(d) - days * 864e5).toISOString().slice(0, 10);
const fwd = (d: string, days: number) => new Date(Date.parse(d) + days * 864e5).toISOString().slice(0, 10);
function sig(d: string, S: { sox: Pt[]; vix: Pt[]; tnx: Pt[] }, peak: Pt) {
  const sx = S.sox.filter(x => x[0] <= d), now = sx.at(-1)!;
  const dd = (now[1] / peak[1] - 1) * 100;
  const lo3 = Math.min(...sx.slice(-63).map(x => x[1])), reb = (now[1] / lo3 - 1) * 100;
  const cal = Math.round((Date.parse(now[0]) - Date.parse(peak[0])) / 864e5);
  const vx = S.vix.filter(x => x[0] <= d), vx1 = vx.slice(-21), vxMax = Math.max(...vx1.map(x => x[1])), vxNow = vx.at(-1)![1];
  const tn = S.tnx.filter(x => x[0] <= d), tn6 = tn.slice(-126), tnMax = Math.max(...tn6.map(x => x[1])), tnNow = tn.at(-1)![1];
  return {
    lead: dd <= -20 && reb >= 15, pe: null, days: dd <= -20 && cal >= 253,
    vix: vxMax >= 30 && vxNow < 30, rate: tnMax - tnNow >= 0.5,
    dd: Math.round(dd * 10) / 10, reb: Math.round(reb * 10) / 10, cal,
  };
}
Deno.serve(async (req) => {
  const cors = { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" };
  if (req.method === "GET") { const { data } = await sb.from("app_config").select("value").eq("key", "semi_backtest").maybeSingle(); return new Response(JSON.stringify(data?.value || {}), { headers: { ...cors, "Cache-Control": "public, max-age=3600" } }); }
  const { data: sec } = await sb.from("app_config").select("value").eq("key", "vn_cron_secret").maybeSingle();
  if (!sec?.value || req.headers.get("x-cron") !== String(sec.value)) return new Response("key", { status: 403 });
  const [sox, vix, tnx] = await Promise.all([yahoo("^SOX"), yahoo("^VIX"), yahoo("^TNX")]);
  const S = { sox, vix, tnx };
  // 바닥 찾기: 기준일 앞뒤 60일 안의 반도체지수 종가 최저일. 고점: 그 바닥 앞 450일 안의 최고 종가
  const eps: [string, string][] = [["2011", "2011-10-03"], ["2015", "2016-02-11"], ["2018", "2018-12-24"], ["2022", "2022-10-13"]];
  const out = eps.map(([nm, d0]) => {
    const win = sox.filter(x => x[0] >= back(d0, 60) && x[0] <= fwd(d0, 60));
    const lo = win.reduce((a, x) => x[1] < a[1] ? x : a, win[0]);
    const pre = sox.filter(x => x[0] >= back(lo[0], 450) && x[0] < lo[0]);
    const peak = pre.reduce((a, x) => x[1] > a[1] ? x : a, pre[0]);
    const after = (days: number) => { const p = sox.find(x => x[0] >= fwd(lo[0], days)); return p ? Math.round((p[1] / lo[1] - 1) * 1000) / 10 : null; };
    const at = (k: number) => { const d = fwd(lo[0], k); const s = sig(d, S, peak); const a = [s.lead, s.pe, s.days, s.vix, s.rate]; return { d, n: a.filter(Boolean).length, a }; };
    const w0 = back(lo[0], 182), w1 = fwd(lo[0], 182);
    // 주마다 켜진 신호 수 (그래프 배경 띠: 2개 이상 켜진 기간) — 2026-11-24 대표 "불 2~3개 켜진 구간도 보여 주자"
    const cnt = sox.filter(x => x[0] >= w0 && x[0] <= w1).filter((_, i) => i % 5 === 0).map(x => { const z = sig(x[0], S, peak); return [x[0], [z.lead, z.days, z.vix, z.rate].filter(Boolean).length]; });
    const first2 = cnt.find(c => c[0] >= lo[0] && (c[1] as number) >= 2) || null;
    const px2 = first2 ? sox.find(x => x[0] >= first2[0]) : null;
    const ser = sox.filter(x => x[0] >= w0 && x[0] <= w1).filter((_, i, arr) => i % 3 === 0 || arr[i][0] === lo[0]).map(x => [x[0], Math.round(x[1] * 10) / 10]);
    return { nm, low: [lo[0], Math.round(lo[1] * 10) / 10], peak: [peak[0], Math.round(peak[1] * 10) / 10], dd: Math.round((lo[1] / peak[1] - 1) * 1000) / 10,
      days: Math.round((Date.parse(lo[0]) - Date.parse(peak[0])) / 864e5), ret1m: after(30), ret3m: after(91), ret1y: after(365),
      atLow: at(0), m1: at(30), m2: at(61), m3: at(91), ser, cnt,
      first2: first2 && px2 ? { d: first2[0], n: first2[1], days: Math.round((Date.parse(first2[0]) - Date.parse(lo[0])) / 864e5), fromLow: Math.round((px2[1] / lo[1] - 1) * 1000) / 10 } : null };
  });
  await sb.from("app_config").upsert({ key: "semi_backtest", value: { at: new Date().toISOString(), names: ["실적", "가격", "기간", "공포", "금리"], out } });
  return new Response(JSON.stringify({ out }), { headers: cors });
});
