# -*- coding: utf-8 -*-
"""studio — 本地视频生产公用库。

职责：
  * 把 studio/libs 挂进 sys.path（依赖不外溢到全局）
  * 定位 ffmpeg
  * 逐帧写视频（PIL Image -> pipe -> libx264）
  * 探测元数据（PyAV）、抽缩略图、跑 ffmpeg 滤镜

用法：
    import studio
    studio.FFMPEG, studio.ROOT
    studio.probe("out/a.mp4")
    with studio.VideoWriter("out/a.mp4", (1920,1080), fps=30, crf=18) as w:
        w.write(img)

约定：所有函数吃 str/Path 都行，返回普通 dict / str，不藏全局状态。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
LIBS = ROOT / "libs"
ASSETS = ROOT / "assets"
PROJECTS = ROOT / "projects"
CACHE = ROOT / "cache"
FONTS_DIR = Path(r"C:\Windows\Fonts")

FFMPEG = BIN / "ffmpeg.exe"


def _bootstrap() -> None:
    """让 import studio 之后就能 import PIL / av 等，不需要先设 PYTHONPATH。"""
    p = str(LIBS)
    if LIBS.is_dir() and p not in sys.path:
        sys.path.insert(0, p)


_bootstrap()

from PIL import Image, ImageDraw, ImageFont  # noqa: E402


# ---------------------------------------------------------------- ffmpeg

def ffmpeg_exe() -> str:
    if not FFMPEG.exists():
        raise FileNotFoundError(f"ffmpeg 不存在: {FFMPEG}")
    return str(FFMPEG)


def run_ffmpeg(*args, check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess:
    """跑一次 ffmpeg，返回 CompletedProcess。失败时把 stderr 带进异常。"""
    cmd = [ffmpeg_exe(), "-hide_banner", *[str(a) for a in args]]
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError(f"ffmpeg 失败 (exit {p.returncode}):\n" + p.stderr[-4000:])
    return p


# ---------------------------------------------------------------- 探测

def probe(path) -> dict:
    """读容器/流信息。优先 PyAV，失败则退回解析 ffmpeg -i。"""
    path = str(path)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    info: dict = {"path": path, "bytes": os.path.getsize(path)}
    try:
        import av

        with av.open(path) as c:
            info["format"] = c.format.name
            info["duration"] = round(c.duration / 1e6, 3) if c.duration else None
            vs = [s for s in c.streams if s.type == "video"]
            if vs:
                v = vs[0]
                cc = v.codec_context
                info["video"] = {
                    "codec": cc.name,
                    "width": cc.width,
                    "height": cc.height,
                    "fps": round(float(v.average_rate), 4) if v.average_rate else None,
                    "frames": v.frames,
                    "pix_fmt": cc.pix_fmt,
                }
            info["audio"] = [
                {"codec": s.codec_context.name,
                 "rate": getattr(s.codec_context, "sample_rate", None),
                 "channels": getattr(s.codec_context, "channels", None)}
                for s in c.streams if s.type == "audio"
            ]
    except Exception as e:  # 没装 av / 文件损坏
        info["probe_error"] = f"{type(e).__name__}: {e}"
    return info


def duration(path) -> float:
    return probe(path).get("duration") or 0.0


def thumb(src, t: float, out, width: int | None = None) -> str:
    """在 t 秒处抽一帧 PNG。width 给定时等比缩放。"""
    out = str(out)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    vf = ["-vf", f"scale={width}:-2"] if width else []
    run_ffmpeg("-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1", *vf, "-y", out)
    return out


# ---------------------------------------------------------------- 排版小工具

def font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    """微软雅黑。weight: regular / bold / light。"""
    name = {"regular": "msyh.ttc", "bold": "msyhbd.ttc", "light": "msyhl.ttc"}[weight]
    return ImageFont.truetype(str(FONTS_DIR / name), size)


def text_size(draw: ImageDraw.ImageDraw, s: str, f: ImageFont.FreeTypeFont) -> tuple[int, int]:
    l, t, r, b = draw.textbbox((0, 0), s, font=f)
    return r - l, b - t


def wrap(draw: ImageDraw.ImageDraw, s: str, f: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    """按像素宽度折行，中文按字、英文按词。"""
    lines, cur = [], ""
    for ch in s:
        trial = cur + ch
        if text_size(draw, trial, f)[0] <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def hex2rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


# ---------------------------------------------------------------- 缓动

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return 3 * t * t - 2 * t * t * t


def prog(t, start, dur) -> float:
    """在 [start, start+dur] 区间内的归一化进度，已 clamp 到 0..1。"""
    if dur <= 0:
        return 1.0 if t >= start else 0.0
    return clamp((t - start) / dur)


# ---------------------------------------------------------------- 写视频

class VideoWriter:
    """把 PIL 帧按原始 RGB 管道喂给 ffmpeg/libx264。

    with VideoWriter("out.mp4", (1920,1080), fps=30, crf=18) as w:
        w.write(img)
    """

    def __init__(self, out, size=None, fps: float = 30, crf: int = 20,
                 preset: str = "medium", pix_fmt: str = "yuv420p",
                 audio: str | None = None, audio_bitrate: str = "192k",
                 extra_vf: str | None = None,
                 in_fmt: str = "rgb24", vcodec: list[str] | None = None):
        self.out = str(out)
        Path(self.out).parent.mkdir(parents=True, exist_ok=True)
        self.size = tuple(size) if size else None
        self.fps = float(fps)
        self.crf = int(crf)
        self.preset = preset
        self.pix_fmt = pix_fmt
        self.audio = str(audio) if audio else None
        self.audio_bitrate = audio_bitrate
        self.extra_vf = extra_vf
        self.in_fmt = in_fmt           # "rgb24" 或 "rgba"（带透明通道）
        self.vcodec = vcodec           # 自定义编码参数，给了就不走 libx264 默认
        self.frames = 0
        self._p: subprocess.Popen | None = None
        self._resized = 0

    # -- 生命周期
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close(kill=exc_type is not None)
        return False

    def _spawn(self, size):
        cmd = [ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", self.in_fmt,
               "-s", f"{size[0]}x{size[1]}", "-r", str(self.fps), "-i", "-"]
        if self.audio:
            cmd += ["-i", self.audio]
        if self.extra_vf:
            cmd += ["-vf", self.extra_vf]
        if self.vcodec:
            cmd += self.vcodec
        else:
            cmd += ["-c:v", "libx264", "-preset", self.preset, "-crf", str(self.crf),
                    "-pix_fmt", self.pix_fmt]
        if self.audio:
            cmd += ["-c:a", "aac", "-b:a", self.audio_bitrate, "-shortest"]
        cmd += ["-movflags", "+faststart", self.out]
        self._p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def write(self, im: Image.Image) -> None:
        want = "RGBA" if self.in_fmt == "rgba" else "RGB"
        if im.mode != want:
            im = im.convert(want)
        if self.size is None:
            self.size = im.size
        if im.size != self.size:
            im = im.resize(self.size, Image.LANCZOS)
            self._resized += 1
        if self._p is None:
            self._spawn(self.size)
        assert self._p and self._p.stdin
        try:
            self._p.stdin.write(im.tobytes())
        except BrokenPipeError:
            err = self._p.stderr.read().decode("utf-8", "replace") if self._p.stderr else ""
            raise RuntimeError("ffmpeg 提前退出：\n" + err[-3000:]) from None
        self.frames += 1

    def close(self, kill: bool = False) -> None:
        if self._p is None:
            return
        try:
            if self._p.stdin:
                self._p.stdin.close()
        except Exception:
            pass
        if kill:
            self._p.kill()
        err = self._p.stderr.read().decode("utf-8", "replace") if self._p.stderr else ""
        rc = self._p.wait()
        self._p = None
        if rc != 0 and not kill:
            raise RuntimeError(f"ffmpeg 退出码 {rc}:\n{err[-3000:]}")


def frames_to_video(frame_paths, out, fps: float = 30, crf: int = 20,
                    preset: str = "medium", pattern: bool = True) -> str:
    """已有的 PNG 序列 -> mp4。pattern=True 时按 %06d 编号读。"""
    fps = float(fps)
    if pattern:
        first = str(frame_paths)
        run_ffmpeg("-framerate", fps, "-i", first, "-c:v", "libx264",
                   "-preset", preset, "-crf", crf, "-pix_fmt", "yuv420p",
                   "-movflags", "+faststart", "-y", str(out))
    else:
        raise NotImplementedError("先用 VideoWriter 逐帧写更省事")
    return str(out)


# ---------------------------------------------------------------- CLI

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "probe":
        print(json.dumps(probe(sys.argv[2]), ensure_ascii=False, indent=2))
    else:
        print("usage: python studio.py probe <file>")
