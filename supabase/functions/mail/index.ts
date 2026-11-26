// 회원 메일 (2026-11-05, 2026-11-23 개편, 2026-11-26 개편)
// - {action:"drain"}   : (5분마다) 대기열(mail_queue)의 메일을 만들어 Resend로 보낸다. RESEND_API_KEY가 없으면 보내지 않고 기다린다.
// - (2026-11-26 중단) 가입 뒤 D+1·D+3·D+7 안내 메일(kind d1/d3/d7, 서비스 안내): 가입 트리거가 not_before(아침 8:30 KST)와 함께 대기열에 넣고 drain이 시각이 되면 보낸다 (2026-11-10)
// - {action:"digest"}  : (매주 월 08:30 KST) 구독한 회원마다 주간 뉴스레터(Weekly Note)를 대기열에 넣고 바로 보낸다. 2년 지난 동의는 재확인 안내도 넣는다.
// - {action:"preview", kind} : (관리자) 메일 미리보기 HTML
// - {action:"test", kind}    : (관리자) 관리자 본인 메일로 한 통 보내기
// - 대기열 ref 가 "test-" 로 시작하면 제목에 [테스트]를 붙여 그 주소로 보낸다 (2026-11-26)
// 대표 검수 스위치(app_config.mail_live)가 켜져야 대기열 메일이 나간다 (2026-11-05)
// - POST ?unsub=토큰           : 메일 앱의 '수신 거부' 버튼(List-Unsubscribe 원클릭)
// verify_jwt = false (메일 앱이 원클릭 수신거부를 직접 호출하므로). 관리자 기능은 함수 안에서 확인한다.
// (2026-11-23 대표) 주간 메일은 회원이 직접 구독 신청한 뉴스레터다 → 제목에 (광고)를 붙이지 않는다.
//   대신 구독 해지 링크·보낸 곳·연락처는 그대로 두고, 아침~저녁에만 보낸다.
//   ※ 나중에 돈을 받고 싣는 광고·협찬, 유료 상품 판매 안내가 들어가면 그 메일은 광고성 정보라 (광고) 표기가 다시 필요하다.
// (2026-11-23 대표) 디자인은 현행 흑백 + 핑크(#FF4D6D) 밑줄 톤, 로고는 VALUE(굵게)+NOTE(얇게).
// (2026-11-26 대표) 메일은 가입 환영 1통 + 월요일 위클리만. 위클리는 지난 7일 블로그 글 전부 + 롱폼 전부 + 계기판 + 일정. D+1·3·7 안내는 중단.
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
/* 표기 규칙: "석 달" → "3달" (제1 원칙 40, 2026-11-23 대표) — 메일에 나가는 제목·요약에 늘 적용 */
const fixWords = (s: string) => String(s || "").replace(/석\s?달/g, "3달");

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
type Vid = { id: string; title: string };
let scoredN: number | null = null;
/* 계산하는 기업 수: c/scores.json 은 { date, c: { 종목: … } } 모양 */
async function scored() {
  if (scoredN !== null) return scoredN;
  try { const r = await fetch(SITE + "/c/scores.json"); const j = await r.json(); const c = j?.c ?? j; scoredN = Array.isArray(c) ? c.length : Object.keys(c || {}).length; } catch (_) { scoredN = 0; }
  if (scoredN < 50) scoredN = 0;
  return scoredN;
}
const companiesText = (n: number) => n ? `${Math.floor(n / 50) * 50}곳이 넘는` : "한국·미국 주요";

