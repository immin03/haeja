// 요즘 가장 핫한 주제 수집 (2026-11-08 대표님: 메인 상단에 핫한 주제, 자세한 건 성과 페이지).
// 08:05·12:05·17:05·21:05 KST pg_cron 이 부른다. Claude 토큰을 쓰지 않는다.
// 개인투자자가 많이 가진 종목·CEO × 사건어로 유튜브 이번 주 영상과 구글 뉴스를 찾아
// 같은 사건을 다룬 영상을 묶고 점수를 매겨 hot_topics 에 넣는다. 제목·각도는 '밸류노트 핫 토픽 정리' 작업이 쓴다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36";
type Ent = { n: string; a: string[]; ceo?: string; hold?: string; w: number };
// 보유액: 11/4 서학개미 평가액(SBS Biz 11/6)·2026-01 세이브로·10월 개인 순매수 기준. 가중치 w는 보유자 규모.
const ENT: Ent[] = [
  { n: "삼성전자", a: ["삼성전자", "삼전"], ceo: "전영현", hold: "개인 순매수 1위", w: 3 },
  { n: "SK하이닉스", a: ["SK하이닉스", "하이닉스"], ceo: "곽노정", hold: "개인 순매수 2위", w: 3 },
  { n: "테슬라", a: ["테슬라", "tesla"], ceo: "일론 머스크", hold: "서학개미 약 30조 원", w: 3 },
  { n: "엔비디아", a: ["엔비디아", "nvidia"], ceo: "젠슨 황", hold: "서학개미 약 22조 원", w: 3 },
  { n: "알파벳", a: ["알파벳", "구글"], ceo: "순다르 피차이", hold: "서학개미 약 10조 원", w: 2 },
  { n: "팔란티어", a: ["팔란티어"], ceo: "알렉스 카프", hold: "서학개미 약 9.6조 원", w: 2 },
  { n: "애플", a: ["애플"], ceo: "팀 쿡", hold: "서학개미 약 6.4조 원", w: 2 },
  { n: "아이온큐", a: ["아이온큐"], hold: "서학개미 약 5.7조 원", w: 2 },
  { n: "마이크로소프트", a: ["마이크로소프트", "MS"], hold: "서학개미 약 5조 원", w: 2 },
  { n: "마이크론", a: ["마이크론"], hold: "서학개미 약 4.7조 원", w: 2 },
  { n: "브로드컴", a: ["브로드컴"], hold: "서학개미 상위", w: 1.5 },
  { n: "스페이스X", a: ["스페이스X", "스페이스엑스"], hold: "서학개미 상위", w: 1.5 },
  { n: "인텔", a: ["인텔"], w: 1.2 }, { n: "AMD", a: ["AMD"], ceo: "리사 수", w: 1.2 },
  { n: "아마존", a: ["아마존"], w: 1.2 }, { n: "메타", a: ["메타 주가", "메타플랫폼"], ceo: "마크 저커버그", w: 1.2 },
  { n: "현대차", a: ["현대차", "현대자동차"], ceo: "정의선", hold: "국내 개인 인기 종목", w: 2 },
  { n: "삼성전기", a: ["삼성전기"], hold: "10월 개인 순매수 3위", w: 1.5 },
  { n: "두산에너빌리티", a: ["두산에너빌리티"], hold: "10월 개인 순매수 5위", w: 1.5 },
  { n: "효성중공업", a: ["효성중공업"], hold: "10월 개인 순매수 4위", w: 1.5 },
  { n: "네이버", a: ["네이버", "NAVER"], w: 1.2 }, { n: "카카오", a: ["카카오"], w: 1.2 },
  { n: "쿠팡", a: ["쿠팡"], ceo: "김범석", w: 1.2 }, { n: "금", a: ["금값", "금 시세"], w: 1.5 }, { n: "비트코인", a: ["비트코인"], w: 1.2 },
  { n: "퇴직연금", a: ["퇴직연금", "IRP"], w: 1.5 }, { n: "국민연금", a: ["국민연금"], w: 1.5 },
];
const WORDS = ["의혹 논란", "조사 소송", "폭락 이유", "급등 이유"];
const EVENT = new Map<string, number>([["스파이", 2], ["의혹", 2], ["논란", 1.6], ["소송", 1.7], ["조사", 1.4], ["수사", 1.8], ["압수수색", 2], ["구속", 2], ["사임", 2], ["해임", 2], ["퇴진", 2], ["청문회", 1.8], ["파산", 2], ["리콜", 1.7], ["해킹", 1.8], ["유출", 1.6], ["쇼크", 1.3], ["규제", 1.3], ["제재", 1.5], ["인수", 1.4], ["합병", 1.4], ["분할", 1.3], ["유상증자", 1.5], ["공매도", 1.2], ["폭락", 1.1], ["급락", 1.1], ["폭등", 1.1], ["급등", 1.1], ["화재", 1.6], ["파업", 1.4], ["사망", 1.6], ["방한", 1.3], ["취소", 1.2], ["고발", 1.6], ["횡령", 2], ["배임", 2], ["담합", 1.7], ["상폐", 2], ["상장폐지", 2]]);
const yti = async (q: string) => {
  const r = await fetch("https://www.youtube.com/youtubei/v1/search?prettyPrint=false", { method: "POST", headers: { "User-Agent": UA, "Content-Type": "application/json" },
    body: JSON.stringify({ context: { client: { clientName: "WEB", clientVersion: "2.20251001.00.00", hl: "ko", gl: "KR" } }, query: q, params: "EgIIAw==" }) }); // 이번 주 업로드
  if (!r.ok) throw new Error("yt " + r.status); return await r.json();
};
const txt = (o: any) => o?.simpleText ?? (o?.runs || []).map((x: any) => x.text).join("") ?? "";
const num = (s: string) => { const d = String(s || "").replace(/[^\d]/g, ""); return d ? +d : null; };
const hoursAgo = (s: string) => { const m = s.match(/(\d+)\s*(초|분|시간|일|주|개월|년)/); if (!m) return null; const n = +m[1], u = m[2]; return u === "초" ? 0.1 : u === "분" ? n / 60 : u === "시간" ? n : u === "일" ? n * 24 : u === "주" ? n * 168 : 9999; };
type Vid = { id: string; title: string; channel: string; views: number; age: number; when: string };
function collect(node: any, out: Vid[]) {
  if (!node || typeof node !== "object") return;
  if (Array.isArray(node)) { for (const x of node) collect(x, out); return; }
  const v = node.videoRenderer;
  if (v?.videoId) { const views = num(txt(v.viewCountText)), when = txt(v.publishedTimeText), age = hoursAgo(when);
    if (views !== null && age !== null && !txt(v.badges?.[0]?.metadataBadgeRenderer?.label).match(/LIVE|실시간/)) out.push({ id: v.videoId, title: txt(v.title), channel: v.ownerText?.runs?.[0]?.text || "", views, age, when });
    return; }
  for (const k in node) collect(node[k], out);
}
async function pool<T>(xs: T[], n: number, f: (x: T) => Promise<void>) { let i = 0; await Promise.all(Array.from({ length: Math.min(n, xs.length) }, async () => { while (i < xs.length) await f(xs[i++]); })); }
const STRIP = /(으로|에서|에게|까지|부터|이라|라고|하고|했다|한다|은|는|이|가|을|를|의|에|도|로|과|와)$/;
const tokens = (t: string) => [...new Set((t.match(/[가-힣A-Za-z0-9]{2,}/g) || []).map((w) => w.length > 2 ? w.replace(STRIP, "") : w))];
const has = (e: Ent, t: string) => { const l = t.toLowerCase(); return e.a.some((a) => l.includes(a.toLowerCase())) || (!!e.ceo && t.includes(e.ceo)); };

