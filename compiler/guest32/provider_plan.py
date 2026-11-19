"""Read declared production provider ownership; never select alternatives. MIT."""
import hashlib
import json
from pathlib import Path
import re

DEFAULT_PLAN = Path(__file__).with_name('main_provider_plan.json')


def load(path, game, records, requested_roots, cmake):
    plan = json.loads(Path(path).read_text())
    if plan.get('version') != 2:
        raise ValueError('Unsupported provider plan version')
    pin = re.search(r'set\(HEARTGOLD_COMMIT ([0-9a-f]{40})\)', Path(cmake).read_text())
    if not pin or plan['source_commit'] != pin[1]:
        raise ValueError('Provider plan does not match the declared game pin')
    if hashlib.sha256((game/'main.lsf').read_bytes()).hexdigest() != plan['source_manifest_sha256']:
        raise ValueError('Original source manifest changed; update the provider plan explicitly')
    members = plan['members']
    names = [m['object'] for m in members]
    if not names or names != sorted(set(names)):
        raise ValueError('Provider plan must contain sorted, unique members')
    original = {r['object']: r for r in records}
    for member in members:
        name = member['object']
        record = original.get(name)
        if record is None or record['kind'] != 'C' or record['source'] != member['source']:
            raise ValueError('Provider plan ownership mismatch: '+name)
        if hashlib.sha256((game/record['source']).read_bytes()).hexdigest() != member['source_sha256']:
            raise ValueError('Provider source changed; update its declaration explicitly: '+name)
    selected = set(names)
    compiled = plan['compiled_members']
    hardware = plan['hardware_members']
    if compiled != sorted(set(compiled)) or set(compiled) & hardware.keys() or set(compiled) | hardware.keys() != selected:
        raise ValueError('Provider plan must explicitly partition compiled and hardware members')
    proof = plan['proof_ir_members']
    if proof != sorted(set(proof)) or any(m not in original or original[m]['kind']!='C' for m in proof):
        raise ValueError('Storage proof IR must name unique original C members')
    for root in requested_roots:
        if root not in plan['entrypoints']:
            raise ValueError('Entrypoint is not declared in provider plan: '+root)
        if plan['entrypoints'][root] not in selected:
            raise ValueError('Entrypoint owner is not selected: '+root)
    return plan, selected
