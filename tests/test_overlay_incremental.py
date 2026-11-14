"""Exercise the production contract/link declarations with real Mach-O archives."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--generator', default='Ninja')
p.add_argument('--baseline-dir', type=Path)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
work = a.build.resolve() / ('overlay-incremental-' + ('baseline-' if a.baseline_dir else '')
                            + a.generator.replace(' ', '-'))
source, binary = work / 'source', work / 'binary'
source.mkdir(parents=True, exist_ok=True)
binary.mkdir(parents=True, exist_ok=True)
cmake_source = ((a.baseline_dir / 'baseline-overlays.cmake') if a.baseline_dir
                else root / 'cmake/native_overlays.cmake').read_text()
# Reuse the actual production declarations, rather than a model of their edges.
start = cmake_source.index('foreach(id IN LISTS hg_selected_overlay_ids)\n    list(APPEND hg_interface_outputs')
end = cmake_source.index('# OVY_0 original-code partial provider:', start)
contract_rule = cmake_source[start:end]
start = cmake_source.index('foreach(id IN LISTS hg_selected_overlay_ids)\n    list(APPEND hg_native_image_targets')
end = cmake_source.index('    if(id EQUAL 45)', start)
link_rule = cmake_source[start:end] + 'endforeach()\n'
shutil.copyfile((a.baseline_dir / 'baseline-link.py') if a.baseline_dir else root / 'cmake/native_overlay_link.py',
                source / 'native_overlay_link.py')
shutil.copyfile(root / 'cmake/native_provider_registry.py', source / 'native_provider_registry.py')
(source / 'empty.c').write_text('/* no resident imports in this fixture */\n')
(source / 'main.c').write_text('int main_provider(void){return 11;}\n'
                               'int DWC_GetMyAID(void){return 0;}\n'
                               'void DWC_ProcessFriendsMatch(void){}\n')
(source / 'overlay_1.c').write_text('extern int b(void), main_provider(void);\n'
                                    'int a(void){return b()+main_provider();}\n')
initial_b = 'int b(void){return 7;}\n'
initial_c = 'int c(void){return 3;}\n'
(source / 'overlay_2.c').write_text(initial_b)
(source / 'overlay_3.c').write_text(initial_c)
(source / 'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.30)
project(overlay_incremental C)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(overlay_link_dir "${PROJECT_BINARY_DIR}/native-overlays")
set(overlay_imports "${overlay_link_dir}/imports.rsp")
set(overlay_exports "${overlay_link_dir}/main-exports.txt")
set(overlay_contracts "${overlay_link_dir}/providers.json")
set(overlay_registry "${overlay_link_dir}/provider-registry.json")
set(hg_interface_outputs "${overlay_link_dir}/interfaces/main.tbd")
set(hg_selected_overlay_ids 1 2 3)
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/native-graph")
file(WRITE "${PROJECT_BINARY_DIR}/native-graph/images.json"
 "{\\"images\\":{\\"OVY_1\\":{\\"id\\":1,\\"kind\\":\\"Overlay\\"},\\"OVY_2\\":{\\"id\\":2,\\"kind\\":\\"Overlay\\"},\\"OVY_3\\":{\\"id\\":3,\\"kind\\":\\"Overlay\\"}}}")
add_library(hg_dwc_main STATIC main.c)
add_library(hg_ovy0_wifi_code OBJECT empty.c)
add_library(hg_dwc_status_code OBJECT empty.c)
set(overlay_link_args --main "$<TARGET_FILE:hg_dwc_main>")
set(overlay_link_dependencies hg_dwc_main "$<TARGET_FILE:hg_dwc_main>")
foreach(id IN LISTS hg_selected_overlay_ids)
 add_library(archive_${id} STATIC overlay_${id}.c)
 set(hg_overlay_${id}_archive archive_${id})
 list(APPEND overlay_link_args --overlay "${id}=$<TARGET_FILE:archive_${id}>")
 list(APPEND overlay_link_dependencies archive_${id} "$<TARGET_FILE:archive_${id}>")
endforeach()
''' + contract_rule + link_rule)
log = work / 'commands.log'
log.write_text('')

def run(cmd, check=True):
    begin = time.monotonic()
    r = subprocess.run(list(map(str, cmd)), text=True, capture_output=True)
    elapsed = time.monotonic() - begin
    with log.open('a') as f:
        f.write(json.dumps(list(map(str, cmd))) + '\n' + r.stdout + r.stderr)
    if check and r.returncode:
        raise AssertionError(r.stdout + r.stderr)
    return r, elapsed

run(['cmake', '-S', source, '-B', binary, '-G', a.generator,
     '-DPython3_EXECUTABLE=' + sys.executable])

def images():
    return {p.name: p.stat().st_mtime_ns for p in (binary / 'native-overlays').glob('*.dylib')}

def artifacts():
    out = binary / 'native-overlays'
    files = [*out.glob('interfaces/*.tbd'), *out.glob('image_*.rsp'),
             *(out / name for name in ['imports.rsp', 'main-exports.txt', 'providers.json', 'provider-registry.json'])]
    return {str(p.relative_to(out)): hashlib.sha256(
        p.read_text().replace(str(binary), '<binary>').encode()).hexdigest() for p in files}

results = {}

def write_source(name, text):
    # Apple's system Make compares timestamps at whole-second resolution.
    if a.generator == 'Unix Makefiles':
        time.sleep(1.05)
    (source / name).write_text(text)

def build(name, expected, ok=True):
    before = images()
    witness = binary / 'native-overlays' / ('interfaces/main.tbd' if a.baseline_dir else 'contracts.stamp')
    previous_validation = witness.stat().st_mtime_ns if witness.exists() else None
    r, elapsed = run(['cmake', '--build', binary, '-j8'], check=ok)
    after = images()
    linked = sorted(p for p in after if before.get(p) != after[p])
    if ok:
        assert linked == [f'libheartgold_image_{i}.dylib' for i in expected], (name, linked, r.stdout)
        if name == 'noop' or name.endswith('_noop'):
            assert witness.stat().st_mtime_ns == previous_validation, 'no-op reran global validation'
    else:
        assert r.returncode and not linked, (name, r.stdout, r.stderr)
        assert 'Competing strong providers' in r.stdout + r.stderr
    results[name] = dict(seconds=elapsed, relinks=linked, artifacts=artifacts(), returncode=r.returncode)

all_images = [1, 2, 3]
conservative = a.baseline_dir is not None or a.generator != 'Ninja'
build('cold', all_images)
build('noop', [])

def verify_runtime(expected):
    # The executable must extract main's dynamic exports, just as production
    # does; an unreferenced static archive member is insufficient for dyld.
    (source / 'driver.c').write_text(f'extern int a(void); int main(void){{return a()!={expected};}}\n')
    run(['cc', source / 'driver.c', binary / 'libhg_dwc_main.a',
         *(binary / 'native-overlays' / f'libheartgold_image_{i}.dylib' for i in all_images),
         '-Wl,-exported_symbols_list,' + str(binary / 'native-overlays/main-exports.txt'),
         '-Wl,-export_dynamic,-rpath,' + str(binary / 'native-overlays'), '-o', binary / 'heartgold'])
    run([binary / 'heartgold'])

verify_runtime(18)
# A generated record must enumerate and hash every input named by its rsp.
if not a.baseline_dir:
    out = binary / 'native-overlays'
    for ident in all_images:
        rsp = out / f'image_{ident}.rsp'
        record = json.loads((out / f'image_{ident}.link.json').read_text())
        expected = [rsp, *(Path(json.loads(line)) for line in rsp.read_text().splitlines())]
        assert record == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in expected}

write_source('overlay_2.c', 'int b(void){return 9;}\n')
build('implementation', all_images if conservative else [2])
assert results['cold']['artifacts'] == results['implementation']['artifacts']
build('implementation_noop', [])
verify_runtime(20)
write_source('overlay_2.c', 'int b(void){return 9;} int extra(void){return 4;}\n')
build('export', all_images if conservative else [1, 2])
build('export_noop', [])
verify_runtime(20)
write_source('overlay_1.c', 'extern int b(void), c(void), main_provider(void);\n'
             'int a(void){return b()+c()+main_provider();}\n')
build('import', all_images if conservative else [1])
build('import_noop', [])
verify_runtime(23)
write_source('overlay_2.c', 'int extra(void){return 4;}\n')
write_source('overlay_3.c', 'int c(void){return 3;} int b(void){return 9;}\n')
build('ownership', all_images)
build('ownership_noop', [])
verify_runtime(23)
# Validation failure must not release waiting link targets or advance success.
stamp = binary / 'native-overlays/contracts.stamp'
old_stamp = stamp.stat().st_mtime_ns if stamp.exists() else None
write_source('overlay_2.c', 'int b(void){return 1;}\n')
build('duplicate_rejected', [], ok=False)
if old_stamp is not None:
    assert stamp.stat().st_mtime_ns == old_stamp
write_source('overlay_2.c', 'int extra(void){return 4;}\n')
build('repaired', all_images if conservative else [2])
build('repaired_noop', [])
# Ninja must recover deleted content-stable byproducts; Make retains the original
# multi-output fallback for precisely this reason.
if a.generator == 'Unix Makefiles':
    time.sleep(1.05)
(binary / 'native-overlays/interfaces/image_3.tbd').unlink()
build('missing_interface', all_images if conservative else [])
build('missing_interface_noop', [])
results['image_bytes'] = {p.name: p.stat().st_size for p in (binary / 'native-overlays').glob('*.dylib')}
(work / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps({k: {x: v[x] for x in ('seconds', 'relinks')} for k, v in results.items()
                  if isinstance(v, dict) and 'seconds' in v}, indent=2))
