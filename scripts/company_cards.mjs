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

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW || 'playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const OUT = path.join(ROOT, 'social', 'company');
const SUIT = path.join(ROOT, 'fonts', 'SUIT-Variable.woff2');
const HANDLE = '@value.note.korea';
const POST_TIME = '21:00';
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
  return docs.filter((d) => d.id.startsWith('chunk-')).sort((a, b) => a.id.localeCompare(b.id)).flatMap((d) => d.data?.rows || []);
}

// 점수 모양으로 이야기 각도를 정한다
function angle(r, sc) {
  const pens = (sc.flags || []).filter((f) => !WARN_FLAGS.has(f));
  const { q, v, b } = sc;
  if (b >= 70 && !pens.length) return { k: 'pass', t: `${r.n},\n버핏 기준 **${b}점**`, s: '품질과 가격이 함께\n기준(70점)을 넘은 드문 경우입니다.' };
  if (q >= 80 && v < 35) return { k: 'pricey', t: `${r.n},\n품질 **${q}점**인데\n종합은 ${b}점`, s: '좋은 회사와 좋은 가격은\n다른 이야기입니다.' };
  const ratio = isNum(sc.iv) && sc.iv > 0 && isNum(r.px) ? r.px / sc.iv : null;
  if (ratio && ratio >= 1.5) return { k: 'over', t: `${r.n},\n지금 가격은\n적정 가격의 **${n0(ratio, 1)}배**`, s: `숫자 품질은 ${q}점.\n그런데 왜 종합은 ${b}점일까요?` };
  if (v >= 60 && q < 50) return { k: 'trap', t: `${r.n},\n싸 보이는데\n왜 **${b}점**일까`, s: '저평가 점수는 높지만\n이익의 질이 따라오지 못합니다.' };
  if (pens.length) return { k: 'flag', t: `${r.n},\n감점 신호 **${pens.length}개**`, s: `${pens.join(', ')}.\n신호 하나에 8점씩 깎입니다.` };
  return { k: 'plain', t: `${r.n}의\n버핏 점수는 **${b}점**`, s: `숫자 품질 ${q}점, 저평가 ${v}점.\n어디서 점수가 갈렸는지 보겠습니다.` };
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
  const all = rows.map((r) => ({ r, sc: scoreRow(r, null, 30) }))
    .filter((x) => isNum(x.sc.b) && isNum(x.sc.q) && isNum(x.sc.v) && x.r.dataConf !== 'low' && !used.has(x.r.t));
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
.disc{position:absolute;left:84px;right:84px;bottom:60px;font-size:22px;color:#7A8394;line-height:1.5}`;

// ---------- 분석: 적정 주가 → 계산 방법 → 차이가 나는 이유 ----------
const DISC_R = { KR: 10, US: 10, CN: 11, HK: 11, JP: 9 };
function analyze(x) {
  const { r, sc } = x, cur = r.cur || 'KRW', f = r.fin || {}, val = r.val || {}, g = grpOf(r.m);
  const M = (v) => money(v, cur);
  const pens = (sc.flags || []).filter((fl) => !WARN_FLAGS.has(fl)), warns = (sc.flags || []).filter((fl) => WARN_FLAGS.has(fl));
  const ratio = isNum(sc.iv) && sc.iv > 0 && isNum(r.px) ? r.px / sc.iv : null;
  const o = { pens, warns, ratio, method: [], why: [], alt: null, verdict: '', cap: [] };
  // 1) 결론
  if (ratio === null) o.verdict = '적정 가격을 계산할 이익 자료가 부족합니다.';
  else if (ratio >= 2) o.verdict = `현재가는 계산한 적정 가격의 **${n0(ratio, 1)}배**입니다.`;
  else if (ratio > 1.05) o.verdict = `현재가가 적정 가격보다 **${n0((ratio - 1) * 100)}%** 높습니다.`;
  else if (ratio >= 0.95) o.verdict = '현재가가 적정 가격과 **거의 같습니다**.';
  else o.verdict = `현재가가 적정 가격보다 **${n0((1 - ratio) * 100)}%** 낮습니다.`;
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
    o.method.push(['공식', '√(22.5 × 이익 × 자산)', '그레이엄이 쓴 적정 가격 공식']);
    o.methodNote = r.fin_sector ? '은행·보험은 현금흐름 계산이 맞지 않아 이익과 자산으로 봅니다.' : '현금 기준 이익이 마이너스라 이익과 자산으로 계산했습니다.';
    o.cap.push(`계산은 그레이엄 공식으로 했습니다. 주당순이익 ${M(val.eps)}과 주당순자산 ${M(val.bps)}을 곱해 22.5배 한 값의 제곱근입니다. ${o.methodNote}`);
  }
  // 3) 차이가 나는 이유
  if (isNum(sc.ig) && isNum(sc.hist)) {
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
      s: `이 이익이 계속된다면 적정 가격은 **${M(sc.ivNow)}**입니다. 결국 질문은 하나입니다. 지금 이익이 한때의 호황인가, 새로운 수준인가.` };
    o.cap.push(`다만 최근 1년 주당순이익 ${M(val.eps)}은 평균의 ${n0(val.eps / val.epsAvg, 1)}배입니다. 이 이익이 계속된다면 적정 가격은 ${M(sc.ivNow)}입니다. 결국 핵심은 지금 이익이 한때의 호황인지, 새로운 수준인지입니다.`);
  }
  return o;
}

