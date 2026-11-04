"""Emit complete manifest-owned original data at verified DS coordinates.

Uses the existing data parser and original numeric section anchors. Unanchored
sections and unresolved relocations fail closed; no packed-coordinate fallback.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from original_layout import annotated_sections,verified_sections
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cmake'))
from native_data_ir import parse,raw_layout,integer
from native_image_graph import parse_manifest,source_record
from native_overlay_link import symbols


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('game','out','llvm-bin'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--owner',required=True);p.add_argument('--member',action='append',required=True)
    a=p.parse_args();game=a.game.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);llvm=a.llvm_bin.resolve()
    original=parse_manifest(game/'main.lsf')[a.owner]['objects'];records=[];known={};spans=[]
    for member in a.member:
        if member not in original:p.error('member is not owned by selected original image: '+member)
        r=source_record(game,member)
        if r['kind']!='assembly':p.error('requires original assembly data member')
        source=game/r['source'];blocks=parse(source);raw,labels,refs=raw_layout(blocks)
        placement=annotated_sections(source.read_text(),raw,labels)
        historical=json.loads(Path(__file__).with_name('original_data_layouts.json').read_text())
        if r['source'] in historical:
            proof=historical[r['source']]
            if hashlib.sha256(source.read_bytes()).hexdigest()!=proof['source_sha256']:raise ValueError('historical source changed')
            placement.update(verified_sections(raw,labels,refs,proof))
        for section,data in raw.items():
            if section not in placement:raise ValueError('section lacks original coordinate: '+member+section)
            base=placement[section]['address']
            for start,end in spans:
                if base<end and start<base+len(data):raise ValueError('overlapping data members')
            spans.append((base,base+len(data)))
        for n,(s,o) in labels.items():
            if n in known:raise ValueError('duplicate data definition: '+n)
            known[n]=placement[s]['address']+o
        records.append((r,blocks,raw,labels,refs,placement))
    objects=[];owners={};hashes={};loads=[];placements={}
    for index,(r,blocks,raw,labels,refs,placement) in enumerate(records):
        member=r['object'];source=game/r['source'];hashes[member]=hashlib.sha256(source.read_bytes()).hexdigest()
        lines=['#include <stdint.h>','#include <string.h>','extern void *g32_resolve(void*,uint32_t,uint32_t,uint32_t);']
        for block in blocks:
            n=block.symbol
            if block.public:
                lines.append('const uint32_t guest32_address_'+n+'='+str(known[n])+';')
                s,o=labels[n];placements[n]=dict(offset=known[n],size=len(raw[s])-o)
        for j,(section,data) in enumerate(raw.items()):
            data=bytearray(data)
            for (s,o),(expr,width) in refs.items():
                if s==section:data[o:o+width]=integer(expr,known).to_bytes(width,'little')
            name='guest32_data_member_'+str(index)+'_'+str(j);loads.append(name+'_load')
            lines.append('static const unsigned char '+name+'[]={'+','.join(map(str,data))+'};')
            lines.append('void '+name+'_load(void *ram){memcpy(g32_resolve(ram,'+str(placement[section]['address'])+','+str(len(data))+',0),'+name+','+str(len(data))+');}')
        work=out/member;work.mkdir(parents=True,exist_ok=True);generated=work/'data.c';obj=work/'data.o';generated.write_text('\n'.join(lines)+'\n')
        subprocess.run([str(llvm/'clang'),'-O2','-c',str(generated),'-o',str(obj)],check=True)
        objects.append(obj)
        for symbol in symbols(obj,nm=str(llvm/'llvm-nm')):
            if symbol in owners:raise ValueError('duplicate emitted data identity')
            owners[symbol]=member
    archive=out/'provider.a';subprocess.run([str(llvm/'llvm-ar'),'rcsD',str(archive),*map(str,objects)],check=True)
    identities={'_guest32_address_'+n:n for n in placements}
    family=dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),original_members=hashes,symbols=owners,original_identities=identities,import_identities={},abi_representation='guest32',scope='complete original data members; explicit loaders require main-image startup integration')
    (out/'providers.json').write_text(json.dumps(dict(schema=1,families={'original-data':family}),indent=2)+'\n')
    (out/'data.json').write_text(json.dumps(dict(globals=placements,loaders=loads,static_end=max(e for s,e in spans),sources=hashes),indent=2)+'\n')
    print('PASS',len(records),'complete original data members;',len(placements),'public guest coordinates')

if __name__=='__main__':main()
