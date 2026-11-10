/* Native storage for original OVY_0 net_common.c state.
 * Original definitions: lib/NitroDWC/asm/dwc_lib_rodata.s, .bss.
 * This is process-local state, never a serialized DS record. The complete
 * original data member must not be linked alongside this partial provider.
 */
#include <stddef.h>
#include <nitro/rtc.h>
#include <dwc/net_common_internal.h>

_Static_assert(sizeof(void *) == 8, "ARM64 runtime pointers");
_Static_assert(sizeof(NetErrorState) == 8, "original error words");
_Static_assert(_Alignof(NetErrorState) == 4, "original error alignment");
_Static_assert(offsetof(NetErrorState, type) == 0, "original error type");
_Static_assert(offsetof(NetErrorState, code) == 4, "original error code");
_Static_assert(sizeof(NetAllocHeader) == 32, "original allocation prefix");
_Static_assert(offsetof(NetAllocHeader, size) == 4, "original size word");
_Static_assert(offsetof(NetAllocHeader, unk_08) == 8, "original prefix padding");
_Static_assert(sizeof(NetAllocator) == 16, "two native callbacks");
_Static_assert(_Alignof(NetAllocator) == 8, "native callback alignment");
_Static_assert(offsetof(NetAllocator, free) == 0, "free callback first");
_Static_assert(offsetof(NetAllocator, alloc) == 8, "full-width alloc callback");
_Static_assert(sizeof(NetConnectionState) == 16, "error and native pointer");
_Static_assert(offsetof(NetConnectionState, error) == 0, "original error word");
_Static_assert(offsetof(NetConnectionState, connection) == 8, "aligned connection pointer");
_Static_assert(sizeof(NetConnection) == 100, "unchanged connection record");
_Static_assert(offsetof(NetConnection, phase) == 16, "original connection phase");
_Static_assert(offsetof(NetConnection, apSpotInfo) == 88, "original AP information");
_Static_assert(sizeof(NetStartParams) == 24, "two callbacks and priority bytes");
_Static_assert(offsetof(NetStartParams, priority) == 16, "native priority offset");
_Static_assert(offsetof(NetStartParams, one) == 17, "native flag offset");

NetErrorState gDwcNetError;
NetAllocator gDwcNetAllocator;
NetConnectionState gDwcNetConnection;
NetAuthWork *gDwcNasLoginWork;
