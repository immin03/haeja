// 네이버 블로그·SNS용 이미지 키트 (1080×1080 PNG, 밸류노트 네이비·골드)
// 준비:  npm i --no-save --no-package-lock satori@0.10.14 @resvg/resvg-js@2.6.2 pretendard@1.3.9
// 사용:  node scripts/blog/kit.mjs <출력폴더> <작업.json>
//   작업.json = [{ "file": "01.png", "kind": "...", ...옵션 }, ...]
// kind 목록
//   cover    { eyebrow, title, sub, date }                       글 첫 장(제목 카드)
//   company  { slug }                                            기업 밸류노트 점수 카드 (예: "000270-ks")
//   price    { slug, date? }                                    지금 주가 · 적정 주가 · 적정 매수가 비교
//   metrics  { slug }                                            핵심 재무 숫자 표 (뜻 풀이 포함)
//   market   { market: "KR"|"US"|"JP"|"HK"|"CN" }                시장별 저평가 기업 수 + 4~8위 (1~3위는 사이트에서)
//   stats    { title, items:[{label, value, note?, tone?:"up"|"down"|"gold"}] }  숫자 2~4개
//   compare  { title, l:{label, value}, r:{label, value}, note } 두 숫자 비교
//   list     { title, items:[문장, ...] }                         요점 3~5개
//   quote    { quote, who, src }                                 거장 인용 (실제 출처가 있는 말만)
//   banner   { hook, sub, button }                               글 끝 밸류노트 배너 (1080×560, 링크를 걸어 쓴다)
//   photocover { photo, eyebrow, title, date }                   실사 사진 표지 (photo = 사진 파일 경로, 1080×1080). 2026-10-19부터 표지는 이것을 쓴다
//   photo    { photo, w?, h? }                                   실사 사진을 그대로 다듬어 저장 (기본 1280×720 JPG 복사는 cp 로 해도 된다)
// 용어는 claude/glossary.md 기준: 밸류노트 점수, 재무 점수, 가격 점수, 적정 주가, 적정 매수가, 저평가/고평가.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { scoreRow, setSettings, WARN_FLAGS } from '../../supabase/functions/watch-select/scoring.js';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const req = createRequire(path.join(ROOT, 'package.json'));
const _sm = await import(req.resolve('satori'));
const satori = typeof _sm.default === 'function' ? _sm.default : (_sm.default?.default || _sm.satori);
const { Resvg } = req('@resvg/resvg-js');
const FONT_DIR = path.join(path.dirname(req.resolve('pretendard/package.json')), 'dist/web/static/woff-subset');
const fonts = [['Medium', 500], ['Bold', 700], ['ExtraBold', 800], ['Black', 900]].map(([w, n]) => ({ name: 'P', data: fs.readFileSync(path.join(FONT_DIR, `Pretendard-${w}.subset.woff`)), weight: n, style: 'normal' }));
// 2026-10-23 확정 로고: Montserrat ExtraBold 'Value'+'Note'(아이보리 베이지), 얇은 금색 줄, 가운데 '밸류노트' (scripts/brand.py와 같은 모양)
fonts.push({ name: 'M', data: fs.readFileSync(new URL('../reels/fonts/Montserrat-ExtraBold.ttf', import.meta.url)), weight: 800, style: 'normal' });
const VNL = (size, st = {}) => h('div', { flexDirection: 'column', alignItems: 'center', ...st },
  h('div', { fontFamily: 'M', fontSize: size, fontWeight: 800, letterSpacing: -0.3, color: '#FFFFFF', lineHeight: 1, paddingBottom: Math.round(size * .2), borderBottom: '1.5px solid #D8C294' }, 'Value', h('span', { color: '#EADBB9' }, 'Note')),
  h('div', { fontFamily: 'P', fontSize: Math.round(size * .5), fontWeight: 700, letterSpacing: Math.round(size * .11), paddingLeft: Math.round(size * .11), marginTop: Math.round(size * .3), color: '#EADBB9', lineHeight: 1 }, '밸류노트'));

