# -*- coding: utf-8 -*-
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
sys.path.insert(0, str(HERE.parent.parent / "libs"))
import studio
from PIL import Image, ImageChops, ImageDraw

W, H, FPS = 1920, 1080, 30
DUR = 31.0
WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#C9D1DC")
DIM = studio.hex2rgb("#7C8798")
YELLOW = studio.hex2rgb("#FFC53D")
BLUE = studio.hex2rgb("#7FB2E5")
F_TITLE = studio.font(52, "bold")
F_SUB = studio.font(32)
F_NUM = studio.font(96, "bold")
F_LAB = studio.font(28)
F_CAP = studio.font(48, "bold")
F_TICK = studio.font(26)

CARDS = [("447", "个时间点，同一分钟发布 ≥3 条"),
         ("68 秒", "中位视频时长"),
         ("43%", "时长不足一分钟")]
RATES = [("点赞率", 12.2, YELLOW), ("投币率", 2.7, GREY), ("收藏率", 1.7, GREY)]

def frame_at(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)

    ta = studio.ease_out_cubic(studio.clamp(studio.prog(t, 0.1, 0.6)))
    if ta > 0.01:
        d.text((W / 2, 140), "同一把锤子", font=F_TITLE, anchor="ms", fill=(*WHITE, int(240 * ta)))
        d.text((W / 2, 188), "839 个账号里，用专门调整过的 skill 或提示词的，不到 20 个", font=F_SUB,
               anchor="ms", fill=(*DIM, int(205 * ta)))

    # 三张卡片
    cw, ch = 420, 200
    gap = 60
    x0 = (W - (cw * 3 + gap * 2)) / 2
    for i, (num, lab) in enumerate(CARDS):
        a = studio.ease_out_cubic(studio.clamp(studio.prog(t, 1.6 + i * 0.5, 0.7)))
        if a <= 0.01:
            continue
        x = x0 + i * (cw + gap)
        y = 290
        d.rectangle([x, y, x + cw, y + ch], outline=(*DIM, int(60 * a)), width=2)
        d.text((x + cw / 2, y + 96), num, font=F_NUM, anchor="ms",
               fill=(*YELLOW, int(245 * a)))
        d.text((x + cw / 2, y + 158), lab, font=F_LAB, anchor="ms",
               fill=(*GREY, int(220 * a)))

    # 互动率
    ra = studio.ease_out_cubic(studio.clamp(studio.prog(t, 13.0, 0.9)))
    if ra > 0.01:
        d.text((W / 2, 580), "同一条视频的互动", font=F_LAB, anchor="ms",
               fill=(*DIM, int(200 * ra)))
        bx, bw = 480, 960
        for i, (name, val, col) in enumerate(RATES):
            y = 620 + i * 52
            d.text((bx - 20, y + 14), name, font=F_LAB, anchor="rm",
                   fill=(*GREY, int(215 * ra)))
            d.rectangle([bx, y, bx + bw * (val / 14.0), y + 28], fill=(*col, int(225 * ra)))
            d.text((bx + bw * (val / 14.0) + 16, y + 14), "%.1f%%" % val, font=F_LAB,
                   anchor="lm", fill=(*GREY, int(215 * ra)))

    # 收尾
    ca = studio.ease_out_cubic(studio.clamp(studio.prog(t, 26.6, 0.9)))
    if ca > 0.01:
        d.text((W / 2, 860), "同一把锤子，锤不出不同的东西", font=F_CAP, anchor="ms",
               fill=(*WHITE, int(245 * ca)))

    fi = studio.ease_in_out(studio.clamp(studio.prog(t, 0.0, 0.6)))
    fo = 1.0 - studio.ease_in_out(studio.clamp(studio.prog(t, DUR - 0.6, 0.6)))
    m = min(fi, fo)
    if m < 0.999:
        c.putalpha(ImageChops.multiply(c.getchannel("A"), Image.new("L", (W, H), int(255 * m))))
    return c


OUT = HERE / "out" / "ch5_alpha.mov"


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
