// 밸류노트 카드뉴스 v2 시안 렌더러 (2026-11-05, 대표 검토용 — 통과 전에는 예약 작업이 쓰지 않는다)
// 새 형식 '한 장 총정리형': 표지(인물·질문) → 2장째에 저장용 총정리 표 → 핵심 숫자 3장 → 저장·공유 장
// 벤치마크 원리: economy.notes(한 장에 20개 리스트, 좋아요 1,032), money_zine('35개 기업 리스트', 836),
//               mijunow(2장째 번호 목차, 953·공유 134). 디자인은 밸류노트 네이비·아이보리 그대로.
// 사용: node scripts/cards/v2/render.mjs <spec.json> <out dir>
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../..');
const req = createRequire(path.join(ROOT, 'package.json'));
const _sm = await import(req.resolve('satori'));
const satori = typeof _sm.default === 'function' ? _sm.default : (_sm.default?.default || _sm.satori);
const { Resvg } = req('@resvg/resvg-js');
const FD = path.join(path.dirname(req.resolve('pretendard/package.json')), 'dist/web/static/woff');
const fonts = [['Medium', 500], ['SemiBold', 600], ['Bold', 700], ['ExtraBold', 800], ['Black', 900]]
  .map(([w, n]) => ({ name: 'P', data: fs.readFileSync(path.join(FD, `Pretendard-${w}.woff`)), weight: n, style: 'normal' }));

const W = 1080, H = 1350, PAD = 72;
const C = { navy: '#0D1828', navy2: '#13223A', card: '#1A2A44', card2: '#22355A', ink: '#F4EFE4', mute: '#B8C2D0', dim: '#7F8CA1', gold: '#EADBB9', gold2: '#C9AF7A', up: '#3DF5A0', down: '#FF4D6D', line: 'rgba(255,255,255,.10)' };
const h = (type, style, ...ch) => ({ type, props: { style: { display: 'flex', ...style }, children: ch.flat().filter((c) => c !== null && c !== undefined && c !== false && c !== '') } });
const t = (s, st) => h('div', { wordBreak: 'keep-all', ...st }, String(s));
const img = (src, st) => ({ type: 'img', props: { src, style: st } });
const uri = (f, m = 'image/jpeg') => `data:${m};base64,` + fs.readFileSync(f).toString('base64');
const LOGO = path.join(ROOT, 'brand/logo-dark.png');
const LR = (() => { const b = fs.readFileSync(LOGO); return b.readUInt32BE(20) / b.readUInt32BE(16); })();
const logo = (w = 170) => img(uri(LOGO, 'image/png'), { width: w, height: Math.round(w * LR) });
const PROFILE = path.join(ROOT, 'brand/profile-1080.png');

// 공통 틀: 위 로고 + 쪽수, 아래 출처 줄
const frame = (sp, i, n, body, { foot = true } = {}) => h('div', { width: W, height: H, flexDirection: 'column', background: C.navy, color: C.ink, fontFamily: 'P', position: 'relative' },
  h('div', { position: 'absolute', left: 0, top: 0, width: W, height: H, background: 'radial-gradient(circle at 90% 0%, rgba(234,219,185,.09), rgba(13,24,40,0) 50%)' }),
  h('div', { justifyContent: 'space-between', alignItems: 'center', padding: `56px ${PAD}px 0 ${PAD}px` }, logo(),
    t(`${i} / ${n}`, { fontSize: 24, fontWeight: 700, color: C.dim, letterSpacing: 1 })),
  h('div', { flexDirection: 'column', flexGrow: 1, padding: `36px ${PAD}px 0 ${PAD}px` }, body),
  foot ? h('div', { flexDirection: 'column', padding: `0 ${PAD}px 44px ${PAD}px` },
    h('div', { width: W - PAD * 2, height: 1, background: C.line, marginBottom: 16 }),
    t(sp.foot, { fontSize: 20, color: C.dim, fontWeight: 500, lineHeight: 1.45 })) : null);

const head = (kicker, title, size = 64) => h('div', { flexDirection: 'column' },
  kicker ? t(kicker, { fontSize: 28, color: C.gold2, fontWeight: 800, letterSpacing: 0.5, marginBottom: 14 }) : null,
  h('div', { flexDirection: 'column' }, String(title).split('\n').map((l, k) => t(l, { fontSize: size, fontWeight: 900, letterSpacing: -2, lineHeight: 1.18, color: k === 1 ? C.gold : C.ink }))));
