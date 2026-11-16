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
from PIL import Image, ImageDraw

W, H, FPS = 1920, 1080, 30
DUR = 26.0
WHITE = studio.hex2rgb("#FFFFFF")
GREY = studio.hex2rgb("#C9D1DC")
DIM = studio.hex2rgb("#7C8798")
YELLOW = studio.hex2rgb("#FFC53D")
BLUE = studio.hex2rgb("#7FB2E5")
F_LAB = studio.font(46, "bold")
F_TICK = studio.font(24)
F_LEG = studio.font(34, "regular")
F_LEG_B = studio.font(34, "bold")
F_STAMP = studio.font(44, "bold")
EXPORT = Path(r"D:/tmp/export")

AX_Y = 860
X0, X1 = 240, 1680
D0 = datetime.fromisoformat("2026-10-08T00:00:00+08:00")
NDAY = 35


def load():
    seen, vids = set(), []
    with open(EXPORT / "video.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["bvid"] in seen:
                continue
            seen.add(r["bvid"])
            vids.append(r)
    cnt = [0] * NDAY
    tot = [0.0] * NDAY
    per = defaultdict(list)
    for v in vids:
        t = datetime.fromisoformat(v["pub_time"])
        d = (t - D0).days
        if 0 <= d < NDAY:
            cnt[d] += 1
            view = float(v["view"] or 0)
            tot[d] += view
            per[d].append(view)
    med = [float(np.median(per[d])) if per[d] else 0.0 for d in range(NDAY)]
    top = []
    for d in range(NDAY):
        arr = np.sort(np.array(per[d])) if per[d] else np.array([0.0])
        k = max(1, len(arr) // 10)
        top.append(float(arr[-k:].sum() / arr.sum()) if arr.sum() > 0 else 0.0)
    accounts = [0] * NDAY
    with open(EXPORT / "account.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            t = datetime.fromisoformat(r["first_pub_time"])
            d = (t - D0).days
            if 0 <= d < NDAY:
                accounts[d] += 1
    return cnt, tot, med, accounts


CNT, TOT, MED, NEW = load()

# 中位数在样本过少时会被单条视频带偏：当天发布不足 10 条的日期不参与
MED_SAFE = [MED[i] if CNT[i] >= 10 else 0.0 for i in range(NDAY)]

# 三个指标：(数组, 标题, 副标题)
METRICS = [
    (CNT, "每天发布的视频数", "供给"),
    (TOT, "每天发布视频的累计播放", "注意力"),
    (MED_SAFE, "每条视频的中位播放", "分到多少"),
]
DAYS = [D0 + timedelta(days=i) for i in range(NDAY)]


def ease(t, a, b):
    return studio.ease_in_out(studio.prog(t, a, b - a))


def day_x(i):
    return X0 + (X1 - X0) * i / (NDAY - 1)


def frame_at(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)

    # 0–1.0：轴线从上一段的位置（y=640）平移落到 y=860
    drop = studio.ease_in_out(studio.clamp(studio.prog(t, 0.0, 1.0)))
    axis_y = 640 + (AX_Y - 640) * drop
    intro = studio.clamp(studio.prog(t, 0.35, 0.6))

    # 显式时间轴：保持 -> 变形 -> 保持 -> 变形 -> 保持
    M1_HOLD = 9.0
    M1_DUR, M2_DUR = 2.2, 2.2
    if t < M1_HOLD:
        i0, morph = 0, 0.0
    elif t < M1_HOLD + M1_DUR:
        i0, morph = 0, studio.ease_in_out((t - M1_HOLD) / M1_DUR)
    elif t < M1_HOLD + M1_DUR + 5.8:
        i0, morph = 1, 0.0
    elif t < M1_HOLD + M1_DUR + 5.8 + M2_DUR:
        i0, morph = 1, studio.ease_in_out((t - (M1_HOLD + M1_DUR + 5.8)) / M2_DUR)
    else:
        i0, morph = 2, 0.0
    va, vb = METRICS[i0][0], METRICS[min(2, i0 + 1)][0]
    # 各自归一化后再插值：变形过程里柱子平滑长高，不会一上来就跳到新形态
    ma = max(va) or 1.0
    mb = max(vb) or 1.0
    vals = [(va[i] / ma) * (1 - morph) + (vb[i] / mb) * morph for i in range(NDAY)]

    grow = 1.0
    mx = 1.0
    # 文案进退场的权重：先退后进，避免同位置叠字
    m_old = studio.clamp(1.0 - morph / 0.12)
    m_new = studio.clamp((morph - 0.88) / 0.12)

    for i in range(NDAY):
        e = studio.ease_out_cubic(studio.clamp(studio.prog(t, 1.15 + i * 0.045, 0.55)))
        if e <= 0.004:
            continue
        h = 470.0 * (vals[i] / mx) * e
        x = day_x(i)
        d.rectangle([x - 9, axis_y - h, x + 9, axis_y], fill=(*YELLOW, 235))

    # 轴线
    d.line([(X0 - 30, axis_y), (X1 + 20, axis_y)], fill=(*DIM, 150), width=2)
    for i in range(NDAY):
        x = day_x(i)
        big = (i % 5 == 0) or (i == NDAY - 1)
        d.line([(x, axis_y), (x, axis_y + (18 if big else 10))],
               fill=(*DIM, int((130 if big else 80) * intro)), width=2)
        if big:
            d.text((x, axis_y + 52), DAYS[i].strftime("%m/%d"), font=F_TICK, anchor="ms",
                   fill=(*DIM, int(190 * intro)))

    # 指标标题
    idx = 0 if morph < 0.5 else 1
    cur = i0 if morph < 0.5 else min(2, i0 + 1)
    title = METRICS[cur][1]
    sub = METRICS[cur][2]
    # 第一幕专属：柱顶折线 + 数值 + 文案
    if cur == 0:
        tops = []
        for i in range(NDAY):
            e = studio.ease_out_cubic(studio.clamp(studio.prog(t, 1.15 + i * 0.045, 0.55)))
            if e > 0.004:
                tops.append((day_x(i), axis_y - 470.0 * (CNT[i] / (max(CNT) or 1)) * e))
        la = studio.ease_out_cubic(studio.clamp(studio.prog(t, 3.4, 0.8))) * m_old
        if la > 0.01 and len(tops) >= 2:
            d.line(tops, fill=(*WHITE, int(120 * la)), width=3, joint="curve")
        # 数值：起点、10/18、最高点、末点
        peak = int(max(range(NDAY), key=lambda i: CNT[i]))
        marks = sorted({0, 10, peak, NDAY - 1})
        for i in marks:
            e = studio.ease_out_cubic(studio.clamp(studio.prog(t, 1.15 + i * 0.045, 0.55)))
            if e < 0.99:
                continue
            y = axis_y - 470.0 * (CNT[i] / (max(CNT) or 1)) * e
            # 峰值统一用 609（与前半段口径对齐）
            lab_v = "609" if i == peak else str(CNT[i])
            d.text((day_x(i), y - 26), lab_v, font=F_TICK, anchor="ms",
                   fill=(*WHITE, int(225 * la)))
        # 第一幕文案：先退场，再让下一幕进场（错开，避免叠字）
        ta2 = studio.ease_out_cubic(studio.clamp(studio.prog(t, 4.4, 1.1))) * m_old
        if ta2 > 0.01:
            f2 = studio.font(60, "bold")
            F_POP = studio.font(68, "bold")
            L1 = "从每天的零星几条"
            L2A = "到瞬间的"
            L2B = "爆炸式增长"
            tx = 246
            ty1 = 408
            ty2 = ty1 + 104
            d.text((tx, ty1), L1, font=f2, anchor="la", fill=(*WHITE, int(240 * ta2)))
            d.text((tx, ty2), L2A, font=f2, anchor="la", fill=(*WHITE, int(240 * ta2)))
            # 「爆炸式增长」逐字弹出：快速放大 + 过冲，黄色、略大
            base_x = tx + f2.getlength(L2A) + 4
            cursor = base_x
            for ci, ch in enumerate(L2B):
                pw = F_POP.getlength(ch)
                p = studio.clamp(studio.prog(t, 5.15 + ci * 0.09, 0.34))
                if p > 0.001:
                    if p < 0.6:
                        sc = 0.45 + (1.12 - 0.45) * (p / 0.6)
                    else:
                        sc = 1.12 - 0.12 * ((p - 0.6) / 0.4)
                    al = min(1.0, p * 3.0)
                    TW, TH, BASE = int(pw) + 40, 220, 130
                    tile = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
                    ImageDraw.Draw(tile).text(((TW - pw) / 2, BASE), ch,
                                              font=F_POP, anchor="la",
                                              fill=(*YELLOW, int(255 * al)))
                    tile = tile.resize((max(1, int(TW * sc)), max(1, int(TH * sc))),
                                       Image.BICUBIC)
                    if ta2 < 0.999:      # 退场时整体淡出，避免与下一幕硬叠
                        arr = list(tile.split())
                        from PIL import ImageChops
                        arr[3] = arr[3].point(lambda v: int(v * ta2))
                        tile = Image.merge("RGBA", arr)
                    c.alpha_composite(tile, (int(cursor - ((TW - pw) / 2) * sc),
                                             int(ty2 - BASE * sc)))
                cursor += pw + 2
            tw = max(f2.getlength(L1), f2.getlength(L2A) + F_POP.getlength(L2B) + 10)
            # 引导线：从曲线上的点画向文字（方向朝文字）
            gx = day_x(13)
            gy = axis_y - 470.0 * (CNT[13] / (max(CNT) or 1)) - 10
            lp = 0.0
            if lp > 0.01:
                x1s, y1s = tx + tw + 46, 404
                xm = x1s + (gx - x1s) * 0.55
                pts = [(x1s, y1s), (xm, (y1s + gy) / 2), (gx, gy)]
                nseg = max(1, int(lp * 2))
                if lp < 1:
                    pts2 = pts[:nseg]
                    a0 = pts[nseg - 1]
                    a1 = pts[nseg]
                    pts2.append((a0[0] + (a1[0]-a0[0])*(lp*2-nseg+1), a0[1] + (a1[1]-a0[1])*(lp*2-nseg+1)))
                else:
                    pts2 = pts
                if len(pts2) >= 2:
                    d.line(pts2, fill=(*WHITE, int(150 * ta2)), width=2)
                if lp > 0.95:
                    d.ellipse([gx - 6, gy - 6, gx + 6, gy + 6], fill=(*WHITE, int(230 * ta2)))

    # 图内注释：放在柱子较低的空白区
    # 第二、三幕文案：与第一幕同样的字号与位置，出现/退场都跟 morph
    w2 = m_new if i0 == 0 else (m_old if i0 == 1 else 0.0)
    if w2 > 0.01:
        f3 = studio.font(60, "bold")
        tx3 = 1000          # 第二幕：文字放右侧空隙，避开左侧柱群
        seg1 = [("把所有视频的播放加起来", WHITE)]
        seg2 = [("峰值前移到 ", WHITE), ("10/20", YELLOW), (" 前后", WHITE)]
        for row, segs in ((408, seg1), (512, seg2)):
            xx = tx3
            for txt_k, col in segs:
                d.text((xx, row), txt_k, font=f3, anchor="la",
                       fill=(col[0], col[1], col[2], int(240 * w2)))
                xx += f3.getlength(txt_k)
    w3 = m_new if i0 == 1 else (1.0 if i0 == 2 else 0.0)
    if w3 > 0.01:
        f3 = studio.font(60, "bold")
        tx3 = 1010          # 第三幕：右移，避开 10/18 起的高柱
        seg1 = [("摊到每条视频上", WHITE)]
        seg2 = [("最后只剩 ", WHITE), ("一两百", YELLOW)]
        for row, segs in ((408, seg1), (512, seg2)):
            xx = tx3
            for txt_k, col in segs:
                d.text((xx, row), txt_k, font=f3, anchor="la",
                       fill=(col[0], col[1], col[2], int(240 * w3)))
                xx += f3.getlength(txt_k)
    ta = studio.ease_out_cubic(studio.clamp(studio.prog(t, 0.6, 0.8)))
    t_old_w = studio.clamp(1.0 - morph / 0.30)
    t_new_w = studio.clamp((morph - 0.30) / 0.30)
    t_old = METRICS[i0][1]
    t_new = METRICS[min(2, i0 + 1)][1]
    s_old = METRICS[i0][2]
    s_new = METRICS[min(2, i0 + 1)][2]
    dy_old = -16 * (1 - t_old_w)
    dy_new = 16 * (1 - t_new_w)
    if ta * t_old_w > 0.01:
        d.text((W / 2, 150 + dy_old), t_old, font=F_LEG_B, anchor="ms",
               fill=(*WHITE, int(235 * ta * t_old_w)))
        d.text((W / 2, 196 + dy_old), s_old, font=F_LEG, anchor="ms",
               fill=(*DIM, int(200 * ta * t_old_w)))
    if i0 < 2 and t_new_w > 0.01:
        d.text((W / 2, 150 + dy_new), t_new, font=F_LEG_B, anchor="ms",
               fill=(*WHITE, int(235 * ta * t_new_w)))
        d.text((W / 2, 196 + dy_new), s_new, font=F_LEG, anchor="ms",
               fill=(*DIM, int(200 * ta * t_new_w)))

    # 结尾整体淡出，交给下一段的淡入
    fo = 1.0 - studio.ease_in_out(studio.clamp(studio.prog(t, DUR - 0.75, 0.75)))
    if fo < 0.999:
        from PIL import ImageChops
        c.putalpha(ImageChops.multiply(c.getchannel("A"), Image.new("L", (W, H), int(255 * fo))))
    return c


OUT = HERE / "out" / "axis_alpha.mov"


def main():
    n = int(DUR * FPS)
    print("%d 帧 -> %s" % (n, OUT))
    print("发布量", CNT[:5], "... 总计", sum(CNT))
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
