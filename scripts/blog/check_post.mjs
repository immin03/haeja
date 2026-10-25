// 네이버 블로그 글 출고 전 점검 (2026-10-19 도입: AI 양산 글로 걸러지지 않게)
// 사용: node scripts/blog/check_post.mjs naver/<id> [naver/<id> ...]
//   오류(✗)가 하나라도 있으면 종료 코드 1. 경고(!)는 읽고 판단한다.
//
// 네이버는 'AI가 썼는지'가 아니라 원본성·정보 가치·구조 반복·사실 오류를 본다. 그래서 점검하는 것은:
//  1. 원본 데이터: 밸류노트만 가진 사진(img.kind = "chart" | "app" | "data") 2장 이상, 그중 그래프나 앱 화면 1장 이상
//  2. 정답 먼저: 소제목 바로 아래는 문단으로 시작하고, 그 첫 문장이 그 단락의 답(사실·숫자)을 말한다
//  3. 구조 반복: 최근 글과 블록 순서(뼈대)가 거의 같으면 경고
//  4. 문장 복사: 다른 글과 같은 문장(20자 이상)이 있으면 오류
//  5. 사실 표: post.json "facts" 에 제목·요약·소제목의 모든 숫자의 출처가 있어야 한다
//  6. 금지어·AI 상투어·제목 형식·태그·필명·고지 문구
//  7. AI 문체(번역투·AI 관용구·연결어미 쉼표·종결어미 반복): scripts/humanize_ko.mjs, 규칙은 scripts/CONTENT.md 6절
// post.json 추가 필드:
//   img 블록의 "kind": "cover"(실사 사진 표지) | "photo"(무료 실사 사진) | "chart"(실제 데이터 그래프) | "app"(실제 앱 화면) | "data"(밸류노트 점수·적정 주가 계산 카드) | "card"(글자·인용 카드, 1장까지) | "banner"
//   실사 사진·영상·표지에는 "src": "mixkit:<번호>" 또는 "pexels:<번호>" (scripts/blog/media/lib/index.json 의 id)
//   img 블록의 "kind": "gif" = 움직이는 실사 사진 (2026-10-19부터 영상 대신. scripts/blog/to_gif.sh)
//   {"video": ...} 영상 블록은 예전 형식 — 새 글에서는 오류
//   "facts": [{"t": "확인한 사실(숫자 포함)", "src": "출처 URL 또는 'VN'(밸류노트 데이터)"}, ...]
import fs from 'node:fs';
import path from 'node:path';
import { scanKo, textFromFile } from '../humanize_ko.mjs';

const dirs = process.argv.slice(2);
if (!dirs.length) { console.error('사용법: node scripts/blog/check_post.mjs naver/<id> ...'); process.exit(1); }
const ROOT = path.dirname(path.resolve(dirs[0]));
const load = (d) => JSON.parse(fs.readFileSync(path.join(d, 'post.json'), 'utf8'));
const strip = (s) => String(s || '').replace(/\*\*/g, '');
const sentences = (s) => strip(s).split(/(?<=[.?!])\s+/).map((x) => x.trim()).filter(Boolean);
const textOf = (p) => [p.title, ...p.blocks.flatMap((b) => [b.h, b.p, b.cap, b.quote, ...(b.summary || []), ...(b.table ? [b.table.head, ...b.table.rows].flat() : [])])].filter(Boolean).map(strip).join(' ');
const bodyLen = (p) => p.blocks.reduce((n, b) => n + strip(b.p || '').length + strip(b.h || '').length + (b.summary || []).join('').length, 0);
const sig = (p) => p.blocks.map((b) => b.h ? 'H' : b.summary ? 'S' : b.table ? 'T' : b.quote ? 'Q' : b.note ? 'N' : b.img ? 'I' : 'P').join('');
const nums = (s) => (strip(s).match(/\d[\d,.]*/g) || []).map((x) => x.replace(/[.,]$/, '')).filter((x) => x.replace(/[,.]/g, '').length >= 1);
// 같은 문장으로 보지 않는 고정 문장
const FIXED = [/에디터 Luciano입니다\.?$/, /^안녕하세요, 밸류노트 에디터 Luciano입니다\.?$/, /^— Editor: Luciano$/, /이 글은 투자 교육용 정보이며/, /밸류노트 에디터 Luciano가 작성했습니다/, /미래 주가를 보장하지 않습니다/];
const BANNED = ['적정가 ', '적정가는', '적정가가', '적정 가격', '내재가치', '품질 점수', '저평가 점수', '무료', '유료', '매수 후보', '싸다', '비싸다'];
const SLOP = ['결론적으로', '종합적으로', '요약하자면', '다양한 측면', '라고 할 수 있습니다', '매우 중요합니다', '필수적입니다', '살펴보았습니다', '알아보았습니다', '도움이 되셨길', '도움이 되셨으면', '시사하는 바가 큽니다', '주목할 만합니다', '눈여겨볼 필요가', '것은 분명합니다'];