// 첫 장 문구: "○○의 적정 주가는 68,685원?" + 아래 줄에 지금 주가와 차이
function hook(r, sc, a) {
  if (a.ratio === null) return `${r.n}의\n적정 주가는\n얼마일까?`;
  return `${r.n}의\n적정 주가는\n**${money(sc.iv, r.cur || 'KRW')}**?`;
}
function gapText(R) {
  if (R >= 1.5) return `적정가의 ${n0(R, 1)}배`;
  if (R > 1.05) return `적정가보다 ${n0((R - 1) * 100)}% 높음`;
  if (R >= 0.95) return '적정가와 비슷';
  return `적정가보다 ${n0((1 - R) * 100)}% 낮음`;
}

function cards(x, a) {
  const { r, sc } = x, cur = r.cur || 'KRW', f = r.fin || {}, g = grpOf(r.m);
  const code = r.code || r.t;
  const out = [];
  out.push({ cls: '', html: `<div class="body"><div class="k">오늘의 기업 분석 · ${MKT[g]}</div><h1>${br(hook(r, sc, a))}</h1>
    <div class="sub">지금 주가 ${money(r.px, cur)}${a.ratio !== null ? `<br><em>${gapText(a.ratio)}</em>` : ''}</div><div class="meta">${esc(code)}${r.ind ? ' · ' + esc(r.ind) : ''}</div></div><div class="swipe">넘겨서 보기 →</div>` });
  if (isNum(sc.iv)) {
    out.push({ cls: '', html: `<div class="body"><h2>결론부터</h2><div class="px"><div><div class="t">현재가</div><div class="v">${money(r.px, cur)}</div></div><div><div class="t">적정 주가</div><div class="v" style="color:#E2C489">${money(sc.iv, cur)}</div></div></div>
      <div class="lead">${br(a.verdict)}</div><div class="note" style="margin-top:30px">밸류노트 종합 점수 ${sc.b}점 · 품질 ${sc.q}점 · 저평가 ${sc.v}점</div></div>` });
  }
  if (a.method.length) {
    out.push({ cls: '', html: `<div class="body"><h2>어떻게 계산했나</h2><div class="steps">${a.method.map((m, i) => `<div><span class="n">${i + 1}</span><span class="tx">${m[0]}<small>${esc(m[2])}</small></span><b>${esc(m[1])}</b></div>`).join('')}</div>
      <div class="note" style="margin-top:34px">${esc(a.methodNote)}</div></div>` });
  }
  if (a.why.length || a.alt) {
    out.push({ cls: '', html: `<div class="body"><h2>왜 이런 차이가 날까</h2>${a.why.map((w) => `<div class="lead" style="margin-bottom:26px">${br(w)}</div>`).join('')}
      ${a.alt ? `<div class="alt"><div class="lead" style="font-size:38px">${br(a.alt.t)}</div><div class="note" style="font-size:34px">${br(a.alt.s)}</div></div>` : ''}</div>` });
  }
  const rows = [
    ['5년 평균 ROE', isNum(f.roeAvg) ? n0(f.roeAvg, 1) + '%' : null, '자기자본으로 1년에 버는 비율'],
    ['현금 전환율', !r.fin_sector && isNum(f.fcfConv) ? n0(f.fcfConv) + '%' : null, '이익 중 실제로 들어온 현금'],
    ['장기부채 ÷ 순이익', !r.fin_sector && isNum(f.ltdNi) ? (f.ltdNi < 0.05 ? '거의 없음' : n0(f.ltdNi, 1) + '배') : null, '이익으로 빚을 갚는 데 걸리는 해'],
    ['PER', isNum(sc.per) ? n0(sc.per, 1) + '배' : null, '그레이엄 기준 15배 이하'],
  ].filter((m) => m[1]);
  out.push({ cls: '', html: `<div class="body"><h2>회사 체력은 어떨까</h2><div class="rows">${rows.map((m) => `<div><span>${m[0]}<small>${m[2]}</small></span><b>${m[1]}</b></div>`).join('')}</div>
    ${a.pens.length || a.warns.length ? `<div class="flags">${a.pens.map((fl) => `<span class="flag">감점 · ${esc(fl)}</span>`).join('')}${a.warns.map((fl) => `<span class="flag w">경고 · ${esc(fl)}</span>`).join('')}</div>` : ''}</div>` });
  out.push({ cls: 'cta', html: `<div class="body"><h2>내 종목의<br>**적정 주가는?**</h2><div class="sub">${josa(esc(r.n), '을', '를')} 포함해 600여 개 기업을<br>같은 방법으로 계산해 두었습니다.</div><div class="btn">프로필 링크에서 확인하기</div><div class="handle">밸류노트 · ${HANDLE}</div></div><div class="disc">${esc(DISC)}</div>` });
  return out.map((c) => ({ ...c, html: c.html.replace(/\*\*(.+?)\*\*/g, '<em>$1</em>') }));
}

