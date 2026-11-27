"""Scene compositor: spec (JSON) + time -> SVG body.

Spec schema (all keys optional except headline):
{
  "headline": "REVENUE *DOUBLED*",          # *word* is highlighted in orange
  "layout": "center|split|row3|row4|flow|hero_scene|versus|chart|hero_center",
  "objects": [{"prop": "chip", "label": "GPU", "motion": "float"}],
  "hero": {"pose": "up|down|fwd|shrug|right_up|left_up", "motion": "bob|jump"},
  "link": "none|arrow|coins|loop",
  "chart": {"kind": "bars_up|bars_down|line_up|line_down|pie|compare", "value": 61, "ratio": 2},
  "callout": "$115.8B"
}
"""
import math
from .gfx import *
from .props import PROPS

LAYOUTS = {"center": 1, "split": 2, "row3": 3, "row4": 4, "flow": 3, "hero_scene": 2, "versus": 2, "chart": 1, "hero_center": 3}
MOTIONS = ["none", "float", "pulse", "shake", "bounce", "spin"]
LINKS = ["none", "arrow", "coins", "loop"]
POSES = ["down", "up", "fwd", "shrug", "right_up", "left_up"]
HERO_MOTIONS = ["bob", "jump"]
CHARTS = ["bars_up", "bars_down", "line_up", "line_down", "pie", "compare"]

SLOTS = {
    "center": [(340, 175)], "split": [(185, 180), (495, 180)], "row3": [(120, 180), (340, 180), (560, 180)],
    "row4": [(95, 185), (260, 185), (425, 185), (590, 185)], "flow": [(340, 95), (525, 255), (155, 255)],
    "hero_scene": [(405, 180), (565, 180)], "versus": [(170, 175), (510, 175)], "chart": [(585, 105)],
    "hero_center": [(130, 140), (550, 140), (340, 62)],
}
SCALES = {"center": 1.7, "split": 1.45, "row3": 1.2, "row4": 1.0, "flow": 1.1, "hero_hero": 1.0,
          "hero_scene": 1.3, "versus": 1.4, "chart": 0.8, "hero_center": 0.9}


def hero(cx, cy, s=1.0, arms="down"):
    """The orange hooded protagonist. Ground line is at cy + 75*s."""
    A = {"down": [(-28, 14), (28, 14)], "up": [(-34, -46), (34, -46)], "left_up": [(-34, -46), (28, 14)],
         "right_up": [(-28, 14), (34, -46)], "fwd": [(46, 8), (46, 16)], "shrug": [(-38, -24), (38, -24)]}[arms]
    o = "".join(line(cx + (-26 * s if dx < 0 else 26 * s), cy - 4 * s, cx + dx * s, cy + dy * s, ORG, 9) for dx, dy in A)
    o += poly([(cx - 30 * s, cy + 75 * s), (cx - 29 * s, cy - 4 * s), (cx - 18 * s, cy - 24 * s), (cx + 18 * s, cy - 24 * s),
               (cx + 29 * s, cy - 4 * s), (cx + 30 * s, cy + 75 * s)], ORG, EDGE, 2.5)
    o += circ(cx, cy - 42 * s, 26 * s, ORG, EDGE, 2.5)
    o += f'<ellipse cx="{cx}" cy="{cy - 42 * s}" rx="{13 * s}" ry="{15 * s}" fill="#0b0b0d"/>'
    o += poly([(cx - 16 * s, cy + 30 * s), (cx + 16 * s, cy + 30 * s), (cx + 16 * s, cy + 50 * s), (cx - 16 * s, cy + 50 * s)], "none", "#a63e00", 2.5)
    return o


def _motion(m, t, ph):
    """-> (dx, dy, scale, rot)"""
    if m == "float":
        return 0, 6 * math.sin(t * 2.0 + ph), 1, 0
    if m == "pulse":
        return 0, 0, 1 + 0.05 * math.sin(t * 3.2 + ph), 0
    if m == "shake":
        return 1.8 * math.sin(t * 34 + ph), 0, 1, 0
    if m == "bounce":
        return 0, -10 * abs(math.sin(t * 3 + ph)), 1, 0
    if m == "spin":
        return 0, 0, 1, math.sin(t * 1.5 + ph) * 8
    return 0, 0, 1, 0


