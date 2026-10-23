// 밸류노트 인스타 카드뉴스 (1080×1350, 4:5) — 2026-10-23 운영자 결정: 하루 카드뉴스 2편
// 준비:  npm i --no-save --no-package-lock satori@0.10.14 @resvg/resvg-js@2.6.2 pretendard@1.3.9
// 사용:  node scripts/cards/cardnews.mjs scripts/cards/specs/<id>.json
//        → social/cards/<id>/01.jpg … 와 social/cards/<id>/post.json (게시 행에 들어갈 제목·캡션·해시태그)
// 장 종류 (spec.slides[].kind)
//   cover    { photo, eyebrow, l1, l2, sub }        실사 사진 표지. l2는 금색 큰 줄
//   text     { eyebrow, title, body:[문단], big?, small? }  설명 한 장 (big = 가운데 큰 숫자·문장, small = 아래 작은 각주)
//   criteria { eyebrow, title, rows:[{label, sub, value}], note }  기준 표 (번호 원 + 이름 + 값)
//   cards    { eyebrow, title, items:[{name, tag, rows:[[이름, 값]], badge}] }  회사 카드 (세로로 쌓음, 2~4개)
//   compare  { eyebrow, title, a, b, rows:[{name, a, b}], note }   두 숫자 막대 비교 (예: PER vs 평균 이익 PER)
//   table    { eyebrow, title, cols, rows, widths, hl, tags?, compact?, dimRows?, note }  표 (tags = 회사 이름 옆 업종, compact = 9~12줄, dimRows = 탈락 예시 줄 번호)
//   grid     { l1, l2, pill, cols, compact?, tiles:[{name, tag, big, bigLabel, chip, note, tone, num?}], notes }  한 장 요약 (기본 형식, 2026-10-23). compact = 타일 10~12개(4열)용 작은 글씨, num = 번호 원 글자(예: '✕')
//   end      { title, body, cta, checks?:[[이름, 설명]], checkHead?, checkNote? }  마지막 장 (체크표 선택) + 밸류노트 워드마크
// 공통: spec.foot = 출처·기준일 한 줄 (모든 장 아래), 고지문은 마지막 장에만 작게.
// 디자인 규칙: 글꼴 Pretendard, 원 안 숫자는 #FFFFFF, 밸류노트 로고는 brand/logo-dark.png (2026-10-23 확정). 인물 사진은 재사용 허락된 것만(README).
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const req = createRequire(path.join(ROOT, 'package.json'));
const _sm = await import(req.resolve('satori'));
const satori = typeof _sm.default === 'function' ? _sm.default : (_sm.default?.default || _sm.satori);
const { Resvg } = req('@resvg/resvg-js');
const FONT_DIR = path.join(path.dirname(req.resolve('pretendard/package.json')), 'dist/web/static/woff-subset');
const fonts = [['Medium', 500], ['Bold', 700], ['ExtraBold', 800], ['Black', 900]].map(([w, n]) => ({ name: 'P', data: fs.readFileSync(path.join(FONT_DIR, `Pretendard-${w}.subset.woff`)), weight: n, style: 'normal' }));

const W = 1080, H = 1350;
const C = { navy: '#0D1828', navy2: '#16253B', card: '#1B2B44', ink: '#F4EFE4', mute: '#B3BDCB', dim: '#8693A7', gold: '#E4CEA1', gold2: '#C9AF7A', up: '#7FD3A8', down: '#F08D8D', line: 'rgba(255,255,255,.12)' };
const h = (type, style, ...children) => ({ type, props: { style: { display: 'flex', ...style }, children: children.flat().filter((c) => c !== null && c !== undefined && c !== false && c !== '') } });
const t = (text, style) => h('div', { wordBreak: 'keep-all', ...style }, String(text));
const img = (src, style) => ({ type: 'img', props: { src, style } });
const uri = (f, mime = 'image/jpeg') => `data:${mime};base64,` + fs.readFileSync(f).toString('base64');

