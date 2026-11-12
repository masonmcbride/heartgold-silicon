#include <stdint.h>
typedef uint64_t uPtr;
typedef int BOOL;
typedef int PXIFifoTag;
typedef void (*PXIFifoCallback)(PXIFifoTag,uPtr,BOOL);
enum { PXI_FIFO_TAG_NVRAM=4, PXI_PROC_ARM7=1, PXI_FIFO_SUCCESS=0, FALSE=0, TRUE=1};
void PXI_SetFifoRecvCallback7(int,PXIFifoCallback);
int PXI_IsCallbackReady(int,int);
int PXI_SendWordByFifo7(int,uPtr,BOOL);
