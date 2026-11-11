/* TPG2 (pixel grid) encoder core: portable, pure, no I/O. Format: python/tpg.py docstring.
 * A record is shown as a square block of RGB565 values, centred on the screen (any size; 400x360 by default) and as small as the report allows; this file only
 * answers "where is the block" and "which value is pixel (x, y)" so the page (fw/suite.inc, TAU_TPG) can write it through the SDRAM mailbox
 * and a host test can compare every pixel with the Python codec. */
#ifndef TPG_CORE_H
#define TPG_CORE_H
#include <stdint.h>

#define TPG_W 400u
#define TPG_H 360u
#define TPG_HDR 16u
#define TPG_MODE_L 0u
#define TPG_MODE_R 1u
#define TPG_CELL 4u

#ifndef TPG_FN
#define TPG_FN static
#endif
#ifndef TPG_CRC32
/* the firmware defines TPG_CRC32 as sr_crc32 (fw/suite_core.h) so the loop exists once */
TPG_FN uint32_t tpg_crc32(const uint8_t *p, uint32_t n)
{
    uint32_t c = 0xFFFFFFFFu;
    for (uint32_t i = 0; i < n; i++) {
        c ^= p[i];
        for (int k = 0; k < 8; k++) c = (c >> 1) ^ (0xEDB88320u & (uint32_t)-(int32_t)(c & 1u));
    }
    return ~c;
}
#define TPG_CRC32 tpg_crc32
#endif

/* ANY SCREEN SIZE. The block is a square centred on the screen; its side comes from a ladder that depends only on the screen's short side
 * (python/tpg.py _base_l / _base_r), so this file, the Python codec and the decoder agree for every resolution. The cell size (mode R) is
 * fixed in pixels, so a bigger screen holds more, a smaller one less. For 400x360 and 4 px cells the ladders are the original ones. */
#define TPG_MIN_CELLS 8u

static inline uint32_t tpg_base_l(uint32_t i) { return i < 5u ? 64u + 16u * i : 128u + 32u * (i - 4u); }
static inline uint32_t tpg_base_r(uint32_t i) { return i < 4u ? 20u + 4u * i : 32u + 8u * (i - 3u); }

/* Step i of the ladder for a short side of cap units (pixels for mode L, cells for mode R); 0 past the end. */
TPG_FN uint32_t tpg_step(uint32_t i, uint32_t cap, uint32_t mode)
{
    uint32_t n = 0;
    while ((mode == TPG_MODE_L ? tpg_base_l(n) : tpg_base_r(n)) < cap) n++;
    if (i < n) return mode == TPG_MODE_L ? tpg_base_l(i) : tpg_base_r(i);
    return i == n ? cap : 0u;
}

/* rec/len/mode, the 16-byte header, the block (x0, y0, px = side in pixels), its side in stream units (pixels for L, cells for R), the screen and the cell. */
typedef struct { const uint8_t *rec; uint32_t len, mode, side, x0, y0, px, w, h, cell; uint8_t hdr[TPG_HDR]; } tpg_t;

TPG_FN uint32_t tpg_units(uint32_t side, uint32_t mode)       /* stream bytes a block holds, header included */
{
    return mode == TPG_MODE_L ? side * side * 2u : side * side * 6u / 8u;
}

TPG_FN uint32_t tpg_cap_units(uint32_t mode, uint32_t w, uint32_t h, uint32_t cell)   /* the largest block side in stream units; 0 = unusable */
{
    uint32_t s = w < h ? w : h;
    if (mode == TPG_MODE_L) return s;
    if (cell == 0u) return 0u;
    s /= cell;
    return s < TPG_MIN_CELLS ? 0u : s;
}

