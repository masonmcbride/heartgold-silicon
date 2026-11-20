#!/usr/bin/env python3
"""Fail-closed local reuse of a *previous* full CTest result.

This is an incremental evidence check, NOT a fresh test execution. The full
regression remains the authority whenever tracked inputs change, and can be
forced with HEARTGOLD_FULL_TESTS=1. Runtime or external observations not
represented by local inputs are not independently retested on a reuse hit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('CMakeLists.txt', 'build.sh', 'cmake', 'compiler', 'docs',
           'hardware_drivers', 'tests')
EXCLUDED_BUILD_DIRS = {'logs', 'Testing', 'bootstrap', '__pycache__'}
EXCLUDED_FILES = {'.ninja_log', '.ninja_deps', '.DS_Store'}
# Presentation/bootstrap counters do not affect compiler or CTest behavior.
EPHEMERAL_ENV = {'HEARTGOLD_BOOTSTRAP_SECONDS', 'SHLVL', 'OLDPWD', '_',
                 'TERM', 'COLUMNS', 'LINES', 'HEARTGOLD_FULL_TESTS'}


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def files(build):
    for name in SOURCES:
        item = ROOT/name
        if item.is_file():
            yield item
        elif item.is_dir():
            for directory, names, filenames in os.walk(item):
                names[:] = [n for n in names if n not in {'__pycache__', '.git'}]
                for filename in filenames:
                    p = Path(directory)/filename
                    if p.is_file() and not p.is_symlink() and filename not in EXCLUDED_FILES:
                        yield p
    for directory, names, filenames in os.walk(build):
        names[:] = [n for n in names if n not in EXCLUDED_BUILD_DIRS]
        for filename in filenames:
            p = Path(directory)/filename
            if p.is_file() and not p.is_symlink() and filename not in EXCLUDED_FILES:
                yield p


def identity(path):
    s = path.stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def measure(path, previous=None):
    before = identity(path)
    if previous and before == previous['identity']:
        return previous
    sha = file_hash(path)
    if identity(path) != before:
        raise ValueError(f'Input modified during test evidence check: {path}')
    return dict(identity=before, sha256=sha)


def context(build):
    # The repository's pinned upstream trees are separately checked as pristine
    # by the production driver. Their commit hashes still enter this receipt.
    upstream = {}
    for name in ('pokeheartgold', 'libntr'):
        path = ROOT/'upstream'/name
        result = subprocess.run(['git','-C',str(path),'rev-parse','HEAD'],
                                text=True,capture_output=True)
        if result.returncode:
            raise ValueError('Missing exact upstream checkout: '+str(path))
        upstream[name] = result.stdout.strip()
    tests = subprocess.check_output(['ctest','--test-dir',str(build),'--show-only=json-v1'],text=True)
    definitions = json.loads(tests)['tests']
    if not definitions:
        raise ValueError('Refusing empty CTest suite')
    return dict(root=str(ROOT),build=str(build),upstream=upstream,
                tests_hash=hashlib.sha256(json.dumps(definitions,sort_keys=True).encode()).hexdigest(),
                tests=len(definitions),platform=platform.platform(),
                python=sys.version,environment=dict(sorted((k,v) for k,v in os.environ.items()
                                        if k not in EPHEMERAL_ENV)))


def receipt_path(build):
    return build/'logs'/'complete-ctest-proof.json'


def perform(build, check):
    build=build.resolve()
    path=receipt_path(build)
    previous=None
    if check:
        if os.environ.get('HEARTGOLD_FULL_TESTS') == '1':
            print('Full testing explicitly requested')
            return False
        try:
            previous=json.loads(path.read_text())
        except (FileNotFoundError,ValueError):
            print('No prior complete CTest receipt')
            return False
    metadata=context(build)
    if previous and previous.get('context')!=metadata:
        print('CTest inputs/environment changed; rerunning full suite')
        return False
    previous_files=previous.get('files',{}) if previous else {}
    current={}
    for f in files(build):
        name=str(f.resolve())
        current[name]=measure(f,previous_files.get(name))
        if previous and (name not in previous_files or current[name]['sha256']!=previous_files[name]['sha256']):
            print('Changed CTest input:',name)
            return False
    if previous and set(current)!=set(previous_files):
        print('CTest input inventory changed; rerunning full suite')
        return False
    record=dict(context=metadata,files=current,full_suite_passed=True)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.ctest-proof-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as stream:
            json.dump(record,stream,separators=(',',':'),sort_keys=True)
            stream.write('\n')
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    if check:
        print(f'{metadata["tests"]} previously passed CTests: input snapshot unchanged; '
              '0 tests executed (reused evidence, not fresh verification)')
    else:
        print(f'Recorded successful full execution of {metadata["tests"]} CTests')
    return True


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',required=True,type=Path)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--check',action='store_true')
    g.add_argument('--record',action='store_true')
    args=p.parse_args()
    try:
        success=perform(args.build,args.check)
    except (ValueError,OSError,subprocess.CalledProcessError) as exc:
        print('Full CTest required:',exc,file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(0 if success else 1)
