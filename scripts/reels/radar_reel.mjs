// 월요일 08:30 '이번 주 경제 레이더' 릴스 대본 (일요일 저녁 company-cards 워크플로가 실행, AI 없이 규칙으로)
// 자료: docs fx/radar (radar 함수가 매일 아침 갱신, 일정 upcoming은 주간 칼럼 작업이 갱신)
// 사용: node scripts/reels/radar_reel.mjs YYYY-MM-DD   (그 날 08:30 게시, 같은 시각 릴스가 있으면 건너뜀)
import fs from 'node:fs';
import path from 'node:path';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..');
const SPECS = path.join(ROOT, 'scripts', 'reels', 'specs');
const ymd = process.argv[2];
if (!/^\d{4}-\d\d-\d\d$/.test(ymd || '')) throw new Error('날짜(YYYY-MM-DD)가 필요합니다');
const when = `${ymd}T08:30:00+09:00`, id = 'W' + ymd.replace(/-/g, '').slice(2);
const taken = fs.readdirSync(SPECS).filter((f) => f.endsWith('.json') && f !== id + '.json').some((f) => { try { return JSON.parse(fs.readFileSync(path.join(SPECS, f), 'utf8')).scheduled_at === when; } catch (_) { return false; } });
if (taken) { console.log('이미 릴스 있음', when); process.exit(0); }
const cfg = fs.readFileSync(path.join(ROOT, 'config.js'), 'utf8');
const U = cfg.match(/SUPABASE_URL:\s*'([^']+)'/)[1], K = cfg.match(/SUPABASE_ANON_KEY:\s*'([^']+)'/)[1];
const d = (await (await fetch(`${U}/rest/v1/docs?collection=eq.fx&id=eq.radar&select=data`, { headers: { apikey: K, Authorization: 'Bearer ' + K } })).json())[0]?.data;
if (!d?.ind) throw new Error('레이더 자료 없음');
const NAME = { hy: '회사채 금리차', stress: '금융 스트레스', vix: '공포지수', curve: '장단기 금리차', rate: '미국 10년 금리', sahm: '실업률 신호', dollar: '달러 흐름', kospi: '코스피', spx: 'S&P 500', euro: '프랑스 국채 금리차' };
const LV = ['안정', '안정', '보통', '주의', '위험'];
const OV = ['안정', '대체로 안정', '주의', '경계', '위험'];
const all = Object.entries(d.ind).filter(([k, v]) => NAME[k] && typeof v.lv === 'number');
const on = all.filter(([, v]) => v.lv >= 3).sort((a, b) => b[1].lv - a[1].lv);
const calm = all.filter(([, v]) => v.lv <= 1);
const fmtV = (k, v) => k === 'kospi' || k === 'spx' ? `고점 대비 ${Math.round(v)}%` : k === 'vix' || k === 'dollar' ? `${(+v).toFixed(1)}` : k === 'sahm' || k === 'stress' ? `${(+v).toFixed(2)}` : k === 'curve' || k === 'euro' ? `${(+v).toFixed(2)}%p` : `${(+v).toFixed(2)}%`;
const josa = (w, a, b) => { const ch = String(w).trim().slice(-1), c = ch.charCodeAt(0) - 0xac00; if (c >= 0 && c <= 11171) return w + (c % 28 ? a : b); return w + ('013678'.includes(ch) ? a : b); };
const plainEv = (t) => t.replace(/한국은행 금통위 기준금리 결정|한국은행 금통위/, '한국은행 금리 결정').replace(/FOMC 금리 결정|FOMC/, '미국 금리 결정').replace(/ECB 통화정책회의 결과|ECB/, '유럽 금리 결정');
const DIG = ['영', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구'];
const nk = (n) => ['', '한', '두', '세', '네', '다섯', '여섯', '일곱', '여덟', '아홉', '열'][n] || String(n);
const day0 = Date.parse(ymd), wk = (d.upcoming || []).filter((e) => { const t = Date.parse(e.date); return t >= day0 && t < day0 + 7 * 864e5; }).slice(0, 3);
const md = (s) => `${+s.slice(5, 7)}/${+s.slice(8, 10)}`;
const ov = typeof d.overall === 'number' ? d.overall : 2;
const scenes = [{ type: 'hook', top: '이번 주 경제 레이더', num: { to: on.length, fmt: 'int', suffix: '개' }, tone: on.length >= 3 ? 'loss' : 'gold', label: `켜진 경고 신호 (${all.length}개 중)`,
  lines: [{ cap: ['이번 주 시장의 위험 신호,', '몇 개나 켜져 있을까요?'] }, { cap: [`${all.length}개 신호 중`, `${on.length}개가 경고 단계입니다`], say: `${all.length}개 신호 중, ${nk(on.length)} 개가 경고 단계입니다.` }] }];
if (on.length) scenes.push({ type: 'list', title: '경고가 켜진 신호', items: on.slice(0, 5).map(([k, v]) => `${NAME[k]} · ${LV[v.lv]} · ${fmtV(k, v.v)}`), say: on.slice(0, 5).map(([k]) => NAME[k]).join(', ') + '입니다.' });
if (calm.length) scenes.push({ type: 'statement', l1: '반대로', l2: `${josa(calm.map(([k]) => NAME[k]).slice(0, 2).join('·'), '은', '는')} 안정입니다`, tone: 'ivory', note: '신호 하나보다 여러 신호를 함께 봐야 합니다',
  say: `반대로, ${josa(calm.map(([k]) => NAME[k]).slice(0, 2).join(', '), '은', '는')} 안정입니다.` });
if (wk.length) scenes.push({ type: 'list', title: '이번 주 관심 일정', items: wk.map((e) => `${md(e.date)} ${plainEv(e.event).slice(0, 18)}`), say: '이번 주 관심 일정은, ' + wk.map((e) => `${+e.date.slice(8, 10)}일 ${plainEv(e.event)}`).join(', ') + '입니다.' });
scenes.push({ type: 'cta', l1: '매일 바뀌는 신호는', l2: '경제 레이더에서', say: '매일 바뀌는 위험 신호는, 밸류노트 경제 레이더에서 확인하세요.' });
const caption = `이번 주 밸류노트 경제 레이더 종합 단계는 '${OV[ov] || '보통'}'입니다. ${all.length}개 신호 중 ${on.length}개가 경고 단계입니다.\n\n`
  + (on.length ? on.map(([k, v]) => `· ${NAME[k]} (${LV[v.lv]}, ${fmtV(k, v.v)}): ${v.why}`).join('\n') + '\n\n' : '')
  + (calm.length ? `안정 단계: ${calm.map(([k]) => NAME[k]).join(', ')}\n\n` : '')
  + (d.outlook ? String(d.outlook).trim() + '\n\n' : '')
  + (wk.length ? '이번 주 관심 일정\n' + wk.map((e) => `· ${md(e.date)} ${e.event}: ${e.why}`).join('\n') + '\n\n' : '')
  + '경제 레이더는 과거 위기(닷컴 버블, 금융위기, 유럽 재정위기, 코로나, 2022년 금리 인상) 때의 수치와 비교해 지금 위치를 신호등으로 보여 줍니다. 신호는 위험을 미리 살피는 도구이며 시장을 예측하지 않습니다.';
fs.writeFileSync(path.join(SPECS, id + '.json'), JSON.stringify({ id, scheduled_at: when, threads_tag: '경제', title: `이번 주 경제 레이더 · 경고 ${on.length}개`, mood: on.length >= 3 ? 'tense' : 'calm', scenes, hashtags: ['경제레이더', '금리', '주식시장', '경제공부', '밸류노트'], caption }, null, 1));
console.log(JSON.stringify({ id, on: on.map(([k]) => k), wk: wk.length }));
