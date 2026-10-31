# bb-loyal-tea-card

Bubble Blush "Loyal-Tea" loyalty card, front and back, as Adobe Illustrator files.

| File | What it is |
| --- | --- |
| `Original png.PNG` | The original artwork (1672 × 941 px). |
| `bubble-blush-loyal-tea-card-original.ai` | **Not editable.** The original PNG placed in an Illustrator file, pixel for pixel, with nothing changed. |
| `bubble-blush-loyal-tea-card-editable.ai` | **Editable.** All artwork as vector shapes and all wording as live text. |
| `bubble-blush-loyal-tea-card-outlined.ai` | **Print-ready outlines.** The editable file with all text converted to outlines (like Type > Create Outlines). Looks identical, needs no fonts, but the wording can no longer be retyped. |
| `preview/editable-preview.png` | What the editable file looks like. |
| `fonts/` | Fonts used in the editable file, with their licences. |
| `source/` | Scripts that generate both `.ai` files from the PNG. |

## Size

All three files have the same single artboard, 181.17 × 101.96 mm, with the front and back side by side,
exactly as laid out in the original image (including the white background and the card shadows).

Each card is 85.6 mm wide (credit-card width) and 61.4 mm tall, with 3.25 mm rounded corners.
The design itself is taller than a credit card (85.6 × 53.98 mm), so the printer will need to decide how to fit it.

The original image is 1672 px wide, so the non-editable file prints at about 234 ppi at this size.
The editable file is vector and prints sharp at any size.

Colours are RGB, as in the original.

## The editable file

- **Text:** every word is live text and can be edited, except the hand-lettered "Loyal-Tea" headline,
  which is a vector shape so it keeps its exact lettering.
- **Artwork:** the backgrounds, cup, leaves, icons, hearts and sparkles are vector shapes traced from the
  original, one shape per colour. The logo, stamp circles, connector lines and the terms rule are redrawn
  as clean geometry.
- The fonts are embedded, so the file displays and prints correctly without installing them.
  Install the fonts in `fonts/` before editing the text.

| Text | Font |
| --- | --- |
| BUBBLE BLUSH, CARD | M PLUS Rounded 1c ExtraBold |
| COLLECT AND ENJOY | M PLUS Rounded 1c Bold |
| SIP • COLLECT • ENJOY, TERMS & CONDITIONS, stamp numbers | Source Sans 3 Bold |
| Terms, "of your choice", "(or a dessert under ฿200)" | Source Sans 3 Medium |
| 5th Drink, FREE TOPPING, 10th Visit, FREE REGULAR DRINK | Nunito ExtraBold |
| ฿ sign | Noto Sans Thai Medium |

## Rebuilding

```sh
pip install -r source/requirements.txt
python source/build_original_ai.py "Original png.PNG" bubble-blush-loyal-tea-card-original.ai
python source/build_editable.py "Original png.PNG" bubble-blush-loyal-tea-card-editable.ai
python source/build_editable.py "Original png.PNG" bubble-blush-loyal-tea-card-outlined.ai --outline
```
