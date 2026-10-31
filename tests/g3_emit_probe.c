/* Emission endpoint for one isolated original producer. No device execution. */
#include <nnsys/g3d/1mat1shp.h>
#include <nnsys/g3d_render_internal.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

_Static_assert(sizeof(u32) == 4 && sizeof(fx32) == 4, "DS scalar ABI");
_Static_assert(sizeof(void *) == 8, "native pointer ABI");
_Static_assert(sizeof(NNSG3dResMdlInfo) == 44, "model info layout");
_Static_assert(offsetof(NNSG3dResMdl, nodeInfo) == 64, "model layout");
_Static_assert(offsetof(G3dResMatData, texMtxData) == 44, "material layout");
_Static_assert(sizeof(G3dResShpData) == 16, "shape layout");
_Static_assert(sizeof(G3dMatAnmResult) == 56, "native math input layout");

static void require(int ok, const char *why) {
    if (!ok) { fprintf(stderr, "g3 probe: %s\n", why); exit(1); }
}
static unsigned char *resource;
static size_t resource_size;
static unsigned char captured[65536];
typedef struct { unsigned kind, offset, length, resource_offset; } Event;
static Event events[32];
static unsigned event_count, captured_size;
static const void *expected_dl;
static unsigned expected_dl_size;
static void range(size_t offset, size_t size) {
    require(offset <= resource_size && size <= resource_size - offset, "resource bounds");
}
static unsigned rd16(size_t o) { range(o, 2); return resource[o] | resource[o+1] << 8; }
static unsigned rd32(size_t o) {
    range(o, 4); return rd16(o) | (unsigned)rd16(o+2) << 16;
}
/* Validate before calling the original unchecked inline resource accessors. */
static unsigned dict_offset(size_t d, unsigned index) {
    range(d, 8);
    unsigned count=resource[d+1], size=rd16(d+2), entry=rd16(d+6);
    range(d, size);
    require(index < count && entry >= 8 && entry + 4 <= size, "dictionary header");
    unsigned unit=rd16(d+entry), names=rd16(d+entry+2);
    require(unit == 4 && entry+4+count*4 <= size, "dictionary entries");
    require(names >= 4+count*4 && entry+names+16*count <= size, "dictionary names");
    return rd32(d+entry+4+index*4);
}
static void append(unsigned kind, const void *p, unsigned bytes, unsigned origin) {
    require(event_count < 32 && bytes <= sizeof(captured)-captured_size, "capture capacity");
    events[event_count++] = (Event){kind,captured_size,bytes,origin};
    if(bytes) memcpy(captured+captured_size,p,bytes);
    captured_size += bytes;
}
void NNS_G3dGeBufferOP_N(u32 op, const u32 *args, u32 num) {
    require(num <= 64 && (!num || args), "emitted parameter count");
    unsigned start=captured_size;
    append(0,&op,4,0);
    require(num*4 <= sizeof(captured)-captured_size, "parameter capacity");
    if(num) memcpy(captured+captured_size,args,num*4);
    captured_size += num*4;
    events[event_count-1].length=captured_size-start;
}
void NNS_G3dGeSendDL(const void *p, u32 bytes) {
    require(p == expected_dl && bytes == expected_dl_size, "original shape display-list identity");
    append(1,p,bytes,(unsigned)((const unsigned char *)p-resource));
}
int main(int argc, char **argv) {
    require(argc == 3, "usage: g3_emit_probe resource.nsbmd capture.bin");
    FILE *f=fopen(argv[1],"rb"); require(f != NULL,"open resource");
    require(fseek(f,0,SEEK_END)==0,"seek resource"); long length=ftell(f);
    require(length >= 24 && length <= 65536,"resource size"); resource_size=(size_t)length;
    resource=malloc(resource_size); require(resource != NULL,"resource allocation");
    rewind(f); require(fread(resource,1,resource_size,f)==resource_size,"read resource");
    require(fclose(f)==0,"close resource");
    require(!memcmp(resource,"BMD0",4) && rd16(4)==0xfeff && rd16(6)==2 &&
        rd32(8)==resource_size && rd16(12)==16 && rd16(14)==2,"BMD0 header");
    unsigned block=rd32(16), tex=rd32(20); range(block,8); range(tex,8);
    require(block==24 && !memcmp(resource+block,"MDL0",4) &&
        block+rd32(block+4)==tex && !memcmp(resource+tex,"TEX0",4) &&
        tex+rd32(tex+4)==resource_size,"resource blocks");
    require(resource[block+9]==1,"single original model");
    unsigned model=block+dict_offset(block+8,0); range(model,64);
    require(rd32(model)<=tex-model && model<tex,"model extent");
    const NNSG3dResMdlSet *set=(const void *)(resource+block);
    const NNSG3dResMdl *m=NNS_G3dGetMdlByIdx(set,0);
    require((const unsigned char *)m==resource+model,"original model accessor");
    require(m->info.numMat==1 && m->info.numShp==1 && m->info.texMtxMode<4,"model indices/mode");
    unsigned mat=model+rd32(model+8), shp=model+rd32(model+12);
    unsigned material=mat+dict_offset(mat+4,0), shape=shp+dict_offset(shp,0);
    range(material,44); range(shape,16);
    unsigned mat_size=rd16(material+2); range(material,mat_size);
    require(mat_size>=44 && material+mat_size<=model+rd32(model),"material extent");
    unsigned flags=rd16(material+30), extra=0;
    if(flags & 1) extra=(!(flags&2))*8+(!(flags&4))*4+(!(flags&8))*8;
    require(mat_size>=44+extra,"texture matrix fields");
    unsigned dl=shape+rd32(shape+8), dl_size=rd32(shape+12); range(dl,dl_size);
    require(!(dl%4) && !(dl_size%4) && dl_size>0 && dl+dl_size<=model+rd32(model),"shape extent/alignment");
    const G3dResShpData *s=G3dGetResShpDataByIdx(G3dGetResShp(m),0);
    require((const unsigned char *)s==resource+shape,"original shape accessor");
    expected_dl=resource+dl; expected_dl_size=dl_size;
    unsigned char *before=malloc(resource_size); require(before != NULL,"snapshot");
    memcpy(before,resource,resource_size);
    NNS_G3dDraw1Mat1Shp(m,0,0,TRUE);
    Event first[32]; unsigned first_count=event_count, first_size=captured_size;
    unsigned char first_bytes[65536];
    memcpy(first,events,sizeof(events)); memcpy(first_bytes,captured,captured_size);
    event_count=captured_size=0;
    NNS_G3dDraw1Mat1Shp(m,0,0,TRUE);
    require(first_count==event_count && first_size==captured_size &&
        !memcmp(first,events,event_count*sizeof(Event)) &&
        !memcmp(first_bytes,captured,captured_size),"repeat emission identity");
    require(!memcmp(before,resource,resource_size),"resource immutability");
    unsigned lists=0;
    for(unsigned i=0;i<event_count;i++) if(events[i].kind==1) {
        lists++; require(!memcmp(captured+events[i].offset,expected_dl,expected_dl_size),"captured shape bytes");
    }
    require(lists==1,"one original shape emission");
    f=fopen(argv[2],"wb"); require(f != NULL,"open capture");
    require(fwrite(captured,1,captured_size,f)==captured_size,"write capture");
    require(fclose(f)==0,"close capture");
    printf("{\"model\":0,\"material\":0,\"shape\":0,\"send_material\":true,\"tex_matrix_mode\":%u,\"material_flags\":%u,\"bytes\":%u,\"events\":[",m->info.texMtxMode,flags,captured_size);
    for(unsigned i=0;i<event_count;i++) printf("%s{\"kind\":\"%s\",\"offset\":%u,\"length\":%u,\"resource_offset\":%u}",i?",":"",events[i].kind?"display_list":"buffer",events[i].offset,events[i].length,events[i].resource_offset);
    puts("]}"); free(before); free(resource); return 0;
}
