# The Pocket adds the core's identity to every screenshot

*Part of [report codes](../README.md). Paths below are relative to `methods/report-codes/`.*

A screenshot taken with Menu+Start is a normal PNG **followed by extra bytes** after its last chunk. Ordinary PNG readers ignore them (every decoder here still works), but they say which core made the picture. Analogue's changelog for framework 1.1 (beta 6) confirms the intent: "all metadata is contained within the PNG file".

## What is in the file

Layout found in 31 real screenshots of Tau cores; all 31 follow it exactly. It is **read from the files, not an Analogue specification**, and the meaning of the fields is inferred from their values.

| After the PNG | Content |
|---|---|
| Block A | a small thumbnail (121x109, BGRA) |
| Block B | a second full-size image (400x360, BGRA). Its pixels do **not** equal the PNG's: use the PNG as the data channel, never this |
| Footer (600 bytes) | text fields (below) plus the PNG length and the block offsets, so a file can be checked for being intact |

| Field | Example | Reads as |
|---|---|---|
| `author` | alfatreze | the core's author |
| `core` | TAU_DEV_BARCODE_04 | the core's short name, spaces as underscores |
| `version` | 0.6.0 | the core's version |
| `file` | tau.rom | a file name, here the ROM the core loaded |
| `platform_id` | tau_devbar04 | the core's platform id |
| `platform_name` | TAU DEV BARCODE 04 | the platform's display name |

The file name also carries the Pocket's clock: `YYYYMMDD_HHMMSS.png`.

## Identify it

```bash
python3 python/pocket_meta.py shot.png            # the fields; --json; --thumb thumb.png saves the thumbnail
python3 python/decode.py shot.png                 # now prints "from <core> <version>" above the payload
```

```python
import pocket_meta
meta = pocket_meta.read("shot.png")               # dict, or None when there is no Pocket trailer
```

`None` means the file is not an original Pocket screenshot: a photo, a JPEG, or a copy re-saved by an editor or chat app (they drop the extra bytes). `consistent: false` means the lengths in the footer do not match the file: it was altered.

## Leverage it

- **Do not put the core name and version in your report payload.** The screenshot already carries them, so the payload is smaller and the two cannot disagree. If your payload also holds a build id, compare it with `version`: a mismatch means the report was made by a different build than the one the screenshot says.
- **Sort and filter a folder of screenshots** by core and version, e.g. keep only those from the build under test.
- **Tell a Pocket screenshot from a re-saved copy.** Only originals keep the trailer, and tier L (lossless) only works on originals anyway. A report that arrived without it was probably re-encoded.
- **Preview cheaply** with the thumbnail, without decoding the full PNG.

## Cautions

- **Privacy:** sharing a screenshot shares the author, core, version and the file name above, and a thumbnail. Strip the trailer (re-save the PNG) before posting if that matters; the grid and QR survive only if the re-save is lossless (tier L needs the exact pixels, which a normal PNG re-save keeps).
- **Not a stable interface.** It is not documented by Analogue and may change with Pocket firmware; `pocket_meta` returns `None` rather than guessing when the layout is not as expected. Seen only on Tau cores, one Pocket firmware family.
- Three footer values are not understood (two fixed numbers and one that varies per file); they are ignored.
- The Rust crate does not read this yet.
