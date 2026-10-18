// 기업별 공개 페이지 생성기: 스크리너 데이터(공개 읽기)를 받아 화면과 같은 점수 코드로 계산하고
// /c/<코드>.html 600여 개 + /c/index.html + sitemap.xml + robots.txt 를 만든다.
// 실행: node scripts/build_pages.mjs   (GitHub Actions pages.yml 이 매일 돌린다)
import fs from 'node:fs';
import path from 'node:path';
import { scoreRow, grpOf, WARN_FLAGS, setSettings } from '../supabase/functions/watch-select/scoring.js';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SITE = 'https://www.valuenote.co.kr';
const INDEXNOW_KEY = 'dac4f1ede3c1ee2f77cc7f3ddcc0c5b8'; // 사이트 루트의 dac4f1ede3c1ee2f77cc7f3ddcc0c5b8.txt 와 같아야 한다
const cfgSrc = fs.readFileSync(path.join(ROOT, 'config.js'), 'utf8');
const URL0 = cfgSrc.match(/SUPABASE_URL:\s*'([^']+)'/)[1];
const KEY = cfgSrc.match(/SUPABASE_ANON_KEY:\s*'([^']+)'/)[1];

// 감점·경고 설명은 앱(index.html)의 FLAG_HELP 를 그대로 가져온다
const html0 = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
let FLAG_HELP = {};
try { FLAG_HELP = new Function('return ' + html0.match(/const FLAG_HELP = (\{.*?\});/)[1])(); } catch (_) {}

const MKT = { KR: '국내', US: '미국', CN: '중국 A', HK: '홍콩', JP: '일본' };
const MKT_ORDER = ['KR', 'US', 'JP', 'HK', 'CN'];
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const isNum = (v) => typeof v === 'number' && isFinite(v);
const slug = (r) => String(r.t || r.code).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const n0 = (v, d = 0) => (isNum(v) ? v.toLocaleString('ko-KR', { maximumFractionDigits: d, minimumFractionDigits: d }) : '–');
function money(v, cur) {
  if (!isNum(v)) return '–';
  if (cur === 'KRW') return n0(v) + '원';
  if (cur === 'JPY') return n0(v) + '엔';
  if (cur === 'CNY') return n0(v, 2) + '위안';
  if (cur === 'HKD') return 'HK$' + n0(v, 2);
  return '$' + n0(v, 2);
}

async function load() {
  const r = await fetch(`${URL0}/rest/v1/docs?collection=eq.screen&select=id,data`, { headers: { apikey: KEY, Authorization: 'Bearer ' + KEY } });
  if (!r.ok) throw new Error('screen ' + r.status);
  const docs = await r.json();
  const meta = docs.find((d) => d.id === 'meta')?.data || {};
  const rows = docs.filter((d) => d.id.startsWith('chunk-')).sort((a, b) => a.id.localeCompare(b.id)).flatMap((d) => d.data?.rows || []);
  return { meta, rows };
}

function summary(r, sc) {
  const out = [];
  const f = r.fin || {};
  if (isNum(sc.q)) {
    const bits = [];
    if (isNum(f.roeAvg)) bits.push(`5년 평균 ROE ${n0(f.roeAvg, 1)}%`);
    if (isNum(f.fcfConv)) bits.push(`이익의 ${n0(f.fcfConv)}%가 현금으로 들어옴`);
    if (isNum(f.ltdNi)) bits.push(`장기부채는 순이익의 ${n0(f.ltdNi, 1)}배`);
    out.push(`숫자 품질은 ${sc.q}점입니다${bits.length ? ' (' + bits.join(', ') + ')' : ''}.`);
  }
  if (isNum(sc.v)) {
    let s = `저평가 점수는 ${sc.v}점입니다.`;
    if (isNum(sc.iv) && sc.iv > 0 && isNum(r.px) && r.px / sc.iv >= 2) s += ` 현재가가 계산한 적정 가격의 ${n0(r.px / sc.iv, 1)}배입니다.`;
    else if (isNum(sc.mos) && isNum(sc.iv)) s += sc.mos >= 0
      ? ` 현재가가 계산한 적정 가격보다 ${n0(sc.mos)}% 낮습니다.`
      : ` 현재가가 계산한 적정 가격보다 ${n0(-sc.mos)}% 높습니다.`;
    out.push(s);
  }
  if (isNum(sc.q) && isNum(sc.v)) {
    if (sc.q >= 80 && sc.v < 30) out.push('회사는 좋지만 지금 가격은 비싼 편이라, 적정 가격 근처로 내려올 때를 기다리는 유형입니다.');
    else if (sc.q >= 70 && sc.v >= 60 && !(sc.flags || []).some((fl) => !WARN_FLAGS.has(fl))) out.push('품질과 가격이 함께 기준에 가까운 드문 경우입니다. 감점 신호와 사업 내용을 함께 확인해 보세요.');
    else if (sc.q < 50 && sc.v >= 60) out.push('숫자로는 싸 보이지만 이익의 질이 낮아, 싼 데에는 이유가 있을 수 있습니다.');
  }
  return out;
}

