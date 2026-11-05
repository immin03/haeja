// 회원 메일 (2026-11-05)
// - {action:"drain"}   : (5분마다) 대기열(mail_queue)의 메일을 만들어 Resend로 보낸다. RESEND_API_KEY가 없으면 보내지 않고 기다린다.
// - {action:"digest"}  : (매주 월 08:30 KST) 수신 동의한 회원마다 이번 주 칼럼 메일을 대기열에 넣고 바로 보낸다. 2년 지난 동의는 재확인 안내도 넣는다.
// - {action:"preview", kind} : (관리자) 메일 미리보기 HTML
// - {action:"test", kind}    : (관리자) 관리자 본인 메일로 한 통 보내기
// 대표 검수 스위치(app_config.mail_live)가 켜져야 대기열 메일이 나간다 (2026-11-05)
// - POST ?unsub=토큰           : 메일 앱의 '수신 거부' 버튼(List-Unsubscribe 원클릭)
// verify_jwt = false (메일 앱이 원클릭 수신거부를 직접 호출하므로). 관리자 기능은 함수 안에서 확인한다.
// 법 기준: 칼럼 메일은 광고성 정보로 보고 제목 앞 (광고), 전송자·연락처, 수신거부 링크, 21~08시 발송 안 함.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const URL_ = Deno.env.get("SUPABASE_URL")!, SRK = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, ANON = Deno.env.get("SUPABASE_ANON_KEY")!;
const sb = createClient(URL_, SRK, { auth: { persistSession: false } });
let KEY = Deno.env.get("RESEND_API_KEY") || "";
// 키가 함수 비밀값에 없으면 DB 암호화 금고(vault: resend_api_key)에서 꺼낸다 (2026-11-05)
async function loadKey() { if (!KEY) { const { data } = await sb.rpc("_mail_key"); KEY = (data as string) || ""; } return KEY; }
const FROM = Deno.env.get("MAIL_FROM") || "밸류노트 <hello@valuenote.co.kr>";
const REPLY = Deno.env.get("MAIL_REPLY_TO") || "value.note.korea@gmail.com";
const SITE = "https://www.valuenote.co.kr";
const CONTACT = "value.note.korea@gmail.com";
const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...cors, "Content-Type": "application/json" } });
const esc = (s: unknown) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/* ---------- 날짜 (한국 시간) ---------- */
const kst = (d = new Date()) => new Date(d.getTime() + 9 * 3600e3);
const ymd = (d: Date) => d.toISOString().slice(0, 10);
const kDate = (iso: string) => { const d = kst(new Date(iso)); return `${d.getUTCFullYear()}년 ${d.getUTCMonth() + 1}월 ${d.getUTCDate()}일`; };
const kDateTime = (iso: string) => { const d = kst(new Date(iso)); return `${kDate(iso)} ${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`; };
function isoWeek(d = kst()) {
  const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  const day = (t.getUTCDay() + 6) % 7; t.setUTCDate(t.getUTCDate() - day + 3);
  const y = t.getUTCFullYear(), w1 = new Date(Date.UTC(y, 0, 4));
  const w = 1 + Math.round(((t.getTime() - w1.getTime()) / 864e5 - 3 + ((w1.getUTCDay() + 6) % 7)) / 7);
  return `${y}-W${String(w).padStart(2, "0")}`;
}
const weekLabel = (d = kst()) => `${d.getUTCMonth() + 1}월 ${Math.ceil(d.getUTCDate() / 7)}주`;
const daytime = () => { const h = kst().getUTCHours(); return h >= 8 && h < 21; };

