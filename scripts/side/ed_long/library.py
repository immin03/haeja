"""황제의 일기 시네마틱 장면 라이브러리 (2026-11-05 대표: "어차피 계속 쓸 장면은 한 번 공들여 만들어 두고 반복해 쓰자")

· 장면마다 영상(고화질 seedance 5초)과 소리 묶음(배경음 + 효과음), 카메라 움직임, 입자 효과를 한 번에 정해 둔다.
· 대본/렌더 설정에서는 lib_shot("tent_stars") 처럼 이름만 부르면 된다. 같은 장면도 편마다 다른 버전·각도가 나오게 variant 를 돌려 쓴다.
· 여운 장면(breath): 목소리 없는 3초 안팎. 지루하지 않게 ① 항상 움직이는 영상 ② 카메라가 계속 움직이고 ③ 소리가 들리고 ④ 목소리가 빠진 만큼 음악이 올라온다(사이드체인 덕킹 해제).

python3 library.py gen 1|2|3   → scripts/side/gen/EDL261105-lib{n}.json (비용 상한 3달러 안에 나눠 생성)
"""
import json, os, sys, copy

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
from ep01 import STYLE, EMP

SEED = "bytedance/seedance-2.5/image-to-video"
CINE = ("Cinematic, like a shot from a big-budget historical film. Keep the painterly oil-painting look, the lighting and every detail identical to the first frame. "
        "Smooth, slow, elegant camera motion only, no cuts, no sudden shake, no morphing faces, no extra fingers or limbs, no text appearing.")

