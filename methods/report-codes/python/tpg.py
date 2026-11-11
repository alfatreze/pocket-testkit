#!/usr/bin/env python3
"""TPG: Tau pixel grid, a screenshot-native container for a Tau report (docs/features/BARCODE_STUDY.md).

The Pocket's screenshot is a lossless 400x360 PNG whose pixels are exact RGB565 values (hardware-confirmed 2026-10-04: four
dense test patterns and a real Check report came back 100% exact). TPG puts the report's binary record straight into those
pixels instead of spending the area on a camera-grade barcode.

Layout TPG2 (current): the stream fills a SQUARE block centred on the screen, as small as the report allows, so a screenshot shows
a compact picture in the middle (the firmware adds a frame and captions around it) and not a strip of pixels on the first row.
The block's side comes from a fixed ladder; the decoder tries each step and keeps the one whose first pixels read `TPG2`.

Stream (identical in both modes): 16 header bytes, then the payload, zero padded to the unit size. All integers big endian.

    0   4  "TPG2"
    4   1  mode: 0 = L (lossless), 1 = R (robust)
    5   1  flags, 0
    6   2  reserved, 0
    8   4  payload length in bytes
   12   4  CRC32 (zlib) of the payload

Mode L: one pixel per 16 stream bits, the pixel's RGB565 value is the two stream bytes (high byte first), row-major inside a
        S x S pixel block, S in LADDER_L (64..360), block at x0 = (400 - S) / 2, y0 = (360 - S) / 2. Up to 259,184 bytes.
        Survives only a lossless copy of the screenshot.
Mode R: one 4x4 pixel cell per 6 stream bits (MSB first: R, G, B, two bits each), row-major inside a C x C cell block, C in
        LADDER_R (20..90 cells = 80..360 px), block centred the same way. The four levels per channel are the RGB565 values
        0/10/21/31 (R, B) and 0/21/42/63 (G). Up to 6,059 bytes. Survives JPEG (quality >= 80 tested) and a resize of the
        whole image by box, Lanczos, nearest or bicubic filters: the decoder resamples to 400x360 and averages the centre of
        each cell. A heavy bilinear downscale corrupts about 14% of the cells at 50% and is detected by the CRC, not repaired:
        there is no error correction. It does not survive a camera.

Layout TPG1 (legacy, the first hardware test 2026-10-04): the stream starts at pixel (0, 0) and runs row-major over the whole
screen (mode L: 1 px per 16 bits; mode R: a 100 x 90 cell grid), magic `TPG1`. Still decoded; no longer produced.

The payload CRC32 makes a bad channel fail loudly. The payload is the Check/Sweep/Info record (`fw/suite_core.h`, parsed by
`decode_tau_suite.py`).

  tpg.py encode record.bin out.png [--mode L|R] [--size WxH] [--cell N]
  tpg.py decode shot.png out.bin [--native WxH]

ANY RESOLUTION: every function takes size=(w, h) (default 400x360). The block is a centred square from a ladder that depends only on
the screen's short side; the robust cell size (default 4 px) is in header byte 5 (0 = 4), so the decoder finds it by itself. A
400x360 picture is byte-identical to the original format (tests/golden_400x360.json).
"""
import argparse
import struct
import sys
import zlib

import numpy as np
from PIL import Image

W, H = 400, 360                    # the default screen (the Analogue Pocket); every function takes size=(w, h) for any other screen
CW, CH = 4, 4                      # the default robust cell (px)
GW, GH = W // CW, H // CH          # legacy TPG1 robust grid: 100 x 90 cells
MAGIC = b"TPG2"
MAGIC_V1 = b"TPG1"
MODE_L, MODE_R = 0, 1
HDR = 16
LV5 = (0, 10, 21, 31)              # robust levels as RGB565 field values
LV6 = (0, 21, 42, 63)
CELLS = (4, 2, 3, 5, 6, 8, 10, 12, 16, 20, 24, 32)     # cell sizes the decoder tries, the default first
MIN_CELLS = 8                      # a robust block needs at least this many cells on its short side


# --- any resolution -----------------------------------------------------------------------------------------------------------------
# The block is a SQUARE centred on the screen. Its side comes from a ladder that depends only on the screen's short side, so a decoder
# that knows the screen size finds it by probing each step for the magic. For 400x360 the ladders are exactly the original ones.
def _base_l(i):                    # pixels: 64, 80, 96, 112, 128, then steps of 32
    return 64 + 16 * i if i < 5 else 128 + 32 * (i - 4)