const CSS = `@font-face{font-family:SUIT;src:url(/fonts/SUIT-Variable.woff2) format("woff2");font-weight:100 900;font-display:swap}
:root{--navy:#0E1A2B;--navy2:#16263D;--gold:#C99A50;--gold2:#E4C78D;--ink:#1B2433;--muted:#6B7584;--line:#E7E2D8;--bg:#F6F3EC;--card:#fff;--good:#2E8B62;--warn:#C27C1E;--bad:#C2493A}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 SUIT,Pretendard,-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;word-break:keep-all}
a{color:inherit}
.top{background:var(--navy);color:#F3EEE3}
.top .in{max-width:760px;margin:0 auto;padding:14px 16px;display:flex;align-items:center;justify-content:space-between;gap:12px}
.brand{font-weight:800;font-size:19px;text-decoration:none;letter-spacing:-.2px}.brand i{color:var(--gold2);font-style:italic}
.top .go{background:linear-gradient(90deg,#C99A50,#E4C78D);color:#0A1322;font-weight:800;text-decoration:none;padding:8px 14px;border-radius:999px;font-size:14px;white-space:nowrap}
main{max-width:760px;margin:0 auto;padding:18px 16px 40px}
.crumb{font-size:13px;color:var(--muted);margin-bottom:10px}.crumb a{text-decoration:none}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px;margin:12px 0}
h1{font-size:26px;line-height:1.3;margin:0 0 4px;letter-spacing:-.4px}h2{font-size:18px;margin:0 0 10px}
.sub{color:var(--muted);font-size:14px}
.hero{background:linear-gradient(160deg,var(--navy2),var(--navy));color:#F3EEE3;border:0}
.hero .sub{color:#AEB8C8}
.score{display:flex;align-items:flex-end;gap:14px;margin:14px 0 6px;flex-wrap:wrap}
.score b{font-size:56px;line-height:1;color:var(--gold2);font-weight:900}
.score span{color:#AEB8C8;font-size:14px;padding-bottom:6px}
.bars{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}
.bar{height:8px;border-radius:9px;background:rgba(255,255,255,.14);overflow:hidden;margin-top:6px}.bar i{display:block;height:100%;background:var(--gold2)}
.lab{font-size:13px;color:#AEB8C8}.val{font-weight:800;font-size:20px}
.price{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;text-align:center}
.price div{background:var(--bg);border-radius:12px;padding:12px 6px}.price .k{font-size:12.5px;color:var(--muted)}.price .v{font-weight:800;font-size:17px;margin-top:2px}
.pos{color:var(--good)}.neg{color:var(--bad)}
p{margin:0 0 10px}
.flag{border-top:1px solid var(--line);padding:10px 0}.flag:first-of-type{border-top:0}
.pill{display:inline-block;font-size:12px;font-weight:700;border-radius:999px;padding:2px 9px;margin-right:6px}
.p-pen{background:#FBEDE0;color:var(--warn)}.p-warn{background:#EEF0F3;color:var(--muted)}
.flag .h{font-size:13.5px;color:var(--muted);margin-top:4px}
table{width:100%;border-collapse:collapse;font-size:14.5px}
td,th{padding:9px 4px;border-top:1px solid var(--line);text-align:left;vertical-align:top}th{font-weight:600;color:var(--muted);font-size:13px}
td.n{text-align:right;font-weight:700;white-space:nowrap}
.note{font-size:12.5px;color:var(--muted)}
.cta{display:block;text-align:center;background:var(--navy);color:#F3EEE3;text-decoration:none;font-weight:800;border-radius:14px;padding:15px;margin:16px 0}
.cta small{display:block;font-weight:500;color:#AEB8C8;margin-top:2px}
.peers a{display:flex;justify-content:space-between;gap:10px;text-decoration:none;padding:9px 0;border-top:1px solid var(--line)}.peers a:first-of-type{border-top:0}
.peers b{color:var(--gold)}
.mk{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 4px}.mk a{font-size:13.5px;text-decoration:none;border:1px solid var(--line);background:#fff;border-radius:999px;padding:5px 12px}
.list td a{text-decoration:none;font-weight:600}.list td.s{color:var(--muted);font-size:13px}
.share{display:flex;gap:8px;margin:14px 0 0}.share button{flex:1;font:inherit;font-size:14px;font-weight:700;border-radius:12px;padding:10px;cursor:pointer;border:1px solid rgba(228,199,141,.45);background:rgba(228,199,141,.12);color:#F3EEE3}
.faq details{border-top:1px solid var(--line);padding:11px 0}.faq details:first-of-type{border-top:0}
.faq summary{font-weight:700;cursor:pointer;list-style:none}.faq summary::-webkit-details-marker{display:none}.faq summary:after{content:"+";float:right;color:var(--muted)}.faq details[open] summary:after{content:"−"}
.faq details p{margin:8px 0 0;color:#3A4352}
.alert{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:12px;padding:12px 14px;border-radius:12px;background:#FBF5EA;border:1px solid #EFE1C6;text-decoration:none}
.alert b{color:var(--ink);font-size:14.5px}.alert span{white-space:nowrap;font-weight:800;color:var(--gold);font-size:14px}
.mlinks{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px;margin:10px 0}.mlinks a{display:block;text-decoration:none;background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 12px;font-weight:700;font-size:14px}.mlinks a small{display:block;font-weight:500;color:var(--muted);font-size:12px}
article.col h1{font-size:25px}article.col h3{font-size:17px;margin:22px 0 8px}article.col p{margin:0 0 14px}article.col figure{margin:14px 0}article.col img{max-width:100%;border-radius:12px}article.col figcaption{font-size:12.5px;color:var(--muted);margin-top:4px}article.col blockquote{margin:14px 0;padding:10px 14px;border-left:3px solid var(--gold);background:#FBF5EA;border-radius:0 10px 10px 0}
.src{font-size:12.5px;color:var(--muted);word-break:break-all}.src a{color:var(--muted)}
footer{max-width:760px;margin:0 auto;padding:0 16px 40px;font-size:12px;color:var(--muted)}
footer nav{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:8px}footer nav a{text-decoration:none;font-weight:600}
@media(max-width:520px){h1{font-size:22px}.score b{font-size:48px}.price .v{font-size:15px}}`;

const TRACK = (p) => `<script>(function(){try{if(navigator.webdriver||/^(localhost|127\\.)/.test(location.hostname))return;var k='vn-sid',s=localStorage.getItem(k);if(!s){s=(crypto.randomUUID?crypto.randomUUID():String(Math.random()).slice(2)+Date.now()).replace(/-/g,'').slice(0,32);localStorage.setItem(k,s)}var u=navigator.userAgent,q=new URLSearchParams(location.search),r='';try{r=document.referrer?new URL(document.referrer).hostname:''}catch(e){}if(r===location.hostname)r='';r=q.get('utm_source')||(/Instagram/.test(u)?'ig':'')||r;try{if(r&&!localStorage.getItem('vn-ref'))localStorage.setItem('vn-ref',r)}catch(e){}var d=(/Mobi|iPhone|Android/.test(u)?'모바일':'PC')+' · '+(/iPhone|iPad/.test(u)?'iOS':/Android/.test(u)?'Android':/Mac/.test(u)?'Mac':/Windows/.test(u)?'Windows':'기타');fetch('${URL0}/rest/v1/events',{method:'POST',headers:{apikey:'${KEY}',Authorization:'Bearer ${KEY}','Content-Type':'application/json',Prefer:'return=minimal'},body:JSON.stringify({kind:'visit',sid:s,path:${JSON.stringify(p)},ref:r.slice(0,300),device:d}),keepalive:true})}catch(e){}})();</script>`;

