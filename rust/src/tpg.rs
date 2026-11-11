//! The colour pixel grid (TPG2, plus the legacy TPG1 of the first Pocket captures) at **any screen size**.
//!
//! A record is a 16-byte header (`TPG2`, mode, flags, reserved, length, CRC32) plus the payload, written into a square block centred on the
//! screen. The pixel size is the same everywhere (1 px per 16 bits for mode L; 4 px cells, 2 bits per channel for mode R), so a bigger screen
//! holds more. The block's side comes from a ladder that depends only on the screen's short side; header byte 5 carries the robust cell size
//! when it is not 4. For a 400x360 screen this is byte-identical to the original Pocket format. Port of `python/tpg.py`; no error
//! correction: the CRC makes damage fail loudly. See `docs/RESOLUTIONS.md` in the repository for capacities.

use crate::{crc::crc32, Error, Options, Tier};
use std::borrow::Cow;

pub const DEFAULT_W: usize = 400;
pub const DEFAULT_H: usize = 360;
pub const CELL: usize = 4;
pub const HDR: usize = 16;
pub const MODE_L: u8 = 0;
pub const MODE_R: u8 = 1;
/// A robust block needs at least this many cells on its short side.
pub const MIN_CELLS: usize = 8;
/// Robust cell sizes the decoder tries, the default first.
pub const CELLS: [usize; 12] = [4, 2, 3, 5, 6, 8, 10, 12, 16, 20, 24, 32];

const MAGIC: &[u8; 4] = b"TPG2";
const MAGIC_V1: &[u8; 4] = b"TPG1";

fn base_l(i: usize) -> usize {
    if i < 5 { 64 + 16 * i } else { 128 + 32 * (i - 4) }
}
fn base_r(i: usize) -> usize {
    if i < 4 { 20 + 4 * i } else { 32 + 8 * (i - 3) }
}
fn ladder(cap: usize, base: fn(usize) -> usize) -> Vec<usize> {
    let mut v = Vec::new();
    let mut i = 0;
    while base(i) < cap {
        v.push(base(i));
        i += 1;
    }
    v.push(cap);
    v
}

/// Block sides in pixels for mode L on a `w` x `h` screen.
pub fn ladder_l(w: usize, h: usize) -> Vec<usize> {
    ladder(w.min(h), base_l)
}
/// Block sides in cells for mode R, or `None` if the screen is too small for `cell`-pixel cells.
pub fn ladder_r(w: usize, h: usize, cell: usize) -> Option<Vec<usize>> {
    if cell == 0 || w.min(h) / cell < MIN_CELLS {
        return None;
    }
    Some(ladder(w.min(h) / cell, base_r))
}

fn units(side: usize, mode: u8) -> usize {
    if mode == MODE_L { side * side * 2 } else { side * side * 6 / 8 }
}

/// Payload capacity in bytes for a mode on a `w` x `h` screen (0 if unusable).
pub fn capacity(mode: u8, w: usize, h: usize, cell: usize) -> usize {
    let side = if mode == MODE_L { Some(w.min(h)) } else { ladder_r(w, h, cell).map(|l| *l.last().unwrap()) };
    side.map_or(0, |s| units(s, mode) - HDR)
}

/// `Ok(Some((length, crc)))` when the 16 header bytes carry this magic, mode and flag.
fn parse_header(head: &[u8], mode: u8, magic: &[u8; 4], cap: usize, flag: u8) -> Result<Option<(usize, u32)>, Error> {
    if head.len() < HDR || &head[..4] != magic || head[4] != mode || head[5] != flag || head[6] != 0 || head[7] != 0 {
        return Ok(None);
    }
    let n = u32::from_be_bytes([head[8], head[9], head[10], head[11]]) as usize;
    let crc = u32::from_be_bytes([head[12], head[13], head[14], head[15]]);
    if n > cap {
        return Err(Error::Damaged("the pixel grid header length is impossible".into()));
    }
    Ok(Some((n, crc)))
}

fn check(raw: &[u8], n: usize, crc: u32, what: &str) -> Result<Vec<u8>, Error> {
    if raw.len() != n || crc32(raw) != crc {
        return Err(Error::Damaged(format!("{what}: CRC mismatch")));
    }
    Ok(raw.to_vec())
}

fn rgb565(px: &[u8]) -> u16 {
    ((px[0] as u16 >> 3) << 11) | ((px[1] as u16 >> 2) << 5) | (px[2] as u16 >> 3)
}

