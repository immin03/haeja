// 관심 후보 자동 선정 (매주 월요일 07:00 KST, pg_cron) — 화면과 똑같은 점수 코드(scoring.js)로 계산한다.
// 규칙: 버핏 근접도 70점 이상, 감점 신호 없음, 데이터 신뢰도 낮음 아님, 보유 종목 아님, 탈락·구조적 훼손 우려 아님,
//       점수순으로 시장마다 최대 4곳, 전체 12곳. 직접 고른(☆·메모) 회사의 관심 표시는 건드리지 않는다.
// {dry:true} 이면 저장하지 않고 결과만 돌려준다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";
// @ts-ignore 화면 코드를 그대로 옮긴 JS
import { scoreRow, grpOf, WARN_FLAGS, setSettings } from "./scoring.js";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const kst = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
const MIN_B = 70, PER_MKT = 4, TOTAL = 12;
const RULE = `기준: ${MIN_B}점 이상, 탈락·감점 없음, 데이터 신뢰도 양호, 시장당 최대 ${PER_MKT}곳, 상위 ${TOTAL}곳`;
const nk = (s: unknown) => String(s || "").toUpperCase().replace(/\.(KS|KQ|T|HK|SS|SZ)$/, "").replace(/^0+(?=\d{4}$)/, "");

async function load(col: string) {
  const { data, error } = await sb.from("docs").select("id,data,owner").eq("collection", col);
  if (error) throw error; return (data || []) as { id: string; data: any; owner: string }[];
}

Deno.serve(async (req: Request) => {
  const body = await req.json().catch(() => ({}));
  try {
    const D = kst();
    const [screen, settings, comps, holds] = await Promise.all(["screen", "settings", "companies", "holdings"].map(load));
    const owner = screen.find((r) => r.id === "meta")?.owner; if (!owner) return Response.json({ ok: false, msg: "screen 없음" });
    const st = settings.find((r) => r.id === "main")?.data || {}; setSettings(st);
    const rows = screen.filter((r) => r.id.startsWith("chunk-")).sort((a, b) => a.id.localeCompare(b.id)).flatMap((r) => r.data?.rows || []);
    const compOf = (r: any) => comps.find((c) => (c.data.yf && c.data.yf === r.t) || nk(c.data.ticker) === nk(r.code || r.t));
    const heldIds = new Set(holds.map((h) => h.data.companyId).filter(Boolean));
    const heldTk = new Set(holds.map((h) => nk(h.data.ticker)).filter(Boolean));

    const scored = rows.map((r: any) => ({ r, sc: scoreRow(r, null, st.reqMOS ?? 30) }));
    const out = (why: string, r: any) => ({ t: r.t, n: r.n, why });
    const rejected: any[] = []; const cands: any[] = [];
    for (const { r, sc } of scored) {
      if (typeof sc.b !== "number" || sc.b < MIN_B) continue;
      const pen = (sc.flags || []).filter((f: string) => !WARN_FLAGS.has(f));
      if (pen.length) { rejected.push(out("감점 신호: " + pen.join(", "), r)); continue; }
      if (r.dataConf === "low") { rejected.push(out("데이터 신뢰도 낮음", r)); continue; }
      const c = compOf(r);
      if ((c && heldIds.has(c.id)) || heldTk.has(nk(r.code || r.t))) { rejected.push(out("보유 중", r)); continue; }
      const q = c?.data?.qual || {};
      if (c && (["lev", "etf"].includes(c.data.kind) || q.circle === false || q.governance === 0)) { rejected.push(out("탈락 조건", r)); continue; }
      if (c?.data?.dropCheck?.verdict === "구조적 훼손 우려") { rejected.push(out("구조적 훼손 우려", r)); continue; }
      cands.push({ r, sc, c });
    }
    cands.sort((a, b) => b.sc.b - a.sc.b);
    const per: Record<string, number> = {}; const pick: any[] = [];
    for (const x of cands) { const g = grpOf(x.r.m); if ((per[g] || 0) >= PER_MKT) continue; per[g] = (per[g] || 0) + 1; pick.push(x); if (pick.length >= TOTAL) break; }

    const writes: any[] = []; const now = new Date().toISOString();
    const added: string[] = [], kept: string[] = [], removed: string[] = [];
    const pickIds = new Set<string>();
    pick.forEach((x, i) => {
      const r = x.r, rank = i + 1;
      const w = { watch: true, watchAt: D, watchRank: rank, watchWhy: `스크리너 근접도 ${x.sc.b}점 · 전체 ${rank}위 (${RULE})` };
      if (x.c) {
        pickIds.add(x.c.id); (x.c.data.watch === true ? kept : added).push(r.n);
        writes.push({ collection: "companies", id: x.c.id, owner, updated_at: now, data: { ...x.c.data, ...w, watchOut: null } });
      } else {
        const id = "w-" + String(r.code || r.t).replace(/[^A-Za-z0-9]/g, "").toUpperCase(); pickIds.add(id); added.push(r.n);
        writes.push({ collection: "companies", id, owner, updated_at: now, data: {
          name: r.n, ticker: r.code || r.t, yf: r.t, market: grpOf(r.m), kind: "stock", sector: r.ind || r.s || "", price: r.px,
          fin: r.fin || {}, val: r.val || {}, finSector: !!r.fin_sector, holdco: !!r.holdco, dataConf: r.dataConf || null,
          qual: {}, thesis: { memo: "" }, pinned: false, source: `스크리너 자동 수집 ${D}`, createdAt: D, ...w } });
      }
    });
    for (const c of comps) {
      if (c.data.watch !== true || pickIds.has(c.id)) continue;
      if (c.data.pinned || String(c.data.thesis?.memo || "").trim()) continue; // 직접 고른 회사는 그대로
      removed.push(c.data.name);
      writes.push({ collection: "companies", id: c.id, owner, updated_at: now, data: { ...c.data, watch: false, watchOut: { at: D, why: `이번 재선정에서 빠짐 (${RULE})` } } });
    }
    const summary = { date: D, picked: pick.map((x, i) => ({ rank: i + 1, n: x.r.n, t: x.r.t, m: grpOf(x.r.m), b: x.sc.b })), added, kept, removed,
      candidates: cands.length, rejectedTop: rejected.slice(0, 15) };
    if (body.dry) return Response.json({ ok: true, dry: true, ...summary });

    for (let i = 0; i < writes.length; i += 20) { const { error } = await sb.from("docs").upsert(writes.slice(i, i + 20)); if (error) throw error; }
    if (added.length || removed.length) {
      const msg = [added.length ? `추가 ${added.slice(0, 4).join(", ")}${added.length > 4 ? ` 외 ${added.length - 4}곳` : ""}` : "", removed.length ? `제외 ${removed.length}곳` : ""].filter(Boolean).join(" · ");
      await sb.from("docs").upsert({ collection: "alerts", id: "watch-" + D, owner, updated_at: now, data: {
        at: now, level: "info", title: "관심 후보 재선정", body: msg.slice(0, 60), link: { tab: "companies" }, read: false, source: "관심 후보 선정" } }, { onConflict: "collection,id", ignoreDuplicates: true });
    }
    return Response.json({ ok: true, ...summary });
  } catch (e) {
    return Response.json({ ok: false, error: String((e as Error)?.message || e) }, { status: 500 });
  }
});
