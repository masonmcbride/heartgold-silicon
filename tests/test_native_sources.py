"""Focused regressions for source-validated native representation changes."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "upstream/pokeheartgold"
WORK = None
spec = importlib.util.spec_from_file_location("native_sources", ROOT / "cmake/native_sources.py")
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def semantic_adapt(relative, original):
    result = native.adapt(relative, original, GAME)
    for quoted, angled in native.coordinated.header_edits(relative, native.apply_pristine_compat(relative, original)):
        result = result.replace(angled, quoted)
    return result


def expected_common_storage(relative, text):
    if relative == 'lib/NitroDWC/src/net_common.c':
        text = text.replace('MI_CpuFill8(&p, 0, 12);', 'MI_CpuFill8(&p, 0, sizeof(p));')
        text = text.replace('DWC_Alloc(4, 7712)', 'DWC_Alloc(4, sizeof(NetAuthWork))')
        text = text.replace('MI_CpuFill8(allocated, 0, 7712)', 'MI_CpuFill8(allocated, 0, sizeof(NetAuthWork))')
        text = text.replace('DWC_Free(4, gDwcNasLoginWork, 7712)',
                            'DWC_Free(4, gDwcNasLoginWork, sizeof(NetAuthWork))')
    return text


class NativeSourceAdaptations(unittest.TestCase):
    def test_bag_heap_reservation_tracks_native_pointer_width(self):
        relative = 'src/application/bag/bag_app.c'
        original = (GAME / relative).read_text()
        adapted = native.adapt(relative, original, GAME)
        creation = re.search(r'Heap_Create\(HEAP_ID_3, HEAP_ID_6, ([^;]+)\);', adapted)[1]
        self.assertEqual(creation, '0x42000 * (sizeof(void *) / sizeof(u32))')
        fixture = '''typedef unsigned int u32;
_Static_assert(EXPRESSION == EXPECTED, "Bag heap ABI budget");
'''.replace('EXPRESSION', creation)
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            source = Path(directory)/'budget.c'
            for target, expected in [('arm64-apple-macos', 0x84000), ('armv5te-none-eabi', 0x42000)]:
                source.write_text(fixture.replace('EXPECTED', str(expected)))
                result = subprocess.run(['xcrun', 'clang', '-target', target, '-fsyntax-only', str(source)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sound_attribute_slots_own_native_handles(self):
        relative = 'src/sound.c'
        original = (GAME / relative).read_text()
        adapted = native.adapt(relative, original, GAME)
        self.assertIn(relative, native.MAIN_NATIVE_SOURCES)
        record = re.search(r'struct SND_WORK \{.*?\n\};', adapted, re.S)[0]
        getter = native.span(adapted, 'void *GF_SdatGetAttrPtr(u32 attr) {',
                             '\nint GF_Snd_SaveState').removesuffix('\nint GF_Snd_SaveState')
        fixture = '''#include <stdint.h>
#include <stddef.h>
#include <assert.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;
typedef struct { int unused; } NNSSndArc, NNSSndHandle, SOUND_CHATOT, SysTask;
typedef void *NNSSndHeapHandle;
typedef void *NNSSndWaveOutHandle;
#define SND_HEAP_SIZE 0xBEAE0
#define SND_HANDLE_MAX 9
#define FALSE 0
#define GF_ASSERT(x) assert(x)
typedef struct SND_WORK SND_WORK;
RECORD
static SND_WORK data;
static SND_WORK *GetSoundDataPointer(void) { return &data; }
GETTER
int main(void) {
    SOUND_CHATOT chatot;
    SysTask task;
    assert((uintptr_t)&task > UINT32_MAX);
    data.myChatot=&chatot;
    SysTask **slot=GF_SdatGetAttrPtr(35);
    assert(sizeof(data.cryStopTask)==sizeof(*slot));
    assert((uintptr_t)slot % _Alignof(SysTask *)==0);
    assert(*slot==NULL);
    *slot=&task; assert(data.cryStopTask==&task); assert(data.myChatot==&chatot);
    *slot=NULL; assert(data.myChatot==&chatot);
    data.queuedBankInfo=0xabc;
    NNSSndWaveOutHandle *first=GF_SdatGetAttrPtr(0), *second=GF_SdatGetAttrPtr(1);
    assert(sizeof(data.waveOut14Handle)==sizeof(*first));
    assert(sizeof(data.waveOut15Handle)==sizeof(*second));
    *first=&task; *second=&chatot;
    assert(data.waveOut14Handle==&task && data.waveOut15Handle==&chatot);
    assert(data.queuedBankInfo==0xabc);
}
'''.replace('RECORD', record).replace('GETTER', getter)
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            source, exe = Path(directory)/'sound.c', Path(directory)/'sound'
            source.write_text(fixture)
            result = subprocess.run(['xcrun', 'clang', '-std=c11', '-Wall', '-Werror',
                                     str(source), '-o', str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            subprocess.run([str(exe)], check=True, capture_output=True)

    def test_battle_owned_tasks_survive_native_teardown(self):
        header = native.adapt('include/battle/battle.h',
                              (GAME / 'include/battle/battle.h').read_text(), GAME)
        adapted = native.adapt('src/battle/battle_main.c',
                              (GAME / 'src/battle/battle_main.c').read_text(), GAME)
        names = ('drawGraphicsTask', 'criticalHpMusicTask', 'scrollBgTask')
        fields = '\n'.join(re.search(r'    SysTask \*' + name + ';', header)[0] for name in names)
        assignments = '\n'.join(re.search(r'    battleSystem->' + name + r' = [^;]+;', adapted)[0] for name in names)
        self.assertNotIn('(u32)', assignments)
        cleanup = '\n'.join(re.search(r'    SysTask_Destroy\([^;]*battleSystem->' + name + r'\);', adapted)[0] for name in names[:2])
        fixture = '''#include <stdint.h>
#include <assert.h>
typedef struct { int id; } SysTask;
typedef struct { FIELDS } BattleSystem;
#define Task_DrawBattleGraphics 0
#define Task_UpdateCriticalHpMusic 0
#define VBlankTask_ScrollBattleBackground 0
static SysTask tasks[3]; static unsigned destroyed;
static SysTask *SysTask_CreateOnMainQueue(int cb, BattleSystem *data, int priority) { (void)cb; (void)data; return &tasks[priority==60000 ? 0 : 1]; }
static SysTask *SysTask_CreateOnVBlankQueue(int cb, BattleSystem *data, int priority) { (void)cb; (void)data; (void)priority; return &tasks[2]; }
static void SysTask_Destroy(SysTask *p) { assert(p==&tasks[destroyed++]); }
int main(void) { BattleSystem system={0}, *battleSystem=&system;
    assert((uintptr_t)tasks>UINT32_MAX);
ASSIGNMENTS
    assert(system.scrollBgTask==&tasks[2]);
CLEANUP
    assert(destroyed==2);
}
'''.replace('FIELDS', fields).replace('ASSIGNMENTS', assignments).replace('CLEANUP', cleanup)
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            source, exe = Path(directory)/'tasks.c', Path(directory)/'tasks'
            source.write_text(fixture)
            result = subprocess.run(['xcrun', 'clang', '-std=c11', '-Wall', '-Werror',
                                     str(source), '-o', str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            subprocess.run([str(exe)], check=True, capture_output=True)

    def test_font_oam_sprite_array_preserves_adjacent_heap_header(self):
        relative = 'src/font_sprite.c'
        original = (GAME / relative).read_text()
        adapted = native.adapt(relative, original, GAME)
        self.assertIn(relative, native.MAIN_NATIVE_SOURCES)
        self.assertNotIn('12 * count', adapted)
        record = re.search(r'struct FontOAMSprite \{.*?\n\};', adapted, re.S)[0]
        writer = native.span(adapted, 'static void TextOBJ_CreateSprites(const TextOBJTemplate *template, FontOAMCell *list, FontSpriteData *sprites, TextOBJ *object) {',
                             '\nstatic void TextOBJ_DeleteSprites').removesuffix('\nstatic void TextOBJ_DeleteSprites')
        allocation = re.search(r'object->sprites = Heap_Alloc\(template->heapID, [^;]+;', adapted)[0]
        old_allocation = re.search(r'object->sprites = Heap_Alloc\(template->heapID, [^;]+;', original)[0]
        fixture = '''#include <stdint.h>
#include <assert.h>
#include <string.h>
typedef struct { int unused; } Sprite;
typedef struct { int heapID; } TextOBJTemplate;
typedef struct FontOAMCell { int x,y,index; struct FontOAMCell *prev,*next; } FontOAMCell;
typedef struct { int unused; } FontSpriteData;
typedef struct FontOAMSprite FontOAMSprite;
RECORD
typedef struct { FontOAMSprite *sprites; } TextOBJ;
#define GF_ASSERT(x) assert(x)
static _Alignas(8) unsigned char arena[1024];
static unsigned extent;
static void *Heap_Alloc(int heap, unsigned size) { (void)heap; extent=size; memset(arena,0xa5,sizeof arena); return arena; }
static Sprite sprite;
static Sprite *FontOAM_CreateCellSprite(const TextOBJTemplate *t, FontOAMCell *n, FontSpriteData *s) { (void)t; (void)n; (void)s; return &sprite; }
WRITER
int main(void) {
    TextOBJ obj, *object=&obj; TextOBJTemplate tmpl={5}, *template=&tmpl;
    FontOAMCell list={0}, nodes[2]={{0}}; FontSpriteData proxies[2];
    int count=2;
    list.prev=&nodes[0]; nodes[0].prev=&nodes[1]; nodes[1].prev=&list; nodes[1].x=4;
    OLD_ALLOCATION
    assert(extent==24 && sizeof(FontOAMSprite)==16);
    TextOBJ_CreateSprites(template,&list,proxies,object);
    unsigned damaged; memcpy(&damaged,arena+extent,4); assert(damaged==32);
    ALLOCATION
    assert(extent==sizeof(FontOAMSprite)*count);
    TextOBJ_CreateSprites(template,&list,proxies,object);
    assert(object->sprites[1].x==32 && object->sprites[1].sprite==&sprite);
    for (unsigned i=extent;i<sizeof arena;i++) assert(arena[i]==0xa5);
}
'''.replace('RECORD', record).replace('WRITER', writer).replace('OLD_ALLOCATION', old_allocation).replace('ALLOCATION', allocation)
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            source, exe = Path(directory)/'font.c', Path(directory)/'font'
            source.write_text(fixture)
            result = subprocess.run(['xcrun', 'clang', '-std=c11', '-Wall', '-Werror',
                                     str(source), '-o', str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            subprocess.run([str(exe)], check=True, capture_output=True)

    def test_battle_bag_page_number_window_keeps_pointer_width(self):
        relative = 'src/battle/battle_bag_menu.c'
        original = (GAME / relative).read_text()
        adapted = native.adapt(relative, original, GAME)
        self.assertIn(relative, native.OVERLAY_NATIVE_SOURCES)
        self.assertNotIn('(u32)(windows)', adapted)
        macro = re.search(r'^#define PAGE_NUMBER_WINDOW.*$', adapted, re.M)[0]
        fixture = '''#include <stdint.h>
#include <assert.h>
typedef struct { void *bg; unsigned char fields[8]; void *pixels; } Window;
MACRO
int main(void) {
    Window windows[26]={0};
    assert((uintptr_t)windows > UINT32_MAX);
    assert(PAGE_NUMBER_WINDOW(windows) == &windows[25]);
    PAGE_NUMBER_WINDOW(windows)->pixels = windows;
    assert(windows[25].pixels == windows);
}
'''.replace('MACRO', macro)
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            source, exe = Path(directory)/'bag.c', Path(directory)/'bag'
            source.write_text(fixture)
            result = subprocess.run(['xcrun', 'clang', '-std=c11', '-Wall', '-Werror',
                                     str(source), '-o', str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            subprocess.run([str(exe)], check=True, capture_output=True)

    def test_battle_input_callbacks_keep_native_function_pointers(self):
        relative = 'src/battle/battle_controller_opponent.c'
        original = (GAME / relative).read_text()
        adapted = native.adapt(relative, original, GAME)
        self.assertIn(relative, native.OVERLAY_NATIVE_SOURCES)
        self.assertNotRegex(adapted, r'inputTasks\[\d\] = \(u32\)')
        header = native.adapt('include/battle/battle.h',
                              (GAME / 'include/battle/battle.h').read_text(), GAME)
        field = re.search(r'    SysTaskFunc inputTasks\[6\];', header)[0]
        for relative in native.BATTLE_CALLBACK_HEADERS[1:]:
            result = native.adapt(relative, (GAME / relative).read_text(), GAME)
            self.assertIn('#include <battle/battle.h>', result)
            self.assertNotIn('#include "battle.h"', result)
        macros = adapted[adapted.index('#define SET_INPUT_TASKS('):
                         adapted.index('\nvoid OpponentData_SetInputTasks(')]
        groups = re.findall(r'#define (SET_\w+_INPUT_TASKS)\(opponentData\)\s+SET_INPUT_TASKS\(opponentData, ([^)]+)\)', macros)
        self.assertEqual(len(groups), 4)
        fixture = '''#include <stdint.h>
#include <assert.h>
typedef void (*SysTaskFunc)(void *, void *);
typedef struct { FIELD unsigned marker; } OpponentData;
static unsigned seen;
'''.replace('FIELD', field)
        for _, names in groups:
            for index, name in enumerate(names.split(', ')):
                fixture += f'static void {name}(void *task, void *data) {{ assert(task == data); seen={index + 1}; }}\n'
        fixture += macros + '\nint main(void) { OpponentData data={0}; data.marker=0xabc;\n'
        fixture += '_Static_assert(sizeof(data.inputTasks[0]) == sizeof(SysTaskFunc), "callback width");\n'
        for group, names in groups:
            fixture += f'{group}(&data);\n'
            for index, name in enumerate(names.split(', ')):
                fixture += f'assert((uintptr_t){name} > UINT32_MAX); assert(data.inputTasks[{index}] == {name});\n'
                fixture += f'data.inputTasks[{index}](&data, &data); assert(seen == {index + 1});\n'
        fixture += 'assert(data.marker == 0xabc); }\n'
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            source, exe = Path(directory)/'callbacks.c', Path(directory)/'callbacks'
            source.write_text(fixture)
            result = subprocess.run(['xcrun', 'clang', '-std=c11', '-Wall', '-Werror',
                                     str(source), '-o', str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            subprocess.run([str(exe)], check=True, capture_output=True)

    def test_battle_hp_bar_vram_pointer_width(self):
        relative = 'src/battle/battle_hp_bar.c'
        self.assertIn(relative, native.OVERLAY_NATIVE_SOURCES)
        original = (GAME / relative).read_text()
        adapted = native.adapt(relative, original, GAME)
        expected = '#include <stdint.h>\n' + original
        for name, count in [('vramAddr', 27), ('vramBaseAddr', 6)]:
            self.assertEqual(original.count('(u32)' + name), count)
            expected = expected.replace('(u32)' + name, '(uintptr_t)' + name)
        self.assertEqual(adapted, expected)
        self.assertNotRegex(adapted, r'\(\s*u32\s*\)\s*vram(?:Base)?Addr\b')
        # The adaptation must not apply to another source with identical text.
        with self.assertRaisesRegex(ValueError, 'No native adaptation is registered'):
            native.adapt_original('src/unrelated.c', original, GAME)
        self.assertEqual((GAME / relative).read_text(), original)

        # Execute every adapted VRAM address expression. Replace only external
        # region-table and image-proxy inputs with controlled byte offsets.
        expressions = re.findall(r'\(void \*\)\((\(uintptr_t\)vram(?:Base)?Addr[^;\n]*?baseAddrOfVram\[NNS_G2D_VRAM_TYPE_2DMAIN\])\)', adapted)
        self.assertEqual(len(expressions), 33)
        fixture = '#include <stdint.h>\n#include <assert.h>\nint main(void) {\n'
        fixture += 'void *vramAddr, *vramBaseAddr; uintptr_t base;\n'
        fixture += 'unsigned offset=0x20, imageOffset=0x1800, i=6, sizeTop=5;\n'
        for base in ('0x1011cc600ULL', '0x011cc600ULL'):
            fixture += f'base={base}; vramAddr=vramBaseAddr=(void *)base;\n'
            for expression in expressions:
                expression = re.sub(r'\b\w+(?:\[[^\]]+\])+\.offset', 'offset', expression)
                expression = expression.replace(
                    'imgProxy->vramLocation.baseAddrOfVram[NNS_G2D_VRAM_TYPE_2DMAIN]', 'imageOffset')
                delta = re.sub(r'\(uintptr_t\)vram(?:Base)?Addr', '0', expression)
                fixture += f'assert(({expression}) == base + ({delta}));\n'
        # Exact LLDB reproducer: 0x011cde20 must retain the upper 32 bits.
        fixture += 'assert((uintptr_t)(void *)0x1011cc600ULL + 0x1820 == 0x1011cde20ULL);\n}\n'
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            source, exe = Path(directory)/'hp_bar.c', Path(directory)/'hp_bar'
            source.write_text(fixture)
            result = subprocess.run(['xcrun', 'clang', '-std=c11', '-Wall', '-Werror',
                                     str(source), '-o', str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            subprocess.run([str(exe)], check=True, capture_output=True)

    def test_mailbox_icon_resources_match_archive_types(self):
        text = native.adapt('src/application/mailbox_app_sprites.c',
            (GAME/'src/application/mailbox_app_sprites.c').read_text(), GAME)
        getters = (GAME/'src/pokemon_icon_idx.c').read_text()
        icons = GAME/'files/poketool/icongra/poke_icon'
        resources = {}
        for kind, getter in re.findall(
                r'SpriteSystem_Load(Cell|Anim)ResObjFromOpenNarc\('
                r'data->spriteSystem, data->spriteManager, data->monIconNarc, '
                r'(\w+)\(\), FALSE, 0x37F0\);', text):
            index = int(re.search(r'u32 '+getter+r'\(void\)\s*\{\s*return (\d+);', getters)[1])
            data = json.loads((icons/f'poke_icon_{index:08d}.json').read_text())
            self.assertIn('cellCount' if kind=='Cell' else 'sequenceCount', data,
                          f'{kind} loader selected member {index} with the wrong asset type')
            resources[kind] = data
        self.assertEqual(set(resources), {'Cell', 'Anim'})
        # The animations must reference cells present in the selected bank.
        for result in resources['Anim']['animationResults']:
            self.assertLess(result['index'], resources['Cell']['cellCount'])

    def test_options_teardown_releases_callback_before_resources(self):
        original = (GAME / 'src/options_app.c').read_text()
        adapted = native.adapt('src/options_app.c', original, GAME)
        function = native.span(adapted,
            'static BOOL OptionsApp_Free(OptionsApp_Data *data) {',
            '\nstatic void OptionsApp_SetupBgConfig').removesuffix(
                '\nstatic void OptionsApp_SetupBgConfig')
        # Execute both original cleanup states and deliver a simulated frame
        # between them. Resource destruction fails if its callback still owns it.
        fixture = r'''
#define CHECK(condition) do { if (!(condition)) __builtin_trap(); } while (0)
#include <stddef.h>
typedef int BOOL;
#define TRUE 1
#define FALSE 0
#define MENU_ENTRY_COUNT 2
#define GX_PLANEMASK_NONE 0
typedef struct { int numStrings; void *strings[1]; } Entry;
typedef struct { int setupAndFreeState; Entry menuEntries[2]; void *msgData; } OptionsApp_Data;
static int registered=1, released, resources;
static void Main_SetVBlankIntrCB(void *cb, void *arg) { CHECK(!cb && !arg); registered=0; }
static void release(void) { CHECK(!registered); ++resources; }
#define GF_DestroyVramTransferManager() release()
#define OptionsApp_FreeWindows(x) release()
#define String_Delete(x) release()
#define DestroyMsgData(x) release()
#define OptionsApp_FreeGraphicsDummy(x) release()
#define OptionsApp_FreeBgConfig(x) do { release(); released=1; } while(0)
#define OptionsApp_FreeSpriteRenderer(x) release()
#define HBlankInterruptDisable() ((void)0)
#define GfGfx_DisableEngineAPlanes() ((void)0)
#define GfGfx_DisableEngineBPlanes() ((void)0)
#define GX_SetVisiblePlane(x) ((void)0)
#define GXS_SetVisiblePlane(x) ((void)0)
'''
        fixture += function + r'''
int main(void) {
    OptionsApp_Data data={0}; data.menuEntries[0].numStrings=1;
    CHECK(!OptionsApp_Free(&data));
    CHECK(released && resources==7 && data.setupAndFreeState==1);
    CHECK(!registered); /* A frame here must not access released resources. */
    CHECK(OptionsApp_Free(&data) && data.setupAndFreeState==0);
    CHECK(resources==7);
}
'''
        from audit_overlays import arguments
        entries = json.loads((WORK / 'compile_commands.json').read_text())
        entry = next(e for e in entries if e['file'].endswith('/src/intro_movie.c'))
        flags = arguments(entry)
        flags.remove('-fsyntax-only')
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            source, exe = Path(directory)/'cleanup.c', Path(directory)/'cleanup'
            source.write_text(fixture)
            result = subprocess.run(flags + ['-UNDEBUG', str(source), '-o', str(exe)],
                cwd=entry['directory'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            subprocess.run([str(exe)], check=True, capture_output=True)
        exit_code = native.span(adapted, 'BOOL OptionsMenu_Exit(', '\nBOOL OptionsMenu_Main(')
        self.assertIn('enum HeapID heapID = data->heapID;', exit_code)
        self.assertNotIn('Heap_Destroy(data->heapID)', exit_code)

    def test_startup_queue_alignment_is_native(self):
        original=(GAME/'src/system.c').read_text()
        adapted=native.adapt('src/system.c',original,GAME)
        calls=re.findall(r'SysTaskQueue_PlacementNew\((\d+), OS_AllocFromArenaLo\(OS_ARENA_MAIN, SysTaskQueue_GetArenaSize\(\1\), (_Alignof\(SysTaskQueue\))\)\)',adapted)
        self.assertEqual([count for count,_ in calls],['160','32','32','4'])

    def test_explicit_compiler_arithmetic_operations(self):
        for relative, (_, declaration, old, new) in native.COMPILER_OPERATIONS.items():
            original = (GAME / relative).read_text()
            adapted = semantic_adapt(relative, original)
            self.assertNotIn(declaration, adapted)
            self.assertNotIn(old, adapted)
            self.assertEqual(adapted.count(new), 1)
            # The only additional edit in disc catch is its existing qsort declaration.
            expected = original.replace(declaration, "").replace(old, new)
            if relative in native.QSORT_DECLARATIONS:
                expected = expected.replace(native.QSORT_DECLARATIONS[relative], "#include <nitro/math/qsort.h>")
            self.assertEqual(adapted, expected)
            with self.assertRaisesRegex(ValueError, 'Compiler arithmetic source drift'):
                native.adapt(relative, original + "\n", GAME)

    def test_eight_case_adaptations(self):
        relative = 'src/application/pokedex/pokedex_main_seq.c'
        original = (GAME / relative).read_text()
        old = '\nPokedexApp_MainSeq_62(PokedexAppData *pokedexApp) {'
        self.assertEqual(semantic_adapt(relative, original), original.replace(old, '\nstatic int PokedexApp_MainSeq_62(PokedexAppData *pokedexApp) {'))
        for changed in (original.replace(old, old.replace('PokedexAppData', 'void')),
                        original.replace('static int PokedexApp_MainSeq_62(', 'static void PokedexApp_MainSeq_62('),
                        original.replace('[POKEDEXAPP_MAINSEQ_62] = PokedexApp_MainSeq_62,', '/* drift */')):
            with self.assertRaises(ValueError):
                native.adapt(relative, changed, GAME)
        relative = 'src/field/weather_manager.c'
        original = (GAME / relative).read_text()
        expected = original
        for table in ('sSnowFallSpeeds', 'sSnowSlowdownIntervals'):
            expected = expected.replace('static const ' + table + '[]', 'static const int ' + table + '[]')
        expected = expected.replace('int table0[4];', 'const int *table0;').replace('int table1[4];', 'const int *table1;')
        expected = expected.replace(
            'files.paletteFile = NARC_AllocAndReadWholeMember(weatherSystem->narc, weatherSystem->bgGfx[bgGfxId].paletteId, HEAP_ID_FIELD1);\n        NNS_G2dGetUnpackedPaletteData(files.paletteFile, &files.paletteData);',
            'files.paletteFile = GfGfxLoader_GetPlttDataFromOpenNarc(weatherSystem->narc, weatherSystem->bgGfx[bgGfxId].paletteId, &files.paletteData, HEAP_ID_FIELD1);')
        expected = expected.replace(
            'files.charFile = NARC_AllocAndReadWholeMember(weatherSystem->narc, weatherSystem->bgGfx[bgGfxId].charId, HEAP_ID_FIELD1);\n        NNS_G2dGetUnpackedCharacterData(files.charFile, &files.charData);',
            'files.charFile = GfGfxLoader_GetCharDataFromOpenNarc(weatherSystem->narc, weatherSystem->bgGfx[bgGfxId].charId, FALSE, &files.charData, HEAP_ID_FIELD1);')
        self.assertEqual(semantic_adapt(relative, original), expected)
        for fragment in ('2, 2, 2, 2', '16, 32, 16, 10', 'int table0[4]', 'table1[index]', 'table0[index]'):
            with self.assertRaises(ValueError):
                native.adapt(relative, original.replace(fragment, fragment + ' /* drift */'), GAME)
        for relative, callback in native.SINIT_CALLBACKS.items():
            original = (GAME / relative).read_text()
            before = ('#pragma define_section SINIT ".sinit" abs32 RWX\n#pragma section SINIT begin\n'
                      'SDK_FORCE_EXPORT static void (*NitroStaticInit_[])(void) = { ' + callback + ' };\n#pragma section SINIT end')
            after = ('SDK_FORCE_EXPORT static void (*NitroStaticInit_[])(void) '
                     '__attribute__((section("__DATA,__ntr_sinit"))) = { ' + callback + ' };')
            result = semantic_adapt(relative, original)
            self.assertNotIn(before, result)
            self.assertEqual(result.count(after), 1)
            for changed in (original.replace('{ ' + callback + ' };', '{ OtherCallback };'),
                            original.replace('".sinit"', '".changed"'), original + '\n' + before):
                with self.assertRaises(ValueError):
                    native.adapt(relative, changed, GAME)

    def test_sdk_force_export_native_retention(self):
        code = ('#include <nitro/types.h>\n'
                'volatile int observed;\n'
                'static void callback(void) { ++observed; }\n'
                'SDK_FORCE_EXPORT static void (*NitroStaticInit_[])(void) '
                '__attribute__((section("__DATA,__ntr_sinit"))) = { callback };\n')
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            obj = Path(directory) / 'sinit.o'
            subprocess.run(['clang', '-x', 'c', '-O2', '-DSDK_PORT', '-DSDK_AARCH64', '-DSDK_64BIT',
                '-DSDK_CW_FORCE_EXPORT_SUPPORT', '-I' + str(ROOT / 'upstream/libntr/include'),
                '-c', '-', '-o', str(obj)], input=code, text=True, capture_output=True, check=True)
            symbols = subprocess.run(['nm', '-m', str(obj)], text=True, capture_output=True, check=True).stdout
            line = next(line for line in symbols.splitlines() if line.endswith('_NitroStaticInit_'))
            self.assertIn('__ntr_sinit', line)
            self.assertIn('no dead strip', line)
            self.assertIn('_callback', symbols)

    def test_original_alignment_contract(self):
        code = ('#include <cw/function_target.h>\n'
                'ALIGN(4) static const unsigned char a[3] = {1,2,3};\n'
                'static const ALIGN(4) short b[2] = {1,2};\n'
                '_Static_assert(__alignof__(a) == 4, "file storage alignment");\n'
                '_Static_assert(__alignof__(b) == 4, "inline placement alignment");\n'
                'void f(void) { ALIGN(4) static const unsigned short c[2] = {1,2};\n'
                '_Static_assert(__alignof__(c) == 4, "block static alignment"); }\n')
        subprocess.run(['clang', '-x', 'c', '-std=c11', '-I' + str(GAME / 'lib/include'), '-fsyntax-only', '-'],
                       input=code, text=True, capture_output=True, check=True)

    def test_private_function_declarations(self):
        self.assertEqual(len(native.PRIVATE_FUNCTIONS), 5)
        self.assertEqual(sum(len(entries) for _, entries in native.PRIVATE_FUNCTIONS.values()), 103)
        for relative, (header, declarations) in native.PRIVATE_FUNCTIONS.items():
            original = (GAME / relative).read_text()
            result = semantic_adapt(relative, original)
            include = '#include "' + header.removeprefix('include/') + '"'
            forwards = ['static ' + prototype for prototype, state in declarations if state == 'needed']
            expected = original.replace(include, include + '\n\n' + '\n'.join(forwards)) if forwards else original
            self.assertEqual(result, expected)  # All bodies, calls and tables unchanged.
            with self.assertRaises(ValueError):
                native.adapt(relative, original.replace(include, '/* changed include */'), GAME)
            for prototype, state in declarations:
                definition = 'static ' + prototype[:-1] + ' {'
                self.assertEqual(result.count('static ' + prototype), int(state != 'none'))
                self.assertEqual(result.count(definition), 1)
                for changed in (original.replace(definition, prototype[:-1] + ' {'),
                                original.replace(definition, definition + '\n}\n' + definition)):
                    with self.assertRaises(ValueError):
                        native.adapt(relative, changed, GAME)
                if state == 'existing':
                    with self.assertRaises(ValueError):
                        native.adapt(relative, original.replace('static ' + prototype, prototype), GAME)
                else:
                    # A new use before a formerly self-declaring definition, or
                    # an unexpected forward, must trigger a source review.
                    with self.assertRaises(ValueError):
                        native.adapt(relative, original + '\nstatic ' + prototype, GAME)
                    if state == 'none':
                        name = re.search(r'\b(\w+)\(', prototype)[1]
                        with self.assertRaises(ValueError):
                            native.adapt(relative, '// ' + name + '\n' + original, GAME)
        for header in {entry[0] for entry in native.PRIVATE_FUNCTIONS.values()}:
            original = (GAME / header).read_text()
            expected = original
            for candidate, declarations in native.PRIVATE_FUNCTIONS.values():
                if candidate != header:
                    continue
                for prototype, _ in declarations:
                    expected = native.drop(expected, prototype)
                    for changed in (original.replace(prototype, '/* changed prototype */'),
                                    original + '\n' + prototype):
                        with self.assertRaises(ValueError):
                            native.adapt(header, changed, GAME)
            self.assertEqual(semantic_adapt(header, original), expected)

    def test_three_source_interfaces(self):
        relative = 'lib/NitroDWC/src/http_engine_request.c'
        original = (GAME / relative).read_text()
        declaration = 'extern int STD_CompareNString(const char *a, const char *b, u32 n);'
        self.assertEqual(native.adapt(relative, original, GAME),
                         original.replace(declaration, '#include <nitro/std/string.h>'))
        for changed in (original.replace(declaration, '/* drift */'),
                        original.replace('sStr_returncd_4, 8)', 'sStr_returncd_4, n)'),
                        original + '\nint other(void) { return NdEngine_StrNCmp(a, b, n); }',
                        original.replace('STD_CompareNString(a, b, n)', 'STD_CompareNString(a, b, n + 1)')):
            with self.assertRaises(ValueError):
                native.adapt(relative, changed, GAME)
        relative = 'src/lobby/ppw_lobby.cpp'
        original = (GAME / relative).read_text()
        result = native.adapt(relative, original, GAME)
        self.assertIn('using ::va_list;', result)
        with self.assertRaises(ValueError):
            native.adapt(relative, original.replace('using std::va_list;', '/* drift */'), GAME)
        subprocess.run(['clang++', '-x', 'c++', '-fsyntax-only', '-'],
            input='#include <stdarg.h>\nusing ::va_list;\n'
                  'void f(int n, ...) { va_list args; va_start(args, n); va_end(args); }\n',
            text=True, capture_output=True, check=True)
        relative = 'src/voice_chat.c'
        original = (GAME / relative).read_text()
        declarations = (
            'extern void MIC_StartAutoSamplingAsync(MICAutoParam *param, void (*callback)(MICResult, void *), void *arg);',
            'extern u8 *MIC_GetLastSamplingAddress(void);',
            'extern void MIC_StopAutoSampling(void);')
        expected = original
        for declaration in declarations:
            expected = native.drop(expected, declaration)
            with self.assertRaises(ValueError):
                native.adapt(relative, original.replace(declaration, '/* drift */'), GAME)
        old = '    if ((u32)(MIC_GetLastSamplingAddress() - address) < size) {'
        expected = expected.replace(old, '    u8 *lastSamplingAddress = MIC_GetLastSamplingAddress();\n'
                                        '    if ((u32)(lastSamplingAddress - address) < size) {')
        result = native.adapt(relative, original, GAME)
        self.assertIn('#include <nitro/spi/ARM9/mic.h>', result)
        self.assertIn('u8 *lastSamplingAddress = MIC_GetLastSamplingAddress();', result)
        self.assertIn('if ((u32)(lastSamplingAddress - address) < size)', result)
        self.assertIn('VoiceChat_AllocAligned(&allocation,', result)
        self.assertNotIn('(u32)*allocation', result)
        self.assertEqual(result.count('count * (8 * HG_VCT_NATIVE_SLOT_SIZE) + 32'), 2)
        with self.assertRaises(ValueError):
            native.adapt(relative, original.replace(old, '/* drift */'), GAME)

    def test_sdk_interface_declarations(self):
        for relative, declarations in native.PRINTF_DECLARATIONS.items():
            original = (GAME / relative).read_text()
            expected = native.native_libc(relative, original) if relative in native.LIBC_DECLARATIONS else original
            for declaration in declarations:
                expected = native.drop(expected, declaration)
                with self.assertRaises(ValueError):
                    native.adapt(relative, original.replace(declaration, '/* declaration changed */'), GAME)
            self.assertEqual(native._adapt(relative, original, GAME),
                             '#include <nitro/os/common/printf.h>\n' + expected)
        for relative in ('lib/include/vct/vct_audio_internal.h', 'lib/include/nitro/wm/wm_internal.h'):
            original = (GAME / relative).read_text()
            declaration = 'int MATH_CountPopulation(u32 value);'
            self.assertEqual(native.adapt(relative, original, GAME), native.drop(original, declaration))
            with self.assertRaises(ValueError):
                native.adapt(relative, original.replace(declaration, '/* declaration changed */'), GAME)

    def test_iterator_layout_in_c_cpp_and_ds(self):
        relative = "lib/NitroDWC/src/tree-iterator4.h"
        original = (GAME / relative).read_text()
        adapted = native.adapt(relative, original, GAME)
        self.assertIn("#ifndef SDK_64BIT\n" + "typedef char DwcTreeIteratorSize4[sizeof(Iterator)==4?1:-1];", adapted)
        with self.assertRaisesRegex(ValueError, "Iterator layout changed"):
            native.adapt(relative, original.replace("void *current;", "void *current; int extra;"), GAME)
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            header = Path(directory) / "iterator.h"
            header.write_text(adapted)
            for language in ("c", "c++"):
                for target in (["-DSDK_64BIT"], ["-target", "armv5te-none-eabi"]):
                    subprocess.run(["/usr/bin/clang", "-x", language, *target,
                        "-fsyntax-only", str(header)], check=True, capture_output=True)

    def test_native_libc_declarations_are_exact_and_calls_unchanged(self):
        for relative, declarations in native.LIBC_DECLARATIONS.items():
            original = (GAME / relative).read_text()
            expected = native.coordinated.adapt(relative, original) if relative in native.coordinated.SOURCES else original
            for declaration in declarations:
                expected = native.drop(expected, declaration)
            prepared = native.coordinated.adapt(relative, original) if relative in native.coordinated.SOURCES else original
            result = native.native_libc(relative, prepared)
            if relative == 'src/lobby/ppw_lobby.cpp':
                expected = native.replace(expected, 'using std::va_list;', 'using ::va_list;')
            headers = '#include <stdio.h>\n#include <string.h>\n'
            if relative == 'src/lobby/ppw_lobby.cpp':
                headers += '#include <cstring>\n'
            expected = headers + expected
            self.assertEqual(result, expected)
            with self.assertRaises(ValueError):
                native.adapt(relative, original.replace(declarations[0], "/* changed declaration */", 1), GAME)
        # Compile and run genuine native libc calls with fortification still on.
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            for language, suffix in (("c", ".c"), ("c++", ".cpp")):
                source = Path(directory) / ("libc" + suffix)
                relative = "lib/NitroDWC/src/gt_socket.c"
                text = "\n".join(native.LIBC_DECLARATIONS[relative])
                source.write_text(native.native_libc(relative, text) + r"""
