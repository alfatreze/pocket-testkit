# Resolutions: how much a screen holds

The pixel grid keeps the same pixel size on every screen (robust cells of 4 px by default, lossless 1 px per 16 bits), so a bigger surface carries more and a smaller one less. The block is a square centred on the screen, sized from the screen's short side. Numbers are payload bytes (the 16-byte header is already deducted), from `tpg.capacity()`.

## Analogue Pocket range

The Pocket's core video interface takes 16x16 up to 800x720 (Analogue's developer docs; the Pocket scales the core's picture to its own panel, so a core never needs more). Typical core sizes: 160x144 Game Boy, 240x160 Game Boy Advance, 256x224 NES/SNES, 400x360 what Tau uses, 800x720 the maximum (QR columns: safe max = `photo` level with the module size it gets; largest that fits = densest code drawable at 2 px modules, screenshots only above 271 bytes):

| Resolution | Grid L | Grid R, 4 px cells | Grid R, 8 px cells | QR safe max (photo) | QR largest that fits |
|---|---|---|---|---|---|
| 160x144 | 41,456 | 956 | 227 | 271 (2 px) | 321 (v11) |
| 240x160 | 51,184 | 1,184 | 284 | 271 (2 px) | 425 (v13) |
| 256x224 | 100,336 | 2,336 | 572 | 271 (3 px) | 929 (v21) |
| 320x240 | 115,184 | 2,684 | 659 | 271 (3 px) | 1,091 (v23) |
| 400x360 | 259,184 | 6,059 | 1,502 | 271 (5 px) | 2,699 (v38) |
| 640x480 | 460,784 | 10,784 | 2,684 | 271 (7 px) | 2,699 (v38) |
| 800x480 | 460,784 | 10,784 | 2,684 | 271 (7 px) | 2,699 (v38) |
| 800x720 | 1,036,784 | 24,284 | 6,059 | 271 (11 px) | 2,699 (v38) |

## Other devices (beyond the Pocket)

The codec has no size limit; these are tested in `tests/test_tpg_resolutions.py` for projects on other hardware.

| Resolution | Lossless (L) | Robust (R), 4 px cells | Robust (R), 8 px cells |
|---|---|---|---|
| 480x272 | 147,952 | 3,452 | 851 |
| 1280x720 | 1,036,784 | 24,284 | 6,059 |
| 1920x1080 | 2,332,784 | 54,659 | 13,652 |
| 3840x2160 | 9,331,184 | 218,684 | 54,659 |

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

