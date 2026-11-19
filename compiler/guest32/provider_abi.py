"""Declared ARM32 provider ABI data. Normal builds never diagnose candidates. MIT."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ABI = Path(__file__).with_name('main_provider_abi.json.gz')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(path):
    return json.dumps(str(path))[1:-1].encode()


def normalize_flags(flags, game, build):
    return [arg.replace(str(game), '$GAME').replace(str(build), '$BUILD') for arg in flags]


def generated_hash(path, build):
    # Nitroarc's guards/comments embed destination paths. Their member IDs and
    # names remain authoritative; normalize only the variable build prefix.
    data = path.read_bytes().replace(str(build).encode(), b'$BUILD')
    guard = re.sub(r'[^a-zA-Z0-9_]', '_', str(build)).encode()
    return sha(data.replace(guard, b'BUILD'))


def compiler_version(clang):
    return subprocess.check_output([str(clang), '--version'], text=True).splitlines()[0]


def predefines(clang, flags):
    result = subprocess.run([str(clang), *flags, '-dM', '-E', '-x', 'c', '-'],
                            input=b'', capture_output=True, check=True)
    return sha(result.stdout)


def recipe_hashes():
    paths = [ROOT/'compiler/guest32/frontend.py', ROOT/'compiler/guest32/lower.cpp']
    paths += sorted((ROOT/'compiler/guest32').glob('*.h'))
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths}


def include_environment():
    return {key: os.environ.get(key) for key in ('CPATH','C_INCLUDE_PATH','CPLUS_INCLUDE_PATH')}


def load(path, game, build, records, adapted, flags, clang, output):
    raw = gzip.decompress(Path(path).read_bytes())
    raw = raw.replace(b'$GAME', encoded(game)).replace(b'$BUILD', encoded(build))
    data = json.loads(raw)
    contract = data['contract']
    if data.get('version') != 1:
        raise ValueError('Unsupported declared provider ABI version')
    if contract['flags'] != list(flags):
        raise ValueError('Declared ABI frontend flags changed; regenerate ABI data explicitly')
    actual_recipes = {name:sha((ROOT/name).read_bytes()) for name in contract['recipes']}
    if contract['compiler'] != compiler_version(clang) or contract['recipes'] != actual_recipes:
        raise ValueError('Declared ABI compiler contract changed; regenerate ABI data explicitly')
    if contract['include_environment'] != include_environment():
        raise ValueError('Declared ABI include environment changed')
    if contract['predefines'] != predefines(clang, flags):
        raise ValueError('Declared ABI target macros changed; regenerate ABI data explicitly')
    roots = {'game': game, 'build': build}
    for scope, files in contract['inputs'].items():
        for relative, expected in files.items():
            source = roots[scope]/relative
            actual = generated_hash(source, build) if scope == 'build' else sha(source.read_bytes())
            if actual != expected:
                raise ValueError('Declared ABI input changed: '+scope+'/'+relative)
    virtual = {str(Path(entry['name']).relative_to(game)): sha(Path(entry['external-contents']).read_bytes())
               for entry in adapted}
    if virtual != contract['virtual']:
        raise ValueError('Declared ABI adaptations changed; regenerate ABI data explicitly')
    expected = [(r['object'],r.get('source'),r['kind']) for r in records]
    actual = [(r['object'],r.get('source'),r['kind']) for r in data['members']]
    if actual != expected:
        raise ValueError('Declared ABI ownership differs from the original source manifest')
    # Preserve the existing diagnostic/state-proof interface without another
    # JSON serialization of the complete table.
    output.write_bytes(raw)
    return data['members']


def freeze(discovery, game, build, clang, output):
    data = json.loads(Path(discovery).read_text())
    overlay = json.loads((build/'provider-discovery/frontend.json').read_text())['roots']
    virtual_by_path = {str(Path(e['external-contents'])): e for e in overlay}
    inputs = {'game': {}, 'build': {}}
    checked = {}
    clang_sha = sha(Path(clang).read_bytes())
    def verify(path, expected):
        path = Path(path)
        actual = checked.setdefault(str(path), sha(path.read_bytes())) if str(path) not in checked else checked[str(path)]
        if actual != expected:
            raise ValueError('ABI generation evidence is stale: '+str(path))
    for member in data['members']:
        if member.get('source'):
            source = game/member['source']
            inputs['game'][member['source']] = sha(source.read_bytes())
        if 'description' in member:
            work = build/'provider-discovery/members'/member['object']
            for receipt in ('guest.ll.receipt.json', 'description.json.receipt.json'):
                evidence = json.loads((work/receipt).read_text())
                if evidence['environment'] != {key:os.environ.get(key) for key in evidence['environment']}:
                    raise ValueError('ABI generation environment differs from verified compilation')
                if receipt.startswith('guest.ll') and evidence['inputs'][evidence['command'][0]] != clang_sha:
                    raise ValueError('ABI generation compiler differs from verified compilation')
                for source, digest in {**evidence['inputs'], **evidence['outputs']}.items():
                    verify(source, digest)
            receipt = json.loads((work/'guest.ll.receipt.json').read_text())
            if json.loads((work/'description.json').read_text()) != member['description']:
                raise ValueError('ABI description differs from verified output: '+member['object'])
            for source in receipt['inputs']:
                path = Path(source)
                if source in virtual_by_path:
                    continue
                if path.is_relative_to(game):
                    inputs['game'][path.relative_to(game).as_posix()] = sha(path.read_bytes())
                elif path.is_relative_to(build):
                    inputs['build'][path.relative_to(build).as_posix()] = generated_hash(path, build)
                elif path.name not in ('clang', 'SDKSettings.json'):
                    raise ValueError('Undeclared external ABI header: '+source)
        if member.get('kind') == 'C':
            member['frontend_diagnostic'] = '' if member.get('frontend') else 'Not a declared executable frontend; normal builds do not probe this source.'
    from frontend import flags
    contract = dict(flags=normalize_flags(flags(game,build),game,build), compiler=compiler_version(clang),
        predefines=predefines(clang, flags(game,build)),
        include_environment=include_environment(),
        recipes=recipe_hashes(), inputs=inputs,
        virtual={str(Path(e['name']).relative_to(game)):sha(Path(e['external-contents']).read_bytes()) for e in overlay})
    payload = dict(version=1, provenance='ARM32 ABI declarations derived from pinned original sources; contains no executable code or objects.',
                   contract=contract, members=data['members'])
    raw = json.dumps(payload, separators=(',', ':')).encode()
    raw = raw.replace(encoded(game), b'$GAME').replace(encoded(build), b'$BUILD')
    output.write_bytes(gzip.compress(raw, mtime=0))
    return sum('description' in m for m in data['members'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Explicit developer-only ABI declaration generation')
    parser.add_argument('--discovery', type=Path, required=True)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--clang', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    count = freeze(args.discovery.resolve(), args.game.resolve(), args.build.resolve(), args.clang.resolve(), args.output.resolve())
    print('Declared ABI descriptions:', count)
