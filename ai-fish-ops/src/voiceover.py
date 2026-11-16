# -*- coding: utf-8 -*-
r"""给成片配旁白：edge-tts 逐句生成 -> 按时间轴摆放 -> 压低 BGM -> 混音输出。

用法： python tools\voiceover.py
"""
import asyncio
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "libs"))
import av  # noqa: E402
import edge_tts  # noqa: E402
import studio  # noqa: E402

VOICE = "zh-CN-YunxiNeural"
VIDEO = HERE.parent / "projects" / "full_preview.mp4"
MUSIC_SRC = Path(r"D:\tmp\bili_audio\[Minecraft] 唱片音乐 《wait》完整版.m4a")
OUT = HERE.parent / "projects" / "full_voiced.mp4"
WORK = HERE.parent / "cache" / "vo"
DUR = 313.567

# (起始, 结束, 文本)
LINES = [
    ( 0.35,  4.60, "如你所见，这大概就是你最近刷到的视频。"),
    ( 4.35,  7.83, "流水线化的创作，模板化的文案。"),
    ( 7.95, 16.30, "观前提醒：账号数据均为人工录入，名单见简介。数据截止十一月十一日，也就是一周前。"),
    (16.45, 20.46, "带你看懂，这场鱼灾到底是什么。"),
    (20.55, 24.87, "10月8日，在绝望中堕落发布了第一期。"),
    (25.00, 29.08, "Claude 大小姐在运营，打响军备竞赛。"),
    (29.25, 35.01, "10月20日到 25日，单日新增从 31 个涨到 109 个。"),
    (35.25, 43.34, "25日发布 505 条，翻 6.7 倍，但播放只有 330 万，审美疲劳已经出现。"),
    (44.00, 51.68, "10月27日，单日发布 609 条，为全期峰值；新增账号数量同期腰斩。"),
    (51.85, 55.91, "11月2日，单日新增账号仅余 5 个。"),
    (57.60, 64.42, "七天不更新即停更。到 11 月 11 日，存活率只剩 66%。"),
    (65.20, 68.70, "增量见顶，存量开始流失。"),
    (68.90, 72.67, "对于跟风账号的清算，已然降临。"),
    (74.30, 79.75, "如果我们把时间拨回开始，从全局重新审视这一场流量风波。"),
    (80.80, 88.55, "这段时间里，每天新增的视频从几十条瞬间涨到五百多条，然后慢慢回落。"),
    (91.10, 96.60, "把这些视频最终的播放加起来，峰值出现在十月二十号前后。"),
    (99.10, 104.76, "而摊到每一条视频，中位播放一路走低，最后只剩一两百。"),
    (106.30, 114.29, "十月二十七日之后，供给开始自己收缩。日发布量从六百二十条，一路降到四百一十四条。"),
    (114.70, 123.72, "而单条视频能分到的注意力，没有继续跌，稳定在一百六到一百九十之间。价格止跌，供给继续退。"),
    (125.50, 129.70, "八百三十九个账号，一共三千七百万播放。"),
    (130.50, 138.80, "最大的十个，拿走百分之五十五点八。其中第一名一个账号，就占了百分之二十三点八。"),
    (139.60, 144.42, "最小的九成账号，加起来只分到百分之十三点五。"),
    (146.90, 152.30, "十月十八日开号的账号，单条视频的中位播放是一千一百六十二。"),
    (153.15, 159.40, "十月二十三日开号，三百三十四。十一月七日开号，六十六。"),
    (159.65, 166.55, "晚两周入场，中位播放相差十八倍。入场券的保质期只有七天。"),
    (168.00, 174.53, "到十一月十一日，八百一十二个账号里，有二百七十四个超过七天没有更新。"),
    (174.90, 186.08, "停更的账号，中位只发了三条视频；还在更新的，中位发了十五条。而两者的单条播放差不多，三百六十二对三百零四。"),
    (186.40, 199.07, "极少的收益和停更的动力，二者互为成因。而每做一条都要花钱：接口、算力、素材。在过千粉之前，收益是零。"),
    (199.40, 203.94, "在面临断供的风险中，停更成了最优的选择。"),
    (206.10, 213.80, "AI 做内容，理论上可以比人做得更好。但前提是，有人明确告诉它要做什么。"),
    (214.20, 221.95, "八百三十九个账号里，用专门调整过的 skill 或提示词的不到二十个；其余的，都在跑同一套通用模板。"),
    (222.35, 231.00, "四百四十七个时间点，同一分钟里有三条以上视频发布；中位时长六十八秒，四成的不到一分钟。"),
    (231.40, 234.90, "同一把锤子，锤不出不同的东西。"),
    (237.00, 245.00, "收入只有两条路：创作激励，和 UP 主推荐广告。没有代运营，没有卖课。"),
    (245.40, 253.40, "而创作激励要求粉丝过千。新号在过千之前，所有播放都是无效播放。"),
    (253.80, 261.70, "按二十到四十元每万播放算，一条中位视频的收益是三角到六角。而生成它，要花一到三元。"),
    (263.55, 267.41, "这门生意的门槛，是交足够的学费。"),
    (268.90, 276.34, "这个赛道现在同时具备三个特征：供给衰退、分配极端、退出加速。"),
    (276.70, 283.71, "它不会崩，因为它本来就不靠内容赚钱；它也不会变大，因为注意力没有增加。"),
    (284.10, 292.50, "真正被消耗的是观众的信任。当模板化的内容铺满推荐位，愿意认真做的人会先离开。"),
    (292.90, 299.09, "至于那些想让 agent 自力更生的人——这条路，在算术上就不成立。"),
    (301.80, 312.58, "顺带一提，制作这条视频一共花了三十五块一毛八：十四块零九分是数据工具，二十一块一毛五是视频制作和数据分析。"),
]