const SITE = 'https://www.valuenote.co.kr';
const C = { navy: '#0E1A2B', navy2: '#1A2C46', ink: '#F3EEE3', mute: '#AEB8C8', dim: '#8E9AAD', gold: '#EADBB9', gold2: '#C9AF7A', up: '#7FD3A8', down: '#FF9BAC', line: 'rgba(255,255,255,.12)' };
const MKT = { KR: '국내', US: '미국', JP: '일본', HK: '홍콩', CN: '중국 A' };
const MKT_LONG = { KR: '국내 주식', US: '미국 주식', JP: '일본 주식', HK: '홍콩 주식', CN: '중국 A주' };
const isNum = (v) => typeof v === 'number' && isFinite(v);
const n0 = (v, d = 0) => (isNum(v) ? v.toLocaleString('ko-KR', { maximumFractionDigits: d, minimumFractionDigits: d }) : '–');
function money(v, cur) {
  if (!isNum(v)) return '–';
  if (cur === 'KRW') return n0(v) + '원';
  if (cur === 'JPY') return n0(v) + '엔';
  if (cur === 'CNY') return n0(v, 2) + '위안';
  if (cur === 'HKD') return 'HK$' + n0(v, 2);
  return '$' + n0(v, 2);
}
const h = (type, style, ...children) => ({ type, props: { style: { display: 'flex', ...style }, children: children.flat().filter((c) => c !== null && c !== undefined && c !== false && c !== '') } });
const t = (text, style) => h('div', style, String(text));

// 공통 틀: 위 로고, 아래 출처 줄
function frame(body, foot = '') {
  return h('div', { width: 1080, height: 1080, flexDirection: 'column', justifyContent: 'space-between', padding: '64px 72px', background: `linear-gradient(155deg,${C.navy2} 0%,${C.navy} 58%,#0A1322 100%)`, color: C.ink, fontFamily: 'P' },
    h('div', { justifyContent: 'space-between', alignItems: 'center' },
      VNL(36),
      h('div', { width: 64, height: 4, borderRadius: 4, background: C.gold2 })),
    h('div', { flexDirection: 'column', flexGrow: 1, justifyContent: 'center' }, body),
    h('div', { justifyContent: 'space-between', alignItems: 'flex-end', fontSize: 22, color: C.dim, fontWeight: 700 },
      t(foot || '투자 교육용 정보 · 매수·매도 권유가 아닙니다', {}), t('valuenote.co.kr', {})));
}
// 줄바꿈(\n)이 있으면 줄마다 따로 그린다 (satori가 \n을 공백처럼 다뤄 어색하게 끊기는 것을 막음)
const title = (s, size = 54) => String(s).includes('\n')
  ? h('div', { flexDirection: 'column', fontSize: size, fontWeight: 900, letterSpacing: -1.5, lineHeight: 1.22 }, String(s).split('\n').map((l) => h('div', { wordBreak: 'keep-all' }, l)))
  : h('div', { fontSize: size, fontWeight: 900, letterSpacing: -1.5, lineHeight: 1.22, wordBreak: 'keep-all', whiteSpace: 'pre-wrap' }, s);
const eyebrow = (s) => t(s, { fontSize: 28, color: C.gold, fontWeight: 800, marginBottom: 22 });

// ── 데이터 (기업 카드용) ─────────────────────────────
let DATA = null;
async function data() {
  if (DATA) return DATA;
  const cfg = fs.readFileSync(path.join(ROOT, 'config.js'), 'utf8');
  const U = cfg.match(/SUPABASE_URL:\s*'([^']+)'/)[1], K = cfg.match(/SUPABASE_ANON_KEY:\s*'([^']+)'/)[1];
  const r = await fetch(`${U}/rest/v1/docs?collection=eq.screen&select=id,data`, { headers: { apikey: K, Authorization: 'Bearer ' + K } });
  const docs = await r.json();
  const rows = docs.filter((d) => d.id.startsWith('chunk-')).flatMap((d) => d.data?.rows || []);
  const sj = await (await fetch(`${SITE}/c/scores.json`)).json();
  setSettings({});
  const slug = (x) => String(x.t || x.code).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const by = {};
  for (const row of rows) { const s = slug(row); if (!by[s]) by[s] = { row, sc: scoreRow(row, null, 30), card: sj.c[s] }; }
  DATA = { by, date: sj.date, scores: sj.c };
  return DATA;
}
async function company(slug) {
  const d = await data(); const x = d.by[slug];
  if (!x || !x.card) throw new Error('기업을 찾을 수 없음: ' + slug);
  return { ...x, date: d.date };
}

