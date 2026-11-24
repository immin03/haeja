// gauge-news (2026-11-24 대표: "계기판이 바뀐 날, 밸류노트에 들어가자마자 팝업 — '11월 24일 07시 기준 무엇이 바뀌었는지', 이틀 동안, 다시 보지 않기")
// GET : 최근 48시간 안에 신호가 바뀐 계기판 목록 (공개, 앱 첫 화면 팝업이 읽는다)
//   반도체(semi_gauge_event) · 금(gold_gauge_event) — 두 계기판 함수가 신호가 바뀔 때 app_config 에 남기는 기록을 그대로 읽는다.
//   계기판 계산·알림 발송은 semi-gauge / gold-gauge 함수가 하고, 이 함수는 읽기만 한다 (쓰기 없음).
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";
const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "content-type", "Access-Control-Allow-Methods": "GET, OPTIONS" };
const WINDOW = 48 * 3600e3;
const G = [
  { id: "semi", name: "반도체 바닥 계기판", gauge: "semi_gauge", event: "semi_gauge_event", url: "/semi?from=pop" },
  { id: "gold", name: "금 바닥 계기판", gauge: "gold_gauge", event: "gold_gauge_event", url: "/semi?tab=gold&from=pop" },
];
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const keys = G.flatMap(g => [g.gauge, g.event]);
  const { data } = await sb.from("app_config").select("key, value").in("key", keys);
  const v = Object.fromEntries((data || []).map((r: any) => [r.key, r.value]));
  const now = Date.now(), items: unknown[] = [];
  for (const g of G) {
    const ev = v[g.event], cur = v[g.gauge];
    if (!ev?.at || !Array.isArray(ev.changed) || !ev.changed.length) continue;
    const t = Date.parse(ev.at);
    if (!isFinite(t) || now - t > WINDOW || t > now + 600e3) continue;
    const sig = (cur?.signals || []) as any[];
    const changed = ev.changed.map((id: string) => {
      const s = sig.find(x => x.id === id);
      return s ? { id, name: s.name, on: !!s.on, now: s.now } : { id, name: id, on: null, now: "" };
    });
    items.push({ key: `${g.id}-${ev.asof || ev.at}`, gauge: g.id, name: g.name, url: g.url, at: ev.at, asof: ev.asof || "", from: ev.from, to: ev.to, total: cur?.total || 5, current: cur?.on ?? ev.to, changed });
  }
  items.sort((a: any, b: any) => String(b.at).localeCompare(String(a.at)));
  return new Response(JSON.stringify({ items, checkedAt: new Date().toISOString() }), { headers: { ...cors, "Content-Type": "application/json; charset=utf-8", "Cache-Control": "public, max-age=300" } });
});
