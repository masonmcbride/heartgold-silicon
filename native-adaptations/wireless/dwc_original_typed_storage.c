#include <stddef.h>

#include <stdint.h>

/* Pointer-only dependencies of the source-extracted structs. */

typedef struct HA HA;

typedef struct Ctx Ctx;

typedef struct ApConnectWork ApConnectWork;

typedef struct HttpReq HttpReq;

typedef struct HState {
    HA *a;
    void *b;
    int state;
} HState;

HState DWCi_Beacon_ApSearch;

_Static_assert(sizeof(HState) == 24, "HState: native size");

_Static_assert(offsetof(HState, a) == 0, "HState.a: native offset");

_Static_assert(offsetof(HState, b) == 8, "HState.b: native offset");

_Static_assert(offsetof(HState, state) == 16, "HState.state: native offset");

typedef struct Globals {
    void *p0;
    void *p4;
    void *p8;
    Ctx *ctx;
    ApConnectWork *work;
} Globals;

Globals DWCi_AC_Globals;

_Static_assert(sizeof(Globals) == 40, "Globals: native size");

_Static_assert(offsetof(Globals, p0) == 0, "Globals.p0: native offset");

_Static_assert(offsetof(Globals, p4) == 8, "Globals.p4: native offset");

_Static_assert(offsetof(Globals, p8) == 16, "Globals.p8: native offset");

_Static_assert(offsetof(Globals, ctx) == 24, "Globals.ctx: native offset");

_Static_assert(offsetof(Globals, work) == 32, "Globals.work: native offset");

typedef struct HttpList {
    HttpReq *head;
    int count;
} HttpList;

HttpList DWCi_GHTTPRequestList;

_Static_assert(sizeof(HttpList) == 16, "HttpList: native size");

_Static_assert(offsetof(HttpList, head) == 0, "HttpList.head: native offset");

_Static_assert(offsetof(HttpList, count) == 8, "HttpList.count: native offset");
