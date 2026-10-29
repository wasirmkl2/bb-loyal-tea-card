"""Rebuild the Bubble Blush Loyal-Tea card as vector artwork and save it as a
PDF-compatible Adobe Illustrator file (.ai).

All drawing is done in the pixel coordinates of the 1024 x 576 reference image
(origin top-left, y down) and scaled so that one card is 85.6 mm wide.
"""
import math
import os
import sys

from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "fonts")

for name, file in [
    ("Chewy", "Chewy-Regular.ttf"),
    ("Fredoka-SemiBold", "Fredoka-SemiBold.ttf"),
    ("Nunito-SemiBold", "Nunito-SemiBold.ttf"),
    ("Nunito-ExtraBold", "Nunito-ExtraBold.ttf"),
    ("NotoSansThai-Medium", "NotoSansThai-Medium.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, file)))

# ---------------------------------------------------------------- geometry
IMG_W, IMG_H = 1024, 576
CARD_W_PX = 484                      # one card in the reference image
MM = 72 / 25.4
S = 85.6 * MM / CARD_W_PX            # points per reference pixel
PAGE_W, PAGE_H = IMG_W * S, IMG_H * S

FRONT = (18, 117, 502, 464)
BACK = (522, 117, 1006, 464)
CARD_R = 15

# ---------------------------------------------------------------- colours
WHITE = HexColor("#FFFFFF")
CREAM = HexColor("#FBF1E4")
CREAM_LIGHT = HexColor("#FCF6EE")
TEAL_PALE = HexColor("#CFE9E1")
TEAL_LIGHT = HexColor("#AEDACE")
TEAL_MID = HexColor("#8CC8B9")
TEAL_LEAF = HexColor("#6DB3A2")
TEAL_LEAF_DARK = HexColor("#4F9B8A")
TEAL_LOGO = HexColor("#5C9189")
TEAL_TEXT = HexColor("#3F7E78")
TEAL_HEAD = HexColor("#2E6B67")
TEAL_STRAW = HexColor("#3E9B8D")
TEAL_STRAW_DARK = HexColor("#2C7C70")
ORANGE = HexColor("#F2691C")
ORANGE_SOFT = HexColor("#F4A15D")
ORANGE_SPARK = HexColor("#F6A85E")
PEACH = HexColor("#FDE1C6")
PEACH_CIRCLE = HexColor("#FDE6D0")
GREY_RING = HexColor("#8FAAA6")
GREY_NUM = HexColor("#6B8583")
BODY = HexColor("#45423F")
PEARL = HexColor("#3B2216")
PEARL_HI = HexColor("#6A4231")
TEA_TOP = HexColor("#F8CB98")
TEA_BOTTOM = HexColor("#EFA463")


def rgba(hex_, a):
    c = HexColor(hex_)
    return Color(c.red, c.green, c.blue, alpha=a)


class Card:
    def __init__(self, path):
        self.c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
        self.c.setTitle("Bubble Blush Loyal-Tea Card (editable)")
        self.c.setAuthor("Bubble Blush")
        self.c.setSubject("Loyalty card, front and back")
        self.c.setCreator("Vector rebuild")
        # pixel space: origin top-left, y down
        self.c.translate(0, PAGE_H)
        self.c.scale(S, -S)

    # ---------------------------------------------------------- primitives
    def fill(self, colour, alpha=1.0):
        self.c.setFillColor(colour)
        self.c.setFillAlpha(alpha)

    def stroke(self, colour, width, alpha=1.0, cap=1, join=1):
        self.c.setStrokeColor(colour)
        self.c.setStrokeAlpha(alpha)
        self.c.setLineWidth(width)
        self.c.setLineCap(cap)
        self.c.setLineJoin(join)

    def path(self, cmds):
        """cmds: list of ('M',x,y) ('L',x,y) ('C',x1,y1,x2,y2,x,y) ('Z',)"""
        p = self.c.beginPath()
        for cmd in cmds:
            op, *a = cmd
            if op == "M":
                p.moveTo(*a)
            elif op == "L":
                p.lineTo(*a)
            elif op == "C":
                p.curveTo(*a)
            elif op == "Z":
                p.close()
        return p

    def draw(self, cmds, fill=None, stroke=None, alpha=1.0, width=1.0):
        if fill is not None:
            self.fill(fill, alpha)
        if stroke is not None:
            self.stroke(stroke, width, alpha)
        self.c.drawPath(self.path(cmds), fill=int(fill is not None),
                        stroke=int(stroke is not None))

    def round_rect(self, x0, y0, x1, y1, r, fill=None, stroke=None, width=1.0, alpha=1.0):
        if fill is not None:
            self.fill(fill, alpha)
        if stroke is not None:
            self.stroke(stroke, width, alpha)
        self.c.roundRect(x0, y0, x1 - x0, y1 - y0, r,
                         fill=int(fill is not None), stroke=int(stroke is not None))

    def circle(self, x, y, r, fill=None, stroke=None, width=1.0, alpha=1.0):
        if fill is not None:
            self.fill(fill, alpha)
        if stroke is not None:
            self.stroke(stroke, width, alpha)
        self.c.circle(x, y, r, fill=int(fill is not None), stroke=int(stroke is not None))

    def line(self, x0, y0, x1, y1, colour, width, alpha=1.0):
        self.stroke(colour, width, alpha)
        self.c.line(x0, y0, x1, y1)

    # ---------------------------------------------------------- text
    def text(self, s, x, y, font, size, colour, anchor="l", space=0.0):
        """Live text. (x, y) is the baseline; anchor l/c/r."""
        w = pdfmetrics.stringWidth(s, font, size) + space * (len(s) - 1)
        if anchor == "c":
            x -= w / 2
        elif anchor == "r":
            x -= w
        c = self.c
        c.saveState()
        c.translate(x, y)
        c.scale(1, -1)
        t = c.beginText(0, 0)
        t.setFont(font, size)
        t.setCharSpace(space)
        t.setFillColor(colour)
        t.textOut(s)
        c.setFillAlpha(1)
        c.drawText(t)
        c.restoreState()
        return w

    def runs(self, parts, x, y, colour, anchor="l"):
        """parts: list of (text, font, size, rise). Drawn as one text object."""
        total = sum(pdfmetrics.stringWidth(t, f, s) for t, f, s, _ in parts)
        if anchor == "c":
            x -= total / 2
        c = self.c
        c.saveState()
        c.translate(x, y)
        c.scale(1, -1)
        t = c.beginText(0, 0)
        t.setFillColor(colour)
        for s, f, size, rise in parts:
            t.setFont(f, size)
            t.setRise(rise)
            t.textOut(s)
        t.setRise(0)
        c.setFillAlpha(1)
        c.drawText(t)
        c.restoreState()
        return total

    def fit(self, s, font, width, space=0.0):
        """Font size that makes `s` exactly `width` px wide."""
        base = pdfmetrics.stringWidth(s, font, 1)
        return (width - space * (len(s) - 1)) / base

    # ---------------------------------------------------------- shapes
    def heart(self, cx, cy, size, colour):
        s = size / 2
        self.draw([
            ("M", cx, cy + s * 0.95),
            ("C", cx - s * 0.2, cy + s * 0.7, cx - s * 1.05, cy + s * 0.15, cx - s * 1.0, cy - s * 0.35),
            ("C", cx - s * 0.95, cy - s * 0.95, cx - s * 0.15, cy - s * 1.0, cx, cy - s * 0.45),
            ("C", cx + s * 0.15, cy - s * 1.0, cx + s * 0.95, cy - s * 0.95, cx + s * 1.0, cy - s * 0.35),
            ("C", cx + s * 1.05, cy + s * 0.15, cx + s * 0.2, cy + s * 0.7, cx, cy + s * 0.95),
            ("Z",),
        ], fill=colour)

    def sparkle(self, cx, cy, r, colour, width=1.3):
        k = r * 0.18
        self.draw([
            ("M", cx, cy - r),
            ("C", cx + k, cy - k, cx + k, cy - k, cx + r, cy),
            ("C", cx + k, cy + k, cx + k, cy + k, cx, cy + r),
            ("C", cx - k, cy + k, cx - k, cy + k, cx - r, cy),
            ("C", cx - k, cy - k, cx - k, cy - k, cx, cy - r),
            ("Z",),
        ], stroke=colour, width=width)

    def leaf(self, x0, y0, x1, y1, fat, colour, vein=None):
        """Pointed leaf from base (x0,y0) to tip (x1,y1)."""
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * fat, dx / L * fat
        a1 = (x0 + dx * 0.3 + nx, y0 + dy * 0.3 + ny)
        a2 = (x0 + dx * 0.75 + nx * 0.9, y0 + dy * 0.75 + ny * 0.9)
        b2 = (x0 + dx * 0.75 - nx * 0.9, y0 + dy * 0.75 - ny * 0.9)
        b1 = (x0 + dx * 0.3 - nx, y0 + dy * 0.3 - ny)
        self.draw([
            ("M", x0, y0),
            ("C", *a1, *a2, x1, y1),
            ("C", *b2, *b1, x0, y0),
            ("Z",),
        ], fill=colour)
        if vein:
            self.draw([("M", x0, y0), ("C", x0 + dx * 0.4, y0 + dy * 0.4,
                                            x0 + dx * 0.7, y0 + dy * 0.7, x1, y1)],
                      stroke=vein, width=0.8, alpha=0.5)

    def burst(self, cx, cy, angles, r0, r1, colour, width=2.2):
        for a in angles:
            t = math.radians(a)
            self.line(cx + math.cos(t) * r0, cy + math.sin(t) * r0,
                      cx + math.cos(t) * r1, cy + math.sin(t) * r1, colour, width)

    def card_base(self, box):
        x0, y0, x1, y1 = box
        # soft drop shadow
        for i, a in enumerate([0.035, 0.035, 0.03, 0.025]):
            g = 1 + i * 1.6
            self.round_rect(x0 - g + 1, y0 - g + 3, x1 + g + 1, y1 + g + 4, CARD_R + g,
                            fill=HexColor("#000000"), alpha=a)
        self.round_rect(x0, y0, x1, y1, CARD_R, fill=CREAM)

    def clip_card(self, box):
        x0, y0, x1, y1 = box
        p = self.c.beginPath()
        p.roundRect(x0, y0, x1 - x0, y1 - y0, CARD_R)
        self.c.clipPath(p, stroke=0, fill=0)

    def save(self):
        self.c.showPage()
        self.c.save()


# ======================================================================
def front(k: Card):
    k.card_base(FRONT)
    k.c.saveState()
    k.clip_card(FRONT)

    # --- background blobs
    k.draw([("M", 0, 100), ("L", 175, 100),
            ("C", 175, 135, 150, 160, 125, 175),
            ("C", 95, 192, 70, 205, 40, 228),
            ("C", 30, 236, 20, 240, 0, 245), ("Z",)], fill=TEAL_PALE)
    k.draw([("M", 0, 100), ("L", 150, 100),
            ("C", 148, 128, 125, 148, 100, 160),
            ("C", 72, 174, 50, 182, 30, 200),
            ("C", 22, 207, 15, 212, 0, 215), ("Z",)], fill=TEAL_LIGHT)
    k.draw([("M", 380, 100), ("L", 520, 100), ("L", 520, 250),
            ("C", 500, 235, 488, 210, 470, 192),
            ("C", 452, 172, 430, 165, 415, 148),
            ("C", 402, 134, 392, 120, 380, 100), ("Z",)], fill=TEAL_PALE)
    k.draw([("M", 430, 100), ("L", 520, 100), ("L", 520, 205),
            ("C", 505, 195, 495, 175, 480, 160),
            ("C", 465, 145, 445, 135, 430, 100), ("Z",)], fill=TEAL_LIGHT)
    k.draw([("M", 0, 405),
            ("C", 60, 415, 110, 440, 175, 442),
            ("C", 240, 444, 285, 425, 330, 438),
            ("C", 375, 451, 430, 452, 520, 432),
            ("L", 520, 480), ("L", 0, 480), ("Z",)], fill=TEAL_PALE)
    k.draw([("M", 0, 430),
            ("C", 70, 440, 130, 458, 200, 458),
            ("C", 240, 458, 270, 450, 300, 455),
            ("C", 330, 460, 350, 470, 360, 480),
            ("L", 0, 480), ("Z",)], fill=TEAL_LIGHT, alpha=0.8)

    # --- plant, bottom right
    k.draw([("M", 470, 470), ("C", 470, 420, 478, 370, 496, 300)],
           stroke=TEAL_LEAF_DARK, width=2.2)
    k.draw([("M", 474, 410), ("C", 462, 400, 452, 392, 440, 380)],
           stroke=TEAL_LEAF_DARK, width=1.6)
    for base, tip, fat, col in [
        ((472, 438), (440, 425), 9, TEAL_LEAF),
        ((474, 405), (436, 372), 11, TEAL_LEAF),
        ((480, 372), (452, 330), 10, TEAL_LEAF_DARK),
        ((488, 335), (470, 295), 9, TEAL_LEAF),
        ((476, 420), (505, 395), 10, TEAL_LEAF_DARK),
        ((482, 385), (512, 350), 10, TEAL_LEAF),
        ((492, 315), (510, 285), 8, TEAL_LEAF_DARK),
    ]:
        k.leaf(*base, *tip, fat, col, vein=WHITE)

    # --- small teal sprigs left of the tagline
    k.leaf(122, 390, 132, 372, 4, TEAL_LEAF)
    k.leaf(115, 392, 108, 378, 3.5, TEAL_LEAF_DARK)

    # --- sparkles and hearts
    k.sparkle(108, 231, 9, ORANGE_SPARK)
    k.sparkle(144, 203, 5.5, ORANGE_SPARK, 1.1)
    k.sparkle(483, 262, 10, ORANGE_SPARK)
    k.heart(422, 231, 17, ORANGE)
    k.heart(268, 418, 11, ORANGE)

    # --- logo monogram
    k.stroke(TEAL_LOGO, 6.5)
    k.c.drawPath(k.path([
        ("M", 236, 152), ("L", 236, 216), ("L", 276, 216),
        ("C", 302, 216, 304, 182, 276, 182), ("L", 236, 182),
    ]), stroke=1, fill=0)
    k.c.drawPath(k.path([
        ("M", 236, 152), ("L", 268, 152),
        ("C", 290, 152, 290, 182, 268, 182),
    ]), stroke=1, fill=0)
    k.line(258, 131, 258, 206, TEAL_LOGO, 5)
    k.round_rect(250, 129, 266, 134, 2, fill=TEAL_LOGO)
    for x, y, r in [(266, 207, 4.6), (277, 199, 4.2), (283, 209, 3.6), (271, 196, 2.8)]:
        k.circle(x, y, r, fill=TEAL_HEAD)

    k.text("BUBBLE BLUSH", 266, 247, "Fredoka-SemiBold",
           k.fit("BUBBLE BLUSH", "Fredoka-SemiBold", 157), TEAL_LOGO, "c")

    # --- headline
    k.text("Loyal-Tea", 276, 313, "Chewy",
           k.fit("Loyal-Tea", "Chewy", 285), ORANGE, "c")
    k.burst(432, 280, [-60, -25, 10], 6, 15, ORANGE)
    k.burst(128, 282, [200, 235], 6, 13, ORANGE)
    k.text("CARD", 281, 362, "Fredoka-SemiBold",
           k.fit("CARD", "Fredoka-SemiBold", 103, 2), ORANGE, "c", space=2)

    tag = "SIP  •  COLLECT  •  ENJOY"
    k.text(tag, 271, 399, "Nunito-SemiBold",
           k.fit(tag, "Nunito-SemiBold", 198, 1.6), TEAL_LOGO, "c", space=1.6)

    # --- boba cup (drawn upright, then tilted)
    c = k.c
    c.saveState()
    c.translate(64, 380)
    c.rotate(5)
    # straw
    k.draw([("M", -8, -96), ("L", 2, -152), ("L", 13, -150), ("L", 4, -96), ("Z",)],
           fill=TEAL_STRAW)
    k.draw([("M", 8, -151), ("L", 13, -150), ("L", 4, -96), ("L", -1, -96), ("Z",)],
           fill=TEAL_STRAW_DARK, alpha=0.6)
    # body (clear cup)
    body = [("M", -57, -82), ("L", 57, -82), ("L", 45, 64),
            ("C", 44, 73, 37, 77, 28, 77), ("L", -28, 77),
            ("C", -37, 77, -44, 73, -45, 64), ("Z",)]
    k.draw(body, fill=WHITE, alpha=0.55)
    # tea
    c.saveState()
    p = k.path([("M", -54, -72), ("L", 54, -72), ("L", 43, 62),
                ("C", 42, 70, 36, 73, 28, 73), ("L", -28, 73),
                ("C", -36, 73, -42, 70, -43, 62), ("Z",)])
    c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(0, -72, 0, 73, (TEA_TOP, TEA_BOTTOM), extend=True)
    # pearls
    for x, y, r in [(-32, 28, 8.5), (-13, 40, 9), (7, 32, 8.5), (26, 44, 8.5), (-28, 54, 9),
                    (-6, 60, 8.5), (16, 62, 8.5), (35, 58, 7.5), (-41, 42, 7.5), (1, 48, 6),
                    (-19, 21, 6.5), (31, 24, 6.5)]:
        k.circle(x, y, r, fill=PEARL)
        k.circle(x - r * 0.35, y - r * 0.35, r * 0.28, fill=PEARL_HI, alpha=0.9)
    c.restoreState()
    # glass highlight and outline
    k.draw([("M", -47, -68), ("L", -40, -68), ("L", -33, 58), ("L", -38, 58), ("Z",)],
           fill=WHITE, alpha=0.45)
    k.draw(body, stroke=WHITE, width=2.5, alpha=0.85)
    # lid
    k.draw([("M", -52, -92), ("C", -45, -108, 45, -108, 52, -92), ("Z",)],
           fill=WHITE, alpha=0.7)
    k.round_rect(-63, -94, 63, -82, 6, fill=WHITE, alpha=0.95)
    k.round_rect(-63, -94, 63, -82, 6, stroke=HexColor("#E7D9C7"), width=1)
    # small logo on cup
    c.translate(14, 0)
    k.stroke(TEAL_LOGO, 3.2)
    c.drawPath(k.path([
        ("M", -46, -42), ("L", -46, -8), ("L", -26, -8),
        ("C", -13, -8, -12, -26, -26, -26), ("L", -46, -26),
    ]), stroke=1, fill=0)
    c.drawPath(k.path([("M", -46, -42), ("L", -30, -42),
                       ("C", -19, -42, -19, -26, -30, -26)]), stroke=1, fill=0)
    k.line(-35, -50, -35, -12, TEAL_LOGO, 2.6)
    for x, y, r in [(-31, -13, 2.4), (-25, -17, 2.2), (-22, -12, 1.8)]:
        k.circle(x, y, r, fill=TEAL_HEAD)
    c.restoreState()

    k.c.restoreState()


# ======================================================================
def back(k: Card):
    k.card_base(BACK)
    k.c.saveState()
    k.clip_card(BACK)

    # --- background blobs
    k.draw([("M", 510, 100), ("L", 620, 100),
            ("C", 612, 130, 590, 150, 565, 165),
            ("C", 545, 177, 530, 195, 510, 215), ("Z",)], fill=TEAL_PALE)
    k.draw([("M", 510, 100), ("L", 585, 100),
            ("C", 578, 122, 560, 135, 540, 148),
            ("C", 528, 156, 520, 168, 510, 180), ("Z",)], fill=TEAL_LIGHT)
    k.draw([("M", 920, 100), ("L", 1020, 100), ("L", 1020, 225),
            ("C", 1000, 210, 985, 185, 965, 165),
            ("C", 945, 145, 930, 130, 920, 100), ("Z",)], fill=TEAL_PALE)
    k.draw([("M", 960, 100), ("L", 1020, 100), ("L", 1020, 175),
            ("C", 1005, 160, 990, 140, 975, 128),
            ("C", 965, 120, 962, 110, 960, 100), ("Z",)], fill=TEAL_LIGHT)
    k.draw([("M", 510, 410), ("C", 545, 420, 585, 440, 610, 452),
            ("C", 630, 462, 640, 470, 650, 480), ("L", 510, 480), ("Z",)], fill=TEAL_PALE)
    k.draw([("M", 1020, 385), ("C", 995, 405, 975, 425, 955, 445),
            ("C", 940, 460, 925, 470, 915, 480), ("L", 1020, 480), ("Z",)], fill=TEAL_PALE)
    k.draw([("M", 1020, 420), ("C", 1000, 435, 985, 455, 975, 480),
            ("L", 1020, 480), ("Z",)], fill=TEAL_LIGHT)

    # --- heading
    head = "COLLECT AND ENJOY"
    k.text(head, 756, 161, "Fredoka-SemiBold",
           k.fit(head, "Fredoka-SemiBold", 212, 3.2), TEAL_TEXT, "c", space=3.2)
    k.burst(636, 155, [195, 225, 165], 6, 14, ORANGE, 2.2)
    k.burst(876, 155, [-15, 15, -45], 6, 14, ORANGE, 2.2)

    # --- stamp circles
    xs = [576, 642, 707, 772, 838]
    rows = [(214, ["1", "2", "3", "4", "5"]), (294, ["6", "7", "8", "9", "10"])]
    R = 31.5
    for cy, labels in rows:
        for cx, lab in zip(xs, labels):
            special = lab in ("5", "10")
            if special:
                k.circle(cx, cy, R + 3, fill=PEACH, alpha=0.6)
                k.circle(cx, cy, R, fill=PEACH_CIRCLE, stroke=ORANGE_SOFT, width=2.4)
            else:
                k.circle(cx, cy, R, fill=CREAM_LIGHT, stroke=GREY_RING, width=2)
                k.text(lab, cx, cy + 7.5, "Nunito-SemiBold", 21, GREY_NUM, "c")

    # stamp 5: number + bowl of toppings
    k.text("5", 838, 213, "Fredoka-SemiBold", 22, ORANGE, "c")
    k.draw([("M", 825, 226), ("L", 851, 226),
            ("C", 850, 236, 845, 241, 838, 241),
            ("C", 831, 241, 826, 236, 825, 226), ("Z",)], fill=HexColor("#6B3F2A"))
    k.round_rect(823, 224, 853, 228, 2, fill=HexColor("#6B3F2A"))
    for x, y, r in [(830.5, 221.5, 3.3), (837.5, 219.5, 3.5), (844.5, 221.5, 3.3)]:
        k.circle(x, y, r, fill=PEARL)
        k.circle(x - r * 0.3, y - r * 0.35, r * 0.3, fill=PEARL_HI)
    k.draw([("M", 828, 233), ("C", 832, 237, 838, 238, 842, 237)],
           stroke=WHITE, width=1, alpha=0.6)

    # stamp 10: number + cup icon
    k.text("10", 838, 284, "Fredoka-SemiBold", 21, ORANGE, "c")
    k.draw([("M", 829, 292), ("L", 847, 292), ("L", 845, 314),
            ("C", 845, 316, 843, 317, 841, 317), ("L", 835, 317),
            ("C", 833, 317, 831, 316, 831, 314), ("Z",)],
           fill=PEACH, stroke=ORANGE, width=1.6)
    k.line(827, 292, 849, 292, ORANGE, 1.8)
    k.line(840, 292, 844, 283, ORANGE, 1.6)
    for x, y in [(834.5, 312), (838.5, 313), (842, 311), (836.5, 308), (840.5, 307.5)]:
        k.circle(x, y, 1.7, fill=ORANGE)

    # small accent dashes
    k.burst(808, 322, [120, 150], 2, 9, ORANGE, 1.8)
    k.burst(812, 186, [-120, -150], 2, 8, ORANGE, 1.8)

    # curved double arrow between the two rewards
    k.draw([("M", 868, 257), ("C", 872, 249, 878, 244, 887, 240)],
           stroke=ORANGE, width=1.6)
    k.draw([("M", 881, 238.5), ("L", 888, 239.5), ("L", 884.5, 245.5)], stroke=ORANGE, width=1.6)
    k.draw([("M", 866.5, 250.5), ("L", 867.5, 258), ("L", 874, 255)], stroke=ORANGE, width=1.6)

    # --- reward callouts
    k.round_rect(886, 178, 996, 242, 8, fill=PEACH)
    k.runs([("5", "Fredoka-SemiBold", 14, 0), ("th", "Fredoka-SemiBold", 8.5, 5),
            (" Drink", "Fredoka-SemiBold", 14, 0)], 941, 196, ORANGE, "c")
    k.text("FREE TOPPING", 941, 214, "Nunito-ExtraBold", 13.6, ORANGE, "c")
    k.text("of your choice", 941, 230, "Nunito-SemiBold", 11, BODY, "c")

    k.round_rect(886, 257, 996, 352, 8, fill=PEACH)
    k.runs([("10", "Fredoka-SemiBold", 14, 0), ("th", "Fredoka-SemiBold", 8.5, 5),
            (" Visit", "Fredoka-SemiBold", 14, 0)], 941, 276, ORANGE, "c")
    k.text("FREE REGULAR", 941, 296, "Nunito-ExtraBold", 13.6, ORANGE, "c")
    k.text("DRINK", 941, 312, "Nunito-ExtraBold", 13.6, ORANGE, "c")
    k.text("(or a dessert", 941, 330, "Nunito-SemiBold", 11, BODY, "c")
    k.runs([("under ", "Nunito-SemiBold", 11, 0), ("฿", "NotoSansThai-Medium", 11, 0),
            ("200)", "Nunito-SemiBold", 11, 0)], 941, 345, BODY, "c")

    # --- terms & conditions
    k.text("TERMS & CONDITIONS", 547, 372, "Nunito-ExtraBold", 13, TEAL_HEAD)
    k.line(704, 367, 966, 367, HexColor("#7FA6A1"), 1.2)
    k.heart(986, 373, 13, ORANGE)
    terms = [
        [("1 stamp per purchase  •  Max. 1 stamp per day", "Nunito-SemiBold")],
        [("Free topping with your 5th drink.", "Nunito-SemiBold")],
        [("Free regular drink on your 10th visit (or a dessert under ", "Nunito-SemiBold"),
         ("฿", "NotoSansThai-Medium"), ("200).", "Nunito-SemiBold")],
        [("Rewards cannot be exchanged for cash.", "Nunito-SemiBold")],
        [("Original card required for redemption.", "Nunito-SemiBold")],
    ]
    for y, parts in zip([389, 407, 424, 440, 456], terms):
        k.circle(553, y - 3.8, 2.3, fill=TEAL_HEAD)
        k.runs([(t, f, 11.6, 0) for t, f in parts], 565, y, BODY)

    k.c.restoreState()


def build(path):
    k = Card(path)
    k.fill(WHITE)
    k.c.rect(0, 0, IMG_W, IMG_H, fill=1, stroke=0)
    front(k)
    back(k)
    k.save()


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "bubble-blush-loyal-tea-card-editable.ai")
    build(out)
    print("wrote", out, f"{PAGE_W / MM:.1f} x {PAGE_H / MM:.1f} mm")
