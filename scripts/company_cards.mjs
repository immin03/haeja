// 매일 저녁 '오늘의 기업' 카드뉴스 1편 자동 생성 (GitHub Actions company-cards.yml)
// 1) 스크리너 데이터(공개)를 화면과 같은 점수 코드로 계산한다
// 2) 아직 다루지 않은 회사 중 오늘 순서의 시장에서 시가총액이 가장 큰 곳을 고른다 (state.json 으로 중복 방지)
// 3) 점수 모양에 따라 각도(좋은데 비쌈 / 기준 통과 / 싼 데는 이유 / 감점 / 일반)를 정해 카드 5장을 그린다
// 4) social/company/<날짜>/NN.jpg, queue.json, state.json 을 쓴다 → Supabase 가 매시 25·28분에 게시 대기열로 가져간다
// 실행: node scripts/company_cards.mjs [YYYY-MM-DD]   (로컬: PW=<playwright 모듈 경로>)
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { scoreRow, grpOf, WARN_FLAGS, setSettings } from '../supabase/functions/watch-select/scoring.js';
import { makeVN } from './vnscore.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW || 'playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const OUT = path.join(ROOT, 'social', 'company');
const SUIT = path.join(ROOT, 'fonts', 'SUIT-Variable.woff2');
const HANDLE = '@value.note.korea';
// 하루 3편: a = 21:00 오늘의 기업(유명 회사), b = 11:00 저평가 기업 분석, rank = 15:30 저평가·고평가 TOP 10
const MODE = process.argv[3] || 'a';
// reel1 = 12:30 기업 릴스 대본, reel2 = 18:00 순위 릴스 대본 (이미 그 시간에 잡힌 릴스가 없을 때만), am = 08:30 기능 카드가 끝난 뒤 채우는 '좋은 회사, 비싼 가격' 분석
const SLOT = { a: ['C', '', '21:00'], b: ['C', 'b', '11:00'], rank: ['K', '', '15:30'], am: ['C', 'm', '08:30'], reel1: ['A', '1', '12:30'], reel2: ['A', '2', '18:00'], ra: ['A', 'a', '21:00'], rb: ['A', 'b', '11:00'], rr: ['A', 'r', '15:30'], rm: ['A', 'm', '08:30'] }[MODE];
const POST_TIME = SLOT[2];
const REEL = ['reel1', 'reel2', 'ra', 'rb', 'rr', 'rm'].includes(MODE);
const DISC = '*본 콘텐츠는 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아닙니다.';
const cfgSrc = fs.readFileSync(path.join(ROOT, 'config.js'), 'utf8');
const URL0 = cfgSrc.match(/SUPABASE_URL:\s*'([^']+)'/)[1];
const KEY = cfgSrc.match(/SUPABASE_ANON_KEY:\s*'([^']+)'/)[1];
const MKT = { KR: '한국', US: '미국', JP: '일본', HK: '홍콩', CN: '중국' };
// 국내 독자 기준: 한국·미국 위주, 닷새에 한 번 일본·홍콩·중국
const ROTA = ['KR', 'US', 'KR', 'US', 'JP', 'KR', 'US', 'KR', 'US', 'HK', 'KR', 'US', 'KR', 'US', 'CN'];

const ymd = process.argv[2] || new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
const tag = ymd.replace(/-/g, '');
const isNum = (v) => typeof v === 'number' && isFinite(v);
const n0 = (v, d = 0) => (isNum(v) ? v.toLocaleString('ko-KR', { maximumFractionDigits: d, minimumFractionDigits: d }) : '–');
const slug = (r) => String(r.t || r.code).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
function money(v, cur) {
  if (!isNum(v)) return '–';
  if (cur === 'KRW') return n0(v) + '원';
  if (cur === 'JPY') return n0(v) + '엔';
  if (cur === 'CNY') return n0(v, 2) + '위안';
  if (cur === 'HKD') return 'HK$' + n0(v, 2);
  return '$' + n0(v, 2);
}
const josa = (w, a, b) => { const c = String(w).trim().slice(-1).charCodeAt(0); if (c < 0xac00 || c > 0xd7a3) return w + b; return w + ((c - 0xac00) % 28 ? a : b); };

async function load() {
  const r = await fetch(`${URL0}/rest/v1/docs?collection=eq.screen&select=id,data`, { headers: { apikey: KEY, Authorization: 'Bearer ' + KEY } });
  if (!r.ok) throw new Error('screen ' + r.status);
  const docs = await r.json();
  await loadVN();
  return docs.filter((d) => d.id.startsWith('chunk-')).sort((a, b) => a.id.localeCompare(b.id)).flatMap((d) => d.data?.rows || []);
}
// 밸류노트 점수(앱과 같은 값): 숫자 65% + 밸류노트 공용 정성 평가 20% + 트렌드 15%
let VN = null;
async function loadVN() {
  const h = { headers: { apikey: KEY, Authorization: 'Bearer ' + KEY } };
  const tr = (await (await fetch(`${URL0}/rest/v1/docs?collection=eq.trends&id=eq.current&select=data`, h)).json())[0]?.data;
  const pf = Object.fromEntries((await (await fetch(`${URL0}/rest/v1/docs?collection=eq.profiles&select=id,data`, h)).json()).map((d) => [d.id, d.data]));
  VN = makeVN(tr, pf);
}
function score(r) { const sc = scoreRow(r, null, 30); const v = VN ? VN(r, sc) : { total: sc.b, qual: null, qualDone: false }; return { ...sc, bNum: sc.b, b: v.total, qualScore: v.qual, qualDone: v.qualDone }; }

// 점수 모양으로 이야기 각도를 정한다
function angle(r, sc) {
  const pens = (sc.flags || []).filter((f) => !WARN_FLAGS.has(f));
  const { q, v, b } = sc;
  if (b >= 70 && !pens.length) return { k: 'pass', t: `${r.n},\n버핏 기준 **${b}점**`, s: '품질과 가격이 함께\n기준(70점)을 넘은 드문 경우입니다.' };
  if (q >= 80 && v < 35) return { k: 'pricey', t: `${r.n},\n품질 **${q}점**인데\n종합은 ${b}점`, s: '좋은 회사와 좋은 가격은\n다른 이야기입니다.' };
  const ratio = isNum(sc.iv) && sc.iv > 0 && isNum(r.px) ? r.px / sc.iv : null;
  if (ratio && ratio >= 1.5) return { k: 'over', t: `${r.n},\n지금 가격은\n적정 주가의 **${n0(ratio, 1)}배**`, s: `재무 점수은 ${q}점.\n그런데 왜 종합은 ${b}점일까요?` };
  if (v >= 60 && q < 50) return { k: 'trap', t: `${r.n},\n싸 보이는데\n왜 **${b}점**일까`, s: '가격 점수는 높지만\n이익의 질이 따라오지 못합니다.' };
  if (pens.length) return { k: 'flag', t: `${r.n},\n감점 신호 **${pens.length}개**`, s: `${pens.join(', ')}.\n신호 하나에 8점씩 깎입니다.` };
  return { k: 'plain', t: `${r.n}의\n버핏 점수는 **${b}점**`, s: `재무 점수 ${q}점, 저평가 ${v}점.\n어디서 점수가 갈렸는지 보겠습니다.` };
}

