"""취재 노트 손그림 페이지 빠른 점검 (영상·음성 없이 장면 끝 페이지만 그린다)

  python3 scripts/youtube/long/nb_pages.py <원고.json> <출력 폴더> [장면 번호 ...]

장면마다 손그림이 다 그려진 마지막 순간의 종이(1920x1080)를 sc<번호>.jpg 로 저장하고,
여러 장을 이어 붙인 sheet.jpg 도 만든다. 문장 길이는 글자 수로 어림한다(실제 음성보다 조금 다를 수 있다).
노트 카메라·책상은 그리지 않으니 배치(겹침·쏠림·빈자리·글씨 크기)만 본다.
"""
import json, os, sys  # noqa: E401
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import render2 as R2  # noqa: E402
import sketch as SK  # noqa: E402


def main():
    spec_path, out = sys.argv[1], sys.argv[2]
    only = [int(a) for a in sys.argv[3:]]
    spec = json.load(open(spec_path, encoding="utf-8"))
    data = json.load(open(spec_path.replace(".json", ".data.json"), encoding="utf-8")); V = data["vars"]; R2.CV.update(V)
    R2.set_look(spec.get("look")); R2.TH["light"]["bg"] = (243, 236, 221); R2._bg.clear()
    os.makedirs(out, exist_ok=True)
    cold = int(spec.get("notebook", {}).get("cold_open", 0)); shots = []
    for k, sc in enumerate(spec["scenes"]):
        if only and k not in only: continue
        typ = sc["v"]["type"]
        if not (k >= cold and (sc.get("sketch") is not None or typ in SK.AUTO_TYPES)): continue
        lines = []; u = .25
        for l in sc["lines"]:
            try: t = R2.fill(l.lstrip("?"), V)
            except KeyError: continue
            d = len(t) / 9.2; lines.append((u, d, t)); u += d + .2
        sk = SK.scene_beats(sc, lines, V, R2.fill, R2.at_time, True)
        if sk is None: continue
        end = max([z.t1 for z in sk] + [u]) + .5
        arr = np.asarray(R2.background("light").convert("RGB")).copy(); SK.apply(arr, sk, end)
        im = Image.fromarray(arr); p = os.path.join(out, f"sc{k:02d}.jpg"); im.save(p, quality=85); shots.append(im)
        for g in SK.gaps(sk, lines): print("  ⚠ 빈틈", k, g)
        print(k, typ, "비트", len(sk))
    if shots:
        cols = 3; tw = 640; th = 360; rows_ = (len(shots) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows_ * th), (40, 40, 40))
        for i, im in enumerate(shots): sheet.paste(im.resize((tw - 4, th - 4)), ((i % cols) * tw + 2, (i // cols) * th + 2))
        sheet.save(os.path.join(out, "sheet.jpg"), quality=85)


if __name__ == "__main__":
    main()
