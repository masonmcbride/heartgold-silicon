#!/usr/bin/env python3
"""Explicit, per-file native build adaptations of the pinned original sources.

No upstream writes. Every caller supplies one input and one deterministic output;
unknown files and changed expected fragments fail instead of silently drifting.
"""
import argparse
import hashlib
from pathlib import Path
import re
import importlib.util

_batch_spec = importlib.util.spec_from_file_location("native_coordinated", Path(__file__).with_name("native_coordinated.py"))
coordinated = importlib.util.module_from_spec(_batch_spec)
_batch_spec.loader.exec_module(coordinated)


def replace(text, old, new, count=1):
    found = text.count(old)
    if found != count:
        raise ValueError(f"Expected {count} occurrence(s), found {found}: {old!r}")
    return text.replace(old, new)


def drop(text, declaration):
    return replace(text, declaration, "\n" * declaration.count("\n"))


def span(text, first, last):
    if text.count(first) != 1:
        raise ValueError("Changed declaration start: " + first)
    start = text.index(first)
    end = text.index(last, start) + len(last)
    return text[start:end]


def party_actions(text):
    table = span(text, "static const u32 _02101CB8[] = {", "\n};")
    entries = re.findall(r"\[(PARTY_MON_CONTEXT_MENU_[A-Z0-9_]+)\] = \(u32\)(PartyMonContextMenuAction_\w+),", table)
    if len(entries) != 30 or len({name for name, _ in entries}) != 30:
        raise ValueError("Party action table changed")
    for name, callback in entries:
        # Replace exact table entries only: Take is a prefix of TakeMail.
        table = replace(table, f"[{name}] = (u32){callback},", f"[{name}] = {name},")
    return entries, table


def callbacks(text):
    """Only the NNS sound heap's native callback payloads carry pointers."""
    text, count = re.subn(r"\bu32 (data[12])\b", r"uintptr_t \1", text)
    if count < 2:
        raise ValueError("Sound callback payload declarations changed")
    return "#include <stdint.h>\n" + text


LIBC_DECLARATIONS = {'src/lobby/lobby_char_vector_assign.cpp': ('void *memmove(void *, const void '
                                            '*, u32);',),
 'src/lobby/lobby_vector_growth.cpp': ('void *memset(void *, int, unsigned);',
                                       'void *memcpy(void *, const void *, '
                                       'unsigned);'),
 'src/lobby/ppw_lobby.cpp': ('int printf(const char *, ...);',
                             'extern "C" int strcmp(const char *, const char '
                             '*);')}

def native_libc(relative, text):
    for declaration in LIBC_DECLARATIONS[relative]:
        text = drop(text, declaration)
    if relative == "src/lobby/ppw_lobby.cpp":
        text = replace(text, "using std::va_list;", "using ::va_list;")
    headers = '#include <stdio.h>\n#include <string.h>\n'
    if relative == "src/lobby/ppw_lobby.cpp":
        headers += '#include <cstring>\n'
    return headers + text


