"""Production evidence and rejection checks for the real network batch. MIT."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','llvm-bin','lowerer'):
        p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();b=a.build.resolve();out=b/'native-overlays/guest32-admission'
    sys.path[:0]=[str(ROOT/'cmake'),str(ROOT/'compiler/guest32')]
    from native_image_graph import parse_manifest
    from original_layout import overlay_id_constants
    from native_data_ir import parse,raw_layout
    game=ROOT/'upstream/pokeheartgold'
    original=parse_manifest(game/'main.lsf')
    data,labels,refs=raw_layout(parse(game/'asm/gts_data.s',constants=overlay_id_constants(game,original)))
    section,offset=labels['gGtsTradeSequenceTemplate']
    assert int.from_bytes(data[section][offset+12:offset+16],'little')==original['OVY_71']['id']
    assert (section,offset+12) not in refs
    r=subprocess.run([sys.executable,'-B',str(ROOT/'cmake/guest32_admission.py'),
        '--build',str(b),'--closure',str(b/'provider-closure170'),'--out',str(out),
        '--llvm-bin',str(a.llvm_bin),'--lowerer',str(a.lowerer)],capture_output=True,text=True)
    assert r.returncode != 0 and 'admission rejected' in r.stderr,r.stdout+r.stderr
    j=json.loads((out/'admission.json').read_text())
    assert not j['admitted']
    native=j['native_partial_links']
    for target in ('hg_dwc_status','hg_ovy0_wifi_subset'):
        row=native[target]
        if not row['returncode']:
            # Original native support providers may now close this partial
            # dylib. That never admits the complete owning image or ABI bridge.
            assert not row['unresolved'] and not row['functions'] and not row['data']
        else:
            assert row['unresolved']
            assert all(f['emitted_guest_provider'] is not None for f in row['functions'].values())
    if 'shared_state_proof' in j:
        proof=j['shared_state_proof']
        assert not proof['execution_admitted']
        if proof['fresh']:
            assert proof['byte_compatible']+proof['blocked']==206 and proof['blocked']>0
    for name,count,data in (('OVY_0',42,4),('OVY_38',8,2)):
        row=j['images'][name]
        assert row['exact_members'] and row['summary']['complete_compilation']
        assert row['summary']['compiled']==count and row['summary']['data_represented']==data
        assert row['bindings'] and Path(row['path']).is_file()
    consumer=j['consumers']['OVY_44']
    assert not consumer['admitted'] and consumer['summary']['complete_compilation']
    assert consumer['summary']['compiled']==4 and Path(consumer['archive']).is_file()
    coverage=json.loads(Path(consumer['coverage']).read_text())
    failures='\n'.join(m.get('blocking_diagnostic','') for m in coverage['members'])
    assert not failures.strip()
    identities=json.loads((out/'OVY_45/inline-identities.json').read_text())
    assert sum('_Z10NewHandlermm' in args for args in identities['members'].values())==2
    assert not identities['unsafe_external_uses']
    assert any('_ZN3StrC2Ev' in args for args in identities['members'].values())
    assert not json.loads((out/'OVY_45/ownership-conflicts.json').read_text())
    assert not j['consumers']['OVY_45']['admitted']
    abi=json.loads((out/'OVY_45/cross-unit-abi.json').read_text())
    assert not any(x['target'] in ('LobbySort_LowerBound','LobbySort_UpperBound','LobbySort_Rotate','LobbyMem_InstallOutOfMemoryHandler') for x in abi['unsupported'])
    assert any(x['target']=='LobbyString_FindFirstOf' for x in abi['unsupported'])
    cpp=json.loads((out/'OVY_45/frontend-coverage.json').read_text())
    assert cpp['cpp_total']==53
    cpp_members=[m for m in cpp['members'] if m['kind']=='C++']
    assert len(cpp_members)==53 and any(m.get('frontend') for m in cpp_members)
    assert all('-std=gnu++98' in m['command'] for m in cpp_members)
    assert all('-fno-exceptions' in m['command'] for m in cpp_members)
    assert not (out/'OVY_45/libheartgold_overlay_45.a').exists()
    consumer=j['consumers']['OVY_75']
    assert consumer['summary']['complete_compilation'] and consumer['summary']['compiled']==3
    assert Path(consumer['archive']).is_file() and consumer['link_returncode']!=0
    assert '_guest32_GtsServer_Init' in consumer['unresolved']
    assert not consumer['admitted']
    for owner,count,data in ((39,3,2),(73,5,2),(90,1,1),(91,1,1),(92,1,1),(93,3,3)):
        row=j['consumers']['OVY_'+str(owner)]
        assert row['summary']['complete_compilation'] and row['summary']['compiled']==count
        assert row['summary']['data_represented']==data and Path(row['archive']).is_file()
        assert not row['admitted']
    state=next(x for x in j['barriers'] if x['cause']=='shared-main-state-ownership')
    assert any(x['name']=='gSystem' for x in state['potential_conflicts'])
    print('PASS real network candidate links, exact members, caller ABI/C++/state rejection')


if __name__=='__main__':main()