def _base_r(i):                    # cells: 20, 24, 28, 32, then steps of 8
    return 20 + 4 * i if i < 4 else 32 + 8 * (i - 3)


def _ladder(cap, base):
    out, i = [], 0
    while base(i) < cap:
        out.append(base(i)); i += 1
    return tuple(out) + (cap,)


def ladder_l(size=(W, H)):
    return _ladder(min(size), _base_l)


def ladder_r(size=(W, H), cell=CW):
    cap = min(size) // cell
    if cap < MIN_CELLS:
        raise ValueError(f"screen {size[0]}x{size[1]} is too small for {cell}-pixel cells")
    return _ladder(cap, _base_r)


LADDER_L = ladder_l()              # the 400x360 ladders, kept for old callers
LADDER_R = ladder_r()


def header(mode: int, payload: bytes, magic: bytes = MAGIC, cell: int = CW) -> bytes:
    flag = cell if (mode == MODE_R and magic == MAGIC and cell != CW) else 0      # byte 5: the robust cell size when it is not 4 (0 = 4)
    return magic + bytes([mode, flag, 0, 0]) + struct.pack(">II", len(payload), zlib.crc32(payload) & 0xFFFFFFFF)


def _units(side: int, mode: int) -> int:
    """Stream bytes a block of `side` (pixels for L, cells for R) can hold, header included."""
    return side * side * 2 if mode == MODE_L else side * side * 6 // 8


def capacity(mode: int, size=(W, H), cell: int = CW) -> int:
    return _units((ladder_l(size) if mode == MODE_L else ladder_r(size, cell))[-1], mode) - HDR


def block(length: int, mode: int, size=(W, H), cell: int = CW):
    """(x0, y0, pixel side) of the centred square block a payload of `length` bytes uses, or None if it does not fit."""
    for s in (ladder_l(size) if mode == MODE_L else ladder_r(size, cell)):
        if _units(s, mode) >= HDR + length:
            px = s if mode == MODE_L else s * cell
            return (size[0] - px) // 2, (size[1] - px) // 2, px
    return None


def encode(payload: bytes, mode: int = MODE_L, size=(W, H), cell: int = CW) -> np.ndarray:
    """Returns an (h, w) uint16 array of RGB565 values for a screen of `size` = (w, h); everything outside the block is 0 (callers draw
    their own page). `cell` (mode R only) is the side of a robust cell in pixels: use 4 on a 400x360 screen, more on a bigger one."""
    blk = block(len(payload), mode, size, cell)
    if blk is None:
        raise ValueError(f"payload of {len(payload)} bytes exceeds mode {'LR'[mode]} capacity {capacity(mode, size, cell)} on {size[0]}x{size[1]}")
    x0, y0, px = blk
    data = header(mode, payload, cell=cell) + payload
    img = np.zeros((size[1], size[0]), np.uint16)
    if mode == MODE_L:
        data += b"\0" * (len(data) % 2)
        p = np.frombuffer(data, ">u2").astype(np.uint16)
        sq = np.zeros(px * px, np.uint16)
        sq[:len(p)] = p
        img[y0:y0 + px, x0:x0 + px] = sq.reshape(px, px)
        return img
    side = px // cell
    bits = np.unpackbits(np.frombuffer(data, np.uint8))
    bits = np.concatenate([bits, np.zeros((-len(bits)) % 6, np.uint8)]).reshape(-1, 6)
    r = bits[:, 0] * 2 + bits[:, 1]
    g = bits[:, 2] * 2 + bits[:, 3]
    b = bits[:, 4] * 2 + bits[:, 5]
    cells = (np.array(LV5, np.uint16)[r] << 11) | (np.array(LV6, np.uint16)[g] << 5) | np.array(LV5, np.uint16)[b]
    grid = np.zeros(side * side, np.uint16)
    grid[:len(cells)] = cells
    img[y0:y0 + px, x0:x0 + px] = np.repeat(np.repeat(grid.reshape(side, side), cell, 0), cell, 1)
    return img


