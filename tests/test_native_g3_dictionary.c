/* Nintendo's real intro dictionaries exercise both lookup paths above 4GiB. */
#include <nitro.h>
#include <nnsys/g3d/binres/res_struct.h>
#include <nnsys/g3d/binres/res_struct_accessor.h>
#include <nnsys/g3d_util_internal.h>
#include <nnsys/g3d_internal.h>
#include <nnsys/g3d/model.h>
#include <nnsys/g3d/binres/res_struct_accessor_inline.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned large;
static void materials(void *file,size_t size)
{
    NNSG3dResMdlSet *set=NNS_G3dGetMdlSet(file);assert(set && set->dict.numEntry);
    unsigned char *expected=malloc(size);assert(expected);
    for(unsigned m=0;m<set->dict.numEntry;++m) {
        NNSG3dResMdl *model=NNS_G3dGetMdlByIdx(set,m);assert(model && model->info.numMat);
        G3dResMat *mat=(void *)((u8 *)model+model->ofsMat);
        for(unsigned alpha=0;alpha<=31;alpha+=1) {
            memcpy(expected,file,size);
            for(unsigned i=0;i<model->info.numMat;++i) {
                const u32 *offset=NNS_G3dGetResDataByIdx(&mat->dict,i);assert(offset);
                G3dResMatData *data=(void *)((u8 *)mat+*offset);
                assert((uintptr_t)data>UINT32_MAX);
                size_t at=(u8 *)&data->prmPolygonAttr-(u8 *)file;
                assert(at+sizeof(u32)<=size);
                u32 value=data->prmPolygonAttr;
                value=(value & ~REG_G3_POLYGON_ATTR_ALPHA_MASK) | (alpha<<REG_G3_POLYGON_ATTR_ALPHA_SHIFT);
                memcpy(expected+at,&value,sizeof value);
            }
            NNS_G3dMdlSetMdlAlphaAll(model,alpha);
            assert(!memcmp(file,expected,size));
        }
    }
    free(expected);
}
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
        materials(data,(size_t)size);
        free(data);
    }
    assert(large>0);
    puts("PASS all real Scene 3 texture/palette names and misses through original Patricia traversal above 4GiB");
}