#if _FORTIFY_SOURCE != 2
#error Fortification must remain enabled
#endif
#ifndef __cplusplus
#ifndef sprintf
#error Darwin C sprintf fortification macro must remain enabled
#endif
#endif
int main(void) {
    char data[32];
    memset(data, 0, sizeof(data));
    sprintf(data, "%s:%d", "native", 64);
    if (strncmp(data, "native:64", sizeof(data))) return 1;
    memmove(data + 1, data, 10);
    return memcmp(data + 1, "native:64", 10) != 0;
}
""")
                exe = Path(directory) / ("libc-" + language)
                subprocess.run(["/usr/bin/clang", "-x", language, "-O2", "-D_FORTIFY_SOURCE=2",
                    str(source), "-o", str(exe)], check=True, capture_output=True)
                subprocess.run([str(exe)], check=True, capture_output=True)

    def test_wifi_archive_layout_and_actual_allocation(self):
        relative = "include/wifi_setup/wifi_setup_ui.h"
        original = (GAME / relative).read_text()
        adapted = native.adapt(relative, original, GAME)
        self.assertIn("#ifndef SDK_64BIT\n    u8 unk_88[", adapted)
        with self.assertRaisesRegex(ValueError, "archive layout changed"):
            native.adapt(relative, original.replace("u16 lockId;", "u32 lockId;"), GAME)
        relative = "src/wifi_setup/wifi_setup_share.c"
        original = (GAME / relative).read_text()
        adapted = native.adapt(relative, original, GAME)
        old = "WifiSetupHeap_AllocZeroed(sizeof(WifiSetupArchiveState), 4)"
        self.assertEqual(adapted, original.replace(old,
            "WifiSetupHeap_AllocZeroed(sizeof(WifiSetupArchiveState), _Alignof(WifiSetupArchiveState))"))
        with self.assertRaises(ValueError):
            native.adapt(relative, original.replace(old, "changed"), GAME)
        # Use the actual native header and compile the entire adapted source to IR.
        # No heap or SDK mocks: the original heap remains a separate runtime blocker.
        from audit_overlays import arguments
        entries = json.loads((WORK / "compile_commands.json").read_text())
        entry = next(e for e in entries if e["file"].endswith("/src/intro_movie.c"))
        flags = arguments(entry)
        flags.remove("-fsyntax-only")
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            directory = Path(directory)
            source, exe = directory / "layout.c", directory / "layout"
            source.write_text(r"""
