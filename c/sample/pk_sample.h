/* Sample test pages for pocket-testkit: nine pages that show the three carriers at typical sizes and at their limits, for ANY screen size.
 * Portable C, no libc, no malloc, no I/O: the caller supplies a payload buffer, a QR work buffer and a row callback, so the same file runs in
 * a host program (c/sample/host_gallery.c), in tests, and inside a core's firmware. Hardware: not run on a Pocket by this kit.
 *
 * Pages (page index -> carrier, payload bytes; "cap" = the capacity for the screen):
 *   0 L-sample 256 B   1 L-typical 4 KB   2 L-max cap          lossless grid, screenshot file only
 *   3 R-sample 128 B   4 R-max cap                              robust grid, survives JPEG and resize
 *   5 Q-photo 120 B    6 Q-photo-max 271 B   7 Q-careful 1,003 B   8 Q-max 2,699 B (locked until `unlocked` is set)
 * A payload larger than the screen can hold is clamped (info.bytes says how much). Every payload starts with a text line saying which
 * page it is, so a decoded picture identifies itself; the rest is a fixed filler pattern a test can check byte for byte (pk_filler). */
#ifndef PK_SAMPLE_H
#define PK_SAMPLE_H
#include <stdint.h>
#include "../tpg.h"
#include "../qr/qrcode.h"
#include "../qr/qr_policy.h"

#define PK_SAMPLE_PAGES 9u
#define PK_SAMPLE_PAYLOAD_MAX 1048576u      /* enough for lossless 720x720; smaller screens need less */
#define PK_QUIET 4u                         /* QR border in modules; keep equal to python/qr_tier.py QUIET */

typedef struct { const char *name; char tier; uint32_t want, maxver; int locked; } pk_page_def;
static const pk_page_def pk_pages[PK_SAMPLE_PAGES] = {
    { "L-sample",     'L',       256u, 0u,            0 },
    { "L-typical",    'L',      4096u, 0u,            0 },
    { "L-max",        'L', 0xFFFFFFFFu, 0u,           0 },
    { "R-sample",     'R',       128u, 0u,            0 },
    { "R-max",        'R', 0xFFFFFFFFu, 0u,           0 },
    { "Q-photo",      'Q',       120u, QR_V_PHOTO,    0 },
    { "Q-photo-max",  'Q',       271u, QR_V_PHOTO,    0 },
    { "Q-careful",    'Q',      1003u, QR_V_CAREFUL,  0 },
    { "Q-max",        'Q',      2699u, QR_V_MAX,      1 },
};
typedef struct { const char *name; char tier; uint32_t bytes, want, version; int locked; } pk_page_info;

/* Largest QR version up to maxver whose symbol plus border fits with modules of at least 2 px; 0 if none. */
static inline uint32_t pk_qr_fit(uint32_t w, uint32_t h, uint32_t maxver)
{
    uint32_t s = w < h ? w : h;
    for (uint32_t v = maxver; v >= 1u; v--) if ((QR_SIZE(v) + 2u * PK_QUIET) * 2u <= s) return v;
    return 0u;
}
static inline uint32_t pk_qr_len_max(uint32_t v) { return (8u * qr_data_cw(v) - 4u - (v < 10u ? 8u : 16u)) / 8u; }

/* What page `page` carries on a w x h screen. Returns 0 when the page cannot be drawn there (screen too small). */
static inline int pk_sample_info(uint32_t page, uint32_t w, uint32_t h, pk_page_info *o)
{
    if (page >= PK_SAMPLE_PAGES) return 0;
    const pk_page_def *d = &pk_pages[page];
    uint32_t cap = 0, n = 0, v = 0;
    if (d->tier == 'Q') { v = pk_qr_fit(w, h, d->maxver); if (!v) return 0; cap = pk_qr_len_max(v); }
    else cap = tpg_capacity_ex(d->tier == 'L' ? TPG_MODE_L : TPG_MODE_R, w, h, TPG_CELL);
    if (!cap) return 0;
    n = d->want < cap ? d->want : cap;
    o->name = d->name; o->tier = d->tier; o->bytes = n; o->want = d->want == 0xFFFFFFFFu ? cap : d->want; o->version = v; o->locked = d->locked;
    return 1;
}

