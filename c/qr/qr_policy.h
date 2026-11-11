/* Density levels for the QR tier (python/qr_tier.py LEVELS, measured in docs/qr_density.md). Pass the level's version as maxver to qr_encode()
 * so a report that is too big for a photo is refused (qr_encode returns 0) instead of silently drawn as a code a phone cannot read.
 * QR_V_MAX is for lossless screenshots only: show it behind a deliberate key press, with a caption saying so. */
#ifndef POCKET_QR_POLICY_H
#define POCKET_QR_POLICY_H
#define QR_V_PHOTO   10u   /* <=   271 bytes: phone scanners */
#define QR_V_CAREFUL 22u   /* <= 1,003 bytes: steady, close, sharp photo, Aruco-class decoder */
#define QR_V_MAX     38u   /* <= 2,699 bytes: 2 px modules, screenshot only */
#endif
