// @ts-nocheck
// index.html(밸류노트 화면)의 점수 계산 코드를 그대로 옮겨 온 것. 화면과 같은 점수를 내야 하므로 손으로 고치지 말고 scripts/sync_scoring.py로 다시 생성한다.
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
const IV_CAP = { base: 25, lowQ: 15, cyc: 10, fin: 12 };
const HOLDCO_DISC = 0.30;
const WARN_FLAGS = new Set(['경기순환·이익 변동','지주회사','주식보상 큼','혁신 의존','중국 본토 규제']);
const CN_RISK = 6;
const FIN_SKIP = new Set(['gpm','fcfConv','capexNi','ltdNi','icr','currentRatio','roic','npm']);
const CYC_RE = /auto|steel|oil|gas|energy|airline|shipping|marine|homebuild|residential construction|chemical|mining|metal|commodit|capital markets|brokerage|자동차|철강|정유|석유|해운|항공|건설|화학|광업|조선|증권/i;
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
  const r = disc/100, t = tg/100, g0 = Math.max(Math.min(growth,20),-10)/100; let s = 0, e = oeps;
  for(let y=1;y<=10;y++){ const g = y <= 5 ? g0 : g0 + (t - g0)*(y - 5)/5; e *= (1+g); s += e/Math.pow(1+r,y); }
  return s + (e*(1+t)/(r-t))/Math.pow(1+r,10);
}
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
  /* ===== 적정 주가 (2026-10-19 개편: 정상 이익 기준으로 보수화) =====
     1) 데이터 이상(통화·단위가 섞인 종목)은 계산하지 않는다
     2) 경기순환·이익 정점 회사는 호황기 이익과 성장률을 10년 동안 이어 붙이지 않는다: 정상 이익, 성장률 = 영구 성장률, 10배 상한
     3) 금융사는 그레이엄 넘버 대신 자기자본 수익력(ROE)으로 본다
     4) 모든 회사에 정상 이익 대비 배수 상한을 두고, 지주회사는 30% 할인한다 */
  const sectorText = [row.s, row.ind, row.sector].filter(Boolean).join(' ');
  const yoy0 = val.revYoY || []; const lastYoY = yoy0.length ? yoy0[yoy0.length-1] : null;
  /* 경기순환 판정: 업종·사업 모델로만 한다. ROE가 들쭉날쭉한 것(보험사 평가손익, 낮은 기저에서 크는 성장주)은 경고만 하고 적정 주가는 건드리지 않는다 */
  const cycInd = CYC_RE.test(sectorText) || row.revModel === '사이클형';
  const roeSwing = isNum(fin.roeMin) && isNum(fin.roeAvg) && fin.roeAvg > 0 && fin.roeMin < fin.roeAvg*0.4;
  const peak = isNum(eps) && isNum(eAvg) && eAvg > 0 && eps > eAvg*1.5 && (lastYoY === null || lastYoY <= 10);
  /* 데이터 이상: PER 2.5 미만, 최근 이익이 평균의 20배 초과·5% 미만, ADR인데 PER 100 초과(ADR 1주 = 원주 여러 주 환산 누락) */
  const isAdr = /\bADR\b|DRC\b/.test(String(row.n || '') + ' ' + String(row.en || ''));
  const suspect = (per !== null && per < 2.5) || (isAdr && per !== null && per > 100) || (isNum(eps) && isNum(eAvg) && eps > 0 && eAvg > 0 && (eps/eAvg > 20 || eps/eAvg < 0.05));
  /* 꾸준한 우량주(경기순환 판정의 거울): 재무 점수 75+, 가장 나쁜 해 ROE 12%+(미국)·10%+(그 외), 적자 없음, 이익·매출 모두 성장,
     현금 전환 60%+, 경기순환 업종·ROE 급변 아님, 최근 성장이 꺾이지 않음. 증거가 있는 만큼 믿는다는 같은 원칙으로, 경기순환주의 성장·이익을 깎은 만큼
     이런 회사는 덜 깎는다: 성장률은 과거(이익·매출 중 낮은 값)의 75%, 최대 12% (일반 50%, 최대 8%), 기준 이익은 현금 이익과 최근 이익 중 큰 값 */
  const durable = !row.fin_sector && !cycInd && !roeSwing && q !== null && q >= 75 && (fin.lossYears||0) === 0
    && isNum(fin.roeMin) && fin.roeMin >= (ts === 'US' ? 12 : 10)
    && isNum(fin.epsCagr) && fin.epsCagr > 0 && isNum(val.revCagr) && val.revCagr > 0 && (!isNum(fin.fcfConv) || fin.fcfConv >= 60)
    /* 성장 꺾임 확인(이익 정점 확인의 거울): 최근 3년 매출이 한 해도 줄지 않았고, 고성장 회사(연 8%+)는 최근 1년 성장이 연평균의 절반 이상 */
    && yoy0.length > 0 && yoy0.every(x => !isNum(x) || x >= 0) && (val.revCagr < 8 || (isNum(lastYoY) && lastYoY >= val.revCagr*0.5));
  /* 이익 정점: 꾸준한 우량주는 평균에 일시적 감소 해가 섞여 최근 이익이 높아 보이는 경우라 경고만 하고 보정하지 않는다 */
  const cycAdj = cycInd || (peak && !durable);
  const gDur = durable ? Math.max(0, Math.min(Math.min(fin.epsCagr, val.revCagr)*0.75, 12)) : null;
  const gUse = cycAdj ? p.tg : durable ? Math.max(gDur, isNum(val.growth) ? val.growth : 0) : val.growth;
  const growthCapex = !row.fin_sector && isNum(oe) && normEps !== null && oe < normEps*0.6 && isNum(fin.capexNi) && fin.capexNi > 100 && isNum(fin.roic) && fin.roic >= 15;
  /* 오너이익(현금)이 최근 이익의 1.3배를 넘으면 일시적 현금 유입으로 보고 이익 쪽으로 낮춘다 */
  const earnTop = Math.max(isNum(eps) && eps > 0 ? eps : 0, isNum(eAvg) && eAvg > 0 ? eAvg : 0) || null;
  let ivBase = growthCapex ? normEps : oe;
  if(isNum(ivBase) && earnTop) ivBase = Math.min(ivBase, earnTop*1.3);
  if(cycAdj && normEps !== null) ivBase = isNum(ivBase) && ivBase > 0 ? Math.min(ivBase, normEps) : normEps;
  /* 꾸준한 우량주는 현금 이익과 최근 이익 중 큰 값 (일시적 세금·인수 대금·성장 투자로 현금이 이익보다 늦을 때). 경기순환주의 '작은 값'과 대칭 */
  if(durable && isNum(eps) && eps > 0) ivBase = Math.max(isNum(ivBase) && ivBase > 0 ? ivBase : 0, eps);
  /* 배수 상한의 기준 이익: 경기순환은 정상 이익(평균과 최근 중 작은 값), 나머지는 최근 이익 (고성장 회사가 과거 낮은 이익에 묶이지 않게) */
  const E = cycAdj ? (normEps ?? (isNum(eps) && eps > 0 ? eps : null)) : (isNum(eps) && eps > 0 ? eps : normEps);
  const capX = row.fin_sector ? IV_CAP.fin : cycAdj ? IV_CAP.cyc : (q !== null && q < 60 ? IV_CAP.lowQ : IV_CAP.base);
  const finish = raw => { if(!isNum(raw) || raw <= 0 || suspect) return null; let v = E ? Math.min(raw, capX*E) : raw; if(row.holdco) v *= 1 - HOLDCO_DISC; return v; };
  /* 금융사: 정당 PBR = (ROE − g) ÷ (할인율 − g). ROE는 최근 여러 해 평균 */
  const roeFin = isNum(fin.roeAvg) ? fin.roeAvg : null;
  const finIv = row.fin_sector && isNum(bps) && bps > 0 && isNum(roeFin) && p.disc > p.tg ? bps * Math.max(0.3, Math.min(2.0, (roeFin - p.tg)/(p.disc - p.tg))) : null;
  const dcf = row.fin_sector ? null : finish(dcfValue(ivBase, gUse, p.disc, p.tg));
  const iv = row.fin_sector ? (finish(finIv) ?? finish(graham)) : (dcf ?? finish(graham));
  const mos = iv && px ? (1 - px/iv)*100 : null;
  const ivSrc = suspect ? null : row.fin_sector ? (finIv ? '자기자본 수익력 (ROE 기준 적정 PBR)' : '그레이엄 넘버')
    : dcf ? (cycAdj ? '경기순환 보정 (정상 이익 × 최대 10배)' : durable ? '꾸준한 우량주 DCF (최근 이익, 과거 성장의 75%)' : growthCapex ? '정상 이익 DCF (다년 평균 EPS, 성장 투자 보정)' : '오너이익 DCF') : (iv ? '그레이엄 넘버' : null);
  /* 가치 범위: 과거 평균 이익으로 돌아갈 때 ~ 최근 12개월 이익이 유지될 때 (같은 성장률·할인율·상한) */
  const ivNorm = row.fin_sector ? null : finish(dcfValue(normEps, gUse, p.disc, p.tg));
  const ivNow = row.fin_sector || cycAdj ? null : finish(dcfValue(isNum(eps) && eps > 0 ? eps : null, gUse, p.disc, p.tg));
  /* 역DCF: 현재가가 가정한 성장률 vs 회사가 보여 준 성장률. 경기순환 회사의 과거 성장은 호황기 성장이라 영구 성장률+1%p까지만 인정 */
  const histArr = [val.revCagr, fin.epsCagr].filter(isNum);
  const hist = histArr.length ? Math.min(Math.min(...histArr), cycAdj ? p.tg + 1 : 15) : null;
  const base = !row.fin_sector && isNum(ivBase) && ivBase > 0 ? ivBase : (isNum(eps) && eps > 0 ? eps : null);
  const igo = base && !suspect ? impliedGrowth(px, base, p.disc, p.tg) : null;
  const ig = igo ? igo.g : null;
  /* 이익수익률·PER×PBR은 경기순환 회사면 정상 이익 기준 PER로 본다 */
  const perV = cycAdj && normEps && px ? px/normEps : per;
  const parts = [];
  if(mos !== null) parts.push([lin(mos,-50,reqMOS,60),2]);
  if(ig !== null && hist !== null) parts.push([lin(hist - ig, -10, 3, 10), 2]);
  if(perV && !suspect) parts.push([lin((100/perV)/p.bond,0.5,2,3.5),1]);
  if(perV && pbr && !suspect) parts.push([lin(-(perV*pbr),-60,-22.5,-10),1]);
  if(row.fin_sector && pbr && isNum(fin.roeAvg)) parts.push([lin((fin.roeAvg/p.disc)/pbr, 0.5, 1.2, 2), 2]);
  if(!per && px && isNum(val.sps) && val.sps > 0){ const fairPE = grpOf(row.m)==='US' ? 20 : 15; parts.push([lin(-(px/(fairPE*0.10)/val.sps),-20,-3,-1),1]); }
  const pp = parts.filter(x => x[0] !== null);
  const v = pp.length ? Math.round(pp.reduce((a,[s,w])=>a+s*w,0)/pp.reduce((a,[,w])=>a+w,0)*100) : null;
  const flags = [];
  if((fin.lossYears||0) >= 2) flags.push('잦은 적자');
  if((isNum(fin.ltdNi) && fin.ltdNi > 8) || (isNum(fin.icr) && fin.icr < 3 && (!isNum(fin.ltdNi) || fin.ltdNi > 0))) flags.push('차입 부담');
  if((fin.shareChg||0) > 10) flags.push('주식 희석');
  if(isNum(fin.fcfConv) && fin.fcfConv < 30) flags.push('현금 전환 약함');
  if(cycInd || roeSwing) flags.push('경기순환·이익 변동');
  /* 이익 정점 경고(실러식): 최근 EPS가 가용 연수 평균의 1.5배 이상이면서 매출 성장 10% 이하 */
  const epsAvg = val.epsAvg;
  if(peak) flags.push('이익 정점 가능');
  if(suspect) flags.push('데이터 확인 필요');
  /* 성장 감속: 매출 YoY 3년 연속 둔화 + 최근 0 이하 */
  const yoy = val.revYoY || [];
  if(yoy.length >= 3 && yoy[0] > yoy[1] && yoy[1] > yoy[2] && yoy[2] <= 0) flags.push('성장 감속');
  if(row.holdco) flags.push('지주회사');
  if((row.tags||[]).includes('국유기업')) flags.push('국유기업·정책 위험');
  if(row.m === 'CN') flags.push('중국 본토 규제');
  if(isNum(val.sbcps) && isNum(val.oeps) && val.oeps > 0 && val.sbcps > val.oeps*0.25) flags.push('주식보상 큼');
  if(row.revModel === '혁신 의존형') flags.push('혁신 의존');
  let b = null;
  /* 경기순환 표시는 경고만 한다. 버크셔 역검증에서 감점이 성공 사례(NUE, 일본 상사)를 깎고 실패를 거르지 못했다 */
  const penal = flags.filter(f => !WARN_FLAGS.has(f)).length;
  /* 가중치 0.4 품질 + 0.6 저평가: 버크셔 매수 62건 역검증에서 가격 점수만 이후 수익률과 양(+)의 상관을 보였다 */
  /* 데이터 이상 종목은 점수를 매기지 않는다 (통화·단위가 섞여 저평가로 잘못 보이던 문제) */
  if(q !== null && cov >= 0.5 && !suspect){ const base2 = 0.4*q + 0.6*(v ?? 40); b = Math.max(0, Math.min(100, Math.round(base2 - 8*Math.min(penal,3) - (row.m === 'CN' ? CN_RISK : 0)))); }
  let mosLo = null, mosHi = null;
  if(dcf !== null && px){ const dHi = finish(dcfValue(ivBase, gUse, p.disc+1, p.tg)), dLo = finish(dcfValue(ivBase, gUse, p.disc-1, p.tg)); mosLo = dHi ? (1 - px/dHi)*100 : null; mosHi = dLo ? (1 - px/dLo)*100 : null; }
  const perAvg = px && isNum(epsAvg) && epsAvg > 0 ? px/epsAvg : null;
  return {q, v, b, cov:Math.round(cov*100)/100, per, pbr, graham, dcf, iv, mos, flags, ig, hist, mosLo, mosHi, perAvg, ivBasis: cycAdj ? 'cyc' : durable ? 'dur' : growthCapex ? 'norm' : 'oe', ivSrc, ivNorm, ivNow, cyc: cycAdj, suspect, ivBase, gUse, capX, E, finIv: row.fin_sector ? finIv : null, roeFin: row.fin_sector ? roeFin : null};
}
function dcfRaw(base, g, disc, tg){
  const r = disc/100, t = tg/100; let s = 0, e = base;
  for(let y=1;y<=10;y++){ e *= (1+g); s += e/Math.pow(1+r,y); }
  return s + (e*(1+t)/(r-t))/Math.pow(1+r,10);
}
function impliedGrowth(price, base, disc, tg){
  if(!isNum(price) || !isNum(base) || price <= 0 || base <= 0 || disc <= tg) return null;
  let lo = -0.3, hi = 0.8;
  if(dcfRaw(base, hi, disc, tg) < price) return {g: 80, over: true};
  if(dcfRaw(base, lo, disc, tg) > price) return {g: -30, under: true};
  for(let i=0;i<70;i++){ const mid = (lo+hi)/2; if(dcfRaw(base, mid, disc, tg) < price) lo = mid; else hi = mid; }
  return {g: (lo+hi)/2*100};
}
export { scoreRow, grpOf, WARN_FLAGS, isNum, IV_CAP, HOLDCO_DISC };