def to_rgb(img565: np.ndarray) -> np.ndarray:
    """What a screenshot contains: RGB565 expanded to 8 bits per channel by bit replication (any display with at least 5/6/5 bits per
    channel and a lossless screenshot round-trips it)."""
    r = (img565 >> 11) & 31
    g = (img565 >> 5) & 63
    b = img565 & 31
    return np.stack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)], -1).astype(np.uint8)


def from_rgb(rgb: np.ndarray) -> np.ndarray:
    a = rgb.astype(np.uint16)
    return ((a[..., 0] >> 3) << 11) | ((a[..., 1] >> 2) << 5) | (a[..., 2] >> 3)


def _parse(stream: bytes, mode: int, magic: bytes, cap: int, flag: int = 0):
    if stream[:4] != magic or stream[4] != mode or stream[5] != flag or stream[6:8] != b"\0\0":
        return None
    n, crc = struct.unpack(">II", stream[8:16])
    if n > cap:
        raise ValueError("TPG header length is impossible (damaged)")
    return n, crc


def _check(raw: bytes, n: int, crc: int, what: str) -> bytes:
    if len(raw) != n or zlib.crc32(raw) & 0xFFFFFFFF != crc:
        raise ValueError(f"{what}: CRC mismatch (the screenshot was altered or cropped, or too much damage)")
    global LAST_READ
    LAST_READ = what                                       # e.g. "TPG2 mode R": lets a caller say which carrier was read
    return raw


LAST_READ = ""


def _cell_levels(img: np.ndarray, x0: int, y0: int, side: int, cell: int = CW) -> np.ndarray:
    """(side*side, 3) levels 0..3 of a robust block: mean of the centre of each cell (edges carry the neighbours' blur)."""
    m = cell // 4
    blk = img[y0:y0 + side * cell, x0:x0 + side * cell].astype(np.float32).reshape(side, cell, side, cell, 3)[:, m:cell - m, :, m:cell - m].mean((1, 3))
    return np.clip(np.rint(blk / 85.0), 0, 3).astype(np.uint8).reshape(-1, 3)


