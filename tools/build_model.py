#!/usr/bin/env python3
"""The shashka model, textures and damage materials, made here (no Object Builder, no Binarize).

    python3 -I tools/build_model.py            -> mod/Shashka/data/{shashka.p3d, *.paa, *.rvmat} + build/preview.png

Layout copied from the vanilla Machete (its memory points and bounding box, measured in game):
origin at the hand grip, +Y towards the tip, the blade's width along X (edge +X, spine -X), its thickness
along Z, the inventory camera ("invview") on -Z. The machete reaches 0.40 m; the shashka 0.885 m.

A Cossack shashka: no guard, a slightly curved single-edged blade with a fuller near the spine and a clipped
point, a silver-and-niello grip and ferrule, and the pommel bent back towards the spine in the
characteristic split "head".

Written unbinarised (MLOD), which the engine loads from a pbo.
The engine reads an MLOD turned 180 degrees about Y (the probe got every memory point back with x and z negated),
so points and normals are written turned the other way and land where they are built here.
Levels: the visible one (1.0), geometry (1e13: convex boxes with mass) and memory (1e15: the named points the
engine and the melee code look up). Faces are built counter-clockwise seen from outside and flipped on write,
since MLOD wants them clockwise with inward normals. Normals are smoothed per group: along the length within a
blade facet, all round the grip, never across a facet edge.

Damage states (config healthLevels swap the two materials): normal (pristine + worn), damaged, badly damaged,
ruined - the vanilla way, the same colour textures with a darker detail map and a damage macro (MC) on top,
all three macros our own: tarnish (damaged), rust (badly damaged), heavy rust (ruined).
"""
from __future__ import annotations

import math
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "mod/Shashka/data"
BUILD = ROOT / "build"
PFX = "shashka\\data\\"
ARMAKE = os.environ.get("ARMAKE2") or shutil.which("armake2") or "armake2"   # rapifies the rvmats

# ---- dimensions (metres) ------------------------------------------------------------------------------------
GRIP0, GRIP1 = -0.072, 0.066        # leather grip
FERR1 = 0.084                        # top of the ferrule, where the blade comes out
TIP = 0.885                          # point of the blade
CURVE = 0.042                        # how far the spine has bent back (-X) at the tip
W0, W1 = 0.035, 0.029                # blade width at the ferrule and before the point
T0, T1 = 0.0075, 0.0035              # blade thickness at the spine, base and near the point
CLIP = 0.88                          # fraction of the blade where the point starts
MASS = 0.85                          # kg

TEX_SHEATH = PFX + "shashka_sheath_co.paa"
MAT_SHEATH = PFX + "shashka_sheath.rvmat"
TEX_BLADE = PFX + "shashka_blade_co.paa"
TEX_HILT = PFX + "shashka_hilt_co.paa"
MAT_BLADE = PFX + "shashka_blade.rvmat"
MAT_HILT = PFX + "shashka_hilt.rvmat"


# ---- mesh ---------------------------------------------------------------------------------------------------
class Mesh:
    def __init__(self):
        self.pts: list[tuple[float, float, float]] = []
        self.faces: list[dict] = []      # {"idx", "uv", "tex", "mat", "group"}
        self.sel: dict[str, set[int]] = {}
        self.track: str | None = None             # points made while set go into that named selection

    def pt(self, p) -> int:
        self.pts.append((float(p[0]), float(p[1]), float(p[2])))
        if self.track:
            self.sel.setdefault(self.track, set()).add(len(self.pts) - 1)
        return len(self.pts) - 1

    def face(self, idx, uv, tex, mat, group, outward_hint=None):
        """idx counter-clockwise seen from outside; with outward_hint (a point inside) the order is fixed up"""
        if outward_hint is not None:
            P = np.array([self.pts[i] for i in idx])
            n = np.cross(P[1] - P[0], P[2] - P[0])
            if len(idx) == 4:
                n = n + np.cross(P[2] - P[0], P[3] - P[0])
            if np.dot(n, P.mean(0) - np.asarray(outward_hint)) < 0:
                idx, uv = idx[::-1], uv[::-1]
        self.faces.append({"idx": list(idx), "uv": list(uv), "tex": tex, "mat": mat, "group": group})
        return len(self.faces) - 1

    def normal(self, f) -> np.ndarray:
        P = np.array([self.pts[i] for i in f["idx"]])
        n = np.cross(P[1] - P[0], P[2] - P[0])
        if len(P) == 4:
            n = n + np.cross(P[2] - P[0], P[3] - P[0])
        return n                                   # area weighted, outward