// 먼저 많이 아는 회사부터 (시장별 순서). 다 쓰면 점수가 극단적인 회사로 넘어간다.
const FAMOUS = {
  KR: ['삼성전자', 'SK하이닉스', '현대차', '카카오', 'NAVER', 'LG에너지솔루션', '셀트리온', 'KB금융', '삼성바이오로직스', 'POSCO홀딩스', '한화에어로스페이스', '신한지주', 'LG화학', '삼성SDI', 'HD현대중공업', '크래프톤', '하이브', '아모레퍼시픽', 'KT&G', '삼성물산', '현대모비스', 'LG전자', '대한항공', '한국전력', '카카오뱅크', '두산에너빌리티', '에코프로비엠', '알테오젠', '기아'],
  US: ['애플', '엔비디아', '테슬라', '마이크로소프트', '알파벳', '아마존', '메타 플랫폼스', '코카콜라', '넷플릭스', '팔란티어', '브로드컴', '일라이 릴리', '비자', '맥도날드', '스타벅스', '월트 디즈니', '코스트코', 'AMD', '인텔', '아메리칸 익스프레스', '뱅크오브아메리카', '존슨앤드존슨', '월마트', '오라클', '처브', '엑슨모빌'],
  JP: ['토요타자동차', '소니', '닌텐도', '미쓰비시상사', '이토추상사', '패스트리테일링', '키엔스'],
  HK: ['텐센트', '알리바바', '샤오미', '비야디'],
  CN: ['CATL(닝더스다이)'],
};
function pick(rows, state) {
  const used = new Set(state.used || []);
  if (MODE === 'b' || MODE === 'rb') return pickUnder(rows, used);
  if (MODE === 'am' || MODE === 'rm') { const L = overList(rows, 'ALL').filter((x) => !used.has(x.r.t) && (!REEL || (expect(x.r, x.sc)?.d > 3))).sort((p, q) => q.sc.q - p.sc.q); return L[0] || null; }
  const all = rows.map((r) => ({ r, sc: score(r) }))
    .filter((x) => isNum(x.sc.b) && isNum(x.sc.q) && isNum(x.sc.v) && x.r.dataConf !== 'low' && !used.has(x.r.t))
    // 적정 주가와 비슷하거나 조금 다른 회사는 이야기가 약하다: 1.5배 이상 비싸거나 25% 이상 싼 회사만
    .filter((x) => { const R = isNum(x.sc.iv) && x.sc.iv > 0 && isNum(x.r.px) ? x.r.px / x.sc.iv : null; return R !== null && ((R >= 1.5 && R <= 5) || (R <= 0.75 && R >= 0.25)); })
    .filter((x) => !REEL || (expect(x.r, x.sc) && Math.abs(expect(x.r, x.sc).d) > 3)); // 너무 극단적인 값(+400% 초과, 상승 여력 300% 초과)은 믿기 어려워 보여 제외
  const day = Math.round((Date.parse(ymd) - Date.parse('2026-10-17')) / 864e5);
  for (let i = 0; i < ROTA.length; i++) {
    const m = ROTA[(day + i) % ROTA.length];
    const inM = all.filter((x) => grpOf(x.r.m) === m);
    for (const n of FAMOUS[m] || []) { const c = inM.find((x) => x.r.n === n); if (c) return c; }
    // 유명 회사를 다 썼으면: 짝수 날은 점수 최상위, 홀수 날은 '품질은 높은데 비싼' 회사
    const c = day % 2 === 0 ? inM.sort((a, b) => b.sc.b - a.sc.b)[0] : inM.filter((x) => x.sc.v < 35).sort((a, b) => b.sc.q - a.sc.q)[0] || inM[0];
    if (c) return c;
  }
  return null;
}

// 저평가 슬롯: 앱의 '저평가' 목록과 같은 기준(25% 이상 싸고, 품질 50점 이상, 감점 없음) 중 품질 높은 순
function underList(rows, mkt) {
  return rows.map((r) => ({ r, sc: score(r) })).filter((x) => {
    const { r, sc } = x; if (!isNum(sc.iv) || sc.iv <= 0 || !isNum(r.px) || r.dataConf === 'low' || !isNum(sc.q)) return false;
    if (mkt && mkt !== 'ALL' && !mkt.split(',').includes(grpOf(r.m))) return false;
    const R = r.px / sc.iv, pen = (sc.flags || []).filter((f) => !WARN_FLAGS.has(f)).length; x.R = R;
    return R <= 0.75 && R >= 0.25 && sc.q >= 50 && !pen;
  });
}
function overList(rows, mkt) {
  return rows.map((r) => ({ r, sc: score(r) })).filter((x) => {
    const { r, sc } = x; if (!isNum(sc.iv) || sc.iv <= 0 || !isNum(r.px) || r.dataConf === 'low' || !isNum(sc.q)) return false;
    if (mkt && mkt !== 'ALL' && !mkt.split(',').includes(grpOf(r.m))) return false;
    const R = r.px / sc.iv; x.R = R; return R >= 1.5 && R <= 5 && sc.q >= 60;
  });
}
function pickUnder(rows, used) {
  const L = underList(rows, 'ALL').filter((x) => !used.has(x.r.t) && (!REEL || (expect(x.r, x.sc)?.d < -3))).sort((a, b) => b.sc.q - a.sc.q);
  if (L.length) return L[0];
  // 다 쓰면 기준을 조금 넓힌다 (감점 신호가 있어도 25% 이상 싼 회사)
  return rows.map((r) => ({ r, sc: score(r) })).filter((x) => !used.has(x.r.t) && isNum(x.sc.iv) && x.sc.iv > 0 && isNum(x.r.px) && x.r.px / x.sc.iv <= 0.75 && x.r.dataConf !== 'low').sort((a, b) => b.sc.q - a.sc.q)[0] || null;
}

