"""Prop library. Every prop is f(cx, cy, s, label, t) -> svg, centred on (cx, cy).

s = scale (1.0 is roughly a 100px box), label = optional caption, t = seconds.
Props may animate themselves using t. Add new props by writing a function and
registering it in PROPS with a one-line description in PROP_DOC.
"""
import math
from .gfx import *


def _lab(cx, cy, s, label, dy=68):
    if not label:
        return ""
    return txt(cx, cy + dy * s, label, min(19, 13 * s + 3))


def building(cx, cy, s, label="", t=0):
    o = rect(cx - 38 * s, cy - 55 * s, 76 * s, 110 * s, PANEL2)
    for r in range(3):
        for c in range(3):
            lit = (int(t * 1.5) + r * 3 + c) % 7 == 0
            o += rect(cx - 28 * s + c * 21 * s, cy - 42 * s + r * 26 * s, 12 * s, 16 * s, ORG if lit else DARK, INK, 2)
    o += rect(cx - 9 * s, cy + 30 * s, 18 * s, 25 * s, DARK, INK, 2)
    return o + _lab(cx, cy, s, label, 74)


def chip(cx, cy, s, label="", t=0):
    o = ""
    for i in range(4):
        d = -24 * s + i * 16 * s
        o += line(cx + d, cy - 44 * s, cx + d, cy - 34 * s) + line(cx + d, cy + 34 * s, cx + d, cy + 44 * s)
        o += line(cx - 44 * s, cy + d, cx - 34 * s, cy + d) + line(cx + 34 * s, cy + d, cx + 44 * s, cy + d)
    o += rect(cx - 34 * s, cy - 34 * s, 68 * s, 68 * s, PANEL)
    o += rect(cx - 16 * s, cy - 16 * s, 32 * s, 32 * s, ORG, EDGE, 2)
    return o + _lab(cx, cy, s, label, 62)


def bolt(cx, cy, s, label="", t=0):
    f = 1 if int(t * 6) % 5 else 0.55
    o = poly([(cx, cy - 40 * s), (cx - 22 * s, cy + 6 * s), (cx - 3 * s, cy + 6 * s), (cx - 11 * s, cy + 40 * s),
              (cx + 22 * s, cy - 10 * s), (cx + 3 * s, cy - 10 * s)], ORG, EDGE, 3)
    return grp(o, alpha=f) + _lab(cx, cy, s, label, 56)


def coin(cx, cy, s, label="", t=0):
    return circ(cx, cy, 20 * s, ORG, EDGE, 3) + txt(cx, cy + 8 * s, "$", 24 * s, INK) + _lab(cx, cy, s, label, 36)


def moneybag(cx, cy, s, label="", t=0):
    o = circ(cx, cy + 8 * s, 34 * s, ORG, EDGE) + rect(cx - 12 * s, cy - 40 * s, 24 * s, 16 * s, ORG, EDGE)
    return o + txt(cx, cy + 20 * s, "$", 36 * s, INK) + _lab(cx, cy, s, label, 58)


def stackcoins(cx, cy, s, label="", t=0):
    o = ""
    for i in range(5):
        o += rect(cx - 34 * s, cy + 36 * s - i * 14 * s, 68 * s, 12 * s, ORG, EDGE, 3)
    return o + _lab(cx, cy, s, label, 62)


def eye(cx, cy, s, label="", t=0):
    d = f"M{cx-48*s} {cy} Q{cx} {cy-38*s} {cx+48*s} {cy} Q{cx} {cy+38*s} {cx-48*s} {cy} Z"
    px = 6 * s * math.sin(t * 1.6)
    return (path(d, DARK) + circ(cx + px, cy, 16 * s, ORG, EDGE, 3) + circ(cx + px, cy, 7 * s, DARK, DARK, 1)
            + _lab(cx, cy, s, label, 52))