const circle = (k, s = 50) => h('div', { width: s, height: s, borderRadius: s, background: '#FFFFFF', alignItems: 'center', justifyContent: 'center', fontSize: s * 0.46, fontWeight: 900, color: C.navy, flexShrink: 0 }, String(k));

const K = {
  // 표지: 인물 사진 위 2/3, 아래 3줄 큰 제목 + 한 줄 약속
  cover: (s, sp, i, n) => h('div', { width: W, height: H, position: 'relative', fontFamily: 'P', color: C.ink, background: C.navy },
    img(uri(path.join(ROOT, 'scripts/blog/media/lib', s.photo)), { position: 'absolute', left: 0, top: 0, width: W, height: 900, objectFit: 'cover', objectPosition: s.pos || 'center 20%' }),
    h('div', { position: 'absolute', left: 0, top: 0, width: W, height: 905, background: 'linear-gradient(180deg, rgba(13,24,40,.35) 0%, rgba(13,24,40,0) 22%, rgba(13,24,40,0) 48%, rgba(13,24,40,.85) 82%, #0D1828 100%)' }),
    h('div', { position: 'absolute', left: PAD, top: 56, right: PAD, justifyContent: 'space-between', alignItems: 'center' }, logo(190),
      t(`${i} / ${n}`, { fontSize: 24, fontWeight: 700, color: '#FFFFFF', background: 'rgba(0,0,0,.35)', borderRadius: 30, padding: '6px 18px' })),
    h('div', { position: 'absolute', left: PAD, right: PAD, bottom: 70, flexDirection: 'column' },
      h('div', { alignSelf: 'flex-start', background: C.gold, color: C.navy, borderRadius: 10, padding: '8px 18px', fontSize: 28, fontWeight: 900, marginBottom: 26 }, s.chip),
      s.lines.map((l, k) => t(l, { fontSize: k === s.lines.length - 1 ? 118 : 86, fontWeight: 900, letterSpacing: -3.5, lineHeight: 1.1, color: k === s.lines.length - 1 ? C.gold : '#FFFFFF', textShadow: '0 4px 24px rgba(0,0,0,.45)' })),
      h('div', { marginTop: 30, alignItems: 'center' },
        h('div', { width: 6, height: 44, background: C.gold2, marginRight: 18, borderRadius: 3 }),
        t(s.sub, { fontSize: 38, fontWeight: 700, color: '#E6EAF0' })),
      s.credit ? t(s.credit, { fontSize: 17, color: 'rgba(255,255,255,.45)', marginTop: 26 }) : null)),

  // 저장용 총정리 표: 10줄, 줄마다 번호·이름·하는 일·비중 막대·금액
  list: (s, sp, i, n) => {
    const max = Math.max(...s.rows.map((r) => r.pct));
    return frame(sp, i, n, h('div', { flexDirection: 'column' },
      h('div', { justifyContent: 'space-between', alignItems: 'flex-end' },
        head(s.kicker, s.title, 54),
        h('div', { flexDirection: 'column', alignItems: 'flex-end', marginBottom: 6 },
          t(s.totalLabel, { fontSize: 22, color: C.dim, fontWeight: 600 }),
          t(s.total, { fontSize: 40, fontWeight: 900, color: C.gold }))),
      h('div', { flexDirection: 'column', marginTop: 26, background: C.navy2, borderRadius: 26, padding: '10px 26px', border: `1px solid ${C.line}` },
        s.rows.map((r, k) => h('div', { alignItems: 'center', height: 80, borderBottom: k < s.rows.length - 1 ? `1px solid ${C.line}` : 'none' },
          circle(k + 1, 44),
          h('div', { flexDirection: 'column', width: 360, marginLeft: 20 },
            h('div', { alignItems: 'baseline' }, t(r.name, { fontSize: 32, fontWeight: 800, color: C.ink }), r.tag ? t(r.tag, { fontSize: 20, fontWeight: 700, color: C.gold2, marginLeft: 10 }) : null),
            t(r.what, { fontSize: 22, fontWeight: 500, color: C.dim, marginTop: 2 })),
          h('div', { width: 220, height: 14, marginRight: 18, alignItems: 'center' },
            h('div', { width: `${Math.max(6, (r.pct / max) * 100)}%`, height: 14, borderRadius: 7, background: k < 5 ? C.gold : 'rgba(234,219,185,.38)' })),
          h('div', { flexDirection: 'column', alignItems: 'flex-end', flexGrow: 1 },
            t(`${r.pct.toFixed(1)}%`, { fontSize: 32, fontWeight: 900, color: C.ink }),
            t(r.usd, { fontSize: 19, fontWeight: 600, color: C.dim }))))),
      s.note ? t(s.note, { fontSize: 22, color: C.mute, fontWeight: 600, marginTop: 18 }) : null));
  },

  // 100달러 쪼개기: 가로 띠 하나에 상위 5곳 + 나머지
  split: (s, sp, i, n) => frame(sp, i, n, h('div', { flexDirection: 'column' },
    head(s.kicker, s.title),
    h('div', { alignItems: 'flex-end', marginTop: 70 },
      t(s.big, { fontSize: 200, fontWeight: 900, color: C.gold, letterSpacing: -8, lineHeight: 0.9 }),
      t(s.bigUnit, { fontSize: 52, fontWeight: 900, color: C.gold, marginLeft: 10, marginBottom: 18 })),
    t(s.bigLabel, { fontSize: 32, fontWeight: 700, color: C.mute, marginTop: 16 }),
    h('div', { marginTop: 50, height: 120, borderRadius: 18, overflow: 'hidden', width: W - PAD * 2 },
      s.parts.map((p, k) => h('div', { width: `${p.pct}%`, height: 120, background: p.rest ? '#2A3B58' : [C.gold, '#D9C79F', '#C6B184', '#B39C6C', '#A08957'][k], alignItems: 'center', justifyContent: 'center', borderRight: `3px solid ${C.navy}` },
        t(`${Math.round(p.pct)}`, { fontSize: p.rest ? 40 : 38, fontWeight: 900, color: p.rest ? C.mute : C.navy })))),
    h('div', { marginTop: 14, width: W - PAD * 2 },
      s.parts.map((p) => h('div', { width: `${p.pct}%`, justifyContent: 'center' }, t(p.label, { fontSize: p.rest ? 24 : 22, fontWeight: 700, color: p.rest ? C.dim : C.mute, textAlign: 'center' })))),
    h('div', { flexDirection: 'column', marginTop: 70, padding: '30px 34px', background: C.navy2, borderRadius: 24, border: `1px solid ${C.line}` }, s.body.map((b) => t(b, { fontSize: 34, fontWeight: 500, color: C.mute, lineHeight: 1.55, marginTop: 8 }))))),

  // 전후 비교: 세로 막대 두 개 + 큰 변화율
  grow: (s, sp, i, n) => {
    const mx = Math.max(s.before.v, s.after.v), bh = 380;
    const bar = (x, hi) => h('div', { flexDirection: 'column', alignItems: 'center', width: 300 },
      t(x.show, { fontSize: 44, fontWeight: 900, color: hi ? C.ink : C.mute, marginBottom: 14 }),
      h('div', { width: 170, height: Math.round(bh * x.v / mx), borderRadius: '18px 18px 0 0', background: hi ? C.gold : '#34476A' }),
      t(x.label, { fontSize: 28, fontWeight: 700, color: C.mute, marginTop: 16 }),
      x.rank ? t(x.rank, { fontSize: 26, fontWeight: 800, color: hi ? C.gold : C.dim, marginTop: 6 }) : null);
    return frame(sp, i, n, h('div', { flexDirection: 'column' },
      head(s.kicker, s.title),
      h('div', { marginTop: 40, background: C.navy2, borderRadius: 28, border: `1px solid ${C.line}`, padding: '40px 40px 34px 40px', alignItems: 'flex-end', justifyContent: 'space-between' },
        bar(s.before, false),
        h('div', { flexDirection: 'column', alignItems: 'center', marginBottom: 150 },
          t(s.delta, { fontSize: 78, fontWeight: 900, color: C.up, letterSpacing: -2 }),
          t(s.deltaLabel, { fontSize: 24, fontWeight: 700, color: C.mute, marginTop: 4 })),
        bar(s.after, true)),
      h('div', { flexDirection: 'column', marginTop: 34 }, s.body.map((b) => t(b, { fontSize: 33, fontWeight: 500, color: C.mute, lineHeight: 1.55, marginTop: 8 })))));
  },

  // 두 숫자 가로 막대 비교
  versus: (s, sp, i, n) => {
    const mx = Math.max(...s.rows.map((r) => r.v));
    return frame(sp, i, n, h('div', { flexDirection: 'column' },
      head(s.kicker, s.title),
      h('div', { flexDirection: 'column', marginTop: 80 },
        s.rows.map((r, k) => h('div', { flexDirection: 'column', marginBottom: 56 },
          h('div', { justifyContent: 'space-between', alignItems: 'baseline' },
            t(r.label, { fontSize: 34, fontWeight: 800, color: C.ink }),
            t(r.show, { fontSize: 56, fontWeight: 900, color: r.tone === 'up' ? C.up : r.tone === 'down' ? C.down : C.ink })),
          h('div', { marginTop: 14, height: 34, borderRadius: 17, background: 'rgba(255,255,255,.06)', width: W - PAD * 2 },
            h('div', { width: `${Math.max(4, r.v / mx * 100)}%`, height: 34, borderRadius: 17, background: r.tone === 'up' ? C.up : r.tone === 'down' ? C.down : r.tone === 'mute' ? '#5A6B88' : C.gold }))))),
      h('div', { marginTop: 10, padding: '30px 34px', background: C.navy2, borderRadius: 24, border: `1px solid ${C.line}`, flexDirection: 'column' },
        t(s.boxTitle, { fontSize: 30, fontWeight: 900, color: C.gold }),
        s.body.map((b) => t(b, { fontSize: 31, fontWeight: 500, color: C.mute, lineHeight: 1.55, marginTop: 10 })))));
  },

  // 마지막: 다음에 볼 날 + 저장·공유·팔로우
  save: (s, sp, i, n) => frame(sp, i, n, h('div', { flexDirection: 'column' },
    head(s.kicker, s.title, 60),
    h('div', { flexDirection: 'column', marginTop: 50, padding: '34px 36px', borderRadius: 24, background: C.card, border: `2px solid ${C.gold2}` },
      t(s.dateLabel, { fontSize: 26, fontWeight: 800, color: C.gold2 }),
      t(s.date, { fontSize: 52, fontWeight: 900, color: C.gold, marginTop: 6 }),
      t(s.dateBody, { fontSize: 29, fontWeight: 500, color: C.mute, lineHeight: 1.5, marginTop: 12 })),
    h('div', { flexDirection: 'column', marginTop: 50 },
      s.acts.map((a, k) => h('div', { alignItems: 'center', marginTop: k ? 26 : 0 }, circle(k + 1, 48),
        t(a, { fontSize: 33, fontWeight: 700, color: C.ink, marginLeft: 22 })))),
    h('div', { marginTop: 60, alignItems: 'center', padding: '24px 28px', borderRadius: 24, background: C.navy2, border: `1px solid ${C.line}` },
      img(uri(PROFILE, 'image/png'), { width: 84, height: 84, borderRadius: 84 }),
      h('div', { flexDirection: 'column', marginLeft: 22, flexGrow: 1 },
        t('@value.note.korea', { fontSize: 32, fontWeight: 900 }),
        t('워렌 버핏·찰리 멍거의 기준으로 보는 주식 이야기', { fontSize: 22, fontWeight: 600, color: C.dim, marginTop: 4 })),
      h('div', { background: '#4F6BFF', borderRadius: 14, padding: '14px 26px', fontSize: 28, fontWeight: 900, color: '#FFFFFF' }, '팔로우')),
    t(sp.disclaimer, { fontSize: 20, color: C.dim, marginTop: 22 }))),
};

const [specPath, out] = process.argv.slice(2);
const sp = JSON.parse(fs.readFileSync(specPath, 'utf8'));
fs.mkdirSync(out, { recursive: true });
const n = sp.slides.length;
for (const [k, s] of sp.slides.entries()) {
  const svg = await satori(K[s.kind](s, { ...sp, foot: s.foot || sp.foot }, k + 1, n), { width: W, height: H, fonts });
  const png = new Resvg(svg, { fitTo: { mode: 'width', value: W } }).render().asPng();
  const f = path.join(out, `${String(k + 1).padStart(2, '0')}.png`);
  fs.writeFileSync(f, png);
  console.log('ok', f);
}
