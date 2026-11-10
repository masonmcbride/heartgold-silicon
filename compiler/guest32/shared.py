"""Joint guest storage/code planning, retaining separate original image members.

This is a compile-time linker plan, not an import registry or a residency manager.
Known original addresses are preserved. Unnamed C constants use relocatable guest
coordinates after the known data; their original absolute addresses are unknown.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from original_layout import MAIN_BASE, MAIN_SIZE
from code_ids import allocate as allocate_code_addresses
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'cmake'))
from native_data_layouts import contracts,validate_inputs
from native_image_graph import parse_manifest


def plan(catalogs, previous=None):
    result = dict(images={}, globals={}, codes=[], register_edges=[])
    previous = previous or {}
    occupied = []
    pending = []
    pending_aliases = []
    pending_sections = []
    functions = {}
    seen_register_edges = set()
    for owner, original in sorted(catalogs.items()):
        c = copy.deepcopy(original)
        # Repeated identical original registration metadata is one edge.
        # Distinct records remain visible to the lowerer's conflict checks.
        for edge in c['register_edges']:
            fingerprint = json.dumps(
                edge, sort_keys=True, separators=(',', ':')
            )
            if fingerprint in seen_register_edges:
                continue
            seen_register_edges.add(fingerprint)
            result['register_edges'].append(edge)
        assembly = c['original_assembly_globals']
        # C aliases are grouped by overlapping ORIGINAL-plan extents, never by
        # spelling or adjacency. Existing source-validated groups provide these.
        groups = []
        for key, view in sorted(c['c_globals'].items(), key=lambda item:item[1]['offset']):
            start, end = view['offset'], view['offset']+view['size']
            if groups and start < groups[-1]['end']:
                groups[-1]['end'] = max(end, groups[-1]['end'])
                groups[-1]['views'][key] = view
            else:
                groups.append(dict(start=start, end=end, views={key:view}))
        projected = {}
        prior_views = previous.get('images', {}).get(owner, {}).get('c_globals', {})
        for group in groups:
            anchors = set()
            pinned = set()
            for key, view in group['views'].items():
                m = re.fullmatch(r'ov\d+_([0-9A-Fa-f]{8})', key)
                if m:anchors.add(int(m[1],16) - (view['offset']-group['start']))
                old = prior_views.get(key)
                if old is not None:
                    if old['size'] != view['size']:
                        raise ValueError('changed guest C object extent: '+owner+' / '+key)
                    pinned.add(old['offset'] - (view['offset']-group['start']))
            if len(anchors)>1:raise ValueError('inconsistent C address anchors: '+owner)
            if len(pinned)>1:raise ValueError('inconsistent pinned C coordinates: '+owner)
            if anchors and pinned and anchors != pinned:
                raise ValueError('original anchor conflicts with pinned C storage: '+owner)
            if anchors or pinned:
                base=next(iter(anchors or pinned))
                for key, view in group['views'].items():
                    projected[key]=dict(offset=base+view['offset']-group['start'],size=view['size'])
                occupied.append((base,base+group['end']-group['start'],owner))
            else:pending.append((owner,group))
        # An original section is one allocation, not one allocation per label.
        # Missing historical coordinates do not imply permission to relocate.
        section_plans = {}
        for section in c.get('assembly_sections', []):
            identity = (section['object'], section['section'])
            if identity in section_plans:
                raise ValueError('duplicate assembly section: '+repr(identity))
            section_plans[identity] = section

        section_coordinates = {}
        for identity, section in sorted(section_plans.items()):
            labels = section['labels']
            size = section['size']
            provisional = section['offset']
            if size < 0:
                raise ValueError('negative assembly section extent: '+repr(identity))
            for name, off in labels.items():
                view = c['assembly_globals'].get(name)
                if view != dict(offset=provisional+off, size=size-off):
                    raise ValueError('inconsistent assembly section view: '+name)
            historical = section['original_placement']
            if historical is not None:
                base = historical['address']
                if historical['size'] != size:
                    raise ValueError('historical section extent mismatch: '+repr(identity))
                for name, off in labels.items():
                    if assembly.get(name) != dict(offset=base+off,size=size-off):
                        raise ValueError('historical section coordinate mismatch: '+name)
                section_coordinates[identity] = base
                continue

            # A section already represented by C storage is not allocated twice.
            # Such aliases are resolved after all C groups have been assigned.
            if labels and all(any(
                    v['offset'] <= provisional+off and
                    provisional+size <= v['offset']+v['size']
                    for v in c['c_globals'].values())
                    for off in labels.values()):
                continue

            # Admit sections described by the original assembly parser.
            # Historical address verification remains mandatory above.
            # New sections receive relocatable Guest32 coordinates below.
            if not re.fullmatch(r"[0-9a-f]{64}", section.get("source_sha256", "")):
                raise ValueError("invalid original assembly source hash: "+repr(identity))
            if not re.fullmatch(r"[0-9a-f]{64}", section.get("bytes_sha256", "")):
                raise ValueError("missing original assembly bytes certificate: "+repr(identity))
            if section["size"] <= 0 or not labels:
                raise ValueError("invalid original assembly section extent or labels: "+repr(identity))
            if any(not isinstance(off,int) or not 0 <= off < size for off in labels.values()):
                raise ValueError("assembly label outside section: "+repr(identity))
            relocations = section.get("relocations")
            if not isinstance(relocations,list) or len(relocations) != section["relocation_count"]:
                raise ValueError("missing original assembly relocation records: "+repr(identity))
            spans = []
            for ref in relocations:
                off, width = ref["offset"], ref["width"]
                if not isinstance(off,int) or width not in (1,2,4) or not 0 <= off <= size-width:
                    raise ValueError("invalid assembly relocation span: "+repr(identity))
                if not isinstance(ref.get("expression"),str) or not ref["expression"]:
                    raise ValueError("invalid assembly relocation expression: "+repr(identity))
                spans.append((off,off+width))
            spans.sort()
            if any(a[1] > b[0] for a,b in zip(spans,spans[1:])):
                raise ValueError("overlapping assembly relocations: "+repr(identity))
            prior_sections = previous.get('images',{}).get(owner,{}).get('assembly_sections',{})
            stable_key = identity[0]+'|'+identity[1]
            prior = prior_sections.get(stable_key)
            if prior is not None:
                if (prior['size'] != size or
                        prior['source_sha256'] != section['source_sha256'] or
                        prior['labels'] != labels):
                    raise ValueError('changed pinned assembly section: '+stable_key)
                base = prior['offset']
                occupied.append((base,base+size,owner))
                section_coordinates[identity] = base
                for name,off in labels.items():
                    assembly[name] = dict(offset=base+off,size=size-off)
            else:
                pending_sections.append((owner,identity,section))
        # Legacy C-owned aliases are resolved after pending C allocations.
        pending_aliases.append((owner,c['assembly_globals'],c['c_globals'],
                                assembly,projected))
        # Assembly view sizes extend to section end; collapse overlapping views
        # within one owner before checking peer ownership.
        spans=[]
        for view in sorted(assembly.values(),key=lambda v:v['offset']):
            start,end=view['offset'],view['offset']+view['size']
            if spans and start<spans[-1][1]:spans[-1]=(spans[-1][0],max(spans[-1][1],end))
            else:spans.append((start,end))
        occupied.extend((start,end,owner) for start,end in spans if end>start)
        result['images'][owner]=dict(assembly_globals=assembly,c_globals=projected,
                                     assembly_sections={
                                         obj+'|'+sec:dict(offset=base,
                                             size=section_plans[(obj,sec)]['size'],
                                             source_sha256=section_plans[(obj,sec)]['source_sha256'],
                                             labels=section_plans[(obj,sec)]['labels'])
                                         for (obj,sec),base in section_coordinates.items()})
        for f in c['codes']:
            old=functions.get(f['key'])
            if old and old['definition'] and f['definition']:
                signature=('origin','origin_line','body_hash','params',
                           'return','local','native','varargs')
                identical=all(old.get(k)==f.get(k) for k in signature)
                shared_header=(
                    old.get('origin') and
                    Path(old['origin']).suffix=='.h' and
                    not old.get('local') and not f.get('local')
                )
                explicit=bool(old.get('coalesce') and f.get('coalesce'))
                if not (identical and (explicit or shared_header)):
                    raise ValueError('multiple guest code owners: '+f['key'])
                # Preserve canonical provenance; subsequent identical header
                # definitions reuse the same synthetic guest code identity.
                chosen=dict(old)
                chosen['coalesce']=True
            else:
                chosen=dict(f if not old or f['definition'] else old)
            chosen['address_taken']=f['address_taken'] or bool(old and old['address_taken'])
            functions[f['key']]=chosen
    for start,end,owner in occupied:
        if start<MAIN_BASE or end>MAIN_BASE+MAIN_SIZE:raise ValueError('storage outside DS RAM')
        for other_start,other_end,peer in occupied:
            if peer!=owner and start<other_end and other_start<end:
                raise ValueError('overlapping image storage: '+owner+' / '+peer)
    cursor=(max([MAIN_BASE, *[end for _,end,_ in occupied],
                 previous.get('static_end', MAIN_BASE)])+15)&~15
    for owner,group in pending:
        for key,view in group['views'].items():
            result['images'][owner]['c_globals'][key]=dict(
                offset=cursor+view['offset']-group['start'],size=view['size'])
        cursor=(cursor+group['end']-group['start']+15)&~15

    # Allocate complete admitted assembly sections after existing C allocations.
    for owner,identity,section in pending_sections:
        cursor=(cursor+15)&~15
        base=cursor
        cursor+=section['size']
        key=identity[0]+'|'+identity[1]
        result['images'][owner]['assembly_sections'][key]=dict(
            offset=base,size=section['size'],
            source_sha256=section['source_sha256'],
            labels=section['labels'])
        for name,off in section['labels'].items():
            result['images'][owner]['assembly_globals'][name]=dict(
                offset=base+off,size=section['size']-off)

    # Resolve original C aliases only after every C group is placed.
    for owner,original_assembly,original_c,assembly,projected in pending_aliases:
        final_c=result['images'][owner]['c_globals']
        for name,view in original_assembly.items():
            if name in assembly:
                continue
            matches=[(key,v) for key,v in original_c.items()
                     if v['offset']<=view['offset'] and
                     view['offset']+view['size']<=v['offset']+v['size']
                     and key in final_c]
            if not matches:
                raise ValueError('unplaced original alias: '+name)
            values={final_c[key]['offset']+view['offset']-v['offset']
                    for key,v in matches}
            if len(values)!=1:
                raise ValueError('inconsistent alias coordinates: '+name)
            assembly[name]=dict(offset=values.pop(),size=view['size'])

    # Check final relocatable allocations against all pinned/original intervals.
    allocated=[]
    for owner,group in pending:
        views=result['images'][owner]['c_globals']
        first=next(iter(group['views']))
        base=views[first]['offset']-(group['views'][first]['offset']-group['start'])
        allocated.append((base,base+group['end']-group['start'],owner))
    for owner,identity,section in pending_sections:
        base=result['images'][owner]['assembly_sections'][identity[0]+'|'+identity[1]]['offset']
        allocated.append((base,base+section['size'],owner))
    for start,end,owner in allocated:
        if start<MAIN_BASE or end>MAIN_BASE+MAIN_SIZE:
            raise ValueError('relocatable storage outside DS RAM: '+owner)
        for other_start,other_end,peer in occupied+allocated:
            if (start,end,owner)==(other_start,other_end,peer):
                continue
            if start<other_end and other_start<end:
                raise ValueError('overlapping allocated storage: '+owner+' / '+peer)
    if cursor>=MAIN_BASE+MAIN_SIZE:raise ValueError('guest static storage exhausted')
    for owner,c in result['images'].items():
        for name,view in [*c['assembly_globals'].items(),*c['c_globals'].items()]:
            if '|' in name:continue
            if name in result['globals']:raise ValueError('multiple storage owners: '+name)
            result['globals'][name]=view
    code_addresses=allocate_code_addresses(functions, previous.get('codes', []))
    for key in sorted(functions):
        f=functions[key];f['address']=code_addresses[key]
        result['codes'].append(f)
    result['static_end']=cursor
    result['scope']='joint original data coordinates and relocatable C constants; separate explicit initializers; residency and native boundaries require admission'
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('game','build','out','llvm-bin','lowerer'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--images',nargs='+',default=['OVY_0','OVY_38'])
    p.add_argument('--prior-catalog',type=Path)
    a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'complete.stamp').unlink(missing_ok=True)
    driver=Path(__file__).with_name('image.py');archive=driver.with_name('archive.py')
    common=['--game',str(a.game),'--build',str(a.build),'--llvm-bin',str(a.llvm_bin),'--lowerer',str(a.lowerer)]
    catalogs={};manifest=parse_manifest(a.game/'main.lsf')
    for owner in a.images:
        directory=a.out/owner
        subprocess.run([sys.executable,'-B',str(driver),*common,'--image',owner,'--out',str(directory),'--plan-only'],check=True)
        catalogs[owner]=json.loads((directory/'plan.json').read_text())
    catalog=a.out/'shared.json'
    prior_path=a.prior_catalog or catalog
    if a.prior_catalog and not prior_path.is_file():
        raise ValueError('prior shared catalog missing: '+str(prior_path))
    previous=json.loads(prior_path.read_text()) if prior_path.is_file() else None
    merged=plan(catalogs, previous)
    # These are native-layout blockers, not permission to widen guest memory.
    # Reuse their source guards while leaving native recipe admission blocked.
    guarded={}
    for owner in a.images:
        for member in manifest[owner]['objects']:
            if member not in contracts():continue
            contract=contracts()[member];validate_inputs(a.game,contract)
            guarded.update(contract['inputs'])
    merged['source_guards']=guarded
    catalog.write_text(json.dumps(merged,indent=2)+'\n')
    for owner in a.images:
        directory=a.out/owner
        subprocess.run([sys.executable,'-B',str(driver),*common,'--image',owner,'--out',str(directory),'--shared-catalog',str(catalog)],check=True)
        subprocess.run([sys.executable,'-B',str(archive),'--coverage',str(directory/'coverage.json'),
                        '--image-dir',str(directory),'--archive',str(directory/f'libheartgold_overlay_{manifest[owner]["id"]}.a'),
                        '--ar',str(a.llvm_bin/'llvm-ar'),'--image-name',owner],check=True)
    dependencies={Path(__file__).resolve(),Path(__file__).with_name('code_ids.py').resolve(),driver,archive,a.game.resolve()/'main.lsf'}
    if a.prior_catalog and prior_path.resolve()!=catalog.resolve():
        dependencies.add(prior_path.resolve())
    dependencies.update(a.game.resolve()/path for path in guarded)
    for receipt in a.out.rglob('*.receipt.json'):
        dependencies.update(Path(path) for path in json.loads(receipt.read_text())['inputs']
                            if not Path(path).is_relative_to(a.out))
    def escape(path):return str(path).replace('\\','\\\\').replace(' ','\\ ').replace('#','\\#').replace('$','$$')
    (a.out/'shared.d').write_text(escape(a.out/'complete.stamp')+': '+' '.join(map(escape,sorted(dependencies)))+'\n')
    (a.out/'complete.stamp').write_text(hashlib.sha256(catalog.read_bytes()).hexdigest()+'\n')


if __name__=='__main__':main()
