/* Unexercised external boundaries trap; they never report SDK success. */
#include <stdlib.h>
#include <stdio.h>
#define TRAP(name) void name(void) { fputs("unexpected test boundary: " #name "\n", stderr); abort(); }
TRAP(MBi_CommParentSendData)
TRAP(MBi_GetAttribute)
TRAP(MBi_GetGgid)
TRAP(MBi_GetTgid)
TRAP(MBi_InitSendVolatBeacon)
TRAP(MBi_SendFixedBeacon)
TRAP(MBi_SendVolatBeacon)
TRAP(OS_SpinWait)
TRAP(WM_End)
TRAP(WM_ReadMPData)
TRAP(WM_SetBeaconIndication)
TRAP(WM_SetGameInfo)
TRAP(WM_SetLifeTime)
TRAP(WM_SetParentParameter)
TRAP(WM_SetPortCallback)
TRAP(WM_StartMPEx)
TRAP(WMi_StartParentEx)
unsigned char bsendBuff[0x5a60];
unsigned char s_HW_MAIN_MEM_SYSTEM[0x4000];
TRAP(FS_OpenFile)
TRAP(OS_CreateThreadDebug)
TRAP(OS_ExitThread)
TRAP(OS_GetThreadPriority)
TRAP(OS_SetThreadPriority)
TRAP(OS_SleepThread)
TRAP(OS_WakeupThreadDirect)
void *gMbTaskWork;
