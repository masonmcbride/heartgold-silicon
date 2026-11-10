#!/usr/bin/env python3
"""Measure original DWC declarations, without rewriting sources or building the game."""
import hashlib,json,re,shlex,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'compiler/guest32'))
from frontend import flags
build=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'build'
work=build/'semantic-law-corpus';work.mkdir(exist_ok=True)
game=ROOT/'upstream/pokeheartgold'
header=game/'lib/include/dwc/auth_internal.h'
source=work/'dwc-layout-probe.c'
structs={'NetCheckState':['work','redirected','ip','mode','unk_10','http','httpParams','authParams'],'NasHttpParams':['url','method','bufferSize','alloc','free','testServer','timeout'],'AuthParams':['ingamesn','gsbrcd','alloc','free']}
expressions=['sizeof(void*)','_Alignof(void*)'];names=['pointer.size','pointer.align']
for struct,fields in structs.items():
 expressions += [f'sizeof({struct})',f'_Alignof({struct})'];names += [struct+'.size',struct+'.align']
 for field in fields:expressions.append(f'__builtin_offsetof({struct},{field})');names.append(struct+'.'+field)
source.write_text('#include "global.h"\n#include "dwc/net_common_internal.h"\nconst unsigned long long layout_values[]={'+','.join(expressions)+'};\n')
entry=next(e for e in json.loads((build/'compile_commands.json').read_text()) if e['file'].endswith('/soc_inet.c'))
native=entry.get('arguments') or shlex.split(entry['command']);i=native.index('-o');del native[i:i+2]
native=[a for a in native if a not in ('-c',entry['file'])]
old_commands=json.loads((build/'dwc-rule-tests/commands.json').read_text())
clang=old_commands[0]['command'][0]
results={};commands=[]
for label,opts in [('arm32',[clang,*flags(game,build)]),('arm64',native)]:
 ll=work/(label+'.ll')
 cmd=[*opts,'-S','-emit-llvm','-Xclang','-fdump-record-layouts-complete',str(source),'-o',str(ll)]
 run=subprocess.run(cmd,capture_output=True,text=True,cwd=build)
 (work/(label+'.stdout')).write_text(run.stdout);(work/(label+'.stderr')).write_text(run.stderr)
 commands.append({'target':label,'command':cmd,'returncode':run.returncode})
 if run.returncode:raise RuntimeError(run.stderr)
 # Assert that the exact original declaration text was selected by this target's preprocessing.
 pp=subprocess.run([*opts,'-E',str(source)],capture_output=True,text=True,cwd=build,check=True).stdout
 for tag in structs:
  definition=re.search(r'typedef struct '+tag+r' \{.*?\} '+tag+r';',header.read_text(),re.S).group()
  # Remove comments and whitespace only; no source edits or type approximations.
  canonical=lambda s:re.sub(r'\s+','',re.sub(r'//[^\n]*|/\*.*?\*/','',s,flags=re.S))
  check=re.search(r'typedef struct '+tag+r' \{.*?\} '+tag+r';',pp,re.S)
  assert check and canonical(definition)==canonical(check.group()),'non-original definition selected: '+tag
 line=next(s for s in ll.read_text().splitlines() if s.startswith('@layout_values ='))
 values=[int(n) for n in re.findall(r'i64 (\d+)',line)]
 assert len(values)==len(names)
 selected=[]
 for block in run.stdout.split('*** Dumping AST Record Layout'):
  if any(re.search(r'^\s*0 \| struct '+tag+r'\s*$',block,re.M) for tag in structs):selected.append(block.strip())
 assert len(selected)==3
 results[label]={'values':dict(zip(names,values)),'complete_record_layouts':selected,'compiler_version':subprocess.check_output([opts[0],'--version'],text=True).splitlines()[0],'llvm_datalayout':next(s for s in ll.read_text().splitlines() if s.startswith('target datalayout')),'original_definitions_preprocessor_verified':True}
(work/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
# Trace named-tree snapshots without treating them as commits or assigning dates.
refs=subprocess.check_output(['git','-C',str(ROOT),'for-each-ref','--format=%(refname) %(objectname)'],text=True).splitlines()
provenance=[]
for path in ('docs/NATIVE_LINK_CLOSURE.md','tests/test_dwc_ac_contract.py','tests/test_guest32_dwc_rules.py'):
 snapshots=[]
 for row in refs:
  name,obj=row.split()
  if subprocess.check_output(['git','-C',str(ROOT),'cat-file','-t',obj],text=True).strip()!='tree':continue
  found=subprocess.run(['git','-C',str(ROOT),'rev-parse',obj+':'+path],capture_output=True,text=True)
  if found.returncode==0:snapshots.append({'ref':name,'tree':obj,'blob':found.stdout.strip()})
 provenance.append({'path':path,'provenance_category':'diagnostic-evidence' if path.startswith('docs/') else 'regression-evidence','worktree_sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),'commit_provenance':'No introducing commit established; files are currently untracked. Named tree snapshots preserve the claims but are not commits.','tree_snapshots':snapshots})
abi_path=build/'provider-closure170/OVY_0/lib/NitroDWC/src/auth_netcheck.o/abi.json'
placements=json.loads(abi_path.read_text())['globals']
coordinates={name:placements[name]['offset'] for name in ('gDwcHttpTestServer','gDwcNetCheckState','ov00_0221A6BC','ov00_0221A6D0','ov00_0221A6EC')}
bases={base:[coordinates[label]-coordinates[base] for label in ('ov00_0221A6D0','ov00_0221A6EC')] for base in ('gDwcHttpTestServer','gDwcNetCheckState')}
assert bases=={'gDwcHttpTestServer':[28,56],'gDwcNetCheckState':[24,52]}
report={'schema':1,'id':'DWC-LAYOUT-CHECK-001','status':'measured','claim_provenance':provenance,'original_placement_evidence':{'path':abi_path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(abi_path.read_bytes()).hexdigest(),'coordinates':coordinates,'offsets_relative_to_each_base':bases},'older_diagnostic_analysis':'The older test measures native offsets with offsetof and compares them against hard-coded 28/56. It does not compute those constants from assembly or an ARM32 record layout. Its emitted native JSON reports 32/72. The older narrative calls 28/56 original aliases of NetCheckState; no derivation or alternate base is identified. Named snapshots retain the same claims. 28/56 numerically match the preceding gDwcHttpTestServer base, but no inspected diagnostic establishes that as their derivation; cause remains unresolved.','header':{'repository':'upstream/pokeheartgold','path':header.relative_to(game).as_posix(),'revision':subprocess.check_output(['git','-C',str(game),'rev-parse','HEAD'],text=True).strip(),'sha256':hashlib.sha256(header.read_bytes()).hexdigest()},'layouts':results,'old_claim_offsets':[28,56],'conclusion':'ARM64 offsets are 32/72, not 28/56. ARM32 offsets are 24/52. Native expansion does not explain the older pair for these exact declarations. Origin of that pair remains unresolved.','artifacts':'build/semantic-law-corpus/{dwc-layout-probe.c,arm32.ll,arm64.ll,arm32.stdout,arm64.stdout,arm32.stderr,arm64.stderr,commands.json}'}
(OUT/'dwc-layout-evidence.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({target:r['values'] for target,r in results.items()},indent=2))
