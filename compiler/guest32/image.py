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
from incremental import run as cached_run
from original_layout import anchored_sections,verified_sections,overlay_id_constants,verify_recovery

def private_inline_plan(members):
    names={f['name'] for r in members for f in r.get('description',{}).get('functions',[])
           if f.get('private_inline_eligible')}
    unsafe={f['name'] for r in members for f in r.get('description',{}).get('functions',[])
            if f['name'] in names and not f.get('private_inline_eligible') and
               ((not f['definition'] and f.get('referenced',True)) or
                (f['definition'] and (not f.get('inline_definition') or f['address_taken'])))}
    # Inline callers from headers must follow their TU-private callees. Select
    # the complete closed inline region, then propagate rejection backwards to
    # every callee reachable from a caller that cannot receive a private body.
    dependencies=[]
    for r in members:
        functions={f['name']:f for f in r.get('description',{}).get('functions',[])}
        for call in r.get('description',{}).get('calls',[]):
            target=call['target']
            if target not in names:continue
            caller=functions.get(call['function'],{})
            callee=functions.get(target,{})
            if caller.get('origin')!=callee.get('source'):
                dependencies.append((call['function'],target))
                if not caller.get('private_inline_eligible'):unsafe.add(target)
        for ref in r.get('relocations',[]):
            symbol=re.match(r'[A-Za-z_.$][\w.$]*',ref['expression'])
            if symbol and symbol[0] in names:unsafe.add(symbol[0])
    changed=True
    while changed:
        changed=False
        for caller,callee in dependencies:
            if caller in unsafe and callee not in unsafe:
                unsafe.add(callee);changed=True
    return {r['object']:[x for name in sorted(f['name'] for f in r.get('description',{}).get('functions',[])
        if f.get('private_inline_eligible') and f['name'] not in unsafe) for x in ('--private-inline',name)]
        for r in members},unsafe

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,default=ROOT/'upstream/pokeheartgold')
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--llvm-bin',type=Path,required=True)
    p.add_argument('--lowerer',type=Path,required=True)
    p.add_argument('--report-only',action='store_true')
    p.add_argument('--plan-only',action='store_true',help='Describe original members and placements without emitting objects')
    p.add_argument('--shared-catalog',type=Path,help='Use a jointly planned storage and code identity catalog')
    p.add_argument('--image',default='OVY_0',help='Original overlay name from main.lsf')
    a=p.parse_args();a.game=a.game.resolve();a.build=a.build.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
    a.lowerer=a.lowerer.resolve();a.llvm_bin=a.llvm_bin.resolve()
    images=parse_manifest(a.game/'main.lsf')
    image=images[a.image]
    constants=overlay_id_constants(a.game,images)
    if image['kind']!='Overlay':p.error('--image must name an original overlay')
    records=[source_record(a.game,m) for m in image['objects']]
    from frontend import private_overlay,cxx_flags
    virtual_flags,virtual_files=private_overlay(a.game,a.out,records)
    def member(record):
        r=dict(record);source=a.game/r['source'];r['sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
        work=a.out/r['object'];work.mkdir(parents=True,exist_ok=True)
        if r['kind'] not in ('C','C++'):
            from native_data_ir import parse,raw_layout
            try:
                blocks=parse(source,constants=constants);sections,labels,refs=raw_layout(blocks)
                r.update(parsed=True,labels={k:list(v) for k,v in labels.items()},bytes={k:len(v) for k,v in sections.items()},
                         relocations=[dict(section=k[0],offset=k[1],expression=v[0],width=v[1]) for k,v in refs.items()],
                         represented=False,issues=[dict(kind='guest-data',source=str(source),line=0,llvm='',reason='shared guest image bytes, labels and relocation lowering required')])
            except ValueError as e:r.update(parsed=False,represented=False,issues=[dict(kind='guest-data',reason=str(e),source=str(source),line=0,llvm='')])
            return r
        ir=work/'guest.ll'
        from frontend import flags as frontend_flags
        flags=frontend_flags(a.game,a.build)+virtual_flags
        if r['kind']=='C++':
            # Compile the original C++ ABI, including its real mangled names,
            # vtables and exception operations. Unsupported IR remains fatal.
            flags=[f for f in flags if f not in ('-std=gnu99','-fgnu89-inline')]
            flags+=cxx_flags(a.game,r['object'])
        args=[str(a.llvm_bin/('clang++' if r['kind']=='C++' else 'clang')),*flags,'-S','-emit-llvm',str(source),'-o',str(ir),'-MD','-MF',str(ir)+'.d']
        run=cached_run(args,[ir],inputs=[source,a.game/'Makefile',a.game/'common.mk'],depfile=str(ir)+'.d',virtual_files=virtual_files)
        (work/'frontend.log').write_text(run.stdout+run.stderr);r.update(frontend=run.returncode==0,command=args)
        if run.returncode:
            r.update(compiled=False,issues=[dict(kind='frontend',source=str(source),line=0,llvm='',reason=run.stderr)]);return r
        diag=work/'operations.json'
        run=cached_run([str(a.lowerer),str(ir),str(work/'native.ll'),'--diagnose',str(diag)], [diag], inputs=[ir])
        if run.returncode:raise RuntimeError(run.stderr)
        r['issues']=json.loads(diag.read_text())['issues']
        r['description']=json.loads(diag.read_text());r['compiled']=False
        return r
    with ThreadPoolExecutor(max_workers=4) as pool:members=list(pool.map(member,records))
    # Closed-image identity proof: source-file inlines with only local direct
    # uses may keep their own bodies. Any outside declaration use or nonprivate
    # definition preserves the ownership rejection instead of guessing an ODR.
    identity_args,unsafe=private_inline_plan(members)
    for r in members:
        r['identity_args']=identity_args[r['object']]
        if not r['identity_args']:continue
        work=a.out/r['object'];diag=work/'operations.json'
        run=cached_run([str(a.lowerer),str(work/'guest.ll'),str(work/'native.ll'),'--diagnose',str(diag),*r['identity_args']],
                       [diag],inputs=[work/'guest.ll',a.game/r['source']])
        if run.returncode:raise RuntimeError(run.stderr)
        r['description']=json.loads(diag.read_text());r['issues']=r['description']['issues']
    (a.out/'inline-identities.json').write_text(json.dumps(dict(unsafe_external_uses=sorted(unsafe),
        members={r['object']:r['identity_args'] for r in members if r['identity_args']}),indent=2)+'\n')
    # Retain a complete original-member census even if code ownership or data
    # placement prevents creating a shared catalog later in this batch.
    (a.out/'frontend-coverage.json').write_text(json.dumps(dict(image=image,
        members=[{k:v for k,v in r.items() if k not in ('description','relocations','labels')} for r in members],
        cpp_total=sum(r['kind']=='C++' for r in members)),indent=2)+'\n')
    from native_data_ir import parse,raw_layout,integer
    position=4096;placements={};original_placements={};sections=[];section_plans=[];functions={};data_names=set()
    historical_layouts=json.loads(Path(__file__).with_name('original_data_layouts.json').read_text())
    for r in members:
        if r['kind']!='assembly' or not r.get('parsed'):continue
        raw,labels,refs=raw_layout(parse(a.game/r['source'],constants=constants))
        original_sections=anchored_sections(raw,labels,image['id'])
        if r['source'] in historical_layouts:
            proof=historical_layouts[r['source']]
            assert r['sha256']==proof['source_sha256'],('original data source changed',r['source'])
            if 'image_id' in proof and proof['image_id']!=image['id']:raise ValueError('historical data image owner mismatch')
            verify_recovery(a.game,a.game/r['source'],(raw,labels,refs),proof,constants)
            original_sections.update(verified_sections(raw,labels,refs,proof))
        for section,data in raw.items():
            position=(position+15)&~15;base=position;position+=len(data)
            for name,(s,off) in labels.items():
                if s==section:
                    if name in placements:raise ValueError('duplicate original data definition: '+name)
                    placements[name]=dict(offset=base+off,size=len(data)-off);data_names.add(name)
                    if section in original_sections:
                        original_placements[name]=dict(offset=original_sections[section]['address']+off,size=len(data)-off)
            section_labels={name:off for name,(s,off) in labels.items() if s==section}
            section_refs=[dict(offset=off,expression=expr,width=width)
                          for (s,off),(expr,width) in refs.items() if s==section]
            section_plans.append(dict(
                object=r['object'],
                source=r['source'],
                source_sha256=r['sha256'],
                section=section,
                offset=base,
                size=len(data),
                labels=section_labels,
                relocation_count=len(section_refs),
                relocations=section_refs,
                bytes_sha256=hashlib.sha256(data).hexdigest(),
                original_placement=original_sections.get(section)))
            sections.append(dict(
                object=r['object'],
                section=section,
                offset=base,
                data=data,
                original_placement=original_sections.get(section),
                references=section_refs))
        r['public_labels']=[b.symbol for b in parse(a.game/r['source'],constants=constants) if b.public]
    definitions={}
    for r in members:
        for f in r.get('description',{}).get('functions',[]):
            if f['definition'] and not f['local']:definitions.setdefault(f['key'],[]).append(f)
            old=functions.get(f['key'])
            if not old or f['definition']:
                functions[f['key']]=dict(f,address_taken=f['address_taken'] or bool(old and old['address_taken']))
            else:old['address_taken'] |= f['address_taken']
    ownership_conflicts=[]
    for key,duplicates in sorted(definitions.items()):
        if len(duplicates)<2:continue
        origins={(f['origin'],f['origin_line'],f['body_hash'],json.dumps(f['params']),json.dumps(f['return'])) for f in duplicates}
        if len(origins)>1:
            ownership_conflicts.append(dict(identity=key,cause='nonidentical-original-definitions',
                definitions=[{k:f[k] for k in ('source','origin','origin_line','body_hash','params','return')} for f in duplicates]))
    (a.out/'ownership-conflicts.json').write_text(json.dumps(ownership_conflicts,indent=2)+'\n')
    if ownership_conflicts:
        raise ValueError('original code ownership conflicts: '+', '.join(r['identity'] for r in ownership_conflicts))
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
            origin,line,_,_,_=next(iter(origins))
            if not Path(origin).is_file() or not line:raise ValueError('unproved compiler-generated ODR/ABI helper: '+key)
            text=Path(origin).read_text().splitlines()[line-1]
            assert Path(origin).suffix in ('.h','.hpp') and (re.search(r'\binline\b',text) or
                all(x.get('inline_definition') for x in duplicates)),('unreviewed duplicate definition',key,origin,line)
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
    register_path=Path(__file__).with_name('ovy'+str(image['id'])+'_registers.json')
    register_spec=(json.loads(register_path.read_text()) if register_path.is_file() else
                   dict(source_hashes={},original_functions={},implicit_r0=[],edges=[]))
    if 'owner' in register_spec and register_spec['owner']!=image['name']:
        raise ValueError('original register contract owner mismatch')
    for relative,digest in register_spec['source_hashes'].items():
        assert hashlib.sha256((a.game/relative).read_bytes()).hexdigest()==digest,('register contract source changed',relative)
    from registration_scope import scoped_spec,validate_machine_edges
    register_spec=scoped_spec(image['name'], register_spec)
    validate_machine_edges(a.game,register_spec)
    register_edges=[]
    for edge in register_spec['edges']:
        edge=dict(edge)
        proof=register_spec['original_functions'][edge['function']]
        if edge['mode']=='preserved-argument':
            proof=register_spec['original_functions']['gti2Listen']
            instructions=[x.strip() for x in proof.splitlines() if x.startswith('\t') and not x.startswith('\tarm_func_')]
            assert instructions==['str r1, [r0, #0x20]','bx lr'],instructions
        if edge['mode']=='branch-value':
            assert '\tldr r1, [sb, #0xc]\n\tldr r5, [sb, #4]\n\tstr r1, [sp, #4]' in proof
            wrapper=register_spec['original_functions'][edge['target']]
            assert '\tmov r1, #0\n\tmov r2, r1\n\tbx ip' in wrapper
            assert 'ldr r0,' not in wrapper
        assert edge['evidence'] in proof,('register evidence mismatch',edge)
        edge['source']=str(a.game/edge['source']);register_edges.append(edge)
    for f in codes:
        if f['key'] in register_spec['implicit_r0']:
            assert not f['params'],('implicit register conflicts with explicit formal',f['key'])
            f['params']=['i32'];f['used_flat']=[True];f['implicit_registers']=['r0']
    code_by_key={c['key']:c for c in codes};constraints=[];external_calls=[]
    for r in members:
        r['observed_operations']=r['issues']
        if r['kind'] in ('C','C++'):
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
    for group in contract['groups'] if image['name']=='OVY_0' else []:
        keys=[str(a.game/m['unit'])+'|'+m['name'] if 'unit' in m else m['name'] for m in group['members']]
        base=min(own_globals[k]['offset'] for k in keys)
        assert sum(own_globals[k]['size'] for k in keys)==group['extent']
        assert max(own_globals[k]['offset']+own_globals[k]['size'] for k in keys)==base+group['extent']
        for k,m in zip(keys,group['members']):own_globals[k]=dict(offset=base+m['offset'],size=m['view_size'])
        for name,off in group['aliases'].items():placements[name]=dict(offset=base+off,size=group['extent']-off)
    if a.shared_catalog:
        shared=json.loads(a.shared_catalog.read_text())
        plan=shared['images'][image['name']]
        placements=plan['assembly_globals'];own_globals=plan['c_globals']
        codes=shared['codes'];position=shared['static_end']
        # Relocations and every translation unit use the same coordinates,
        # including declarations whose defining member belongs to a peer image.
        code_values={f['name']:f['address'] for f in codes if not f['local']}
        register_edges=shared['register_edges']
    record=dict(codes=codes,register_edges=register_edges,static_end=position,
                assembly_globals=placements,c_globals=own_globals,
                original_assembly_globals=original_placements,
                assembly_sections=section_plans)
    if image['name']=='OVY_0':
        from ac_config import contract as ac_contract
        record['ac_socket_config']=ac_contract(a.game,placements)
    catalog=a.out/('plan.json' if a.plan_only else 'image.json');catalog.write_text(json.dumps(record,indent=2)+'\n')
    if a.plan_only:return
    native=a.out/'native-abi.ll';native.write_text('target datalayout = "e-p:64:64"\n')
    def lower(r):
        if not r.get('frontend'):return r
        work=a.out/r['object'];globals=dict(placements)
        if a.shared_catalog:globals.update(shared['globals'])
        for g in r['description']['globals']:
            if g['key'] in own_globals:globals[g['name']]=own_globals[g['key']]
            elif g['name'] in own_globals:globals[g['name']]=own_globals[g['name']]
        from original_layout import overlay_id_symbols
        abi=work/'abi.json';abi.write_text(json.dumps(dict(version=1,globals=globals,calls={},exports={},absolute_symbols=overlay_id_symbols(a.game,images))))
        run=cached_run([str(a.lowerer),str(work/'guest.ll'),str(work/'native.ll'),'--abi',str(abi),'--native-ir',str(native),
                            '--image',str(catalog),'--guest-externals','--prefix','guest32_',*r.get('identity_args',[])],[work/'native.ll'],inputs=[work/'guest.ll',abi,native,catalog,a.game/r['source']])
        (work/'lower.log').write_text(run.stdout+run.stderr)
        r['blocking_diagnostic']=run.stderr
        if not run.returncode:
            verify=subprocess.run([str(a.llvm_bin/'opt'),'-passes=verify','-disable-output',str(work/'native.ll')],capture_output=True,text=True)
            if verify.returncode:raise RuntimeError(verify.stderr)
            run=cached_run([str(a.llvm_bin/'clang'),'-O2','-c',str(work/'native.ll'),'-o',str(work/'native.o')],[work/'native.o'],inputs=[work/'native.ll'])
            (work/'object.log').write_text(run.stdout+run.stderr);r['compiled']=run.returncode==0
            r['blocking_diagnostic']=run.stderr if run.returncode else ''
        return r
    with ThreadPoolExecutor(max_workers=4) as pool:members=list(pool.map(lower,members))
    known={n:v['offset'] for n,v in placements.items()};known.update(code_values);known.update({n:v['offset'] for n,v in own_globals.items() if '|' not in n})
    if a.shared_catalog:known.update({n:v['offset'] for n,v in shared['globals'].items()})

    # Resolve original numeric macros separately from guest address identities.
    # Only constants required by parsed original assembly are admitted.
    import_tokens = set()
    for section in sections:
        for ref in section['references']:
            if ref['width']<4:
                import_tokens.update(
                    re.findall(r'\b[A-Za-z_]\w*\b',ref['expression'])
                )

    definitions={}
    for header in sorted((a.game/'include').rglob('*.h')):
        for number,line in enumerate(header.read_text(errors='replace').splitlines(),1):
            match=re.match(r'^\s*#define\s+([A-Za-z_]\w*)\s+(.+)$',line)
            if not match:
                continue
            name,expression=match.groups()
            expression=expression.split('//',1)[0].strip()
            if name in definitions:
                definitions[name].append((expression,str(header),number))
            else:
                definitions[name]=[(expression,str(header),number)]

    original_constants={}
    visiting=set()

    def resolve_original_constant(name):
        if name in original_constants:
            return original_constants[name]
        if name in visiting:
            raise ValueError('cyclic original constant: '+name)
        if name not in definitions:
            raise ValueError('missing original constant: '+name)
        visiting.add(name)
        try:
            candidates=[]
            for expression,header,number in definitions[name]:
                dependencies=set(re.findall(r'\\b[A-Za-z_]\\w*\\b',expression))
                environment=dict(constants)
                for dependency in sorted(dependencies):
                    if dependency!=name and dependency in definitions:
                        environment[dependency]=resolve_original_constant(dependency)
                try:
                    value=integer(expression,environment)
                except ValueError:
                    continue
                candidates.append((value,header,number))
            if not candidates:
                raise ValueError('no evaluable definition for '+name)
            values={item[0] for item in candidates}
            if len(values)!=1:
                raise ValueError('conflicting original definitions for '+name+
                                 ': '+repr(candidates[:8]))
            value=candidates[0][0]
            original_constants[name]=value
            return value
        finally:
            visiting.remove(name)

    for name in sorted(import_tokens):
        if name in known:
            continue
        value=resolve_original_constant(name)
        if name in known and known[name]!=value:
            raise ValueError('constant/address collision: '+name)
        known[name]=value
    data_sources={r['object']:[] for r in members if r['kind']=='assembly'}
    for r in members:
        for name in r.get('public_labels',[]):
            data_sources[r['object']].append('const uint32_t guest32_address_'+name+'='+str(placements[name]['offset'])+';')
    unresolved=set()
    for idx,s in enumerate(sections):
        lines=data_sources[s['object']]
        name=('guest32_data_' if image['id']==0 else 'guest32_image_'+str(image['id'])+'_data_')+str(idx)
        (a.out/s['object']/(s['section'].lstrip('.')+'.bin')).write_bytes(s['data'])
        lines.append('static const unsigned char '+name+'[]={'+','.join(map(str,s['data']))+'};')
        base=s['offset']
        if a.shared_catalog:
            identity=s['object']+'|'+s['section']
            shared_section=plan.get('assembly_sections',{}).get(identity)
            if shared_section is None:
                raise ValueError('missing shared assembly section: '+identity)
            if shared_section['size']!=len(s['data']):
                raise ValueError('shared assembly section extent mismatch: '+identity)
            base=shared_section['offset']
            if s['original_placement'] is not None:
                if base!=s['original_placement']['address']:
                    raise ValueError('original assembly section moved: '+identity)
            else:
                if not (0x02000000<=base and
                        base+len(s['data'])<=0x02400000):
                    raise ValueError('relocatable assembly outside DS RAM: '+identity)
            labels=shared_section['labels']
            if not labels:
                raise ValueError('shared assembly section has no labels: '+identity)
            for label,off in labels.items():
                expected=dict(offset=base+off,size=len(s['data'])-off)
                if placements.get(label)!=expected:
                    raise ValueError('shared assembly label mismatch: '+label)
            s['offset']=base
        body=['void '+name+'_load(void *ram){unsigned char *p=g32_resolve(ram,'+str(base)+','+str(len(s['data']))+',0);memcpy(p,'+name+','+str(len(s['data']))+');']
        for ref in s['references']:
            width=ref['width']
            if width not in (1,2,4):
                raise ValueError('unsupported assembly relocation width: '+repr(ref))
            expr=ref['expression']
            try:
                resolved=integer(expr,known)
            except ValueError as error:
                if not expr.isidentifier():
                    raise ValueError('unresolved assembly expression: '+expr) from error
                if width!=4:
                    raise ValueError('unresolved narrow assembly relocation: '+expr) from error
                symbol='guest32_address_'+expr
                unresolved.add(expr)
                lines.append('extern const uint32_t '+symbol+';')
                value=symbol
            else:
                minimum=-(1<<(8*width-1))
                maximum=(1<<(8*width))-1
                if not minimum<=resolved<=maximum:
                    raise ValueError('assembly relocation overflows '+str(width)+
                                     ' bytes: '+expr+' = '+str(resolved))
                value=str(resolved&maximum)
            ctype={1:'uint8_t',2:'uint16_t',4:'uint32_t'}[width]
            body.append('{'+ctype+' v='+value+';memcpy(p+'+
                        str(ref['offset'])+',&v,'+str(width)+');}')
        lines.append(''.join(body)+'}')
    for r in members:
        if r['kind']!='assembly' or not r.get('parsed'):continue
        work=a.out/r['object'];source=work/'data.c'
        source.write_text('#include <stdint.h>\n#include <string.h>\nextern void *g32_resolve(void*,uint32_t,uint32_t,uint32_t);\n'+'\n'.join(data_sources[r['object']])+'\n')
        run=cached_run([str(a.llvm_bin/'clang'),'-arch','arm64','-O2','-c',str(source),'-o',str(work/'native.o'),'-MD','-MF',str(work/'data.d')],[work/'native.o'],inputs=[source],depfile=work/'data.d')
        (work/'object.log').write_text(run.stdout+run.stderr);r['represented']=run.returncode==0
        r['issues']=[] if r['represented'] else r['issues']
    (a.out/'data-relocations.json').write_text(json.dumps(dict(external_guest_coordinates=sorted(unresolved),sections=[{k:v for k,v in s.items() if k!='data'} for s in sections]),indent=2)+'\n')
    summary=dict(c_total=sum(r['kind'] in ('C','C++') for r in members),cpp_total=sum(r['kind']=='C++' for r in members),frontend=sum(r.get('frontend',False) for r in members),
                 compiled=sum(r.get('compiled',False) for r in members),data_total=sum(r['kind']=='assembly' for r in members),
                 data_represented=sum(r.get('represented',False) for r in members),
                 issues=dict(Counter(i['kind'] for r in members for i in r['issues'])))
    summary['complete_compilation']=summary['compiled']==summary['c_total'] and summary['data_represented']==summary['data_total'] and not constraints
    (a.out/'coverage.json').write_text(json.dumps(dict(image=image,summary=summary,members=members),indent=2)+'\n')
    # Root CMake must observe transitive frontend headers too; receipts only
    # help once this driver has actually been scheduled.
    dependencies = {Path(__file__).resolve(), Path(__file__).with_name('incremental.py').resolve()}
    dependencies.add(Path(__file__).with_name('original_layout.py').resolve())
    if image['name']=='OVY_0':
        from ac_config import INPUTS as ac_inputs
        dependencies.add(Path(__file__).with_name('ac_config.py').resolve())
        dependencies.update(a.game/source for source in ac_inputs)
    dependencies.add(a.game/'lib/include/nitro/fs/overlay.h')
    dependencies.add(Path(__file__).with_name('registration_scope.py').resolve())
    dependencies.update((a.game/'Makefile',a.game/'common.mk',ROOT/'cmake/native_sources.py'))
    dependencies.update(Path(s) for s in virtual_files)
    dependencies.add(Path(__file__).with_name('frontend.py').resolve())
    dependencies.add(Path(__file__).with_name('original_data_layouts.json').resolve())
    if register_path.is_file():dependencies.add(register_path.resolve())
    if a.shared_catalog:dependencies.add(a.shared_catalog.resolve())
    for receipt in a.out.rglob('*.receipt.json'):
        dependencies.update(Path(p) for p in json.loads(receipt.read_text())['inputs']
                            if not Path(p).is_relative_to(a.out))
    def dep_escape(path):
        return str(path).replace('\\', '\\\\').replace(' ', '\\ ').replace('#', '\\#').replace('$', '$$')
    (a.out/'image.d').write_text(dep_escape(a.out/'complete.stamp')+': '+
                               ' '.join(dep_escape(p) for p in sorted(dependencies))+'\n')
    print(json.dumps(summary))
    if summary['complete_compilation']:(a.out/'complete.stamp').write_text('manifest-complete guest compilation\n')
    if not summary['complete_compilation'] and not a.report_only:raise SystemExit(1)

if __name__=='__main__':main()
