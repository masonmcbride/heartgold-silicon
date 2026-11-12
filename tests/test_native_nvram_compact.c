#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "test_nvram_nitro.h"
#include "nvram.h"
static PXIFifoCallback callback;
static uint32_t response;
static int completions;
void PXI_SetFifoRecvCallback7(int tag,PXIFifoCallback fn){assert(tag==PXI_FIFO_TAG_NVRAM);callback=fn;}
int PXI_IsCallbackReady(int tag,int proc){return tag==PXI_FIFO_TAG_NVRAM && proc==PXI_PROC_ARM7 && callback!=NULL;}
int PXI_SendWordByFifo7(int tag,uPtr word,BOOL err){assert(tag==PXI_FIFO_TAG_NVRAM && !err);response=word;completions++;return PXI_FIFO_SUCCESS;}
static void send(uint16_t *words,int n,int cmd,int status){
    completions=0;
    for(int i=0;i<n;i++)callback(PXI_FIFO_TAG_NVRAM,
       ((uint32_t)i<<16)|words[i] | (i==0 ? 0x02000000u:0)|(i==n-1?0x01000000u:0),FALSE);
    assert(completions==1 && response==(0x03000000u|((cmd|0x80u)<<8)|status));
}
int main(void){
    char path[]="/tmp/hg-compact-fw-XXXXXX";
    int fd=mkstemp(path);assert(fd>=0);close(fd);unlink(path);
    assert(HG_NVRAM_Initialize(path));
    char *buf=malloc(1024);assert(buf && (uintptr_t)buf>UINT32_MAX);
    uint32_t id=HG_NVRAM_BindBuffer(buf,1024);assert(id>=0xe0000000u);
    uint16_t rd[6]={0x2300,0x20,0,32,(uint16_t)(id>>16),(uint16_t)id};
    send(rd,6,0x23,0);assert((uint8_t)buf[0]==0xc0 && (uint8_t)buf[1]==0x7f);
    rd[0]=0x2303;rd[1]=0xfa00;rd[3]=256;
    send(rd,6,0x23,0); for(int i=0;i<256;i++)assert((uint8_t)buf[i]==0xff);
    uint16_t wren[]={0x2000};send(wren,1,0x20,0);
    uint16_t status[3]={0x22e0,0,(uint16_t)((id&255)<<8)};status[0]|=(uint16_t)(id>>24);
    status[1]=(uint16_t)(id>>8);send(status,3,0x22,0);assert((uint8_t)buf[0]==2);
    memset(buf,0x5a,256);
    uint16_t wr[5]={0x2503,0xfa00,256,(uint16_t)(id>>16),(uint16_t)id};
    send(wr,5,0x25,0);send(status,3,0x22,0);assert((uint8_t)buf[0]==0);
    memset(buf,0,256);send(rd,6,0x23,0);for(int i=0;i<256;i++)assert((uint8_t)buf[i]==0x5a);
    HG_NVRAM_UnbindBuffer(id,buf,1024);
    send(rd,6,0x23,2);
    HG_NVRAM_Shutdown();
    assert(HG_NVRAM_Initialize(path));
    id=HG_NVRAM_BindBuffer(buf,1024);
    rd[4]=(uint16_t)(id>>16);rd[5]=(uint16_t)id;
    send(rd,6,0x23,0);for(int i=0;i<256;i++)assert((uint8_t)buf[i]==0x5a);
    HG_NVRAM_UnbindBuffer(id,buf,1024);
    HG_NVRAM_Shutdown();unlink(path);free(buf);
    puts("PASS native NVRAM: generated layout, protocol, callback, write persistence, ABI");
}