/* ---------- 콘텐츠 ---------- */
type Col = { id: string; title: string; cover?: string; excerpt: string; views: number };
type Vid = { id: string; title: string };
async function columns(days: number, n: number): Promise<Col[]> {
  const from = ymd(new Date(kst().getTime() - days * 864e5));
  const { data } = await sb.from("docs").select("id,data").eq("collection", "trends").like("id", "col-%").gte("id", "col-" + from).order("id", { ascending: false }).limit(40);
  const L = (data || []).filter((d) => d.data?.title && d.data?.body);
  const { data: st } = await sb.from("column_stats").select("id,views").in("id", L.map((d) => d.id));
  const V: Record<string, number> = Object.fromEntries((st || []).map((x) => [x.id, x.views || 0]));
  return L.map((d) => {
    const quote = String(d.data.body).split("\n").filter((l: string) => l.startsWith(">")).map((l: string) => l.replace(/^>\s?/, "")).join(" ");
    const raw = (quote || String(d.data.body)).replace(/!\[[^\]]*\]\([^)]*\)/g, "").replace(/\[([^\]]*)\]\([^)]*\)/g, "$1").replace(/[*_#>|■]/g, "").replace(/\s+/g, " ").trim();
    const cut = raw.length > 120 ? raw.slice(0, 120).replace(/\s\S*$/, "") + "…" : raw;
    return { id: d.id, title: d.data.title, cover: d.data.cover, excerpt: cut, views: V[d.id] || 0 };
  }).sort((a, b) => b.views - a.views || b.id.localeCompare(a.id)).slice(0, n);
}
async function videos(days: number, n: number): Promise<Vid[]> {
  let q = sb.from("youtube_posts").select("youtube_id,title,scheduled_at,kind").not("youtube_id", "is", null).eq("kind", "long").order("scheduled_at", { ascending: false }).limit(n);
  if (days) q = q.gte("scheduled_at", new Date(Date.now() - days * 864e5).toISOString());
  const { data } = await q;
  return (data || []).map((v) => ({ id: v.youtube_id, title: v.title }));
}
let scoredN: number | null = null;
/* 계산하는 기업 수: c/scores.json 은 { date, c: { 종목: … } } 모양 (2026-11-05 고침: 예전엔 바깥 키 2개를 세서 '2개'로 나왔다) */
async function scored() {
  if (scoredN !== null) return scoredN;
  try { const r = await fetch(SITE + "/c/scores.json"); const j = await r.json(); const c = j?.c ?? j; scoredN = Array.isArray(c) ? c.length : Object.keys(c || {}).length; } catch (_) { scoredN = 0; }
  if (scoredN < 50) scoredN = 0;
  return scoredN;
}
const companiesText = (n: number) => n ? `${Math.floor(n / 50) * 50}곳이 넘는` : "한국·미국 주요";

