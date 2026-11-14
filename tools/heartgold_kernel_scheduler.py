#!/usr/bin/env python3
"""HeartGold semantic kernel planning + safe Ninja execution backend.

Uses the *real* Ninja dependency graph to construct stable kernel nodes.
This is a first working scheduler IR, not a replacement for Ninja's execution
semantics, dynamic dependencies, restat, or sandboxing. The --build path keeps
Ninja in charge of executing edges while measuring process memory. No files are
written unless --output is provided or Ninja itself generates build outputs.

Python standard library only; works with macOS Python 3.12.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
import hashlib
import heapq
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

NODE = re.compile(r'^\s*"([^"]+)"\s*\[(.*)\]')
EDGE = re.compile(r'^\s*"([^"]+)"\s*->\s*"([^"]+)"')
LABEL = re.compile(r'\blabel="((?:\\.|[^"\\])*)"')
MD_NODE = re.compile(r'^- (RULE|ARTIFACT) `(0x[0-9a-f]+)`: (.*)$')
MD_EDGE = re.compile(r'^- `(0x[0-9a-f]+)` → `(0x[0-9a-f]+)`$')


@dataclass
class Graph:
    labels: dict[str, str]
    rules: set[str]
    outgoing: dict[str, list[str]]
    incoming: dict[str, list[str]]

    @classmethod
    def from_dot(cls, lines):
        labels = {}
        rules = set()
        outgoing = defaultdict(list)
        incoming = defaultdict(list)
        for line in lines:
            n = NODE.match(line)
            if n:
                ident, attrs = n.groups()
                match = LABEL.search(attrs)
                labels[ident] = match.group(1) if match else ident
                if 'shape=ellipse' in attrs:
                    rules.add(ident)
            e = EDGE.match(line)
            if e:
                a, b = e.groups()
                outgoing[a].append(b)
                incoming[b].append(a)
        return cls(labels, rules, dict(outgoing), dict(incoming))

    @classmethod
    def from_capture(cls, file):
        labels = {}
        rules = set()
        outgoing = defaultdict(list)
        incoming = defaultdict(list)
        mode = ''
        with file.open('r', encoding='utf-8') as stream:
            for line in stream:
                if line.startswith('## Canonical topological waves'):
                    mode = 'nodes'
                    continue
                if line.startswith('## Concrete graph edges'):
                    mode = 'edges'
                    continue
                if line.startswith('## Expanded Ninja command sequence'):
                    break
                if mode == 'nodes':
                    match = MD_NODE.match(line)
                    if match:
                        typ, ident, label = match.groups()
                        labels[ident] = label.rstrip()
                        if typ == 'RULE':
                            rules.add(ident)
                elif mode == 'edges':
                    match = MD_EDGE.match(line)
                    if match:
                        a, b = match.groups()
                        outgoing[a].append(b)
                        incoming[b].append(a)
        return cls(labels, rules, dict(outgoing), dict(incoming))


def normalize(s: str, root: Path, build: Path) -> str:
    s = s.replace('\\"', '"')
    if s.startswith('0x'):
        return '<unlabeled>'  # never use ephemeral graph node addresses as IDs
    if s.startswith(str(build) + '/'):
        return '@build/' + s[len(str(build))+1:]
    if s.startswith(str(root) + '/'):
        return '@repo/' + s[len(str(root))+1:]
    if s.startswith('/'):
        return s
    return '@build/' + s.removeprefix('./')


def category(rule: str, outputs: list[str], inputs: list[str]) -> tuple[str, str]:
    joined = ' '.join(outputs).lower()
    reads = ' '.join(inputs).lower()
    rule_low = rule.lower()
    # Classify using declared output contracts *before* generic transitive
    # dependencies. Overlay providers may depend on arbitrary image assets;
    # that does not make their own operation a graphics conversion.
    if 'native-overlays/' in joined:
        if 'bindings.' in joined: return 'SOLVE', 'overlay-bindings'
        if 'dynamic-closure' in joined: return 'VERIFY', 'overlay-closure'
        if 'preflight' in joined: return 'VERIFY', 'overlay-preflight'
        if joined.endswith('.dylib'): return 'LOWER', 'overlay-link'
        if joined.endswith(('.tbd','.rsp','.json','.inc')): return 'SOLVE', 'overlay-provider'
        return 'LOWER', 'overlay-generation'
    if 'dwc-native/' in joined:
        if '-validated' in joined: return 'VERIFY', 'dwc-layout'
        return 'LOWER', 'dwc-data'
    if 'build_heartgold_script.py' in reads or any('/generated/' + x + '_archive/' in joined for x in ('move_script','subscript','scr_seq')):
        return 'LOWER', 'script-assemble'
    if '.naix' in joined and '/script/' in joined:
        return 'LOWER', 'script-index'
    if '/zone_event/' in reads or 'zone_event' in joined:
        return 'LOWER', 'zone-events'
    if ('native/src/' in joined or 'native/lib/' in joined or 'native/include/' in joined) and not any(x.endswith('.o') for x in outputs):
        return 'LIFT', 'native-source'
    if any(x.endswith(('.c.o','.cpp.o','.cc.o','.cxx.o','.m.o','.mm.o','.s.o','.S.o')) for x in outputs):
        return 'LOWER', 'native-object'
    if any(x.endswith(('.dylib', '.a', '.tbd', '/heartgold')) for x in outputs):
        return 'LOWER', 'link-archive'
    if '/msgdata/' in reads or '/msgdata/' in joined:
        return 'LOWER', 'text-encode'
    if 'build_heartgold_json_binary.py' in reads:
        return 'LOWER', 'json-binary'
    if '.png' in reads or 'nitrogfx' in reads:
        return 'LOWER', 'graphics-convert'
    if 'generated/files/' in joined or '/assets/' in joined:
        if any(x in joined for x in ('.narc', '/graphic/', '/pokegra/', '.nclr', '.ncgr', '.nscr')):
            return 'LOWER', 'graphics-archive'
        return 'LOWER', 'asset-generation'
    if 'test' in joined and ('verify' in rule_low or 'check' in joined):
        return 'VERIFY', 'regression'
    if rule_low == 'phony': return 'SOURCE', 'phony'
    return 'LOWER', 'misc-' + re.sub(r'[^a-z0-9_-]', '', rule_low)[:34]


def topo(g: Graph) -> list[str]:
    verts = set(g.labels) | set(g.outgoing) | set(g.incoming) | g.rules
    count = {v: len(g.incoming.get(v, [])) for v in verts}
    queue = deque(v for v in verts if count[v] == 0)
    order = []
    while queue:
        v = queue.popleft()
        order.append(v)
        for u in g.outgoing.get(v, []):
            count[u] -= 1
            if count[u] == 0:
                queue.append(u)
    if len(order) != len(verts):
        raise RuntimeError(f'Graph is not acyclic: {len(order)}/{len(verts)} visited')
    return order


def stable_id(operation: str, backend: str, outputs: list[str], rule_label: str) -> str:
    data = json.dumps((operation, backend, sorted(outputs), rule_label), separators=(',', ':'))
    return hashlib.sha256(data.encode()).hexdigest()[:20]


def extract_kernels(g: Graph, root: Path, build: Path):
    """Make ONE kernel per non-phony Ninja rule, without expanding phony deps.

    Graph edges remain canonical and compact. Expanding the closure of each
    phony barrier into kernel->kernel edges multiplies the graph by orders of
    magnitude and is both slower and less faithful to Ninja's representation.
    """
    kernels = {}
    rule_ids = {}
    for vertex in g.rules:
        if g.labels.get(vertex, '') == 'phony':
            continue
        outpaths = sorted(set(normalize(g.labels.get(x, x), root, build)
                              for x in g.outgoing.get(vertex, ()) if x not in g.rules))
        outpaths = [x for x in outpaths if x != '<unlabeled>']
        ins = sorted(set(normalize(g.labels.get(p,p),root,build)
                         for p in g.incoming.get(vertex, ()) if p not in g.rules))
        if not outpaths:
            # This is a rare Ninja utility edge; it has no stable output path
            # and therefore is ineligible for independent cached execution.
            outpaths = ['<anonymous-rule>:' + g.labels.get(vertex, 'unknown')]
            # We still need a unique local identity; no cross-build cache claim.
        op, backend = category(g.labels.get(vertex,''), outpaths, ins)
        ident = stable_id(op,backend,outpaths,g.labels.get(vertex,''))
        if ident in kernels:
            # Anonymous rules can share a rule name. Distinguish based on
            # stable parent/output names when possible, otherwise fail closed.
            ident = stable_id(op,backend,outpaths + ['inputs:'+repr(ins)],g.labels.get(vertex,''))
        if ident in kernels:
            raise RuntimeError('Ambiguous rule identities; unable to cache safely')
        kernels[ident] = {
            'id': ident, 'op': op, 'backend': backend,
            'rule': g.labels.get(vertex,''), 'outputs': outpaths,
            'inputs': ins, 'duration_ms': None,
            'cache_safe': False, # cannot prove hermeticity from a Ninja graph
        }
        rule_ids[vertex] = ident
    return kernels, rule_ids


def attach_ninja_log(kernels: dict, build: Path):
    log = build / '.ninja_log'
    if not log.is_file():
        return 0
    per_output = {}
    for line in log.open(encoding='utf8', errors='replace'):
        fields = line.rstrip('\n').split('\t')
        if len(fields) != 5:
            continue
        try:
            start, end = int(fields[0]), int(fields[1])
        except ValueError:
            continue
        if 0 <= end-start < 86_400_000:
            name = fields[3]
            if name.startswith(str(build) + '/'):
                name = name[len(str(build))+1:]
            per_output['@build/' + name.removeprefix('./')] = end - start
    hits = 0
    for k in kernels.values():
        durations = [per_output[x] for x in k['outputs'] if x in per_output]
        if durations:
            k['duration_ms'] = max(durations)
            hits += 1
    return hits


def critical_path(g: Graph, kernels: dict, rule_ids: dict, target: str='all'):
    """Longest *observed-weight* chain over the original bipartite graph.

    File nodes and phony rules cost zero. Critical-path estimates are invalid
    for missing durations; we retain them only as historical-log indicators.
    """
    order=topo(g)
    finish={}
    depth={}
    parent={}
    for v in order:
        preds=g.incoming.get(v,())
        pred=max(preds,key=lambda p:(finish[p],depth[p]),default=None)
        k=kernels.get(rule_ids.get(v,''))
        finish[v]=(finish[pred] if pred is not None else 0)+(k['duration_ms'] or 0 if k else 0)
        depth[v]=(depth[pred] if pred is not None else 0)+(1 if k else 0)
        parent[v]=pred
    endings=[v for v in order if v not in g.rules and g.labels.get(v,'')==target]
    if not endings:
        endings=[v for v in order if not g.outgoing.get(v)]
    if not endings:return [],0,0
    last=max(endings,key=lambda v:(finish[v],depth[v]))
    chain_ms=finish[last]
    path=[]
    while last is not None:
        if last in rule_ids: path.append(kernels[rule_ids[last]])
        last=parent[last]
    total=sum(k['duration_ms'] or 0 for k in kernels.values())
    return path[::-1],chain_ms,total


def compact_graph(g:Graph,rule_ids:dict,root:Path,build:Path):
    """Integer-indexed exact edges preserve shared barriers; no transitive blowup."""
    order=topo(g)
    index={v:i for i,v in enumerate(order)}
    nodes=[]
    for v in order:
        label=g.labels.get(v,v)
        if v in rule_ids:
            nodes.append({'type':'kernel', 'kernel_id':rule_ids[v]})
        elif v in g.rules:
            nodes.append({'type':'phony', 'label':label})
        else:
            nodes.append({'type':'artifact', 'label':normalize(label,root,build)})
    edges=[[index[a],index[b]] for a, dst in g.outgoing.items() for b in dst]
    return {'nodes':nodes,'edges':edges}


def summary(g:Graph, kernels:dict, hits:int, path:list, path_ms:int, total_ms:int):
    count = Counter(k['backend'] for k in kernels.values())
    measured = Counter()
    for k in kernels.values():
        if k['duration_ms'] is not None:
            measured[k['backend']] += k['duration_ms']
    print(f'Graph: {len(g.labels):,} labeled nodes, {sum(map(len,g.outgoing.values())):,} edges')
    print(f'Kernels: {len(kernels):,} actual computational rule nodes (phony excluded)')
    print(f'Durations matched: {hits:,}/{len(kernels):,} from historical Ninja log')
    print('\nBackends                              kernels    observed edge-seconds')
    for name,n in count.most_common():
        print(f'{name:<38} {n:>6} {measured[name]/1000:>17.1f}')
    print('\nHistorical-log model (NOT a measured build critical path):')
    print(f'  summed matched work: {total_ms/1000:.2f} edge-seconds')
    print(f'  longest weighted chain: {path_ms/1000:.2f} seconds')
    print(f'  idealized >= max(chain, summed work / 8): {max(path_ms,total_ms/8)/1000:.2f} seconds')
    print('  Note: unmatched edges assigned 0 ms; historical log mixes builds.')
    print('  This is an optimistic bound, not a real speed forecast.')
    print('\nLongest weighted dependency chain, last 15 kernels:')
    for k in path[-15:]:
        print(f'  {(k["duration_ms"] or 0)/1000:7.3f}s  {k["backend"]:<20} {k["outputs"][0][:98]}')




def simulate_ready_queue(g: Graph, kernels: dict, rule_ids: dict, jobs: int):
    """Event-driven dependency scheduler; zero-cost artifacts are NOT barriers.

    Uses Ninja log times for observed edges. Missing timings use one synthetic
    millisecond purely to exercise scheduler logic, never to forecast speed.
    """
    order = topo(g)
    weight = {v: (max(1, (kernels[rule_ids[v]]['duration_ms'] or 1))
                  if v in rule_ids else 0) for v in order}
    tail = {}
    for v in reversed(order):
        tail[v] = weight[v] + max((tail[u] for u in g.outgoing.get(v, ())),default=0)
    remaining = {v:len(g.incoming.get(v, ())) for v in order}
    waiting=[]
    serial=0
    now=0
    active=[]
    completed=0
    max_active=0
    for v in order:
        if remaining[v] == 0:
            heapq.heappush(waiting,(-tail[v],serial,v));serial+=1
    # This is a *real ready-queue scheduler simulation* over all graph nodes;
    # actual command invocation stays with Ninja until depfile/restat parity.
    while waiting or active:
        # Traverse zero-cost routing nodes immediately, even with full CPU pool.
        postponed=[]
        while waiting:
            _,_,v=heapq.heappop(waiting)
            if weight[v] == 0:
                completed+=1
                for child in g.outgoing.get(v,()):
                    remaining[child]-=1
                    if remaining[child]==0:
                        heapq.heappush(waiting,(-tail[child],serial,child));serial+=1
            else:
                postponed.append(v)
        for v in postponed:
            heapq.heappush(waiting,(-tail[v],serial,v));serial+=1
        while waiting and len(active) < jobs:
            _,_,v=heapq.heappop(waiting)
            heapq.heappush(active,(now+weight[v],serial,v));serial+=1
            max_active=max(max_active,len(active))
        if active:
            now=active[0][0]
            while active and active[0][0]==now:
                _,_,v=heapq.heappop(active)
                completed+=1
                for child in g.outgoing.get(v,()):
                    remaining[child]-=1
                    if remaining[child]==0:
                        heapq.heappush(waiting,(-tail[child],serial,child));serial+=1
        elif waiting:
            raise RuntimeError('No executable events despite ready work')
    if completed != len(order):
        raise RuntimeError(f'Simulation incomplete {completed}/{len(order)}')
    print('\n=== EVENT-DRIVEN READY-QUEUE SIMULATION ===')
    print(f'  scheduled vertices: {completed:,}; CPU slots: {jobs}; peak concurrent jobs: {max_active}')
    print(f'  modeled duration: {now/1000:.2f}s (1 ms synthetic cost for unmeasured kernels)')
    print('  This is NOT a build-time prediction or an independent build executor.')
    print('  Routing nodes complete immediately; no wave-wide synchronization.')
    return now


def memory_regions(kernels: dict, root: Path, build: Path):
    """Analyze materialized file regions, NOT C/C++/Python heap allocations.

    Lifetime: producer output until last declared direct consumer. This does not
    authorize deleting any output; cached artifacts, depfiles and external
    consumers may require indefinite retention.
    """
    producer = {}
    for ident, k in kernels.items():
        for path in k['outputs']:
            if path.startswith('@') and path not in producer:
                producer[path] = ident
    consumers = defaultdict(set)
    for ident,k in kernels.items():
        for inp in k['inputs']:
            if inp in producer and producer[inp] != ident:
                consumers[inp].add(ident)
    file_bytes = 0
    known = 0
    examples=[]
    regions=[]
    for path, ident in producer.items():
        if path.startswith('@build/'):
            actual = build / path[len('@build/'):]
        elif path.startswith('@repo/'):
            actual = root / path[len('@repo/'):]
        else:continue
        try:
            st=actual.stat()
        except (FileNotFoundError, OSError):
            size=None
        else:
            size=st.st_size if actual.is_file() else None
        if size is not None:
            known+=1
            file_bytes+=size
            examples.append((size, path, len(consumers[path])))
        regions.append({'path':path,'producer':ident,'size_bytes':size,
                        'direct_consumers':len(consumers[path]),
                        'note':'File-backed artifact; size != heap RSS. Never auto-delete.'})
    print('\n=== MATERIALIZED FILE REGION OWNERSHIP ===')
    print(f'Outputs with a unique producing kernel: {len(producer):,}')
    print(f'Existing outputs with known file length: {known:,}')
    print(f'Aggregate known output lengths: {file_bytes/1024/1024:.1f} MiB (not physical RAM)')
    print('Largest produced artifacts (bytes, #declared direct consumers):')
    for size, path, fanout in sorted(examples,reverse=True)[:12]:
        print(f'  {size/1024/1024:8.1f} MiB   {fanout:4d} readers   {path[:96]}')
    print('No file cleanup, mmap, or heap-allocation inference is performed.')
    return regions


def self_test():
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
        root=Path(d)
        build=root/'build/native'
        lines=['digraph ninja {',
               '"s" [label="source.c"]',
               '"r1" [label="C_COMPILER",shape=ellipse]',
               '"o1" [label="obj1.o"]',
               '"o2" [label="obj2.o"]',
               '"p" [label="phony",shape=ellipse]',
               '"alias" [label="all_objects"]',
               '"r2" [label="C_LINKER",shape=ellipse]',
               '"final" [label="heartgold"]',
               '"s" -> "r1"',
               '"r1" -> "o1"', '"r1" -> "o2"',
               '"o2" -> "p"', '"p" -> "alias"',
               '"o1" -> "r2"', '"alias" -> "r2"',
               '"r2" -> "final"', '}']
        g=Graph.from_dot(lines)
        k, ids=extract_kernels(g,root,build)
        assert len(k)==2, len(k)
        compilations=[v for v in k.values() if len(v['outputs'])==2]
        assert len(compilations)==1
        linker=next(v for v in k.values() if v not in compilations)
        assert 'all_objects' in ' '.join(linker['inputs'])
        g2=Graph.from_dot([x.replace('"r1"','"z99"').replace('"r2"','"z100"') for x in lines])
        k2,_=extract_kernels(g2,root,build)
        assert set(k)==set(k2), 'IDs must ignore ephemeral graph pointer identities'
        chain,ms,total=critical_path(g,k,ids,'heartgold')
        assert len(chain)==2 and ms==total==0
        simulated=simulate_ready_queue(g,k,ids,2)
        assert simulated==2
    print('SELF-TEST PASS: multi-output dedup, phony dependencies, stable IDs, acyclic chain')


def mem_ps_tree(pid: int):
    try:
        data = subprocess.check_output(['ps','-axo','pid=,ppid=,rss=,comm='], text=True)
    except subprocess.CalledProcessError:
        return 0, []
    rows = {}
    children = defaultdict(list)
    for line in data.splitlines():
        bits=line.split(None,3)
        if len(bits)<4: continue
        try: p,ppid,rss=map(int,bits[:3])
        except ValueError: continue
        rows[p]=(rss,bits[3]); children[ppid].append(p)
    queue = deque([pid]); seen = set(); total=0; members=[]
    while queue:
        p=queue.popleft()
        if p in seen: continue
        seen.add(p)
        if p in rows:
            rss,name=rows[p]; total+=rss; members.append((rss,Path(name).name))
        queue.extend(children.get(p, ()))
    return total, members


def run_ninja(build:Path, jobs:int, target:str, sample:bool):
    print(f'\n=== EXECUTE with proven Ninja backend: {target}, -j{jobs} ===',flush=True)
    print('This first kernel scheduler version does NOT replay commands independently.',flush=True)
    start=time.monotonic()
    proc = subprocess.Popen(['ninja','-C',str(build),f'-j{jobs}',target])
    peak=0; by_name=defaultdict(int)
    try:
        while proc.poll() is None:
            if sample:
                rss, members=mem_ps_tree(proc.pid)
                peak=max(peak,rss)
                for size,name in members: by_name[name]=max(by_name[name],size)
            time.sleep(0.2)
    except KeyboardInterrupt:
        proc.send_signal(2)
        proc.wait()
        raise
    result=proc.wait()
    print(f'\nNinja wall time: {time.monotonic()-start:.2f}s; exit={result}',flush=True)
    if sample:
        print(f'Peak sampled sum RSS: {peak/1024:.1f} MiB (shared pages counted repeatedly)')
        for name,size in sorted(by_name.items(),key=lambda x:-x[1])[:15]:
            print(f'  {size/1024:8.1f} MiB  {name}')
        print('Sampling misses short-lived processes and cannot attribute mallocs to edges.')
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path.cwd())
    ap.add_argument('--build-dir',type=Path)
    ap.add_argument('--capture',type=Path,help='read existing 110 MB capture rather than invoking Ninja')
    ap.add_argument('--output',type=Path,help='optional JSON kernel plan (overwrites atomically)')
    ap.add_argument('--build',action='store_true',help='execute through Ninja while we establish parity')
    ap.add_argument('--jobs',type=int,default=8)
    ap.add_argument('--target',default='all')
    ap.add_argument('--trace-memory',action='store_true',help='sample build process tree RSS')
    ap.add_argument('--regions',action='store_true',help='inventory materialized output regions and consumer counts')
    ap.add_argument('--simulate',action='store_true',help='event-driven ready-queue scheduling simulation, never builds')
    ap.add_argument('--self-test',action='store_true',help='run scheduler invariant tests without reading build')
    args=ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    root=args.root.resolve()
    build=(args.build_dir or (root/'build/native')).resolve()
    if not args.capture and not (build/'build.ninja').is_file():
        ap.error(f'{build}/build.ninja not found; nothing was built/changed')
    if args.jobs<1: ap.error('--jobs must be positive')
    if args.capture:
        print(f'Reconstructing kernels from: {args.capture}',flush=True)
        g=Graph.from_capture(args.capture)
    else:
        print(f'Querying configured Ninja DAG: {build}',flush=True)
        raw=subprocess.run(['ninja','-C',str(build),'-t','graph'],check=True,capture_output=True,text=True)
        g=Graph.from_dot(raw.stdout.splitlines())
    kernels,rule_ids=extract_kernels(g,root,build)
    hits=attach_ninja_log(kernels,build)
    path,chain,total=critical_path(g,kernels,rule_ids,args.target)
    summary(g,kernels,hits,path,chain,total)
    if args.simulate:
        simulate_ready_queue(g,kernels,rule_ids,args.jobs)
    regions=memory_regions(kernels,root,build) if args.regions else None
    if args.output:
        output=args.output.resolve()
        if output == build or output == root: ap.error('Output cannot overwrite a directory')
        payload={'schema':1,'root':str(root),'build':str(build),'note':'Complete compact graph, including artifacts and phony barriers. Rule names/output contracts are observed, not hermetic command fingerprints. This is a planning IR, NOT a verified independent command-execution manifest. Ninja retains dynamic dependency/restat execution semantics.', 'kernels':list(kernels.values()),'graph':compact_graph(g,rule_ids,root,build)}
        if regions is not None: payload['file_regions']=regions
        pending=output.with_name(output.name+'.partial')
        with pending.open('w') as f:json.dump(payload,f,separators=(',',':'))
        os.replace(pending,output)
        print(f'JSON kernel plan: {output} ({output.stat().st_size/1024/1024:.1f} MiB)')
    if args.build:
        return run_ninja(build,args.jobs,args.target,args.trace_memory)
    return 0

if __name__=='__main__':
    sys.exit(main())
