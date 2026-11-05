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
const KEY = Deno.env.get("RESEND_API_KEY") || "";
const FROM = Deno.env.get("MAIL_FROM") || "밸류노트 <hello@valuenote.co.kr>";
const REPLY = Deno.env.get("MAIL_REPLY_TO") || "immin03@gmail.com";
const SITE = "https://www.valuenote.co.kr";
const CONTACT = "immin03@gmail.com";
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
async function scored() {
  if (scoredN !== null) return scoredN;
  try { const r = await fetch(SITE + "/c/scores.json"); const j = await r.json(); scoredN = Array.isArray(j) ? j.length : Object.keys(j || {}).length; } catch (_) { scoredN = 0; }
  return scoredN;
}

/* ---------- 메일 틀 ---------- */
const F = `'Pretendard','Apple SD Gothic Neo','Malgun Gothic','맑은 고딕',sans-serif`;
const NAVY = "#0E1A2B", GOLD = "#C9B180", INK = "#0E1A2B", MUTED = "#6B7484", LINE = "#E6E1D6", BG = "#F5F3EE";
const btn = (href: string, t: string) => `<table role="presentation" cellpadding="0" cellspacing="0" style="margin:18px 0 4px"><tr><td style="background:${NAVY};border-radius:10px"><a href="${href}" style="display:inline-block;padding:13px 22px;font-family:${F};font-size:15px;font-weight:700;color:#FFFFFF;text-decoration:none;word-break:keep-all">${t}</a></td></tr></table>`;
const h2 = (t: string) => `<tr><td style="padding:30px 28px 10px;font-family:${F};font-size:17px;font-weight:800;color:${INK};word-break:keep-all"><span style="display:inline-block;width:3px;height:15px;background:${GOLD};border-radius:2px;margin-right:8px;vertical-align:-2px"></span>${t}</td></tr>`;
const p = (t: string, extra = "") => `<p style="margin:0 0 12px;font-family:${F};font-size:15px;line-height:1.75;color:${INK};word-break:keep-all;${extra}">${t}</p>`;
const tabUrl = (tab: string, src: string) => `${SITE}/?tab=${tab}&utm_source=mail&utm_medium=email&utm_campaign=${src}`;
const colUrl = (id: string, src: string) => `${SITE}/?col=${encodeURIComponent(id)}&utm_source=mail&utm_medium=email&utm_campaign=${src}`;
const ytUrl = (id: string, src: string) => `https://www.youtube.com/watch?v=${encodeURIComponent(id)}&utm_source=valuenote_mail&utm_campaign=${src}`;
function colBig(c: Col, src: string) {
  return `<tr><td style="padding:4px 28px 8px"><a href="${colUrl(c.id, src)}" style="text-decoration:none;color:${INK}">
    ${c.cover ? `<img src="${esc(c.cover)}" width="544" alt="" style="display:block;width:100%;max-width:544px;height:auto;border-radius:12px;border:1px solid ${LINE}">` : ""}
    <div style="font-family:${F};font-size:19px;font-weight:800;line-height:1.45;margin:14px 0 6px;word-break:keep-all">${esc(c.title)}</div>
    <div style="font-family:${F};font-size:14px;line-height:1.7;color:#3B4657;word-break:keep-all">${esc(c.excerpt)}</div>
    <div style="font-family:${F};font-size:14px;font-weight:700;color:${NAVY};margin-top:8px">칼럼 읽기 →</div></a></td></tr>`;
}
function colRow(c: Col, src: string) {
  return `<tr><td style="padding:10px 28px"><a href="${colUrl(c.id, src)}" style="text-decoration:none;color:${INK}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
    ${c.cover ? `<td width="112" valign="top" style="padding-right:14px"><img src="${esc(c.cover)}" width="112" alt="" style="display:block;width:112px;height:auto;border-radius:8px;border:1px solid ${LINE}"></td>` : ""}
    <td valign="top"><div style="font-family:${F};font-size:15px;font-weight:800;line-height:1.45;word-break:keep-all">${esc(c.title)}</div>
    <div style="font-family:${F};font-size:13px;line-height:1.6;color:${MUTED};margin-top:4px;word-break:keep-all">${esc(c.excerpt.slice(0, 70))}${c.excerpt.length > 70 ? "…" : ""}</div></td></tr></table></a></td></tr>`;
}
function vidGrid(V: Vid[], src: string) {
  if (!V.length) return "";
  const cell = (v: Vid) => `<td width="50%" valign="top" style="padding:0 6px 14px"><a href="${ytUrl(v.id, src)}" style="text-decoration:none;color:${INK}">
    <img src="https://i.ytimg.com/vi/${esc(v.id)}/hqdefault.jpg" width="262" alt="" style="display:block;width:100%;height:auto;border-radius:10px">
    <div style="font-family:${F};font-size:13.5px;font-weight:700;line-height:1.5;margin-top:8px;word-break:keep-all">${esc(v.title)}</div></a></td>`;
  let rows = "";
  for (let i = 0; i < V.length; i += 2) rows += `<tr>${cell(V[i])}${V[i + 1] ? cell(V[i + 1]) : '<td width="50%"></td>'}</tr>`;
  return `<tr><td style="padding:4px 22px 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">${rows}</table></td></tr>`;
}
const channels = (src: string) => `<tr><td style="padding:22px 28px 6px;font-family:${F};font-size:14px;color:${INK};word-break:keep-all">
  <a href="https://www.youtube.com/@valuenote_korea?utm_source=valuenote_mail&utm_campaign=${src}" style="color:${NAVY};font-weight:700;text-decoration:none">유튜브</a>
  <span style="color:${LINE}">&nbsp;|&nbsp;</span><a href="https://www.instagram.com/value.note.korea/" style="color:${NAVY};font-weight:700;text-decoration:none">인스타그램</a>
  <span style="color:${LINE}">&nbsp;|&nbsp;</span><a href="https://blog.naver.com/valuenote_korea" style="color:${NAVY};font-weight:700;text-decoration:none">네이버 블로그</a>
  <span style="color:${LINE}">&nbsp;|&nbsp;</span><a href="${SITE}/?utm_source=mail&utm_campaign=${src}" style="color:${NAVY};font-weight:700;text-decoration:none">밸류노트 앱</a></td></tr>`;
