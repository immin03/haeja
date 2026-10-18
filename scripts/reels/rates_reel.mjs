// 매주 수요일 19:30 '이번 주 금리' 릴스 대본 자동 생성 (AI 없이 규칙으로, company-cards 워크플로가 화요일 저녁에 실행)
// 자료: docs fx/rates (rates 함수가 매일 FRED·야후에서 받아 저장). 미국 10년 국채 금리를 중심으로, 한국 10년물·기준금리는 있으면 캡션에.
// 대본 규칙(README): 판정·추천 없이 사실만, 처음 보는 사람도 이해하게, 한 줄 = 한 문장, 20초 안팎.
// 실행: node scripts/reels/rates_reel.mjs YYYY-MM-DD   (그 날짜 19:30 게시, 같은 시각 릴스가 이미 있으면 건너뜀)
import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..');
const SPECS = path.join(ROOT, 'scripts', 'reels', 'specs');
const cfg = fs.readFileSync(path.join(ROOT, 'config.js'), 'utf8');
const U = cfg.match(/SUPABASE_URL:\s*'([^']+)'/)[1], K = cfg.match(/SUPABASE_ANON_KEY:\s*'([^']+)'/)[1];
const ymd = process.argv[2];
if (!/^\d{4}-\d\d-\d\d$/.test(ymd || '')) throw new Error('날짜(YYYY-MM-DD)가 필요합니다');
const when = process.env.REEL_AT || `${ymd}T19:30:00+09:00`;
const id = process.env.REEL_ID || 'M' + ymd.replace(/-/g, '').slice(2);

const taken = fs.readdirSync(SPECS).filter((f) => f.endsWith('.json') && f !== id + '.json')
  .some((f) => { try { return JSON.parse(fs.readFileSync(path.join(SPECS, f), 'utf8')).scheduled_at === when; } catch (_) { return false; } });
if (taken) { console.log('이미 릴스 있음', when); process.exit(0); }

const res = await fetch(`${U}/rest/v1/docs?collection=eq.fx&id=eq.rates&select=data`, { headers: { apikey: K, Authorization: 'Bearer ' + K } });
const d = (await res.json())[0]?.data;
if (!d?.auto?.US10Y || !d?.series?.US10Y?.daily?.length) throw new Error('금리 자료 없음');

const isNum = (v) => typeof v === 'number' && isFinite(v);
const f2 = (v) => (+v).toFixed(2);
const DIG = ['영', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구'];
function sino(n) { n = Math.round(n); if (n === 0) return '영'; const u = ['', '십', '백', '천']; let s = ''; String(n).split('').reverse().forEach((c, i) => { const k = +c; if (k) s = ((k === 1 && i > 0) ? '' : DIG[k]) + u[i] + s; }); return s; }
// 5.09 → "오 점 영 구", 1.04 → "일 점 영 사"
const sayNum = (v) => { const [a, b] = f2(Math.abs(v)).split('.'); const t = b.replace(/0$/, ''); return sino(+a) + (t ? ' 점 ' + t.split('').map((c) => DIG[+c]).join(' ') : ''); };

const us = d.auto.US10Y, v = us.v;
const daily = d.series.US10Y.daily;
// 지난 6개월 월말 값 + 최신값 (선 차트)
const byMonth = new Map(); for (const [dt, val] of [...(d.series.US10Y.monthly || []), ...daily]) byMonth.set(dt.slice(0, 7), [dt, val]);
const mons = [...byMonth.values()].slice(-7);
const xs = mons.map(([dt]) => `${+dt.slice(5, 7)}월`), vs = mons.map(([, val]) => val);
const y1 = isNum(us.chg1y) ? us.chg1y : null, m1 = isNum(us.chg1m) ? us.chg1m : null;
const up1y = y1 !== null && y1 > 0;

const scenes = [];
// 1) 첫 2초: 내 일로 묻는 질문 → 숫자로 답
scenes.push({ type: 'hook', top: '미국 10년 국채 금리', num: { to: v, fmt: 'pct', dec: 2, plus: false }, tone: up1y ? 'loss' : 'gold',
  label: y1 !== null ? `1년 전보다 ${y1 >= 0 ? '+' : '-'}${f2(Math.abs(y1))}%p` : '이번 주 금리',
  lines: [{ cap: ['금리가 오르면', '내 주식은 왜 떨어질까요?'] },
    { cap: ['미국 10년 국채 금리는', `지금 ${f2(v)}%입니다`], say: `미국 십 년 국채 금리는, 지금 ${sayNum(v)} 퍼센트입니다.` }] });
// 2) 흐름 + 쉬운 원리
scenes.push({ type: 'line', series: [{ name: '미국 10년 국채', v: vs }], x: xs, fmt: { fmt: 'pct', dec: 2, plus: false }, end: `${f2(v)}%`, end_tone: up1y ? 'loss' : 'gold',
  lines: [{ cap: ['안전한 국채가 이만큼 주면', '주식에 바라는 수익도 커집니다'] },
    { cap: ['그래서 같은 회사라도', '적정 주가는 낮아집니다'] }] });
// 3) 1년 변화 또는 다가오는 일정
const fresh = d.issuesAt && (Date.parse(ymd) - Date.parse(d.issuesAt)) / 864e5 <= 9;
const ev = fresh ? (d.issues || []).find((x) => /금통위|FOMC|연준|기준금리/.test(x.title || '')) : null;
const evDay = ev ? +(ev.title.match(/^(\d{1,2})일/) || [])[1] : NaN;
// 아직 오지 않은 일정만 (게시일보다 뒤, 2주 안)
if (ev && evDay > +ymd.slice(8) && evDay - +ymd.slice(8) <= 9 && ev.title.length <= 14) scenes.push({ type: 'statement', l1: '이번 주 관심 일정', l2: ev.title, tone: 'gold', note: '기준금리 결정은 대출·예금 금리와 주가에 함께 영향을 줍니다',
  say: `이번 주 관심 일정은, ${ev.title}입니다.` });
else if (y1 !== null) scenes.push({ type: 'statement', l1: '1년 전과 비교하면', l2: `${f2(Math.abs(y1))}%p ${y1 >= 0 ? '높아졌습니다' : '낮아졌습니다'}`, tone: 'gold', note: '퍼센트포인트(%p)는 금리 숫자 자체의 차이입니다',
  say: `1년 전과 비교하면, ${sayNum(y1)} 퍼센트포인트 ${y1 >= 0 ? '높아졌습니다' : '낮아졌습니다'}.` });
scenes.push({ type: 'cta', l1: '금리 흐름은', l2: '경제 레이더에서', say: '금리 흐름과 위험 신호는, 밸류노트 경제 레이더에서 확인하세요.' });

const kr = d.auto.KR10Y, upol = d.auto.USPOL;
const mm = (s) => `${+s.slice(5, 7)}월`;
const cap = `이번 주 미국 10년 국채 금리는 ${f2(v)}%입니다(${mm(us.date)} ${+us.date.slice(8)}일 기준).`
  + (m1 !== null ? ` 한 달 전보다 ${f2(Math.abs(m1))}%p ${m1 >= 0 ? '높고' : '낮고'},` : '')
  + (y1 !== null ? ` 1년 전보다 ${f2(Math.abs(y1))}%p ${y1 >= 0 ? '높습니다' : '낮습니다'}.` : '')
  + (upol && isNum(upol.v) ? ` 미국 기준금리(상단)는 ${f2(upol.v)}%입니다.` : '')
  + (kr && isNum(kr.v) ? ` 한국 10년 국채 금리는 ${mm(kr.date)} 평균 ${f2(kr.v)}%였습니다.` : '')
  + '\n\n금리가 주가에 중요한 이유는 간단합니다. 위험이 거의 없는 국채가 높은 이자를 주면, 투자자는 주식에도 그보다 높은 수익을 바랍니다. 그래서 회사가 앞으로 벌 돈의 지금 가치가 줄어들고, 같은 회사라도 적정 주가가 낮아집니다. 이익보다 먼 미래의 기대가 큰 성장주일수록 이 영향을 더 크게 받습니다.'
  + (ev ? `\n\n이번 주 관심 일정: ${ev.title}. ${ev.body || ''}` : '')
  + '\n\n금리 흐름과 위험 신호는 밸류노트 경제 레이더에서 매일 확인할 수 있습니다. 이 글은 금리 흐름에 대한 정보이며 특정 종목의 매수·매도 권유가 아닙니다.';

const spec = { id, scheduled_at: when, threads_tag: '경제', title: `이번 주 금리 · 미국 10년물 ${f2(v)}%`, mood: up1y ? 'tense' : 'calm', scenes,
  hashtags: ['금리', '미국국채', '국채금리', '주식공부', '밸류노트'], caption: cap };
fs.writeFileSync(path.join(SPECS, id + '.json'), JSON.stringify(spec, null, 1));
console.log(JSON.stringify({ id, title: spec.title }));
