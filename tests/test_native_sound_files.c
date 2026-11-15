/* Serialized SBNK/SWAR layouts remain DS words; runtime pointers do not. */
#include <nitro.h>
#include <simulator/sim.h>
#include <nitro/snd/common/bank.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
_Static_assert(offsetof(SNDBankData,instCount)==56,"SBNK disk count offset");
_Static_assert(offsetof(SNDBankData,instOffset)==60,"SBNK disk instrument table");
_Static_assert(offsetof(SNDWaveArc,waveCount)==56,"SWAR disk count offset");
_Static_assert(offsetof(SNDWaveArc,waveOffset)==60,"SWAR disk wave table");
_Alignas(32) static u8 bankBytes[160],arcBytes[128],otherBytes[128];
_Alignas(32) static u8 loadedBytes[32];
int main(int argc,char **argv)
{
    SIM_pxiInit();
    SND_Init();
    assert(argc==2);
    FILE *original=fopen(argv[1],"rb");assert(original);
    u32 fatOffset,fatSize;assert(!fseek(original,0x20,SEEK_SET));
    assert(fread(&fatOffset,4,1,original)==1 && fread(&fatSize,4,1,original)==1);
    u8 *fat=malloc(fatSize);assert(fat && !fseek(original,fatOffset,SEEK_SET));
    assert(fread(fat,1,fatSize,original)==fatSize);
    u32 count;memcpy(&count,fat+8,4);int checkedWave=0;
    for(u32 i=0;i<count && !checkedWave;++i) {
        u32 offset,size;memcpy(&offset,fat+12+i*16,4);memcpy(&size,fat+16+i*16,4);
        char signature[4];assert(!fseek(original,offset,SEEK_SET) && fread(signature,1,4,original)==4);
        if(memcmp(signature,"SWAR",4))continue;
        u8 *bytes=malloc(size);assert(bytes && !fseek(original,offset,SEEK_SET) && fread(bytes,1,size,original)==size);
        u32 waves,first;memcpy(&waves,bytes+56,4);memcpy(&first,bytes+60,4);
        assert(waves && SND_GetWaveDataCount((void *)bytes)==waves);
        assert(SND_GetWaveDataAddress((void *)bytes,0)==(void *)(bytes+first));
        free(bytes);checkedWave=1;
    }
    assert(checkedWave);free(fat);fclose(original);
    SNDBankData *bank=(void *)bankBytes;
    SNDWaveArc *arc=(void *)arcBytes,*other=(void *)otherBytes;
    assert((uintptr_t)bank>UINT32_MAX && (uintptr_t)loadedBytes>UINT32_MAX);
    bank->instCount=1;bank->instOffset[0]=(64<<8)|SND_INST_PCM;
    SNDInstParam param={.wave={0,0},.original_key=60,.attack=127,.decay=64,.sustain=100,.release=64,.pan=32};
    memcpy(bankBytes+64,&param,sizeof param);
    arc->waveCount=other->waveCount=1;arc->waveOffset[0]=other->waveOffset[0]=64;
    u8 before[160];memcpy(before,bankBytes,sizeof before);
    SND_AssignWaveArc(bank,0,arc);
    assert(!memcmp(bankBytes,before,sizeof before));
    SNDInstData inst;assert(SND_ReadInstData(bank,0,60,&inst));
    assert(inst.type==SND_INST_PCM && !memcmp(&inst.param,&param,sizeof param));
    assert(SND_GetWaveDataAddress(arc,0)==(void *)(arcBytes+64));
    SND_SetWaveDataAddress(arc,0,(void *)loadedBytes);
    assert(SND_GetWaveDataAddress(arc,0)==(void *)loadedBytes && arc->waveOffset[0]==64);
    SND_SetWaveDataAddress(arc,0,NULL);assert(SND_GetWaveDataAddress(arc,0)==NULL);
    SND_AssignWaveArc(bank,0,other);SND_DestroyWaveArc(other);
    SND_DestroyBank(bank);SND_DestroyWaveArc(arc);
    // Reusing the same allocation must not resurrect a disposed override.
    assert(SND_GetWaveDataAddress(arc,0)==(void *)(arcBytes+64));SND_DestroyWaveArc(arc);
    puts("PASS original SBNK instrument bytes, SWAR offsets, >4GiB runtime wave pointers, disposal and reuse");
}