def write_mlod(lods) -> bytes:
    """lods: [(resolution, Mesh, properties, masses or None)]"""
    out = [b"MLOD", struct.pack("<II", 0x101, len(lods))]
    for res, m, props, mass in lods:
        # one normal per (point, smoothing group): the sum of the group's face normals at that point
        acc: dict[tuple[int, str], np.ndarray] = {}
        fn = [m.normal(f) for f in m.faces]
        for f, n in zip(m.faces, fn):
            for i in f["idx"]:
                acc[(i, f["group"])] = acc.get((i, f["group"]), 0) + n
        keys = list(acc)
        nidx = {k: j for j, k in enumerate(keys)}
        out.append(b"P3DM" + struct.pack("<IIIIII", 0x1C, 0x100, len(m.pts), len(keys), len(m.faces), 0))
        for x, y, z in m.pts:                                       # the engine turns an MLOD 180 deg about Y
            out.append(struct.pack("<fffI", -x, y, -z, 0))
        for k in keys:
            n = acc[k]
            n = n / max(np.linalg.norm(n), 1e-12)
            out.append(struct.pack("<fff", n[0], -n[1], n[2]))         # stored inward, turned as the points
        for f in m.faces:
            idx, uv = f["idx"][::-1], f["uv"][::-1]                    # clockwise seen from outside
            out.append(struct.pack("<I", len(idx)))
            for k in range(4):
                if k < len(idx):
                    out.append(struct.pack("<IIff", idx[k], nidx[(idx[k], f["group"])], uv[k][0], uv[k][1]))
                else:
                    out.append(struct.pack("<IIff", 0, 0, 0.0, 0.0))
            out.append(struct.pack("<I", 0) + f["tex"].encode("latin1") + b"\0" + f["mat"].encode("latin1") + b"\0")
        out.append(b"TAGG")

        def tagg(name, data):
            out.append(b"\x01" + name.encode("latin1") + b"\0" + struct.pack("<I", len(data)) + data)
        for k, v in props.items():
            tagg("#Property#", k.encode("latin1").ljust(64, b"\0") + str(v).encode("latin1").ljust(64, b"\0"))
        for name, sel in m.sel.items():
            pm = bytearray(len(m.pts))
            fm = bytearray(len(m.faces))
            for i in sel:
                pm[i] = 1
            for fi, f in enumerate(m.faces):
                if all(i in sel for i in f["idx"]):
                    fm[fi] = 1
            tagg(name, bytes(pm) + bytes(fm))
        if mass is not None:
            tagg("#Mass#", struct.pack(f"<{len(m.pts)}f", *mass))
        tagg("#EndOfFile#", b"")
        out.append(struct.pack("<f", res))
    return b"".join(out)


# ---- the blade ------------------------------------------------------------------------------------------------
def blade_station(s):
    """spine x, width, thickness and centre y at fraction s of the blade (0 = ferrule, 1 = point)"""
    y = FERR1 + (TIP - FERR1) * s
    xs = -W0 / 2 - CURVE * s * s
    w = W0 + (W1 - W0) * min(s / CLIP, 1.0)
    if s > CLIP:                                   # the clipped point: the edge sweeps up to meet the spine
        q = (s - CLIP) / (1 - CLIP)
        w = w * math.sqrt(max(1 - q * q, 0.0))
    t = T0 + (T1 - T0) * s
    if s > CLIP:
        t *= 1 - 0.85 * (s - CLIP) / (1 - CLIP)
    return xs, w, t, y


def blade_ring(s):
    """the cross-section at s: (x, z) points round it, starting at the spine top, counter-clockwise from +Y"""
    xs, w, t, _ = blade_station(s)
    bev = min(0.0075, w * 0.35)
    xe = xs + w
    xm = xs + 0.55 * w
    return [(xs, t / 2), (xm, t * 0.42), (xe - bev, t * 0.30), (xe, 0.0),
            (xe - bev, -t * 0.30), (xm, -t * 0.42), (xs, -t / 2)]


def blade_uv(x, z, s):
    xs, w, _, _ = blade_station(s)
    f = 0.0 if w < 1e-6 else min(max((x - xs) / max(w, 1e-6), 0.0), 1.0)
    u = 0.02 + 0.46 * f if z >= 0 else 0.52 + 0.46 * f
    return (u, 1.0 - s)


def build_blade(m: Mesh):
    N = 48
    ss = [i / N for i in range(N)]
    rings = []
    for s in ss:
        _, _, _, y = blade_station(s)
        rings.append([m.pt((x, y, z)) for x, z in blade_ring(s)])
    tip = m.pt((blade_station(1.0)[0], TIP, 0.0))
    nr = len(rings[0])
    for a in range(N - 1):
        sa, sb = ss[a], ss[a + 1]
        xs, w, _, ya = blade_station((sa + sb) / 2)
        inside = (xs + w * 0.4, (ya + blade_station(sb)[3]) / 2, 0.0)
        for k in range(nr):
            j = (k + 1) % nr
            i0, i1, i2, i3 = rings[a][k], rings[a][j], rings[a + 1][j], rings[a + 1][k]
            zc = (m.pts[i0][2] + m.pts[i1][2]) / 2
            uv = [blade_uv(m.pts[i][0], zc, s) for i, s in ((i0, sa), (i1, sa), (i2, sb), (i3, sb))]
            if j == 0:                                              # the spine's flat back
                uv = [(0.005, 1 - sa), (0.015, 1 - sa), (0.015, 1 - sb), (0.005, 1 - sb)]
            m.face([i0, i1, i2, i3], uv, TEX_BLADE, MAT_BLADE, f"blade{k}", inside)
    last = rings[-1]
    xs, w, _, y = blade_station(ss[-1])
    for k in range(nr):
        j = (k + 1) % nr
        zc = (m.pts[last[k]][2] + m.pts[last[j]][2]) / 2
        uv = [blade_uv(m.pts[last[k]][0], zc, ss[-1]), blade_uv(m.pts[last[j]][0], zc, ss[-1]), (0.25 if zc >= 0 else 0.75, 0.0)]
        m.face([last[k], last[j], tip], uv, TEX_BLADE, MAT_BLADE, f"blade{k}", (xs + w * 0.3, y, 0.0))
    # the base, hidden in the ferrule, closed anyway
    first = rings[0]
    xs, w, _, y = blade_station(0.0)
    for k in range(1, nr - 1):
        m.face([first[0], first[k], first[k + 1]], [(0.01, 0.99)] * 3, TEX_BLADE, MAT_BLADE, "bladebase",
               (xs + w / 2, y + 0.01, 0.0))


# ---- grip, ferrule, pommel: lofted ellipses ---------------------------------------------------------------------
SEG = 20