// 워드마크: 2026-10-23 확정 로고 (brand/logo-dark.png = scripts/brand.py로 만든 투명 로고)
const MARK = path.join(ROOT, 'brand', 'logo-dark.png');
const MARK_R = (() => { const b = fs.readFileSync(MARK); return b.readUInt32BE(20) / b.readUInt32BE(16); })();   // PNG 머리에서 높이÷너비
const mark = (w = 190) => img(uri(MARK, 'image/png'), { width: w, height: Math.round(w * MARK_R) });

function shell(spec, i, n, body, { light = false } = {}) {
  return h('div', { width: W, height: H, flexDirection: 'column', background: C.navy, color: C.ink, fontFamily: 'P', position: 'relative' },
    h('div', { position: 'absolute', left: 0, top: 0, width: W, height: H, background: 'radial-gradient(circle at 85% 0%, rgba(228,206,161,.10), rgba(13,24,40,0) 55%)' }),
    h('div', { justifyContent: 'space-between', alignItems: 'center', padding: '56px 64px 0 64px' },
      mark(), h('div', { fontSize: 26, fontWeight: 800, color: C.mute, background: 'rgba(255,255,255,.08)', borderRadius: 40, padding: '8px 22px' }, `${i}/${n}`)),
    h('div', { flexDirection: 'column', flexGrow: 1, padding: '40px 64px 0 64px' }, body),
    h('div', { flexDirection: 'column', padding: '0 64px 46px 64px' },
      h('div', { width: W - 128, height: 2, background: C.line, marginBottom: 18 }),
      t(spec.foot || '', { fontSize: 21, color: C.dim, fontWeight: 500, lineHeight: 1.45 })));
}
const eyebrow = (s) => s ? t(s, { fontSize: 30, color: C.gold, fontWeight: 800, marginBottom: 18 }) : null;
const bigTitle = (s, size = 66) => h('div', { flexDirection: 'column' }, String(s).split('\n').map((l) => t(l, { fontSize: size, fontWeight: 900, letterSpacing: -2, lineHeight: 1.2 })));
const para = (s, extra = {}) => t(s, { fontSize: 37, color: C.mute, fontWeight: 500, lineHeight: 1.55, marginTop: 26, ...extra });
const num = (k, bg = C.gold2) => h('div', { width: 64, height: 64, borderRadius: 64, background: bg, alignItems: 'center', justifyContent: 'center', fontSize: 30, fontWeight: 900, color: '#FFFFFF', flexShrink: 0 }, String(k));

