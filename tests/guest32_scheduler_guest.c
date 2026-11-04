/* Original scheduler/message/mutex execution under compiled continuations. MIT */
#include <nitro.h>
#include <stddef.h>
#include "nitrowifi/socl_internal.h"
#define CHECK(x) do{if(!(x))failure=__LINE__;}while(0)
typedef char ThreadSize[sizeof(OSThread)==192?1:-1];
typedef char ContextOffset[offsetof(OSThread,context)==0?1:-1];
typedef char StateOffset[offsetof(OSThread,state)==100?1:-1];
typedef char ContextSize[sizeof(OSContext)==100?1:-1];
typedef char StackTop[offsetof(OSThread,stackTop)==144?1:-1];
typedef char StackBottom[offsetof(OSThread,stackBottom)==148?1:-1];
extern OSThread **OSi_CurrentThreadPtr;
static OSThread launcher,first,second,third,fourth,waker;
static u32 stacks[6][4096/4];
static OSMessageQueue queue;
static OSMessage messages[2];
static OSThreadQueue gate;
static OSMutex mutex;
static volatile int failure,received,sent,mutexDone;
static SoclCommandPipe commandPipe;
static SoclCommandPacket command;
static SoclSocket socket;
static OSMessage commandMessages[2],freeMessages[1];
static volatile int commandEntered;
static int SoftwareCommand(SoclCommandPacket *packet){
    CHECK(packet==&command);CHECK(commandPipe.queue.usedCount==1);
    commandEntered=1;OS_SleepThread(&gate);
    CHECK(packet->reply!=0);CHECK(commandPipe.queue.usedCount==1);
    return 0x45670001;
}
static void CommandWaker(void *arg){CHECK(commandEntered);OS_WakeupThread(&gate);}
static void Nested(int depth) {
    volatile u32 local[9];for(int i=0;i<9;i++)local[i]=0x71230000u+depth*16+i;
    if(depth)Nested(depth-1);
    else {CHECK(OS_SendMessage(&queue,(OSMessage)3,OS_MESSAGE_BLOCK));sent=3;}
    for(int i=0;i<9;i++)CHECK(local[i]==0x71230000u+depth*16+i);
}
static void Producer(void *arg) {
    CHECK(arg==(void*)0x1234);CHECK(OS_SendMessage(&queue,(OSMessage)1,OS_MESSAGE_BLOCK));
    CHECK(OS_SendMessage(&queue,(OSMessage)2,OS_MESSAGE_BLOCK));sent=2;Nested(5);
}
static void Consumer(void *arg) {
    for(int i=1;i<=3;i++){OSMessage message=0;CHECK(OS_ReceiveMessage(&queue,&message,OS_MESSAGE_BLOCK));CHECK((u32)message==(u32)i);received++;}
}
static void LockOwner(void *arg) {
    OS_LockMutex(&mutex);OS_LockMutex(&mutex);CHECK(mutex.count==2);
    OS_SleepThread(&gate);CHECK(mutex.thread==OS_GetCurrentThread());
    OS_UnlockMutex(&mutex);CHECK(mutex.count==1);OS_UnlockMutex(&mutex);
}
static void LockWaiter(void *arg) {
    OS_LockMutex(&mutex);CHECK(mutex.thread==OS_GetCurrentThread());mutexDone=1;OS_UnlockMutex(&mutex);
}
int ProbeScheduler(void) {
    /* Explicit regression preconditions. OS_InitThread startup/DTCM and IRQ
     * device initialization are separate; this does not run or skip game boot. */
    OSi_CurrentThreadPtr=&OSi_ThreadInfo.current;OSi_ThreadInfo.current=&launcher;OSi_ThreadInfo.list=&launcher;
    launcher.priority=16;launcher.state=OS_THREAD_STATE_READY;
    OS_InitMessageQueue(&queue,messages,2);OS_InitMutex(&mutex);OS_InitThreadQueue(&gate);
    OS_CreateThread(&first,Producer,(void*)0x1234,stacks[0]+1024,4096,8);
    OS_CreateThread(&second,Consumer,0,stacks[1]+1024,4096,8);
    OS_WakeupThreadDirect(&first);CHECK(sent==2);CHECK(first.state==OS_THREAD_STATE_WAITING);
    OS_WakeupThreadDirect(&second);CHECK(sent==3 && received==3);
    CHECK(OS_IsThreadTerminated(&first));CHECK(OS_IsThreadTerminated(&second));
    OS_JoinThread(&first);OS_JoinThread(&second);
    OS_CreateThread(&third,LockOwner,0,stacks[2]+1024,4096,8);
    OS_CreateThread(&fourth,LockWaiter,0,stacks[3]+1024,4096,8);
    OS_WakeupThreadDirect(&third);CHECK(third.state==OS_THREAD_STATE_WAITING);
    OS_WakeupThreadDirect(&fourth);CHECK(fourth.state==OS_THREAD_STATE_WAITING);CHECK(!mutexDone);
    OS_WakeupThread(&gate);CHECK(mutexDone);CHECK(OS_IsThreadTerminated(&third));CHECK(OS_IsThreadTerminated(&fourth));
    CHECK(OS_GetCurrentThread()==&launcher);CHECK(!mutex.thread && !mutex.count);
    OS_InitMessageQueue(&commandPipe.queue,commandMessages,2);
    OS_InitMessageQueue(&gSoclCommandPacketQueue,freeMessages,1);
    OS_CreateThread(&commandPipe.thread,SOCLi_CommandPacketHandler,&commandPipe.queue,stacks[4]+1024,4096,8);
    OS_CreateThread(&waker,CommandWaker,0,stacks[5]+1024,4096,20);
    OS_WakeupThreadDirect(&commandPipe.thread);OS_WakeupThreadDirect(&waker);
    command.handler=SoftwareCommand;command.socket=&socket;command.flags=1;
    CHECK(SOCLi_ExecCommandPacket(&commandPipe,&command)==0x45670001);
    CHECK(socket.result==0x45670001);CHECK(gSoclCommandPacketQueue.usedCount==1);
    CHECK(commandPipe.queue.usedCount==0);OS_JoinThread(&waker);
    CHECK(SOCLi_SendCommandPacket(&commandPipe,0)==0);OS_JoinThread(&commandPipe.thread);
    CHECK(OS_IsThreadTerminated(&commandPipe.thread));
    return failure;
}