// 기업별 점수 카드 이미지(카톡·인스타 DM 미리보기용). Supabase 함수 og 가 /c/scores.json 을 읽어 그린다
const OG_FN = `${URL0}/functions/v1/og`;
const ogUrl = (slug, date) => `${OG_FN}?c=${encodeURIComponent(slug)}&d=${encodeURIComponent(date)}`;
const ldJson = (ld) => `<script type="application/ld+json">${JSON.stringify(ld).replace(/</g, '\\u003c')}</script>`;

function head({ title, desc, url, ld, img, type = 'article', src = 'c', rss = false }) {
  const image = img || `${SITE}/og.png`;
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(desc)}"><link rel="canonical" href="${url}"><meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="${type}"><meta property="og:locale" content="ko_KR"><meta property="og:site_name" content="밸류노트 ValueNote"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(desc)}"><meta property="og:url" content="${url}"><meta property="og:image" content="${esc(image)}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="${esc(image)}">
<link rel="icon" type="image/png" href="/favicon-64.png?v=4"><meta name="theme-color" content="#0E1A2B"><link rel="preload" href="/fonts/SUIT-Variable.woff2" as="font" type="font/woff2" crossorigin><link rel="stylesheet" href="/c/c.css">${rss ? `<link rel="alternate" type="application/rss+xml" title="밸류노트 칼럼" href="${SITE}/rss.xml">` : ''}
${ld ? ldJson(ld) : ''}</head><body>
<header class="top"><div class="in"><a class="brand" href="/">Value<i>Note</i></a><a class="go" href="/?utm_source=${esc(src)}">밸류노트 열기</a></div></header>`;
}
const FOOT_NAV = `<nav><a href="/c/">기업 점수 전체</a><a href="/c/kr">국내</a><a href="/c/us">미국</a><a href="/c/jp">일본</a><a href="/c/hk">홍콩</a><a href="/c/cn">중국 A</a><a href="/blog/">칼럼</a></nav>`;
const FOOT = (date, what = '공개 재무 자료(Yahoo Finance 연간 재무, 네이버 증권)로 매일 자동 계산한 결과입니다.') => `<footer>${FOOT_NAV}${what} 데이터 기준 ${esc(date)}. 투자 판단의 참고 자료이며 특정 종목의 매수·매도를 권하지 않습니다. © 밸류노트</footer>`;

// 공유 버튼: 휴대폰은 공유 시트, PC는 링크 복사. 공유 링크에는 유입 경로 표시를 붙인다
const SHARE_JS = `<script>document.querySelectorAll('[data-sh]').forEach(function(b){b.onclick=async function(){var u=b.dataset.u+(b.dataset.u.indexOf('?')<0?'?':'&')+'utm_source=share-'+b.dataset.sh,t=b.dataset.t;try{if(navigator.share){await navigator.share({title:document.title,text:t,url:u});return}}catch(e){if(e&&e.name==='AbortError')return}try{await navigator.clipboard.writeText(t+'\\n'+u);b.textContent='링크를 복사했어요'}catch(e){prompt('이 링크를 복사해 보내세요',u)}}})</script>`;

const josa = (w, a, b) => { const c = String(w).trim().slice(-1).charCodeAt(0); if (c < 0xAC00 || c > 0xD7A3) return w + a; return w + ((c - 0xAC00) % 28 ? a : b); };
const gapTxt = (mos) => (mos >= 0 ? `${n0(mos)}% 낮은` : `${n0(-mos)}% 높은`);

function faqItems(x, date) {
  const { r, sc } = x, cur = r.cur || 'KRW', f = r.fin || {};
  const out = [];
  if (isNum(sc.iv) && sc.iv > 0) {
    let a = `밸류노트가 과거 평균 이익·주주 이익과 자산 가치로 계산한 ${r.n} 적정 가격은 ${money(sc.iv, cur)}입니다.`;
    if (isNum(r.px)) a += isNum(sc.mos) && r.px / sc.iv < 2 ? ` ${date} 기준 현재가 ${money(r.px, cur)}는 적정 가격보다 ${gapTxt(sc.mos)} 수준입니다.` : ` ${date} 기준 현재가 ${money(r.px, cur)}는 적정 가격의 ${n0(r.px / sc.iv, 1)}배입니다.`;
    a += ' 공식에 따른 추정치이며 미래 주가를 보장하지 않습니다.';
    out.push([`${r.n} 적정 주가는 얼마인가요?`, a]);
  }
  if (isNum(sc.v)) {
    const ok = isNum(sc.mos) && sc.mos >= 30;
    out.push([`${r.n} 지금 저평가인가요?`, `저평가 점수는 100점 만점에 ${sc.v}점입니다. ` + (ok
      ? `현재가가 적정 가격보다 30% 이상 낮아, 그레이엄이 말한 안전마진 30% 기준을 충족합니다. 다만 싼 데에는 이유가 있을 수 있으니 품질 점수(${sc.q ?? '–'}점)와 감점 신호를 함께 보세요.`
      : `밸류노트는 적정 가격보다 30% 이상 낮을 때를 안전마진 기준으로 봅니다. 지금은 그 기준에 들어오지 않았습니다.`)]);
  }
  const bits = [];
  if (isNum(sc.per)) bits.push(`PER ${n0(sc.per, 1)}배`);
  if (isNum(sc.pbr)) bits.push(`PBR ${n0(sc.pbr, 2)}배`);
  if (isNum(f.roeAvg)) bits.push(`5년 평균 ROE ${n0(f.roeAvg, 1)}%`);
  if (bits.length) out.push([`${r.n} PER·PBR·ROE는?`, `${date} 기준 ${bits.join(', ')}입니다. PER은 낮을수록 이익 대비 싸고, ROE는 꾸준히 높을수록 자본을 잘 굴리는 회사입니다. 한 해 숫자보다 여러 해 평균을 보는 것이 안전합니다.`]);
  out.push(['밸류노트 점수는 어떻게 계산하나요?', '그레이엄·버핏·멍거의 기준을 숫자로 옮겼습니다. ROE·이익률·현금흐름 등 13개 지표로 본 숫자 품질 40%, 적정 가격 대비 할인율로 본 저평가 60%를 합치고, 잦은 적자·과도한 빚·잦은 증자 같은 위험 신호는 감점합니다. 버크셔 해서웨이의 실제 매수 62건으로 검증한 공식입니다.']);
  return out;
}

function companyPage(x, peers, date) {
  const { r, sc } = x, g = grpOf(r.m), cur = r.cur || 'KRW', f = r.fin || {};
  const url = `${SITE}/c/${x.slug}`;
  const code = r.code || r.t;
  const pens = (sc.flags || []).filter((fl) => !WARN_FLAGS.has(fl)), warns = (sc.flags || []).filter((fl) => WARN_FLAGS.has(fl));
  const b = sc.b;
  const hasIv = isNum(sc.iv) && sc.iv > 0;
  // 검색어 '○○ 적정주가'에 맞춘 제목
  const title = `${r.n} 적정주가 ${hasIv ? money(sc.iv, cur) + ' · ' : ''}가치투자 점수 ${isNum(b) ? b + '점' : ''} | 밸류노트`;
  const desc = `${r.n}(${code}) 적정주가와 밸류노트 점수 ${isNum(b) ? b + '점' : '계산 불가'}(숫자 품질 ${sc.q ?? '–'}점, 저평가 ${sc.v ?? '–'}점).` +
    (hasIv && isNum(r.px) ? ` 현재가 ${money(r.px, cur)}, 적정 가격 ${money(sc.iv, cur)}.` : '') +
    (isNum(sc.per) ? ` PER ${n0(sc.per, 1)}배` : '') + (isNum(f.roeAvg) ? `, 5년 평균 ROE ${n0(f.roeAvg, 1)}%.` : '.') + ` 그레이엄·버핏 기준으로 매일 계산합니다.`;
  const sum = summary(r, sc);
  const faq = faqItems(x, date);
  const rowsM = [
    ['5년 평균 ROE', isNum(f.roeAvg) ? n0(f.roeAvg, 1) + '%' : '–', '자기자본으로 1년에 몇 %를 버는지'],
    ['5년 중 최저 ROE', isNum(f.roeMin) ? n0(f.roeMin, 1) + '%' : '–', '나쁜 해에도 버티는지'],
    ['ROIC', isNum(f.roic) ? n0(f.roic, 1) + '%' : '–', '빚까지 포함한 투자 자본 수익률'],
    ['매출총이익률', isNum(f.gpm) ? n0(f.gpm, 1) + '%' : '–', '가격 결정력의 흔적'],
    ['순이익률', isNum(f.npm) ? n0(f.npm, 1) + '%' : '–', ''],
    ['EPS 연평균 성장', isNum(f.epsCagr) ? n0(f.epsCagr, 1) + '%' : '–', '주당순이익 성장'],
    ['현금 전환율', isNum(f.fcfConv) ? n0(f.fcfConv) + '%' : '–', '이익 중 실제 현금으로 들어온 비율'],
    ['장기부채 ÷ 순이익', isNum(f.ltdNi) ? n0(f.ltdNi, 1) + '배' : '–', '이익으로 빚을 갚는 데 걸리는 해'],
    ['적자 연도', isNum(f.lossYears) ? f.lossYears + '년' : '–', `최근 ${r.yrs || 5}년 중`],
    ['주식 수 변화', isNum(f.shareChg) ? (f.shareChg > 0 ? '+' : '') + n0(f.shareChg, 1) + '%' : '–', '늘면 주주 몫이 희석'],
    ['PER', isNum(sc.per) ? n0(sc.per, 1) + '배' : '–', '그레이엄 기준 15배 이하'],
    ['PBR', isNum(sc.pbr) ? n0(sc.pbr, 2) + '배' : '–', ''],
  ].filter((m) => m[1] !== '–' && !(r.fin_sector && ['매출총이익률', '순이익률', '현금 전환율', '장기부채 ÷ 순이익', 'ROIC'].includes(m[0])));
  const mUrl = `${SITE}/c/${MSLUG[g]}`;
  const ld = { '@context': 'https://schema.org', '@graph': [
    { '@type': 'BreadcrumbList', itemListElement: [
      { '@type': 'ListItem', position: 1, name: '밸류노트', item: SITE + '/' },
      { '@type': 'ListItem', position: 2, name: `${MKT[g]} 기업 점수`, item: mUrl },
      { '@type': 'ListItem', position: 3, name: r.n, item: url }] },
    { '@type': 'FAQPage', mainEntity: faq.map(([q, a]) => ({ '@type': 'Question', name: q, acceptedAnswer: { '@type': 'Answer', text: a } })) },
    { '@type': 'WebPage', name: title, url, dateModified: date, inLanguage: 'ko-KR', about: { '@type': 'Corporation', name: r.n, ...(r.en ? { alternateName: r.en } : {}), tickerSymbol: String(r.t || code) } },
  ] };
  const appLink = `/?co=${encodeURIComponent(code)}&q=${encodeURIComponent(r.n)}&utm_source=c`;
  const alertLink = `/?co=${encodeURIComponent(code)}&q=${encodeURIComponent(r.n)}&utm_source=c-alert`;
  const shareText = `${r.n} 밸류노트 점수 ${isNum(b) ? b + '점' : '–'}` + (hasIv && isNum(sc.mos) && isNum(r.px) && r.px / sc.iv < 2 ? ` · 적정가보다 ${gapTxt(sc.mos)} 가격` : '') + '. 그레이엄·버핏 기준으로 본 숫자';
  return head({ title, desc, url, ld, img: ogUrl(x.slug, date) }) + `<main>