def magnifier(cx, cy, s, label="", t=0):
    o = line(cx + 18 * s, cy + 18 * s, cx + 52 * s, cy + 52 * s, INK, 9)
    o += circ(cx - 6 * s, cy - 6 * s, 34 * s, PANEL2)
    if label:
        o += txt(cx - 6 * s, cy - 1 * s, label, 15 * s)
    return o


def cloud(cx, cy, s, label="", t=0):
    o = circ(cx - 32 * s, cy + 6 * s, 24 * s, PANEL) + circ(cx, cy - 12 * s, 32 * s, PANEL) + circ(cx + 34 * s, cy + 6 * s, 24 * s, PANEL)
    o += rect(cx - 32 * s, cy + 4 * s, 66 * s, 26 * s, PANEL, PANEL, 1)
    return o + _lab(cx, cy, s, label, 56)


def document(cx, cy, s, label="", t=0):
    o = rect(cx - 36 * s, cy - 48 * s, 72 * s, 96 * s, PANEL2) + rect(cx - 36 * s, cy - 48 * s, 72 * s, 16 * s, ORG, EDGE, 3)
    for i in range(4):
        o += line(cx - 24 * s, cy - 14 * s + i * 16 * s, cx + 24 * s, cy - 14 * s + i * 16 * s, INK, 3)
    return o + _lab(cx, cy, s, label, 66)


def newspaper(cx, cy, s, label="", t=0):
    o = rect(cx - 52 * s, cy - 44 * s, 104 * s, 88 * s, PANEL2) + rect(cx - 44 * s, cy - 36 * s, 88 * s, 18 * s, ORG, EDGE, 3)
    for i in range(3):
        o += line(cx - 44 * s, cy - 4 * s + i * 16 * s, cx + 44 * s, cy - 4 * s + i * 16 * s, INK, 3)
    return o + _lab(cx, cy, s, label, 62)


def globe(cx, cy, s, label="", t=0):
    o = circ(cx, cy, 46 * s, PANEL2)
    o += poly([(cx - 22 * s, cy - 24 * s), (cx + 4 * s, cy - 32 * s), (cx + 8 * s, cy - 8 * s), (cx - 14 * s, cy - 2 * s)], ORG, EDGE, 2)
    o += poly([(cx + 14 * s, cy + 4 * s), (cx + 34 * s, cy - 2 * s), (cx + 30 * s, cy + 24 * s), (cx + 14 * s, cy + 22 * s)], ORG, EDGE, 2)
    o += line(cx - 46 * s, cy, cx + 46 * s, cy, INK, 2)
    return o + _lab(cx, cy, s, label, 62)


def rocket(cx, cy, s, label="", t=0):
    dx = 1.5 * s * math.sin(t * 38)
    tip = cy + (64 + 12 * abs(math.sin(t * 27))) * s
    o = poly([(cx, cy - 56 * s), (cx - 20 * s, cy - 24 * s), (cx + 20 * s, cy - 24 * s)], ORG, EDGE, 3)
    o += rect(cx - 20 * s, cy - 24 * s, 40 * s, 62 * s, PANEL) + circ(cx, cy - 6 * s, 9 * s, PANEL2, INK, 3)
    o += poly([(cx - 20 * s, cy + 14 * s), (cx - 38 * s, cy + 40 * s), (cx - 20 * s, cy + 38 * s)], ORG, EDGE, 3)
    o += poly([(cx + 20 * s, cy + 14 * s), (cx + 38 * s, cy + 40 * s), (cx + 20 * s, cy + 38 * s)], ORG, EDGE, 3)
    o += poly([(cx - 10 * s, cy + 38 * s), (cx, tip), (cx + 10 * s, cy + 38 * s)], ORG, EDGE, 2)
    return grp(o, dx=dx) + _lab(cx, cy, s, label, 84)


