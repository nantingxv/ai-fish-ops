# -*- coding: utf-8 -*-
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
sys.path.insert(0, str(HERE.parent.parent / "libs"))
import studio
from PIL import Image, ImageChops, ImageDraw

W, H, FPS = 1920, 1080, 30
DUR = 38.0
WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#C9D1DC")
DIM = studio.hex2rgb("#7C8798")
YELLOW = studio.hex2rgb("#FFC53D")
BLUE = studio.hex2rgb("#7FB2E5")
F_TITLE = studio.font(52, "bold")
F_SUB = studio.font(32)
F_VAL = studio.font(30, "bold")
F_BIG = studio.font(86, "bold")
F_TICK = studio.font(26)
F_CAP = studio.font(52, "bold")

# 存活率（7 天未更新即停更），11/03 起才有区分度
SERIES = [("11/03", 91.9), ("11/04", 88.6), ("11/05", 85.0), ("11/06", 80.6),
          ("11/07", 76.7), ("11/08", 73.3), ("11/09", 71.0), ("11/10", 68.3),
          ("11/11", 66.3)]

def frame_at(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)

    ta = studio.ease_out_cubic(studio.clamp(studio.prog(t, 0.1, 0.6)))
    if ta > 0.01:
        d.text((W / 2, 150), "停更潮", font=F_TITLE, anchor="ms", fill=(*WHITE, int(240 * ta)))
        d.text((W / 2, 200), "超过 7 天没有更新，记为停更", font=F_SUB, anchor="ms",
               fill=(*DIM, int(205 * ta)))

    # 大数字
    na = studio.ease_out_cubic(studio.clamp(studio.prog(t, 0.9, 0.7)))
    if na > 0.01:
        d.text((470, 360), "274", font=F_BIG, anchor="ms", fill=(*YELLOW, int(245 * na)))
        d.text((470, 420), "个账号已停更", font=F_SUB, anchor="ms", fill=(*GREY, int(220 * na)))
        d.text((790, 360), "/ 812", font=F_BIG, anchor="ms", fill=(*GREY, int(190 * na)))
        d.text((790, 420), "总账号", font=F_SUB, anchor="ms", fill=(*DIM, int(190 * na)))

    # 对比：停更 vs 在更（中位条数）
    ca2 = studio.ease_out_cubic(studio.clamp(studio.prog(t, 3.2, 0.9)))
    if ca2 > 0.01:
        bx = 1150
        bw = 420
        d.text((bx, 322), "停更账号", font=F_SUB, anchor="lm", fill=(*DIM, int(210 * ca2)))
        d.text((bx, 356), "中位发 3 条", font=F_SUB, anchor="lm", fill=(*GREY, int(220 * ca2)))
        d.rectangle([bx, 374, bx + bw * (3 / 15.0), 396], fill=(*GREY, int(150 * ca2)))
        d.text((bx, 442), "在更账号", font=F_SUB, anchor="lm", fill=(*DIM, int(210 * ca2)))
        d.text((bx, 476), "中位发 15 条", font=F_SUB, anchor="lm", fill=(*GREY, int(220 * ca2)))
        d.rectangle([bx, 494, bx + bw, 516], fill=(*YELLOW, int(215 * ca2)))
        d.text((bx, 560), "单条播放：362  vs  304", font=F_TICK, anchor="lm",
               fill=(*DIM, int(200 * ca2)))

    # 折线
    x0, x1 = 300, 1600
    y0, y1 = 660, 880
    n = len(SERIES)
    step = (x1 - x0) / (n - 1)
    la = studio.ease_in_out(studio.clamp(studio.prog(t, 2.4, 1.6)))
    if la > 0.01:
        pts = []
        for i, (_, v) in enumerate(SERIES):
            yy = y1 - (v - 60.0) / 40.0 * (y1 - y0)
            pts.append((x0 + i * step, yy))
        k = int(la * (n - 1))
        seg = pts[:k + 1]
        if k < n - 1:
            a0 = pts[k]
            a1 = pts[k + 1]
            f = la * (n - 1) - k
            seg.append((a0[0] + (a1[0] - a0[0]) * f, a0[1] + (a1[1] - a0[1]) * f))
        if len(seg) >= 2:
            d.line(seg, fill=(*BLUE, 240), width=5, joint="curve")
        for i, (lab, v) in enumerate(SERIES):
            if i / (n - 1) <= la + 0.01:
                d.ellipse([pts[i][0] - 6, pts[i][1] - 6, pts[i][0] + 6, pts[i][1] + 6],
                          fill=(*BLUE, 240))
                d.text((pts[i][0], y1 + 34), lab, font=F_TICK, anchor="ms",
                       fill=(*DIM, int(200 * ta)))
        # 首末数值
        for idx in (0, n - 1):
            if idx / (n - 1) <= la + 0.01:
                v = SERIES[idx][1]
                d.text((pts[idx][0], pts[idx][1] - 26), "%.1f%%" % v, font=F_VAL, anchor="ms",
                       fill=(*WHITE, int(235 * la)))

    # 收尾句
    ca = studio.ease_out_cubic(studio.clamp(studio.prog(t, 32.4, 0.9)))
    if ca > 0.01:
        d.text((W / 2, 998), "在面临断供的风险中，停更成了最优的选择", font=studio.font(46, "bold"),
               anchor="ms", fill=(*WHITE, int(245 * ca)))

    fi = studio.ease_in_out(studio.clamp(studio.prog(t, 0.0, 0.6)))
    fo = 1.0 - studio.ease_in_out(studio.clamp(studio.prog(t, DUR - 0.6, 0.6)))
    m = min(fi, fo)
    if m < 0.999:
        c.putalpha(ImageChops.multiply(c.getchannel("A"), Image.new("L", (W, H), int(255 * m))))
    return c


OUT = HERE / "out" / "ch4_alpha.mov"


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
