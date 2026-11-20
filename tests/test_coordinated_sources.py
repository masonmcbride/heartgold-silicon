"""Source drift and authentic-data checks for the coordinated native batch."""
import hashlib
import importlib.util
from pathlib import Path
import re
import subprocess
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / 'upstream/pokeheartgold'
spec = importlib.util.spec_from_file_location('batch', ROOT / 'cmake/native_coordinated.py')
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)

import sys
sys.path.insert(0, str(ROOT / 'cmake'))
from native_sources import apply_pristine_compat, adapt as adapt_native


def original_words(name, following):
    asm = (GAME / 'lib/asm/nitro_sdk_data.s').read_text()
    block = asm.split(name + ':\n', 1)[1].split(following + ':', 1)[0]
    values = []
    for line in block.splitlines():
        if '.byte' in line:
            values.extend(int(n.strip(), 0) for n in line.split('.byte')[1].split(','))
    return [int.from_bytes(bytes(values[n:n+4]), 'little') for n in range(0, len(values), 4)]


class CoordinatedSources(unittest.TestCase):
    def test_shared_header_routing_preserves_local_exceptions_and_source_guards(self):
        relative = 'src/union_room_objects.c'
        original = (GAME/relative).read_text()
        edits = dict(batch.header_edits(relative, original))
        self.assertNotIn('#include "union_room_internal.h"', edits)
        self.assertNotIn('#include "union_room_talk.h"', edits)
        self.assertTrue(edits)
        for quoted, angled in edits.items():
            self.assertIn(quoted, original)
            self.assertEqual(angled, quoted.replace('"', '<', 1)[:-1]+'>')
        # A new include must not gain admission from the shared routing rule.
        with self.assertRaisesRegex(ValueError, 'source drift'):
            adapt_native(relative, original+'\n#include "script.h"\n', GAME)

    def test_battle_font_cells_have_retained_native_pointers(self):
        archive = (GAME/'files/a/0/3/5').read_bytes()
        cursor = 16
        while cursor < len(archive):
            tag, size = struct.unpack_from('<4sI', archive, cursor)
            if tag == b'BTAF':
                entries = [struct.unpack_from('<II', archive, cursor+12+i*8)
                           for i in range(struct.unpack_from('<H', archive, cursor+8)[0])]
            if tag == b'GMIF':
                assets = [archive[cursor+8+a:cursor+8+b] for a,b in entries]
            cursor += size
        self.assertEqual(len(assets), 12)
        relative = 'src/gf_gfx_loader.c'
        native = adapt_native(relative, (GAME/relative).read_text(), GAME)
        function = re.search(r'static void \*GfGfxLoader_GetCellBankInternal\([^)]*\) \{.*?\n\}', native, re.S).group(0)
        harness = r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "resource_decode.h"
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
enum HeapID { TEST_HEAP };
typedef int NNSG2dCharacterDataMapingType;
typedef struct { u16 attr0,attr1,attr2; } NNSG2dCellOAMAttrData;
typedef struct { u16 numOAMAttrs,cellAttr; NNSG2dCellOAMAttrData *pOamAttrArray; } NNSG2dCellData;
typedef struct {
    u16 numCells,cellBankAttr;
    NNSG2dCellData *pCellDataArrayHead;
    NNSG2dCharacterDataMapingType mappingMode;
    void *pVramTransferData,*pStringBank,*pExtendedData;
} NNSG2dCellDataBank;
static int live;
void *Heap_Alloc(enum HeapID heap,u32 size) { void *p=malloc(size);assert(p);++live;return p; }
void Heap_Free(void *p) { if(p) { --live;free(p); } }
'''+function+r'''
int main(int argc,char **argv) {
    assert(sizeof(NNSG2dCellDataBank)==48 && sizeof(NNSG2dCellData)==16);
    for(int a=1;a<argc;++a) {
        unsigned char bytes[4096];FILE *f=fopen(argv[a],"rb");assert(f);
        size_t size=fread(bytes,1,sizeof(bytes),f);fclose(f);
        size_t payloadSize;const u8 *p=hg_g2d_block(bytes,size,"RECN","KBEC",&payloadSize);assert(p);
        size_t count=hg_nclr_u16(p),attr=hg_nclr_u16(p+2),offset=hg_nclr_u32(p+4);
        size_t stride=(attr&1)?16:8,oam=offset+count*stride;
        void *raw=Heap_Alloc(TEST_HEAP,size);memcpy(raw,bytes,size);
        NNSG2dCellDataBank *bank;
        void *owner=GfGfxLoader_GetCellBankInternal(raw,size,TEST_HEAP,&bank);
        assert(owner && bank && live==1);
        assert((uintptr_t)bank>UINT32_MAX && (uintptr_t)bank%8==0);
        assert(bank->numCells==count && bank->cellBankAttr==attr);
        assert(!memcmp(owner,bytes,size));
        for(size_t i=0;i<count;++i) {
            NNSG2dCellData *cell=(void *)((u8 *)bank->pCellDataArrayHead+i*((attr&1)?24:16));
            const u8 *wire=p+offset+i*stride;
            assert(cell->numOAMAttrs==hg_nclr_u16(wire));
            assert(cell->cellAttr==hg_nclr_u16(wire+2));
            const u8 *expected=p+oam+hg_nclr_u32(wire+4);
            assert((u8 *)cell->pOamAttrArray==(u8 *)owner+(expected-bytes));
            assert(!memcmp(cell->pOamAttrArray,expected,cell->numOAMAttrs*6));
            if(attr&1) assert(!memcmp((u8 *)cell+16,wire+8,8));
        }
        Heap_Free(owner);assert(!live);
        /* A truncated owner and an invalid OAM offset must be rejected and freed. */
        raw=Heap_Alloc(TEST_HEAP,size);memcpy(raw,bytes,size);
        assert(!GfGfxLoader_GetCellBankInternal(raw,size-1,TEST_HEAP,&bank) && !bank && !live);
        raw=Heap_Alloc(TEST_HEAP,size);memcpy(raw,bytes,size);
        memset((u8 *)raw+(p-bytes)+offset+4,255,4);
        assert(!GfGfxLoader_GetCellBankInternal(raw,size,TEST_HEAP,&bank) && !bank && !live);
    }
}
'''
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            fixtures = []
            for i,asset in enumerate(assets):
                path = work/f'font-{i}.ncer'
                path.write_bytes(asset)
                fixtures.append(str(path))
            # The same public getter also serves standard cells (8-byte wire
            # records), so exercise both name-entry banks alongside the fonts.
            fixtures.extend(str(GAME/'files/data/namein'/f'namein_{i:08d}.NCER')
                            for i in (12, 13))
            (work/'probe.c').write_text(harness)
            subprocess.run(['clang', '-Werror', '-fsanitize=address,undefined',
                            '-I'+str(ROOT/'hardware_drivers/g2d'), str(work/'probe.c'),
                            '-o', str(work/'probe')], check=True)
            subprocess.run([str(work/'probe'), *fixtures], check=True)

    def test_signpost_frame_loads_real_asset_extent(self):
        archive = (GAME/'files/a/0/3/6').read_bytes()
        cursor = 16
        while cursor < len(archive):
            tag, size = struct.unpack_from('<4sI', archive, cursor)
            if tag == b'BTAF':
                start, end = struct.unpack_from('<II', archive, cursor+12)
            if tag == b'GMIF':
                frame = archive[cursor+8+start:cursor+8+end]
            cursor += size
        relative = 'src/render_window_icons.c'
        native = adapt_native(relative, (GAME/relative).read_text(), GAME)
        function = re.search(r'void LoadMapSignpostFrameAndGraphic\(.*?\n\}', native, re.S).group(0)
        harness = r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "resource_decode.h"
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int BOOL;
typedef int BgConfig;
typedef int GFBgLayer;
enum HeapID { HEAP_TEST };
#define FALSE 0
#define NARC_a_0_3_6 0
typedef struct { void *pRawData; } NNSG2dPaletteData;
static unsigned char asset[4096], vram[4096], colors[512];
static size_t length;
static NNSG2dPaletteData palette={colors};
static u16 graphicTile;
u32 GfGfxLoader_LoadCharData(int narc,int member,BgConfig *bg,GFBgLayer layer,
        u32 tile,u32 size,BOOL compressed,enum HeapID heap) {
    HG_NCGR_View view;
    assert(hg_ncgr_decode(asset,length,&view));
    if(!size) size=view.size;
    /* Same bounds contract as the production loader. */
    assert(size<=view.size);
    memcpy(vram+tile*32,view.pixels,size);
    return size;
}
void *GfGfxLoader_GetPlttData(int narc,int member,NNSG2dPaletteData **p,enum HeapID heap) {
    *p=&palette;return colors;
}
void BG_LoadPlttData(u32 bg,const void *data,u16 size,u16 offset) {
    assert(data==colors+32);assert(size==32);assert(offset==9*32);
}
void Heap_FreeExplicit(enum HeapID heap,void *data) {}
void LoadMapSignpostGraphic(BgConfig *bg,u32 layer,u16 tile,BOOL type,u16 map,enum HeapID heap) {
    graphicTile=tile;
}
'''+function+r'''
int main(int argc,char **argv) {
    FILE *f=fopen(argv[1],"rb");assert(f);
    length=fread(asset,1,sizeof(asset),f);fclose(f);
    memset(vram,0xa5,sizeof(vram));
    LoadMapSignpostFrameAndGraphic(0,3,2,9,1,29,HEAP_TEST);
    HG_NCGR_View view;assert(hg_ncgr_decode(asset,length,&view));
    assert(view.size==18*32);
    assert(!memcmp(vram+64,view.pixels,view.size));
    assert(vram[64+view.size]==0xa5);
    assert(graphicTile==2+30);
}
'''
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work/'frame.ncgr').write_bytes(frame)
            (work/'probe.c').write_text(harness)
            subprocess.run(['clang', '-Werror', '-I'+str(ROOT/'hardware_drivers/g2d'),
                            str(work/'probe.c'), '-o', str(work/'probe')], check=True)
            subprocess.run([str(work/'probe'), str(work/'frame.ncgr')], check=True)

    def test_native_script_backward_call_and_jump(self):
        relative = 'src/scrcmd_c.c'
        original = apply_pristine_compat(relative, (GAME / relative).read_text())
        native = adapt_native(relative, original, GAME)
        functions = '\n'.join(re.search(
            r'BOOL ' + name + r'\(ScriptContext \*ctx\) \{.*?\n\}',
            native, re.S).group(0) for name in ('ScrCmd_Call', 'ScrCmd_GoTo'))
        # Run actual adapted handlers on both directions; do not dereference a
        # bad target, so the historical failure is a deterministic assertion.
        harness = r'''
#include <stdint.h>
#include <assert.h>
typedef uint32_t u32;
typedef int32_t s32;
typedef int BOOL;
#define FALSE 0
typedef struct { const unsigned char *script_ptr, *ret; } ScriptContext;
u32 ScriptReadWord(ScriptContext *ctx) {
    const unsigned char *p = ctx->script_ptr;
    ctx->script_ptr += 4;
    return (u32)p[0] | (u32)p[1]<<8 | (u32)p[2]<<16 | (u32)p[3]<<24;
}
void ScriptJump(ScriptContext *ctx, const unsigned char *p) { ctx->script_ptr=p; }
void ScriptCall(ScriptContext *ctx, const unsigned char *p) {
    ctx->ret=ctx->script_ptr; ctx->script_ptr=p;
}
'''+functions+r'''
int main(void) {
    unsigned char code[64]={0};
    for (int delta=-24; delta<=24; delta+=48) {
        u32 bits=(u32)delta;
        for(int i=0;i<4;i++) code[28+i]=(unsigned char)(bits>>(i*8));
        ScriptContext ctx={code+28,0};
        ScrCmd_Call(&ctx);
        assert(ctx.ret==code+32);
        assert(ctx.script_ptr==code+32+delta);
        ctx.script_ptr=code+28;
        ScrCmd_GoTo(&ctx);
        assert(ctx.script_ptr==code+32+delta);
    }
}
'''
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'script.c'
            executable = Path(directory)/'script'
            source.write_text(harness)
            subprocess.run(['clang', '-Werror', str(source), '-o', str(executable)], check=True)
            subprocess.run([str(executable)], check=True)

    def test_fail_closed_and_reproducible(self):
        for relative, record in batch.SOURCES.items():
            original = apply_pristine_compat(relative, (GAME / relative).read_text())
            self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), record['sha256'])
            first = batch.adapt(relative, original)
            self.assertEqual(first, batch.adapt(relative, original))
            with self.assertRaises(ValueError):
                batch.adapt(relative, original + '\n')

    def test_mb_fragment_guards(self):
        for name in ('mb_cache', 'mb_task_thread', 'mb_parent_send_block', 'mb_read_segment',
                     'mb_parent_data', 'mb_parent_send_data'):
            relative = 'lib/NitroSDK/src/mb/' + name + '.c'
            original = (GAME / relative).read_text()
            record = batch.SOURCES[relative]
            saved = record['edits']
            try:
                for i, (old, new) in enumerate(saved):
                    record['edits'] = saved[:i] + [(old + ' changed guard', new)] + saved[i+1:]
                    with self.assertRaisesRegex(ValueError, 'fragment changed'):
                        batch.adapt(relative, original)
            finally:
                record['edits'] = saved

    def test_field_protection_boundary_only(self):
        relative = 'src/field/fieldmap.c'
        original = (GAME / relative).read_text()
        adapted = batch.adapt(relative, original)
        # The complete source must be recoverable by removing ONLY the three
        # native platform guards; no fake status or field-state operation added.
        restored = adapted.replace('#ifndef SDK_PORT\n', '').replace('\n#endif /* original DS cartridge protection instrumentation */', '')
        self.assertEqual(restored, original)
        self.assertEqual(adapted.count('#ifndef SDK_PORT'), 3)
        self.assertIn('FieldSystem_InitBottomScreen(fieldSystem);', adapted)
        self.assertIn('fieldSystem->runningFieldMap = TRUE;', adapted)
        self.assertIn('(*state)++;', adapted)

    def test_original_msl_generation(self):
        first = ''
        for relative in batch.RUNTIME_INPUTS:
            original = (GAME / relative).read_text()
            output = batch.runtime_source(relative, original)
            self.assertEqual(output, batch.runtime_source(relative, original))
            with self.assertRaises(ValueError):
                batch.runtime_source(relative, original + '\n')
            first += output
        self.assertIn('u32 NTR_StrToU32(', first)
        self.assertIn('void NTR_QSort(', first)
        self.assertNotIn('u32 strtoul(', first)
        self.assertNotIn('void qsort(', first)
        self.assertIn('NTR_Digit[128]', first)
        self.assertIn('__upper_mapC[128]', first)
        for relative, expected in batch.RUNTIME_INPUTS.items():
            self.assertEqual(hashlib.sha256((GAME / relative).read_bytes()).hexdigest(), expected)

    def test_md5_tables_are_original(self):
        spec = importlib.util.spec_from_file_location(
            "native_hash1", ROOT / "cmake/native_hash1.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        original = (GAME / "lib/NitroSDK/src/dgt_hash.c").read_text()
        asm = (GAME / "lib/asm/nitro_sdk_data.s").read_text()
        implementation = module.generate(original, asm)

        self.assertEqual(implementation, module.generate(original, asm))
        for name, next_name, length in [
            ("gDgtHash1MessageOrder", "gDgtHash1Constants", 48),
            ("gDgtHash1Constants", "_02110E6C", 64),
        ]:
            expected = original_words(name, next_name)
            marker = name + "[] = {"
            self.assertEqual(implementation.count(marker), 1)
            table = implementation.split(marker, 1)[1].split("}", 1)[0]
            actual = [int(n.strip(), 0) for n in table.split(",")
                      if n.strip()]
            self.assertEqual(len(expected), length)
            self.assertEqual(actual, expected)

        self.assertIn(
            "static void ProcessBlock(struct DGTHash1Context *context) {",
            implementation)
        self.assertIn("context->a += a;", implementation)
        self.assertIn("HG_DGT_Hash1SetSource32", implementation)
        self.assertIn("unsigned long length", implementation)
        self.assertNotIn("void DGT_Hash2Reset(", implementation)



if __name__ == '__main__':
    unittest.main()