// ── 템플릿 ─────────────────────────────────────────
const dataUri = (f) => 'data:image/jpeg;base64,' + fs.readFileSync(path.resolve(f)).toString('base64');
const T = {
  // 실사 사진 표지: 사진을 꽉 채우고 아래쪽만 어둡게 깔아 제목을 올린다 (카드 느낌을 줄이고 블로그 사진처럼 보이게)
  photocover: (o) => h('div', { width: 1080, height: 1080, position: 'relative', fontFamily: 'P', color: '#FFFFFF', background: C.navy },
    { type: 'img', props: { src: dataUri(o.photo), width: 1080, height: 1080, style: { position: 'absolute', left: 0, top: 0, width: 1080, height: 1080, objectFit: 'cover' } } },
    h('div', { position: 'absolute', left: 0, top: 0, width: 1080, height: 1080, background: 'linear-gradient(180deg,rgba(10,19,34,.10) 0%,rgba(10,19,34,.05) 40%,rgba(10,19,34,.78) 72%,rgba(10,19,34,.92) 100%)' }),
    VNL(34, { position: 'absolute', left: 64, top: 56, textShadow: '0 2px 8px rgba(0,0,0,.55)' }),
    h('div', { position: 'absolute', left: 64, right: 64, bottom: 64, flexDirection: 'column' },
      o.eyebrow ? t(o.eyebrow, { fontSize: 28, color: C.gold, fontWeight: 800, marginBottom: 18 }) : null,
      title(o.title, o.title.length > 28 ? 58 : 68),
      o.date ? t(o.date, { fontSize: 24, color: '#D6DCE6', marginTop: 22, fontWeight: 700 }) : null)),
  cover: (o) => frame(h('div', { flexDirection: 'column' },
    o.eyebrow ? eyebrow(o.eyebrow) : null, title(o.title, o.title.length > 28 ? 60 : 72),
    o.sub ? t(o.sub, { fontSize: 32, color: C.mute, marginTop: 28, lineHeight: 1.45, fontWeight: 500, wordBreak: 'keep-all' }) : null,
    h('div', { width: 120, height: 6, borderRadius: 6, background: C.gold2, marginTop: 44 }),
    o.date ? t(o.date, { fontSize: 26, color: C.dim, marginTop: 22, fontWeight: 700 }) : null), ' '),

  async company(o) {
    const { card, date } = await company(o.slug);
    const [name, b, q, v, m, mos] = card;
    const bar = (label, val) => h('div', { flexDirection: 'column', width: 420 },
      h('div', { justifyContent: 'space-between', fontSize: 30, color: C.mute, fontWeight: 700 }, label, h('span', { color: C.ink, fontWeight: 800 }, val == null ? '–' : `${val}점`)),
      h('div', { marginTop: 14, height: 16, borderRadius: 16, background: 'rgba(255,255,255,.14)', width: 420 }, h('div', { width: Math.round(4.2 * Math.max(0, Math.min(100, val ?? 0))), height: 16, borderRadius: 16, background: C.gold })));
    return frame(h('div', { flexDirection: 'column', alignItems: 'center' },
      t(`${MKT[m] || ''} · 밸류노트 점수`, { fontSize: 28, color: C.gold, fontWeight: 800 }),
      h('div', { fontSize: name.length > 12 ? 60 : 84, fontWeight: 900, marginTop: 14, letterSpacing: -2, textAlign: 'center', wordBreak: 'keep-all' }, name),
      h('div', { width: 330, height: 330, borderRadius: 330, border: `12px solid ${C.gold2}`, flexDirection: 'column', alignItems: 'center', justifyContent: 'center', marginTop: 36, background: 'rgba(234,219,185,.08)' },
        t(b == null ? '–' : b, { fontSize: 150, fontWeight: 900, color: C.gold, lineHeight: 1 }), t('/ 100점', { fontSize: 30, color: C.mute, fontWeight: 700, marginTop: 6 })),
      h('div', { gap: 60, marginTop: 44 }, bar('재무 점수', q), bar('가격 점수', v)),
      mos == null ? null : t(mos >= 0 ? `지금 주가는 적정 주가보다 ${mos}% 저평가돼 있습니다` : `지금 주가는 적정 주가보다 ${-mos}% 고평가돼 있습니다`, { fontSize: 36, fontWeight: 800, color: mos >= 0 ? C.up : C.down, marginTop: 40 })),
      `${date} 종가 기준 · 투자 교육용 정보`);
  },

  async price(o) {
    const { row, sc, card, date } = await company(o.slug);
    const cur = row.cur || 'KRW', px = row.px, iv = sc.iv, buy = isNum(iv) ? iv * 0.7 : null;
    const vals = [['지금 주가', px, C.ink], ['적정 주가', iv, C.gold], ['적정 매수가', buy, C.gold2]].filter((x) => isNum(x[1]));
    const max = Math.max(...vals.map((x) => x[1]));
    const ratio = isNum(px) && isNum(iv) && iv > 0 ? px / iv : null;
    const verdict = ratio == null ? '' : ratio >= 2 ? `지금 주가는 적정 주가의 ${n0(ratio, 1)}배로 고평가돼 있습니다` : sc.mos >= 0 ? `지금 주가는 적정 주가보다 ${n0(sc.mos)}% 저평가돼 있습니다` : `지금 주가는 적정 주가보다 ${n0(-sc.mos)}% 고평가돼 있습니다`;
    return frame(h('div', { flexDirection: 'column' },
      eyebrow(card[0]), title('지금 주가와 적정 주가', 60),
      h('div', { flexDirection: 'column', marginTop: 56, gap: 40 }, vals.map(([label, v, col]) => h('div', { flexDirection: 'column' },
        h('div', { justifyContent: 'space-between', fontSize: 32, fontWeight: 700, color: C.mute }, label, h('span', { color: col, fontWeight: 900, fontSize: 38 }, money(v, cur))),
        h('div', { marginTop: 14, height: 34, borderRadius: 10, background: 'rgba(255,255,255,.08)', width: 936 }, h('div', { width: Math.max(8, Math.round(936 * v / max)), height: 34, borderRadius: 10, background: col, opacity: label === '지금 주가' ? 0.85 : 1 }))))),
      verdict ? t(verdict, { fontSize: 38, fontWeight: 900, marginTop: 56, color: ratio != null && ratio <= 1 ? C.up : C.down }) : null,
      t('적정 매수가는 적정 주가의 70%입니다. 계산이 틀려도 버틸 여유(안전마진)를 30% 두는 그레이엄의 원칙입니다.', { fontSize: 26, color: C.dim, marginTop: 22, lineHeight: 1.5, fontWeight: 500, wordBreak: 'keep-all' })),
      `${o.date || date} 종가 기준 · 공식에 따른 추정치이며 미래 주가를 보장하지 않습니다`);
  },

  async metrics(o) {
    const { row, sc, card, date } = await company(o.slug);
    const f = row.fin || {};
    const rows = [
      ['5년 평균 ROE', isNum(f.roeAvg) ? n0(f.roeAvg, 1) + '%' : null, '주주 돈 100원으로 1년에 번 이익'],
      ['PER', isNum(sc.per) ? n0(sc.per, 1) + '배' : null, '주가가 1년 이익의 몇 배인지'],
      ['PBR', isNum(sc.pbr) ? n0(sc.pbr, 2) + '배' : null, '주가가 순자산의 몇 배인지'],
      ['순이익률', !row.fin_sector && isNum(f.npm) ? n0(f.npm, 1) + '%' : null, '매출 100원 중 남는 이익'],
      ['현금 전환율', !row.fin_sector && isNum(f.fcfConv) ? n0(f.fcfConv) + '%' : null, '이익 중 실제 현금으로 들어온 비율'],
      ['장기부채 ÷ 순이익', !row.fin_sector && isNum(f.ltdNi) ? n0(f.ltdNi, 1) + '배' : null, '이익으로 빚을 갚는 데 걸리는 해'],
      ['적자 연도', isNum(f.lossYears) ? `${f.lossYears}년 / ${row.yrs || 5}년` : null, '최근 몇 해 중 손실을 낸 해'],
    ].filter((x) => x[1] != null).slice(0, 5);
    return frame(h('div', { flexDirection: 'column' },
      eyebrow(card[0]), title('숫자로 본 회사', 56),
      h('div', { flexDirection: 'column', marginTop: 30 }, rows.map(([k, v, note], i) => h('div', { justifyContent: 'space-between', alignItems: 'center', padding: '18px 0', borderTop: i ? `2px solid ${C.line}` : 'none' },
        h('div', { flexDirection: 'column' }, t(k, { fontSize: 34, fontWeight: 800 }), t(note, { fontSize: 24, color: C.dim, marginTop: 6, fontWeight: 500 })),
        t(v, { fontSize: 42, fontWeight: 900, color: C.gold }))))),
      `${date} 기준 · 공개 재무 자료로 계산`);
  },

  async market(o) {
    const d = await data();
    const m = o.market;
    const list = Object.entries(d.by).filter(([, x]) => x.card && x.card[4] === m);
    const bar = list.filter(([, x]) => isNum(x.sc.mos) && x.sc.mos >= 30 && isNum(x.sc.q) && x.sc.q >= 60 && !(x.sc.flags || []).some((fl) => !WARN_FLAGS.has(fl))).sort((a, b) => b[1].sc.mos - a[1].sc.mos);
    const show = bar.slice(3, 8);
    return frame(h('div', { flexDirection: 'column' },
      eyebrow(`${MKT_LONG[m]} ${list.length}곳 중`), title(`적정 주가보다 30% 이상 저평가된 좋은 회사는 ${bar.length}곳입니다`, 52),
      t('재무 점수 60점 이상이면서 지금 주가가 적정 주가보다 30% 이상 낮은 회사입니다.', { fontSize: 26, color: C.dim, marginTop: 18, fontWeight: 500, wordBreak: 'keep-all', lineHeight: 1.45 }),
      h('div', { flexDirection: 'column', marginTop: 34 },
        h('div', { justifyContent: 'space-between', padding: '16px 0', fontSize: 30, fontWeight: 800, color: C.gold }, t('1~3위', {}), t('밸류노트에서 볼 수 있습니다', {})),
        show.map(([, x], i) => h('div', { justifyContent: 'space-between', alignItems: 'center', padding: '16px 0', borderTop: `2px solid ${C.line}` },
          h('div', { alignItems: 'baseline' }, t(`${i + 4}`, { fontSize: 30, color: C.dim, width: 56, fontWeight: 800 }), t(x.card[0], { fontSize: 34, fontWeight: 800 })),
          t(`${n0(x.sc.mos)}% 저평가`, { fontSize: 32, fontWeight: 900, color: C.up }))))),
      `${d.date} 종가 기준 · 숫자로 거른 목록이며 매수 권유가 아닙니다`);
  },

  stats: (o) => frame(h('div', { flexDirection: 'column' },
    o.eyebrow ? eyebrow(o.eyebrow) : null, title(o.title, 56),
    h('div', { flexWrap: 'wrap', gap: 28, marginTop: 48 }, o.items.slice(0, 4).map((it) => h('div', { flexDirection: 'column', width: o.items.length === 1 ? 936 : 454, padding: '30px 32px', borderRadius: 24, background: 'rgba(255,255,255,.06)', border: `2px solid ${C.line}` },
      t(it.label, { fontSize: 28, color: C.mute, fontWeight: 700 }),
      t(it.value, { fontSize: String(it.value).length > 9 ? 50 : 64, fontWeight: 900, whiteSpace: 'nowrap', marginTop: 10, color: it.tone === 'up' ? C.up : it.tone === 'down' ? C.down : C.gold }),
      it.note ? t(it.note, { fontSize: 24, color: C.dim, marginTop: 8, fontWeight: 500, wordBreak: 'keep-all', lineHeight: 1.4 }) : null)))), o.foot),

  compare: (o) => frame(h('div', { flexDirection: 'column' },
    o.eyebrow ? eyebrow(o.eyebrow) : null, title(o.title, 56),
    h('div', { gap: 28, marginTop: 56 }, [o.l, o.r].map((x, i) => h('div', { flexDirection: 'column', width: 454, padding: '40px 32px', borderRadius: 24, background: i ? 'rgba(234,219,185,.10)' : 'rgba(255,255,255,.06)', border: `2px solid ${i ? C.gold2 : C.line}`, alignItems: 'center' },
      t(x.label, { fontSize: 30, color: C.mute, fontWeight: 700, textAlign: 'center' }), t(x.value, { fontSize: 70, fontWeight: 900, marginTop: 16, color: i ? C.gold : C.ink })))),
    o.note ? t(o.note, { fontSize: 32, fontWeight: 700, marginTop: 44, lineHeight: 1.45, wordBreak: 'keep-all' }) : null), o.foot),

  list: (o) => frame(h('div', { flexDirection: 'column' },
    o.eyebrow ? eyebrow(o.eyebrow) : null, title(o.title, 56),
    h('div', { flexDirection: 'column', marginTop: 44, gap: 26 }, o.items.slice(0, 5).map((s, i) => h('div', { alignItems: 'flex-start' },
      h('div', { width: 54, height: 54, borderRadius: 54, background: C.gold2, color: '#FFFFFF', fontSize: 28, fontWeight: 900, alignItems: 'center', justifyContent: 'center', flexShrink: 0 }, String(i + 1)),
      t(s, { fontSize: 34, fontWeight: 700, marginLeft: 24, lineHeight: 1.45, wordBreak: 'keep-all', width: 850 }))))), o.foot),

  quote: (o) => frame(h('div', { flexDirection: 'column' },
    t('“', { fontSize: 180, color: C.gold2, fontWeight: 900, lineHeight: 0.8, height: 110 }),
    t(o.quote, { fontSize: o.quote.length > 70 ? 46 : 54, fontWeight: 800, lineHeight: 1.5, wordBreak: 'keep-all' }),
    h('div', { width: 90, height: 5, borderRadius: 5, background: C.gold2, marginTop: 44 }),
    t(o.who, { fontSize: 34, color: C.gold, fontWeight: 800, marginTop: 24 }),
    o.src ? t(o.src, { fontSize: 26, color: C.dim, marginTop: 8, fontWeight: 500 }) : null), o.foot),
};

