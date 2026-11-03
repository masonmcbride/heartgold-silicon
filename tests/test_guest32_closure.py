"""Original OVY_38 register/data contracts and executable account/CRC providers."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cmake'))
from native_data_ir import parse,raw_layout,integer


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--llvm-bin',type=Path,required=True);p.add_argument('--lowerer',type=Path,required=True)
    a=p.parse_args();b=a.build.resolve();llvm=a.llvm_bin.resolve();game=ROOT/'upstream/pokeheartgold'
    out=b/'guest32-closure-tests';out.mkdir(exist_ok=True);commands=[]
    def run(args,ok=True):
        r=subprocess.run(list(map(str,args)),capture_output=True,text=True)
        commands.append(dict(command=list(map(str,args)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        assert (r.returncode==0)==ok,r.stdout+r.stderr
        return r.stdout+r.stderr
    run(['cmake','--build',b,'--target','heartgold_guest32_ovy38_archive','heartgold_guest32_account_build','heartgold_guest32_crc_build','-j8'])
    image=b/'guest32-ovy38-image';catalog=json.loads((image/'image.json').read_text());coverage=json.loads((image/'coverage.json').read_text())
    assert coverage['summary']['compiled']==8 and coverage['summary']['data_represented']==2 and coverage['summary']['complete_compilation']
    register=json.loads((ROOT/'compiler/guest32/ovy38_registers.json').read_text())
    old=run(['git','-C',game,'show',register['provenance']['commit']+':'+register['provenance']['path']])
    assert hashlib.sha256(old.encode()).hexdigest()==register['provenance']['sha256']
    for proof in register['original_functions'].values():assert proof in old
    data_proof=json.loads((ROOT/'compiler/guest32/original_data_layouts.json').read_text())['lib/NitroDWC/asm/http_data.s']
    historical_data=old[old.index('\t.data\n'):old.index('\t.bss\n')]
    assert hashlib.sha256(historical_data.encode()).hexdigest()==data_proof['provenance']['section_sha256']
    # Independent source snapshots versus the actual generated loader functions.
    known={n:v['offset'] for n,v in catalog['assembly_globals'].items()}
    known.update({f['name']:f['address'] for f in catalog['codes'] if not f['local']})
    known.update({n:v['offset'] for n,v in catalog['c_globals'].items() if '|' not in n})
    checks=[];declarations=[];objects=[];index=0;relocations=0
    for m in coverage['members']:
        if m['kind']!='assembly':continue
        raw,labels,refs=raw_layout(parse(game/m['source']))
        for section,data in raw.items():
            first=next((n,o) for n,(s,o) in labels.items() if s==section);base=known[first[0]]-first[1]
            expected=bytearray(data)
            for (s,off),(expr,width) in refs.items():
                if s==section:expected[off:off+width]=(integer(expr,known)&((1<<(width*8))-1)).to_bytes(width,'little');relocations+=1
            name='guest32_image_38_data_'+str(index);declarations.append('extern void '+name+'_load(void*);')
            checks.append('{static const unsigned char expected[]={'+','.join(map(str,expected))+'};'+name+'_load(ram);assert(!memcmp(g32_resolve(ram,'+str(base)+',sizeof expected,0),expected,sizeof expected));}')
            index+=1
        objects.append(image/m['object']/'native.o')
    assert relocations==4
    host=out/'data.c';host.write_text('#include "guest32.h"\n#include <assert.h>\n#include <string.h>\n'+'\n'.join(declarations)+'\nint main(void){void *ram=g32_create(1<<20,'+str(catalog['static_end'])+');assert(ram);'+''.join(checks)+'g32_destroy(ram);}\n')
    run([llvm/'clang','-I'+str(ROOT/'hardware_drivers'),host,ROOT/'hardware_drivers/guest32.c',*objects,'-o',out/'data-test']);run([out/'data-test'])
    # A mismatched source field must fail, even with the otherwise genuine catalog.
    broken=copy.deepcopy(catalog);broken['register_edges'][0]['offset']=16
    bad=out/'bad-field.json';bad.write_text(json.dumps(broken))
    member=image/'lib/NitroDWC/src/http_engine_request.o'
    diagnostic=run([a.lowerer,member/'guest.ll',out/'rejected.ll','--abi',member/'abi.json','--native-ir',image/'native-abi.ll','--image',bad,'--guest-externals','--prefix','guest32_'],ok=False)
    assert 'register branch-value field mismatch' in diagnostic
    results=[]
    for opt in ['0','2']:
        for sanitized in [False,True]:
            tag='O'+opt+('.asan' if sanitized else '');san=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitized else []
            objects=[]
            for name in ['account','crc']:
                directory=b/('guest32-'+name);ir=out/(name+'.'+tag+'.ll')
                run([a.lowerer,directory/'guest.ll',ir,'--abi',directory/'abi.json','--native-ir',directory/'native-abi.ll','--guest-externals','--prefix','guest32_',*(['--asan'] if sanitized else [])])
                obj=out/(name+'.'+tag+'.o');run([llvm/'clang','-O'+opt,*san,'-c',ir,'-o',obj]);objects.append(obj)
            exe=out/('account.'+tag)
            run([llvm/'clang','-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),ROOT/'tests/guest32_account_host.c',ROOT/'hardware_drivers/guest32.c',*objects,'-Wl,-dead_strip','-o',exe])
            results.append(run([exe]).strip())
    (out/'results.json').write_text(json.dumps(dict(results=results,original_data_sections=index,original_data_relocations=relocations,negative_contract='wrong request field rejected'),indent=2)+'\n')
    print('\n'.join(results));print('PASS all eight OVY_38 C members; original data loaders/4 relocations; register evidence and negative control')

if __name__=='__main__':main()
