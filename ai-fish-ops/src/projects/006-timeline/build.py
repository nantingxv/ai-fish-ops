# -*- coding: utf-8 -*-
r"""006-timeline —— 收尾后拉出时间轴。

  0.0–1.5   日期从左上角原位（150,118）滑到屏幕中央并放大，横线跟随
  1.5–2.0   刻度与轴线淡入
  2.0–7.4   日期连续倒数到 10月8日；时间轴以当前日期为中心、左右对称滚动
            可见窗口 = 画面 2/3，两端渐隐
  7.4–8.8   整体缩小并居中，35 天完整进画
"""
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import studio  # noqa: E402
from PIL import Image, ImageChops, ImageDraw  # noqa: E402

W, H, FPS = 1920, 1080, 30
DUR = 5.7

D0 = date(2026, 10, 8)
N = 35
SP = 90.0
AXIS_Y = 640
LABEL_CY = 540          # 标签光学中心（用 anchor="mm" 对齐）
TICK = 26
F_TICK = studio.font(20)
WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#8C97A6")

T_FLY0, T_FLY1 = 0.0, 0.8
T_TICKS0, T_TICKS1 = 0.8, 1.2
T_CNT0, T_CNT1 = 1.2, 3.6
T_SH0, T_SH1 = 3.6, 4.6
T_MORPH0, T_MORPH1 = 4.6, 5.7
MORPH_I = 10        # 10月18日

WIN = W * 2 / 3          # 可见窗口宽度
FADE = 110

SRC_X, SRC_Y, SRC_SIZE = 150, 118, 44


def ease(t, a, b):
    return studio.ease_in_out(studio.prog(t, a, b - a))


def label_of(i):
    d = D0 + timedelta(days=i)
    return f"{d.month}月{d.day}日"


def ink_center(text, font, left, baseline):
    """把 anchor='ls' 画在 (left, baseline) 的文字，换算成它墨迹的几何中心。"""
    l, t, r, b = font.getbbox(text)
    asc, _ = font.getmetrics()
    return (left + (l + r) / 2.0, baseline - asc + (t + b) / 2.0)


def draw_ink_centered(draw, cx, cy, text, font, fill):
    """以墨迹中心对齐 (cx, cy) 绘制文字（几何居中 != 视觉居中）。"""
    l, t, r, b = font.getbbox(text)
    draw.text((cx - (l + r) / 2.0, cy - (t + b) / 2.0), text, font=font,
              anchor="la", fill=fill)
    return (cx - (l + r) / 2.0, cy - (t + b) / 2.0, r - l, b - t)


