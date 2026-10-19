// 매일 종가 갱신 (pg_cron이 평일 16:10, 06:40 KST에 호출)
// 1) 보유 종목·내 종목/관심 후보 현재가  2) 가격 기록(일·주·월)  3) 스크리너 전 종목 px  4) 환율
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const kstDate = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);

type Pt = [string, number];

async function chart(sym: string, range: string): Promise<Pt[] | null> {
  try {
    const r = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=${range}&interval=1d`, {
      headers: { "User-Agent": "Mozilla/5.0 (haeja-ledger)" },
    });
    if (!r.ok) return null;
    const j = await r.json();
    const res = j?.chart?.result?.[0];
    const ts: number[] = res?.timestamp || [];
    const cl: (number | null)[] = res?.indicators?.quote?.[0]?.close || [];
    const off = (res?.meta?.gmtoffset ?? 0) * 1000;
    const pts: Pt[] = [];
    ts.forEach((t, i) => {
      const v = cl[i];
      if (typeof v === "number" && isFinite(v)) pts.push([new Date(t * 1000 + off).toISOString().slice(0, 10), Math.round(v * 10000) / 10000]);
    });
    const m = res?.meta;
    if (m && typeof m.regularMarketPrice === "number" && m.regularMarketTime) {
      const d = new Date(m.regularMarketTime * 1000 + off).toISOString().slice(0, 10);
      if (!pts.length || pts[pts.length - 1][0] < d) pts.push([d, m.regularMarketPrice]);
      else if (pts[pts.length - 1][0] === d) pts[pts.length - 1][1] = m.regularMarketPrice;
    }
    return pts.length ? pts : null;
  } catch (_) {
    return null;
  }
}
async function chartKR(sym: string, range: string) {
  let p = await chart(sym, range);
  if (!p && /^\d{6}\.KS$/.test(sym)) p = await chart(sym.replace(".KS", ".KQ"), range);
  return p;
}
async function pool<T, R>(items: T[], n: number, fn: (x: T) => Promise<R>): Promise<R[]> {
  const out: R[] = new Array(items.length); let i = 0;
  await Promise.all(Array.from({ length: n }, async () => { while (i < items.length) { const k = i++; out[k] = await fn(items[k]); } }));
  return out;
}

function yfSymbol(h: any, companies: Record<string, any>) {
  const c = companies[h.companyId || ""];
  if (c?.yf) return c.yf;
  const t = String(h.ticker || "").trim().toUpperCase(), m = h.market || "KR";
  if (m === "US") return t; if (m === "JP") return t + ".T"; if (m === "HK") return t.padStart(4, "0") + ".HK";
  if (m === "CN") return t + (t.startsWith("6") ? ".SS" : ".SZ"); if (m === "KOSDAQ") return t + ".KQ";
  return t + ".KS";
}
const isoWeek = (d: string) => { const x = new Date(d + "T00:00:00Z"); const day = (x.getUTCDay() + 6) % 7; x.setUTCDate(x.getUTCDate() - day + 3); const y = x.getUTCFullYear(); const f = new Date(Date.UTC(y, 0, 4)); return y + "-" + Math.round(((x.getTime() - f.getTime()) / 864e5 - 3 + ((f.getUTCDay() + 6) % 7)) / 7); };

function mergeSeries(doc: any, pts: Pt[], today: string) {
  let daily: Pt[] = doc.daily || [], weekly: Pt[] = doc.points || [], monthly: Pt[] = doc.monthly || [];
  const have = new Set(daily.map((p) => p[0]));
  for (const p of pts.slice(-30)) if (!have.has(p[0])) daily.push(p);
  daily = daily.sort((a, b) => a[0] < b[0] ? -1 : 1).slice(-130);
  for (const [d, v] of pts.slice(-30)) {
    const lw = weekly[weekly.length - 1];
    if (lw && isoWeek(lw[0]) === isoWeek(d)) { if (d >= lw[0]) weekly[weekly.length - 1] = [d, v]; }
    else if (!lw || d > lw[0]) weekly.push([d, v]);
    const lm = monthly[monthly.length - 1];
    if (lm && lm[0].slice(0, 7) === d.slice(0, 7)) { if (d >= lm[0]) monthly[monthly.length - 1] = [d, v]; }
    else if (!lm || d > lm[0]) monthly.push([d, v]);
  }
  if (weekly.length < 10) { const w: Record<string, Pt> = {}; for (const p of pts) w[isoWeek(p[0])] = p; weekly = Object.values(w).sort((a, b) => a[0] < b[0] ? -1 : 1); }
  if (monthly.length < 6) { const m: Record<string, Pt> = {}; for (const p of pts) m[p[0].slice(0, 7)] = p; monthly = Object.values(m).sort((a, b) => a[0] < b[0] ? -1 : 1); }
  return { ...doc, daily, points: weekly.slice(-260), monthly: monthly.slice(-120), freq: "W", source: "Yahoo Finance", updatedAt: today };
}

async function load(col: string) {
  const { data, error } = await sb.from("docs").select("id,data,owner").eq("collection", col);
  if (error) throw error;
  return data as { id: string; data: any; owner: string }[];
}

Deno.serve(async (_req: Request) => {
  const today = kstDate();
  try {
    const [holdings, comps, prices, screen] = await Promise.all(["holdings", "companies", "prices", "screen"].map(load));
    // 공용 데이터(가격 기록·스크리너)의 주인 = 운영자. 사용자별 데이터(보유·기업·설정·알림)는 각자 주인에게 쓴다.
    const pub = screen.find((r) => r.id === "meta")?.owner || (holdings[0] || comps[0])?.owner;
    if (!pub) return Response.json({ ok: false, msg: "데이터 없음" });
    const owners = [...new Set([...holdings.map((r) => r.owner), ...comps.map((r) => r.owner), pub])];
    const key = (o: string, id: string) => o + "|" + id;
    const companies: Record<string, any> = Object.fromEntries(comps.map((r) => [key(r.owner, r.id), r.data]));
    const compsOf = (o: string) => Object.fromEntries(comps.filter((r) => r.owner === o).map((r) => [r.id, r.data]));
    const heldSym: Record<string, string> = {};
    for (const h of holdings) if (String(h.data.ticker || "").trim()) heldSym[key(h.owner, h.id)] = yfSymbol(h.data, compsOf(h.owner));
    const compSym: Record<string, string> = {};
    for (const r of comps) {
      const c = r.data;
      const inScope = c.watch || c.pinned || (c.thesis?.memo || "").trim() || holdings.some((h) => h.owner === r.owner && h.data.companyId === r.id);
      if (inScope && (c.yf || c.ticker)) compSym[key(r.owner, r.id)] = c.yf || c.ticker;
    }
    const fxSym: Record<string, string> = { fx: "KRW=X", fxJPY: "JPYKRW=X", fxCNY: "CNYKRW=X", fxHKD: "HKDKRW=X" };
    const histSyms = [...new Set([...Object.values(heldSym), ...Object.values(compSym), ...Object.values(fxSym)])];
    const hist: Record<string, Pt[]> = {};
    await pool(histSyms, 8, async (s) => { const p = await chartKR(s, "2y"); if (p) hist[s] = p; });
    const last = (s: string) => hist[s]?.[hist[s].length - 1];

    const rows: any[] = [];
    const put = (owner: string, collection: string, id: string, data: any) => rows.push({ owner, collection, id, data, updated_at: new Date().toISOString() });
    // 종가와 직전 거래일 종가를 함께 저장한다. 직전 종가를 그대로 두면 며칠 전 값과 비교돼 하루 변동이 크게 틀어진다
    for (const h of holdings) { const pts = hist[heldSym[key(h.owner, h.id)]]; const p = pts?.[pts.length - 1]; if (p) put(h.owner, "holdings", h.id, { ...h.data, price: p[1], prevClose: pts.length >= 2 ? pts[pts.length - 2][1] : (h.data.prevClose ?? null), priceAt: p[0], updatedAt: today }); }
    // 보유 종목 하루 5% 이상 움직이면 알림 (같은 날 한 번)
    const alertRows: any[] = [];
    for (const h of holdings) {
      const pts = hist[heldSym[key(h.owner, h.id)]]; if (!pts || pts.length < 2) continue;
      const [d1, v1] = pts[pts.length - 1], v0 = pts[pts.length - 2][1];
      const chg = (v1 / v0 - 1) * 100; if (Math.abs(chg) < 5) continue;
      const name = String(h.data.name || h.data.ticker).replace(/\s*\(.*\)$/, "");
      const cur = h.data.currency === "USD" ? "$" + v1.toFixed(2) : Math.round(v1).toLocaleString("ko-KR") + "원";
      alertRows.push({ collection: "alerts", id: `move-${h.id}-${d1}`, owner: h.owner, updated_at: new Date().toISOString(), data: {
        at: new Date().toISOString(), level: chg <= -7 ? "urgent" : chg < 0 ? "warn" : "info",
        title: `${name} ${chg > 0 ? "+" : ""}${chg.toFixed(1)}%`, body: `${d1} 종가 ${cur}. ${chg < 0 ? "급락 이유와 매도 조건을 확인하세요." : "내재가치 대비 가격을 확인하세요."}`,
        link: { co: h.data.companyId || null, tab: "portfolio" }, read: false, source: "종가 갱신" } });
    }
    for (const [k, s] of Object.entries(compSym)) { const p = last(s); if (!p) continue; const [o, cid] = k.split("|"); put(o, "companies", cid, { ...companies[k], price: p[1] }); }
    // 관심 종목이 적정 매수가 아래로 내려오면 알림 (화면을 열지 않아도). 적정 매수가(buyAt)는 화면이 판정할 때 회사 문서에 적어 둔다.
    // 알림 번호는 화면과 같은 buy-<회사>-<월> 이라 한 달에 한 번만 간다.
    const month = today.slice(0, 7);
    for (const [k, s] of Object.entries(compSym)) {
      const c = companies[k], ba = c?.buyAt; if (!ba || typeof ba.v !== "number") continue;
      const [o, cid] = k.split("|");
      if (holdings.some((h) => h.owner === o && h.data.companyId === cid)) continue;
      const p = last(s); if (!p || p[1] > ba.v) continue;
      const name = String(c.name || c.ticker).replace(/\s*\(.*\)$/, "");
      const ys = String(c.yf || c.ticker || "");
      const cur = c.currency || (/\.(KS|KQ)$|^\d{6}$/.test(ys) ? "KRW" : /\.T$/.test(ys) ? "JPY" : /\.HK$/.test(ys) ? "HKD" : /\.(SS|SZ)$/.test(ys) ? "CNY" : "USD");
      const f = (v: number) => cur === "USD" ? "$" + v.toFixed(2) : cur === "KRW" ? Math.round(v).toLocaleString("ko-KR") + "원" : v.toLocaleString("ko-KR") + " " + cur;
      alertRows.push({ collection: "alerts", id: `buy-${cid}-${month}`, owner: o, updated_at: new Date().toISOString(), data: {
        at: new Date().toISOString(), level: "good", title: `${name} 적정 매수가 도달`,
        body: `${p[0]} 종가 ${f(p[1])}, 적정 매수가 ${f(ba.v)} 아래로 내려왔습니다. 판단 근거와 매도 조건을 다시 확인하세요.`,
        link: { co: cid }, read: false, source: "종가 갱신" } });
    }
    // 가격 기록은 공용(운영자 소유) 한 벌로 모은다. 모든 사용자가 읽는다.
    const pmap: Record<string, any> = Object.fromEntries(prices.filter((r) => r.owner === pub).map((r) => [r.id, r.data]));
    for (const s of new Set([...Object.values(heldSym), ...Object.values(compSym)])) {
      if (!hist[s]) continue;
      const k = s.split(".")[0].toUpperCase();
      put(pub, "prices", k, mergeSeries(pmap[k] || { ticker: k }, hist[s], today));
    }

    // 스크리너 현재가 (공용)
    let nScreen = 0;
    const scr = screen.filter((r) => r.owner === pub && Array.isArray(r.data.rows));
    const tickers = [...new Set(scr.flatMap((r) => r.data.rows.map((x: any) => x.t).filter(Boolean)))] as string[];
    const px: Record<string, number> = {};
    await pool(tickers, 10, async (t) => { const p = await chart(t, "5d"); if (p) px[t] = p[p.length - 1][1]; });
    for (const r of scr) {
      const d = { ...r.data, rows: r.data.rows.map((x: any) => (x.t in px ? (nScreen++, { ...x, px: px[x.t] }) : x)), pxAt: today };
      put(pub, "screen", r.id, d);
    }

    // 환율: 사용자별 설정에 넣는다. 설정은 쓰기 직전에 다시 읽는다 (그사이 바꾼 예수금을 덮어쓰지 않도록)
    const fresh = await load("settings");
    const fxAt = new Date(Date.now() + 9 * 3600e3).toISOString().slice(5, 16).replace("-", "/").replace("T", " ");
    for (const o of owners) {
      const st = { ...(fresh.find((r) => r.owner === o && r.id === "main")?.data || {}) };
      if (o !== pub && !fresh.some((r) => r.owner === o && r.id === "main")) continue; // 설정이 없는 사용자는 건너뜀
      for (const [k, s] of Object.entries(fxSym)) { const p = last(s); if (p) st[k] = Math.round(p[1] * 10000) / 10000; }
      st.fxAt = fxAt;
      put(o, "settings", "main", st);
    }

    // 알림은 새로 생길 때만 넣는다 (이미 있으면 건드리지 않아 중복 푸시가 없다)
    if (alertRows.length) { const { error } = await sb.from("docs").upsert(alertRows, { onConflict: "owner,collection,id", ignoreDuplicates: true }); if (error) throw error; }
    for (let i = 0; i < rows.length; i += 50) {
      const { error } = await sb.from("docs").upsert(rows.slice(i, i + 50), { onConflict: "owner,collection,id" });
      if (error) throw error;
    }
    return Response.json({ ok: true, date: today, owners: owners.length, writes: rows.length, held: Object.keys(heldSym).length, hist: Object.keys(hist).length, screen: nScreen + "/" + tickers.length, alerts: alertRows.length });
  } catch (e) {
    return Response.json({ ok: false, error: String((e as Error)?.message || e) }, { status: 500 });
  }
});