def trophy(cx, cy, s, label="", t=0):
    o = poly([(cx - 34 * s, cy - 44 * s), (cx + 34 * s, cy - 44 * s), (cx + 26 * s, cy + 6 * s), (cx - 26 * s, cy + 6 * s)], ORG, EDGE)
    o += line(cx - 34 * s, cy - 34 * s, cx - 52 * s, cy - 34 * s) + line(cx - 52 * s, cy - 34 * s, cx - 42 * s, cy - 10 * s)
    o += line(cx + 34 * s, cy - 34 * s, cx + 52 * s, cy - 34 * s) + line(cx + 52 * s, cy - 34 * s, cx + 42 * s, cy - 10 * s)
    o += rect(cx - 7 * s, cy + 6 * s, 14 * s, 26 * s, ORG, EDGE, 3) + rect(cx - 26 * s, cy + 32 * s, 52 * s, 12 * s, ORG, EDGE, 3)
    return o + _lab(cx, cy, s, label, 64)


def scale(cx, cy, s, label="", t=0):
    ang = 7 * math.sin(t * 1.2)
    beam = line(cx - 56 * s, cy - 20 * s, cx + 56 * s, cy - 20 * s) + poly([(cx - 62 * s, cy - 2 * s), (cx - 38 * s, cy - 2 * s), (cx - 44 * s, cy + 12 * s), (cx - 56 * s, cy + 12 * s)], ORG, EDGE, 3)
    beam += poly([(cx + 38 * s, cy - 2 * s), (cx + 62 * s, cy - 2 * s), (cx + 56 * s, cy + 12 * s), (cx + 44 * s, cy + 12 * s)], PANEL, INK, 3)
    o = line(cx, cy - 20 * s, cx, cy + 40 * s) + rect(cx - 24 * s, cy + 40 * s, 48 * s, 10 * s, PANEL)
    return o + grp(beam, rot=ang, cx=cx, cy=cy - 20 * s) + _lab(cx, cy, s, label, 70)


def datacentre(cx, cy, s, label="", t=0):
    o = ""
    for i in range(3):
        x = cx - 66 * s + i * 46 * s
        o += rect(x, cy - 52 * s, 40 * s, 104 * s, PANEL2)
        for k in range(4):
            lit = (int(t * 3) + i + k) % 3 == 0
            o += circ(x + 10 * s, cy - 36 * s + k * 24 * s, 4 * s, ORG if lit else DARK, INK, 2)
            o += line(x + 18 * s, cy - 36 * s + k * 24 * s, x + 34 * s, cy - 36 * s + k * 24 * s, INK, 2)
    return o + _lab(cx, cy, s, label, 68)


def laptop(cx, cy, s, label="", t=0):
    o = rect(cx - 46 * s, cy - 38 * s, 92 * s, 60 * s, PANEL2) + poly([(cx - 58 * s, cy + 22 * s), (cx + 58 * s, cy + 22 * s), (cx + 66 * s, cy + 36 * s), (cx - 66 * s, cy + 36 * s)], PANEL)
    o += poly([(cx - 34 * s, cy + 10 * s), (cx - 14 * s, cy - 6 * s), (cx + 4 * s, cy), (cx + 36 * s, cy - 24 * s)], "none", ORG, 4, False)
    return o + _lab(cx, cy, s, label, 62)


def phone(cx, cy, s, label="", t=0):
    o = rect(cx - 26 * s, cy - 46 * s, 52 * s, 92 * s, PANEL2) + rect(cx - 20 * s, cy - 36 * s, 40 * s, 62 * s, PANEL)
    o += circ(cx, cy + 36 * s, 4 * s, DARK, INK, 2)
    b = 1 if int(t * 2) % 2 else 0.4
    return o + grp(circ(cx + 22 * s, cy - 46 * s, 9 * s, ORG, EDGE, 2), alpha=b) + _lab(cx, cy, s, label, 66)


def bank(cx, cy, s, label="", t=0):
    o = rect(cx - 52 * s, cy + 30 * s, 104 * s, 14 * s, PANEL) + poly([(cx - 56 * s, cy - 24 * s), (cx, cy - 56 * s), (cx + 56 * s, cy - 24 * s)], PANEL2)
    for i in range(5):
        o += rect(cx - 44 * s + i * 20 * s, cy - 18 * s, 12 * s, 48 * s, PANEL)
    return o + _lab(cx, cy, s, label, 66)


