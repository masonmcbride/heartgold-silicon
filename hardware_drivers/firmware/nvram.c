/* Host SPI firmware service for original NitroDWC; no Nintendo firmware bytes. */
#define _POSIX_C_SOURCE 200809L
#ifdef HG_NVRAM_UNIT_TEST
#include "test_nvram_nitro.h"
#else
#include <nitro.h>
#endif
#include "nvram.h"
#include <stdint.h>
#include <pthread.h>
#ifndef _DARWIN_C_SOURCE
#define _DARWIN_C_SOURCE 1
#endif
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FLASH_SIZE 0x40000u
#define BIND_CAP 32
static int flash_fd = -1;
static uint32_t flash_size;
static int wel;
static uint16_t words[16];
static unsigned expected, bad, active;
static struct {uint32_t id, bytes; void *ptr;} binds[BIND_CAP];
static uint32_t serial;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

static int io(uint32_t pos, void *ptr, uint32_t bytes, int writing) {
    uint32_t done = 0;
    while (done < bytes) {
        ssize_t n = writing ? pwrite(flash_fd, (char *)ptr+done, bytes-done, pos+done)
                            : pread(flash_fd, (char *)ptr+done, bytes-done, pos+done);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return 0;
        done += (uint32_t)n;
    }
    return 1;
}
static int span(uint32_t pos, uint32_t bytes) {
    return bytes && pos <= flash_size && bytes <= flash_size-pos;
}
uint32_t HG_NVRAM_BindBuffer(void *p, uint32_t bytes) {
    if (flash_fd < 0 || !p || !bytes) return 0;
    uint32_t id = 0;
    pthread_mutex_lock(&lock);
    for (unsigned i=0;i<BIND_CAP;i++) if (!binds[i].ptr && serial < 0x0fffffffu) {
        id = 0xe0000000u | ++serial;
        binds[i].id=id; binds[i].ptr=p; binds[i].bytes=bytes; break;
    }
    pthread_mutex_unlock(&lock);
    return id;
}
void HG_NVRAM_UnbindBuffer(uint32_t id, void *p, uint32_t bytes) {
    if (!id) return;
    int found=0;
    pthread_mutex_lock(&lock);
    for (unsigned i=0;i<BIND_CAP;i++) if (binds[i].id==id && binds[i].ptr==p && binds[i].bytes==bytes) {
        memset(&binds[i],0,sizeof binds[i]); found=1; break;
    }
    pthread_mutex_unlock(&lock);
    if (!found) abort();
}
static void *resolve(uint32_t id, uint32_t bytes) {
    void *p=NULL;
    pthread_mutex_lock(&lock);
    for (unsigned i=0;i<BIND_CAP;i++) if (binds[i].id==id && binds[i].ptr && bytes<=binds[i].bytes) {
        p=binds[i].ptr; break;
    }
    pthread_mutex_unlock(&lock);
    return p;
}
static uint8_t execute(uint8_t command, unsigned count) {
    uint32_t addr=((uint32_t)(words[0]&255)<<16)|words[1], size=0, id=0;
    void *ptr;
    switch (command) {
    case 0x20: if(count!=1)return 2; wel=1; return 0; // WREN
    case 0x21: case 0x2d: if(count!=1)return 2; wel=0; return 0; // WRDI/reset
    case 0x22: // RDSR, split pointer in three original SPI words
        if(count!=3)return 2;
        id=((uint32_t)(words[0]&255)<<24)|((uint32_t)words[1]<<8)|(words[2]>>8);
        ptr=resolve(id,1); if(!ptr)return 2;
        *(uint8_t *)ptr=wel?2:0; return 0;
    case 0x23: case 0x24: // READ
        if(count!=6)return 2;
        size=((uint32_t)words[2]<<16)|words[3];
        id=((uint32_t)words[4]<<16)|words[5];
        if(!span(addr,size) || !(ptr=resolve(id,size)))return 2;
        return io(addr,ptr,size,0)?0:3;
    case 0x25: case 0x26: // original page-write protocol
        if(count!=5)return 2;
        size=words[2]; id=((uint32_t)words[3]<<16)|words[4];
        if(!span(addr,size) || !(ptr=resolve(id,size)))return 2;
        if(!wel)return 3;
        wel=0;
        if(size > 256-(addr&255))size=256-(addr&255);
        return io(addr,ptr,size,1) && fsync(flash_fd)==0 ? 0:3;
    default: return 1; // do not invent unsupported firmware operations
    }
}
static void on_nvram(PXIFifoTag tag, uPtr raw, BOOL err) {
    if (tag!=PXI_FIFO_TAG_NVRAM || raw>UINT32_MAX) abort();
    uint32_t word=(uint32_t)raw;
    if(word&0x02000000u) {expected=bad=0; active=1; memset(words,0,sizeof words);}
    if(!active)return;
    unsigned index=(word>>16)&15u;
    if(err || index!=expected || expected>=16)bad=1;
    else {words[index]=(uint16_t)word; expected++;}
    if(!(word&0x01000000u))return;
    uint8_t cmd=(uint8_t)(words[0]>>8);
    uint8_t status=bad?2:execute(cmd,expected);
    active=0;
    uint32_t answer=0x03000000u|((uint32_t)(cmd|0x80)<<8)|status;
    if(PXI_SendWordByFifo7(PXI_FIFO_TAG_NVRAM,answer,FALSE)!=PXI_FIFO_SUCCESS)abort();
}
int HG_NVRAM_Initialize(const char *path) {
    if(flash_fd>=0)return 0;
    if(!path || !*path)path="heartgold-native-firmware.bin";
    int created=0;
    int fd=open(path,O_RDWR|O_NOFOLLOW|O_CLOEXEC|O_CREAT|O_EXCL,0600);
    if(fd>=0)created=1;
    else if(errno==EEXIST)fd=open(path,O_RDWR|O_NOFOLLOW|O_CLOEXEC);
    if(fd<0)return 0;
    flash_fd=fd;
    if(created){
        uint8_t blank[4096]; memset(blank,0xff,sizeof blank);
        for(uint32_t i=0;i<FLASH_SIZE;i+=sizeof blank)
            if(!io(i,blank,sizeof blank,1))goto fail;
        uint8_t location[2]={0xc0,0x7f}; // 0x3fe00 / 8; DWC pages start 0x3fa00
        if(!io(0x20,location,2,1)||fsync(fd))goto fail;
    }
    struct stat st;
    if(fstat(fd,&st)!=0 || !S_ISREG(st.st_mode) ||
       (st.st_size!=0x40000 && st.st_size!=0x80000))goto fail;
    flash_size=(uint32_t)st.st_size;
    PXI_SetFifoRecvCallback7(PXI_FIFO_TAG_NVRAM,on_nvram);
    if(!PXI_IsCallbackReady(PXI_FIFO_TAG_NVRAM,PXI_PROC_ARM7)){
        PXI_SetFifoRecvCallback7(PXI_FIFO_TAG_NVRAM,NULL); goto fail;
    }
    return 1;
fail:
    close(fd); flash_fd=-1;
    if(created)unlink(path);
    return 0;
}
void HG_NVRAM_Shutdown(void) {
    if(flash_fd<0)return;
    PXI_SetFifoRecvCallback7(PXI_FIFO_TAG_NVRAM,NULL);
    close(flash_fd); flash_fd=-1;
}
