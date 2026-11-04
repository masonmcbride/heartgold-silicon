/* Original wireless/OS layout hypotheses. SPDX-License-Identifier: MIT */
#include <nitro.h>
#include "nitrowifi/socl_internal.h"
#include <stddef.h>
#define REQUIRE(name, expr) typedef char name[(expr)?1:-1]
REQUIRE(ConfigSize,sizeof(CpsConfig)==48);
REQUIRE(StateSize,sizeof(SoclState)==64);
REQUIRE(StateIp,offsetof(SoclState,lastIp)==4);
REQUIRE(StateAddr,offsetof(SoclState,addressState)==8);
REQUIRE(StateSocket,offsetof(SoclState,ctrlSocket)==12);
REQUIRE(StateConfig,offsetof(SoclState,cpsConfig)==16);
REQUIRE(PollStride,sizeof(SocPollFd)==8);
REQUIRE(PollEvents,offsetof(SocPollFd,events)==4);
REQUIRE(PollResults,offsetof(SocPollFd,revents)==6);
REQUIRE(InfoSize,sizeof(OSThreadInfo)==16);
