"""Verify original MI contract and sound alias against the emitted SDK archive."""
import argparse
import json
from pathlib import Path
import re
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', type=Path, required=True)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--compiler', required=True)
a = p.parse_args()
root, build = a.root.resolve(), a.build.resolve()
work = build / 'linker-contracts'
work.mkdir(parents=True, exist_ok=True)
game = root / 'upstream/pokeheartgold'
order = json.loads((game / 'tools/nitro-section-renames/nitro_link_order.json').read_text())
def find_rodata(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'rodata' and isinstance(child, list):
                yield child
            yield from find_rodata(child)
    elif isinstance(value, list):
        for child in value:
            yield from find_rodata(child)
assert any(any(items[i:i+2] == [
    {'path': 'lib/asm/nitro_sdk_data.o', 'selector': '.rodata.alias_d750'},
    {'path': 'lib/NitroSDK/src/snd/SND_util.o', 'selector': '.rodata.snd_decibel'}]
    for i in range(len(items)-1)) for items in find_rodata(order))
assembly = (game / 'lib/asm/nitro_sdk_data.s').read_text()
assert re.search(r'\.section \.rodata.alias_d750,4,1,2\s+\.public _0210D750\s+_0210D750:\s+\.section', assembly)
def table(path):
    text = path.read_text()
    body = re.search(r'const s16 SNDi_DecibelTable\[[^]]+\] = \{(.*?)\};', text, re.S)[1]
    return [int(n) for n in re.findall(r'-?\d+', body)]
expected = table(game / 'lib/NitroSDK/src/snd/SND_util.c')
assert len(expected) == 128
assert expected == table(root / 'upstream/libntr/libraries/snd/src/snd_util.c')
(work / 'decibel_expected.h').write_text('static const int16_t expected_decibels[128] = {' + ','.join(map(str, expected)) + '};\n')
command = [a.compiler, '-arch', 'arm64', '-O2', '-fsanitize=address,undefined',
           '-fno-sanitize-recover=all', '-I' + str(work),
           str(root / 'tests/test_linker_contracts.c'),
           str(build / 'native/lib/NitroSDK/src/mi/mi_clear_fast.c'),
           str(build / 'libntr/libntr_snd.a'), '-Wl,-dead_strip',
           '-Wl,-alias,_SNDi_DecibelTable,__0210D750', '-o', str(work / 'contracts')]
subprocess.run(command, check=True)
subprocess.run([str(work / 'contracts')], check=True)