const K = {
  cover: (s, sp, i, n) => h('div', { width: W, height: H, position: 'relative', fontFamily: 'P', color: '#FFFFFF', background: C.navy },
    img(uri(path.join(ROOT, 'scripts/blog/media/lib', s.photo)), { position: 'absolute', left: 0, top: 0, width: W, height: H, objectFit: 'cover' }),
    h('div', { position: 'absolute', left: 0, top: 0, width: W, height: H, background: 'linear-gradient(180deg,rgba(9,17,30,.55) 0%,rgba(9,17,30,.25) 30%,rgba(9,17,30,.80) 62%,rgba(9,17,30,.96) 100%)' }),
    h('div', { position: 'absolute', left: 64, top: 56, right: 64, justifyContent: 'space-between', alignItems: 'center' }, mark(210),
      h('div', { fontSize: 26, fontWeight: 800, color: '#FFFFFF', background: 'rgba(0,0,0,.35)', borderRadius: 40, padding: '8px 22px' }, `${i}/${n}`)),
    h('div', { position: 'absolute', left: 64, right: 64, bottom: 96, flexDirection: 'column' },
      eyebrow(s.eyebrow),
      t(s.l1, { fontSize: s.l1.length > 13 ? 84 : 100, fontWeight: 900, letterSpacing: -3, lineHeight: 1.12, textShadow: '0 4px 18px rgba(0,0,0,.5)' }),
      t(s.l2, { fontSize: s.l2.length > 13 ? 84 : 100, fontWeight: 900, letterSpacing: -3, lineHeight: 1.12, color: C.gold, textShadow: '0 4px 18px rgba(0,0,0,.5)' }),
      s.sub ? t(s.sub, { fontSize: 36, fontWeight: 700, color: '#E3E8EF', marginTop: 30, lineHeight: 1.4 }) : null)),

  text: (s, sp, i, n) => shell(sp, i, n, h('div', { flexDirection: 'column' },
    eyebrow(s.eyebrow), bigTitle(s.title, s.size || 66),
    s.big ? h('div', { marginTop: 44, padding: '34px 40px', borderRadius: 28, background: C.card, border: `2px solid ${C.gold2}`, flexDirection: 'column' },
      String(s.big).split('\n').map((l, k) => t(l, { fontSize: k ? 34 : 46, fontWeight: k ? 600 : 900, color: k ? C.mute : C.gold, lineHeight: 1.4, marginTop: k ? 10 : 0 }))) : null,
    (s.body || []).map((p) => para(p)),
    s.small ? t(s.small, { fontSize: 25, color: C.dim, fontWeight: 500, lineHeight: 1.45, marginTop: 30 }) : null)),

  criteria: (s, sp, i, n) => shell(sp, i, n, h('div', { flexDirection: 'column' },
    eyebrow(s.eyebrow), bigTitle(s.title, s.size || 62),
    h('div', { flexDirection: 'column', marginTop: s.rows.length > 4 ? 30 : 40, gap: s.rows.length > 4 ? 14 : 20 }, s.rows.map((r, k) => h('div', { alignItems: 'center', background: '#F4EFE4', borderRadius: 24, padding: s.rows.length > 4 ? '20px 30px' : '30px 32px', gap: 26 },
      num(k + 1, C.navy2),
      h('div', { flexDirection: 'column', flexGrow: 1, flexShrink: 1 },
        t(r.label, { fontSize: 40, fontWeight: 900, color: C.navy, letterSpacing: -1 }),
        r.sub ? t(r.sub, { fontSize: 27, fontWeight: 600, color: '#5B6678', marginTop: 6, lineHeight: 1.35 }) : null),
      r.value ? h('div', { flexShrink: 0, borderLeft: '2px solid #D9D1C1', paddingLeft: 26, minWidth: 190, justifyContent: 'flex-end' },
        t(r.value, { fontSize: 38, fontWeight: 900, color: '#1F7A55', letterSpacing: -1 })) : null))),
    s.note ? para(s.note, { fontSize: 28, marginTop: 30 }) : null)),

  cards: (s, sp, i, n) => shell(sp, i, n, h('div', { flexDirection: 'column' },
    eyebrow(s.eyebrow), bigTitle(s.title, s.size || 58),
    h('div', { flexDirection: 'column', marginTop: 34, gap: 26 }, s.items.map((it) => h('div', { flexDirection: 'column', background: C.card, borderRadius: 28, padding: '34px 36px', border: `1px solid ${C.line}` },
      h('div', { justifyContent: 'space-between', alignItems: 'center' },
        h('div', { alignItems: 'baseline', gap: 14 }, t(it.name, { fontSize: 50, fontWeight: 900, letterSpacing: -1 }), it.tag ? t(it.tag, { fontSize: 27, color: C.dim, fontWeight: 700 }) : null),
        it.badge ? h('div', { background: 'rgba(127,211,168,.16)', color: C.up, fontSize: 28, fontWeight: 900, borderRadius: 30, padding: '8px 20px' }, it.badge) : null),
      h('div', { marginTop: 24, justifyContent: 'space-between' }, it.rows.map(([k, v]) => h('div', { flexDirection: 'column', width: Math.floor((W - 128 - 72) / it.rows.length) },
        t(k, { fontSize: 26, color: C.dim, fontWeight: 700 }), t(v, { fontSize: 38, fontWeight: 900, color: C.ink, marginTop: 6, letterSpacing: -0.5 }))))))))),

  // 한 장 요약 그리드 (2026-10-23 운영자: "엄청 간단하고 직관적으로") — 밝은 바탕, 큰 제목, 타일마다 큰 숫자 하나
  // { l1, l2(강조색), l3?, pill, cols(2|3), tiles:[{name, tag, big, bigLabel, chip, note, tone:'red'|'green'|'navy'}], notes:[작은 주석] }
  grid: (s, sp, i, n) => {
    const P = { bg: '#FBF8F1', ink: '#0F1E36', red: '#D83030', green: '#16794D', gold: '#B89E6B', chip: '#FCE5B7', line: '#E6DECD' };
    const cols = s.cols || 3, gap = 18, tw = Math.floor((W - 72 - gap * (cols - 1)) / cols);
    const tone = (t) => t === 'green' ? P.green : t === 'navy' ? P.ink : P.red;
    const c = s.compact ? 0.78 : 1, z = (v) => Math.round(v * c);  // compact: 타일 10~12개용 작은 글씨
    const tile = (x, k) => h('div', { width: tw, flexDirection: 'column', background: '#FFFFFF', borderRadius: 20, padding: s.compact ? '18px 14px 16px 14px' : '26px 22px 24px 22px', border: `2px solid ${P.line}`, boxShadow: '0 4px 14px rgba(15,30,54,.08)' },
      h('div', { alignItems: 'center', gap: z(10) },
        h('div', { width: z(40), height: z(40), borderRadius: 10, background: tone(x.tone), color: '#FFFFFF', fontSize: z(24), fontWeight: 900, alignItems: 'center', justifyContent: 'center', flexShrink: 0 }, x.num || String(k + 1)),
        t(x.name, { fontSize: z(x.name.length > 7 ? 26 : x.name.length > 5 ? 31 : 36), fontWeight: 900, color: P.ink, letterSpacing: -1 })),
      x.tag ? t(x.tag, { fontSize: z(22), color: '#6B7484', fontWeight: 700, marginTop: z(8) }) : null,
      t(x.big, { fontSize: z(x.big.length > 9 ? 48 : 76), fontWeight: 900, color: tone(x.tone), letterSpacing: -2, marginTop: z(6), lineHeight: 1.1 }),
      x.bigLabel ? t(x.bigLabel, { fontSize: z(22), color: '#4A5363', fontWeight: 700, marginTop: 4, lineHeight: 1.3 }) : null,
      x.chip ? h('div', { marginTop: z(12), background: P.chip, borderRadius: 10, padding: '8px 10px', justifyContent: 'center' }, t(x.chip, { fontSize: z(x.chip.length > 16 ? 21 : 23), fontWeight: 900, color: P.ink, letterSpacing: -0.5 })) : null,
      x.note ? h('div', { flexDirection: 'column', marginTop: z(14) }, String(x.note).split('\n').map((l) => t(l, { fontSize: z(23), color: P.ink, fontWeight: 800, lineHeight: 1.4 }))) : null);
    const rows = []; for (let k = 0; k < s.tiles.length; k += cols) rows.push(s.tiles.slice(k, k + cols));
    return h('div', { width: W, height: H, flexDirection: 'column', background: P.bg, fontFamily: 'P', color: P.ink, padding: '40px 36px 30px 36px' },
      h('div', { justifyContent: 'space-between', alignItems: 'center' },
        h('div', { background: C.navy, borderRadius: 12, padding: '8px 14px' }, mark(150)),
        t(`${i}/${n}`, { fontSize: 22, fontWeight: 800, color: '#6B7484' })),
      h('div', { flexDirection: 'column', marginTop: 22 },
        t(s.l1, { fontSize: 82, fontWeight: 900, letterSpacing: -3, lineHeight: 1.08 }),
        t(s.l2, { fontSize: 82, fontWeight: 900, letterSpacing: -3, lineHeight: 1.08, color: P.red }),
        s.l3 ? t(s.l3, { fontSize: 82, fontWeight: 900, letterSpacing: -3, lineHeight: 1.08 }) : null),
      s.pill ? h('div', { alignSelf: 'flex-start', marginTop: 16, background: P.ink, color: '#FFFFFF', borderRadius: 40, padding: '10px 22px' }, t(s.pill, { fontSize: 25, fontWeight: 800 })) : null,
      h('div', { flexDirection: 'column', gap: s.compact ? 16 : 22, marginTop: s.compact ? 20 : 26 }, rows.map((r) => h('div', { gap }, r.map((x) => tile(x, s.tiles.indexOf(x)))))),
      h('div', { flexDirection: 'column', marginTop: 'auto', paddingTop: 14 }, (s.notes || []).map((x) => t(x, { fontSize: 19, color: '#5C6575', fontWeight: 600, lineHeight: 1.45 }))));
  },

  // 표: cols = [제목, ...], rows = [[이름, 값, ...]], widths = 각 칸 비율, hl = 강조할 칸 번호
  table: (s, sp, i, n) => {
    const tw = W - 128, ws = s.widths || s.cols.map(() => 1), sum = ws.reduce((a, b) => a + b, 0);
    const cz = s.compact ? 0.84 : 1;  // compact: 9~12줄용
    const cell = (v, k, head, dim) => t(v, { width: Math.floor(tw * ws[k] / sum), fontSize: Math.round((head ? 25 : (k === 0 ? 36 : 33)) * (head ? 1 : cz)), fontWeight: head ? 700 : 900, color: head ? C.dim : dim && k ? C.down : (k === s.hl ? C.up : C.ink), justifyContent: k ? 'flex-end' : 'flex-start', letterSpacing: -0.5 });
    const first = (v, j) => (s.tags && s.tags[j])
      ? h('div', { width: Math.floor(tw * ws[0] / sum), alignItems: 'baseline', gap: 10 }, t(v, { fontSize: Math.round(36 * cz), fontWeight: 900, color: C.ink, letterSpacing: -0.5 }), t(s.tags[j], { fontSize: Math.round(23 * cz), fontWeight: 600, color: C.dim }))
      : cell(v, 0, false);
    return shell(sp, i, n, h('div', { flexDirection: 'column' },
      eyebrow(s.eyebrow), bigTitle(s.title, s.size || 58),
      h('div', { flexDirection: 'column', marginTop: 34, background: C.card, borderRadius: 26, padding: '14px 28px', border: `1px solid ${C.line}` },
        h('div', { padding: '16px 8px', borderBottom: `2px solid ${C.line}` }, s.cols.map((c, k) => cell(c, k, true))),
        s.rows.map((r, j) => h('div', { padding: s.compact ? '13px 8px' : '20px 8px', alignItems: 'center', borderBottom: j < s.rows.length - 1 ? `1px solid ${C.line}` : 'none', ...((s.dimRows || []).includes(j) ? { background: 'rgba(240,141,141,.10)' } : {}) }, r.map((v, k) => k === 0 ? first(v, j) : cell(v, k, false, (s.dimRows || []).includes(j)))))),
      s.note ? para(s.note, { fontSize: s.compact ? 24 : 28, marginTop: s.compact ? 20 : 28 }) : null));
  },

  compare: (s, sp, i, n) => {
    const max = Math.max(...s.rows.flatMap((r) => [r.a, r.b]));
    const bar = (v, col, label) => h('div', { alignItems: 'center', gap: 16, marginTop: 10 },
      h('div', { width: Math.max(16, Math.round(640 * v / max)), height: 52, borderRadius: 12, background: col }),
      t(label, { fontSize: 40, fontWeight: 900, color: col }));
    return shell(sp, i, n, h('div', { flexDirection: 'column' },
      eyebrow(s.eyebrow), bigTitle(s.title, s.size || 58),
      h('div', { gap: 34, marginTop: 30 },
        h('div', { alignItems: 'center', gap: 12 }, h('div', { width: 26, height: 26, borderRadius: 6, background: C.mute }), t(s.a, { fontSize: 28, color: C.mute, fontWeight: 700 })),
        h('div', { alignItems: 'center', gap: 12 }, h('div', { width: 26, height: 26, borderRadius: 6, background: C.gold }), t(s.b, { fontSize: 28, color: C.gold, fontWeight: 700 }))),
      h('div', { flexDirection: 'column', marginTop: 40, gap: 46 }, s.rows.map((r) => h('div', { flexDirection: 'column' },
        t(r.name, { fontSize: 44, fontWeight: 900, marginBottom: 4 }),
        bar(r.a, C.mute, r.al || `${Number(r.a).toFixed(1)}배`), bar(r.b, C.gold, r.bl || `${Number(r.b).toFixed(1)}배`)))),
      s.note ? para(s.note, { fontSize: 32, marginTop: 44 }) : null));
  },

  end: (s, sp, i, n) => shell({ ...sp, foot: sp.disclaimer || '' }, i, n, h('div', { flexDirection: 'column', flexGrow: 1, justifyContent: 'center' },
    bigTitle(s.title, s.size || 64),
    s.checks ? h('div', { flexDirection: 'column', marginTop: 34, background: C.card, borderRadius: 26, padding: '26px 30px', border: `1px solid ${C.line}` },
      s.checkHead ? t(s.checkHead, { fontSize: 27, color: C.gold, fontWeight: 800, marginBottom: 12 }) : null,
      s.checks.map(([k, v], j) => h('div', { alignItems: 'center', gap: 20, marginTop: j ? 14 : 4 }, num(j + 1, C.gold2), h('div', { flexDirection: 'column', flexShrink: 1 }, t(k, { fontSize: 32, fontWeight: 900 }), t(v, { fontSize: 28, fontWeight: 600, color: C.mute, marginTop: 2 })))),
      s.checkNote ? t(s.checkNote, { fontSize: 23, color: C.dim, fontWeight: 500, lineHeight: 1.45, marginTop: 18 }) : null) : null,
    (s.body || []).map((p) => para(p, s.checks ? { fontSize: 32, marginTop: 24 } : {})),
    s.cta ? h('div', { marginTop: 54, alignSelf: 'flex-start', background: C.gold, color: C.navy, fontSize: 34, fontWeight: 900, borderRadius: 60, padding: '22px 40px' }, s.cta) : null,
    h('div', { marginTop: 60, alignItems: 'center', gap: 22 }, mark(260), t('@value.note.korea', { fontSize: 28, color: C.mute, fontWeight: 700 })))),
};

