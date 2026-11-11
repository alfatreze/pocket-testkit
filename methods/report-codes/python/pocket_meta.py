"""Read the core information the Pocket appends to its screenshots (Menu+Start).

A Pocket screenshot is a normal PNG followed by extra bytes after the PNG's final IEND chunk (ordinary PNG readers ignore them):

    block A   ' IPA' + u16 width + u16 height (little endian), then width*height BGRA pixels     a small thumbnail (121x109 seen)
    block B   ' IPA' + u16 width + u16 height, then width*height BGRA pixels                      a full-size copy (400x360 seen)
    footer    600 bytes: '\\x01RPA', then u32 little endian: PNG length, offset of block B, size of block B, 0, 10, <unknown>, 0,
              then NUL-padded text fields: author @72, core @104, version @136, file @168, platform id @424, platform name @440

Layout read from 31 screenshots of Tau cores (all identical in structure); it is NOT an Analogue specification. The meaning of the
fields is inferred from their values. Use the metadata to identify a screenshot, never as the data channel: the PNG pixels are the
lossless data (KB-103), the second image does not equal them.

  python3 python/pocket_meta.py shot.png [--json] [--thumb thumb.png]
As a library:  import pocket_meta; meta = pocket_meta.read("shot.png")   # dict, or None when the file has no Pocket trailer
"""
import argparse, json, struct, sys

MAGIC_IMG = b" IPA"
MAGIC_FOOT = b"\x01RPA"
FOOTER_LEN = 600
FIELDS = (("author", 72, 32), ("core", 104, 32), ("version", 136, 32), ("file", 168, 32), ("platform_id", 424, 16), ("platform_name", 440, 32))


def _png_end(b: bytes):
    """Offset just after the PNG's IEND chunk (walks the chunks), or None if this is not a PNG."""
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    i = 8
    while i + 12 <= len(b):
        n = struct.unpack(">I", b[i:i + 4])[0]
        if b[i + 4:i + 8] == b"IEND":
            return i + 12 + n
        i += 12 + n
    return None


def _text(raw: bytes) -> str:
    return raw.split(b"\0")[0].decode("utf-8", "replace")


def read(src, with_images=False):
    """Metadata dict from a path or bytes, or None if there is no Pocket trailer. Keys: author, core, version, file, platform_id,
    platform_name, png_bytes, thumbnail (w, h), image2 (w, h), consistent (the footer's lengths match the file), and with
    with_images=True also thumbnail_rgb / image2_rgb as (h, w, 3) uint8 arrays (needs numpy)."""
    b = open(src, "rb").read() if isinstance(src, str) else bytes(src)
    end = _png_end(b)
    if end is None or b[end:end + 4] != MAGIC_IMG:
        return None
    t = b[end:]
    try:
        wa, ha = struct.unpack("<HH", t[4:8]); a_end = 8 + wa * ha * 4
        if t[a_end:a_end + 4] != MAGIC_IMG:
            return None
        wb, hb = struct.unpack("<HH", t[a_end + 4:a_end + 8]); b_end = a_end + 8 + wb * hb * 4
        foot = t[b_end:]
        if foot[:4] != MAGIC_FOOT or len(foot) < FOOTER_LEN:
            return None
        png_len, off_b, size_b = struct.unpack("<III", foot[4:16])
    except struct.error:
        return None
    meta = {name: _text(foot[o:o + n]) for name, o, n in FIELDS}
    meta.update(png_bytes=end, thumbnail=(wa, ha), image2=(wb, hb),
                consistent=(png_len == end and off_b == end + a_end and size_b == 8 + wb * hb * 4 and len(foot) == FOOTER_LEN))
    if with_images:
        import numpy as np
        for key, off, w, h in (("thumbnail_rgb", 8, wa, ha), ("image2_rgb", a_end + 8, wb, hb)):
            px = np.frombuffer(t[off:off + w * h * 4], np.uint8).reshape(h, w, 4)
            meta[key] = px[..., [2, 1, 0]].copy()          # BGRA -> RGB
    return meta


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image"); ap.add_argument("--json", action="store_true"); ap.add_argument("--thumb", help="save the thumbnail as a PNG")
    a = ap.parse_args(argv)
    m = read(a.image, with_images=bool(a.thumb))
    if m is None:
        print("no Pocket trailer (not an original Pocket screenshot, or re-saved by an editor)", file=sys.stderr); return 1
    if a.thumb:
        from PIL import Image
        Image.fromarray(m.pop("thumbnail_rgb")).save(a.thumb); m.pop("image2_rgb", None)
    if a.json: print(json.dumps(m))
    else:
        for k in ("author", "core", "version", "file", "platform_id", "platform_name"): print("%-14s %s" % (k, m[k]))
        print("%-14s %dx%d thumbnail, %dx%d second image, footer %s" % ("trailer", *m["thumbnail"], *m["image2"], "consistent" if m["consistent"] else "INCONSISTENT"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
