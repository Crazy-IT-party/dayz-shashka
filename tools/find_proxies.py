#!/usr/bin/env python3
"""Which vanilla buildings carry a given furniture proxy, and where: scans every structures_*.pbo model (binarised
ODOL) for proxies whose path contains a word (default "carpet"; "picture_g" for the painting of charging soldiers). An ODOL proxy is: asciiz model path, a 4x3 transform (3 axis columns + position, floats), then
ints. Writes build/carpets.json: {model path: [{proxy, pos, up, dir, aside}]} in the model's own coordinates.

    python3 -I tools/find_carpets.py [word] [out.json]
"""
import json
import os
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pbo_extract import parse, data_of  # noqa: E402

if not os.environ.get("DAYZ_SERVER"):
    sys.exit("set DAYZ_SERVER to the DayZ server (or client) folder")
ADDONS = Path(os.environ["DAYZ_SERVER"]) / ("addons" if (Path(os.environ["DAYZ_SERVER"]) / "addons").is_dir() else "Addons")
WORD = sys.argv[1] if len(sys.argv) > 1 else "carpet"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "build/carpets.json"
PAT = re.compile(rb"[\x20-\x7e]*" + re.escape(WORD.encode()) + rb"[\x20-\x7e]*\x00", re.I)

found = {}
for pbo in sorted(ADDONS.glob("structures_*.pbo")):
    b, props, entries = parse(str(pbo))
    prefix = props.get("prefix", "")
    for e in entries:
        if not e[0].lower().endswith(".p3d") or "furniture" in pbo.name:
            continue
        d = data_of(b, e)
        if d[:4] != b"ODOL" or WORD.encode().lower() not in d.lower():
            continue
        hits = []
        for m in PAT.finditer(d):
            name = m.group()[:-1].decode("latin1")
            if name.lower().endswith((".paa", ".rvmat")):
                continue
            at = m.end()
            if at + 48 > len(d):
                continue
            f = struct.unpack_from("<12f", d, at)
            ax, up, dr, pos = f[0:3], f[3:6], f[6:9], f[9:12]
            norms = [sum(c * c for c in v) ** 0.5 for v in (ax, up, dr)]
            if not all(0.5 < n < 2.0 for n in norms) or not all(abs(c) < 100 for c in pos):
                continue
            hits.append({"proxy": name, "pos": [round(c, 3) for c in pos], "aside": [round(c, 3) for c in ax],
                         "up": [round(c, 3) for c in up], "dir": [round(c, 3) for c in dr]})
        if hits:
            found[prefix + "\\" + e[0]] = hits
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(found, indent=1))
for k, v in found.items():
    print(f"{len(v):3}  {k}  {sorted(set(h['proxy'].split(chr(92))[-1] for h in v))}")
