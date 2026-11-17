/* SPDX-License-Identifier: MIT
 * Decode fixed-width NCLR/NCGR bytes into caller-owned native views. */
#ifndef HG_G2D_RESOURCE_DECODE_H
#define HG_G2D_RESOURCE_DECODE_H
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

typedef struct HG_NCLR_View {
    uint32_t format, extended, size;
    const unsigned char *colors;
} HG_NCLR_View;

static inline uint32_t hg_nclr_u32(const unsigned char *p) {
    return p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static inline uint16_t hg_nclr_u16(const unsigned char *p) {
    return p[0] | (uint16_t)p[1]<<8;
}
static inline const unsigned char *hg_g2d_block(const void *bytes, size_t length,
        const char magic[4], const char tag[4], size_t *payload_size) {
    *payload_size=0;
    if (!bytes || length < 16) return NULL;
    const unsigned char *file=bytes;
    if (memcmp(file,magic,4) || hg_nclr_u16(file+4)!=0xfeff) return NULL;
    size_t end=hg_nclr_u32(file+8), cursor=hg_nclr_u16(file+12);
    unsigned blocks=hg_nclr_u16(file+14);
    if (end>length || cursor<16 || cursor>end) return NULL;
    const unsigned char *found=NULL;
    for (unsigned i=0;i<blocks;++i) {
        if (end-cursor<8) return NULL;
        const unsigned char *block=file+cursor;
        size_t size=hg_nclr_u32(block+4);
        if (size<8 || size>end-cursor) return NULL;
        if (!memcmp(block,tag,4)) {
            if (found) return NULL;
            found=block+8;*payload_size=size-8;
        }
        cursor+=size;
    }
    if (!found || cursor!=end) return NULL;
    return found;
}
static inline bool hg_nclr_decode(const void *bytes, size_t length, HG_NCLR_View *out) {
    if (!out) return false;
    memset(out,0,sizeof(*out));
    size_t size;
    const unsigned char *payload=hg_g2d_block(bytes,length,"RLCN","TTLP",&size);
    if (!payload || size<16) return false;
    size_t offset=hg_nclr_u32(payload+12), raw=hg_nclr_u32(payload+8);
    if (offset<16 || offset>size || raw>size-offset || (offset&1) || (raw&1)) return false;
    out->format=hg_nclr_u32(payload);out->extended=hg_nclr_u32(payload+4);
    out->size=(uint32_t)raw;out->colors=payload+offset;return true;
}

typedef struct HG_NCGR_View {
    uint16_t height, width;
    uint32_t pixel_format, mapping, character_format, size;
    const unsigned char *pixels;
} HG_NCGR_View;

static inline bool hg_ncgr_decode(const void *bytes, size_t length, HG_NCGR_View *out) {
    if (!out) return false;
    memset(out,0,sizeof(*out));
    size_t size;
    const unsigned char *payload=hg_g2d_block(bytes,length,"RGCN","RAHC",&size);
    if (!payload || size<24) return false;
    size_t offset=hg_nclr_u32(payload+20), raw=hg_nclr_u32(payload+16);
    if (offset<24 || offset>size || raw>size-offset) return false;
    out->height=hg_nclr_u16(payload);out->width=hg_nclr_u16(payload+2);
    out->pixel_format=hg_nclr_u32(payload+4);out->mapping=hg_nclr_u32(payload+8);
    out->character_format=hg_nclr_u32(payload+12);
    out->size=(uint32_t)raw;out->pixels=payload+offset;return true;
}
#endif
