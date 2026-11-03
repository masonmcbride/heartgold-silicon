/* Test-only OS/locking observations; physical register access remains the
 * production fatal boundary, so no test synthesizes a successful SPI result. */
#include <string.h>
#include <nitro.h>
#include <nitro/card/card_spi_wait_internal.h>
#include <stdio.h>
/* Hide C's distinct-global assumption when checking linker interior aliases. */
__attribute__((noinline)) static const void *observed(const void *p) {
    __asm__ volatile("" : "+r"(p));
    return p;
}
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"failed: %s\n",#x); __builtin_trap(); } } while (0)
extern CardSpiWait gCardSpiWait;
static u64 tick;
static unsigned allocations;
s32 OS_GetLockID(void) { ++allocations; return 42; }
u64 OS_GetTick(void) { return tick += 100; }
void CARD_LockBackup(u16 id) { CHECK(id == 42); }
void CARD_UnlockBackup(u16 id) { CHECK(id == 42); }
s32 OS_LockCard(u16 id) { CHECK(id == 42); return 0; }
s32 OS_UnLockCard(u16 id) { CHECK(id == 42); return 0; }
int main(int argc, char **argv) {
    CHECK(gCardSpiLockId == 0xfffd);
    CARD_SpiWaitInit();
    CARD_SpiWaitInit();
    CHECK(allocations == 1 && gCardSpiLockId == 42);
    CHECK(gCardSpiWait.transfer.active == 1);
    CHECK(gCardSpiWait.dummyWait == 50 && gCardSpiWait.readWait == 50 && gCardSpiWait.writeWait == 50);
    CARD_SetSpiReadWaitCycles(300); CARD_SetSpiWriteWaitCycles(511);
    CHECK(gCardSpiWait.readWait == 44 && gCardSpiWait.writeWait == 255);
    CHECK((const char *)observed(&gCardSpiTransfer) == (const char *)observed(&gCardSpiWait.transfer.active));
    CHECK((const char *)observed(&gCardSpiTransfer.input) == (const char *)observed(&gCardSpiWait.transfer.input));
    CHECK((const char *)observed(&gCardSpiTransfer.output) == (const char *)observed(&gCardSpiWait.transfer.output));
    if (argc > 1) {
        u8 data[200];
        if (!strcmp(argv[1],"status")) CARD_SpiWaitGetStatus();
        else if (!strcmp(argv[1],"read")) CARD_SpiWaitReadRange(data);
        else CARD_SpiWaitWriteRange(data,1);
        CHECK(!"hardware call must not return");
    }
    return 0;
}
