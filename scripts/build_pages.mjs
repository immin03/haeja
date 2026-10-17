// 기업별 공개 페이지 생성기: 스크리너 데이터(공개 읽기)를 받아 화면과 같은 점수 코드로 계산하고
// /c/<코드>.html 600여 개 + /c/index.html + sitemap.xml + robots.txt 를 만든다.
// 실행: node scripts/build_pages.mjs   (GitHub Actions pages.yml 이 매일 돌린다)
import fs from 'node:fs';
import path from 'node:path';
import { scoreRow, grpOf, WARN_FLAGS, setSettings } from '../supabase/functions/watch-select/scoring.js';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SITE = 'https://www.valuenote.co.kr';
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
footer{max-width:760px;margin:0 auto;padding:0 16px 40px;font-size:12px;color:var(--muted)}
@media(max-width:520px){h1{font-size:22px}.score b{font-size:48px}.price .v{font-size:15px}}`;

const TRACK = (p) => `<script>(function(){try{if(navigator.webdriver||/^(localhost|127\\.)/.test(location.hostname))return;var k='vn-sid',s=localStorage.getItem(k);if(!s){s=(crypto.randomUUID?crypto.randomUUID():String(Math.random()).slice(2)+Date.now()).replace(/-/g,'').slice(0,32);localStorage.setItem(k,s)}var u=navigator.userAgent,q=new URLSearchParams(location.search),r='';try{r=document.referrer?new URL(document.referrer).hostname:''}catch(e){}if(r===location.hostname)r='';r=q.get('utm_source')||(/Instagram/.test(u)?'ig':'')||r;try{if(r&&!localStorage.getItem('vn-ref'))localStorage.setItem('vn-ref',r)}catch(e){}var d=(/Mobi|iPhone|Android/.test(u)?'모바일':'PC')+' · '+(/iPhone|iPad/.test(u)?'iOS':/Android/.test(u)?'Android':/Mac/.test(u)?'Mac':/Windows/.test(u)?'Windows':'기타');fetch('${URL0}/rest/v1/events',{method:'POST',headers:{apikey:'${KEY}',Authorization:'Bearer ${KEY}','Content-Type':'application/json',Prefer:'return=minimal'},body:JSON.stringify({kind:'visit',sid:s,path:${JSON.stringify(p)},ref:r.slice(0,300),device:d}),keepalive:true})}catch(e){}})();</script>`;

function head({ title, desc, url, ld }) {
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(desc)}"><link rel="canonical" href="${url}">
<meta property="og:type" content="article"><meta property="og:site_name" content="밸류노트 ValueNote"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(desc)}"><meta property="og:url" content="${url}"><meta property="og:image" content="${SITE}/og.png"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="/favicon-64.png?v=4"><meta name="theme-color" content="#0E1A2B"><link rel="preload" href="/fonts/SUIT-Variable.woff2" as="font" type="font/woff2" crossorigin><link rel="stylesheet" href="/c/c.css">
${ld ? `<script type="application/ld+json">${JSON.stringify(ld)}</script>` : ''}</head><body>
<header class="top"><div class="in"><a class="brand" href="/">Value<i>Note</i></a><a class="go" href="/?utm_source=c">밸류노트 열기</a></div></header>`;
}
const FOOT = (date) => `<footer>공개 재무 자료(Yahoo Finance 연간 재무, 네이버 증권)로 매일 자동 계산한 결과입니다. 데이터 기준 ${esc(date)}. 투자 판단의 참고 자료이며 특정 종목의 매수·매도를 권하지 않습니다. © 밸류노트</footer>`;

