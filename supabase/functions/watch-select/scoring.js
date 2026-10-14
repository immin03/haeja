// @ts-nocheck
// moat-ledger.html(가치노트 화면)의 점수 계산 코드를 그대로 옮겨 온 것. 화면과 같은 점수를 내야 하므로 손으로 고치지 말고 scripts/sync_scoring.py로 다시 생성한다.
const isNum = v => typeof v === 'number' && isFinite(v);
const DEF_SETTINGS = { fx:1339, fxCNY:188, fxHKD:172, fxJPY:9.3, cashKRW:0, reqMOS:30, discKR:10, discUS:10, discCN:11, discHK:11, discJP:9, tgKR:2, tgUS:2.5, tgCN:2, tgHK:2, tgJP:1.5, bondKR:4.3, bondUS:5.2, bondCN:1.8, bondHK:4.2, bondJP:1.7 };
let __st = {...DEF_SETTINGS};
export function setSettings(s){ __st = {...DEF_SETTINGS, ...(s||{})}; }
const cfg = () => __st;
const BANDS = {
  roeAvg:{US:[5,15,25],KR:[3,12,20],w:2,dir:'up'}, roeMin:{US:[0,10,18],KR:[0,8,15],w:2,dir:'up'},
  roic:{US:[4,15,25],KR:[3,10,20],w:2,dir:'up'}, gpm:{US:[15,40,60],KR:[10,30,50],w:1,dir:'up'},
  npm:{US:[2,10,20],KR:[1,8,15],w:1,dir:'up'}, epsCagr:{US:[-5,7,15],KR:[-5,7,15],w:1,dir:'up'},
  lossYears:{US:[2,0,0],KR:[2,0,0],w:2,dir:'down'}, fcfConv:{US:[30,80,110],KR:[30,80,110],w:2,dir:'up'},
  capexNi:{US:[120,50,25],KR:[120,50,25],w:1,dir:'down'}, ltdNi:{US:[8,4,1],KR:[8,4,1],w:2,dir:'down'},
  icr:{US:[2,7,20],KR:[2,7,20],w:1,dir:'up'}, currentRatio:{US:[0.8,1.5,2.5],KR:[0.8,1.5,2.5],w:1,dir:'up'},
  shareChg:{US:[10,0,-5],KR:[10,0,-5],w:1,dir:'down'},
};
const MKT = {US:{label:'미국',cur:'USD',grp:'US'}, KR:{label:'국내',cur:'KRW',grp:'KR'}, KOSPI:{label:'코스피',cur:'KRW',grp:'KR'}, KOSDAQ:{label:'코스닥',cur:'KRW',grp:'KR'}, CN:{label:'중국 A',cur:'CNY',grp:'CN'}, HK:{label:'홍콩',cur:'HKD',grp:'HK'}, JP:{label:'일본',cur:'JPY',grp:'JP'}};
const grpOf = m => (MKT[m]||MKT.KR).grp;
const thSet = m => grpOf(m) === 'US' ? 'US' : 'KR';
function paramsFor(m){
  const st = cfg(), g = grpOf(m);
  if(g==='US') return {disc:st.discUS, tg:st.tgUS, bond:st.bondUS};
  if(g==='CN') return {disc:st.discCN, tg:st.tgCN, bond:st.bondCN};
  if(g==='HK') return {disc:st.discHK, tg:st.tgHK, bond:st.bondHK};
  if(g==='JP') return {disc:st.discJP, tg:st.tgJP, bond:st.bondJP};
  return {disc:st.discKR, tg:st.tgKR, bond:st.bondKR};
}
function metricScore(k, v, ts){
  if(!isNum(v)) return null; const b = BANDS[k]; const [bad, th, great] = b[ts];
  if(k === 'lossYears') return v <= 0 ? 1 : v <= 1 ? 0.4 : 0;
  if(b.dir === 'up'){ if(v<=bad) return 0; if(v<=th) return 0.7*(v-bad)/(th-bad); if(v>=great) return 1; return 0.7+0.3*(v-th)/(great-th); }
  if(v>=bad) return 0; if(v>=th) return 0.7*(bad-v)/(bad-th); if(v<=great) return 1; return 0.7+0.3*(th-v)/(th-great);
}
function lin(v, lo, mid, hi){ if(!isNum(v)) return null; if(v<=lo) return 0; if(v<=mid) return 0.7*(v-lo)/(mid-lo); if(v>=hi) return 1; return 0.7+0.3*(v-mid)/(hi-mid); }
function dcfValue(oeps, growth, disc, tg){
  if(!isNum(oeps) || !isNum(growth) || oeps <= 0 || disc <= tg) return null;
  const r = disc/100, t = tg/100, g = Math.max(Math.min(growth,20),-10)/100; let s = 0, e = oeps;
  for(let y=1;y<=10;y++){ e *= (1+g); s += e/Math.pow(1+r,y); }
  return s + (e*(1+t)/(r-t))/Math.pow(1+r,10);
}
/* 품질(q)·저평가(v)·버핏 근접도(b). row = {m, px, fin, val, fin_sector} */
const WARN_FLAGS = new Set(['경기순환·이익 변동','지주회사','주식보상 큼','혁신 의존']);
const FIN_SKIP = new Set(['gpm','fcfConv','capexNi','ltdNi','icr','currentRatio','roic']);
const CYC_RE = /auto|steel|oil|gas|energy|airline|shipping|marine|homebuild|residential construction|chemical|mining|metal|commodit|자동차|철강|정유|석유|해운|항공|건설|화학|광업|조선/i;
/* 품질(q)·저평가(v)·버핏 근접도(b). row = {m, px, fin, val, fin_sector, s, ind, sector} — screener.py score_row와 동일 */
function scoreRow(row, p, reqMOS){
  p = p || paramsFor(row.m); reqMOS = reqMOS ?? cfg().reqMOS; const ts = thSet(row.m);
  const fin = row.fin || {}, val = row.val || {};
  let wsum=0, wall=0, acc=0;
  for(const k in BANDS){ if(row.fin_sector && FIN_SKIP.has(k)) continue; wall += BANDS[k].w; const s = metricScore(k, fin[k], ts); if(s===null) continue; wsum += BANDS[k].w; acc += s*BANDS[k].w; }
  const cov = wall ? wsum/wall : 0; const q = wsum ? Math.round(acc/wsum*100) : null;
  const px = row.px, eps = val.eps, bps = val.bps;
  const per = px && eps && eps > 0 ? px/eps : null, pbr = px && bps && bps > 0 ? px/bps : null;
  const graham = eps && bps && eps > 0 && bps > 0 ? Math.sqrt(22.5*eps*bps) : null;
  /* 주식보상비용 차감: 스톡옵션·RSU는 현금이 나가지 않아도 주주 몫을 희석하는 실제 비용이다 */
  const oe = isNum(val.oeps) ? (isNum(val.sbcps) ? val.oeps - val.sbcps : val.oeps) : null;
  /* 성장 투자 보정: 설비투자가 순이익보다 크고(capex/NI>100%) ROIC가 15% 이상이면 FCF는 '유지 투자'가 아니라 '성장 투자'에 눌린 값이다.
     버핏의 오너이익은 유지 투자만 뺀다. 이런 회사는 그레이엄식 정상 이익(다년 평균 EPS, 최근 EPS보다 크지 않게)을 기준으로 삼는다 */
  const eAvg = val.epsAvg;
  const normEps = isNum(eAvg) && eAvg > 0 ? (isNum(eps) && eps > 0 ? Math.min(eAvg, eps) : eAvg) : null;
  const growthCapex = !row.fin_sector && isNum(oe) && normEps !== null && oe < normEps*0.6 && isNum(fin.capexNi) && fin.capexNi > 100 && isNum(fin.roic) && fin.roic >= 15;
  const ivBase = growthCapex ? normEps : oe;
  const dcf = row.fin_sector ? null : dcfValue(ivBase, val.growth, p.disc, p.tg);
  const iv = dcf ?? graham; const mos = iv && px ? (1 - px/iv)*100 : null;
  /* 가치 범위: 과거 평균 이익으로 돌아갈 때 ~ 최근 12개월 이익이 유지될 때 (같은 성장률·할인율) */
  const ivNorm = row.fin_sector ? null : dcfValue(normEps, val.growth, p.disc, p.tg);
  const ivNow = row.fin_sector ? null : dcfValue(isNum(eps) && eps > 0 ? eps : null, val.growth, p.disc, p.tg);
  /* 역DCF: 현재가가 가정한 성장률 vs 회사가 보여 준 성장률 */
  const histArr = [val.revCagr, fin.epsCagr].filter(isNum);
  const hist = histArr.length ? Math.min(Math.min(...histArr), 15) : null;
  const base = !row.fin_sector && isNum(ivBase) && ivBase > 0 ? ivBase : (isNum(eps) && eps > 0 ? eps : null);
  const igo = base ? impliedGrowth(px, base, p.disc, p.tg) : null;
  const ig = igo ? igo.g : null;
  const parts = [];
  if(mos !== null) parts.push([lin(mos,-50,reqMOS,60),2]);
  if(ig !== null && hist !== null) parts.push([lin(hist - ig, -10, 3, 10), 2]);
  if(per) parts.push([lin((100/per)/p.bond,0.5,2,3.5),1]);
  if(per && pbr) parts.push([lin(-(per*pbr),-60,-22.5,-10),1]);
  if(row.fin_sector && pbr && isNum(fin.roeAvg)) parts.push([lin((fin.roeAvg/p.disc)/pbr, 0.5, 1.2, 2), 2]);
  if(!per && px && isNum(val.sps) && val.sps > 0){ const fairPE = grpOf(row.m)==='US' ? 20 : 15; parts.push([lin(-(px/(fairPE*0.10)/val.sps),-20,-3,-1),1]); }
  const pp = parts.filter(x => x[0] !== null);
  const v = pp.length ? Math.round(pp.reduce((a,[s,w])=>a+s*w,0)/pp.reduce((a,[,w])=>a+w,0)*100) : null;
  const flags = [];
  if((fin.lossYears||0) >= 2) flags.push('잦은 적자');
  if((isNum(fin.ltdNi) && fin.ltdNi > 8) || (isNum(fin.icr) && fin.icr < 3 && (!isNum(fin.ltdNi) || fin.ltdNi > 0))) flags.push('차입 부담');
  if((fin.shareChg||0) > 10) flags.push('주식 희석');
  if(isNum(fin.fcfConv) && fin.fcfConv < 30) flags.push('현금 전환 약함');
  const sectorText = [row.s, row.ind, row.sector].filter(Boolean).join(' ');
  if(CYC_RE.test(sectorText) || (isNum(fin.roeMin) && isNum(fin.roeAvg) && fin.roeAvg > 0 && fin.roeMin < fin.roeAvg*0.4)) flags.push('경기순환·이익 변동');
  /* 이익 정점 경고(실러식): 최근 EPS가 가용 연수 평균의 1.5배 이상이면서 매출 성장 10% 이하 */
  const epsAvg = val.epsAvg;
  const yoy0 = val.revYoY || []; const lastYoY = yoy0.length ? yoy0[yoy0.length-1] : null;
  if(isNum(eps) && isNum(epsAvg) && epsAvg > 0 && eps > epsAvg*1.5 && (lastYoY === null || lastYoY <= 10)) flags.push('이익 정점 가능');
  /* 성장 감속: 매출 YoY 3년 연속 둔화 + 최근 0 이하 */
  const yoy = val.revYoY || [];
  if(yoy.length >= 3 && yoy[0] > yoy[1] && yoy[1] > yoy[2] && yoy[2] <= 0) flags.push('성장 감속');
  if(row.holdco) flags.push('지주회사');
  if(isNum(val.sbcps) && isNum(val.oeps) && val.oeps > 0 && val.sbcps > val.oeps*0.25) flags.push('주식보상 큼');
  if(row.revModel === '사이클형' && !flags.includes('경기순환·이익 변동')) flags.push('경기순환·이익 변동');
  if(row.revModel === '혁신 의존형') flags.push('혁신 의존');
  let b = null;
  /* 경기순환 표시는 경고만 한다. 버크셔 역검증에서 감점이 성공 사례(NUE, 일본 상사)를 깎고 실패를 거르지 못했다 */
  const penal = flags.filter(f => !WARN_FLAGS.has(f)).length;
  /* 가중치 0.4 품질 + 0.6 저평가: 버크셔 매수 62건 역검증에서 저평가 점수만 이후 수익률과 양(+)의 상관을 보였다 */
  if(q !== null && cov >= 0.5){ const base2 = 0.4*q + 0.6*(v ?? 40); b = Math.max(0, Math.min(100, Math.round(base2 - 8*Math.min(penal,3)))); }
  let mosLo = null, mosHi = null;
  if(dcf !== null && px){ const dHi = dcfValue(ivBase, val.growth, p.disc+1, p.tg), dLo = dcfValue(ivBase, val.growth, p.disc-1, p.tg); mosLo = dHi ? (1 - px/dHi)*100 : null; mosHi = dLo ? (1 - px/dLo)*100 : null; }
  const perAvg = px && isNum(epsAvg) && epsAvg > 0 ? px/epsAvg : null;
  return {q, v, b, cov:Math.round(cov*100)/100, per, pbr, graham, dcf, iv, mos, flags, ig, hist, mosLo, mosHi, perAvg, ivBasis: growthCapex ? 'norm' : 'oe', ivNorm, ivNow};
}
function dcfRaw(base, g, disc, tg){
  const r = disc/100, t = tg/100; let s = 0, e = base;
  for(let y=1;y<=10;y++){ e *= (1+g); s += e/Math.pow(1+r,y); }
  return s + (e*(1+t)/(r-t))/Math.pow(1+r,10);
}
/* 현재가를 정당화하려면 향후 10년간 필요한 연평균 성장률(%) */
function impliedGrowth(price, base, disc, tg){
  if(!isNum(price) || !isNum(base) || price <= 0 || base <= 0 || disc <= tg) return null;
  let lo = -0.3, hi = 0.8;
  if(dcfRaw(base, hi, disc, tg) < price) return {g: 80, over: true};
  if(dcfRaw(base, lo, disc, tg) > price) return {g: -30, under: true};
  for(let i=0;i<70;i++){ const mid = (lo+hi)/2; if(dcfRaw(base, mid, disc, tg) < price) lo = mid; else hi = mid; }
  return {g: (lo+hi)/2*100};
}
export { scoreRow, grpOf, WARN_FLAGS, isNum };