def house(cx, cy, s, label="", t=0):
    o = rect(cx - 40 * s, cy - 10 * s, 80 * s, 56 * s, PANEL2) + poly([(cx - 50 * s, cy - 10 * s), (cx, cy - 52 * s), (cx + 50 * s, cy - 10 * s)], ORG, EDGE, 3)
    o += rect(cx - 10 * s, cy + 16 * s, 20 * s, 30 * s, DARK, INK, 3)
    return o + _lab(cx, cy, s, label, 66)


def car(cx, cy, s, label="", t=0):
    o = rect(cx - 56 * s, cy - 4 * s, 112 * s, 32 * s, ORG, EDGE, 3) + poly([(cx - 30 * s, cy - 4 * s), (cx - 16 * s, cy - 30 * s), (cx + 24 * s, cy - 30 * s), (cx + 40 * s, cy - 4 * s)], PANEL, INK, 3)
    o += circ(cx - 32 * s, cy + 30 * s, 12 * s, DARK) + circ(cx + 32 * s, cy + 30 * s, 12 * s, DARK)
    return o + _lab(cx, cy, s, label, 58)


def factory(cx, cy, s, label="", t=0):
    o = rect(cx - 52 * s, cy - 6 * s, 104 * s, 52 * s, PANEL2) + rect(cx - 40 * s, cy - 40 * s, 14 * s, 36 * s, PANEL) + rect(cx - 14 * s, cy - 30 * s, 14 * s, 26 * s, PANEL)
    for k in range(3):
        q = (t * 28 + k * 22) % 66
        o += grp(circ(cx - 33 * s + q * 0.2 * s, cy - 48 * s - q * s, (5 + q / 9) * s, PANEL3, INK, 2), alpha=1 - q / 66)
    return o + _lab(cx, cy, s, label, 62)


def clock(cx, cy, s, label="", t=0):
    o = circ(cx, cy, 46 * s, PANEL2)
    a = t * 1.4
    o += line(cx, cy, cx + 30 * s * math.sin(a), cy - 30 * s * math.cos(a), INK, 5)
    o += line(cx, cy, cx + 20 * s * math.sin(a / 12), cy - 20 * s * math.cos(a / 12), ORG, 6)
    return o + _lab(cx, cy, s, label, 62)


def lightbulb(cx, cy, s, label="", t=0):
    o = ""
    for k in range(8):
        a = k * math.pi / 4
        o += line(cx + 52 * s * math.cos(a), cy - 10 * s + 52 * s * math.sin(a), cx + 66 * s * math.cos(a), cy - 10 * s + 66 * s * math.sin(a), ORG, 4)
    o += circ(cx, cy - 10 * s, 38 * s, ORG, EDGE) + rect(cx - 16 * s, cy + 26 * s, 32 * s, 22 * s, PANEL) + line(cx - 12 * s, cy + 56 * s, cx + 12 * s, cy + 56 * s)
    return grp(o, s=1 + 0.03 * math.sin(t * 4), cx=cx, cy=cy) + _lab(cx, cy, s, label, 80)


def gear(cx, cy, s, label="", t=0):
    pts = []
    for k in range(16):
        r = 46 * s if k % 2 == 0 else 36 * s
        a = k * math.pi / 8 + t * 0.9
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(pts, PANEL) + circ(cx, cy, 14 * s, ORG, EDGE, 3) + _lab(cx, cy, s, label, 62)


def shield(cx, cy, s, label="", t=0):
    o = poly([(cx - 40 * s, cy - 40 * s), (cx + 40 * s, cy - 40 * s), (cx + 40 * s, cy + 8 * s), (cx, cy + 50 * s), (cx - 40 * s, cy + 8 * s)], PANEL2)
    o += poly([(cx - 16 * s, cy), (cx - 4 * s, cy + 14 * s), (cx + 20 * s, cy - 16 * s)], "none", ORG, 6, False)
    return o + _lab(cx, cy, s, label, 66)


