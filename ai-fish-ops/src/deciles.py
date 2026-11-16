# -*- coding: utf-8 -*-
import csv
from collections import defaultdict

import numpy as np

rows = list(csv.DictReader(open(r"D:\tmp\export\video.csv", encoding="utf-8")))
seen, acc = set(), defaultdict(float)
for r in rows:
    if r["bvid"] in seen:
        continue
    seen.add(r["bvid"])
    acc[r["account_id"]] += float(r["view"] or 0)
v = np.sort(np.array(list(acc.values())))
cum = np.cumsum(v) / v.sum()
n = len(v)
pts = []
for i in range(11):
    k = min(n - 1, int(round(i / 10 * (n - 1))))
    pts.append((i / 10, float(cum[k])))
print("N", n, "total", int(v.sum()))
print("lorenz", [(round(x, 2), round(y, 3)) for x, y in pts])
print("top8 share", round(float(v[-8:].sum() / v.sum()), 3))
print("median", int(np.median(v)))

# 队列：按开号周的中位播放
accts = list(csv.DictReader(open(r"D:\tmp\export\account.csv", encoding="utf-8")))
buckets = defaultdict(list)
for a in accts:
    t = a["first_pub_time"][:10]
    if t < "2026-10-01":
        continue
    wk = {"10-08": 0}
    buckets[t[:7] + "/" + str(int(t[8:10]) // 7)].append(float(a["total_view"] or 0) / max(1, int(a["video_count"] or 1)))
print("cohort median view/video:")
for k in sorted(buckets):
    arr = np.array(buckets[k])
    print(" ", k, len(arr), int(np.median(arr)))