function shell(pre: string, body: string, foot: string) {
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>밸류노트</title></head>
<body style="margin:0;padding:0;background:${BG}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">${esc(pre)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${BG}"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:#FFFFFF;border-radius:16px;overflow:hidden;border:1px solid ${LINE}">
<tr><td align="center" style="background:${NAVY};padding:26px 20px 22px">
  <div style="font-family:Montserrat,${F};font-size:26px;font-weight:800;color:#FFFFFF;letter-spacing:-.01em;line-height:1">Value<span style="color:#EADBB9">Note</span></div>
  <div style="width:120px;height:1px;background:#D8C294;margin:9px auto 7px;line-height:1px;font-size:1px">&nbsp;</div>
  <div style="font-family:${F};font-size:12px;font-weight:700;letter-spacing:.22em;color:#EADBB9">밸류노트</div></td></tr>
${body}
<tr><td style="padding:26px 28px 28px;border-top:1px solid ${LINE};font-family:${F};font-size:12px;line-height:1.75;color:${MUTED};word-break:keep-all">${foot}
  <div style="margin-top:8px">밸류노트의 글과 영상은 공개된 자료를 정리한 것이며 특정 종목의 매수·매도를 권하지 않습니다.</div>
  <div style="margin-top:8px">보낸 곳: 밸류노트(ValueNote) · 문의 <a href="mailto:${CONTACT}" style="color:${MUTED}">${CONTACT}</a></div></td></tr>
</table></td></tr></table></body></html>`;
}
const toText = (html: string) => html.replace(/<head[\s\S]*?<\/head>/g, "").replace(/<div style="display:none[^"]*">[\s\S]*?<\/div>/, "").replace(/<style[\s\S]*?<\/style>/g, "").replace(/<a [^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g, "$2 ($1)").replace(/<br\s*\/?>|<\/(p|div|tr|h\d)>/g, "\n").replace(/<[^>]+>/g, "").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/[ \t]+/g, " ").replace(/\n\s*\n+/g, "\n\n").trim();

/* ---------- 메일 종류별 ---------- */
type Who = { uid?: string; email: string; name?: string; ok?: boolean; consent_at?: string | null; token?: string };
const unsubUrl = (w: Who) => w.token ? `${SITE}/mail?u=${w.token}` : `${SITE}/?tab=account`;
async function welcome(w: Who) {
  const [C, V, N] = await Promise.all([columns(14, 3), videos(0, 4), scored()]);
  const nm = w.name || w.email.split("@")[0];
  const steps = [
    ["보유 종목을 넣어 보세요", "가지고 계신 종목을 넣으면 지금 주가가 적정 주가보다 싼지 비싼지 바로 보여 드립니다.", tabUrl("portfolio", "welcome")],
    ["궁금한 회사를 관심 종목에 담아 두세요", "담아 둔 회사가 저평가 구간에 들어오면 알림으로 알려 드려요.", tabUrl("companies", "welcome")],
    ["알림을 켜 두세요", "휴대폰에서는 홈 화면에 밸류노트를 추가하면 앱처럼 쓰고 알림도 받을 수 있습니다.", tabUrl("alerts", "welcome")],
  ];
  const stepHtml = steps.map(([t, d, href], i) => `<tr><td style="padding:8px 28px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
    <td width="40" valign="top"><div style="width:28px;height:28px;border-radius:14px;background:${NAVY};color:#FFFFFF;font-family:${F};font-size:14px;font-weight:800;line-height:28px;text-align:center">${i + 1}</div></td>
    <td valign="top"><a href="${href}" style="text-decoration:none;color:${INK}"><div style="font-family:${F};font-size:15px;font-weight:800;line-height:1.5;word-break:keep-all">${t} →</div>
    <div style="font-family:${F};font-size:14px;line-height:1.65;color:#3B4657;word-break:keep-all">${d}</div></a></td></tr></table></td></tr>`).join("");
  const consent = w.ok && w.consent_at
    ? `${kDate(w.consent_at)}에 칼럼·투자 정보 메일 수신에 동의하셨습니다. 원하지 않으시면 <a href="${unsubUrl(w)}" style="color:${MUTED}">여기서 수신을 거부</a>할 수 있습니다.`
    : `칼럼 메일은 위 버튼을 누르거나 앱의 <a href="${tabUrl("account", "welcome")}" style="color:${MUTED}">내 계정</a>에서 켤 수 있습니다. 켜지 않으면 이 가입 안내 메일 말고는 보내지 않습니다.`;
  /* 2026-11-05 대표: 가입 축하 메일에서 칼럼 구독을 바로 유도 — 칼럼을 보여 준 바로 다음에 구독 상자 */
  const sub = w.ok
    ? `<tr><td style="padding:18px 28px 0"><div style="background:${BG};border-radius:12px;padding:16px 18px;font-family:${F};font-size:14px;line-height:1.7;color:${INK};word-break:keep-all"><b>칼럼 메일 구독 완료</b><br>매주 월요일 아침 8시 30분, 그 주에 가장 많이 읽힌 칼럼과 새 영상을 보내 드립니다.</div></td></tr>`
    : `<tr><td style="padding:20px 28px 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${NAVY};border-radius:14px"><tr><td style="padding:24px 22px">
      <div style="font-family:${F};font-size:13px;font-weight:700;letter-spacing:.06em;color:#EADBB9">매주 월요일 아침 8시 30분</div>
      <div style="font-family:${F};font-size:19px;font-weight:800;line-height:1.45;color:#FFFFFF;margin:6px 0 10px;word-break:keep-all">이런 칼럼을 메일로 받아 보세요</div>
      <div style="font-family:${F};font-size:14px;line-height:1.75;color:#D9DEE6;word-break:keep-all">한 주 동안 가장 많이 읽힌 칼럼 4편과 새 영상을 한 통에 모아 보내 드립니다. 일주일에 한 번만 보내고, 메일 아래 링크로 언제든 그만 받을 수 있습니다.</div>
      <table role="presentation" cellpadding="0" cellspacing="0" style="margin:16px 0 0"><tr><td style="background:#EADBB9;border-radius:10px"><a href="${w.token ? `${SITE}/mail?s=${w.token}` : tabUrl("account", "welcome")}" style="display:inline-block;padding:13px 22px;font-family:${F};font-size:15px;font-weight:800;color:${NAVY};text-decoration:none">칼럼 메일 받기 →</a></td></tr></table>
      <div style="font-family:${F};font-size:11.5px;line-height:1.6;color:#9AA4B2;margin-top:10px;word-break:keep-all">누르면 열리는 화면에서 한 번 더 확인하면 구독됩니다. 구독은 광고성 정보 수신 동의이며 선택 사항입니다.</div>
    </td></tr></table></td></tr>`;
  const body = `<tr><td style="padding:32px 28px 4px">
    <div style="font-family:${F};font-size:23px;font-weight:800;line-height:1.4;color:${INK};word-break:keep-all">${esc(nm)} 님, 밸류노트에 오신 걸 환영합니다</div></td></tr>
  <tr><td style="padding:14px 28px 0">${p(`밸류노트는 워렌 버핏·벤저민 그레이엄·찰리 멍거가 회사를 고르던 기준으로 ${N ? `<b>${N.toLocaleString("ko-KR")}개</b> 회사의` : "한국·미국 주요 회사의"} 적정 주가와 점수를 매일 다시 계산합니다.`)}
    ${p("주가가 오를지 맞히는 서비스가 아닙니다. 지금 가격이 회사가 버는 돈에 비해 싼지 비싼지를 보수적인 계산으로 보여 드립니다.")}
    ${btn(`${SITE}/?utm_source=mail&utm_campaign=welcome`, "밸류노트 열기")}</td></tr>
  ${h2("처음 하면 좋은 세 가지")}${stepHtml}
  ${C.length ? h2("요즘 많이 읽힌 칼럼") + C.map((c) => colRow(c, "welcome")).join("") : ""}
  ${sub}
  ${V.length ? h2("유튜브 밸류노트 최신 영상") + `<tr><td style="padding:0 28px 6px">${p("회사가 돈을 버는 구조를 10분 안팎으로 풀어 드립니다.", `color:#3B4657;font-size:14px`)}</td></tr>` + vidGrid(V, "welcome") : ""}
  ${channels("welcome")}`;
  return { subject: "밸류노트 가입을 환영합니다 · 처음 하면 좋은 세 가지", html: shell("보유 종목을 넣으면 적정 주가를 바로 계산해 드립니다.", body, `이 메일은 밸류노트 가입 안내 메일입니다. ${consent}`) };
}
async function digest(w: Who) {
  const [C, V] = await Promise.all([columns(7, 4), videos(7, 4)]);
  if (!C.length && !V.length) return null;
  const top = C[0];
  const body = `<tr><td style="padding:30px 28px 0;font-family:${F};font-size:13px;font-weight:700;color:${MUTED};letter-spacing:.04em">이번 주 밸류노트 · ${weekLabel()}</td></tr>
  ${top ? `<tr><td style="padding:6px 28px 10px">${p("지난 한 주 밸류노트에서 가장 많이 읽힌 글부터 정리했습니다.", "color:#3B4657;font-size:14px;margin:0")}</td></tr>` + colBig(top, "digest") : ""}
  ${C.length > 1 ? h2("함께 읽으면 좋은 칼럼") + C.slice(1).map((c) => colRow(c, "digest")).join("") : ""}
  ${V.length ? h2("이번 주 새 영상") + vidGrid(V, "digest") : ""}
  <tr><td style="padding:6px 28px 0">${btn(tabUrl("column", "digest"), "칼럼 전체 보기")}</td></tr>
  ${channels("digest")}`;
  const foot = `이 메일은 ${w.consent_at ? kDate(w.consent_at) + "에 " : ""}칼럼·투자 정보 메일 수신에 동의하신 분께 보내는 광고성 정보입니다. 더 받지 않으시려면 <a href="${unsubUrl(w)}" style="color:${MUTED};font-weight:700">수신 거부</a>를 누르세요. 한 번 누르면 바로 처리됩니다.`;
  return { subject: `(광고) ${top ? top.title : "이번 주 밸류노트 새 영상"}`, html: shell(top ? top.excerpt : "이번 주 밸류노트 새 영상", body, foot) };
}
function consentMail(w: Who, on: boolean, at: string) {
  const body = `<tr><td style="padding:32px 28px 8px"><div style="font-family:${F};font-size:21px;font-weight:800;line-height:1.4;color:${INK};word-break:keep-all">칼럼 메일 수신 ${on ? "동의" : "거부"}가 처리됐습니다</div></td></tr>
  <tr><td style="padding:12px 28px 8px">${p(`${esc(w.email)} 주소로 요청하신 칼럼·투자 정보 메일 수신 ${on ? "동의" : "거부"}를 ${kDateTime(at)}에 처리했습니다.`)}
  ${p(on ? "매주 월요일 아침, 그 주에 많이 읽힌 칼럼과 새 영상을 보내 드립니다. 언제든 메일 아래 수신 거부 링크나 앱의 내 계정에서 끌 수 있습니다." : "앞으로 칼럼 메일은 보내지 않습니다. 가입·계정 관련 안내처럼 꼭 필요한 메일만 보냅니다. 다시 받고 싶으시면 앱의 내 계정에서 켤 수 있습니다.")}
  ${on ? "" : btn(tabUrl("account", "consent"), "내 계정 열기")}</td></tr>`;
  return { subject: `[밸류노트] 칼럼 메일 수신 ${on ? "동의" : "거부"} 처리 결과 안내`, html: shell(`칼럼 메일 수신 ${on ? "동의" : "거부"}를 처리했습니다.`, body, "정보통신망법에 따라 수신 동의·거부 처리 결과를 알려 드리는 메일입니다.") };
}
function reconfirmMail(w: Who) {
  const body = `<tr><td style="padding:32px 28px 8px"><div style="font-family:${F};font-size:21px;font-weight:800;line-height:1.4;color:${INK};word-break:keep-all">칼럼 메일 수신 동의를 확인해 주세요</div></td></tr>
  <tr><td style="padding:12px 28px 8px">${p(`${w.consent_at ? kDate(w.consent_at) + "에 " : ""}칼럼·투자 정보 메일 수신에 동의하셨습니다. 법에 따라 2년마다 동의 여부를 다시 알려 드립니다.`)}
  ${p("계속 받으시려면 아무것도 하지 않으셔도 됩니다. 그만 받으시려면 아래 버튼을 눌러 주세요.")}${btn(unsubUrl(w), "칼럼 메일 그만 받기")}</td></tr>`;
  return { subject: "[밸류노트] 칼럼 메일 수신 동의 확인 안내", html: shell("2년마다 수신 동의 여부를 알려 드립니다.", body, "정보통신망법에 따라 2년마다 수신 동의 여부를 알려 드리는 메일입니다.") };
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
      if (!KEY) return json({ ok: false, error: "RESEND_API_KEY가 아직 없습니다" });
      const id = await send(admin.email!, { subject: "[테스트] " + m.subject, html: m.html }, w, kind === "digest");
      return json({ ok: true, id, to: admin.email });
    }
    if (body.action === "status") return json({ ok: true, key: !!KEY, from: FROM });
    return json({ ok: false, error: "action 필요" }, 400);
  } catch (e) {
    return json({ ok: false, error: String((e as Error)?.message || e) }, 500);
  }
});