const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const br = (s) => esc(s).replace(/\n/g, '<br>').replace(/\*\*(.+?)\*\*/g, '<em>$1</em>');
const CSS = `@font-face{font-family:SUIT;src:url(data:font/woff2;base64,${fs.readFileSync(SUIT).toString('base64')}) format('woff2');font-weight:100 900}
*{box-sizing:border-box;margin:0;padding:0}html,body{width:1080px;height:1350px}
body{font-family:SUIT,sans-serif;word-break:keep-all;overflow-wrap:break-word;-webkit-font-smoothing:antialiased}
.s{position:relative;width:1080px;height:1350px;overflow:hidden;background:radial-gradient(120% 80% at 50% 0%,#17283F 0%,#0E1B2E 55%,#0A1322 100%);color:#F3EEE3}
.top{position:absolute;left:84px;right:84px;top:64px;display:flex;justify-content:space-between;align-items:center;z-index:5}
.wm{font-weight:700;font-size:30px;letter-spacing:-.02em}.wm .ko{font-weight:600;font-size:24px;color:#8F9AAB;margin-left:14px;letter-spacing:.04em}.wm i{font-style:normal;color:#E2C489}.pg{color:#8F9AAB;font-size:26px}
em{font-style:normal;color:#E2C489}
.body{position:absolute;left:84px;right:84px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center}
.k{color:#E2C489;font-size:34px;font-weight:700;margin-bottom:30px}
h1{font-size:92px;line-height:1.2;font-weight:800;letter-spacing:-.045em}
h2{font-size:60px;line-height:1.25;font-weight:800;letter-spacing:-.04em;margin-bottom:56px}
.sub{margin-top:44px;font-size:40px;line-height:1.55;color:#C7CEDA;font-weight:500}
.meta{margin-top:34px;font-size:30px;color:#8F9AAB;font-weight:600}
.swipe{position:absolute;left:84px;bottom:64px;font-size:28px;color:#E2C489;font-weight:700}
.big{display:flex;align-items:flex-end;gap:26px;margin-bottom:60px}.big b{font-size:220px;line-height:.85;font-weight:900;color:#E2C489;letter-spacing:-.05em}.big span{font-size:34px;color:#8F9AAB;padding-bottom:14px;line-height:1.4}
.bar{margin-bottom:44px}.bar .l{display:flex;justify-content:space-between;font-size:38px;font-weight:700;margin-bottom:16px}.bar .l span{color:#8F9AAB;font-weight:600;font-size:30px}
.track{position:relative;height:26px;border-radius:20px;background:rgba(255,255,255,.12)}.track i{position:absolute;left:0;top:0;bottom:0;border-radius:20px;background:#E2C489}
.track .th{position:absolute;top:-14px;bottom:-14px;width:4px;background:#F3EEE3;opacity:.7}
.note{font-size:30px;line-height:1.55;color:#C7CEDA;margin-top:20px}
.px{display:grid;grid-template-columns:1fr 1fr;gap:26px;margin-bottom:46px}.px>div{background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.1);border-radius:28px;padding:34px 30px}
.px .t{font-size:30px;color:#8F9AAB;font-weight:600}.px .v{font-size:58px;font-weight:800;margin-top:10px;letter-spacing:-.03em}
.mos{font-size:64px;font-weight:900;letter-spacing:-.03em}.pos{color:#7FD1A8}.neg{color:#F08C78}
.rows div{display:flex;justify-content:space-between;align-items:baseline;border-top:2px solid rgba(255,255,255,.1);padding:26px 0;font-size:38px;font-weight:600}.rows div:first-child{border-top:0}.rows b{font-size:44px;font-weight:800}
.rows small{display:block;font-size:26px;color:#8F9AAB;font-weight:500;margin-top:4px}
.lead{font-size:44px;line-height:1.5;font-weight:700;color:#F3EEE3}
.steps>div{display:flex;align-items:center;gap:26px;border-top:2px solid rgba(255,255,255,.1);padding:30px 0}.steps>div:first-child{border-top:0}
.steps .n{flex:0 0 64px;height:64px;border-radius:50%;background:#E2C489;color:#0A1322;font-weight:900;font-size:32px;display:flex;align-items:center;justify-content:center}
.steps .tx{flex:1;font-size:38px;font-weight:700}.steps small{display:block;font-size:27px;color:#8F9AAB;font-weight:500;margin-top:6px;line-height:1.4}.steps b{font-size:42px;font-weight:800;color:#E2C489;text-align:right}
.alt{margin-top:26px;border-left:6px solid #E2C489;padding:10px 0 10px 34px}
.flags{margin-top:30px;display:flex;flex-wrap:wrap;gap:14px}.flag{border-radius:999px;padding:12px 24px;font-size:30px;font-weight:700;background:rgba(240,140,120,.16);color:#F5B3A5}.flag.w{background:rgba(255,255,255,.1);color:#C7CEDA}
.cta{background:#F3EEE3;color:#0A1322}.cta .wm{color:#0A1322}.cta .wm i{color:#A8823F}.cta .wm .ko,.cta .pg{color:#7A8394}
.cta h2{font-size:76px;margin-bottom:0}.cta em{color:#A8823F}.cta .sub{color:#3A4558}
.btn{margin-top:56px;display:inline-flex;align-self:flex-start;background:#0A1322;color:#F3EEE3;border-radius:999px;padding:26px 40px;font-size:34px;font-weight:700}
.handle{margin-top:28px;font-size:30px;color:#7A8394;font-weight:600}
.disc{position:absolute;left:84px;right:84px;bottom:60px;font-size:22px;color:#7A8394;line-height:1.5}
.top .pgs{display:flex;gap:4px;font-size:22px;color:#5E6B80;font-weight:700;letter-spacing:.02em}.top .pgs>*{padding:4px 8px;border:2px solid transparent;border-radius:999px}.top .pgs b{color:#F3EEE3;border-color:#F3EEE3}
.cover{position:absolute;left:84px;right:84px;top:190px}.cover h1{font-size:88px;line-height:1.18}
.vis{position:absolute;left:84px;right:84px;top:170px;height:560px;display:flex;flex-direction:column;justify-content:center}
.vis-low{top:650px;height:420px}
.txt{position:absolute;left:84px;right:84px;top:760px}
.txt .no{color:#E8A07E;font-size:32px;font-weight:800;letter-spacing:.06em;margin-bottom:18px}
.txt h3{font-size:64px;line-height:1.22;font-weight:800;letter-spacing:-.04em}
.txt .acc{margin-top:22px;font-size:38px;font-weight:700;color:#E8A07E;line-height:1.4}
.txt .bd{margin-top:18px;font-size:32px;line-height:1.55;color:#AEB8C8}
.bars2{display:flex;flex-direction:column;gap:40px}
.b2l{font-size:32px;color:#C7CEDA;font-weight:600;margin-bottom:14px}.b2t{height:56px;border-radius:16px;background:rgba(255,255,255,.07);overflow:hidden}.b2t i{display:block;height:100%;border-radius:16px}
.b2v{font-size:46px;font-weight:900;margin-top:12px;letter-spacing:-.02em}
.bars2.b3{gap:22px}.b3 .b2l{font-size:28px;margin-bottom:10px}.b3 .b2t{height:44px}.b3 .b2v{font-size:38px;margin-top:8px}
.gap{margin-top:30px;font-size:48px;font-weight:900}.gap.neg{color:#F08C78}.gap.pos{color:#7FD1A8}
.vis .steps>div{padding:26px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.grid div{background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.1);border-radius:26px;padding:32px 30px}
.grid span{display:block;font-size:28px;color:#8F9AAB;font-weight:600}.grid b{display:block;font-size:60px;font-weight:900;margin-top:8px;letter-spacing:-.03em}
.quote{position:absolute;left:84px;right:84px;top:0;bottom:250px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}
.ql span{display:inline-block;font-size:70px;line-height:1.5;font-weight:800;letter-spacing:-.04em;border-bottom:5px solid #E8A07E;margin:6px 0}.ql{display:flex;flex-direction:column;align-items:center}
.qs{margin-top:40px;font-size:28px;color:#8F9AAB}
.chk{display:flex;flex-direction:column;gap:26px}.chk div{display:flex;align-items:center;gap:28px;font-size:44px;font-weight:700;background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.1);border-radius:26px;padding:34px 32px}
.cb{flex:0 0 64px;height:64px;border-radius:16px;border:4px solid #E2C489;color:#E2C489;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:900}
.outro{position:absolute;left:84px;right:84px;top:0;bottom:200px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}
.outro .be{font-size:26px;letter-spacing:.4em;color:#8F9AAB;font-weight:600}.outro .logo{font-size:120px;font-weight:800;letter-spacing:-.03em;margin:18px 0 26px}.outro .logo i{font-style:italic;color:#E2C489}
.outro h2{font-size:64px;line-height:1.3;margin-bottom:24px}.outro p{font-size:34px;line-height:1.6;color:#AEB8C8}
.fbtn{margin-top:50px;width:720px;display:flex;justify-content:space-between;align-items:center;border:3px solid #F3EEE3;border-radius:999px;padding:30px 30px 30px 50px;font-size:36px;font-weight:800}
.fbtn b{width:72px;height:72px;border-radius:50%;background:#F3EEE3;color:#0A1322;display:flex;align-items:center;justify-content:center;font-size:40px}
.lk{margin-top:28px;font-size:28px;color:#8F9AAB}
.wmk{position:absolute;left:0;right:0;bottom:120px;text-align:center;font-size:26px;letter-spacing:.5em;color:#5E6B80;font-weight:700}
.disc{bottom:60px}
.rlist{position:absolute;left:84px;right:84px;top:170px;height:560px;display:flex;flex-direction:column;justify-content:center;gap:18px}
.rlist-full{height:auto;bottom:220px;justify-content:center}
.rk{display:flex;align-items:center;gap:24px;background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.1);border-radius:26px;padding:28px 30px}
.rn{flex:0 0 56px;font-size:44px;font-weight:900;color:#E2C489;text-align:center}
.rnm{flex:1;min-width:0;display:flex;flex-direction:column;gap:6px}.rnm b{font-size:42px;font-weight:800;letter-spacing:-.03em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rnm small,.rv small{font-size:24px;color:#8F9AAB;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rv{flex:0 0 auto;display:flex;flex-direction:column;align-items:flex-end;gap:6px;text-align:right;max-width:52%}.rv b{font-size:34px;font-weight:900}
.rv b.pos{color:#7FD1A8}.rv b.neg{color:#F08C78}
.rk.hide .rnm b{filter:blur(9px)}
`;