function companyPage(x, peers, date) {
  const { r, sc } = x, g = grpOf(r.m), cur = r.cur || 'KRW', f = r.fin || {};
  const url = `${SITE}/c/${x.slug}`;
  const code = r.code || r.t;
  const pens = (sc.flags || []).filter((fl) => !WARN_FLAGS.has(fl)), warns = (sc.flags || []).filter((fl) => WARN_FLAGS.has(fl));
  const b = sc.b;
  const title = `${r.n} 가치투자 점수 ${isNum(b) ? b + '점' : ''}·적정 가격 | 밸류노트`;
  const desc = `${r.n}(${code}) 밸류노트 점수 ${isNum(b) ? b + '점' : '계산 불가'}, 숫자 품질 ${sc.q ?? '–'}점, 저평가 ${sc.v ?? '–'}점.` +
    (isNum(sc.iv) ? ` 현재가 ${money(r.px, cur)}, 적정 가격 ${money(sc.iv, cur)}.` : '') + ` 그레이엄·버핏 기준으로 ${MKT[g]} 기업 600여 곳과 비교합니다.`;
  const sum = summary(r, sc);
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
  const ld = { '@context': 'https://schema.org', '@type': 'BreadcrumbList', itemListElement: [
    { '@type': 'ListItem', position: 1, name: '밸류노트', item: SITE + '/' },
    { '@type': 'ListItem', position: 2, name: '기업 점수', item: SITE + '/c/' },
    { '@type': 'ListItem', position: 3, name: r.n, item: url }] };
  const appLink = `/?co=${encodeURIComponent(code)}&q=${encodeURIComponent(r.n)}&utm_source=c`;
  return head({ title, desc, url, ld }) + `<main>
<div class="crumb"><a href="/c/">기업 점수</a> › <a href="/c/#${g}">${MKT[g]}</a> › ${esc(r.n)}</div>
<section class="card hero"><h1>${esc(r.n)}</h1><div class="sub">${esc(code)} · ${MKT[g]}${r.en ? ' · ' + esc(r.en) : ''}${r.ind ? ' · ' + esc(r.ind) : ''}</div>
<div class="score"><b>${isNum(b) ? b : '–'}</b><span>버핏 근접도 (100점 만점, 70점 이상이 기준)</span></div>
<div class="bars"><div><div class="lab">숫자 품질</div><div class="val">${sc.q ?? '–'}점</div><div class="bar"><i style="width:${sc.q || 0}%"></i></div></div>
<div><div class="lab">저평가</div><div class="val">${sc.v ?? '–'}점</div><div class="bar"><i style="width:${sc.v || 0}%"></i></div></div></div></section>
${isNum(r.px) ? `<section class="card"><h2>가격</h2><div class="price"><div><div class="k">현재가</div><div class="v">${money(r.px, cur)}</div></div><div><div class="k">적정 가격</div><div class="v">${money(sc.iv, cur)}</div></div><div><div class="k">안전마진</div><div class="v ${isNum(sc.mos) ? (sc.mos >= 0 ? 'pos' : 'neg') : ''}">${isNum(sc.mos) ? (sc.mos > 0 ? '+' : '') + n0(sc.mos) + '%' : '–'}</div></div></div>
<p class="note" style="margin-top:10px">적정 가격은 과거 평균 이익·주주 이익과 자산 가치로 계산한 값입니다. ${r.fin_sector ? '금융업은 현금흐름 할인 대신 자산·이익 기준을 씁니다. ' : ''}미래를 보장하지 않습니다.</p></section>` : ''}
${sum.length ? `<section class="card"><h2>한 줄씩 읽기</h2>${sum.map((s) => `<p>${esc(s)}</p>`).join('')}</section>` : ''}
${pens.length || warns.length ? `<section class="card"><h2>감점·경고 신호</h2>${pens.map((fl) => `<div class="flag"><span class="pill p-pen">감점 −8</span><b>${esc(fl)}</b>${FLAG_HELP[fl] ? `<div class="h">${esc(FLAG_HELP[fl])}</div>` : ''}</div>`).join('')}${warns.map((fl) => `<div class="flag"><span class="pill ${fl === '중국 본토 규제' ? 'p-pen' : 'p-warn'}">${fl === '중국 본토 규제' ? '할인 −6' : '경고'}</span><b>${esc(fl)}</b>${FLAG_HELP[fl] ? `<div class="h">${esc(FLAG_HELP[fl])}</div>` : ''}</div>`).join('')}</section>` : ''}
${rowsM.length ? `<section class="card"><h2>핵심 숫자</h2><table>${rowsM.map((m) => `<tr><td>${m[0]}${m[2] ? `<div class="note">${m[2]}</div>` : ''}</td><td class="n">${m[1]}</td></tr>`).join('')}</table></section>` : ''}
<a class="cta" href="${appLink}">밸류노트에서 ${esc(r.n)} 자세히 보기<small>적정 가격 알림 · 내 포트폴리오 점수 · 멍거의 질문 체크</small></a>
${peers.length ? `<section class="card peers"><h2>같은 업종의 다른 회사</h2>${peers.map((p) => `<a href="/c/${p.slug}"><span>${esc(p.r.n)} <span class="note">${MKT[grpOf(p.r.m)]}</span></span><b>${p.sc.b ?? '–'}점</b></a>`).join('')}</section>` : ''}
</main>${FOOT(date)}${TRACK('/c/' + x.slug)}</body></html>`;
}

