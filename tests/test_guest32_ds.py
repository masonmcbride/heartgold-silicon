"""Original OVY_0/OVY_38 entries sharing checked, original-addressed DS RAM."""
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'cmake'),str(ROOT/'compiler/guest32')]
from native_data_ir import parse,raw_layout,integer
from original_layout import anchored_sections,verified_sections,MAIN_BASE,MAIN_SIZE


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--llvm-bin',type=Path,required=True)
    p.add_argument('--lowerer',type=Path,required=True)
    a=p.parse_args();build=a.build.resolve();llvm=a.llvm_bin.resolve();clang=llvm/'clang'
    out=build/'guest32-ds-tests';out.mkdir(parents=True,exist_ok=True)
    game=ROOT/'upstream/pokeheartgold';commands=[]
    def run(args,ok=True):
        r=subprocess.run(list(map(str,args)),text=True,capture_output=True)
        commands.append(dict(command=list(map(str,args)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        assert (r.returncode==0)==ok,r.stdout+r.stderr
        return r.stdout+r.stderr
    globals={};sections=[];proof=[]
    for stem,ident in [('dwc_lib_rodata',0),('dwc_lib_data',0),('dwc_lib_bss',0),('dwc_gamespy_bss',0),('http_data',38),('http_socket_bss',38)]:
        source=game/'lib/NitroDWC/asm'/(stem+'.s')
        raw,labels,refs=raw_layout(parse(source));placement=anchored_sections(raw,labels,ident)
        # An unanchored section must stay unknown, never inherit a neighbour.
        if stem=='http_data':assert '.data' not in placement
        historical=json.loads((ROOT/'compiler/guest32/original_data_layouts.json').read_text()).get(str(source.relative_to(game)))
        if historical:placement.update(verified_sections(raw,labels,refs,historical))
        for section,meta in placement.items():
            for name,(s,off) in labels.items():
                if s==section:globals[name]=dict(offset=meta['address']+off,size=len(raw[s])-off)
            proof.append(dict(source=str(source.relative_to(game)),section=section,**meta))
            sections.append((meta['address'],raw[section],[(off,expr,width) for (s,off),(expr,width) in refs.items() if s==section]))
    # Prove disagreement is rejected independently of the original source data.
    try:anchored_sections({'.bss':bytes(16)},{'ov00_02000000':('.bss',0),'ov00_02000008':('.bss',4)},0)
    except ValueError:pass
    else:raise AssertionError('inconsistent anchors accepted')
    units=[];codes={}
    entries={'gt_socket':['gt2Listen'],'gt_connection':['gti2Listen'],
             'http_engine_init':['NdEngine_Base64Encode','NdEngine_Base64Decode']}
    for stem,roots in entries.items():
        source=game/'lib/NitroDWC/src'/(stem+'.c');ir=out/(stem+'.ll')
        run([clang,'-target','armv5-apple-darwin','-ffreestanding','-fno-builtin','-fsigned-char','-fno-short-enums','-std=gnu89',
             '-DSDK_ARM9','-DSDK_CODE_ARM','-DSDK_FINALROM',
             '-I'+str(build/'include'),'-I'+str(game/'include'),'-I'+str(game/'include/library'),'-I'+str(game/'lib/include'),
             '-O0','-g','-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes','-S','-emit-llvm',source,'-o',ir])
        desc=out/(stem+'.json');run([a.lowerer,ir,out/'unused.ll','--diagnose',desc])
        data=json.loads(desc.read_text())
        for f in data['functions']:
            old=codes.get(f['key'])
            if old and (old['definition'] or not f['definition']):continue
            f=copy.deepcopy(f);f.update(native='guest32_'+f['name'],used_flat=[True]*len(f['params']),coalesce=False,address_taken=False)
            codes[f['key']]=f
        for g in data['globals']:
            if not g['definition']:continue
            m=re.fullmatch('ov38_([0-9A-Fa-f]{8})',g['name'])
            assert m,('unverified original C address',g)
            globals[g['name']]=dict(offset=int(m[1],16),size=g['size'])
        units.append((stem,ir,roots))
    spec=json.loads((ROOT/'compiler/guest32/ovy0_registers.json').read_text())
    import hashlib
    for relative,digest in spec['source_hashes'].items():assert hashlib.sha256((game/relative).read_bytes()).hexdigest()==digest
    edges=[dict(e,source=str(game/e['source'])) for e in spec['edges']]
    for i,f in enumerate(codes.values()):f['address']=0x10000000+i*4
    catalog=out/'image.json';catalog.write_text(json.dumps(dict(codes=list(codes.values()),register_edges=edges)))
    abi=out/'abi.json';abi.write_text(json.dumps(dict(version=1,calls={},exports={},globals=globals)))
    # Load original bytes with genuine DS data relocations. Code references are
    # deliberately excluded here: full code identity/provider admission is separate.
    known={n:v['offset'] for n,v in globals.items()}
    # This regression reserves verified data, not the unimplemented full image
    # text/residency map. Its allocator boundary is a fixture choice.
    static_end=(max(m['address']+m['size'] for m in proof)+15)&~15
    lines=['#define DS_STATIC_END '+str(static_end)+'u','static void load_original_data(void *ram){']
    loaded=[];relocations=0
    for i,(address,data,refs) in enumerate(sections):
        try:values=[(off,integer(expr,known),width) for off,expr,width in refs]
        except ValueError:continue
        lines+=['{ static const unsigned char bytes[]={'+','.join(map(str,data))+'};',
                'unsigned char *p=g32_resolve(ram,'+str(address)+','+str(len(data))+',0);memcpy(p,bytes,sizeof bytes);']
        for off,value,width in values:
            assert width==4
            lines+=['{uint32_t v='+str(value&0xffffffff)+';memcpy(p+'+str(off)+',&v,4);}']
            relocations+=1
        lines+=['}'];loaded.append(address)
    lines+=['}'];assert globals['gNdBase64Alphabet']['offset']>=MAIN_BASE
    assert relocations>0
    assert next(m['address'] for m in proof if m['source'].endswith('http_data.s') and m['section']=='.rodata') in loaded
    (out/'ds_expectations.h').write_text('\n'.join(lines)+'\n')
    native=out/'native.ll';native.write_text('target datalayout = "e-p:64:64"\n')
    results=[]
    for opt in ['0','2']:
        for sanitized in [False,True]:
            tag='O'+opt+('.asan' if sanitized else '')
            san=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitized else []
            objects=[]
            for stem,ir,roots in units:
                dest=out/(stem+'.'+tag+'.ll')
                run([a.lowerer,ir,dest,'--abi',abi,'--native-ir',native,'--image',catalog,'--guest-externals',
                     '--prefix','guest32_',*[arg for entry in roots for arg in ['--entry',entry]],*(['--asan'] if sanitized else [])])
                run([llvm/'opt','-passes=verify','-disable-output',dest])
                obj=out/(stem+'.'+tag+'.o');run([clang,'-O'+opt,*san,'-c',dest,'-o',obj]);objects.append(obj)
            exe=out/('test.'+tag)
            run([clang,'-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),'-I'+str(out),ROOT/'tests/guest32_ds_host.c',
                 ROOT/'hardware_drivers/guest32.c',*objects,'-Wl,-dead_strip','-o',exe])
            results.append(run([exe]).strip())
            for mode in ['below','above','overflow','foreign','null','freed','frame']:
                diagnostic=run([exe,mode],ok=False);assert 'guest32 memory:' in diagnostic,diagnostic
            if sanitized:assert 'AddressSanitizer: use-after-poison' in run([exe,'asan-freed'],ok=False)
    (out/'results.json').write_text(json.dumps(dict(results=results,placement=proof,loaded_sections=loaded,relocations=relocations,
        scope='selected original entries; not full images, overlay lifecycle, or missing-provider admission'),indent=2)+'\n')
    print('\n'.join(results))

if __name__=='__main__':main()
