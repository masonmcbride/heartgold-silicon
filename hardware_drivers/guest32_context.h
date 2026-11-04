/* Private compiled-guest continuations. SPDX-License-Identifier: MIT */
#ifndef HG_GUEST32_CONTEXT_H
#define HG_GUEST32_CONTEXT_H
#include <stdint.h>
void g32_execution_save(void*,void**,uint32_t*,uint32_t*);
void g32_execution_load(void*,void*,uint32_t,uint32_t);
void g32_execution_discard(void*);
uint32_t *g32_cpsr(void*);
unsigned char *g32_cp_state(void*);
void **g32_context_storage(void*);
void g32_context_cleanup(void*,void(*)(void*));
void guest32_OS_InitContext(void*,uint32_t,uint32_t,uint32_t);
void g32_bind_thread_context(void*,uint32_t,uint32_t,uint32_t);
__attribute__((returns_twice)) int guest32_OS_SaveContext(void*,uint32_t);
__attribute__((noreturn)) void guest32_OS_LoadContext(void*,uint32_t);
/* Generated from the shared code catalog; no native address enters guest RAM. */
void guest32_thread_entry(void*,uint32_t,uint32_t);
#endif
