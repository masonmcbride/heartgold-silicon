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
objects = []
for name in ['mb_cache', 'mb_task_thread', 'mb_download_info', 'mb_parent_recv_child',
             'mb_init', 'mb_parent_start_end', 'mb_parent_comm', 'mb_wm_callbacks', 'mb_parent_data', 'mb_read_segment', 'mb_parent_util', 'mb_wm_error']:
    rel = 'lib/NitroSDK/src/mb/' + name + '.c'
    game = root / 'upstream/pokeheartgold'
    source = out / (name + '.c')
    source.write_text(native.adapt(rel, (game / rel).read_text(), game))
    obj = source.with_suffix('.o')
    subprocess.run([a.compiler, *flags, '-c', str(source), '-o', str(obj)], check=True)
    objects.append(str(obj))
trap_obj = out / 'unexpected.o'
subprocess.run([a.compiler, '-O1', '-g', '-fsanitize=address,undefined', '-c',
                str(root / 'tests/mb_native_unexpected.c'), '-o', str(trap_obj)], check=True)
exe = out / 'test_mb'
subprocess.run([a.compiler, *flags, str(root / 'tests/test_mb_native.c'),
                str(root / 'hardware_drivers/wireless/mb_native.c'), str(trap_obj), *objects,
                '-Wl,-dead_strip', '-o', str(exe)], check=True)
subprocess.run([str(exe)], check=True)
