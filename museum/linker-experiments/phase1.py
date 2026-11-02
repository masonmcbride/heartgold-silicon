#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
"""Inspect unique emitted main-image providers without changing build membership.

uv run tools/link-closure/phase1.py --build build \
  --diagnostic build/native-lifecycle/build-final-integrated.log
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

import native_link_evidence as lc


def arm64(path):
    with path.open('rb') as stream:
        header = stream.read(8)
    return header == struct.pack('<II', 0xfeedfacf, 0x0100000c)


def choose(symbols, objects, inputs, owners):
    """Fail closed: one original src owner, byte-identical loose copies, no conflicts.

    Library/SDK objects need separate ABI/service review. Archives are indexed for
    conflicts but never force-loaded or extracted to bypass image ownership.
    """
    index = lc.provider_index(objects)
    linked = {item.file for item in inputs}
    chosen = {}
    reasons = {}
    for symbol in sorted(symbols):
        providers = [objects[k] for k in index.get(symbol, [])]
        paths = {original for original, owner in owners.items() if owner == 'main'
                 and original.startswith('src/')
                 and any(lc.original_object_name(p.member or p.file).endswith(original)
                         for p in providers)}
        loose = [p for p in providers if p.member is None and p.file not in linked]
        reason = ('no emitted provider' if not providers else
                  'overlay-owned provider; preserve image boundary' if any(
                      p.owner not in {'main', 'unknown', 'ambiguous'} for p in providers) else
                  'library/SDK provider requires ABI/service review' if not paths else
                  'ambiguous ownership, definition, or existing link input')
        if (len(paths) == 1 and providers and loose
                and all(p.owner == 'main' and lc.is_strong(p.defs[symbol]) for p in providers)
                and not any(p.file in linked for p in providers)):
            original = next(iter(paths))
            if all(lc.original_object_name(p.member or p.file).endswith(original)
                   or (p.member and Path(original).name == lc.original_object_name(p.member))
                   for p in providers):
                hashes = {hashlib.sha256(Path(p.file).read_bytes()).hexdigest() for p in loose}
                if len(hashes) == 1 and all(arm64(Path(p.file)) for p in loose):
                    candidate = min(loose, key=lambda p: p.file)
                    # Adding an object must not introduce any competing definition.
                    conflicts = [s for s, kind in candidate.defs.items() if lc.is_strong(kind)
                                 and any(objects[k].file in linked for k in index[s])]
                    if not conflicts:
                        chosen[candidate.file] = original
                        reason = 'selected main-owned provider'
                    else:
                        reason = 'competing definition in existing link inputs'
                else:
                    reason = 'different object copies or non-ARM64 object'
        reasons[symbol] = reason
    return chosen, reasons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=Path('build'))
    parser.add_argument('--diagnostic', required=True, type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    build = args.build.resolve()
    out = (args.out or build / 'link-phase1').resolve()
    out.relative_to(build)
    out.mkdir(parents=True, exist_ok=True)
    before = lc.load_linker_diagnostic(args.diagnostic)
    if not before:
        raise ValueError('Expected a real failed executable linker diagnostic')
    link = build / 'CMakeFiles/heartgold.dir/link.txt'
    inputs, missing = lc.parse_link_command(link, build)
    if missing:
        raise ValueError(f'Missing link inputs: {missing}')
    import shutil
    nm = shutil.which('nm')
    files = sorted({p.resolve() for p in build.rglob('*') if p.suffix in {'.a', '.o'} and p.is_file()}
                   | {Path(i.file) for i in inputs})
    objects, errors = lc.scan_binary_files(files, nm, 'arm64')
    if errors:
        raise ValueError(errors)
    owners = lc.load_owners(root / 'upstream/pokeheartgold/main.lsf')
    lc.assign_owners(objects, owners)
    selected, reasons = choose(before, objects, inputs, owners)
    (out / 'before.json').write_text(json.dumps(sorted(before), indent=2) + '\n')
    provider_map = lc.provider_index(objects)
    (out / 'selection.json').write_text(json.dumps({'objects': selected, 'decisions': reasons,
        'providers': {symbol: [{'file': objects[k].file, 'member': objects[k].member,
                                'owner': objects[k].owner, 'kind': objects[k].defs[symbol]}
                               for k in provider_map.get(symbol, [])]
                      for symbol in sorted(before)}}, indent=2) + '\n')
    report = {'unresolved':len(before), 'candidate_objects':selected,
              'scope':'Read-only emitted-provider diagnostic. Build membership comes from native_image_graph.py.'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
