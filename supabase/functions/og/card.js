// 기업 점수 카드(1200×630) 레이아웃. satori 가 읽는 요소 트리를 만든다.
// row = [이름, 종합, 품질, 저평가, 시장, 안전마진%, 업종]  (scripts/build_pages.mjs 가 c/scores.json 에 쓴다)
const MKT = { KR: '국내', US: '미국', JP: '일본', HK: '홍콩', CN: '중국 A' };
const h = (type, style, ...children) => ({ type, props: { style: { display: 'flex', ...style }, children: children.flat().filter((c) => c !== null && c !== undefined && c !== false) } });

function bar(label, v) {
  const w = Math.max(0, Math.min(100, v ?? 0));
  return h('div', { flexDirection: 'column', width: 300 },
    h('div', { justifyContent: 'space-between', fontSize: 26, color: '#AEB8C8', fontWeight: 700 }, label, h('span', { color: '#F3EEE3', fontWeight: 800 }, v == null ? '–' : `${v}점`)),
    h('div', { marginTop: 12, height: 14, borderRadius: 14, background: 'rgba(255,255,255,.14)', width: 300 },
      h('div', { width: Math.round(3 * w), height: 14, borderRadius: 14, background: '#EADBB9' })));
}

export function companyCard(row, date) {
  const [name, b, q, v, m, mos, ind] = row;
  const nameSize = name.length > 28 ? 46 : name.length > 14 ? 58 : name.length > 9 ? 70 : 84;
  const gap = mos == null ? null : mos >= 0
    ? h('div', { fontSize: 32, fontWeight: 800, color: '#7FD3A8' }, `적정 주가보다 ${mos}% 저평가`)
    : h('div', { fontSize: 32, fontWeight: 800, color: '#F08D8D' }, `적정 주가보다 ${-mos}% 고평가`);
  return h('div', { width: 1200, height: 630, flexDirection: 'column', justifyContent: 'space-between', padding: '56px 72px', background: 'linear-gradient(150deg,#1A2C46 0%,#0E1A2B 60%,#0A1322 100%)', color: '#F3EEE3', fontFamily: 'P' },
    h('div', { justifyContent: 'space-between', alignItems: 'center' },
      h('div', { alignItems: 'baseline', fontSize: 40, fontWeight: 900, letterSpacing: -1 }, 'Value', h('span', { color: '#EADBB9' }, 'Note'), h('span', { fontSize: 26, color: '#C9AF7A', marginLeft: 16, fontWeight: 700 }, '밸류노트')),
      h('div', { fontSize: 24, color: '#AEB8C8', fontWeight: 700 }, `${MKT[m] || ''} · 밸류노트 점수`)),
    h('div', { alignItems: 'center', justifyContent: 'space-between' },
      h('div', { flexDirection: 'column', width: 700 },
        h('div', { fontSize: nameSize, fontWeight: 900, letterSpacing: -2, lineHeight: 1.12, wordBreak: 'keep-all', flexWrap: 'wrap' }, name),
        ind ? h('div', { fontSize: 24, color: '#8E9AAD', marginTop: 10, fontWeight: 700 }, String(ind).slice(0, 48)) : null,
        h('div', { marginTop: 34, gap: 48 }, bar('재무 점수', q), bar('가격 점수', v))),
      h('div', { width: 300, height: 300, borderRadius: 300, border: '10px solid #C9AF7A', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'rgba(234,219,185,.08)' },
        h('div', { fontSize: 128, fontWeight: 900, color: '#EADBB9', lineHeight: 1 }, b == null ? '–' : String(b)),
        h('div', { fontSize: 26, color: '#AEB8C8', fontWeight: 700, marginTop: 6 }, '/ 100점'))),
    h('div', { justifyContent: 'space-between', alignItems: 'flex-end' },
      gap || h('div', { fontSize: 28, color: '#AEB8C8', fontWeight: 700 }, '그레이엄·버핏 기준으로 매일 계산'),
      h('div', { fontSize: 22, color: '#8E9AAD', fontWeight: 700 }, `valuenote.co.kr${date ? ' · ' + date : ''}`)));
}

// 점수표에 없는 주소일 때 쓰는 기본 카드
export function brandCard() {
  return h('div', { width: 1200, height: 630, flexDirection: 'column', justifyContent: 'center', padding: '72px', background: 'linear-gradient(150deg,#1A2C46 0%,#0E1A2B 60%,#0A1322 100%)', color: '#F3EEE3', fontFamily: 'P' },
    h('div', { alignItems: 'baseline', fontSize: 72, fontWeight: 900 }, 'Value', h('span', { color: '#EADBB9' }, 'Note')),
    h('div', { fontSize: 44, fontWeight: 800, marginTop: 24 }, '주식 사기 전에, 점수부터 확인하세요'),
    h('div', { fontSize: 30, color: '#AEB8C8', marginTop: 16, fontWeight: 700 }, '그레이엄·버핏·멍거 기준 · 5개 시장 600+ 기업'));
}
