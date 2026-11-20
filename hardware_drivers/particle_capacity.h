/* SPDX-License-Identifier: MIT
 * Native storage for the original intro's 20 emitters / 200 particles.
 * a/0/5/9 member 4 has nine resources and nine textures. Each resource can
 * allocate at most six field records, one per original field flag.
 */
#ifndef HG_PARTICLE_CAPACITY_H
#define HG_PARTICLE_CAPACITY_H
#include "library/spl.h"
/* SPL_Init always allocates these three pools. The remaining DS arena stores
 * only SPLResource (32 bytes), SPLTexture (20), and SPLField (8). Translate
 * that remaining budget at their largest native/DS expansion, two, rather
 * than guessing resource counts or changing the parent battle heap's size.
 * All native records and arrays have eight-byte strides; the slot allocator's
 * four-byte rounding therefore introduces no additional native padding.
 */
_Static_assert(sizeof(SPLResource) <= 2 * 32, "SPL resource budget");
_Static_assert(sizeof(SPLTexture) <= 2 * 20, "SPL texture budget");
_Static_assert(sizeof(SPLField) <= 2 * 8, "SPL field budget");
_Static_assert(sizeof(SPLManager) % 8 == 0 && sizeof(SPLEmitter) % 8 == 0 &&
    sizeof(SPLParticle) % 8 == 0 && sizeof(SPLResource) % 8 == 0 &&
    sizeof(SPLTexture) % 8 == 0 && sizeof(SPLField) % 8 == 0,
    "SPL native bump alignment");
enum {
    HG_PARTICLE_DS_INIT_BYTES = 76 + 20 * 156 + 200 * 68,
    HG_PARTICLE_NATIVE_INIT_BYTES = sizeof(SPLManager)
        + 20 * sizeof(SPLEmitter) + 200 * sizeof(SPLParticle),
    HG_BATTLE_PARTICLE_WORK_BYTES = HG_PARTICLE_NATIVE_INIT_BYTES
        + 2 * (0x4800 - HG_PARTICLE_DS_INIT_BYTES),
    HG_BATTLE_PARTICLE_SMALL_WORK_BYTES = HG_PARTICLE_NATIVE_INIT_BYTES
        + 2 * (0x4200 - HG_PARTICLE_DS_INIT_BYTES)
};
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