<div class="crumb"><a href="/c/">기업 점수</a> › <a href="/c/${MSLUG[g]}">${MKT[g]}</a> › ${esc(r.n)}</div>
<section class="card hero"><h1>${esc(r.n)} 적정주가와 가치투자 점수</h1><div class="sub">${esc(code)} · ${MKT[g]}${r.en ? ' · ' + esc(r.en) : ''}${r.ind ? ' · ' + esc(r.ind) : ''}</div>
<div class="score"><b>${isNum(b) ? b : '–'}</b><span>밸류노트 점수 (100점 만점, 70점 이상이 기준)</span></div>
<div class="bars"><div><div class="lab">숫자 품질</div><div class="val">${sc.q ?? '–'}점</div><div class="bar"><i style="width:${sc.q || 0}%"></i></div></div>
<div><div class="lab">저평가</div><div class="val">${sc.v ?? '–'}점</div><div class="bar"><i style="width:${sc.v || 0}%"></i></div></div></div>
<div class="share"><button type="button" data-sh="c" data-u="${url}" data-t="${esc(shareText)}">이 점수 공유하기</button></div></section>
${isNum(r.px) ? `<section class="card"><h2>가격</h2><div class="price"><div><div class="k">현재가</div><div class="v">${money(r.px, cur)}</div></div><div><div class="k">적정 가격</div><div class="v">${money(sc.iv, cur)}</div></div><div><div class="k">안전마진</div><div class="v ${isNum(sc.mos) ? (sc.mos >= 0 ? 'pos' : 'neg') : ''}">${isNum(sc.mos) ? (sc.mos > 0 ? '+' : '') + n0(sc.mos) + '%' : '–'}</div></div></div>
<p class="note" style="margin-top:10px">적정 가격은 과거 평균 이익·주주 이익과 자산 가치로 계산한 값입니다. ${r.fin_sector ? '금융업은 현금흐름 할인 대신 자산·이익 기준을 씁니다. ' : ''}미래를 보장하지 않습니다.</p>
${hasIv ? `<a class="alert" href="${alertLink}"><b>${esc(josa(r.n, '이', '가'))} 적정 매수가에 오면 알려 드릴까요?</b><span>알림 받기 ›</span></a>` : ''}</section>` : ''}
${sum.length ? `<section class="card"><h2>한 줄씩 읽기</h2>${sum.map((s) => `<p>${esc(s)}</p>`).join('')}</section>` : ''}
${pens.length || warns.length ? `<section class="card"><h2>감점·경고 신호</h2>${pens.map((fl) => `<div class="flag"><span class="pill p-pen">감점 −8</span><b>${esc(fl)}</b>${FLAG_HELP[fl] ? `<div class="h">${esc(FLAG_HELP[fl])}</div>` : ''}</div>`).join('')}${warns.map((fl) => `<div class="flag"><span class="pill ${fl === '중국 본토 규제' ? 'p-pen' : 'p-warn'}">${fl === '중국 본토 규제' ? '할인 −6' : '경고'}</span><b>${esc(fl)}</b>${FLAG_HELP[fl] ? `<div class="h">${esc(FLAG_HELP[fl])}</div>` : ''}</div>`).join('')}</section>` : ''}
${rowsM.length ? `<section class="card"><h2>핵심 숫자</h2><table>${rowsM.map((m) => `<tr><td>${m[0]}${m[2] ? `<div class="note">${m[2]}</div>` : ''}</td><td class="n">${m[1]}</td></tr>`).join('')}</table></section>` : ''}
<a class="cta" href="${appLink}">밸류노트에서 ${esc(r.n)} 자세히 보기<small>적정 가격 알림 · 내 포트폴리오 점수 · 멍거의 질문 체크</small></a>
<section class="card faq"><h2>자주 묻는 질문</h2>${faq.map(([q, a], i) => `<details${i === 0 ? ' open' : ''}><summary>${esc(q)}</summary><p>${esc(a)}</p></details>`).join('')}</section>
${peers.length ? `<section class="card peers"><h2>같은 업종의 다른 회사</h2>${peers.map((p) => `<a href="/c/${p.slug}"><span>${esc(p.r.n)} <span class="note">${MKT[grpOf(p.r.m)]}</span></span><b>${p.sc.b ?? '–'}점</b></a>`).join('')}</section>` : ''}
</main>${FOOT(date)}${SHARE_JS}${TRACK('/c/' + x.slug)}</body></html>`;
}

// 시장 순위 표 (기업 점수 전체·시장별 페이지 공통)
const rankTable = (list) => `<table><tr><th>#</th><th>회사</th><th style="text-align:right">점수</th></tr>${list.map((x, i) => `<tr><td class="s">${i + 1}</td><td><a href="/c/${x.slug}">${esc(x.r.n)}</a><div class="s">${esc(x.r.ind || x.r.s || '')}</div></td><td class="n">${x.sc.b ?? '–'}</td></tr>`).join('')}</table>`;
const MSLUG = { KR: 'kr', US: 'us', JP: 'jp', HK: 'hk', CN: 'cn' };
const MKT_LONG = { KR: '국내 주식(코스피·코스닥)', US: '미국 주식', JP: '일본 주식', HK: '홍콩 주식', CN: '중국 A주' };
// 품질이 기준 이상이고 적정 가격보다 30% 이상 싼 회사 (사실 기준 필터. 추천 아님)
const isBargain = (x) => isNum(x.sc.mos) && x.sc.mos >= 30 && isNum(x.sc.q) && x.sc.q >= 60 && !(x.sc.flags || []).some((fl) => !WARN_FLAGS.has(fl));

