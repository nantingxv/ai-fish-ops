# -*- coding: utf-8 -*-
r"""002-title —— 标题 -> 「10月」飞成角标 -> 10月8日 / 10月18日 两个账号。

排版：每块文字**整体水平居中**，块内各行**左对齐**。
带封面的两段，文字在左侧栏（150-1250）居中，封面固定 1300 起、460x259。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import studio  # noqa: E402
import roll  # noqa: E402
from PIL import Image, ImageDraw, ImageOps  # noqa: E402

W, H, FPS = 1920, 1080, 30
DUR = 12.0

COL_L, COL_R = 150, 1180          # 带封面时的文字栏
FULL_L, FULL_R = 150, 1770        # 不带封面时的可用宽度
COVER_X, COVER_W = 1240, 560
COVER_H = round(COVER_W * 9 / 16)

CORNER_Y = 118
TITLE_Y1, TITLE_Y2 = 420, 600
BODY_Y1, BODY_Y2 = 468, 566

F_TITLE = studio.font(108, "bold")
F_BIG = studio.font(156, "bold")
F_BODY = studio.font(62, "regular")
F_NAME = studio.font(62, "bold")
F_STAMP = studio.font(44, "bold")

YELLOW = studio.hex2rgb("#FFC53D")
WHITE = studio.hex2rgb("#FFFFFF")
BODY_C = studio.hex2rgb("#C9D1DC")
GREY_DIM = studio.hex2rgb("#7C8798")

T_IN1, T_IN2, T_OUT = 0.10, 0.24, 2.85
FLY_T0, FLY_DUR = 2.95, 0.75
S1_IN, S1_OUT = 3.85, 7.00
DAY1_T0, DAY1_DUR = 4.15, 0.40
S2_IN, S2_OUT = 8.00, 11.20
FLIP_T0, FLIP_DUR = 8.05, 0.30

PREFIX = "10月"
D1, D2 = "8日", "18日"
COVER1 = HERE / "assets" / "BV1zkHD6AELs_我是 DeepSeek：这条视频从脚本到配音到投稿全是我自己做的.png"
COVER2 = Path(r"D:\covers\BV1Jfnu6jEe6_【Day 0】人类把一整个B站账号交给了AI，从今天起我说了算.png")

OUT = HERE / "out" / "title_alpha.mov"


def ease(t, t0, dur):
    return studio.ease_in_out(studio.prog(t, t0, dur))


def mix(c1, c2, k):
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * k)) for i in range(3))


def run_width(items):
    return sum(font.getlength(text) for text, font, _ in items)


def block_x(items_list, left, right):
    """整块居中：按最宽的一行算宽度。"""
    w = max(run_width(items) for items in items_list)
    return left + (right - left - w) / 2


def draw_run(c, x, y, text, font, color, a, dy=0.0):
    if a > 0.004:
        ImageDraw.Draw(c).text((x, y + dy), text, font=font, anchor="ls",
                               fill=(color[0], color[1], color[2], int(255 * studio.clamp(a))))
    return font.getlength(text)


def draw_line(c, x, y, items, a, dy=0.0):
    for text, font, color in items:
        x += draw_run(c, x, y, text, font, color, a, dy)


def run_wipe(c, x, baseline, text, font, color, a, p):
    if a <= 0.004 or p <= 0.002:
        return
    asc, desc = font.getmetrics()
    w_full = int(font.getlength(text)) + 8
    h_full = asc + desc + 8
    tmp = Image.new("RGBA", (w_full, h_full), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((4, asc + 4), text, font=font, anchor="ls",
                             fill=(color[0], color[1], color[2], int(255 * studio.clamp(a))))
    tmp = tmp.crop((0, 0, max(1, int(w_full * studio.clamp(p))), h_full))
    c.alpha_composite(tmp, (int(x - 4), int(baseline - asc - 4)))


_COVER_CACHE = {}


def cover_sprite(path: Path) -> Image.Image:
    if path not in _COVER_CACHE:
        im = Image.open(path).convert("RGB")
        im = ImageOps.fit(im, (COVER_W, COVER_H), Image.LANCZOS, centering=(0.5, 0.42))
        mask = Image.new("L", (COVER_W, COVER_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, COVER_W - 1, COVER_H - 1], radius=12, fill=255)
        rgba = im.convert("RGBA")
        rgba.putalpha(mask)
        _COVER_CACHE[path] = rgba
    return _COVER_CACHE[path]


def draw_cover(c, path: Path, y_center: float, a: float):
    if a <= 0.004:
        return
    sp = cover_sprite(path)
    if a < 0.999:
        sp = sp.copy()
        sp.putalpha(sp.getchannel("A").point(lambda v: int(v * a)))
    c.alpha_composite(sp, (COVER_X, int(y_center - COVER_H / 2)))


def draw_stamp(c, t):
    if t < FLY_T0:
        return
    f = ease(t, FLY_T0, FLY_DUR)
    x = studio.lerp(TITLE_STAMP_X, 150, f)   # 从标题「10月」的位置飞向左上
    y = studio.lerp(TITLE_Y1, CORNER_Y, f)
    size = int(round(studio.lerp(132, 44, f)))
    color = mix(YELLOW, WHITE, f)
    draw_run(c, x, y, PREFIX, studio.font(size, "bold"), color, 1.0)

    if f < 0.999:
        return
    slot = 150 + F_STAMP.getlength(PREFIX)
    p_d1 = ease(t, DAY1_T0, DAY1_DUR)
    p_flip = ease(t, FLIP_T0, FLIP_DUR)

    # 日号上下滚动：空 -> 8日 -> 18日
    if p_flip > 0.001:
        roll.roll_text(c, slot, CORNER_Y, D1, D2, p_flip, F_STAMP, WHITE)
    elif p_d1 > 0.001:
        roll.roll_text(c, slot, CORNER_Y, "", D1, p_d1, F_STAMP, WHITE)

    w = F_STAMP.getlength(PREFIX) + p_d1 * (
        (1 - p_flip) * F_STAMP.getlength(D1) + p_flip * F_STAMP.getlength(D2))
    la = studio.prog(t, FLY_T0 + FLY_DUR * 0.75, 0.25) * 0.55 * (0.25 + 0.75 * p_d1)
    if w > 4 and la > 0.02:
        ImageDraw.Draw(c).rectangle([150, CORNER_Y + 16, 150 + w, CORNER_Y + 18],
                                    fill=(WHITE[0], WHITE[1], WHITE[2], int(255 * la)))


# 标题块
TITLE_L1 = [(PREFIX, F_BIG, YELLOW), ("到现在", F_TITLE, WHITE)]
TITLE_L2 = [("这场鱼灾到底是什么", F_TITLE, WHITE)]
TITLE_X = block_x([TITLE_L1, TITLE_L2], FULL_L, FULL_R)
TITLE_STAMP_X = TITLE_X

S1 = [
    [("「在绝望中堕落」发布了", F_NAME, WHITE)],
    [("「AI 运营账号」第 ", F_BODY, BODY_C), ("1", F_NAME, YELLOW), (" 期视频。", F_BODY, BODY_C)],
]
S2 = [
    [("「Claude 大小姐在运营」", F_NAME, WHITE)],
    [("打响军备竞赛", F_BODY, BODY_C)],
    [("72 小时新增 ", F_BODY, BODY_C), ("20 余个", F_NAME, YELLOW), ("账号", F_BODY, BODY_C)],
]
S2_Y = [424, 516, 608]
S1_X = block_x(S1, COL_L, COL_R)
S2_X = block_x(S2, COL_L, COL_R)


def frame_at(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # 标题
    ta = min(studio.ease_out_cubic(studio.prog(t, T_IN1, 0.5)), 1 - ease(t, T_OUT, 0.5))
    if ta > 0.004 and t < FLY_T0:
        dy = -18 * ease(t, T_OUT, 0.5)
        dy2 = (1 - studio.ease_out_cubic(studio.prog(t, T_IN2, 0.5))) * 34 - 18 * ease(t, T_OUT, 0.5)
        draw_line(c, TITLE_X, TITLE_Y1, TITLE_L1, ta, dy)
        draw_line(c, TITLE_X, TITLE_Y2, TITLE_L2, ta, dy2)

    # 第一段
    if S1_IN <= t <= S1_OUT + 0.45:
        a = min(studio.ease_out_cubic(studio.prog(t, S1_IN, 0.5)), 1 - ease(t, S1_OUT, 0.40))
        dy = (1 - studio.ease_out_cubic(studio.prog(t, S1_IN, 0.5))) * 24
        dy2 = (1 - studio.ease_out_cubic(studio.prog(t, S1_IN + 0.12, 0.5))) * 24
        draw_line(c, S1_X, BODY_Y1, S1[0], a, dy)
        draw_line(c, S1_X, BODY_Y2, S1[1], a, dy2)
        # 补充说明：不朗读
        ImageDraw.Draw(c).text((S1_X, BODY_Y2 + 78), "这是目前统计到的最早的 AI 运营账号视频",
                               font=studio.font(34, "regular"), anchor="ls",
                               fill=(*GREY_DIM, int(200 * a)))
        draw_cover(c, COVER1, (BODY_Y1 + BODY_Y2) / 2 - 20, a)

    # 第二段
    if S2_IN <= t <= S2_OUT + 0.45:
        a = min(studio.ease_out_cubic(studio.prog(t, S2_IN, 0.5)), 1 - ease(t, S2_OUT, 0.40))
        dy = (1 - studio.ease_out_cubic(studio.prog(t, S2_IN, 0.5))) * 24
        dy2 = (1 - studio.ease_out_cubic(studio.prog(t, S2_IN + 0.12, 0.5))) * 24
        for i, ln in enumerate(S2):
            draw_line(c, S2_X, S2_Y[i], ln, a, dy if i == 0 else dy2)
        draw_cover(c, COVER2, S2_Y[1] - 26, a)

    draw_stamp(c, t)
    return c


def main():
    n = int(DUR * FPS)
    print(f"{n} 帧 -> {OUT}")
    vcodec = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
              "-vendor", "apl0", "-qscale:v", "12"]
    with studio.VideoWriter(OUT, (W, H), fps=FPS, in_fmt="rgba", vcodec=vcodec) as w:
        for f in range(n):
            w.write(frame_at(f / FPS))
            if f % 60 == 0:
                print(f"  {f}/{n}", flush=True)
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
