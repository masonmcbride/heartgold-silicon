"""Admission/ordering/overlap checks against the production guest32 lowerer. MIT."""
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--lowerer', type=Path, required=True)
    a = p.parse_args()
    out = a.build.resolve() / 'rule-model-tests'
    out.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((ROOT/'compiler/guest32/rules.json').read_text())
    log = []

    def check(value, message=None):
        path = out/'candidate.json'
        path.write_text(json.dumps(value))
        r = subprocess.run([str(a.lowerer), '--check-rules', str(path)], capture_output=True, text=True, timeout=10)
        log.append(dict(candidate=value, code=r.returncode, stderr=r.stderr))
        (out/'results.json').write_text(json.dumps(log, indent=2)+'\n')
        assert (r.returncode == 0) == (message is None), r.stderr
        if message:
            assert message in r.stderr, r.stderr

    check(catalog)
    reversed_catalog = copy.deepcopy(catalog)
    reversed_catalog['rules'].reverse()
    check(reversed_catalog)
    bad = copy.deepcopy(catalog)
    bad['rules'].append(dict(bad['rules'][1], id='competing-allocation'))
    check(bad, 'ambiguous competing rules')
    bad = copy.deepcopy(catalog)
    bad['rules'][0]['depends'] = ['g32.memory']
    check(bad, 'rule dependency cycle')
    bad = copy.deepcopy(catalog)
    bad['rules'][1]['depends'].append('absent')
    check(bad, 'unknown rule dependency')
    bad = copy.deepcopy(catalog)
    bad['rules'][1]['depends'].append('g32.memory')
    check(bad, 'unsupported operation dependency')
    bad = copy.deepcopy(catalog)
    bad['rules'][1]['incompatible'] = ['g32.memory']
    check(bad, 'incompatible rules')
    for field, value, message in [
        ('status', 'candidate', 'not explicitly admitted'),
        ('version', 2, 'unsupported rule version'),
        ('requires', [], 'unsupported rule preconditions'),
        ('provides', ['host-native-pointer'], 'cannot assert representation facts'),
        ('tests', [], 'lacks evidence'),
        ('phase', 0, 'phase mismatch'),
        ('depends', [], 'explicit layout dependency'),
    ]:
        bad = copy.deepcopy(catalog)
        bad['rules'][1][field] = value
        check(bad, message)
    bad = copy.deepcopy(catalog)
    bad['rules'].pop()
    check(bad, 'missing implemented rule family')
    # A non-32-bit GEP index is not licensed by a 32-bit pointer width.
    src, dst = out/'index16.ll', out/'bad.ll'
    src.write_text('target datalayout = "e-p:32:32:32:16"\ndefine i32 @f(){ret i32 0}\n')
    r = subprocess.run([str(a.lowerer), str(src), str(dst)], capture_output=True, text=True)
    assert r.returncode and 'rule layout needs' in r.stderr, r.stderr
    # The manifest gates real lowering and records applications exactly once.
    src = out/'operations.ll'
    src.write_text('''target datalayout = "e-p:32:32"
define i32 @operations(ptr %p, i32 %i) {
  %q = getelementptr i32, ptr %p, i32 %i
  %v = load i32, ptr %q
  %n = add i32 %v, 1
  store i32 %n, ptr %q
  ret i32 %n
}
''')
    outputs = []
    for n in range(2):
        dst = out/('operations'+str(n)+'.ll')
        r = subprocess.run([str(a.lowerer),str(src),str(dst)],capture_output=True,text=True,timeout=10)
        assert r.returncode == 0, r.stderr
        outputs.append(dst.read_bytes())
    assert outputs[0] == outputs[1], 'nondeterministic lowering'
    matches = re.findall(r'!\{!"(g32\.[^"]+)", !"(\d+)", !"(\d+)"\}', outputs[0].decode())
    assert {name:(int(version),int(count)) for name,version,count in matches} == {
        'g32.layout':(1,1),'g32.interior':(1,1),'g32.memory':(1,2),'g32.integer':(1,1)}
    print('PASS: deterministic admission, conflicts, cycles, unknown facts, phases, closed capabilities')


if __name__ == '__main__':
    main()
