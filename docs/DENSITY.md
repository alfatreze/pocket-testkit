# QR density: what is reasonable

Measured by `tests/qr_density_study.py` (table: [qr_density.md](qr_density.md)): for each version a payload that **fills** it (level L, byte mode), drawn on the 400x360 screen with the largest whole-pixel modules, then decoded after a lossless screenshot, JPEG q80, and three **simulated** phone photos (tilt, blur sigma 1.0/1.6/2.4, noise, JPEG 70). Two decoders: Aruco+classic ("any") and OpenCV's classic detector alone (the nearest stand-in for a phone scanner here).

| Level | QR version | Bytes | Module size on 400x360 | What the study showed | Friction |
|---|---|---|---|---|---|
| `photo` (default) | 1-10 | 271 | 4-6 px | Aruco+classic read every simulated photo; the classic detector alone read 2-3 of 3 | none |
| `careful` | 11-22 | 1,003 | 2-4 px | Aruco reads every simulated photo; the classic detector fails from about version 14 | a warning |
| `max` | 23-38 | 2,699 | 2 px | Lossless and JPEG q80 screenshots decode with Aruco at every version; simulated photos drop out from version 24 and **fail at version 38 under heavy blur** | an error unless `allow_max=True` / `--yes-max` / typing `MAX`; the C guide says to put it behind a key press and caption it "SCREENSHOT ONLY" |

## Resolution

**QR is resolution independent.** What a code can carry is set by its version (the level), never by the screen; the screen only decides how large the modules are drawn (the biggest whole-pixel size that fits, at least 2 px). The study used a 400x360 screen, where the denser versions end up with 2-3 px modules; on a bigger screen the same version is drawn with bigger modules, so the table is conservative there. On a screen too small for a version the drawing is refused with a clear message.

**The pixel grid (tiers L and R) is the one that scales with the screen:** the cell size stays the same in pixels (4 by default) and a bigger surface simply holds more. See [RESOLUTIONS.md](RESOLUTIONS.md).

## Limits of this evidence

- **Simulation only.** No glare, no moire from the screen's own pixel grid, no autofocus miss, no real phone scanner. Real photos will do worse; treat `photo` as the only level promised to work with a phone, and confirm with a real photo before relying on any other.
- A small sample (3 seeds per cell). The edges of the table are soft: "flaky" means 1-2 of 3 passed.
- OpenCV's classic detector is a conservative proxy, not a phone. Phone scanners (ZXing, Apple, Google) often read denser codes.
- If you have real phone photos of dense Pocket QR codes, they are better fixtures than this study; add them and rerun.

To re-measure on your own screen size or decoder: `python3 tests/qr_density_study.py --seeds 5`.
