# -*- coding: utf-8 -*-
import csv
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np

D0 = datetime.fromisoformat("2026-10-08T00:00:00+08:00")
rows = list(csv.DictReader(open(r"D:\tmp\export\video.csv", encoding="utf-8")))
seen, vids = set(), []
for r in rows:
    if r["bvid"] in seen:
        continue
    seen.add(r["bvid"])
    t = datetime.fromisoformat(r["pub_time"])
    if t.year != 2026 or t < D0:
        continue
    r["_t"] = t
    vids.append(r)

print("2026-10-08 起视频数", len(vids))
bygroup = defaultdict(list)
for v in vids:
    bygroup[(v["_t"] - D0).days // 5].append(v)

print("\n组  日期范围          视频数   中位24h   中位累计   top10%份额")
for k in sorted(bygroup):
    g = bygroup[k]
    t0 = D0 + timedelta(days=k * 5)
    t1 = t0 + timedelta(days=4)
    v24 = [float(x["view_24h"]) for x in g if x["view_24h"]]
    vv = np.sort([float(x["view"]) for x in g if x["view"]])
    top = vv[-max(1, len(vv) // 10):].sum() / vv.sum() if len(vv) else 0
    m24 = int(np.median(v24)) if v24 else 0
    mv = int(np.median(vv)) if len(vv) else 0
    print("%2d  %s~%s  %6d  %8d  %9d  %6.2f"
          % (k, t0.strftime("%m-%d"), t1.strftime("%m-%d"), len(g), m24, mv, top))
