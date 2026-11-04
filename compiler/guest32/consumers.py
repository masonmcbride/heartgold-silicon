"""Source-hashed census of every original six-member data label and consumer.

Lexical edges are review evidence, not a pointer escape or alias analysis. The
report deliberately leaves indirect/parameter-derived access proof outstanding.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cmake'))
from native_data_ir import parse,raw_layout
from native_image_graph import parse_manifest,source_record


def provider_demands(game,image_root,links):
    """Locate original definition text; retain alternatives, never select by name."""
    catalog=json.loads((image_root/'shared.json').read_text())
    names={'_guest32_'+f['name']:f['name'] for f in catalog['codes'] if not f['local']}
    names.update({'_'+f['native']:f['name'] for f in catalog['codes']})
    demands={}
    for ident in (0,38):
        link=json.loads((links/f'OVY_{ident}-global.json').read_text())
        for symbol in link['unresolved']:
            identity=(symbol[len('_guest32_address_'):] if symbol.startswith('_guest32_address_') else
                      symbol[len('_guest32_'):] if symbol.startswith('_guest32_') else symbol[1:])
            name=names.get(symbol,identity)
            row=demands.setdefault(name,dict(symbols=[],images=[],original_definitions=[]))
            if symbol not in row['symbols']:row['symbols'].append(symbol)
            row['images'].append(f'OVY_{ident}')
    token=re.compile(r'\b('+'|'.join(map(re.escape,sorted(demands,key=len,reverse=True)))+r')\b')
    for owner,image in parse_manifest(game/'main.lsf').items():
        for member in image['objects']:
            record=source_record(game,member)
            if not record.get('source'):continue
            source=game/record['source'];text=source.read_text()
            for match in token.finditer(text):
                name=match[0];line_start=text.rfind('\n',0,match.start())+1
                tail=text[match.end():];head=text[line_start:match.start()]
                kind=None
                if source.suffix=='.s' and re.match(r'\s*:',tail):kind='assembly label'
                elif source.suffix in ('.c','.cpp') and re.match(r'\s*\(',tail):
                    position=tail.index('(');depth=1;position+=1
                    while position<len(tail) and depth:
                        depth+=(tail[position]=='(')-(tail[position]==')');position+=1
                    if re.match(r'\s*\{',tail[position:]):kind='C function definition text'
                elif (source.suffix in ('.c','.cpp') and re.fullmatch(r'\s*[\w\s*]+\s+',head)
                      and not re.search(r'\b(?:extern|return|goto|case)\b',head)):
                    if re.match(r'\s*(?:\[[^\]]*\]\s*)?=(?!=)',tail):kind='initialized C data definition text'
                    elif re.match(r'\s*(?:\[[^\]]*\]\s*)?;',tail):kind='tentative C data definition text'
                if kind:
                    evidence=dict(owner=owner,member=member,source=record['source'],line=text.count('\n',0,match.start())+1,kind=kind,
                                  sha256=hashlib.sha256(source.read_bytes()).hexdigest())
                    if evidence not in demands[name]['original_definitions']:demands[name]['original_definitions'].append(evidence)
    for name,row in demands.items():
        declaration=next((f for f in catalog['codes'] if f['name']==name and not f['local']),None)
        row['guest_signature']={k:declaration[k] for k in ('params','return','varargs')} if declaration else None
        row['missing_capability']=('guest data coordinates with original ownership' if any(s.startswith('_guest32_address_') for s in row['symbols']) else
            'native provider implementation demanded by an existing typed scalar bridge' if any(not s.startswith('_guest32_') for s in row['symbols']) else
            'canonical original provider signature for non-prototype calls, or ARM32 variadic argument homes / verified typed boundary' if declaration and declaration['varargs'] else
            'guest compilation of original provider, or typed native boundary with layout, pointer and callback ownership checks')
    return demands


def census(game,image_root):
    manifest=parse_manifest(game/'main.lsf');owners=defaultdict(set)
    for image,record in manifest.items():
        for member in record['objects']:
            source=source_record(game,member).get('source')
            if source:owners[source].add(image)
    compiled=set();represented=set();definitions={};members=[]
    for ident in (0,38):
        directory=image_root/f'OVY_{ident}'
        coverage=json.loads((directory/'coverage.json').read_text())
        for record in coverage['members']:
            if record.get('compiled'):compiled.add(record['source'])
            if record['kind']!='assembly':continue
            if record.get('represented'):represented.add(record['source'])
            path=game/record['source'];blocks=parse(path);raw,labels,refs=raw_layout(blocks)
            members.append(dict(source=record['source'],owner=f'OVY_{ident}',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                blocks=len(blocks),relocations=[dict(section=s,offset=off,expression=expr,width=width) for (s,off),(expr,width) in refs.items()]))
            for block in blocks:
                section,offset=labels[block.symbol]
                following=sorted({off for s,off in labels.values() if s==section and off>offset})
                end=following[0] if following else len(raw[section])
                aliases=sorted(n for n,location in labels.items() if location==(section,offset))
                definitions[block.symbol]=dict(member=record['object'],source=record['source'],owner=f'OVY_{ident}',
                    section=section,offset=offset,size_to_next_label=end-offset,alignment_directive=block.before_alignment,
                    aliases=aliases,public=block.public,consumers=[])
    pattern=re.compile(r'(?<![\w.$])('+'|'.join(map(re.escape,sorted(definitions,key=len,reverse=True)))+r')(?![\w.$])')
    hashes={};numeric=[]
    files=subprocess.run(['rg','--files','--hidden',str(game)],capture_output=True,text=True,check=True).stdout.splitlines()
    for filename in files:
        path=Path(filename)
        if path.suffix not in ('.c','.cpp','.h','.s','.inc'):continue
        relative=str(path.relative_to(game));text=path.read_text(errors='replace')
        for number,line in enumerate(text.splitlines(),1):
            matches=set(pattern.findall(line))
            if not matches:continue
            hashes[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
            # Preserve complete expressions for review. Hints may overlap and
            # do not claim that lexical assignment means a store to the object.
            hints=[]
            for hint,expr in [('bulk',r'\b(?:MI\w*(?:Clear|Copy|Fill)\w*|memcpy|memmove|memset)\s*\('),
                              ('index',r'\['),('pointer-or-callback',r'\*|->|\(u32\)|\(void\s*\*\)'),('assignment',r'(?<![=!<>])=(?!=)')]:
                if re.search(expr,line):hints.append(hint)
            for symbol in matches:
                definitions[symbol]['consumers'].append(dict(source=relative,line=number,text=line.strip(),
                    owners=sorted(owners[relative]),execution='guest32' if relative in compiled else 'guest32-data' if relative in represented else 'declaration' if path.suffix in ('.h','.inc') else 'native-or-uncompiled',
                    declaration=bool(re.match(r'\s*(?:extern|typedef)\b',line)),
                    operation_hints=hints))
        if path.suffix in ('.c','.cpp'):
            for number,line in enumerate(text.splitlines(),1):
                for match in re.finditer(r'\b0x0?2[0-3][0-9a-fA-F]{5}\b',line):
                    numeric.append(dict(source=relative,line=number,value=match[0],text=line.strip()))
    return dict(schema=1,members=members,objects=definitions,consumer_source_hashes=hashes,numeric_ram_candidates=numeric,
                summary=dict(blocks=sum(m['blocks'] for m in members),relocations=sum(len(m['relocations']) for m in members),
                             direct_edges=sum(len(d['consumers']) for d in definitions.values()),
                             native_or_uncompiled_edges=sum(c['execution']=='native-or-uncompiled' for d in definitions.values() for c in d['consumers'])),
                proof_status='DIRECT-REFERENCE CENSUS ONLY: parameter/heap/callback escapes and raw numeric candidates require semantic review; not exhaustive access-path approval')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('game','image-root','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--links',type=Path,help='Add ownership evidence for actual failed global links')
    a=p.parse_args();report=census(a.game.resolve(),a.image_root.resolve());a.out.parent.mkdir(parents=True,exist_ok=True)
    if a.links:report['unresolved_provider_demands']=provider_demands(a.game.resolve(),a.image_root.resolve(),a.links.resolve())
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']))


if __name__=='__main__':main()