async function news(q: string) {
  try {
    const r = await fetch(`https://news.google.com/rss/search?q=${encodeURIComponent(q + " when:2d")}&hl=ko&gl=KR&ceid=KR:ko`, { headers: { "User-Agent": UA } });
    const x = await r.text(), items = x.split("<item>").slice(1);
    const dec = (s: string) => s.replace(/<!\[CDATA\[|\]\]>/g, "").replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">");
    const g = (s: string, t: string) => dec((s.match(new RegExp(`<${t}[^>]*>([\\s\\S]*?)</${t}>`)) || [])[1] || "");
    return { n: items.length, top: items.slice(0, 5).map((s) => ({ title: g(s, "title"), link: g(s, "link"), source: g(s, "source"), at: g(s, "pubDate") })) };
  } catch (_) { return { n: 0, top: [] as any[] }; }
}

async function run() {
  const t0 = Date.now(), log: string[] = [], qs: { e: Ent; q: string }[] = [];
  for (const e of ENT) { for (const w of WORDS) qs.push({ e, q: `${e.a[0]} ${w}` }); if (e.ceo) qs.push({ e, q: `${e.ceo} 의혹` }, { e, q: e.ceo }); }
  const seen = new Map<string, Map<string, Vid>>(); let fails = 0;
  await pool(qs, 4, async ({ e, q }) => { for (let k = 0; k < 2; k++) try {
      const out: Vid[] = []; collect(await yti(q), out); const m = seen.get(e.n) || new Map<string, Vid>();
      for (const v of out) if (v.age <= 96 && has(e, v.title)) m.set(v.id, v); seen.set(e.n, m); break;
    } catch (_) { if (k) fails++; await new Promise((r) => setTimeout(r, 1200)); } });
  const rows: any[] = [];
  for (const e of ENT) {
    const vids = [...(seen.get(e.n)?.values() || [])]; const used = new Set<string>();
    const cnt = new Map<string, Set<string>>();
    for (const v of vids) for (const t of tokens(v.title)) if (EVENT.has(t)) { const s = cnt.get(t) || new Set<string>(); s.add(v.channel); cnt.set(t, s); }
    const order = [...cnt.entries()].filter(([, s]) => s.size >= 2).sort((a, b) => b[1].size * EVENT.get(b[0])! - a[1].size * EVENT.get(a[0])!).slice(0, 3);
    for (const [tok] of order) {
      const vs = vids.filter((v) => !used.has(v.id) && v.title.includes(tok)); if (!vs.length) continue; vs.forEach((v) => used.add(v.id));
      const ch = new Set(vs.map((v) => v.channel)); if (ch.size < 2) continue;
      const views = vs.reduce((a, v) => a + v.views, 0), per = vs.reduce((a, v) => a + v.views / Math.max(v.age, 2), 0);
      if (views < 20000) continue;
      rows.push({ e, tok, views, per, channels: ch.size, score: Math.round(per * e.w * EVENT.get(tok)! * (1 + Math.log2(ch.size))), vs: vs.sort((a, b) => b.views - a.views).slice(0, 8) });
    }
  }
  rows.sort((a, b) => b.score - a.score);
  const top = rows.slice(0, 20);
  await pool(top, 4, async (r) => { const q = r.e.ceo && r.vs.some((v: Vid) => v.title.includes(r.e.ceo)) ? `${r.e.ceo} ${r.tok}` : `${r.e.a[0]} ${r.tok}`; r.news = await news(q); });
  const now = new Date().toISOString();
  if (top.length) {
    const { error } = await sb.from("hot_topics").upsert(top.map((r) => ({ key: `${r.e.n}:${r.tok}`, entity: r.e.n, token: r.tok, holding: r.e.hold || null, score: r.score + Math.min(r.news.n, 50) * r.score * 0.01,
      views: r.views, per_hour: Math.round(r.per), channels: r.channels, videos: r.vs, news: r.news.top, news_n: r.news.n, seen_at: now, updated_at: now })), { onConflict: "key" });
    if (error) log.push("저장 오류 " + error.message);
  }
  log.push(`검색 ${qs.length}개 (실패 ${fails}) · 후보 ${rows.length}개 · 저장 ${top.length}개 · ${Math.round((Date.now() - t0) / 1000)}초`);
  const { data: pub } = await sb.rpc("publisher_id");
  if (pub) await sb.from("docs").upsert({ owner: pub, collection: "trends", id: "hot_log", data: { at: now, log }, updated_at: now }, { onConflict: "owner,collection,id" });
  return { log, top: top.slice(0, 12).map((r) => `${r.e.n}:${r.tok} ${r.score} v${r.views} c${r.channels} n${r.news.n}`) };
}
Deno.serve(async (req: Request) => {
  const body = await req.json().catch(() => ({}));
  if (body?.wait) return Response.json({ ok: true, ...(await run()) });
  // @ts-ignore EdgeRuntime 은 Supabase 런타임에 있다
  EdgeRuntime.waitUntil(run());
  return Response.json({ ok: true, started: true }, { status: 202 });
});
