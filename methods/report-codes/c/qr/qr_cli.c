/* Native command line around qrcode.h: the SAME encoder the Pocket firmware ran.
 * stdin: payload bytes.  argv: [minver maxver mask]  (mask -1 = automatic).  stdout: "QR <ver> <mask> <size> <hexbits>" or "TOOBIG". */
#include <stdio.h>
#include <stdlib.h>
#include "qrcode.h"
static uint8_t in[2800];
static uint8_t buf[QR_BUF_LEN] __attribute__((aligned(4)));
int main(int argc, char **argv)
{
    uint32_t minv = argc > 1 ? (uint32_t)atoi(argv[1]) : 1, maxv = argc > 2 ? (uint32_t)atoi(argv[2]) : QR_MAXV;
    int mask = argc > 3 ? atoi(argv[3]) : -1;
    size_t n = fread(in, 1, sizeof in, stdin), v = 0, m = 0;
    uint32_t vv = 0, mm = 0, sz = qr_encode(in, (uint32_t)n, minv, maxv, mask, buf, &vv, &mm); (void)v; (void)m;
    if (!sz) { puts("TOOBIG"); return 0; }
    printf("QR %u %u %u ", vv, mm, sz);
    uint32_t acc = 0, nb = 0;
    for (uint32_t y = 0; y < sz; y++) for (uint32_t x = 0; x < sz; x++) {
        acc = (acc << 1) | (uint32_t)qr_get(buf, sz, (int)x, (int)y);
        if (++nb == 4u) { putchar("0123456789abcdef"[acc]); acc = 0; nb = 0; }
    }
    if (nb) putchar("0123456789abcdef"[acc << (4u - nb)]);
    putchar('\n'); return 0;
}