/* ---------- 메일 틀 (2026-11-05 대표: 더 세련되게 · SUIT · 웹과 같은 느낌) ---------- */
const F = `'SUIT Variable','SUIT','Pretendard','Apple SD Gothic Neo','Malgun Gothic','맑은 고딕',sans-serif`;
const WM = `'Montserrat','Helvetica Neue',Arial,sans-serif`;
const NAVY = "#0E1A2B", NAVY2 = "#17283F", GOLD = "#C9B180", GOLD2 = "#B49C6D", IVORY = "#EADBB9", INK = "#0E1A2B", BODY = "#3B4657", MUTED = "#6B7484", LINE = "#E9E4D8", BG = "#F5F3EE";
const eyebrow = (t: string, c = GOLD2) => `<div style="font-family:${F};font-size:11px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:${c}">${t}</div>`;
const btn = (href: string, t: string, dark = true) => `<table role="presentation" cellpadding="0" cellspacing="0" style="margin:22px 0 2px"><tr><td style="background:${dark ? NAVY : IVORY};border-radius:999px"><a href="${href}" style="display:inline-block;padding:14px 26px;font-family:${F};font-size:14.5px;font-weight:700;letter-spacing:-.01em;color:${dark ? "#FFFFFF" : NAVY};text-decoration:none;word-break:keep-all">${t}</a></td></tr></table>`;
const h2 = (eb: string, t: string) => `<tr><td style="padding:44px 36px 14px">${eyebrow(eb)}<div style="font-family:${F};font-size:21px;font-weight:800;letter-spacing:-.02em;line-height:1.4;color:${INK};margin-top:8px;word-break:keep-all">${t}</div></td></tr>`;
const p = (t: string, extra = "") => `<p style="margin:0 0 14px;font-family:${F};font-size:15px;line-height:1.8;color:${BODY};word-break:keep-all;${extra}">${t}</p>`;
const rule = `<tr><td style="padding:0 36px"><div style="height:1px;background:${LINE};line-height:1px;font-size:1px">&nbsp;</div></td></tr>`;
const tabUrl = (tab: string, src: string) => `${SITE}/?tab=${tab}&utm_source=mail&utm_medium=email&utm_campaign=${src}`;
const colUrl = (id: string, src: string) => `${SITE}/?col=${encodeURIComponent(id)}&utm_source=mail&utm_medium=email&utm_campaign=${src}`;
const ytUrl = (id: string, src: string) => `https://www.youtube.com/watch?v=${encodeURIComponent(id)}&utm_source=valuenote_mail&utm_campaign=${src}`;
function colBig(c: Col, src: string) {
  return `<tr><td style="padding:0 36px 8px"><a href="${colUrl(c.id, src)}" style="text-decoration:none;color:${INK}">
    ${c.cover ? `<img src="${esc(c.cover)}" width="528" alt="" style="display:block;width:100%;max-width:528px;height:auto;border-radius:14px">` : ""}
    <div style="font-family:${F};font-size:20px;font-weight:800;letter-spacing:-.02em;line-height:1.45;margin:18px 0 8px;word-break:keep-all">${esc(c.title)}</div>
    <div style="font-family:${F};font-size:14.5px;line-height:1.8;color:${BODY};word-break:keep-all">${esc(c.excerpt)}</div>
    <div style="font-family:${F};font-size:13.5px;font-weight:700;color:${GOLD2};margin-top:12px;letter-spacing:.02em">칼럼 읽기 →</div></a></td></tr>`;
}
function colRow(c: Col, src: string, last = false) {
  return `<tr><td style="padding:0 36px"><a href="${colUrl(c.id, src)}" style="text-decoration:none;color:${INK}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="${last ? "" : `border-bottom:1px solid ${LINE};`}"><tr>
    ${c.cover ? `<td width="104" valign="top" style="padding:18px 16px 18px 0"><img src="${esc(c.cover)}" width="104" alt="" style="display:block;width:104px;height:auto;border-radius:10px"></td>` : ""}
    <td valign="top" style="padding:18px 0"><div style="font-family:${F};font-size:15.5px;font-weight:700;letter-spacing:-.015em;line-height:1.5;word-break:keep-all">${esc(c.title)}</div>
    <div style="font-family:${F};font-size:13px;line-height:1.65;color:${MUTED};margin-top:5px;word-break:keep-all">${esc(c.excerpt.slice(0, 64))}${c.excerpt.length > 64 ? "…" : ""}</div></td></tr></table></a></td></tr>`;
}
function vidGrid(V: Vid[], src: string) {
  if (!V.length) return "";
  const cell = (v: Vid) => `<td width="50%" valign="top" style="padding:0 7px 20px"><a href="${ytUrl(v.id, src)}" style="text-decoration:none;color:${INK}">
    <img src="https://i.ytimg.com/vi/${esc(v.id)}/hqdefault.jpg" width="250" alt="" style="display:block;width:100%;height:auto;border-radius:12px">
    <div style="font-family:${F};font-size:13.5px;font-weight:700;letter-spacing:-.01em;line-height:1.55;margin-top:10px;word-break:keep-all">${esc(v.title)}</div></a></td>`;
  let rows = "";
  for (let i = 0; i < V.length; i += 2) rows += `<tr>${cell(V[i])}${V[i + 1] ? cell(V[i + 1]) : '<td width="50%"></td>'}</tr>`;
  return `<tr><td style="padding:0 29px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">${rows}</table></td></tr>`;
}
const channels = (src: string) => {
  const a = (href: string, t: string) => `<a href="${href}" style="font-family:${F};font-size:12.5px;font-weight:700;color:${IVORY};text-decoration:none;letter-spacing:.02em">${t}</a>`;
  const dot = `<span style="color:#3A4A62">&nbsp;&nbsp;·&nbsp;&nbsp;</span>`;
  return `${a(`https://www.youtube.com/@valuenote_korea?utm_source=valuenote_mail&utm_campaign=${src}`, "YouTube")}${dot}${a("https://www.instagram.com/value.note.korea/", "Instagram")}${dot}${a("https://blog.naver.com/valuenote_korea", "Naver Blog")}${dot}${a(`${SITE}/?utm_source=mail&utm_campaign=${src}`, "valuenote.co.kr")}`;
};
/* 로고: Montserrat "Value"(흰)+"Note"(아이보리) · 아래 얇은 금선 · 그 아래 가운데 '밸류노트' (2026-10-23 확정안) */
const wordmark = `<table role="presentation" cellpadding="0" cellspacing="0"><tr><td align="center">
  <div style="font-family:${WM};font-size:22px;font-weight:800;color:#FFFFFF;letter-spacing:-.01em;line-height:1;padding-bottom:7px;border-bottom:1px solid ${GOLD};white-space:nowrap">Value<span style="color:${IVORY}">Note</span></div>
  <div style="font-family:${F};font-size:10.5px;font-weight:700;letter-spacing:.32em;padding-left:.32em;color:${IVORY};margin-top:6px">밸류노트</div></td></tr></table>`;
