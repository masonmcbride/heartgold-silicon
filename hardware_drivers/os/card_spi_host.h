/* Physical DS cartridge SPI has no macOS register mapping. Original protocol
 * code uses these lvalues in its original order. An unavailable register access
 * is a fatal unsupported hardware operation, never a successful transaction. */
#ifndef HG_CARD_SPI_HOST_H
#define HG_CARD_SPI_HOST_H
#include <stdint.h>
volatile uint16_t *HG_CardSpiRegister(unsigned offset);
#undef reg_MI_MCCNT0
#undef reg_MI_MCD0
#define reg_MI_MCCNT0 (*HG_CardSpiRegister(0x1a0))
#define reg_MI_MCD0 (*HG_CardSpiRegister(0x1a2))
#endif