def adapt(relative, text, root):
    if relative in coordinated.SOURCES:
        text = coordinated.adapt(relative, text)
        if relative in LIBC_DECLARATIONS:
            text = native_libc(relative, text)
        return text
    if relative == "lib/include/nnsys/g2d/g2d_CellTransferManager.h":
        return replace(text, "\nNNS_G2dInitCellTransferStateManager(", "\nint NNS_G2dInitCellTransferStateManager(")
    if relative == "src/party_menu_list_items.c":
        entries, table = party_actions(text)
        original = span(text, "static const u32 _02101CB8[] = {", "\n};")
        text = replace(text, original, table)
        dispatch = "".join(f"        [{name}] = {callback},\n" for name, callback in entries)
        return text + ("\nvoid HG_PartyMenu_InvokeAction(u32 action, PartyMenu *menu, int *state) {\n"
                       "    static const PartyMonContextMenuActionFunc actions[PARTY_MON_CONTEXT_MENU_MAX] = {\n"
                       + dispatch + "    };\n"
                       "    if (action >= PARTY_MON_CONTEXT_MENU_MAX || !actions[action]) __builtin_trap();\n"
                       "    actions[action](menu, state);\n}\n")
    if relative == "src/party_menu.c":
        for arg in ("&result", "(int *)pState"):
            text = replace(text, f"((PartyMonContextMenuActionFunc)func)(partyMenu, {arg});",
                           f"HG_PartyMenu_InvokeAction(func, partyMenu, {arg});")
        return ("struct PartyMenu;\nextern void HG_PartyMenu_InvokeAction(unsigned int, struct PartyMenu *, int *);\n"
                f'#line 1 "{root / relative}"\n' + text)
    if relative == "src/comm_state_private.h":
        text = drop(text, "typedef struct {\n    u64 x;\n    u64 mul;\n    u64 add;\n} MATHRandContext32;")
        original = (root / "src/comm_state.c").read_text()
        private = set(re.findall(r"^static\s+(?:void|BOOL|s32|int)\s+(CommState_\w+)\(", original, re.M))
        if len(private) != 77:
            raise ValueError("CommState private helper definitions changed")
        # These definitions are file-local; do not export them to satisfy bad declarations.
        for name in sorted(private):
            text, count = re.subn(r"^(?:void|BOOL|s32|int) " + name + r"\([^;\n]*;", "", text, flags=re.M)
            if count != 1:
                raise ValueError("Private CommState declaration changed: " + name)
        text = replace(text, "int DWC_Init(int);", "int DWC_Init(void *work);")
        return replace(text, '#include "global.h"', '#include "global.h"\n#include <nitro/math/rand.h>')
    if relative == "src/comm_state.c":
        text = replace(text, "    void (*const linkedStates[3])(void);\n    ARRAY_ASSIGN(linkedStates, gCommLinkedStates);",
                       "    void (*const *linkedStates)(void) = gCommLinkedStates;")
        text = replace(text, "DWC_Init(((u32)work + 31) & ~31)",
                       "DWC_Init((void *)(((uintptr_t)work + 31) & ~(uintptr_t)31))")
        return "#include <stdint.h>\n" + text
    if relative == "src/wireless_manager.c":
        checks = span(text, "typedef char WirelessWorkSizeCheck", "typedef char WirelessWorkBeaconCheck[offsetof(WirelessWork, beaconCount) == 0x1345 ? 1 : -1];")
        text = replace(text, checks, "#ifndef SDK_64BIT\n" + checks + "\n#endif")
        old = "    u32 p = (u32)buffer;\n    u32 mod;\n\n    mod = p << 27;\n    mod = mod >> 27;\n    if (mod != 0) {\n        p += 32 - mod;\n    }"
        text = replace(text, old, "    uintptr_t p = ((uintptr_t)buffer + 31) & ~(uintptr_t)31;")
        text = drop(text, "void WVR_TerminateAsync(void (*callback)(void *), void *arg);")
        return "#include <stdint.h>\n" + text
    if relative == "src/comm_wireless.c":
        check = "typedef char CommWirelessWorkSizeCheck[sizeof(CommWirelessWork) == 0xD98 ? 1 : -1];"
        text = replace(text, check, "#ifndef SDK_64BIT\n" + check + "\n#endif")
        text = drop(text, "int WVR_StartUpAsync(int mode, void (*callback)(void *, int), void *arg);\nint WVR_TerminateAsync(void (*callback)(void *), void *arg);")
        wrappers = ("\nstatic void HG_WVR_StartCallback(void *arg, WVRResult result) {\n"
                    "    CommWireless_OnStartedUp(arg, result != WVR_RESULT_SUCCESS);\n}\n"
                    "static void HG_WVR_TerminateCallback(void *arg, WVRResult result) {\n"
                    "    if (result != WVR_RESULT_SUCCESS) { OS_Terminate(); return; }\n"
                    "    CommWireless_OnTerminated(arg);\n}\n")
        text = replace(text, "static void CommWireless_OnTerminated(void *unused);",
                       "static void CommWireless_OnTerminated(void *unused);" + wrappers)
        text = replace(text, "WVR_StartUpAsync(8, CommWireless_OnStartedUp, NULL) != 1",
                       "WVR_StartUpAsync(8, HG_WVR_StartCallback, NULL) != WVR_RESULT_OPERATING")
        text = replace(text, "WVR_TerminateAsync(CommWireless_OnTerminated, NULL)",
                       "WVR_TerminateAsync(HG_WVR_TerminateCallback, NULL)")
        text = replace(text, "misalignment = (u32)buffer & 0x1F;", "misalignment = (u32)((uintptr_t)buffer & 0x1F);")
        return "#include <stdint.h>\n" + text
    if relative == "src/code_entry.c":
        for reg in ("REG_BLDCNT_ADDR", "REG_DB_BLDCNT_ADDR"):
            text = replace(text, f"G2x_SetBlendAlpha_({reg},", f"G2x_SetBlendAlpha_((u64){reg},")
        return text
    if relative == "src/spin_trade_link.c":
        return drop(text, "u32 MATH_CountPopulation(u32 value);")
    if relative in ("include/drawing_session_link_internal.h", "include/record_mixing/record_mixing_link_internal.h", "lib/include/nitro/wm/wm_internal.h"):
        declaration = {"include/drawing_session_link_internal.h": "int MATH_CountPopulation(u32);",
                       "include/record_mixing/record_mixing_link_internal.h": "u32 MATH_CountPopulation(u32);",
                       "lib/include/nitro/wm/wm_internal.h": "int MATH_CountPopulation(u32 value);"}[relative]
        return drop(text, declaration)
    if relative == "include/field/field_fog.h":
        return drop(text, "void G3X_SetFogTable(u32 *fogTable);")
    if relative == "lib/include/nnsys/g3d_render_internal.h":
        for name in ("G3X_GetClipMtx", "G3X_GetVectorMtx"):
            text = drop(text, f"u32 {name}(void *dst);")
        return text
    if relative in ("lib/NitroSystem/src/gfd_vram_transfer_manager.c", "lib/NitroSystem/src/g3d_kernel.c"):
        names = ["GX_LoadTex", "GX_LoadTexPltt"]
        if relative.endswith("gfd_vram_transfer_manager.c"):
            names += ["GX_LoadClearImageColor", "GX_LoadClearImageDepth"]
        for name in names:
            text = replace(text, f"void {name}(void *src,", f"void {name}(const void *src,")
        return text
    if relative in ("lib/NitroSystem/src/g2d_char_canvas.c", "lib/NitroSystem/src/g2d_char_canvas_util.c", "lib/NitroSystem/src/g2d_canvas_arrange.c"):
        return replace(text, "asm { clz x, x }", "x = x ? __builtin_clz((unsigned int)x) : 32;")
    if relative == "src/save_fashion.c":
        text = drop(text, "void MATHi_CRC32InitTableRev(u32 *table, u32 polynomial);")
        text = drop(text, "u32 MATH_CalcCRC32(const u32 *table, const void *data, u32 size);")
        text = replace(text, "    u32 table[256];", "    MATHCRC32Table storage;\n    MATHCRC32Table *table = &storage;")
        return text
    if relative == "src/screen_fade_effects.c":
        return drop(text, "static inline int GX_IsHBlank(void) {\n    return reg_GX_DISPSTAT & REG_GX_DISPSTAT_HBLK_MASK;\n}")
    if relative == "lib/include/nitro/os/ownerInfo.h":
        if hashlib.sha256(text.encode()).hexdigest() != "6d2be5a4fc3b525bab2fbccbe9491e64aee4ff4206b479e958b1fac51452e67d":
            raise ValueError("Original owner-info declarations changed")
        return ("#ifndef NITRO_OS_OWNERINFO_H_\n#define NITRO_OS_OWNERINFO_H_\n#include <stddef.h>\n"
                "#include <nitro/os/common/ownerInfo.h>\n"
                '_Static_assert(sizeof(OSBirthday) == 2 && sizeof(OSOwnerInfo) == 84, "DS owner data sizes");\n'
                '_Static_assert(offsetof(OSOwnerInfo, birthday) == 2 && offsetof(OSOwnerInfo, nickName) == 4, "DS owner fields");\n'
                '_Static_assert(offsetof(OSOwnerInfo, nickNameLength) == 26 && offsetof(OSOwnerInfo, comment) == 28 && offsetof(OSOwnerInfo, commentLength) == 82, "DS owner text offsets");\n'
                "#endif\n")
    if relative == "include/orbit_cursor.h":
        checks = span(text, "typedef char AssertTouchSpriteSize", "typedef char AssertTouchTask[(offsetof(OrbitCursor, task) == 0xF4) ? 1 : -1];")
        native = ('_Static_assert(offsetof(OrbitCursor, sprites) % _Alignof(OrbitCursorSprite) == 0, "Native sprite alignment");\n'
                  '_Static_assert(offsetof(OrbitCursor, task) % _Alignof(void *) == 0, "Native task pointer alignment");')
        return replace(text, checks, "#ifndef SDK_64BIT\n" + checks + "\n#else\n" + native + "\n#endif")
    if relative == "lib/NitroDWC/src/tree-iterator4.h":
        text = replace(text, "typedef char DwcTreeIteratorSize4[sizeof(Iterator)==4?1:-1];",
                       'typedef char DwcTreeIteratorNativeSize[sizeof(Iterator)==sizeof(void*)?1:-1];')
        return text
    if relative in SOUND_FILES:
        text = callbacks(text)
        if relative.endswith("snd_internal.h"):
            pm = span(text, "typedef struct PmSleepCallback {", "} PmSleepCallback;")
            text = replace(text, pm, "typedef PMSleepCallbackInfo PmSleepCallback;")
            for name in ("PM_PrependPreSleepCallback", "PM_AppendPostSleepCallback", "PM_DeletePreSleepCallback", "PM_DeletePostSleepCallback"):
                text = drop(text, f"void {name}(PmSleepCallback *info);")
            driver = '#define SND_DRIVER_INFO_SIZE 0x11E0\n\ntypedef struct SndDriverInfo {\n    u8 data[SND_DRIVER_INFO_SIZE];\n} SndDriverInfo;'
            text = replace(text, driver, '#define SND_DRIVER_INFO_SIZE sizeof(SNDDriverInfo)\ntypedef SNDDriverInfo SndDriverInfo;')
            for declaration in SOUND_DECLARATIONS:
                text = drop(text, declaration)
        elif relative.endswith("snd_arc_internal.h"):
            text = drop(text, "void SND_AssignWaveArc(void *bank, int index, void *waveArc);")
            text = replace(text, "} SndHeapBlock;", "} __attribute__((aligned(32))) SndHeapBlock;")
            text += ('\n_Static_assert(sizeof(SndHeapBlock) % 32 == 0 && _Alignof(SndHeapBlock) == 32, "Sound payload alignment");\n'
                     '_Static_assert(sizeof(((SndHeapBlock *)0)->data1) == sizeof(uintptr_t), "Sound callback pointer width");\n')
        elif relative.endswith("snd_arc_strm_internal.h"):
            for first, last, alias in (("typedef struct SndInstPos {", "} SndInstPos;", "typedef SNDInstPos SndInstPos;"),
                                       ("typedef struct SndInstData {", "} SndInstData;", "typedef SNDInstData SndInstData;")):
                text = replace(text, span(text, first, last), alias)
            for declaration in WAVE_DECLARATIONS:
                text = drop(text, declaration)
            text += ('\n_Static_assert(sizeof(SNDInstPos) == 8 && sizeof(SNDInstData) == 12, "DS instrument data widths");\n'
                     '_Static_assert(__builtin_offsetof(SNDInstData, param.wave[0]) == 2 && __builtin_offsetof(SNDInstData, param.wave[1]) == 4, "DS instrument wave fields");\n')
        elif relative.endswith("snd_arc_loader_wave.c"):
            text = replace(text, "instData.waveNo", "instData.param.wave[0]")
            text = replace(text, "instData.waveArcIdx", "instData.param.wave[1]")
            text = replace(text, "start = (u32)SND_GetWaveDataAddress(table, index);", "start = SND_GetWaveDataAddress(table, index) != NULL;")
        elif relative.endswith("snd_heap.c"):
            text = replace(text, "u32 alignedAddr = (u32)buffer + 3;", "uintptr_t alignedAddr = (uintptr_t)buffer + _Alignof(struct NNSSndHeap) - 1;")
            text = replace(text, "u8 *start = (u8 *)(alignedAddr & ~3);", "u8 *start = (u8 *)(alignedAddr & ~((uintptr_t)_Alignof(struct NNSSndHeap) - 1));")
        text = re.sub(r"\(u32\)(arc|table)\b", r"(uintptr_t)\1", text)
        return text
    if relative in ("lib/NitroSystem/src/snd_system.c", "lib/NitroSystem/src/snd_stream.c"):
        text = replace(text, "preSleep.func", "preSleep.callback")
        return replace(text, "postSleep.func", "postSleep.callback")
    raise ValueError("No native adaptation is registered for " + relative)