function indexPage(all, date) {
  const url = `${SITE}/c/`;
  const by = Object.fromEntries(MKT_ORDER.map((m) => [m, all.filter((x) => grpOf(x.r.m) === m).sort((a, b) => (b.sc.b ?? -1) - (a.sc.b ?? -1))]));
  const title = `기업 점수 ${all.length}곳 · 그레이엄·버핏 기준 가치투자 순위 | 밸류노트`;
  const desc = `국내·미국·일본·홍콩·중국 ${all.length}개 기업의 적정주가와 가치투자 점수를 같은 기준(숫자 품질·저평가·감점 신호)으로 매일 계산합니다. 저평가 우량주를 시장별로 확인하세요.`;
  const ld = { '@context': 'https://schema.org', '@type': 'CollectionPage', name: title, url, dateModified: date, inLanguage: 'ko-KR' };
  return head({ title, desc, url, ld, type: 'website' }) + `<main>
<h1>기업 점수 ${all.length}곳</h1><p class="sub">그레이엄·버핏·멍거의 기준을 숫자로 옮겨, 5개 시장의 기업을 같은 잣대로 매일 다시 계산합니다. 70점 이상이 기준입니다.</p>
<div class="mlinks">${MKT_ORDER.map((m) => `<a href="/c/${MSLUG[m]}">${MKT[m]} 순위<small>${by[m].length}곳 · 저평가 기준 통과 ${by[m].filter(isBargain).length}곳</small></a>`).join('')}<a href="/blog/">칼럼<small>매주 시장·거장의 투자</small></a></div>
${MKT_ORDER.map((m) => `<section class="card list" id="${m}"><h2><a href="/c/${MSLUG[m]}" style="text-decoration:none">${MKT[m]} ›</a></h2>${rankTable(by[m])}</section>`).join('')}
<a class="cta" href="/?utm_source=c-index">내 종목 점수 확인하기<small>포트폴리오를 넣으면 같은 기준으로 채점합니다</small></a>
</main>${FOOT(date)}${TRACK('/c/')}</body></html>`;
}

