"""Build the editable Bubble Blush Loyal-Tea card (.ai, PDF-compatible) from the
original PNG.

* Artwork (backgrounds, logo, cup, leaves, icons, "Loyal-Tea" lettering,
  card shadows) is vector-traced from the original, one shape per colour.
* Stamp rings, their connector lines and the terms rule are clean vector strokes.
* All other words are live, editable text placed over the original lettering.

Coordinates are pixels of the original image (origin top-left, y down) and are
scaled so one card is 85.6 mm wide, the same scale as the non-editable file.

usage: python build_editable.py original.png out.ai
"""
import os
import sys

import cv2
import numpy as np
import potrace
from fontTools.ttLib import TTFont as FTFont
from reportlab.lib.colors import Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.environ.get("FONT_DIR", os.path.join(HERE, "..", "fonts"))

FONTS = {
    "MPlusRounded-ExtraBold": "MPLUSRounded1c-ExtraBold.ttf",
    "MPlusRounded-Bold": "MPLUSRounded1c-Bold.ttf",
    "SourceSans3-Bold": "SourceSans3-Bold.ttf",
    "SourceSans3-Medium": "SourceSans3-Medium.ttf",
    "Nunito-ExtraBold": "Nunito-ExtraBold.ttf",
    "NotoSansThai-Medium": "NotoSansThai-Medium.ttf",
}
FT = {}
for name, file in FONTS.items():
    path = os.path.join(FONT_DIR, file)
    pdfmetrics.registerFont(TTFont(name, path))
    FT[name] = FTFont(path)
FONT_PATH = {name: os.path.join(FONT_DIR, file) for name, file in FONTS.items()}

# ------------------------------------------------------------------ geometry
CARD_W_PX = 790
PT_PER_PX = 85.6 / 25.4 * 72 / CARD_W_PX
CARDS = {"front": (29.3, 191.5, 819.8, 758.0), "back": (851.0, 191.5, 1642.5, 760.5)}
CARD_R = 30
N_COLOURS = 64                     # colours per card for the vector trace
UPSCALE = 2                        # trace at 2x for finer detail

RING_COLOUR = HexColor("#6F9393")
RING_R, RING_W = 48.4, 4.4
RINGS = [(942.1, 350.3), (1047.5, 350.3), (1153.9, 350.3), (1260.0, 350.3),
         (942.1, 479.8), (1048.2, 479.8), (1153.8, 479.8), (1261.1, 479.8)]
CONNECTOR_W = 3.4
CONNECTORS = []                    # (x0, x1, y): ring to ring, ring 4/9 to the orange stamps
for row in (0, 4):
    xs = [RINGS[row + i][0] for i in range(4)]
    y = RINGS[row][1] - 0.6
    for a, b in zip(xs, xs[1:]):
        CONNECTORS.append((a + RING_R, b - RING_R, y))
    CONNECTORS.append((xs[3] + RING_R, 1323.5 if row == 0 else 1324.5, y))
RULE = (1146.5, 1577.5, 600.2, 2.3, HexColor("#6E8E8A"))

