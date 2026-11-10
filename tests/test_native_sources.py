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
    for quoted, angled in native.coordinated.HEADER_ROUTES.get(relative, {}).get('edits', []):
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
        for local, table in (('table0', 'sSnowSlowdownIntervals'), ('table1', 'sSnowFallSpeeds')):
            expected = expected.replace(local + ' = ' + table + ';', 'memcpy(' + local + ', ' + table + ', sizeof(' + local + '));')
        self.assertEqual(semantic_adapt(relative, original), '#include <string.h>\n' + expected)
        for fragment in ('2, 2, 2, 2', '16, 32, 16, 10', 'int table0[4]', 'table1[index]', 'table0[index]'):
            with self.assertRaises(ValueError):
                native.adapt(relative, original.replace(fragment, fragment + ' /* drift */'), GAME)
        for relative, callback in native.SINIT_CALLBACKS.items():
            original = (GAME / relative).read_text()
            before = ('#pragma define_section SINIT ".sinit" abs32 RWX\n#pragma section SINIT begin\n'
                      'SDK_FORCE_EXPORT static void (*NitroStaticInit_[])(void) = { ' + callback + ' };\n#pragma section SINIT end')
            after = ('SDK_FORCE_EXPORT static void (*NitroStaticInit_[])(void) '
                     '__attribute__((section("__DATA,__ntr_sinit"))) = { ' + callback + ' };')
            self.assertEqual(semantic_adapt(relative, original), original.replace(before, after))
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
        self.assertEqual(native.adapt(relative, original, GAME), '#include <nitro/spi/ARM9/mic.h>\n' + expected)
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
            self.assertEqual(native.adapt(relative, original, GAME),
                             '#include <nitro/os/common/printf.h>\n' + expected_common_storage(relative, expected))
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
            result = native.adapt(relative, original, GAME)
            if relative == 'src/lobby/ppw_lobby.cpp':
                expected = native.replace(expected, 'using std::va_list;', 'using ::va_list;')
            headers = '#include <stdio.h>\n#include <string.h>\n'
            if relative == 'src/lobby/ppw_lobby.cpp':
                headers += '#include <cstring>\n'
            expected = headers + expected
            if relative in native.PRINTF_DECLARATIONS:
                for declaration in native.PRINTF_DECLARATIONS[relative]:
                    expected = native.drop(expected, declaration)
                expected = '#include <nitro/os/common/printf.h>\n' + expected
            self.assertEqual(result, expected_common_storage(relative, expected))
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
        original = (GAME / "src/comm_state_private.h").read_text()
        result = native.adapt("src/comm_state_private.h", original, GAME)
        private = set(re.findall(r"^static\s+(?:void|BOOL|s32|int)\s+(CommState_\w+)\(", source, re.M))
        self.assertEqual(len(private), 77)
        for name in private:
            self.assertNotRegex(result, rf"\b{name}\s*\(")
        self.assertIn("int DWC_Init(void *work);", result)
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
