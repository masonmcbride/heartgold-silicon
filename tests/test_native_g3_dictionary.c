/* Nintendo's real intro dictionaries exercise both lookup paths above 4GiB. */
#include <nitro.h>
#include <nnsys/g3d/binres/res_struct.h>
#include <nnsys/g3d/binres/res_struct_accessor.h>
#include <nnsys/g3d_util_internal.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned large;
static void dictionary(const NNSG3dResDict *dict)
{
    assert((uintptr_t)dict>UINT32_MAX);
    const NNSG3dResDictEntryHeader *entries=(void *)((const u8 *)dict+dict->ofsEntry);
    const NNSG3dResName *names=(void *)((const u8 *)entries+entries->ofsName);
    large+=dict->numEntry>=16;
    for(unsigned i=0;i<dict->numEntry;++i) {
        assert(NNS_G3dGetResDataByName(dict,names+i)==entries->data+entries->sizeUnit*i);
        assert(NNS_G3dGetResDictIdxByName(dict,names+i)==(int)i);
    }
    NNSG3dResName absent;memset(&absent,255,sizeof absent);
    assert(NNS_G3dGetResDataByName(dict,&absent)==NULL);
    assert(NNS_G3dGetResDictIdxByName(dict,&absent)==-1);
}
int main(int argc,char **argv)
{
    assert(argc==4);
    for(int i=1;i<argc;++i) {
        FILE *f=fopen(argv[i],"rb");assert(f);assert(!fseek(f,0,SEEK_END));long size=ftell(f);rewind(f);
        void *data=malloc(size);assert(data && fread(data,1,size,f)==(size_t)size);fclose(f);
        NNSG3dResTex *tex=NNS_G3dGetTex(data);assert(tex);
        dictionary(&tex->dict);
        dictionary((void *)((u8 *)tex+tex->plttInfo.ofsDict));
        free(data);
    }
    assert(large>0);
    puts("PASS all real Scene 3 texture/palette names and misses through original Patricia traversal above 4GiB");
}