function indexPage(all, date) {
  const url = `${SITE}/c/`;
  const by = Object.fromEntries(MKT_ORDER.map((m) => [m, all.filter((x) => grpOf(x.r.m) === m).sort((a, b) => (b.sc.b ?? -1) - (a.sc.b ?? -1))]));
  const title = `기업 점수 ${all.length}곳 · 그레이엄·버핏 기준 가치투자 순위 | 밸류노트`;
  const desc = `국내·미국·일본·홍콩·중국 ${all.length}개 기업을 같은 기준(숫자 품질·저평가·감점 신호)으로 매일 점수화했습니다. 회사를 눌러 적정 가격과 근거를 확인하세요.`;
  return head({ title, desc, url }) + `<main>
<h1>기업 점수 ${all.length}곳</h1><p class="sub">그레이엄·버핏·멍거의 기준을 숫자로 옮겨, 5개 시장의 기업을 같은 잣대로 매일 다시 계산합니다. 70점 이상이 기준입니다.</p>
<div class="mk">${MKT_ORDER.map((m) => `<a href="#${m}">${MKT[m]} ${by[m].length}</a>`).join('')}</div>
${MKT_ORDER.map((m) => `<section class="card list" id="${m}"><h2>${MKT[m]}</h2><table><tr><th>#</th><th>회사</th><th style="text-align:right">점수</th></tr>${by[m].map((x, i) => `<tr><td class="s">${i + 1}</td><td><a href="/c/${x.slug}">${esc(x.r.n)}</a><div class="s">${esc(x.r.ind || x.r.s || '')}</div></td><td class="n">${x.sc.b ?? '–'}</td></tr>`).join('')}</table></section>`).join('')}
<a class="cta" href="/?utm_source=c-index">내 종목 점수 확인하기<small>포트폴리오를 넣으면 같은 기준으로 채점합니다</small></a>
</main>${FOOT(date)}${TRACK('/c/')}</body></html>`;
}

const { meta, rows } = await load();
if (rows.length < 300) throw new Error('rows too few: ' + rows.length);
setSettings({});
const seen = new Set();
const all = rows.map((r) => ({ r, sc: scoreRow(r, null, 30), slug: slug(r) })).filter((x) => x.slug && !seen.has(x.slug) && seen.add(x.slug));
const date = meta.generatedAt || new Date().toISOString().slice(0, 10);
const dir = path.join(ROOT, 'c');
fs.rmSync(dir, { recursive: true, force: true });
fs.mkdirSync(dir, { recursive: true });
fs.writeFileSync(path.join(dir, 'c.css'), CSS);
for (const x of all) {
  const key = x.r.ind || x.r.s;
  const peers = all.filter((y) => y !== x && (y.r.ind || y.r.s) === key && isNum(y.sc.b)).sort((a, b) => b.sc.b - a.sc.b).slice(0, 6);
  fs.writeFileSync(path.join(dir, x.slug + '.html'), companyPage(x, peers, date));
}
fs.writeFileSync(path.join(dir, 'index.html'), indexPage(all, date));
const urls = [`${SITE}/`, `${SITE}/c/`, ...all.map((x) => `${SITE}/c/${x.slug}`)];
fs.writeFileSync(path.join(ROOT, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map((u) => `<url><loc>${u}</loc><lastmod>${date}</lastmod></url>`).join('\n')}\n</urlset>\n`);
fs.writeFileSync(path.join(ROOT, 'robots.txt'), `User-agent: *\nAllow: /\nDisallow: /admin\n\nSitemap: ${SITE}/sitemap.xml\n`);
console.log(`pages ${all.length} · date ${date}`);
