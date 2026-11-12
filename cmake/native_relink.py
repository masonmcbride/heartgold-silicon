"""Replay an existing native link checkpoint with verified dynamic closure.

This does not regenerate checkpoint objects. The source CMake pipeline owns
source compilation; this tool records an explicit working directory and every
resolved input when diagnosing/relinking a historical checkpoint.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from native_dynamic_closure import audit
from native_overlay_link import symbols, write_if_changed


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', required=True, type=Path)
    p.add_argument('--working-directory', required=True, type=Path)
    p.add_argument('--output-directory', required=True, type=Path)
    a = p.parse_args()
    cwd, out = a.working_directory.resolve(), a.output_directory.resolve()
    out.mkdir(parents=True, exist_ok=True)
    args = json.loads(a.manifest.read_text())['arguments'].copy()
    if any('dynamic_lookup' in s or 'flat_namespace' in s for s in args):
        raise ValueError('Permissive binding is forbidden')
    original = Path(args[args.index('-o')+1])
    if not original.is_absolute(): original = cwd/original
    before = audit(original)
    (out/'before.json').write_text(json.dumps(before, indent=2)+'\n')
    export_index = args.index('-exported_symbols_list')+2
    prior_exports = Path(args[export_index])
    if not prior_exports.is_absolute(): prior_exports = cwd/prior_exports
    required = set(prior_exports.read_text().splitlines()) | set(before['main_required'])
    inputs, available = [], set()
    for i, value in enumerate(args):
        if not value.endswith(('.a', '.o', '.dylib')): continue
        path = Path(value)
        if not path.is_absolute(): path = cwd/path
        path = path.resolve(strict=True)
        args[i] = str(path)
        inputs.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        if path.suffix in ('.a', '.o'): available.update(symbols(path))
        if path.name == 'libntr_spi.a':
            # Do not accidentally admit the experimental host MIC replacement.
            definitions = subprocess.check_output(['nm', '-A', '-gU', str(path)], text=True)
            lines = [line for line in definitions.splitlines() if line.endswith(' _MIC_GetLastSamplingAddress')]
            if len(lines) != 1 or ':mic.c.o:' not in lines[0]:
                raise ValueError('SPI must supply Nintendo mic.c.o: '+str(lines))
    if required - available:
        raise ValueError('No linked original provider for '+str(sorted(required-available)))
    exports = out/'main-exports.txt'
    write_if_changed(exports, '\n'.join(sorted(required))+'\n')
    args[export_index] = str(exports)
    args[args.index('-o')+1] = str(out/'heartgold')
    args.extend(['-Xlinker', '-map', '-Xlinker', str(out/'link.map'),
                 '-Xlinker', '-why_load'])
    record = dict(arguments=args, working_directory=str(cwd), inputs=inputs,
                  parent_manifest=str(a.manifest.resolve()))
    (out/'link-manifest.json').write_text(json.dumps(record, indent=2)+'\n')
    with (out/'link.log').open('w') as log:
        result = subprocess.run(args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Link failed; see '+str(out/'link.log'))
    after = audit(out/'heartgold')
    (out/'after.json').write_text(json.dumps(after, indent=2)+'\n')
    if after['missing']: raise ValueError('Dynamic closure failed: '+str(after['missing']))
    print(f"{out/'heartgold'}: {after['application_images']} images, "
          f"{after['strong_application_imports']} strong application imports, zero missing")


if __name__ == '__main__':
    main()