#include "wifi_setup/wifi_setup_ui.h"
#include <stdio.h>
int main(void) {
    _Static_assert(_Alignof(WifiSetupArchiveState) > 4, "ARM64 requires stronger alignment");
    _Static_assert(_Alignof(WifiSetupArchiveState) == _Alignof(FSArchive), "native state alignment");
    _Static_assert(offsetof(WifiSetupArchiveState, tables) == 0, "first field");
    _Static_assert(offsetof(WifiSetupArchiveState, filePool) % _Alignof(void*) == 0, "pool alignment");
    printf("%zu %zu\n", sizeof(WifiSetupArchiveState), _Alignof(WifiSetupArchiveState));
    return 0;
}
""")
            subprocess.run(flags + [str(source), "-o", str(exe)], cwd=entry["directory"],
                check=True, capture_output=True)
            size, alignment = map(int, subprocess.check_output([str(exe)], text=True).split())
            print(f"Native WifiSetupArchiveState: size={size}, alignment={alignment}")
            generated = WORK / "native" / relative
            ir = directory / "share.ll"
            subprocess.run(flags + ["-iquote", str((GAME / relative).parent), "-S", "-emit-llvm",
                str(generated), "-o", str(ir)], cwd=entry["directory"], check=True, capture_output=True)
            function = ir.read_text().split("define void @WifiSetupArchive_Load(", 1)[1].split("\n}", 1)[0]
            calls = re.findall(r"call ptr @WifiSetupHeap_AllocZeroed\(i32 noundef (\d+), i32 noundef (\d+)\)", function)
            self.assertEqual(tuple(map(int, calls[0])), (size, alignment))

    def test_typed_assembly_storage_is_guarded(self):
        for name, owners in native.STORAGE.items():
            source = GAME / "lib/asm" / name
            original = source.read_text()
            result = native.native_storage(original, source)
            for owner in owners.split():
                self.assertRegex(result, r"(?m)^[^\n;]*\b" + owner + r"(?:\[[^\]]*\])?;")
            self.assertNotIn(".space", result)
            if "gSndMainState" in owners:
                self.assertIn("offsetof(SndMainState, preSleep)", result)
                self.assertIn("offsetof(SndPlayerInfo, playerList.numObjects)", result)
                self.assertIn("sizeof(SndPlayerInfo)", result)
            with self.assertRaisesRegex(ValueError, "ownership changed"):
                native.native_storage(original.replace(".space 0xC", ".space 0x10", 1), source)


    def test_every_party_action_and_cancel_value(self):
        original = (GAME / "src/party_menu_list_items.c").read_text()
        result = semantic_adapt("src/party_menu_list_items.c", original)
        entries, expected = native.party_actions(original)
        self.assertEqual(len(entries), 30)
        actual = native.span(result, "static const u32 _02101CB8[] = {", "\n};")
        self.assertEqual(actual, expected)
        self.assertEqual(actual.count("= LIST_CANCEL,"), 3)
        # Take and TakeMail must remain distinct identifiers and callbacks.
        self.assertIn("[PARTY_MON_CONTEXT_MENU_TAKE_MAIL] = PARTY_MON_CONTEXT_MENU_TAKE_MAIL,", actual)
        self.assertNotIn("PARTY_MON_CONTEXT_MENU_TAKEMail", result)
        for action, callback in entries:
            self.assertIn(f"[{action}] = {callback},", result)
        # Every original callback body and the original getter are untouched.
        first, last = original.index("static const u32 _02101CB8[]"), original.index("u32 GetPartyMenuContextMenuActionFunc")
        native_first, native_last = result.index("static const u32 _02101CB8[]"), result.index("u32 GetPartyMenuContextMenuActionFunc")
        self.assertEqual(result[:native_first], original[:first])
        self.assertEqual(result[native_last:result.index("\nvoid HG_PartyMenu_InvokeAction")], original[last:])

    def test_party_source_has_only_verified_dispatch_changes(self):
        original = (GAME / "src/party_menu.c").read_text()
        result = native.adapt("src/party_menu.c", original, GAME)
        self.assertEqual(result.count("HG_PartyMenu_InvokeAction(func, partyMenu,"), 2)
        self.assertNotIn("((PartyMonContextMenuActionFunc)func)", result)

    def test_private_comm_state_helpers_stay_private(self):
        source = (GAME / "src/comm_state.c").read_text()
        original = (GAME / "include/comm_state_internal.h").read_text()
        result = native.adapt("include/comm_state_internal.h", original, GAME)
        private = set(re.findall(r"^static\s+(?:void|BOOL|s32|int)\s+(CommState_\w+)\(", source, re.M))
        self.assertEqual(len(private), 77)
        for name in private:
            self.assertNotRegex(result, rf"\b{name}\s*\(")
        self.assertIn('DWC_Init((void *)', source)
        adapted = native.adapt("src/comm_state.c", source, GAME)
        for name in private:
            self.assertRegex(adapted, rf"static\s+(?:void|BOOL|s32|int)\s+{name}\(")
        self.assertIn("((uintptr_t)work + 31) & ~(uintptr_t)31", adapted)

    def test_changed_source_is_rejected(self):
        text = (GAME / "lib/NitroSystem/src/g2d_char_canvas.c").read_text()
        with self.assertRaises(ValueError):
            native.adapt("lib/NitroSystem/src/g2d_char_canvas.c", text.replace("asm { clz x, x }", "unknown"), GAME)
        with self.assertRaises(ValueError):
            native.adapt("not-a-registered-file.c", "", GAME)
        original = (GAME / "lib/NitroSystem/src/snd_arc.c").read_text()
        with self.assertRaises(ValueError):
            native.adapt("lib/NitroSystem/src/snd_arc.c", original.replace("(u32)arc", "(void *)arc", 1), GAME)

    def test_unchanged_outputs_are_not_rewritten(self):
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            path = Path(directory) / "native.c"
            native.write_if_changed(path, "same\n")
            stamp = path.stat().st_mtime_ns
            native.write_if_changed(path, "same\n")
            self.assertEqual(path.stat().st_mtime_ns, stamp)

    def test_cli_paths_and_upstream_write_rejection(self):
        with tempfile.TemporaryDirectory(prefix='native "sources" ', dir=WORK) as directory:
            work = Path(directory)
            root = work / "original tree"
            source = root / "lib/NitroSystem/src/g2d_char_canvas.c"
            source.parent.mkdir(parents=True)
            original = (GAME / source.relative_to(root)).read_text()
            source.write_text(original)
            output = work / "build tree" / "canvas.c"
            command = [sys.executable, "-B", str(ROOT / "cmake/native_sources.py"),
                       "--root", str(root), "--input", str(source), "--output", str(output)]
            subprocess.run(command, cwd=work, check=True, capture_output=True)
            self.assertTrue(output.read_text().startswith(
                f'#line 1 {json.dumps(str(source), ensure_ascii=False)}\n'))
            stamp = output.stat().st_mtime_ns
            subprocess.run(command, cwd=work, check=True, capture_output=True)
            self.assertEqual(output.stat().st_mtime_ns, stamp)
            # An explicit destination in upstream must fail without touching it.
            command[-1] = str(source)
            failure = subprocess.run(command, cwd=work, capture_output=True, text=True)
            self.assertNotEqual(failure.returncode, 0)
            self.assertIn("must not overwrite original upstream files", failure.stderr)
            self.assertEqual(source.read_text(), original)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    args, unittest_args = parser.parse_known_args()
    WORK = args.work.resolve()
    if not WORK.is_dir():
        parser.error("--work must be an existing build directory")
    unittest.main(argv=[sys.argv[0], *unittest_args])
