// 주요 일정 알림: 매일 저녁(한국 시각 18시) pg_cron이 호출한다.
// 1) 모든 사용자의 보유·관심 종목 실적 발표일을 야후에서 모아 공용 문서 fx/earnings 에 저장한다.
// 2) 일정 알림을 켠 사용자(settings.main.calAlert === true)에게 "내일" 있는 일정을 알림 문서로 넣는다.
//    - 경제 일정: fx/radar 의 upcoming (주간 칼럼 작업이 채움)
//    - 실적 발표: 그 사용자의 보유·관심 종목
//    알림 번호가 같으면 다시 넣지 않으므로 같은 일정은 한 번만 간다. 푸시는 docs 트리거가 notify 함수로 보낸다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36";
const kst = (offsetDays = 0) => new Date(Date.now() + 9 * 3600e3 + offsetDays * 864e5).toISOString().slice(0, 10);

function yfSymbol(h: any, companies: Record<string, any>) {
  const c = companies[h.companyId || ""];
  if (c?.yf) return c.yf;
  const t = String(h.ticker || "").trim().toUpperCase(), m = h.market || "KR";
  if (m === "US") return t; if (m === "JP") return t + ".T"; if (m === "HK") return t.padStart(4, "0") + ".HK";
  if (m === "CN") return t + (t.startsWith("6") ? ".SS" : ".SZ"); if (m === "KOSDAQ") return t + ".KQ";
  return t + ".KS";
}
async function load(col: string) {
  const { data, error } = await sb.from("docs").select("id,data,owner").eq("collection", col);
  if (error) throw error;
  return data as { id: string; data: any; owner: string }[];
}
async function pool<T>(xs: T[], n: number, f: (x: T) => Promise<void>) {
  let i = 0; await Promise.all(Array.from({ length: Math.min(n, xs.length) }, async () => { while (i < xs.length) await f(xs[i++]); }));
}