def mp3_duration(path: Path) -> float:
    with av.open(str(path)) as c:
        return float(c.duration) / 1e6


async def synth(text: str, out: Path, rate: str) -> None:
    last = None
    for attempt in range(4):
        try:
            await edge_tts.Communicate(text, VOICE, rate=rate).save(str(out))
            if out.exists() and out.stat().st_size > 1000:
                return
        except Exception as e:      # 网络抖动 / 空音频
            last = e
        await asyncio.sleep(1.5 + attempt)
    raise RuntimeError(f"TTS 失败: {last}")


def make_line(i: int, start: float, end: float, text: str) -> dict:
    """永远 +0% 语速；窗口只用于对位，不用于压缩语音。"""
    out = WORK / f"l{i:02d}.mp3"
    asyncio.run(synth(text, out, "+0%"))   # 固定原速，永不变速
    d = mp3_duration(out)
    flag = "OK" if start + d <= end + 0.05 else "OVER"
    return {"i": i, "start": start, "end": end, "text": text,
            "rate": "+0%", "dur": round(d, 2), "flag": flag}


def build_music() -> Path:
    """按需要的时长把曲子循环拼够，拼接处 2 秒交叉淡化。"""
    music = WORK / "music.wav"
    with av.open(str(MUSIC_SRC)) as c:
        src = float(c.duration) / 1e6
    need = DUR + 4.0
    n = max(1, int((need - 1) // max(1.0, src - 2.0)) + 1)
    n = min(n, 6)
    ins = []
    for _ in range(n):
        ins += ["-i", str(MUSIC_SRC)]
    if n == 1:
        chain = f"[0:a]atrim=0:{DUR},asetpts=PTS-STARTPTS"
    else:
        parts = []
        prev = "[0:a]"
        for i in range(1, n):
            out = f"[x{i}]"
            parts.append(f"{prev}[{i}:a]acrossfade=d=2:c1=tri:c2=tri{out}")
            prev = out
        chain = ";".join(parts) + f";{prev}atrim=0:{DUR},asetpts=PTS-STARTPTS"
    subprocess.run([studio.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
                    *ins, "-filter_complex",
                    f"{chain},afade=t=in:st=0:d=1.2,afade=t=out:st={DUR-2.2}:d=2.0,"
                    "aresample=48000,aformat=channel_layouts=stereo[a]",
                    "-map", "[a]", str(music)], check=True)
    print(f"  音乐：{src:.0f}s × {n} 次拼接")
    return music


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    print("生成语音…")
    rows = [make_line(i, s, e, t) for i, (s, e, t) in enumerate(LINES, 1)]
    for r in rows:
        flag = "OK " if r["dur"] <= (r["end"] - r["start"]) else "LONG"
        print(f'  [{flag}] #{r["i"]:02d} {r["start"]:5.2f}-{r["end"]:5.2f} '
              f'({r["end"]-r["start"]:4.2f}s窗口) 实际 {r["dur"]:4.2f}s {r["rate"]}')
    (WORK / "lines.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    music = build_music()
    print("混音…")

    inputs = ["-i", str(VIDEO)]
    for r in rows:
        inputs += ["-i", str(WORK / f'l{r["i"]:02d}.mp3')]
    inputs += ["-i", str(music)]
    music_idx = len(rows) + 1

    parts = []
    for r in rows:
        ms = int(r["start"] * 1000)
        parts.append(f'[{r["i"]}:a]adelay={ms}|{ms},aresample=48000[a{r["i"]}]')
    mix_in = "".join(f'[a{r["i"]}]' for r in rows)
    parts.append(f"{mix_in}amix=inputs={len(rows)}:normalize=0,volume=1.0,"
                 f"apad=whole_dur={DUR}[voice]")
    parts.append("[voice]asplit=2[v1][v2]")
    parts.append(f'[{music_idx}:a]volume=0.30[bed]')
    parts.append("[bed][v1]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=450[duck]")
    parts.append("[duck][v2]amix=inputs=2:normalize=0,alimiter=limit=0.94,apad[aout]")

    cmd = [studio.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", *inputs,
           "-filter_complex", ";".join(parts),
           "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
           "-c:a", "aac", "-b:a", "192k", "-ac", "2",
           "-t", f"{DUR}", str(OUT)]
    subprocess.run(cmd, check=True)
    p = studio.probe(str(OUT))
    print("完成:", OUT.name, p["duration"], "s", round(p["bytes"] / 1048576, 1), "MB")


if __name__ == "__main__":
    main()
