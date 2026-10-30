"""Wrap the original PNG, untouched, in a PDF-compatible Adobe Illustrator file."""
import sys

import pymupdf

SRC, OUT = sys.argv[1], sys.argv[2]
CARD_W_PX = 790                      # width of one card in the original image
PT_PER_PX = 85.6 / 25.4 * 72 / CARD_W_PX

pix = pymupdf.Pixmap(SRC)
w, h = pix.width * PT_PER_PX, pix.height * PT_PER_PX
doc = pymupdf.open()
page = doc.new_page(width=w, height=h)
page.insert_image(page.rect, filename=SRC)
doc.set_metadata({"title": "Bubble Blush Loyal-Tea Card (original artwork, not editable)",
                  "author": "Bubble Blush", "creator": "Original PNG embedded unchanged"})
doc.save(OUT, deflate=True, garbage=3)
print(f"wrote {OUT}: {pix.width}x{pix.height} px, {w / 72 * 25.4:.1f} x {h / 72 * 25.4:.1f} mm")