def _chart(c, t, callout):
    kind = c.get("kind", "bars_up")
    x0, x1, yb, ht = 150, 530, 300, 190
    o = line(x0 - 10, yb + 6, x1 + 10, yb + 6, INK, 3) + line(x0 - 10, yb + 6, x0 - 10, yb - ht - 16, INK, 3)
    if kind in ("bars_up", "bars_down"):
        hs = [0.3, 0.5, 0.75, 1.0] if kind == "bars_up" else [1.0, 0.75, 0.5, 0.3]
        for i, h in enumerate(hs):
            g = ez((t - (0.3 + 0.55 * i)) / 0.55)
            hh = ht * h * g
            o += _bar(x0 + 20 + i * 90, yb, 64, ht * h, g, i == 3)
    elif kind in ("line_up", "line_down"):
        pts = [(150, 285), (225, 245), (290, 262), (370, 195), (445, 165), (530, 100)]
        if kind == "line_down":
            pts = [(x, 385 - y) for x, y in pts]
        p = ez(t / 2.0)
        n = len(pts) - 1
        seg = p * n
        vis = [pts[0]]
        for i in range(1, len(pts)):
            if seg >= i:
                vis.append(pts[i])
            elif seg > i - 1:
                f = seg - (i - 1)
                vis.append((pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f))
        if len(vis) < 2:
            vis.append((pts[0][0] + 0.1, pts[0][1]))
        o += poly(vis, "none", ORG, 7, False)
        o += circ(vis[-1][0], vis[-1][1], 9, ORG, EDGE, 3)
    elif kind == "pie":
        val = float(c.get("value", 60))
        r = 78
        circum = 2 * math.pi * r
        fill = circum * val / 100 * ez(t / 1.3)
        o = (f'<circle cx="340" cy="195" r="{r}" fill="none" stroke="{PANEL3}" stroke-width="26"/>'
             f'<circle cx="340" cy="195" r="{r}" fill="none" stroke="{ORG}" stroke-width="26" stroke-dasharray="{fill:.1f} {circum:.1f}"'
             f' transform="rotate(-90 340 195)"/>')
        o += txt(340, 210, f"{int(round(val * ez(t / 1.3)))}%", 44)
    elif kind == "compare":
        ratio = float(c.get("ratio", 2))
        g1, g2 = ez(t / 0.8), ez((t - 1.0) / 1.2)
        o += _bar(220, yb, 90, 70, g1, False) + _bar(400, yb, 90, min(185, 70 * ratio), g2, True)
        o += grp(txt(445, yb - min(185, 70 * ratio) - 14, f"x{ratio:g}", 36, ORG), alpha=ez((t - 2.2) / 0.5))
        lb = c.get("labels")
        if lb and len(lb) >= 2:
            o += txt(265, yb + 28, str(lb[0])[:14], 16) + txt(445, yb + 28, str(lb[1])[:14], 16)
    return o


def _bar(x, yb, w, h, g, hot):
    hh = max(h * g, 0.1)
    return grp(rect(x, yb - hh, w, hh, ORG if hot else PANEL, EDGE if hot else INK), alpha=1 if hh > 3 else 0)


def _link_pts(lay, pos, scs):
    L = []
    if lay in ("split", "row3", "row4", "hero_scene"):
        for i in range(len(pos) - 1):
            L.append((pos[i], pos[i + 1], scs))
    elif lay == "flow":
        for i in range(len(pos)):
            L.append((pos[i], pos[(i + 1) % len(pos)], scs))
    return L


def compose(spec, t, D):
    lay = spec.get("layout", "center")
    if lay not in LAYOUTS:
        lay = "center"
    objs = (spec.get("objects") or [])[:LAYOUTS[lay]]
    slots = SLOTS[lay]
    if lay == "hero_scene" and len(objs) == 1:
        slots = [(450, 180)]
    sc = SCALES.get(lay, 1.2)
    o = ""
    pos = []
    # chart
    if lay == "chart":
        o += _chart(spec.get("chart") or {"kind": "bars_up"}, t, spec.get("callout"))
    # versus divider
    if lay == "versus":
        o += line(340, 70, 340, 300, INK, 3, "8 7") + grp(txt(340, 195, "VS", 34, ORG), alpha=ez((t - 0.6) / 0.4))
    # objects
    for i, ob in enumerate(objs):
        cx, cy = slots[min(i, len(slots) - 1)]
        pos.append((cx, cy))
        fn = PROPS.get(ob.get("prop"), PROPS["question"])
        dx, dy, ms, rot = _motion(ob.get("motion", "none"), t, i * 1.3)
        pop = ez((t - 0.15 - 0.25 * i) / 0.4)
        s = sc * (0.6 + 0.4 * pop) * ms
        o += grp(fn(cx, cy, sc, str(ob.get("label", "")), t), dx=dx, dy=dy, s=(0.6 + 0.4 * pop) * ms, rot=rot,
                 alpha=pop, cx=cx, cy=cy)
    # links
    link = spec.get("link", "none")
    if link != "none" and len(pos) > 1:
        r = 56 * sc
        for (a, b, _) in _link_pts(lay, pos, sc):
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            a2 = (a[0] + r * math.cos(ang), a[1] + r * math.sin(ang))
            b2 = (b[0] - r * math.cos(ang), b[1] - r * math.sin(ang))
            if math.hypot(b2[0] - a2[0], b2[1] - a2[1]) < 24:
                continue
            al = ez((t - 0.8) / 0.4)
            o += grp(arrow(a2[0], a2[1], b2[0], b2[1]), alpha=al)
            if link in ("coins", "loop"):
                for k in range(3):
                    f = (t * 0.5 + k / 3) % 1
                    env = min(1, f * 6) * min(1, (1 - f) * 6)
                    o += grp(PROPS["coin"](a2[0] + (b2[0] - a2[0]) * f, a2[1] + (b2[1] - a2[1]) * f, 0.55, "", t), alpha=env * al)
    # hero
    h = spec.get("hero")
    if isinstance(h, str):
        h = {"pose": h}
    if h:
        pose = h.get("pose", "down") if h.get("pose") in POSES else "down"
        mot = h.get("motion", "bob")
        pos_h = {"hero_scene": (130, 200, 1.25), "hero_center": (340, 240, 1.15), "chart": (85, 215, 1.0),
                 "center": (95, 215, 1.0), "split": (340, 225, 0.9), "versus": (340, 250, 0.7)}.get(lay)
        if pos_h:
            hx, hy, hs = pos_h
            by = 3 * math.sin(2 * math.pi * 1.3 * t) if mot == "bob" else -26 * abs(math.sin(2 * math.pi * 0.9 * t))
            o += hero(hx, hy + by, hs, pose)
    # callout
    if spec.get("callout"):
        cyc = 352 if lay == "chart" else 332
        o += grp(txt(340, cyc, str(spec["callout"]), 34, ORG), alpha=ez((t - 0.9) / 0.4), s=0.8 + 0.2 * ez((t - 0.9) / 0.4), cx=340, cy=cyc - 12)
    return o