// ── 실행 ───────────────────────────────────────────
// 글 끝 배너: 가로로 긴 카드. 크기는 실행부에서 1080×560
T.banner = (o) => h('div', { width: 1080, height: 560, flexDirection: 'column', justifyContent: 'space-between', padding: '52px 64px', background: `linear-gradient(120deg,${C.navy2} 0%,${C.navy} 55%,#0A1322 100%)`, color: C.ink, fontFamily: 'P', border: `6px solid ${C.gold2}` },
  h('div', {}, VNL(36)),
  h('div', { flexDirection: 'column' },
    String(o.hook).split('\n').map((ln) => t(ln, { fontSize: o.hook.length > 26 ? 50 : 58, fontWeight: 900, lineHeight: 1.25, wordBreak: 'keep-all', letterSpacing: -1.5 })),
    o.sub ? t(o.sub, { fontSize: 28, color: C.mute, marginTop: 16, fontWeight: 600, wordBreak: 'keep-all', lineHeight: 1.4 }) : null),
  h('div', { justifyContent: 'space-between', alignItems: 'center' },
    h('div', { background: `linear-gradient(90deg,${C.gold2},${C.gold})`, color: '#0A1322', fontSize: 34, fontWeight: 900, padding: '18px 36px', borderRadius: 999 }, o.button || '밸류노트에서 확인하기 ›'),
    t('valuenote.co.kr', { fontSize: 26, color: C.dim, fontWeight: 800 })));