# ------------------------------------------------------------------ text
# (id, runs, fit, region, ink, baseline)
#   runs:     [(text, font, rel_size, rel_rise)]
#   fit:      "cap"   size from cap height, width matched by horizontal scale
#             "space" size from cap height, width matched by letter spacing
#             "width" size from width, no scaling
#             "ref:<id>" same size as an earlier item
#   region:   box around the original lettering
#   ink:      "dark" or "orange" (how to find the lettering pixels)
#   baseline: explicit baseline for lines with descenders, else the ink bottom
SUP = 0.62, 0.36
TEXT = [
    ("bubble_blush", [("BUBBLE BLUSH", "MPlusRounded-ExtraBold", 1, 0)], "space", (300, 368, 570, 409), "dark", None),
    ("tagline", [("SIP  •  COLLECT  •  ENJOY", "SourceSans3-Bold", 1, 0)], "space", (272, 630, 608, 656), "dark", None),
    ("card", [("CARD", "MPlusRounded-ExtraBold", 1, 0)], "cap", (362, 534, 552, 598), "orange", None),
    ("terms_title", [("TERMS & CONDITIONS", "SourceSans3-Bold", 1, 0)], "cap", (886, 586, 1138, 612), "dark", None),
    ("term2", [("Free topping with your 5th drink.", "SourceSans3-Medium", 1, 0)], "width", (915, 646, 1530, 676), "dark", 665.5),
    ("term1a", [("1 stamp per purchase", "SourceSans3-Medium", 1, 0)], "width", (915, 615, 1126, 647), "dark", 637),
    ("term1b", [("Max. 1 stamp per day", "SourceSans3-Medium", 1, 0)], "width", (1142, 615, 1530, 647), "dark", 637),
    ("term3", [("Free regular drink on your 10th visit (or a dessert under ", "SourceSans3-Medium", 1, 0),
               ("฿", "NotoSansThai-Medium", 1, 0), ("200).", "SourceSans3-Medium", 1, 0)], "ref:term2", (915, 674, 1530, 704), "dark", 693.5),
    ("term4", [("Rewards cannot be exchanged for cash.", "SourceSans3-Medium", 1, 0)], "width", (915, 702, 1530, 731), "dark", 719.5),
    ("term5", [("Original card required for redemption.", "SourceSans3-Medium", 1, 0)], "width", (915, 728, 1530, 758), "dark", 745.5),
    ("r5_title", [("5", "Nunito-ExtraBold", 1, 0), ("th", "Nunito-ExtraBold", *SUP),
                  (" Drink", "Nunito-ExtraBold", 1, 0)], "cap", (1465, 293, 1605, 325), "orange", None),
    ("r5_free", [("FREE TOPPING", "Nunito-ExtraBold", 1, 0)], "cap", (1452, 326, 1618, 356), "orange", None),
    ("r5_choice", [("of your choice", "SourceSans3-Medium", 1, 0)], "width", (1465, 355, 1605, 383), "dark", 373),
    ("r10_title", [("10", "Nunito-ExtraBold", 1, 0), ("th", "Nunito-ExtraBold", *SUP),
                   (" Visit", "Nunito-ExtraBold", 1, 0)], "cap", (1470, 430, 1610, 463), "orange", None),
    ("r10_free", [("FREE REGULAR", "Nunito-ExtraBold", 1, 0)], "cap", (1455, 465, 1622, 494), "orange", None),
    ("r10_drink", [("DRINK", "Nunito-ExtraBold", 1, 0)], "cap", (1495, 493, 1585, 521), "orange", None),
    ("r10_or", [("(or a dessert", "SourceSans3-Medium", 1, 0)], "width", (1478, 519, 1600, 545), "dark", 537),
    ("r10_under", [("under ", "SourceSans3-Medium", 1, 0), ("฿", "NotoSansThai-Medium", 1, 0),
                   ("200)", "SourceSans3-Medium", 1, 0)], "ref:r10_or", (1478, 543, 1600, 568), "dark", 559),
    ("stamp5", [("5", "SourceSans3-Bold", 1, 0)], "cap", (1352, 309, 1398, 352), "orange", None),
    ("stamp10", [("10", "SourceSans3-Bold", 1, 0)], "cap", (1350, 432, 1404, 474), "orange", None),
]
for (x, y), label in zip(RINGS, ["1", "2", "3", "4", "6", "7", "8", "9"]):
    TEXT.append((f"stamp{label}", [(label, "SourceSans3-Bold", 1, 0)], "cap",
                 (int(x) - 24, int(y) - 28, int(x) + 24, int(y) + 26), "dark", None))

HEADING = ("COLLECT AND ENJOY", "MPlusRounded-Bold", (1056, 228, 1410, 272))
BULLETS = [(903.65, y) for y in (632.1, 660.5, 688.15, 714.55, 740.8)]
BULLET_R = 4.35
INLINE_BULLETS = [(1134.9, 631.2, 3.35)]       # the dot between "purchase" and "Max."
INLINE_BULLET_REGION = (1127, 622, 1142, 641)
BULLET_REGION = (893, 620, 914, 750)