# 이름: (그림 설명, 영상 움직임, 기본 소리 amb, 효과음 sfx [[파일, 시작초, 크기]], 카메라 move, 입자, 그림 질감)
LIB = {
 "quill": ("Extreme macro close-up at night of the tip of a thin reed pen writing on rough papyrus, a fresh line of dark brown ink still wet and glistening, "
           "an older man's weathered fingers holding the pen in the edge of the frame, the deep crimson sleeve of a cloak, warm candle bokeh glowing in the soft background, "
           "dust motes floating in the candlelight, the writing is only soft abstract ink strokes, nothing readable, very shallow depth of field.",
           "The pen tip glides slowly to the right leaving a thin wet ink stroke, tiny lifts between strokes; the candle bokeh shimmers; the camera slides very slowly sideways along the line.",
           ["fire_0.mp3", 0.3], [["paper_6.mp3", 0.2, 0.55]], {"zoom": [1.0, 1.06], "pan": [[0.01, 0], [-0.01, 0]]}, "dust", None),
 "quill2": ("Close-up at night, seen from the side at desk height, of an older man's weathered hand in a deep crimson sleeve writing with a thin reed pen across a sheet of papyrus, "
            "several long straight horizontal rows of small faint brown handwriting already on the sheet, so soft and out of focus that they are only blurred grey-brown lines, "
            "the pen tip at the end of the newest row, a candle glowing warmly on the far side of the desk, dust motes in the candlelight, shallow depth of field, nothing readable, no symbols.",
            "The hand writes slowly along the same straight row, the pen gliding to the right in small natural strokes; the candle flame flickers; the camera slides very slowly sideways.",
            ["fire_0.mp3", 0.3], [["paper_6.mp3", 0.2, 0.55]], {"zoom": [1.0, 1.06], "pan": [[0.01, 0], [-0.01, 0]]}, "dust", None),
 "candle_face": ("Close portrait in profile of " + EMP + " sitting at a wooden desk inside his command tent at night, writing, his eyes lowered to the papyrus, "
                 "his face lit only by a single candle flame in the foreground, warm golden rim light on his beard and grey curls, deep darkness behind, "
                 "his face is in the middle of the frame, fully visible, with space above his head.",
                 "He keeps writing slowly, pauses, and his eyes lift a little as he thinks, then lower again; the candle flame breathes and its light moves over his face; very slow push-in.",
                 ["fire_4.mp3", 0.3], [["paper_6.mp3", 0.6, 0.35]], {"zoom": [1.0, 1.07], "pingpong": True}, None, None),
 "tent_stars": ("Wide shot at night of " + EMP + " standing alone outside his command tent on a hill above a Roman legion camp beside the Danube river, seen from behind and a little to the side, "
                "looking up at a vast starry sky with the Milky Way, rows of tents glowing with small campfires below, thin smoke rising, sparks drifting up, cool deep blue night with warm firelight.",
                "Sparks and embers drift slowly upward from the campfires, thin smoke curls, his cloak moves gently in the wind, stars twinkle; the camera rises slowly and tilts up toward the sky.",
                ["night_6.mp3", 0.28], [["fire_3.mp3", 0.0, 0.25]], {"zoom": [1.0, 1.06], "pan": [[0.0, 0.02], [0.0, -0.02]]}, "embers", None),
 "candle_diary": ("Close-up on a wooden desk at night: an open leather-bound diary of papyrus pages, a reed pen resting across it, a half-burnt candle with wax dripping slowly down, "
                  "a thin curl of smoke, a bronze inkpot, warm candlelight in deep darkness, extremely shallow depth of field, the pages show only soft blurred ink strokes, nothing readable.",
                  "The candle flame flickers and leans, a drop of wax rolls slowly down the candle, the smoke curls; the camera orbits very slowly around the diary.",
                  ["fire_0.mp3", 0.32], [["paper_3.mp3", 1.2, 0.3]], {"zoom": [1.0, 1.08]}, "dust", None),
 "dawn_camp": ("Wide view at dawn of a Roman legion camp on the bank of the Danube river, low golden mist drifting over the water and the rows of tents, legion standards and eagles silhouetted against a pale golden sunrise, "
               "a few soldiers walking, a flock of birds over the river, cold blue shadows and warm gold light.",
               "Mist drifts slowly over the river and the tents, the birds fly across the sky, standards sway gently; the camera dollies slowly sideways along the river bank.",
               ["wind_2.mp3", 0.25], [["horse_3.mp3", 0.3, 0.18]], {"zoom": [1.0, 1.05], "pan": [[0.02, 0], [-0.02, 0]]}, None, None),
 "window_moon": ("Medium shot of " + EMP + " standing at a tall arched window of a dark marble palace room at night, looking out at the moonlit city of Rome, a sheer curtain beside him, "
                 "cold silver moonlight on his face and a faint warm oil lamp behind him, his face is in the middle of the frame, fully visible, with space above his head.",
                 "The sheer curtain billows slowly in the night wind, the lamp flame flickers behind him, he breathes slowly and keeps looking out; very slow push-in.",
                 ["wind_2.mp3", 0.25], [["night_4.mp3", 0.0, 0.15]], {"zoom": [1.0, 1.07]}, None, None),
 "close_diary": ("Close-up at night on a wooden desk: an older man's weathered hand in a crimson sleeve gently closing a leather-bound diary, beside it a single candle burning, "
                 "warm candlelight, deep shadows, dust in the air, shallow depth of field.",
                 "The hand slowly closes the leather diary and rests on it for a moment; the candle flame leans and flickers; the camera pushes in very slowly.",
                 ["fire_0.mp3", 0.25], [["paper_3.mp3", 0.6, 0.5]], {"zoom": [1.0, 1.07]}, "dust", None),
 "rain_march": ("Wide shot at dusk of a long column of Roman legionaries marching in steady rain along a muddy road through a dark forest, torches hissing, red cloaks soaked, "
                "breath steaming, a mounted figure in a crimson cloak in the middle of the column, grey-blue light with warm torchlight.",
                "The column marches slowly forward through the rain, raindrops streak down, torch flames gutter and smoke; the camera tracks slowly alongside the column.",
                ["rain_4.mp3", 0.35], [["war_7.mp3", 0.0, 0.12]], {"zoom": [1.0, 1.05], "pan": [[-0.02, 0], [0.02, 0]]}, None, None),
 "river_night": ("Very wide shot at night of the Danube river under a full moon, the moon's silver reflection shimmering on the water, a Roman camp with small campfires on the far bank, "
                 "on the near bank the small dark silhouette of a lone man in a cloak standing at the water's edge, mist over the water, deep blue night.",
                 "The moonlight shimmers and ripples on the river, mist drifts slowly over the water, the campfires flicker far away; the camera pushes in very slowly toward the lone figure.",
                 ["wind_7.mp3", 0.22], [["night_3.mp3", 0.0, 0.2]], {"zoom": [1.0, 1.06]}, None, None),
 "brazier_hands": ("Close-up at night of an older man's weathered hands held out over a bronze brazier full of glowing coals inside a dark command tent, the deep crimson sleeves of his cloak, "
                   "sparks rising, warm orange light on the hands, deep shadows behind.",
                   "Sparks rise and swirl slowly from the coals, the glow pulses, the fingers flex slightly in the warmth; the camera drifts slowly upward with the sparks.",
                   ["fire_4.mp3", 0.35], [], {"zoom": [1.0, 1.06], "pan": [[0.0, 0.01], [0.0, -0.015]]}, "embers", None),
}
# 생성 묶음 (push 한 번당 비용 상한 3달러: 그림 0.05 · seedance 5초 약 0.75)
BATCH = {1: ["quill", "candle_face", "tent_stars"], 2: ["candle_diary", "dawn_camp", "window_moon", "close_diary"], 3: ["rain_march", "river_night", "quill2"], 4: ["brazier_hands"]}   # quill(1차)은 잉크 자국이 기호처럼 보여 quill2 로 다시


