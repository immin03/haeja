# 원화 기준 배당 포함 수익률: 그날 환율로 사서, 배당은 현지 통화로 모았다가 기준일 환율로 환산
# 사용: python3 scripts/research/returns.py <then.json> <자료 폴더> <buyDate> <market.json>
import json, sys, glob, os
then = json.load(open(sys.argv[1])); D = sys.argv[2]; buy = sys.argv[3]; M = json.load(open(sys.argv[4]))
fx0, fx1 = M['fx'][buy], M['fx']['2026-10-20']
rate = {'KRW': (1, 1), 'USD': (fx0['USDKRW'], fx1['USDKRW']), 'JPY': (fx0['JPYKRW100'] / 100, fx1['JPYKRW100'] / 100)}
k0, k1 = M['kospi'][buy], M['kospi']['2026-10-20']
out = []
for f in sorted(glob.glob(os.path.join(D, '*.json'))):
    d = json.load(open(f))
    if 'ticker' not in d or d['ticker'] not in then: continue
    t = d['ticker']; p0 = d['prices'][buy]['close']; p1 = d['prices']['latest']['close'] * d.get('split', 1)
    div = sum(d['divs']) + d.get('extra', 0)
    r0, r1 = rate[d['cur']]
    local = (p1 + div) / p0; won = local * r1 / r0
    a = then[t][buy]
    out.append(dict(t=t, n=then[t]['n'], score=a['b'], q=a['q'], v=a['v'], per=a['per'], now=then[t]['now']['b'], local=round(local, 3), won=round(won, 3), man=round(won * 10000)))
out.sort(key=lambda x: -x['score'])
for o in out: print(f"{o['score']:>3}점  {o['n']:14} 1억→{o['won']:.2f}억  (현지 {o['local']:.2f}배)  지금 {o['now']}점")
print('코스피 1억→', round(k1 / k0, 2), '억')
for th in (70, 60):
    g = [o['won'] for o in out if o['score'] >= th]; r = [o['won'] for o in out if o['score'] < th]
    if g: print(f'{th}점 이상 {len(g)}곳 평균 {sum(g)/len(g):.2f}억 · 미만 {len(r)}곳 평균 {sum(r)/len(r):.2f}억')
json.dump(dict(rows=out, kospi=round(k1 / k0, 3)), open(os.path.join(D, 'results.json'), 'w'), ensure_ascii=False, indent=1)