/// The first `bytes` stream bytes of a lossless block (one RGB565 value per pixel, row-major, high byte first).
fn lossless_stream(rgb: &[u8], stride: usize, x0: usize, y0: usize, side: usize, bytes: usize) -> Vec<u8> {
    let mut out = Vec::with_capacity(bytes + 1);
    'rows: for y in 0..side {
        for x in 0..side {
            if out.len() >= bytes {
                break 'rows;
            }
            let v = rgb565(&rgb[((y0 + y) * stride + x0 + x) * 3..][..3]);
            out.push((v >> 8) as u8);
            out.push(v as u8);
        }
    }
    out
}

/// The bit stream carried by the first `cells` cells of a robust block: per cell and channel the mean of the cell's centre (the cell
/// without its outer quarter on each side, where blur from the neighbours lives), rounded to the nearest of the levels 0, 85, 170, 255.
fn robust_stream(img: &[u8], stride: usize, x0: usize, y0: usize, side: usize, cell: usize, cells: usize) -> Vec<u8> {
    let m = cell / 4;
    let (lo, hi) = (m, cell - m);
    let count = ((hi - lo) * (hi - lo)) as f32;
    let mut bits: Vec<u8> = Vec::with_capacity(cells * 6);
    for i in 0..cells.min(side * side) {
        let (cx, cy) = (i % side, i / side);
        for c in 0..3 {
            let mut sum = 0u32;
            for dy in lo..hi {
                for dx in lo..hi {
                    sum += img[((y0 + cy * cell + dy) * stride + x0 + cx * cell + dx) * 3 + c] as u32;
                }
            }
            let level = (((sum as f32 / count) / 85.0).round_ties_even() as i32).clamp(0, 3) as u8;
            bits.push(level >> 1);
            bits.push(level & 1);
        }
    }
    bits.chunks_exact(8).map(|b| b.iter().fold(0u8, |a, &bit| (a << 1) | bit)).collect()
}

fn axis_weights(src: usize, dst: usize) -> Vec<Vec<(usize, f32)>> {
    let mut out = Vec::with_capacity(dst);
    if dst < src {
        // downscale: area average (box filter) over the source span of each output pixel
        let scale = src as f32 / dst as f32;
        for i in 0..dst {
            let (a, b) = (i as f32 * scale, (i + 1) as f32 * scale);
            let mut ws = Vec::new();
            let mut total = 0.0;
            for s in (a.floor() as usize)..(b.ceil() as usize).min(src) {
                let w = (b.min(s as f32 + 1.0) - a.max(s as f32)).max(0.0);
                if w > 0.0 {
                    ws.push((s, w));
                    total += w;
                }
            }
            for p in ws.iter_mut() {
                p.1 /= total;
            }
            out.push(ws);
        }
    } else {
        // upscale: bilinear between pixel centres
        let scale = src as f32 / dst as f32;
        for i in 0..dst {
            let pos = (i as f32 + 0.5) * scale - 0.5;
            let i0 = pos.floor();
            let f = pos - i0;
            let a = (i0.max(0.0) as usize).min(src - 1);
            let b = ((i0 + 1.0).max(0.0) as usize).min(src - 1);
            out.push(vec![(a, 1.0 - f), (b, f)]);
        }
    }
    out
}

/// Resample packed RGB to `sw` x `sh` (box filter when shrinking, bilinear when growing) so a resized copy can be read at the screen's own size.
fn resize(rgb: &[u8], w: usize, h: usize, sw: usize, sh: usize) -> Vec<u8> {
    let (wx, wy) = (axis_weights(w, sw), axis_weights(h, sh));
    let mut tmp = vec![0f32; sw * h * 3];
    for y in 0..h {
        for (x, ws) in wx.iter().enumerate() {
            for c in 0..3 {
                tmp[(y * sw + x) * 3 + c] = ws.iter().map(|&(s, wt)| rgb[(y * w + s) * 3 + c] as f32 * wt).sum();
            }
        }
    }
    let mut out = vec![0u8; sw * sh * 3];
    for (y, ws) in wy.iter().enumerate() {
        for x in 0..sw {
            for c in 0..3 {
                let v: f32 = ws.iter().map(|&(s, wt)| tmp[(s * sw + x) * 3 + c] * wt).sum();
                out[(y * sw + x) * 3 + c] = v.round().clamp(0.0, 255.0) as u8;
            }
        }
    }
    out
}

