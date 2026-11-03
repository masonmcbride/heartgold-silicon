#include "global.h"
#include "dwc/match_internal.h"
unsigned WorkSize(void){return sizeof(MatchWork);}
void SetupWork(MatchWork *work,void *browser){gDwcMatch.work=work;work->list=browser;}
