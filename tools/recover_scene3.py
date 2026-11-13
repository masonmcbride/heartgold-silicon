#!/usr/bin/env python3
"""Read-only provenance recovery; never replays or copies checkpoint objects.

The executable and its link map are primary evidence. Saved manifests and
nearby compilation records are checked, not assumed to describe that binary.
All output belongs to a selected binary directory.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cmake'))
from native_image_graph import parse_manifest,ownership


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def link_map(text):
    objects={int(i):dict(input=p,live_symbols=[]) for i,p in
             re.findall(r'^\[\s*(\d+)\]\s+(.+)$',text.split('# Sections:')[0],re.M)}
    live=text.split('# Symbols:',1)[1].split('# Dead Stripped Symbols:',1)[0]
    for address,size,index,name in re.findall(
            r'^(0x[\da-fA-F]+)\s+(0x[\da-fA-F]+)\s+\[\s*(\d+)\]\s+(.+)$',live,re.M):
        objects[int(index)]['live_symbols'].append(dict(name=name,address=int(address,16),size=int(size,16)))
    return objects


def compile_records(paths,root):
    """Recover recorded input/output pairs, not inferred executable semantics."""
    records=defaultdict(list)
    def absolute(value):
        p=Path(value)
        return str(p.resolve() if p.is_absolute() else (root/p).resolve())
    def visit(node,path):
        if isinstance(node,dict):
            args=node.get('command',node.get('arguments'))
            if isinstance(args,list) and '-c' in args and '-o' in args:
                source=args[args.index('-c')+1];output=args[args.index('-o')+1]
                records[absolute(output)].append(dict(source=source,record=str(path),command=args))
            elif isinstance(node.get('source'),str) and isinstance(node.get('object'),str):
                records[absolute(node['object'])].append(dict(source=node['source'],record=str(path)))
            for value in node.values():visit(value,path)
        elif isinstance(node,list):
            for value in node:visit(value,path)
    for path in sorted(paths):
        try:visit(json.loads(path.read_text()),path)
        except (ValueError,UnicodeError):continue
    return records


def current_link(build):
    if (build/'build.ninja').exists():
        cache=(build/'CMakeCache.txt').read_text()
        make=re.search(r'^CMAKE_MAKE_PROGRAM:FILEPATH=(.+)$',cache,re.M)[1]
        text=subprocess.run([make,'-C',str(build),'-t','commands','heartgold'],
                            capture_output=True,text=True,check=True).stdout
        lines=[line for line in text.splitlines() if re.search(r' -o (?:\S*/)?heartgold(?: |$)',line)]
        if len(lines)!=1:raise ValueError('Expected one current heartgold link command')
        text=lines[0].removeprefix(': && ').split(' && ',1)[0]
    else:text=(build/'CMakeFiles/heartgold.dir/link.txt').read_text()
    args=shlex.split(text)
    return dict(arguments=args,working_directory=str(build),inputs=[str((build/p).resolve())
                if not Path(p).is_absolute() else p for p in args if p.endswith(('.o','.a','.dylib'))])


def recover(root,executable,manifest_path,map_path,out,current_build=None):
    if out.is_relative_to(executable.parent):
        raise ValueError('Recovery output must not modify the historical reference directory')
    game=root/'upstream/pokeheartgold'
    images=parse_manifest(game/'main.lsf');owners=ownership(images)
    by_name=defaultdict(list)
    by_hash=defaultdict(list)
    for member in owners:
        by_name[Path(member).name].append(member)
        for suffix in ('.c','.cpp','.s'):
            source=member[:-2]+suffix
            if (game/source).is_file():by_hash[hashlib.sha256(source.encode()).hexdigest()[:12]].append(member)
    native_sources=defaultdict(list)
    for directory in ('upstream/libntr','hardware_drivers','cmake','native-adaptations','tests'):
        for path in (root/directory).rglob('*'):
            if path.suffix in ('.c','.cpp','.mm','.s','.S') and path.is_file():
                native_sources[path.stem].append(str(path.relative_to(root)))
    manifest=json.loads(manifest_path.read_text());cwd=Path(manifest['working_directory'])
    objects=link_map(map_path.read_text())
    def resolve(value):
        p=Path(value);return p if p.is_absolute() else cwd/p
    paths=[]
    for item in objects.values():
        match=re.fullmatch(r'(.+\.a)\((.+)\)',item['input'])
        item.update(archive=match[1] if match else None,member=match[2] if match else None)
        if item['input']=='linker synthesized':continue
        item['artifact']=str(resolve(match[1] if match else item['input']).resolve())
        paths.append(Path(item['artifact']))
    contract_paths=set()
    for path in set(paths):
        for directory in (path.parent,path.parent.parent):
            if directory.is_relative_to(root/'build'):
                contract_paths.update(p for p in directory.glob('*.json')
                                      if 'link-manifest' not in p.name and p.stat().st_size<10*1024*1024)
    records=compile_records(contract_paths,root)
    for index,item in objects.items():
        item['index']=index
        if 'artifact' not in item:continue
        name=item['member'] or Path(item['artifact']).name
        item['input_kind']=('archive_member' if item['member'] else
                            'dynamic_interface' if Path(name).suffix in ('.dylib','.tbd') else
                            'object')
        original=re.sub(r'\.(?:c|cpp|cc|s|S)\.o$','.o',name)
        candidates=by_name.get(Path(original).name,[])
        hashed=re.fullmatch(r'(?:closure|provider)_([0-9a-f]{12})\.o',name)
        if hashed:candidates=by_hash.get(hashed[1],[])
        item['original_member_candidates']=candidates
        item['original_image_candidates']=sorted({i for p in candidates for i in owners[p]})
        item['compilation_records']=records.get(item['artifact'],[]) if not item['member'] else []
        stem=re.sub(r'\.(?:c|cpp|cc|s|S)$','',Path(name).stem)
        item['native_source_candidates']=native_sources.get(stem,[])
        # A generated translation unit's filename is evidence of an input, not
        # evidence that a source-controlled producer for that input exists.
        item['producer_verified']=False
        if item['input_kind']=='dynamic_interface':
            item['source_mapping']='dynamic import interface; implementation belongs to its provider image'
        elif len(candidates)==1:
            item['source_mapping']='unique original member basename; transformation still needs validation'
        elif item['compilation_records']:
            item['source_mapping']='recorded compilation input; generation still needs validation'
        elif item['native_source_candidates']:
            item['source_mapping']='native source basename candidate; compilation and original ownership still need validation'
        else:item['source_mapping']='unresolved source provenance'
    checks=[]
    for entry in manifest['inputs']:
        path=resolve(entry['path']);actual=digest(path) if path.is_file() else None
        checks.append(dict(**entry,present=actual is not None,current_sha256=actual,
                           matches_recorded_hash=actual==entry['sha256']))
    nm=subprocess.run(['nm','-n','-gU',str(executable)],capture_output=True,text=True,check=True).stdout
    addresses={name:int(address,16) for address,name in
               re.findall(r'^([\da-fA-F]+)\s+\S\s+(\S+)$',nm,re.M)}
    mismatches=[];matched=0
    for item in objects.values():
        for symbol in item['live_symbols']:
            if symbol['name'] not in addresses:continue
            if addresses[symbol['name']]!=symbol['address']:mismatches.append(symbol)
            else:matched+=1
    loads=subprocess.run(['otool','-L',str(executable)],capture_output=True,text=True,check=True).stdout
    libraries=[line.strip().split(' (compatibility',1)[0] for line in loads.splitlines()[1:]]
    dynamic_ids=sorted(int(m[1]) for p in libraries if (m:=re.search(r'libheartgold_image_(\d+)\.dylib',p)))
    direct_owners=Counter()
    for item in objects.values():
        if item['live_symbols'] and len(item.get('original_image_candidates',[]))==1:
            direct_owners[item['original_image_candidates'][0]]+=1
    report=dict(schema=1,scope='Read-only recovery evidence, not a source-reproduction or runtime-success claim',
                executable=dict(path=str(executable),sha256=digest(executable)),
                manifest=str(manifest_path),link_map=str(map_path),
                map_validation=dict(matched_public_symbol_addresses=matched,mismatches=mismatches),
                input_hash_checks=checks,objects=list(objects.values()),load_commands=libraries,
                dynamically_linked_original_image_ids=dynamic_ids,
                explicitly_linked_member_owner_counts=dict(sorted(direct_owners.items())),
                original_overlays_not_in_load_commands=[n for n,i in images.items()
                    if i['kind']=='Overlay' and i['id'] not in dynamic_ids],
                counters=dict(map_objects=len(objects),objects_with_live_symbols=sum(bool(o['live_symbols']) for o in objects.values()),
                    dynamic_interfaces=sum(o.get('input_kind')=='dynamic_interface' for o in objects.values()),
                    input_files=len(checks),input_files_absent=sum(not c['present'] for c in checks),
                    input_hash_mismatches=sum(c['present'] and not c['matches_recorded_hash'] for c in checks),
                    object_source_provenance_unresolved=sum(o.get('source_mapping')=='unresolved source provenance' for o in objects.values())),
                caveats=['A link-map input can have no surviving symbols.',
                         'A matching basename is not a proven source transformation.',
                         'A recorded compiler command does not regenerate its generated source.',
                         'LC_LOAD_DYLIB records physical linkage, not original FS overlay activation.',
                         'Missing source provenance remains a blocker; historical compiled inputs are never production sources.'])
    if current_build:
        current=current_link(current_build)
        historical={Path(p['path']).name for p in manifest['inputs']}
        present={Path(p).name for p in current['inputs']}
        report['current_link_comparison']=dict(current=current,
            comparison_unit='artifact basename only; no equivalence of archive contents is implied',
            historical_only=sorted(historical-present),current_only=sorted(present-historical),
            shared_basenames=sorted(present&historical))
    out.mkdir(parents=True,exist_ok=True)
    (out/'historical-link.json').write_text(json.dumps(report,indent=2)+'\n')
    rows=['# Historical Scene 3 link recovery','',report['scope'],'',
          f"Map: {len(objects)} inputs; {matched} public symbol addresses match the executable; {len(mismatches)} mismatches.",
          f"Manifest: {len(checks)} inputs; {report['counters']['input_files_absent']} absent; {report['counters']['input_hash_mismatches']} hash mismatches.",'',
          '| Original member candidate / recorded source | Image candidate | Actual link input | Live symbols |',
          '| --- | --- | --- | --- |']
    for item in objects.values():
        sources=item.get('original_member_candidates',[]) or [r['source'] for r in item.get('compilation_records',[])]
        rows.append('| '+ ' | '.join([', '.join(sources) or 'UNRESOLVED',', '.join(item.get('original_image_candidates',[])) or 'UNRESOLVED',item['input'],str(len(item['live_symbols']))])+' |')
    (out/'historical-members.md').write_text('\n'.join(rows)+'\n')
    print(json.dumps(report['counters'],indent=2));print('Map symbol address mismatches:',len(mismatches))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--executable',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--map',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--current-build',type=Path)
    a=p.parse_args()
    recover(a.root.resolve(),a.executable.resolve(),a.manifest.resolve(),a.map.resolve(),a.out.resolve(),
            a.current_build.resolve() if a.current_build else None)


if __name__=='__main__':main()
