"""이슈 감지 → 릴스 대본 자동 생성 (사람·AI 없이 규칙으로 작성, 토큰 0)
GitHub Actions에서 3시간마다 실행. 조건에 걸리면 events/E*.json 을 쓰고 build.py가 영상으로 만든다.
고정 편성 사이에 '유기적으로' 끼워 넣는다: 감지 1시간 뒤 게시(인스타 90분 간격 규칙 때문에 더 밀릴 수 있음).
게시 대기열에 들어가면 관리자 알림이 가고, 관리자 → SNS 게시에서 멈출 수 있다.

감지 기준
  미국 기준금리 결정(연준 목표 상단이 바뀐 날), 미국 소비자물가(CPI) 새 발표
  코스피 ±3%, 코스닥 ±4%, S&P 500 ±2%, 나스닥 ±2.5%, 원·달러 환율 ±1.2% (전일 대비)
  미국 10년 국채 금리 ±0.15%p
제한: 하루(한국 시간) 1편, 우선순위는 위 순서. 새벽(01~07시)에는 07:30으로 미뤄 게시.
대본 원칙(README 규칙 13): 판정·예측·과거 평균 수익률 없이, 사실 + 쉬운 의미 + 밸류노트에서 확인.

테스트: python3 events.py --fake KS11 -4.2   (가짜 변동으로 대본만 만들어 본다)
"""
import os, sys, json, math, time, datetime as dt, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EVDIR = os.path.join(HERE, "events")
STATE = os.path.join(ROOT, "social", "reels", "events_state.json")
KST = dt.timezone(dt.timedelta(hours=9))
MAX_PER_DAY = 1

SYMS = {  # 키: (야후 심볼, 이름, 기준, 종류)
    "KS11": ("^KS11", "코스피", 3.0, "idx"),
    "KQ11": ("^KQ11", "코스닥", 4.0, "idx"),
    "GSPC": ("^GSPC", "S&P 500", 2.0, "idx"),
    "IXIC": ("^IXIC", "나스닥", 2.5, "idx"),
    "KRW": ("KRW=X", "원·달러 환율", 1.2, "fx"),
    "TNX": ("^TNX", "미국 10년물 금리", 0.15, "rate"),
}


def josa(word, a, b):  # 받침 있으면 a, 없으면 b
    ch = word.strip()[-1]
    if "가" <= ch <= "힣": return a if (ord(ch) - 0xAC00) % 28 else b
    return a if ch in "0136780LMN" else b  # 숫자·영문 끝 (영·일·삼·육·칠·팔·공…)


def history(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(sym)}?range=10y&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (valuenote)"})
    j = json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
    closes = [c for c in j["indicators"]["quote"][0]["close"] if c is not None]
    m = j["meta"]; live = m.get("regularMarketPrice")
    if live and abs(live - closes[-1]) / closes[-1] > 1e-6: closes.append(live)
    t = m.get("regularMarketTime") or j["timestamp"][-1]
    off = dt.timedelta(seconds=m.get("gmtoffset", 0))
    day = (dt.datetime.fromtimestamp(t, dt.timezone.utc) + off).date()          # 거래소 기준 날짜
    end = (m.get("currentTradingPeriod") or {}).get("regular", {}).get("end", 0)
    live_now = time.time() < end                                                # 장중이면 True
    return closes, {"day": day, "age_h": (time.time() - t) / 3600, "live": live_now}


def stats(closes, kind, chg):
    """최근 10년 동안 이만큼 움직인 날 수 + 그 1년(252거래일) 뒤 평균 수익률"""
    days, fwd = 0, []
    for i in range(1, len(closes) - 1):
        c = closes[i] - closes[i - 1] if kind == "rate" else (closes[i] / closes[i - 1] - 1) * 100
        if (chg < 0 and c <= chg) or (chg > 0 and c >= chg):
            days += 1
            if kind == "idx" and i + 252 < len(closes): fwd.append((closes[i + 252] / closes[i] - 1) * 100)
    return days, (sum(fwd) / len(fwd) if len(fwd) >= 3 else None), len(fwd)