// ---------- 분석: 적정 주가 → 계산 방법 → 차이가 나는 이유 ----------
const DISC_R = { KR: 10, US: 10, CN: 11, HK: 11, JP: 9 };
function analyze(x) {
  const { r, sc } = x, cur = r.cur || 'KRW', f = r.fin || {}, val = r.val || {}, g = grpOf(r.m);
  const M = (v) => money(v, cur);
  const pens = (sc.flags || []).filter((fl) => !WARN_FLAGS.has(fl)), warns = (sc.flags || []).filter((fl) => WARN_FLAGS.has(fl));
  const ratio = isNum(sc.iv) && sc.iv > 0 && isNum(r.px) ? r.px / sc.iv : null;
  const o = { pens, warns, ratio, method: [], why: [], alt: null, verdict: '', cap: [] };
  // 1) 결론
  if (ratio === null) o.verdict = '적정 주가을 계산할 이익 자료가 부족합니다.';
  else if (ratio >= 2) o.verdict = `현재가는 계산한 적정 주가의 **${n0(ratio, 1)}배**입니다.`;
  else if (ratio > 1.05) o.verdict = `현재가가 적정 주가보다 **${n0((ratio - 1) * 100)}%** 높습니다.`;
  else if (ratio >= 0.95) o.verdict = '현재가가 적정 주가과 **거의 같습니다**.';
  else o.verdict = `현재가가 적정 주가보다 **${n0((1 - ratio) * 100)}%** 낮습니다.`;
  // 2) 계산 방법
  const disc = DISC_R[g] ?? 10;
  if (isNum(sc.dcf)) {
    const oe = isNum(val.oeps) ? (isNum(val.sbcps) ? val.oeps - val.sbcps : val.oeps) : null;
    const base = sc.ivBasis === 'norm' ? Math.min(val.epsAvg, isNum(val.eps) && val.eps > 0 ? val.eps : Infinity) : oe;
    o.method.push(sc.ivBasis === 'norm'
      ? ['기준 이익', `주당 ${M(base)}`, `최근 ${r.yrs || 5}년 평균 주당순이익. 호황·불황을 고르게 반영`]
      : ['기준 이익', `주당 ${M(base)}`, '실제로 남은 현금(주주 이익). 주식 보상 비용은 뺌']);
    o.method.push(['성장 가정', `연 ${n0(val.growth, 1)}%`, '앞으로 10년, 과거 성장률을 보수적으로 반영']);
    o.method.push(['할인율', `연 ${disc}%`, '이 정도는 벌어야 한다는 기대 수익률']);
    o.methodNote = '10년 동안 벌 이익과 그 이후 가치를 오늘 돈으로 바꿔 더했습니다 (현금흐름 할인).';
    o.cap.push(`계산은 이렇게 했습니다. ${sc.ivBasis === 'norm' ? `최근 ${r.yrs || 5}년 평균 주당순이익 ${M(base)}` : `주당 주주 이익(현금 기준) ${M(base)}`}을 기준으로, 앞으로 10년간 연 ${n0(val.growth, 1)}% 성장한다고 보고 연 ${disc}%의 기대 수익률로 할인했습니다.`);
  } else if (isNum(sc.graham)) {
    o.method.push(['주당순이익', M(val.eps), '최근 1년']);
    o.method.push(['주당순자산', M(val.bps), '회사가 가진 순자산을 주식 수로 나눈 값']);
    o.method.push(['공식', '√(22.5 × 이익 × 자산)', '그레이엄이 쓴 적정 주가 공식']);
    o.methodNote = r.fin_sector ? '은행·보험은 현금흐름 계산이 맞지 않아 이익과 자산으로 봅니다.' : '현금 기준 이익이 마이너스라 이익과 자산으로 계산했습니다.';
    o.cap.push(`계산은 그레이엄 공식으로 했습니다. 주당순이익 ${M(val.eps)}과 주당순자산 ${M(val.bps)}을 곱해 22.5배 한 값의 제곱근입니다. ${o.methodNote}`);
  }
  // 3) 차이가 나는 이유
  if (false && isNum(sc.ig) && isNum(sc.hist)) { // 30초 상한 때문에 뺌(목표 20초)
    const need = sc.ig >= 80 ? '80% 이상' : sc.ig <= -30 ? '-30% 이하' : `${n0(sc.ig, 1)}%`;
    if (sc.ig > sc.hist + 2) {
      o.why.push(`지금 주가가 맞으려면 앞으로 10년간 이익이 **매년 ${need}** 늘어야 합니다.`);
      o.why.push(`지난 몇 년 실제 성장은 연 ${n0(sc.hist, 1)}%였습니다.`);
      o.cap.push(`지금 주가가 맞으려면 앞으로 10년간 이익이 매년 ${need}씩 늘어야 합니다. 지난 몇 년 실제 성장은 연 ${n0(sc.hist, 1)}%였습니다.`);
    } else {
      o.why.push(sc.ig < 0 ? `지금 주가는 앞으로 이익이 **매년 ${n0(-sc.ig, 1)}%씩 줄어든다**고 가정한 수준입니다.` : `지금 주가는 앞으로 이익이 **매년 ${need}** 늘어난다는 정도만 가정합니다.`);
      o.why.push(`지난 몇 년 실제 성장(연 ${n0(sc.hist, 1)}%)보다 ${sc.ig < sc.hist - 2 ? '낮은 기대입니다' : '크게 높지 않습니다'}.`);
      o.cap.push(`지금 주가는 ${sc.ig < 0 ? `이익이 매년 ${n0(-sc.ig, 1)}%씩 줄어든다고` : `이익이 매년 ${need} 늘어나는 정도만`} 가정합니다. 지난 몇 년 실제 성장은 연 ${n0(sc.hist, 1)}%였습니다.`);
    }
  }
  if (ratio !== null && ratio < 1 && pens.length) {
    o.why.push(`다만 싼 데는 이유가 있을 수 있습니다. 감점 신호: **${pens.join(', ')}**.`);
    o.cap.push(`다만 싼 데는 이유가 있을 수 있습니다. ${pens.join(', ')} 신호가 있어 이 부분을 먼저 확인해야 합니다.`);
  }
  // 최근 이익이 평균과 크게 다를 때: 반대 시나리오
  if (sc.ivBasis === 'norm' && isNum(sc.ivNow) && isNum(val.eps) && isNum(val.epsAvg) && val.eps > val.epsAvg * 1.5) {
    o.alt = { t: `다만 최근 1년 이익(주당 ${M(val.eps)})은 평균의 ${n0(val.eps / val.epsAvg, 1)}배입니다.`,
      s: `이 이익이 계속된다면 적정 주가은 **${M(sc.ivNow)}**입니다. 결국 질문은 하나입니다. 지금 이익이 한때의 호황인가, 새로운 수준인가.` };
    o.cap.push(`다만 최근 1년 주당순이익 ${M(val.eps)}은 평균의 ${n0(val.eps / val.epsAvg, 1)}배입니다. 이 이익이 계속된다면 적정 주가은 ${M(sc.ivNow)}입니다. 결국 핵심은 지금 이익이 한때의 호황인지, 새로운 수준인지입니다.`);
  }
  return o;
}

// 첫 장 문구: "○○의 적정 주가는 68,685원?" + 아래 줄에 지금 주가와 차이
function hook(r, sc, a) {
  if (a.ratio === null) return `${r.n}의\n적정 주가는\n얼마일까?`;
  return `${r.n}의\n적정 주가는\n**${money(sc.iv, r.cur || 'KRW')}**?`;
}
// 저평가·고평가 표준 문구 (앱 gapLong과 같다). R = 현재가 ÷ 적정 주가
function gapText(R) {
  if (R < 0.95) return `적정 주가보다 ${n0((1 - R) * 100)}% 저평가`;
  if (R <= 1.05) return '적정 주가 수준';
  return `적정 주가보다 +${n0((R - 1) * 100)}% 고평가`;
}
const upside = (R) => n0((1 / R - 1) * 100);
// 3분의 1·절반처럼 딱 떨어지면 말로 (예: 적정 주가의 3분의 1 가격)
const fracText = (R) => { const f = [[2, '절반'], [3, '3분의 1'], [4, '4분의 1']].find(([k]) => Math.abs(R - 1 / k) <= 0.03); return f ? `적정 주가의 ${f[1]} 가격` : null; };
const gapSentence = (R) => R < 0.95 ? `${fracText(R) || gapText(R)}로, 적정 주가까지 상승 여력이 +${upside(R)}%입니다` : gapText(R) + (R <= 1.05 ? '입니다' : ' 상태입니다');

