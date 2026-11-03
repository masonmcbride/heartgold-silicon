#include "card_spi_host.h"
#include <stdio.h>
#include <stdlib.h>

volatile uint16_t *HG_CardSpiRegister(unsigned offset) {
    fprintf(stderr, "Unsupported physical DS cartridge SPI register 0x%08x: no host transport\n",
            0x04000000u + offset);
    abort();
}