def loft(m: Mesh, centres, radii, u0, u1, v0, v1, group, cap_start=False, cap_end=False, frame_t=None,
         tex=TEX_HILT, mat=MAT_HILT):
    """rings of SEG points round a path; radii (rx, rz) per ring; uv: u round the ring in [u0,u1], v along"""
    rings = []
    n = len(centres)
    for i, (c, (rx, rz)) in enumerate(zip(centres, radii)):
        if frame_t is not None:
            T = np.asarray(frame_t[i], float)
        else:
            a, b = centres[max(i - 1, 0)], centres[min(i + 1, n - 1)]
            T = np.asarray(b, float) - np.asarray(a, float)
        T = T / np.linalg.norm(T)
        Z = np.array([0.0, 0.0, 1.0])
        X = np.cross(T, Z)
        X = X / np.linalg.norm(X)
        ring = []
        for k in range(SEG):
            ang = 2 * math.pi * k / SEG
            p = np.asarray(c, float) + rx * math.cos(ang) * X + rz * math.sin(ang) * Z
            ring.append(m.pt(p))
        rings.append(ring)
    for i in range(n - 1):
        va = v0 + (v1 - v0) * i / (n - 1)
        vb = v0 + (v1 - v0) * (i + 1) / (n - 1)
        mid = (np.asarray(centres[i]) + np.asarray(centres[i + 1])) / 2
        for k in range(SEG):
            j = (k + 1) % SEG
            ua = u0 + (u1 - u0) * k / SEG
            ub = u0 + (u1 - u0) * (k + 1) / SEG
            m.face([rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]],
                   [(ua, va), (ub, va), (ub, vb), (ua, vb)], tex, mat, group, mid)
    for cap, ring, c, other in ((cap_start, rings[0], centres[0], centres[min(1, n - 1)]),
                                (cap_end, rings[-1], centres[-1], centres[max(n - 2, 0)])):
        if not cap:
            continue
        centre = m.pt(c)
        inside = np.asarray(c, float) + (np.asarray(other, float) - np.asarray(c, float)) * 0.5
        for k in range(SEG):
            j = (k + 1) % SEG
            m.face([ring[k], ring[j], centre], [(u0, v0), (u1, v0), ((u0 + u1) / 2, v0)], tex, mat,
                   group + "cap", inside)
    return rings


def build_hilt(m: Mesh):
    # grip: a slight swell in the middle, oval
    ys = np.linspace(GRIP0, GRIP1, 14)
    cs = [(0.0, y, 0.0) for y in ys]
    rs = []
    for y in ys:
        q = (y - GRIP0) / (GRIP1 - GRIP0)
        rx = 0.0150 + 0.0022 * math.sin(math.pi * q)
        rs.append((rx, rx * 0.80))
    loft(m, cs, rs, 0.0, 0.5, 0.0, 1.0, "grip")
    # ferrule: from round to the blade's flat section
    ys = np.linspace(GRIP1 - 0.004, FERR1, 5)
    cs = [(0.0, y, 0.0) for y in ys]
    rs = []
    for y in ys:
        q = (y - ys[0]) / (ys[-1] - ys[0])
        rs.append((0.0185 - 0.0008 * q, 0.0140 - 0.0085 * q))
    loft(m, cs, rs, 0.5, 0.75, 0.0, 0.5, "ferrule", cap_end=True)
    # pommel: the head bends back towards the spine (-X) and swells into the split cap
    K = 12
    cs, rs, ts = [], [], []
    for i in range(K):
        q = i / (K - 1)
        a = q * 0.75                                               # bend angle, radians
        R = 0.06
        x = -(R - R * math.cos(a))
        y = GRIP0 + 0.004 - R * math.sin(a)
        cs.append((x, y, 0.0))
        ts.append((-math.sin(a), -math.cos(a), 0.0))
        sw = 0.0150 + 0.0060 * math.sin(math.pi * min(q * 1.15, 1.0) * 0.5) ** 2
        if q > 0.82:                                              # rounded end
            sw *= math.sqrt(max(1 - ((q - 0.82) / 0.18) ** 2, 0.08))
        rs.append((sw, sw * 0.82))
    loft(m, cs, rs, 0.75, 1.0, 0.0, 1.0, "pommel", cap_end=True, frame_t=ts)


# ---- the sheath -----------------------------------------------------------------------------------------------
SHEATH0 = FERR1 - 0.004            # the throat, just under the ferrule
SHEATH1 = TIP + 0.028              # the chape's end
MOUNTS = ((0.0, 0.12), (0.19, 0.245), (0.43, 0.485), (0.93, 1.0))   # silver along the sheath (fraction of its
                                                     # length), as on the reference: throat, two bands, chape


DARK_UV = (0.25, 0.6)          # a spot of the sheath texture's leather: the inside of the mouth


