/* Frame retirement and scheduler negative controls. SPDX-License-Identifier: MIT */
#include "guest32.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>
int main(int argc,char **argv) {
    void *ram=g32_create_ds(0x02200000);assert(ram);
    if(argc>1) {
        void *a=g32_frame_enter(ram);uint32_t x=g32_stack_alloc(ram,a,16,16);
        if(!strcmp(argv[1],"order")) {
            void *b=g32_frame_enter(ram);g32_stack_alloc(ram,b,16,16);
            /* Resuming/retiring A while B is suspended has no supported context. */
            g32_frame_leave(ram,a);
        } else {
            g32_frame_leave(ram,a);g32_resolve(ram,x,1,0);
        }
        return 1;
    }
    for(unsigned i=0;i<20000;i++) {
        void *f=g32_frame_enter(ram);uint32_t a=g32_stack_alloc(ram,f,16,16);
        *(uint32_t*)g32_resolve(ram,a,4,0)=i;
        void *nested=g32_frame_enter(ram);uint32_t b=g32_stack_alloc(ram,nested,16,16);
        *(uint32_t*)g32_resolve(ram,b,4,0)=~i;
        void *heap=0;
        if(i==0)heap=g32_allocate(ram,32,16);
        g32_frame_leave(ram,nested);
        assert(*(uint32_t*)g32_resolve(ram,a,4,0)==i);
        g32_frame_leave(ram,f);
        if(heap){uint32_t h=g32_encode(ram,heap,32,0);g32_release(ram,heap,32);g32_check_consumed(ram,h);}
        assert(g32_stack_pointer(ram)==G32_MAIN_RAM_BASE+G32_MAIN_RAM_SIZE);
    }
    assert(g32_live_allocations(ram)==0);g32_destroy(ram);
}
