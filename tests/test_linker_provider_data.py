"""Compile recovered original data providers and independently check their bytes and relocations."""
import argparse
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game', type=Path, required=True)
parser.add_argument('--build', type=Path, required=True)
parser.add_argument('--compiler', required=True)
args = parser.parse_args()
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cmake'))
import native_assembly_data as assembly
from native_data_layouts import contracts

work = args.build / 'linker-provider-data-test'
work.mkdir(parents=True, exist_ok=True)
count = 0
for member, contract in contracts().items():
    if not contract.get('native_output_sha256'):
        continue
    source = work / (Path(member).stem + '.S')
    obj = source.with_suffix('.o')
    source.write_text(assembly.emit(args.game, member))
    subprocess.run([args.compiler, '-arch', 'arm64', '-c', str(source), '-o', str(obj)], check=True)
    assembly.validate_object(obj, assembly.recipe(args.game, member))
    count += 1
if not count:
    raise ValueError('No recovered provider contracts were validated')
print(f'Validated {count} native provider objects, including symbol offsets and relocations')
