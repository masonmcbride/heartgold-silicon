"""Single build owner for the explicitly declared native source transformations."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def publish_dependencies(depfile, stamp, inputs):
    """Publish the complete dynamic read set for Ninja and the output barrier."""
    if depfile is None and stamp is None:
        return
    if depfile is None or stamp is None:
        raise ValueError('stamp and depfile must be supplied together')
    stamp, depfile = Path(stamp), Path(depfile)
    stamp.parent.mkdir(parents=True, exist_ok=True)
    depfile.parent.mkdir(parents=True, exist_ok=True)
    def escape(path):
        # Ninja depfile syntax is Make-style: escape path metacharacters.
        return str(path).replace('\\', '\\\\').replace(' ', '\\ ').replace('#', '\\#').replace('$', '$$').replace(':', '\\:')
    contents = escape(stamp) + ': ' + ' '.join(escape(p) for p in sorted(map(str, inputs))) + '\n'
    # Write to a temporary file so a failure never publishes incomplete edges.
    temp = depfile.with_name(depfile.name + '.tmp')
    temp.write_text(contents)
    temp.replace(depfile)
    stamp.touch()


def run(manifest, depfile=None, stamp=None):
    started = time.monotonic()
    manifest = Path(manifest).resolve()
    spec = json.loads(manifest.read_text())
    root, binary = Path(spec['root']).resolve(), Path(spec['binary']).resolve()
    receipt = binary / 'native-source-batch/receipt.json'
    jobs = spec['jobs']
    outputs = [Path(j['output']).resolve() for j in jobs]
    if len(set(outputs)) != len(outputs):
        raise ValueError('Native source outputs must have exactly one owner')
    for job, output in zip(jobs, outputs):
        Path(job['input']).resolve().relative_to(root)
        if output.is_relative_to(root) or not output.is_relative_to(binary):
            raise ValueError('Native source output must belong to the binary directory')
    declared = {manifest, *(Path(p).resolve() for p in spec['recipes'])}
    for job in jobs:
        declared.add(Path(job['input']).resolve())
        declared.update(Path(p).resolve() for p in job.get('dependencies', []))
    previous = json.loads(receipt.read_text()) if receipt.exists() else None
    if (previous and set(previous['outputs']) == {str(p) for p in outputs}
            and declared <= {Path(p) for p in previous['inputs']}
            and all(Path(p).is_file() and digest(p) == h
                    for p, h in previous['inputs'].items())
            and all(Path(p).is_file() and digest(p) == h
                    for p, h in previous['outputs'].items())):
        publish_dependencies(depfile, stamp, previous['inputs'])
        print(f'Native source preparation: {len(jobs)} outputs verified, 0 transformations '
              f'({time.monotonic()-started:.3f}s)')
        return

    # Record auxiliary original headers and recipe data actually read by the
    # guarded transformations. These are dependencies, never discovered jobs.
    reads = set(declared)
    active = True
    project = Path(__file__).resolve().parents[1]
    def observe(event, args):
        if active and event == 'open' and isinstance(args[0], (str, bytes)):
            path = Path(args[0].decode() if isinstance(args[0], bytes) else args[0]).resolve()
            if (path.suffix != '.pyc' and (path.is_relative_to(project) or path.is_relative_to(root))
                    and not path.is_relative_to(binary) and path.is_file()):
                reads.add(path)
    sys.addaudithook(observe)
    import native_sources
    rendered = [native_sources.render(root, Path(j['input']), j['kind']) for j in jobs]
    active = False
    # Validate the whole batch before publishing anything. Unchanged bytes keep
    # their timestamps, so a recipe edit does not recompile unrelated objects.
    inputs = {str(p): digest(p) for p in sorted(reads)}
    for output, text in zip(outputs, rendered):
        native_sources.write_if_changed(output, text)
    record = {'inputs': inputs, 'outputs': {str(p): digest(p) for p in outputs}}
    receipt.parent.mkdir(parents=True, exist_ok=True)
    temporary = receipt.with_suffix('.tmp')
    temporary.write_text(json.dumps(record, sort_keys=True) + '\n')
    temporary.replace(receipt)
    publish_dependencies(depfile, stamp, inputs)
    print(f'Native source preparation: {len(jobs)} guarded transformations '
          f'({time.monotonic()-started:.3f}s)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--depfile', type=Path)
    parser.add_argument('--stamp', type=Path)
    args = parser.parse_args()
    run(args.manifest, args.depfile, args.stamp)