SOUND_DECLARATIONS = (
    "const void *SND_RecvCommandReply(u32 flags);",
    "void SND_ReadDriverInfo(SndDriverInfo *info);",
    "BOOL SND_ReadChannelInfo(const SndDriverInfo *driverInfo, int chNo, SNDChannelInfo *chInfo);",
    "BOOL SND_ReadTrackInfo(const SndDriverInfo *driverInfo, int playerNo, int trackNo, SNDTrackInfo *trackInfo);",
    "u16 SND_GetChannelStatus(void);", "int SND_GetPlayerLocalVariable(u32 playerNo, int varNo);",
    "void SND_SetOutputSelector(s32 left, s32 right, s32 channel1, s32 channel3);",
    "void SND_SetupChannelPcm(s32 chNo, s32 format, const void *data, s32 loopMode, s32 loopStart, s32 dataLen, s32 volume, s32 shift, s32 timer, s32 pan);",
    "void SND_SetChannelVolume(u32 chBitMask, s32 volume, s32 shift);",
    "void SND_PrepareSeq(s32 playerNo, const void *seqBase, u32 seqOffset, void *bank);",
)
WAVE_DECLARATIONS = (
    "void SND_DestroyBank(void *bank);", "void SND_DestroyWaveArc(void *waveArc);",
    "u32 SND_GetWaveDataCount(const void *waveArc);", "const void *SND_GetWaveDataAddress(const void *waveArc, int index);",
    "void SND_SetWaveDataAddress(void *waveArc, int index, const void *waveData);",
    "SndInstPos SND_GetFirstInstDataPos(const void *bank);",
    "BOOL SND_GetNextInstData(const void *bank, SndInstData *instData, SndInstPos *instPos);",
)
SOUND_FILES = {"lib/include/nnsys/" + name + ".h" for name in ("snd_internal", "snd_arc_internal", "snd_arc_strm_internal")}
SOUND_FILES.update("lib/NitroSystem/src/" + name + ".c" for name in ("snd_heap", "snd_arc", "snd_arc_loader", "snd_arc_loader_wave", "snd_player"))


