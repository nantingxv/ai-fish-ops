# -*- coding: utf-8 -*-
r"""003-notice —— 观前提醒（居中）。

放在片头之后、正文之前。风格和正文一致，只是整段居中。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import studio  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

W, H, FPS = 1920, 1080, 30
DUR = 8.2

F_HEAD = studio.font(58, "bold")
F_BODY = studio.font(52, "regular")

WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#AEB8C6")

LINES = [
    "本片统计的账号均为人工手动录入，完整名单见简介。",
    "受录入方式限制，名单存在缺漏，数据整体偏低，",
    "仅用于相对比较。",
    "数据截止于 11 月 11 日，也就是一周前。",
]
HEAD_Y = 392
LINE_Y = 486
LINE_GAP = 76
HILITE = 3

OUT = HERE / "out" / "notice_alpha.mov"


def frame_at(t: float) -> Image.Image:
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    a = min(studio.ease_out_cubic(studio.prog(t, 0.10, 0.55)),
            1 - studio.ease_in_out(studio.prog(t, DUR - 0.75, 0.55)))
    if a <= 0.004:
        return c
    dy = (1 - studio.ease_out_cubic(studio.prog(t, 0.10, 0.55))) * 24

    head = "观前提醒"
    w = F_HEAD.getlength(head)
    d.text(((W - w) / 2, HEAD_Y + dy), head, font=F_HEAD, anchor="ls",
           fill=(*WHITE, int(255 * a)))
    # 标题下方短横线
    la = a * 0.5
    d.rectangle([(W - w) / 2, HEAD_Y + 26 + dy, (W + w) / 2, HEAD_Y + 28 + dy],
                fill=(*WHITE, int(255 * la)))

    YELLOW = studio.hex2rgb("#FFC53D")
    for i, line in enumerate(LINES):
        a_i = studio.clamp(a * (1.0 if i == 0 else 0.95))
        # 最后一行（数据截止）单独晚一点出现，并高亮
        if i == HILITE:
            a_i *= studio.ease_out_cubic(studio.clamp(studio.prog(t, 1.6, 0.6)))
            if a_i <= 0.004:
                continue
            col = YELLOW
        else:
            col = GREY
        lw = F_BODY.getlength(line)
        d.text(((W - lw) / 2, LINE_Y + i * LINE_GAP + dy), line, font=F_BODY, anchor="ls",
               fill=(*col, int(255 * a_i)))
    return c


def main():
    n = int(DUR * FPS)
    print(f"{n} 帧 -> {OUT}")
    vcodec = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
              "-vendor", "apl0", "-qscale:v", "12"]
    with studio.VideoWriter(OUT, (W, H), fps=FPS, in_fmt="rgba", vcodec=vcodec) as w:
        for f in range(n):
            w.write(frame_at(f / FPS))
    print("done:", OUT, round(OUT.stat().st_size / 1048576, 1), "MB")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--frame":
        t = float(sys.argv[2])
        dst = sys.argv[3] if len(sys.argv) > 3 else str(HERE / "out" / f"frame_{t}.png")
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        frame_at(t).save(dst)
        print("saved", dst)
    else:
        main()
