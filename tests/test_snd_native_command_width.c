
#include <nitro/snd/common/command.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    SNDCommand command;
    memset(&command, 0, sizeof(command));

    uintptr_t address = UINT64_C(0x123456789ABCDEF0);

    if (sizeof(command.arg[1]) < sizeof(address)) {
        fprintf(stderr,
            "FAIL: command argument cannot represent host pointer\n");
        return 1;
    }

    command.arg[1] = address;

    if ((uintptr_t)command.arg[1] != address) {
        fprintf(stderr,
            "FAIL: native pointer truncated in command storage\n");
        return 1;
    }

    printf("PASS: %zu-byte command arguments preserve "
           "64-bit pointer words\n", sizeof(command.arg[1]));
    return 0;
}
