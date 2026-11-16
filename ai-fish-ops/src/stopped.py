# -*- coding: utf-8 -*-
import csv
from datetime import datetime

import numpy as np

DROP = {"暮之鸣", "一支小馋猫", "lmlmlmlmzh"}
ACC = []
with open(r"D:\tmp\export\account.csv", encoding="utf-8") as f:
    for a in csv.DictReader(f):
        if a["account_name"] in DROP:
            continue
        ACC.append(a)

CUT = datetime.fromisoformat("2026-11-04T00:00:00+08:00")
stopped, active = [], []
for a in ACC:
    last = datetime.fromisoformat(a["last_pub_time"])
    v = float(a["total_view"] or 0)
    c = int(a["video_count"] or 1)
    (stopped if last < CUT else active).append((v, c, v / max(1, c)))

for name, arr in (("停更", stopped), ("在更", active)):
    if not arr:
        continue
    vs = np.array([x[0] for x in arr])
    cs = np.array([x[1] for x in arr])
    ps = np.array([x[2] for x in arr])
    print("%s 账号 %3d  中位总播放 %7d  中位条数 %2d  中位单条播放 %6d"
          % (name, len(arr), int(np.median(vs)), int(np.median(cs)), int(np.median(ps))))

print("停更占比 %.1f%%" % (100.0 * len(stopped) / max(1, len(ACC))))
