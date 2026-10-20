// 맞춤 푸시 (pg_cron: 매일 08:40 KST 전체, 19:10 KST 칼럼·큰 변화만)
// 알림을 켠 사용자마다 "지금 알아 두면 좋은 것" 하나만 골라 푸시한다. 나머지는 알림함에만 쌓는다(push:false).
//   1) 관심 회사 큰 변화  : 사용자가 본 회사(interests)의 저평가 폭이 지난번 알림보다 8%p 이상 바뀌었거나, 저평가 구간(25% 이상)에 새로 들어옴
//   2) 새 칼럼            : 운영자 칼럼(trends/col-*)이 3일 안에 새로 올라왔는데 아직 안 보낸 경우
//   3) 새로 싸진 회사     : 오늘 처음 적정 주가보다 25% 이상 싸진 회사(종합 60점·재무 50점 이상), 이틀에 한 번까지
//   4) 관심 회사 근황     : 1~3이 없으면 최근 본 회사 하나의 지금 숫자 (사흘에 한 번, 한 회사는 7일에 한 번)
// 하루 푸시 상한 2회(다른 알림 포함), 보유 종목·데모 계정 제외. {dry:true} 면 저장하지 않고 고른 결과만 돌려준다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const kst = (ms = Date.now()) => new Date(ms + 9 * 3600e3).toISOString().slice(0, 10);
const slugOf = (t: unknown) => String(t || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const nk = (s: unknown) => String(s || "").toUpperCase().replace(/\.(KS|KQ|T|HK|SS|SZ)$/, "").replace(/^0+(?=\d{4}$)/, "");
const daysSince = (iso?: string) => (iso ? (Date.now() - Date.parse(iso)) / 864e5 : 1e9);
type Row = [string, number | null, number | null, number | null, string, number | null, string];

// 받침에 따라 은/는, 이/가
const jo = (w: string, a: string, b: string) => { const c = w.charCodeAt(w.length - 1); if (c < 0xac00 || c > 0xd7a3) return w + b; return w + ((c - 0xac00) % 28 ? a : b); };
// 저평가 폭(mos) → 사람이 읽는 문장
function gap(mos: number | null) {
  if (mos === null) return "적정 주가의 2배가 넘는 가격에 거래되고 있습니다";
  if (mos >= 0) return `적정 주가보다 ${Math.round(mos)}% 쌉니다. 적정 주가까지 상승 여력은 +${Math.round(100 / (100 - mos) * 100 - 100)}%입니다`;
  return `적정 주가보다 ${Math.round(-mos)}% 높은 가격에 거래되고 있습니다`;
}
const coUrl = (code: string, name: string) => `/?co=${encodeURIComponent(code)}&q=${encodeURIComponent(name)}&from=push`;

async function load(col: string, owners?: string[]) {
  let q = sb.from("docs").select("id,data,owner,updated_at").eq("collection", col);
  if (owners) q = q.in("owner", owners);
  const { data, error } = await q; if (error) throw error;
  return (data || []) as { id: string; data: any; owner: string; updated_at: string }[];
}
async function cfg(key: string) { const { data } = await sb.from("app_config").select("value").eq("key", key).maybeSingle(); return data?.value ?? null; }
async function setCfg(key: string, value: unknown) { await sb.from("app_config").upsert({ key, value }); }

Deno.serve(async (req: Request) => {
  const body = await req.json().catch(() => ({}));
  const evening = body.mode === "evening", dry = !!body.dry;
  try {
    const site = (await cfg("site_url")) || "https://www.valuenote.co.kr";
    const demo = await cfg("demo"), publisher = await cfg("publisher");
    const sj = await fetch(site + "/c/scores.json", { headers: { "cache-control": "no-cache" } }).then((r) => r.json());
    const S: Record<string, Row> = sj?.c || {};
    if (Object.keys(S).length < 100) return Response.json({ ok: false, msg: "점수표가 비어 있음" });

    // 어제 점수(저평가 폭)와 비교해 '오늘 새로 싸진 회사'를 찾는다. 날짜가 바뀔 때만 기준을 넘긴다.
    const snap = (await cfg("pd_scores")) || {};
    let prev: Record<string, number | null> = snap.prev || {};
    if (snap.date && snap.date !== sj.date) prev = snap.cur || {};
    const curMos = Object.fromEntries(Object.entries(S).map(([k, r]) => [k, r[5]]));
    const fresh = Object.keys(prev).length > 100 ? Object.entries(S)
      .filter(([k, r]) => r[5] !== null && r[5] >= 25 && (r[1] ?? 0) >= 60 && (r[2] ?? 0) >= 50 && (prev[k] == null || (prev[k] as number) < 25))
      .sort((a, b) => (b[1][1] ?? 0) - (a[1][1] ?? 0)) : [];

    // 새 칼럼(3일 안)
    const cols = (await load("trends", publisher ? [publisher] : undefined)).filter((d) => d.id.startsWith("col-") && d.data?.title)
      .sort((a, b) => b.id.localeCompare(a.id));
    const col = cols[0] && daysSince(cols[0].updated_at) < 3 ? cols[0] : null;

    // 알림을 켠 사용자
    const subs = await load("push_subs");
    const owners = [...new Set(subs.map((s) => s.owner))].filter((o) => o !== demo);
    if (!owners.length) return Response.json({ ok: true, owners: 0 });
    const [ints, holds, states, prefs, alerts] = await Promise.all([
      load("interests", owners), load("holdings", owners), load("push_state", owners), load("push_prefs", owners),
      sb.from("docs").select("owner,id,data,updated_at").eq("collection", "alerts").in("owner", owners).gte("updated_at", new Date(Date.parse(kst() + "T00:00:00+09:00")).toISOString()).then((r) => r.data || []),
    ]);

    const today = kst(), now = new Date().toISOString(), writes: any[] = [], report: any[] = [];
    for (const o of owners) {
      const pf = { interest: true, value: true, column: true, ...(prefs.find((p) => p.owner === o && p.id === "main")?.data || {}) };
      const stDoc = states.find((s) => s.owner === o && s.id === "main");
      const st: any = { int: {}, sent: {}, ...(stDoc?.data || {}) };
      const pushedToday = (alerts as any[]).filter((a) => a.owner === o && a.data?.push !== false && !String(a.id).startsWith("test-")).length;
      const heldTk = new Set(holds.filter((h) => h.owner === o).map((h) => nk(h.data?.ticker)).filter(Boolean));
      const myInts = ints.filter((x) => x.owner === o && daysSince(x.data?.last) < 45)
        .map((x) => ({ ...x.data, slug: x.data?.slug || slugOf(x.data?.t || x.data?.code) }))
        .filter((x) => S[x.slug] && !heldTk.has(nk(x.code || x.t)));
      const cands: { pri: number; kind: string; key: string; title: string; body: string; url: string; level: string; link?: any }[] = [];

      // 1) 관심 회사 큰 변화
      if (pf.interest) for (const x of myInts) {
        const r = S[x.slug], name = r[0], m = r[5], last = st.int[x.slug];
        if (!last) continue; // 처음 본 회사는 기준만 잡고 다음부터 변화를 잰다
        const base = last.mos;
        const entered = m !== null && m >= 25 && (base === null || base < 25);
        const moved = m !== null && base !== null && Math.abs(m - base) >= 8;
        if (!entered && !moved) continue;
        const better = base === null || (m as number) > base;
        cands.push({ pri: entered ? 100 : 80, kind: "int", key: x.slug, level: entered ? "good" : "info",
          title: entered ? `${name}, 저평가 구간에 들어왔습니다` : `${name}, ${better ? "적정 주가에 더 가까워졌습니다" : "가격이 더 비싸졌습니다"}`,
          body: `최근 보신 ${jo(name, "은", "는")} 지금 버핏 기준 ${gap(m)}. 점수와 근거를 확인해 보세요.`,
          url: coUrl(x.code || x.slug, name), link: { tab: "companies", q: name, coCode: x.code } });
      }
      // 2) 새 칼럼
      if (pf.column && col && st.col !== col.id) {
        const ser = col.data.series === "giants" ? "거장의 투자" : "주간 칼럼";
        cands.push({ pri: 90, kind: "col", key: col.id, level: "info", title: `새 칼럼 · ${col.data.title}`,
          body: `${jo(ser, "이", "가")} 올라왔습니다. 5분이면 읽을 수 있습니다.`, url: `/?col=${encodeURIComponent(col.id)}&from=push`, link: { tab: "column", col: col.id } });
      }
      // 3) 새로 싸진 회사 (저녁에는 보내지 않음, 이틀에 한 번)
      if (!evening && pf.value && daysSince(st.valueAt) >= 2) {
        const seen = new Set<string>(st.valueSeen || []);
        const f = fresh.find(([k, r]) => !seen.has(k) && !heldTk.has(nk(k.split("-")[0])) && !myInts.some((x) => x.slug === k));
        if (f) { const [k, r] = f;
          cands.push({ pri: 60, kind: "val", key: k, level: "good", title: `새로 싸진 회사 · ${r[0]}`,
            body: `오늘 처음으로 ${gap(r[5])}. 종합 ${r[1]}점, 확인해 보실래요?`, url: coUrl(k.split("-")[0].toUpperCase(), r[0]), link: { tab: "companies", q: r[0] } }); }
      }
      // 4) 관심 회사 근황: 1~3이 없을 때, 사흘에 한 번까지. 한 회사는 7일에 한 번, 최근에 본 회사부터
      if (!evening && pf.interest && !cands.length && daysSince(st.recapAt) >= 3) {
        const x = myInts.filter((y) => daysSince(st.int[y.slug]?.recap) >= 7).sort((a, b) => String(b.last || "").localeCompare(String(a.last || "")))[0];
        if (x) { const r = S[x.slug];
          cands.push({ pri: 40, kind: "recap", key: x.slug, level: "info", title: `최근 보신 ${r[0]}, 지금은 이렇습니다`,
            body: `${jo(r[0], "은", "는")} 지금 버핏 기준 ${gap(r[5])}. 종합 ${r[1]}점입니다.`, url: coUrl(x.code || x.slug, r[0]), link: { tab: "companies", q: r[0], coCode: x.code } }); }
      }
      if (evening) for (let i = cands.length - 1; i >= 0; i--) if (cands[i].pri < 80) cands.splice(i, 1);
      cands.sort((a, b) => b.pri - a.pri);
      let pushLeft = Math.max(0, 2 - pushedToday);
      cands.slice(0, 3).forEach((c, i) => {
        const push = i === 0 && pushLeft > 0; if (push) pushLeft--;
        writes.push({ collection: "alerts", owner: o, id: `pd-${c.kind}-${c.key}-${today}`, updated_at: now,
          data: { at: now, level: c.level, title: c.title, body: c.body, url: c.url, link: c.link, read: false, push, source: "맞춤 알림" } });
        if (c.kind === "int") st.int[c.key] = { ...(st.int[c.key] || {}), mos: S[c.key][5], at: now };
        if (c.kind === "recap") { st.recapAt = now; st.int[c.key] = { ...(st.int[c.key] || {}), mos: S[c.key][5], at: now, recap: now }; }
        if (c.kind === "col") st.col = c.key;
        if (c.kind === "val") { st.valueAt = now; st.valueSeen = [...(st.valueSeen || []), c.key].slice(-60); }
        report.push({ o: o.slice(0, 8), kind: c.kind, title: c.title, push });
      });
      // 처음 본 관심 회사는 지금 값을 기준으로 잡아 둔다(다음부터 변화를 잰다)
      for (const x of myInts) if (!st.int[x.slug]) st.int[x.slug] = { mos: S[x.slug][5], at: now };
      writes.push({ collection: "push_state", owner: o, id: "main", updated_at: now, data: st });
    }

    if (!dry) {
      // 알림함·상태를 먼저 저장(트리거가 push:true 인 알림만 푸시)
      for (let i = 0; i < writes.length; i += 200) { const { error } = await sb.from("docs").upsert(writes.slice(i, i + 200), { onConflict: "owner,collection,id", ignoreDuplicates: false }); if (error) throw error; }
      await setCfg("pd_scores", { date: sj.date, cur: curMos, prev });
    }
    return Response.json({ ok: true, date: sj.date, mode: evening ? "evening" : "morning", owners: owners.length, fresh: fresh.length, col: col?.id || null, sent: report });
  } catch (e) {
    return Response.json({ ok: false, error: String((e as Error)?.message || e) }, 500);
  }
});