def _levels_to_bytes(lv: np.ndarray) -> bytes:
    bits = np.stack([lv[:, 0] >> 1, lv[:, 0] & 1, lv[:, 1] >> 1, lv[:, 1] & 1, lv[:, 2] >> 1, lv[:, 2] & 1], 1).reshape(-1)
    return np.packbits(bits[:len(bits) // 8 * 8]).tobytes()


def _try_size(rgb: np.ndarray, size, cells):
    """Look for a TPG2 block assuming the screen is `size`; the image is resampled to it when it has another size (robust only)."""
    sw, sh = size
    h, w = rgb.shape[:2]
    exact = (w, h) == (sw, sh)
    if exact:
        flat565 = from_rgb(rgb)
        for s in ladder_l(size):                                    # mode L: header in the first pixels of the centred block
            x0, y0 = (sw - s) // 2, (sh - s) // 2
            head = flat565[y0, x0:x0 + HDR // 2].astype(">u2").tobytes()
            got = _parse(head, MODE_L, MAGIC, capacity(MODE_L, size))
            if got:
                n, crc = got
                sq = flat565[y0:y0 + s, x0:x0 + s].reshape(-1)
                return _check(sq[:(HDR + n + 1) // 2].astype(">u2").tobytes()[HDR:HDR + n], n, crc, "TPG2 mode L")
        if size == (W, H):
            head = flat565.reshape(-1)[:HDR // 2].astype(">u2").tobytes()          # legacy TPG1 mode L: from pixel (0, 0)
            got = _parse(head, MODE_L, MAGIC_V1, W * H * 2 - HDR)
            if got:
                n, crc = got
                return _check(flat565.reshape(-1)[:(HDR + n + 1) // 2].astype(">u2").tobytes()[HDR:HDR + n], n, crc, "TPG1 mode L")
    img = rgb if exact else np.asarray(Image.fromarray(rgb).resize((sw, sh), Image.BOX if w > sw else Image.BILINEAR))
    for cell in cells:                                              # mode R: the cell size is in the header, so probe each size
        if min(size) // cell < MIN_CELLS:
            continue
        flag = 0 if cell == CW else cell
        for s in ladder_r(size, cell):
            px = s * cell
            x0, y0 = (sw - px) // 2, (sh - px) // 2
            head = _levels_to_bytes(_cell_levels(img, x0, y0, s, cell)[:(HDR * 8 + 5) // 6])[:HDR]
            got = _parse(head, MODE_R, MAGIC, capacity(MODE_R, size, cell), flag)
            if got:
                n, crc = got
                return _check(_levels_to_bytes(_cell_levels(img, x0, y0, s, cell))[HDR:HDR + n], n, crc, "TPG2 mode R")
    if size == (W, H):
        f = _levels_to_bytes(np.clip(np.rint(img.astype(np.float32).reshape(GH, CH, GW, CW, 3)[:, 1:3, :, 1:3].mean((1, 3)) / 85.0), 0, 3)
                             .astype(np.uint8).reshape(-1, 3))       # legacy TPG1 mode R: 100 x 90 cells from (0, 0)
        got = _parse(f, MODE_R, MAGIC_V1, GW * GH * 6 // 8 - HDR)
        if got:
            n, crc = got
            return _check(f[HDR:HDR + n], n, crc, "TPG1 mode R")
    return None


def decode(rgb: np.ndarray, native=None, cells=CELLS) -> bytes:
    """rgb: (h, w, 3) uint8 screenshot pixels of ANY size. Returns the payload or raises ValueError.
    native=(w, h): the screen the picture was made for, when `rgb` is a resized copy (robust mode survives that; lossless does not).
    Without it the picture is taken to be the screen itself; a picture that is not 400x360 and holds no grid is also tried as a resized
    copy of a 400x360 screen (the old behaviour)."""
    h, w = rgb.shape[:2]
    sizes = [tuple(native)] if native else [(w, h)] + ([(W, H)] if (w, h) != (W, H) else [])
    for size in sizes:
        got = _try_size(rgb, size, cells)
        if got is not None:
            return got
    raise ValueError("no TPG grid found (not a TPG picture, a wrong `native` size, or a camera photo)")


def decode_file(path: str, native=None) -> bytes:
    return decode(np.asarray(Image.open(path).convert("RGB")), native)



def encode_v1(payload: bytes, mode: int = MODE_L) -> np.ndarray:
    """The legacy TPG1 layout (stream from pixel (0, 0)); only used by the tests to prove old captures still decode."""
    data = header(mode, payload, MAGIC_V1) + payload
    img = np.zeros((H, W), np.uint16)
    if mode == MODE_L:
        data += b"\0" * (len(data) % 2)
        p = np.frombuffer(data, ">u2").astype(np.uint16)
        img.reshape(-1)[:len(p)] = p
        return img
    bits = np.unpackbits(np.frombuffer(data, np.uint8))
    bits = np.concatenate([bits, np.zeros((-len(bits)) % 6, np.uint8)]).reshape(-1, 6)
    cells = (np.array(LV5, np.uint16)[bits[:, 0] * 2 + bits[:, 1]] << 11) | (np.array(LV6, np.uint16)[bits[:, 2] * 2 + bits[:, 3]] << 5) \
        | np.array(LV5, np.uint16)[bits[:, 4] * 2 + bits[:, 5]]
    grid = np.zeros(GW * GH, np.uint16)
    grid[:len(cells)] = cells
    return np.repeat(np.repeat(grid.reshape(GH, GW), CH, 0), CW, 1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    size = lambda t: tuple(int(v) for v in t.lower().split("x"))
    e = sub.add_parser("encode"); e.add_argument("src"); e.add_argument("dst"); e.add_argument("--mode", choices="LR", default="L")
    e.add_argument("--size", type=size, default=(W, H), metavar="WxH", help="screen size (default 400x360)")
    e.add_argument("--cell", type=int, default=CW, help="robust cell in pixels (default 4; use more on a big screen)")
    d = sub.add_parser("decode"); d.add_argument("src"); d.add_argument("dst")
    d.add_argument("--native", type=size, metavar="WxH", help="the screen size, when the picture is a resized copy")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "encode":
            img = to_rgb(encode(open(a.src, "rb").read(), MODE_L if a.mode == "L" else MODE_R, a.size, a.cell))
            Image.fromarray(img).save(a.dst)
        else:
            open(a.dst, "wb").write(decode_file(a.src, a.native))
    except ValueError as ex:
        print(f"invalid: {ex}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