/* Payload capacity in bytes for a mode on a w x h screen with `cell`-pixel robust cells (0 if the screen is too small). */
TPG_FN uint32_t tpg_capacity_ex(uint32_t mode, uint32_t w, uint32_t h, uint32_t cell)
{
    uint32_t c = tpg_cap_units(mode, w, h, cell);
    return c ? tpg_units(c, mode) - TPG_HDR : 0u;
}
/* The original 400x360, 4 px signature: 259,184 for L, 6,059 for R. */
TPG_FN uint32_t tpg_capacity(uint32_t mode) { return tpg_capacity_ex(mode, TPG_W, TPG_H, TPG_CELL); }

/* Returns 0 when the record does not fit the mode on this screen. Picks the smallest ladder step that holds it. */
TPG_FN int tpg_init_ex(tpg_t *t, const uint8_t *rec, uint32_t len, uint32_t mode, uint32_t w, uint32_t h, uint32_t cell)
{
    if (mode > TPG_MODE_R || len > tpg_capacity_ex(mode, w, h, cell)) return 0;
    uint32_t cap = tpg_cap_units(mode, w, h, cell), side = cap;
    for (uint32_t i = 0; tpg_step(i, cap, mode); i++) {
        side = tpg_step(i, cap, mode);
        if (tpg_units(side, mode) >= TPG_HDR + len) break;
    }
    uint32_t crc = TPG_CRC32(rec, len);
    t->rec = rec; t->len = len; t->mode = mode; t->side = side; t->w = w; t->h = h; t->cell = cell;
    t->px = mode == TPG_MODE_L ? side : side * cell;
    t->x0 = (w - t->px) / 2u; t->y0 = (h - t->px) / 2u;
    t->hdr[0] = 'T'; t->hdr[1] = 'P'; t->hdr[2] = 'G'; t->hdr[3] = '2';
    t->hdr[4] = (uint8_t)mode; t->hdr[5] = (uint8_t)((mode == TPG_MODE_R && cell != TPG_CELL) ? cell : 0u); t->hdr[6] = 0; t->hdr[7] = 0;
    for (int k = 0; k < 4; k++) { t->hdr[8 + k] = (uint8_t)(len >> (24 - 8 * k)); t->hdr[12 + k] = (uint8_t)(crc >> (24 - 8 * k)); }
    return 1;
}
/* The original 400x360, 4 px signature. */
TPG_FN int tpg_init(tpg_t *t, const uint8_t *rec, uint32_t len, uint32_t mode) { return tpg_init_ex(t, rec, len, mode, TPG_W, TPG_H, TPG_CELL); }

TPG_FN uint32_t tpg_byte(const tpg_t *t, uint32_t i)
{
    if (i < TPG_HDR) return t->hdr[i];
    i -= TPG_HDR;
    return i < t->len ? t->rec[i] : 0u;
}

/* The RGB565 value of SCREEN pixel (x, y), which must lie inside the block [x0, x0 + px) x [y0, y0 + px). */
TPG_FN uint16_t tpg_pixel(const tpg_t *t, uint32_t x, uint32_t y)
{
    const uint32_t lx = x - t->x0, ly = y - t->y0;
    if (t->mode == TPG_MODE_L) {
        uint32_t i = 2u * (ly * t->side + lx);
        return (uint16_t)((tpg_byte(t, i) << 8) | tpg_byte(t, i + 1u));
    }
    static const uint8_t l5[4] = { 0, 10, 21, 31 }, l6[4] = { 0, 21, 42, 63 };
    uint32_t bit = 6u * ((ly / t->cell) * t->side + lx / t->cell);       /* first stream bit of this cell */
    uint32_t byte = bit >> 3, sh = bit & 7u;
    uint32_t v = (tpg_byte(t, byte) << 8) | tpg_byte(t, byte + 1u);        /* 16 bits holding the 6 we need */
    v = (v >> (10u - sh)) & 63u;
    return (uint16_t)((l5[(v >> 4) & 3u] << 11) | (l6[(v >> 2) & 3u] << 5) | l5[v & 3u]);
}
#endif
