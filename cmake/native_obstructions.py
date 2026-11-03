"""Classify actual failed links and incomplete images using artifact-backed graph evidence.

Source candidates are identified separately from compiled definitions. They never
become linker permissions or a successful provider claim.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re


def source_candidates(game, images):
    owners=defaultdict(list)
    for name,image in images.items():
        for member in image['members']:
            source=member.get('source')
            if not source:continue
            path=game/source
            if not path.is_file():continue
            text=path.read_text()
            text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
            # Function bodies, including original asm functions, not declarations.
            symbols=set(re.findall(r'(?m)^[A-Za-z_][\w \t*]*\b(\w+)\s*\([^;{}]*\)\s*\{',text))
            if member['kind']=='assembly':
                symbols.update(re.findall(r'(?m)^([A-Za-z_.$][\w.$]*):',text))
                symbols.update(re.findall(r'(?m)^\s*(?:thumb_func_start|arm_func_start)\s+(\w+)',text))
            for symbol in symbols:
                owners['_'+symbol].append(dict(image=name,object=member['object'],source=source,
                    representation=member['status'],compiled=bool(member['artifacts']),
                    evidence='source definition candidate; not a compiled export'))
    return owners


def obstruction_graph(graph, game):
    images=graph['images'];candidates=source_candidates(game,images)
    roots=defaultdict(set);records={}
    for name,image in images.items():
        actual=image.get('actual_link_undefined_symbols')
        failed=bool(actual) and image['link_status']!='linked'
        if not failed and not image['missing_members']:continue
        scope='actual image link' if failed else 'observed object imports; missing members have unknown imports'
        references=actual if failed else image['imports']
        symbols={}
        for symbol in references:
            owners=image['providers'].get(symbol,[])
            native=image['native_main_providers'].get(symbol,[])
            system=image['system_providers'].get(symbol,[])
            sources=candidates.get(symbol,[])
            if owners:
                incomplete=[o for o in owners if images[o]['missing_members']]
                category='compiled provider in incomplete image' if incomplete else 'compiled original provider'
                for owner in incomplete:roots['image:'+owner].add(name)
            elif native:
                category='actual main-link input provider'
            elif system:
                category='actual system provider'
            elif sources:
                category='original source candidate without compiled export'
                for source in sources:
                    family='/'.join(Path(source['source']).parts[:2])
                    roots['source:'+family].add(name)
            else:
                category='no established original implementation'
                roots['unestablished provider'].add(name)
            symbols[symbol]=dict(category=category,original_images=owners,main_inputs=native,
                system_inputs=system,source_candidates=sources)
        missing=[]
        for member in image['members']:
            if member['object'] not in image['missing_members']:continue
            if member['kind']=='missing':category='original source absent at manifest path'
            elif (member.get('source') and member['kind'] in ('C','C++') and
                    re.search(r'(?m)^\s*asm\b',(game/member['source']).read_text())):
                category='original ARM inline implementation needs native representation'
            elif member['status']=='available':category='representation available; complete image not selected or object not emitted'
            elif member['kind']=='assembly' and 'Executable ARM/Thumb instructions' in member.get('classification',{}).get('classes',[]):category='original ARM implementation needs native representation'
            elif member['kind']=='assembly':category='data/consumer ABI contract or unsupported assembly directive'
            else:category='unrepresented original member'
            missing.append(dict(object=member['object'],category=category,reason=member.get('reason'),source=member.get('source')))
        records[name]=dict(scope=scope,actual_failed_link=failed,missing_members=missing,symbols=symbols)
    ranked=[dict(root=root,affected_images=sorted(names),image_count=len(names)) for root,names in roots.items()]
    ranked.sort(key=lambda r:(-r['image_count'],r['root']))
    return dict(scope='Direct observed obstructions, ranked by distinct affected images; no projected closure guarantees.',
        roots=ranked,images=records)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graph',type=Path,required=True)
    parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=obstruction_graph(json.loads(args.graph.read_text()),args.game)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result['roots']))
