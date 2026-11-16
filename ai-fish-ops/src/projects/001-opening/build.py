# -*- coding: utf-8 -*-
r"""001-opening —— 片头：24 张封面在一个圆角卡片里向上滚动。

画面内容：
  * 居中的圆角矩形卡片（1640x940，不占满屏幕），里面 4 列 x 3 行的封面网格
  * 网格缓慢向上滚动，行间距、封面间距留白
  * 卡片上下边缘做透明度渐变，滚出去的封面是"淡出"而不是被切断
  * 整块卡片从 0 放大到 1（带回一点点过冲）
  * 背景透明：卡片外面没有内容，后期叠在 nantingxv 背景上

输出：
  out/opening_alpha.mov   ProRes 4444（带 alpha 的母版）
  out/opening_preview.mp4 压到背景上的预览（合成用 ffmpeg 另跑）

跑法： D:\Python\python.exe projects\001-opening\build.py
      D:\Python\python.exe projects\001-opening\build.py --frame 3.0 out.png
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import studio  # noqa: E402
from PIL import Image, ImageDraw, ImageOps  # noqa: E402

# ---------------------------------------------------------------- 参数
MANIFEST = Path(r"D:\covers\manifest.json")
W, H, FPS = 1920, 1080, 30
if "--fps" in sys.argv:                      # 可选：按项目帧率出片
    FPS = int(sys.argv[sys.argv.index("--fps") + 1])
DUR = 7.8           # 出场的最后一帧正好滑出画面，不留空尾

SPEED = 70.0            # 像素/秒，向上滚动；线性匀速，后期可直接变速不糊
PANEL_W, PANEL_H = 1640, 940
PAD, GAP_X, GAP_Y = 40, 22, 20
COLS, ROWS = 4, 3
RADIUS, COVER_RADIUS = 28, 10

SCALE_START, SCALE_DUR = 0.0, 1.2   # 进场：放大的起点与时长

# 出场：整块卡片往上滑走，同时轻微缩小（像镜头往后退）。
# 方向沿用卡片内部封面向上滚的方向，接得上后面进来的内容。
EXIT_START, EXIT_DUR = 7.0, 0.85
EXIT_RISE = 1250.0      # 向上位移总量（大于画高，保证完全出画）
EXIT_SHRINK = 0.92      # 出场时缩到原来的 92%


CARD_BG = studio.hex2rgb("#15161C")
BORDER = (255, 255, 255, 22)
TITLE_C = studio.hex2rgb("#E6EBF2")
BV_C = studio.hex2rgb("#6F7B8C")
FADE_PX = 190           # 上下各 190px 透明渐变
FADE_POW = 2.6          # 越大，越靠边掉得越狠

CELL_W = (PANEL_W - 2 * PAD - (COLS - 1) * GAP_X) / COLS
COVER_H = round(CELL_W * 9 / 16)
TEXT_GAP, CELL_PAD_TEXT = 8, 4
F_TITLE = studio.font(21, "regular")
F_BV = studio.font(15, "regular")
CELL_H = COVER_H + TEXT_GAP + 30 + CELL_PAD_TEXT + 21
ROW_H = CELL_H + GAP_Y

_DBG = "--debug-frames" in sys.argv
OUT = HERE / "out" / (
    f"opening_alpha_{FPS}fps{'_debug' if _DBG else ''}.mov" if FPS != 30
    else f"opening_alpha{'_debug' if _DBG else ''}.mov")


def scale_at(t: float) -> float:
    """尺寸按 smoothstep 插值：两头速度为 0，0 秒开始，1.2 秒落定。

    试过对数插值（每帧固定 x1.14，比例绝对均匀），但那样 0.8 秒时卡片才 328px，
    前面 0.8 秒几乎是个点，最后 0.4 秒才呼地撑开 —— 反而更怪。
    smoothstep 在像素域是线性的，节奏自然，且实测每帧尺寸都在变。
    """
    return studio.ease_in_out(studio.prog(t, SCALE_START, SCALE_DUR))


def load_items() -> list[dict]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    items = [i for i in data["items"] if i.get("ok")]
    return items


def truncate(draw, text: str, font, max_w: int) -> str:
    """按像素宽截断，超出加省略号。"""
    if studio.text_size(draw, text, font)[0] <= max_w:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if studio.text_size(draw, text[:mid] + "…", font)[0] <= max_w:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + "…" if lo else "…"


def build_assets() -> dict:
    items = load_items()
    cw, ch = int(CELL_W), COVER_H
    # 圆角遮罩
    rmask = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(rmask).rounded_rectangle([0, 0, cw - 1, ch - 1], radius=COVER_RADIUS, fill=255)

    covers = {}
    for it in items:
        im = Image.open(it["path"]).convert("RGB")
        # 稍微偏上取景，人像/标题一般在上面
        fit = ImageOps.fit(im, (cw, ch), Image.LANCZOS, centering=(0.5, 0.38))
        fit.putalpha(rmask)
        covers[it["bvid"]] = fit

    # 上下渐变遮罩（255 = 显示卡片底色）
    fade = Image.new("L", (PANEL_W, PANEL_H), 0)
    px = fade.load()
    for y in range(PANEL_H):
        d = min(y, PANEL_H - 1 - y)
        shown = studio.clamp(d / FADE_PX) ** FADE_POW   # 可见度：贴边几乎为 0
        val = int(255 * (1 - shown))
        for x in range(0, PANEL_W):
            px[x, y] = val

    # 卡片圆角遮罩
    mask = Image.new("L", (PANEL_W, PANEL_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, PANEL_W - 1, PANEL_H - 1], radius=RADIUS, fill=255)

    return {"items": items, "covers": covers, "fade": fade, "mask": mask}


def panel_at(assets: dict, t: float) -> Image.Image:
    items, covers = assets["items"], assets["covers"]
    card = Image.new("RGB", (PANEL_W, PANEL_H), CARD_BG)
    d = ImageDraw.Draw(card)
    off = SPEED * t
    top = PAD

    n_rows = math.ceil(len(items) / COLS)
    for r in range(n_rows):
        y = top + r * ROW_H - off
        if y > PANEL_H or y + CELL_H < 0:
            continue
        for c in range(COLS):
            k = r * COLS + c
            if k >= len(items):
                break
            it = items[k]
            x = PAD + c * (CELL_W + GAP_X)
            cv = covers[it["bvid"]]
            card.paste(cv, (int(x), int(y)), cv)
            title = truncate(d, it.get("csv_title") or it.get("title", ""), F_TITLE, int(CELL_W))
            d.text((x, y + COVER_H + TEXT_GAP), title, font=F_TITLE, fill=TITLE_C)
            d.text((x, y + COVER_H + TEXT_GAP + 30), it["bvid"], font=F_BV, fill=BV_C)

    # 上下淡出：越靠边越接近卡片底色
    card = Image.composite(Image.new("RGB", card.size, CARD_BG), card, assets["fade"])
    # 描边
    ImageDraw.Draw(card).rounded_rectangle([0, 0, PANEL_W - 1, PANEL_H - 1],
                                           radius=RADIUS, outline=BORDER, width=2)
    out = card.convert("RGBA")
    out.putalpha(assets["mask"])
    return out


def frame_at(assets: dict, t: float) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s = scale_at(t)
    e = studio.prog(t, EXIT_START, EXIT_DUR) ** 2.2      # 出场用加速，像被抽走
    if e > 0:
        s *= 1 - (1 - EXIT_SHRINK) * e
        dy = -EXIT_RISE * e
    else:
        dy = 0.0
    if s <= 0.002:
        return canvas
    panel = panel_at(assets, t)
    if abs(s - 1.0) > 0.001:
        panel = panel.resize((max(1, int(PANEL_W * s)), max(1, int(PANEL_H * s))), Image.LANCZOS)
    canvas.paste(panel, ((W - panel.width) // 2, int((H - panel.height) // 2 + dy)))
    return canvas


def burn_frame_number(img: Image.Image, i: int) -> Image.Image:
    """帧号烧到左上角（画布上、卡片之外），用于在剪辑软件里逐帧核对。"""
    d = ImageDraw.Draw(img)
    d.text((56, 36), f"f{i:03d}", font=studio.font(64, "bold"), fill=(255, 92, 92, 245))
    d.text((58, 114), f"{FPS}fps", font=studio.font(24, "regular"), fill=(255, 92, 92, 180))
    return img


def main() -> None:
    assets = build_assets()
    n = int(DUR * FPS)
    debug = "--debug-frames" in sys.argv
    print(f"{len(assets['items'])} 个条目 / {n} 帧 -> {OUT}" + ("  [烧帧号]" if debug else ""))
    vcodec = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
              "-vendor", "apl0", "-qscale:v", "12"]
    with studio.VideoWriter(OUT, (W, H), fps=FPS, in_fmt="rgba", vcodec=vcodec) as w:
        for f in range(n):
            img = frame_at(assets, f / FPS)
            if debug:
                img = burn_frame_number(img, f)
            w.write(img)
            if f % 60 == 0:
                print(f"  {f}/{n}", flush=True)
    print("done:", OUT, round(OUT.stat().st_size / 1048576, 1), "MB")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--frame":
        a = build_assets()
        t = float(sys.argv[2])
        dst = sys.argv[3] if len(sys.argv) > 3 else str(HERE / "out" / f"frame_{t}.png")
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        frame_at(a, t).save(dst)
        print("saved", dst)
    else:
        main()