// ---------- 8장 구성: 장마다 위쪽은 큰 그래픽, 아래쪽은 번호 · 결론 제목 · 강조 한 줄 · 설명 2줄 ----------
function frame(no, title, accent, body) {
  return `<div class="txt">${no ? `<div class="no">${no}</div>` : ''}<h3>${br(title)}</h3>${accent ? `<div class="acc">${br(accent)}</div>` : ''}${body ? `<p class="bd">${br(body)}</p>` : ''}</div>`;
}
function bars(items, unit) {
  const mx = Math.max(...items.map((x) => x.v)) || 1;
  return `<div class="bars2${items.length > 2 ? ' b3' : ''}">${items.map((x) => `<div class="b2"><div class="b2l">${esc(x.l)}</div><div class="b2t"><i style="width:${Math.max(3, x.v / mx * 100)}%;background:${x.c}"></i></div><div class="b2v" style="color:${x.c}">${esc(x.t)}</div></div>`).join('')}</div>`;
}
function cards(x, a) {
  const { r, sc } = x, cur = r.cur || 'KRW', f = r.fin || {}, val = r.val || {}, g = grpOf(r.m);
  const M = (v) => money(v, cur), code = r.code || r.t, R = a.ratio, over = R !== null && R > 1;
  const GOLD = '#E2C489', RED = '#F08C78', GREEN = '#7FD1A8', GRAY = '#8F9AAB';
  const out = [];
  // 1. 표지: 질문형 제목 + 지금 주가 vs 적정 주가 막대
  out.push(`<div class="cover"><div class="k">${MODE === 'b' ? '저평가 기업 분석' : MODE === 'am' ? '좋은 회사, 비싼 가격' : '오늘의 기업 분석'} · ${MKT[g]}</div><h1>${br(hook(r, sc, a))}</h1></div>
    <div class="vis vis-low">${bars([{ l: '지금 주가', v: r.px, t: M(r.px), c: over ? RED : '#F3EEE3' }, { l: '적정 주가', v: sc.iv, t: M(sc.iv), c: GOLD }])}
    <div class="gap ${over ? 'neg' : 'pos'}">${esc(gapText(R))}</div></div>`);
  // 2. 시장의 기대 vs 실제 성장 (두 번째 장도 표지만큼 강하게)
  if (false && isNum(sc.ig) && isNum(sc.hist)) { // 30초 상한 때문에 뺌(목표 20초)
    const need = Math.max(Math.min(sc.ig, 80), -30);
    const hi = need > sc.hist + 2;
    out.push(`<div class="vis">${bars([{ l: '지금 주가가 가정한 성장', v: Math.max(Math.abs(need), 0.5), t: `연 ${n0(need, 1)}%`, c: hi ? RED : GREEN }, { l: '지난 몇 년 실제 성장', v: Math.max(Math.abs(sc.hist), 0.5), t: `연 ${n0(sc.hist, 1)}%`, c: GOLD }])}</div>`
      + frame('01', hi ? `지금 주가에는\n연 ${n0(need, 1)}% 성장이 들어 있다` : need < 0 ? `지금 주가는\n이익 감소를 가정한다` : `지금 주가는\n낮은 성장만 가정한다`,
        hi ? `실제 성장은 연 ${n0(sc.hist, 1)}%였습니다.` : `실제 성장은 연 ${n0(sc.hist, 1)}%였습니다.`,
        '앞으로 10년 이익이 얼마나 늘어야 지금 주가가 맞는지 거꾸로 계산했습니다.'));
  }
  // 3. 계산 방법
  if (a.method.length) {
    out.push(`<div class="vis"><div class="steps">${a.method.map((m, i) => `<div><span class="n">${i + 1}</span><span class="tx">${esc(m[0])}<small>${esc(m[2])}</small></span><b>${esc(m[1])}</b></div>`).join('')}</div></div>`
      + frame('02', `적정 주가 ${M(sc.iv)},\n이렇게 계산했다`, a.methodNote.replace(/\.$/, '') + '.', ''));
  }
  // 4. 반대 시나리오 (최근 이익이 평균과 크게 다를 때)
  if (a.alt) {
    out.push(`<div class="vis">${bars([{ l: '평균 이익 기준 적정 주가', v: sc.iv, t: M(sc.iv), c: GOLD }, { l: '최근 이익 기준 적정 주가', v: sc.ivNow, t: M(sc.ivNow), c: GREEN }, { l: '지금 주가', v: r.px, t: M(r.px), c: '#F3EEE3' }])}</div>`
      + frame('03', `하지만, 최근 이익은\n평균의 ${n0(val.eps / val.epsAvg, 1)}배`, `이 이익이 계속되면 적정 주가는 ${M(sc.ivNow)}.`, '어느 이익을 기준으로 보느냐에 따라 답이 달라집니다.'));
  }
  // 5. 회사 체력
  const mets = [
    ['5년 평균 ROE', isNum(f.roeAvg) ? n0(f.roeAvg, 1) + '%' : null],
    ['현금 전환율', !r.fin_sector && isNum(f.fcfConv) ? n0(f.fcfConv) + '%' : null],
    ['장기부채 ÷ 순이익', !r.fin_sector && isNum(f.ltdNi) ? (f.ltdNi < 0.05 ? '거의 없음' : n0(f.ltdNi, 1) + '배') : null],
    ['PER', isNum(sc.per) ? n0(sc.per, 1) + '배' : null],
    ['PBR', isNum(sc.pbr) ? n0(sc.pbr, 2) + '배' : null],
  ].filter((m) => m[1]).slice(0, 4);
  const qT = sc.q >= 80 ? '회사 체력은 상위권' : sc.q >= 60 ? '회사 체력은 중간 이상' : '회사 체력은 약한 편';
  out.push(`<div class="vis"><div class="grid">${mets.map((m) => `<div><span>${m[0]}</span><b>${m[1]}</b></div>`).join('')}</div>
    ${a.pens.length || a.warns.length ? `<div class="flags">${a.pens.map((fl) => `<span class="flag">감점 · ${esc(fl)}</span>`).join('')}${a.warns.map((fl) => `<span class="flag w">경고 · ${esc(fl)}</span>`).join('')}</div>` : ''}</div>`
    + frame(a.alt ? '04' : '03', `${qT}\n(품질 ${sc.q}점)`, `밸류노트 종합 ${sc.b}점 · 저평가 ${sc.v}점`, '돈을 잘 버는지, 빚이 적은지, 이익이 현금으로 들어오는지 봅니다.'));
  // 6. 핵심 한 문장 (밑줄 강조)
  const quote = a.alt ? '핵심은 하나.\n지금 이익이 한때의 호황인가,\n새로운 수준인가.'
    : over ? '좋은 회사와\n좋은 가격은\n다른 이야기입니다.'
    : a.pens.length ? '싼 가격에는\n이유가 있는지부터\n확인해야 합니다.' : '시장이 놓친 기회인지,\n싼 이유가 있는지\n숫자로 확인할 차례입니다.';
  out.push(`<div class="quote"><div class="ql">${quote.split('\n').map((l) => `<span>${esc(l)}</span>`).join('')}</div><div class="qs">— 밸류노트의 해석 · 투자 판단은 본인의 몫입니다</div></div>`);
  // 7. 체크리스트 (저장 유도)
  const chk = over ? ['이익이 평균 이상으로 유지되는가', '그 이익이 현금으로 들어오는가', '주가가 적정 주가에 다가오는가']
    : ['이익이 꾸준히 유지되는가', '새로운 감점 신호가 생기지 않는가', '주가가 적정 주가로 돌아오는가'];
  out.push(`<div class="vis"><div class="chk">${chk.map((c, i) => `<div><span class="cb">${i + 1}</span>${esc(c)}</div>`).join('')}</div></div>`
    + frame(a.alt ? '05' : '04', '다음 실적에서\n이 세 가지를 보세요', '저장해 두고 다음 실적 때 꺼내 보세요.', ''));
  // 8. 마무리: 팔로우 + 프로필 링크, 첫 장으로 돌아가는 질문
  out.push(`<div class="outro"><div class="be">VALUE INVESTING GUIDE</div><div class="logo">Value<i>Note</i></div><h2>현명한 투자를 위한<br>가치투자 가이드</h2>
    <p>${MODE === 'b' ? '매일 600여 개 기업의 적정 주가를 계산합니다.<br>다음 저평가 기업은 어디일까요?' : '매일 밤 9시, 한 기업의 적정 주가를 계산합니다.<br>내일은 어떤 회사일까요?'}</p>
    <div class="fbtn"><span>밸류노트 팔로우하기</span><b>→</b></div><div class="lk">600여 개 기업 점수와 적정 주가 · 프로필 링크</div></div><div class="disc">${esc(DISC)}</div>`);
  return out.map((html) => ({ cls: '', html: html.replace(/\*\*(.+?)\*\*/g, '<em>$1</em>') }));
}

function caption(x, a) {
  const { r, sc } = x, cur = r.cur || 'KRW', f = r.fin || {};
  const L = [a.ratio === null ? `${r.n}의 적정 주가는 얼마일까요?` : `${r.n}의 적정 주가는 ${money(sc.iv, r.cur || 'KRW')}? 지금 주가는 ${money(r.px, r.cur || 'KRW')}, ${gapSentence(a.ratio)}.`, ''];
  if (isNum(sc.iv)) L.push(`밸류노트가 계산한 적정 주가는 ${money(sc.iv, cur)}, 지금 주가는 ${money(r.px, cur)}입니다.`);
  L.push('');
  for (const c of a.cap) L.push(c, '');
  const q = [];
  if (isNum(f.roeAvg)) q.push(`5년 평균 ROE(주주 돈 100원으로 1년에 번 이익) ${n0(f.roeAvg, 1)}%`);
  if (!r.fin_sector && isNum(f.fcfConv)) q.push(`현금 전환율(이익 중 실제 현금으로 들어온 비율) ${n0(f.fcfConv)}%`);
  L.push(`회사 체력은 ${q.length ? q.join(', ') + '이고, ' : ''}밸류노트 점수는 100점 만점에 ${sc.b}점입니다.${a.pens.length ? ` 감점 신호는 ${a.pens.join(', ')}입니다.` : ''}`);
  L.push('', '적정 주가는 회사가 앞으로 벌어들일 이익과 현금을 바탕으로 밸류노트가 계산한 1주당 가치입니다. 현재가가 이보다 낮으면 저평가, 높으면 고평가입니다.');
  L.push('', `기업별 전체 계산은 밸류노트 기업 페이지(valuenote.co.kr/c/${slug(r)})에서 볼 수 있습니다.`);
  return L.join('\n').replace(/\n{3,}/g, '\n\n');
}

