"""Historical DS placement, ARM register evidence and TU-local inline rules. MIT."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'cmake'),str(ROOT/'compiler/guest32')]
from native_data_ir import parse,raw_layout
from native_image_graph import parse_manifest
from original_layout import recover_sections,verify_recovery,verified_sections,overlay_id_constants
from registration_scope import validate_machine_edges,scoped_spec
from image import private_inline_plan
from code_ids import allocate
from frontend import cxx_flags


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','llvm-bin','lowerer'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();b=a.build.resolve();out=b/'guest32-rule-tests';out.mkdir(exist_ok=True)
    llvm=a.llvm_bin;game=ROOT/'upstream/pokeheartgold';commands=[]
    def run(args,ok=True):
        args=list(map(str,args));r=subprocess.run(args,capture_output=True,text=True)
        commands.append(dict(command=args,code=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        assert (r.returncode==0)==ok,r.stdout+r.stderr
        return r.stdout+r.stderr
    constants=overlay_id_constants(game,parse_manifest(game/'main.lsf'))
    assert '-fno-exceptions' in cxx_flags(game,'src/lobby/lobby_chat_enter_channel.o')
    assert '-fexceptions' in cxx_flags(game,'lib/MSL_C/src/msl_vector_length_error.o')
    catalog=json.loads((ROOT/'compiler/guest32/original_data_layouts.json').read_text());checked=0
    for source,proof in catalog.items():
        if proof['provenance'].get('rule')!='anchored-retained-range-v1':continue
        current=raw_layout(parse(game/source,constants=constants))
        verify_recovery(game,game/source,current,proof,constants)
        got=verified_sections(*current,proof)
        assert set(got)==set(proof['sections']) and set(got)<=set(current[0]),source
        for section,record in proof['sections'].items():
            assert record['address']>=0x02000000 and record['size']==len(current[0][section])
        planned=json.loads((b/'native-overlays/guest32-admission'/('OVY_'+str(proof['image_id']))/'plan.json').read_text())
        for name,(section,offset) in current[1].items():
            if section not in got:continue
            span=proof['sections'][section]
            assert 0<=offset<=span['size']
            view=planned['original_assembly_globals'][name]
            assert view==dict(offset=span['address']+offset,size=span['size']-offset)
        # The tail view includes interior labels; it is not a guessed C object
        # extent. All relocation words must fit in that original section.
        for (section,offset),(_,width) in current[2].items():
            if section in got:assert 0<=offset and offset+width<=proof['sections'][section]['size']
        corrupted=copy.deepcopy(proof);section=next(iter(corrupted['sections']))
        corrupted['sections'][section]['address']+=4
        try:verify_recovery(game,game/source,current,corrupted,constants)
        except ValueError:pass
        else:raise AssertionError('invented placement accepted')
        wrong_owner=copy.deepcopy(proof);wrong_owner['image_id']=38
        try:verify_recovery(game,game/source,current,wrong_owner,constants)
        except ValueError:pass
        else:raise AssertionError('foreign original image owner accepted')
        checked+=int(set(got)==set(current[0]))
    assert checked>=10
    # Execute the actual generated data loaders for the five completed owners.
    # These link only original data objects plus the existing checked arena;
    # no game callback/provider implementation is substituted.
    for ident in (39,90,91,92,93):
        directory=b/'native-overlays/guest32-admission'/('OVY_'+str(ident))
        coverage=json.loads((directory/'coverage.json').read_text())
        image=json.loads((directory/'image.json').read_text())
        assert coverage['summary']['complete_compilation']
        known={f['name']:f['address'] for f in image['codes']}
        shared=json.loads((directory/'shared.json').read_text())
        known.update({n:v['offset'] for n,v in shared['globals'].items()})
        known.update({n:v['offset'] for n,v in image['assembly_globals'].items()})
        known.update({n:v['offset'] for n,v in image['c_globals'].items() if '|' not in n})
        objects=[];declarations=[];checks=[]
        for member in coverage['members']:
            if member['kind']!='assembly':continue
            work=directory/member['object'];objects.append(work/'native.o')
            loads={(int(base),int(size)):name for name,base,size in re.findall(
                r'void (\w+_load)\(void \*ram\)\{unsigned char \*p=g32_resolve\(ram,(\d+),(\d+),0\)',(work/'data.c').read_text())}
            data,labels,refs=raw_layout(parse(game/member['source'],constants=constants))
            from native_data_ir import integer
            for section,raw in data.items():
                label,(_,offset)=next((n,v) for n,v in labels.items() if v[0]==section)
                base=image['original_assembly_globals'][label]['offset']-offset
                expected=bytearray(raw)
                for (s,offset),(expr,width) in refs.items():
                    if s!=section:continue
                    value=integer(expr,known);assert width==4 and -(1<<31)<=value<(1<<32)
                    expected[offset:offset+width]=(value&0xffffffff).to_bytes(width,'little')
                name=loads[(base,len(raw))];declarations.append('extern void '+name+'(void*);')
                checks.append('{static const unsigned char bytes[]={'+','.join(map(str,expected))+'};'+name+'(ram);assert(!memcmp(g32_resolve(ram,'+str(base)+',sizeof bytes,0),bytes,sizeof bytes));}')
        host=out/('data'+str(ident)+'.c')
        host.write_text('#include "guest32.h"\n#include <assert.h>\n#include <string.h>\n'+'\n'.join(declarations)+
            '\nint main(void){void *ram=g32_create_ds('+str(image['static_end'])+');assert(ram);'+''.join(checks)+'g32_destroy(ram);}\n')
        exe=out/('data'+str(ident))
        run([llvm/'clang','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'hardware_drivers'),host,ROOT/'hardware_drivers/guest32.c',*objects,'-o',exe]);run([exe])
    old='.rodata\nov90_02200000:\n.word ext\n.byte 1,2,3,4\n'
    historical=raw_layout(parse(out/'old.s',text=old))
    changed=raw_layout(parse(out/'new.s',text=old.replace('.word ext','.word other')))
    assert not recover_sections(changed,historical,old,90)
    ambiguous=raw_layout(parse(out/'new.s',text='.rodata\na:\n.byte 1,2,3,4\n'))
    assert not recover_sections(ambiguous,historical,old,90),'unanchored matching substring accepted'
    try:raw_layout(parse(out/'duplicate.s',text='.data\na:\n.byte 1\na:\n.byte 2\n'))
    except ValueError:pass
    else:raise AssertionError('duplicate label accepted')
    spec=json.loads((ROOT/'compiler/guest32/ovy44_registers.json').read_text())
    validate_machine_edges(game,spec)
    assert len({e['source'] for e in spec['edges']})>=2
    bad=copy.deepcopy(spec);bad['edges'][0]['evidence']=bad['edges'][0]['evidence'].replace('\n','\n\tmov r0, #0\n',1)
    try:validate_machine_edges(game,bad)
    except ValueError:pass
    else:raise AssertionError('clobbered ARM result accepted')
    bad=copy.deepcopy(spec);bad['edges'][0]['argument']=1
    try:validate_machine_edges(game,bad)
    except ValueError:pass
    else:raise AssertionError('wrong ARM register lane accepted')
    assert scoped_spec('OVY_45',spec)['edges']==[]
    empty=out/'empty.json';empty.write_text(json.dumps(dict(version=1,calls={},exports={},globals={})))
    empty_image=out/'empty-image.json';empty_image.write_text('{"codes":[]}')
    native_abi=out/'native-abi.ll';native_abi.write_text('target datalayout = "e-p:64:64"\n')
    opaque=out/'opaque.ll';opaque.write_text('target datalayout = "e-p:32:32"\n%T = type opaque\n@record = external global %T\ndefine ptr @opaque_address(){ret ptr @record}\n')
    placed=out/'opaque.json';placed.write_text(json.dumps(dict(version=1,calls={},exports={},globals=dict(record=dict(offset=0x02001000,size=4)))))
    lowered=out/'opaque-native.ll'
    run([a.lowerer,opaque,lowered,'--abi',placed,'--native-ir',native_abi,'--image',empty_image,'--guest-externals'])
    assert 'ret i32 33558528' in lowered.read_text() and '@record =' not in lowered.read_text()
    tls=out/'tls.ll';tls.write_text('target datalayout = "e-p:32:32"\n@tls = external thread_local global i32\ndefine ptr @tls_address(){ret ptr @tls}\n')
    assert 'TLS global requires guest thread ownership' in run([a.lowerer,tls,out/'bad.ll','--abi',empty,'--native-ir',native_abi,'--image',empty_image,'--guest-externals'],ok=False)
    # The real original call must continue to reject without its proved edge.
    directory=b/'native-overlays/guest32-admission/OVY_44'
    no_edges=json.loads((directory/'image.json').read_text());no_edges['register_edges']=[]
    path=out/'unproved-calls.json';path.write_text(json.dumps(no_edges))
    work=directory/'src/wifi_club/wifi_club_game_entry.o'
    args=[a.lowerer,work/'guest.ll',out/'unproved.ll','--abi',work/'abi.json',
          '--native-ir',directory/'native-abi.ll','--image',path,'--guest-externals',
          '--prefix','guest32_','--entry','WifiClubGameEntry_EnableVoiceChat']
    assert 'missing observable guest argument' in run(args,ok=False)

    # Two original request constructors retain different source/vtable identities.
    members=[]
    for name in ('lobby_chat_enter_channel','lobby_chat_get_channel_mode_async'):
        ir=b/'native-overlays/guest32-admission/OVY_45/src/lobby'/(name+'.o')/'guest.ll'
        desc=out/(name+'.json')
        run([a.lowerer,ir,out/'unused.ll','--diagnose',desc])
        members.append(dict(object=name,description=json.loads(desc.read_text())))
    requests,unsafe=private_inline_plan(members);assert not unsafe
    keys=[]
    for member in members:
        name=member['object'];ir=b/'native-overlays/guest32-admission/OVY_45/src/lobby'/(name+'.o')/'guest.ll'
        desc=out/(name+'.private.json')
        run([a.lowerer,ir,out/'unused.ll','--diagnose',desc,*requests[name]])
        fn=next(f for f in json.loads(desc.read_text())['functions'] if f['name']=='_Z10NewHandlermm')
        assert fn['local'] and fn['private_inline']
        keys.append(fn['key'])
        body=re.search(r'(?ms)^define[^\n]*@_Z10NewHandlermm\([^\n]*\).*?^}',ir.read_text()).group()
        target='gLobbyEnterChannelRequestVtable' if name.endswith('enter_channel') else 'gLobbyGetChannelModeRequestVtable'
        assert '@'+target in body
    assert len(set(keys))==2
    outside=dict(object='outside',description=dict(functions=[dict(name='_Z10NewHandlermm',definition=False,referenced=True)]))
    rejected,unsafe=private_inline_plan([*members,outside])
    assert '_Z10NewHandlermm' in unsafe and all('_Z10NewHandlermm' not in v for v in rejected.values())
    asm=dict(object='callbacks.s',relocations=[dict(expression='_Z10NewHandlermm',width=4)])
    _,unsafe=private_inline_plan([*members,asm]);assert '_Z10NewHandlermm' in unsafe
    header=copy.deepcopy(members)
    header[0]['description']['functions'].append(dict(name='header_caller',origin='header.hpp',source='source.cpp',definition=True))
    header[0]['description']['calls'].append(dict(function='header_caller',target='_Z10NewHandlermm'))
    _,unsafe=private_inline_plan(header);assert '_Z10NewHandlermm' in unsafe
    header[0]['description']['functions'][-1].update(private_inline_eligible=True)
    selected,unsafe=private_inline_plan(header)
    assert not unsafe and 'header_caller' in selected[header[0]['object']]
    outside_header=dict(object='outside-header',description=dict(functions=[dict(name='header_caller',definition=False,referenced=True)]))
    _,unsafe=private_inline_plan([*header,outside_header])
    assert {'header_caller','_Z10NewHandlermm'}<=unsafe
    escape=out/'escape.cpp';escape.write_text('inline unsigned escaped(unsigned x){return x;}\nextern "C" void *escape(){return (void*)&escaped;}\n')
    ir=out/'escape.ll';desc=out/'escape.json'
    run([llvm/'clang++','-target','armv5-apple-darwin','-g','-O0','-S','-emit-llvm',escape,'-o',ir])
    run([a.lowerer,ir,out/'unused.ll','--diagnose',desc])
    fn=next(f for f in json.loads(desc.read_text())['functions'] if 'escaped' in f['name'])
    assert fn['address_taken'] and not fn['private_inline_eligible']
    assert 'unproved translation-unit inline identity' in run([a.lowerer,ir,out/'unused.ll','--private-inline',fn['name']],ok=False)

    # Executable compiler fixtures exercise the rule, not substitute game providers.
    (out/'region.h').write_text('inline unsigned *header_record(unsigned *r,unsigned x){return make_record(r,x); }\n')
    fixtures=[];functions={}
    for name,tag in (('left',11),('right',29)):
        source=out/(name+'.cpp');source.write_text('static unsigned tag='+str(tag)+';\n'
            'inline unsigned *make_record(unsigned *r,unsigned x){r[0]=(unsigned)&tag;r[1]=x+'+str(tag)+';return r;}\n'
            '#include "region.h"\nextern "C" unsigned *'+name+'(unsigned *r,unsigned x){return header_record(r,x);}\n')
        ir=out/(name+'.ll');desc=out/(name+'.json')
        run([llvm/'clang++','-target','armv5-apple-darwin','-std=gnu++98','-ffreestanding','-g','-O0','-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes','-S','-emit-llvm',source,'-o',ir])
        run([a.lowerer,ir,out/'unused.ll','--diagnose',desc])
        d=json.loads(desc.read_text());helper=next(f for f in d['functions'] if 'make_record' in f['name'])
        assert helper['private_inline_eligible']
        flags,unsafe=private_inline_plan([dict(object=name,description=d)])
        assert not unsafe
        flags=flags[name]
        assert any('header_record' in x for x in flags)
        run([a.lowerer,ir,out/'unused.ll','--diagnose',desc,*flags]);d=json.loads(desc.read_text())
        for f in d['functions']:
            if f['definition']:functions[f['key']]=f
        global_name=next(g['name'] for g in d['globals'] if g['definition'])
        fixtures.append((name,ir,flags,0x02001000+len(fixtures)*16,global_name))
    codes=[];ids=allocate(functions)
    for key,f in functions.items():codes.append(dict(f,address=ids[key],native='fixture_'+(hashlib.sha256(key.encode()).hexdigest()[:16] if f['local'] else f['name']),used_flat=[True]*len(f['params'])))
    image=out/'image.json';image.write_text(json.dumps(dict(codes=codes)))
    native=out/'abi.ll';native.write_text('target datalayout = "e-p:64:64"\n')
    for opt in ('0','2'):
        objects=[];initializers=[];san=['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        for name,ir,flags,offset,global_name in fixtures:
            abi=out/(name+'.abi.json');abi.write_text(json.dumps(dict(version=1,calls={},exports={},globals={global_name:dict(offset=offset,size=4)})))
            lowered=out/(name+'.native.ll');obj=out/(name+'.O'+opt+'.o')
            run([a.lowerer,ir,lowered,'--abi',abi,'--native-ir',native,'--image',image,'--guest-externals','--prefix','fixture_','--asan',*flags])
            initializers+=re.findall(r'^define void @(fixture_initialize_\w+)',lowered.read_text(),re.M)
            run([llvm/'clang','-O'+opt,*san,'-c',lowered,'-o',obj]);objects.append(obj)
        host=out/'host.c';host.write_text('#include "guest32.h"\n#include <assert.h>\n#include <stdint.h>\n'
            'extern uint32_t fixture_left(void*,uint32_t,uint32_t),fixture_right(void*,uint32_t,uint32_t);\n'+
            ''.join('extern void '+n+'(void*);\n' for n in initializers)+
            'int main(void){void *r=g32_create_ds(0x02002000);assert(r);'+''.join(n+'(r);' for n in initializers)+
            'uint32_t *p=g32_allocate(r,16,4);uint32_t a=g32_encode(r,p,16,0);assert(fixture_left(r,a,7)==a);assert(fixture_right(r,a+8,7)==a+8);assert(p[0]==0x02001000&&p[1]==18&&p[2]==0x02001010&&p[3]==36);assert(*(uint32_t*)g32_resolve(r,p[0],4,0)==11);assert(*(uint32_t*)g32_resolve(r,p[2],4,0)==29);g32_destroy(r);}\n')
        exe=out/('execute.O'+opt)
        run([llvm/'clang','-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),host,ROOT/'hardware_drivers/guest32.c',*objects,'-o',exe]);run([exe])
    print('PASS',checked,'complete original historical members, original ARM edges, distinct original inline identities, opaque/TLS boundaries, executable O0/O2 ASan/UBSan fixtures')


if __name__=='__main__':main()
