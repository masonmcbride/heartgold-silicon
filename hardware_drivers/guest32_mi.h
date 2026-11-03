/* Checked native memory operations for original guest MI instructions. MIT */
#ifndef HG_GUEST32_MI_H
#define HG_GUEST32_MI_H
#include "guest32.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static inline void *g32_mi_span(void *ram,uint32_t address,uint32_t width){
    if((width!=2 && width!=4) || (address&(width-1))){
        fputs("guest32 MI: unaligned original memory instruction\n",stderr);abort();
    }
    return g32_resolve(ram,address,width,0);
}
static inline uint32_t g32_mi_read(void *ram,uint32_t address,uint32_t width){
    void *p=g32_mi_span(ram,address,width);
    if(width==2){uint16_t v;memcpy(&v,p,2);return v;}
    uint32_t v;memcpy(&v,p,4);return v;
}
static inline void g32_mi_write(void *ram,uint32_t address,uint32_t value,uint32_t width){
    void *p=g32_mi_span(ram,address,width);
    if(width==2){uint16_t v=(uint16_t)value;memcpy(p,&v,2);}else memcpy(p,&value,4);
}
#endif
