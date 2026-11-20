typedef struct HGNativeCellAttrBlock {
    u32 signature;
    u32 size;
    struct {
        u16 numCells;
        u16 numAttribute;
        const u32 **pCellAttrArray;
    } attributes;
} HGNativeCellAttrBlock;

static NNSG2dCellDataBank *HGDecodeCellBank(
    void *resource, enum HeapID heapID)
{
    u8 *block;
    const u8 *p, *extension = NULL;
    u32 blockSize, size, cellsOffset, mapping;
    u32 count, attributes, wireStride, nativeStride;
    u32 recordBytes, oamOffset, oamEnd;
    u32 transferOffset, stringOffset, extendedOffset;
    u32 arrayOffset = 0, maximum = 0;
    u32 extensionSize = 0, attrArrayOffset = 0;
    u32 attributeCount = 0, i;
    size_t allocation;
    NNSG2dCellDataBank *bank;
    u8 *cells, *cursor;

    if (!resource)
        return NULL;

    block = NNS_G2dFindBinaryBlock(resource, (u32)'CEBK');
    if (!block)
        return NULL;

    blockSize = HGCellRead32(block + 4);
    if (blockSize < 32)
        return NULL;

    p = block + 8;
    size = blockSize - 8;

    count = HGCellRead16(p);
    attributes = HGCellRead16(p + 2);
    cellsOffset = HGCellRead32(p + 4);
    mapping = HGCellRead32(p + 8);
    transferOffset = HGCellRead32(p + 12);
    stringOffset = HGCellRead32(p + 16);
    extendedOffset = HGCellRead32(p + 20);

    if (!count || (attributes & ~1u) || stringOffset)
        return NULL;

    wireStride = (attributes & 1) ? 16 : 8;
    nativeStride = (attributes & 1)
        ? sizeof(HGNativeCellWithBR)
        : sizeof(NNSG2dCellData);

    if (cellsOffset < 24 || cellsOffset > size ||
        count > (size - cellsOffset) / wireStride)
        return NULL;

    recordBytes = count * wireStride;
    oamOffset = cellsOffset + recordBytes;
    oamEnd = size;

    if (transferOffset) {
        if (transferOffset < oamOffset ||
            transferOffset > size ||
            size - transferOffset < 8)
            return NULL;

        maximum = HGCellRead32(p + transferOffset);
        arrayOffset = HGCellRead32(p + transferOffset + 4);

        if (!maximum || arrayOffset < 8 ||
            arrayOffset > size - transferOffset ||
            count > (size - transferOffset - arrayOffset) / 8)
            return NULL;

        oamEnd = transferOffset;
    }

    if (extendedOffset) {
        u32 n, attributeArray;

        if (extendedOffset < oamOffset ||
            extendedOffset > size ||
            size - extendedOffset < 16)
            return NULL;

        extension = p + extendedOffset;
        extensionSize = HGCellRead32(extension + 4);

        /* TACU is Nintendo's user-extended cell-attribute block. */
        if (HGCellRead32(extension) != 0x55434154u ||
            extensionSize < 16 ||
            extensionSize > size - extendedOffset ||
            HGCellRead16(extension + 8) != count)
            return NULL;

        attributeCount = HGCellRead16(extension + 10);
        attributeArray = HGCellRead32(extension + 12);

        if (!attributeCount ||
            attributeArray < 8 ||
            attributeArray > extensionSize - 8 ||
            count > (extensionSize - 8 - attributeArray) / 4)
            return NULL;

        attrArrayOffset = 8 + attributeArray;

        for (n = 0; n < count; ++n) {
            u32 relative = HGCellRead32(
                extension + attrArrayOffset + n * 4);
            u32 offset;

            if (relative > extensionSize - 8)
                return NULL;

            offset = 8 + relative;

            if (offset < attrArrayOffset + count * 4 ||
                attributeCount >
                    (extensionSize - offset) / sizeof(u32))
                return NULL;
        }

        if (extendedOffset < oamEnd)
            oamEnd = extendedOffset;
    }

    if (oamEnd < oamOffset)
        return NULL;

    allocation = sizeof(*bank) + (size_t)count * nativeStride;

    if (transferOffset)
        allocation += sizeof(NNSG2dVramTransferData)
            + (size_t)count * sizeof(NNSG2dCellVramTransferData);

    if (extendedOffset)
        allocation += sizeof(HGNativeCellAttrBlock)
            + (size_t)count * sizeof(const u32 *);

    bank = Heap_Alloc(heapID, allocation);
    if (!bank)
        return NULL;

    memset(bank, 0, allocation);
    cells = (u8 *)(bank + 1);

    for (i = 0; i < count; ++i) {
        const u8 *wire = p + cellsOffset + i * wireStride;
        NNSG2dCellData *cell =
            (NNSG2dCellData *)(cells + i * nativeStride);
        u32 numOam = HGCellRead16(wire);
        u32 relative = HGCellRead32(wire + 4);

        if (relative > oamEnd - oamOffset ||
            numOam > (oamEnd - oamOffset - relative) / 6) {
            Heap_Free(bank);
            return NULL;
        }

        cell->numOAMAttrs = (u16)numOam;
        cell->cellAttr = HGCellRead16(wire + 2);
        cell->pOamAttrArray = (NNSG2dCellOAMAttrData *)
            (p + oamOffset + relative);

        if (attributes & 1)
            memcpy(((HGNativeCellWithBR *)cell)->bounds,
                   wire + 8, 8);
    }

    bank->numCells = (u16)count;
    bank->cellBankAttr = (u16)attributes;
    bank->pCellDataArrayHead = (NNSG2dCellData *)cells;
    bank->mappingMode = (NNSG2dCharacterDataMapingType)mapping;

    cursor = cells + (size_t)count * nativeStride;

    if (transferOffset) {
        NNSG2dVramTransferData *transfer =
            (NNSG2dVramTransferData *)cursor;
        NNSG2dCellVramTransferData *records =
            (NNSG2dCellVramTransferData *)(transfer + 1);
        const u8 *wire =
            p + transferOffset + arrayOffset;

        transfer->szByteMax = maximum;
        transfer->pCellTransferDataArray = records;

        for (i = 0; i < count; ++i) {
            records[i].srcDataOffset =
                HGCellRead32(wire + i * 8);
            records[i].szByte =
                HGCellRead32(wire + i * 8 + 4);

            if (records[i].szByte > maximum) {
                Heap_Free(bank);
                return NULL;
            }
        }

        bank->pVramTransferData = transfer;
        cursor = (u8 *)(records + count);
    }

    if (extendedOffset) {
        HGNativeCellAttrBlock *ext =
            (HGNativeCellAttrBlock *)cursor;
        const u32 **references =
            (const u32 **)(ext + 1);

        ext->signature = HGCellRead32(extension);
        ext->size = (u32)(
            sizeof(*ext) + count * sizeof(*references));
        ext->attributes.numCells = (u16)count;
        ext->attributes.numAttribute = (u16)attributeCount;
        ext->attributes.pCellAttrArray = references;

        for (i = 0; i < count; ++i) {
            u32 relative = HGCellRead32(
                extension + attrArrayOffset + i * 4);

            references[i] = (const u32 *)(
                extension + 8 + relative);
        }

        bank->pExtendedData = ext;
    }

    return bank;
}
