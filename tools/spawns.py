#!/usr/bin/env python3
"""Shashka spawns for a mission: where a sheath (with the shashka in it) may stand - on the floor under the painting
of charging soldiers that hangs in some village houses (wallboards\\picture_g and picture_g_02, one texture).

    python3 -I tools/find_proxies.py picture_g build/pictures_g.json       # once: where the paintings hang
    python3 -I tools/spawns.py <mission folder>

The painting's model has its origin on the floor right under the picture, flat on the wall (its box: 0.66-1.34 m
up, 1.7 cm deep), so each proxy position is the floor spot under a painting in the house's model coordinates; it
faces its proxy's +Z, the room's side (seen in game). Every house of those types in the mission's mapgrouppos.xml
gives a world spot: house position + the point turned by the house's yaw (the third rpy value; checked in game
against ModelToWorld to 7 mm).

The economy can't place it there: its containers ignore a category of their own, and with "weapons" the sheath
went into the houses' ordinary weapon containers. So the mod spawns them itself (SK_Spawner.c, numbers in
shashka.json); this writes what it needs into the mission:
    shashka/spots.json        {"Spots": [{"Pos": [x, y, z], "Wall": [dx, 0, dz]}, ...]} - the floor spot and the
                              way to the wall (the sheath leans back on it)
    shashka/types.xml         SK_Sheath, SK_Shashka at nominal 0: the economy knows their lifetime, spawns none
    cfgeconomycore.xml        + <ce folder="shashka"> listing types.xml
and takes out what earlier versions put into mapgroupproto.xml / cfglimitsdefinition.xml.
"""
import argparse
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PICTURES = ROOT / "build/pictures_g.json"
# village houses and stores with the painting (not the military guardhouses, the town block or Livonia's ruins)
HOUSES = ["House_1W05", "House_1W06", "House_2B03", "House_2W02", "Village_Store", "Village_Store_Enoch",
          "House_1W13_Dam"]
MARK = "<!-- shashka -->"             # what earlier versions wrote into mapgroupproto.xml, taken out again
OFF_WALL = 0.20                        # metres off the wall: room for the sheath to lean back on it


def has_group(s: str, group: str) -> bool:
    return re.search(r'<group name="%s"' % re.escape(group), s) is not None


def spawn_points(mapgroup: str):
    data = json.loads(PICTURES.read_text())
    out = {}
    for model, hits in data.items():
        name = model.split("\\")[-1][:-4]
        if name not in HOUSES:
            continue
        group = "Land_" + name
        if not has_group(mapgroup, group):
            continue
        pts = []
        for h in hits:
            x, y, z = h["pos"]
            dx, dz = h["dir"][0], h["dir"][2]
            n = math.hypot(dx, dz) or 1.0
            dx, dz = dx / n, dz / n
            sgn = 1                         # the painting faces its +Z (dir): the room is on that side
            p = (round(x + sgn * dx * OFF_WALL, 3), round(y, 3), round(z + sgn * dz * OFF_WALL, 3),
                 round(-sgn * dx, 4), round(-sgn * dz, 4))               # + the way to the wall, model axes
            if p not in pts:
                pts.append(p)
        out[group] = pts
    return out


def world_spots(m: Path, points: dict):
    """every house of those types in mapgrouppos.xml: its spot in world coordinates and the painting's yaw"""
    out = []
    for line in (m / "mapgrouppos.xml").read_text().splitlines():
        g = re.search(r'<group name="([^"]+)" pos="([^"]+)" rpy="([^"]+)"', line)
        if not g or g.group(1) not in points:
            continue
        px, py, pz = (float(c) for c in g.group(2).split())
        yaw = float(g.group(3).split()[2])
        t = math.radians(yaw)
        c, s_ = math.cos(t), math.sin(t)
        for x, y, z, wx, wz in points[g.group(1)]:
            out.append({"Pos": [round(px + x * c + z * s_, 3), round(py + y, 3), round(pz - x * s_ + z * c, 3)],
                        "Wall": [round(wx * c + wz * s_, 4), 0, round(-wx * s_ + wz * c, 4)]})
    return out


def clean_old(m: Path):
    f = m / "mapgroupproto.xml"
    s = f.read_text()
    s2 = re.sub(r"\s*" + re.escape(MARK) + r".*?" + re.escape(MARK), "", s, flags=re.S)
    if s2 != s:
        f.write_text(s2)
    f = m / "cfglimitsdefinition.xml"
    s = f.read_text()
    s2 = s.replace('    <category name="shashka"/>\n', "").replace('    <tag name="shashka"/>\n', "")
    if s2 != s:
        f.write_text(s2)


def write_files(m: Path, spots: list):
    d = m / "shashka"
    d.mkdir(exist_ok=True)
    for old in ("spawnabletypes.xml", "types_shashka.xml"):
        (d / old).unlink(missing_ok=True)
    (d / "spots.json").write_text(json.dumps({"Spots": spots}, indent=1))
    flags = '<flags count_in_cargo="0" count_in_hoarder="0" count_in_map="1" count_in_player="0" crafted="0" deloot="0"/>'
    types = "".join(f'''
    <type name="{t}">
        <nominal>0</nominal>
        <lifetime>14400</lifetime>
        <restock>0</restock>
        <min>0</min>
        <quantmin>-1</quantmin>
        <quantmax>-1</quantmax>
        <cost>100</cost>
        {flags}
        <category name="weapons"/>
    </type>''' for t in ("SK_Sheath", "SK_Shashka"))
    (d / "types.xml").write_text('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n<!-- spawned by the mod (SK_Spawner.c), not the economy: nominal 0, the lifetime is what counts -->\n<types>' + types + "\n</types>\n")
    f = m / "cfgeconomycore.xml"
    s = re.sub(r'\s*<ce folder="shashka">.*?</ce>', "", f.read_text(), flags=re.S)
    s = s.replace("</economycore>", '    <ce folder="shashka">\n        <file name="types.xml" type="types" />\n    </ce>\n</economycore>')
    f.write_text(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mission")
    a = ap.parse_args()
    m = Path(a.mission)
    clean_old(m)
    pts = spawn_points((m / "mapgroupproto.xml").read_text())
    spots = world_spots(m, pts)
    write_files(m, spots)
    print(f"{m.name}: {len(spots)} spots under paintings in {len(pts)} house types")


if __name__ == "__main__":
    main()
