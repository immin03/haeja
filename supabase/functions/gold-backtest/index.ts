// gold-backtest (2026-11-24 대표: 과거 금 바닥에서 신호가 몇 개 켜져 있었는지 백테스트) — POST(x-cron)로 계산해 app_config.gold_backtest 에 저장, GET 은 저장된 결과
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";
const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
type Pt = [string, number];
async function yahoo(sym: string): Promise<Pt[]> {
  const r = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?period1=946684800&period2=${Math.floor(Date.now()/1000)}&interval=1d`, { headers: { "User-Agent": "Mozilla/5.0" } });
  const res = (await r.json())?.chart?.result?.[0]; const ts: number[] = res?.timestamp || [], cl = res?.indicators?.quote?.[0]?.close || []; const p: Pt[] = [];
  ts.forEach((t, i) => { const v = cl[i]; if (typeof v === "number") p.push([new Date(t * 1000).toISOString().slice(0, 10), v]); }); return p;
}
async function fred(id: string): Promise<Pt[]> {
  const t = await (await fetch(`https://fred.stlouisfed.org/graph/fredgraph.csv?id=${id}&cosd=2000-01-01`, { headers: { "User-Agent": "Mozilla/5.0" } })).text(); const p: Pt[] = [];
  t.split("\n").slice(1).forEach(l => { const [d, v] = l.trim().split(","); const x = Number(v); if (d && v && v !== "." && isFinite(x)) p.push([d, x]); }); return p;
}
async function gld(): Promise<Pt[]> {
  try { const t = await (await fetch("https://www.spdrgoldshares.com/assets/dynamic/GLD/GLD_US_archive_EN.csv", { headers: { "User-Agent": "Mozilla/5.0" } })).text();
    const p: Pt[] = []; t.split("\n").forEach(l => { const c = l.split(","); const d = Date.parse(c[0]); const tonnes = Number(String(c[9] || "").replace(/[^0-9.]/g, "")); if (isFinite(d) && tonnes > 0) p.push([new Date(d).toISOString().slice(0, 10), tonnes]); });
    return p.sort((a, b) => a[0] < b[0] ? -1 : 1); } catch (_) { return []; }
}
const upto = (p: Pt[], d: string) => p.filter(x => x[0] <= d);
const back = (d: string, days: number) => new Date(Date.parse(d) - days * 864e5).toISOString().slice(0, 10);
function sig(d: string, S: any) {
  const ry = upto(S.ry, d), ry6 = ry.filter(x => x[0] >= back(d, 183)), ryMax = Math.max(...ry6.map(x => x[1])), ryNow = ry.at(-1)![1];
  const ff = upto(S.ff, d), ffNow = ff.at(-1)![1], ff3 = upto(S.ff, back(d, 92)).at(-1)![1];
  const dx = upto(S.dx, d), dx6 = dx.filter(x => x[0] >= back(d, 183)), dxMax = Math.max(...dx6.map(x => x[1])), dxNow = dx.at(-1)![1], dx50 = dx.slice(-50).reduce((a, x) => a + x[1], 0) / 50;
  const vx = upto(S.vix, d), vx1 = vx.filter(x => x[0] >= back(d, 31)), vxMax = Math.max(...vx1.map(x => x[1])), vxNow = vx.at(-1)![1];
  const g = upto(S.gld, d), g30 = upto(S.gld, back(d, 30)).at(-1);
  const flow = g.length && g30 ? g.at(-1)![1] - g30[1] : null;
  return {
    ry: { on: ryMax - ryNow >= 0.29, now: ryNow, max: ryMax },
    fed: { on: ffNow <= ff3 + 0.05, now: ffNow, before: ff3 },
    dxy: { on: dxNow / dxMax - 1 <= -0.03 && dxNow < dx50, off: (dxNow / dxMax - 1) * 100 },
    etf: { on: flow != null && flow > 0, flow },
    vix: { on: vxMax >= 30 && vxNow < 30, now: vxNow, max: vxMax },
  };
}
Deno.serve(async (req) => {
  if (req.method === "GET" && new URL(req.url).searchParams.get("from")) {   // 그래프용 시세 (영상·랜딩): ?from=YYYY-MM-DD&to=&step=
    const u = new URL(req.url), f = u.searchParams.get("from")!, t = u.searchParams.get("to") || "2100-01-01", st = Math.max(1, Number(u.searchParams.get("step") || 1));
    const p = (await yahoo("GC=F")).filter(x => x[0] >= f && x[0] <= t).filter((_, i) => i % st === 0).map(x => [x[0], Math.round(x[1] * 10) / 10]);
    return new Response(JSON.stringify(p), { headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" } });
  }
  if (req.method === "GET") { const { data } = await sb.from("app_config").select("value").eq("key", "gold_backtest").maybeSingle(); return new Response(JSON.stringify(data?.value || {}), { headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" } }); }
  const { data: sec } = await sb.from("app_config").select("value").eq("key", "vn_cron_secret").maybeSingle();
  if (req.headers.get("x-cron") !== String(sec?.value)) return new Response("key", { status: 403 });
  const [gc, dx, vix, ry, ff, g] = await Promise.all([yahoo("GC=F"), yahoo("DX-Y.NYB"), yahoo("^VIX"), fred("DFII10"), fred("DFF"), gld()]);
  const S = { gc, dx, vix, ry, ff, gld: g };
  // 바닥일: 금 선물(GC=F) 종가 최저일 (2008은 현물 최저 10/24보다 선물 종가 최저 11/13이 그래프 최저점이라 11/13)
  const eps = [["2008", "2008-11-13"], ["2015", "2015-12-17"], ["2020", "2020-03-19"], ["2022", "2022-11-03"]];
  const out = eps.map(([nm, d0]) => {
    const lo = gc.find(x => x[0] >= d0)!;
    const after = (days: number) => { const p = gc.find(x => x[0] >= new Date(Date.parse(lo[0]) + days * 864e5).toISOString().slice(0, 10)); return p ? Math.round((p[1] / lo[1] - 1) * 1000) / 10 : null; };
    const at = (k: number) => { const d = new Date(Date.parse(lo[0]) + k * 864e5).toISOString().slice(0, 10); const s = sig(d, S); return { d, n: Object.values(s).filter((x: any) => x.on).length, s }; };
    const w0 = back(lo[0], 182), w1 = new Date(Date.parse(lo[0]) + 182 * 864e5).toISOString().slice(0, 10);
    const ser = gc.filter(x => x[0] >= w0 && x[0] <= w1).filter((_, i, arr) => i % 3 === 0 || arr[i][0] === lo[0]).map(x => [x[0], Math.round(x[1] * 10) / 10]);
    const pk = (x: any) => ({ d: x.d, n: x.n, a: [x.s.ry.on, x.s.fed.on, x.s.dxy.on, null, x.s.vix.on] });   // ④ 금 ETF는 과거 일별 자료 없음(null)
    return { nm, low: lo, ret1m: after(30), ret3m: after(91), ret1y: after(365), atLow: pk(at(0)), m1: pk(at(30)), m2: pk(at(61)), m3: pk(at(91)), ser };
  });
  await sb.from("app_config").upsert({ key: "gold_backtest", value: { at: new Date().toISOString(), out } });
  return new Response(JSON.stringify({ out }), { headers: { "Content-Type": "application/json" } });
});
