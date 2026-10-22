// 기업별 공개 페이지 생성기: 스크리너 데이터(공개 읽기)를 받아 화면과 같은 점수 코드로 계산하고
// /c/<코드>.html 600여 개 + /c/index.html + sitemap.xml + robots.txt 를 만든다.
// 실행: node scripts/build_pages.mjs   (GitHub Actions pages.yml 이 매일 돌린다)
import fs from 'node:fs';
import path from 'node:path';
import { scoreRow, grpOf, WARN_FLAGS, setSettings } from '../supabase/functions/watch-select/scoring.js';
import { makeVN } from './vnscore.mjs';

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
  await loadVN();
  return { meta, rows };
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

function summary(r, sc) {
  const out = [];
  const f = r.fin || {};
  if (isNum(sc.q)) {
    const bits = [];
    if (isNum(f.roeAvg)) bits.push(`5년 평균 ROE ${n0(f.roeAvg, 1)}%`);
    if (isNum(f.fcfConv)) bits.push(`이익의 ${n0(f.fcfConv)}%가 현금으로 들어옴`);
    if (isNum(f.ltdNi)) bits.push(`장기부채는 순이익의 ${n0(f.ltdNi, 1)}배`);
    out.push(`재무 점수는 ${sc.q}점입니다${bits.length ? ' (' + bits.join(', ') + ')' : ''}.`);
  }
  if (isNum(sc.v)) {
    let s = `가격 점수는 ${sc.v}점입니다.`;
    if (isNum(sc.iv) && sc.iv > 0 && isNum(r.px) && r.px / sc.iv >= 2) s += ` 현재가가 계산한 적정 주가의 ${n0(r.px / sc.iv, 1)}배입니다.`;
    else if (isNum(sc.mos) && isNum(sc.iv)) s += sc.mos >= 0
      ? ` 현재가가 계산한 적정 주가보다 ${n0(sc.mos)}% 낮습니다.`
      : ` 현재가가 계산한 적정 주가보다 ${n0(-sc.mos)}% 높습니다.`;
    out.push(s);
  }
  if (isNum(sc.q) && isNum(sc.v)) {
    if (sc.q >= 80 && sc.v < 30) out.push('회사는 좋지만 지금 가격은 비싼 편이라, 적정 주가 근처로 내려올 때를 기다리는 유형입니다.');
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
.note.cyc{margin-top:8px;padding:10px 12px;border-radius:10px;background:#F4F1EA;color:var(--ink)}.note.cyc b{display:block;font-size:13px;margin-bottom:2px}
.wbar{position:fixed;left:0;right:0;bottom:0;z-index:30;padding:10px 14px calc(10px + env(safe-area-inset-bottom));background:#0E1A2B;box-shadow:0 -8px 24px rgba(14,26,43,.18);transform:translateY(110%);transition:transform .3s ease}
.wbar.on{transform:none}
.wbar .in{max-width:720px;margin:0 auto;display:flex;align-items:center;gap:10px}
.wbar .t{flex:1;min-width:0;line-height:1.35}
.wbar .t b{display:block;color:#fff;font-size:18px;font-weight:900;letter-spacing:-.01em;white-space:nowrap}
.wbar .t span{display:block;color:#AEB8C8;font-size:12px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.wbar .t span:last-child{color:var(--gold2)}
.wbar a.k{display:inline-flex;align-items:center;gap:6px;height:44px;padding:0 15px;border-radius:12px;background:#FEE500;color:#191600;font-weight:800;font-size:14.5px;text-decoration:none;white-space:nowrap}
.wbar a.e{display:block;color:#AEB8C8;font-size:11.5px;text-decoration:none;margin-top:2px}
body.has-wbar footer{padding-bottom:90px}
.mlinks{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px;margin:10px 0}.mlinks a{display:block;text-decoration:none;background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 12px;font-weight:700;font-size:14px}.mlinks a small{display:block;font-weight:500;color:var(--muted);font-size:12px}
article.col h1{font-size:25px}article.col h3{font-size:17px;margin:22px 0 8px}article.col p{margin:0 0 14px}article.col figure{margin:14px 0}article.col img{max-width:100%;border-radius:12px}article.col figcaption{font-size:12.5px;color:var(--muted);margin-top:4px}article.col blockquote{margin:14px 0;padding:10px 14px;border-left:3px solid var(--gold);background:#FBF5EA;border-radius:0 10px 10px 0}
.src{font-size:12.5px;color:var(--muted);word-break:break-all}.src a{color:var(--muted)}
/* 기업 페이지 랜딩형 */
main.lp .crumb .note{font-size:12px}
.hero2{background:radial-gradient(120% 80% at 100% 0,rgba(201,154,80,.22),transparent 55%),linear-gradient(165deg,#1A2D47,var(--navy));color:#F3EEE3;border-radius:20px;padding:22px 18px 18px;margin:8px 0 12px}
.hero2 .eyebrow{display:inline-block;font-size:12px;font-weight:700;color:var(--gold2);border:1px solid rgba(228,199,141,.4);border-radius:999px;padding:3px 10px;margin-bottom:12px}
.hero2 h1{font-size:27px;line-height:1.32;color:#fff;margin:0 0 10px;letter-spacing:-.5px}.hero2 h1 em{font-style:normal;color:var(--gold2)}
.verdict{font-size:16px;color:#D5DCE7;margin:0 0 6px}.verdict b{font-weight:900}.hot{color:#FF9B8A}.cool{color:#7FD8AE}
.ruler{margin:20px 2px 6px}.ruler .up,.ruler .dn{position:relative;height:38px}
.ruler .m{position:absolute;bottom:0;white-space:nowrap;font-weight:800;font-size:15px;color:#fff;line-height:1.25}.ruler .dn .m{top:0;bottom:auto}
.ruler .m small{display:block;font-size:11.5px;font-weight:700;color:#AEB8C8}.ruler .m.l{transform:translateX(-6px)}.ruler .m.r{transform:translateX(calc(-100% + 6px));text-align:right}
.ruler .dn .m{color:var(--gold2)}.ruler .dn .m.sm{color:#D5DCE7;font-size:13px}
.track{position:relative;height:10px;border-radius:9px;background:rgba(255,255,255,.12);margin:6px 0}
.track .gap{position:absolute;top:0;bottom:0;border-radius:9px;transform-origin:left;animation:grow 1s .2s ease-out both}.gap.hot{background:linear-gradient(90deg,rgba(255,155,138,.35),#FF9B8A)}.gap.cool{background:linear-gradient(90deg,#7FD8AE,rgba(127,216,174,.35))}
.track .dot{position:absolute;top:50%;width:16px;height:16px;margin:-8px 0 0 -8px;border-radius:50%;border:3px solid #16263D}.dot.px{background:#fff}.dot.iv{background:var(--gold2)}.dot.b{background:#AEB8C8;width:12px;height:12px;margin:-6px 0 0 -6px}
@keyframes grow{from{transform:scaleX(0)}to{transform:none}}
.room{font-size:13px;line-height:1.6;color:#C9D1DD;background:rgba(255,255,255,.06);border-radius:12px;padding:11px 13px;margin:14px 0 0}.room b{display:block;color:#fff;font-size:13px;margin-bottom:2px}
.meter{margin:16px 0 4px}.meter .mh{display:flex;align-items:baseline;gap:8px}.meter .mh b{font-size:40px;line-height:1;font-weight:900;color:var(--gold2)}.meter .mh span{font-size:13px;color:#AEB8C8;font-weight:700}
.mbar{position:relative;height:8px;border-radius:9px;background:rgba(255,255,255,.12);margin:10px 0 6px}.mbar i{display:block;height:100%;border-radius:9px;background:var(--gold2);animation:grow 1s .3s ease-out both;transform-origin:left}
.mbar u{position:absolute;top:-4px;bottom:-4px;width:2px;background:#fff;opacity:.8}.meter .mt{font-size:12.5px;color:#AEB8C8}
.how summary{cursor:pointer;font-size:13px;font-weight:700;color:var(--muted);list-style:none}.how summary::-webkit-details-marker{display:none}.how summary:after{content:" +"}.how[open] summary:after{content:" −"}.how p{margin-top:6px}
.join{display:flex;flex-direction:column;gap:8px;margin-top:18px}
.join a.k{display:flex;align-items:center;justify-content:center;gap:8px;height:54px;border-radius:14px;background:#FEE500;color:#191600;font-weight:900;font-size:16.5px;text-decoration:none;box-shadow:0 6px 18px rgba(254,229,0,.18)}
.join a.e{text-align:center;font-size:13.5px;font-weight:700;color:#AEB8C8;text-decoration:none;padding:4px}
.hs{text-align:center;font-size:12.5px;color:#AEB8C8;margin:2px 0 0}
.hero2 .share{margin-top:12px}.hero2 .share button{background:transparent;border-color:rgba(255,255,255,.18);color:#AEB8C8;font-weight:600;font-size:13px;padding:8px}
.kick{font-size:12.5px;font-weight:800;color:var(--gold);letter-spacing:.02em;margin-bottom:4px}
.proof h2,.lock h2{font-size:20px;line-height:1.4}
.proof .big{background:var(--navy);color:#fff;border-radius:14px;padding:16px;text-align:center;margin:12px 0}.proof .big span{display:block;font-size:12.5px;color:#AEB8C8;font-weight:700}.proof .big b{display:block;font-size:34px;font-weight:900;color:var(--gold2);line-height:1.25;margin:4px 0}
.proof .ex{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:12px 0}
.proof .ex a{display:block;text-decoration:none;border:1px solid var(--line);border-radius:12px;padding:10px 12px;background:var(--bg)}.proof .ex .sc{display:inline-block;font-size:12px;font-weight:800;color:#fff;background:var(--gold);border-radius:999px;padding:1px 8px;margin-right:6px}.proof .ex b{font-size:14.5px}.proof .ex em{display:block;font-style:normal;font-weight:800;color:var(--good);font-size:14px;margin-top:2px}
.proof .note{line-height:1.6}
.lock .lk{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0 0}
.lock .lk a{position:relative;display:flex;min-height:150px;border-radius:14px;overflow:hidden;background:var(--bg);border:1px solid var(--line);text-decoration:none}
.lock .blur{position:absolute;inset:12px;filter:blur(3px);opacity:.55}.lock .blur i{display:block;height:9px;border-radius:9px;background:#C9BFAE;margin-bottom:9px}.lock .blur i:nth-child(1){width:70%}.lock .blur i:nth-child(2){width:90%;background:var(--gold2)}.lock .blur i:nth-child(3){width:50%}
.lock .lt{position:relative;flex:1;padding:12px;display:flex;flex-direction:column;gap:3px;background:linear-gradient(180deg,rgba(246,243,236,.2),rgba(246,243,236,.96) 45%)}
.lock .ic{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;background:var(--navy)}
.lock .lt b{font-size:14.5px;line-height:1.35;margin-top:auto;padding-top:14px}.lock .lt small{font-size:12px;color:var(--muted);line-height:1.45}
.lock .join a.e{color:var(--muted)}
.bars2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0}.bars2 span{font-size:12.5px;color:var(--muted);display:block}.bars2 b{font-size:18px}.bars2 .bar{background:#EEE8DC}.bars2 .bar i{background:var(--gold)}
.nums summary{list-style:none;cursor:pointer}.nums summary::-webkit-details-marker{display:none}.nums summary h2{margin:0;display:flex;justify-content:space-between}.nums summary h2:after{content:"+";color:var(--muted)}.nums[open] summary h2:after{content:"−"}.nums table{margin-top:10px}
.endc{background:linear-gradient(165deg,#1A2D47,var(--navy));color:#F3EEE3;border-radius:20px;padding:24px 18px 18px;margin:16px 0}
.endc h2{font-size:22px;line-height:1.4;color:#fff;margin:0 0 14px}
.endc ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}.endc li{display:flex;justify-content:space-between;gap:10px;border-top:1px solid rgba(255,255,255,.1);padding-top:8px;font-size:14px}.endc li:first-child{border-top:0;padding-top:0}.endc li b{color:var(--gold2)}.endc li span{color:#C9D1DD;text-align:right}
@media(max-width:520px){.hero2 h1{font-size:23.5px}.proof .big b{font-size:30px}.lock .lk a{min-height:140px}}
@media(prefers-reduced-motion:reduce){.track .gap,.mbar i{animation:none}}
main .names{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:14.5px;line-height:1.5}main .names a{text-decoration:none;color:#3A4352}
footer{max-width:760px;margin:0 auto;padding:0 16px 40px;font-size:12px;color:var(--muted)}
footer nav{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:8px}footer nav a{text-decoration:none;font-weight:600}
@media(max-width:520px){h1{font-size:22px}.score b{font-size:48px}.price .v{font-size:15px}}`;

const TRACK = (p) => `<script>(function(){try{if(navigator.webdriver||/^(localhost|127\\.)/.test(location.hostname)||/bot|crawl|spider|slurp|yeti|headless|lighthouse|preview|facebookexternalhit/i.test(navigator.userAgent))return;var k='vn-sid',s=localStorage.getItem(k);if(!s){s=(crypto.randomUUID?crypto.randomUUID():String(Math.random()).slice(2)+Date.now()).replace(/-/g,'').slice(0,32);localStorage.setItem(k,s)}var u=navigator.userAgent,q=new URLSearchParams(location.search),r='';try{r=document.referrer?new URL(document.referrer).hostname:''}catch(e){}if(r===location.hostname)r='';r=q.get('utm_source')||(/Instagram/.test(u)?'ig':'')||r;try{if(r&&!localStorage.getItem('vn-ref'))localStorage.setItem('vn-ref',r)}catch(e){}var d=(/Mobi|iPhone|Android/.test(u)?'모바일':'PC')+' · '+(/iPhone|iPad/.test(u)?'iOS':/Android/.test(u)?'Android':/Mac/.test(u)?'Mac':/Windows/.test(u)?'Windows':'기타');fetch('${URL0}/rest/v1/events',{method:'POST',headers:{apikey:'${KEY}',Authorization:'Bearer ${KEY}','Content-Type':'application/json',Prefer:'return=minimal'},body:JSON.stringify({kind:'visit',sid:s,path:${JSON.stringify(p)},ref:r.slice(0,300),device:d}),keepalive:true})}catch(e){}})();</script>`;

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
const FOOT_NAV = `<nav><a href="/c/">기업 점수 전체</a><a href="/c/kr">국내</a><a href="/c/us">미국</a><a href="/c/jp">일본</a><a href="/c/hk">홍콩</a><a href="/c/cn">중국 A</a><a href="/blog/">칼럼 · 이슈 분석</a></nav>`;
const FOOT = (date, what = '공개 재무 자료(Yahoo Finance 연간 재무, 네이버 증권)로 매일 자동 계산한 결과입니다.') => `<footer>${FOOT_NAV}${what} 데이터 기준 ${esc(date)}. 투자 판단의 참고 자료이며 특정 종목의 매수·매도를 권하지 않습니다. © 밸류노트</footer>`;

// 공유 버튼: 휴대폰은 공유 시트, PC는 링크 복사. 공유 링크에는 유입 경로 표시를 붙인다
const SHARE_JS = `<script>document.querySelectorAll('[data-sh]').forEach(function(b){b.onclick=async function(){var u=b.dataset.u+(b.dataset.u.indexOf('?')<0?'?':'&')+'utm_source=share-'+b.dataset.sh,t=b.dataset.t;try{if(navigator.share){await navigator.share({title:document.title,text:t,url:u});return}}catch(e){if(e&&e.name==='AbortError')return}try{await navigator.clipboard.writeText(t+'\\n'+u);b.textContent='링크를 복사했어요'}catch(e){prompt('이 링크를 복사해 보내세요',u)}}})</script>`;

const josa = (w, a, b) => { const c = String(w).trim().slice(-1).charCodeAt(0); if (c < 0xAC00 || c > 0xD7A3) return w + a; return w + ((c - 0xAC00) % 28 ? a : b); };
const gapTxt = (mos) => (mos >= 0 ? `${n0(mos)}% 낮은` : `${n0(-mos)}% 높은`);

function faqItems(x, date) {
  const { r, sc } = x, cur = r.cur || 'KRW', f = r.fin || {};
  const out = [];
  if (isNum(sc.iv) && sc.iv > 0) {
    let a = `그레이엄·워렌 버핏·찰리 멍거의 방식으로 과거 평균 이익·주주 이익과 자산 가치를 바탕으로 계산한 ${r.n}의 적정 주가는 ${money(sc.iv, cur)}입니다.`;
    if (isNum(r.px)) a += isNum(sc.mos) && r.px / sc.iv < 2 ? ` ${date} 기준 현재가(${money(r.px, cur)})는 적정 주가보다 ${gapTxt(sc.mos)} 수준입니다.` : ` ${date} 기준 현재가(${money(r.px, cur)})는 적정 주가의 ${n0(r.px / sc.iv, 1)}배입니다.`;
    a += ' 공식에 따른 추정치이며 미래 주가를 보장하지 않습니다.';
    out.push([`${r.n} 적정 주가는 얼마인가요?`, a]);
  }
  if (isNum(sc.v)) {
    const ok = isNum(sc.mos) && sc.mos >= 30;
    out.push([`${r.n} 지금 저평가인가요?`, `가격 점수는 100점 만점에 ${sc.v}점입니다. ` + (ok
      ? `현재가가 적정 주가보다 30% 이상 낮아, 그레이엄이 말한 안전마진 30% 기준을 충족합니다. 다만 싼 데에는 이유가 있을 수 있으니 재무 점수(${sc.q ?? '–'}점)와 감점 신호를 함께 보세요.`
      : `밸류노트는 적정 주가보다 30% 이상 낮을 때를 안전마진 기준으로 봅니다. 지금은 그 기준에 들어오지 않았습니다.`)]);
  }
  const bits = [];
  if (isNum(sc.per)) bits.push(`PER ${n0(sc.per, 1)}배`);
  if (isNum(sc.pbr)) bits.push(`PBR ${n0(sc.pbr, 2)}배`);
  if (isNum(f.roeAvg)) bits.push(`5년 평균 ROE ${n0(f.roeAvg, 1)}%`);
  if (bits.length) out.push([`${r.n} PER·PBR·ROE는?`, `${date} 기준 ${bits.join(', ')}입니다. PER은 낮을수록 이익 대비 싸고, ROE는 꾸준히 높을수록 자본을 잘 굴리는 회사입니다. 한 해 숫자보다 여러 해 평균을 보는 것이 안전합니다.`]);
  out.push(['밸류노트 점수는 어떻게 계산하나요?', '밸류노트 점수는 숫자 점수 65%, 정성 평가 20%, 트렌드 15%를 합친 값입니다. 숫자 점수는 ROE·이익률·현금흐름 등 13개 지표로 본 재무 점수 40%와 적정 주가 대비 할인율로 본 저평가 점수 60%로 계산하고, 잦은 적자·과도한 빚·잦은 증자 같은 위험 신호는 감점합니다. 정성 평가는 그레이엄·워렌 버핏·찰리 멍거의 질문으로 사업 자체를 따져 본 결과이며, 모든 사용자에게 같은 값을 보여 줍니다. 이 방식은 버크셔 해서웨이의 실제 매수 62건으로 검증했습니다.']);
  return out;
}

// 4년 전 점수 백테스트(소개 페이지 /start 04번과 같은 숫자): slug → [2022-10-20 점수, 1억 원이 2026-10-20에 된 금액]
const BT = { 'meta': ['메타', 92, '4억 9천만 원'], '105560-ks': ['KB금융', 89, '3억 8천만 원'], '000660-ks': ['SK하이닉스', 73, '13억 6천만 원'],
  '6758-t': ['소니그룹', 69, '1억 9천만 원'], '8306-t': ['미쓰비시UFJ', 65, '4억 5천만 원'], 'msft': ['마이크로소프트', 63, '2억 1천만 원'],
  '7203-t': ['토요타', 58, '1억 5천만 원'], '005930-ks': ['삼성전자', 49, '3억 9천만 원'], 'aapl': ['애플', 47, '2억 2천만 원'],
  'googl': ['알파벳', 47, '3억 2천만 원'], '7974-t': ['닌텐도', 42, '1억 3천만 원'], '005380-ks': ['현대차', 22, '2억 1천만 원'] };
const BT_NOTE = '한국·미국·일본에서 많이 아는 회사 12곳을 결과를 보기 전에 먼저 정하고 모두 계산했습니다. 그때 점수는 지금 밸류노트 공식에 2022년 10월 20일까지 나온 결산 자료와 그날 종가만 넣어 다시 계산한 값입니다. 배당 포함·원화 기준 세전 금액이며 수수료는 넣지 않았습니다. 과거 수익률은 미래 수익을 보장하지 않습니다.';
let HI70 = 0, TOTAL = 0; // 지금 70점 이상인 회사 수 / 전체 회사 수 (빌드 때 채운다)
const KAKAO_SVG = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="#000" d="M12 3C6.48 3 2 6.58 2 11c0 2.83 1.84 5.31 4.6 6.73l-.98 3.62c-.09.33.29.59.57.39l4.3-2.86c.5.06 1 .1 1.51.1 5.52 0 10-3.58 10-8S17.52 3 12 3z"/></svg>';
const LOCK_SVG = '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path fill="#FFFFFF" d="M17 9h-1V7a4 4 0 0 0-8 0v2H7a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2zm-7-2a2 2 0 0 1 4 0v2h-4V7z"/></svg>';
// 가입 버튼 한 쌍(카카오 + 이메일). src 로 어느 자리 버튼인지 관리자 통계에서 구분한다
const joinBtns = (wq, src, ktxt = '카카오로 3초 만에 시작') => `<div class="join"><a class="k" href="/?kakao=1&${wq}&utm_source=${src}">${KAKAO_SVG}${ktxt}</a><a class="e" href="/?signup&${wq}&utm_source=${src}-email">이메일로 가입</a></div>`;

function companyPage(x, peers, date) {
  const { r, sc } = x, g = grpOf(r.m), cur = r.cur || 'KRW', f = r.fin || {};
  const url = `${SITE}/c/${x.slug}`;
  const code = r.code || r.t;
  const pens = (sc.flags || []).filter((fl) => !WARN_FLAGS.has(fl)), warns = (sc.flags || []).filter((fl) => WARN_FLAGS.has(fl));
  const b = sc.b;
  const hasIv = isNum(sc.iv) && sc.iv > 0;
  const hasPx = hasIv && isNum(r.px);
  // 검색어 '○○ 적정 주가'에 맞춘 제목 (검색 결과·공유 미리보기용, 그대로 둔다)
  const title = `${r.n} 적정 주가 ${hasIv ? money(sc.iv, cur) + ' · ' : ''}가치투자 점수 ${isNum(b) ? b + '점' : ''} | 밸류노트`;
  const desc = `${r.n}(${code}) 적정 주가와 밸류노트 점수 ${isNum(b) ? b + '점' : '계산 불가'}(재무 점수 ${sc.q ?? '–'}점, 저평가 ${sc.v ?? '–'}점${isNum(sc.qualScore) ? `, 정성 평가 ${sc.qualScore}점` : ''}).` +
    (hasPx ? ` 현재가 ${money(r.px, cur)}, 적정 주가 ${money(sc.iv, cur)}.` : '') +
    (isNum(sc.per) ? ` PER ${n0(sc.per, 1)}배` : '') + (isNum(f.roeAvg) ? `, 5년 평균 ROE ${n0(f.roeAvg, 1)}%.` : '.') + ` 그레이엄·워렌 버핏 기준으로 매일 계산합니다.`;
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
  // 가입 직후 앱이 이 회사를 관심 종목에 담는다
  const wq = `co=${encodeURIComponent(code)}&q=${encodeURIComponent(r.n)}&watch=${encodeURIComponent(r.t || code)}`;
  /* 적정 매수가(적정 주가의 70%) 알림은 현재가가 30% 안쪽일 때만 권한다. 너무 먼 회사는 알림 대신 내 종목 채점을 권한다 */
  const buy = hasIv ? sc.iv * 0.7 : null;
  const below = isNum(buy) && isNum(r.px) && r.px <= buy;
  const near = isNum(buy) && isNum(r.px) && !below && r.px / buy < 1.4;
  const R = hasPx ? r.px / sc.iv : null;
  const cyc = hasIv && (sc.cyc || (sc.flags || []).includes('경기순환·이익 변동'));

  // ① 첫 화면: 결론 한 줄(구체 숫자) → 가격 자 → 가입 버튼
  const h1 = hasIv ? `${esc(r.n)} 적정 주가,<br>워렌 버핏 기준으로는 <em>${money(sc.iv, cur)}</em>` : `${esc(r.n)} 가치투자 점수 <em>${isNum(b) ? b + '점' : '–'}</em>`;
  const verdict = !hasPx ? ''
    : R >= 2 ? `지금 주가 ${josa(money(r.px, cur), '은', '는')} 적정 주가의 <b class="hot">${n0(R, 1)}배</b>입니다.`
    : R > 1 ? `지금 주가 ${josa(money(r.px, cur), '은', '는')} 적정 주가보다 <b class="hot">${n0((R - 1) * 100)}% 고평가</b>돼 있습니다.`
    : `지금 주가 ${josa(money(r.px, cur), '은', '는')} 적정 주가보다 <b class="cool">${n0((1 - R) * 100)}% 저평가</b>돼 있습니다. 적정 주가까지 상승 여력은 <b class="cool">+${n0((1 / R - 1) * 100)}%</b>입니다.`;
  let ruler = '';
  if (hasPx) {
    const max = Math.max(r.px, sc.iv) * 1.06, pos = (v) => Math.max(2, Math.min(98, (v / max) * 100));
    const pP = pos(r.px), pI = pos(sc.iv), pB = pos(buy), side = (p) => (p < 50 ? 'l' : 'r');
    const lo = Math.min(pP, pI), hi = Math.max(pP, pI);
    ruler = `<div class="ruler" aria-hidden="true"><div class="up"><span class="m ${side(pP)}" style="left:${pP}%"><small>지금 주가</small>${money(r.px, cur)}</span></div>
<div class="track"><i class="gap ${R > 1 ? 'hot' : 'cool'}" style="left:${lo}%;width:${hi - lo}%"></i>${near || below ? `<i class="dot b" style="left:${pB}%"></i>` : ''}<i class="dot iv" style="left:${pI}%"></i><i class="dot px" style="left:${pP}%"></i></div>
<div class="dn">${near || below ? `<span class="m r sm" style="left:${pB}%"><small>적정 매수가</small>${money(buy, cur)}</span><span class="m ${side(pI)}" style="left:${pI}%"><small>적정 주가</small>${money(sc.iv, cur)}</span>` : `<span class="m ${side(pI)}" style="left:${pI}%"><small>적정 주가</small>${money(sc.iv, cur)}</span>`}</div></div>`;
  }
  const heroBtnTxt = below ? '카카오로 3초 만에 관심 종목 담기' : near ? `카카오로 ${money(buy, cur)} 알림 받기` : '카카오로 3초 만에 내 종목 채점받기';
  const heroSub = below ? '지금 적정 매수가 아래입니다. 담아 두면 관심 종목에서 매일 점수를 확인할 수 있습니다.'
    : near ? '적정 매수가에 닿는 날 휴대폰으로 바로 알려 드립니다.'
    : `밸류노트는 ${TOTAL}개 회사를 같은 기준으로 매일 계산합니다.`;
  const meter = isNum(b) ? `<div class="meter"><div class="mh"><b>${b}</b><span>/ 100 · 밸류노트 점수</span></div><div class="mbar"><i style="width:${b}%"></i><u style="left:70%"></u></div><div class="mt">흰 선이 70점입니다. 지금 ${TOTAL}개 회사 중 70점을 넘는 회사는 ${HI70}곳입니다.</div></div>` : '';
  const hero = `<section class="hero2"><div class="eyebrow">워렌 버핏·벤저민 그레이엄 기준 · ${esc(date)} 계산</div>
<h1>${h1}</h1>${verdict ? `<p class="verdict">${verdict}</p>` : ''}${ruler}
${cyc ? `<p class="room"><b>이 계산이 틀릴 수 있는 경우</b>좋은 해의 이익이 계속된다고 보지 않고 보수적으로 계산했습니다. 호황이 길게 이어지면 적정 주가는 더 높아질 수 있습니다.</p>` : ''}
${meter}
<div id="heroJoin">${joinBtns(wq, below ? 'c-hero-below' : near ? 'c-hero-alert' : 'c-hero', heroBtnTxt)}<p class="hs">${heroSub}</p></div>
<div class="share"><button type="button" data-sh="c" data-u="${url}" data-t="">이 점수 공유하기</button></div></section>`;

  // ② 증거: 그때 그 점수였을 때 샀다면
  const bt = BT[x.slug];
  const ex = ['000660-ks', 'meta', '105560-ks'];
  const proof = `<section class="card proof"><div class="kick">밸류노트 점수대로 샀다면</div>
${bt ? `<h2>4년 전 ${esc(josa(r.n, '은', '는'))} ${bt[1]}점이었습니다</h2><div class="big"><span>2022년 10월 1억 원</span><b>${bt[2]}</b><span>2026년 10월 · 배당 포함</span></div>
<p>지금 ${esc(r.n)} 점수는 ${isNum(b) ? b + '점' : '–'}입니다. 같은 기준으로 매일 다시 계산하기 때문에, 점수가 다시 올라오는 날도 바로 알 수 있습니다.</p>`
  : `<h2>4년 전 70점 이상이던 회사에 1억 원을 넣었다면</h2><div class="big"><span>2022년 10월 1억 원</span><b>평균 7억 4,500만 원</b><span>같은 돈을 코스피에 넣었다면 2억 5천만 원</span></div>`}
<div class="ex">${ex.filter((s) => s !== x.slug).slice(0, bt ? 2 : 3).map((s) => `<a href="/c/${s}"><span class="sc">${BT[s][1]}점</span><b>${BT[s][0]}</b><em>1억 → ${BT[s][2]}</em></a>`).join('')}</div>
<p>그때 70점을 넘었던 세 곳은 모두 코스피보다 많이 벌었습니다. 70점이 안 되던 아홉 곳 가운데 코스피를 이긴 곳은 세 곳뿐이었습니다.</p><details class="how"><summary>어떻게 계산했나요?</summary><p class="note">${BT_NOTE} 점수가 늘 맞지는 않습니다. 버크셔 해서웨이는 이 방식으로 고평가로 나오는 알파벳을 올해도 더 샀습니다.</p></details></section>`;

  // ③ 가입하면 보이는 것(잠금 미리보기). 가짜 숫자는 넣지 않고 모양만 흐리게 보여 준다
  const locks = [
    ['찰리 멍거의 질문 체크', `${esc(r.n)}의 사업을 10년 뒤에도 괜찮은지 질문으로 따져 본 정성 평가`],
    ['주가 차트와 적정 주가', '지금 가격이 적정 주가 위·아래 어디에 있는지 한눈에'],
    near || below ? ['적정 매수가 알림', `${money(buy, cur)}에 닿는 날 휴대폰으로 알림`] : ['저평가 순위 전체', '5개 시장에서 적정 주가보다 싼 회사 순위, 매일 갱신'],
    ['내 포트폴리오 채점', '가진 종목을 넣으면 가치주·관찰주·투기주로 나눠 유지·정리 판단'],
  ];
  const lockSec = `<section class="card lock"><div class="kick">가입하면 바로 열립니다</div><h2>${esc(r.n)}, 여기서부터는 밸류노트 안에서 볼 수 있습니다</h2>
<div class="lk">${locks.map(([t, d], i) => `<a href="/?kakao=1&${wq}&utm_source=c-lock"><div class="blur b${i}"><i></i><i></i><i></i></div><div class="lt"><span class="ic">${LOCK_SVG}</span><b>${t}</b><small>${d}</small></div></a>`).join('')}</div>
${joinBtns(wq, 'c-lock')}</section>`;

  // ④ 마지막 가입 블록
  const endSec = `<section class="endc" id="endJoin"><h2>${esc(r.n)}만이 아닙니다.<br>내가 가진 종목은 몇 점일까요?</h2>
<ul><li><b>${TOTAL}개 회사</b><span>5개 시장을 매일 같은 기준으로 계산</span></li><li><b>적정 매수가 알림</b><span>싸지는 날 휴대폰·PC로</span></li><li><b>유지·정리 판단</b><span>내 종목을 넣으면 바로</span></li></ul>
${joinBtns(wq, 'c-end')}<p class="hs">워렌 버핏·찰리 멍거의 기준으로 주식을 평가해 현명한 투자를 돕습니다.</p></section>`;

  /* 아래 고정 바: 첫 화면 가입 버튼이 화면에서 사라지면 나타나고, 마지막 가입 블록이 보이면 숨는다 */
  const wtxt = below ? `<span>${esc(r.n)} 적정 매수가 ${money(buy, cur)}</span><b>지금 그 아래입니다</b><span>관심 종목에 담아 두고 지켜보세요</span>`
    : near ? `<span>${esc(r.n)} 적정 매수가</span><b>${money(buy, cur)}</b><span>이 가격에 오면 알려 드려요</span>`
    : `<b>내 종목은 몇 점일까요?</b><span>보유 종목을 같은 기준으로 채점해 드려요</span>`;
  const wbar = hasPx ? `<div class="wbar" id="wbar"><div class="in"><div class="t">${wtxt}</div><div style="text-align:center"><a class="k" href="/?kakao=1&${wq}&utm_source=${below ? 'c-wbar-below' : near ? 'c-wbar' : 'c-wbar-score'}">${KAKAO_SVG.replace(/18/g, '17')}${below ? '카카오로 담기' : near ? '카카오로 알림' : '카카오로 3초'}</a><a class="e" href="/?signup&${wq}&utm_source=c-wbar-email">이메일로 가입</a></div></div></div>
<script>(function(){var b=document.getElementById('wbar');if(!b)return;document.body.classList.add('has-wbar');var h=document.getElementById('heroJoin'),e=document.getElementById('endJoin'),hv=true,ev=false;function u(){b.classList.toggle('on',!hv&&!ev)}if(!('IntersectionObserver'in window)){addEventListener('scroll',function(){hv=scrollY<innerHeight*.6;u()},{passive:true});return}new IntersectionObserver(function(a){hv=a[0].isIntersecting;u()}).observe(h);new IntersectionObserver(function(a){ev=a[0].isIntersecting;u()}).observe(e)})();</script>` : '';
  const shareText = `${r.n} 밸류노트 점수 ${isNum(b) ? b + '점' : '–'}` + (hasPx && R < 2 && isNum(sc.mos) ? ` · 적정 주가보다 ${gapTxt(sc.mos)} 가격` : '') + '. 그레이엄·워렌 버핏 기준으로 본 숫자';
  return head({ title, desc, url, ld, img: ogUrl(x.slug, date) }) + `<main class="lp">
<div class="crumb"><a href="/c/">기업 점수</a> › <a href="/c/${MSLUG[g]}">${MKT[g]}</a> › ${esc(r.n)} <span class="note">· ${esc(code)}${r.ind ? ' · ' + esc(r.ind) : ''}</span></div>
${hero.replace('data-t=""', `data-t="${esc(shareText)}"`)}
${proof}
${lockSec}
${sum.length || pens.length || warns.length ? `<section class="card"><h2>숫자로 읽는 ${esc(r.n)}</h2>${sum.map((s) => `<p>${esc(s)}</p>`).join('')}
${cyc ? `<p class="note cyc"><b>이 계산이 틀릴 수 있는 경우</b> 이익이 해마다 크게 오르내리는 업종이라, 지금 같은 좋은 해의 이익이 계속된다고 보지 않고 보수적으로 계산했습니다. 호황이 일시적이지 않고 구조적으로 길게 이어진다면, 이 적정 주가는 가치를 낮게 잡은 것이 됩니다.${isNum(sc.per) && sc.per > 0 ? ` 최근 이익만 보면 PER은 ${n0(sc.per, 1)}배입니다.` : ''}</p>` : ''}
${pens.map((fl) => `<div class="flag"><span class="pill p-pen">감점 −8</span><b>${esc(fl)}</b>${FLAG_HELP[fl] ? `<div class="h">${esc(FLAG_HELP[fl])}</div>` : ''}</div>`).join('')}${warns.map((fl) => `<div class="flag"><span class="pill ${fl === '중국 본토 규제' ? 'p-pen' : 'p-warn'}">${fl === '중국 본토 규제' ? '할인 −6' : '경고'}</span><b>${esc(fl)}</b>${FLAG_HELP[fl] ? `<div class="h">${esc(FLAG_HELP[fl])}</div>` : ''}</div>`).join('')}
<div class="bars2"><div><span>재무 점수</span><b>${sc.q ?? '–'}점</b><div class="bar"><i style="width:${sc.q || 0}%"></i></div></div><div><span>저평가 점수</span><b>${sc.v ?? '–'}점</b><div class="bar"><i style="width:${sc.v || 0}%"></i></div></div></div>
<p class="note">밸류노트 점수는 숫자 65%·정성 평가 20%·트렌드 15%를 합친 값입니다${sc.qualDone ? '' : '(이 회사는 정성 평가 전)'}. 적정 주가는 과거 평균 이익·주주 이익과 자산 가치로 계산한 값이며 미래를 보장하지 않습니다.${r.fin_sector ? ' 금융업은 현금흐름 할인 대신 자산·이익 기준을 씁니다.' : ''}</p></section>` : ''}
${rowsM.length ? `<section class="card"><details class="nums"><summary><h2>핵심 숫자 ${rowsM.length}개 모두 보기</h2></summary><table>${rowsM.map((m) => `<tr><td>${m[0]}${m[2] ? `<div class="note">${m[2]}</div>` : ''}</td><td class="n">${m[1]}</td></tr>`).join('')}</table></details></section>` : ''}
${endSec}
<section class="card faq"><h2>자주 묻는 질문</h2>${faq.map(([q, a], i) => `<details${i === 0 ? ' open' : ''}><summary>${esc(q)}</summary><p>${esc(a)}</p></details>`).join('')}</section>
${peers.length ? `<section class="card peers"><h2>같은 업종의 다른 회사</h2>${peers.map((p) => `<a href="/c/${p.slug}"><span>${esc(p.r.n)} <span class="note">${MKT[grpOf(p.r.m)]}</span></span><b>${p.sc.b ?? '–'}점</b></a>`).join('')}</section>` : ''}
</main>${FOOT(date)}${wbar}${SHARE_JS}${TRACK('/c/' + x.slug)}</body></html>`;
}

// 시장 순위 표 (기업 점수 전체·시장별 페이지 공통)
const rankTable = (list) => `<table><tr><th>#</th><th>회사</th><th style="text-align:right">점수</th></tr>${list.map((x, i) => `<tr><td class="s">${i + 1}</td><td><a href="/c/${x.slug}">${esc(x.r.n)}</a><div class="s">${esc(x.r.ind || x.r.s || '')}</div></td><td class="n">${x.sc.b ?? '–'}</td></tr>`).join('')}</table>`;
const MSLUG = { KR: 'kr', US: 'us', JP: 'jp', HK: 'hk', CN: 'cn' };
const MKT_LONG = { KR: '국내 주식(코스피·코스닥)', US: '미국 주식', JP: '일본 주식', HK: '홍콩 주식', CN: '중국 A주' };
// 품질이 기준 이상이고 적정 주가보다 30% 이상 싼 회사 (사실 기준 필터. 추천 아님)
const isBargain = (x) => isNum(x.sc.mos) && x.sc.mos >= 30 && isNum(x.sc.q) && x.sc.q >= 60 && !(x.sc.flags || []).some((fl) => !WARN_FLAGS.has(fl));

// 순위는 앞부분만 공개하고(1~3위는 가입 후, 4위부터 몇 곳만), 나머지 회사는 점수 없이 가나다순 이름 목록으로만 연결한다
const byName = (list) => [...list].sort((a, b) => String(a.r.n).localeCompare(String(b.r.n), 'ko'));
const nameList = (list) => `<div class="names">${byName(list).map((x) => `<a href="/c/${x.slug}">${esc(x.r.n)}</a>`).join('')}</div>`;
const appValue = (m, src) => `/?tab=value&mkt=${m}&utm_source=${src}`;
const lockRow = (i, m, sub, right) => `<tr><td><a href="${appValue(m, 'c-' + MSLUG[m] + '-gate')}" style="color:var(--gold)">${i + 1}위 · 밸류노트에 가입하면 볼 수 있습니다 ›</a><div class="s">${sub}</div></td><td class="n pos">${right}</td></tr>`;
const SHOW_TO = 8; // 4~8위만 이름 공개

function indexPage(all, date) {
  const url = `${SITE}/c/`;
  const by = Object.fromEntries(MKT_ORDER.map((m) => [m, all.filter((x) => grpOf(x.r.m) === m)]));
  const title = `기업 ${all.length}곳의 적정 주가와 밸류노트 점수 · 그레이엄·워렌 버핏 기준 | 밸류노트`;
  const desc = `국내·미국·일본·홍콩·중국 ${all.length}개 기업의 적정 주가와 밸류노트 점수를 같은 기준(재무 점수·가격 점수·감점 신호)으로 매일 계산합니다. 회사 이름을 눌러 확인하세요.`;
  const ld = { '@context': 'https://schema.org', '@type': 'CollectionPage', name: title, url, dateModified: date, inLanguage: 'ko-KR' };
  return head({ title, desc, url, ld, type: 'website' }) + `<main>
<h1>기업 ${all.length}곳의 적정 주가와 점수</h1><p class="sub">그레이엄·워렌 버핏·찰리 멍거의 기준을 숫자로 옮겨, 5개 시장의 기업을 같은 잣대로 매일 다시 계산합니다. 회사 이름을 누르면 적정 주가와 점수를 볼 수 있습니다.</p>
<div class="mlinks">${MKT_ORDER.map((m) => `<a href="/c/${MSLUG[m]}">${MKT[m]} 저평가 순위<small>${by[m].length}곳 중 기준 통과 ${by[m].filter(isBargain).length}곳</small></a>`).join('')}<a href="/blog/">칼럼<small>매주 시장·거장의 투자</small></a></div>
${MKT_ORDER.map((m) => `<section class="card list" id="${m}"><h2>${MKT[m]} ${by[m].length}곳 <span class="note">(가나다순)</span></h2>${nameList(by[m])}</section>`).join('')}
<a class="cta" href="${appValue('ALL', 'c-index')}">밸류노트에서 저평가 순위 전체 보기<small>가입은 이메일만으로 10초 · 관심 종목 적정 매수가 알림</small></a>
</main>${FOOT(date)}${TRACK('/c/')}</body></html>`;
}

function marketPage(m, list, date) {
  const url = `${SITE}/c/${MSLUG[m]}`;
  const sorted = [...list].sort((a, b) => (b.sc.b ?? -1) - (a.sc.b ?? -1)).filter((x) => isNum(x.sc.b));
  const bar = list.filter(isBargain).sort((a, b) => b.sc.mos - a.sc.mos);
  const title = `${MKT_LONG[m]} 저평가 우량주 순위 · 적정 주가 ${list.length}곳 | 밸류노트`;
  const desc = `${MKT_LONG[m]} ${list.length}곳의 적정 주가와 밸류노트 점수를 매일 계산합니다. 재무 점수 60점 이상이면서 적정 주가보다 30% 이상 저평가된 회사는 ${bar.length}곳입니다(${date} 기준).`;
  const ld = { '@context': 'https://schema.org', '@graph': [
    { '@type': 'BreadcrumbList', itemListElement: [
      { '@type': 'ListItem', position: 1, name: '밸류노트', item: SITE + '/' },
      { '@type': 'ListItem', position: 2, name: '기업 점수', item: SITE + '/c/' },
      { '@type': 'ListItem', position: 3, name: `${MKT[m]} 순위`, item: url }] },
  ] };
  const shareText = `${MKT_LONG[m]} 중 적정 주가보다 30% 이상 저평가된 좋은 회사는 ${bar.length}곳입니다`;
  const barRows = bar.slice(0, SHOW_TO).map((x, i) => i < 3
    ? lockRow(i, m, `재무 점수 ${x.sc.q}점`, `${n0(x.sc.mos)}% 저평가`)
    : `<tr><td><a href="/c/${x.slug}">${esc(x.r.n)}</a><div class="s">재무 점수 ${x.sc.q}점 · 밸류노트 점수 ${x.sc.b ?? '–'}점</div></td><td class="n pos">${n0(x.sc.mos)}% 저평가</td></tr>`).join('');
  const topRows = sorted.slice(0, SHOW_TO + 2).map((x, i) => i < 3
    ? lockRow(i, m, esc(x.r.ind || x.r.s || ''), `${x.sc.b}점`)
    : `<tr><td><a href="/c/${x.slug}">${esc(x.r.n)}</a><div class="s">${esc(x.r.ind || x.r.s || '')}</div></td><td class="n">${x.sc.b}점</td></tr>`).join('');
  return head({ title, desc, url, ld, type: 'website' }) + `<main>
<div class="crumb"><a href="/c/">기업 점수</a> › ${MKT[m]}</div>
<section class="card hero"><h1>${MKT_LONG[m]} 저평가 우량주 순위</h1><p class="sub" style="margin-top:6px">${list.length}곳을 그레이엄·워렌 버핏 기준으로 매일 다시 계산합니다. 적정 주가보다 30% 이상 낮으면 저평가가 크다고 봅니다.</p>
<div class="share"><button type="button" data-sh="m" data-u="${url}" data-t="${esc(shareText)}">이 순위 공유하기</button></div></section>
<section class="card list"><h2>적정 주가보다 30% 이상 저평가된 좋은 회사는 ${bar.length}곳입니다</h2>${bar.length ? `<table><tr><th>회사</th><th style="text-align:right">적정 주가 대비</th></tr>${barRows}</table>
${bar.length > SHOW_TO ? `<a class="alert" href="${appValue(m, 'c-' + MSLUG[m] + '-more')}"><b>나머지 ${bar.length - SHOW_TO}곳과 1~3위는 밸류노트에서 볼 수 있습니다</b><span>전체 보기 ›</span></a>` : ''}` : '<p class="note">오늘은 이 기준을 통과한 회사가 없습니다. 좋은 회사의 가격이 내려올 때까지 기다리는 날입니다.</p>'}
<p class="note" style="margin-top:8px">재무 점수 60점 이상이고 감점 신호(잦은 적자·과도한 빚·잦은 증자 등)가 없는 회사만 넣었습니다. 숫자로 거른 목록이며 매수 권유가 아닙니다.</p></section>
<section class="card list"><h2>밸류노트 점수 상위 ${Math.min(sorted.length, SHOW_TO + 2)}곳</h2><table><tr><th>회사</th><th style="text-align:right">점수</th></tr>${topRows}</table>
<a class="alert" href="${appValue(m, 'c-' + MSLUG[m] + '-rank')}"><b>전체 순위와 1~3위는 밸류노트에서 볼 수 있습니다</b><span>전체 보기 ›</span></a></section>
<section class="card list"><h2>${MKT[m]} 기업 ${list.length}곳 <span class="note">(가나다순 · 이름을 누르면 적정 주가를 볼 수 있습니다)</span></h2>${nameList(list)}</section>
<a class="cta" href="${appValue(m, 'c-' + MSLUG[m])}">관심 종목이 적정 매수가에 오면 알림 받기<small>가입은 이메일만으로 10초</small></a>
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
const colBy = (c) => { const a = String(c.author || '').trim(); return a && !/^(valuenote|밸류노트)$/i.test(a) ? a : ''; };
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
<h1>${esc(c.title)}</h1>${c.sub ? `<p class="sub">${esc(c.sub)}</p>` : ''}<p class="note">${esc(colDateK(c))} · ${esc(colBy(c) || '밸류노트')}</p>
${colBodyHtml(c.body)}
${(c.sources || []).length ? `<div class="src"><b>참고한 자료</b><br>${c.sources.map((s) => `<a href="${esc(s)}" rel="nofollow noopener" target="_blank">${esc(s.replace(/^https?:\/\//, '').slice(0, 70))}</a>`).join('<br>')}</div>` : ''}
${colBy(c) ? `<p class="note" style="margin-top:14px">밸류노트 에디터 Luciano가 작성한 글입니다.</p>` : ''}
<div class="share" style="margin-top:16px"><button type="button" data-sh="blog" data-u="${url}" data-t="${esc(c.title)}" style="color:var(--ink);border-color:var(--line);background:var(--bg)">이 글 공유하기</button></div>
</article>
<a class="cta" href="/?utm_source=blog">매주 월요일, 칼럼을 메일로 받기<small>밸류노트에 가입하고 구독을 켜세요 · 600+ 기업 점수도 함께</small></a>
${others.length ? `<section class="card peers"><h2>다른 칼럼</h2>${others.map((o) => `<a href="/blog/${o.id}"><span>${esc(o.title)}</span><span class="note">${esc(colDateK(o))}</span></a>`).join('')}</section>` : ''}
</main>${FOOT(iso.slice(0, 10), '투자 교육용 칼럼입니다.')}${SHARE_JS}${TRACK('/blog/' + c.id)}</body></html>`;
}
function blogIndex(cols, date, issues = []) {
  const url = `${SITE}/blog/`;
  const title = '밸류노트 칼럼 · 이슈 분석, 주간 시장, 거장의 투자';
  const desc = '화제의 기업을 숫자로 파고드는 이슈 분석, 매주 시장·금리·환율 흐름, 워렌 버핏·그레이엄·찰리 멍거의 투자를 정리하는 밸류노트 칼럼입니다.';
  const issueRow = (x) => `<a href="/blog/${esc(x.slug)}"><span><b style="color:var(--ink)">${esc(x.title)}</b><span class="note" style="display:block">이슈 분석 · ${esc(x.date || '')}</span></span></a>`;
  return head({ title, desc, url, type: 'website', src: 'blog', rss: true, ld: { '@context': 'https://schema.org', '@type': 'Blog', name: title, url, inLanguage: 'ko-KR' } }) + `<main>
<h1>칼럼</h1><p class="sub">${esc(desc)}</p>
<h2 style="margin:18px 0 8px">이슈 분석</h2><p class="note" style="margin:0 0 8px">릴스에서 다 못 한 숫자와 원인, 내 종목 점검법까지 정리한 글입니다.</p>
<section class="card peers" id="issues">${issues.map(issueRow).join('') || '<p class="note">곧 올라옵니다.</p>'}</section>
<script>fetch('/blog/issues.json',{cache:'no-cache'}).then(function(r){return r.json()}).then(function(L){if(!L||!L.length)return;var e=function(t){return String(t).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})};document.getElementById('issues').innerHTML=L.map(function(x){return '<a href="/blog/'+e(x.slug)+'"><span><b style="color:var(--ink)">'+e(x.title)+'</b><span class="note" style="display:block">이슈 분석 · '+e(x.date||'')+'</span></span></a>'}).join('')}).catch(function(){});</script>
<h2 style="margin:22px 0 8px">주간 시장 · 거장의 투자</h2>
<section class="card peers">${cols.map((c) => `<a href="/blog/${c.id}"><span><b style="color:var(--ink)">${esc(c.title)}</b><span class="note" style="display:block">${esc(COL_SERIES[c.series || 'weekly'])} · ${esc(colDateK(c))}</span></span></a>`).join('')}</section>
<a class="cta" href="/?utm_source=blog-index">밸류노트 열기<small>600+ 기업 점수 · 적정 매수가 알림</small></a>
</main>${FOOT(date, '투자 교육용 칼럼입니다.')}${TRACK('/blog/')}</body></html>`;
}
const xmlEsc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' }[c]));
function rss(cols, issues = []) {
  const iss = issues.map((x) => { const u = `${SITE}/blog/${x.slug}`; const d = new Date(x.at);
    return `<item><title>${xmlEsc(x.title)}</title><link>${u}</link><guid isPermaLink="true">${u}</guid><pubDate>${(isNaN(d) ? new Date() : d).toUTCString()}</pubDate><description>${xmlEsc(x.desc || '')}</description></item>`; });
  const items = cols.map((c) => { const u = `${SITE}/blog/${c.id}`; const d = new Date(c.at || c.id.slice(4, 14));
    return `<item><title>${xmlEsc(c.title)}</title><link>${u}</link><guid isPermaLink="true">${u}</guid><pubDate>${(isNaN(d) ? new Date() : d).toUTCString()}</pubDate><description>${xmlEsc((c.sub ? c.sub + ' · ' : '') + plain(c.body).slice(0, 300))}</description></item>`; }).concat(iss).join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>밸류노트 칼럼</title><link>${SITE}/blog/</link><description>가치투자 칼럼 · 주간 시장과 거장의 투자</description><language>ko</language>\n${items}\n</channel></rss>\n`;
}
// 이슈 분석(릴스 정리본): scripts/reels/guide.py 가 blog/<slug>.html 과 blog/issues.json 을 쓴다. 여기서는 목록·RSS·사이트맵에만 넣는다
function loadIssues() {
  try { return JSON.parse(fs.readFileSync(path.join(ROOT, 'blog', 'issues.json'), 'utf8')).filter((x) => x.slug && x.title); } catch (_) { return []; }
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
const all = rows.map((r) => ({ r, sc: score(r), slug: slug(r) })).filter((x) => x.slug && !seen.has(x.slug) && seen.add(x.slug));
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
HI70 = all.filter((x) => isNum(x.sc.b) && x.sc.b >= 70).length; TOTAL = all.length;
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
// 소개 페이지 마지막 '지금 적정 매수가 아래' 순위: 앱 저평가 순위(valueRows 'under')와 같은 기준·같은 순서
//  현재가 ≤ 적정 주가의 75%, 재무 점수 50점 이상, 감점 신호 없음, 데이터 신뢰도 낮음 제외 → 가장 많이 싼 순
const vt = {};
for (const x of all) {
  const { r, sc } = x;
  if (!isNum(sc.iv) || sc.iv <= 0 || !isNum(r.px) || r.dataConf === 'low') continue;
  const R = r.px / sc.iv, pen = (sc.flags || []).filter((fl) => !WARN_FLAGS.has(fl)).length;
  if (!(R <= 0.75 && isNum(sc.q) && sc.q >= 50 && !pen)) continue;
  (vt[grpOf(r.m)] = vt[grpOf(r.m)] || []).push({ R, b: R0(sc.b), ind: r.ind || r.s || '', n: r.n, slug: x.slug });
}
const valueTop = {};
for (const [m, L] of Object.entries(vt)) { L.sort((a, b) => a.R - b.R);
  valueTop[m] = { n: L.length, top: L.slice(0, 5).map((y, i) => Object.assign({ b: y.b, ind: y.ind, low: Math.round((1 - y.R) * 100), up: Math.round((1 / y.R - 1) * 100) }, i === 0 ? { n: y.n, s: y.slug } : {})) }; }
fs.writeFileSync(path.join(dir, 'value-top.json'), JSON.stringify({ date, m: valueTop }));
// 이름은 시장별 1위만 소개 첫 화면 맛보기로 공개하고, 2위부터는 가입 후에만 보인다
if (process.env.VT_DEBUG) console.log(JSON.stringify(Object.fromEntries(Object.entries(vt).map(([m, L]) => [m, L.slice(0, 5).map((y) => y.n + ' ' + Math.round((1 - y.R) * 100) + '%')]))));

// 칼럼 정적 페이지·RSS (blog/ 아래 이미지 폴더는 건드리지 않는다)
const cols = await loadColumns();
const issues = loadIssues();
const bdir = path.join(ROOT, 'blog');
fs.mkdirSync(bdir, { recursive: true });
// 칼럼 글(col-*)만 지우고 다시 쓴다. 이슈 분석 글(blog/<slug>.html)은 guide.py 담당이라 건드리지 않는다
for (const f of fs.readdirSync(bdir)) if (/^col-.*\.html$/.test(f)) fs.rmSync(path.join(bdir, f));
for (const c of cols) fs.writeFileSync(path.join(bdir, c.id + '.html'), colPage(c, cols));
fs.writeFileSync(path.join(bdir, 'index.html'), blogIndex(cols, date, issues));
fs.writeFileSync(path.join(ROOT, 'rss.xml'), rss(cols, issues));
// 이슈 분석 글(guide.py)이 '다른 칼럼'에 쓰는 목록
fs.writeFileSync(path.join(bdir, 'columns.json'), JSON.stringify(cols.slice(0, 6).map((c) => ({ id: c.id, title: c.title, series: COL_SERIES[c.series || 'weekly'], date: colDateK(c) }))));

const sm = [[`${SITE}/`, date, '1.0'], [`${SITE}/c/`, date, '0.9'], ...MKT_ORDER.map((m) => [`${SITE}/c/${MSLUG[m]}`, date, '0.9']),
  [`${SITE}/blog/`, (cols[0]?.at || date).slice(0, 10), '0.8'], ...cols.map((c) => [`${SITE}/blog/${c.id}`, (c.at || c.id.slice(4, 14)).slice(0, 10), '0.7']),
  ...issues.map((x) => [`${SITE}/blog/${x.slug}`, String(x.at || date).slice(0, 10), '0.7']),
  ...all.map((x) => [`${SITE}/c/${x.slug}`, date, '0.6'])];
fs.writeFileSync(path.join(ROOT, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${sm.map(([u, d, p]) => `<url><loc>${u}</loc><lastmod>${d}</lastmod><priority>${p}</priority></url>`).join('\n')}\n</urlset>\n`);
fs.writeFileSync(path.join(ROOT, 'robots.txt'), `User-agent: *\nAllow: /\nDisallow: /admin\n\nSitemap: ${SITE}/sitemap.xml\n`);
console.log(`pages ${all.length} · markets ${MKT_ORDER.length} · columns ${cols.length} · date ${date}`);

// 네이버·빙 등 검색엔진에 바뀐 주소만 바로 알린다(IndexNow). GitHub Actions 에서만 INDEXNOW=1 로 켠다
if (process.env.INDEXNOW === '1') {
  const changed = all.filter((x) => { const o = prev[x.slug]; const n = scores[x.slug]; return !o || o[1] !== n[1] || o[0] !== n[0]; }).map((x) => `${SITE}/c/${x.slug}`);
  const list = [...new Set([`${SITE}/`, `${SITE}/c/`, ...MKT_ORDER.map((m) => `${SITE}/c/${MSLUG[m]}`), `${SITE}/blog/`, ...cols.slice(0, 3).map((c) => `${SITE}/blog/${c.id}`), ...issues.slice(0, 3).map((x) => `${SITE}/blog/${x.slug}`), ...changed])].slice(0, 9000);
  const body = JSON.stringify({ host: 'www.valuenote.co.kr', key: INDEXNOW_KEY, keyLocation: `${SITE}/${INDEXNOW_KEY}.txt`, urlList: list });
  for (const ep of ['https://searchadvisor.naver.com/indexnow', 'https://api.indexnow.org/indexnow']) {
    try { const r = await fetch(ep, { method: 'POST', headers: { 'Content-Type': 'application/json; charset=utf-8' }, body }); console.log(`::notice::IndexNow ${ep} → ${r.status} (${list.length}개 주소)`); }
    catch (e) { console.log(`::warning::IndexNow ${ep} 실패: ${e.message}`); }
  }
}
