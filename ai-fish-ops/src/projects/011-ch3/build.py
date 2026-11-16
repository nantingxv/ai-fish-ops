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
DUR = 21.0
WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#C9D1DC")
DIM = studio.hex2rgb("#7C8798")
YELLOW = studio.hex2rgb("#FFC53D")
F_TITLE = studio.font(52, "bold")
F_VAL = studio.font(44, "bold")
F_TICK = studio.font(26)
F_CAP = studio.font(52, "bold")
F_BODY = studio.font(34)
EXPORT = Path(r"D:/tmp/export")
DROP = {"暮之鸣", "一支小馋猫", "lmlmlmlmzh"}
D0 = datetime.fromisoformat("2026-10-08T00:00:00+08:00")


def load():
    med = {}
    with open(EXPORT / "account.csv", encoding="utf-8") as f:
        for a in csv.DictReader(f):
            if a["account_name"] in DROP:
                continue
            d = a["first_pub_time"][:10]
            if d < "2026-10-08":
                continue
            t = datetime.fromisoformat(d + "T00:00:00+08:00")
            k = (t - D0).days // 5
            v = float(a["total_view"] or 0) / max(1, int(a["video_count"] or 1))
            med.setdefault(k, []).append(v)
    out = []
    for k in sorted(med):
        if len(med[k]) < 10:
            continue
        out.append((k, len(med[k]), float(np.median(med[k]))))
    return out


COH = load()

def frame_at(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)

    ta = studio.ease_out_cubic(studio.clamp(studio.prog(t, 0.1, 0.6)))
    if ta > 0.01:
        d.text((W / 2, 150), "入场即出局", font=F_TITLE, anchor="ms", fill=(*WHITE, int(240 * ta)))
        d.text((W / 2, 200), "按开号时间分组，每条视频的中位播放", font=F_BODY, anchor="ms",
               fill=(*DIM, int(205 * ta)))

    n = len(COH)
    x0, x1 = 380, 1540
    step = (x1 - x0) / max(1, n - 1)
    base = 820
    mx = max(v for _, _, v in COH)
    for i, (k, cnt, med) in enumerate(COH):
        e = studio.ease_out_cubic(studio.clamp(studio.prog(t, 1.1 + i * 0.18, 0.6)))
        if e <= 0.01:
            continue
        h = 430.0 * (med / mx) * e
        x = x0 + i * step
        d.rectangle([x - 34, base - h, x + 34, base], fill=(*YELLOW, 235))
        d.text((x, base - h - 24), "%d" % round(med), font=F_VAL, anchor="ms",
               fill=(*WHITE, int(235 * e)))
        dd = D0 + timedelta(days=k * 5)
        d.text((x, base + 46), dd.strftime("%m/%d"), font=F_TICK, anchor="ms",
               fill=(*DIM, int(200 * e)))
    d.line([(x0 - 80, base), (x1 + 80, base)], fill=(*DIM, int(140 * ta)), width=2)

    ca = studio.ease_out_cubic(studio.clamp(studio.prog(t, 14.0, 0.9)))
    if ca > 0.01:
        d.text((W / 2, 960), "入场券的保质期，只有 7 天", font=F_CAP, anchor="ms",
               fill=(*WHITE, int(245 * ca)))

    fi = studio.ease_in_out(studio.clamp(studio.prog(t, 0.0, 0.6)))
    fo = 1.0 - studio.ease_in_out(studio.clamp(studio.prog(t, DUR - 0.6, 0.6)))
    m = min(fi, fo)
    if m < 0.999:
        c.putalpha(ImageChops.multiply(c.getchannel("A"), Image.new("L", (W, H), int(255 * m))))
    return c


OUT = HERE / "out" / "ch3_alpha.mov"


def main():
    n = int(DUR * FPS)
    print("%d 帧 -> %s" % (n, OUT))
    print("队列", [(k, c, round(v)) for k, c, v in COH])
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
