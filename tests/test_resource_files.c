/* Loose asset service coverage; genuine ROM FS is exercised by test_native_cartridge.c. */
#include <nitro.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
extern FILE *HG_OpenResource(const char *path);

int main(void)
{
    const char *paths[] = {
        "rom:/demo/title/titledemo.narc",
        "rom:/demo/opening/gs_opening.narc",
        "rom:/data/sound/gs_sound_data.sdat",
        "rom:/a/0/1/6",
        "rom:/a/0/2/7"
    };
    const unsigned path_count = sizeof(paths) / sizeof(paths[0]);
    for (unsigned cycle = 0; cycle < 3; ++cycle) {
        for (unsigned i = 0; i < path_count; ++i) {
            FILE *file;
            char magic[4];
            file = HG_OpenResource(paths[i]);
            assert(file);
            assert(fread(magic, 1, sizeof(magic), file) == sizeof(magic));
            assert(!memcmp(magic, i == 2 ? "SDAT" : "NARC", 4));
            assert(fseek(file, 0, SEEK_END) == 0);
            if (i == 2) assert(ftell(file) == 8660096);
            if (i == 3) assert(ftell(file) == 201528);
            if (i == 4) assert(ftell(file) == 4622756);
            assert(fclose(file) == 0);
        }
        assert(!HG_OpenResource("rom:/__nonexistent_resource__.narc"));
    }
    puts("loose asset service: title, opening, SDAT, numeric font/message archives and missing resources passed");
}
