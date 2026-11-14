#!/usr/bin/env python3
"""Capture a configured Ninja DAG and an overinclusive line-numbered source corpus.

Read-only: queries Ninja and reads files, never builds or executes HeartGold.
Not dynamic line coverage; does not claim to know which Python/C/C++ lines ran.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import heapq
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SOURCE_EXT = {'.py','.cmake','.sh','.c','.cc','.cpp','.cxx','.h','.hpp','.hh','.m','.mm','.s','.S','.metal','.rs','.ll','.inc','.inl'}
SKIP_DIRS = {'.git','build','.heartgold-preservation','__pycache__','.venv','.pytest_cache','node_modules'}
NODE = re.compile(r'^\s*"([^"]+)"\s*\[(.*)\]')
EDGE = re.compile(r'^\s*"([^"]+)"\s*->\s*"([^"]+)"')
LABEL = re.compile(r'\blabel="((?:\\.|[^"\\])*)"')


def command(argv, cwd):
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, errors='replace')
    if p.returncode:
        raise RuntimeError(f"{' '.join(map(str,argv))}: {p.stderr[-1800:]}")
    return p.stdout


def extract_graph(dot):
    labels = {}
    rules = set()
    outgoing = defaultdict(list)
    incoming = defaultdict(int)
    vertices = set()
    for line in dot.splitlines():
        n = NODE.match(line)
        if n:
            ident, attrs = n.groups()
            vertices.add(ident)
            match = LABEL.search(attrs)
            labels[ident] = match.group(1) if match else ident
            if 'shape=ellipse' in attrs:
                rules.add(ident)
        e = EDGE.match(line)
        if e:
            a,b = e.groups()
            outgoing[a].append(b)
            incoming[b] += 1
            vertices.update((a,b))
    ready = [v for v in vertices if incoming[v] == 0]
    heapq.heapify(ready)
    waves = []
    visited = 0
    while ready:
        current = [heapq.heappop(ready) for _ in range(len(ready))]
        visited += len(current)
        waves.append(([(v,labels.get(v,v)) for v in current if v in rules],
                      [(v,labels.get(v,v)) for v in current if v not in rules]))
        for a in current:
            for b in outgoing[a]:
                incoming[b] -= 1
                if incoming[b] == 0:
                    heapq.heappush(ready,b)
    if visited != len(vertices):
        raise RuntimeError(f'Incomplete Ninja topological sort: {visited}/{len(vertices)}')
    return labels, rules, outgoing, waves


def sources(root, build):
    found = set()
    for base, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            p = Path(base) / name
            if p.is_symlink() or not p.is_file():
                continue
            if p.suffix in SOURCE_EXT or name in {'CMakeLists.txt','Makefile','build.sh'}:
                found.add(p.resolve())
    # Generated C/C++ and assembly source files from compile_commands.json are
    # build inputs even though the build directory is omitted from the tree walk.
    compdb = build / 'compile_commands.json'
    if compdb.is_file():
        try:
            for item in json.loads(compdb.read_text()):
                p = Path(item['file'])
                if not p.is_absolute():
                    p = Path(item['directory']) / p
                if p.is_file() and not p.is_symlink():
                    found.add(p.resolve())
        except (OSError, ValueError, KeyError) as e:
            print(f'WARNING: could not read compile_commands.json: {e}',file=sys.stderr)
    return sorted(found, key=str)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path.cwd())
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    if not (root/'.git').is_dir() or not (root/'CMakeLists.txt').is_file():
        ap.error('Run from the heartgold-silicon repository root')
    builds = [root/'build/native', root/'build']
    build = next((p for p in builds if (p/'build.ninja').is_file()),None)
    if build is None:
        ap.error('No configured build.ninja under build/native or build. Configure/build with ./build.sh first. The copied verified-build.ninja alone is not a resolved working Ninja graph.')
    output = (args.output or root.parent/'heartgold-scheduler-source.md').resolve()
    if output.exists():
        ap.error(f'Output exists; refusing to overwrite: {output}')
    if output.is_relative_to(root):
        ap.error('Put the output outside the repo to prevent including generated reports')
    print('Reading configured Ninja graph...',flush=True)
    dot = command(['ninja','-C',str(build),'-t','graph'],root)
    labels,rules,outgoing,waves = extract_graph(dot)
    print('Reading expanded Ninja commands...',flush=True)
    cmds = command(['ninja','-C',str(build),'-t','commands'],root).splitlines()
    paths = sources(root,build)
    print(f'Graph: {len(labels):,} labeled nodes, {len(waves):,} waves; {len(cmds):,} commands; {len(paths):,} source files',flush=True)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',encoding='utf-8') as f:
        def w(s=''):
            f.write(s+'\n')
        w('# HeartGold build: configured execution DAG and full source corpus')
        w(f'\nRepository: `{root}`  ')
        w(f'Configured Ninja build: `{build}`  ')
        w(f'Graph nodes: **{len(set(labels)|set(outgoing)):,}**  ')
        w(f'Graph edges: **{sum(map(len,outgoing.values())):,}**  ')
        w(f'Topological antichain waves: **{len(waves):,}**  ')
        w(f'Expanded commands: **{len(cmds):,}**  ')
        w(f'Source files: **{len(paths):,}**')
        w('\n## Interpretation and coverage limits')
        w('This is a read-only static source superset plus a resolved configured Ninja graph, NOT a dynamic trace of every executed line.')
        w('Wave members are dependency-ready together; implicit shared resources or subprocess work may still constrain parallelism.')
        w('Python imports, conditional branches, CMake configure-time execution, dynamically dispatched subprocesses, compiler internals, and runtime HeartGold control flow are not fully resolved here.')
        w('All present source-like files under the repository (including upstream) are included, not only reachable ones. Generated translation units from compile_commands.json are also included.')
        w('Inspect before sharing: contents may include private source paths, project secrets, or copyrighted upstream material.')
        w('\n## Canonical topological waves (file and rule nodes)')
        for i,(active, artifacts) in enumerate(waves):
            w(f'\n### Wave {i}: {len(active):,} rule nodes, {len(artifacts):,} artifact nodes')
            for v,name in active:
                w(f'- RULE `{v}`: {name}')
            for v,name in artifacts:
                w(f'- ARTIFACT `{v}`: {name}')
        w('\n## Concrete graph edges')
        for a,children in sorted(outgoing.items()):
            for b in children:
                w(f'- `{a}` → `{b}`')
        w('\n## Expanded Ninja command sequence')
        for i,cmd in enumerate(cmds,1):
            w(f'\n### Command {i}')
            w('```sh')
            w(cmd)
            w('```')
        w('\n## Full numbered source corpus')
        for index,p in enumerate(paths,1):
            try:
                raw = p.read_bytes()
                if b'\x00' in raw:
                    continue
                source = raw.decode('utf-8',errors='replace')
            except OSError as e:
                w(f'\n### UNREADABLE: `{p}` — {e}')
                continue
            try:
                relative = p.relative_to(root)
            except ValueError:
                relative = p
            w(f'\n### Source {index}: `{relative}`')
            w(f'\nSHA-256: `{hashlib.sha256(raw).hexdigest()}`; bytes: {len(raw):,}')
            w('\n```text')
            for lineno,line in enumerate(source.splitlines(),1):
                w(f'{lineno:06d} | {line}')
            w('```')
            if index % 1000 == 0:
                print(f'  Captured {index:,}/{len(paths):,} source files',flush=True)
    print(f'OUTPUT: {output}',flush=True)
    print(f'SIZE: {output.stat().st_size / 1024**2:.1f} MiB',flush=True)
    print('No build, test, delete, or source modification performed.',flush=True)

if __name__ == '__main__':
    main()
