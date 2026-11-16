# -*- coding: utf-8 -*-
import csv
from datetime import datetime

import numpy as np

rows = list(csv.DictReader(open(r"D:\tmp\export\video.csv", encoding="utf-8")))
seen, vids = set(), []
for r in rows:
    if r["bvid"] in seen:
        continue
    seen.add(r["bvid"])
    t = datetime.fromisoformat(r["pub_time"])
    if t < datetime.fromisoformat("2026-10-08T00:00:00+08:00"):
        continue
    r["_t"] = t
    vids.append(r)

def rate(field):
    out = []
    for v in vids:
        try:
            view = float(v["view"] or 0)
            val = float(v[field] or 0)
        except Exception:
            continue
        if view >= 100:          # 只看有基本曝光的
            out.append(val / view)
    return np.array(out)

for f_, name in (("like", "点赞"), ("coin", "投币"), ("favorite", "收藏"), ("reply", "评论")):
    a = rate(f_)
    if len(a) == 0:
        continue
    print("%s/播放  样本 %4d  中位 %.2f%%  均值 %.2f%%  超过4%%的比例 %.1f%%"
          % (name, len(a), 100 * np.median(a), 100 * a.mean(), 100 * (a > 0.04).mean()))

# 播放越高，互动率是否更高？
vids2 = [v for v in vids if float(v["view"] or 0) >= 100]
vids2.sort(key=lambda v: -float(v["view"]))
k = len(vids2) // 4
for i, label in enumerate(("前25%（高播放）", "25-50%", "50-75%", "后25%（低播放）")):
    seg = vids2[i * k:(i + 1) * k]
    r = np.array([float(v["like"] or 0) / float(v["view"]) for v in seg])
    print("%s  点赞率中位 %.2f%%" % (label, 100 * np.median(r)))
