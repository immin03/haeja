"""The Emperor's Diary (EN) EP4 'The Night He Lost Her' thumbnails — same build as make_thumb_en4.py (large coin, Anton, white + gold, face right).
python3 scripts/side/ed_long/en/make_thumb_ep04_en.py <out_dir>
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import make_thumb_en4 as T4
WHITE, YEL = T4.WHITE, T4.YEL
# chosen EN layout (owner 2026-11-11, thumb_cine_ep01_en): coin in the top-left corner, d=520, ~15% cropped left/top, words lower (yc 0.66)
C = (182, 182, 520, 0.55)
_w = T4.words
T4.words = lambda img, lines, sub, yc=0.66: _w(img, lines, sub, yc)
T4.V = {
    "1": ("e4_alone.jpeg", (0.40, 0.14, 0.60, 0.58), [("LOST SOMEONE", 0.80, WHITE), ("YOU LOVE?", 1.0, YEL)], False,
          "WHAT MARCUS AURELIUS WROTE THAT NIGHT", C),
    "2": ("e4_dawn.jpeg", (0.435, 0.156, 0.557, 0.403), [("WHEN GRIEF", 0.80, WHITE), ("WON'T LEAVE", 1.0, YEL)], False,
          "5 STOIC WAYS THROUGH LOSS", C),
    "3": ("e4_faustina.jpeg", (0.373, 0.108, 0.56, 0.469), [("HE LOST HER.", 0.80, WHITE), ("THEN HE WROTE", 1.0, YEL)], False,
          "THE NIGHT AN EMPEROR LOST HIS WIFE", C),
}
if __name__ == "__main__":
    T4.main(sys.argv[1] if len(sys.argv) > 1 else "_thumbs_ep04")
