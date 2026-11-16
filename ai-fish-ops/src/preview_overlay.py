# -*- coding: utf-8 -*-
r"""把带透明通道的图或视频压到背景上，方便肉眼验收。

用法：
    python tools\preview_overlay.py in.png out.png [背景色:#0B0B0D | 背景图.jpg]
    python tools\preview_overlay.py in.mov out.mp4 [背景视频.mp4]
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "libs"))
import studio  # noqa: E402
from PIL import Image  # noqa: E402


def main() -> None:
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    bg_arg = sys.argv[3] if len(sys.argv) > 3 else "#0B0B0D"
    dst.parent.mkdir(parents=True, exist_ok=True)

    if src.suffix.lower() in (".png", ".jpg", ".webp"):
        im = Image.open(src).convert("RGBA")
        if bg_arg.startswith("#"):
            bg = Image.new("RGB", im.size, studio.hex2rgb(bg_arg))
        else:
            bg = Image.open(bg_arg).convert("RGB").resize(im.size, Image.LANCZOS)
        out = Image.alpha_composite(bg.convert("RGBA"), im).convert("RGB")
        out.save(dst)
        print(f"{dst}  {out.width}x{out.height}")
        return

    # 视频：ffmpeg overlay
    if src.suffix.lower() not in (".mov", ".webm", ".mkv", ".avi"):
        raise SystemExit("不认识的格式: " + str(src))
    if bg_arg.startswith("#"):
        rgb = studio.hex2rgb(bg_arg)
        base = f"color=c=0x{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}:s=1920x1080"
        inputs = ["-f", "lavfi", "-i", base, "-i", str(src)]
        graph = "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    else:
        inputs = ["-stream_loop", "-1", "-i", bg_arg, "-i", str(src)]
        graph = "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    cmd = [studio.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", *inputs,
           "-filter_complex", graph, "-map", "[v]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-shortest", str(dst)]
    subprocess.run(cmd, check=True)
    print(f"{dst}  {dst.stat().st_size/1048576:.1f} MB")


if __name__ == "__main__":
    main()
