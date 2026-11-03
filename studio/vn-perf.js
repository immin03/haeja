/* 밸류노트 성과 진단·숏폼 진단·벤치마킹 화면 — 성과 관리 플랫폼(/studio)과 관리자(admin.html)가 함께 쓴다 (2026-11-03 분리).
   필요한 전역: sb $ esc kst n0 toast head render page subPage */
/* 벤치마킹 (2026-10-29 운영자): "구독자는 별로 없는데 영상 몇 개로 조회수가 터진 사람들을 조사해서 벤치마킹할 내용을 계속 전달 →
   내가 반영하면 좋겠다는 부분을 승인하면 다음 영상부터 그대로 렌더링". 벤치마킹 데스크(예약 작업)가 docs 'bench' 에 영상별 카드를 쌓고,
   여기서 항목별로 승인·반려한다. 승인 항목은 데스크가 제작 규칙(릴스·쇼츠·롱폼·썸네일)에 옮기고 '반영 완료'로 바꾼다.
   '대기 영상도 다시 렌더'를 켜면 아직 안 올라간 영상까지 다시 만든다. */
const BN = { list: null, msg: '' };
async function benchLoad(){
  const { data, error } = await sb.from('docs').select('id,data,updated_at').eq('collection', 'bench').order('id', { ascending: false }).limit(120);
  BN.list = error ? [] : (data || []); BN.err = error ? error.message : '';
}
const manK = v => { v = +v || 0; if(v >= 1e8) return (Math.round(v / 1e7) / 10) + '억'; if(v >= 1e4) return (Math.round(v / 1e3) / 10) + '만'; if(v >= 1e3) return (Math.round(v / 100) / 10) + '천'; return String(v); };
const BN_ST = { proposed: ['run', '승인 대기'], approved: ['ok', '승인 · 반영 대기'], applied: ['ok', '반영 완료'], rejected: ['off', '반려'] };
const BN_TABS = [['new', '새 제안', ['proposed']], ['approved', '반영 대기', ['approved']], ['applied', '반영 완료', ['applied']], ['rejected', '반려', ['rejected']]];
function bnPoints(d){ return Array.isArray(d && d.points) ? d.points : []; }
function benchCounts(){ const c = { proposed: 0, approved: 0, applied: 0, rejected: 0 }; (BN.list || []).forEach(r => bnPoints(r.data).forEach(x => { c[x.status || 'proposed'] = (c[x.status || 'proposed'] || 0) + 1; })); return c; }
function bnCard(r, sts){
  const d = r.data || {}, v = d.video || {}, pts = bnPoints(d).map((x, i) => [x, i]).filter(([x]) => sts.includes(x.status || 'proposed'));
  if(!pts.length) return '';
  const id = esc(r.id), open = sts.includes('proposed');
  const meta = [v.channel ? `<b>${esc(v.channel)}</b>` : '', v.subs != null ? `구독자 ${manK(v.subs)}명` : '', v.views ? `조회수 ${manK(v.views)}회` : '', v.length ? `길이 ${esc(v.length)}` : '', v.published ? esc(String(v.published).slice(0, 10)) : '', v.platform && v.platform !== 'youtube' ? esc(v.platform) : ''].filter(Boolean).join(' · ');
  const pt = ([x, i]) => { const st = BN_ST[x.status || 'proposed'] || ['', x.status];
    return `<div class="bn-pt" data-bn="${id}" data-i="${i}">
      <div class="h"><span class="t">${esc(x.target || '공통')}</span><span class="i">${esc(x.idea || '')}</span><span class="st ${st[0]}">${st[1]}</span></div>
      ${x.apply ? `<div class="a"><em>우리 영상엔:</em> ${esc(x.apply)}</div>` : ''}
      ${x.example ? `<div class="a"><em>예:</em> ${esc(x.example)}</div>` : ''}
      ${x.owner_note ? `<div class="a"><em>대표님 메모:</em> ${esc(x.owner_note)}</div>` : ''}
      ${x.applied_note ? `<div class="a"><em>반영:</em> ${esc(x.applied_note)}${x.applied_at ? ` · ${kst(x.applied_at)}` : ''}</div>` : ''}
      ${open ? `<div class="bn-act"><input type="text" placeholder="메모 (예: 숫자만 더 크게, 롱폼에만)" data-bn-note><label><input type="checkbox" data-bn-rr> 아직 안 올라간 영상도 다시 렌더</label>
        <button class="bn-btn" data-bn-ok>승인</button><button class="bn-btn ghost" data-bn-no>반려</button></div>`
        : (x.status === 'approved' ? `<div class="bn-act"><span class="bn-meta">${x.rerender ? '대기 영상도 다시 렌더' : '다음 영상부터 반영'}</span><button class="bn-btn ghost" data-bn-undo>승인 취소</button></div>` : '')}
    </div>`; };
  return `<div class="card bn-card">
    <a class="bn-thumb" href="${esc(v.url || '#')}" target="_blank" rel="noopener">${v.thumb ? `<img src="${esc(v.thumb)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : ''}${v.is_short ? '<span class="tag">쇼츠</span>' : ''}</a>
    <div>
      <a class="bn-title" href="${esc(v.url || '#')}" target="_blank" rel="noopener">${esc(v.title || r.id)}</a>
      <div class="bn-meta">${meta}${v.ratio ? ` <span class="bn-ratio">구독자의 ${n0(Math.round(v.ratio))}배</span>` : ''}</div>
      ${d.why ? `<div class="bn-why"><b>왜 터졌나</b> · ${esc(d.why)}</div>` : ''}
      ${pts.map(pt).join('')}
      ${open && pts.length > 1 ? `<div class="bn-act"><button class="bn-btn ghost bn-all" data-bn-all="${id}">이 영상 항목 전부 승인</button></div>` : ''}
    </div></div>`;
}
function vBench(){
  if(BN.list === null){ benchLoad().then(() => render()); return head('벤치마킹', '불러오는 중', 'bench'); }
  if(BN.err) return head('벤치마킹', '', 'bench') + `<div class="card">불러오지 못했습니다: ${esc(BN.err)}</div>`;
  const c = benchCounts(); let cur = subPage(); if(!BN_TABS.some(t => t[0] === cur)) cur = c.proposed ? 'new' : c.approved ? 'approved' : 'new';
  const tab = BN_TABS.find(t => t[0] === cur);
  const seg = `<div class="seg">${BN_TABS.map(([k, t, st]) => { const n = st.reduce((a, x) => a + (c[x] || 0), 0); return `<a href="#bench/${k}"${k === cur ? ' aria-current="page"' : ''}${k === 'new' && n ? ' class="hot"' : ''}>${t}<b>${n}</b></a>`; }).join('')}</div>`;
  const cards = (BN.list || []).map(r => bnCard(r, tab[2])).join('');
  const last = (BN.list || [])[0];
  const note = { new: '구독자는 적은데 조회수가 크게 터진 영상에서 우리가 따라 할 만한 점입니다. 반영하고 싶은 항목만 승인하세요. 메모를 남기면 그 방향으로 반영합니다.',
    approved: '승인한 항목입니다. 벤치마킹 작업이 하루 두 번(10:23·16:23) 제작 규칙에 옮기고, 다음 영상부터 반영합니다.', applied: '제작 규칙에 들어간 항목입니다.', rejected: '반려한 항목은 비슷한 제안이 다시 올라오지 않게 참고합니다.' }[cur];
  return `${head('벤치마킹', '조회수가 구독자보다 훨씬 많이 나온 영상을 매일 조사해 올립니다.' + (last ? ` 마지막 조사 ${kst(last.updated_at)}` : ''), 'bench')}
  ${seg}
  ${BN.msg ? `<div class="soc-flash ok">${esc(BN.msg)}</div>` : ''}
  <div class="yt-note">${note}</div>
  ${cards || `<div class="card empty" style="padding:14px">${cur === 'new' ? '새 제안이 없습니다. 매일 오전 조사 후 올라옵니다.' : '해당하는 항목이 없습니다.'}</div>`}`;
}
async function bnSave(id, f, msg){
  const r = (BN.list || []).find(x => x.id === id); if(!r) return;
  const data = JSON.parse(JSON.stringify(r.data || {})); f(data);
  const { error } = await sb.from('docs').update({ data, updated_at: new Date().toISOString() }).eq('collection', 'bench').eq('id', id);
  if(error){ toast('저장하지 못했습니다: ' + error.message, true); return; }
  r.data = data; BN.msg = ''; toast(msg); render();
}
function bindBench(){
  const box = $('#main');
  box.querySelectorAll('[data-bn-ok],[data-bn-no],[data-bn-undo]').forEach(b => b.onclick = () => {
    const w = b.closest('[data-bn]'), id = w.dataset.bn, i = +w.dataset.i;
    const note = (w.querySelector('[data-bn-note]') || {}).value || '', rr = !!(w.querySelector('[data-bn-rr]') || {}).checked;
    const to = b.hasAttribute('data-bn-ok') ? 'approved' : b.hasAttribute('data-bn-no') ? 'rejected' : 'proposed';
    bnSave(id, d => { const x = d.points[i]; x.status = to; x.decided_at = new Date().toISOString(); if(to === 'approved') x.rerender = rr; if(note.trim()) x.owner_note = note.trim(); },
      to === 'approved' ? '승인했습니다. 다음 영상부터 반영합니다.' : to === 'rejected' ? '반려했습니다.' : '승인을 취소했습니다.');
  });
  box.querySelectorAll('[data-bn-all]').forEach(b => b.onclick = () => {
    bnSave(b.dataset.bnAll, d => { d.points.forEach(x => { if((x.status || 'proposed') === 'proposed'){ x.status = 'approved'; x.decided_at = new Date().toISOString(); } }); }, '이 영상의 항목을 전부 승인했습니다.');
  });
}

/* ───────── 성과 진단 (2026-10-29 운영자: "성과에 대한 진단도 관리자에서 보기 쉽게 … 일일 단위로 정리하고 보고하고,
   당장 개선 가능한 버튼들과 내가 피드백 남길 칸 … 거기에서 바로 적용해서 개선할 수 있게 다음 콘텐츠부터")
   데이터: rpc perf_admin() → { videos: yt_perf(30), perf: docs agent 'perf-YYYY-MM-DD' 최근 14개, optimize }
           docs agent 'perf-inbox' → 대표님 피드백함 (예약 작업이 읽고 답을 달아 둔다)
   승인한 개선 항목은 매일 05:37 개선 작업이 제작 규칙(FORMAT.md 등)에 옮기고 status를 'applied'로 바꾼다.
   'live'(이미 올라간 영상 수정) 항목은 유튜브 업로드 작업이 스튜디오에서 처리한다. */
const PF = { data: null, inbox: null, err: '', msg: '', busy: false };
const PF_GOAL = { ctr: 4, s15: 60, avg_pct: 35 };
const PF_ST = { proposed: ['run', '결정 대기'], approved: ['ok', '승인 · 다음 콘텐츠부터 적용 대기'], applied: ['ok', '적용 완료'], hold: ['hold', '보류'], rejected: ['off', '반려'], apply_failed: ['off', '적용 실패'] };
const PF_AREA_SCOPE = { next: ['', '다음 콘텐츠부터'], live: ['live', '이미 올린 영상 수정'], system: ['sys', '운영 방식'] };
async function perfLoad(){
  const [r, ib] = await Promise.all([sb.rpc('perf_admin'), sb.from('docs').select('id,data,updated_at').eq('collection', 'agent').eq('id', 'perf-inbox').maybeSingle()]);
  PF.err = r.error ? r.error.message : ''; PF.data = r.error ? { videos: [], perf: [], perfs: [], optimize: [] } : (r.data || { videos: [], perf: [], perfs: [], optimize: [] });
  PF.inbox = ib.data ? ib.data : { id: 'perf-inbox', data: { items: [] } };
}
/* 날짜 칩: 보고가 있는 날은 링크, 최근 7일 중 보고가 없는 날은 '빠짐' 칩 (2026-11-03 대표님: "11월 2일꺼 업데이트… 안 놓치게 하루 단위로")
   빠진 날은 매일 07:31 사용량 경보 작업이 성과 평가 작업을 깨워 그 날짜로 보충한다 */
function pfSeg(reps, prefix, hash, rep){
  const have = {}; reps.forEach(r => have[r.id.slice(prefix.length)] = r);
  const today = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10), days = [];
  for(let i = 0; i < 7; i++){ const x = new Date(Date.parse(today + 'T00:00:00Z') - i * 864e5).toISOString().slice(0, 10); days.push(x); }
  const older = reps.filter(r => !days.includes(r.id.slice(prefix.length))).slice(0, 4);
  const chip = (day, r) => { if(!r){ if(day === today) return `<a href="#${hash}/${day}" class="miss" title="오늘 진단은 '오늘 진단 새로고침'을 누를 때만 작성됩니다" style="opacity:.55;border-style:dashed">${day.slice(5).replace('-', '월 ')}일 <b style="background:var(--bg);color:var(--muted)">아직</b></a>`; return `<a href="#${hash}/${day}" class="miss" title="이 날 보고가 없습니다 — 열어서 '보충 요청'을 누르면 다음 회차가 채웁니다" style="opacity:.55;border-style:dashed">${day.slice(5).replace('-', '월 ')}일 <b style="background:rgba(216,65,90,.12);color:var(--bad)">빠짐</b></a>`; }
    const pend = (r.data.actions || []).filter(a => (a.status || 'proposed') === 'proposed').length;
    return `<a href="#${hash}/${day}"${rep && r.id === rep.id ? ' aria-current="page"' : ''}${pend ? ' class="hot"' : ''}>${day.slice(5).replace('-', '월 ')}일${pend ? `<b>${pend}</b>` : ''}${r.data.backfill ? ' <small style="font-weight:500">보충</small>' : ''}</a>`; };
  const missing = pfMissingDays(reps, prefix);
  const html = days.map(d => chip(d, have[d])).join('') + older.map(r => chip(r.id.slice(prefix.length), r)).join('')
    + `<span style="margin-left:auto;display:inline-flex;gap:6px;flex-wrap:wrap">${missing.length ? `<button class="pf-btn ghost" type="button" data-pf-refresh="${hash}" data-pf-day="${missing.join(',')}" title="빠진 ${missing.length}일을 저장된 데이터로 보충">빠진 ${missing.length}일 보충 요청</button>` : ''}<button class="pf-btn" type="button" data-pf-refresh="${hash}" data-pf-day="${today}" title="오늘 진단을 지금 작성합니다 (정규 회차 없음 — 누를 때만)">${have[today] ? '오늘 진단 다시 쓰기' : '오늘 진단 새로고침'}</button></span>`;
  return html ? `<div class="seg" style="display:flex;flex-wrap:wrap;align-items:center">${html}</div>` : '';
}
function pfReports(){ return (PF.data && PF.data.perf || []).filter(x => /^perf-\d{4}-\d{2}-\d{2}$/.test(x.id)); }
function pfCur(){ const reps = pfReports(); const want = 'perf-' + subPage(); return reps.find(x => x.id === want) || (/^\d{4}-\d{2}-\d{2}$/.test(subPage()) ? null : reps[0] || null); }
/* 2026-11-03 17:30·18:11 대표님: "성과 쪽도 새로 고침 해야 불러오는 걸로, 자동으로 하지 말고", "정규 회차를 싹 다 없애버리고 내가 눌러야만 업데이트"
   → 성과 평가·개선 작업의 정규 회차 없음. 버튼을 누르면 docs agent 'perf-refresh'에 요청이 적히고, 브리핑 작업(하루 4번)이 그 요청을 보고
   해당 진단 작업을 깨운다. 오늘 날짜 = 전체 진단 작성, 과거 날짜 = 저장된 데이터로 보충. */
const pfMissCard = (kind) => /^\d{4}-\d{2}-\d{2}$/.test(subPage()) ? `<div class="card pf-hero"><div class="k">${esc(subPage())} ${kind}</div><div class="h">이 날 보고가 없습니다.</div><div class="n">그날 작업이 사용량 한도 등으로 못 돌았습니다. 자동으로 채우지 않습니다 — 아래 '보충 요청'을 누르면 다음 브리핑 회차(08·12·17·21시 17분)가 진단 작업을 깨워 이 날짜를 저장된 데이터로 보충하고, 보충한 보고에는 '보충' 표시가 붙습니다.</div><div class="pf-ctl" style="margin-top:10px"><button class="pf-btn" type="button" data-pf-refresh="${kind === '롱폼 진단' ? 'perf' : 'perfs'}" data-pf-day="${esc(subPage())}">이 날 보충 요청</button></div></div>` : '';
/* 최근 7일 중 빠진 날 목록 */
function pfMissingDays(reps, prefix){
  const have = new Set(reps.map(r => r.id.slice(prefix.length)));
  const today = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10), out = [];
  for(let i = 1; i < 7; i++){ const x = new Date(Date.parse(today + 'T00:00:00Z') - i * 864e5).toISOString().slice(0, 10); if(!have.has(x)) out.push(x); }
  return out;
}
async function pfRequestRefresh(kind, days){
  const { data: row } = await sb.from('docs').select('data,updated_at').eq('collection', 'agent').eq('id', 'perf-refresh').maybeSingle();
  const cur = (row && row.data) || { items: [] };
  const items = (cur.items || []).filter(x => !(x.kind === kind && days.includes(x.day))).concat(days.map(day => ({ kind, day, at: new Date().toISOString(), status: 'new', by: 'owner' })));
  const data = { ...cur, items, at: new Date().toISOString() };
  const q = row ? sb.from('docs').update({ data, updated_at: new Date().toISOString() }).eq('collection', 'agent').eq('id', 'perf-refresh')
    : sb.from('docs').upsert({ owner: (await sb.auth.getUser()).data.user.id, collection: 'agent', id: 'perf-refresh', data, updated_at: new Date().toISOString() });
  const { error } = await q; if(error){ toast('요청을 저장하지 못했습니다: ' + error.message, true); return false; }
  toast(`요청을 넣었습니다 (${days.map(d => d.slice(5)).join(', ')}). 브리핑 작업(08·12·17·21시 17분)이 받아서 진단 작업을 깨우고, 깨운 뒤 ${kind === 'perf' ? '10~15분' : '5~10분'} 안에 올라옵니다.`); return true;
}
function pfPending(){ const r = pfReports()[0]; return r ? (r.data.actions || []).filter(a => (a.status || 'proposed') === 'proposed').length : 0; }
const pfNum = (v, unit = '', d = 1) => v == null || v === '' || isNaN(+v) ? '–' : (Math.round(+v * Math.pow(10, d)) / Math.pow(10, d)).toLocaleString('ko-KR') + unit;
const pfSec = s => { if(s == null || isNaN(+s)) return '–'; s = Math.round(+s); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };
const pfCls = (v, goal, warnRatio = .6) => v == null || isNaN(+v) ? '' : +v >= goal ? 'ok' : +v >= goal * warnRatio ? 'warn' : 'bad';
function pfKpi(label, v, unit, goal, sub){
  const has = v != null && !isNaN(+v), c = goal ? pfCls(v, goal) : '';
  const w = goal && has ? Math.min(100, +v / goal * 100) : 0, col = c === 'ok' ? 'var(--good)' : c === 'warn' ? '#E0A526' : 'var(--bad)';
  return `<div class="card pf-kpi"><div class="l">${label}</div><div class="v ${c ? 'pf-' + c : ''}">${has ? pfNum(v, '', unit === '%' ? 1 : 0) : '–'}${has && unit ? `<small>${unit}</small>` : ''}</div>
    ${goal ? `<div class="g"><i style="width:${w}%;background:${col}"></i></div><div class="t">목표 ${(+goal).toLocaleString('ko-KR')}${unit}${has ? ` · ${+v >= goal ? '달성' : '목표의 ' + Math.round(+v / goal * 100) + '%'}` : ''}</div>` : `<div class="t">${sub || ''}</div>`}</div>`;
}
function pfRetSvg(ret, dur){
  if(!ret || typeof ret !== 'object') return '';
  const pts = [['0', 0, 100], ['5초', 5, ret.s5], ['10초', 10, ret.s10], ['15초', 15, ret.s15], ['30초', 30, ret.s30], ['1분', 60, ret.m1]];
  if(dur){ pts.push(['25%', dur * .25, ret.p25], ['50%', dur * .5, ret.p50], ['75%', dur * .75, ret.p75], ['끝', dur, ret.end]); }
  const ok = pts.filter(p => p[2] != null && !isNaN(+p[2])); if(ok.length < 3) return '';
  const W = 320, H = 110, L = 34, B = 18, maxX = Math.max(...ok.map(p => p[1])) || 1;
  /* 앞 1분이 잘 보이게 시간축을 제곱근으로 편다 */
  const X = t => L + Math.sqrt(t / maxX) * (W - L - 8), Y = v => 6 + (100 - Math.min(100, +v)) / 100 * (H - B - 6);
  const line = ok.map((p, i) => (i ? 'L' : 'M') + X(p[1]).toFixed(1) + ',' + Y(p[2]).toFixed(1)).join('');
  const goal = Y(PF_GOAL.s15);
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="시청 지속 곡선">
    ${[100, 50, 0].map(v => `<line x1="${L}" x2="${W - 8}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--grid)"/><text x="${L - 4}" y="${Y(v) + 3}" font-size="9" text-anchor="end" fill="var(--muted)">${v}%</text>`).join('')}
    <line x1="${X(15)}" x2="${X(15)}" y1="6" y2="${H - B}" stroke="var(--line)" stroke-dasharray="3 3"/>
    <line x1="${L}" x2="${W - 8}" y1="${goal}" y2="${goal}" stroke="var(--good)" stroke-dasharray="4 3" opacity=".7"/><text x="${W - 10}" y="${goal - 3}" font-size="9" text-anchor="end" fill="var(--good)">15초 목표 ${PF_GOAL.s15}%</text>
    <path d="${line}" fill="none" stroke="var(--bad)" stroke-width="2.2" stroke-linejoin="round"/>
    ${ok.map(p => `<circle cx="${X(p[1])}" cy="${Y(p[2])}" r="2.6" fill="var(--bad)"><title>${p[0]} ${p[2]}%</title></circle>`).join('')}
    ${ok.filter(p => ['15초', '1분', '50%', '끝'].includes(p[0])).map(p => `<text x="${X(p[1])}" y="${H - 5}" font-size="9" text-anchor="middle" fill="var(--muted)">${p[0]}</text>`).join('')}
    ${ok.filter(p => p[0] === '15초').map(p => `<text x="${X(p[1]) + 4}" y="${Y(p[2]) - 5}" font-size="10" font-weight="800" fill="var(--bad)">${p[2]}%</text>`).join('')}
  </svg>`;
}
const PF_SRC_COL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#8a94a6', '#5b6b85'];
function pfSrc(src){
  const e = Object.entries(src || {}).filter(([, v]) => +v > 0).sort((a, b) => b[1] - a[1]); if(!e.length) return '';
  return `<div class="pf-src"><div class="cap">유입 경로</div><div class="bar">${e.map(([k, v], i) => `<span style="width:${v}%;background:${PF_SRC_COL[i % 7]}" title="${esc(k)} ${v}%"></span>`).join('')}</div>
    <div class="lg">${e.slice(0, 5).map(([k, v], i) => `<span><i style="background:${PF_SRC_COL[i % 7]}"></i>${esc(k)} ${pfNum(v, '%')}</span>`).join('')}</div></div>`;
}
function pfVideo(v, diag){
  const s = v.studio || {}, d = diag || {}, ret = s.retention || d.retention, dur = s.duration_sec || d.duration_sec || v.duration;
  const ctr = s.ctr ?? d.ctr, s15 = ret && ret.s15, ap = s.avg_pct ?? d.avg_pct ?? (s.avg_sec && dur ? s.avg_sec / dur * 100 : null);
  const vr = s.valid_views && s.views ? Math.round(s.valid_views / s.views * 100) : d.valid_rate;
  const verdict = d.verdict || (pfCls(ctr, PF_GOAL.ctr) === 'bad' || pfCls(s15, PF_GOAL.s15) === 'bad' ? 'bad' : 'warn');
  const vdTxt = { bad: '개선 시급', warn: '보완 필요', ok: '양호' }[verdict] || '';
  const yid = v.youtube_id || d.youtube_id, link = yid ? `https://studio.youtube.com/video/${yid}/analytics/tab-overview/period-default` : '#';
  const m = [
    ['조회', pfNum(s.views ?? d.views, '회', 0), ''],
    ['노출', pfNum(s.impressions ?? d.impressions, '회', 0), ''],
    ['클릭률', pfNum(ctr, '%'), pfCls(ctr, PF_GOAL.ctr)],
    ['15초 유지', pfNum(s15, '%', 0), pfCls(s15, PF_GOAL.s15)],
    ['평균 시청', pfSec(s.avg_sec ?? d.avg_sec) + (dur ? ' / ' + pfSec(dur) : ''), ''],
    ['평균 조회율', pfNum(ap, '%'), pfCls(ap, PF_GOAL.avg_pct)],
    vr != null ? ['유효 조회', vr + '%', pfCls(vr, 70)] : null,
    s.subs != null ? ['구독', (+s.subs > 0 ? '+' : '') + s.subs, ''] : null
  ].filter(Boolean);
  const ab = s.ab || d.ab;
  const age = v.age_h != null ? (v.age_h >= 48 ? Math.round(v.age_h / 24) + '일째' : v.age_h + '시간째') : '';
  return `<div class="card pf-vid" data-pfv="${esc(v.id)}">
    <a class="th" href="${link}" target="_blank" rel="noopener">${yid ? `<img src="https://i.ytimg.com/vi/${esc(yid)}/mqdefault.jpg" alt="" loading="lazy" referrerpolicy="no-referrer">` : ''}${vdTxt ? `<span class="vd ${verdict}">${vdTxt}</span>` : ''}</a>
    <div>
      <a class="tt" href="${link}" target="_blank" rel="noopener">${esc(v.title || d.title || v.id)}</a>
      <div class="bn-meta">${v.published_at ? kst(v.published_at) + ' 공개' : ''}${age ? ' · ' + age : ''}${s.at ? ' · 지표 ' + kst(s.at) : ' · 스튜디오 지표 미수집'}</div>
      <div class="pf-m">${m.map(([k, val, c]) => `<span class="${c}">${k} ${val}</span>`).join('')}</div>
      <div class="pf-two">${pfRetSvg(ret, dur) ? `<div class="pf-ret"><div class="cap">시청 지속 곡선</div>${pfRetSvg(ret, dur)}</div>` : `<div class="pf-ret"><div class="cap">시청 지속 곡선</div><div class="pf-empty">${esc((ret && ret.note) || '아직 곡선이 나오지 않았습니다 (조회가 적거나 처리 중)')}</div></div>`}${pfSrc(s.sources || d.sources) || '<div></div>'}</div>
      ${(d.issues || []).length || (d.good || []).length ? `<ul class="pf-li">${(d.issues || []).map(x => `<li class="b">${esc(x)}</li>`).join('')}${(d.good || []).map(x => `<li class="g">${esc(x)}</li>`).join('')}</ul>` : ''}
      ${ab && ab.state && ab.state !== '없음' ? `<div class="pf-ab"><b>A/B 테스트</b> · ${esc(ab.state)}${ab.winner ? ` · 승자 ${esc(ab.winner)}` : ''}${ab.note ? ` · ${esc(ab.note)}` : ''}</div>` : ''}
      <div class="pf-vfb"><input type="text" placeholder="이 영상에 대한 의견 (예: 썸네일 글씨가 작아, 인트로 질문을 더 세게)" data-pfv-note>
        <button class="pf-btn ghost" data-pfv-kind="thumb">썸네일 교체 요청</button><button class="pf-btn ghost" data-pfv-kind="title">제목 교체 요청</button><button class="pf-btn ghost" data-pfv-kind="keep">이 방식 유지</button><button class="pf-btn" data-pfv-kind="note">의견 보내기</button></div>
    </div></div>`;
}
function pfAction(a, i, repId){
  const st = PF_ST[a.status || 'proposed'] || ['', a.status], sc = PF_AREA_SCOPE[a.scope || 'next'] || PF_AREA_SCOPE.next, open = (a.status || 'proposed') === 'proposed' || a.status === 'hold';
  return `<div class="card pf-act" data-pfa="${i}" data-rep="${esc(repId)}">
    <div class="top"><span class="no">${esc(a.no || i + 1)}</span><span class="ti">${esc(a.title)}</span><span class="pf-tag">${esc(a.area || '')}</span><span class="pf-tag ${sc[0]}">${sc[1]}</span>${a.impact ? `<span class="pf-stars" title="예상 효과">${'★'.repeat(a.impact)}${'☆'.repeat(5 - a.impact)}</span>` : ''}<span class="pf-st ${st[0]}">${st[1]}</span></div>
    ${a.why ? `<div class="row"><em>근거</em> · ${esc(a.why)}</div>` : ''}
    ${a.change ? `<div class="row"><em>바꾸는 것</em> · ${esc(a.change)}</div>` : ''}
    ${a.owner_note ? `<div class="row"><em>대표님 메모</em> · ${esc(a.owner_note)}</div>` : ''}
    ${a.result ? `<div class="row"><em>적용 결과</em> · ${esc(a.result)}${a.applied_at ? ' · ' + kst(a.applied_at) : ''}</div>` : ''}
    ${a.effect ? `<div class="row"><em>적용 뒤 성과</em> · ${esc(a.effect)}</div>` : ''}
    ${open ? `<div class="pf-ctl"><input type="text" placeholder="고쳐서 적용할 내용 (비워 두면 그대로 적용)" data-pfa-note>
      <button class="pf-btn" data-pfa-to="approved">${a.scope === 'live' ? '지금 영상에 적용' : '다음 콘텐츠부터 적용'}</button>
      ${a.status !== 'hold' ? '<button class="pf-btn ghost" data-pfa-to="hold">보류</button>' : ''}<button class="pf-btn ghost" data-pfa-to="rejected">반려</button></div>`
      : a.status === 'approved' ? `<div class="pf-ctl"><span class="bn-meta">${/^perfs-/.test(repId) ? (a.scope === 'live' ? '유튜브 업로드 작업이 다음 회차(07:10·12:10·20:10)에 스튜디오에서 바꿉니다.' : '매일 05:37 개선 작업이 쇼츠·릴스 제작 기준과 자동 검수 기준에 넣고, 그다음 만드는 쇼츠·릴스부터 반영됩니다. 급하면 채팅에 "숏폼 개선 지금 적용"이라고 남겨 주세요.') : a.scope === 'live' ? '유튜브 업로드 작업이 다음 회차(07:10·12:10·20:10)에 스튜디오에서 바꿉니다.' : '매일 05:37 개선 작업이 제작 규칙에 넣고, 그다음 만드는 콘텐츠부터 반영됩니다. 급하면 채팅에 "성과 개선 지금 적용"이라고 남겨 주세요.'}</span><button class="pf-btn ghost" data-pfa-to="proposed">승인 취소</button></div>` : ''}
  </div>`;
}
function pfTrend(reps){
  const pts = reps.slice().reverse().map(r => ({ d: r.id.slice(10), k: r.data.kpis || {} })).filter(p => p.k.ctr != null || p.k.s15 != null);
  if(pts.length < 2) return `<div class="card pf-trend"><div class="pf-empty">추이는 진단이 이틀 이상 쌓이면 그려집니다. 매일 20:52 진단이 하나씩 쌓입니다.</div></div>`;
  const W = 640, H = 170, L = 30, R = 12, T = 10, B = 22, n = pts.length;
  const X = i => L + i / (n - 1) * (W - L - R), Y = v => T + (100 - Math.min(100, v)) / 100 * (H - T - B);
  const Yc = v => T + (10 - Math.min(10, v)) / 10 * (H - T - B);
  const path = (f, y) => pts.map((p, i) => f(p) == null ? '' : `${i && f(pts[i - 1]) != null ? 'L' : 'M'}${X(i).toFixed(1)},${y(f(p)).toFixed(1)}`).join('');
  return `<div class="card pf-trend"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="성과 추이">
    ${[0, 50, 100].map(v => `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--grid)"/><text x="${L - 4}" y="${Y(v) + 3}" font-size="9" text-anchor="end" fill="var(--muted)">${v}%</text>`).join('')}
    <path d="${path(p => p.k.s15, Y)}" fill="none" stroke="var(--bad)" stroke-width="2.2"/>
    <path d="${path(p => p.k.avg_pct, Y)}" fill="none" stroke="#E0A526" stroke-width="2.2"/>
    <path d="${path(p => p.k.ctr, Yc)}" fill="none" stroke="var(--s-visit)" stroke-width="2.2"/>
    ${pts.map((p, i) => `<text x="${X(i)}" y="${H - 6}" font-size="9" text-anchor="middle" fill="var(--muted)">${p.d.slice(3).replace('-', '/')}</text>`).join('')}
  </svg><div class="lg"><span><i style="background:var(--s-visit)"></i>클릭률 (0~10% 축)</span><span><i style="background:var(--bad)"></i>15초 유지율</span><span><i style="background:#E0A526"></i>평균 조회율</span></div></div>`;
}
function pfInboxHtml(ch){
  const items = ((PF.inbox && PF.inbox.data && PF.inbox.data.items) || []).filter(x => ch === 'short' ? x.channel === 'short' : x.channel !== 'short').slice().reverse().slice(0, 12);
  if(!items.length) return '';
  const kindKo = { note: '의견', thumb: '썸네일 교체 요청', title: '제목 교체 요청', keep: '유지 요청', general: '전체 의견' };
  return `<div class="pf-msgs">${items.map(x => `<div class="pf-msg"><div class="m"><b>${esc(kindKo[x.kind] || '의견')}</b><span>${kst(x.at)}</span>${x.video_title ? `<span>${esc(x.video_title.slice(0, 28))}…</span>` : ''}<span class="pf-st ${x.status === 'done' ? 'ok' : 'run'}">${x.status === 'done' ? '반영함' : '반영 대기'}</span></div>${esc(x.text)}${x.reply ? `<div class="r"><b>Claude</b> · ${esc(x.reply)}${x.replied_at ? ' · ' + kst(x.replied_at) : ''}</div>` : ''}</div>`).join('')}</div>`;
}
/* 성장·수익 창출·유입 (2026-10-30 대표님 대화: 성장 목표선과 비교, 8,000시간 진행, 유튜브→밸류노트 다리, 터진 영상 후속, 적정 매수가 도달 기록)
   20:52 성과 진단이 perf-<D>.data 에 track · monetize · funnel · breakouts · alert_track 을 채운다 */
function pfGrowth(d){
  const t = d.track || null, m = d.monetize || null, f = d.funnel || null, b = d.breakouts || [], at = d.alert_track || null;
  if(!t && !m && !f && !b.length && !at) return '';
  const tile = (label, v, unit, goal, sub) => pfKpi(label, v, unit, goal, sub);
  const pathTxt = t ? ({ below: '기본 경로 아래', base: '기본 경로', between: '기본~잘 됨 사이', good: '잘 됨 경로', above: '잘 됨 위 (터진 영상 효과)' }[t.path] || t.path || '') : '';
  const A = (t && t.actual) || {}, G = (t && t.good) || {}, B = (t && t.base) || {};
  const trackHtml = t ? `<div class="pf-kpis">
      ${tile('구독자', A.subs, '명', G.subs, '')}
      ${tile('쇼츠 조회 (30일)', A.short_views, '회', G.short_views, '')}
      ${tile('롱폼 조회 (30일)', A.long_views, '회', G.long_views, '')}
      ${tile('롱폼 평균 시청', A.avg_view_min != null ? Math.round(A.avg_view_min * 60) : null, '초', G.avg_view_min != null ? Math.round(G.avg_view_min * 60) : null, '')}
      <div class="card pf-kpi"><div class="l">지금 경로 · ${esc(t.month || '')}</div><div class="v" style="font-size:20px">${esc(pathTxt || '–')}</div><div class="t">이달 목표 구독 · 기본 ${pfNum(B.subs, '명', 0)} · 잘 됨 ${pfNum(G.subs, '명', 0)}</div></div></div>
    ${t.note ? `<div class="note" style="margin:-6px 0 12px">${esc(t.note)}</div>` : ''}` : '';
  const monHtml = m ? `<div class="pf-kpis">
      ${tile('구독자', m.subs, '명', 1000, '')}
      ${tile('최근 1년 롱폼 시청시간', m.watch_h_12m, '시간', m.rule_h || 8000, '')}
      ${tile('최근 90일 쇼츠 조회', m.shorts_90d, '회', m.rule_shorts || 20000000, '')}
      <div class="card pf-kpi"><div class="l">예상 도달</div><div class="v" style="font-size:20px">${esc(m.eta || '–')}</div><div class="t">${esc(m.basis || '')}</div></div>
      <div class="card pf-kpi"><div class="l">기준</div><div class="v" style="font-size:14px;line-height:1.35;word-break:keep-all">${esc(m.rule || '2027-02-01부터 1,000명 + 8,000시간')}</div><div class="t">${m.at ? '스튜디오 ' + kst(m.at) : ''}</div></div></div>` : '';
  const rows = f ? (f.rows || []) : [];
  const fRows = rows.map(r => `<tr><td>${esc(r.src)}</td><td class="num">${pfNum(r.visits, '', 0)}</td><td class="num">${pfNum(r.deep, '', 0)}</td><td class="num">${pfNum(r.cta, '', 0)}</td><td class="num">${pfNum(r.emails, '', 0)}</td><td class="num">${pfNum(r.signups, '', 0)}</td><td class="num">${r.visits ? pfNum((r.signups || 0) / r.visits * 100, '%') : '–'}</td></tr>`).join('');
  const fHtml = rows.length ? `<div class="card" style="padding:0;overflow-x:auto;margin-bottom:8px"><table class="pf-tbl" style="width:100%;min-width:620px"><thead><tr><th>들어온 곳 (${esc(String(f.days || 7))}일)</th><th class="num">방문</th><th class="num">깊이 읽음</th><th class="num">가입 버튼</th><th class="num">이메일</th><th class="num">가입</th><th class="num">가입률</th></tr></thead><tbody>${fRows}</tbody></table></div>${f.note ? `<div class="note" style="margin:0 0 12px">${esc(f.note)}</div>` : ''}` : '';
  const bHtml = b.length ? `<div class="pf-find">${b.map(x => `<div class="card pf-f good"><b>${esc(x.title || x.id)}</b><p>${x.kind === 'long' ? '롱폼' : '쇼츠'} · 평소의 ${pfNum(x.ratio, '배')}${x.follow ? ' · ' + esc(x.follow) : ''}</p></div>`).join('')}</div>` : '';
  const aHtml = at ? `<div class="card" style="padding:12px 14px;margin:12px 0"><b>적정 매수가 도달 기록</b> · 누적 ${pfNum(at.count, '건', 0)}${at.ret30 != null ? ` · 30일 뒤 평균 ${pfNum(at.ret30, '%')}` : ''}${at.ret90 != null ? ` · 90일 뒤 평균 ${pfNum(at.ret90, '%')}` : ''}${at.note ? `<div class="bn-meta" style="margin-top:4px">${esc(at.note)}</div>` : ''}</div>` : '';
  return `${trackHtml ? `<div class="pf-sec"><h2>성장 목표선</h2><span>기본 · 잘 됨 시나리오와 실제 비교</span></div>${trackHtml}` : ''}
  ${monHtml ? `<div class="pf-sec"><h2>수익 창출까지</h2><span>2027-02-01부터 시청시간 8,000시간 기준</span></div>${monHtml}` : ''}
  ${fHtml ? `<div class="pf-sec"><h2>유튜브 → 밸류노트 다리</h2><span>들어온 곳별 방문 → 가입</span></div>${fHtml}` : ''}
  ${bHtml ? `<div class="pf-sec"><h2>터진 영상 · 48시간 후속</h2><span>평소의 3배 이상</span></div>${bHtml}` : ''}
  ${aHtml}`;
}

function vPerf(){
  if(PF.data === null){ perfLoad().then(() => render()); return head('롱폼 진단', '불러오는 중', 'perf'); }
  if(PF.err) return head('롱폼 진단', '', 'perf') + `<div class="card">불러오지 못했습니다: ${esc(PF.err)}</div>`;
  const reps = pfReports(), rep = pfCur(), d = rep ? rep.data : {}, k = d.kpis || {};
  d.findings = (d.findings || []).map(f => typeof f === 'string' ? { level: 'info', title: f, body: '' } : f);
  const seg = pfSeg(reps, 'perf-', 'perf', rep);
  const diag = {}; (d.videos || []).forEach(v => diag[v.id] = v);
  const longs = (PF.data.videos || []).filter(v => v.kind === 'long'), shorts = (PF.data.videos || []).filter(v => v.kind === 'short');
  const acts = d.actions || [], pend = acts.filter(a => (a.status || 'proposed') === 'proposed').length;
  const order = { bad: 0, warn: 1, info: 2, good: 3 };
  const shortRows = shorts.slice(0, 12).map(v => { const s = v.studio || {}; return `<tr><td style="max-width:340px;white-space:normal;word-break:keep-all">${esc(v.title)}</td><td>${kst(v.published_at)}</td><td class="num">${pfNum(s.views, '', 0)}</td><td class="num ${pfCls(s.viewed_pct, 70) ? 'pf-' + pfCls(s.viewed_pct, 70) : ''}">${pfNum(s.viewed_pct, '%')}</td><td class="num">${pfNum(s.avg_pct, '%')}</td><td class="num">${s.subs != null ? s.subs : '–'}</td></tr>`; }).join('');
  return `${head('롱폼 진단', '진단은 "오늘 진단 새로고침"을 누를 때만 작성(정규 회차 없음) · 승인한 개선은 다음 콘텐츠부터 반영' + (rep ? ` · 이 진단 ${kst(rep.at)}` : ''), 'perf')}
  ${seg}
  ${PF.msg ? `<div class="soc-flash ok">${esc(PF.msg)}</div>` : ''}
  ${rep ? '' : pfMissCard('롱폼 진단')}
  ${rep ? `<div class="card pf-hero"><div class="k">${esc(rep.id.slice(5))} 롱폼 진단 · ${esc(d.by || 'Claude')}</div><div class="h">${esc(d.headline || '스튜디오 지표를 모으기 전의 기록입니다. 아래 발견 사항만 참고하세요.')}</div>${d.sample_note ? `<div class="n">${esc(d.sample_note)}</div>` : ''}</div>
  <div class="pf-kpis">${pfKpi('썸네일 클릭률', k.ctr, '%', PF_GOAL.ctr)}${pfKpi('15초 유지율', k.s15, '%', PF_GOAL.s15)}${pfKpi('평균 조회율', k.avg_pct, '%', PF_GOAL.avg_pct)}${pfKpi('조회수', k.views, '회', 0, `롱폼 ${k.longs || '–'}편 · 노출 ${pfNum(k.impressions, '회', 0)}`)}${pfKpi('구독 증가', k.subs, '명', 0, `평균 시청 ${pfSec(k.avg_sec)}`)}</div>

  ${pfGrowth(d)}

  <div class="pf-sec"><h2>지금 결정할 개선 ${pend ? `<span class="pf-st run" style="margin-left:6px">${pend}건 대기</span>` : ''}</h2><span>승인하면 다음 콘텐츠부터 · 메모를 쓰면 그 방향으로 고쳐서</span></div>
  ${pend > 1 ? `<div class="pf-all"><button class="pf-btn" data-pfa-all="${esc(rep.id)}">대기 ${pend}건 전부 적용</button></div>` : ''}
  ${acts.length ? acts.map((a, i) => [a, i]).sort((x, y) => ((x[0].status || 'proposed') === 'proposed' ? 0 : 1) - ((y[0].status || 'proposed') === 'proposed' ? 0 : 1) || (y[0].impact || 0) - (x[0].impact || 0)).map(([a, i]) => pfAction(a, i, rep.id)).join('') : '<div class="card pf-empty" style="padding:14px">이 날은 새 개선 제안이 없습니다.</div>'}

  <div class="pf-sec"><h2>대표님 피드백</h2><span>남기면 다음 진단·제작 작업이 읽고 반영 후 답을 답니다</span></div>
  <div class="card pf-fb"><textarea placeholder="진단이나 영상 방향에 대한 의견을 자유롭게 (예: 인트로는 머니스웨거처럼 결론부터, 썸네일엔 인물 얼굴 더 많이)" data-pf-fb></textarea>
    <div class="pf-chips">${['인트로를 더 짧고 세게', '썸네일 더 자극적으로(과장 없이)', '숫자 줄이고 이야기 위주로', '다음 롱폼에 바로 반영', '이 진단 방향 좋음'].map(t => `<button type="button" data-pf-chip="${esc(t)}">${esc(t)}</button>`).join('')}</div>
    <div class="pf-ctl" style="margin-top:0"><span class="bn-meta" style="flex:1">급한 건 채팅에 "성과 피드백 지금 반영"이라고 남기면 바로 처리합니다.</span><button class="pf-btn" data-pf-send>피드백 보내기</button></div>
    ${pfInboxHtml('long')}</div>

  <div class="pf-sec"><h2>무엇이 문제인가</h2><span>${(d.findings || []).length}가지 발견</span></div>
  <div class="pf-find">${(d.findings || []).slice().sort((a, b) => (order[a.level] ?? 9) - (order[b.level] ?? 9)).map(f => `<div class="card pf-f ${esc(f.level)}"><b>${esc(f.title)}</b>${f.body ? `<p>${esc(f.body)}</p>` : ''}${f.evidence ? `<small>근거 · ${esc(f.evidence)}</small>` : ''}</div>`).join('')}</div>` : `<div class="card pf-empty" style="padding:14px">아직 진단이 없습니다. 매일 20:52에 올라옵니다.</div>`}

  <div class="pf-sec"><h2>추이</h2><span>진단마다 한 점</span></div>
  ${pfTrend(reps)}

  <div class="pf-sec"><h2>롱폼 영상별 진단</h2><span>최근 30일 · ${longs.length}편 · 숫자는 최신 스튜디오 지표</span></div>
  ${longs.length ? longs.map(v => pfVideo(v, diag[v.id])).join('') : '<div class="card pf-empty" style="padding:14px">올라간 롱폼이 없습니다.</div>'}

  ${shorts.length ? `<div class="pf-sec"><h2>쇼츠 지표</h2><span>자세한 진단은 <a href="#perfs">숏폼 진단</a>에서</span></div>
  <div class="card" style="padding:0;overflow-x:auto"><table class="pf-tbl" style="width:100%;min-width:620px"><thead><tr><th>쇼츠</th><th>공개</th><th class="num">조회</th><th class="num">조회함 비율</th><th class="num">평균 조회율</th><th class="num">구독</th></tr></thead><tbody>${shortRows}</tbody></table></div>` : ''}
  <div class="pf-goal">목표 기준 · 썸네일 클릭률 ${PF_GOAL.ctr}% 이상 · 15초 유지율 ${PF_GOAL.s15}% 이상 · 평균 조회율 ${PF_GOAL.avg_pct}% 이상 (구독자 수만 명 규모 금융 채널의 무난한 수준). 조회 300회 미만 영상은 표본이 작아 방향만 봅니다.</div>`;
}

/* ───────── 숏폼 진단 (2026-10-30 운영자: "현재 관리자 페이지에 롱폼 진단은 되어있는데 숏폼 진단도 추가해줘")
   데이터: rpc perf_admin() → perfs: docs agent 'perfs-YYYY-MM-DD' 최근 14개 (매일 05:37 개선 작업이 쓴다), videos: yt_perf(30) 중 kind 'short'
   보고서 형식은 롱폼과 같다 (headline · kpis · findings · videos · actions). 승인한 개선은 다음 날 05:37 작업이 쇼츠·릴스 제작 기준(scripts/reels/README.md)과
   자동 검수 기준(docs agent 'auto-review-rules')에 넣는다. 보고서가 아직 없어도 스튜디오 지표는 바로 보인다. 피드백은 perf-inbox에 channel 'short'로 쌓인다. */
const PFS_GOAL = { viewed_pct: 60, avg_pct: 60, sub_k: 2 };
function pfsReports(){ return (PF.data && PF.data.perfs || []).filter(x => /^perfs-\d{4}-\d{2}-\d{2}$/.test(x.id)); }
function pfsCur(){ const reps = pfsReports(); const want = 'perfs-' + subPage(); return reps.find(x => x.id === want) || (/^\d{4}-\d{2}-\d{2}$/.test(subPage()) ? null : reps[0] || null); }
function pfsPending(){ const r = pfsReports()[0]; return r ? (r.data.actions || []).filter(a => (a.status || 'proposed') === 'proposed').length : 0; }
function pfsApct(s, dur){ return s.avg_pct != null ? +s.avg_pct : s.avg_sec != null && dur ? Math.round(s.avg_sec / dur * 1000) / 10 : null; }
/* 보고서가 없을 때(또는 보고서 뒤로 새 지표가 들어왔을 때) 최근 7일 스튜디오 지표로 바로 계산 */
function pfsLive(shorts){
  const wk = shorts.filter(v => v.studio && (v.age_h == null || v.age_h <= 24 * 7)), n = wk.length;
  const views = wk.reduce((a, v) => a + (+v.studio.views || 0), 0), subs = wk.reduce((a, v) => a + (+v.studio.subs || 0), 0);
  const wv = wk.filter(v => v.studio.viewed_pct != null), vp = wv.reduce((a, v) => a + (+v.studio.views || 0), 0);
  const viewed_pct = vp ? Math.round(wv.reduce((a, v) => a + v.studio.viewed_pct * (+v.studio.views || 0), 0) / vp * 10) / 10 : null;
  const ap = wk.map(v => pfsApct(v.studio, v.studio.duration_sec || v.duration)).filter(x => x != null);
  return { shorts: n, views, subs, viewed_pct, avg_pct: ap.length ? Math.round(ap.reduce((a, b) => a + b, 0) / ap.length * 10) / 10 : null,
    sub_k: views ? Math.round(subs / views * 10000) / 10 : null, missing: shorts.filter(v => (v.age_h == null || v.age_h <= 24 * 7) && !v.studio && (v.age_h || 0) >= 20).length };
}
function pfsVideo(v, diag){
  const s = v.studio || {}, d = diag || {}, ret = s.retention || d.retention, dur = s.duration_sec || d.duration_sec || v.duration;
  const vp = s.viewed_pct ?? d.viewed_pct, ap = pfsApct(s, dur) ?? d.avg_pct, views = s.views ?? d.views;
  const vr = s.valid_views && s.views ? Math.round(s.valid_views / s.views * 100) : d.valid_rate;
  const feed = (s.sources || {})['Shorts 피드'], subk = views && s.subs != null ? Math.round(s.subs / views * 10000) / 10 : null;
  const verdict = d.verdict || (!s.at ? '' : pfCls(vp, PFS_GOAL.viewed_pct) === 'bad' || pfCls(ap, PFS_GOAL.avg_pct) === 'bad' ? 'bad' : pfCls(vp, PFS_GOAL.viewed_pct) === 'ok' && pfCls(ap, PFS_GOAL.avg_pct) === 'ok' ? 'ok' : 'warn');
  const vdTxt = { bad: '개선 시급', warn: '보완 필요', ok: '양호' }[verdict] || '';
  const yid = v.youtube_id || d.youtube_id, link = yid ? `https://studio.youtube.com/video/${yid}/analytics/tab-overview/period-default` : '#';
  const m = [
    ['조회', pfNum(views, '회', 0), ''],
    ['조회함 비율', pfNum(vp, '%'), pfCls(vp, PFS_GOAL.viewed_pct)],
    ['평균 시청', pfSec(s.avg_sec ?? d.avg_sec) + (dur ? ' / ' + pfSec(dur) : ''), ''],
    ['평균 조회율', pfNum(ap, '%'), pfCls(ap, PFS_GOAL.avg_pct)],
    vr != null ? ['유효 조회', vr + '%', ''] : null,
    s.subs != null ? ['구독', (+s.subs > 0 ? '+' : '') + s.subs + (subk != null ? ` (1천 회당 ${subk})` : ''), pfCls(subk, PFS_GOAL.sub_k)] : null,
    feed != null ? ['Shorts 피드', pfNum(feed, '%'), ''] : null
  ].filter(Boolean);
  const age = v.age_h != null ? (v.age_h >= 48 ? Math.round(v.age_h / 24) + '일째' : v.age_h + '시간째') : '';
  const thumb = yid ? `<img src="https://i.ytimg.com/vi/${esc(yid)}/oardefault.jpg" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='https://i.ytimg.com/vi/${esc(yid)}/hqdefault.jpg'">` : '';
  const curve = pfRetSvg(ret, dur);
  return `<div class="card pf-vid sh" data-pfv="${esc(v.id)}">
    <a class="th" href="${link}" target="_blank" rel="noopener">${thumb}${vdTxt ? `<span class="vd ${verdict}">${vdTxt}</span>` : ''}</a>
    <div>
      <a class="tt" href="${link}" target="_blank" rel="noopener">${esc(v.title || d.title || v.id)}</a>
      <div class="bn-meta">${v.published_at ? kst(v.published_at) + ' 공개' : ''}${age ? ' · ' + age : ''}${s.at ? ' · 지표 ' + kst(s.at) : ' · 스튜디오 지표 미수집'}${!yid ? ' · youtube_id 없음' : ''}</div>
      <div class="pf-m">${m.map(([k, val, c]) => `<span class="${c}">${k} ${val}</span>`).join('')}</div>
      <div class="pf-two"><div class="pf-ret"><div class="cap">시청 지속 곡선</div>${curve || `<div class="pf-empty">${esc((ret && ret.note) || (s.at ? '아직 곡선이 나오지 않았습니다 (최대 2일)' : '지표 수집 전'))}</div>`}${ret && ret.dips && ret.dips.length ? `<div class="bn-meta" style="margin-top:4px">급락 구간 · ${ret.dips.slice(0, 3).map(x => esc(x.t + ' ' + (x.note || ''))).join(' · ')}</div>` : ''}</div>${pfSrc(s.sources || d.sources) || '<div></div>'}</div>
      ${(d.issues || []).length || (d.good || []).length ? `<ul class="pf-li">${(d.issues || []).map(x => `<li class="b">${esc(x)}</li>`).join('')}${(d.good || []).map(x => `<li class="g">${esc(x)}</li>`).join('')}</ul>` : ''}
      <div class="pf-vfb"><input type="text" placeholder="이 쇼츠에 대한 의견 (예: 첫 장면 숫자를 더 크게, 끝맺음이 길어)" data-pfv-note>
        <button class="pf-btn ghost" data-pfv-kind="thumb">썸네일 교체 요청</button><button class="pf-btn ghost" data-pfv-kind="title">제목 교체 요청</button><button class="pf-btn ghost" data-pfv-kind="keep">이 방식 유지</button><button class="pf-btn" data-pfv-kind="note">의견 보내기</button></div>
    </div></div>`;
}
function pfsTrend(reps){
  const pts = reps.slice().reverse().map(r => ({ d: r.id.slice(11), k: r.data.kpis || {} })).filter(p => p.k.viewed_pct != null || p.k.avg_pct != null);
  if(pts.length < 2) return `<div class="card pf-trend"><div class="pf-empty">추이는 진단이 이틀 이상 쌓이면 그려집니다. 매일 05:37 진단이 하나씩 쌓입니다.</div></div>`;
  const W = 640, H = 170, L = 30, R = 12, T = 10, B = 22, n = pts.length;
  const X = i => L + i / (n - 1) * (W - L - R), Y = v => T + (100 - Math.min(100, v)) / 100 * (H - T - B);
  const path = f => pts.map((p, i) => f(p) == null ? '' : `${i && f(pts[i - 1]) != null ? 'L' : 'M'}${X(i).toFixed(1)},${Y(f(p)).toFixed(1)}`).join('');
  return `<div class="card pf-trend"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="숏폼 성과 추이">
    ${[0, 50, 100].map(v => `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--grid)"/><text x="${L - 4}" y="${Y(v) + 3}" font-size="9" text-anchor="end" fill="var(--muted)">${v}%</text>`).join('')}
    <path d="${path(p => p.k.viewed_pct)}" fill="none" stroke="var(--s-visit)" stroke-width="2.2"/>
    <path d="${path(p => p.k.avg_pct)}" fill="none" stroke="#E0A526" stroke-width="2.2"/>
    ${pts.map((p, i) => `<text x="${X(i)}" y="${H - 6}" font-size="9" text-anchor="middle" fill="var(--muted)">${p.d.slice(3).replace('-', '/')}</text>`).join('')}
  </svg><div class="lg"><span><i style="background:var(--s-visit)"></i>조회함 비율</span><span><i style="background:#E0A526"></i>평균 조회율</span></div></div>`;
}
function vPerfs(){
  if(PF.data === null){ perfLoad().then(() => render()); return head('숏폼 진단', '불러오는 중', 'perfs'); }
  if(PF.err) return head('숏폼 진단', '', 'perfs') + `<div class="card">불러오지 못했습니다: ${esc(PF.err)}</div>`;
  const reps = pfsReports(), rep = pfsCur(), d = rep ? rep.data : {};
  d.findings = (d.findings || []).map(f => typeof f === 'string' ? { level: 'info', title: f, body: '' } : f);
  const shorts = (PF.data.videos || []).filter(v => v.kind === 'short').sort((a, b) => String(b.published_at).localeCompare(String(a.published_at)));
  const live = pfsLive(shorts), k = Object.keys(d.kpis || {}).length ? d.kpis : live, isLive = !Object.keys(d.kpis || {}).length;
  const seg = pfSeg(reps, 'perfs-', 'perfs', rep);
  const diag = {}; (d.videos || []).forEach(v => diag[v.id] = v);
  const acts = d.actions || [], pend = acts.filter(a => (a.status || 'proposed') === 'proposed').length;
  const order = { bad: 0, warn: 1, info: 2, good: 3 };
  const withData = shorts.filter(v => v.studio), noData = shorts.filter(v => !v.studio);
  const reels = d.reels || [];
  return `${head('숏폼 진단', '쇼츠·릴스 진단은 "오늘 진단 새로고침"을 누를 때만 작성(정규 회차 없음) · 승인한 개선은 다음 쇼츠·릴스부터 반영' + (rep ? ` · 이 진단 ${kst(rep.at)}` : ''), 'perfs')}
  ${seg}
  ${PF.msg ? `<div class="soc-flash ok">${esc(PF.msg)}</div>` : ''}
  ${rep ? '' : pfMissCard('숏폼 진단')}
  <div class="card pf-hero"><div class="k">${rep ? esc(rep.id.slice(6)) + ' 숏폼 진단 · ' + esc(d.by || 'Claude') : '실시간 지표 · 최근 7일'}</div>
    <div class="h">${esc(rep ? (d.headline || '') : `최근 7일 쇼츠 ${live.shorts}편 조회 ${pfNum(live.views, '회', 0)} · 조회함 비율 ${pfNum(live.viewed_pct, '%')} — 진단은 '오늘 진단 새로고침'을 누르면 작성됩니다.`)}</div>
    ${d.sample_note || live.missing ? `<div class="n">${esc(d.sample_note || '')}${live.missing ? `${d.sample_note ? ' · ' : ''}올린 지 하루가 지났는데 스튜디오 지표가 없는 쇼츠 ${live.missing}편 (업로드 작업 20:10 회차가 모읍니다)` : ''}</div>` : ''}</div>
  <div class="pf-kpis">${pfKpi('조회함 비율', k.viewed_pct, '%', PFS_GOAL.viewed_pct)}${pfKpi('평균 조회율', k.avg_pct, '%', PFS_GOAL.avg_pct)}${pfKpi('1천 회당 구독', k.sub_k, '명', PFS_GOAL.sub_k)}${pfKpi('조회수', k.views, '회', 0, `쇼츠 ${k.shorts ?? '–'}편${k.reels != null ? ` · 릴스 ${k.reels}편` : ''}${isLive ? ' · 실시간' : ''}`)}${pfKpi('구독 증가', k.subs, '명', 0, k.best ? `최고 ${esc(k.best)}` : '최근 7일')}</div>

  <div class="pf-sec"><h2>지금 결정할 개선 ${pend ? `<span class="pf-st run" style="margin-left:6px">${pend}건 대기</span>` : ''}</h2><span>승인하면 다음 쇼츠·릴스부터 · 메모를 쓰면 그 방향으로 고쳐서</span></div>
  ${pend > 1 ? `<div class="pf-all"><button class="pf-btn" data-pfa-all="${esc(rep.id)}">대기 ${pend}건 전부 적용</button></div>` : ''}
  ${rep ? (acts.length ? acts.map((a, i) => [a, i]).sort((x, y) => ((x[0].status || 'proposed') === 'proposed' ? 0 : 1) - ((y[0].status || 'proposed') === 'proposed' ? 0 : 1) || (y[0].impact || 0) - (x[0].impact || 0)).map(([a, i]) => pfAction(a, i, rep.id)).join('') : '<div class="card pf-empty" style="padding:14px">이 날은 새 개선 제안이 없습니다.</div>') : '<div class="card pf-empty" style="padding:14px">아직 진단이 없습니다. 매일 05:37에 올라옵니다.</div>'}

  <div class="pf-sec"><h2>대표님 피드백</h2><span>남기면 다음 날 05:37 작업이 쇼츠·릴스 기준에 넣고 답을 답니다</span></div>
  <div class="card pf-fb"><textarea placeholder="쇼츠·릴스 방향에 대한 의견을 자유롭게 (예: 첫 2초에 회사 이름과 숫자 같이, 끝맺음은 더 짧게)" data-pf-fb></textarea>
    <div class="pf-chips">${['첫 2초 훅을 더 세게', '전환을 더 부드럽게', '끝맺음 더 짧게', '숫자 줄이고 이야기 위주로', '이 진단 방향 좋음'].map(t => `<button type="button" data-pf-chip="${esc(t)}">${esc(t)}</button>`).join('')}</div>
    <div class="pf-ctl" style="margin-top:0"><span class="bn-meta" style="flex:1">급한 건 채팅에 "숏폼 피드백 지금 반영"이라고 남기면 바로 처리합니다.</span><button class="pf-btn" data-pf-send>피드백 보내기</button></div>
    ${pfInboxHtml('short')}</div>

  ${rep ? `<div class="pf-sec"><h2>무엇이 문제인가</h2><span>${d.findings.length}가지 발견</span></div>
  <div class="pf-find">${d.findings.slice().sort((a, b) => (order[a.level] ?? 9) - (order[b.level] ?? 9)).map(f => `<div class="card pf-f ${esc(f.level)}"><b>${esc(f.title)}</b>${f.body ? `<p>${esc(f.body)}</p>` : ''}${f.evidence ? `<small>근거 · ${esc(f.evidence)}</small>` : ''}</div>`).join('')}</div>` : ''}

  <div class="pf-sec"><h2>추이</h2><span>진단마다 한 점</span></div>
  ${pfsTrend(reps)}

  <div class="pf-sec"><h2>쇼츠 영상별 진단</h2><span>최근 30일 · 지표 있는 ${withData.length}편 · 숫자는 최신 스튜디오 지표</span></div>
  ${withData.length ? withData.map(v => pfsVideo(v, diag[v.id])).join('') : '<div class="card pf-empty" style="padding:14px">아직 스튜디오 지표가 들어온 쇼츠가 없습니다.</div>'}
  ${noData.length ? `<details class="card" style="padding:12px 14px;margin-top:4px"><summary style="cursor:pointer;font-weight:800;font-size:13.5px">지표 미수집 쇼츠 ${noData.length}편</summary><table class="pf-tbl" style="width:100%;margin-top:8px"><tbody>${noData.map(v => `<tr><td style="white-space:normal;word-break:keep-all">${esc(v.title)}</td><td>${kst(v.published_at)}</td><td>${v.youtube_id ? '' : '<span class="pf-bad">youtube_id 없음</span>'}</td></tr>`).join('')}</tbody></table></details>` : ''}

  ${reels.length ? `<div class="pf-sec"><h2>인스타 릴스</h2><span>진단에 들어간 릴스 · 보이는 숫자만</span></div>
  <div class="card" style="padding:0;overflow-x:auto"><table class="pf-tbl" style="width:100%;min-width:620px"><thead><tr><th>릴스</th><th>게시</th><th class="num">조회·도달</th><th class="num">좋아요</th><th class="num">댓글</th><th class="num">저장</th><th>판정</th></tr></thead><tbody>${reels.map(r => `<tr><td style="max-width:340px;white-space:normal;word-break:keep-all">${esc(r.title || r.id)}</td><td>${r.posted_at ? kst(r.posted_at) : '–'}</td><td class="num">${pfNum(r.views ?? r.reach, '', 0)}</td><td class="num">${pfNum(r.likes, '', 0)}</td><td class="num">${pfNum(r.comments, '', 0)}</td><td class="num">${pfNum(r.saves, '', 0)}</td><td>${esc(r.note || '')}</td></tr>`).join('')}</tbody></table></div>` : ''}
  <div class="pf-goal">목표 기준 · 조회함 비율(피드에서 넘기지 않고 본 비율) ${PFS_GOAL.viewed_pct}% 이상 · 평균 조회율 ${PFS_GOAL.avg_pct}% 이상 · 조회 1천 회당 구독 ${PFS_GOAL.sub_k}명 이상. 조회 300회 미만 쇼츠는 표본이 작아 방향만 봅니다.</div>`;
}
async function pfSaveReport(repId, f, msg){
  const r = pfReports().find(x => x.id === repId) || pfsReports().find(x => x.id === repId); if(!r) return;
  const data = JSON.parse(JSON.stringify(r.data || {})); f(data);
  const { error } = await sb.from('docs').update({ data, updated_at: new Date().toISOString() }).eq('collection', 'agent').eq('id', repId);
  if(error){ toast('저장하지 못했습니다: ' + error.message, true); return; }
  r.data = data; PF.msg = ''; toast(msg); render();
}
async function pfAddInbox(item){
  const cur = PF.inbox && PF.inbox.data ? PF.inbox.data : { items: [] };
  const data = { ...cur, items: [...(cur.items || []), { id: 'f' + Date.now().toString(36), at: new Date().toISOString(), status: 'new', ...item }] };
  const q = PF.inbox && PF.inbox.updated_at ? sb.from('docs').update({ data, updated_at: new Date().toISOString() }).eq('collection', 'agent').eq('id', 'perf-inbox')
    : sb.from('docs').upsert({ owner: (await sb.auth.getUser()).data.user.id, collection: 'agent', id: 'perf-inbox', data, updated_at: new Date().toISOString() });
  const { error } = await q;
  if(error){ toast('보내지 못했습니다: ' + error.message, true); return false; }
  PF.inbox = { ...(PF.inbox || {}), id: 'perf-inbox', data, updated_at: new Date().toISOString() }; return true;
}
function bindPerf(){
  const box = $('#main');
  box.querySelectorAll('[data-pfa-to]').forEach(b => b.onclick = () => {
    const w = b.closest('[data-pfa]'), i = +w.dataset.pfa, rep = w.dataset.rep, to = b.dataset.pfaTo;
    const note = ((w.querySelector('[data-pfa-note]') || {}).value || '').trim();
    pfSaveReport(rep, d => { const a = d.actions[i]; a.status = to; a.decided_at = new Date().toISOString(); a.decided_by = 'owner'; if(note) a.owner_note = note; },
      to === 'approved' ? (note ? '메모대로 고쳐서 적용합니다.' : '승인했습니다. 다음 콘텐츠부터 적용합니다.') : to === 'hold' ? '보류했습니다.' : to === 'rejected' ? '반려했습니다. 비슷한 제안은 다시 올리지 않습니다.' : '승인을 취소했습니다.');
  });
  box.querySelectorAll('[data-pfa-all]').forEach(b => b.onclick = () => {
    if(!confirm('대기 중인 개선을 전부 다음 콘텐츠부터 적용할까요?')) return;
    pfSaveReport(b.dataset.pfaAll, d => { (d.actions || []).forEach(a => { if((a.status || 'proposed') === 'proposed'){ a.status = 'approved'; a.decided_at = new Date().toISOString(); a.decided_by = 'owner'; } }); }, '전부 승인했습니다. 다음 콘텐츠부터 적용합니다.');
  });
  box.querySelectorAll('[data-pf-refresh]').forEach(b => b.onclick = async () => { b.disabled = true; await pfRequestRefresh(b.dataset.pfRefresh, b.dataset.pfDay.split(',')); b.disabled = false; });
  box.querySelectorAll('[data-pf-chip]').forEach(b => b.onclick = () => { const t = box.querySelector('[data-pf-fb]'); t.value = (t.value ? t.value.trim() + '\n' : '') + b.dataset.pfChip; t.focus(); });
  const send = box.querySelector('[data-pf-send]');
  if(send) send.onclick = async () => { const t = box.querySelector('[data-pf-fb]'), text = (t.value || '').trim(); if(!text){ t.focus(); return; }
    send.disabled = true; const rep = pfCur(); const sh = page() === 'perfs', cr = sh ? pfsCur() : rep; if(await pfAddInbox({ kind: 'general', text, report: cr ? cr.id : null, channel: sh ? 'short' : 'long' })){ toast('피드백을 남겼습니다. 다음 작업부터 반영합니다.'); render(); } send.disabled = false; };
  box.querySelectorAll('[data-pfv-kind]').forEach(b => b.onclick = async () => {
    const w = b.closest('[data-pfv]'), id = w.dataset.pfv, kind = b.dataset.pfvKind, inp = w.querySelector('[data-pfv-note]'), note = (inp.value || '').trim();
    const v = (PF.data.videos || []).find(x => x.id === id) || {};
    if(kind === 'note' && !note){ inp.focus(); return; }
    const def = { thumb: '썸네일을 다른 안으로 바꿔 주세요', title: '제목을 다른 안으로 바꿔 주세요', keep: '이 영상 방식은 좋으니 유지해 주세요' }[kind];
    b.disabled = true;
    if(await pfAddInbox({ kind, text: note || def, video_id: id, youtube_id: v.youtube_id || null, video_title: v.title || id, channel: v.kind === 'short' ? 'short' : 'long' })){ toast(kind === 'thumb' || kind === 'title' ? '요청을 남겼습니다. 업로드 작업이 스튜디오에서 바꿉니다.' : '의견을 남겼습니다.'); render(); }
    b.disabled = false;
  });
}