// ---------- 순위 카드: 저평가·고평가 TOP 10 (1~3위는 앱에서 공개) ----------
const RANK_ROTA = [['under', 'ALL', '5개 시장'], ['over', 'US', '미국'], ['under', 'KR', '한국'], ['over', 'KR', '한국'], ['under', 'JP,HK,CN', '일본·중국·홍콩'], ['over', 'JP', '일본']];
function rankCards(L, side, label) {
  const under = side === 'under', top = L.slice(0, 10);
  const row = (x, i, hide) => `<div class="rk${hide ? ' hide' : ''}"><span class="rn">${i + 1}</span><span class="rnm"><b>${hide ? '●●●●●' : esc(x.r.n)}</b><small>${esc(MKT[grpOf(x.r.m)])} · ${esc(x.r.ind || x.r.s || '')}</small></span>
    <span class="rv"><b class="${under ? 'pos' : 'neg'}">${esc(gapText(x.R))}</b><small>${hide ? '밸류노트에서 공개' : `현재 ${money(x.r.px, x.r.cur || 'KRW')} · 적정 주가 ${money(x.sc.iv, x.r.cur || 'KRW')}`}</small></span></div>`;
  const out = [];
  const h1 = under ? `지금 가장\n**저평가된**\n${label} 기업 TOP ${top.length}` : `좋은 회사지만\n**가장 비싼**\n${label} 기업 TOP ${top.length}`;
  out.push(`<div class="cover"><div class="k">밸류노트 순위 · ${esc(label)}</div><h1>${br(h1)}</h1>
    <div class="sub" style="margin-top:40px">${under ? '현재가가 계산한 적정 주가보다 25% 이상 낮고,<br>재무 점수 50점 이상 · 감점 신호 없는 회사' : '현재가가 적정 주가의 1.5배 이상인 회사 중<br>재무 점수이 높은 순서'}</div></div>`);
  out.push(`<div class="rlist">${top.slice(0, 3).map((x, i) => row(x, i, true)).join('')}</div>`
    + frame('TOP 3', '1~3위는\n밸류노트에서 공개합니다', '프로필 링크 → 기업 → 저평가·고평가', '600여 개 기업을 매일 다시 계산해 순위를 바꿉니다.'));
  for (const [a0, b0] of [[3, 7], [7, 10]]) {
    const part = top.slice(a0, b0); if (!part.length) continue;
    out.push(`<div class="rlist rlist-full">${part.map((x, i) => row(x, a0 + i, false)).join('')}</div>`);
  }
  out.push(`<div class="vis"><div class="steps">${[['적정 주가 계산', '과거 평균 이익·주주 이익과 자산 가치', '600여 곳'], ['현재가와 비교', under ? '적정 주가보다 25% 이상 낮은 회사' : '적정 주가의 1.5배 이상', '매일'], ['품질 거르기', under ? '재무 점수 50점 이상, 감점 신호 없음' : '재무 점수 60점 이상', '13개 지표']].map((m, i) => `<div><span class="n">${i + 1}</span><span class="tx">${m[0]}<small>${m[1]}</small></span><b>${m[2]}</b></div>`).join('')}</div></div>`
    + frame('기준', '이렇게 골랐습니다', under ? '싸다고 다 좋은 회사는 아닙니다.' : '좋은 회사도 비싸게 사면 수익이 줄어듭니다.', '저장해 두고 다음 주 순위와 비교해 보세요.'));
  out.push(`<div class="outro"><div class="be">VALUE INVESTING GUIDE</div><div class="logo">Value<i>Note</i></div><h2>현명한 투자를 위한<br>가치투자 가이드</h2>
    <p>매일 600여 개 기업의 적정 주가를 계산합니다.<br>내 종목은 몇 위일까요?</p>
    <div class="fbtn"><span>밸류노트 팔로우하기</span><b>→</b></div><div class="lk">전체 순위와 1~3위 · 프로필 링크</div></div><div class="disc">${esc(DISC)}</div>`);
  return out.map((html) => ({ cls: '', html: html.replace(/\*\*(.+?)\*\*/g, '<em>$1</em>') }));
}
function rankCaption(L, side, label) {
  const under = side === 'under', top = L.slice(0, 10);
  const lines = [under ? `지금 가장 저평가된 ${label} 기업 TOP ${top.length}입니다.` : `좋은 회사지만 가장 비싼 ${label} 기업 TOP ${top.length}입니다.`, '',
    under ? '현재가가 밸류노트가 계산한 적정 주가보다 25% 이상 낮고, 재무 점수 50점 이상(100점 만점)에 빚 부담·잦은 적자 같은 경고 신호가 없는 회사만 골랐습니다.' : '현재가가 적정 주가의 1.5배 이상인 회사 중 재무 점수가 높은 순서입니다. 좋은 회사도 비싸게 사면 수익이 줄어듭니다.', '',
    ...top.slice(3).map((x, i) => `${i + 4}위 ${x.r.n} · ${gapText(x.R)}`), '',
    '적정 주가는 회사가 앞으로 벌어들일 이익과 현금을 바탕으로 밸류노트가 계산한 1주당 가치입니다. 현재가가 이보다 낮으면 저평가, 높으면 고평가입니다.', '',
    '1~3위는 밸류노트 앱의 저평가·고평가 화면에서 볼 수 있습니다.'];
  return lines.join('\n');
}

