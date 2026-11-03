/* Original SDK declarations and inline entry points, compiled as ARM32. MIT */
#include <nitro/mi/memory.h>
void MemoryContracts(void *dst,const void *src){
    MIi_CpuClear16(0x1234,dst,16);
    MIi_CpuCopy16(src,dst,16);
    MIi_CpuClear32(0x12345678,dst,32);
    MIi_CpuCopy32(src,dst,32);
    MIi_CpuClearFast(0x11223344,dst,36);
    MI_CpuFill8(dst,0xa5,7);
    MI_CpuCopy8(src,dst,7);
}
