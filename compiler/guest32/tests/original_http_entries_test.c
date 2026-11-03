#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "hardware_drivers/guest32.h"

/*
 * Original functions compiled from auth_netcheck.c by guest32.
 * These are not replacements or reimplementations.
 */
extern uint32_t guest32_DWCi_Http_GetEntry(
    void *ram, uint32_t http, uint32_t label
);

extern int32_t guest32_DWCi_Http_GetStringEntry(
    void *ram, uint32_t http, uint32_t label,
    uint32_t output, int32_t capacity
);

enum {
    NAS_HTTP_SIZE = 0x1C14,
    ENTRY_OFFSET = 0x1A38,
    ENTRY_STRIDE = 8,
    ENTRY_COUNT = 32
};

static void put32(void *ram, uint32_t address, uint32_t value) {
    void *p = g32_resolve(ram, address, 4, 0);
    memcpy(p, &value, sizeof(value));
}

static uint32_t guest_string(void *ram, const char *value) {
    size_t n = strlen(value) + 1;
    assert(n <= UINT32_MAX);

    char *p = g32_allocate(ram, (uint32_t)n, 16);
    assert(p);

    memcpy(p, value, n);
    return g32_encode(ram, p, (uint32_t)n, 0);
}

static uint32_t guest_buffer(void *ram, uint32_t size) {
    void *p = g32_allocate(ram, size, 16);
    assert(p);
    return g32_encode(ram, p, size, 0);
}

static void set_entry(
    void *ram, uint32_t http, uint32_t index,
    uint32_t label, uint32_t value
) {
    assert(index < ENTRY_COUNT);

    uint32_t location =
        http + ENTRY_OFFSET + index * ENTRY_STRIDE;

    put32(ram, location, label);
    put32(ram, location + 4, value);
}

static void fill(void *ram, uint32_t address, uint32_t size) {
    memset(g32_resolve(ram, address, size, 0), 0xA5, size);
}

static void unchanged(
    void *ram, uint32_t address, uint32_t size
) {
    const unsigned char *p =
        g32_resolve(ram, address, size, 0);

    for (uint32_t i = 0; i < size; ++i)
        assert(p[i] == 0xA5);
}

int main(void) {
    void *ram = g32_create(1 << 20, 8192);
    assert(ram);

    void *http_storage =
        g32_allocate(ram, NAS_HTTP_SIZE, 16);
    assert(http_storage);

    uint32_t http = g32_encode(
        ram, http_storage, NAS_HTTP_SIZE, 0
    );

    uint32_t label_status = guest_string(ram, "status");
    uint32_t label_token = guest_string(ram, "token");
    uint32_t label_missing = guest_string(ram, "missing");

    uint32_t value_status = guest_string(ram, "200");
    uint32_t value_token = guest_string(ram, "HeartGold");

    uint32_t output = guest_buffer(ram, 32);

    /* Preserve the original 32-bit entry structure. */
    assert(ENTRY_OFFSET + ENTRY_STRIDE * ENTRY_COUNT
           <= NAS_HTTP_SIZE);

    set_entry(
        ram, http, 0, label_status, value_status
    );
    set_entry(
        ram, http, 1, label_token, value_token
    );

    /* Null third label terminates the original scan. */
    set_entry(ram, http, 2, 0, 0);

    puts("=== ORIGINAL HTTP ENTRY LOOKUP ===");

    assert(
        guest32_DWCi_Http_GetEntry(
            ram, http, label_status
        ) == value_status
    );

    assert(
        guest32_DWCi_Http_GetEntry(
            ram, http, label_token
        ) == value_token
    );

    assert(
        guest32_DWCi_Http_GetEntry(
            ram, http, label_missing
        ) == 0
    );

    puts("PASS: original lookup returns guest value addresses");
    puts("PASS: original lookup handles missing labels");

    puts("\n=== ORIGINAL HTTP STRING EXTRACTION ===");

    fill(ram, output, 32);

    assert(
        guest32_DWCi_Http_GetStringEntry(
            ram, http, label_token, output, 32
        ) == 1
    );

    assert(
        strcmp(
            g32_resolve(ram, output, 10, 0),
            "HeartGold"
        ) == 0
    );

    /* Guest strcpy must return and write real guest memory. */
    assert(
        *(const char *)g32_resolve(
            ram, output + 9, 1, 0
        ) == '\0'
    );

    puts("PASS: original string extraction through guest32 libc");

    /* Nine characters plus NUL: capacity 10 succeeds. */
    fill(ram, output, 32);

    assert(
        guest32_DWCi_Http_GetStringEntry(
            ram, http, label_token, output, 10
        ) == 1
    );

    assert(
        strcmp(
            g32_resolve(ram, output, 10, 0),
            "HeartGold"
        ) == 0
    );

    unchanged(ram, output + 10, 22);

    puts("PASS: exact destination capacity");

    /* Capacity 9 must fail and leave destination untouched. */
    fill(ram, output, 32);

    assert(
        guest32_DWCi_Http_GetStringEntry(
            ram, http, label_token, output, 9
        ) == 0
    );

    unchanged(ram, output, 32);

    puts("PASS: insufficient capacity rejects without writing");

    fill(ram, output, 32);

    assert(
        guest32_DWCi_Http_GetStringEntry(
            ram, http, label_missing, output, 32
        ) == 0
    );

    unchanged(ram, output, 32);

    puts("PASS: missing entry leaves output unchanged");

    /* A null label terminates the search, even with
       a matching entry later in the fixed 32-entry array. */
    set_entry(ram, http, 3, label_missing, value_status);

    assert(
        guest32_DWCi_Http_GetEntry(
            ram, http, label_missing
        ) == 0
    );

    puts("PASS: original null-entry termination");

    /*
     * The host allocations are above 4 GiB, but all game
     * pointers remain 32-bit guest offsets.
     */
    assert((uintptr_t)ram > UINT32_MAX);

    puts("\n=== MILESTONE ===");
    puts("PASS: original GetEntry executed");
    puts("PASS: original GetStringEntry executed");
    puts("PASS: genuine guest32 strcmp/strlen/strcpy");
    puts("PASS: original 32-bit NasHttp entry layout");
    puts("PASS: original lookup and buffer boundary semantics");

    g32_destroy(ram);
    return 0;
}