def mouth(m: Mesh, ring, centre, lip=0.82, depth=0.03):
    """the throat open, as on a real scabbard: a thin silver rim (the throat mount's top edge), then a dark slot
    going in depth metres with a floor - instead of a flat cap with the texture smeared over it"""
    c = np.asarray(centre, float)
    outer = [np.asarray(m.pts[i]) for i in ring]
    inner = [m.pt(c + lip * (p - c)) for p in outer]
    deep = [m.pt(c + lip * (np.asarray(m.pts[i]) - c) + np.array([0.0, depth, 0.0])) for i in inner]
    n = len(ring)
    for k in range(n):
        j = (k + 1) % n
        u0, u1 = k / n, (k + 1) / n
        m.face([ring[k], ring[j], inner[j], inner[k]], [(u0, 0.004), (u1, 0.004), (u1, 0.012), (u0, 0.012)],
               TEX_SHEATH, MAT_SHEATH, "mouthrim", c + np.array([0.0, 0.01, 0.0]))
        q = (np.asarray(m.pts[inner[k]]) + np.asarray(m.pts[deep[j]])) / 2
        outside = c + 3.0 * (q - c) * np.array([1.0, 0.0, 1.0]) + np.array([0.0, q[1] - c[1], 0.0])
        m.face([inner[k], inner[j], deep[j], deep[k]], [DARK_UV] * 4, TEX_SHEATH, MAT_SHEATH, "mouthwall", outside)
    floor = m.pt(c + np.array([0.0, depth, 0.0]))
    for k in range(n):
        j = (k + 1) % n
        m.face([deep[k], deep[j], floor], [DARK_UV] * 3, TEX_SHEATH, MAT_SHEATH, "mouthfloor",
               c + np.array([0.0, depth + 0.01, 0.0]))


def sheath_grip():
    """the hand's place on the sheath, in the turned model (chape at y 0, hilt up): midway between the two bands
    with the stones"""
    g = (MOUNTS[1][1] + MOUNTS[2][0]) / 2
    y = SHEATH0 + g * (SHEATH1 - SHEATH0)
    cs, _ = sheath_sections()
    c = min(cs, key=lambda p: abs(p[1] - y))
    return -c[0], SHEATH1 - y


def sheath_sections():
    """centres and (rx, rz) of the scabbard's oval rings, throat to chape"""
    # the section follows the blade at every height, the point included (there the blade's middle swings back to
    # the spine): half its width / thickness plus a margin, never less than the throat-to-chape taper; past the
    # tip it closes round
    N = 48
    cs, rs = [], []
    xs_tip = blade_station(1.0)[0]
    for i in range(N + 1):
        q = i / N
        y = SHEATH0 + (SHEATH1 - SHEATH0) * q
        sb = (y - FERR1) / (TIP - FERR1)
        if sb <= 1.0:
            xs, w, t, _ = blade_station(min(max(sb, 0.0), 1.0))
            cx = xs + w / 2
            rx = max(w / 2 + 0.0045, W0 / 2 + 0.0055 - 0.006 * q)
            rz = max(t / 2 + 0.0035, 0.0085 - 0.0025 * q)
            rx = max(rx, w / 2 + 0.0045)
        else:                                              # beyond the tip: the chape's rounded end
            k = (y - TIP) / (SHEATH1 - TIP)
            cx = xs_tip + 0.004
            r0x, r0z = cs and rs[-1] or (0.01, 0.006)
            rx = r0x * math.sqrt(max(1 - k * k, 0.0)) if k < 1 else 0.0005
            rz = r0z * math.sqrt(max(1 - k * k, 0.0)) if k < 1 else 0.0005
        cs.append((cx, y, 0.0))
        rs.append((max(rx, 0.0005), max(rz, 0.0005)))
    return cs, rs


def build_sheath(m: Mesh):
    """leather over a wooden core round the blade's curve, an oval section a little wider than the blade, and the
    proxy for the blade's slot at the shashka's own origin: a sheathed shashka is drawn there, hilt out of the
    throat, blade inside"""
    cs, rs = sheath_sections()
    rings = loft(m, cs, rs, 0.0, 1.0, 0.0, 1.0, "sheath", cap_end=True, tex=TEX_SHEATH, mat=MAT_SHEATH)
    mouth(m, rings[0], cs[0])
    proxy(m, PROXY_SHASHKA)


PROXY_SHASHKA = "\\shashka\\data\\proxy\\sk_shashka"


def proxy(m: Mesh, path: str, index: int = 1):
    """an MLOD proxy: one triangle in a selection named "proxy:<model path>.<index>"; its right-angle corner is the
    position, the long side (2) the model's up (+Y), the short side (1) its forward (+Z). Proxy triangles are taken
    as written, without the 180 degree turn the engine gives the rest of an MLOD; since write_mlod turns every point,
    the identity is built here with the short side on -Z (tried in game: +Z put the blade beside the scabbard)"""
    idx = [m.pt((0.0, 0.0, 0.0)), m.pt((0.0, 2.0, 0.0)), m.pt((0.0, 0.0, -1.0))]
    m.face(idx, [(0, 0), (0, 0), (0, 0)], "", "", "proxy")
    m.sel[f"proxy:{path}.{index:03d}"] = set(idx)


