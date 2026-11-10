/*
 * Native representation of original OVY_0 dwc_lib_bss.s:gDwcMatchKeys.
 * Original: 154 records x 12 DS bytes.
 * ARM64:    154 records x 24 native bytes.
 *
 * Source adaptation in native_sources.py converts raw DS-stride
 * operations into typed MatchKeyEntry accesses.
 *
 * Original upstream storage and gameplay code remain unchanged.
 */
#include "global.h"
#include "dwc/match_internal.h"
#include <stddef.h>

_Static_assert(sizeof(MatchKeyEntry) == 24,
               "Native match-key record size");
_Static_assert(_Alignof(MatchKeyEntry) == 8,
               "Native match-key alignment");
_Static_assert(offsetof(MatchKeyEntry, id) == 0,
               "Native id offset");
_Static_assert(offsetof(MatchKeyEntry, isString) == 1,
               "Native isString offset");
_Static_assert(offsetof(MatchKeyEntry, buffer) == 8,
               "Native buffer offset");
_Static_assert(offsetof(MatchKeyEntry, value) == 16,
               "Native value offset");

MatchKeyEntry gDwcMatchKeys[154];

_Static_assert(sizeof(gDwcMatchKeys) == 3696,
               "Complete native match-key allocation");


/* BEGIN SOURCE-VERIFIED OVY_0 NETWORK ARRAYS */

/* Original DS: 32 four-byte pointers; native: 32 eight-byte pointers. */
void *gDwcGt2Connections[32];

/* Original DS: 32 byte-sized AID entries; unchanged on ARM64. */
u8 gDwcValidAidList[32];

_Static_assert(sizeof(gDwcGt2Connections) == 256,
               "GT2 connection pointer array ABI");
_Static_assert(sizeof(gDwcValidAidList) == 32,
               "Valid AID array ABI");

/* END SOURCE-VERIFIED OVY_0 NETWORK ARRAYS */


/* BEGIN ORIGINAL OVY_0 MATCH GLOBAL */

/*
 * Original owner: OVY_0 / dwc_lib_bss.s.
 * Preserve the original MatchGlobal type.
 * The ARM64 compiler determines the native pointer layout.
 */
MatchGlobal gDwcMatch;

_Static_assert(sizeof(gDwcMatch) >= 32,
               "Native MatchGlobal must represent the original state");

/* END ORIGINAL OVY_0 MATCH GLOBAL */

/* BEGIN REVIEWED ORIGINAL DWC TYPED GLOBALS */
/* Original C declarations determine the complete native types. */
#include "dwc/dwc_main_internal.h"
#include "dwc/sb_internal.h"
__typeof__(gDwcGt2ConnectionInfo) gDwcGt2ConnectionInfo;
__typeof__(sbServerGlobals) sbServerGlobals;
/* END REVIEWED ORIGINAL DWC TYPED GLOBALS */


/* BEGIN VERIFIED OVY_0 GAMESPY INITIALIZED DATA */
char sStr_final[] = "final";
char sStr_queryid[] = "queryid";
unsigned char sbInvalidServerIp[8] = {
    0xff, 0xff, 0xff, 0xff, 0, 0, 0, 0
};
_Static_assert(sizeof(sStr_final) == 6, "final size");
_Static_assert(sizeof(sStr_queryid) == 8, "queryid size");
_Static_assert(sizeof(sbInvalidServerIp) == 8, "server IP size");
/* END VERIFIED OVY_0 GAMESPY INITIALIZED DATA */

Transport *gDwcTransport;

#include "dwc/sb_internal.h"
SBServer *sbNoServer;

#include "dwc/sb_internal.h"
SBListGlobals sbListGlobals;

#include "dwc/dwc_main_internal.h"
FriendGlobal gDwcFriends;

void *DWCi_Beacon_Work;

extern char sStr_QueryError[];
char *sbQueryErrorPrefix = sStr_QueryError;

/* Original OVY_0 typed allocations */
typedef struct NatGlobals {
    const char *server2Name; // 0x00, NULL: default host name
    const char *server1Name; // 0x04
    u32 server2Ip;           // 0x08
    u32 server1Ip;           // 0x0C
    void *negotiators;       // 0x10, DArray of NatNegotiator
} NatGlobals;
NatGlobals nnNegotiatorList[1];
_Static_assert(sizeof(NatGlobals)==32,"NAT record");
_Static_assert(offsetof(NatGlobals,negotiators)==24,"NAT pointer");
char sStr_QueryError[] = "Query Error: ";
