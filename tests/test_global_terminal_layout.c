/* Compile the actual adapted original consumer, so private types cannot drift
 * from the assembly storage recipe. Unused networking code is dead-stripped. */
#include HG_GLOBAL_TERMINAL_SOCKET_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdatomic.h>
#include <pthread.h>
#include <bg_window.h>
_Static_assert(sizeof(BgTemplate)==28,"original background record byte stride");
_Static_assert(sizeof(GlobalTerminalSocketHostEntry)==32 && offsetof(GlobalTerminalSocketHostEntry,addrList)==24,"canonical native host entry");
_Static_assert(sizeof(GlobalTerminalSocketAddress)==8 && offsetof(GlobalTerminalSocketAddress,ip)==4,"fixed IPv4 address ABI");
_Static_assert(sizeof(GlobalTerminalSocketInAddr)==4,"IPv4 scalar ABI");

#define CHECK(expr) do { if (!(expr)) { fprintf(stderr,"FAIL: %s\n",#expr); abort(); } } while (0)

extern const int _0222A9AC[];
extern unsigned char ov39_0222AB8A[];
static atomic_int release_thread;
static void thread_probe(void *arg)
{
    CHECK(arg==&release_thread);
    while(!atomic_load(&release_thread))HG_Delay(1);
    /* Test the real pthread-backed SDK creation/stack writes, without entering
     * the separately unsupported SDK context/scheduler exit machinery. */
    pthread_exit(NULL);
}
int main(void)
{
    unsigned char *base=(unsigned char *)&sGlobalTerminalSocket;
    unsigned char *thread=(unsigned char *)&sGlobalTerminalSocketThread;
    unsigned char *mutex=(unsigned char *)&sGlobalTerminalSocketMutex;
    unsigned char *end=sGlobalTerminalSocketThreadStackEnd;
    CHECK((uintptr_t)base>UINT32_MAX);
    CHECK((const void *)_0222A9AC==(const void *)&sGlobalTerminalServerCommandIds);
    const int commands[]={0,20000,20001,21000,21001,22000,22001,23000,23001,23002,23003,-1};
    CHECK(!memcmp(commands,&sGlobalTerminalServerCommandIds,sizeof(commands)));
    CHECK(ov39_0222AB8A==base+6);
    CHECK((unsigned char *)sGlobalTerminalSocketHost==base+offsetof(GlobalTerminalSocket,host));
    CHECK((unsigned char *)&sGlobalTerminalSocketSettings==base+offsetof(GlobalTerminalSocket,unk_200));
    CHECK(thread==base+sizeof(GlobalTerminalSocket));
    CHECK(mutex==thread+sizeof(OSThread));
    CHECK(end-0x800==mutex+sizeof(OSMutex));
    CHECK((uintptr_t)(end-0x800)%16==0 && (uintptr_t)end%16==0);
    memcpy(sGlobalTerminalSocketHost,"native-host",12);
    CHECK(!strcmp(sGlobalTerminalSocket.host,"native-host"));
    sGlobalTerminalSocketSettings.port=443;CHECK(sGlobalTerminalSocket.port==443);
    memset(thread,0xa5,sizeof(OSThread));
    memset(mutex,0x5a,sizeof(OSMutex));
    memset(end-0x800,0x6b,0x800);memset(end,0x3c,0x10);
    /* The original SDK clears exactly this interior of its downward stack.
     * Use the real primitive; check both endpoints and both adjacent objects. */
    MI_CpuClear32(end-0x800+sizeof(u32),0x800-2*sizeof(u32));
    CHECK(!memcmp(end-0x800,"kkkk",4));
    CHECK(!memcmp(end-4,"kkkk",4));
    for(unsigned i=4;i<0x800-4;++i)CHECK((end-0x800)[i]==0);
    for(unsigned i=0;i<sizeof(OSThread);++i)CHECK(thread[i]==0xa5);
    for(unsigned i=0;i<sizeof(OSMutex);++i)CHECK(mutex[i]==0x5a);
    for(unsigned i=0;i<0x10;++i)CHECK(end[i]==0x3c);
    OS_InitMutex(&sGlobalTerminalSocketMutex);
    CHECK(sGlobalTerminalSocketMutex.sdlMutex!=NULL);
    CHECK((uintptr_t)sGlobalTerminalSocketMutex.sdlMutex>UINT32_MAX);
    for(unsigned i=0;i<0x10;++i)CHECK(end[i]==0x3c);
    for(unsigned i=0;i<4;++i)CHECK((end-0x800)[i]==0x6b);
    HG_DestroyMutex(sGlobalTerminalSocketMutex.sdlMutex);
    memset(thread,0,sizeof(OSThread));
    OS_Init();
    OS_CreateThread(&sGlobalTerminalSocketThread,thread_probe,&release_thread,end,0x800,16);
    CHECK(sGlobalTerminalSocketThread.stackBottom==(uintptr_t)end);
    CHECK(sGlobalTerminalSocketThread.stackTop==(uintptr_t)(end-0x800));
    CHECK(sGlobalTerminalSocketThread.stackBottom>UINT32_MAX);
    for(unsigned i=0;i<0x10;++i)CHECK(end[i]==0x3c);
    CHECK((end-0x800)[0]==0x6b&&end[-1]==0x6b);
    atomic_store(&release_thread,1);
    HG_WaitThread(sGlobalTerminalSocketThread.win_sdlThread,NULL);
    puts("OVY_39 original aliases, native private ABI, 0x800 stack and adjacent storage verified");
}
