# -*- coding: utf-8 -*-
import csv
from collections import defaultdict

import numpy as np

rows = list(csv.DictReader(open(r"D:\tmp\export\video.csv", encoding="utf-8")))
seen, by_acc = set(), defaultdict(list)
for r in rows:
    if r["bvid"] in seen:
        continue
    seen.add(r["bvid"])
    r["view"] = float(r["view"] or 0)
    by_acc[r["account_id"]].append(r)

rank = sorted(by_acc.items(), key=lambda kv: -sum(v["view"] for v in kv[1]))
tot = sum(sum(v["view"] for v in vs) for _, vs in rank)

print("名次  账号                    条数   总播放     中位播放   top1 视频")
for i, (aid, vs) in enumerate(rank[:15], 1):
    tot_v = sum(v["view"] for v in vs)
    med = int(np.median([v["view"] for v in vs]))
    top = max(vs, key=lambda v: v["view"])
    print("%2d  %-22s %3d  %9.0f  %8d   %s (%d万)"
          % (i, vs[0]["account_name"][:22], len(vs), tot_v, med,
             top["title"][:26], round(top["view"] / 10000)))
    for v in sorted(vs, key=lambda v: -v["view"])[:2]:
        print("        · %-34s %8.0f  %s" % (v["title"][:34], v["view"], v["bvid"]))
print("\n全部账号", len(rank), "总播放", int(tot))
