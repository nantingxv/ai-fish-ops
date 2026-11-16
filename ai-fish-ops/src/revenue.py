# -*- coding: utf-8 -*-
import csv
from collections import defaultdict

import numpy as np

rows = list(csv.DictReader(open(r"D:\tmp\export\video.csv", encoding="utf-8")))
seen, acc = set(), defaultdict(float)
cnt = defaultdict(int)
for r in rows:
    if r["bvid"] in seen:
        continue
    seen.add(r["bvid"])
    acc[r["account_id"]] += float(r["view"] or 0)
    cnt[r["account_id"]] += 1

v = np.sort(np.array(list(acc.values())))
n = len(v)
print("账号", n, "总播放", int(v.sum()))
for th in (1000, 5000, 10000, 50000, 100000, 1000000):
    k = int((v < th).sum())
    print("  总播放 < %8d 的账号: %3d (%4.1f%%)" % (th, k, 100.0 * k / n))
print("中位账号播放", int(np.median(v)), " 均值", int(v.mean()))
# 按 20-40 元/万有效播放估算，一条中位视频(161 播放)的收益
for rate in (20, 30, 40):
    print("  按 %d 元/万播放：中位视频 161 播放 ≈ %.2f 元" % (rate, 161 * rate / 10000.0))
