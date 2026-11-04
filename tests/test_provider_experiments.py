"""Measure complete original providers; execute software contracts without SDK stubs.

All generated input, IR, objects, diagnostics and command receipts stay in --build.
This probe does not admit experimental objects as completed original images.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'compiler/guest32'), str(ROOT/'cmake')]
from native_image_graph import parse_manifest, source_record
from incremental import run as cached_run


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'llvm-bin', 'lowerer'):
        p.add_argument('--'+name, required=True, type=Path)
    p.add_argument('--execute',action='store_true',help='Run the original software and data regressions after the translation census')
    a = p.parse_args()
    b, llvm, lowerer = a.build.resolve(), a.llvm_bin.resolve(), a.lowerer.resolve()
    out = b/'provider-experiments'
    out.mkdir(parents=True, exist_ok=True)
    game = ROOT/'upstream/pokeheartgold'
    inventory = json.loads((ROOT/'docs/provider-closure/provider-176.json').read_text())['unresolved_provider_demands']
    ledger = (ROOT/'docs/provider-closure/OVY_0_38_176_symbol_fix_ledger_v9.md').read_text()
    assert len(inventory) == 176
    assert set(re.findall(r'^### \d+\. `([^`]+)`', ledger, re.M)) == set(inventory)
    manifest = parse_manifest(game/'main.lsf')['main']['objects']
    sources = {r['source']: m for m in manifest for r in [source_record(game, m)] if 'source' in r}
    selected = {d['source'] for v in inventory.values() for d in v['original_definitions'] if d['owner']=='main' and d['kind']=='C function definition text'}
    selected.update('lib/NitroSystem/src/'+n+'.c' for n in ('fnd_heapcommon', 'fnd_list'))
    selected.update('lib/libVCT/src/'+n+'.c' for n in ('vct_audio_queue','vct_decoder','vct_packet_buffer'))
    selected.update('lib/NitroWiFi/src/'+n+'.c' for n in ('socl_command','socl_socket','socl_read','socl_write'))
    selected.add('lib/NitroSDK/src/wm_settings.c')
    flags = ['-target','armv5-apple-darwin','-ffreestanding','-fno-builtin','-fsigned-char','-fno-short-enums','-std=gnu89',
             '-DSDK_ARM9','-DSDK_CODE_ARM','-DSDK_FINALROM','-DHEARTGOLD','-DENGLISH',
             '-Wno-error=incompatible-pointer-types',
             *['-I'+str(d) for d in (b/'include',game/'include',game/'include/library',game/'lib/include',game/'lib/NitroSDK/include',b/'generated/files')],
             '-O0','-g','-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes']
    def run(args, outputs=(), inputs=(), depfile=None):
        r = cached_run(list(map(str,args)),list(outputs),inputs=list(inputs),**({'depfile':depfile} if depfile else {}))
        return r
    def frontend(relative):
        assert relative in sources, relative
        source = game/relative
        work = out/'members'/sources[relative]
        work.mkdir(parents=True,exist_ok=True)
        ir, desc = work/'guest.ll', work/'description.json'
        cmd = [llvm/'clang',*flags,'-S','-emit-llvm',source,'-o',ir,'-MD','-MF',str(ir)+'.d']
        r = run(cmd,[ir],[source],str(ir)+'.d')
        (work/'frontend.log').write_text(r.stdout+r.stderr)
        record = dict(source=relative,member=sources[relative],sha256=hashlib.sha256(source.read_bytes()).hexdigest(),frontend=r.returncode==0,frontend_diagnostic=r.stderr)
        if not r.returncode:
            r = run([lowerer,ir,work/'unused.ll','--diagnose',desc],[desc],[ir])
            if not r.returncode: record['description'] = json.loads(desc.read_text())
        return record
    with ThreadPoolExecutor(max_workers=4) as pool:
        members = list(pool.map(frontend,sorted(selected)))
    # One catalog for each independent experiment. No per-name algorithm changes.
    groups = {
        'heap': ['fnd_expheap','fnd_heapcommon','fnd_list'],
        'sound': ['snd_stream','fnd_list'],
        'vct': ['vct_audio','vct_audio_queue','vct_decoder','vct_packet_buffer','vct_vad'],
        'soc': ['soc','soc_inet','wcm','socl_command','socl_socket','socl_read','socl_write','wm_core','wm_requests','wm_settings'],
        'other': ['rand','msl_string_extras','msl_qsort'],
    }
    native = out/'native.ll'
    native.write_text('target datalayout = "e-p:64:64"\n')
    for group, stems in groups.items():
        records = [m for m in members if Path(m['source']).stem in stems and 'description' in m]
        functions, globals_ = {}, {}
        cursor = 0x02300000
        for m in records:
            for f in m['description']['functions']:
                old = functions.get(f['key'])
                if not old or f['definition']: functions[f['key']] = dict(f)
                functions[f['key']]['address_taken'] |= bool(old and old['address_taken'])
            for g in m['description']['globals']:
                if not g['definition']: continue
                if g['key'] in globals_:
                    assert globals_[g['key']]['size']==g['size']
                    continue
                cursor = (cursor+g['alignment']-1)&~(g['alignment']-1)
                globals_[g['key']] = dict(offset=cursor,size=g['size'])
                cursor += g['size']
        codes=[]
        for key, f in sorted(functions.items()):
            f.update(address=0x18000000+len(codes)*4,native='guest32_'+(hashlib.sha256(key.encode()).hexdigest()[:16]+'_' if f['local'] else '')+f['name'],coalesce=False,used_flat=[True]*len(f['params']))
            if f['definition'] and not f['local'] and Path(f.get('origin','')).suffix=='.h': f['coalesce']=True
            codes.append(f)
        directory=out/group;directory.mkdir(exist_ok=True)
        catalog=directory/'catalog.json';catalog.write_text(json.dumps(dict(codes=codes,c_globals=globals_,static_end=cursor),indent=2)+'\n')
        for m in records:
            work=out/'members'/m['member'];abi=work/'abi.json'
            coordinates={g['name']:globals_[g['key']] for g in m['description']['globals'] if g['key'] in globals_}
            abi.write_text(json.dumps(dict(version=1,calls={},exports={},globals=coordinates)))
            cmd=[lowerer,work/'guest.ll',work/'native.ll','--abi',abi,'--native-ir',native,'--image',catalog,'--guest-externals','--prefix','guest32_']
            r=run(cmd,[work/'native.ll'],[work/'guest.ll',abi,native,catalog])
            (work/'lower.log').write_text(r.stdout+r.stderr)
            m['lowered']=r.returncode==0
            m['blocking_diagnostic']=r.stderr
            if not r.returncode:
                r=run([llvm/'clang','-O2','-c',work/'native.ll','-o',work/'native.o'],[work/'native.o'],[work/'native.ll'])
                (work/'object.log').write_text(r.stdout+r.stderr);m['compiled']=r.returncode==0
    # Also measure every remaining complete member in ordinary member mode.
    measured={m['source'] for m in members if 'lowered' in m}
    for m in members:
        if m['source'] in measured or not m['frontend']: continue
        work=out/'members'/m['member']
        r=subprocess.run([sys.executable,'-B',str(ROOT/'compiler/guest32/member.py'),'--game',str(game),'--build',str(b),'--out',str(work),'--llvm-bin',str(llvm),'--lowerer',str(lowerer),'--owner','main','--member',m['member']],capture_output=True,text=True)
        (work/'member.log').write_text(r.stdout+r.stderr)
        m['compiled']=r.returncode==0;m['blocking_diagnostic']=r.stderr
    demands={}
    by_source={m['source']:m for m in members}
    for n,v in inventory.items():
        definitions=[d for d in v['original_definitions'] if d['kind'] in ('C function definition text','assembly label','tentative C data definition text')]
        if n=='rand': definitions=[d for d in definitions if d['source']=='lib/MSL_C/src/rand.c']
        rows=[]
        for d in definitions:
            source=game/d['source'];m=by_source.get(d['source'])
            row=dict(d,hash_matches=hashlib.sha256(source.read_bytes()).hexdigest()==d['sha256'])
            if m:
                row.update(frontend=m['frontend'],compiled=m.get('compiled',False),blocking_diagnostic=m.get('blocking_diagnostic',''))
                row['definition_in_ir']=any(f['name']==n and f['definition'] for f in m.get('description',{}).get('functions',[]))
                row['direct_calls']=sorted({c['target'] for c in m.get('description',{}).get('calls',[]) if c['function']==n})
            rows.append(row)
        demands[n]=dict(imports=v['symbols'],images=v['images'],signature=v['guest_signature'],definitions=rows,
                        evidence='original translation compiled' if any(r.get('compiled') and r.get('definition_in_ir') for r in rows) else 'original source located',
                        image_linked=False,cross_image_bound=False,software_executed=False,full_contract_validated=False)
    # Actual function-level direct-call SCCs; indirect/hardware edges stay unknown.
    graph={}
    for m in members:
        keys={f['name']:f['key'] for f in m.get('description',{}).get('functions',[])}
        for f in m.get('description',{}).get('functions',[]):
            if f['definition']:graph.setdefault(f['key'],set())
        for c in m.get('description',{}).get('calls',[]):
            caller=keys.get(c['function'],c['function'])
            target=c['target'] or 'INDIRECT:'+m['source']+':'+c['function']+':'+str(c['line'])
            graph.setdefault(caller,set()).add(target)
    index={};low={};stack=[];active=set();scc=[]
    def visit(v):
        index[v]=low[v]=len(index);stack.append(v);active.add(v)
        for w in graph.get(v,()):
            if w not in index:visit(w);low[v]=min(low[v],low[w])
            elif w in active:low[v]=min(low[v],index[w])
        if low[v]==index[v]:
            component=[]
            while True:
                w=stack.pop();active.remove(w);component.append(w)
                if w==v:break
            scc.append(sorted(component))
    for v in list(graph):
        if v not in index:visit(v)
    result=dict(inventory_sha256=hashlib.sha256((ROOT/'docs/provider-closure/provider-176.json').read_bytes()).hexdigest(),demands=demands,members=members,
                counts=dict(Counter(v['evidence'] for v in demands.values())),
                graph=dict(scope='Observed direct IR call edges only; not a complete semantic dependency graph',edges={n:sorted(v) for n,v in graph.items()},scc=sorted(scc,key=lambda x:(-len(x),x))))
    (out/'census.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['counts']))
    print('Members',len(members),'frontend',sum(m['frontend'] for m in members),'compiled',sum(m.get('compiled',False) for m in members))
    if a.execute:
        def execute(args):subprocess.run(list(map(str,args)),check=True)
        execute([sys.executable,'-B',ROOT/'compiler/guest32/data.py','--game',game,'--out',out/'main-data','--llvm-bin',llvm,'--owner','main',
                 '--member','lib/MSL_C/asm/MSL_Common_ctype.o','--member','lib/MSL_C/asm/MSL_Common_errno.o','--member','lib/asm/wifi_bss.o'])
        execute([sys.executable,'-B',ROOT/'compiler/guest32/member.py','--game',game,'--build',b,'--out',out/'string-provider','--llvm-bin',llvm,'--lowerer',lowerer,
                 '--owner','main','--member','lib/MSL_C/src/msl_string_extras.o','--catalog',out/'other/catalog.json'])
        incomplete=json.loads((out/'other/catalog.json').read_text());incomplete['c_globals']={}
        bad=out/'missing-storage.json';bad.write_text(json.dumps(incomplete))
        rejected=subprocess.run(list(map(str,[sys.executable,'-B',ROOT/'compiler/guest32/member.py','--game',game,'--build',b,'--out',out/'rejected-rng','--llvm-bin',llvm,'--lowerer',lowerer,
                                             '--owner','main','--member','lib/MSL_C/src/rand.o','--catalog',bad])),capture_output=True,text=True)
        (out/'missing-storage-rejection.log').write_text(rejected.stdout+rejected.stderr)
        assert rejected.returncode and 'shared catalog lacks defined storage' in rejected.stderr
        execute([sys.executable,'-B',ROOT/'tests/provider_software_execution.py','--build',b,'--llvm-bin',llvm,'--lowerer',lowerer])
        execute([sys.executable,'-B',ROOT/'tests/provider_data_execution.py','--build',b,'--llvm-bin',llvm,'--lowerer',lowerer])
        execute([llvm/'clang',*flags,'-fsyntax-only',ROOT/'tests/provider_soc_layout_guest.c'])

if __name__=='__main__':main()
