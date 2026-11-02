#ifndef HEARTGOLD_MB_NATIVE_H
#define HEARTGOLD_MB_NATIVE_H
#include <stddef.h>
#include <stdint.h>
/* Native identities for four-byte fields in original MB work records. Keys are
 * field addresses within the actual owning allocation, never DS pointer bits.
 * Callers retain the original SDK interrupt/queue synchronization discipline. */
/* Native registration input; the embedded DS download/cache records stay fixed. */
typedef struct MBNativeFile {
    uint32_t reserved;
    const uint16_t *name, *description;
    void *icon1, *icon2;
    uint32_t game;
    uint8_t flag;
    uint8_t reserved_after_flag[3];
    uint8_t userData[32];
} MBNativeFile;
#define MB_DS_ROM_HEADER 0x027ffe00u
typedef struct Task {
    uint32_t next;
    union {
        uint32_t flags;
        struct { uint32_t busy : 1, priority : 31; } bits;
    };
    uint32_t function, callback;
    uint8_t payload[16];
} Task;
#ifdef __cplusplus
static_assert(sizeof(Task) == 0x20 && offsetof(Task, payload) == 0x10, "fixed MB task record");
#else
_Static_assert(sizeof(Task) == 0x20 && offsetof(Task, payload) == 0x10, "fixed MB task record");
#endif
typedef void (*MBNativeTaskCallback)(void *);
typedef union MBNativeReference {
    struct Task *next;
    MBNativeTaskCallback task;
    void *pointer;
    void (*wm)(int, void *);
    void (*beacon)(uint32_t);
    void (*parent)(uint32_t, uint32_t, void *);
    void (*indication)(void *);
} MBNativeReference;
#ifdef __cplusplus
extern "C" {
#endif
MBNativeReference *MB_NativeReference(const void *owner, size_t offset);
void MB_NativeForget(const void *owner, size_t length);
#ifdef __cplusplus
}
#endif
#define MB_PTR(owner, offset) (MB_NativeReference((owner), (offset))->pointer)
#define MB_WM(owner) (MB_NativeReference((owner), 0x51c)->wm)
#define MB_PARENT(owner) (MB_NativeReference((owner), 0x14e4)->parent)
#define MB_IND(owner) (MB_NativeReference((owner), 0x508)->indication)
#endif