/* ---------- 메일 틀 (2026-11-23: 현행 흑백 + 핑크 포인트 톤) ---------- */
const F = `'SUIT Variable','SUIT','Pretendard','Apple SD Gothic Neo','Malgun Gothic','맑은 고딕',sans-serif`;
const WM = `'Montserrat','Helvetica Neue',Helvetica,Arial,sans-serif`;
/* 로고는 메일 앱 대부분이 웹 글꼴을 안 읽으므로 기본 글꼴로 굵기 대비(VALUE 800 / NOTE 300)를 낸다 */
const LOGO = `'Helvetica Neue',Helvetica,Arial,sans-serif`;
/* 검정 바탕 · 흰 글씨 · 회색 · 포인트는 핑크 하나 */
const DARK = "#111111", DARK2 = "#1F1F1F", PINK = "#FF4D6D", INK = "#111111", BODY = "#3A3A3A", MUTED = "#707070", LINE = "#E6E6E6", BG = "#F2F2F2";
const ON_DARK = "#BDBDBD", ON_DARK2 = "#8A8A8A";
const eyebrow = (t: string, c = PINK) => `<div style="font-family:${F};font-size:11px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:${c}">${t}</div>`;
const btn = (href: string, t: string, dark = true) => `<table role="presentation" cellpadding="0" cellspacing="0" style="margin:22px 0 2px"><tr><td style="background:${dark ? DARK : "#FFFFFF"};border-radius:999px"><a href="${href}" style="display:inline-block;padding:14px 26px;font-family:${F};font-size:14.5px;font-weight:700;letter-spacing:-.01em;color:${dark ? "#FFFFFF" : DARK};text-decoration:none;word-break:keep-all">${t}</a></td></tr></table>`;
/* 섹션 제목 아래 핑크 둥근 밑줄 (로고와 같은 모양) */
const pinkBar = (w = 28) => `<div style="width:${w}px;height:4px;background:${PINK};border-radius:2px;line-height:4px;font-size:1px;margin-top:12px">&nbsp;</div>`;
const h2 = (eb: string, t: string) => `<tr><td style="padding:44px 36px 14px">${eyebrow(eb, MUTED)}<div style="font-family:${F};font-size:22px;font-weight:800;letter-spacing:-.02em;line-height:1.4;color:${INK};margin-top:8px;word-break:keep-all">${t}</div>${pinkBar()}</td></tr>`;
const p = (t: string, extra = "") => `<p style="margin:0 0 14px;font-family:${F};font-size:16px;line-height:1.8;color:${BODY};word-break:keep-all;${extra}">${t}</p>`;
const tabUrl = (tab: string, src: string) => `${SITE}/?tab=${tab}&utm_source=mail&utm_medium=email&utm_campaign=${src}`;
const colUrl = (id: string, src: string) => `${SITE}/?col=${encodeURIComponent(id)}&utm_source=mail&utm_medium=email&utm_campaign=${src}`;
const ytUrl = (id: string, src: string) => `https://www.youtube.com/watch?v=${encodeURIComponent(id)}&utm_source=valuenote_mail&utm_campaign=${src}`;
function vidGrid(V: Vid[], src: string) {
  if (!V.length) return "";
  const cell = (v: Vid) => `<td width="50%" valign="top" style="padding:0 7px 20px"><a href="${ytUrl(v.id, src)}" style="text-decoration:none;color:${INK}">
    <img src="https://i.ytimg.com/vi/${esc(v.id)}/hqdefault.jpg" width="250" alt="" style="display:block;width:100%;height:auto;border-radius:12px">
    <div style="font-family:${F};font-size:15px;font-weight:700;letter-spacing:-.01em;line-height:1.5;margin-top:10px;word-break:keep-all">${esc(v.title)}</div></a></td>`;
  let rows = "";
  for (let i = 0; i < V.length; i += 2) rows += `<tr>${cell(V[i])}${V[i + 1] ? cell(V[i + 1]) : '<td width="50%"></td>'}</tr>`;
  return `<tr><td style="padding:0 29px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">${rows}</table></td></tr>`;
}
/* 푸터 채널 아이콘 (2026-11-24 대표: "푸터에 유튜브·인스타·블로그 아이콘으로 예쁘게") — 메일 앱은 SVG를 못 그려서 PNG(/brand/mail/mail-ic-*.png) */
const VN_KAKAO = "https://pf.kakao.com/_TxcBvX/friend";
const channels = (src: string) => {
  const ic = (href: string, k: string, alt: string) => `<td style="padding:0 6px"><a href="${href}" style="text-decoration:none"><img src="${SITE}/brand/mail/mail-ic-${k}.png" width="40" height="40" alt="${alt}" style="display:block;width:40px;height:40px;border:0"></a></td>`;
  return `<table role="presentation" cellpadding="0" cellspacing="0" align="center" style="margin:0 auto"><tr>
    ${ic(`https://www.youtube.com/@valuenote_korea?utm_source=valuenote_mail&utm_campaign=${src}`, "yt", "YouTube")}${ic("https://www.instagram.com/value.note.korea/", "ig", "Instagram")}${ic("https://blog.naver.com/valuenote_korea", "bl", "네이버 블로그")}${ic(VN_KAKAO, "kt", "카카오톡 채널")}${ic(`${SITE}/?utm_source=mail&utm_campaign=${src}`, "web", "밸류노트")}
  </tr></table>`;
};
/* 로고 (2026-11-16 확정 B안): 한 줄 'VALUE'(굵게) + 'NOTE'(얇게), 흰색 · 아래 핑크 둥근 밑줄 · 한글 '밸류노트'는 영문보다 작게 */
const wordmark = `<table role="presentation" cellpadding="0" cellspacing="0"><tr><td align="left">
  <div style="font-family:${LOGO};font-size:22px;color:#FFFFFF;letter-spacing:.06em;line-height:1;white-space:nowrap"><span style="font-weight:800">VALUE</span><span style="font-weight:300">NOTE</span></div>
  <div style="width:44px;height:4px;background:${PINK};border-radius:2px;line-height:4px;font-size:1px;margin-top:9px">&nbsp;</div>
  <div style="font-family:${F};font-size:10.5px;font-weight:600;letter-spacing:.32em;color:${ON_DARK};margin-top:8px">밸류노트</div></td></tr></table>`;
/* SUIT는 → 를 꺾쇠 모양으로 그려서, 화살표만 기본 글꼴로 그린다 (대표 기준: 화살표는 →) */
const ARW = `<span style="font-family:Arial,Helvetica,sans-serif;font-weight:400">→</span>`;
/* hero: 검정 첫 화면 — 위에 로고, 아래에 작은 핑크 라벨 + 큰 제목 + 한 줄 설명 (+ 버튼) */
function hero(eb: string, title: string, sub: string, cta?: [string, string]) {
  return `<tr><td style="background:${DARK};background-image:linear-gradient(160deg,${DARK2} 0%,${DARK} 55%,#000000 100%);padding:34px 36px 44px">
    ${wordmark}
    <div style="height:40px;line-height:40px;font-size:1px">&nbsp;</div>
    ${eyebrow(eb, PINK)}
    <div style="font-family:${F};font-size:28px;font-weight:800;letter-spacing:-.03em;line-height:1.38;color:#FFFFFF;margin-top:12px;word-break:keep-all">${title}</div>
    <div style="font-family:${F};font-size:16px;line-height:1.8;color:${ON_DARK};margin-top:14px;word-break:keep-all">${sub}</div>
    ${cta ? btn(cta[0], cta[1], false) : ""}
  </td></tr>`;
}
/* 메일 속 밸류노트 링크는 /go 를 거쳐 실제 브라우저(또는 설치한 앱)로 연다 (2026-11-05 대표). 수신 거부·구독 화면(/mail)은 그대로 */
const bridge = (h: string) => h
  .replace(/href="https:\/\/www\.valuenote\.co\.kr(\/[^"]*)"/g, (m, path: string) => path.startsWith("/mail") ? m : `href="${SITE}/go?to=${encodeURIComponent(path)}"`)
  .replace(/<a href=/g, '<a target="_blank" rel="noopener" href=');
function shell(pre: string, body: string, foot: string, src = "mail") {
  return bridge(`<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light"><title>밸류노트</title>
<style>@font-face{font-family:'SUIT Variable';font-weight:100 900;font-display:swap;src:url(${SITE}/fonts/SUIT-Variable.woff2) format('woff2')}@font-face{font-family:'Montserrat';font-weight:800;font-display:swap;src:url(${SITE}/fonts/montserrat-800.woff2) format('woff2')}
body{margin:0;padding:0;-webkit-font-smoothing:antialiased}a{text-decoration:none}@media (max-width:600px){.vn-wrap{padding:0!important}.vn-card{border-radius:0!important}}</style></head>
<body style="margin:0;padding:0;background:${BG}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">${esc(pre)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${BG}"><tr><td class="vn-wrap" align="center" style="padding:28px 12px">
<table class="vn-card" role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:#FFFFFF;border-radius:20px;overflow:hidden">
${body.replace(/→/g, ARW)}
<tr><td style="height:44px;line-height:44px;font-size:1px">&nbsp;</td></tr>
<tr><td align="center" style="background:${DARK};padding:34px 32px 32px;text-align:center">
  <div style="font-family:${LOGO};font-size:17px;color:#FFFFFF;letter-spacing:.06em;line-height:1"><span style="font-weight:800">VALUE</span><span style="font-weight:300">NOTE</span></div>
  <div style="width:32px;height:3px;background:${PINK};border-radius:2px;line-height:3px;font-size:1px;margin:8px auto 0">&nbsp;</div>
  <div style="font-family:${F};font-size:13px;color:${ON_DARK};margin:12px 0 18px;word-break:keep-all">유튜브 · 인스타 · 블로그 · 카카오톡에서도 만나요</div>
  ${channels(src)}
  <div style="height:1px;background:#2A2A2A;line-height:1px;font-size:1px;margin:26px 0 18px">&nbsp;</div>
  <div style="font-family:${F};font-size:12.5px;line-height:1.8;color:${ON_DARK2};word-break:keep-all">${foot}</div>
  <div style="font-family:${F};font-size:12.5px;line-height:1.8;color:${ON_DARK2};margin-top:8px;word-break:keep-all">밸류노트의 글과 영상은 공개된 자료를 정리한 것이며 특정 종목의 매수·매도를 권하지 않습니다.</div>
  <div style="font-family:${F};font-size:12.5px;line-height:1.8;color:${ON_DARK2};margin-top:8px">주식회사 더트러스티스 · 밸류노트(ValueNote) · <a href="mailto:${CONTACT}" style="color:${ON_DARK};text-decoration:underline">${CONTACT}</a></div>
</td></tr>
</table></td></tr></table></body></html>`);
}
const toText = (html: string) => html.replace(/<head[\s\S]*?<\/head>/g, "").replace(/<div style="display:none[^"]*">[\s\S]*?<\/div>/, "").replace(/<style[\s\S]*?<\/style>/g, "").replace(/<a [^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g, "$2 ($1)").replace(/<br\s*\/?>|<\/(p|div|tr|h\d)>/g, "\n").replace(/<[^>]+>/g, "").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/[ \t]+/g, " ").replace(/\n\s*\n+/g, "\n\n").trim();

/* ---------- 메일 종류별 ---------- */
type Who = { uid?: string; email: string; name?: string; ok?: boolean; consent_at?: string | null; token?: string; source?: string };
const unsubUrl = (w: Who) => w.token ? `${SITE}/mail?u=${w.token}` : `${SITE}/?tab=account`;
/* 뉴스레터 구독 상자 (가입 축하·D+7 공용, 2026-11-23: '광고성 정보' 문구 대신 뉴스레터 구독) */
const subscribeBox = (w: Who, src: string, title: string, desc: string, pad = "32px 36px 0") => `<tr><td style="padding:${pad}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${DARK};background-image:linear-gradient(150deg,${DARK2} 0%,${DARK} 60%);border-radius:18px"><tr><td style="padding:30px 28px">
      ${eyebrow("Weekly Note · 매주 월요일 08:30", PINK)}
      <div style="font-family:${F};font-size:21px;font-weight:800;letter-spacing:-.025em;line-height:1.45;color:#FFFFFF;margin-top:10px;word-break:keep-all">${title}</div>
      <div style="font-family:${F};font-size:15px;line-height:1.8;color:${ON_DARK};margin-top:12px;word-break:keep-all">${desc}</div>
      ${btn(w.token ? `${SITE}/mail?s=${w.token}` : tabUrl("account", src), "뉴스레터 구독하기 →", false)}
      <div style="font-family:${F};font-size:11px;line-height:1.7;color:${ON_DARK2};margin-top:12px;word-break:keep-all">버튼을 누른 뒤 열리는 화면에서 한 번 더 확인하면 구독됩니다. 선택 사항이며 언제든 해지할 수 있습니다.</div>
    </td></tr></table></td></tr>`;
/* 가입 축하 메일 (2026-11-24 대표: 계기판·칼럼·기능 소개 / 같은 날 오후 대표: "길고 텍스트가 많다 → 사진·스샷으로 직관적으로")
   순서: 첫 화면 → ① 내 종목 점수(앱 화면 사진) → ② 바닥 계기판(오늘 숫자 그대로, 앱 모양) → ③ 좋고 싼 회사 찾기(기업 지도 사진) → 칼럼 1편 → 뉴스레터 → 영상 2편
   문장은 섹션마다 한 줄. 앱 화면 사진은 /brand/mail/ (2026-11-24 캡처) */
type Sig = { name: string; on: boolean };
type GaugeNow = { name: string; on: number; asof: string; url: string; sigs: Sig[] };
async function gaugesNow(): Promise<GaugeNow[]> {
  const { data } = await sb.from("app_config").select("key,value").in("key", ["semi_gauge", "gold_gauge"]);
  const by: Record<string, any> = Object.fromEntries((data || []).map((r) => [r.key, r.value]));
  const sigs = (v: any): Sig[] => (Array.isArray(v?.signals) ? v.signals : []).slice(0, 5).map((s: any) => ({ name: String(s.name || "").replace(/^[①-⑤]\s*/, "").replace(/\(.*\)/, "").trim(), on: !!s.on }));
  const out: GaugeNow[] = [];
  if (typeof by.semi_gauge?.on === "number") out.push({ name: "반도체", on: by.semi_gauge.on, asof: by.semi_gauge.asof || "", url: `${SITE}/semi?from=mail`, sigs: sigs(by.semi_gauge) });
  if (typeof by.gold_gauge?.on === "number") out.push({ name: "금", on: by.gold_gauge.on, asof: by.gold_gauge.asof || "", url: `${SITE}/semi?tab=gold&from=mail`, sigs: sigs(by.gold_gauge) });
  return out;
}
/* 앱 계기판 화면과 같은 모양(검정 바탕 · 켜진 신호만 핑크)으로 그린다 — 사진이 아니라 매번 오늘 숫자로 그려서 날짜가 지나도 틀리지 않는다 */
function gaugeCard(x: GaugeNow) {
  const cells = x.sigs.map((s) => `<td width="20%" align="center" style="padding:0 3px"><div style="border:1.5px solid ${s.on ? PINK : "#3A3A3A"};border-radius:12px;padding:12px 0 10px;background:${s.on ? "#2A1418" : "#1A1A1A"}">
      <div style="width:12px;height:12px;border-radius:6px;margin:0 auto;background:${s.on ? PINK : "#4A4A4A"};line-height:12px;font-size:1px">&nbsp;</div>
      <div style="font-family:${F};font-size:13px;font-weight:700;color:${s.on ? "#FFFFFF" : "#8A8A8A"};margin-top:8px;white-space:nowrap">${esc(s.name)}</div></div></td>`).join("");
  const md = x.asof ? `${+x.asof.slice(5, 7)}/${+x.asof.slice(8, 10)} 마감 기준` : "";
  return `<tr><td style="padding:0 36px 12px"><a href="${x.url}" style="display:block;text-decoration:none"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${DARK};background-image:linear-gradient(160deg,#2A2A2A 0%,${DARK} 60%);border-radius:18px"><tr><td style="padding:20px 15px 18px">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
      <td style="padding:0 3px;font-family:${F};font-size:17px;font-weight:800;letter-spacing:-.02em;color:#FFFFFF;word-break:keep-all">${x.name} 바닥 계기판</td>
      <td align="right" style="padding:0 3px;font-family:${F};font-size:24px;font-weight:800;color:${PINK};white-space:nowrap">${x.on}<span style="font-size:14px;color:${ON_DARK}"> / 5</span></td></tr></table>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:14px"><tr>${cells}</tr></table>
    <div style="font-family:${F};font-size:13px;color:${ON_DARK2};margin-top:12px;padding:0 3px">${md}${md ? " · " : ""}<span style="color:#FFFFFF;font-weight:700">자세히 보기 →</span></div>
  </td></tr></table></a></td></tr>`;
}
/* 섹션: 번호 + 제목 + 한 줄 + (사진) + 버튼 */
const step = (n: number, t: string, d: string) => `<tr><td style="padding:44px 36px 16px">
  <table role="presentation" cellpadding="0" cellspacing="0"><tr><td valign="middle" style="padding-right:10px"><div style="width:28px;height:28px;border-radius:14px;background:${PINK};color:#FFFFFF;font-family:${F};font-size:14px;font-weight:800;line-height:28px;text-align:center">${n}</div></td>
  <td valign="middle" style="font-family:${F};font-size:21px;font-weight:800;letter-spacing:-.02em;color:${INK};word-break:keep-all">${t}</td></tr></table>
  <div style="font-family:${F};font-size:16px;line-height:1.75;color:${BODY};margin-top:10px;word-break:keep-all">${d}</div></td></tr>`;
const shot = (src: string, href: string, alt: string, cap = "") => `<tr><td style="padding:0 36px"><a href="${href}" style="display:block;text-decoration:none"><img src="${SITE}/brand/mail/${src}" width="528" alt="${alt}" style="display:block;width:100%;max-width:528px;height:auto;border-radius:16px;border:1px solid ${LINE}"></a>${cap ? `<div style="font-family:${F};font-size:13px;color:${MUTED};margin-top:8px;text-align:center">${cap}</div>` : ""}</td></tr>`;
const btnRow = (href: string, t: string) => `<tr><td style="padding:0 36px">${btn(href, t)}</td></tr>`;
async function welcome(w: Who) {
  /* 2026-11-26 대표: 메일이 너무 많고 길다 → 한 번만, 짧게. 점수 설명·칼럼·영상 목록은 뺀다 (D+1·3·7 안내 메일도 중단) */
  const [N, G] = await Promise.all([scored(), gaugesNow()]);
  const nm = w.name || w.email.split("@")[0], src = "welcome";
  const body = `${hero("Welcome to ValueNote", `${esc(nm)} 님,<br>환영합니다`,
      `버핏·그레이엄·멍거의 기준으로 ${companiesText(N)} 기업의 점수와 적정 주가를 매일 계산합니다.`, [tabUrl("portfolio", src), "밸류노트 열기 →"])}
  ${step(1, "내 종목, 몇 점일까", "종목 하나만 넣으면 버핏·그레이엄·멍거 기준 점수와 적정 주가가 바로 나옵니다.")}
  ${shot("welcome-company.jpg", tabUrl("portfolio", src), "종목 점수 화면", "예시 화면 · 특정 종목 추천이 아닙니다")}
  ${btnRow(tabUrl("portfolio", src), "내 종목 넣기 →")}
  ${step(2, "좋고 싼 회사 찾기", "점 하나가 회사 하나. 오른쪽 위로 갈수록 좋고 싼 회사입니다.")}
  ${shot("welcome-map.jpg", tabUrl("companies", src), "기업 지도")}
  ${btnRow(tabUrl("companies", src), "기업 지도 보기 →")}
  ${G.length ? step(3, "바닥 신호, 몇 개 켜졌나", "신호가 바뀌면 카카오톡·앱 알림으로 바로 알려 드립니다.") + G.map(gaugeCard).join("") : ""}
  ${w.ok ? "" : subscribeBox(w, src, "월요일 아침,<br>지난주를 한 통으로", "지난주 새 글과 영상, 계기판 변화를 정리해 매주 월요일 한 번 보냅니다. 언제든 해지할 수 있습니다.")}`;
  const consent = w.ok && w.consent_at
    ? `${kDate(w.consent_at)}에 밸류노트 뉴스레터를 구독하셨습니다. 매주 월요일 한 번 보내 드립니다. 원하지 않으시면 <a href="${unsubUrl(w)}" style="color:${ON_DARK};text-decoration:underline">구독 해지</a>를 누르세요.`
    : `이 메일은 밸류노트 가입 안내 메일이며 한 번만 보냅니다. 뉴스레터는 구독하신 분께만 매주 월요일 보냅니다.`;
  return { subject: `${nm} 님, 밸류노트 3분 사용법`, html: shell("내 종목 점수 · 기업 지도 · 바닥 계기판", body, consent, src) };
}
/* ===== 월요일 위클리 노트 (2026-11-26 대표 개편) =====
   "매주 월요일 정기 뉴스레터는 정말 좋은 내용, 저번 주 내용들이 촘촘하게 다 정리되고 유튜브까지 같이 소개하는 레터"
   지난 7일 블로그 글 전부(칼럼으로 옮겨졌으면 칼럼 링크) + 롱폼 전부(많이 본 순) + 바닥 계기판 + 다가오는 일정 */
type Post = { id: string; title: string; cat: string; sum: string; cover: string; col?: string };
const CAT_ORDER: [string, string, string][] = [["기업 분석", "기업 이야기", "Company Stories"], ["거장의 투자", "거장의 투자", "Great Investors"], ["투자 상식", "투자 상식", "Basics"], ["주간 시장 정리", "시장 정리", "Market"], ["밸류노트 사용법", "사용법", "Guide"]];
async function blogWeek(days = 7): Promise<Post[]> {
  const { data } = await sb.from("docs").select("data").eq("collection", "naver").eq("id", "posted").maybeSingle();
  const posted: Record<string, string> = (data?.data as any)?.posted || {}, cleared: string[] = (data?.data as any)?.cleared || [];
  const today = Date.parse(ymd(kst()));
  const ids = Object.keys(posted).filter((k) => /^[ab]\d{6}/.test(k) && !cleared.includes(k) && k !== "b261020x").filter((k) => {
    const t = Date.UTC(2000 + +k.slice(1, 3), +k.slice(3, 5) - 1, +k.slice(5, 7)); const age = (today - t) / 864e5; return age >= 1 && age <= days;
  }).sort();
  const out: Post[] = [];
  for (const id of ids) {
    try {
      const r = await fetch(`${SITE}/naver/${id}/post.json`); if (!r.ok) continue; const j = await r.json();
      const bl = (j.blocks || []) as any[];
      const sum = fixWords(((bl.find((x) => x.summary)?.summary || []) as string[]).join(" ") || String(bl.find((x) => x.p)?.p || "")).replace(/\*\*/g, "").replace(/\s+/g, " ").trim();
      const cv = bl.find((x) => x.kind === "cover" && x.img)?.img;
      out.push({ id, title: fixWords(j.title || ""), cat: j.category || "기업 분석", sum: sum.length > 150 ? sum.slice(0, 150).replace(/\s\S*$/, "") + "…" : sum, cover: cv ? `${SITE}/naver/${id}/${cv}` : "" });
    } catch (_) { /* 글 하나 못 읽어도 나머지는 보낸다 */ }
  }
  if (out.length) {   // 칼럼으로 옮겨진 글은 앱 칼럼으로 연결 (사이트 유입)
    const { data: C } = await sb.from("docs").select("id,data").eq("collection", "trends").like("id", "col-%").in("data->>from", out.map((b) => "naver/" + b.id));
    for (const c of C || []) { const b = out.find((x) => "naver/" + x.id === (c.data as any)?.from); if (b && !(c.data as any)?.hidden) b.col = c.id; }
  }
  return out;
}
async function upcoming(days = 14) {
  const d0 = ymd(kst()), d1 = ymd(new Date(kst().getTime() + days * 864e5));
  const { data } = await sb.from("issue_events").select("day,title").gte("day", d0).lte("day", d1).order("day").limit(6);
  return (data || []) as { day: string; title: string }[];
}
const postHref = (b: Post, src: string) => b.col ? colUrl(b.col, src) : `${SITE}/naver/${b.id}.html?utm_source=mail&utm_medium=email&utm_campaign=${src}`;
function postBig(b: Post, src: string) {
  return `<tr><td style="padding:0 36px 8px"><a href="${postHref(b, src)}" style="text-decoration:none;color:${INK}">
    ${b.cover ? `<img src="${esc(b.cover)}" width="528" alt="" style="display:block;width:100%;max-width:528px;height:auto;border-radius:14px">` : ""}
    <div style="font-family:${F};font-size:20px;font-weight:800;letter-spacing:-.02em;line-height:1.45;margin:16px 0 8px;word-break:keep-all">${esc(b.title)}</div>
    <div style="font-family:${F};font-size:15px;line-height:1.75;color:${BODY};word-break:keep-all">${esc(b.sum)}</div>
    <div style="font-family:${F};font-size:13.5px;font-weight:700;color:${INK};margin-top:12px"><span style="border-bottom:3px solid ${PINK};padding-bottom:2px">이어서 읽기</span> →</div></a></td></tr>`;
}
function postLine(b: Post, src: string, last: boolean) {
  return `<tr><td style="padding:0 36px"><a href="${postHref(b, src)}" style="text-decoration:none;color:${INK}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="${last ? "" : `border-bottom:1px solid ${LINE};`}"><tr>
    ${b.cover ? `<td width="88" valign="top" style="padding:16px 14px 16px 0"><img src="${esc(b.cover)}" width="88" alt="" style="display:block;width:88px;height:auto;border-radius:10px"></td>` : ""}
    <td valign="top" style="padding:16px 0"><div style="font-family:${F};font-size:16px;font-weight:700;letter-spacing:-.015em;line-height:1.5;word-break:keep-all">${esc(b.title)}</div>
    <div style="font-family:${F};font-size:13.5px;line-height:1.65;color:${MUTED};margin-top:4px;word-break:keep-all">${esc(b.sum.slice(0, 70))}${b.sum.length > 70 ? "…" : ""}</div></td></tr></table></a></td></tr>`;
}
type VidV = Vid & { views: number };
async function videosV(days: number, n: number): Promise<VidV[]> {
  const now = new Date().toISOString();
  const { data } = await sb.from("youtube_posts").select("youtube_id,title,scheduled_at,stats").not("youtube_id", "is", null).eq("kind", "long").eq("status", "uploaded").lte("scheduled_at", now).gte("scheduled_at", new Date(Date.now() - days * 864e5).toISOString()).limit(30);
  const views = (v: any) => Math.max(Number(v?.stats?.api?.views) || 0, Number(v?.stats?.public?.views) || 0);
  return (data || []).map((v) => ({ id: v.youtube_id, title: fixWords(v.title), views: views(v) })).sort((a, b) => b.views - a.views).slice(0, n);
}
function vidBig(v: VidV, src: string) {
  return `<tr><td style="padding:0 36px 6px"><a href="${ytUrl(v.id, src)}" style="text-decoration:none;color:${INK}">
    <img src="https://i.ytimg.com/vi/${esc(v.id)}/hqdefault.jpg" width="528" alt="" style="display:block;width:100%;max-width:528px;height:auto;border-radius:14px">
    <div style="font-family:${F};font-size:19px;font-weight:800;letter-spacing:-.02em;line-height:1.45;margin-top:14px;word-break:keep-all">${esc(v.title)}</div>
    <div style="font-family:${F};font-size:13.5px;color:${MUTED};margin-top:6px">조회수 ${v.views.toLocaleString("ko-KR")}회 · 지난주 가장 많이 본 영상</div></a></td></tr>`;
}
function calendar(E: { day: string; title: string }[]) {
  if (!E.length) return "";
  const rows = E.map((e, i) => `<tr><td width="74" style="padding:12px 0;${i ? `border-top:1px solid ${LINE};` : ""}font-family:${F};font-size:15px;font-weight:800;color:${PINK};white-space:nowrap">${+e.day.slice(5, 7)}/${+e.day.slice(8, 10)}</td><td style="padding:12px 0;${i ? `border-top:1px solid ${LINE};` : ""}font-family:${F};font-size:15.5px;color:${INK};word-break:keep-all">${esc(e.title)}</td></tr>`).join("");
  return h2("Coming Up", "다음에 볼 일정") + `<tr><td style="padding:0 36px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">${rows}</table></td></tr>`;
}
async function digest(w: Who) {
  const [B, V, G, E] = await Promise.all([blogWeek(7), videosV(7, 8), gaugesNow(), upcoming(14)]);
  if (!B.length && !V.length) return null;
  const src = "weekly", top = B.find((b) => b.cover) || B[0];
  const totalV = V.reduce((s, v) => s + v.views, 0);
  const groups = CAT_ORDER.map(([k, t, en]) => [t, en, B.filter((b) => b.cat === k && b !== top)] as [string, string, Post[]]);
  const etc = B.filter((b) => b !== top && !CAT_ORDER.some(([k]) => k === b.cat));
  if (etc.length) groups.push(["그 밖의 글", "More", etc]);
  const body = `${hero(`Weekly Note · ${weekLabel()}`, "지난주 밸류노트,<br>한 통으로 정리했습니다",
      `글 ${B.length}편 · 영상 ${V.length}편 · 바닥 계기판까지. 월요일 아침 5분이면 지난주를 따라잡습니다.`)}
  <tr><td style="padding:28px 36px 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${BG};border-radius:14px"><tr>
    ${[[B.length + "편", "새 글"], [V.length + "편", "새 영상"], [(totalV >= 10000 ? Math.round(totalV / 10000) + "만" : totalV.toLocaleString("ko-KR")) + " 회", "영상 조회수"]].map(([n, t]) => `<td align="center" width="33%" style="padding:16px 4px"><div style="font-family:${F};font-size:22px;font-weight:800;color:${INK}">${n}</div><div style="font-family:${F};font-size:12.5px;color:${MUTED};margin-top:2px">${t}</div></td>`).join("")}
  </tr></table></td></tr>
  ${G.length ? h2("Gauges", "바닥 계기판, 지금 몇 개 켜졌나") + G.map(gaugeCard).join("") : ""}
  ${V.length ? h2("On YouTube", "지난주 영상") + vidBig(V[0], src) + (V.length > 1 ? `<tr><td style="height:18px;line-height:18px;font-size:1px">&nbsp;</td></tr>` + vidGrid(V.slice(1, 7), src) : "") : ""}
  ${top ? h2("Top Story", "지난주 가장 읽어 볼 만한 글") + postBig(top, src) : ""}
  ${groups.filter(([, , L]) => L.length).map(([t, en, L]) => h2(en, `${t} ${L.length}편`) + L.map((b, i) => postLine(b, src, i === L.length - 1)).join("")).join("")}
  ${calendar(E)}
  <tr><td style="padding:24px 36px 0">${btn(tabUrl("column", src), "밸류노트에서 더 보기 →")}</td></tr>`;
  const foot = `이 메일은 ${w.consent_at ? kDate(w.consent_at) + "에 " : ""}밸류노트 뉴스레터를 구독하신 분께 매주 월요일 아침에 보내 드립니다. 더 받지 않으시려면 <a href="${unsubUrl(w)}" style="color:${ON_DARK};text-decoration:underline;font-weight:700">구독 해지</a>를 누르세요. 한 번 누르면 바로 처리됩니다.`;
  /* 제목: (광고) 없이 뉴스레터 이름 + 지난주 가장 많이 본 영상(없으면 대표 글) */
  const head = V[0] ? V[0].title.split("|")[0].trim() : top.title;
  return { subject: `[밸류노트 위클리] ${head}`, html: shell(`${top ? top.title + " 외 " : ""}글 ${B.length}편 · 영상 ${V.length}편`, body, foot, src) };
}
function consentMail(w: Who, on: boolean, at: string) {
  const body = `${hero("Notice", `뉴스레터 ${on ? "구독" : "구독 해지"}가<br>처리됐습니다`, `${esc(w.email)} 주소로 요청하신 밸류노트 뉴스레터 ${on ? "구독" : "구독 해지"}를 ${kDateTime(at)}에 처리했습니다.`)}
  <tr><td style="padding:36px 36px 0">${p(on ? "매주 월요일 아침 8시 30분, 지난주 밸류노트의 글과 새 영상, 바닥 계기판을 한 통에 정리해 보내 드립니다. 언제든 메일 아래 구독 해지 링크나 앱의 내 계정에서 끌 수 있습니다." : "앞으로 뉴스레터는 보내지 않습니다. 가입·계정 관련 안내처럼 꼭 필요한 메일만 보냅니다. 다시 받고 싶으시면 앱의 내 계정에서 켤 수 있습니다.")}
  ${on ? "" : btn(tabUrl("account", "consent"), "내 계정 열기 →")}</td></tr>`;
  return { subject: `[밸류노트] 뉴스레터 ${on ? "구독" : "구독 해지"} 처리 안내`, html: shell(`뉴스레터 ${on ? "구독" : "구독 해지"}를 처리했습니다.`, body, "구독·해지 처리 결과를 알려 드리는 메일입니다.", "consent") };
}
function reconfirmMail(w: Who) {
  const body = `${hero("Notice", "뉴스레터 구독을<br>확인해 주세요", `${w.consent_at ? kDate(w.consent_at) + "에 " : ""}밸류노트 뉴스레터를 구독하셨습니다. 2년마다 구독 여부를 다시 알려 드립니다.`)}
  <tr><td style="padding:36px 36px 0">${p("계속 받으시려면 아무것도 하지 않으셔도 됩니다. 그만 받으시려면 아래 버튼을 눌러 주세요.")}${btn(unsubUrl(w), "뉴스레터 그만 받기")}</td></tr>`;
  return { subject: "[밸류노트] 뉴스레터 구독 확인 안내", html: shell("2년마다 구독 여부를 알려 드립니다.", body, "2년마다 구독 여부를 알려 드리는 메일입니다.", "reconfirm") };
}


/* ---------- 보내기 ---------- */
async function send(to: string, m: { subject: string; html: string }, w?: Who, kind = "service") {
  const headers: Record<string, string> = {};
  if (w?.token) { headers["List-Unsubscribe"] = `<${URL_}/functions/v1/mail?unsub=${w.token}>, <mailto:${CONTACT}?subject=unsubscribe>`; headers["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"; }
  const r = await fetch("https://api.resend.com/emails", { method: "POST", headers: { Authorization: `Bearer ${KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from: FROM, to: [to], reply_to: REPLY, subject: m.subject, html: m.html, text: toText(m.html), headers, tags: [{ name: "kind", value: kind }] }) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j?.message || j?.name || `HTTP ${r.status}`);
  return j.id as string;
}
async function who(uid: string | null, email: string): Promise<Who> {
  const w: Who = { uid: uid || undefined, email };
  if (uid) {
    const { data: p } = await sb.from("mail_prefs").select("ok,consent_at,token,source").eq("uid", uid).maybeSingle();
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
  const { data: Q } = await sb.from("mail_queue").select("*").eq("status", "queued").lt("tries", 5).lte("not_before", new Date().toISOString()).order("created_at").limit(40);
  if (!Q?.length) return { ok: true, sent: 0 };
  await loadKey();
  if (!KEY) return { ok: false, waiting: Q.length, reason: "RESEND_API_KEY 없음 · 키를 넣으면 대기 중인 메일부터 보냅니다" };
  const { data: live } = await sb.from("app_config").select("value").eq("key", "mail_live").maybeSingle();
  if (live?.value !== true) return { ok: false, waiting: Q.length, reason: "대표 검수 전 · 관리자 메일 탭에서 '검수 완료 · 발송 시작'을 누르면 보냅니다" };
  let sent = 0, failed = 0, held = 0;
  for (const q of Q) {
    const news = q.kind === "digest";
    if (news && !daytime()) { held++; continue; }                     // 뉴스레터도 21~08시에는 보내지 않는다
    const w = await who(q.uid, q.email);
    const isTest = String(q.ref || "").startsWith("test-");
    if (isTest) { w.ok = true; if (!w.consent_at) w.consent_at = new Date().toISOString(); if (!w.token) w.token = "00000000-0000-0000-0000-000000000000"; }
    if (news && !w.ok) { await sb.from("mail_queue").update({ status: "skipped", error: "구독 해지됨" }).eq("id", q.id); continue; }
    if (isTest && q.kind === "welcome") w.ok = false;
    if (q.kind === "welcome" && Date.now() - Date.parse(q.created_at) > 8 * 864e5) { await sb.from("mail_queue").update({ status: "skipped", error: "가입 8일이 지나 보내지 않음" }).eq("id", q.id); continue; }
    if (q.kind === "d1" || q.kind === "d3" || q.kind === "d7") { await sb.from("mail_queue").update({ status: "skipped", error: "2026-11-26 대표: 첫 주 안내 메일(D+1·3·7) 중단" }).eq("id", q.id); continue; }
    try {
      const m = await build(q, w);
      if (!m) { await sb.from("mail_queue").update({ status: "skipped", error: "보낼 내용 없음" }).eq("id", q.id); continue; }
      const id = await send(q.email, isTest ? { ...m, subject: "[테스트] " + m.subject } : m, w, news ? "newsletter" : "service");
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
    if (tok && req.method === "POST") {
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
      if (kind === "welcome" && body.as !== "sub") { w.ok = false; w.consent_at = null; }
      else { w.ok = true; if (!w.consent_at) w.consent_at = new Date().toISOString(); }
      const m = await build({ kind, ref: "on:preview" }, w);
      if (!m) return json({ ok: false, error: "지난주에 보낼 글·영상이 없습니다" });
      if (body.action === "preview") return json({ ok: true, subject: m.subject, html: m.html });
      await loadKey();
      if (!KEY) return json({ ok: false, error: "RESEND_API_KEY가 아직 없습니다" });
      const id = await send(admin.email!, { subject: "[테스트] " + m.subject, html: m.html }, w, kind === "digest" ? "newsletter" : "service");
      return json({ ok: true, id, to: admin.email });
    }
    if (body.action === "status") { await loadKey(); return json({ ok: true, key: !!KEY, from: FROM }); }
    return json({ ok: false, error: "action 필요" }, 400);
  } catch (e) {
    return json({ ok: false, error: String((e as Error)?.message || e) }, 500);
  }
});
