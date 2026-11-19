/* SPDX-License-Identifier: MIT */
#include <nitro.h>
#include <ntr_host.h>
#include <assert.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static atomic_uint callbacks;
static HG_ThreadID caller;
static void finished(void *arg)
{
    assert(arg == &callbacks);
    assert(HG_GetThreadID(NULL) != caller);
    atomic_fetch_add(&callbacks, 1);
}

int main(int argc, char **argv)
{
    assert(argc == 2);
    char path[4096];
    assert(snprintf(path, sizeof path, "%s/backup-test-XXXXXX", argv[1]) < sizeof path);
    int fd = mkstemp(path); assert(fd >= 0); close(fd); assert(!unlink(path));
    const uint32_t size = 512 * 1024;
    assert(HG_BackupOpen(path, size));
    assert(!HG_BackupOpen(path, size));
    unsigned char *input = malloc(1024), *output = malloc(1024);
    assert(input && output && (uintptr_t)input > UINT32_MAX && (uintptr_t)output > UINT32_MAX);
    assert(HG_BackupRead(size-1024, output, 1024));
    for (unsigned i=0; i<1024; ++i) assert(output[i] == 0xff);
    assert(!HG_BackupRead(size-1, output, 2));
    assert(!HG_BackupRead(UINT32_MAX, output, 1));
    assert(!HG_BackupWrite(size, input, 1, 0));
    assert(!HG_BackupErase(size-1, 2));

    /* Exercise the actual SDK, including its worker and callback path. */
    OS_Init();
    caller = HG_GetThreadID(NULL);
    u16 id = OS_GetLockID();
    assert(id != OS_LOCK_ID_ERROR);
    CARD_LockBackup(id);
    assert(CARD_IdentifyBackup(CARD_BACKUP_TYPE_FLASH_4MBITS_EX));
    assert(CARD_GetBackupTotalSize() == size);
    for (unsigned i=0; i<1024; ++i) input[i] = (unsigned char)(i*13);
    CARD_WriteAndVerifyBackupAsync(0x1ff80, input, 1024, finished, &callbacks);
    assert(CARD_WaitBackupAsync());
    /* EndTask clears busy before calling back; synchronize on the callback too. */
    uint64_t start = HG_GetTicks64();
    while (!atomic_load(&callbacks) && HG_GetTicks64()-start < 1000) HG_Delay(1);
    assert(atomic_load(&callbacks) == 1 && CARD_GetResultCode() == CARD_RESULT_SUCCESS);
    assert(CARD_ReadBackup(0x1ff80, output, 1024));
    assert(!memcmp(input, output, 1024));
    output[0] ^= 1;
    assert(!CARD_VerifyBackup(0x1ff80, output, 1024));
    assert(CARD_GetResultCode() != CARD_RESULT_SUCCESS);
    assert(!HG_BackupVerify(0x1ff80, output, 1024));
    CARD_UnlockBackup(id);

    HG_BackupClose();
    assert(!HG_BackupOpen(path, size/2)); // Must preserve a differently sized file.
    assert(HG_BackupOpen(path, size));
    assert(HG_BackupRead(0x1ff80, output, 1024));
    assert(!memcmp(input, output, 1024));
    memset(input, 0xff, 1024);
    assert(HG_BackupWrite(0x1ff80, input, 1024, 1));
    assert(HG_BackupRead(0x1ff80, input, 1024));
    assert(!memcmp(input, output, 1024)); // Programming cannot turn zero bits to one.
    assert(HG_BackupErase(0x10000, 0x20000));
    assert(HG_BackupRead(0x1ff80, output, 1024));
    for (unsigned i=0; i<1024; ++i) assert(output[i] == 0xff);
    HG_BackupClose();
    assert(!HG_BackupRead(0, output, 1));
    free(input); free(output); assert(!unlink(path));
    puts("Backup: original SDK async write/verify, high pointers, erased bytes, bounds, persistence and size rejection");
}
