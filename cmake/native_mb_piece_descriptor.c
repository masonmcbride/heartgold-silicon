/* Original multiboot descriptor, native ARM64 ABI. */
#include "global.h"
#include <stddef.h>

typedef struct {
    u32 p;
    u8 *buffer;
    u32 piece;
    int count;
    u32 dataSize;
} Global;

_Static_assert(sizeof(void *) == 8, "Requires ARM64 pointers");
_Static_assert(offsetof(Global, p) == 0, "p offset");
_Static_assert(offsetof(Global, buffer) == 8, "buffer offset");
_Static_assert(offsetof(Global, piece) == 16, "piece offset");
_Static_assert(offsetof(Global, count) == 20, "count offset");
_Static_assert(offsetof(Global, dataSize) == 24, "dataSize offset");
_Static_assert(sizeof(Global) == 32, "Native descriptor extent");
_Static_assert(_Alignof(Global) == 8, "Native descriptor alignment");

Global ov13_0224CF84;
