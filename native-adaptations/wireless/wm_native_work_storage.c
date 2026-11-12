#include <nitro.h>
#include <nitro/wm/wm_internal.h>
/* Original WM storage, adapted to native SDK layouts. */
__typeof__(gWmCommandQueue) gWmCommandQueue;
_Static_assert(sizeof(gWmCommandQueue) >= 32, "Storage too small: gWmCommandQueue");
__typeof__(gWmCommandMessages[0]) gWmCommandMessages[10];
_Static_assert(sizeof(gWmCommandMessages) >= 40, "Storage too small: gWmCommandMessages");
__typeof__(gWmPortEvent) gWmPortEvent;
_Static_assert(sizeof(gWmPortEvent) >= 20, "Storage too small: gWmPortEvent");
__typeof__(gWmPortEventMacAddress[0]) gWmPortEventMacAddress[16];
_Static_assert(sizeof(gWmPortEventMacAddress) >= 16, "Storage too small: gWmPortEventMacAddress");
__typeof__(gWmPortEventData[0]) gWmPortEventData[22];
_Static_assert(sizeof(gWmPortEventData) >= 44, "Storage too small: gWmPortEventData");
__typeof__(gWmCommandBuffers[0]) gWmCommandBuffers[10];
_Static_assert(sizeof(gWmCommandBuffers) >= 2560, "Storage too small: gWmCommandBuffers");