# ------------------------------------------------------------------ fonts
def glyph_bounds(font, ch):
    ft = FT[font]
    gname = ft.getBestCmap().get(ord(ch))
    if gname is None:
        raise ValueError(f"{font} has no glyph for {ch!r}")
    upm = ft["head"].unitsPerEm
    adv = ft["hmtx"][gname][0] / upm
    g = ft["glyf"][gname]
    if g.numberOfContours == 0:
        return adv, None
    g.recalcBounds(ft["glyf"])
    return adv, (g.xMin / upm, g.yMin / upm, g.xMax / upm, g.yMax / upm)


def layout(runs, size, hscale=1.0, space=0.0):
    """Ink extent (x0, x1) relative to the text origin, in px."""
    x = 0.0
    xs = []
    n = sum(len(t) for t, *_ in runs)
    k = 0
    for text, font, rel, rise in runs:
        s = size * rel
        for ch in text:
            adv, b = glyph_bounds(font, ch)
            if b:
                xs += [(x + b[0] * s) * hscale, (x + b[2] * s) * hscale]
            x += adv * s
            k += 1
            if k < n:
                x += space
    return min(xs), max(xs)


def cap_ratio(runs):
    text, font, rel, rise = runs[0]
    return max(glyph_bounds(font, ch)[1][3] for ch in text if glyph_bounds(font, ch)[1])


# ------------------------------------------------------------------ pixels
def lum_of(img):
    f = img.astype(np.float32)
    return 0.114 * f[..., 0] + 0.587 * f[..., 1] + 0.299 * f[..., 2]


def text_mask(img, region, ink):
    """Lettering pixels inside region; pieces touching the region edge are
    ignored (they belong to neighbouring artwork)."""
    x0, y0, x1, y1 = region
    sub = img[y0:y1, x0:x1].astype(int)
    b, g, r = sub[..., 0], sub[..., 1], sub[..., 2]
    if ink == "orange":
        m = (r > 190) & (g < 140) & (b < 120)
    else:
        m = lum_of(img[y0:y1, x0:x1]) < 175
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    keep = np.zeros(n, bool)
    for i in range(1, n):
        sx, sy, sw, sh, area = stats[i]
        keep[i] = sx > 0 and sy > 0 and sx + sw < m.shape[1] and sy + sh < m.shape[0]
    full = np.zeros(img.shape[:2], bool)
    full[y0:y1, x0:x1] = keep[lab]
    return full


def ink_colour(img, m):
    core = cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    if core.sum() < 20:
        core = m
    px = img[core].astype(int)
    lum = px @ np.array([0.114, 0.587, 0.299])
    sel = px[lum <= np.percentile(lum, 50)]
    b, g, r = np.median(sel, axis=0)
    return Color(r / 255, g / 255, b / 255)


def bbox(m):
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def coverage(img, m, region, ink):
    """Soft 0..1 ink coverage of the original lettering inside region."""
    X0, Y0, X1, Y1 = region
    sub = (slice(Y0, Y1), slice(X0, X1))
    keep = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)[sub]
    ch = img[..., 1][sub].astype(np.float32) if ink == "orange" else lum_of(img)[sub]
    bgv = np.median(ch[~keep]) if (~keep).sum() > 20 else 245.0
    inkv = np.percentile(ch[m[sub]], 10)
    return np.clip((bgv - ch) / (bgv - inkv), 0, 1) * keep


def render_cov(runs, size, hs, sp, x, base, region, ss=4):
    """Soft coverage of our text, rendered with FreeType at ss x supersampling."""
    from PIL import Image, ImageDraw, ImageFont
    X0, Y0, X1, Y1 = region
    w, h = X1 - X0, Y1 - Y0
    pad = 20.0
    tmp = Image.new("L", (int((w / hs + 2 * pad) * ss), h * ss), 0)
    d = ImageDraw.Draw(tmp)
    pen = pad
    n = sum(len(t) for t, *_ in runs)
    k = 0
    for text, font, rel, rise in runs:
        f = ImageFont.truetype(FONT_PATH[font], size * rel * ss)
        for ch in text:
            d.text((pen * ss, (base - Y0 - size * rise) * ss), ch, font=f, fill=255, anchor="ls")
            pen += glyph_bounds(font, ch)[0] * size * rel
            k += 1
            if k < n:
                pen += sp
    tmp = tmp.resize((max(1, int(round(tmp.width * hs))), tmp.height), Image.LANCZOS)
    out = Image.new("L", (w * ss, h * ss), 0)
    out.paste(tmp, (int(round((x - X0 - pad * hs) * ss)), 0))
    return np.asarray(out.resize((w, h), Image.BOX), np.float32) / 255


