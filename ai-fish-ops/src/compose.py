# -*- coding: utf-8 -*-
r"""把若干「带 alpha 的片段」一次性压到同一条背景时间轴上。

为什么不用一段一段分别合成：那样每段的背景都从 0 秒开始，拼接处背景会跳回去
（水印瞬移）。这里背景只解一次、只播一遍，所有片段叠加在它上面，时间轴连续。

用法：
    python tools\compose.py spec.json

spec.json：
{
  "bg": "projects/nantingxv-bg/out/nantingxv-bg.mp4",
  "duration": 22.0,
  "out": "projects/001-opening/out/demo_composed.mp4",
  "crf": 18,
  "segments": [
    {"file": "projects/001-opening/out/opening_alpha.mov", "start": 0.0},
    {"file": "projects/001-opening/out/opening_alpha.mov", "start": 12.0}
  ]
}
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "libs"))
import studio  # noqa: E402


def bg_frame_count(path: str) -> int:
    p = studio.probe(path)
    v = p.get("video") or {}
    return int(v.get("frames") or round((p.get("duration") or 0) * (v.get("fps") or 30)))


def main() -> None:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    bg = spec["bg"]
    dur = float(spec["duration"])
    out = Path(spec["out"])
    segs = spec["segments"]

    n_bg = bg_frame_count(bg)
    inputs = ["-i", bg]
    for s in segs:
        inputs += ["-i", s["file"]]

    # 背景：循环自己的帧，裁到总时长，时间轴从 0 开始
    parts = [f"[0:v]loop=loop=-1:size={n_bg}:start=0,trim=0:{dur},setpts=PTS-STARTPTS[bg0]"]
    last = "bg0"
    for i, s in enumerate(segs, start=1):
        start = float(s.get("start", 0.0))
        parts.append(f"[{i}:v]setpts=PTS-STARTPTS+{start}/TB[s{i}]")
        parts.append(f"[{last}][s{i}]overlay=0:0:eof_action=pass:format=auto[o{i}]")
        last = f"o{i}"
    parts.append(f"[{last}]format=yuv420p[v]")

    fps = int(spec.get("fps", 30))
    cmd = [studio.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", *inputs,
           "-filter_complex", ";".join(parts), "-map", "[v]", "-t", str(dur),
           # 强制 CFR：overlay/trim/setpts 这条链在多输入时不保证等间隔时间戳，
           # 输出成 VFR 后播放器会忽快忽慢（剪辑软件也可能对不上帧）
           "-fps_mode", "cfr", "-r", str(fps),
           "-c:v", "libx264", "-preset", "medium", "-crf", str(spec.get("crf", 18)),
           "-movflags", "+faststart", str(out)]
    print("合成", len(segs), "段 ->", out, f"({dur}s)")
    subprocess.run(cmd, check=True)
    p = studio.probe(str(out))
    print("完成:", p.get("duration"), "s", p.get("video"))
    check_cfr(str(out))


def check_cfr(path: str) -> None:
    """输出后立刻验时间戳是否等间隔；VFR 直接报警。"""
    try:
        import av

        with av.open(path) as c:
            st = c.streams.video[0]
            ts = [float(fr.pts * fr.time_base) for fr in c.decode(video=0)]
        deltas = [round(ts[i + 1] - ts[i], 6) for i in range(len(ts) - 1)]
        uniq = sorted(set(deltas))
        if len(uniq) <= 2 and (max(uniq) - min(uniq)) < 0.002:
            print(f"[ok] CFR: {len(ts)} 帧, 帧间隔 {uniq[0]:.6f}s")
        else:
            from collections import Counter
            print(f"[!!] 可能是 VFR: {dict(Counter(deltas).most_common(5))}")
    except Exception as e:
        print("时间戳检查跳过:", e)


if __name__ == "__main__":
    main()
