# -*- coding: utf-8 -*-
import csv
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
sys.path.insert(0, str(HERE.parent.parent / "libs"))
import studio
from PIL import Image, ImageChops, ImageDraw

W, H, FPS = 1920, 1080, 30
DUR = 19.5
WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#C9D1DC")
DIM = studio.hex2rgb("#7C8798")
YELLOW = studio.hex2rgb("#FFC53D")
BLUE = studio.hex2rgb("#7FB2E5")
F_TICK = studio.font(24)
F_LEG = studio.font(28)
F_TITLE = studio.font(52, "bold")
F_CAP = studio.font(56, "bold")
F_VAL = studio.font(30, "bold")
EXPORT = Path(r"D:/tmp/export")
AX_Y = 860
X0, X1 = 240, 1680      # 与 008 段完全一致：轴线和纵坐标位置不变，只换刻度
D0 = datetime.fromisoformat("2026-10-08T00:00:00+08:00")
NDAY = 35
I0, I1 = 19, 34

def load():
    seen, vids = set(), []
    with open(EXPORT / "video.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["bvid"] in seen:
                continue
            seen.add(r["bvid"])
            vids.append(r)
    cnt = [0] * NDAY
    per = defaultdict(list)
    for v in vids:
        dd = (datetime.fromisoformat(v["pub_time"]) - D0).days
        if 0 <= dd < NDAY:
            cnt[dd] += 1
            per[dd].append(float(v["view"] or 0))
    med = [float(np.median(per[i])) if per[i] else 0.0 for i in range(NDAY)]
    return cnt, med

CNT, MED = load()
DAYS = [D0 + timedelta(days=i) for i in range(NDAY)]
N = I1 - I0 + 1

def day_x(i):
    return X0 + (X1 - X0) * (i - I0) / (N - 1)

def frame_at(t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    ax_a = studio.ease_in_out(studio.clamp(studio.prog(t, 0.10, 0.70)))
    ta = studio.ease_out_cubic(studio.clamp(studio.prog(t, 0.2, 0.9)))
    if ta > 0.01:
        d.text((W / 2, 190), "价格止跌，供给退场", font=F_TITLE, anchor="ms",
               fill=(*WHITE, int(240 * ta)))
        d.text((W / 2, 246), "10 月 27 日 — 11 月 11 日", font=F_LEG, anchor="ms",
               fill=(*DIM, int(200 * ta)))

    for i in range(I0, I1 + 1):
        e = studio.ease_out_cubic(studio.clamp(studio.prog(t, 1.3 + (i - I0) * 0.06, 0.6)))
        if e <= 0.004:
            continue
        h = 430.0 * (CNT[i] / 700.0) * e
        x = day_x(i)
        d.rectangle([x - 13, AX_Y - h, x + 13, AX_Y], fill=(*YELLOW, 235))

    la = studio.ease_out_cubic(studio.clamp(studio.prog(t, 3.6, 1.2)))
    if la > 0.01:
        pts = []
        for i in range(I0, I1 + 1):
            v = max(0.0, min(1.0, (MED[i] - 120.0) / 180.0))
            pts.append((day_x(i), AX_Y - (470 + 110 * v)))
        d.line(pts, fill=(*BLUE, int(240 * la)), width=5, joint="curve")
        for x_, y_ in (pts[0], pts[-1]):
            d.ellipse([x_ - 7, y_ - 7, x_ + 7, y_ + 7], fill=(*BLUE, int(240 * la)))

    # 轴线立刻就在（和上一段同一条线），只让刻度淡入
    d.line([(X0 - 30, AX_Y), (X1 + 20, AX_Y)], fill=(*DIM, 160), width=2)
    for i in range(I0, I1 + 1):
        x = day_x(i)
        big = (i - I0) % 3 == 0 or i == I1
        d.line([(x, AX_Y), (x, AX_Y + (16 if big else 9))],
               fill=(*DIM, int((130 if big else 80) * ax_a)), width=2)
        if big and i >= I0:
            d.text((x, AX_Y + 48), DAYS[i].strftime("%m/%d"), font=F_TICK, anchor="ms",
                   fill=(*DIM, int(195 * ta)))

    if ta > 0.01:
        d.rectangle([X1 - 340, 246, X1 - 324, 262], fill=(*YELLOW, int(230 * ta)))
        d.text((X1 - 312, 262), "每日发布", font=F_LEG, anchor="ls", fill=(*GREY, int(210 * ta)))
        d.line([(X1 - 136, 254), (X1 - 100, 254)], fill=(*BLUE, int(230 * ta)), width=5)
        d.text((X1 - 88, 262), "单条中位", font=F_LEG, anchor="ls", fill=(*GREY, int(210 * ta)))

    va = studio.ease_out_cubic(studio.clamp(studio.prog(t, 5.2, 0.8)))
    if va > 0.01:
        d.text((day_x(I0), AX_Y - 430.0 * (CNT[I0] / 700.0) - 26), "620",
               font=F_VAL, anchor="ms", fill=(*WHITE, int(230 * va)))
        d.text((day_x(I1), AX_Y - 430.0 * (CNT[I1] / 700.0) - 26), "414",
               font=F_VAL, anchor="ms", fill=(*WHITE, int(230 * va)))

    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    c.alpha_composite(layer)

    ca = studio.ease_out_cubic(studio.clamp(studio.prog(t, 8.0, 1.0)))
    if ca > 0.01:
        ImageDraw.Draw(c).text((W / 2, 990), "价格止跌，供给继续退。", font=F_CAP,
                               anchor="ms", fill=(*WHITE, int(245 * ca)))
    # 结尾淡出，交给下一段
    fo = 1.0 - studio.ease_in_out(studio.clamp(studio.prog(t, DUR - 0.6, 0.6)))
    if fo < 0.999:
        c.putalpha(ImageChops.multiply(c.getchannel("A"),
                                       Image.new("L", (W, H), int(255 * fo))))
    return c


OUT = HERE / "out" / "summary_alpha.mov"


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
