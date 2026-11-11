# Resolutions: how much a screen holds

The pixel grid keeps the same pixel size on every screen (robust cells of 4 px by default, lossless 1 px per 16 bits), so a bigger surface carries more and a smaller one less. The block is a square centred on the screen, sized from the screen's short side. Numbers are payload bytes (the 16-byte header is already deducted), from `tpg.capacity()`.

## Analogue Pocket range

The Pocket's core video interface takes 16x16 up to 800x720 (Analogue's developer docs; the Pocket scales the core's picture to its own panel, so a core never needs more). Typical core sizes:

| Screen | Size | Lossless (L) | Robust (R), 4 px cells | Robust (R), 8 px cells |
|---|---|---|---|---|
| Game Boy | 160x144 | 41,456 | 956 | 227 |
| Game Boy Advance | 240x160 | 51,184 | 1,184 | 284 |
| NES / SNES | 256x224 | 100,336 | 2,336 | 572 |
| QVGA | 320x240 | 115,184 | 2,684 | 659 |
| **Tau default** | 400x360 | 259,184 | 6,059 | 1,502 |
| VGA | 640x480 | 460,784 | 10,784 | 2,684 |
| WVGA | 800x480 | 460,784 | 10,784 | 2,684 |
| **Pocket maximum** | 800x720 | 1,036,784 | 24,284 | 6,059 |

## Other devices (beyond the Pocket)

The codec has no size limit; these are tested in `tests/test_tpg_resolutions.py` for projects on other hardware.

| Screen | Size | Lossless (L) | Robust (R), 4 px cells | Robust (R), 8 px cells |
|---|---|---|---|---|
| Small LCD | 480x272 | 147,952 | 3,452 | 851 |
| 720p | 1280x720 | 1,036,784 | 24,284 | 6,059 |
| 1080p | 1920x1080 | 2,332,784 | 54,659 | 13,652 |
| 4K | 3840x2160 | 9,331,184 | 218,684 | 54,659 |

## Notes

- Lossless needs a lossless copy of the screen and a display with at least 5/6/5 bits per channel. Robust survives JPEG q80+ and, with `native=(w, h)`, a resize.
- A screen whose short side is under 32 px (8 cells of 4 px) cannot hold a robust grid; use a smaller `cell` or lossless.
- QR does not scale this way: it is resolution independent (see [DENSITY.md](DENSITY.md)).
- The 400x360 numbers equal the original Pocket format, byte for byte (`tests/golden_400x360.json`).

```python
import tpg
img = tpg.to_rgb(tpg.encode(record, tpg.MODE_R, size=(800, 480), cell=4))   # any screen
payload = tpg.decode(img)                                   # finds the size, block and cell by itself
```
