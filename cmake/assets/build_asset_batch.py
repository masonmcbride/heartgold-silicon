#!/usr/bin/env python3
"""Run bounded groups of unchanged asset recipes in one Python process. MIT."""
import argparse
import json
from pathlib import Path
import build_heartgold_script
import build_zone_event


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--depfile', required=True, type=Path)
    args = parser.parse_args()
    plan = json.loads(args.manifest.read_text())
    recipe = {'script': build_heartgold_script.main, 'zone': build_zone_event.main}[plan['kind']]
    # One Make job runs a bounded group sequentially, preserving -j parallelism
    # without creating another thread pool or an independent scheduler.
    args.depfile.unlink(missing_ok=True)
    deps = []
    for source in plan['sources']:
        stem = Path(source).stem
        command = ['--source', source]
        if plan['kind'] == 'script':
            command += ['--binary', str(Path(plan['output']) / (stem + '.bin')),
                        '--work-dir', plan['work']]
        else:
            command += ['--output-dir', plan['output']]
        recipe(command + plan['common'])
        deps.append(Path(plan['work']) / (stem + '.d'))
    # CMake accepts multiple output rules in one depfile. Keep each original
    # rule verbatim, including escaped paths and original assembler includes.
    args.depfile.write_text('\n'.join(dep.read_text() for dep in deps))


if __name__ == '__main__':
    main()
