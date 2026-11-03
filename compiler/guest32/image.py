"""Manifest-complete original guest compilation; never drops failed members."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cmake'))
from native_image_graph import parse_manifest,source_record

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,default=ROOT/'upstream/pokeheartgold')
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--llvm-bin',type=Path,required=True)
    p.add_argument('--lowerer',type=Path,required=True)
    p.add_argument('--report-only',action='store_true')
    a=p.parse_args();a.game=a.game.resolve();a.build=a.build.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
    a.lowerer=a.lowerer.resolve();a.llvm_bin=a.llvm_bin.resolve()
    image=parse_manifest(a.game/'main.lsf')['OVY_0']
    records=[source_record(a.game,m) for m in image['objects']]
    def member(record):
        r=dict(record);source=a.game/r['source'];r['sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
        work=a.out/r['object'];work.mkdir(parents=True,exist_ok=True)
        if r['kind']!='C':
            from native_data_ir import parse,raw_layout
            try:
                blocks=parse(source);sections,labels,refs=raw_layout(blocks)
                r.update(parsed=True,labels={k:list(v) for k,v in labels.items()},bytes={k:len(v) for k,v in sections.items()},
                         relocations=[dict(section=k[0],offset=k[1],expression=v[0],width=v[1]) for k,v in refs.items()],
                         represented=False,issues=[dict(kind='guest-data',source=str(source),line=0,llvm='',reason='shared guest image bytes, labels and relocation lowering required')])
            except ValueError as e:r.update(parsed=False,represented=False,issues=[dict(kind='guest-data',reason=str(e),source=str(source),line=0,llvm='')])
            return r
        ir=work/'guest.ll'
        args=[str(a.llvm_bin/'clang'),'-target','armv5-apple-darwin','-ffreestanding','-fno-builtin','-fsigned-char','-fno-short-enums','-std=gnu89',
              '-DSDK_ARM9','-DSDK_CODE_ARM','-DSDK_FINALROM','-DHEARTGOLD','-DENGLISH','-Wno-error=incompatible-pointer-types',
              '-I'+str(a.build/'include'),'-I'+str(a.game/'include'),'-I'+str(a.game/'include/library'),
              '-I'+str(a.game/'lib/include'),'-I'+str(a.game/'lib/NitroSDK/include'),'-I'+str(a.build/'generated/files'),
              '-O0','-g','-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes','-S','-emit-llvm',str(source),'-o',str(ir)]
        run=subprocess.run(args,capture_output=True,text=True)
        (work/'frontend.log').write_text(run.stdout+run.stderr);r.update(frontend=run.returncode==0,command=args)
        if run.returncode:
            r.update(compiled=False,issues=[dict(kind='frontend',source=str(source),line=0,llvm='',reason=run.stderr)]);return r
        diag=work/'operations.json'
        run=subprocess.run([str(a.lowerer),str(ir),str(work/'native.ll'),'--diagnose',str(diag)],capture_output=True,text=True)
        if run.returncode:raise RuntimeError(run.stderr)
        r['issues']=json.loads(diag.read_text())['issues']
        r['description']=json.loads(diag.read_text());r['compiled']=False
        return r
    with ThreadPoolExecutor(max_workers=4) as pool:members=list(pool.map(member,records))
    from native_data_ir import parse,raw_layout,integer
    position=4096;placements={};sections=[];functions={};data_names=set()
    for r in members:
        if r['kind']!='assembly' or not r.get('parsed'):continue
        raw,labels,refs=raw_layout(parse(a.game/r['source']))
        for section,data in raw.items():
            position=(position+15)&~15;base=position;position+=len(data)
            for name,(s,off) in labels.items():
                if s==section:
                    if name in placements:raise ValueError('duplicate original data definition: '+name)
                    placements[name]=dict(offset=base+off,size=len(data)-off);data_names.add(name)
            sections.append(dict(object=r['object'],section=section,offset=base,data=data,
                references=[dict(offset=off,expression=expr,width=width) for (s,off),(expr,width) in refs.items() if s==section]))
        r['public_labels']=[b.symbol for b in parse(a.game/r['source']) if b.public]
    definitions={}
    for r in members:
        for f in r.get('description',{}).get('functions',[]):
            if f['definition'] and not f['local']:definitions.setdefault(f['key'],[]).append(f)
            old=functions.get(f['key'])
            if not old or f['definition']:
                functions[f['key']]=dict(f,address_taken=f['address_taken'] or bool(old and old['address_taken']))
            else:old['address_taken'] |= f['address_taken']
    used={key:[bool(u['observed']) for u in f['argument_uses']] for key,f in functions.items() if f['definition']}
    changed=True
    while changed:
        changed=False
        for key,f in functions.items():
            if not f['definition']:continue
            for j,u in enumerate(f['argument_uses']):
                live=bool(u['observed'])
                for d in u['dependencies']:
                    target=used.get(d['function'])
                    live |= target is None or (d['argument']<len(target) and target[d['argument']])
                if live and not used[key][j]:used[key][j]=True;changed=True
    def flat_used(t,live):
        return sum((flat_used(t['element'],live) for _ in range(t['array'])),[]) if isinstance(t,dict) and 'array' in t else [live]
    codes=[]
    for i,key in enumerate(sorted(functions)):
        f=dict(functions[key],address=0x10000000+i*4)
        duplicates=definitions.get(key,[])
        f['coalesce']=False
        if len(duplicates)>1:
            origins={(str(Path(x['origin']).resolve()),x['origin_line'],x['body_hash'],json.dumps(x['params']),json.dumps(x['return'])) for x in duplicates}
            assert len(origins)==1,('conflicting original function definitions',key,origins)
            origin,line,_,_,_=next(iter(origins));text=Path(origin).read_text().splitlines()[line-1]
            assert Path(origin).suffix=='.h' and re.search(r'\binline\b',text),('unreviewed duplicate definition',key,origin,line)
            f['coalesce']=True
        if f['local']:
            identity=str(Path(f['source']).relative_to(a.game))+'|'+f['name']
            f['native']='guest32_local_'+hashlib.sha256(identity.encode()).hexdigest()[:16]+'_'+f['name']
        else:f['native']='guest32_'+f['name']
        if any(ref['expression']==f['name'] for s in sections for ref in s['references']):f['address_taken']=True
        f['used_flat']=sum((flat_used(t,live) for t,live in zip(f['params'],used.get(key,[True]*len(f['params'])))),[])
        codes.append(f)
    def flat_types(t):
        if isinstance(t,dict) and 'array' in t:return flat_types(t['element'])*t['array']
        return ['i32' if t=='ptr' else t]
    def compatible(x,y):
        return x==y or (isinstance(x,str) and isinstance(y,str) and x.startswith('i') and y.startswith('i') and int(x[1:])<=32 and int(y[1:])<=32)
    # Original ARM register contracts are data, not function-name rules in the compiler.
    register_spec=json.loads((Path(__file__).with_name('ovy0_registers.json')).read_text())
    for relative,digest in register_spec['source_hashes'].items():
        assert hashlib.sha256((a.game/relative).read_bytes()).hexdigest()==digest,('register contract source changed',relative)
    register_edges=[]
    for edge in register_spec['edges']:
        edge=dict(edge)
        proof=register_spec['original_functions'][edge['function']]
        if edge['mode']=='preserved-argument':
            proof=register_spec['original_functions']['gti2Listen']
            instructions=[x.strip() for x in proof.splitlines() if x.startswith('\t') and not x.startswith('\tarm_func_')]
            assert instructions==['str r1, [r0, #0x20]','bx lr'],instructions
        assert edge['evidence'] in proof,('register evidence mismatch',edge)
        edge['source']=str(a.game/edge['source']);register_edges.append(edge)
    for f in codes:
        if f['key'] in register_spec['implicit_r0']:
            assert not f['params'],('implicit register conflicts with explicit formal',f['key'])
            f['params']=['i32'];f['used_flat']=[True];f['implicit_registers']=['r0']
    code_by_key={c['key']:c for c in codes};constraints=[];external_calls=[]
    for r in members:
        r['observed_operations']=r['issues']
        r['issues']=[i for i in r['issues'] if i['kind']=='frontend']
        for call in r.get('description',{}).get('calls',[]):
            target=code_by_key.get(call['target'])
            if not target or not target['definition']:
                if target:external_calls.append(dict(call,kind='external-guest-provider',requirement='guest ABI provider or explicit typed native bridge'))
                continue
            actual=sum((flat_types(t) for t in call['args']),[])
            expected=sum((flat_types(t) for t in target['params']),[])
            reasons=[]
            for i in range(len(actual),len(expected)):
                if target['used_flat'][i]:reasons.append('observable argument '+str(i)+' is absent at callsite')
            for i,(x,y) in enumerate(zip(actual,expected)):
                if not compatible(x,y):reasons.append('argument '+str(i)+' has incompatible ABI classes '+str(x)+' / '+str(y))
            if call['result_used'] and target['return']=='void' and call['return']!='void':reasons.append('caller observes a result from a void implementation')
            contract=next((e for e in register_edges if all(e[k]==call[k] for k in ('source','function','target','line'))),None)
            if contract:reasons=[] # The lowerer must independently validate SSA producer / argument identity.
            for reason in reasons:
                issue=dict(call,kind='call-register-state',reason=reason,requirement='original argument/return register semantics; no invented values',
                    provider_source=target['source'],provider_params=target['params'],provider_return=target['return'])
                constraints.append(issue);r['issues'].append(issue)
    (a.out/'cross-unit-abi.json').write_text(json.dumps(dict(unsupported=constraints,external_providers=external_calls),indent=2)+'\n')
    code_values={f['name']:f['address'] for f in codes if not f['local']}
    own_globals={}
    for r in members:
        for g in r.get('description',{}).get('globals',[]):
            if not g['definition']:continue
            if g['key'] in own_globals:
                if own_globals[g['key']]['size']!=g['size']:raise ValueError('inconsistent global definition: '+g['key'])
                continue
            if g['name'] in data_names:raise ValueError('C/assembly duplicate global: '+g['name'])
            position=(position+g['alignment']-1)&~(g['alignment']-1)
            own_globals[g['key']]=dict(offset=position,size=g['size']);position+=g['size']
    contract=json.loads((ROOT/'compiler/guest32/ovy0_layout.json').read_text())
    for relative,expected in contract['inputs'].items():
        assert hashlib.sha256((a.game/relative).read_bytes()).hexdigest()==expected,relative
    for group in contract['groups']:
        keys=[str(a.game/m['unit'])+'|'+m['name'] if 'unit' in m else m['name'] for m in group['members']]
        base=min(own_globals[k]['offset'] for k in keys)
        assert sum(own_globals[k]['size'] for k in keys)==group['extent']
        assert max(own_globals[k]['offset']+own_globals[k]['size'] for k in keys)==base+group['extent']
        for k,m in zip(keys,group['members']):own_globals[k]=dict(offset=base+m['offset'],size=m['view_size'])
        for name,off in group['aliases'].items():placements[name]=dict(offset=base+off,size=group['extent']-off)
    catalog=a.out/'image.json';catalog.write_text(json.dumps(dict(codes=codes,register_edges=register_edges,static_end=position,assembly_globals=placements,c_globals=own_globals),indent=2)+'\n')
    native=a.out/'native-abi.ll';native.write_text('target datalayout = "e-p:64:64"\n')
    def lower(r):
        if not r.get('frontend'):return r
        work=a.out/r['object'];globals=dict(placements)
        for g in r['description']['globals']:
            if g['key'] in own_globals:globals[g['name']]=own_globals[g['key']]
            elif g['name'] in own_globals:globals[g['name']]=own_globals[g['name']]
        abi=work/'abi.json';abi.write_text(json.dumps(dict(version=1,globals=globals,calls={},exports={})))
        run=subprocess.run([str(a.lowerer),str(work/'guest.ll'),str(work/'native.ll'),'--abi',str(abi),'--native-ir',str(native),
                            '--image',str(catalog),'--guest-externals','--prefix','guest32_'],capture_output=True,text=True)
        (work/'lower.log').write_text(run.stdout+run.stderr)
        r['blocking_diagnostic']=run.stderr
        if not run.returncode:
            verify=subprocess.run([str(a.llvm_bin/'opt'),'-passes=verify','-disable-output',str(work/'native.ll')],capture_output=True,text=True)
            if verify.returncode:raise RuntimeError(verify.stderr)
            run=subprocess.run([str(a.llvm_bin/'clang'),'-O2','-c',str(work/'native.ll'),'-o',str(work/'native.o')],capture_output=True,text=True)
            (work/'object.log').write_text(run.stdout+run.stderr);r['compiled']=run.returncode==0
            r['blocking_diagnostic']=run.stderr if run.returncode else ''
        return r
    with ThreadPoolExecutor(max_workers=4) as pool:members=list(pool.map(lower,members))
    known={n:v['offset'] for n,v in placements.items()};known.update(code_values);known.update({n:v['offset'] for n,v in own_globals.items() if '|' not in n})
    data_sources={r['object']:[] for r in members if r['kind']=='assembly'}
    for r in members:
        for name in r.get('public_labels',[]):
            data_sources[r['object']].append('const uint32_t guest32_address_'+name+'='+str(placements[name]['offset'])+';')
    unresolved=set()
    for idx,s in enumerate(sections):
        lines=data_sources[s['object']];name='guest32_data_'+str(idx)
        (a.out/s['object']/(s['section'].lstrip('.')+'.bin')).write_bytes(s['data'])
        lines.append('static const unsigned char '+name+'[]={'+','.join(map(str,s['data']))+'};')
        body=['void '+name+'_load(void *ram){unsigned char *p=g32_resolve(ram,'+str(s['offset'])+','+str(len(s['data']))+',0);memcpy(p,'+name+','+str(len(s['data']))+');']
        for ref in s['references']:
            assert ref['width']==4,ref
            try:value=str(integer(ref['expression'],known)&0xffffffff)
            except ValueError:
                # External coordinates remain genuine undefined metadata imports.
                expr=ref['expression'];assert expr.isidentifier(),expr
                symbol='guest32_address_'+expr;unresolved.add(expr);lines.append('extern const uint32_t '+symbol+';');value=symbol
            body.append('{uint32_t v='+value+';memcpy(p+'+str(ref['offset'])+',&v,4);}')
        lines.append(''.join(body)+'}')
    for r in members:
        if r['kind']!='assembly' or not r.get('parsed'):continue
        work=a.out/r['object'];source=work/'data.c'
        source.write_text('#include <stdint.h>\n#include <string.h>\nextern void *g32_resolve(void*,uint32_t,uint32_t,uint32_t);\n'+'\n'.join(data_sources[r['object']])+'\n')
        run=subprocess.run([str(a.llvm_bin/'clang'),'-arch','arm64','-O2','-c',str(source),'-o',str(work/'native.o')],capture_output=True,text=True)
        (work/'object.log').write_text(run.stdout+run.stderr);r['represented']=run.returncode==0
        r['issues']=[] if r['represented'] else r['issues']
    (a.out/'data-relocations.json').write_text(json.dumps(dict(external_guest_coordinates=sorted(unresolved),sections=[{k:v for k,v in s.items() if k!='data'} for s in sections]),indent=2)+'\n')
    summary=dict(c_total=sum(r['kind']=='C' for r in members),frontend=sum(r.get('frontend',False) for r in members),
                 compiled=sum(r.get('compiled',False) for r in members),data_total=sum(r['kind']=='assembly' for r in members),
                 data_represented=sum(r.get('represented',False) for r in members),
                 issues=dict(Counter(i['kind'] for r in members for i in r['issues'])))
    summary['complete_compilation']=summary['compiled']==summary['c_total'] and summary['data_represented']==summary['data_total'] and not constraints
    (a.out/'coverage.json').write_text(json.dumps(dict(image=image,summary=summary,members=members),indent=2)+'\n')
    print(json.dumps(summary))
    if summary['complete_compilation']:(a.out/'complete.stamp').write_text('manifest-complete guest compilation\n')
    if not summary['complete_compilation'] and not a.report_only:raise SystemExit(1)

if __name__=='__main__':main()