const [outDir, jobFile] = process.argv.slice(2);
if (!outDir || !jobFile) { console.error('사용법: node scripts/blog/kit.mjs <출력폴더> <작업.json>'); process.exit(1); }
const jobs = JSON.parse(fs.readFileSync(jobFile, 'utf8'));
fs.mkdirSync(outDir, { recursive: true });
let bad = 0;
for (const j of jobs) {
  try {
    const fn = T[j.kind]; if (!fn && j.kind !== 'photo') throw new Error('없는 kind: ' + j.kind);
    if (j.kind === 'photo') { const { execFileSync } = await import('node:child_process'); const out = path.join(outDir, j.file); execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', j.photo, '-vf', `scale=${j.w || 1280}:${j.h || 720}:force_original_aspect_ratio=increase,crop=${j.w || 1280}:${j.h || 720}`, '-q:v', '3', out]); console.log('✓', out); continue; }
    const el = await fn(j);
    const H = j.kind === 'banner' ? 560 : 1080;
    const svg = await satori(el, { width: 1080, height: H, fonts });
    const png = new Resvg(svg, { fitTo: { mode: 'width', value: 1080 } }).render().asPng();
    const out = path.join(outDir, j.file);
    fs.writeFileSync(out, png);
    console.log('✓', out);
  } catch (e) { bad++; console.log('✗', j.file, e.message); }
}
process.exit(bad ? 1 : 0);
