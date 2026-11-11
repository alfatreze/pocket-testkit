# Resolutions: how much a screen holds

The pixel grid keeps the same pixel size on every screen (robust cells of 4 px by default, lossless 1 px per 16 bits), so a bigger surface carries more and a smaller one less. The block is a square centred on the screen, sized from the screen's short side. Numbers below are payload bytes (the 16-byte header is already deducted); they come from `tpg.capacity()`.

| Screen | Lossless (L) | Robust (R), 4 px cells | Robust (R), 8 px cells |
|---|---|---|---|
| Game Boy 160x144 | 41,456 | 956 | 227 |
| GBA 240x160 | 51,184 | 1,184 | 284 |
| Analogue Pocket 400x360 | 259,184 | 6,059 | 1,502 |
| QVGA 320x240 | 115,184 | 2,684 | 659 |
| Small LCD 480x272 | 147,952 | 3,452 | 851 |
| VGA 640x480 | 460,784 | 10,784 | 2,684 |
| WVGA 800x480 | 460,784 | 10,784 | 2,684 |
| 720p 1280x720 | 1,036,784 | 24,284 | 6,059 |
| 1080p 1920x1080 | 2,332,784 | 54,659 | 13,652 |
| 4K 3840x2160 | 9,331,184 | 218,684 | 54,659 |

Notes:
- Lossless needs a lossless copy of the screen and a display with at least 5/6/5 bits per channel. Robust survives JPEG q80+ and (with `native=(w, h)`) a resize; it needs more pixels per cell on a very large screen if you want it to survive harsh scaling.
- A screen whose short side is under 8 cells (32 px at 4 px cells) cannot hold a robust grid; use a smaller `cell` or lossless.
- QR does not scale this way: it is resolution independent (see [DENSITY.md](DENSITY.md)).
- The 400x360 numbers equal the original Pocket format, byte for byte (`tests/golden_400x360.json`).

```python
import tpg
img = tpg.to_rgb(tpg.encode(record, tpg.MODE_R, size=(1280, 720), cell=4))   # any screen
payload = tpg.decode(img)                                  # finds the size, the block and the cell by itself
```