/* Filler: byte i (0-based, counted after the title line) of page p. Tests use the same formula. */
static inline uint8_t pk_filler(uint32_t page, uint32_t i)
{
    return (i % 64u) == 63u ? (uint8_t)'\n' : (uint8_t)('a' + (i * 7u + page) % 26u);
}
static inline uint32_t pk_put_u(uint8_t *b, uint32_t pos, uint32_t cap, uint32_t v)
{
    char t[10]; uint32_t n = 0; do { t[n++] = (char)('0' + v % 10u); v /= 10u; } while (v);
    while (n && pos < cap) b[pos++] = (uint8_t)t[--n];
    return pos;
}
static inline uint32_t pk_put_s(uint8_t *b, uint32_t pos, uint32_t cap, const char *s)
{
    while (*s && pos < cap) b[pos++] = (uint8_t)*s++;
    return pos;
}
/* Fill the payload for a page: "pocket-testkit sample page=P name=N tier=T size=WxH bytes=B\n" then the filler. */
static inline void pk_sample_payload(uint32_t page, uint32_t w, uint32_t h, const pk_page_info *in, uint8_t *b)
{
    uint32_t n = in->bytes, p = 0;
    p = pk_put_s(b, p, n, "pocket-testkit sample page="); p = pk_put_u(b, p, n, page);
    p = pk_put_s(b, p, n, " name="); p = pk_put_s(b, p, n, in->name);
    p = pk_put_s(b, p, n, " tier="); { char t[2] = { in->tier, 0 }; p = pk_put_s(b, p, n, t); }
    p = pk_put_s(b, p, n, " size="); p = pk_put_u(b, p, n, w); p = pk_put_s(b, p, n, "x"); p = pk_put_u(b, p, n, h);
    p = pk_put_s(b, p, n, " bytes="); p = pk_put_u(b, p, n, n); p = pk_put_s(b, p, n, "\n");
    for (uint32_t i = 0; p < n; i++, p++) b[p] = pk_filler(page, i);
}

typedef void (*pk_row_fn)(void *ctx, uint32_t y, const uint16_t *rgb565, uint32_t w);

/* Draw page `page` on a w x h screen by calling row(ctx, y, pixels, w) for y = 0..h-1.
 * payload: PK_SAMPLE_PAYLOAD_MAX bytes (less is enough for small screens: pass its size in payload_len);
 * qrbuf: QR_BUF_LEN bytes, 4-byte aligned (only used by Q pages); rowbuf: w uint16_t.
 * A locked page (Q-max) draws red diagonal stripes unless `unlocked` is non-zero: the caller should make that a deliberate key press.
 * A small marker of page+1 white squares is drawn in the top-left corner when it does not touch the code.
 * Returns 1 drawn, 0 page unusable on this screen, -1 payload buffer too small, -2 the code did not fit its density level. */
static inline int pk_sample_draw(uint32_t page, uint32_t w, uint32_t h, int unlocked, uint8_t *payload, uint32_t payload_len,
                                 uint8_t *qrbuf, uint16_t *rowbuf, pk_row_fn row, void *ctx, pk_page_info *info_out)
{
    pk_page_info in;
    if (!pk_sample_info(page, w, h, &in)) return 0;
    if (info_out) *info_out = in;
    int stripes = in.locked && !unlocked;
    uint32_t bx0 = 0, by0 = 0, bx1 = w, by1 = h;            /* the content's bounding box */
    tpg_t t; uint32_t qsz = 0, qpx = 0, qx0 = 0, qy0 = 0;
    if (!stripes) {
        if (in.bytes > payload_len) return -1;
        pk_sample_payload(page, w, h, &in, payload);
        if (in.tier == 'Q') {
            uint32_t ver, mask;
            qsz = qr_encode(payload, in.bytes, 1u, pk_pages[page].maxver, -1, qrbuf, &ver, &mask);
            if (!qsz) return -2;
            uint32_t s = w < h ? w : h, n = qsz + 2u * PK_QUIET;
            qpx = s / n; if (qpx < 2u) return -2;
            qx0 = (w - n * qpx) / 2u; qy0 = (h - n * qpx) / 2u;
            bx0 = qx0; by0 = qy0; bx1 = qx0 + n * qpx; by1 = qy0 + n * qpx;
        } else {
            if (!tpg_init_ex(&t, payload, in.bytes, in.tier == 'L' ? TPG_MODE_L : TPG_MODE_R, w, h, TPG_CELL)) return 0;
            bx0 = t.x0; by0 = t.y0; bx1 = t.x0 + t.px; by1 = t.y0 + t.px;
        }
    }
    uint32_t mk_w = 5u * (page + 1u) + 2u;
    int marker = !stripes && (bx0 > mk_w + 2u || by0 > 8u);
    for (uint32_t y = 0; y < h; y++) {
        for (uint32_t x = 0; x < w; x++) {
            uint16_t c = 0;
            if (stripes) c = (((x + y) / 8u) & 1u) ? 0xF800u : 0u;
            else if (x >= bx0 && x < bx1 && y >= by0 && y < by1) {
                if (in.tier == 'Q') {
                    int mx = (int)((x - qx0) / qpx) - (int)PK_QUIET, my = (int)((y - qy0) / qpx) - (int)PK_QUIET;
                    int dark = mx >= 0 && my >= 0 && mx < (int)qsz && my < (int)qsz && qr_get(qrbuf, qsz, mx, my);
                    c = dark ? 0u : 0xFFFFu;
                } else c = tpg_pixel(&t, x, y);
            }
            if (marker && y >= 2u && y < 5u && x >= 2u && x < mk_w && ((x - 2u) % 5u) < 3u) c = 0xFFFFu;
            rowbuf[x] = c;
        }
        row(ctx, y, rowbuf, w);
    }
    return 1;
}
#endif
