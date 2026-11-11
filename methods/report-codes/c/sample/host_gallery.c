/* Render every sample page at one or more screen sizes to binary PPM files (convert to PNG with examples/make_gallery.py).
 *   host_gallery OUTDIR [-u] [WxH ...]      default sizes 160x144 400x360 800x480; -u unlocks the Q-max page
 * Writes OUTDIR/page<N>_<name>_<W>x<H>.ppm and OUTDIR/manifest.tsv (file, page, name, tier, bytes, want, w, h). RGB565 is expanded by bit
 * replication, as a Pocket screenshot does (python/tpg.py to_rgb). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pk_sample.h"

typedef struct { FILE *f; } sink_t;
static void row_cb(void *ctx, uint32_t y, const uint16_t *p, uint32_t w)
{
    (void)y; sink_t *s = ctx;
    for (uint32_t x = 0; x < w; x++) {
        uint32_t r = (p[x] >> 11) & 31u, g = (p[x] >> 5) & 63u, b = p[x] & 31u;
        uint8_t px[3] = { (uint8_t)((r << 3) | (r >> 2)), (uint8_t)((g << 2) | (g >> 4)), (uint8_t)((b << 3) | (b >> 2)) };
        fwrite(px, 1, 3, s->f);
    }
}
static uint8_t qrbuf[QR_BUF_LEN] __attribute__((aligned(4)));
int main(int argc, char **argv)
{
    if (argc < 2) { fputs("usage: host_gallery OUTDIR [-u] [WxH ...]\n", stderr); return 2; }
    const char *dir = argv[1]; int unlock = 0;
    uint32_t sw[16], sh[16], ns = 0;
    for (int i = 2; i < argc; i++) {
        if (!strcmp(argv[i], "-u")) unlock = 1;
        else if (ns < 16 && sscanf(argv[i], "%ux%u", &sw[ns], &sh[ns]) == 2) ns++;
    }
    if (!ns) { sw[0] = 160; sh[0] = 144; sw[1] = 400; sh[1] = 360; sw[2] = 800; sh[2] = 480; ns = 3; }
    uint8_t *payload = malloc(PK_SAMPLE_PAYLOAD_MAX);
    uint16_t *rowbuf = malloc(2u * 4096u);
    char path[512];
    snprintf(path, sizeof path, "%s/manifest.tsv", dir);
    FILE *mf = fopen(path, "w"); if (!mf || !payload || !rowbuf) { perror("setup"); return 1; }
    fputs("file\tpage\tname\ttier\tbytes\twant\tw\th\tstatus\n", mf);
    for (uint32_t k = 0; k < ns; k++) for (uint32_t p = 0; p < PK_SAMPLE_PAGES; p++) {
        pk_page_info in;
        if (!pk_sample_info(p, sw[k], sh[k], &in)) { fprintf(mf, "-\t%u\t%s\t%c\t0\t0\t%u\t%u\tunusable\n", p, pk_pages[p].name, pk_pages[p].tier, sw[k], sh[k]); continue; }
        snprintf(path, sizeof path, "%s/page%u_%s_%ux%u.ppm", dir, p, in.name, sw[k], sh[k]);
        FILE *f = fopen(path, "wb"); if (!f) { perror(path); return 1; }
        fprintf(f, "P6\n%u %u\n255\n", sw[k], sh[k]);
        sink_t s = { f };
        int r = pk_sample_draw(p, sw[k], sh[k], unlock, payload, PK_SAMPLE_PAYLOAD_MAX, qrbuf, rowbuf, row_cb, &s, &in);
        fclose(f);
        fprintf(mf, "%s\t%u\t%s\t%c\t%u\t%u\t%u\t%u\t%s\n", path + strlen(dir) + 1, p, in.name, in.tier, in.bytes, in.want, sw[k], sh[k],
                r == 1 ? (in.locked && !unlock ? "locked" : "ok") : "error");
    }
    fclose(mf); free(payload); free(rowbuf); return 0;
}
