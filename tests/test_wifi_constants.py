"""Native resident bytes versus independently assembled original directives. MIT."""
import argparse
import json
import re
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'cmake'))
from native_wifi_constants import selected, RECORDS, ALIASES, SOURCE
from native_data_ir import parse, raw_layout
from native_assembly_data import read_object, validate_object
from link_symbols import image_groups


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'build', 'object', 'compiler', 'objcopy', 'readelf'):
        p.add_argument('--'+name, required=True, type=Path)
    a = p.parse_args()
    out = a.build/'wifi-constants'
    out.mkdir(parents=True, exist_ok=True)
    blocks, evidence = selected(a.game)
    assert image_groups(a.game)['lib/asm/wifi_data'] == ['Static main']
    validated = validate_object(a.object, blocks)
    data, sections, native_symbols = read_object(a.object)
    section = next(s for s in sections if s['segment'] == '__DATA' and s['name'] == '__data')
    assert section['nreloc'] == 0 and section['align'] == 2
    original = a.game/SOURCE
    parsed = parse(original)
    _, labels, _ = raw_layout(parsed)
    lines = original.read_text().splitlines(True)
    # Only the chosen original definitions are assembled. No neighboring
    # pointers or whole-member conversion enters either object.
    reference = '.data\n'
    for record in evidence:
        name, start, size = record['symbol'], record['original_offset'], record['size']
        original_section = labels[name][0]
        first = next(b.line for b in parsed if b.symbol == name)
        following = [b.line for b in parsed if b.section == original_section and labels[b.symbol][1] >= start+size]
        last = min(following, default=len(lines)+1)
        reference += original_section+'\n.balign 4, 0\n.globl '+name+'\n'
        reference += ''.join(lines[first-1:last-1])
    reference += ''.join('.globl '+alias+'\n' for alias in ALIASES)
    reference = re.sub(r'(?m)^(\s*)\.public\b',r'\1.globl',reference)
    (out/'original-selected.s').write_text(reference)
    commands = []

    def run(command):
        r = subprocess.run(list(map(str, command)), capture_output=True, text=True)
        commands.append(dict(command=list(map(str, command)), returncode=r.returncode,
                             stdout=r.stdout, stderr=r.stderr))
        (out/'test-commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        assert r.returncode == 0, r.stdout+r.stderr
        return r.stdout

    run([a.compiler, '-target', 'armv5-none-eabi', '-c', out/'original-selected.s', '-o', out/'original-selected.o'])
    compared_bytes = 0
    for original_section, segment, native_section in (('.data','__DATA','__data'),('.rodata','__TEXT','__const')):
        target = next((s for s in sections if s['segment']==segment and s['name']==native_section),None)
        if target is None: continue
        binary = out/(native_section+'.bin')
        run([a.objcopy, '--dump-section', original_section+'='+str(binary), out/'original-selected.o'])
        reference_bytes = binary.read_bytes()
        native_bytes = data[target['offset']:target['offset']+target['size']]
        assert native_bytes == reference_bytes
        compared_bytes += len(native_bytes)
    symbols = {s['name']: s['value']-sections[s['section']-1]['address'] for s in native_symbols if s['kind'] & 0xe == 0xe}
    reference_symbols = {}
    # The existing object tool independently observes ARM32 label coordinates.
    for line in run([a.readelf, '--symbols', '--wide', out/'original-selected.o']).splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[0].endswith(':') and fields[0][:-1].isdigit():
            reference_symbols[fields[7]] = int(fields[1], 16)
    for name in [*(record['symbol'] for record in evidence), *ALIASES]:
        assert symbols['_'+name] == reference_symbols[name]
    assert symbols['__02110899'] == symbols['_gCpsSha1Padding']+1
    assert not run(['nm', '-u', a.object]).strip()
    assert 'weak' not in run(['nm', '-gU', '-m', a.object]).lower(), 'Weak definition is not a provider'
    report = dict(validated=validated, original_owner='resident',
                  native_object=str(a.object), original_reference_object=str(out/'original-selected.o'),
                  compared_bytes=compared_bytes, records=evidence,
                  aliases={'__02110899': '_gCpsSha1Padding+1'}, undefined=[], relocations=0)
    (out/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(str(len(evidence))+' original resident constants plus interior alias: '+str(compared_bytes)+' bytes, alignment, strong identities and zero relocations verified')


if __name__ == '__main__':
    main()
