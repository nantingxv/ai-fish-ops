# 好多鱼？！：B 站「AI 运营账号」19 天复盘

一部 5 分 14 秒的数据分析视频，以及生成它的全部代码与数据。

**成片**：[video/haoduoyu_bilibili.mp4](video/haoduoyu_bilibili.mp4)

> 2026 年 10 月 8 日到 11 月 11 日，839 个账号在 B 站发布了超过一万条视频。
> 本片统计了它们的开号时间、发布量、播放量、互动率与停更情况，
> 试图回答一个问题：为什么大部分人进来之后就没再更新了。

---

## 结论速览

| 指标 | 数值 |
|---|---|
| 统计账号 | 839 |
| 视频总数 | 10,664 |
| 累计播放 | 3,728 万 |
| 播放集中度 | 前 10 个账号占 55.8%（Gini 0.905） |
| 单条中位播放 | 161 |
| 7 天存活率 | 66.3%（八天掉 25 个百分点） |
| 停更账号中位发布量 | 3 条（在更账号 15 条） |
| 互动率 | 点赞 12.2% / 投币 2.7% / 收藏 1.7% |

核心判断：**供给无限、分配极端、退出加速**。赛道不靠内容赚钱（创作激励门槛为 1000 粉），
单条视频收益 0.3–0.6 元，成本 1–3 元，于是「停更」成为理性选择。

---

## 目录结构

```
├─ video/          成片（1920×1080 / 30fps / AAC）
├─ cover/          封面（1920×1080 与 B 站 1146×717）
├─ docs/
│  ├─ 文案.md       42 句旁白，含每句起止时间
│  ├─ 制作计划.md    分镜与章节设计
│  ├─ 数据说明.md    口径、字段、已知偏差
│  └─ 简介.txt      B 站投稿简介原稿
├─ data/
│  ├─ video.csv     10,664 条视频（bvid、账号、发布时间、播放、点赞等）
│  ├─ account.csv   839 个账号（开号时间、视频数、总播放）
│  └─ account_day.csv  账号 × 日期 明细
└─ src/
   ├─ studio.py     绘图 / 渲染 / 探测 工具库
   ├─ compose.py    把 15 段 alpha 素材按时间轴合成
   ├─ voiceover.py  edge-tts 配音 + BGM 混音
   ├─ projects/     每个片段一个 build.py（逐帧绘制）
   └─ full_spec.json 时间轴
```

---

## 怎么复现

**依赖**：Python 3.11+、ffmpeg（含 libx264 与 prores_ks）

```bash
pip install -r requirements.txt
```

**渲染单个片段**（输出 ProRes 4444 带 alpha 的 .mov）：

```bash
cd src
python projects/008-axis/build.py
```

**预览某一帧**：

```bash
python projects/008-axis/build.py --frame 12.0 preview.png
```

**合成全片**（需要先渲染所有片段）：

```bash
python compose.py projects/full_spec.json
```

**配音与混音**（需要联网，使用 edge-tts）：

```bash
python voiceover.py
```

> 渲染管线：PIL 逐帧绘制 → RGBA 原始帧 → ProRes 4444（yuva444p12le）→
> 最后一次性合成背景与前景，避免背景被反复编码。

---

## 数据说明

- 数据为**人工逐条录入**，非官方接口，名单存在缺漏，总量整体偏低，仅用于相对比较。
- 截止日期 2026-11-11。
- 「停更」定义为超过 7 天未更新。
- 剔除 3 个非 AI 内容账号（暮之鸣、一支小馋猫、lmlmlmlmzh）后为 839 个。
- 详见 [docs/数据说明.md](docs/数据说明.md)。

---

## 制作成本

| 项 | 金额 |
|---|---|
| 数据获取工具 | 14.09 元 |
| 视频制作与数据分析 | 21.15 元 |
| **合计** | **35.18 元** |

---

## 音乐

C418 – *Wait*（Minecraft Volume Beta）。非商业用途，仅作背景音乐。

## 许可

代码 MIT；数据与成片 CC BY-NC 4.0。

---

## 关于路径

仓库里的脚本沿用制作时的绝对路径（D:\tmp\export、D:\tmp\studio\libs），复现前需要按本地环境调整两处：

- 数据目录：src/projects/*/build.py 顶部的 EXPORT
- 第三方库目录：sys.path.insert(... "libs")

成片的分段渲染与合成逻辑（studio.py / compose.py / voiceover.py）与路径无关。

## 已知问题

- 音轨中 BGM 为 C418 的 Wait，若仓库用于商业用途请自行替换。
- data/ 中的播放量为 2026-11-11 快照，随平台数据变化会与当前现实产生偏差。
- 视频内嵌字体为微软雅黑（Windows 授权字体），仓库不包含该字体文件。
- 封面中的人物立绘由 AI 生成，源文件见 cover/characters.png。