/* SUIT는 → 를 꺾쇠 모양으로 그려서, 화살표만 기본 글꼴로 그린다 (대표 기준: 화살표는 →) */
const ARW = `<span style="font-family:Arial,Helvetica,sans-serif;font-weight:400">→</span>`;
/* hero: 남색 첫 화면 — 위에 로고, 아래에 작은 금색 라벨 + 큰 제목 + 한 줄 설명 (+ 버튼) */
function hero(eb: string, title: string, sub: string, cta?: [string, string]) {
  return `<tr><td style="background:${NAVY};background-image:linear-gradient(160deg,${NAVY2} 0%,${NAVY} 55%,#0A1322 100%);padding:34px 36px 44px">
    ${wordmark}
    <div style="height:40px;line-height:40px;font-size:1px">&nbsp;</div>
    ${eyebrow(eb, GOLD)}
    <div style="font-family:${F};font-size:28px;font-weight:800;letter-spacing:-.03em;line-height:1.38;color:#FFFFFF;margin-top:12px;word-break:keep-all">${title}</div>
    <div style="font-family:${F};font-size:15px;line-height:1.8;color:#B9C2CF;margin-top:14px;word-break:keep-all">${sub}</div>
    ${cta ? btn(cta[0], cta[1], false) : ""}
  </td></tr>`;
}
function shell(pre: string, body: string, foot: string, src = "mail") {
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light"><title>밸류노트</title>
<style>@font-face{font-family:'SUIT Variable';font-weight:100 900;font-display:swap;src:url(${SITE}/fonts/SUIT-Variable.woff2) format('woff2')}@font-face{font-family:'Montserrat';font-weight:800;font-display:swap;src:url(${SITE}/fonts/montserrat-800.woff2) format('woff2')}
body{margin:0;padding:0;-webkit-font-smoothing:antialiased}a{text-decoration:none}@media (max-width:600px){.vn-wrap{padding:0!important}.vn-card{border-radius:0!important}}</style></head>
<body style="margin:0;padding:0;background:${BG}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">${esc(pre)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${BG}"><tr><td class="vn-wrap" align="center" style="padding:28px 12px">
<table class="vn-card" role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:#FFFFFF;border-radius:20px;overflow:hidden">
${body.replace(/→/g, ARW)}
<tr><td style="height:44px;line-height:44px;font-size:1px">&nbsp;</td></tr>
<tr><td style="background:${NAVY};padding:28px 36px 30px">
  <div>${channels(src)}</div>
  <div style="font-family:${F};font-size:11.5px;line-height:1.8;color:#8C97A8;margin-top:16px;word-break:keep-all">${foot}</div>
  <div style="font-family:${F};font-size:11.5px;line-height:1.8;color:#8C97A8;margin-top:8px;word-break:keep-all">밸류노트의 글과 영상은 공개된 자료를 정리한 것이며 특정 종목의 매수·매도를 권하지 않습니다.</div>
  <div style="font-family:${F};font-size:11.5px;line-height:1.8;color:#8C97A8;margin-top:8px">보낸 곳: 밸류노트(ValueNote) · 문의 <a href="mailto:${CONTACT}" style="color:#B9C2CF;text-decoration:underline">${CONTACT}</a></div>
</td></tr>
</table></td></tr></table></body></html>`;
}
const toText = (html: string) => html.replace(/<head[\s\S]*?<\/head>/g, "").replace(/<div style="display:none[^"]*">[\s\S]*?<\/div>/, "").replace(/<style[\s\S]*?<\/style>/g, "").replace(/<a [^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g, "$2 ($1)").replace(/<br\s*\/?>|<\/(p|div|tr|h\d)>/g, "\n").replace(/<[^>]+>/g, "").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/[ \t]+/g, " ").replace(/\n\s*\n+/g, "\n\n").trim();

/* ---------- 메일 종류별 ---------- */
type Who = { uid?: string; email: string; name?: string; ok?: boolean; consent_at?: string | null; token?: string };
const unsubUrl = (w: Who) => w.token ? `${SITE}/mail?u=${w.token}` : `${SITE}/?tab=account`;
async function welcome(w: Who) {
  const [C, V, N] = await Promise.all([columns(14, 3), videos(0, 4), scored()]);
  const nm = w.name || w.email.split("@")[0];
  /* 2026-11-05 대표: 촌스럽지 않게 — 현명한 투자, 거장의 기준으로 판단, 어떤 장에서도 흔들리지 않는 투자 */
  const pillars = [
    ["가격이 아니라 가치를 봅니다", "주가의 오르내림이 아니라 기업이 실제로 벌어들이는 이익에서 출발합니다. 그 이익을 보수적으로 할인해 지금 가격이 합리적인지 판단합니다."],
    ["거장의 원칙을 숫자로 옮겼습니다", "워렌 버핏의 경쟁우위, 벤저민 그레이엄의 안전마진, 찰리 멍거의 사업의 질. 세 사람이 기업을 고르던 기준을 하나의 점수와 적정 주가로 정리합니다."],
    ["어떤 장에서도 흔들리지 않도록", "급등장에서는 과열을, 급락장에서는 기회를 숫자로 확인합니다. 시장의 소음이 아니라 정해 둔 기준으로 판단할 수 있게 돕습니다."],
  ];
  const pillarHtml = pillars.map(([t, d], i) => `<tr><td style="padding:0 36px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="${i < pillars.length - 1 ? `border-bottom:1px solid ${LINE};` : ""}"><tr>
    <td width="52" valign="top" style="padding:22px 0"><div style="font-family:${WM};font-size:13px;font-weight:800;color:${GOLD2};letter-spacing:.04em">0${i + 1}</div></td>
    <td valign="top" style="padding:20px 0"><div style="font-family:${F};font-size:16.5px;font-weight:800;letter-spacing:-.02em;line-height:1.5;color:${INK};word-break:keep-all">${t}</div>
    <div style="font-family:${F};font-size:14px;line-height:1.8;color:${BODY};margin-top:6px;word-break:keep-all">${d}</div></td></tr></table></td></tr>`).join("");
  const steps = [
    ["보유 종목 등록", "지금 가진 종목이 적정 주가보다 싼지 비싼지 바로 확인합니다.", tabUrl("portfolio", "welcome")],
    ["관심 기업 담기", "담아 둔 기업이 저평가 구간에 들어오면 알려 드립니다.", tabUrl("companies", "welcome")],
    ["알림 켜기", "홈 화면에 추가하면 앱처럼 쓰고 알림도 받을 수 있습니다.", tabUrl("alerts", "welcome")],
  ];
  const stepHtml = `<tr><td style="padding:0 36px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${BG};border-radius:16px"><tr><td style="padding:8px 22px">
    ${steps.map(([t, d, href], i) => `<a href="${href}" style="display:block;text-decoration:none;color:${INK}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="${i < steps.length - 1 ? `border-bottom:1px solid ${LINE};` : ""}"><tr>
      <td width="38" valign="middle" style="padding:16px 0"><div style="width:26px;height:26px;border-radius:13px;background:${NAVY};color:#FFFFFF;font-family:${F};font-size:12.5px;font-weight:800;line-height:26px;text-align:center">${i + 1}</div></td>
      <td valign="middle" style="padding:16px 0"><div style="font-family:${F};font-size:14.5px;font-weight:800;letter-spacing:-.015em;color:${INK}">${t}</div><div style="font-family:${F};font-size:13px;line-height:1.6;color:${MUTED};margin-top:2px;word-break:keep-all">${d}</div></td>
      <td width="20" valign="middle" align="right" style="font-family:${F};font-size:15px;color:${GOLD2}">→</td></tr></table></a>`).join("")}
  </td></tr></table></td></tr>`;
  const consent = w.ok && w.consent_at
    ? `${kDate(w.consent_at)}에 칼럼·투자 정보 메일 수신에 동의하셨습니다. 원하지 않으시면 <a href="${unsubUrl(w)}" style="color:#B9C2CF;text-decoration:underline">수신 거부</a>를 누르세요.`
    : `이 메일은 밸류노트 가입 안내 메일입니다. 칼럼 메일은 위 버튼이나 앱의 <a href="${tabUrl("account", "welcome")}" style="color:#B9C2CF;text-decoration:underline">내 계정</a>에서 켤 수 있으며, 켜지 않으면 이 안내 말고는 보내지 않습니다.`;
  /* 칼럼을 보여 준 바로 다음에 구독 상자 */
  const sub = w.ok
    ? `<tr><td style="padding:28px 36px 0"><div style="border:1px solid ${LINE};border-radius:16px;padding:20px 22px">${eyebrow("Weekly Note")}<div style="font-family:${F};font-size:15px;font-weight:700;color:${INK};margin-top:8px;line-height:1.6;word-break:keep-all">칼럼 메일 구독이 완료됐습니다. 매주 월요일 아침 8시 30분, 한 주 동안 가장 많이 읽힌 칼럼과 새 영상을 보내 드립니다.</div></div></td></tr>`
    : `<tr><td style="padding:32px 36px 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${NAVY};background-image:linear-gradient(150deg,${NAVY2} 0%,${NAVY} 60%);border-radius:18px"><tr><td style="padding:30px 28px">
      ${eyebrow("Weekly Note · 매주 월요일 08:30", GOLD)}
      <div style="font-family:${F};font-size:21px;font-weight:800;letter-spacing:-.025em;line-height:1.45;color:#FFFFFF;margin-top:10px;word-break:keep-all">한 주의 시장을<br>칼럼 네 편으로 정리해 드립니다</div>
      <div style="font-family:${F};font-size:14px;line-height:1.8;color:#B9C2CF;margin-top:12px;word-break:keep-all">가장 많이 읽힌 칼럼과 새 영상을 월요일 아침 한 통에 담아 보냅니다. 일주일에 한 번, 언제든 한 번의 클릭으로 그만 받을 수 있습니다.</div>
      ${btn(w.token ? `${SITE}/mail?s=${w.token}` : tabUrl("account", "welcome"), "칼럼 메일 받기 →", false)}
      <div style="font-family:${F};font-size:11px;line-height:1.7;color:#7F8B9D;margin-top:12px;word-break:keep-all">버튼을 누른 뒤 열리는 화면에서 한 번 더 확인하면 구독됩니다. 칼럼·투자 정보(광고성 정보) 수신 동의이며 선택 사항입니다.</div>
    </td></tr></table></td></tr>`;
  const body = `${hero("Welcome to ValueNote", `${esc(nm)} 님,<br>시장이 흔들려도<br>기준은 흔들리지 않게.`,
      `밸류노트는 워렌 버핏·벤저민 그레이엄·찰리 멍거가 기업을 판단하던 원칙으로 ${companiesText(N)} 기업의 적정 주가와 점수를 매일 다시 계산합니다. 감정이 아닌 기준으로, 오래 가는 투자를 돕습니다.`,
      [`${SITE}/?utm_source=mail&utm_campaign=welcome`, "밸류노트 시작하기 →"])}
  ${h2("Our Principle", "현명한 투자를 위한 세 가지 기준")}${pillarHtml}
  ${h2("Get Started", "처음 5분, 이렇게 시작해 보세요")}${stepHtml}
  ${C.length ? h2("Most Read", "요즘 가장 많이 읽힌 칼럼") + C.map((c, i) => colRow(c, "welcome", i === C.length - 1)).join("") : ""}
  ${sub}
  ${V.length ? h2("On YouTube", "기업이 돈을 버는 구조를 10분 안에") + vidGrid(V, "welcome") : ""}`;
  return { subject: `${nm} 님, 밸류노트에 오신 걸 환영합니다`, html: shell("거장의 기준으로 기업의 적정 주가를 매일 계산합니다. 처음 5분 시작 가이드를 확인하세요.", body, consent, "welcome") };
}
async function digest(w: Who) {
  const [C, V] = await Promise.all([columns(7, 4), videos(7, 4)]);
  if (!C.length && !V.length) return null;
  const top = C[0];
  const body = `${hero(`Weekly Note · ${weekLabel()}`, "이번 주,<br>가장 많이 읽힌 밸류노트", "지난 한 주 시장에서 놓치면 아쉬운 이야기를 칼럼과 영상으로 정리했습니다.")}
  ${top ? h2("Top Story", "이번 주 1위 칼럼") + colBig(top, "digest") : ""}
  ${C.length > 1 ? h2("More Columns", "함께 읽으면 좋은 칼럼") + C.slice(1).map((c, i, a) => colRow(c, "digest", i === a.length - 1)).join("") : ""}
  ${V.length ? h2("On YouTube", "이번 주 새 영상") + vidGrid(V, "digest") : ""}
  <tr><td style="padding:12px 36px 0">${btn(tabUrl("column", "digest"), "칼럼 전체 보기 →")}</td></tr>`;
  const foot = `이 메일은 ${w.consent_at ? kDate(w.consent_at) + "에 " : ""}칼럼·투자 정보 메일 수신에 동의하신 분께 보내는 광고성 정보입니다. 더 받지 않으시려면 <a href="${unsubUrl(w)}" style="color:#B9C2CF;text-decoration:underline;font-weight:700">수신 거부</a>를 누르세요. 한 번 누르면 바로 처리됩니다.`;
  return { subject: `(광고) ${top ? top.title : "이번 주 밸류노트 새 영상"}`, html: shell(top ? top.excerpt : "이번 주 밸류노트 새 영상", body, foot, "digest") };
}
function consentMail(w: Who, on: boolean, at: string) {
  const body = `${hero("Notice", `칼럼 메일 수신 ${on ? "동의" : "거부"}가<br>처리됐습니다`, `${esc(w.email)} 주소로 요청하신 칼럼·투자 정보 메일 수신 ${on ? "동의" : "거부"}를 ${kDateTime(at)}에 처리했습니다.`)}
  <tr><td style="padding:36px 36px 0">${p(on ? "매주 월요일 아침 8시 30분, 한 주 동안 가장 많이 읽힌 칼럼과 새 영상을 보내 드립니다. 언제든 메일 아래 수신 거부 링크나 앱의 내 계정에서 끌 수 있습니다." : "앞으로 칼럼 메일은 보내지 않습니다. 가입·계정 관련 안내처럼 꼭 필요한 메일만 보냅니다. 다시 받고 싶으시면 앱의 내 계정에서 켤 수 있습니다.")}
  ${on ? "" : btn(tabUrl("account", "consent"), "내 계정 열기 →")}</td></tr>`;
  return { subject: `[밸류노트] 칼럼 메일 수신 ${on ? "동의" : "거부"} 처리 결과 안내`, html: shell(`칼럼 메일 수신 ${on ? "동의" : "거부"}를 처리했습니다.`, body, "정보통신망법에 따라 수신 동의·거부 처리 결과를 알려 드리는 메일입니다.", "consent") };
}
function reconfirmMail(w: Who) {
  const body = `${hero("Notice", "칼럼 메일 수신 동의를<br>확인해 주세요", `${w.consent_at ? kDate(w.consent_at) + "에 " : ""}칼럼·투자 정보 메일 수신에 동의하셨습니다. 법에 따라 2년마다 동의 여부를 다시 알려 드립니다.`)}
  <tr><td style="padding:36px 36px 0">${p("계속 받으시려면 아무것도 하지 않으셔도 됩니다. 그만 받으시려면 아래 버튼을 눌러 주세요.")}${btn(unsubUrl(w), "칼럼 메일 그만 받기")}</td></tr>`;
  return { subject: "[밸류노트] 칼럼 메일 수신 동의 확인 안내", html: shell("2년마다 수신 동의 여부를 알려 드립니다.", body, "정보통신망법에 따라 2년마다 수신 동의 여부를 알려 드리는 메일입니다.", "reconfirm") };
}

/* ---------- 보내기 ---------- */
async function send(to: string, m: { subject: string; html: string }, w?: Who, ad = false) {
  const headers: Record<string, string> = {};
  if (w?.token) { headers["List-Unsubscribe"] = `<${URL_}/functions/v1/mail?unsub=${w.token}>, <mailto:${CONTACT}?subject=unsubscribe>`; headers["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"; }
  const r = await fetch("https://api.resend.com/emails", { method: "POST", headers: { Authorization: `Bearer ${KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from: FROM, to: [to], reply_to: REPLY, subject: m.subject, html: m.html, text: toText(m.html), headers, tags: [{ name: "kind", value: ad ? "ad" : "service" }] }) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j?.message || j?.name || `HTTP ${r.status}`);
  return j.id as string;
}
async function who(uid: string | null, email: string): Promise<Who> {
  const w: Who = { uid: uid || undefined, email };
  if (uid) {
    const { data: p } = await sb.from("mail_prefs").select("ok,consent_at,token").eq("uid", uid).maybeSingle();
    if (p) Object.assign(w, p);
    const { data: a } = await sb.auth.admin.getUserById(uid);
    const md = a?.user?.user_metadata || {};
    const nm = String(md.name || md.full_name || "").trim(); if (nm) w.name = nm.slice(0, 20);
  }
  return w;
}
async function build(q: { kind: string; ref: string }, w: Who) {
  if (q.kind === "welcome") return await welcome(w);
  if (q.kind === "digest") return await digest(w);
  if (q.kind === "consent") return consentMail(w, q.ref.startsWith("on:"), new Date().toISOString());
  if (q.kind === "reconfirm") return reconfirmMail(w);
  return null;
}
async function drain() {
  const { data: Q } = await sb.from("mail_queue").select("*").eq("status", "queued").lt("tries", 5).order("created_at").limit(40);
  if (!Q?.length) return { ok: true, sent: 0 };
  await loadKey();
  if (!KEY) return { ok: false, waiting: Q.length, reason: "RESEND_API_KEY 없음 · 키를 넣으면 대기 중인 메일부터 보냅니다" };
  const { data: live } = await sb.from("app_config").select("value").eq("key", "mail_live").maybeSingle();
  if (live?.value !== true) return { ok: false, waiting: Q.length, reason: "대표 검수 전 · 관리자 메일 탭에서 '검수 완료 · 발송 시작'을 누르면 보냅니다" };
  let sent = 0, failed = 0, held = 0;
  for (const q of Q) {
    const ad = q.kind === "digest";
    if (ad && !daytime()) { held++; continue; }                     // 광고성 정보는 21~08시 보내지 않는다
    const w = await who(q.uid, q.email);
    if (ad && !w.ok) { await sb.from("mail_queue").update({ status: "skipped", error: "수신 거부됨" }).eq("id", q.id); continue; }
    if (q.kind === "welcome" && Date.now() - Date.parse(q.created_at) > 8 * 864e5) { await sb.from("mail_queue").update({ status: "skipped", error: "가입 8일이 지나 보내지 않음" }).eq("id", q.id); continue; }
    try {
      const m = await build(q, w);
      if (!m) { await sb.from("mail_queue").update({ status: "skipped", error: "보낼 내용 없음" }).eq("id", q.id); continue; }
      const id = await send(q.email, m, w, ad);
      await sb.from("mail_queue").update({ status: "sent", sent_at: new Date().toISOString(), provider_id: id, subject: m.subject, tries: q.tries + 1, error: null }).eq("id", q.id);
      sent++;
    } catch (e) {
      const t = q.tries + 1;
      await sb.from("mail_queue").update({ status: t >= 5 ? "failed" : "queued", tries: t, error: String((e as Error).message || e).slice(0, 300) }).eq("id", q.id);
      failed++;
    }
    await sleep(600);                                                 // Resend 초당 2건 제한
  }
  return { ok: true, sent, failed, held };
}
async function enqueueDigest() {
  const wk = isoWeek();
  const { data: P } = await sb.from("mail_prefs").select("uid,email,consent_at").eq("ok", true);
  const rows = (P || []).filter((p) => p.email).map((p) => ({ uid: p.uid, email: p.email, kind: "digest", ref: wk }));
  if (rows.length) await sb.from("mail_queue").upsert(rows, { onConflict: "uid,kind,ref", ignoreDuplicates: true });
  const old = (P || []).filter((p) => p.email && p.consent_at && Date.now() - Date.parse(p.consent_at) > 700 * 864e5);
  if (old.length) await sb.from("mail_queue").upsert(old.map((p) => ({ uid: p.uid, email: p.email, kind: "reconfirm", ref: "y" + kst().getUTCFullYear() })), { onConflict: "uid,kind,ref", ignoreDuplicates: true });
  return { week: wk, queued: rows.length, reconfirm: old.length };
}
async function adminOf(req: Request) {
  const auth = req.headers.get("Authorization") || "";
  if (!auth.startsWith("Bearer ")) return null;
  const c = createClient(URL_, ANON, { global: { headers: { Authorization: auth } }, auth: { persistSession: false } });
  const { data: { user } } = await c.auth.getUser();
  if (!user) return null;
  const { data } = await c.rpc("is_admin");
  return data === true ? user : null;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const u = new URL(req.url);
  try {
    const tok = u.searchParams.get("unsub");
    if (tok && req.method === "POST") {                               // 메일 앱 원클릭 수신 거부 (GET은 링크 검사기가 열 수 있어 받지 않는다)
      const { data, error } = await sb.rpc("mail_unsub", { p_token: tok });
      return json(error ? { ok: false, error: error.message } : data);
    }
    const body = await req.json().catch(() => ({}));
    if (body.action === "drain") return json(await drain());
    if (body.action === "digest") { const e = await enqueueDigest(); return json({ ...e, drain: await drain() }); }
    if (body.action === "preview" || body.action === "test") {
      const admin = await adminOf(req);
      if (!admin) return json({ ok: false, error: "관리자만 쓸 수 있습니다" }, 403);
      const w = await who(admin.id, admin.email!);
      if (!w.token) w.token = "00000000-0000-0000-0000-000000000000";
      const kind = ["welcome", "digest", "consent", "reconfirm"].includes(body.kind) ? body.kind : "welcome";
      // 미리보기는 실제 받을 모양: 가입 축하는 기본이 '구독 전' 회원용(구독 버튼 있는 판), as=sub이면 구독한 회원용
      if (kind === "welcome" && body.as !== "sub") { w.ok = false; w.consent_at = null; }
      else { w.ok = true; if (!w.consent_at) w.consent_at = new Date().toISOString(); }
      const m = await build({ kind, ref: "on:preview" }, w);
      if (!m) return json({ ok: false, error: "이번 주에 보낼 칼럼·영상이 없습니다" });
      if (body.action === "preview") return json({ ok: true, subject: m.subject, html: m.html });
      await loadKey();
      if (!KEY) return json({ ok: false, error: "RESEND_API_KEY가 아직 없습니다" });
      const id = await send(admin.email!, { subject: "[테스트] " + m.subject, html: m.html }, w, kind === "digest");
      return json({ ok: true, id, to: admin.email });
    }
    if (body.action === "status") { await loadKey(); return json({ ok: true, key: !!KEY, from: FROM }); }
    return json({ ok: false, error: "action 필요" }, 400);
  } catch (e) {
    return json({ ok: false, error: String((e as Error)?.message || e) }, 500);
  }
});