/* 야후 인증(쿠키 + crumb). 실패하면 null → 실적 일정은 건너뛰고 경제 일정 알림만 보낸다. */
async function yahooAuth(): Promise<{ cookie: string; crumb: string } | null> {
  try {
    const r = await fetch("https://fc.yahoo.com", { headers: { "User-Agent": UA }, redirect: "manual" });
    const raw = r.headers.get("set-cookie") || "";
    const cookie = raw.split(/,(?=[^;]+=)/).map((s) => s.split(";")[0].trim()).filter(Boolean).join("; ");
    if (!cookie) return null;
    const c = await fetch("https://query2.finance.yahoo.com/v1/test/getcrumb", { headers: { "User-Agent": UA, Cookie: cookie } });
    const crumb = (await c.text()).trim();
    if (!c.ok || !crumb || crumb.length > 40 || /[<{ ]/.test(crumb)) return null;
    return { cookie, crumb };
  } catch (_) { return null; }
}
/* 다음 실적 발표일(YYYY-MM-DD, 미국 기업은 현지 날짜). quote 한 번에 여러 종목을 묻는다. */
async function earnings(syms: string[], auth: { cookie: string; crumb: string }) {
  const out: Record<string, { date: string; name: string; est: boolean }> = {};
  const chunks: string[][] = []; for (let i = 0; i < syms.length; i += 40) chunks.push(syms.slice(i, i + 40));
  await pool(chunks, 3, async (ch) => {
    try {
      const u = `https://query2.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(ch.join(","))}&fields=earningsTimestamp,earningsTimestampStart,earningsTimestampEnd,isEarningsDateEstimate,shortName,longName&crumb=${encodeURIComponent(auth.crumb)}`;
      const r = await fetch(u, { headers: { "User-Agent": UA, Cookie: auth.cookie } });
      const rows = (await r.json())?.quoteResponse?.result || [];
      for (const q of rows) {
        const ts = q.earningsTimestampStart || q.earningsTimestamp; if (!ts) continue;
        const off = (q.gmtOffSetMilliseconds ?? 0);
        const date = new Date(ts * 1000 + off).toISOString().slice(0, 10);
        out[String(q.symbol).toUpperCase()] = { date, name: q.shortName || q.longName || q.symbol, est: !!q.isEarningsDateEstimate || (!!q.earningsTimestampEnd && q.earningsTimestampEnd !== q.earningsTimestampStart) };
      }
    } catch (_) { /* 한 묶음 실패는 무시 */ }
  });
  return out;
}

Deno.serve(async (req: Request) => {
  const body = await req.json().catch(() => ({}));
  try {
    const { data: cfg } = await sb.from("app_config").select("value").eq("key", "publisher").maybeSingle();
    const pub = cfg?.value as string; if (!pub) return Response.json({ error: "no publisher" }, { status: 500 });
    const [holdings, comps, settings] = await Promise.all(["holdings", "companies", "settings"].map(load));

    // 사용자별 보유·관심 종목 심볼
    const compsBy: Record<string, Record<string, any>> = {};
    for (const r of comps) (compsBy[r.owner] ||= {})[r.id] = r.data;
    const mine: Record<string, Map<string, string>> = {}; // owner → 심볼 → 이름
    const add = (o: string, sym: string, name: string) => { if (!sym) return; (mine[o] ||= new Map()).set(sym.toUpperCase(), String(name || sym).replace(/\s*\(.*\)$/, "")); };
    for (const h of holdings) if (String(h.data.ticker || "").trim()) add(h.owner, yfSymbol(h.data, compsBy[h.owner] || {}), h.data.name || h.data.ticker);
    for (const r of comps) {
      const c = r.data; if (c.kind && c.kind !== "stock") continue;
      const inScope = c.watch === true || c.pinned || (c.thesis?.memo || "").trim();
      if (inScope && (c.yf || c.ticker)) add(r.owner, c.yf || c.ticker, c.name || c.ticker);
    }
    const allSyms = [...new Set(Object.values(mine).flatMap((m) => [...m.keys()]))];

    // 실적 발표일 수집 → 공용 문서
    const { data: oldDoc } = await sb.from("docs").select("data").eq("owner", pub).eq("collection", "fx").eq("id", "earnings").maybeSingle();
    let items: Record<string, any> = (oldDoc?.data as any)?.items || {};
    const auth = allSyms.length ? await yahooAuth() : null;
    let got = 0;
    if (auth) {
      const fresh = await earnings(allSyms, auth); got = Object.keys(fresh).length;
      items = { ...items, ...fresh };
    }
    // 지난 일정(7일 넘게 지난 것)은 정리
    const cut = kst(-7);
    items = Object.fromEntries(Object.entries(items).filter(([_, v]: any) => v?.date >= cut));
    await sb.from("docs").upsert({ owner: pub, collection: "fx", id: "earnings", data: { items, at: new Date().toISOString(), yahoo: !!auth }, updated_at: new Date().toISOString() }, { onConflict: "owner,collection,id" });

    // 내일 일정 알림
    const D1 = body.date || kst(1);
    const { data: rd } = await sb.from("docs").select("data").eq("owner", pub).eq("collection", "fx").eq("id", "radar").maybeSingle();
    const macro = (((rd?.data as any)?.upcoming) || []).filter((u: any) => u?.date === D1 && u?.event);
    const optIn = settings.filter((s) => s.id === "main" && s.data?.calAlert === true).map((s) => s.owner);
    const hash = (s: string) => { let h = 0; for (const ch of s) h = (h * 31 + ch.charCodeAt(0)) | 0; return (h >>> 0).toString(36); };
    const rows: any[] = []; const now = new Date().toISOString();
    for (const o of optIn) {
      for (const u of macro) rows.push({ owner: o, collection: "alerts", id: `cal-m-${D1}-${hash(u.event)}`, updated_at: now, data: {
        at: now, level: "info", title: `내일 ${u.event}`, body: u.why ? `${u.why}. 경제 레이더에서 지금 신호를 확인하세요.` : "경제 레이더에서 지금 신호를 확인하세요.",
        link: { tab: "radar" }, read: false, source: "일정 알림" } });
      for (const [sym, name] of mine[o] || []) {
        const e = items[sym]; if (!e || e.date !== D1) continue;
        rows.push({ owner: o, collection: "alerts", id: `cal-e-${sym}-${D1}`, updated_at: now, data: {
          at: now, level: "info", title: `내일 ${name} 실적 발표`, body: `${e.est ? "예정일 기준입니다. " : ""}발표 뒤 매출·이익이 투자 판단 근거와 맞는지 확인하세요.`,
          link: { tab: "radar" }, read: false, source: "일정 알림" } });
      }
    }
    let inserted = 0;
    if (rows.length) {
      const { data: ins, error } = await sb.from("docs").upsert(rows, { onConflict: "owner,collection,id", ignoreDuplicates: true }).select("id");
      if (error) throw error; inserted = ins?.length || 0;
    }
    return Response.json({ ok: true, date: D1, symbols: allSyms.length, yahoo: !!auth, earnings: got, optIn: optIn.length, macro: macro.length, alerts: inserted });
  } catch (e) {
    return Response.json({ error: String((e as Error)?.message || e) }, { status: 500 });
  }
});
