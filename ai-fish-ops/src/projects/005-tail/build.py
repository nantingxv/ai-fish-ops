# -*- coding: utf-8 -*-
r"""005-tail —— 从 10月27日 到收尾。

四拍：
  A 10月27日：单日 609 条 / 活跃 413；但新开号 109 -> 55
  B 11月2日：新开号只剩 5 个（配 新开号 折线）
  C 11月5日：日更 413；发布 24h 中位 197 -> 134，只跌三成（配双线）
  D 收尾：19 天 707 个新号 / 7153 条视频；样本 779 / 9126

数据源：D:\tmp\每日汇总_1018-1105.xlsx（快照 20261110T080006）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import studio  # noqa: E402
import roll  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

W, H, FPS = 1920, 1080, 30
DUR = 30.5

X_CORNER, CORNER_Y = 150, 118
F_BODY = studio.font(60, "regular")
F_BOLD = studio.font(60, "bold")
F_BIG = studio.font(150, "bold")
F_STAMP = studio.font(44, "bold")
F_TICK = studio.font(22)
F_VAL = studio.font(21, "bold")
F_LEG = studio.font(22)

WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#C9D1DC")
YELLOW = studio.hex2rgb("#FFC53D")
BLUE = studio.hex2rgb("#7FB2E5")

# ---- 时间轴
A_IN, A_OUT = 0.35, 7.60
B_IN, B_OUT = 8.10, 13.20
C_IN, C_OUT = 13.70, 20.80
D_IN, D_OUT = 21.40, 28.40
DATES = [("10月27日", 0.0), ("11月2日", 6.00), ("11月5日", 11.60), ("", 18.60)]
SW_DUR = 0.45

# ---- 数据（每日汇总_1018-1105）
DAYS = ["10/18", "10/20", "10/22", "10/24", "10/26", "10/28", "10/30", "11/01", "11/03", "11/05"]
NEW_ACC = [3, 32, 33, 79, 104, 42, 45, 25, 3, 4]
VIDEOS = [8, 77, 154, 319, 561, 557, 553, 531, 443, 413]
H24 = [None, None, None, None, None, 197, 147, 136, 129, 134]

CH_Y, CH_W, CH_H = 620, 1060, 250
CH_X = (W - CH_W) // 2


def ease(t, t0, dur):
    return studio.ease_in_out(studio.prog(t, t0, dur))


def draw_line(c, x, y, items, a, dy=0.0):
    for text, font, color in items:
        if a > 0.004:
            ImageDraw.Draw(c).text((x, y + dy), text, font=font, anchor="ls",
                                   fill=(color[0], color[1], color[2], int(255 * studio.clamp(a))))
        x += font.getlength(text)
    return x


def line_width(items):
    return sum(f.getlength(t) for t, f, _ in items)


def block_x(lines, left=150, right=1770):
    w = max(line_width(i) for i in lines)
    return left + (right - left - w) / 2


# 阶段时钟：(切换时刻, 月前缀, 日)
STATES = [(0.00, "10月", "25日"), (0.15, "10月", "27日"),
          (8.00, "11月", "2日"), (13.60, "11月", "11日")]


def draw_corner(c, t):
    """前缀「10月/11月」小幅淡换，日号上下滚动；下方细线跟着宽度走。"""
    d = ImageDraw.Draw(c)
    idx = 0
    for i, (t0, _, _) in enumerate(STATES):
        if t >= t0:
            idx = i
    t0, pref, day = STATES[idx]

    if idx == 0:
        d.text((X_CORNER, CORNER_Y), pref + day, font=F_STAMP, anchor="ls", fill=(*WHITE, 255))
        w = F_STAMP.getlength(pref + day)
        d.rectangle([X_CORNER, CORNER_Y + 16, X_CORNER + w, CORNER_Y + 18], fill=(*WHITE, 140))
        return

    prev_pref, prev_day = STATES[idx - 1][1], STATES[idx - 1][2]
    p = ease(t, t0, SW_DUR)
    w_prev = F_STAMP.getlength(prev_pref + prev_day)
    w_now = F_STAMP.getlength(pref + day)

    if pref and pref != prev_pref:
        # 换月：整串一起滚，避免两个"10月/11月"叠着糊掉
        roll.roll_text(c, X_CORNER, CORNER_Y, prev_pref + prev_day, pref + day, p, F_STAMP, WHITE)
        w = w_prev * (1 - p) + w_now * p
    elif pref:
        # 同月：前缀不动，只滚日号
        d.text((X_CORNER, CORNER_Y), pref, font=F_STAMP, anchor="ls", fill=(*WHITE, 255))
        slot = X_CORNER + F_STAMP.getlength(pref)
        if p < 1:
            roll.roll_text(c, slot, CORNER_Y, prev_day, day, p, F_STAMP, WHITE)
        else:
            d.text((slot, CORNER_Y), day, font=F_STAMP, anchor="ls", fill=(*WHITE, 255))
        w = w_prev * (1 - p) + w_now * p
    else:
        # 收尾：整串滚出
        roll.roll_text(c, X_CORNER, CORNER_Y, prev_pref + prev_day, "", p, F_STAMP, WHITE)
        w = w_prev * (1 - p)

    if w > 4:
        d.rectangle([X_CORNER, CORNER_Y + 16, X_CORNER + w, CORNER_Y + 18], fill=(*WHITE, 140))


def axis(c, t, a, labels, bar_vals=None, line_vals=None, colors=(YELLOW, BLUE),
         legend=("", ""), bar_max=None, line_max=None, start=1.2, line_start=2.6):
    """迷你图：柱 + 线，各自缩放。"""
    if a <= 0.004:
        return
    d = ImageDraw.Draw(c)
    base = CH_Y + CH_H
    step = CH_W / len(labels)
    al = int(255 * a)

    if legend[0]:
        d.rectangle([CH_X, CH_Y - 52, CH_X + 14, CH_Y - 38], fill=(*colors[0], al))
        d.text((CH_X + 22, CH_Y - 34), legend[0], font=F_LEG, anchor="ls", fill=(*GREY, int(190 * a)))
    if legend[1]:
        d.line([(CH_X + 190, CH_Y - 45), (CH_X + 218, CH_Y - 45)], fill=(*colors[1], al), width=3)
        d.text((CH_X + 226, CH_Y - 34), legend[1], font=F_LEG, anchor="ls", fill=(*GREY, int(190 * a)))

    d.rectangle([CH_X, base, CH_X + CH_W, base + 1], fill=(*GREY, int(70 * a)))

    if bar_vals:
        bw = step * 0.42
        for i, v in enumerate(bar_vals):
            e = studio.ease_out_cubic(studio.prog(t, start + i * 0.06, 0.45))
            if e <= 0.001:
                continue
            h = CH_H * (v / (bar_max or max(bar_vals))) * e
            x = CH_X + i * step + (step - bw) / 2
            d.rounded_rectangle([x, base - h, x + bw, base], radius=3, fill=(*colors[0], al))
            if e > 0.96 and v == max(bar_vals):
                d.text((x + bw / 2, base - h - 12), str(v), font=F_VAL, anchor="ms",
                       fill=(*WHITE, int(235 * a)))

    if line_vals:
        pts = [(CH_X + i * step + step / 2,
                base - CH_H * (v / (line_max or max(line_vals))) * 0.9) for i, v in enumerate(line_vals)]
        p = studio.ease_in_out(studio.prog(t, line_start, 0.9))
        if p > 0:
            seg = p * (len(pts) - 1)
            k = int(seg)
            lp = pts[:k + 1]
            if k < len(pts) - 1:
                x0, y0 = pts[k]
                x1, y1 = pts[k + 1]
                f = seg - k
                lp.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f))
            if len(lp) >= 2:
                d.line(lp, fill=(*colors[1], al), width=4, joint="curve")
            for (x_, y_), v in ((pts[0], line_vals[0]), (pts[-1], line_vals[-1])):
                if k >= len(pts) - 1 or (x_, y_) == pts[0]:
                    tw = F_VAL.getlength(str(v))
                    d.rounded_rectangle([x_ - tw / 2 - 8, y_ - 40, x_ + tw / 2 + 8, y_ - 12],
                                        radius=6, fill=(11, 11, 13, int(210 * a)))
                    d.text((x_, y_ - 26), str(v), font=F_VAL, anchor="ms",
                           fill=(*colors[1], int(245 * a)))

    for i, lab in enumerate(labels):
        d.text((CH_X + i * step + step / 2, base + 32), lab, font=F_TICK, anchor="ms",
               fill=(*GREY, int(150 * a)))


A_TXT = [
    [("10月27日，内容供给达到峰值：单日发布 ", F_BODY, GREY), ("609", F_BOLD, YELLOW), (" 条。", F_BODY, GREY)],
    [("同时新增账号数量也进入拐点", F_BODY, GREY)],
    [("相比 10月25日降低约 ", F_BODY, GREY), ("50%", F_BOLD, YELLOW), ("。", F_BODY, GREY)],
]
B_TXT = [
    [("11月2日，单日新增账号仅余 ", F_BODY, GREY), ("5", F_BOLD, YELLOW), (" 个。", F_BODY, GREY)],
    [("增量入场基本停止。", F_BODY, GREY)],
]
C_TXT = [
    [("把「超过 7 天没有更新」记为停更。", F_BODY, GREY)],
    [("到 11月11日，", F_BODY, GREY), ("812", F_BOLD, YELLOW), (" 个账号中已有 ", F_BODY, GREY),
     ("274", F_BOLD, YELLOW), (" 个停更。", F_BODY, GREY)],
    [("存活率 ", F_BODY, GREY), ("66.3%", F_BOLD, YELLOW), ("，八天掉了 25 个百分点。", F_BODY, GREY)],
]
D_TXT = [
    [("19 天，", F_BODY, GREY), ("707", F_BOLD, YELLOW), (" 个新增账号，", F_BODY, GREY),
     ("7153", F_BODY, GREY), (" 条视频。", F_BODY, GREY)],
    [("增量在 10月27日见顶，存量自 11月初开始流失。", F_BODY, GREY)],
    [("对于跟风账号的清算，已然降临。", F_BODY, WHITE)],
]


def beat(c, t, t_in, t_out, lines, chart=None):
    if not (t_in <= t <= t_out + 0.45):
        return
    a = min(studio.ease_out_cubic(studio.prog(t, t_in, 0.5)), 1 - ease(t, t_out, 0.4))
    dy = (1 - studio.ease_out_cubic(studio.prog(t, t_in, 0.5))) * 22
    x = block_x(lines)
    # 有图的段落文字压在图表上方；纯文字段落整块垂直居中
    y0 = 280 if chart else 470
    for i, ln in enumerate(lines):
        draw_line(c, x, y0 + i * 88, ln, a, dy)
    if chart:
        chart(c, t, a)


def frame_at(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_corner(c, t)
    beat(c, t, A_IN, A_OUT, A_TXT,
         lambda cc, tt, aa: axis(cc, tt, aa, ["10/25", "10/27", "11/02", "11/05"],
                                 [109, 55, 5, 4], None, legend=("新开号（个）", ""), bar_max=120))
    beat(c, t, B_IN, B_OUT, B_TXT,
         lambda cc, tt, aa: axis(cc, tt, aa, DAYS, NEW_ACC, None,
                                 legend=("新开号（个）", ""), bar_max=120, start=0.9))
    beat(c, t, C_IN, C_OUT, C_TXT,
         lambda cc, tt, aa: axis(cc, tt, aa,
                                 ["11/03", "11/04", "11/05", "11/06", "11/07",
                                  "11/08", "11/09", "11/10", "11/11"],
                                 None, [91.9, 88.6, 85.0, 80.6, 76.7, 73.3, 71.0, 68.3, 66.3],
                                 legend=("", "存活率（%，7 天未更新即停更）"),
                                 line_max=100, line_start=1.4))
    beat(c, t, D_IN, D_OUT, D_TXT, None)
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
    OUT = HERE / "out" / "tail_alpha.mov"
    if len(sys.argv) >= 3 and sys.argv[1] == "--frame":
        t = float(sys.argv[2])
        dst = sys.argv[3] if len(sys.argv) > 3 else str(HERE / "out" / f"frame_{t}.png")
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        frame_at(t).save(dst)
        print("saved", dst)
    else:
        main()
