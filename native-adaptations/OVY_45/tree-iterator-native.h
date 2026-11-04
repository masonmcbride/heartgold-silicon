#ifndef HEARTGOLD_NATIVE_DWC_TREE_ITERATOR4_H
#define HEARTGOLD_NATIVE_DWC_TREE_ITERATOR4_H

/* Native ABI equivalent of the original DS pointer iterator.
 * Preincluded for ppw_lobby_get_work.c only.
 * The upstream header remains unchanged and pinned.
 */
#ifndef DWC_TREE_ITERATOR4_H
#define DWC_TREE_ITERATOR4_H
typedef struct Iterator {
    void *current;
#ifdef __cplusplus
    void Advance();
#endif
} Iterator;

typedef char DwcTreeIteratorNativePointerSize[
    sizeof(Iterator) == sizeof(void *) ? 1 : -1
];

#ifndef __cplusplus
void LobbyTreeIterator_Advance(Iterator *);
#endif
#endif
#endif