function caption(x, a) {
  const { r, sc } = x, cur = r.cur || 'KRW', f = r.fin || {};
  const L = [a.ratio === null ? `${r.n}의 적정 주가는 얼마일까요?` : `${r.n}의 적정 주가는 ${money(sc.iv, r.cur || 'KRW')}? 지금 주가는 ${money(r.px, r.cur || 'KRW')}, ${gapText(a.ratio).replace(/음$/, '습니다').replace(/배$/, '배입니다').replace(/비슷$/, '비슷합니다')}.`, ''];
  if (isNum(sc.iv)) L.push(`밸류노트가 계산한 적정 주가는 ${money(sc.iv, cur)}, 지금 주가는 ${money(r.px, cur)}입니다.`);
  L.push('');
  for (const c of a.cap) L.push(c, '');
  const q = [];
  if (isNum(f.roeAvg)) q.push(`5년 평균 ROE ${n0(f.roeAvg, 1)}%`);
  if (!r.fin_sector && isNum(f.fcfConv)) q.push(`현금 전환율 ${n0(f.fcfConv)}%`);
  L.push(`회사 체력은 ${q.length ? q.join(', ') + '이고, ' : ''}밸류노트 종합 점수는 ${sc.b}점(품질 ${sc.q}, 저평가 ${sc.v})입니다.${a.pens.length ? ` 감점 신호는 ${a.pens.join(', ')}입니다.` : ''}`);
  L.push('', `기업별 전체 계산은 밸류노트 기업 페이지(valuenote.co.kr/c/${slug(r)})에서 볼 수 있습니다.`);
  return L.join('\n').replace(/\n{3,}/g, '\n\n');
}

const state0 = path.join(OUT, 'state.json');
const state = fs.existsSync(state0) ? JSON.parse(fs.readFileSync(state0, 'utf8')) : { used: [] };
const qPath = path.join(OUT, 'queue.json');
const queue = fs.existsSync(qPath) ? JSON.parse(fs.readFileSync(qPath, 'utf8')) : [];
if (queue.some((q) => q.id === 'C' + tag)) { console.log('이미 생성됨', tag); process.exit(0); }

setSettings({});
const rows = await load();
if (rows.length < 300) throw new Error('rows too few');
const x = pick(rows, state);
if (!x) throw new Error('고를 회사가 없음');
const a = analyze(x);
const C = cards(x, a);
const dir = path.join(OUT, tag); fs.mkdirSync(dir, { recursive: true });
const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1080, height: 1350 } });
const images = [];
for (let i = 0; i < C.length; i++) {
  const top = `<div class="top"><span class="wm">Value<i>Note</i><b class="ko">밸류노트</b></span><span class="pg">${i + 1} / ${C.length}</span></div>`;
  await pg.setContent(`<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${CSS}</style></head><body><section class="s ${C[i].cls}">${top}${C[i].html}</section></body></html>`);
  await pg.evaluate(() => document.fonts.ready);
  const fn = String(i + 1).padStart(2, '0') + '.jpg';
  await pg.screenshot({ path: path.join(dir, fn), type: 'jpeg', quality: 92 });
  images.push(`/social/company/${tag}/${fn}`);
}
await b.close();

const name = x.r.n.replace(/\s+/g, '');
const item = { id: 'C' + tag, seq: Number(tag), title: `오늘의 기업 · ${x.r.n}`, scheduled_at: `${ymd}T${POST_TIME}:00+09:00`, caption: caption(x, a),
  hashtags: [name, name + '주가', '가치투자', '주식공부', '밸류노트'], threads_tag: '주식', images, to_ig: true, approved: true };
fs.writeFileSync(qPath, JSON.stringify([...queue.filter((q) => q.id !== item.id).slice(-6), item], null, 1));
fs.writeFileSync(state0, JSON.stringify({ used: [...(state.used || []), x.r.t] }, null, 1));
for (const f of fs.readdirSync(OUT)) if (/^\d{8}$/.test(f) && f < new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10).replace(/-/g, '')) fs.rmSync(path.join(OUT, f), { recursive: true });
console.log(JSON.stringify({ id: item.id, n: x.r.n, m: x.r.m, angle: a.k, b: x.sc.b, q: x.sc.q, v: x.sc.v }));
