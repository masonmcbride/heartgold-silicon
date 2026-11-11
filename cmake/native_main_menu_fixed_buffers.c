/* Original zero storage: asm/main_menu_data.s
 * Fixed-width native arrays, no DS address relocation.
 * Consumer layout audit is required before runtime certification.
 */
#include "global.h"

u32 gMainMenuUtilGiftSpriteWork[800] = {0};
u8 gMysteryGiftWfcFileList[1760] = {0};

_Static_assert(sizeof(gMainMenuUtilGiftSpriteWork) == 3200,
               "Gift sprite work storage");
_Static_assert(sizeof(gMysteryGiftWfcFileList) == 1760,
               "Mystery Gift file-list storage");