def tex_sheath():
    """u round the sheath, v along it (0 throat .. 1 chape): near-black leather (Leather037's grain) and the
    reference's silver mounts, where they sit on it - the long ornamented throat, two bands with a carnelian set in
    each (rings for the straps), a plain chape"""
    H, W = 1024, 256
    leather, lrough = leather_from(H, W, 61)
    rgb = leather * 0.45                                             # the reference's leather is nearly black
    spec = 0.18 - 0.12 * lrough
    gloss = 0.45 - 0.25 * lrough
    rgb[..., 0] *= 1.1                                               # still brown, just
    for (a_, b_), box, gem in ((MOUNTS[0], (730, 278, 835, 480), None),
                                (MOUNTS[1], (750, 795, 890, 925), (0.5, 0.55, 0.2, 0.17)),
                                (MOUNTS[2], (750, 795, 890, 925), (0.5, 0.55, 0.2, 0.17))):
        r0, r1 = int(a_ * H), int(b_ * H)
        half = ref_crop(box, (W // 2, r1 - r0))
        lum = np.concatenate([half, half], 1)                        # the same face front and back
        m_rgb, m_spec, m_gloss = silver(lum, 62)
        if gem:
            g1, gm = stone(m_rgb[:, :W // 2], half, *gem)
            m_rgb = np.concatenate([g1, g1], 1)
            gm = np.concatenate([gm, gm], 1)
            m_spec = m_spec * (1 - gm) + 0.9 * gm
        rgb[r0:r1], spec[r0:r1], gloss[r0:r1] = m_rgb, m_spec, m_gloss
    r0 = int(MOUNTS[3][0] * H)                                       # the chape: plain silver, worn
    plain = 0.55 + 0.25 * noise(H - r0, W, 24, 63) + 0.15 * tile(np.rot90(photo("Metal009", "Color", (256, 256)).mean(-1)), H - r0, W)
    c_rgb, c_spec, c_gloss = silver(np.clip(plain, 0, 1), 64)
    rgb[r0:], spec[r0:], gloss[r0:] = c_rgb, c_spec, c_gloss
    return to_img(rgb), to_img(np.stack([np.ones_like(spec), spec, gloss], -1))


# ---- geometry and memory levels ----------------------------------------------------------------------------------
def box(m: Mesh, lo, hi, group):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    idx = [m.pt(p) for p in c]
    centre = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)):
        m.face([idx[i] for i in q], [(0, 0)] * 4, "", "", group, centre)
    return set(idx)


def build_geometry(total_mass=MASS) -> tuple[Mesh, list[float]]:
    g = Mesh()
    parts = [((-0.040, -0.115, -0.017), (0.019, FERR1, 0.017))]   # pommel, grip, ferrule
    bounds = [(0.0, 0.34), (0.34, 0.68), (0.68, 1.0)]
    for a, b in bounds:
        xs_a, w_a, _, ya = blade_station(a)
        xs_b, w_b, _, yb = blade_station(b)
        x0 = min(xs_a, xs_b) - 0.001
        x1 = max(xs_a + w_a, xs_b + w_b, xs_a + blade_station((a + b) / 2)[1]) + 0.001
        parts.append(((x0, ya, -0.004), (x1, yb, 0.004)))
    for n, (lo, hi) in enumerate(parts):
        g.sel[f"Component{n + 1:02d}"] = box(g, lo, hi, f"c{n}")
    mass = [total_mass / len(g.pts)] * len(g.pts)
    return g, mass


def build_memory() -> Mesh:
    m = Mesh()
    tip_x = blade_station(1.0)[0]
    points = {
        "meleerangestart": (0.0, 0.0, 0.0),
        "meleerangeend": (tip_x, TIP, 0.0),
        "throwingimpulseposition": (0.0, 0.08, 0.0),
        "ce_center": (-0.01, 0.40, 0.0),
        "ce_radius": (tip_x, TIP, 0.0),
        "invview": (-0.01, 0.40, -0.72),
        "boundingbox_min": (0.022, -0.115, -0.017),
        "boundingbox_max": (tip_x - 0.002, TIP, 0.017),
    }
    for name, p in points.items():
        m.sel[name] = {m.pt(p)}
    return m


# ---- textures --------------------------------------------------------------------------------------------------
RNG = np.random.default_rng(7)
CC0 = BUILD / "cc0"          # ambientCG photo materials, CC0 (tools/fetch_cc0.sh): Metal009 brushed steel (blade
                             # brushing, scratches on the silver), Leather037 leather grain, Metal056B rusted iron
REF = BUILD / "ref" / "shashka_ref_hi.png"     # Caucasian shashka, Livrustkammaren 1315 (Wikimedia Commons, CC0;
                                               # the 2776 px original): black and white - its light and shade, our
                                               # colours. Crop boxes below are in 1920 px-wide coordinates, scaled.
REF_BASE = 1920
SILVER = np.array([0.80, 0.80, 0.78])
NIELLO = np.array([0.05, 0.05, 0.06])
CARNELIAN = np.array([0.62, 0.20, 0.08])


def photo(asset, kind, size=None, gray=False):
    """an ambientCG map as floats 0..1 (H, W, 3) or (H, W); size (w, h) resamples"""
    im = Image.open(CC0 / asset / f"{asset}_1K-JPG_{kind}.jpg").convert("L" if gray else "RGB")
    if size:
        im = im.resize(size, Image.LANCZOS)
    return np.asarray(im, np.float32) / 255.0


def highpass(a, r=6):
    """detail only: the map minus its blur, centred on 0"""
    return a - smooth(np.clip(a, 0, 1), r)


def leather_from(h, w, seed):
    """dark brown leather: Leather037's pebble grain (its height map, high-passed) on a less red brown, and pale
    scuffs where noise says so"""
    disp = tile(photo("Leather037", "Displacement", (512, 512), gray=True), h, w)
    col = tile(photo("Leather037", "Color", (512, 512)), h, w)
    grain = highpass(disp, 4) * 3.0
    base = np.array([0.20, 0.12, 0.075]) * (0.85 + 0.3 * (col.mean(-1, keepdims=True) - col.mean()) * 4)
    rgb = base * (1 + grain[..., None])
    scuff = np.clip((noise(h, w, 40, seed) - 0.72) / 0.1, 0, 1) * np.clip(noise(h, w, 6, seed + 1) * 1.5 - 0.3, 0, 1)
    rgb = rgb * (1 - 0.3 * scuff[..., None]) + np.array([0.38, 0.30, 0.24]) * 0.3 * scuff[..., None]
    rough = tile(photo("Leather037", "Roughness", (512, 512), gray=True), h, w) * 0.8 + 0.2 * scuff
    return rgb, rough


_REF = None


def ref_image():
    global _REF
    if _REF is None:
        _REF = Image.open(REF).convert("L")
    return _REF


def ref_crop(box, size):
    """a piece of the reference photo, grey 0..1: scaled up from the 1920-wide box, sharpened (it is a century-old
    plate, soft at this size) and contrast stretched (2nd..98th percentile)"""
    im = ref_image()
    k = im.width / REF_BASE
    piece = im.crop(tuple(int(round(c * k)) for c in box)).resize(size, Image.LANCZOS)
    piece = piece.filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=2))
    a = np.asarray(piece, np.float32) / 255.0
    lo, hi = np.percentile(a, 2), np.percentile(a, 98)
    return np.clip((a - lo) / max(hi - lo, 1e-3), 0, 1)


