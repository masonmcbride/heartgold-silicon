/* Independent bit transition from the recorded historical native provider. */
#include <nitro/os/common/systemCall.h>
#include <stdint.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>

static uint16_t reference(uint32_t seed,const unsigned char *data,unsigned size)
{
    uint16_t state=seed;
    for(unsigned i=0;i<size;i++){
        state^=data[i];
        for(unsigned bit=0;bit<8;bit++)
            state=(state>>1)^((state&1)?0xa001:0);
    }
    return state;
}
int main(void)
{
    unsigned char *data=malloc(1026);assert(data && (uintptr_t)data>UINT32_MAX);
    for(unsigned i=0;i<1026;i++)data[i]=i*73+i/7;
    const uint32_t seeds[]={0,1,0x8000,0xffff,0x1234ffff};
    assert(SVC_GetCRC16(0,"123456789",9)==0xbb3d);
    for(unsigned s=0;s<sizeof seeds/sizeof *seeds;s++)for(unsigned n=0;n<=1025;n++){
        assert(SVC_GetCRC16(seeds[s],data,n)==reference(seeds[s],data,n));
        unsigned half=n/2;
        assert(SVC_GetCRC16(SVC_GetCRC16(seeds[s],data,half),data+half,n-half)==reference(seeds[s],data,n));
    }
    free(data);return 0;
}
