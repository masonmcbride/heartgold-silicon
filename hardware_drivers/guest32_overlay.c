/* Guest callback admission uses the real native overlay lifecycle. MIT */
#include "guest32.h"
#include "os/overlay_native.h"
#include <errno.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>

void g32_check_code_image(void *ram, uint32_t code, uint32_t owner, const void *entry)
{
    (void)g32_epoch(ram);
    HG_OverlayImage *image = HG_GetOverlayImage(owner);
    if (!HG_OverlayIsResident(image) || !HG_OverlayOwnsAddress(image, entry) ||
        !HG_OverlayAcceptsArena(image, ram))
        g32_bad_code(ram, code);
}


typedef struct GuestImage {void *ram;uint32_t owner;void (*start)(void *);} GuestImage;
static void activate(void *context){GuestImage *g=context;g32_overlay_active(g->ram,g->owner,1);}
static void deactivate(void *context){GuestImage *g=context;g32_overlay_active(g->ram,g->owner,0);}
static void retire(void *context){
    GuestImage *g=context;g32_forget_overlay(g->ram,g->owner);g32_release_arena(g->ram);free(g);
}
static void start_original(void *context){
    GuestImage *g=context;void *previous=g32_enter(g->ram);
    g->start(g->ram);g32_leave(previous);
}

HG_OverlayImage *g32_register_guest_overlay_start(
    void *ram,uint32_t overlay_id,const void *const *entries,size_t entry_count,
    const G32_OverlaySection *sections,size_t section_count,void (*original_start)(void *))
{
    if(!ram || (entry_count && !entries) || (section_count && !sections) ||
       section_count>SIZE_MAX/sizeof(HG_OverlayData)){errno=EINVAL;return NULL;}
    if(HG_GetOverlayImage(overlay_id)){errno=EEXIST;return NULL;}
    HG_OverlayData *data=section_count?calloc(section_count,sizeof(*data)):NULL;
    GuestImage *guest=calloc(1,sizeof(*guest));
    if((section_count && !data) || !guest){free(data);free(guest);return NULL;}
    for(size_t i=0;i<section_count;i++){
        const G32_OverlaySection *section=&sections[i];
        if(!section->size || !section->initial_bytes){errno=EINVAL;goto bad;}
        data[i]=(HG_OverlayData){g32_overlay_storage(ram,section->guest_address,section->size),section->initial_bytes,section->size};
    }
    *guest=(GuestImage){ram,overlay_id,original_start};
    HG_OverlayImage *image=HG_RegisterResidentOverlay(ram,entries,entry_count,data,section_count,
        original_start?start_original:NULL,guest);
    free(data);data=NULL;
    if(!image)goto bad;
    if(!HG_BindOverlayID(overlay_id,image) || !g32_reserve_overlay(ram,overlay_id,sections,section_count)){
        int error=errno;HG_ReleaseOverlayImage(image);errno=error;goto bad;
    }
    g32_retain_arena(ram);
    if(!HG_SetOverlayStorageHooks(image,activate,deactivate,retire,guest))abort();
    return image;
bad:
    free(data);free(guest);return NULL;
}
HG_OverlayImage *g32_register_guest_overlay(void *ram,uint32_t owner,
    const void *const *entries,size_t entry_count,const G32_OverlaySection *sections,size_t section_count){
    return g32_register_guest_overlay_start(ram,owner,entries,entry_count,sections,section_count,NULL);
}
int g32_capture_entry(void *ram,uint32_t owner,const void *entry,G32_EntryTicket *ticket){
    if(!g32_is_game_thread(ram)){errno=EPERM;return 0;}
    HG_OverlayImage *image=HG_GetOverlayImage(owner);
    if(!ticket || g32_game_arena()!=ram){errno=EINVAL;return 0;}
    uint64_t generation=HG_OverlayGeneration(image);
    if(!HG_AcquireOverlayEntry(image,generation,ram,entry))return 0;
    HG_ReleaseOverlayEntry(image);*ticket=(G32_EntryTicket){owner,generation,entry};return 1;
}
int g32_enter_entry(void *ram,const G32_EntryTicket *ticket,void **previous){
    if(!g32_is_game_thread(ram)){errno=EPERM;return 0;}
    if(!ticket || !previous || g32_game_arena()!=ram){errno=EINVAL;return 0;}
    if(!HG_AcquireOverlayEntry(HG_GetOverlayImage(ticket->owner),ticket->generation,ram,ticket->entry))return 0;
    *previous=g32_enter(ram);return 1;
}
void g32_leave_entry(void *ram,const G32_EntryTicket *ticket,void *previous){
    if(g32_current()!=ram || !ticket)abort();
    g32_leave(previous);HG_ReleaseOverlayEntry(HG_GetOverlayImage(ticket->owner));
}

typedef struct EntryScope {G32_EntryContext context;void *previous;} EntryScope;
int g32_capture_entry_context(void *ram,uint32_t owner,const void *entry,G32_EntryContext *context){
    if(!context){errno=EINVAL;return 0;}
    G32_EntryTicket ticket;if(!g32_capture_entry(ram,owner,entry,&ticket))return 0;
    *context=(G32_EntryContext){ram,ticket};return 1;
}
void *g32_begin_entry_context(const G32_EntryContext *context,uint32_t owner,const void *entry){
    if(!context || context->ticket.owner!=owner || context->ticket.entry!=entry){
        fputs("guest32 entry: wrong original owner or callback context\n",stderr);abort();
    }
    EntryScope *scope=malloc(sizeof(*scope));if(!scope)abort();scope->context=*context;
    if(!g32_enter_entry(context->arena,&context->ticket,&scope->previous)){
        free(scope);fputs("guest32 entry: stale callback or wrong execution thread\n",stderr);abort();
    }
    return scope;
}
void *g32_entry_context_arena(void *scope){if(!scope)abort();return ((EntryScope*)scope)->context.arena;}
void g32_end_entry_context(void *opaque){
    EntryScope *scope=opaque;if(!scope)abort();
    g32_leave_entry(scope->context.arena,&scope->context.ticket,scope->previous);free(scope);
}
