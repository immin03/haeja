"""시장 급변 감지 → 릴스 대본 자동 생성 (사람·AI 없이 규칙으로 작성, 토큰 0)
GitHub Actions에서 3시간마다 실행. 조건에 걸리면 events/E*.json 을 쓰고 build.py가 영상으로 만든다.

감지 기준 (전일 종가 대비)
  코스피 ±3%, 코스닥 ±4%, S&P 500 ±2%, 나스닥 ±2.5%, 원·달러 환율 ±1.2%, 미국 10년물 금리 ±0.15%p
제한: 하루(한국 시간) 최대 2편, 같은 지표는 하루 1편, 새벽(01~07시)에는 07:30으로 미뤄 게시

테스트: python3 events.py --fake KS11 -4.2   (가짜 변동으로 대본만 만들어 본다)
"""
import os, sys, json, math, time, datetime as dt, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EVDIR = os.path.join(HERE, "events")
STATE = os.path.join(ROOT, "social", "reels", "events_state.json")
KST = dt.timezone(dt.timedelta(hours=9))
MAX_PER_DAY = 2

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


def pass_count():
    try:
        st = json.load(open(os.path.join(ROOT, "social", "daily", "state.json"), encoding="utf-8"))
        if (dt.date.today() - dt.date.fromisoformat(st["date"])).days <= 4: return len(st.get("pass", []))
    except Exception:
        pass
    return None


def man(v): return f"{round(v):,}만"


