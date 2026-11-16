/* SPDX-License-Identifier: MIT
 * Native storage for the original intro's 20 emitters / 200 particles.
 * a/0/5/9 member 4 has nine resources and nine textures. Each resource can
 * allocate at most six field records, one per original field flag.
 */
#ifndef HG_PARTICLE_CAPACITY_H
#define HG_PARTICLE_CAPACITY_H
#include "library/spl.h"
enum {
    HG_INTRO_PARTICLE_NATIVE_BYTES = sizeof(SPLManager) + 20 * sizeof(SPLEmitter)
        + 200 * sizeof(SPLParticle) + 9 * sizeof(SPLResource)
        + 9 * sizeof(SPLTexture) + 9 * 6 * sizeof(SPLField) + sizeof(void *),
    /* Retain the DS reservation when it exceeds the typed native requirement.
     * The final pointer-sized margin preserves the allocator's strict < end. */
    HG_INTRO_PARTICLE_WORK_BYTES = HG_INTRO_PARTICLE_NATIVE_BYTES > 0x4800
        ? HG_INTRO_PARTICLE_NATIVE_BYTES : 0x4800
};
#endif