function marketPage(m, list, date) {
  const url = `${SITE}/c/${MSLUG[m]}`;
  const sorted = [...list].sort((a, b) => (b.sc.b ?? -1) - (a.sc.b ?? -1));
  const bar = sorted.filter(isBargain).sort((a, b) => b.sc.mos - a.sc.mos);
  const top = sorted.filter((x) => isNum(x.sc.b));
  const title = `${MKT_LONG[m]} 저평가 우량주 순위 ${list.length}곳 · 적정주가 | 밸류노트`;
  const desc = `${MKT_LONG[m]} ${list.length}곳의 적정주가와 가치투자 점수를 매일 계산한 순위입니다. 품질 60점 이상이면서 적정 가격보다 30% 이상 싼 회사는 ${bar.length}곳입니다(${date} 기준).`;
  const ld = { '@context': 'https://schema.org', '@graph': [
    { '@type': 'BreadcrumbList', itemListElement: [
      { '@type': 'ListItem', position: 1, name: '밸류노트', item: SITE + '/' },
      { '@type': 'ListItem', position: 2, name: '기업 점수', item: SITE + '/c/' },
      { '@type': 'ListItem', position: 3, name: `${MKT[m]} 순위`, item: url }] },
    { '@type': 'ItemList', name: title, numberOfItems: Math.min(20, top.length), itemListElement: top.slice(0, 20).map((x, i) => ({ '@type': 'ListItem', position: i + 1, url: `${SITE}/c/${x.slug}`, name: x.r.n })) },
  ] };
  const shareText = `${MKT_LONG[m]} 가치투자 점수 순위. 적정 가격보다 30% 이상 싼 우량주 ${bar.length}곳`;
  return head({ title, desc, url, ld, type: 'website' }) + `<main>
<div class="crumb"><a href="/c/">기업 점수</a> › ${MKT[m]}</div>
<section class="card hero"><h1>${MKT_LONG[m]} 저평가 우량주 순위</h1><p class="sub" style="margin-top:6px">${list.length}곳을 그레이엄·버핏 기준으로 매일 다시 계산합니다. 점수 70점 이상이 기준이고, 적정 가격보다 30% 이상 낮으면 안전마진이 있다고 봅니다.</p>
<div class="share"><button type="button" data-sh="m" data-u="${url}" data-t="${esc(shareText)}">이 순위 공유하기</button></div></section>
<section class="card list"><h2>안전마진 30% 이상 · 품질 60점 이상 (${bar.length}곳)</h2>${bar.length ? `<table><tr><th>회사</th><th style="text-align:right">적정가 대비</th></tr>${bar.map((x, i) => i < 3 && bar.length > 5
    // 앱 첫 화면과 같이 할인율 1~3위는 가입하면 보이게 둔다(가입 동기)
    ? `<tr><td><a href="/?signup&utm_source=c-${MSLUG[m]}-gate" style="color:var(--gold)">${i + 1}위 · 가입하고 보기 ›</a><div class="s">품질 ${x.sc.q}점 · 종합 ${x.sc.b ?? '–'}점</div></td><td class="n pos">${n0(x.sc.mos)}% 낮음</td></tr>`
    : `<tr><td><a href="/c/${x.slug}">${esc(x.r.n)}</a><div class="s">품질 ${x.sc.q}점 · 종합 ${x.sc.b ?? '–'}점</div></td><td class="n pos">${n0(x.sc.mos)}% 낮음</td></tr>`).join('')}</table>` : '<p class="note">오늘은 이 기준을 통과한 회사가 없습니다. 좋은 회사의 가격이 내려올 때까지 기다리는 날입니다.</p>'}
<p class="note" style="margin-top:8px">감점 신호(잦은 적자·과도한 빚·잦은 증자 등)가 있는 회사는 뺐습니다. 숫자로 거른 목록일 뿐, 매수 권유가 아닙니다.</p></section>
<section class="card list"><h2>밸류노트 점수 순위</h2>${rankTable(sorted)}</section>
<a class="cta" href="/?utm_source=c-${MSLUG[m]}">관심 종목이 적정 가격에 오면 알림 받기<small>가입은 이메일만으로 10초</small></a>
<div class="mlinks">${MKT_ORDER.filter((k) => k !== m).map((k) => `<a href="/c/${MSLUG[k]}">${MKT[k]} 순위</a>`).join('')}</div>
</main>${FOOT(date)}${SHARE_JS}${TRACK('/c/' + MSLUG[m])}</body></html>`;
}