// ---------- 릴스 대본 자동 생성 (영상은 reels 워크플로가 렌더) ----------
const SPECS = path.join(ROOT, 'scripts', 'reels', 'specs');
const DIG = ['영', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구'];
function sino(n) { n = Math.round(n); if (n === 0) return '영'; const u = ['', '십', '백', '천']; let s = '', d = String(n).split('').reverse();
  d.forEach((c, i) => { const k = +c; if (!k) return; s = ((k === 1 && i > 0) ? '' : DIG[k]) + u[i] + s; }); return s; }
const sayRatio = (R) => { const [a, b] = R.toFixed(1).split('.'); return b === '0' ? `${sino(+a)} 배` : `${sino(+a)} 점 ${DIG[+b]} 배`; };
function sayMoney(v, cur) {
  if (!isNum(v)) return '';
  if (cur === 'KRW') { const w = Math.round(v), man = Math.floor(w / 10000), cheon = Math.floor((w % 10000) / 1000), baek = Math.floor((w % 1000) / 100); return (man ? `${man}만 ` : '') + (cheon ? `${cheon}천 ` : '') + (baek ? `${baek}백 ` : '') + '원'; }
  const unit = { USD: '달러', JPY: '엔', HKD: '홍콩달러', CNY: '위안' }[cur] || '';
  return `${Math.round(v)} ${unit}`;
}
// 적정 주가는 밸류노트의 의견이 아니라 버핏·그레이엄이 쓴 계산법을 그대로 적용한 값임을 밝힌다 (사장님 지시 2026-10-18)
const FAIR_B = { type: 'statement', l1: '버핏의 계산법', l2: '앞으로 남을 현금의 가치', tone: 'gold', note: '주주에게 남는 현금(오너 이익)을 연 10%로 할인',
  say: '버핏은 앞으로 남을 현금을, 지금 가치로 바꿔 계산합니다.' };
const FAIR_G = { type: 'statement', l1: '그레이엄의 계산법', l2: '이익과 자산으로 계산', tone: 'gold', note: '은행·보험처럼 현금 계산이 맞지 않는 회사에 씁니다',
  say: '버핏의 스승 그레이엄은, 회사의 이익과 자산으로 계산합니다.' };
const FAIR_BG = { type: 'statement', l1: '버핏·그레이엄의 계산법', l2: '앞으로 남을 이익의 가치', tone: 'gold', note: '밸류노트의 의견이 아니라 그들의 계산 방식입니다',
  say: '버핏과 그레이엄의 방식으로 계산했습니다.' };
// 계산이 늘 맞지는 않는다는 점도 밝힌다: 버크셔도 이 방식으로는 비싸 보이는 알파벳을 2025년부터 샀다 (2025년 3분기 13F 공시)
const LIMIT_OVER = { type: 'statement', l1: '물론 늘 맞지는 않습니다', l2: '버크셔도 구글을 샀습니다', tone: 'ivory', note: '1등 프리미엄은 계산에 넣지 않습니다',
  say: '물론 늘 맞지는 않습니다. 버크셔도 비싸 보이던 구글을 샀습니다.' };
const LIMIT_UNDER = { type: 'statement', l1: '물론 늘 맞지는 않습니다', l2: '싼 데는 이유가 있을 수 있습니다', tone: 'ivory', note: '숫자는 출발점일 뿐입니다',
  say: '물론 늘 맞지는 않습니다. 싼 데는 이유가 있을 수 있습니다.' };
const METHOD_CAP = (g) => g
  ? '적정 주가는 벤저민 그레이엄의 계산법(이익과 자산을 함께 보는 그레이엄 공식)으로 계산한 1주당 가치입니다. 은행·보험처럼 현금흐름 계산이 맞지 않는 회사에 씁니다. 밸류노트의 의견이나 매수·매도 추천이 아닙니다.'
  : '적정 주가는 워런 버핏이 설명한 계산법으로 구한 1주당 가치입니다. 앞으로 주주에게 남을 현금(오너 이익)을 연 10%로 할인해 지금 가치로 바꿉니다. 밸류노트의 의견이나 매수·매도 추천이 아닙니다.';
const LIMIT_CAP = '이 계산이 늘 맞지는 않습니다. 세계 1위라는 프리미엄이나 앞으로의 신사업 가치는 계산에 넣지 않기 때문입니다. 실제로 버크셔 해서웨이도 2025년부터 이 방식으로는 비싸 보이는 알파벳(구글) 주식을 사들였습니다. 숫자는 판단의 출발점으로 봐 주세요.';
const pct1 = (v) => +Math.abs(v).toFixed(1);
// 대본 규칙(scripts/reels/README.md): 한 줄 = 완결된 한 문장, 자막과 음성은 같은 문장, 낯선 말은 처음 나올 때 뜻을 말한다.
// ---------- 2026-10-18 방식 변경: 점수·고평가 %·상승 여력을 릴스에 박지 않는다 ----------
// 트랙 레코드(2027-04 공개 검증)가 쌓이기 전까지는 '판정' 대신 '지금 주가에 담긴 기대'와 '실제 실적'을 나란히 보여 주고 판단은 보는 사람에게 넘긴다.
// 기대 = 지금 주가가 맞으려면 앞으로 10년간 필요한 이익 성장률(역DCF, scoring.js ig). 실제 = 지난 몇 년 주당순이익 연평균 성장률(fin.epsCagr, 상한 없이 그대로).
const GROW_CAP = (g) => Math.max(Math.min(g, 80), -30);
function expect(r, sc) {
  const ig = sc.ig, eps = r.fin?.epsCagr;
  if (!isNum(ig) || !isNum(eps)) return null;
  const e = +GROW_CAP(ig).toFixed(1), h = +eps.toFixed(1), d = e - h;
  const yrs = Math.max(3, (r.yrs || 6) - 1);
  if (h <= 0 || h > 100) return null;
  return { e, h, d, yrs, k: d > 3 ? 'ahead' : d < -3 ? 'behind' : 'match', disc: DISC_R[grpOf(r.m)] ?? 10 };
}
const realWord = (v) => v >= 0 ? `매년 ${pct1(v)}%씩 늘었습니다` : `매년 ${pct1(v)}%씩 줄었습니다`;
const sayPct = (v) => { const a = pct1(v), [i, f] = String(a).split('.'); return f ? `${sino(+i)} 점 ${f.split('').map((c) => DIG[+c]).join(' ')} 퍼센트` : `${sino(+i)} 퍼센트`; };
const CTA_SCORE = { type: 'cta', l1: '버핏 기준 점수는', l2: '밸류노트에서', say: '버핏 기준으로 본 점수와 적정 주가는, 밸류노트에서 확인하세요.' };
const NOT_ADVICE = '기대가 실제보다 높다고 꼭 비싼 것도, 낮다고 꼭 싼 것도 아닙니다. 판단은 각자의 몫이며 밸류노트의 의견이나 매수·매도 추천이 아닙니다.';
function reelCompany(x) {
  const { r, sc } = x, cur = r.cur || 'KRW', X = expect(r, sc);
  if (!X) throw new Error('기대·실제 성장률 없음 ' + r.n);
  const { e, h, yrs, k } = X, scenes = [];
  // 1) 첫 2초: 아는 이름 + 궁금증, 둘째 줄에 숫자로 답 (README 대본 규칙 11)
  const q = k === 'ahead' ? [`${r.n} 주가에는`, '큰 기대가 숨어 있습니다'] : k === 'behind' ? [`${r.n},`, '시장은 왜 이렇게 볼까요?'] : [`${r.n} 주가에`, '숨은 숫자가 있습니다'];
  const ans = e < 0 ? ['지금 주가는 이익이', `매년 ${pct1(e)}%씩 줄어든다고 봅니다`]
    : k === 'behind' ? ['지금 주가는 이익이', `매년 ${pct1(e)}%만 늘어도 맞는 가격입니다`] : ['지금 주가가 맞으려면', `이익이 매년 ${pct1(e)}% 늘어야 합니다`];
  const ansSay = e < 0 ? `지금 주가는 이익이, 매년 ${sayPct(e)}씩 줄어든다고 봅니다.`
    : k === 'behind' ? `지금 주가는 이익이, 매년 ${sayPct(e)}만 늘어도 맞는 가격입니다.` : `지금 주가가 맞으려면, 이익이 매년 ${sayPct(e)} 늘어야 합니다.`;
  scenes.push({ type: 'hook', top: r.n, num: { to: e, fmt: 'pct', dec: Number.isInteger(e) ? 0 : 1 }, tone: k === 'ahead' ? 'loss' : 'gold', label: '주가에 담긴 이익 성장 기대 (매년)',
    lines: [{ cap: q }, { cap: ans, say: ansSay }] });
  // 2) 기대 vs 실제 막대
  scenes.push({ type: 'bars', title: '주가에 담긴 기대 vs 실제',
    items: [{ label: '지금 주가에 담긴 기대 (앞으로 10년)', v: Math.max(Math.abs(e), .5), text: `연 ${e}%`, tone: k === 'ahead' ? 'loss' : 'gold' },
            { label: `지난 ${yrs}년 실제 이익 성장`, v: Math.max(Math.abs(h), .5), text: `연 ${h}%`, tone: h >= 0 ? 'good' : 'loss' }],
    lines: [{ cap: [`지난 ${yrs}년 동안 실제로는`, realWord(h)], say: `지난 ${sino(yrs)} 년 동안 실제로는, 매년 ${sayPct(h)}씩 ${h >= 0 ? '늘었습니다' : '줄었습니다'}.` }] });
  // 3) 판단은 보는 사람에게
  const st = k === 'ahead' ? ['이 기대, 이뤄질까요?', '판단은 당신의 몫입니다', '이 기대가 이뤄질까요? 판단은 당신의 몫입니다.']
    : k === 'behind' ? ['시장이 너무 비관적일까요?', '아니면 이유가 있을까요?', '시장이 너무 비관적일까요? 아니면 이유가 있을까요?']
    : ['기대와 실적이', '비슷한 수준입니다', '주가에 담긴 기대와 실제 실적이 비슷한 수준입니다.'];
  scenes.push({ type: 'statement', l1: st[0], l2: st[1], tone: 'gold', note: '지금 주가에서 필요한 성장률을 거꾸로 계산했습니다', say: st[2] });
  scenes.push(CTA_SCORE);
  const name = r.n.replace(/\s+/g, '');
  const cap = (e >= 0 ? `${r.n}의 지금 주가(${money(r.px, cur)})가 맞으려면 앞으로 10년간 이익이 매년 ${pct1(e)}%씩 늘어야 합니다.` : `${r.n}의 지금 주가(${money(r.px, cur)})는 앞으로 10년간 이익이 매년 ${pct1(e)}%씩 줄어든다고 보는 가격입니다.`)
    + ` 지난 ${yrs}년 동안 주당순이익은 실제로 ${realWord(h)}.\n\n`
    + `이 숫자는 지금 주가를 거꾸로 계산해, 시장이 이 회사에 어떤 성장을 기대하고 있는지 꺼낸 것입니다. 주주에게 남는 현금을 연 ${X.disc}%로 할인하는 버핏의 계산법을 거꾸로 적용했습니다.\n\n`
    + (k === 'ahead' ? '기대가 실제보다 높다는 것은 앞으로 실적이 지금보다 훨씬 빨라져야 지금 주가가 설명된다는 뜻입니다. 1등 프리미엄이나 신사업처럼 숫자에 아직 잡히지 않은 가치가 있을 수도 있습니다.\n\n'
      : k === 'behind' ? '기대가 실제보다 낮다는 것은 시장이 앞으로 실적이 꺾일 것으로 본다는 뜻입니다. 시장이 지나치게 비관적일 수도 있고, 숫자에 아직 드러나지 않은 이유가 있을 수도 있습니다.\n\n' : '')
    + NOT_ADVICE + `\n\n버핏·그레이엄 기준으로 본 점수와 적정 주가는 밸류노트 기업 페이지(valuenote.co.kr/c/${slug(r)})에서 볼 수 있습니다.`;
  return { title: `${r.n} 주가에 담긴 기대`, mood: k === 'ahead' ? 'tense' : 'calm', scenes, hashtags: [name, name + '주가', '주식공부', '가치투자', '밸류노트'], caption: cap };
}
// 순위 릴스: 기대가 실적보다 가장 앞선 곳 / 시장이 실적보다 가장 낮게 보는 곳. 1~3위 이름은 앱에서 공개
function rankByExpect(L, side) {
  return L.map((x) => ({ ...x, X: expect(x.r, x.sc) })).filter((x) => x.X && (side === 'under' ? x.X.d < -3 : x.X.d > 3))
    .sort((p, q) => side === 'under' ? p.X.d - q.X.d : q.X.d - p.X.d);
}
function reelRank(L, side, label) {
  const under = side === 'under', top = L.slice(0, 5), X1 = top[0].X;
  const it = (x) => `${x.r.n} · 기대 ${x.X.e}% · 실제 ${x.X.h}%`;
  const scenes = [];
  if (under) scenes.push({ type: 'hook', top: `${label} TOP 5`, num: { to: X1.e, fmt: 'pct', dec: 1 }, tone: 'gold', label: '1위 주가에 담긴 이익 성장 기대 (매년)',
    lines: [{ cap: ['실적에 비해 시장이', '가장 낮게 보는 회사 5곳'] }, { cap: X1.e >= 0 ? ['1위는 이익이 매년', `${pct1(X1.e)}%만 늘어도 되는 가격입니다`] : ['1위는 이익이 매년', `${pct1(X1.e)}%씩 줄어든다고 보는 가격입니다`],
      say: X1.e >= 0 ? `일위는 이익이 매년, ${sayPct(X1.e)}만 늘어도 되는 가격입니다.` : `일위는 이익이 매년, ${sayPct(X1.e)}씩 줄어든다고 보는 가격입니다.` }] });
  else scenes.push({ type: 'hook', top: `${label} TOP 5`, num: { to: X1.e, fmt: 'pct', dec: 1 }, tone: 'loss', label: '1위 주가에 담긴 이익 성장 기대 (매년)',
    lines: [{ cap: ['실적보다 기대가', '가장 앞서 있는 회사 5곳'] }, { cap: ['1위는 이익이 매년', `${pct1(X1.e)}% 늘어야 지금 주가가 맞습니다`], say: `일위는 이익이 매년, ${sayPct(X1.e)} 늘어야 지금 주가가 맞습니다.` }] });
  scenes.push({ type: 'list', title: `${label} · 주가에 담긴 기대와 실제`, items: top.map((x, i) => i < 3 ? `${i + 1}위 ●●●●● · 기대 ${x.X.e}% · 실제 ${x.X.h}%` : `${i + 1}위 ${it(x)}`),
    say: `네 번째는 ${top[3].r.n}, 다섯 번째는 ${top[4].r.n}입니다.` });
  scenes.push({ type: 'statement', l1: under ? '시장이 너무 비관적일까요?' : '이 기대, 이뤄질까요?', l2: under ? '아니면 이유가 있을까요?' : '판단은 당신의 몫입니다', tone: 'gold', note: '기대는 앞으로 10년 매년, 실제는 지난 몇 년 매년 이익 성장률',
    say: under ? '시장이 너무 비관적일까요? 아니면 이유가 있을까요?' : '이 기대가 이뤄질까요? 판단은 당신의 몫입니다.' });
  scenes.push({ type: 'cta', l1: '1~3위는', l2: '밸류노트에서', say: '일위부터 삼위는, 프로필 링크의 밸류노트에서 확인하세요.' });
  return { title: `${under ? '시장이 낮게 보는' : '기대가 앞선'} TOP 5 · ${label}`, mood: 'calm', scenes, hashtags: ['주식공부', '미국주식', '가치투자', '주식투자', '밸류노트'].map((h) => label === '한국' && h === '미국주식' ? '한국주식' : h),
    caption: `${under ? `실적에 비해 시장이 가장 낮게 보는 ${label} 회사 TOP 5입니다.` : `실적보다 주가에 담긴 기대가 가장 앞서 있는 ${label} 회사 TOP 5입니다.`}\n\n기대는 지금 주가가 맞으려면 앞으로 10년간 필요한 이익 성장률(매년)이고, 실제는 지난 몇 년 동안 주당순이익이 실제로 늘어난 속도(매년)입니다. 주주에게 남는 현금을 할인하는 버핏의 계산법을 거꾸로 적용해 구했습니다.\n\n`
      + top.slice(3).map((x, i) => `${i + 4}위 ${x.r.n} · 기대 연 ${x.X.e}% · 실제 연 ${x.X.h}%`).join('\n') + '\n\n' + NOT_ADVICE + '\n\n1~3위와 버핏 기준 점수는 밸류노트에서 볼 수 있습니다.' };
}

const state0 = path.join(OUT, 'state.json');
const state = fs.existsSync(state0) ? JSON.parse(fs.readFileSync(state0, 'utf8')) : { used: [] };
const qPath = path.join(OUT, 'queue.json');
const queue = fs.existsSync(qPath) ? JSON.parse(fs.readFileSync(qPath, 'utf8')) : [];
if (['reel1', 'reel2', 'ra', 'rb', 'rr', 'rm'].includes(MODE)) {
  const when = process.env.REEL_AT || `${ymd}T${POST_TIME}:00+09:00`;
  const taken = !process.env.REEL_ID && fs.readdirSync(SPECS).filter((f) => f.endsWith('.json')).some((f) => { try { return JSON.parse(fs.readFileSync(path.join(SPECS, f), 'utf8')).scheduled_at === when; } catch (_) { return false; } });
  if (taken) { console.log('이미 릴스 있음', when); process.exit(0); }
  setSettings({});
  const rows = await load(); if (rows.length < 300) throw new Error('rows too few');
  let spec;
  if (MODE !== 'reel2' && MODE !== 'rr') {
    // 기업 릴스(11:00 저평가·21:00 오늘의 기업·12:30 예비): 카드와 릴스가 같은 회사를 겹쳐 쓰지 않게 한 목록을 같이 쓴다
    const used = new Set([...(state.used || []), ...(state.reelUsed || [])]);
    // REEL_T=<티커>: 같은 회사로 대본만 다시 만들 때 (예: 문구 규칙이 바뀐 뒤 다시 만들기)
    const forced = process.env.REEL_T ? rows.find((r) => r.t === process.env.REEL_T) : null;
    const x0 = forced ? { r: forced, sc: score(forced) } : pick(rows, { used: [...used] }); if (!x0) throw new Error('릴스 회사 없음');
    spec = reelCompany(x0);
    if (MODE === 'ra') spec.title = `오늘의 기업 · ${x0.r.n}`;
    if (MODE === 'rb') spec.title = `시장이 낮게 보는 기업 · ${x0.r.n}`;
    if (MODE === 'rm') spec.title = `기대가 앞선 기업 · ${x0.r.n}`;
    if (!forced) { state.reelUsed = [...(state.reelUsed || []), x0.r.t]; state.used = [...(state.used || []), x0.r.t]; }
    fs.writeFileSync(path.join(OUT, 'state.json'), JSON.stringify(state, null, 1));
  } else {
    const day = Math.round((Date.parse(ymd) - Date.parse('2026-10-18')) / 864e5) + (MODE === 'rr' ? 0 : 3);
    const [side, mkt, label] = RANK_ROTA[((day % RANK_ROTA.length) + RANK_ROTA.length) % RANK_ROTA.length];
    const L = rankByExpect(side === 'under' ? underList(rows, mkt) : overList(rows, mkt), side);
    if (L.length < 5) throw new Error('순위 후보 부족');
    spec = reelRank(L, side, label);
  }
  const id = process.env.REEL_ID || ('A' + tag.slice(2) + SLOT[1]);
  fs.writeFileSync(path.join(SPECS, id + '.json'), JSON.stringify({ id, scheduled_at: when, threads_tag: '주식', ...spec }, null, 1));
  console.log(JSON.stringify({ id, title: spec.title })); process.exit(0);
}
const ID = SLOT[0] + tag + SLOT[1], DIRN = SLOT[0] === 'K' ? 'k' + tag : tag + SLOT[1];
if (queue.some((q) => q.id === ID)) { console.log('이미 생성됨', ID); process.exit(0); }

setSettings({});
const rows = await load();
if (rows.length < 300) throw new Error('rows too few');
let x = null, a = null, C, RK = null;
if (MODE === 'rank') {
  const day = Math.round((Date.parse(ymd) - Date.parse('2026-10-18')) / 864e5);
  const [side, mkt, label] = RANK_ROTA[((day % RANK_ROTA.length) + RANK_ROTA.length) % RANK_ROTA.length];
  const L = (side === 'under' ? underList(rows, mkt).sort((p, q) => p.R - q.R) : overList(rows, mkt).sort((p, q) => q.sc.q - p.sc.q || q.R - p.R));
  if (L.length < 6) throw new Error('순위 후보 부족 ' + L.length);
  RK = { L, side, label }; C = rankCards(L, side, label);
} else {
  x = pick(rows, state);
  if (!x) throw new Error('고를 회사가 없음');
  a = analyze(x); C = cards(x, a);
}
const dir = path.join(OUT, DIRN); fs.mkdirSync(dir, { recursive: true });
const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1080, height: 1350 } });
const images = [];
for (let i = 0; i < C.length; i++) {
  const pgs = C.map((_, k) => k === i ? `<b>${String(k + 1).padStart(2, '0')}</b>` : `<span>${String(k + 1).padStart(2, '0')}</span>`).join('');
  const top = `<div class="top"><span class="wm">Value<i>Note</i><b class="ko">밸류노트</b></span><span class="pgs">${pgs}</span></div>${i > 0 && i < C.length - 1 ? '<div class="wmk">VALUENOTE</div>' : ''}${i === 0 ? '<div class="swipe">넘겨서 보기 →</div>' : ''}`;
  await pg.setContent(`<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${CSS}</style></head><body><section class="s ${C[i].cls}">${top}${C[i].html}</section></body></html>`);
  await pg.evaluate(() => document.fonts.ready);
  const fn = String(i + 1).padStart(2, '0') + '.jpg';
  await pg.screenshot({ path: path.join(dir, fn), type: 'jpeg', quality: 92 });
  images.push(`/social/company/${DIRN}/${fn}`);
}
await b.close();