def make_spec(key, chg, closes, now, info=None):
    sym, name, th, kind = SYMS[key]
    up = chg > 0
    day = (info or {}).get("day") or now.date()
    md = f"{day.month}월 {day.day}일" + (" 장중" if (info or {}).get("live") else "")
    when = now + dt.timedelta(minutes=60)
    if 1 <= when.hour < 7: when = when.replace(hour=7, minute=30)
    days, fwd, nf = stats(closes[:-1], kind, chg)
    scenes = []
    if kind == "rate":
        prev, cur = closes[-2], closes[-1]
        scenes.append({"type": "hook", "top": f"{name} 하루", "num": {"to": chg, "fmt": "int", "dec": 2, "suffix": "%p", "sign": True},
                       "tone": "loss" if up else "gold", "label": f"{md} · {cur:.2f}%",
                       "cap": [f"{name}{josa(name, '이', '가')} 하루에", f"{chg:+.2f}%p"]})
        scenes.append({"type": "compare", "l": {"label": "전날", "v": f"{prev:.2f}%", "tone": "gray"},
                       "r": {"label": "오늘", "v": f"{cur:.2f}%", "tone": "loss" if up else "good"},
                       "cap": [f"{prev:.2f}%에서 {cur:.2f}%로"]})
        st = ("금리가 오르면", "미래 이익의 값이 줄어듭니다") if up else ("금리가 내리면", "기다림의 값이 달라집니다")
    else:
        money = 1000 * (1 + chg / 100); diff = money - 1000
        unit = "원" if kind == "fx" else ""
        cur = closes[-1]
        label = f"{md} · {cur:,.1f}원" if kind == "fx" else f"{md} 기준"
        tone = ("loss" if not up else "gold") if kind == "idx" else "gold"
        scenes.append({"type": "hook", "top": f"{name} 하루", "num": {"to": round(chg, 1), "fmt": "pct", "dec": 1}, "tone": tone, "label": label,
                       "cap": [f"{name}{josa(name, '이', '가')} 하루에 {chg:+.1f}%"]})
        if kind == "idx":
            scenes.append({"type": "compare", "l": {"label": "어제", "v": "1,000만", "tone": "gray"},
                           "r": {"label": "오늘", "v": man(money), "sub": f"{diff:+,.0f}만 원", "tone": "good" if up else "loss"},
                           "cap": ["1,000만 원이었다면", f"하루 만에 {man(abs(diff))} 원이 {'늘었습니다' if up else '사라졌습니다'}"]})
        else:
            scenes.append({"type": "compare", "l": {"label": "달러 자산\n1,000만 원", "v": "1,000만", "tone": "gray"},
                           "r": {"label": "원화로 환산하면", "v": man(money), "sub": f"{diff:+,.0f}만 원", "tone": "good" if up else "loss"},
                           "cap": ["달러로 1,000만 원을 가졌다면", f"원화 기준 {man(money)} 원"]})
        if up: st = ("급등장에서 먼저 볼 것은", "가격입니다") if kind == "idx" else ("환율이 흔들릴 때", "기업 실적이 갈립니다")
        else: st = ("급락장에서 먼저 볼 것은", "내 기준입니다") if kind == "idx" else ("환율이 흔들릴 때", "기업 실적이 갈립니다")
    word = "오른" if up else "빠진"
    if days >= 2:
        if fwd is not None:
            scenes.append({"type": "compare", "l": {"label": f"최근 10년\n이만큼 {word} 날", "v": f"{days}번", "tone": "gold"},
                           "r": {"label": "그 1년 뒤\n평균", "v": f"{fwd:+.0f}%", "tone": "good" if fwd > 0 else "loss"},
                           "cap": [f"최근 10년 이런 날은 {days}번", f"1년 뒤 평균 {fwd:+.0f}%"]})
        else:
            scenes.append({"type": "compare", "l": {"label": "최근 10년", "v": f"{days}번", "tone": "gold"},
                           "r": {"label": "1년에", "v": f"{days / 10:.1f}번", "tone": "gray"},
                           "cap": [f"최근 10년 이런 날은 {days}번"]})
    n = pass_count()
    note = f"밸류노트 기준 통과 기업 {n}개" if n else None
    scenes.append({"type": "statement", "l1": st[0], "l2": st[1], "tone": "loss" if (kind == "rate" and up) else "gold", **({"note": note} if note else {})})
    scenes.append({"type": "cta"})
    head = f"{md} {name}{josa(name, '이', '가')} 하루에 " + (f"{chg:+.2f}%p" if kind == "rate" else f"{chg:+.1f}%") + (" 올랐습니다." if up else " 내렸습니다." if kind != "idx" else " 빠졌습니다.")
    lines = [head]
    if kind == "idx": lines.append(f"1,000만 원이었다면 하루 만에 {man(abs(diff))} 원이 {'늘었습니다' if up else '사라졌습니다'}.")
    if days >= 2:
        lines.append(f"최근 10년 동안 이만큼 {word} 날은 {days}번이었습니다." + (f"\n그 1년 뒤 지수는 평균 {fwd:+.0f}%였습니다. (과거 평균이며 앞으로를 보장하지 않습니다)" if fwd is not None else ""))
    lines.append(f"{st[0]} {st[1].rstrip('.')}.")
    if note: lines.append(f"지금 {note.replace('밸류노트 ', '밸류노트 ')}입니다.")
    return {"id": f"E{day:%y%m%d}{key}", "title": f"{md} {name} " + (f"{chg:+.2f}%p" if kind == "rate" else f"{chg:+.1f}%"),
            "scheduled_at": when.isoformat(timespec="minutes"), "mood": "tense", "event": key,
            "caption": "\n\n".join(lines), "hashtags": [name.replace(" ", "").replace("·", ""), "오늘의시장", "주식뉴스", "주식공부", "밸류노트"],
            "threads_tag": "주식뉴스", "scenes": scenes}


def main():
    now = dt.datetime.now(KST)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    today = now.date().isoformat()
    st = state.get(today, {"keys": []})
    seen = {k for v in state.values() for k in v.get("seen", [])}
    fake = None
    if "--fake" in sys.argv:
        i = sys.argv.index("--fake"); fake = (sys.argv[i + 1], float(sys.argv[i + 2]))
    made = []
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
        spec = make_spec(key, chg, closes, now, info)
        os.makedirs(EVDIR, exist_ok=True)
        json.dump(spec, open(os.path.join(EVDIR, spec["id"] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        st["keys"].append(key); st.setdefault("seen", []).append(tag); made.append(spec["id"])
        print("  → 릴스 대본 생성", spec["id"], spec["scheduled_at"])
    if not fake:
        state = {k: v for k, v in state.items() if k >= (now.date() - dt.timedelta(days=7)).isoformat()}
        state[today] = st
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
