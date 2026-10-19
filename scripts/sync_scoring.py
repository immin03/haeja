#!/usr/bin/env python3
"""index.html(밸류노트 화면)의 점수 계산 코드를 supabase/functions/watch-select/scoring.js로 옮긴다.

공개 기업 페이지(/c/), 관심 후보 자동 선정, 릴스·블로그·기업 카드가 모두 scoring.js를 쓰므로
index.html의 점수·적정 주가 공식을 바꾸면 반드시 이 스크립트를 다시 돌린다.

    python3 scripts/sync_scoring.py          # scoring.js 다시 생성
    python3 scripts/sync_scoring.py --check  # 어긋났으면 종료 코드 1
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'index.html'
DST = ROOT / 'supabase/functions/watch-select/scoring.js'

# index.html에서 그대로 가져올 최상위 선언 (순서대로)
CONSTS = ['BANDS', 'MKT', 'grpOf', 'thSet', 'IV_CAP', 'HOLDCO_DISC', 'WARN_FLAGS', 'CN_RISK', 'FIN_SKIP', 'CYC_RE']
FUNCS = ['paramsFor', 'metricScore', 'lin', 'dcfValue', 'scoreRow', 'dcfRaw', 'impliedGrowth']

HEAD = """// @ts-nocheck
// index.html(밸류노트 화면)의 점수 계산 코드를 그대로 옮겨 온 것. 화면과 같은 점수를 내야 하므로 손으로 고치지 말고 scripts/sync_scoring.py로 다시 생성한다.
const isNum = v => typeof v === 'number' && isFinite(v);
{DEF}
let __st = {{...DEF_SETTINGS}};
export function setSettings(s){{ __st = {{...DEF_SETTINGS, ...(s||{{}})}}; }}
const cfg = () => __st;
"""


def grab_const(src, name):
    # 한 줄 선언 또는 { 로 시작해 여러 줄에 걸친 선언(BANDS)
    m = re.search(r'^const ' + re.escape(name) + r' = .*$', src, re.M)
    if not m:
        raise SystemExit(f'index.html에서 const {name}를 찾지 못했습니다')
    line = m.group(0)
    if line.rstrip().endswith('{'):
        end = src.index('\n};', m.end())
        return src[m.start():end + 3]
    return line


def grab_func(src, name):
    # 한 줄짜리 함수(lin 등)
    one = re.search(r'^function ' + re.escape(name) + r'\(.*}\s*$', src, re.M)
    if one and one.group(0).count('{') == one.group(0).count('}'):
        return one.group(0).rstrip()
    m = re.search(r'^function ' + re.escape(name) + r'\(.*?^}\n', src, re.M | re.S)
    if not m:
        raise SystemExit(f'index.html에서 function {name}를 찾지 못했습니다')
    return m.group(0).rstrip('\n')


def build():
    src = SRC.read_text(encoding='utf-8')
    parts = [HEAD.format(DEF=grab_const(src, 'DEF_SETTINGS'))]
    for c in CONSTS:
        parts.append(grab_const(src, c))
    for f in FUNCS:
        parts.append(grab_func(src, f))
    parts.append('export { scoreRow, grpOf, WARN_FLAGS, isNum, IV_CAP, HOLDCO_DISC };\n')
    return '\n'.join(parts)


if __name__ == '__main__':
    out = build()
    if '--check' in sys.argv:
        same = DST.exists() and DST.read_text(encoding='utf-8') == out
        print('scoring.js 일치' if same else 'scoring.js가 index.html과 다릅니다. python3 scripts/sync_scoring.py 를 실행하세요')
        sys.exit(0 if same else 1)
    DST.write_text(out, encoding='utf-8')
    print(f'{DST.relative_to(ROOT)} 생성 ({len(out):,}자)')
