#include <nitro.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>

int main(void)
{
    const char *paths[] = {
        "rom:/demo/title/titledemo.narc", "rom:/demo/opening/gs_opening.narc",
        "rom:/data/sound/gs_sound_data.sdat"
    };
    for (unsigned cycle = 0; cycle < 3; ++cycle) {
        for (unsigned i = 0; i < 3; ++i) {
            FSFile file;
            char magic[4];
            FS_InitFile(&file);
            assert(FS_OpenFile(&file, paths[i]));
            assert(FS_ReadFile(&file, magic, sizeof(magic)) == sizeof(magic));
            assert(!memcmp(magic, i == 2 ? "SDAT" : "NARC", 4));
            if (i == 2) assert(FS_GetLength(&file) == 8660096);
            assert(FS_CloseFile(&file));
        }
        FSFile missing;
        FS_InitFile(&missing);
        assert(!FS_OpenFile(&missing, "rom:/__nonexistent_resource__.narc"));
        assert(missing.pcFilePtr == NULL);
    }
    puts("original FS_OpenFile/ReadFile/CloseFile: title, opening, SDAT and missing resources passed");
}
