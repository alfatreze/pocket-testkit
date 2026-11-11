//! Reading picture files into packed RGB (features `png`, `jpeg`), and decoding a file in one call.

use crate::{decode_rgb, Decoded, Error, Options};
use std::path::Path;

/// Packed RGB with its size: (width, height, `w * h * 3` bytes). Alpha is dropped; greyscale is replicated.
pub type Rgb = (usize, usize, Vec<u8>);

#[cfg(feature = "png")]
pub fn decode_png_bytes(bytes: &[u8]) -> Result<Rgb, Error> {
    let bad = |e: String| Error::Invalid(format!("invalid PNG: {e}"));
    let mut decoder = png::Decoder::new(std::io::Cursor::new(bytes));
    decoder.set_transformations(png::Transformations::EXPAND | png::Transformations::STRIP_16);
    let mut reader = decoder.read_info().map_err(|e| bad(e.to_string()))?;
    let size = reader.output_buffer_size().ok_or_else(|| bad("frame too large".into()))?;
    let mut buf = vec![0u8; size];
    let info = reader.next_frame(&mut buf).map_err(|e| bad(e.to_string()))?;
    let channels = match info.color_type {
        png::ColorType::Grayscale => 1,
        png::ColorType::GrayscaleAlpha => 2,
        png::ColorType::Rgb => 3,
        png::ColorType::Rgba => 4,
        png::ColorType::Indexed => return Err(bad("indexed PNG was not expanded".into())),
    };
    Ok((info.width as usize, info.height as usize, to_rgb(&buf[..info.buffer_size()], channels)))
}

#[cfg(feature = "jpeg")]
pub fn decode_jpeg_bytes(bytes: &[u8]) -> Result<Rgb, Error> {
    let mut decoder = zune_jpeg::JpegDecoder::new(std::io::Cursor::new(bytes));
    let pixels = decoder.decode().map_err(|e| Error::Invalid(format!("invalid JPEG: {e}")))?;
    let info = decoder.info().ok_or_else(|| Error::Invalid("JPEG had no image info".into()))?;
    let channels = decoder.output_colorspace().map(|s| s.num_components()).unwrap_or(3);
    Ok((info.width as usize, info.height as usize, to_rgb(&pixels, channels)))
}

#[cfg(any(feature = "png", feature = "jpeg"))]
fn to_rgb(buf: &[u8], channels: usize) -> Vec<u8> {
    let mut rgb = Vec::with_capacity(buf.len() / channels * 3);
    for p in buf.chunks_exact(channels) {
        if channels <= 2 {
            rgb.extend_from_slice(&[p[0]; 3]);
        } else {
            rgb.extend_from_slice(&p[..3]);
        }
    }
    rgb
}

/// Decode PNG or JPEG bytes (chosen by their first bytes) into packed RGB.
pub fn decode_image_bytes(bytes: &[u8]) -> Result<Rgb, Error> {
    #[cfg(feature = "png")]
    if bytes.starts_with(&[0x89, b'P', b'N', b'G']) {
        return decode_png_bytes(bytes);
    }
    #[cfg(feature = "jpeg")]
    if bytes.starts_with(&[0xFF, 0xD8]) {
        return decode_jpeg_bytes(bytes);
    }
    Err(Error::Invalid("not a PNG or JPEG this build can read (enable the `png` / `jpeg` features)".into()))
}

/// Read a picture file (PNG or JPEG) into packed RGB.
pub fn read_rgb(path: impl AsRef<Path>) -> Result<Rgb, Error> {
    let bytes = std::fs::read(path.as_ref()).map_err(|e| Error::Invalid(format!("{}: {e}", path.as_ref().display())))?;
    decode_image_bytes(&bytes)
}

/// Read a picture file and decode whatever it carries (grid L or R, then QR).
pub fn decode_file(path: impl AsRef<Path>, opts: &Options) -> Result<Decoded, Error> {
    let (w, h, rgb) = read_rgb(path)?;
    decode_rgb(w, h, &rgb, opts)
}
