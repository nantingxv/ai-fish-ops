# -*- coding: utf-8 -*-
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
sys.path.insert(0, str(HERE.parent.parent / "libs"))
import studio
from PIL import Image, ImageDraw

W, H, FPS = 1920, 1080, 30
DUR = 21.5
WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#C9D1DC")
DIM = studio.hex2rgb("#7C8798")
YELLOW = studio.hex2rgb("#FFC53D")
F_TITLE = studio.font(52, "bold")
F_BIG = studio.font(150, "bold")
F_ROW = studio.font(30, "bold")
F_BODY = studio.font(36)
F_CAP = studio.font(52, "bold")
F_TICK = studio.font(26)
EXPORT = Path(r"D:/tmp/export")
DROP = {"暮之鸣", "一支小馋猫", "lmlmlmlmzh"}


def load():
    seen, acc = set(), defaultdict(float)
    with open(EXPORT / "video.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["bvid"] in seen:
                continue
            seen.add(r["bvid"])
            if r["account_name"] in DROP:
                continue
            acc[(r["account_id"], r["account_name"])] += float(r["view"] or 0)
    top = sorted(acc.items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in top)
    vals = np.sort(np.array([v for _, v in top]))
    n = len(vals)
    gini = float((n + 1 - 2 * np.sum(np.cumsum(vals)) / vals.sum()) / n)
    top10 = sum(v for _, v in top[:10]) / total
    top1 = top[0][1] / total
    bottom90 = float(vals[: int(n * 0.9)].sum() / vals.sum())
    return top[:10], total, len(top), gini, top10, top1, bottom90


TOP, TOTAL, NACC, GINI, TOP10, TOP1, BOT90 = load()

def frame_at(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)

    # 标题
    ta = studio.ease_out_cubic(studio.clamp(studio.prog(t, 0.15, 0.7)))
    if ta > 0.01:
        d.text((W / 2, 150), "赢者通吃", font=F_TITLE, anchor="ms", fill=(*WHITE, int(240 * ta)))
        d.text((W / 2, 200), "%d 个账号 · 累计播放 %d 万" % (NACC, round(TOTAL / 1e4)),
               font=F_BODY, anchor="ms", fill=(*DIM, int(210 * ta)))

    # 前十名横条
    base_y = 268
    rowh = 50
    mx = TOP[0][1]
    for i, ((aid, name), val) in enumerate(TOP):
        ra = studio.ease_out_cubic(studio.clamp(studio.prog(t, 1.2 + i * 0.16, 0.6)))
        if ra <= 0.01:
            continue
        y = base_y + i * rowh
        wmax = 760
        w = wmax * (val / mx) * ra
        d.text((300, y + 14), "%d" % (i + 1), font=F_TICK, anchor="rm",
               fill=(*DIM, int(180 * ra)))
        nm = name if len(name) <= 12 else name[:12] + "…"
        d.text((320, y + 14), nm, font=F_ROW, anchor="lm",
               fill=(*WHITE, int(235 * ra)))
        d.rectangle([700, y + 2, 700 + w, y + 30],
                    fill=(*YELLOW, int((235 if i < 3 else 170) * ra)))
        d.text((700 + w + 16, y + 14), "%.1f%%" % (100 * val / TOTAL), font=F_ROW,
               anchor="lm", fill=(*GREY, int(225 * ra)))

    # 对比条：前 10 vs 其余
    ca = studio.ease_out_cubic(studio.clamp(studio.prog(t, 6.2, 1.0)))
    if ca > 0.01:
        y = 812
        W_total = 1160
        d.text((300, y - 32), "前 10 个账号", font=F_TICK, anchor="lm",
               fill=(*DIM, int(200 * ca)))
        d.rectangle([300, y, 300 + W_total * TOP10, y + 40], fill=(*YELLOW, int(235 * ca)))
        d.rectangle([300 + W_total * TOP10, y, 300 + W_total, y + 40],
                    fill=(*GREY, int(70 * ca)))
        d.text((300 + W_total * TOP10 / 2, y + 20), "%.1f%%" % (100 * TOP10), font=F_ROW,
               anchor="mm", fill=(17, 17, 19, int(245 * ca)))
        d.text((300 + W_total * (1 + TOP10) / 2, y + 20), "%.1f%%" % (100 * (1 - TOP10)),
               font=F_ROW, anchor="mm", fill=(*GREY, int(210 * ca)))
        d.text((300, y + 62), "其余 %d 个账号" % (NACC - 10), font=F_TICK, anchor="lm",
               fill=(*DIM, int(190 * ca)))

    # 收尾句
    fa = studio.ease_out_cubic(studio.clamp(studio.prog(t, 15.3, 0.9)))
    if fa > 0.01:
        d.text((W / 2, 972), "底部九成账号，加起来只分到 %.1f%%" % (100 * BOT90),
               font=F_CAP, anchor="ms", fill=(*WHITE, int(240 * fa)))
    # 进场淡入 / 退场淡出
    from PIL import ImageChops
    fi = studio.ease_in_out(studio.clamp(studio.prog(t, 0.0, 0.6)))
    fo = 1.0 - studio.ease_in_out(studio.clamp(studio.prog(t, DUR - 0.7, 0.7)))
    m = min(fi, fo)
    if m < 0.999:
        c.putalpha(ImageChops.multiply(c.getchannel("A"), Image.new("L", (W, H), int(255 * m))))
    return c


OUT = HERE / "out" / "ch2_alpha.mov"


def main():
    n = int(DUR * FPS)
    print("%d 帧 -> %s" % (n, OUT))
    print("账号", NACC, "总播放", int(TOTAL), "Gini", round(GINI, 3),
          "top10", round(TOP10, 3), "top1", round(TOP1, 3))
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
