"""ASan/UBSan regression of the generated original multiboot functions."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--compiler', required=True)
a = p.parse_args()
root, build = a.root.resolve(), a.build.resolve()
spec = importlib.util.spec_from_file_location('native', root / 'cmake/native_sources.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
out = build / 'mb-native'
out.mkdir(parents=True, exist_ok=True)
from audit_overlays import arguments
entries = json.loads((build / 'compile_commands.json').read_text())
entry = next(e for e in entries if e['file'].endswith('/src/intro_movie.c'))
flags = [flag for flag in arguments(entry)[1:] if flag not in ('-fsyntax-only', '-ferror-limit=0')]
flags += ['-I' + str(root / 'hardware_drivers/wireless'), '-O1', '-g', '-UNDEBUG', '-fsanitize=address,undefined', '-fno-sanitize-recover=all']
# The shared API must reject a callback with the reconstructed no-argument ABI.
bad = out / 'bad-task-callback.c'
bad.write_text('#include "mb_native.h"\nvoid wrong(void) {}\n'
               'void submit(Task *task) { MBi_SetTask(task, wrong, 0, 4); }\n')
rejected = subprocess.run([a.compiler, *flags, '-Werror=incompatible-function-pointer-types',
                           '-fsyntax-only', str(bad)], capture_output=True, text=True)
assert rejected.returncode and 'incompatible function pointer' in rejected.stderr, rejected.stderr
bad.write_text('#include "mb_native.h"\n'
               'void MBi_SendFixedBeacon(uint16_t, uint32_t, uint32_t);\n')
rejected = subprocess.run([a.compiler, *flags, '-fsyntax-only', str(bad)],
                          capture_output=True, text=True)
assert rejected.returncode and 'conflicting types' in rejected.stderr, rejected.stderr

# Input pins and the final typedef-removal guards still fail closed.
for name in ('mb_task_piece_buffer', 'mb_task_thread', 'mb_parent_send_block'):
    relative = 'lib/NitroSDK/src/mb/' + name + '.c'
    game = root / 'upstream/pokeheartgold'
    original = (game / relative).read_text()
    try:
        native.adapt(relative, original + '\n', game)
    except ValueError as error:
        assert 'source drift' in str(error), str(error)
    else:
        raise AssertionError('Changed original MB source accepted')
    record = native.coordinated.SOURCES[relative]
    saved = record['edits']
    record['edits'] = [(old + ' changed typedef' if '} Task;' in old and not new else old, new)
                       for old, new in saved]
    try:
        native.adapt(relative, original, game)
    except ValueError as error:
        assert 'fragment changed' in str(error), str(error)
    else:
        raise AssertionError('Missing original Task typedef accepted')
    finally:
        record['edits'] = saved

objects = []
for name in ['mb_beacon_fixed', 'mb_beacon_volat', 'mb_beacon_volat_init',
             'mb_task_piece_buffer', 'mb_cache', 'mb_task_thread', 'mb_download_info', 'mb_parent_recv_child',
             'mb_init', 'mb_parent_start_end', 'mb_parent_comm', 'mb_wm_callbacks', 'mb_parent_data', 'mb_read_segment', 'mb_parent_util', 'mb_wm_error']:
    rel = 'lib/NitroSDK/src/mb/' + name + '.c'
    game = root / 'upstream/pokeheartgold'
    source = out / (name + '.c')
    source.write_text(native.adapt(rel, (game / rel).read_text(), game))
    obj = source.with_suffix('.o')
    # Unoptimized beacon definitions expose callee-side argument narrowing that
    # an optimizer may elide across these separately compiled ABI boundaries.
    beacon_flags = ['-O0'] if name in ('mb_beacon_fixed', 'mb_beacon_volat') else []
    subprocess.run([a.compiler, *flags, *beacon_flags, '-c', str(source), '-o', str(obj)], check=True)
    # Compile the actual task definition against the shared header. The runtime
    # fixture supplies task services separately and does not execute this queue.
    if name != 'mb_task_piece_buffer':
        objects.append(str(obj))
trap_obj = out / 'unexpected.o'
subprocess.run([a.compiler, '-O1', '-g', '-fsanitize=address,undefined', '-c',
                str(root / 'tests/mb_native_unexpected.c'), '-o', str(trap_obj)], check=True)
exe = out / 'test_mb'
subprocess.run([a.compiler, *flags, str(root / 'tests/test_mb_native.c'),
                str(root / 'hardware_drivers/wireless/mb_native.c'), str(trap_obj), *objects,
                '-Wl,-dead_strip', '-o', str(exe)], check=True)
subprocess.run([str(exe)], check=True)