_RATES = None
def rates_doc():
    """금리·물가 자료: Supabase rates 함수가 매일 FRED에서 받아 둔 fx/rates 문서 (GitHub 서버에서는 FRED가 응답하지 않는다)"""
    global _RATES
    if _RATES is None:
        import re
        cfg = open(os.path.join(ROOT, "config.js"), encoding="utf-8").read()
        url = re.search(r"SUPABASE_URL:\s*'([^']+)'", cfg).group(1); key = re.search(r"SUPABASE_ANON_KEY:\s*'([^']+)'", cfg).group(1)
        req = urllib.request.Request(f"{url}/rest/v1/docs?collection=eq.fx&id=eq.rates&select=data", headers={"apikey": key, "Authorization": "Bearer " + key})
        _RATES = json.load(urllib.request.urlopen(req, timeout=30))[0]["data"]
    return _RATES


def fred(series):
    d = rates_doc()
    if series == "DFEDTARU": return [tuple(x) for x in d["series"]["USPOL"]["daily"]]
    if series == "CPIAUCSL": return [tuple(x) for x in (d.get("cpi") or {}).get("monthly", [])]
    raise KeyError(series)


def nsay(v, dec):  # 5.09 → "오 점 영 구" 대신 숫자 그대로 두면 korean.py가 읽는다. 소수 둘째 자리 0은 지운다
    s_ = f"{abs(v):.{dec}f}"
    return s_.rstrip("0").rstrip(".") if "." in s_ else s_


NOT_ADVICE = ""  # 고지문은 게시할 때 * 한 줄로 자동으로 붙는다
RATE_UP = ("금리가 오르면", "같은 회사도 적정 주가가 낮아집니다", "국채 이자가 높아지면 주식에 바라는 수익도 높아집니다")
RATE_DN = ("금리가 내리면", "먼 미래 이익의 가치가 커집니다", "이익이 먼 미래에 몰린 성장주일수록 영향이 큽니다")
RATE_WHY = "금리가 주가에 중요한 이유는 간단합니다. 위험이 거의 없는 국채가 높은 이자를 주면, 투자자는 주식에도 그보다 높은 수익을 바랍니다. 그래서 회사가 앞으로 벌 돈의 지금 가치가 줄어들고, 같은 회사라도 적정 주가가 낮아집니다. 금리가 내리면 반대입니다."
CTA_RADAR = {"type": "cta", "l1": "금리·환율 흐름은", "l2": "경제 레이더에서", "say": "금리와 환율 흐름은, 밸류노트 경제 레이더에서 확인하세요."}


def when_from(now):
    w = now + dt.timedelta(minutes=60)
    if 1 <= w.hour < 7: w = w.replace(hour=7, minute=30)
    return w


def wrap(id_, title, scenes, caption, tags, now, mood="tense"):
    return {"id": id_, "title": title, "scheduled_at": when_from(now).isoformat(timespec="minutes"), "mood": mood, "event": id_,
            "caption": caption, "hashtags": tags + ["주식공부", "밸류노트"], "threads_tag": "주식뉴스", "scenes": scenes}


