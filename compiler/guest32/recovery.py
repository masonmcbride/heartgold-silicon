"""Pinned resident selection and actual Mach-O callback identity checks. MIT."""
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]


def deferred_blockers(report, retry=False):
    """Historical failures may be retained, but never suppress an explicit retry."""
    if report is None or retry:
        return {}
    return {r['member']: r for r in report['results']
            if not r['compiled'] and r['member'] != 'src/scrcmd_battle.o'}


def load(path, out, game):
    from script_callback_roots import original_owners
    recovery = json.loads(Path(path).read_text())
    report = Path(recovery['historical_report'])
    if not report.is_absolute():
        report = ROOT / report
    raw = report.read_bytes()
    if hashlib.sha256(raw).hexdigest() != recovery['historical_report_sha256']:
        raise ValueError('historical closure provenance changed')
    historical = json.loads(raw)
    floor = set(recovery['selected_members'])
    compiled = {r['member'] for r in historical['results'] if r['compiled']}
    if floor != set(historical['selected_members']):
        raise ValueError('historical selection mismatch')
    if compiled != set(recovery['previous_compiled_objects_sha256']):
        raise ValueError('historical compiled-member census mismatch')
    owners = original_owners(game)
    if any(owners.get(m) != 'main' for m in floor):
        raise ValueError('selection floor crosses original image ownership')
    historical_objects(out,recovery['previous_compiled_objects_sha256'])
    return historical, json.loads(report.with_name('catalog.json').read_text())


def historical_objects(out, expected):
    # Atomic publication retains the preceding generation. Recovery may compile
    # new dispatch domains, but must keep the original 581 objects byte-exact.
    out=Path(out)
    roots=[out]
    canonical=out.name.split('.pending-',1)[0]
    roots.extend(sorted(out.parent.glob(canonical+'.previous-*')))
    for root in roots:
        if all((root/member/'native.o').is_file() and
               hashlib.sha256((root/member/'native.o').read_bytes()).hexdigest()==digest
               for member,digest in expected.items()):
            return root
    raise ValueError('historical native object missing or changed: no intact generation')


def code_constants(path):
    """Read defined four-byte callback handles from actual ARM64 Mach-O storage."""
    data = Path(path).read_bytes()
    magic, cpu, _, kind, count, _, _, _ = struct.unpack_from('<8I', data)
    if (magic, cpu, kind) != (0xfeedfacf, 0x100000c, 1):
        raise ValueError('expected native ARM64 Mach-O object: ' + str(path))
    offset = 32
    sections = []
    symtab = None
    for _ in range(count):
        cmd, size = struct.unpack_from('<II', data, offset)
        if cmd == 0x19:
            nsects = struct.unpack_from('<I', data, offset + 64)[0]
            for j in range(nsects):
                section = offset + 72 + 80 * j
                address, extent, fileoff = struct.unpack_from('<QQI', data, section + 32)
                sections.append((address, extent, fileoff))
        if cmd == 2:
            symtab = struct.unpack_from('<4I', data, offset + 8)
        offset += size
    if symtab is None:
        raise ValueError('missing Mach-O symbol table')
    symoff, nsyms, stroff, strsize = symtab
    result = {}
    prefix = '_guest32_code_address_'
    for i in range(nsyms):
        index, typ, sect, _, value = struct.unpack_from('<IBBHQ', data, symoff + i * 16)
        if typ & 0xe0 or typ & 0x0e != 0x0e or not sect:
            continue
        name = data[stroff + index:stroff + strsize].split(b'\0', 1)[0].decode()
        if not name.startswith(prefix):
            continue
        address, extent, fileoff = sections[sect - 1]
        delta = value - address
        if delta < 0 or delta + 4 > extent or fileoff + delta + 4 > len(data):
            raise ValueError('callback constant outside initialized section: ' + name)
        result[name[len(prefix):]] = struct.unpack_from('<I', data, fileoff + delta)[0]
    return result


def verify_callbacks(out, members, catalog):
    codes = {f['name']: f for f in catalog['codes'] if not f['local']}
    count = 0
    for member in sorted(members):
        for name, value in code_constants(Path(out) / member / 'native.o').items():
            if name not in codes or codes[name]['address'] != value:
                raise ValueError('compiled original callback identity/address mismatch: ' + name)
            count += 1
    return count
