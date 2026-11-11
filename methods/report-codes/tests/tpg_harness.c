/* prints the block of tpg.h for (w h mode cell len) as hex RGB565, row by row: "BLOCK x0 y0 px" then px lines. The record is rec(n) of tests/test_tpg_c.py. */
#include <stdio.h>
#include <stdlib.h>
#include "../c/tpg.h"
int main(int argc, char **argv)
{
    if (argc < 6) return 2;
    uint32_t w = (uint32_t)atoi(argv[1]), h = (uint32_t)atoi(argv[2]), mode = (uint32_t)atoi(argv[3]), cell = (uint32_t)atoi(argv[4]), n = (uint32_t)atoi(argv[5]);
    uint8_t *rec = malloc(n + 1u); for (uint32_t i = 0; i < n; i++) rec[i] = (uint8_t)((i * 131u + n) & 255u);
    tpg_t t; if (!tpg_init_ex(&t, rec, n, mode, w, h, cell)) { puts("REFUSED"); return 0; }
    printf("BLOCK %u %u %u\n", t.x0, t.y0, t.px);
    for (uint32_t y = t.y0; y < t.y0 + t.px; y++) { for (uint32_t x = t.x0; x < t.x0 + t.px; x++) printf("%04x", tpg_pixel(&t, x, y)); putchar('\n'); }
    return 0;
}
