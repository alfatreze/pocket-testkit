//! Tier Q: find and read a QR code in a picture (a screenshot or a phone photo), feature `qr`. Uses the `rqrr` crate.
//! Dense codes (2 px modules) are tried again with the picture enlarged by whole-number nearest-neighbour steps, as the Python decoder does,
//! because detectors struggle with modules this small. The payload comes back as the bytes the code carried.

use crate::Error;

fn grey(w: usize, h: usize, rgb: &[u8]) -> Vec<u8> {
    (0..w * h)
        .map(|i| {
            let p = &rgb[i * 3..i * 3 + 3];
            ((p[0] as u32 * 299 + p[1] as u32 * 587 + p[2] as u32 * 114) / 1000) as u8
        })
        .collect()
}

fn try_grey(w: usize, h: usize, g: &[u8]) -> Option<Vec<u8>> {
    let mut prepared = rqrr::PreparedImage::prepare_from_greyscale(w, h, |x, y| g[y * w + x]);
    for grid in prepared.detect_grids() {
        let mut out = Vec::new();
        if grid.decode_to(&mut out).is_ok() {
            return Some(out);
        }
    }
    None
}

/// Decode a QR code from packed RGB (`w * h * 3` bytes). `Err(Error::NotFound)` when none can be read.
pub fn decode_rgb(w: usize, h: usize, rgb: &[u8]) -> Result<Vec<u8>, Error> {
    if w == 0 || h == 0 || rgb.len() < w * h * 3 {
        return Err(Error::Invalid(format!("expected {w}x{h} RGB, got {} bytes", rgb.len())));
    }
    let g = grey(w, h, rgb);
    for scale in 1..=4usize {
        let found = if scale == 1 {
            try_grey(w, h, &g)
        } else {
            let (sw, sh) = (w * scale, h * scale);
            let big: Vec<u8> = (0..sw * sh).map(|i| g[(i / sw / scale) * w + (i % sw) / scale]).collect();
            try_grey(sw, sh, &big)
        };
        if let Some(text) = found {
            return Ok(text);
        }
    }
    Err(Error::NotFound)
}