def asset_types(kind, text, source):
    if kind == "zukan-template":
        # In ARM assembler syntax @ begins a comment, so ELF object types use %.
        return replace(text, ", @object", ", %object", count=12)
    if kind == "ppark-types":
        declaration = span(text, "enum PalParkEncounterType {", "#define PPMONDAT_OFFSET_LAND_SECTOR")
        declaration = declaration[:declaration.rindex("#define PPMONDAT_OFFSET_LAND_SECTOR")]
        return ("typedef unsigned char u8;\n" + declaration
                + '_Static_assert(sizeof(struct PalParkMonsData) == 6, "DS Pal Park data");\n')
    if kind == "resdat-types":
        header = (source.parent / "sprite_resource_header.h").read_text()
        declarations = [
            span(text, "typedef enum GF_GraphicsResourceType {", "} GfGfxResType;"),
            span(text, "typedef struct GF_2DGfxResHeaderNarc {", "} GF_2DGfxResHeaderNarc;"),
            span(text, "typedef struct GF_2DGfxResHeaderNarcList {", "} GF_2DGfxResHeaderNarcList;"),
            span(header, "struct ResdatNarcEntry {", "};"),
        ]
        return ("typedef unsigned int u32;\ntypedef int BOOL;\n#define TRUE 1\n#define FALSE 0\n"
                + "\n".join(declarations)
                + '\n_Static_assert(sizeof(GfGfxResType) == 4 && sizeof(GF_2DGfxResHeaderNarc) == 24, "DS resource records");\n'
                + '_Static_assert(__builtin_offsetof(GF_2DGfxResHeaderNarcList, internal) == 4, "DS resource list");\n'
                + '_Static_assert(sizeof(struct ResdatNarcEntry) == 32, "DS resource entry");\n')
    if kind == "o2narc-reader":
        if hashlib.sha256(text.encode()).hexdigest() != "a98edd26a38234f4bf1000756568ebe1e4c0823786cff7b44bf5cbe85f7ba3a8":
            raise ValueError("Original ELF reader changed")
        start = text.index("void Elf::open(")
        end = text.index("Elf::~Elf()", start)
        return "#include <memory>\n#include <cstdint>\n" + text[:start] + ELF_OPEN + "\n" + text[end:]
    raise ValueError("Unknown asset adaptation kind: " + kind)