def img_id(name): return "lib_" + name
def vid_id(name): return "libv_" + name


def gen(n):
    jobs = []
    if n == 3: jobs.append({"id": img_id("quill2"), "kind": "image", "endpoint": "xai/grok-imagine-image-2.0", "body": {"aspect_ratio": "16:9", "prompt": LIB["quill2"][0] + " " + STYLE}})
    if n == 1:   # 그림은 첫 묶음에서 전부
        jobs += [{"id": img_id(k), "kind": "image", "endpoint": "xai/grok-imagine-image-2.0", "body": {"aspect_ratio": "16:9", "prompt": v[0] + " " + STYLE}} for k, v in LIB.items()]
    jobs += [{"id": vid_id(k), "kind": "video", "endpoint": SEED, "image": f"social/side/gen/{img_id(k)}.jpeg", "body": {"duration": 5, "prompt": LIB[k][1] + " " + CINE}} for k in BATCH[n]]
    p = os.path.join(ROOT, f"scripts/side/gen/EDL261105-lib{n}.json"); json.dump(jobs, open(p, "w"), ensure_ascii=False, indent=1)
    print(p, len(jobs))


def have(name):
    return os.path.exists(os.path.join(ROOT, "social/side/gen", vid_id(name) + ".mp4"))


def lib_shot(name, voices=None, dur=3.2, extra=None):
    """라이브러리 장면 하나. voices 가 없으면 여운 장면(목소리 없이 dur 초)."""
    _, _, amb, sfx, move, parts, grade = LIB[name]
    src = vid_id(name) if have(name) else img_id(name)
    s = {"type": "video" if have(name) else "still", "src": src, "amb": list(amb), "sfx": copy.deepcopy(sfx), "move": copy.deepcopy(move), "lib": name}
    if parts: s["particles"] = parts
    if grade: s["grade"] = grade
    if voices: s["voice"] = voices
    else: s.update({"dur": dur, "fixed": True, "breath": True, "tin": "dissolve"})
    if extra: s.update(extra)
    return s


if __name__ == "__main__":
    if sys.argv[1] == "gen": gen(int(sys.argv[2]))