def make_spec(key, chg, closes, now, info=None):
    """지수·환율·국채 금리 급변"""
    sym, name, th, kind = SYMS[key]
    up = chg > 0
    day = (info or {}).get("day") or now.date()
    md = f"{day.month}월 {day.day}일" + (" 장중" if (info or {}).get("live") else "")
    cur = closes[-1]
    days, _, _ = stats(closes[:-1], kind, chg)
    scenes = []
    if kind == "rate":
        word = "올랐습니다" if up else "내렸습니다"
        scenes.append({"type": "hook", "top": "미국 10년 국채 금리", "num": {"to": round(cur, 2), "fmt": "pct", "dec": 2, "plus": False},
                       "tone": "loss" if up else "gold", "label": f"{md} · 하루 {chg:+.2f}%p",
                       "lines": [{"cap": ["미국 국채 금리가", f"하루에 {abs(chg):.2f}%p {word}"], "say": f"미국 국채 금리가, 하루에 {nsay(chg, 2)} 퍼센트포인트 {word}."},
                                 {"cap": ["지금 미국 10년 국채 금리는", f"{cur:.2f}%입니다"], "say": f"지금 미국 십 년 국채 금리는, {nsay(cur, 2)} 퍼센트입니다."}]})
        m = RATE_UP if up else RATE_DN
        scenes.append({"type": "statement", "l1": m[0], "l2": m[1], "tone": "gold", "note": m[2], "say": f"{m[0]}, {m[1]}."})
        scenes.append(CTA_RADAR)
        cap = f"{md} 미국 10년 국채 금리가 하루에 {abs(chg):.2f}%p {word}. 지금 {cur:.2f}%입니다." + (f" 최근 10년 동안 하루에 이만큼 움직인 날은 {days}번이었습니다." if days >= 2 else "") + "\n\n" + RATE_WHY
        return wrap(f"E{day:%y%m%d}{key}", f"{md} 미국 10년 국채 금리 {chg:+.2f}%p", scenes, cap, ["금리", "미국국채"], now)
    if kind == "fx":
        word = "올랐습니다" if up else "내렸습니다"
        scenes.append({"type": "hook", "top": "원·달러 환율 하루", "num": {"to": round(chg, 1), "fmt": "pct", "dec": 1}, "tone": "gold", "label": f"{md} · {cur:,.1f}원",
                       "lines": [{"cap": ["원·달러 환율이 하루에", f"{abs(chg):.1f}% {word}"]}, {"cap": ["지금 1달러는", f"{cur:,.0f}원입니다"]}]})
        m = ("환율이 오르면", "달러 자산은 원화로 늘어납니다", "수출 기업에는 도움, 수입 원가가 큰 기업에는 부담") if up else ("환율이 내리면", "달러 자산은 원화로 줄어듭니다", "수입 원가가 큰 기업에는 도움, 수출 기업에는 부담")
        scenes.append({"type": "statement", "l1": m[0], "l2": m[1], "tone": "gold", "note": m[2], "say": f"{m[0]}, {m[1]}."})
        scenes.append({"type": "cta", "l1": "내 계좌의 환율 영향은", "l2": "밸류노트에서", "say": "내 계좌가 환율에 얼마나 영향을 받는지, 밸류노트에서 확인하세요."})
        cap = (f"{md} 원·달러 환율이 하루에 {abs(chg):.1f}% {word}. 지금 1달러는 {cur:,.1f}원입니다." + (f" 최근 10년 동안 하루에 이만큼 움직인 날은 {days}번이었습니다." if days >= 2 else "")
               + f"\n\n{m[0]} 미국 주식이나 달러 자산은 원화로 {'늘어납니다' if up else '줄어듭니다'}. {'수출 기업에는 도움이 되고, 수입 원가가 큰 기업에는 부담이 됩니다' if up else '수입 원가가 큰 기업에는 도움이 되고, 수출 기업에는 부담이 됩니다'}. 밸류노트 환율 화면에서는 내 포트폴리오의 달러 비중과 환율 10원당 평가액 변화를 볼 수 있습니다.")
        return wrap(f"E{day:%y%m%d}{key}", f"{md} 원·달러 환율 {chg:+.1f}%", scenes, cap, ["환율", "원달러환율"], now)
    # 지수
    word = "올랐습니다" if up else "빠졌습니다"
    scenes.append({"type": "hook", "top": f"{name} 하루", "num": {"to": round(chg, 1), "fmt": "pct", "dec": 1}, "tone": "gold" if up else "loss", "label": md,
                   "lines": [{"cap": [f"{name}{josa(name, '이', '가')} 하루에", f"{abs(chg):.1f}% {word}"]}, {"cap": ["이럴 때", "무엇을 봐야 할까요?"]}]})
    if days >= 2:
        scenes.append({"type": "statement", "l1": "최근 10년 동안", "l2": f"이런 날은 {days}번이었습니다", "tone": "ivory", "say": f"최근 10년 동안, 이런 날은 {days}번이었습니다."})
    m = ("급등장에서 먼저 볼 것은", "지금 가격입니다") if up else ("급락장에서 먼저 볼 것은", "내가 정한 기준입니다")
    scenes.append({"type": "statement", "l1": m[0], "l2": m[1], "tone": "gold", "say": f"{m[0]}, {m[1]}."})
    scenes.append({"type": "cta", "l1": "적정 매수가에 오면", "l2": "밸류노트가 알려 드립니다", "say": "관심 종목이 적정 매수가에 오면, 밸류노트가 알려 드립니다."} if not up else CTA_RADAR)
    cap = (f"{md} {name}{josa(name, '이', '가')} 하루에 {abs(chg):.1f}% {word}." + (f" 최근 10년 동안 이만큼 움직인 날은 {days}번이었습니다." if days >= 2 else "")
           + "\n\n" + ("크게 오른 날일수록 사고 싶은 마음이 커집니다. 그럴 때 먼저 볼 것은 기대가 아니라 지금 가격이 적정 주가와 비교해 어디쯤인지입니다." if up
                       else "크게 빠진 날일수록 판단이 흔들립니다. 그럴 때 먼저 볼 것은 뉴스가 아니라 내가 미리 정한 매수·매도 기준입니다. 밸류노트는 관심 종목이 적정 매수가에 오면 알림을 보냅니다."))
    return wrap(f"E{day:%y%m%d}{key}", f"{md} {name} {chg:+.1f}%", scenes, cap, [name.replace(" ", "").replace("&", ""), "오늘의시장"], now)