def silver(lum, seed):
    """silver with niello: the photo's light as silver (a warm tarnish in the mid tones), its darkest lines as black
    niello; returns rgb, spec, gloss"""
    n = np.clip((0.30 - lum) / 0.22, 0, 1)
    tarnish = np.exp(-((lum - 0.5) / 0.2) ** 2) * (0.5 + 0.5 * noise(*lum.shape, 16, seed))
    h, w = lum.shape                                                 # micro-scratches: sharp where the photo is soft
    scr = tile(highpass(photo("Metal009", "Color", (512, 512)).mean(-1), 2), h, w)
    lum = np.clip(lum + 0.35 * scr * (1 - n), 0, 1)
    rgb = (0.25 + 0.85 * lum)[..., None] * SILVER
    rgb = rgb * (1 - 0.25 * tarnish[..., None]) + np.array([0.50, 0.42, 0.30]) * 0.25 * tarnish[..., None]
    rgb = rgb * (1 - n[..., None]) + NIELLO * n[..., None]
    return rgb, 0.85 * (1 - n) + 0.25 * n, 0.75 * (1 - n) + 0.45 * n


def stone(rgb, lum, cx, cy, rx, ry):
    """colour the oval stone set in a mount: carnelian, the photo's light kept for its shine"""
    h, w = lum.shape
    yy, xx = np.mgrid[0:h, 0:w]
    m = np.clip((1 - (((xx - cx * w) / (rx * w)) ** 2 + ((yy - cy * h) / (ry * h)) ** 2)) / 0.15, 0, 1)
    col = CARNELIAN * (0.5 + 1.0 * lum[..., None])
    return rgb * (1 - m[..., None]) + col * m[..., None], m


