"""운영자 목소리 클론 청취 샘플 만들기 (2026-10-25)
scripts/voice/sample_request.json 의 문장을 렌더와 같은 방식(타입캐스트 클론 1.1배 + 발음 변환)으로 읽어
문장별 mp3 와, 여러 문장을 문장 사이 쉼(gaps)별로 이어 붙인 mp3 를 out 폴더에 만든다.
결과는 워크플로가 암호화해서 voice-xchg 가지에 올린다 (목소리 파일은 평문으로 저장소에 남기지 않는다).
사용: python3 scripts/voice/sample.py <out_dir>"""
import json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "reels"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "youtube", "long"))
from korean import to_speech  # noqa: E402
from tts import speak, SR  # noqa: E402


def mp3(a, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-b:a", "160k", path],
                   input=np.asarray(a, np.float32).tobytes(), check=True)


def main(out):
    req = json.load(open(os.path.join(HERE, "sample_request.json"), encoding="utf-8"))
    os.makedirs(out, exist_ok=True)
    for i, t in enumerate(req.get("singles", []), 1):
        mp3(speak(to_speech(t), 1.1), os.path.join(out, f"{i:02d}_문장.mp3"))
        print("문장", i, t[:30], flush=True)
    seq = [speak(to_speech(t), 1.1) for t in req.get("joined", [])]
    for g in req.get("gaps", [0.18]):
        parts = []
        for a in seq:
            parts += [a, np.zeros(int(g * SR), np.float32)]
        if parts:
            mp3(np.concatenate(parts), os.path.join(out, f"이어듣기_쉼{g:.2f}초.mp3"))
            print("이어 듣기", g, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