def frame_at(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # 连续进度：34 -> 0
    # 倒数用缓入缓出：先慢、中段快、末尾再慢下来
    p = studio.ease_in_out(studio.clamp(studio.prog(t, T_CNT0, T_CNT1 - T_CNT0)))
    fidx = (N - 1) * (1 - p)
    idx = int(round(fidx))

    # 收拢
    ps = ease(t, T_SH0, T_SH1)
    s = studio.lerp(1.0, 0.50, ps)

    # 标签位置：起点与角标完全对齐（左边缘 150、基线 118、字号 44）
    pfly = studio.ease_in_out(studio.prog(t, T_FLY0, T_FLY1))
    size = studio.lerp(SRC_SIZE, 56, pfly)
    txt = label_of(idx)
    # 起点精确对齐上一段的角标（左 150、基线 118、字号 44），用墨迹中心表达
    f_src = studio.font(SRC_SIZE, "bold")
    cx_src, cy_src = ink_center("11月11日", f_src, SRC_X, SRC_Y)
    cx = studio.lerp(cx_src, W / 2, pfly)
    cy = studio.lerp(cy_src, LABEL_CY, pfly)
    cx_final = W / 2 - (N - 1) * SP * 0.50 / 2
    cx = studio.lerp(cx, cx_final, ps)
    s_size = studio.lerp(size, 44, ps)

    # 轴线与刻度层
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    ta = studio.ease_out_cubic(studio.prog(t, T_TICKS0, T_TICKS1 - T_TICKS0))
    if ta > 0.004:
        x_of = lambda i: cx + (i - fidx) * SP * s
        dl.line([(x_of(0), AXIS_Y), (x_of(N - 1), AXIS_Y)],
                fill=(*GREY, int(190 * ta)), width=2)
        for i in range(N):
            x = x_of(i)
            if x < -30 or x > W + 30:
                continue
            big = i in (0, N - 1)
            hh = TICK * (1.7 if big else 1.0) * (0.7 + 0.3 * s)
            dl.line([(x, AXIS_Y), (x, AXIS_Y + hh)],
                    fill=(*GREY, int((255 if big else 165) * ta)), width=2)
            if (i % 5 == 0 and i != 0) or (big and i == N - 1):
                la = int(160 * ta)
                if i == MORPH_I:      # 由大标签落位接管，这里始终保留作底
                    la = int(160 * ta)
                dl.text((x, AXIS_Y + hh + 28), label_of(i), font=F_TICK,
                        anchor="ms", fill=(*GREY, la))

    # 窗口遮罩：2/3 画面居中，两端渐隐。
    # 收拢时窗口平滑张开到整屏（而不是突然撤掉遮罩），避免"闪一下"。
    if ta > 0.004:
        win = studio.lerp(WIN, W * 2.6, ps)
        L, R = (W - win) / 2, (W + win) / 2
        mask = Image.new("L", (W, 1), 0)
        px = mask.load()
        for x in range(W):
            if L + FADE <= x <= R - FADE:
                v = 255
            elif x < L + FADE:
                v = int(255 * max(0.0, (x - L) / FADE))
            else:
                v = int(255 * max(0.0, (R - x) / FADE))
            px[x, 0] = max(0, min(255, v))
        alpha = layer.getchannel("A")
        layer.putalpha(ImageChops.multiply(alpha, mask.resize((W, H))))
    c.alpha_composite(layer)

    # 最后一拍：大标签缩小、变灰、落到 10月18日 的刻度标签位置
    pm = ease(t, T_MORPH0, T_MORPH1)
    lab_x, lab_y, lab_size = cx, cy, s_size
    lab_rgb, lab_a = WHITE, 1.0
    if pm > 0:
        x_t = cx        # 原地缩小下落，不做横向位移
        y_t = AXIS_Y + TICK * (0.7 + 0.3 * s) + 28
        lab_x = studio.lerp(cx, x_t, pm)
        lab_y = studio.lerp(cy, y_t, pm)
        lab_size = studio.lerp(s_size, 20, pm)
        lab_rgb = tuple(int(studio.lerp(255, GREY[k], pm)) for k in range(3))
        lab_a = 1.0 - studio.ease_in_out(studio.prog(pm, 0.40, 0.40))

    # 当前时间的指示刻度：从标签下沿连到轴线（morph 时淡出），不穿过文字。
    # 必须画在独立图层再合成——ImageDraw 直接写像素，低 alpha 会把底下的刻度擦掉。
    if ta > 0.004 and pm < 0.999:
        f_tmp = studio.font(int(s_size), "bold")
        bh_tmp = f_tmp.getbbox(txt)[3] - f_tmp.getbbox(txt)[1]
        # 弹出时：起点从标签下方 4px 缓慢下移到 26px，长度随之变短（下端永远不越过刻度）
        pc = studio.ease_out_cubic(studio.clamp(studio.prog(t, T_TICKS0, 0.45)))
        top = cy + bh_tmp / 2 + studio.lerp(4, 26, pc)
        hh_cur = TICK * 1.7 * (0.7 + 0.3 * s)
        ia = int(235 * ta * (1 - pm) * min(1.0, pc * 1.6))
        if ia > 2:
            ind = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ind).line([(cx, top), (cx, AXIS_Y + hh_cur)],
                                     fill=(*WHITE, ia), width=3)
            c.alpha_composite(ind)

    # 标签（含横线），垂直居中
    d = ImageDraw.Draw(c)
    f_lab = studio.font(int(lab_size), "bold")
    if int(255 * lab_a) <= 2:
        return c
    # 标签也画在独立图层上合成，避免低 alpha 直接覆盖轴线
    lab = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl2 = ImageDraw.Draw(lab)
    if pm <= 0.001:
        bx, by, bw, bh = draw_ink_centered(dl2, lab_x, lab_y, txt, f_lab, (*WHITE, 255))
        dl2.rectangle([bx, by + bh + 20, bx + bw, by + bh + 22], fill=(*WHITE, 150))
    else:
        draw_ink_centered(dl2, lab_x, lab_y, txt, f_lab, (*lab_rgb, int(255 * lab_a)))
        x0 = cx + (0 - fidx) * SP * s
        dl2.text((x0, AXIS_Y + TICK * 1.7 + 28), label_of(0), font=F_TICK, anchor="ms",
                 fill=(*GREY, int(160 * min(1.0, pm * 1.6))))
    c.alpha_composite(lab)
    return c


OUT = HERE / "out" / "timeline_alpha.mov"


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
