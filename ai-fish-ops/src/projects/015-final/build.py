# -*- coding: utf-8 -*-
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
sys.path.insert(0, str(HERE.parent.parent / "libs"))
import studio
from PIL import Image, ImageChops, ImageDraw

W, H, FPS = 1920, 1080, 30
DUR = 32.4
WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#C9D1DC")
DIM = studio.hex2rgb("#7C8798")
YELLOW = studio.hex2rgb("#FFC53D")
F_WORD = studio.font(72, "bold")
F_LINE = studio.font(44)
F_BIG = studio.font(54, "bold")
F_TICK = studio.font(26)
WORDS = ["供给衰退", "分配极端", "退出加速"]



def fade(t, a, b):
    return studio.ease_in_out(studio.clamp(studio.prog(t, a, b - a)))


def ctext(d, y, txt, font, col, a, dim=1.0, rise=18):
    """居中 + 上浮淡入"""
    if a <= 0.01:
        return
    d.text((W / 2, y + (1 - a) * rise), txt, font=font, anchor="ms",
           fill=(col[0], col[1], col[2], int(255 * a * dim)))


def frame_at(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)

    # 1) 三个特征：居中一行，逐个出现
    a_any = fade(t, 1.1, 1.7)
    if a_any > 0.01:
        dim = 1.0 - 0.45 * fade(t, 8.4, 9.0)
        # 用墨迹宽度（bbox）而不是 advance 宽度来排版，保证左右对称
        def ink(txt):
            b = d.textbbox((0, 0), txt, font=F_WORD)
            return b[0], b[2] - b[0]

        wid = [ink(w)[1] for w in WORDS]
        off = [ink(w)[0] for w in WORDS]
        dot_off, dot_w = ink("·")
        gap = 64
        sep = 2 * gap + dot_w            # 两个间隔词之间：空 + 点 + 空
        total = sum(wid) + 2 * sep
        x = (W - total) / 2
        for i, w in enumerate(WORDS):
            a = fade(t, 1.1 + i * 0.45, 1.7 + i * 0.45)
            if a > 0.01:
                d.text((x - off[i], 288 + (1 - a) * 16), w, font=F_WORD, anchor="ls",
                       fill=(*WHITE, int(245 * a * dim)))
            x += wid[i]
            if i < 2:
                ad = fade(t, 1.35 + i * 0.45, 1.95 + i * 0.45)
                if ad > 0.01:
                    d.text((x + gap - dot_off, 288), "·", font=F_WORD, anchor="ls",
                           fill=(*YELLOW, int(220 * ad * dim)))
                x += sep

    # 2) 两句判断
    det = 1.0 - 0.4 * fade(t, 16.6, 17.2)
    ctext(d, 392, "它不会崩，因为它本来就不靠内容赚钱", F_LINE, GREY, fade(t, 8.9, 9.5), det)
    ctext(d, 450, "它也不会变大，因为注意力没有增加", F_LINE, GREY, fade(t, 9.9, 10.5), det)

    # 3) 信任
    ctext(d, 548, "真正被消耗的，是观众的信任", studio.font(50, "bold"), WHITE, fade(t, 17.0, 17.7))
    ctext(d, 606, "当模板化的内容铺满推荐位，愿意认真做的人会先离开", F_LINE, GREY, fade(t, 18.3, 18.9))

    # 4) 收尾
    ctext(d, 712, "想让 agent 自力更生，这条路在算术上就不成立", F_BIG, YELLOW, fade(t, 25.1, 25.8))

    # 5) 数据卡
    a7 = fade(t, 29.6, 30.4)
    if a7 > 0.01:
        d.text((W / 2, 820), "数据截至 2026 年 11 月 11 日 · 839 个账号 · 10664 条视频",
               font=studio.font(30), anchor="ms", fill=(*DIM, int(200 * a7)))

    fi = studio.ease_in_out(studio.clamp(studio.prog(t, 0.0, 0.6)))
    fo = 1.0 - studio.ease_in_out(studio.clamp(studio.prog(t, DUR - 1.2, 1.2)))
    m = min(fi, fo)
    if m < 0.999:
        c.putalpha(ImageChops.multiply(c.getchannel("A"), Image.new("L", (W, H), int(255 * m))))
    return c

OUT = HERE / "out" / "final_alpha.mov"


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