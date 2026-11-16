# -*- coding: utf-8 -*-
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
sys.path.insert(0, str(HERE.parent.parent / "libs"))
import studio
from PIL import Image, ImageChops, ImageDraw

W, H, FPS = 1920, 1080, 30
DUR = 13.0
WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#C9D1DC")
DIM = studio.hex2rgb("#7C8798")
YELLOW = studio.hex2rgb("#FFC53D")
F_TITLE = studio.font(40, "bold")
F_ROW = studio.font(34)
F_NUM = studio.font(40, "bold")
F_TOTAL = studio.font(64, "bold")
ROWS = [("数据获取工具", "14.09"), ("视频制作与数据分析", "21.15")]


def fade(t, a, b):
    return studio.ease_in_out(studio.clamp(studio.prog(t, a, b - a)))

def frame_at(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)

    a0 = fade(t, 0.3, 1.0)
    if a0 > 0.01:
        d.text((W / 2, 330), "制作这条视频的成本", font=F_TITLE, anchor="ms",
               fill=(*DIM, int(220 * a0)))

    for i, (lab, val) in enumerate(ROWS):
        a = fade(t, 1.2 + i * 0.6, 1.8 + i * 0.6)
        if a <= 0.01:
            continue
        y = 430 + i * 74 + (1 - a) * 16
        d.text((620, y), lab, font=F_ROW, anchor="rm", fill=(*GREY, int(225 * a)))
        d.text((1040, y), val + " 元", font=F_NUM, anchor="lm", fill=(*WHITE, int(240 * a)))

    a2 = fade(t, 3.4, 4.0)
    if a2 > 0.01:
        d.line([(620, 596), (1180, 596)], fill=(*DIM, int(90 * a2)), width=2)
        d.text((620, 664), "合计", font=F_ROW, anchor="rm", fill=(*GREY, int(225 * a2)))
        d.text((860, 660), "35.18 元", font=F_TOTAL, anchor="lm",
               fill=(*YELLOW, int(248 * a2)))

    a3 = fade(t, 6.0, 7.0)
    if a3 > 0.01:
        d.text((W / 2, 810), "数据截止 2026 年 11 月 11 日", font=studio.font(26),
               anchor="ms", fill=(*DIM, int(170 * a3)))

    fi = studio.ease_in_out(studio.clamp(studio.prog(t, 0.0, 0.8)))
    fo = 1.0 - studio.ease_in_out(studio.clamp(studio.prog(t, DUR - 1.4, 1.4)))
    m = min(fi, fo)
    if m < 0.999:
        c.putalpha(ImageChops.multiply(c.getchannel("A"), Image.new("L", (W, H), int(255 * m))))
    return c


OUT = HERE / "out" / "cost_alpha.mov"


def main():
    n = int(DUR * FPS)
    print("%d 帧 -> %s" % (n, OUT))
    vcodec = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
              "-vendor", "apl0", "-qscale:v", "12"]
    with studio.VideoWriter(OUT, (W, H), fps=FPS, in_fmt="rgba", vcodec=vcodec) as w:
        for f_ in range(n):
            w.write(frame_at(f_ / FPS))
    print("done:", OUT, round(OUT.stat().st_size / 1048576, 1), "MB")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--frame":
        tv = float(sys.argv[2])
        dst = sys.argv[3] if len(sys.argv) > 3 else str(HERE / "out" / ("f_%s.png" % tv))
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        frame_at(tv).save(dst)
        print("saved", dst)
    else:
        main()
