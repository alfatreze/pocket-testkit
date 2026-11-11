//! CRC-32 (IEEE, the zlib/PNG polynomial 0xEDB88320), table-free so the crate has no dependencies.

pub fn crc32(data: &[u8]) -> u32 {
    let mut c = 0xFFFF_FFFFu32;
    for &b in data {
        c ^= b as u32;
        for _ in 0..8 {
            c = (c >> 1) ^ (0xEDB8_8320 & (0u32.wrapping_sub(c & 1)));
        }
    }
    !c
}

#[cfg(test)]
mod tests {
    #[test]
    fn known_value() {
        assert_eq!(super::crc32(b"123456789"), 0xCBF4_3926);
    }
}
