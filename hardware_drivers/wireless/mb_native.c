#include "mb_native.h"
#include <stdlib.h>
#include <pthread.h>
/* Metadata is outside serialized storage. Lookup allocation is protected; the
 * values obey the same synchronization as their original work-area fields. */
typedef struct Reference {
    uintptr_t key;
    MBNativeReference value;
    struct Reference *next;
} Reference;
static Reference *references;
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
MBNativeReference *MB_NativeReference(const void *owner, size_t offset) {
    uintptr_t key = (uintptr_t)owner + offset;
    pthread_mutex_lock(&mutex);
    Reference *r = references;
    while (r && r->key != key) r = r->next;
    if (!r) {
        r = calloc(1, sizeof(*r));
        if (!r) abort();
        r->key = key;
        r->next = references;
        references = r;
    }
    pthread_mutex_unlock(&mutex);
    return &r->value;
}
void MB_NativeForget(const void *owner, size_t length) {
    uintptr_t start = (uintptr_t)owner;
    pthread_mutex_lock(&mutex);
    Reference **link = &references;
    while (*link) {
        Reference *r = *link;
        if (r->key >= start && r->key - start < length) {
            *link = r->next;
            free(r);
        } else link = &r->next;
    }
    pthread_mutex_unlock(&mutex);
}
