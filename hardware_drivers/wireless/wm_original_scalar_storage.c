#include <nitro.h>
/* Original resident WM data; native representations. */
u8 gWmGameInfo[0x80];
u32 gWmNextTgid = 0x00010000u;
_Static_assert(sizeof(gWmGameInfo)==128,"original game-info extent");
_Static_assert(sizeof(gWmNextTgid)==4,"original TGID extent");
