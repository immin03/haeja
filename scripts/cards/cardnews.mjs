// 밸류노트 인스타 카드뉴스 (1080×1350, 4:5) — 2026-10-23 운영자 결정: 하루 카드뉴스 2편
// 준비:  npm i --no-save --no-package-lock satori@0.10.14 @resvg/resvg-js@2.6.2 pretendard@1.3.9
// 사용:  node scripts/cards/cardnews.mjs scripts/cards/specs/<id>.json
//        → social/cards/<id>/01.jpg … 와 social/cards/<id>/post.json (게시 행에 들어갈 제목·캡션·해시태그)
// 장 종류 (spec.slides[].kind)
//   cover    { photo, eyebrow, l1, l2, sub }        실사 사진 표지. l2는 금색 큰 줄
//   text     { eyebrow, title, body:[문단], big? }  설명 한 장 (big = 가운데 큰 숫자·문장)
//   criteria { eyebrow, title, rows:[{label, sub, value}], note }  기준 표 (번호 원 + 이름 + 값)
//   cards    { eyebrow, title, items:[{name, tag, rows:[[이름, 값]], badge}] }  회사 카드 (세로로 쌓음, 2~4개)
//   compare  { eyebrow, title, a, b, rows:[{name, a, b}], note }   두 숫자 막대 비교 (예: PER vs 평균 이익 PER)
//   end      { title, body, cta }                    마지막 장 (밸류노트 워드마크 + 팔로우 안내)
// 공통: spec.foot = 출처·기준일 한 줄 (모든 장 아래), 고지문은 마지막 장에만 작게.
// 디자인 규칙: 글꼴 Pretendard, 네이비·금색·아이보리, 원 안 아이콘·숫자는 #FFFFFF, 인물 사진·로고 이미지 없음, 로고는 사이트 og.png 워드마크를 잘라 쓴다.
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
const C = { navy: '#0D1828', navy2: '#16253B', card: '#1B2B44', ink: '#F4EFE4', mute: '#B3BDCB', dim: '#8693A7', gold: '#E4C78D', gold2: '#C99A50', up: '#7FD3A8', down: '#F0A397', line: 'rgba(255,255,255,.12)' };
const h = (type, style, ...children) => ({ type, props: { style: { display: 'flex', ...style }, children: children.flat().filter((c) => c !== null && c !== undefined && c !== false && c !== '') } });
const t = (text, style) => h('div', { wordBreak: 'keep-all', ...style }, String(text));
const img = (src, style) => ({ type: 'img', props: { src, style } });
const uri = (f, mime = 'image/jpeg') => `data:${mime};base64,` + fs.readFileSync(f).toString('base64');

// 워드마크: og.png 가운데 'ValueNote' 부분을 잘라 쓴다 (새로 그리지 않는다)
const MARK = path.join(ROOT, 'social', 'cards', '_mark.png');
if (!fs.existsSync(MARK)) {
  fs.mkdirSync(path.dirname(MARK), { recursive: true });
  // 어두운 바탕을 투명하게 바꿔 사진 위에서도 상자가 보이지 않게 한다
  execFileSync('python3', ['-c', `from PIL import Image
im = Image.open('${path.join(ROOT, 'og.png')}').convert('RGB').crop((278,175,922,305)); px = im.load(); out = Image.new('RGBA', im.size)
for y in range(im.size[1]):
    for x in range(im.size[0]):
        r, g, b = px[x, y]; a = max(0, min(255, int((max(r, g, b) - 48) * 1.9)))
        out.putpixel((x, y), (r, g, b, a))
out.save('${MARK}')`]);
}
const mark = (w = 190) => img(uri(MARK, 'image/png'), { width: w, height: Math.round(w * 130 / 644) });

function shell(spec, i, n, body, { light = false } = {}) {
  return h('div', { width: W, height: H, flexDirection: 'column', background: C.navy, color: C.ink, fontFamily: 'P', position: 'relative' },
    h('div', { position: 'absolute', left: 0, top: 0, width: W, height: H, background: 'radial-gradient(circle at 85% 0%, rgba(228,199,141,.10), rgba(13,24,40,0) 55%)' }),
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
    (s.body || []).map((p) => para(p)))),

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

  // 표: cols = [제목, ...], rows = [[이름, 값, ...]], widths = 각 칸 비율, hl = 강조할 칸 번호
  table: (s, sp, i, n) => {
    const tw = W - 128, ws = s.widths || s.cols.map(() => 1), sum = ws.reduce((a, b) => a + b, 0);
    const cell = (v, k, head) => t(v, { width: Math.floor(tw * ws[k] / sum), fontSize: head ? 25 : (k === 0 ? 36 : 33), fontWeight: head ? 700 : 900, color: head ? C.dim : (k === s.hl ? C.up : C.ink), justifyContent: k ? 'flex-end' : 'flex-start', letterSpacing: -0.5 });
    return shell(sp, i, n, h('div', { flexDirection: 'column' },
      eyebrow(s.eyebrow), bigTitle(s.title, s.size || 58),
      h('div', { flexDirection: 'column', marginTop: 34, background: C.card, borderRadius: 26, padding: '14px 28px', border: `1px solid ${C.line}` },
        h('div', { padding: '16px 8px', borderBottom: `2px solid ${C.line}` }, s.cols.map((c, k) => cell(c, k, true))),
        s.rows.map((r, j) => h('div', { padding: '20px 8px', alignItems: 'center', borderBottom: j < s.rows.length - 1 ? `1px solid ${C.line}` : 'none' }, r.map((v, k) => cell(v, k, false))))),
      s.note ? para(s.note, { fontSize: 28, marginTop: 28 }) : null));
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
    (s.body || []).map((p) => para(p)),
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