def lock(cx, cy, s, label="", t=0):
    o = path(f"M{cx-18*s} {cy-6*s} V{cy-24*s} A{18*s} {18*s} 0 0 1 {cx+18*s} {cy-24*s} V{cy-6*s}", "none", INK, 6)
    o += rect(cx - 32 * s, cy - 8 * s, 64 * s, 50 * s, ORG, EDGE) + circ(cx, cy + 16 * s, 6 * s, DARK, DARK, 1)
    return o + _lab(cx, cy, s, label, 62)


def question(cx, cy, s, label="", t=0):
    b = 1 + 0.06 * math.sin(t * 4)
    return grp(txt(cx, cy + 30 * s, "?", 110 * s, ORG), s=b, cx=cx, cy=cy) + _lab(cx, cy, s, label, 60)


def exclaim(cx, cy, s, label="", t=0):
    b = 1 + 0.06 * math.sin(t * 5)
    return grp(txt(cx, cy + 30 * s, "!", 110 * s, ORG), s=b, cx=cx, cy=cy) + _lab(cx, cy, s, label, 60)


def check(cx, cy, s, label="", t=0):
    o = circ(cx, cy, 44 * s, PANEL2) + poly([(cx - 22 * s, cy), (cx - 6 * s, cy + 18 * s), (cx + 24 * s, cy - 20 * s)], "none", ORG, 9, False)
    return o + _lab(cx, cy, s, label, 62)


def cross(cx, cy, s, label="", t=0):
    o = circ(cx, cy, 44 * s, PANEL2) + line(cx - 22 * s, cy - 22 * s, cx + 22 * s, cy + 22 * s, ORG, 9) + line(cx + 22 * s, cy - 22 * s, cx - 22 * s, cy + 22 * s, ORG, 9)
    return o + _lab(cx, cy, s, label, 62)


def fire(cx, cy, s, label="", t=0):
    f = 1 + 0.12 * math.sin(t * 13)
    o = poly([(cx, cy - 52 * s * f), (cx + 30 * s, cy - 6 * s), (cx + 22 * s, cy + 34 * s), (cx - 22 * s, cy + 34 * s), (cx - 30 * s, cy - 6 * s)], ORG, EDGE)
    o += poly([(cx, cy - 14 * s), (cx + 12 * s, cy + 8 * s), (cx + 8 * s, cy + 30 * s), (cx - 8 * s, cy + 30 * s), (cx - 12 * s, cy + 8 * s)], INK, INK, 2)
    return o + _lab(cx, cy, s, label, 56)


def heart(cx, cy, s, label="", t=0):
    d = (f"M{cx} {cy+40*s} C{cx-62*s} {cy-2*s} {cx-34*s} {cy-48*s} {cx} {cy-16*s} "
         f"C{cx+34*s} {cy-48*s} {cx+62*s} {cy-2*s} {cx} {cy+40*s} Z")
    b = 1 + 0.07 * abs(math.sin(t * 3))
    return grp(path(d, ORG, EDGE), s=b, cx=cx, cy=cy) + _lab(cx, cy, s, label, 62)


def balloon(cx, cy, s, label="", t=0):
    b = 1 + 0.05 * math.sin(t * 2.5)
    o = circ(cx, cy - 8 * s, 42 * s, ORG, EDGE) + line(cx, cy + 34 * s, cx + 6 * s, cy + 70 * s)
    return grp(o, s=b, cx=cx, cy=cy) + (txt(cx, cy - 2 * s, label, 14 * s) if label else "")