def refine(cov, runs, size, hs, sp, x, base, region, step=0.25, reach=2.5, reach_x=1.0):
    """Nudge the text (up to reach_x px sideways, `reach` px up/down) so it
    overlaps the original lettering best."""
    def score(dx, dy):
        r = render_cov(runs, size, hs, sp, x + dx, base + dy, region)
        return np.minimum(cov, r).sum() / max(np.maximum(cov, r).sum(), 1e-6)
    best = (score(0, 0), 0.0, 0.0)
    for dy in np.arange(-reach, reach + 1e-6, 0.5):
        for dx in np.arange(-reach_x, reach_x + 1e-6, 0.5):
            s = score(dx, dy)
            if s > best[0]:
                best = (s, dx, dy)
    _, bx, by = best
    for dy in np.arange(by - 0.5, by + 0.51, step):
        for dx in np.arange(max(bx - 0.5, -reach_x), min(bx + 0.5, reach_x) + 1e-6, step):
            s = score(dx, dy)
            if s > best[0]:
                best = (s, dx, dy)
    return best


def rounded_mask(shape, box, r, grow=0.0):
    x0, y0, x1, y1 = box
    Y, X = np.mgrid[0:shape[0], 0:shape[1]] + 0.5
    cx = np.clip(X, x0 + r, x1 - r)
    cy = np.clip(Y, y0 + r, y1 - r)
    return np.hypot(X - cx, Y - cy) <= r + grow


# ------------------------------------------------------------------ tracing
def trace(mask):
    # potracer treats True as white paper, so pass the inverse
    return potrace.Bitmap(~mask).trace(turdsize=4, alphamax=1.0, opticurve=True, opttolerance=0.3)