def check_fomc(now, seen):
    """연준 목표금리 상단(DFEDTARU)이 바뀐 날 → 결정 릴스. 3일 지난 결정은 다루지 않는다"""
    pts = fred("DFEDTARU")
    for i in range(len(pts) - 1, 0, -1):
        if pts[i][1] != pts[i - 1][1]:
            d_, new = pts[i]; old = pts[i - 1][1]; break
    else:
        return None
    tag = f"FOMC@{d_}"
    day = dt.date.fromisoformat(d_)
    if tag in seen or (now.date() - day).days > 3: return None
    chg = new - old; up = chg > 0; word = "올렸습니다" if up else "내렸습니다"
    md = f"{day.month}월 {day.day}일"
    m = RATE_UP if up else RATE_DN
    scenes = [{"type": "hook", "top": "미국 기준금리", "num": {"to": new, "fmt": "pct", "dec": 2, "plus": False}, "tone": "loss" if up else "gold", "label": f"{md} 결정 · {chg:+.2f}%p",
               "lines": [{"cap": ["미국이 기준금리를", f"{abs(chg):.2f}%p {word}"], "say": f"미국이 기준금리를, {nsay(chg, 2)} 퍼센트포인트 {word}."},
                         {"cap": ["기준금리 상단은", f"{new:.2f}%가 됐습니다"], "say": f"기준금리 상단은, {nsay(new, 2)} 퍼센트가 됐습니다."}]},
              {"type": "statement", "l1": m[0], "l2": m[1], "tone": "gold", "note": m[2], "say": f"{m[0]}, {m[1]}."}, CTA_RADAR]
    cap = f"미국 연방준비제도가 {md} 기준금리를 {abs(chg):.2f}%p {word}. 목표 범위 상단은 {old:.2f}%에서 {new:.2f}%가 됐습니다.\n\n" + RATE_WHY
    return tag, wrap(f"E{day:%y%m%d}FOMC", f"{md} 미국 기준금리 {chg:+.2f}%p", scenes, cap, ["미국금리", "기준금리", "금리"], now)


def radar_doc():
    import re
    cfg = open(os.path.join(ROOT, "config.js"), encoding="utf-8").read()
    url = re.search(r"SUPABASE_URL:\s*'([^']+)'", cfg).group(1); key = re.search(r"SUPABASE_ANON_KEY:\s*'([^']+)'", cfg).group(1)
    req = urllib.request.Request(f"{url}/rest/v1/docs?collection=eq.fx&id=eq.radar&select=data", headers={"apikey": key, "Authorization": "Bearer " + key})
    return json.load(urllib.request.urlopen(req, timeout=30))[0]["data"]


RNAME = {"hy": "회사채 금리차", "stress": "금융 스트레스", "vix": "공포지수", "curve": "장단기 금리차", "rate": "미국 10년 금리", "sahm": "실업률 신호", "dollar": "달러 흐름", "kospi": "코스피", "spx": "S&P 500", "euro": "프랑스 국채 금리차"}
OVN = ["안정", "대체로 안정", "주의", "경계", "위험"]


