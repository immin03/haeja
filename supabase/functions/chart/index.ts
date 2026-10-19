// 종목 상세 차트 데이터: 로그인 여부와 상관없이 호출 (verify_jwt 끔)
// 요청: POST {symbol: "005930.KS"}  응답: {ticker, sym, cur, price, prevClose, daily, weekly, monthly, hi52, lo52, ...}
// 하루 한 번만 야후에서 받아 docs(charts, 운영자 소유)에 저장해 두고, 같은 날엔 저장본을 돌려준다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const kstDate = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
type Pt = [string, number];
type Bar = { d: string; c: number; h: number | null; l: number | null; v: number | null };

async function yahoo(sym: string, range: string, interval: string) {
  try {
    const r = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=${range}&interval=${interval}`, {
      headers: { "User-Agent": "Mozilla/5.0 (valuenote)" },
    });
    if (!r.ok) return null;
    const j = await r.json();
    const res = j?.chart?.result?.[0];
    if (!res) return null;
    const ts: number[] = res.timestamp || [];
    const q = res.indicators?.quote?.[0] || {};
    const off = (res.meta?.gmtoffset ?? 0) * 1000;
    const bars: Bar[] = [];
    ts.forEach((t, i) => {
      const c = q.close?.[i];
      if (typeof c !== "number" || !isFinite(c)) return;
      const n = (x: unknown) => (typeof x === "number" && isFinite(x) ? x : null);
      bars.push({ d: new Date(t * 1000 + off).toISOString().slice(0, 10), c: Math.round(c * 10000) / 10000, h: n(q.high?.[i]), l: n(q.low?.[i]), v: n(q.volume?.[i]) });
    });
    const m = res.meta || {};
    if (typeof m.regularMarketPrice === "number" && m.regularMarketTime) {
      const d = new Date(m.regularMarketTime * 1000 + off).toISOString().slice(0, 10);
      const last = bars[bars.length - 1];
      if (!last || last.d < d) bars.push({ d, c: m.regularMarketPrice, h: null, l: null, v: null });
      else if (last.d === d) last.c = m.regularMarketPrice;
    }
    return bars.length ? { bars, meta: m } : null;
  } catch (_) {
    return null;
  }
}
async function yahooKR(sym: string, range: string, interval: string) {
  let p = await yahoo(sym, range, interval);
  if (!p && /^\d{6}\.KS$/.test(sym)) p = await yahoo(sym.replace(".KS", ".KQ"), range, interval);
  return p;
}

function build(sym: string, d2y: { bars: Bar[]; meta: any }, w10y: { bars: Bar[]; meta: any } | null, today: string) {
  const daily: Pt[] = d2y.bars.map((b) => [b.d, b.c]);
  const weekly: Pt[] = (w10y?.bars || []).map((b) => [b.d, b.c]);
  // 월간: 주간에서 달마다 마지막 값
  const mm: Record<string, Pt> = {};
  for (const p of weekly) mm[p[0].slice(0, 7)] = p;
  const monthly = Object.values(mm).sort((a, b) => (a[0] < b[0] ? -1 : 1));
  // 52주 최고·최저: 일간 고가·저가 (없으면 종가)
  const y = d2y.bars.slice(-252);
  let hi52: number | null = null, lo52: number | null = null, hiAt = "", loAt = "";
  for (const b of y) {
    const h = b.h ?? b.c, l = b.l ?? b.c;
    if (hi52 === null || h > hi52) { hi52 = h; hiAt = b.d; }
    if (lo52 === null || l < lo52) { lo52 = l; loAt = b.d; }
  }
  const vol = y.map((b) => b.v).filter((v): v is number => typeof v === "number");
  const avgVol = vol.length ? Math.round(vol.slice(-20).reduce((a, b) => a + b, 0) / Math.min(20, vol.length)) : null;
  const m = d2y.meta || {};
  const last = daily[daily.length - 1], prev = daily[daily.length - 2];
  return {
    sym, ticker: sym.split(".")[0].toUpperCase(), cur: m.currency ?? null, exch: m.exchangeName ?? null,
    price: last?.[1] ?? null, prevClose: prev?.[1] ?? null, priceAt: last?.[0] ?? null,
    daily: daily.slice(-520), weekly: weekly.slice(-530), monthly: monthly.slice(-130),
    hi52, lo52, hiAt, loAt, avgVol, source: "Yahoo Finance", updatedAt: today,
  };
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { ...cors, "Content-Type": "application/json" } });
  const body = await req.json().catch(() => ({}));
  const sym = String(body.symbol || "").trim().toUpperCase();
  if (!/^[A-Z0-9.=^\-]{1,20}$/.test(sym)) return json({ ok: false, error: "symbol" }, 400);
  const today = kstDate();
  const id = sym; // 같은 코드가 시장마다 다를 수 있어 야후 심볼 그대로 저장
  // 1) 오늘 저장본이 있으면 그대로
  const { data: pub } = await sb.from("docs").select("owner").eq("collection", "screen").eq("id", "meta").maybeSingle();
  const owner = pub?.owner;
  if (owner) {
    const { data: hit } = await sb.from("docs").select("data").eq("collection", "charts").eq("id", id).eq("owner", owner).maybeSingle();
    if (hit?.data?.updatedAt === today && !body.force) return json({ ok: true, cached: true, ...hit.data });
  }
  // 2) 야후: 2년 일간 + 10년 주간
  const [d2y, w10y] = await Promise.all([yahooKR(sym, "2y", "1d"), yahooKR(sym, "10y", "1wk")]);
  if (!d2y) {
    // 야후가 막히면 저장본이라도
    if (owner) {
      const { data: hit } = await sb.from("docs").select("data").eq("collection", "charts").eq("id", id).eq("owner", owner).maybeSingle();
      if (hit?.data) return json({ ok: true, cached: true, stale: true, ...hit.data });
    }
    return json({ ok: false, error: "no data" }, 502);
  }
  const doc = build(sym, d2y, w10y, today);
  if (owner) await sb.from("docs").upsert({ owner, collection: "charts", id, data: doc, updated_at: new Date().toISOString() }, { onConflict: "owner,collection,id" });
  return json({ ok: true, ...doc });
});
