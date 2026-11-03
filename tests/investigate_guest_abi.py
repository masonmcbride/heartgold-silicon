"""Read-only guest ABI investigation; emits evidence, never rewrites program IR.

Source slices and shape probes are labelled separately from actual built objects.
Clang ARMv5 EABI is a comparison target, not a CodeWarrior equivalence claim.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cmake'))
from native_image_graph import parse_manifest,source_record
import native_sources


def block(text,start):
    begin=text.index(start);brace=text.index('{',begin);depth=1;end=brace+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[begin:end]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--game',type=Path,default=ROOT/'upstream/pokeheartgold')
    parser.add_argument('--out',type=Path)
    args=parser.parse_args();build=args.build.resolve();game=args.game.resolve()
    out=(args.out or build/'guest-abi-design').resolve()
    if not out.is_relative_to(build):raise ValueError('Evidence must remain in selected binary directory')
    out.mkdir(parents=True,exist_ok=True)
    evidence=dict(compiler=subprocess.check_output(['clang','--version'],text=True),commands=[],inputs={},probes={})
    def read(relative):
        path=game/relative;text=path.read_text();evidence['inputs'][relative]=hashlib.sha256(path.read_bytes()).hexdigest();return text
    def run(command,dest=None):
        r=subprocess.run(command,capture_output=True,text=True)
        evidence['commands'].append(dict(command=list(map(str,command)),returncode=r.returncode,diagnostics=r.stderr))
        if dest:dest.write_text(r.stdout+r.stderr)
        if r.returncode:raise RuntimeError('Investigation command failed: '+shlex.join(list(map(str,command)))+'\n'+r.stderr)
        return r.stdout
    for relative in ['main.lsf','Makefile','common.mk']:
        read(relative)
    evidence['native_sources_sha256']=hashlib.sha256((ROOT/'cmake/native_sources.py').read_bytes()).hexdigest()
    images=parse_manifest(game/'main.lsf');members=sorted({m for i in images.values() for m in i['objects']})
    patterns={
        'integer_pointer_cast_candidates':r'\(\s*(?:u32|s32|unsigned int|unsigned long)\s*\)',
        'bitfield_candidates':r'\b(?:u8|u16|u32|unsigned\s+(?:int|char|short))\s+\w+\s*:\s*\d+',
        'raw_offset_candidates':r'\(\s*(?:u8|char|unsigned char)\s*\*\s*\).*?(?:\+|-)\s*(?:0x[\da-fA-F]+|\d+)',
        'assembly_candidates':r'\basm\b|\b(?:arm_func_start|thumb_func_start)\b',
        'member_pointer_candidates':r'::\*|->\*',
        'varargs_candidates':r'\b(?:va_start|va_arg|va_list)\b',
        'control_candidates':r'\b(?:OS_SaveContext|OS_LoadContext|OS_KillThread|setjmp|longjmp)\b',
        'device_candidates':r'\b(?:reg_[A-Z]\w*|HW_REG_BASE|CP15|mcr|mrc|SWI_\w+)\b'}
    compiled={k:re.compile(v) for k,v in patterns.items()};rows=[]
    for original in members:
        row=source_record(game,original);row['images']=[n for n,i in images.items() if original in i['objects']]
        if row.get('source'):
            path=game/row['source'];text=path.read_text();row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            row['abi_candidates']={kind:[n for n,line in enumerate(text.splitlines(),1) if pattern.search(line)]
                               for kind,pattern in compiled.items()}
        rows.append(row)
    headers=[]
    for directory in ['include','lib/include']:
        for path in sorted((game/directory).rglob('*.h')):
            text=path.read_text();hits={k:[n for n,line in enumerate(text.splitlines(),1) if p.search(line)] for k,p in compiled.items()}
            if any(hits.values()):headers.append(dict(source=str(path.relative_to(game)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),candidates=hits))
    census=dict(scope='All manifest members and matching declarations in original include/ and lib/include/. Lexical candidates include comments/inactive branches; counts are not proven failures.',
        images=len(images),members=len(rows),placements=sum(len(i['objects']) for i in images.values()),
        kinds=dict(Counter(r['kind'] for r in rows)),
        candidate_members={k:sum(bool(r.get('abi_candidates',{}).get(k)) for r in rows) for k in patterns},
        native_adaptation_entries=len(native_sources.OVERLAY_NATIVE_SOURCES),records=rows,headers=headers)
    (out/'census.json').write_text(json.dumps(census,indent=2)+'\n')
    prefix='typedef unsigned char u8;typedef unsigned short u16;typedef unsigned int u32;typedef unsigned long long u64;typedef int s32;typedef short s16;\n'
    match=read('lib/include/dwc/match_internal.h');init=read('lib/NitroDWC/src/query_report_init.c');report=read('lib/NitroDWC/src/server_report.c')
    platform=read('lib/NitroDWC/src/gs_platform.c');ca=read('lib/include/cps/cps_ssl_internal.h')
    types=prefix
    for text,name in [(match,'MatchKeyEntry'),(init,'QueryReport'),(report,'SockAddr'),(report,'QRBuffer'),(report,'QRKeyList')]:
        types+=block(text,'typedef struct '+name+' {')+' '+name+';\n'
    types+='\n'.join(re.findall(r'(?m)^typedef .*\(\*QR\w+Callback\).*;',report))+'\n'
    for text,name in [(report,'QRRecord'),(platform,'Ov00SocketState'),(ca,'CpsRootCa')]:types+=block(text,'typedef struct '+name+' {')+' '+name+';\n'
    login=read('lib/NitroDWC/src/dwc_login.c');browse=read('lib/NitroDWC/src/match_browse.c');voice=read('src/voice_chat.c')
    store=next(l.strip() for l in login.splitlines() if '((int *)&gDwcControl)[1] = error;' in l)
    align=next(l.strip() for l in voice.splitlines() if '*aligned = (void *)(((u32)*allocation' in l)
    stores='\n'.join(re.findall(r'(?m)^    qr->(?:callbacks\[\d\]|userData) = \w+;',init))
    body='''extern MatchKeyEntry gDwcMatchKeys[154];extern void *gDwcControl;
void *typed_value(int i) {return gDwcMatchKeys[i].value;}
u8 raw_id(int id) {int index=id-100;index*=12;return *((u8 *)gDwcMatchKeys+index);}
void socket_error(int error) {'''+store+'''}
void pointer_alignment(void **allocation,void **aligned) {'''+align+'''}
void query_write(QueryReport *qr,u32 cb0,u32 cb1,u32 cb2,u32 cb3,u32 cb4,u32 cb5,u32 userData) {'''+stores+'''}
void query_read(QRRecord *r,u8 k,QRBuffer *b) {r->serverKeyCallback(k,b,r->param);}
char **alias_base(Ov00SocketState *s) {return (char **)((char *)&s->hName-8);}
CpsRootCa abi_shape(CpsRootCa value) {return value;}
extern void sink(void *);
void stack_address(u32 value) {u32 local=value;sink(&local);}
u32 scalar_long_width(void) {return sizeof(long);}
u32 layouts[] = {sizeof(void *),sizeof(MatchKeyEntry),__builtin_offsetof(MatchKeyEntry,value),sizeof(QueryReport),sizeof(QRRecord),__builtin_offsetof(QueryReport,lastHeartbeatTime),__builtin_offsetof(QRRecord,lastHeartbeatTime),sizeof(CpsRootCa)};
'''
    cases={'dwc':(types+body,'c','actual declarations and operation slices; typed getter, ABI shape and stack sink are labelled harness probes')}
    pmf=read('src/lobby/ppw_lobby_players_all_have_profiles.cpp');remove=read('src/lobby/lobby_chat_remove_channel.cpp')
    cpp=prefix+block(pmf,'struct Value {')+';\n'+re.search(r'typedef bool \(Value::\*Pmf\)\(\);',pmf)[0]+'\n'
    cpp+=block(pmf,'struct Holder {')+';\n'+block(pmf,'struct Pred {')+';\n'
    cpp+='extern "C" Holder ov45_02255200;\nstruct SetNode;\n'
    for name in ['MapNode','ChannelMap','Root']:cpp+=block(remove,'struct '+name+' {')+';\n'
    cpp+=re.search(r'typedef void \(Root::\*Method\)\(int\);',remove)[0]+'\n'
    for name in ['MemberTable','Bound']:cpp+=block(remove,'struct '+name+' {')+';\n'
    cpp+='extern "C" const MemberTable ov45_02255358;\nextern "C" bool call_pred(Value *v) {return Pred(ov45_02255200.pmf)(v);}\n'
    cpp+='extern "C" void call_bound(Root *r,int v) {Bound(ov45_02255358.method,r)(v);}\n'
    cpp+='extern "C" void *map_address(Root *r) {return &r->channels;}\n'
    cpp+='extern "C" const u32 cpp_layouts[]={sizeof(Pmf),sizeof(Holder),__builtin_offsetof(Holder,pmf),sizeof(MemberTable),__builtin_offsetof(MapNode,isize),__builtin_offsetof(MapNode,hdr),__builtin_offsetof(MapNode,first)};\n'
    cases['plaza']=(cpp,'c++','actual private declarations and member invocation expressions; wrappers do not implement game routines')
    map_header=read('include/map_header.h')
    bits=prefix+block(map_header,'typedef struct MapHeader {')+' MapHeader;\n'
    bits+='const MapHeader control={.wildEncounterBank=0x12,.areaDataBank=0x34,.moveModelBank=3,.worldMapX=17,.worldMapY=22,.regionNo=1,.weather=7,.mapType=3,.cameraType=5,.bikeAllowed=1,.radioSignal=1};\n'
    cases['bitfields']=(bits,'c','actual pointer-free MapHeader; positive control, not proof of all CodeWarrior bitfield layouts')
    cases['relocation']=(prefix+'static int callback(int x){return x+7;} int (*code_reference)(int)=callback;\n','c','synthetic interworking/relocation shape probe, not an original function body')
    cases['varargs']=(prefix+'''int variadic(int count,...) {__builtin_va_list a;__builtin_va_start(a,count);int sum=0;while(count--)sum+=__builtin_va_arg(a,int);__builtin_va_end(a);return sum;}
void *msl_argument_home(u32 *arg) {return (void *)(((u32)arg & ~3u)+4);}
''','c','builtin target ABI compared with original stdarg.h argument-home formula; not CodeWarrior validation')
    read('lib/include/stdarg.h')
    objdump=Path(run(['xcrun','--find','llvm-objdump']).strip())
    targets={'arm32': ['-target','armv5te-none-eabi','-mcpu=arm946e-s','-mfloat-abi=soft'],
             'arm64':['-target','arm64-apple-macos11.0']}
    for name,(text,language,scope) in cases.items():
        source=out/(name+('.cpp' if language=='c++' else '.c'));source.write_text(text)
        evidence['probes'][name]=dict(scope=scope,source=source.name)
        for target,target_flags in targets.items():
            for opt in [0,2]:
                base=out/f'{name}.{target}.O{opt}'
                command=['clang',*target_flags,'-ffreestanding','-fno-builtin','-fsigned-char','-x',language,'-std=c++17' if language=='c++' else '-std=c11',f'-O{opt}',str(source)]
                run([*command,'-S','-emit-llvm','-o',str(base.with_suffix(base.suffix+'.ll'))])
                run([*command,'-c','-o',str(base.with_suffix(base.suffix+'.o'))])
                run([str(objdump),'--disassemble','--reloc','--syms',str(base.with_suffix(base.suffix+'.o'))],base.with_suffix(base.suffix+'.disassembly'))
    thumb=out/'relocation.thumb.o'
    run(['clang',*targets['arm32'],'-mthumb','-ffreestanding','-O2','-c',str(out/'relocation.c'),'-o',str(thumb)])
    run([str(objdump),'--disassemble','--reloc','--syms',str(thumb)],out/'relocation.thumb.disassembly')
    actual=['lib/NitroDWC/src/query_report_init.c','lib/NitroDWC/src/server_report.c','lib/NitroDWC/src/gs_platform.c','lib/NitroDWC/src/match_browse.c','src/lobby/ppw_lobby_players_all_have_profiles.cpp','src/lobby/lobby_chat_remove_channel.cpp']
    run([str(objdump),'--reloc','--full-contents',str(thumb)],out/'relocation.thumb.data')
    for name in cases:
        for target in targets:
            obj=out/f'{name}.{target}.O2.o'
            run([str(objdump),'--reloc','--full-contents',str(obj)],out/f'{name}.{target}.O2.data')
    evidence['actual_objects']=[]
    for relative in actual:
        path=build/'abi-barrier/objects'/(relative+'.o')
        if not path.is_file():raise FileNotFoundError('Explicit prior original-object inventory required: '+str(path))
        destination=out/(Path(relative).stem+'.actual.disassembly')
        run([str(objdump),'--disassemble','--reloc','--syms',str(path)],destination)
        evidence['actual_objects'].append(dict(source=relative,object=str(path.relative_to(build)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),disassembly=destination.name))
    # Exercise the already-built SDK libraries without changing their implementation.
    entries=json.loads((build/'compile_commands.json').read_text())
    entry=next(e for e in entries if e['file'].endswith('/soc_inet.c'))
    flags=entry.get('arguments') or shlex.split(entry['command']);i=flags.index('-o');del flags[i:i+2]
    flags=[a for a in flags if a not in ['-c',entry['file']] and not a.startswith('-std=')]
    source=out/'sdk_runtime.c'
    source.write_text('#include <nitro.h>\n#include <stdio.h>\nint main(void) {u32 words[2]={0};OSContext ctx={0};MIi_CpuClear32(0x11223344,words,8);int initial=OS_SaveContext(&ctx);OS_LoadContext(&ctx);printf("clear=%08x,%08x initial_save=%d load_returned=1\\n",words[0],words[1],initial);return 0;}\n')
    libraries=[build/'libntr'/f'libntr_{n}.a' for n in ['mi','os','sim_state']]
    run([*flags,str(source),*map(str,libraries),'-Wl,-dead_strip','-o',str(out/'sdk_runtime')])
    run([str(out/'sdk_runtime')],out/'sdk_runtime.result.txt')
    evidence['sdk_libraries']={str(p.relative_to(build)):hashlib.sha256(p.read_bytes()).hexdigest() for p in libraries}
    (out/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({k:census[k] for k in ['images','members','placements','kinds','candidate_members','native_adaptation_entries']},indent=2))
    print('Evidence written to',out)

if __name__=='__main__':main()