let item;
if (RK) {
  item = { id: ID, seq: Number(tag), title: `${RK.side === 'under' ? '저평가' : '고평가'} TOP 10 · ${RK.label}`, scheduled_at: `${ymd}T${POST_TIME}:00+09:00`, caption: rankCaption(RK.L, RK.side, RK.label),
    hashtags: [RK.side === 'under' ? '저평가주' : '고평가주', '저평가주식', '가치투자', '주식공부', '밸류노트'], threads_tag: '주식', images, to_ig: true, approved: true };
} else {
  const name = x.r.n.replace(/\s+/g, '');
  item = { id: ID, seq: Number(tag), title: `${MODE === 'b' ? '저평가 기업' : MODE === 'am' ? '좋은 회사, 비싼 가격' : '오늘의 기업'} · ${x.r.n}`, scheduled_at: `${ymd}T${POST_TIME}:00+09:00`, caption: caption(x, a),
    hashtags: [name, name + '주가', MODE === 'b' ? '저평가주' : '가치투자', '주식공부', '밸류노트'], threads_tag: '주식', images, to_ig: true, approved: true };
  fs.writeFileSync(state0, JSON.stringify({ ...state, used: [...(state.used || []), x.r.t] }, null, 1));
}
fs.writeFileSync(qPath, JSON.stringify([...queue.filter((q) => q.id !== item.id).slice(-14), item], null, 1));
for (const f of fs.readdirSync(OUT)) if (/^k?\d{8}b?$/.test(f) && f.replace(/\D/g, '') < new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10).replace(/-/g, '')) fs.rmSync(path.join(OUT, f), { recursive: true });
console.log(JSON.stringify({ id: item.id, title: item.title }));
