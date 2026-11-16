# -*- coding: utf-8 -*-
import csv
from collections import Counter, defaultdict
from datetime import datetime

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
print("样本", len(vids), "条视频")

titles = Counter(v["title"].strip() for v in vids)
dup = {k: c for k, c in titles.items() if c >= 3}
print("完全同名标题(>=3次)", len(dup), "共覆盖", sum(dup.values()), "条")
for k, c in sorted(dup.items(), key=lambda x: -x[1])[:8]:
    print("  %2d 次  %s" % (c, k[:36]))

mins = Counter(v["_t"].strftime("%Y-%m-%d %H:%M") for v in vids)
clust = [c for c in mins.values() if c >= 3]
print("同一分钟发>=3条的时刻", len(clust), "涉及视频", sum(clust))

acct_day = defaultdict(int)
for v in vids:
    acct_day[(v["account_id"], v["_t"].strftime("%m-%d"))] += 1
multi = [c for c in acct_day.values() if c >= 5]
print("单账号单日发>=5条的次数", len(multi), "最多", max(acct_day.values()) if acct_day else 0)

durs = [int(v["duration_sec"]) for v in vids if v["duration_sec"]]
durs.sort()
if durs:
    n = len(durs)
    print("时长 中位 %ds  25%%-%ds  75%%-%ds  最长 %ds" % (
        durs[n // 2], durs[n // 4], durs[3 * n // 4], durs[-1]))
    short = sum(1 for d in durs if d <= 60)
    print("<=60 秒的占比 %.0f%%" % (100.0 * short / n))
