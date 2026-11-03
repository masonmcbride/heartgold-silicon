#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "hardware_drivers/guest32.h"

extern uint32_t guest32_strlen(void *, uint32_t);
extern int32_t guest32_strcmp(void *, uint32_t, uint32_t);
extern int32_t guest32_strncmp(void *, uint32_t, uint32_t, uint32_t);
extern uint32_t guest32_memcpy(void *, uint32_t, uint32_t, uint32_t);
extern uint32_t guest32_memmove(void *, uint32_t, uint32_t, uint32_t);
extern uint32_t guest32_memset(void *, uint32_t, int32_t, uint32_t);
extern int32_t guest32_memcmp(void *, uint32_t, uint32_t, uint32_t);
extern uint32_t guest32_strcpy(void *, uint32_t, uint32_t);
extern uint32_t guest32_strncpy(void *, uint32_t, uint32_t, uint32_t);
extern uint32_t guest32_strcat(void *, uint32_t, uint32_t);
extern uint32_t guest32_strchr(void *, uint32_t, int32_t);
extern uint32_t guest32_strstr(void *, uint32_t, uint32_t);

static uint32_t alloc(
    void *ram, const char *value, uint32_t capacity
) {
    char *p = g32_allocate(ram, capacity, 16);
    assert(p);
    if (value) {
        assert(strlen(value) < capacity);
        strcpy(p, value);
    }
    return g32_encode(ram, p, capacity, 0);
}

static char *at(void *ram, uint32_t p, uint32_t size) {
    return g32_resolve(ram, p, size, 0);
}

int main(void) {
    void *ram = g32_create(1 << 20, 8192);
    assert(ram);

    uint32_t a = alloc(ram, "HeartGold", 64);
    uint32_t b = alloc(ram, "Heart", 64);
    uint32_t c = alloc(ram, "Gold", 64);
    uint32_t d = alloc(ram, NULL, 64);

    assert(guest32_strlen(ram, a) == 9);
    assert(guest32_strcmp(ram, a, b) > 0);
    assert(guest32_strcmp(ram, b, b) == 0);
    assert(guest32_strncmp(ram, a, b, 5) == 0);
    assert(guest32_strncmp(ram, a, b, 6) > 0);

    assert(guest32_memcpy(ram, d, a, 10) == d);
    assert(memcmp(at(ram, d, 10), "HeartGold", 10) == 0);

    assert(guest32_memmove(ram, d + 2, d, 10) == d + 2);
    assert(memcmp(at(ram, d + 2, 10), "HeartGold", 10) == 0);

    assert(guest32_memset(ram, d, 'x', 3) == d);
    assert(memcmp(at(ram, d, 3), "xxx", 3) == 0);
    assert(guest32_memcmp(ram, a, b, 5) == 0);
    assert(guest32_memcmp(ram, a, c, 1) > 0);

    assert(guest32_strcpy(ram, d, b) == d);
    assert(strcmp(at(ram, d, 6), "Heart") == 0);

    assert(guest32_strcat(ram, d, c) == d);
    assert(strcmp(at(ram, d, 10), "HeartGold") == 0);

    assert(guest32_strchr(ram, a, 'G') == a + 5);
    assert(guest32_strchr(ram, a, '\0') == a + 9);
    assert(guest32_strchr(ram, a, 'Z') == 0);
    assert(guest32_strstr(ram, a, c) == a + 5);
    assert(guest32_strstr(ram, a, b) == a);
    assert(guest32_strstr(ram, b, a) == 0);

    memset(at(ram, d, 64), 0x7f, 64);
    assert(guest32_strncpy(ram, d, b, 12) == d);
    assert(memcmp(at(ram, d, 6), "Heart", 6) == 0);
    for (unsigned i = 6; i < 12; ++i)
        assert(((unsigned char *)at(ram, d, 64))[i] == 0);
    assert(((unsigned char *)at(ram, d, 64))[12] == 0x7f);

    assert(guest32_memcpy(ram, 0, 0, 0) == 0);
    assert(guest32_memmove(ram, 0, 0, 0) == 0);
    assert(guest32_memset(ram, 0, 0, 0) == 0);
    assert(guest32_memcmp(ram, 0, 0, 0) == 0);

    printf("PASS: 12/12 guest32 libc functions executed\n");
    printf("PASS: guest pointer returns, overlap, zero lengths\n");
    printf("PASS: string terminators and strncpy padding\n");

    g32_destroy(ram);
    return 0;
}