def ref_blade(h, w):
    """the reference blade straightened: every photo row from the hilt to the point, cut from its spine to its edge
    and stretched to w; a median along the length takes out the plate's crack and dust spots"""
    im = np.asarray(ref_image(), np.float32)
    k = im.shape[1] / REF_BASE
    x0, x1 = int(150 * k), int(520 * k)
    rows, last = [], None
    for y in range(int(580 * k), int(3120 * k)):
        r = im[y, x0:x1]
        dark = np.where(r < 170)[0]
        if len(dark) >= int(20 * k):
            runs = np.split(dark, np.where(np.diff(dark) > 3)[0] + 1)
            run = max(runs, key=len)
            seg = im[y, run[0] + x0:run[-1] + x0 + 1]
            last = np.interp(np.linspace(0, len(seg) - 1, w), np.arange(len(seg)), seg)
        if last is not None:
            rows.append(last)
    a = np.array(rows)
    k = 61                                                           # the crack runs across ~45 straightened rows
    pad = np.pad(a, ((k // 2, k // 2), (0, 0)), mode="edge")
    a = np.median(np.lib.stride_tricks.sliding_window_view(pad, k, axis=0), axis=-1)
    a = np.asarray(Image.fromarray(a.astype(np.float32)).resize((w, h), Image.BILINEAR), np.float32)
    lo, hi = np.percentile(a, 2), np.percentile(a, 98)
    return np.clip((a - lo) / max(hi - lo, 1e-3), 0, 1)        # row 0 at the hilt, column 0 at the spine


def tile(a, h, w):
    """repeat a map to (h, w)"""
    reps = (-(-h // a.shape[0]), -(-w // a.shape[1])) + ((1,) if a.ndim == 3 else ())
    return np.tile(a, reps)[:h, :w]


def noise(h, w, scale, seed=None):
    r = np.random.default_rng(seed).random((max(h // scale, 2), max(w // scale, 2))).astype(np.float32)
    im = Image.fromarray((r * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


def smooth(a, r):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im, np.float32) / 255.0


def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def tex_blade():
    """the reference blade (straightened, its three fullers by the spine and its worn surface) as the light and
    shade of a grey steel, with Metal009's fine brushing on top and a honed bevel and edge"""
    H, W = 2048, 256
    side = 118                                                       # u 0.02..0.48 / 0.52..0.98 of 256
    ref = ref_blade(H, side)[::-1]                                   # texture v runs from the point (0) to the hilt
    steel = np.rot90(photo("Metal009", "Color", (1024, 1024)).mean(-1))
    brush = tile(highpass(steel, 3), H, side)
    u = np.ones((H, 1)) * np.linspace(0, 1, side)[None, :]
    bevel = np.clip((u - 0.80) / 0.08, 0, 1)
    edge = np.clip((u - 0.96) / 0.04, 0, 1)
    lum = 0.30 + 0.45 * ref + 0.4 * brush + 0.10 * bevel + 0.12 * edge
    one = np.stack([lum * 0.93, lum * 0.96, lum * 1.0], -1)
    spec1 = (0.35 + 0.45 * ref + 0.2 * bevel).clip(0.1, 1)
    gloss1 = (0.55 + 0.25 * ref + 0.15 * bevel).clip(0.2, 1)
    rgb = np.zeros((H, W, 3), np.float32)
    spec = np.full((H, W), 0.5, np.float32)
    gloss = np.full((H, W), 0.6, np.float32)
    for x0 in (5, 133):                                              # both flats
        rgb[:, x0:x0 + side] = one
        spec[:, x0:x0 + side] = spec1
        gloss[:, x0:x0 + side] = gloss1
    rgb[:, :5] = one[:, :1].mean(1, keepdims=True)                   # the spine strip
    return to_img(rgb), to_img(np.stack([np.ones_like(spec), spec, gloss], -1))


def tex_hilt():
    """the reference hilt, silver and niello all over: grip (u 0..0.5) its ornamented panel, twice round;
    ferrule (u 0.5..0.75, v 0..0.5) the mount under the grip; head (u 0.75..1) the pommel, grip end at v 0"""
    S = 512
    lum = np.zeros((S, S), np.float32)
    grip = ref_crop((278, 285, 338, 425), (128, 512))
    lum[:, 0:128] = grip
    lum[:, 128:256] = grip
    lum[0:256, 256:384] = ref_crop((272, 440, 330, 555), (128, 256))
    lum[256:, 256:384] = ref_crop((272, 440, 330, 555), (128, 256))[::-1]
    lum[:, 384:] = ref_crop((285, 115, 365, 200), (128, 512))[::-1]   # head: from the grip up
    rgb, spec, gloss = silver(lum, 51)
    return to_img(rgb), to_img(np.stack([np.ones_like(spec), spec, gloss], -1))


def tex_rust(coverage, pits, seed):
    """a damage macro: rusted iron (Metal056B) where its own height map is lowest - pitting first - over the
    given share of the surface, alpha there"""
    S = 512
    rust = photo("Metal056B", "Color", (S, S))
    h = photo("Metal056B", "Displacement", (S, S), gray=True)
    h = h * 0.7 + noise(S, S, 48, seed) * 0.3                       # break up the tiling
    thr = np.quantile(h, coverage)
    a = smooth(np.clip((thr - h) / 0.05, 0, 1), 1.2)
    pit = (h < np.quantile(h, coverage * pits * 4)) & (a > 0.5)
    rgb = rust * 0.5 + np.array([0.45, 0.22, 0.09]) * (0.6 + 0.8 * (rust.mean(-1, keepdims=True) - 0.3))
    rgb[pit] *= 0.45
    return Image.fromarray((np.concatenate([rgb, a[..., None]], -1).clip(0, 1) * 255).astype(np.uint8), "RGBA")


def tex_tarnish(coverage, seed):
    """the damaged macro: dull grey-brown tarnish from the rust photo, desaturated, a few rust specks"""
    S = 512
    rust = photo("Metal056B", "Color", (S, S))
    h = photo("Metal056B", "Displacement", (S, S), gray=True) * 0.5 + noise(S, S, 32, seed) * 0.5
    thr = np.quantile(h, coverage)
    a = smooth(np.clip((thr - h) / 0.08, 0, 1), 1.0) * 0.8
    grey = rust.mean(-1, keepdims=True)
    rgb = grey * 0.7 + rust * 0.3
    specks = noise(S, S, 2, seed + 3) > 0.985
    rgb[specks] = rust[specks]
    a = np.where(specks, 1.0, a)
    return Image.fromarray((np.concatenate([rgb, a[..., None]], -1).clip(0, 1) * 255).astype(np.uint8), "RGBA")


# ---- materials -----------------------------------------------------------------------------------------------------
def rvmat(nohq, smdi, dt, mc, spec_power=120.4, diffuse=1.0) -> str:
    d = f"{diffuse:g}"

    def stage(n, tex, uv="tex", tile=1):
        tr = (f"\tclass uvTransform\n\t{{\n\t\taside[] = {{{tile}, 0, 0}};\n\t\tup[] = {{0, {tile}, 0}};\n"
              f"\t\tdir[] = {{0, 0, 0}};\n\t\tpos[] = {{0, 0, 0}};\n\t}};\n") if uv == "tex" else ""
        return f"class Stage{n}\n{{\n\ttexture = \"{tex}\";\n\tuvSource = \"{uv}\";\n{tr}}};\n"
    return (f"ambient[] = {{{d}, {d}, {d}, 1}};\ndiffuse[] = {{{d}, {d}, {d}, 1}};\nforcedDiffuse[] = {{0, 0, 0, 0}};\n"
            f"emmisive[] = {{0, 0, 0, 1}};\nspecular[] = {{1, 1, 1, 1}};\nspecularPower = {spec_power};\n"
            "PixelShaderID = \"Super\";\nVertexShaderID = \"Super\";\n"
            + stage(1, nohq)
            + stage(2, f"#(argb,8,8,3)color({dt},{dt},{dt},1,DT)", tile=20)
            + stage(3, mc, tile=2)
            + stage(4, "#(argb,8,8,3)color(1,1,1,1,AS)")
            + stage(5, smdi)
            + stage(6, "#(ai,64,64,1)fresnel(1.82,0.71)", "none")
            + stage(7, "#(argb,8,8,3)color(0,0,0,1,CO)", "none"))


NOHQ_FLAT = "#(argb,8,8,3)color(0.5,0.5,1,1,NOHQ)"
MC_NONE = "#(argb,8,8,3)color(0,0,0,0,MC)"
STATES = {                     # suffix: (detail, macro, specular power, diffuse)
    "": (0.5, MC_NONE, 120.4, 1.0),
    "_damage": (0.4, PFX + "shashka_damaged_mc.paa", 90.0, 0.95),
    "_badly": (0.35, PFX + "shashka_badly_mc.paa", 60.0, 0.9),
    "_destruct": (0.3, PFX + "shashka_ruined_mc.paa", 30.0, 0.8),
}


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    m = Mesh()
    build_blade(m)
    build_hilt(m)
    g, mass = build_geometry()
    mem = build_memory()
    p3d = write_mlod([(1.0, m, {}, None), (1e13, g, {"autocenter": "0"}, mass), (1e15, mem, {}, None)])
    (DATA / "shashka.p3d").write_bytes(p3d)
    print(f"shashka.p3d {len(p3d)} B: visual {len(m.pts)} pts {len(m.faces)} faces, geometry {len(g.sel)} components")
    # the sheath stands on its chape, hilt up, origin at the chape's end: that is how the game sets an item down
    # (upright as modelled) - under the painting it then leans on the wall instead of standing on its pommel.
    # The origin is where a hand holds it - between the two bands with the stones - since an item sits in the
    # hand by its origin; the spawner and the belt slot offset from there (SK_Spawner.c, config.cpp).
    # The same turn and shift for its geometry, memory points and the blade's proxy.
    sh = Mesh()
    build_sheath(sh)
    sg, smass = build_geometry(0.45)
    smem = build_memory()
    gx, gy = sheath_grip()
    for mesh in (sh, sg, smem):
        mesh.pts = [(-x - gx, SHEATH1 - y - gy, z) for x, y, z in mesh.pts]   # a turn: the winding stays
    print(f"sheath grip: {gy:.4f} m above the chape, {gx:.4f} m across (SK_SHEATH_GRIP in SK_Spawner.c)")
    sp3d = write_mlod([(1.0, sh, {}, None), (1e13, sg, {"autocenter": "0"}, smass), (1e15, smem, {}, None)])
    (DATA / "shashka_sheath.p3d").write_bytes(sp3d)
    print(f"shashka_sheath.p3d {len(sp3d)} B: visual {len(sh.pts)} pts {len(sh.faces)} faces, selections {sorted(sh.sel)}")
    # the proxy's own model (CfgNonAIVehicles Proxysk_shashka): only a stand-in, the attached item replaces it
    pm = Mesh()
    pm.face([pm.pt((0, 0, 0)), pm.pt((0, 0.02, 0)), pm.pt((0, 0, 0.01))], [(0, 0)] * 3, "", "", "p")
    (DATA / "proxy").mkdir(exist_ok=True)
    (DATA / "proxy" / "sk_shashka.p3d").write_bytes(write_mlod([(1.0, pm, {}, None)]))

    sco, ssm = tex_sheath()
    bco, bsm = tex_blade()
    hco, hsm = tex_hilt()
    images = {"shashka_sheath_co": sco, "shashka_sheath_smdi": ssm, "shashka_blade_co": bco, "shashka_blade_smdi": bsm, "shashka_hilt_co": hco, "shashka_hilt_smdi": hsm,
              "shashka_damaged_mc": tex_tarnish(0.35, 11),
              "shashka_badly_mc": tex_rust(0.30, 0.15, 21), "shashka_ruined_mc": tex_rust(0.70, 0.25, 31)}
    for name, im in images.items():
        im.save(BUILD / f"{name}.png")
        (DATA / f"{name}.paa").write_bytes(paa.encode(im, dxt5=name.endswith("_mc")))

    for part in ("blade", "hilt", "sheath"):
        for suffix, (dt, mc, sp, diff) in STATES.items():
            text = rvmat(NOHQ_FLAT, PFX + f"shashka_{part}_smdi.paa", dt, mc, sp, diff)
            src = BUILD / f"shashka_{part}{suffix}.rvmat.txt"
            src.write_text(text)
            dst = DATA / f"shashka_{part}{suffix}.rvmat"
            subprocess.run([str(ARMAKE), "rapify", "-f", str(src), str(dst)], check=True)
    print("textures + rvmats ->", DATA)
    preview(m, BUILD / "preview.png")
    preview(sh, BUILD / "preview_sheath.png")


def preview(m: Mesh, out: Path):
    """flat-shaded side and edge-on views, textured by face colour only - to eyeball the shape (needs matplotlib;
    skipped without it)"""
    try:
        import matplotlib
    except ImportError:
        return
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    P = np.array(m.pts)
    fig = plt.figure(figsize=(14, 6), dpi=110)
    light = np.array([0.4, 0.3, -0.85])
    light /= np.linalg.norm(light)
    for k, (elev, azim, title) in enumerate(((0, -90, "flat (from -Z, the inventory view)"), (90, -90, "spine/edge (from +Y down)"), (20, -60, "3/4"))):
        ax = fig.add_subplot(1, 3, k + 1, projection="3d")
        polys, cols = [], []
        for f in m.faces:
            if f["group"] == "proxy":
                continue
            q = P[f["idx"]]
            n = m.normal(f)
            n = n / max(np.linalg.norm(n), 1e-12)
            lit = 0.35 + 0.65 * max(float(-np.dot(n, light)), 0.0)
            base = {TEX_BLADE: np.array([0.75, 0.77, 0.8]), TEX_SHEATH: np.array([0.3, 0.18, 0.1])}.get(f["tex"], np.array([0.45, 0.3, 0.2]))
            polys.append(q[:, [0, 2, 1]])
            cols.append(tuple((base * lit).clip(0, 1)))
        ax.add_collection3d(Poly3DCollection(polys, facecolors=cols, edgecolors="none"))
        ax.set_xlim(-0.45, 0.45); ax.set_ylim(-0.45, 0.45); ax.set_zlim(-0.12, 0.9)
        ax.set_box_aspect((1, 1, 1.13))
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title, fontsize=9)
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(out)
    print("preview ->", out)


if __name__ == "__main__":
    main()
