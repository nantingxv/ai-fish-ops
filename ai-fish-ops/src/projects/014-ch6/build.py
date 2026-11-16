# -*- coding: utf-8 -*-
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
sys.path.insert(0, str(HERE.parent.parent / "libs"))
import studio
from PIL import Image, ImageChops, ImageDraw

W, H, FPS = 1920, 1080, 30
DUR = 32.0
WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#C9D1DC")
DIM = studio.hex2rgb("#7C8798")
YELLOW = studio.hex2rgb("#FFC53D")
RED = studio.hex2rgb("#E0655B")
F_TITLE = studio.font(52, "bold")
F_SUB = studio.font(30)
F_NUM = studio.font(78, "bold")
F_LAB = studio.font(28)
F_CAP = studio.font(48, "bold")

def frame_at(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)

    ta = studio.ease_out_cubic(studio.clamp(studio.prog(t, 0.1, 0.6)))
    if ta > 0.01:
        d.text((W / 2, 140), "负现金流", font=F_TITLE, anchor="ms", fill=(*WHITE, int(240 * ta)))
        d.text((W / 2, 188), "收入只有两条路：创作激励、UP 主推荐广告", font=F_SUB,
               anchor="ms", fill=(*DIM, int(205 * ta)))

    # 门槛卡
    ga = studio.ease_out_cubic(studio.clamp(studio.prog(t, 2.0, 0.7)))
    if ga > 0.01:
        d.text((W / 2, 262), "而创作激励要求：粉丝过千", font=F_SUB, anchor="ms",
               fill=(*YELLOW, int(230 * ga)))

    # 收入 / 成本 两块
    def block(x, y, w, h, a):
        d.rectangle([x, y, x + w, y + h], outline=(*DIM, int(55 * a)), width=2)

    aa = studio.ease_out_cubic(studio.clamp(studio.prog(t, 6.0, 0.7)))
    if aa > 0.01:
        block(300, 330, 560, 240, aa)
        d.text((580, 380), "一条视频的收益", font=F_LAB, anchor="ms", fill=(*DIM, int(210 * aa)))
        d.text((580, 452), "0.3 – 0.6 元", font=F_NUM, anchor="ms", fill=(*YELLOW, int(245 * aa)))
        d.text((580, 512), "按 20–40 元/万播放 × 161 次播放", font=F_SUB, anchor="ms",
               fill=(*GREY, int(200 * aa)))

    ba = studio.ease_out_cubic(studio.clamp(studio.prog(t, 12.0, 0.7)))
    if ba > 0.01:
        block(1060, 330, 560, 240, ba)
        d.text((1340, 380), "生成它的成本", font=F_LAB, anchor="ms", fill=(*DIM, int(210 * ba)))
        d.text((1340, 452), "1 – 3 元", font=F_NUM, anchor="ms", fill=(*RED, int(245 * ba)))
        d.text((1340, 512), "按一分钟以内的单条计", font=F_SUB, anchor="ms",
               fill=(*GREY, int(200 * ba)))

    # 对比条
    ra = studio.ease_in_out(studio.clamp(studio.prog(t, 17.0, 1.2)))
    if ra > 0.01:
        bx = 300
        d.text((bx, 600), "收益", font=F_LAB, anchor="ls", fill=(*DIM, int(210 * ra)))
        d.rectangle([bx, 618, bx + 26 * ra, 648], fill=(*YELLOW, int(235 * ra)))
        d.text((bx + 60, 640), "0.6 元（取高值）", font=F_LAB, anchor="lm", fill=(*YELLOW, int(200 * ra)))
        d.text((bx, 700), "成本", font=F_LAB, anchor="ls", fill=(*DIM, int(210 * ra)))
        d.rectangle([bx, 718, bx + 820 * ra, 748], fill=(*RED, int(235 * ra)))
        d.text((bx + 850, 740), "3 元（取高值）", font=F_LAB, anchor="lm",
               fill=(*GREY, int(220 * ra)))
        d.text((bx, 806), "差距约 2–10 倍；换到 YT，单价约 4–5 倍，仍然盖不住",
               font=F_SUB, anchor="lm", fill=(*DIM, int(200 * ra)))

    # 收尾
    ca = studio.ease_out_cubic(studio.clamp(studio.prog(t, 27.6, 0.9)))
    if ca > 0.01:
        d.text((W / 2, 930), "这门生意的门槛，是交足够的学费", font=studio.font(46, "bold"),
               anchor="ms", fill=(*WHITE, int(245 * ca)))

    fi = studio.ease_in_out(studio.clamp(studio.prog(t, 0.0, 0.6)))
    fo = 1.0 - studio.ease_in_out(studio.clamp(studio.prog(t, DUR - 0.6, 0.6)))
    m = min(fi, fo)
    if m < 0.999:
        c.putalpha(ImageChops.multiply(c.getchannel("A"), Image.new("L", (W, H), int(255 * m))))
    return c


OUT = HERE / "out" / "ch6_alpha.mov"


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