def tag(cx, cy, s, label="", t=0):
    o = poly([(cx - 52 * s, cy), (cx - 28 * s, cy - 28 * s), (cx + 52 * s, cy - 28 * s), (cx + 52 * s, cy + 28 * s), (cx - 28 * s, cy + 28 * s)], ORG, EDGE)
    o += circ(cx - 32 * s, cy, 5 * s, DARK, DARK, 1)
    return o + (txt(cx + 8 * s, cy + 7 * s, label, 18 * s) if label else "")


def calendar(cx, cy, s, label="", t=0):
    o = rect(cx - 44 * s, cy - 40 * s, 88 * s, 84 * s, PANEL2) + rect(cx - 44 * s, cy - 40 * s, 88 * s, 22 * s, ORG, EDGE, 3)
    return o + (txt(cx, cy + 20 * s, label, 22 * s) if label else "")


def person(cx, cy, s, label="", t=0):
    o = circ(cx, cy - 36 * s, 18 * s, SOFT, INK, 3)
    o += poly([(cx - 24 * s, cy + 44 * s), (cx - 27 * s, cy - 6 * s), (cx - 14 * s, cy - 16 * s), (cx + 14 * s, cy - 16 * s), (cx + 27 * s, cy - 6 * s), (cx + 24 * s, cy + 44 * s)], SOFT, INK, 3)
    return o + _lab(cx, cy, s, label, 66)


def crane(cx, cy, s, label="", t=0):
    sw = math.sin(t * 2.4)
    ex, ey = cx + 30 * s + 14 * s * sw, cy - 40 * s + 50 * s
    o = line(cx - 30 * s, cy + 50 * s, cx - 30 * s, cy - 50 * s, INK, 6) + line(cx - 50 * s, cy - 50 * s, cx + 56 * s, cy - 50 * s, INK, 6)
    o += line(cx + 30 * s, cy - 50 * s, ex, ey, INK, 3) + rect(ex - 18 * s, ey, 36 * s, 24 * s, ORG, EDGE, 3)
    return o + _lab(cx, cy, s, label, 70)


PROPS = {f.__name__: f for f in [
    building, chip, bolt, coin, moneybag, stackcoins, eye, magnifier, cloud, document, newspaper, globe, rocket,
    trophy, scale, datacentre, laptop, phone, bank, house, car, factory, clock, lightbulb, gear, shield, lock,
    question, exclaim, check, cross, fire, heart, balloon, tag, calendar, person, crane]}

PROP_DOC = {
    "building": "company / office / headquarters", "chip": "processor, GPU, semiconductor",
    "bolt": "power, electricity, energy, speed", "coin": "a single dollar / small money",
    "moneybag": "money, profit, funds", "stackcoins": "savings, pile of cash, wealth",
    "eye": "watching, scrutiny, attention, investors", "magnifier": "investigation, audit, looking closely (label shows inside)",
    "cloud": "cloud computing, uncertainty, fog", "document": "report, filing, contract, accounts",
    "newspaper": "news, press report, headline", "globe": "world, countries, global, geography",
    "rocket": "launch, growth, boom, engines", "trophy": "win, record, success", "scale": "balance, fairness, trade-off, verdict",
    "datacentre": "servers, data centres, infrastructure", "laptop": "software, work, using a product, AI tool",
    "phone": "mobile, notifications, messages", "bank": "bank, lender, finance institution", "house": "home, real estate",
    "car": "vehicle, cars", "factory": "manufacturing, industry", "clock": "time, deadline, duration",
    "lightbulb": "idea, insight, lesson", "gear": "process, mechanism, how it works", "shield": "protection, safety, hedge",
    "lock": "security, locked, restricted", "question": "uncertainty, a question", "exclaim": "warning, surprise",
    "check": "confirmed, correct, success", "cross": "wrong, blocked, removed, no", "fire": "danger, hot, urgent",
    "heart": "love, care, health", "balloon": "bubble, inflating, hype (label shows inside)", "tag": "price, label (label inside)",
    "calendar": "date, schedule (label = the date)", "person": "a person, customer, investor, staff",
    "crane": "construction, building projects",
}