// ── 밸류노트 숫자 대조 ─────────────────────────────
// c/scores.json: slug → [이름, 밸류노트 점수, 재무 점수, 가격 점수, 시장, 저평가%, 업종]. 적정 주가는 c/<slug>.html 제목에서 읽는다.
const SITE = path.resolve(ROOT, '..', 'c');
let VN = null;
function vnData() {
  if (VN) return VN;
  try { VN = JSON.parse(fs.readFileSync(path.join(SITE, 'scores.json'), 'utf8')); } catch (_) { VN = { c: {} }; }
  return VN;
}
function fairOf(slug) {
  try { const t = (fs.readFileSync(path.join(SITE, slug + '.html'), 'utf8').match(/<title>[^<]*적정 주가 ([^ ·<]+)/) || [])[1]; return t || null; } catch (_) { return null; }
}
const numOf = (s) => { const v = parseFloat(String(s).replace(/[^\d.]/g, '')); return isFinite(v) ? v : null; };
function checkVN(p) {
  const out = [], C = vnData().c || {};
  const names = Object.entries(C).filter(([, r]) => r && r[0] && r[0].length >= 2).map(([slug, r]) => ({ slug, n: r[0], b: r[1], q: r[2], v: r[3] }));
  const blocks = p.blocks.flatMap((b) => [b.h, b.p, b.cap, ...(b.summary || []), ...(b.table ? b.table.rows.map((r) => r.join(' ')) : [])]).filter(Boolean).map(strip);
  const seen = new Set();
  for (const txt of blocks) for (const sen of sentences(txt)) {
    const hits = names.filter((x) => sen.includes(x.n)); if (!hits.length) continue;
    // 문장에 회사가 하나만 나올 때만 대조 (여러 회사를 나열한 문장은 짝을 정확히 알 수 없다)
    if (hits.length > 1 && !hits.every((h) => hits.some((o) => o !== h && o.n.includes(h.n)))) continue;
    const x = hits.sort((a, b) => b.n.length - a.n.length)[0];
    const dated = /\d+월\s*\d+일/.test(sen);
    const pairs = [['밸류노트 점수', x.b], ['재무 점수', x.q], ['가격 점수', x.v]];
    for (const [label, cur] of pairs) {
      const m = sen.match(new RegExp(label + '(?:는|은|가|이)?\\s*(?:100점 만점에\\s*)?(\\d{1,3})점'));
      if (!m || cur == null) continue;
      const said = +m[1], d = Math.abs(said - cur), key = x.slug + label + said; if (seen.has(key)) continue; seen.add(key);
      if (d >= 3) out.push({ err: !dated, msg: `${x.n} ${label} ${said}점 — 지금 계산은 ${cur}점${dated ? ' (날짜를 밝힌 문장이라 경고만)' : ''}` });
      else if (d > 0) out.push({ err: false, msg: `${x.n} ${label} ${said}점 — 지금 ${cur}점 (작은 차이)` });
    }
    const fm = sen.match(/적정 주가(?:는|은|가|이)?\s*(?:약\s*)?((?:HK\$|\$)?[\d,]+(?:\.\d+)?(?:원|엔|위안)?)/);
    if (fm) {
      const said = numOf(fm[1]), curS = fairOf(x.slug), cur = curS ? numOf(curS) : null, key = x.slug + 'iv' + said;
      if (said && cur && !seen.has(key)) { seen.add(key); const r = Math.abs(said / cur - 1);
        if (r > 0.03) out.push({ err: !dated, msg: `${x.n} 적정 주가 ${fm[1]} — 지금 계산은 ${curS}${dated ? ' (날짜를 밝힌 문장이라 경고만)' : ''}` }); }
    }
  }
  return out;
}

