"""The resident and overlay guest frontends share verified ABI corrections."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'compiler/guest32'), str(ROOT / 'cmake')]
from frontend import flags, private_overlay
from native_sources import GUEST32_PRISTINE_COMPAT, PRISTINE_COMPAT, guest32_frontend
from guest32_closure import hardware_identities

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--llvm-bin', type=Path, required=True)
a = p.parse_args()
build = a.build.resolve()
game = ROOT / 'upstream/pokeheartgold'
out = build / 'provider-frontend-tests'
out.mkdir(exist_ok=True)
records = [dict(source=s) for s in GUEST32_PRISTINE_COMPAT]
vfs, virtual = private_overlay(game, out, records)
assert set(virtual) == {str(game / s) for s in GUEST32_PRISTINE_COMPAT}
def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)

ir = {}
for relative in GUEST32_PRISTINE_COMPAT:
    source = game / relative
    text = source.read_text()
    corrected = guest32_frontend(relative, text, game)
    assert hashlib.sha256(corrected.encode()).hexdigest() == PRISTINE_COMPAT[relative]['adapted_sha256']
    assert Path(virtual[str(source)]).read_text() == corrected
    try:
        guest32_frontend(relative, text + '\n', game)
    except ValueError:
        pass
    else:
        raise AssertionError('source drift accepted: ' + relative)
    dest = out / (source.stem + '.ll')
    run([str(a.llvm_bin / 'clang'), *flags(game, build), *vfs,
         '-S', '-emit-llvm', str(source), '-o', str(dest)])
    ir[relative] = dest.read_text()

for source, callee in (
    ('src/colosseum.c', 'CommPlayerManager_GetPlayerFrontX'),
    ('src/communication_club_link.c', 'Comm_IsNetIdConnected'),
    ('src/union_room.c', 'CommState_StartAlternateSearch'),
):
    calls = re.findall(r'call [^\n]*@' + callee + r'\(([^)]*)\)', ir[source])
    assert calls and all(c.strip() and ',' not in c for c in calls), (source, calls)
    assert not re.search(r'declare [^\n]*@' + callee + r'\(\)', ir[source])

manager = ir['lib/NitroSystem/src/gfd_linked_list_tex_vram_man.c']
reset = ir['lib/NitroSystem/src/gfd_linked_list_tex_vram_man_reset.c']
assert re.search(r'@gLnkTexVramFreeList = external global ptr', manager)
assert re.search(r'@gLnkTexVramFreeList = .*global ptr', reset)
assert not re.search(r'getelementptr[^\n]*@gLnkTexVramFreeList', manager)
assert not re.search(r'getelementptr[^\n]*@gLnkTexVramFreeList', reset)

layout = out / 'layout.c'
layout.write_text('''#include <nitro.h>
#include <nnsys/gfd_internal.h>
_Static_assert(sizeof(void *) == 4, "guest pointers");
_Static_assert(sizeof(LnkVramBlock) == 16, "original block extent");
_Static_assert(sizeof(LnkTexVramManagerWork) == 20, "original work extent");
''')
run([str(a.llvm_bin / 'clang'), *flags(game, build),
     '-fsyntax-only', str(layout)])

# Admission uses present source/manifest/catalog evidence, never an old frontier.
hardware = [dict(key=name, native='guest32_' + name, params=params,
                 local=False, varargs=False, **{'return': result})
            for name, params, result in (
                ('OS_DisableInterrupts', [], 'i32'),
                ('OS_RestoreInterrupts', ['i32'], 'i32'),
                ('DC_InvalidateRange', ['ptr', 'i32'], 'void'))]
assert hardware_identities(game, hardware) == {'_' + f['native'] for f in hardware}
for incorrect in (hardware[:-1], [dict(f, params=['ptr']) for f in hardware]):
    try:
        hardware_identities(game, incorrect)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid hardware catalog accepted')
with patch('native_image_graph.parse_manifest', return_value={'main': {'objects': []}}):
    try:
        hardware_identities(game, hardware)
    except ValueError as error:
        assert 'ownership drift' in str(error)
    else:
        raise AssertionError('wrong hardware owner accepted')
with patch('guest32_closure.hashlib.sha256') as digest:
    digest.return_value.hexdigest.return_value = '0' * 64
    try:
        hardware_identities(game, hardware)
    except ValueError as error:
        assert 'source drift' in str(error)
    else:
        raise AssertionError('hardware source drift accepted')
(out / 'result.json').write_text(json.dumps(dict(
    sources=list(GUEST32_PRISTINE_COMPAT), guest_pointer_bytes=4,
    block_bytes=16, work_bytes=20, source_drift_rejected=True), indent=2) + '\n')
print('PASS: all four provider ABI failures, split manager ownership, and ARM32 layout')
