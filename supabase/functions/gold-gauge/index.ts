// gold-gauge (2026-11-24 대표: "금도 계기판 똑같이" — 금값 3편 4장 화면과 같은 이름·기준)
// GET  : 최신 금 계기판 JSON (공개, 사이트 /semi 의 '금' 탭이 읽음)
// POST : x-cron = app_config.vn_cron_secret 일 때 다시 계산해 app_config.gold_gauge 에 저장 (매일 미국 마감 뒤)
// 금 바닥 신호 5개 (영상 L261124-gold-3 GAUGE 와 같은 이름·기준)
//  ① 실질금리: 정점 뒤 2.66% 아래로 — 미국 10년 물가연동국채 금리(FRED DFII10). 6개월 최고를 찍은 뒤 2.66% 아래면 켬
//     (FRED 가 막히면 app_config.gold_gauge_ry {v, asof} 수동값)
//  ② 연준: 12월 9일 인상 멈춤 신호 — app_config.gold_gauge_fed {on, asof, now, note} 수동
//  ③ 달러: 정점 찍고 하락 — 달러지수(DX-Y.NYB)가 6개월 최고에서 3% 이상 내려오고 50일 평균 아래면 켬
//  ④ 금 ETF: 유출 멈추고 유입 — app_config.gold_gauge_etf {flow30, asof, src} 수동(억 달러, 30일 합). 0 초과면 켬
//  ⑤ 공포(VIX): 최근 1개월에 30 이상 치솟았다가 30 아래로 내려오면 켬 (반도체 계기판 ④와 같은 기준)
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";
const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "content-type, x-cron", "Access-Control-Allow-Methods": "GET, POST, OPTIONS" };
const json = (o: unknown, s = 200, extra: Record<string, string> = {}) => new Response(JSON.stringify(o), { status: s, headers: { ...cors, "Content-Type": "application/json; charset=utf-8", ...extra } });
type Pt = [string, number];
async function chart(sym: string, range = "5y"): Promise<Pt[]> {
  const r = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=${range}&interval=1d`, { headers: { "User-Agent": "Mozilla/5.0 (valuenote-gauge)" } });
  if (!r.ok) throw new Error(sym + " HTTP " + r.status);
  const res = (await r.json())?.chart?.result?.[0];
  const ts: number[] = res?.timestamp || [], cl: (number | null)[] = res?.indicators?.quote?.[0]?.close || [];
  const off = (res?.meta?.gmtoffset ?? 0) * 1000, pts: Pt[] = [];
  ts.forEach((t, i) => { const v = cl[i]; if (typeof v === "number" && isFinite(v)) pts.push([new Date(t * 1000 + off).toISOString().slice(0, 10), v]); });
  return pts;
}
async function fred(id: string): Promise<Pt[]> {
  const from = new Date(Date.now() - 400 * 864e5).toISOString().slice(0, 10);
  const r = await fetch(`https://fred.stlouisfed.org/graph/fredgraph.csv?id=${id}&cosd=${from}`, { headers: { "User-Agent": "Mozilla/5.0 (valuenote-gauge)" } });
  if (!r.ok) throw new Error(id + " HTTP " + r.status);
  const pts: Pt[] = [];
  (await r.text()).split("\n").slice(1).forEach(l => { const [d, v] = l.trim().split(","); const x = Number(v); if (d && v && v !== "." && isFinite(x)) pts.push([d, x]); });
  if (!pts.length) throw new Error(id + " empty");
  return pts;
}
const r2 = (x: number) => Math.round(x * 100) / 100;
const cfg = async (k: string) => (await sb.from("app_config").select("value").eq("key", k).maybeSingle()).data?.value;
function ddInfo(p: Pt[]) {
  let hi = -Infinity, hiI = 0;
  p.forEach(([, v], i) => { if (v > hi) { hi = v; hiI = i; } });
  const last = p[p.length - 1];
  return { hi: r2(hi), hiDate: p[hiI][0], last: r2(last[1]), lastDate: last[0], dd: r2((last[1] / hi - 1) * 100), days: p.length - 1 - hiI };
}
async function compute() {
  const [gc, gld, iau, gdx, vix, dxy] = await Promise.all([chart("GC=F"), chart("GLD"), chart("IAU"), chart("GDX"), chart("^VIX", "6mo"), chart("DX-Y.NYB", "1y")]);
  // ① 실질금리
  let ry: Pt[] = [], rySrc = "FRED DFII10";
  try { ry = await fred("DFII10"); } catch (_) {
    const m = await cfg("gold_gauge_ry"); if (m?.v != null) { ry = [[m.asof || "", Number(m.v)]]; rySrc = "수동 " + (m.asof || ""); }
  }
  const ry6 = ry.slice(-126), ryMax = ry6.length ? Math.max(...ry6.map(x => x[1])) : NaN, ryNow = ry.length ? ry[ry.length - 1][1] : NaN;
  const ryMaxDate = ry6.find(x => x[1] === ryMax)?.[0] || "";
  const ryOn = isFinite(ryNow) && ryMax >= 2.66 && ryNow < 2.66;
  // ② 연준
  const fed = (await cfg("gold_gauge_fed")) || { on: false, asof: "2026-11-23", now: "인상 확률 90%대", note: "12월 9일 연준 회의에서 확인" };
  // ③ 달러
  const dx6 = dxy.slice(-126), dxMax = Math.max(...dx6.map(x => x[1])), dxNow = dxy[dxy.length - 1][1];
  const dx50 = dxy.slice(-50).reduce((a, x) => a + x[1], 0) / Math.min(50, dxy.length), dxOff = r2((dxNow / dxMax - 1) * 100);
  const dxOn = dxOff <= -3 && dxNow < dx50;
  // ④ 금 ETF
  const etfCfg = (await cfg("gold_gauge_etf")) || { flow30: -26, asof: "2026-11-23", src: "GLD 30일 순유출 보도" };
  const flow = Number(etfCfg.flow30);
  // ⑤ VIX
  const vix1m = vix.slice(-21), vixMax = Math.max(...vix1m.map(x => x[1])), vixNow = vix[vix.length - 1][1];
  const g = ddInfo(gc);
  const signals = [
    { id: "ry", name: "① 실질금리", now: isFinite(ryNow) ? `${r2(ryNow)}% (6개월 최고 ${r2(ryMax)}%)` : "자료 대기", target: "정점 뒤 2.66% 아래로", on: ryOn,
      pct: isFinite(ryNow) ? Math.min(100, Math.max(0, (ryMax - ryNow) / Math.max(0.01, ryMax - 2.66) * 100)) : 0, note: `물가를 뺀 금리 · 높을수록 이자 없는 금에 불리 · ${rySrc}` },
    { id: "fed", name: "② 연준", now: String(fed.now || ""), target: "12월 9일 인상 멈춤 신호", on: fed.on === true, pct: fed.on === true ? 100 : 20,
      note: `${fed.note || ""} · 2015년 12월 첫 인상 직후가 4년 하락의 바닥` },
    { id: "dxy", name: "③ 달러", now: `${r2(dxNow)} (6개월 최고 대비 ${dxOff}%)`, target: "정점 찍고 하락 (최고 대비 -3%)", on: dxOn,
      pct: Math.min(100, Math.max(0, -dxOff / 3 * 100)), note: `달러지수 · 50일 평균 ${r2(dx50)} 아래로 내려와야 켜짐` },
    { id: "etf", name: "④ 금 ETF", now: `30일 ${flow > 0 ? "+" : ""}${flow}억 달러`, target: "유출 멈추고 유입", on: flow > 0,
      pct: flow > 0 ? 100 : Math.min(90, Math.max(0, 90 + flow * 2)), note: `${etfCfg.asof} 기준 · ${etfCfg.src || ""} · 주 1회 갱신` },
    { id: "vix", name: "⑤ 공포(VIX)", now: `${r2(vixNow)} (1개월 최고 ${r2(vixMax)})`, target: "30 위 → 30 아래로", on: vixMax >= 30 && vixNow < 30,
      pct: vixMax >= 30 ? Math.min(100, Math.max(0, (vixMax - vixNow) / Math.max(0.01, vixMax - 30) * 100)) : 0, note: "공포가 치솟았다 가라앉을 때 투매가 끝나는 경우가 많았습니다" },
  ];
  const etf = (name: string, p: Pt[], lev: string) => { const d = ddInfo(p); return { name, lev, last: d.last, dd: d.dd, hiDate: d.hiDate, lastDate: d.lastDate }; };
  const spark = (p: Pt[], n = 260) => p.slice(-n).filter((_, i, a) => i % 5 === 0 || i === a.length - 1).map(x => [x[0], r2(x[1])]);
  return {
    kind: "gold", updatedAt: new Date().toISOString(), asof: g.lastDate,
    on: signals.filter(x => x.on).length, total: signals.length, signals,
    etfs: [etf("GLD", gld, "금 1배"), etf("IAU", iau, "금 1배"), etf("GDX", gdx, "금광주")],
    gold: { ...g, spark: spark(gc) },
    raw: { ryNow: r2(ryNow), ryMax: r2(ryMax), ryMaxDate, rySrc, dxNow: r2(dxNow), dxMax: r2(dxMax), dx50: r2(dx50), dxOff, flow30: flow, vixNow: r2(vixNow), vixMax: r2(vixMax) },
  };
}
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method === "POST") {
    const sec = await cfg("vn_cron_secret");
    if (!sec || req.headers.get("x-cron") !== String(sec)) return json({ error: "key" }, 403);
    try {
      const g = await compute();
      const pv = await cfg("gold_gauge");
      await sb.from("app_config").upsert({ key: "gold_gauge", value: g });
      // 신호가 켜지거나 꺼지면 알림: push_prefs main.gold = true 회원
      const changed = pv?.signals ? g.signals.filter(s => { const o = pv.signals.find((x: any) => x.id === s.id); return o && o.on !== s.on; }) : [];
      let sent = 0;
      if (changed.length && pv?.asof !== g.asof) {
        const md = (d: string) => { const p = d.split("-"); return `${+p[1]}/${+p[2]}`; };
        const title = `금 바닥 계기판 ${pv.on}개 → ${g.on}개`;
        const body = changed.map(s => `${s.name} ${s.on ? "켜짐" : "꺼짐"}(${s.now})`).join(" · ") + ` · 미국 ${md(g.asof)} 마감 기준`;
        const { data: subs } = await sb.from("docs").select("owner").eq("collection", "push_prefs").eq("id", "main").eq("data->>gold", "true");
        const rows = [...new Set((subs || []).map((r: any) => r.owner))].map(owner => ({ owner, collection: "alerts", id: `gold-${g.asof}`, updated_at: new Date().toISOString(),
          data: { at: new Date().toISOString(), level: "info", title, body, url: "/semi?tab=gold&from=push", read: false, push: true, source: "금 계기판" } }));
        if (rows.length) { const { error } = await sb.from("docs").upsert(rows, { onConflict: "owner,collection,id", ignoreDuplicates: true }); if (!error) sent = rows.length; }
        await sb.from("app_config").upsert({ key: "gold_gauge_event", value: { at: g.updatedAt, from: pv.on, to: g.on, asof: g.asof, changed: changed.map(s => s.id), sent } });
      }
      return json({ ok: true, on: g.on, asof: g.asof, changed: changed.map(s => s.id), sent, raw: g.raw });
    } catch (e) { return json({ error: String((e as Error).message || e) }, 500); }
  }
  const v = await cfg("gold_gauge");
  return json(v || { error: "아직 계산 전" }, v ? 200 : 503, { "Cache-Control": "public, max-age=600" });
});