ELF_OPEN = """void Elf::open(const string &filename, ios::openmode openmode) {
    ELF_ASSERT(!handle.is_open() && strtab == nullptr && shstrtab == nullptr);
    handle.open(filename, openmode);
    ELF_ASSERT(handle.good());
    handle.seekg(0, ios::end);
    const streamoff file_size = handle.tellg();
    ELF_ASSERT(file_size >= static_cast<streamoff>(sizeof(Elf32_Ehdr)));
    handle.seekg(0);
    handle.read(reinterpret_cast<char *>(&ehdr), sizeof(ehdr));
    ELF_ASSERT(handle.good());
    ELF_ASSERT(memcmp(ehdr.e_ident, ELFMAG, SELFMAG) == 0);
    ELF_ASSERT(ehdr.e_ident[EI_CLASS] == ELFCLASS32);
    ELF_ASSERT(ehdr.e_ident[EI_DATA] == ELFDATA2LSB);
    ELF_ASSERT(ehdr.e_ident[EI_VERSION] == EV_CURRENT);
    ELF_ASSERT(ehdr.e_ehsize == sizeof(Elf32_Ehdr));
    ELF_ASSERT(ehdr.e_shentsize == sizeof(Elf32_Shdr));
    ELF_ASSERT(ehdr.e_shnum != 0 && ehdr.e_shstrndx < ehdr.e_shnum);
    ELF_ASSERT(uint64_t(ehdr.e_shoff) + uint64_t(ehdr.e_shnum) * sizeof(Elf32_Shdr) <= uint64_t(file_size));
    shdr.resize(ehdr.e_shnum);
    handle.seekg(ehdr.e_shoff);
    handle.read(reinterpret_cast<char *>(shdr.data()), shdr.size() * sizeof(Elf32_Shdr));
    ELF_ASSERT(handle.good());
    for (const auto &section : shdr) {
        if (section.sh_type != SHT_NOBITS)
            ELF_ASSERT(uint64_t(section.sh_offset) + section.sh_size <= uint64_t(file_size));
    }

    auto strings = [&](const Elf32_Shdr &section) {
        ELF_ASSERT(section.sh_type == SHT_STRTAB && section.sh_size != 0);
        std::unique_ptr<char[]> data(new char[section.sh_size]);
        handle.seekg(section.sh_offset);
        handle.read(data.get(), section.sh_size);
        ELF_ASSERT(handle.good());
        ELF_ASSERT(data[0] == 0 && data[section.sh_size - 1] == 0);
        return data;
    };
    const auto &section_strings = shdr[ehdr.e_shstrndx];
    auto section_names = strings(section_strings);
    const Elf32_Shdr *symbols = nullptr;
    for (const auto &section : shdr) {
        ELF_ASSERT(section.sh_name < section_strings.sh_size);
        ELF_ASSERT(memchr(section_names.get() + section.sh_name, 0, section_strings.sh_size - section.sh_name));
        if (section.sh_type == SHT_SYMTAB) {
            ELF_ASSERT(symbols == nullptr);
            symbols = &section;
        }
    }
    ELF_ASSERT(symbols != nullptr && symbols->sh_link < shdr.size());
    ELF_ASSERT(symbols->sh_entsize == sizeof(Elf32_Sym) && symbols->sh_size % sizeof(Elf32_Sym) == 0);
    const auto &symbol_strings = shdr[symbols->sh_link];
    // Even when both names use one ELF section, own two separate allocations:
    // the original Elf destructor independently deletes strtab and shstrtab.
    auto symbol_names = strings(symbol_strings);
    sym.resize(symbols->sh_size / sizeof(Elf32_Sym));
    handle.seekg(symbols->sh_offset);
    handle.read(reinterpret_cast<char *>(sym.data()), symbols->sh_size);
    ELF_ASSERT(handle.good());
    for (const auto &symbol : sym) {
        ELF_ASSERT(symbol.st_name < symbol_strings.sh_size);
        ELF_ASSERT(memchr(symbol_names.get() + symbol.st_name, 0, symbol_strings.sh_size - symbol.st_name));
        if (ELF32_ST_TYPE(symbol.st_info) == STT_OBJECT)
            ELF_ASSERT(symbol.st_shndx < shdr.size());
    }
    shstrtab = section_names.release();
    strtab = symbol_names.release();
}
"""


def write_if_changed(path, data):
    if path.exists() and path.read_text() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--kind", default="native")
    args = parser.parse_args()
    root, source = args.root.resolve(), args.input.resolve()
    if args.output.resolve().is_relative_to(root):
        raise ValueError("Native outputs must not overwrite original upstream files")
    original = source.read_text()
    if args.kind == "native":
        result = adapt(source.relative_to(root).as_posix(), original, root)
    else:
        result = asset_types(args.kind, original, source)
    write_if_changed(args.output, f'#line 1 "{source}"\n' + result)


if __name__ == "__main__":
    main()
