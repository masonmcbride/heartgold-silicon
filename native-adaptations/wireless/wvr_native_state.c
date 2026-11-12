#include <nitro.h>
#include <stddef.h>
typedef WVRCallbackFunc WvrAsyncCallback;
typedef struct WvrState {
    volatile u16 lockId;
    volatile u16 vramBank;
    void *arg;
    WvrAsyncCallback callback;
} WvrState;
WvrState wvrLockId;
_Static_assert(offsetof(WvrState,lockId)==0,"lock");
_Static_assert(offsetof(WvrState,vramBank)==2,"bank");
_Static_assert(offsetof(WvrState,arg)==8,"arg");
_Static_assert(offsetof(WvrState,callback)==16,"callback");
_Static_assert(sizeof(WvrState)==24,"state");
