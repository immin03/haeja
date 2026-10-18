// 밸류노트 점수(앱 index.html과 같은 계산): 숫자(품질 40%·저평가 60% − 위험 신호) 65% + 정성 평가 20% + 트렌드 15%
// 정성 평가는 밸류노트 공용 평가(profiles 문서의 qual). 없으면 빈 항목을 빼고 나머지로 다시 나눈다.
// index.html의 TREND_KW·autoTrendLinks·trendScore·qualScoreOf·vnTotal을 그대로 옮긴 것이므로 바꿀 때 둘 다 고친다.
const isNum = (x) => typeof x === 'number' && isFinite(x);
const TREND_KW = [
  [/semiconductor/i, {ai_compute_datacenter:2, memory_hbm_supercycle:1}],
  [/electrical equipment|utilities|uranium|specialty industrial machinery|electric/i, {power_grid_nuclear:2}],
  [/aerospace|defense/i, {defense_rearmament:2, space_economy:1}],
  [/software - infrastructure|information technology services|communication equipment|computer hardware|electronic components/i, {ai_compute_datacenter:2}],
  [/biotechnology|drug manufacturers/i, {obesity_glp1:1}],
  [/marine|shipbuild|ship/i, {shipbuilding_masga:2}],
  [/robot|industrial automation/i, {physical_ai_robotics:2}],
];
export function makeVN(trends, profiles) {
  const tl = (trends && trends.trends) || [];
  const idx = {};
  tl.forEach((t) => Object.values(t.beneficiaries || {}).flat().forEach((b) => {
    const mm = String(b).match(/\(([^)]+)\)/); if (!mm) return;
    mm[1].split('/').forEach((code) => {
      const k = code.trim().toUpperCase().replace(/\.SH$/, '.SS');
      (idx[k] ||= {})[t.key] = 3;
      const bare = k.replace(/\.(SS|SZ|HK|KS|KQ)$/, ''); (idx[bare] ||= {})[t.key] = 3;
    });
  }));
  const links = (r) => {
    const L = { ...(idx[(r.t || '').toUpperCase()] || {}), ...(idx[(r.code || '').toUpperCase()] || {}) };
    const text = (r.ind || '') + ' ' + (r.s || '');
    TREND_KW.forEach(([re, ks]) => { if (re.test(text)) Object.entries(ks).forEach(([k, v]) => { L[k] = Math.max(L[k] || 0, v); }); });
    if ((r.m === 'CN' || r.m === 'HK') && /technology|semiconductor|software|internet/i.test(text)) L.china_tech_selfreliance = Math.max(L.china_tech_selfreliance || 0, 2);
    if ((r.m === 'KOSPI' || r.m === 'KOSDAQ' || r.m === 'KR') && /bank|insurance|capital markets|financial/i.test(text)) L.korea_valueup_governance = Math.max(L.korea_valueup_governance || 0, 1);
    return L;
  };
  const trendScore = (L) => {
    if (!tl.length) return null;
    const hits = Object.entries(L).filter(([, s]) => s > 0).map(([k, s]) => ({ t: tl.find((x) => x.key === k), s })).filter((x) => x.t);
    if (!hits.length) return null;
    return Math.round(100 * Math.max(...hits.map(({ t, s }) => s / 3 * (0.4 + 0.6 * ((t.momentum ?? 0) + 2) / 4))));
  };
  const qualScoreOf = (q) => {
    if (!q) return null; let qin = 0, qsum = 0;
    [['moatStr', 35], ['pricing', 20], ['mgmt', 25], ['governance', 20]].forEach(([k, w]) => { if (isNum(q[k])) { qin += w; qsum += q[k] / 3 * w; } });
    let s = qin ? Math.round(qsum / qin * 100) : null; if (s !== null && q.hold10 === false) s = Math.max(0, s - 15); return s;
  };
  const norm = (k) => String(k || '').toUpperCase();
  const prof = {}; for (const [k, v] of Object.entries(profiles || {})) prof[norm(k)] = v;
  return function vn(r, sc) {
    const P = prof[norm(r.t)]; const qs = qualScoreOf(P?.qual);
    const ts = trendScore(P?.trendLinks && Object.keys(P.trendLinks).length ? P.trendLinks : links(r)); // 조사한 트렌드 연결이 있으면 그것을, 없으면 업종으로 자동 연결
    let total = null;
    if (isNum(sc.b)) { const parts = [[sc.b, 0.65], [qs, 0.20], [ts, 0.15]].filter(([x]) => isNum(x)); total = Math.round(parts.reduce((a, [x, w]) => a + x * w, 0) / parts.reduce((a, [, w]) => a + w, 0)); }
    return { total, qual: qs, trend: ts, qualDone: qs !== null };
  };
}
