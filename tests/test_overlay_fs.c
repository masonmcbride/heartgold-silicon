/* Exercise original FS lifecycle/chain algorithms with native-image fixtures. */
#include <nitro.h>
#include <ntr_host.h>
#include "mw_dtor.h"
#include <assert.h>
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>

static int calls, external_object;
static MWiDestructorChain added;
static void *native_object;
static void observe(void) { ++calls; }
static void added_destructor(void *object) { assert(object == native_object); ++calls; }
static void register_during_disposal(void *object)
{
    assert(object == native_object);
    ++calls;
    added.next = __global_destructor_chain;
    added.obj = object;
    added.dtor = added_destructor;
    __global_destructor_chain = &added;
}

int main(int argc, char **argv)
{
    assert(argc == 2);
    void *library = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    assert(library);
    int *value = dlsym(library, "overlay_initialized");
    int *bss = dlsym(library, "overlay_bss");
    void (*set_observer)(void (*)(void)) = dlsym(library, "overlay_set_observer");
    void (*destructor)(void *) = dlsym(library, "overlay_destructor");
    assert(value && bss && set_observer && destructor);
    native_object = value;
    HG_OverlayImage *image = HG_InspectOverlayImage(value);
    assert(image && HG_BindOverlayID(60, image));
    assert(HG_GetOverlayImage(60) == image && !HG_GetOverlayImage(36));
    assert(!HG_BindOverlayID(36, image));
    FSOverlayInfo info = {0};
    info.header.id = 60;
    info.target = MI_PROCESSOR_ARM9;
    assert(!FS_UnloadOverlayImage(&info));
    FSFile request;
    assert(FS_LoadOverlayImageAsync(&info, &request));
    assert(FS_WaitAsync(&request));
    assert(FS_CloseFile(&request));
    assert(request.nativeOverlayResult == 0 && request.pcFilePtr == NULL);
    assert(!FS_LoadOverlayImage(&info));
    assert(!FS_LoadOverlayImageAsync(&info, &request));
    assert(!FS_WaitAsync(&request));
    assert(FS_CloseFile(&request));
    set_observer(observe);
    FS_StartOverlay(&info);
    assert(calls == 1 && *bss == 1);
    MWiDestructorChain nodes[5] = {
        { &nodes[1], added_destructor, &external_object },
        { &nodes[2], register_during_disposal, value },
        { &nodes[3], destructor, NULL },
        { &nodes[4], NULL, value },
        { NULL, added_destructor, &external_object }
    };
    assert((uintptr_t)value > UINT32_MAX && (uintptr_t)nodes > UINT32_MAX);
    __global_destructor_chain = nodes;
    *value = 99;
    assert(FS_UnloadOverlayImage(&info));
    /* Original first sweep preserves unrelated nodes; second drains the node
     * registered by a destructor. Null destructors are detached safely. */
    assert(calls == 4);
    assert(__global_destructor_chain == &nodes[0]);
    assert(nodes[0].next == &nodes[4] && nodes[4].next == NULL);
    assert(!HG_OverlayCanUnload(image) && !FS_UnloadOverlayImage(&info));
    assert(FS_LoadOverlayImage(&info));
    assert(*value == 0x12345678 && *bss == 0);
    FS_StartOverlay(&info);
    assert(*bss == 1 && calls == 4); /* observer was reset with image BSS */
    assert(FS_UnloadOverlayImage(&info));
    __global_destructor_chain = NULL;
    assert(HG_ReleaseOverlayImage(image) && !HG_GetOverlayImage(60));
    puts("original FS native-image start/unload/destructor-chain/reload: passed");
}
