// Emit original JSONPROC data; all serialized offsets below must match DS layout.
#include <stddef.h>
#include "wild_encounter.h"

#define ABI_SIZE(type, n) _Static_assert(sizeof(type) == (n), #type " size changed")
#define ABI_AT(field, n) _Static_assert(offsetof(EncounterData, field) == (n), #field " offset changed")

ABI_SIZE(EncounterData, 0xC4);
ABI_SIZE(LandEncounterData, 0x54);
ABI_SIZE(EncounterDataSlot, 4);
ABI_AT(encounterRate_walking, 0x00);
ABI_AT(encounterRate_surfing, 0x01);
ABI_AT(encounterRate_rockSmash, 0x02);
ABI_AT(encounterRate_oldRod, 0x03);
ABI_AT(encounterRate_goodRod, 0x04);
ABI_AT(encounterRate_superRod, 0x05);
ABI_AT(dummy, 0x06);
ABI_AT(landSlots, 0x08);
ABI_AT(hoennSoundsSpecies, 0x5C);
ABI_AT(sinnohSoundsSpecies, 0x60);
ABI_AT(surfSlots, 0x64);
ABI_AT(rockSmashSlots, 0x78);
ABI_AT(oldRodSlots, 0x80);
ABI_AT(goodRodSlots, 0x94);
ABI_AT(superRodSlots, 0xA8);
ABI_AT(landSwarm, 0xBC);
ABI_AT(surfSwarm, 0xBE);
ABI_AT(nightFish, 0xC0);
ABI_AT(fishSwarm, 0xC2);

_Static_assert(offsetof(LandEncounterData, levels) == 0, "land levels offset");
_Static_assert(offsetof(LandEncounterData, species_morn) == 12, "land morning offset");
_Static_assert(offsetof(LandEncounterData, species_day) == 36, "land day offset");
_Static_assert(offsetof(LandEncounterData, species_nite) == 60, "land night offset");
_Static_assert(offsetof(EncounterDataSlot, level_min) == 0, "slot min offset");
_Static_assert(offsetof(EncounterDataSlot, level_max) == 1, "slot max offset");
_Static_assert(offsetof(EncounterDataSlot, species) == 2, "slot species offset");

#include <stdio.h>
#include <limits.h>
#include "gs_enc_data.c"

_Static_assert(__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__, "DS byte order");
_Static_assert(sizeof(u32) == 4, "DS word size");

int main(int argc, char **argv) {
    if (argc != 3) return 1;
    for (size_t i = 0; i < sizeof(__data) / sizeof(__data[0]); ++i) {
        char path[PATH_MAX];
        int n = snprintf(path, sizeof(path), "%s/%s_%08zu", argv[1], argv[2], i);
        if (n < 0 || (size_t)n >= sizeof(path)) return 1;
        FILE *file = fopen(path, "wb");
        if (!file) { perror(path); return 1; }
        int failed = fwrite(&__data[i], sizeof(__data[i]), 1, file) != 1;
        if (fclose(file)) failed = 1;
        if (failed) { perror(path); return 1; }
    }
    return 0;
}