const specPath = process.argv[2];
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const out = path.join(ROOT, 'social', 'cards', spec.id);
fs.mkdirSync(out, { recursive: true });
const n = spec.slides.length;
for (let k = 0; k < n; k++) {
  const s = spec.slides[k];
  const node = K[s.kind](s, spec, k + 1, n);
  const svg = await satori(node, { width: W, height: H, fonts });
  const png = new Resvg(svg, { fitTo: { mode: 'width', value: W } }).render().asPng();
  const pngPath = path.join(out, `${String(k + 1).padStart(2, '0')}.png`);
  fs.writeFileSync(pngPath, png);
  execFileSync('python3', ['-c', `from PIL import Image; Image.open('${pngPath}').convert('RGB').save('${pngPath.replace(/\.png$/, '.jpg')}', quality=92)`]);
  fs.unlinkSync(pngPath);
}
const images = spec.slides.map((_, k) => `/social/cards/${spec.id}/${String(k + 1).padStart(2, '0')}.jpg`);
fs.writeFileSync(path.join(out, 'post.json'), JSON.stringify({ id: spec.id, title: spec.title, scheduled_at: spec.scheduled_at, caption: spec.caption, hashtags: spec.hashtags, threads_tag: spec.threads_tag || '주식공부', images }, null, 1));
console.log('ok', spec.id, n, 'slides →', out);