const all = fs.readdirSync(ROOT).filter((d) => fs.existsSync(path.join(ROOT, d, 'post.json'))).map((d) => ({ id: d, p: load(path.join(ROOT, d)) }));
let bad = 0;
for (const dir of dirs) {
  const id = path.basename(dir), p = load(dir), E = [], W = [];
  const others = all.filter((o) => o.id !== id);
  // 제목
  if (/[:：]/.test(p.title)) E.push('제목에 콜론이 있습니다');
  if ((p.title.match(/\?/g) || []).length > 1 || /!/.test(p.title)) E.push('제목에 물음표 여러 개 또는 느낌표가 있습니다');
  if (p.title.length < 28 || p.title.length > 46) W.push(`제목 ${p.title.length}자 (30~45자 권장)`);
  if (!/\d/.test(p.title)) W.push('제목에 숫자가 없습니다');
  // 길이
  const len = bodyLen(p);
  if (len < 2000 || len > 3600) W.push(`본문 ${len}자 (2,000~3,500자)`);
  // 사진
  const imgs = p.blocks.filter((b) => b.img && !b.href);
  const orig = imgs.filter((b) => ['chart', 'app', 'data'].includes(b.kind));
  const K = (k) => imgs.filter((b) => b.kind === k);
  if (imgs.some((b) => !b.kind)) E.push(`kind 가 없는 사진: ${imgs.filter((b) => !b.kind).map((b) => b.img).join(', ')}`);
  if (orig.length < 2) E.push(`원본 데이터 사진(chart·app·data) ${orig.length}장 — 2장 이상 필요`);
  if (!imgs.some((b) => b.kind === 'chart' || b.kind === 'app')) E.push('실제 데이터 그래프(chart) 또는 앱 화면(app)이 한 장도 없습니다');
  // 실사 사진·영상 (2026-10-19 결정: 카드 디자인이 많을수록 AI 글처럼 보인다)
  const cover = p.blocks[0];
  if (!cover?.img || cover.kind !== 'cover') E.push('첫 블록이 표지 사진(kind cover)이 아닙니다');
  else if (!cover.src) E.push('표지가 실사 사진 표지(kit photocover)가 아닙니다 — 표지에 쓴 사진의 src 를 다세요');
  if (K('photo').length < 2) E.push(`실사 사진(photo) ${K('photo').length}장 — 2장 이상 필요 (scripts/blog/media/lib)`);
  if (K('card').length > 1) E.push(`글자 카드(card) ${K('card').length}장 — 1장까지 (나머지는 실사 사진·그래프·앱 화면으로)`);
  if (K('data').length > 2) W.push(`점수·계산 카드(data) ${K('data').length}장 — 2장까지 권장`);
  const media = [...imgs.filter((b) => b.kind === 'photo' || b.kind === 'gif'), ...p.blocks.filter((b) => b.video)];
  if (media.some((b) => !b.src)) E.push(`출처(src)가 없는 실사 사진·영상: ${media.filter((b) => !b.src).map((b) => b.img || b.video).join(', ')}`);
  if (p.blocks.some((b) => b.video)) E.push('영상(video) 블록 대신 GIF(kind gif)를 씁니다 — bash scripts/blog/to_gif.sh <mp4> naver/<id>/g1.gif');
  if (!K('gif').length) W.push('움직이는 사진(gif)이 없습니다 — 짧은 실사 GIF 1개를 권장합니다');
  const coNames = Object.values(vnData().c || {}).map((r) => r && r[0]).filter((n) => n && n.length >= 2);
  for (const b of media) { const hit = coNames.find((n) => strip(b.cap || b.alt || '').includes(n)); if (hit) E.push(`실사 사진·영상 설명(alt)에 회사 이름("${hit}")이 있습니다 — 무료 소재는 그 회사가 아니므로 "자동차 조립 라인"처럼 일반 설명으로`); }
  for (let i = 1; i < p.blocks.length; i++) { const a = p.blocks[i - 1], b = p.blocks[i]; if (a.img && b.img && !a.href && !b.href && !['photo', 'gif'].includes(a.kind) && !['photo', 'gif'].includes(b.kind) && i > 1) W.push(`디자인 사진 두 장이 붙어 있습니다: ${a.img}, ${b.img}`); }
  const stills = imgs.filter((b) => b.kind !== 'gif').length;
  if (stills < 5 || stills > 8) W.push(`사진 ${stills}장 (GIF 빼고 5~7장)`);
  // 사진 설명 (2026-10-19 결정): 사진 밑 설명 문장은 AI 같아 보인다. 실사 사진·영상·표지는 설명 없음, 데이터 이미지는 짧은 명사로
  for (const b of p.blocks.filter((x) => (x.img || x.video) && !x.href)) {
    if (b.cap && (b.video || ['photo', 'gif', 'cover'].includes(b.kind))) E.push(`${b.img || b.video}: 실사 사진·GIF·표지에는 설명(cap)을 달지 않습니다 (alt 만)`);
    else if (b.cap && (/[다요]\.?$|[.:?!]/.test(b.cap.trim()) || b.cap.length > 30)) E.push(`${b.img}: 설명은 30자 이내의 명사로 끝냅니다 — "${b.cap}"`);
  }
  if (imgs.length && imgs.every((b) => b.kind === imgs[0].kind)) W.push('사진 종류가 한 가지뿐입니다');
  // 정답 먼저: 소제목 바로 아래 블록은 문단, 첫 문장은 70자 이내로 그 단락의 답을 말한다
  const leads = [];
  p.blocks.forEach((b, i) => {
    if (!b.h) return;
    const nx = p.blocks[i + 1];
    if (!nx || !nx.p) { E.push(`소제목 "${b.h}" 아래가 문단이 아니라 ${nx ? (nx.img ? '사진' : nx.table ? '표' : '다른 블록') : '없음'}입니다 (답 문장을 먼저)`); return; }
    const first = sentences(nx.p)[0] || '';
    leads.push(`${b.h} → ${first}`);
    if (first.length > 75) W.push(`리드 문장이 깁니다(${first.length}자): ${first.slice(0, 40)}…`);
  });
  const hs = p.blocks.filter((b) => b.h);
  if (hs.length < 3 || hs.length > 6) W.push(`소제목 ${hs.length}개 (3~6개)`);
  if (hs.filter((b) => /\?$/.test(b.h)).length > 1) E.push('물음표 소제목이 2개 이상입니다');
  // 구조 반복
  const s = sig(p);
  const recent = others.slice().sort((a, b) => b.id.localeCompare(a.id)).slice(0, 14);
  const lev = (a, b) => { const d = Array.from({ length: a.length + 1 }, (_, i) => [i]); for (let j = 1; j <= b.length; j++) d[0][j] = j; for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)); return d[a.length][b.length]; };
  for (const o of recent) { const r = 1 - lev(s, sig(o.p)) / Math.max(s.length, sig(o.p).length); if (r >= 0.88) W.push(`뼈대가 ${o.id}와 ${Math.round(r * 100)}% 같습니다 (블록 순서·소제목 수를 바꿔 보세요)`); }
  // 문장 복사
  const mine = new Set(p.blocks.flatMap((b) => sentences(b.p)).filter((x) => x.length >= 20 && !FIXED.some((re) => re.test(x))));
  for (const o of others) for (const x of o.p.blocks.flatMap((b) => sentences(b.p))) if (mine.has(x)) E.push(`${o.id}와 같은 문장: ${x.slice(0, 50)}`);
  // 같은 날 핵심어
  const day = (id.match(/^b(\d{6})/) || [])[1];
  if (day) for (const o of others.filter((o) => o.id.startsWith('b' + day))) if ((o.p.tags || [])[0] && o.p.tags[0] === (p.tags || [])[0]) E.push(`같은 날 ${o.id}와 첫 태그(핵심어)가 같습니다`);
  // 금지어·상투어
  const T = textOf(p);
  for (const w of BANNED) if (T.includes(w)) E.push(`쓰지 않는 말: "${w.trim()}"`);
  const slop = SLOP.filter((w) => T.includes(w));
  if (slop.length) W.push(`AI 상투어: ${slop.join(', ')}`);
  // AI 문체 (2026-10-26 운영자 결정, CONTENT.md 6절): ✗ 는 고친 뒤 출고, ! 는 읽고 판단
  for (const x of scanKo(textFromFile(dir))) (x.lv === 'err' ? E : W).push(`AI 문체 ${x.id} ${x.c}회 (${x.ex.join(' / ')}) → ${x.fix}`);
  // 필명·고지·출처 목록
  if (!p.blocks.some((b) => b.p === '— Editor: Luciano')) E.push('"— Editor: Luciano" 줄이 없습니다');
  const note = p.blocks.find((b) => b.note);
  if (!note || !/에디터 Luciano가 작성했습니다/.test(note.note)) E.push('고지에 작성자 문장(에디터 Luciano가 작성했습니다)이 없습니다');
  if (note && /AI ?(도구|로 (초안|작성|만))/.test(note.note)) E.push('고지에 AI 언급이 있습니다');
  if (p.blocks.some((b) => b.sources)) E.push('참고 자료 목록(sources) 블록은 넣지 않습니다');
  // 사람이 쓴 글처럼 (2026-10-25 운영자 결정): 배너·고정 인사·굵은 후킹 문단 없이, 1인칭 화자, 링크는 텍스트 1개까지
  if (p.blocks.some((b) => b.img && (b.href || b.kind === 'banner'))) E.push('끝맺음 배너는 쓰지 않습니다 — 본문 속 1인칭 언급 + {"link","text"} 텍스트 링크 1개로');
  if (p.blocks.some((b) => /^안녕하세요/.test(strip(b.p)))) W.push('인사로 시작합니다 — 가끔(세 편에 한 편 정도)만, 인사 뒤 바로 계기 문장으로');
  if (/가게|옆집|본전까지/.test(p.title)) E.push('제목에 비유(가게·옆집·본전까지)가 있습니다 — 제목만 읽어도 뜻이 통하게');
  const links = p.blocks.filter((b) => b.link);
  if (links.length > 1) E.push(`밸류노트 링크 ${links.length}개 — 1개까지`);
  { const ed = p.blocks.findIndex((b) => b.p === '— Editor: Luciano'); const after = ed >= 0 ? p.blocks.slice(ed + 1).filter((b) => b.p && /^\*\*/.test(b.p)) : []; if (after.length) E.push('Editor 줄 뒤 굵은 후킹 문단은 쓰지 않습니다'); }
  { const body = p.blocks.map((b) => strip(b.p || '')).join(' '); const fp = (body.match(/(^|[\s"'(])(저는|제가|저도|제 생각|저 역시)/g) || []).length; if (fp < 2) W.push(`1인칭(저는·제가) ${fp}번 — Luciano 한 사람이 쓴 글처럼 2번 이상`); }
  if (day) for (const o of others.filter((o) => o.id.startsWith('b' + day))) if (links.length && o.p.blocks.some((b) => b.link)) W.push(`같은 날 ${o.id}에도 링크가 있습니다 — 같은 날 두 편 가운데 링크는 한 편만`);
  // 사실 표: 제목·요약·소제목의 숫자는 모두 facts 에 있어야 한다
  const facts = p.facts || [];
  if (!facts.length) E.push('facts(확인한 사실과 출처)가 없습니다');
  const F = facts.map((f) => strip(f.t)).join(' ');
  if (facts.some((f) => !f.src)) E.push('출처(src)가 빈 facts 가 있습니다');
  const head = [p.title, ...p.blocks.flatMap((b) => [b.h, ...(b.summary || [])])].filter(Boolean).join(' ');
  const miss = [...new Set(nums(head))].filter((n) => !F.includes(n));
  if (miss.length) E.push(`facts 에 없는 제목·요약·소제목 숫자: ${miss.join(', ')}`);
  const bodyMiss = [...new Set(nums(p.blocks.map((b) => b.p || '').join(' ')))].filter((n) => n.replace(/\D/g, '').length >= 2 && !F.includes(n) && !/^(19|20)\d\d$/.test(n));
  if (bodyMiss.length) W.push(`facts 에 없는 본문 숫자 ${bodyMiss.length}개: ${bodyMiss.slice(0, 12).join(', ')}${bodyMiss.length > 12 ? ' …' : ''}`);

  // 시점 불일치 (2026-10-21): 지금 점수·적정 주가로 과거 매수·과거 주가를 평가하는 문장
  {
    const paras = (p.blocks || []).map((b) => b.p || '').filter(Boolean);
    for (const t of paras) {
      const pastBuy = /(19\d\d|20[01]\d|202[0-5])년[^.]*(샀|매수|사들|투자)/.test(t) || /년 전[^.]*(샀|매수|사들|투자)/.test(t);
      const score = /\d+점/.test(t) || /적정 주가/.test(t);
      const timed = /당시|그때 점수|그 시점|지금 계산한|지금 기준|기준일|지금 점수|지금은|지금 적정|지금 고평가|지금 저평가|지금 주가|지금 코카콜라|지금 기준으로/.test(t);
      if (pastBuy && score && !timed) W.push(`시점 확인: 과거 매수 이야기에 점수·적정 주가가 나오는데 '매수 당시/지금 계산한' 같은 시점 표시가 없습니다 → ${t.slice(0, 50)}…`);
      if (/(매수 당시|산 당시|살 때|당시)[^.]{0,20}\d+점/.test(t)) W.push(`시점 확인: '매수 당시 ○○점'이 지금 공식으로 다시 계산한 값(scripts/research/vn_then.mjs)인지 확인하세요. 버크셔 62건 VALIDATION 점수는 개편 전 값입니다 → ${t.slice(0, 50)}…`);
      if (/(월말|거래일|\d년 동안|개월)[^.]*적정 (주가|매수가)[^.]*(아래|넘|낮았|위)/.test(t) && !/지금 계산한|지금 기준|과거 그 시점|지금의 이익/.test(t))
        W.push(`시점 확인: 과거 주가를 지금 적정 주가와 비교하는 문장입니다. '지금 계산한 적정 주가'임을 밝히고 과거 저평가·고평가로 결론 내리지 마세요 → ${t.slice(0, 50)}…`);
    }
  }
  // 밸류노트 숫자 대조 (2026-10-19 적정 주가 공식 개편 뒤 도입): 글 속 회사 점수·적정 주가가 지금 계산값(c/scores.json, c/<slug>.html)과 같은지
  for (const m of checkVN(p)) (m.err ? E : W).push(m.msg);
  // 개편 전 공식으로 낸 버크셔 62건 검증 수치는 재검증 전까지 새 글에 쓰지 않는다
  if (/62\s*건/.test(T) && /(15|37)\s*%/.test(T) && !/재검증|다시 검증/.test(T)) E.push('버크셔 62건 검증 수치(실패율 15%·37%)는 10/12 공식 기준이라 재검증 전까지 쓰지 않습니다 (claude/valuation-method.md)');

  // 태그 (README 태그 규칙의 본문 일치 점검)
  const TT = T.replace(/\s/g, '');
  const tagMiss = (p.tags || []).filter((t) => !TT.includes(t) && !Array.from({ length: Math.max(0, t.length - 3) }, (_, k) => k + 2).some((i) => TT.includes(t.slice(0, i)) && TT.includes(t.slice(i))));
  if ((p.tags || []).length < 10 || (p.tags || []).length > 14) W.push(`태그 ${(p.tags || []).length}개 (10~14개)`);
  if (tagMiss.length) W.push(`본문에 없는 태그(표기 변형이면 괜찮음): ${tagMiss.join(', ')}`);

  console.log(`\n[${id}] ${p.title}`);
  console.log(`  본문 ${len}자 · 사진 ${imgs.length}장(실사 ${K('photo').length} · 원본 데이터 ${orig.length} · 카드 ${K('card').length}) · GIF ${K('gif').length} · 소제목 ${hs.length} · 뼈대 ${s}`);
  for (const l of leads) console.log('  리드  ' + l);
  for (const e of E) console.log('  ✗ ' + e);
  for (const w of W) console.log('  ! ' + w);
  if (!E.length) console.log('  ✓ 오류 없음');
  bad += E.length;
}
process.exit(bad ? 1 : 0);