/* ============ 칼럼: 앱과 같은 글을 검색에 잡히는 정적 페이지로 ============ */
const colInline = (t) => esc(t).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
function colBodyHtml(t) {
  return String(t || '').split(/\n{2,}/).map((p) => p.trim()).filter(Boolean).map((p) => {
    const img = p.match(/^!\[([^\]]*)\]\(([^)\s]+)\)$/);
    if (img) return `<figure><img src="${esc(img[2])}" alt="${esc(img[1])}" loading="lazy">${img[1] ? `<figcaption>${esc(img[1])}</figcaption>` : ''}</figure>`;
    if (/^>\s*/.test(p)) return `<blockquote>${p.split('\n').map((l) => colInline(l.replace(/^>\s*/, ''))).join('<br>')}</blockquote>`;
    if (/^■\s*/.test(p)) { const [h, ...rest] = p.replace(/^■\s*/, '').split('\n'); return `<h3>${colInline(h)}</h3>${rest.length ? `<p>${rest.map(colInline).join('<br>')}</p>` : ''}`; }
    return `<p>${p.split('\n').map(colInline).join('<br>')}</p>`;
  }).join('\n');
}
const COL_SERIES = { weekly: '주간 시장', giants: '거장의 투자' };
const colDateK = (c) => { const d = new Date(c.at || c.id.slice(4, 14)); return isNaN(d) ? '' : `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일`; };
const plain = (t) => String(t || '').replace(/!\[[^\]]*\]\([^)]*\)/g, '').replace(/\*\*/g, '').replace(/^[■>]\s*/gm, '').replace(/\s+/g, ' ').trim();
const colImage = (c) => c.cover || (String(c.body || '').match(/!\[[^\]]*\]\((https?:[^)\s]+)\)/) || [])[1] || `${SITE}/og.png`;

