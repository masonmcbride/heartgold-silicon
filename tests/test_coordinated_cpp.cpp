#include "lobby_sort.h"
#include <assert.h>
#include <stdint.h>
extern "C" void TestNativeCursor(void) {
    LobbySort::Pair elements[3];
    LobbySort::Cursor first(elements), last(elements + 3);
    assert((uintptr_t)elements > UINT32_MAX);
    assert(last - first == 3 && first - last == -3 && first - first == 0);
}
