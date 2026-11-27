"""Low-level drawing helpers: wobbly neon line art on a dark background.

Every helper draws a faint wide 'glow' stroke under the real stroke.
Jitter is driven by a module-level RNG that the renderer re-seeds for every
frame, so shapes keep the same wobble from frame to frame (no flicker).
"""
import math, random, html

R = random.Random()
ORG = "#ff6a00"      # accent
EDGE = "#ffb27a"     # light edge for orange fills
INK = "#ffffff"      # outlines and text
DARK = "#101014"     # default fill
PANEL = "#26262e"
PANEL2 = "#1e1e27"
PANEL3 = "#2c2c36"
SOFT = "#e6e6e6"     # pale 'person' figures


def seed(n):
    R.seed(n)


def J(v, a=1.5):
    return v + R.uniform(-a, a)


def esc(s):
    return html.escape(str(s), quote=False)


def _stroke(d, col, w, dash=None, fill="none"):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w + 8}" stroke-opacity=".14"'
            f' stroke-linecap="round" stroke-linejoin="round"{da}/>'
            f'<path d="{d}" fill="{fill}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"'
            f' stroke-linejoin="round"{da}/>')


def line(x1, y1, x2, y2, col=INK, w=4, dash=None):
    mx = (x1 + x2) / 2 + R.uniform(-2, 2)
    my = (y1 + y2) / 2 + R.uniform(-2, 2)
    d = f"M{J(x1, 1):.1f} {J(y1, 1):.1f} Q{mx:.1f} {my:.1f} {J(x2, 1):.1f} {J(y2, 1):.1f}"
    return _stroke(d, col, w, dash)


def poly(pts, fill="none", col=INK, w=4, close=True):
    p = [(J(x), J(y)) for x, y in pts]
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in p) + (" Z" if close else "")
    return _stroke(d, col, w, None, fill)


def path(d, fill="none", col=INK, w=4):
    return _stroke(d, col, w, None, fill)


def rect(x, y, w, h, fill=DARK, col=INK, sw=4):
    return poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, col, sw)


def circ(cx, cy, r, fill=DARK, col=INK, sw=4):
    n = 18
    pts = [(cx + (r + R.uniform(-1, 1)) * math.cos(2 * math.pi * k / n),
            cy + (r + R.uniform(-1, 1)) * math.sin(2 * math.pi * k / n)) for k in range(n)]
    return poly(pts, fill, col, sw)


def txt(x, y, s, size=16, fill=INK, anchor="middle", bold=True):
    wt = ' font-weight="bold"' if bold else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size:.1f}"'
            f' font-family="DejaVu Sans, Arial, sans-serif" fill="{fill}"{wt}>{esc(s)}</text>')


def arrow(x1, y1, x2, y2, col=ORG, w=5):
    a = math.atan2(y2 - y1, x2 - x1)
    h = 14
    return (line(x1, y1, x2, y2, col, w)
            + line(x2, y2, x2 - h * math.cos(a - 0.5), y2 - h * math.sin(a - 0.5), col, w)
            + line(x2, y2, x2 - h * math.cos(a + 0.5), y2 - h * math.sin(a + 0.5), col, w))


def grp(inner, dx=0.0, dy=0.0, s=1.0, rot=0.0, alpha=1.0, cx=0.0, cy=0.0):
    """Wrap svg in a group: translate, then scale/rotate about (cx, cy), with opacity."""
    a = max(0.0, min(1.0, alpha))
    return (f'<g opacity="{a:.3f}" transform="translate({dx:.2f},{dy:.2f}) translate({cx:.2f},{cy:.2f})'
            f' rotate({rot:.2f}) scale({max(s, 0.001):.3f}) translate({-cx:.2f},{-cy:.2f})">{inner}</g>')


def cl(x):
    return max(0.0, min(1.0, x))


def ez(x):
    x = cl(x)
    return x * x * (3 - 2 * x)