def trace_card(img, box, k, up=UPSCALE):
    """Posterise one card to k colours and trace each colour region.

    The card is enlarged `up` times first so small details (pearls, icon
    lines, arrow) keep their shape; coordinates are scaled back afterwards."""
    x0, y0 = int(box[0]) - 3, int(box[1]) - 3
    x1, y1 = int(np.ceil(box[2])) + 3, int(np.ceil(box[3])) + 3
    sub = img[y0:y1, x0:x1].copy()
    inside = rounded_mask(img.shape, box, CARD_R, grow=-2.0)[y0:y1, x0:x1]
    # replace the card edge and the outside with colours from just inside the card
    sub = cv2.inpaint(sub, (~inside).astype(np.uint8), 4, cv2.INPAINT_TELEA)
    big = cv2.resize(sub, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC)
    smooth = cv2.pyrMeanShiftFiltering(big, 3 * up, 10)
    smooth = cv2.bilateralFilter(smooth, 5 * up, 18, 3 * up)
    lab = cv2.cvtColor(smooth, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    cv2.setRNGSeed(7)
    _, labels, _ = cv2.kmeans(lab, k, None, crit, 2, cv2.KMEANS_PP_CENTERS)
    labels = labels.reshape(big.shape[:2])
    win = 2 * up + 1
    votes = np.stack([cv2.boxFilter((labels == i).astype(np.float32), -1, (win, win)) for i in range(k)])
    labels = votes.argmax(0)                       # majority filter removes speckles
    shapes = []
    for i in range(k):
        m = labels == i
        area = int(m.sum())
        if area < 6 * up * up:
            continue
        core = cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        b, g, r = np.median(big[core if core.sum() >= 20 else m].reshape(-1, 3), axis=0)
        curves = potrace.Bitmap(~m).trace(turdsize=3 * up * up, alphamax=1.0, opticurve=True,
                                          opttolerance=0.25)
        shapes.append((area, Color(r / 255, g / 255, b / 255), curves, x0, y0))
    shapes.sort(key=lambda s: -s[0])
    base = shapes[0][1]
    return base, shapes, 1.0 / up


def trace_background(img, step=2.0):
    """White page and card shadows as stacked, nested grey shapes."""
    inside = np.zeros(img.shape[:2], bool)
    for box in CARDS.values():
        inside |= rounded_mask(img.shape, box, CARD_R, grow=1.0)
    blur = cv2.GaussianBlur(img, (0, 0), 2.0)
    lum = lum_of(blur)
    # under the cards, continue the nearest outside value so no level edge shows at the card edge
    _, idx = cv2.distanceTransformWithLabels((~inside).astype(np.uint8) * 0 + inside.astype(np.uint8),
                                             cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(~inside)
    lut = np.zeros(idx.max() + 1, np.float32)
    lut[idx[~inside]] = lum[~inside]
    lum = np.where(inside, lut[idx], lum)
    out_lum = lum[~inside]
    top = float(np.percentile(out_lum, 99.5))
    levels = np.arange(top - step, out_lum.min() - step, -step)
    base_px = blur[~inside & (lum > top - step)]
    b, g, r = base_px.reshape(-1, 3).mean(0)
    shapes = []
    for lv in levels:
        m = lum <= lv
        band = ~inside & m & (lum > lv - step)
        if band.sum() < 10:
            band = ~inside & m
            if band.sum() == 0:
                continue
        bb, gg, rr = blur[band].reshape(-1, 3).mean(0)
        shapes.append((Color(rr / 255, gg / 255, bb / 255), trace(m)))
    return Color(r / 255, g / 255, b / 255), shapes


def add_curves(path, curves, dx=0.0, dy=0.0, k=1.0):
    """Append potrace curves; points are scaled by k, then offset by (dx, dy)."""
    for c in curves:
        p = c.start_point
        path.moveTo(p.x * k + dx, p.y * k + dy)
        for s in c.segments:
            if s.is_corner:
                path.lineTo(s.c.x * k + dx, s.c.y * k + dy)
                path.lineTo(s.end_point.x * k + dx, s.end_point.y * k + dy)
            else:
                path.curveTo(s.c1.x * k + dx, s.c1.y * k + dy, s.c2.x * k + dx, s.c2.y * k + dy,
                             s.end_point.x * k + dx, s.end_point.y * k + dy)
        path.close()


# ------------------------------------------------------------------ logo
LOGO_REGION = (371, 209, 498, 369)
LOGO_W = 7.6
LOGO_LIGHT, LOGO_DARK = HexColor("#8AB0A8"), HexColor("#568E87")
STRAW = (414.2, 215.0, 424.4, 324.3)
STRAW_COLOUR = HexColor("#578E88")
HALO = HexColor("#FDFAF2")
BAND_ORANGE, BAND_LIGHT = HexColor("#F59E45"), HexColor("#F3EFD6")
LOGO_BUBBLES = [(401.0, 330.0, 7.0, "#3A7B78"), (445.0, 315.0, 5.4, "#387C76"),
                (459.0, 332.4, 8.4, "#33716C"), (431.0, 343.0, 10.4, "#3C7A75")]


def arc(cx, cy, rx, ry, a0, a1, n=40):
    t = np.radians(np.linspace(a0, a1, n))
    return list(zip(cx + rx * np.cos(t), cy + ry * np.sin(t)))


def logo_outline():
    """Outline of the 'B' monogram (a stroked centre line) as a polygon."""
    from shapely.geometry import LineString, MultiLineString
    from shapely.ops import unary_union
    left, top, mid, bottom = 381.0, 246.2, 293.5, 360.5
    loop = ([(left, 322.0), (left, top), (459.0, top)]
            + arc(459.0, (top + mid) / 2, 23.65, (mid - top) / 2, -90, 90)
            + arc(459.5, (mid + bottom) / 2, 28.9, (bottom - mid) / 2, -90, 90)
            + [(419.5, bottom)]
            + arc(419.5, 322.0, 38.5, 38.5, 90, 180))
    bar = [(left, mid), (459.0, mid)]
    lines = unary_union(MultiLineString([LineString(loop), LineString(bar)]))
    return lines.buffer(LOGO_W / 2, quad_segs=16, cap_style="round", join_style="round")


def draw_polygon(c, poly):
    p = c.beginPath()
    polys = getattr(poly, "geoms", [poly])
    for pg in polys:
        for ring in [pg.exterior, *pg.interiors]:
            pts = list(ring.coords)
            p.moveTo(*pts[0])
            for q in pts[1:]:
                p.lineTo(*q)
            p.close()
    return p


HEADLINE_REGION = (200, 405, 722, 585)          # "Loyal-Tea" lettering and its accent marks


def headline_mask(img, exclude):
    x0, y0, x1, y1 = HEADLINE_REGION
    sub = img[y0:y1, x0:x1].astype(int)
    m = (sub[..., 2] > 190) & (sub[..., 1] < 150) & (sub[..., 0] < 120) & ~exclude[y0:y1, x0:x1]
    full = np.zeros(img.shape[:2], bool)
    full[y0:y1, x0:x1] = m
    return full


def trace_headline(img, m, up=4):
    """Smooth outline of the hand-lettered headline, traced at `up` x."""
    x0, y0, x1, y1 = HEADLINE_REGION
    g = img[y0:y1, x0:x1, 1].astype(np.float32)
    ink = np.percentile(g[m[y0:y1, x0:x1]], 20)
    bg = 245.0
    cov = np.clip((bg - g) / (bg - ink), 0, 1)
    cov *= cv2.dilate(m[y0:y1, x0:x1].astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    big = cv2.resize(cov, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(big, (0, 0), up * 0.6)
    shape = big > 0.5
    curves = potrace.Bitmap(~shape).trace(turdsize=4 * up * up, alphamax=1.1, opticurve=True,
                                          opttolerance=0.3)
    px = img[y0:y1, x0:x1][cv2.erode(m[y0:y1, x0:x1].astype(np.uint8), np.ones((3, 3), np.uint8)) > 0]
    b, gg, r = np.median(px, axis=0)
    return curves, (x0, y0, 1.0 / up), Color(r / 255, gg / 255, b / 255)


def draw_logo(c):
    # B monogram, light-to-dark gradient from left to right
    c.saveState()
    c.clipPath(draw_polygon(c, logo_outline()), stroke=0, fill=0, fillMode=0)
    c.linearGradient(377, 0, 492, 0, (LOGO_LIGHT, LOGO_DARK), extend=True)
    c.restoreState()
    # straw with its light outline and orange band
    x0, y0, x1, y1 = STRAW
    c.setFillColor(STRAW_COLOUR)
    c.setStrokeColor(HALO)
    c.setLineWidth(2.2)
    c.roundRect(x0, y0, x1 - x0, y1 - y0, 2.5, stroke=1, fill=1)
    c.setFillColor(BAND_ORANGE)
    c.rect(x0 - 0.6, 242.4, (x1 - x0) + 1.2, 5.0, stroke=0, fill=1)
    c.setFillColor(BAND_LIGHT)
    c.rect(417.4, 243.0, 3.6, 3.8, stroke=0, fill=1)
    # bubbles with their light outline
    for x, y, r, col in LOGO_BUBBLES:
        c.setFillColor(HexColor(col))
        c.setStrokeColor(HALO)
        c.setLineWidth(1.6)
        c.circle(x, y, r, stroke=1, fill=1)


# ------------------------------------------------------------------ drawing
def draw_text(c, runs, x, y, size, colour, hscale=1.0, space=0.0):
    c.saveState()
    c.translate(x, y)
    c.scale(1, -1)
    t = c.beginText(0, 0)
    t.setFillColor(colour)
    t.setHorizScale(hscale * 100)
    t.setCharSpace(space)
    for text, font, rel, rise in runs:
        t.setFont(font, size * rel)
        t.setRise(size * rise)
        t.textOut(text)
    t.setRise(0)
    c.drawText(t)
    c.restoreState()


def build(src, out):
    img = cv2.imread(src)
    H, W = img.shape[:2]
    lum = lum_of(img)
    Y, X = np.mgrid[0:H, 0:W] + 0.5

    # 1. lettering that becomes live text
    remove = np.zeros((H, W), bool)
    placed = []
    for tid, runs, fit, region, ink, baseline in TEXT:
        m = text_mask(img, region, ink)
        if m.sum() == 0:
            raise RuntimeError(f"no lettering found for {tid}")
        x0, y0, x1, y1 = bbox(m)
        colour = ink_colour(img, m)
        remove |= m
        base = baseline if baseline is not None else y1 - 0.5
        if fit.startswith("ref:"):
            # same size as a neighbouring line (the ฿ glyph differs, so width can't be used)
            size = next(t["size"] for t in placed if t["id"] == fit[4:])
            hs, sp = 1.0, 0.0
        elif fit == "width":
            l0, l1 = layout(runs, 1.0)
            size = (x1 - x0) / (l1 - l0)
            hs, sp = 1.0, 0.0
        else:
            size = (base - y0) / cap_ratio(runs)
            l0, l1 = layout(runs, size)
            if fit == "cap":
                hs, sp = (x1 - x0) / (l1 - l0), 0.0
            else:
                n = sum(len(t) for t, *_ in runs)
                hs, sp = 1.0, ((x1 - x0) - (l1 - l0)) / (n - 1)
        l0, _ = layout(runs, size, hs, sp)
        x = x0 - l0
        cov = coverage(img, m, region, ink)
        match, dx, dy = refine(cov, runs, size, hs, sp, x, base, region)
        placed.append(dict(id=tid, runs=runs, x=x + dx, y=base + dy, size=size, colour=colour,
                           hs=hs, sp=sp, ink=(int(x0), int(y0), int(x1), int(y1)),
                           match=match, shift=(dx, dy)))

    # heading on an arc: one live letter per letter of the original
    text, font, region = HEADING
    hm = text_mask(img, region, "dark")
    remove |= hm
    n_lab, _, stats, _ = cv2.connectedComponentsWithStats(hm.astype(np.uint8), connectivity=8)
    comps = sorted([stats[i] for i in range(1, n_lab) if stats[i][4] > 15], key=lambda s: s[0])
    letters = text.replace(" ", "")
    if len(comps) != len(letters):
        raise RuntimeError(f"heading: found {len(comps)} letters, expected {len(letters)}")
    cxs = np.array([s[0] + s[2] / 2 for s in comps])
    bottoms = np.array([s[1] + s[3] for s in comps], float) - 0.5
    tops = np.array([s[1] for s in comps], float)
    flat = [i for i, ch in enumerate(letters) if ch in "ELTNDAY"]
    fitb = np.polyfit(cxs[flat], bottoms[flat], 2)
    cap = np.median(bottoms[flat] - tops[flat])
    hsize = cap / glyph_bounds(font, "E")[1][3]
    hcolour = ink_colour(img, hm)
    heading = []
    for ch, s, x in zip(letters, comps, cxs):
        b = np.polyval(fitb, x)
        ang = float(np.degrees(np.arctan(2 * fitb[0] * x + fitb[1])))
        _, gb = glyph_bounds(font, ch)
        w_ink = (gb[2] - gb[0]) * hsize
        hs = s[2] / w_ink
        ox = -(gb[0] * hsize + w_ink / 2) * hs
        heading.append((ch, x, b, ang, ox, hs))

    bm = text_mask(img, BULLET_REGION, "dark") | text_mask(img, INLINE_BULLET_REGION, "dark")
    remove |= bm
    bullet_colour = ink_colour(img, bm)

    # 2. rings, connectors and the rule become clean strokes
    for cx, cy in RINGS:
        d = np.hypot(X - cx, Y - cy)
        remove |= (np.abs(d - RING_R) < RING_W / 2 + 1.5) & (lum < 225)
    for x0, x1, y in CONNECTORS:
        remove |= (X > x0 - 2) & (X < x1 + 2) & (np.abs(Y - y) < CONNECTOR_W / 2 + 1.5) & (lum < 225)
    rx0, rx1, ry, rw, _ = RULE
    remove |= (X > rx0 - 2) & (X < rx1 + 2) & (np.abs(Y - ry) < rw / 2 + 1.5) & (lum < 235)

    # 3. the "B" monogram is redrawn as clean geometry
    lx0, ly0, lx1, ly1 = LOGO_REGION
    logo = np.zeros((H, W), bool)
    sub = img[ly0:ly1, lx0:lx1].astype(int)
    logo[ly0:ly1, lx0:lx1] = (lum[ly0:ly1, lx0:lx1] < 238) | ((sub[..., 2] - sub[..., 0]) > 40)
    remove |= cv2.dilate(logo.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)

    # 4. the "Loyal-Tea" lettering gets its own smooth outline
    head = headline_mask(img, remove)
    head_curves, head_xf, head_colour = trace_headline(img, head)
    remove |= head

    remove = cv2.dilate(remove.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=1)
    clean = cv2.inpaint(img, remove, 5, cv2.INPAINT_TELEA)

    # 5. trace
    bg_colour, bg_shapes = trace_background(img)
    cards = {name: trace_card(clean, box, N_COLOURS) for name, box in CARDS.items()}

    # 6. write the file
    c = rl_canvas.Canvas(out, pagesize=(W * PT_PER_PX, H * PT_PER_PX), initialFontName="SourceSans3-Medium")
    c.setTitle("Bubble Blush Loyal-Tea Card (editable)")
    c.setAuthor("Bubble Blush")
    c.setCreator("Vector trace of the original artwork with live text")
    c.translate(0, H * PT_PER_PX)
    c.scale(PT_PER_PX, -PT_PER_PX)
    c.setLineJoin(1)

    # background and shadows
    c.setFillColor(bg_colour)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    for colour, curves in bg_shapes:
        p = c.beginPath()
        add_curves(p, curves)
        c.setFillColor(colour)
        c.drawPath(p, fill=1, stroke=0, fillMode=0)

    # card artwork, clipped to the card shape
    for name, box in CARDS.items():
        base, shapes, k = cards[name]
        c.saveState()
        clip = c.beginPath()
        clip.roundRect(box[0], box[1], box[2] - box[0], box[3] - box[1], CARD_R)
        c.clipPath(clip, stroke=0, fill=0)
        c.setFillColor(base)
        c.rect(box[0], box[1], box[2] - box[0], box[3] - box[1], fill=1, stroke=0)
        for area, colour, curves, dx, dy in shapes:
            p = c.beginPath()
            add_curves(p, curves, dx, dy, k)
            c.setFillColor(colour)
            c.setStrokeColor(colour)
            c.setLineWidth(0.9)
            c.drawPath(p, fill=1, stroke=1, fillMode=0)
        c.restoreState()

    draw_logo(c)
    hx, hy, hk = head_xf
    p = c.beginPath()
    add_curves(p, head_curves, hx, hy, hk)
    c.setStrokeColor(HALO)
    c.setLineWidth(2.6)
    c.drawPath(p, fill=0, stroke=1)
    c.setFillColor(head_colour)
    c.drawPath(p, fill=1, stroke=0, fillMode=0)

    # stamp rings, connectors, rule
    c.setStrokeColor(RING_COLOUR)
    c.setLineWidth(RING_W)
    for cx, cy in RINGS:
        c.circle(cx, cy, RING_R, stroke=1, fill=0)
    c.setLineWidth(CONNECTOR_W)
    c.setLineCap(0)
    for x0, x1, y in CONNECTORS:
        c.line(x0, y, x1, y)
    rx0, rx1, ry, rw, rcol = RULE
    c.setStrokeColor(rcol)
    c.setLineWidth(rw)
    c.line(rx0, ry, rx1, ry)

    # live text
    for t in placed:
        draw_text(c, t["runs"], t["x"], t["y"], t["size"], t["colour"], t["hs"], t["sp"])
    for ch, x, b, ang, ox, hs in heading:
        c.saveState()
        c.translate(x, b)
        c.rotate(ang)
        draw_text(c, [(ch, font, 1, 0)], ox, 0, hsize, hcolour, hs)
        c.restoreState()
    c.setFillColor(bullet_colour)
    for x, y in BULLETS:
        c.circle(x, y, BULLET_R, fill=1, stroke=0)
    for x, y, r in INLINE_BULLETS:
        c.circle(x, y, r, fill=1, stroke=0)

    c.showPage()
    c.save()
    return placed


if __name__ == "__main__":
    placed = build(sys.argv[1], sys.argv[2])
    for t in placed:
        print(f"{t['id']:12s} size {t['size']:5.1f}px  hscale {t['hs'] * 100:5.1f}%  "
              f"spacing {t['sp']:4.1f}  shift {t['shift'][0]:+.2f},{t['shift'][1]:+.2f}  "
              f"overlap {t['match']:.3f}")
    print("wrote", sys.argv[2])
