# -*- coding: utf-8 -*-
import csv
from collections import defaultdict

import numpy as np

DROP = {"暮之鸣", "一支小馋猫", "lmlmlmlmzh"}

rows = list(csv.DictReader(open(r"D:\tmp\export\video.csv", encoding="utf-8")))
seen, by_acc = set(), defaultdict(list)
for r in rows:
    if r["bvid"] in seen:
        continue
    seen.add(r["bvid"])
    if r["account_name"] in DROP:
        continue
    r["view"] = float(r["view"] or 0)
    by_acc[r["account_id"]].append(r)

rank = sorted(by_acc.items(), key=lambda kv: -sum(v["view"] for v in kv[1]))
tot = sum(sum(v["view"] for v in vs) for _, vs in rank)
nvid = sum(len(vs) for _, vs in rank)
print("剩余账号", len(rank), "视频", nvid, "总播放", int(tot))
for k in (5, 10, 20):
    s = sum(sum(v["view"] for v in vs) for _, vs in rank[:k])
    print("top%-2d 占 %.1f%%" % (k, 100 * s / tot))

print("\n新的 top10：")
for i, (aid, vs) in enumerate(rank[:10], 1):
    tv = sum(v["view"] for v in vs)
    med = int(np.median([v["view"] for v in vs]))
    print("%2d  %-20s %3d 条  %9.0f 播放  中位 %7d  %5.1f%%"
          % (i, vs[0]["account_name"][:20], len(vs), tv, med, 100 * tv / tot))
