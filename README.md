# bb-loyal-tea-card

Bubble Blush "Loyal-Tea" loyalty card, front and back, as an Adobe Illustrator file.

| File | What it is |
| --- | --- |
| `bubble-blush-loyal-tea-card-editable.ai` | Editable vector version. Live text, separate shapes, colours you can change. |
| `preview/editable-preview.png` | Preview of the editable file. |
| `fonts/` | Fonts used in the file, with their licences. Install them before editing text. |
| `source/build_card.py` | Script that generates the `.ai` file. |

## About the file

- Opens directly in Illustrator (File > Open). It is a PDF-compatible `.ai` file.
- One artboard, 181.1 x 101.9 mm, with both cards side by side, as in the original image.
- Each card is 85.6 mm wide (credit-card width) and 61.4 mm tall, the original image's proportions.
- Colours are RGB.

## Fonts

| Text | Font |
| --- | --- |
| Loyal-Tea | Chewy Regular |
| BUBBLE BLUSH, CARD, COLLECT AND ENJOY, numbers 5 and 10, reward titles | Fredoka SemiBold |
| Stamp numbers, body text | Nunito SemiBold |
| FREE TOPPING, FREE REGULAR DRINK, TERMS & CONDITIONS | Nunito ExtraBold |
| ฿ sign | Noto Sans Thai Medium |

The fonts are embedded in the file, so it displays and prints correctly without them.
Install the fonts from `fonts/` if you want to edit the text.

## Rebuilding

```sh
pip install reportlab
python source/build_card.py
```