fn try_size(rgb: &[u8], w: usize, h: usize, size: (usize, usize), cells: &[usize]) -> Result<Option<(Tier, Vec<u8>)>, Error> {
    let (sw, sh) = size;
    let exact = (w, h) == size;
    if exact {
        for s in ladder_l(sw, sh) {
            let (x0, y0) = ((sw - s) / 2, (sh - s) / 2);
            let head = lossless_stream(rgb, sw, x0, y0, s, HDR);
            if let Some((n, crc)) = parse_header(&head, MODE_L, MAGIC, capacity(MODE_L, sw, sh, CELL), 0)? {
                let all = lossless_stream(rgb, sw, x0, y0, s, HDR + n);
                let body = all.get(HDR..(HDR + n).min(all.len())).unwrap_or(&[]);
                return check(body, n, crc, "TPG2 mode L").map(|p| Some((Tier::L, p)));
            }
        }
        if size == (DEFAULT_W, DEFAULT_H) {
            // legacy TPG1 mode L: from pixel (0, 0) over the whole screen
            let mut all: Vec<u8> = Vec::with_capacity(sw * sh * 2);
            for i in 0..sw * sh {
                let v = rgb565(&rgb[i * 3..][..3]);
                all.push((v >> 8) as u8);
                all.push(v as u8);
            }
            if let Some((n, crc)) = parse_header(&all, MODE_L, MAGIC_V1, sw * sh * 2 - HDR, 0)? {
                return check(&all[HDR..HDR + n], n, crc, "TPG1 mode L").map(|p| Some((Tier::L, p)));
            }
        }
    }
    let img: Cow<[u8]> = if exact { Cow::Borrowed(rgb) } else { Cow::Owned(resize(rgb, w, h, sw, sh)) };
    for &cell in cells {
        let Some(ladder) = ladder_r(sw, sh, cell) else { continue };
        let flag = if cell == CELL { 0 } else { cell as u8 };
        for s in ladder {
            let px = s * cell;
            let (x0, y0) = ((sw - px) / 2, (sh - px) / 2);
            let head = robust_stream(&img, sw, x0, y0, s, cell, (HDR * 8).div_ceil(6));
            if let Some((n, crc)) = parse_header(&head, MODE_R, MAGIC, capacity(MODE_R, sw, sh, cell), flag)? {
                let all = robust_stream(&img, sw, x0, y0, s, cell, s * s);
                let body = all.get(HDR..(HDR + n).min(all.len())).unwrap_or(&[]);
                return check(body, n, crc, "TPG2 mode R").map(|p| Some((Tier::R, p)));
            }
        }
    }
    if size == (DEFAULT_W, DEFAULT_H) {
        // legacy TPG1 mode R: a 100 x 90 cell grid from (0, 0)
        let (gw, gh) = (sw / CELL, sh / CELL);
        let all = robust_stream(&img, sw, 0, 0, gw, CELL, gw * gh);
        if let Some((n, crc)) = parse_header(&all, MODE_R, MAGIC_V1, gw * gh * 6 / 8 - HDR, 0)? {
            return check(&all[HDR..HDR + n], n, crc, "TPG1 mode R").map(|p| Some((Tier::R, p)));
        }
    }
    Ok(None)
}

/// Decode the colour grid from packed RGB (`w * h * 3` bytes) of any size. `Err(Error::NotFound)`: no grid. `Err(Error::Damaged)`: a grid
/// header was found but the payload fails its CRC (never a guess). Without `opts.native` the picture is taken to be the screen itself; a
/// picture that is not 400x360 and holds no grid is also tried as a resized copy of a 400x360 screen (the old behaviour).
pub fn decode_rgb(w: usize, h: usize, rgb: &[u8], opts: &Options) -> Result<(Tier, Vec<u8>), Error> {
    if w == 0 || h == 0 || rgb.len() < w * h * 3 {
        return Err(Error::Invalid(format!("expected {w}x{h} RGB, got {} bytes", rgb.len())));
    }
    let mut sizes = match opts.native {
        Some(n) => vec![n],
        None => vec![(w, h)],
    };
    if opts.native.is_none() && (w, h) != (DEFAULT_W, DEFAULT_H) {
        sizes.push((DEFAULT_W, DEFAULT_H));
    }
    for size in sizes {
        if let Some(found) = try_size(rgb, w, h, size, &opts.cells)? {
            return Ok(found);
        }
    }
    Err(Error::NotFound)
}
