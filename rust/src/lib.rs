//! Decode test and diagnostic reports that a device carries out as a picture.
//!
//! Three carriers, one payload and one CRC32 (see the repository README):
//! * **L** lossless colour grid, **R** robust colour grid ([`tpg`]): any screen size, same pixel size everywhere, capacity follows the screen.
//! * **Q** QR code ([`qr`], feature `qr`): resolution independent, the one that survives a phone photo.
//!
//! The core is plain Rust over raw RGB bytes: no file system, no OS calls, no dependencies, so it builds for Windows, macOS, Linux and
//! WebAssembly alike. Files (PNG, JPEG) and QR reading are opt-in features.
//!
//! ```
//! # use pocket_testkit::*;
//! // `rgb` is w*h*3 bytes of a screenshot (any size); here a blank one, so nothing is found.
//! let rgb = vec![0u8; 400 * 360 * 3];
//! assert!(matches!(tpg::decode_rgb(400, 360, &rgb, &Options::default()), Err(Error::NotFound)));
//! ```

pub mod crc;
pub mod tpg;

#[cfg(any(feature = "png", feature = "jpeg"))]
pub mod files;
#[cfg(feature = "qr")]
pub mod qr;

use std::fmt;

/// Which carrier a payload came from.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Tier {
    /// Lossless colour grid (a lossless screenshot only).
    L,
    /// Robust colour grid (survives JPEG q80+ and, with [`Options::native`], a resize).
    R,
    /// QR code (survives a phone photo).
    Q,
}

/// Why a picture could not be decoded. A damaged picture is never returned as a wrong payload.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Error {
    /// No grid and no QR code in the picture.
    NotFound,
    /// A grid header was found but the payload failed its CRC32, or the header is impossible.
    Damaged(String),
    /// The input itself is unusable (bad dimensions, undecodable file, feature not compiled in).
    Invalid(String),
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::NotFound => write!(f, "no pixel grid or QR code found"),
            Error::Damaged(w) => write!(f, "{w} (the picture was altered or cropped, or too much damage)"),
            Error::Invalid(w) => write!(f, "{w}"),
        }
    }
}
impl std::error::Error for Error {}

/// Decoder options. The default reads the picture at its own size.
#[derive(Debug, Clone)]
pub struct Options {
    /// The screen size the grid was made for, when the picture is a resized copy (robust grids only).
    pub native: Option<(usize, usize)>,
    /// Robust cell sizes to try (pixels), in order. The default tries 4 first, then the others.
    pub cells: Vec<usize>,
}

impl Default for Options {
    fn default() -> Self {
        Options { native: None, cells: tpg::CELLS.to_vec() }
    }
}

/// What was read.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Decoded {
    pub tier: Tier,
    pub payload: Vec<u8>,
}

/// Decode a picture given as packed RGB (`w * h * 3` bytes): the colour grid first, then (feature `qr`) a QR code.
pub fn decode_rgb(w: usize, h: usize, rgb: &[u8], opts: &Options) -> Result<Decoded, Error> {
    match tpg::decode_rgb(w, h, rgb, opts) {
        Ok((tier, payload)) => return Ok(Decoded { tier, payload }),
        Err(Error::NotFound) => {}
        Err(e) => return Err(e), // a damaged grid is loud: do not fall through to guessing
    }
    #[cfg(feature = "qr")]
    {
        let text = qr::decode_rgb(w, h, rgb)?;
        Ok(Decoded { tier: Tier::Q, payload: text })
    }
    #[cfg(not(feature = "qr"))]
    Err(Error::NotFound)
}
