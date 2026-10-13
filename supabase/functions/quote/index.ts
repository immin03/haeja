// 시세 조회: 로그인한 사용자만 호출 (verify_jwt). 화면이 열려 있을 때 보유 종목·환율을 가져온다.
// 요청: POST {symbols: ["000270.KS","SOXL","KRW=X"]}  응답: {"000270.KS": {price, prev, cur, time}, ...}
import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

async function one(sym: string) {
  try {
    const r = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=5d&interval=1d`, {
      headers: { "User-Agent": "Mozilla/5.0 (haeja-ledger)" },
    });
    if (!r.ok) return null;
    const j = await r.json();
    const m = j?.chart?.result?.[0]?.meta;
    if (!m || typeof m.regularMarketPrice !== "number") return null;
    return {
      price: m.regularMarketPrice,
      prev: (() => { const c = (j?.chart?.result?.[0]?.indicators?.quote?.[0]?.close || []).filter((v: unknown) => typeof v === "number"); return c.length >= 2 ? c[c.length - 2] : (m.chartPreviousClose ?? null); })(),
      cur: m.currency ?? null,
      time: m.regularMarketTime ? new Date(m.regularMarketTime * 1000).toISOString() : null,
    };
  } catch (_) {
    return null;
  }
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const body = await req.json().catch(() => ({}));
  const syms: string[] = (Array.isArray(body.symbols) ? body.symbols : [])
    .map((s: unknown) => String(s).trim())
    .filter((s: string) => /^[A-Za-z0-9.=^\-]{1,20}$/.test(s))
    .slice(0, 40);
  const out: Record<string, unknown> = {};
  await Promise.all(syms.map(async (s) => {
    let q = await one(s);
    if (!q && /^\d{6}\.KS$/.test(s)) q = await one(s.replace(".KS", ".KQ"));
    if (q) out[s] = q;
  }));
  return new Response(JSON.stringify(out), { headers: { ...cors, "Content-Type": "application/json" } });
});