def check_radar(now, seen):
    """경제 레이더 종합 단계(0~4)가 바뀐 날 → 신호등 릴스. 이틀 이상 지난 변화는 다루지 않는다"""
    d = radar_doc(); h = [x for x in d.get("hist", []) if isinstance(x.get("o"), int)]
    if len(h) < 2 or h[-1]["o"] == h[-2]["o"]: return None
    day = h[-1]["d"]; tag = f"RADAR@{day}"
    if tag in seen or (now.date() - dt.date.fromisoformat(day)).days > 2: return None
    new, old = h[-1]["o"], h[-2]["o"]; up = new > old
    on = sorted([(k, v) for k, v in d.get("ind", {}).items() if k in RNAME and (v.get("lv") or 0) >= 3], key=lambda x: -x[1]["lv"])
    scenes = [{"type": "statement", "l1": "경제 레이더 신호등이", "l2": f"'{OVN[old]}'에서 '{OVN[new]}'로", "tone": "loss" if up else "gold", "note": "위기 신호 10개를 모아 매일 계산합니다",
               "say": f"경제 레이더 신호등이, {OVN[old]}에서 {OVN[new]}{'으' if OVN[new][-1] in '험의' else ''}로 바뀌었습니다."}]
    if on: scenes.append({"type": "list", "title": "경고가 켜진 신호", "items": [f"{RNAME[k]} · {'위험' if v['lv'] >= 4 else '주의'}" for k, v in on[:5]], "say": ", ".join(RNAME[k] for k, _ in on[:5]) + "에 경고가 켜져 있습니다."})
    scenes.append({"type": "statement", "l1": "신호는 예측이 아니라", "l2": "미리 살피라는 경고입니다", "tone": "ivory", "say": "신호는 예측이 아니라, 미리 살피라는 경고입니다."})
    scenes.append(CTA_RADAR)
    cap = (f"밸류노트 경제 레이더의 종합 단계가 '{OVN[old]}'에서 '{OVN[new]}'(으)로 {'올라갔습니다' if up else '내려왔습니다'}.\n\n"
           + ("\n".join(f"· {RNAME[k]}: {v.get('why', '')}" for k, v in on) + "\n\n" if on else "")
           + "경제 레이더는 회사채 금리차, 금융 스트레스, 공포지수, 장단기 금리차, 미국 10년 금리, 실업률 신호, 달러 흐름, 주가 하락 폭 등을 과거 위기 때 수치와 비교해 신호등으로 보여 줍니다. 신호는 시장을 예측하지 않으며, 위험을 미리 살피기 위한 도구입니다.")
    return tag, wrap(f"E{now:%y%m%d}RADAR", f"경제 레이더 {OVN[old]} → {OVN[new]}", scenes, cap, ["경제레이더", "경제위기", "금리"], now)


def check_cpi(now, seen):
    """미국 소비자물가(CPIAUCSL) 새 달 자료가 올라오면 → 물가 릴스 (1년 전 대비 상승률)"""
    pts = fred("CPIAUCSL")
    if len(pts) < 14: return None
    d_, v = pts[-1]
    tag = f"CPI@{d_[:7]}"
    if tag in seen: return None
    obs = dt.date.fromisoformat(d_)
    if (now.date() - obs).days > 50: return None   # 발표는 보통 다음 달 중순. 너무 오래된 자료는 건너뜀
    yoy = (v / pts[-13][1] - 1) * 100; prev = (pts[-2][1] / pts[-14][1] - 1) * 100
    yoy, prev = round(yoy, 1), round(prev, 1)
    hot = yoy > prev
    m = ("물가가 오르면", "금리를 내리기 어려워집니다") if yoy >= prev else ("물가가 내려오면", "금리를 내릴 여유가 생깁니다")
    scenes = [{"type": "hook", "top": "미국 소비자물가", "num": {"to": yoy, "fmt": "pct", "dec": 1, "plus": False}, "tone": "loss" if hot else "gold", "label": f"{obs.month}월 · 1년 전 대비",
               "lines": [{"cap": [f"미국 {obs.month}월 물가가", f"1년 전보다 {yoy}% 올랐습니다"]}, {"cap": ["바로 전 달에는", f"{prev}%였습니다"]}]},
              {"type": "statement", "l1": m[0], "l2": m[1], "tone": "gold", "note": "미국의 물가 목표는 2%입니다", "say": f"{m[0]}, {m[1]}."},
              {"type": "statement", "l1": "금리가 높으면", "l2": "같은 회사도 적정 주가가 낮아집니다", "tone": "ivory", "say": "금리가 높으면, 같은 회사라도 적정 주가가 낮아집니다."},
              CTA_RADAR]
    cap = (f"미국 {obs.month}월 소비자물가(CPI)가 1년 전보다 {yoy}% 올랐습니다. 바로 전 달에는 {prev}%였습니다. 미국 중앙은행의 물가 목표는 2%입니다.\n\n"
           f"{m[0]} 중앙은행이 {m[1].replace('어려워집니다', '어려워지고').replace('생깁니다', '생기고')}, 금리는 주가에도 영향을 줍니다. " + RATE_WHY)
    return tag, wrap(f"E{now:%y%m%d}CPI", f"미국 {obs.month}월 물가 {yoy}%", scenes, cap, ["미국물가", "CPI", "금리"], now)