function colPage(c, cols) {
  const url = `${SITE}/blog/${c.id}`;
  const ser = COL_SERIES[c.series || 'weekly'];
  const desc = (c.sub ? c.sub + ' · ' : '') + plain(c.body).slice(0, 120) + '…';
  const iso = c.at || c.id.slice(4, 14);
  const ld = { '@context': 'https://schema.org', '@type': 'Article', headline: c.title, description: desc, datePublished: iso, dateModified: iso, image: [colImage(c)], inLanguage: 'ko-KR', mainEntityOfPage: url,
    author: { '@type': 'Organization', name: '밸류노트', url: SITE }, publisher: { '@type': 'Organization', name: '밸류노트', logo: { '@type': 'ImageObject', url: `${SITE}/icon-512.png` } } };
  const others = cols.filter((o) => o.id !== c.id).slice(0, 5);
  return head({ title: `${c.title} | 밸류노트 칼럼`, desc, url, ld, img: colImage(c), src: 'blog', rss: true }) + `<main><article class="card col">
<div class="crumb"><a href="/blog/">칼럼</a> › ${esc(ser)}</div>
<h1>${esc(c.title)}</h1>${c.sub ? `<p class="sub">${esc(c.sub)}</p>` : ''}<p class="note">${esc(colDateK(c))} · 밸류노트</p>
${colBodyHtml(c.body)}
${(c.sources || []).length ? `<div class="src"><b>참고한 자료</b><br>${c.sources.map((s) => `<a href="${esc(s)}" rel="nofollow noopener" target="_blank">${esc(s.replace(/^https?:\/\//, '').slice(0, 70))}</a>`).join('<br>')}</div>` : ''}
<div class="share" style="margin-top:16px"><button type="button" data-sh="blog" data-u="${url}" data-t="${esc(c.title)}" style="color:var(--ink);border-color:var(--line);background:var(--bg)">이 글 공유하기</button></div>
</article>
<a class="cta" href="/?utm_source=blog">매주 월요일, 칼럼을 메일로 받기<small>밸류노트에 가입하고 구독을 켜세요 · 600+ 기업 점수도 함께</small></a>
${others.length ? `<section class="card peers"><h2>다른 칼럼</h2>${others.map((o) => `<a href="/blog/${o.id}"><span>${esc(o.title)}</span><span class="note">${esc(colDateK(o))}</span></a>`).join('')}</section>` : ''}
</main>${FOOT(iso.slice(0, 10), '투자 교육용 칼럼입니다.')}${SHARE_JS}${TRACK('/blog/' + c.id)}</body></html>`;
}
function blogIndex(cols, date) {
  const url = `${SITE}/blog/`;
  const title = '밸류노트 칼럼 · 주간 시장과 거장의 투자';
  const desc = '매주 시장·금리·환율 흐름과 버핏·그레이엄·멍거의 투자를 숫자로 정리하는 밸류노트 칼럼입니다.';
  return head({ title, desc, url, type: 'website', src: 'blog', rss: true, ld: { '@context': 'https://schema.org', '@type': 'Blog', name: title, url, inLanguage: 'ko-KR' } }) + `<main>
<h1>칼럼</h1><p class="sub">${esc(desc)}</p>
<section class="card peers">${cols.map((c) => `<a href="/blog/${c.id}"><span><b style="color:var(--ink)">${esc(c.title)}</b><span class="note" style="display:block">${esc(COL_SERIES[c.series || 'weekly'])} · ${esc(colDateK(c))}</span></span></a>`).join('')}</section>
<a class="cta" href="/?utm_source=blog-index">밸류노트 열기<small>600+ 기업 점수 · 적정 매수가 알림</small></a>
</main>${FOOT(date, '투자 교육용 칼럼입니다.')}${TRACK('/blog/')}</body></html>`;
}
const xmlEsc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' }[c]));
function rss(cols) {
  const items = cols.map((c) => { const u = `${SITE}/blog/${c.id}`; const d = new Date(c.at || c.id.slice(4, 14));
    return `<item><title>${xmlEsc(c.title)}</title><link>${u}</link><guid isPermaLink="true">${u}</guid><pubDate>${(isNaN(d) ? new Date() : d).toUTCString()}</pubDate><description>${xmlEsc((c.sub ? c.sub + ' · ' : '') + plain(c.body).slice(0, 300))}</description></item>`; }).join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>밸류노트 칼럼</title><link>${SITE}/blog/</link><description>가치투자 칼럼 · 주간 시장과 거장의 투자</description><language>ko</language>\n${items}\n</channel></rss>\n`;
}
async function loadColumns() {
  try {
    const r = await fetch(`${URL0}/rest/v1/docs?collection=eq.trends&id=like.col-*&select=id,data`, { headers: { apikey: KEY, Authorization: 'Bearer ' + KEY } });
    if (!r.ok) return [];
    return (await r.json()).map((d) => ({ id: d.id, ...(d.data || {}) })).filter((c) => c.title && c.body && /^col-[0-9a-z-]+$/.test(c.id)).sort((a, b) => b.id.localeCompare(a.id));
  } catch (_) { return []; }
}

const { meta, rows } = await load();
if (rows.length < 300) throw new Error('rows too few: ' + rows.length);
setSettings({});
const seen = new Set();
const all = rows.map((r) => ({ r, sc: scoreRow(r, null, 30), slug: slug(r) })).filter((x) => x.slug && !seen.has(x.slug) && seen.add(x.slug));
// 시장 순위 페이지 주소(/c/kr 등)와 겹치는 기업 주소가 생기면 멈춘다
for (const s of Object.values(MSLUG)) if (seen.has(s)) throw new Error('slug clash: ' + s);
const date = meta.generatedAt || new Date().toISOString().slice(0, 10);
const dir = path.join(ROOT, 'c');
// 어제 점수(색인 요청 대상 고르기용)
let prev = {};
try { prev = JSON.parse(fs.readFileSync(process.env.PREV_SCORES || path.join(dir, 'scores.json'), 'utf8')).c || {}; } catch (_) {}
fs.rmSync(dir, { recursive: true, force: true });
fs.mkdirSync(dir, { recursive: true });
fs.writeFileSync(path.join(dir, 'c.css'), CSS);
for (const x of all) {
  const key = x.r.ind || x.r.s;
  const peers = all.filter((y) => y !== x && (y.r.ind || y.r.s) === key && isNum(y.sc.b)).sort((a, b) => b.sc.b - a.sc.b).slice(0, 6);
  fs.writeFileSync(path.join(dir, x.slug + '.html'), companyPage(x, peers, date));
}
fs.writeFileSync(path.join(dir, 'index.html'), indexPage(all, date));
for (const m of MKT_ORDER) fs.writeFileSync(path.join(dir, MSLUG[m] + '.html'), marketPage(m, all.filter((x) => grpOf(x.r.m) === m), date));
// OG 이미지 함수가 읽는 점수표: slug → [이름, 종합, 품질, 저평가, 시장, 안전마진%, 업종]
const R0 = (v) => (isNum(v) ? Math.round(v) : null);
const scores = Object.fromEntries(all.map((x) => [x.slug, [x.r.n, R0(x.sc.b), R0(x.sc.q), R0(x.sc.v), grpOf(x.r.m),
  isNum(x.sc.iv) && x.sc.iv > 0 && isNum(x.r.px) && x.r.px / x.sc.iv < 2 ? R0(x.sc.mos) : null, x.r.ind || x.r.s || '']]));
fs.writeFileSync(path.join(dir, 'scores.json'), JSON.stringify({ date, c: scores }));

// 칼럼 정적 페이지·RSS (blog/ 아래 이미지 폴더는 건드리지 않는다)
const cols = await loadColumns();
const bdir = path.join(ROOT, 'blog');
fs.mkdirSync(bdir, { recursive: true });
for (const f of fs.readdirSync(bdir)) if (f.endsWith('.html')) fs.rmSync(path.join(bdir, f));
for (const c of cols) fs.writeFileSync(path.join(bdir, c.id + '.html'), colPage(c, cols));
fs.writeFileSync(path.join(bdir, 'index.html'), blogIndex(cols, date));
fs.writeFileSync(path.join(ROOT, 'rss.xml'), rss(cols));

const sm = [[`${SITE}/`, date, '1.0'], [`${SITE}/c/`, date, '0.9'], ...MKT_ORDER.map((m) => [`${SITE}/c/${MSLUG[m]}`, date, '0.9']),
  [`${SITE}/blog/`, (cols[0]?.at || date).slice(0, 10), '0.8'], ...cols.map((c) => [`${SITE}/blog/${c.id}`, (c.at || c.id.slice(4, 14)).slice(0, 10), '0.7']),
  ...all.map((x) => [`${SITE}/c/${x.slug}`, date, '0.6'])];
fs.writeFileSync(path.join(ROOT, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${sm.map(([u, d, p]) => `<url><loc>${u}</loc><lastmod>${d}</lastmod><priority>${p}</priority></url>`).join('\n')}\n</urlset>\n`);
fs.writeFileSync(path.join(ROOT, 'robots.txt'), `User-agent: *\nAllow: /\nDisallow: /admin\n\nSitemap: ${SITE}/sitemap.xml\n`);
console.log(`pages ${all.length} · markets ${MKT_ORDER.length} · columns ${cols.length} · date ${date}`);

// 네이버·빙 등 검색엔진에 바뀐 주소만 바로 알린다(IndexNow). GitHub Actions 에서만 INDEXNOW=1 로 켠다
if (process.env.INDEXNOW === '1') {
  const changed = all.filter((x) => { const o = prev[x.slug]; const n = scores[x.slug]; return !o || o[1] !== n[1] || o[0] !== n[0]; }).map((x) => `${SITE}/c/${x.slug}`);
  const list = [...new Set([`${SITE}/`, `${SITE}/c/`, ...MKT_ORDER.map((m) => `${SITE}/c/${MSLUG[m]}`), `${SITE}/blog/`, ...cols.slice(0, 3).map((c) => `${SITE}/blog/${c.id}`), ...changed])].slice(0, 9000);
  const body = JSON.stringify({ host: 'www.valuenote.co.kr', key: INDEXNOW_KEY, keyLocation: `${SITE}/${INDEXNOW_KEY}.txt`, urlList: list });
  for (const ep of ['https://searchadvisor.naver.com/indexnow', 'https://api.indexnow.org/indexnow']) {
    try { const r = await fetch(ep, { method: 'POST', headers: { 'Content-Type': 'application/json; charset=utf-8' }, body }); console.log(`::notice::IndexNow ${ep} → ${r.status} (${list.length}개 주소)`); }
    catch (e) { console.log(`::warning::IndexNow ${ep} 실패: ${e.message}`); }
  }
}
