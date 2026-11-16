# -*- coding: utf-8 -*-
r"""004-jump —— S3 + S4：井喷期到白热化。

左上角日期戳是「阶段时钟」，独立于正文，到点直接切换：
    10月18日 --(S3 开始)--> 10月20日 --(S4 开始)--> 10月25日

正文里的「10月25日」是另一回事：S3 退场时它留在原地，
挪到 S4 第一行的行首，变成下一句的开头。

S4 两段不再"前一段退场后一段进场"，第二段只是晚一点出现，第一段留在屏幕上。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import studio  # noqa: E402
import roll  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

W, H, FPS = 1920, 1080, 30
DUR = 15.6

X = 150
CORNER_Y = 118
F_BODY = studio.font(60, "regular")
F_BOLD = studio.font(60, "bold")
F_STAMP = studio.font(44, "bold")

WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#C9D1DC")
YELLOW = studio.hex2rgb("#FFC53D")

# 正文坐标
S3_Y0 = 300                     # 三行：300 / 392 / 484（下面留图表）
CH_Y, CH_W, CH_H = 600, 1060, 280
CH_X = (W - CH_W) // 2          # 图表独立水平居中
S4A_Y1, S4A_Y2 = 420, 512
S4B_Y1, S4B_Y2 = 640, 732

# 时间
SW1_T0 = 0.10                   # 角标 10月18日 -> 10月20日
SW_DUR = 0.28
S3_IN, S3_OUT = 0.35, 6.45
FLY_T0, DATE_LAND = 6.55, 7.15
SW2_T0 = 7.05                   # 角标 10月20日 -> 10月25日
S4A_IN = 7.30
S4B_IN = 9.80
S4B_OUT = 15.00

# 图表数据（井喷期 10/20-10/25）
DAYS = ["10/20", "10/21", "10/22", "10/23", "10/24", "10/25"]
NEW = [31, 37, 33, 50, 79, 109]
PLAYS = [490.3, 292.4, 263.7, 369.9, 179.1, 329.8]   # 万
BAR_C = studio.hex2rgb("#FFC53D")
LINE_C = studio.hex2rgb("#7FB2E5")
F_TICK = studio.font(22)
F_VAL = studio.font(21, "bold")
F_LEG = studio.font(22)

OUT = HERE / "out" / "jump_alpha.mov"

S3 = [
    [("10月20日，单日新增账号 ", F_BODY, GREY), ("31", F_BOLD, YELLOW), (" 个，", F_BODY, GREY)],
    [("到 ", F_BODY, GREY), ("10月25日", F_BODY, WHITE),
     ("，单日新增账号达 ", F_BODY, GREY), ("109", F_BOLD, YELLOW), (" 个，", F_BODY, GREY)],
    [("历经 ", F_BODY, GREY), ("6", F_BOLD, YELLOW), (" 天，单日新增账号数量翻三倍不止", F_BODY, GREY)],
]
S4A_REST = ("，军备竞赛进入白热化阶段，", F_BODY, GREY)
S4A_L2 = [("单日发布视频达 ", F_BODY, GREY), ("505", F_BOLD, YELLOW), (" 条，", F_BODY, GREY),
          ("相比 ", F_BODY, GREY), ("6", F_BOLD, YELLOW), (" 天前翻 ", F_BODY, GREY),
          ("6.7", F_BOLD, YELLOW), (" 倍", F_BODY, GREY)]
S4B = [
    [("需要注意的是，10月25日的总播放 ", F_BODY, GREY), ("330", F_BOLD, YELLOW), (" 万", F_BODY, GREY)],
    [("低于 10月20日的 ", F_BODY, GREY), ("490", F_BOLD, YELLOW),
     (" 万，观众已出现审美疲劳。", F_BODY, GREY)],
]


def ease(t, t0, dur):
    return studio.ease_in_out(studio.prog(t, t0, dur))


def draw_line(c, x, y, items, a, dy=0.0, skip=None):
    xs = []
    for i, (text, font, color) in enumerate(items):
        xs.append(x)
        if skip is not None and i == skip:
            x += font.getlength(text)
            continue
        if a > 0.004:
            ImageDraw.Draw(c).text((x, y + dy), text, font=font, anchor="ls",
                                   fill=(color[0], color[1], color[2], int(255 * studio.clamp(a))))
        x += font.getlength(text)
    return xs


PREFIX = "10月"
D18, D20, D25 = "18日", "20日", "25日"


def draw_corner(c, t):
    """10月 固定不动，日号上下滚动。"""
    d = ImageDraw.Draw(c)
    d.text((X, CORNER_Y), PREFIX, font=F_STAMP, anchor="ls", fill=(*WHITE, 255))
    slot = X + F_STAMP.getlength(PREFIX)
    p1, p2 = ease(t, SW1_T0, SW_DUR), ease(t, SW2_T0, SW_DUR)

    if p2 > 0.001:
        roll.roll_text(c, slot, CORNER_Y, D20, D25, p2, F_STAMP, WHITE)
    elif p1 > 0.001:
        roll.roll_text(c, slot, CORNER_Y, D18, D20, p1, F_STAMP, WHITE)
    else:
        d.text((slot, CORNER_Y), D18, font=F_STAMP, anchor="ls", fill=(*WHITE, 255))

    w_day = (F_STAMP.getlength(D18) * (1 - p1) + F_STAMP.getlength(D20) * (p1 - p2)
             + F_STAMP.getlength(D25) * p2)
    w = F_STAMP.getlength(PREFIX) + max(0.0, w_day)
    if w > 4:
        d.rectangle([X, CORNER_Y + 16, X + w, CORNER_Y + 18], fill=(*WHITE, 140))


def draw_chart(c, t, alpha):
    """柱：新增账号；线：当日播放。两个量纲各自缩放，只标首末。"""
    if alpha <= 0.004:
        return
    d = ImageDraw.Draw(c)
    base = CH_Y + CH_H
    step = CH_W / len(DAYS)
    maxv, maxp = 120.0, 520.0
    a = int(255 * alpha)

    # 图例
    d.rectangle([CH_X, CH_Y - 52, CH_X + 14, CH_Y - 38], fill=(*BAR_C, a))
    d.text((CH_X + 22, CH_Y - 34), "新增账号", font=F_LEG, anchor="ls",
           fill=(*GREY, int(190 * alpha)))
    d.line([(CH_X + 150, CH_Y - 45), (CH_X + 178, CH_Y - 45)],
           fill=(*LINE_C, a), width=3)
    d.text((CH_X + 186, CH_Y - 34), "当日播放（万）", font=F_LEG, anchor="ls",
           fill=(*GREY, int(190 * alpha)))

    # 基线
    d.rectangle([CH_X, base, CH_X + CH_W, base + 1], fill=(*GREY, int(70 * alpha)))

    # 柱
    bw = step * 0.42
    for i, v in enumerate(NEW):
        e = studio.ease_out_cubic(studio.prog(t, 1.20 + i * 0.09, 0.55))
        if e <= 0.001:
            continue
        h = CH_H * (v / maxv) * e
        x = CH_X + i * step + (step - bw) / 2
        d.rounded_rectangle([x, base - h, x + bw, base], radius=4, fill=(*BAR_C, a))
        if e > 0.96:
            d.text((x + bw / 2, base - h - 12), str(v), font=F_VAL, anchor="ms",
                   fill=(*WHITE, int(235 * alpha)))

    # 折线
    p = studio.ease_in_out(studio.prog(t, 2.95, 1.05))
    if p > 0:
        pts = [(CH_X + i * step + step / 2, base - CH_H * (v / maxp) * 0.92)
               for i, v in enumerate(PLAYS)]
        seg = p * (len(pts) - 1)
        k = int(seg)
        frac = seg - k
        line_pts = pts[:k + 1]
        if k < len(pts) - 1:
            x0, y0 = pts[k]
            x1, y1 = pts[k + 1]
            line_pts.append((x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac))
        if len(line_pts) >= 2:
            d.line(line_pts, fill=(*LINE_C, a), width=4, joint="curve")
        for (x, y) in pts[:k + 1]:
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(*LINE_C, a))
        if p > 0.97:
            for (x, y), txt in ((pts[0], "490"), (pts[-1], "330")):
                tw = F_VAL.getlength(txt)
                d.rounded_rectangle([x - tw / 2 - 8, y - 24 - 18, x + tw / 2 + 8, y - 24 + 8],
                                    radius=6, fill=(11, 11, 13, int(215 * alpha)))
                d.text((x, y - 24), txt, font=F_VAL, anchor="ms",
                       fill=(*LINE_C, int(245 * alpha)))

    for i, lab in enumerate(DAYS):
        x = CH_X + i * step + step / 2
        d.text((x, base + 34), lab, font=F_TICK, anchor="ms",
               fill=(*GREY, int(150 * alpha)))


def line_width(items):
    return sum(font.getlength(text) for text, font, _ in items)


def block_x(lines, left=150, right=1770):
    w = max(line_width(items) for items in lines)
    return left + (right - left - w) / 2


S3_X = block_x(S3)
S4A_X = None      # 由 S4 四行统一算，见下
S4_ALL = [S4A_L2, S4B[0], S4B[1]]
S4_BLOCK_X = None


def init_layout():
    global S4_BLOCK_X
    # S4 第一行 = 日期 + 后续文字，宽度要一起算
    l1 = [("10月25日", F_BODY, WHITE), S4A_REST]
    S4_BLOCK_X = block_x([l1, S4A_L2, S4B[0], S4B[1]])


init_layout()


def frame_at(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_corner(c, t)

    # ---------- S3
    s3_alpha = min(studio.ease_out_cubic(studio.prog(t, S3_IN, 0.55)), 1 - ease(t, S3_OUT, 0.35))
    date_x = S3_X + F_BODY.getlength("到 ")
    if s3_alpha > 0.004:
        dy = (1 - studio.ease_out_cubic(studio.prog(t, S3_IN, 0.55))) * 24
        detached = t >= FLY_T0
        draw_line(c, S3_X, S3_Y0, S3[0], s3_alpha, dy)
        draw_line(c, S3_X, S3_Y0 + 92, S3[1], s3_alpha, dy, skip=1 if detached else None)
        draw_line(c, S3_X, S3_Y0 + 184, S3[2], s3_alpha, dy)
        draw_chart(c, t, s3_alpha)

    # ---------- 正文里的「10月25日」：从 S3 第二行挪到 S4 第一行行首
    d = ImageDraw.Draw(c)
    if t >= FLY_T0:
        if t < DATE_LAND:
            f = ease(t, FLY_T0, DATE_LAND - FLY_T0)
            dx = studio.lerp(date_x, S4_BLOCK_X, f)
            dyy = studio.lerp(S3_Y0 + 92, S4A_Y1, f)
        else:
            dx, dyy = S4_BLOCK_X, S4A_Y1
        # 跟着 S4 两段一起退场，避免只有它留在画面上
        fade = 1.0 - ease(t, S4B_OUT, 0.45) if t >= DATE_LAND else 1.0
        d.text((dx, dyy), "10月25日", font=F_BODY, anchor="ls",
               fill=(*WHITE, int(255 * studio.clamp(fade))))

    # ---------- S4 前半（第二段晚到；两段一起退场，避免一淡一切）
    if S4A_IN <= t <= S4B_OUT + 0.45:
        a = min(studio.ease_out_cubic(studio.prog(t, S4A_IN, 0.5)),
                1 - ease(t, S4B_OUT, 0.45))
        dy = (1 - studio.ease_out_cubic(studio.prog(t, S4A_IN, 0.5))) * 20
        x_rest = S4_BLOCK_X + F_BODY.getlength("10月25日")
        draw_line(c, x_rest, S4A_Y1, [S4A_REST], a, dy)
        draw_line(c, S4_BLOCK_X, S4A_Y2, S4A_L2, a, dy)

    # ---------- S4 后半
    if S4B_IN <= t <= S4B_OUT + 0.5:
        a = min(studio.ease_out_cubic(studio.prog(t, S4B_IN, 0.5)), 1 - ease(t, S4B_OUT, 0.45))
        dy = (1 - studio.ease_out_cubic(studio.prog(t, S4B_IN, 0.5))) * 20
        draw_line(c, S4_BLOCK_X, S4B_Y1, S4B[0], a, dy)
        draw_line(c, S4_BLOCK_X, S4B_Y2, S4B[1], a, dy)
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