LOG = []
_print = print
def print(*a, **k):  # 실행 기록을 state 파일에도 남긴다 (Actions 로그를 못 볼 때 확인용)
    LOG.append(" ".join(str(x) for x in a)); _print(*a, **k)


def main():
    now = dt.datetime.now(KST)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    today = now.date().isoformat()
    st = state.get(today, {"keys": []})
    perm = state.get("_perm", [])
    was_seeded = bool(state.get("_seeded"))
    seen = {k for kk, v in state.items() if not kk.startswith("_") for k in v.get("seen", [])} | set(perm)
    fake = None
    if "--fake" in sys.argv:
        i = sys.argv.index("--fake"); fake = (sys.argv[i + 1], float(sys.argv[i + 2]))
    made = []
    def put(tag, spec):
        os.makedirs(EVDIR, exist_ok=True)
        json.dump(spec, open(os.path.join(EVDIR, spec["id"] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        st["keys"].append(spec["id"]); st.setdefault("seen", []).append(tag); made.append(spec["id"])
        if tag.startswith(("CPI@", "FOMC@", "RADAR@")): perm.append(tag)
        print("  → 릴스 대본 생성", spec["id"], spec["scheduled_at"])
    # 1) 경제 레이더 종합 단계 변화, 2) 미국 기준금리 결정, 3) 미국 물가 발표 (가장 중요한 이슈부터)
    for chk in (check_radar, check_fomc, check_cpi):
        if fake or len(st["keys"]) >= MAX_PER_DAY: break
        try: r = chk(now, seen)
        except Exception as e:
            print("자료 실패", chk.__name__, e); continue
        if "--seed" in sys.argv and r:   # 처음 켤 때: 이미 지난 발표는 다루지 않게 표시만
            st.setdefault("seen", []).append(r[0]); seen.add(r[0]); perm.append(r[0]); print("  표시만:", r[0]); continue
        if r: put(*r)
    for key, (sym, name, th, kind) in SYMS.items():
        if len(st["keys"]) >= MAX_PER_DAY: break
        if fake and key != fake[0]: continue
        try: closes, info = history(sym)
        except Exception as e:
            print("데이터 실패", key, e); continue
        chg = (closes[-1] - closes[-2]) if kind == "rate" else (closes[-1] / closes[-2] - 1) * 100
        if fake:
            chg = fake[1]
            closes = closes[:-1] + [closes[-2] + chg if kind == "rate" else closes[-2] * (1 + chg / 100)]
            info["age_h"] = 0
        print(f"{name}: {chg:+.2f}{'%p' if kind == 'rate' else '%'} (기준 ±{th}) · {info['day']} · {info['age_h']:.0f}시간 전")
        if abs(chg) < th: continue
        tag = f"{key}@{info['day']}"
        if not fake and (tag in seen or info["age_h"] > 20):   # 이미 다룬 변동이거나 오래된 데이터(주말·휴장)면 건너뜀
            print("  건너뜀:", "이미 게시" if tag in seen else "오래된 데이터"); continue
        if "--seed" in sys.argv:
            st.setdefault("seen", []).append(tag); print("  표시만:", tag); continue
        put(tag, make_spec(key, chg, closes, now, info))
    if not fake:
        state = {k: v for k, v in state.items() if not k.startswith("_") and k >= (now.date() - dt.timedelta(days=7)).isoformat()}
        state[today] = st; state["_perm"] = perm[-60:]
        if "--seed" in sys.argv or was_seeded: state["_seeded"] = True
        state["_last"] = {"at": now.isoformat(timespec="minutes"), "log": LOG[-30:]}
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        json.dump(state, open(STATE, "w"), ensure_ascii=False)
    # 7일 지난 이벤트 대본·영상 정리
    for f in os.listdir(EVDIR) if os.path.isdir(EVDIR) else []:
        if not f.endswith(".json"): continue
        sp = json.load(open(os.path.join(EVDIR, f), encoding="utf-8"))
        if dt.datetime.fromisoformat(sp["scheduled_at"]) < now - dt.timedelta(days=7):
            os.remove(os.path.join(EVDIR, f))
            d = os.path.join(ROOT, "social", "reels", sp["id"])
            for x in os.listdir(d) if os.path.isdir(d) else []: os.remove(os.path.join(d, x))
            if os.path.isdir(d): os.rmdir(d)
    print("생성:", made or "없음")


if __name__ == "__main__":
    main()
