#!/usr/bin/env python3
"""Reproduce the partial research corpus. Reads Git and files; writes only beside this script."""
import hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
if (OUT/'history-manifest.json').exists() and json.loads((OUT/'history-manifest.json').read_text()).get('review_batches'):
 raise SystemExit('Refusing to overwrite incremental review batches. Resume pending-review.json with review_updates.py; reconstruct.py is the archived initial inventory generator.')
REPOS=['.','upstream/libntr']
def git(repo,*args):
 return subprocess.check_output(['git','-C',str(ROOT/repo),*args],stderr=subprocess.PIPE).decode('utf-8','surrogateescape')
def digest(data): return hashlib.sha256(data).hexdigest()
def write(name,data): (OUT/name).write_text(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=True)+'\n')
def lines(name,rows): (OUT/name).write_text(''.join(json.dumps(r,sort_keys=True,ensure_ascii=True)+'\n' for r in sorted(rows,key=lambda r:r['id'])))
def ref(path,repo='.',revision=None,locator=None):
 revision=revision or 'worktree'
 category=('original-source-contract' if repo=='upstream/pokeheartgold' else 'diagnostic-evidence' if path.startswith('build/') else 'regression-evidence' if path.startswith('tests/') else 'hardware-or-sdk-reference' if repo=='upstream/libntr' and revision=='worktree' else 'porting-history')
 r={'repository':repo,'path':path,'revision':revision,'provenance_category':category}
 if revision=='worktree': r['sha256']=digest((ROOT/repo/path).read_bytes())
 if locator:r['locator']=locator
 return r
manifest={'schema':1,'completeness':'incomplete','scope':'Project commits and libntr fork delta only, per user scope correction. pokeheartgold is source authority, with historical commits included only on demonstrated relevance. Inventory is not semantic review.','repositories':[],'excluded_paths':{'docs/semantic-law-corpus':'This assignment output, excluded to avoid recursive inventory.'},'reviewed_evidence':[]}
changes=[]
for repo in REPOS:
 refs=[]; tips=[]; snapshots=[]
 for row in git(repo,'for-each-ref','--format=%(refname) %(objectname)').splitlines():
  name,obj=row.split(); typ=git(repo,'cat-file','-t',obj).strip(); refs.append({'name':name,'object':obj,'type':typ})
  if typ=='commit':tips.append(obj)
  elif typ=='tree':
   entries=[]
   for entry in git(repo,'ls-tree','-r',obj).splitlines():
    meta,path=entry.split('\t',1); entries.append({'path':path,'object':meta.split()[-1],'disposition':'needs_review'})
   snapshots.append({'tree':obj,'disposition':'needs_review','files':entries})
  elif typ=='tag':
   try:tips.append(git(repo,'rev-parse',obj+'^{commit}').strip())
   except subprocess.CalledProcessError:pass
 try:tips+=git(repo,'reflog','--all','--format=%H').splitlines()
 except subprocess.CalledProcessError:pass
 exclusions=[]
 if repo=='upstream/libntr':
  exclusions=['^'+git(repo,'rev-parse','refs/heads/main').strip()]
  exclusions += ['^'+r['object'] for r in refs if r['name'].startswith('refs/remotes/origin/features/')]
 commits=git(repo,'rev-list','--topo-order',*sorted(set(tips)),*exclusions).splitlines() if tips else []
 rr={'path':repo,'head':git(repo,'rev-parse','HEAD').strip(),'shallow':git(repo,'rev-parse','--is-shallow-repository').strip()=='true','refs':refs,'tree_snapshots':snapshots,'commits':[],'excluded_ancestry':exclusions}
 # Single raw history traversal covers every parent edge, including merges.
 raw=git(repo,'log','--format=COMMIT %H %P','--raw','--no-abbrev','--no-renames','--root','-m',*sorted(set(tips)),*exclusions)
 current=None
 for row in raw.splitlines():
  if row.startswith('COMMIT '):current=row.split()[1]
  elif row.startswith(':'):
   meta,path=row.split('\t',1); fields=meta.split(); old,new,status=fields[2:5]
   key=f'{repo}:{current}:{path}:{old}:{new}'
   changes.append({'id':'CH-'+digest(key.encode())[:24],'repository':repo,'commit':current,'path':path,'old_blob':old,'new_blob':new,'git_status':status,'disposition':'needs_finer_grained_review','classification':None,'correction_ids':[],'reason':'Inventoried; content/hunks have not been exhaustively analyzed.'})
 for commit in sorted(set(commits)):
  rr['commits'].append({'commit':commit,'subject':git(repo,'show','-s','--format=%s',commit).strip(),'disposition':'needs_finer_grained_review'})
 rr['worktree']=[]
 workpaths=set(git(repo,'ls-files','-c','-o','--exclude-standard','-z').split('\0'))-{''}
 if repo=='upstream/libntr':
  workpaths &= {c['path'] for c in changes if c['repository']==repo} | set(git(repo,'ls-files','-o','--exclude-standard','-z').split('\0'))
 for path in sorted(workpaths):
  if path.startswith('docs/semantic-law-corpus/'):continue
  p=ROOT/repo/path
  if p.is_file():rr['worktree'].append({'path':path,'sha256':digest(p.read_bytes()),'disposition':'needs_review'})
 rr['status_porcelain']=[x for x in git(repo,'status','--porcelain=v1','--untracked-files=all').splitlines() if 'docs/semantic-law-corpus/' not in x]
 manifest['repositories'].append(rr)
workchanges=[]
for repo in REPOS:
 changed=set(git(repo,'diff','HEAD','--name-only','-z').split('\0'))-{''}
 changed |= set(git(repo,'ls-files','--others','--exclude-standard','-z').split('\0'))-{''}
 for path in sorted(changed):
  if path.startswith('docs/semantic-law-corpus/'):continue
  p=ROOT/repo/path
  diff=git(repo,'diff','HEAD','--no-ext-diff','--no-renames','--',path)
  workchanges.append({'id':'WT-'+digest((repo+':'+path).encode())[:24],'repository':repo,'path':path,'base_revision':git(repo,'rev-parse','HEAD').strip(),'sha256':digest(p.read_bytes()) if p.is_file() else None,'diff_sha256':digest(diff.encode('utf-8','surrogateescape')),'hunk_headers':re.findall(r'^@@.*?@@.*$',diff,re.M),'disposition':'needs_finer_grained_review','classification':None,'reason':'Current modified or untracked file; preserve existing contents.'})
manifest['worktree_changes_file']='worktree-changes.jsonl'
# Deduplicate repeated parent-edge records; objects encode the precise edge contents.
changes=list({r['id']:r for r in changes}.values())
# Fully inspected nonsemantic change (all hunks).
for c in changes:
 if c['repository']=='.' and c['commit'].startswith('49dfeadc'):
  c.update(disposition='fully_reviewed',classification='refactor_or_unrelated',reason='Only .gitignore patterns changed: generated outputs/editor recovery files; no engine/compiler behavior.',correction_ids=[])
for rr in manifest['repositories']:
 for c in rr['commits']:
  if c['commit'].startswith('49dfeadc'):c['disposition']='fully_reviewed_nonsemantic'
# Root hunk index is an exact deterministic resume queue; entire additions may still require splitting.
hunks=[]
for c in changes:
 if c['repository'] not in REPOS:continue
 old,new=c['old_blob'],c['new_blob']
 a='' if set(old)=={'0'} else git(c['repository'],'cat-file','blob',old)
 b='' if set(new)=={'0'} else git(c['repository'],'cat-file','blob',new)
 import difflib
 diff=list(difflib.unified_diff(a.splitlines(True),b.splitlines(True),n=3))
 headers=[i for i,s in enumerate(diff) if s.startswith('@@')]
 for j,i in enumerate(headers):
  text=''.join(diff[i:headers[j+1] if j+1<len(headers) else len(diff)])
  hunks.append({'id':c['id']+'-H'+str(j+1),'change_id':c['id'],'header':diff[i].strip(),'sha256':digest(text.encode('utf-8','surrogateescape')),'disposition':c['disposition'],'correction_ids':[]})
# Inventory artifacts without reading binaries or asserting they passed tests.
artifacts=[]; errors=[]
for base,dirs,files in os.walk(ROOT,onerror=lambda e:errors.append(str(e))):
 dirs[:]=sorted(d for d in dirs if d!='.git' and not (Path(base)/d==OUT))
 for name in sorted(files):
  p=Path(base)/name; rel=p.relative_to(ROOT).as_posix()
  if rel.startswith('upstream/'):continue
  if rel.startswith(('build/','build-','cmake-build-')) or p.suffix in ('.log','.out','.err'):
   try:artifacts.append({'path':rel,'bytes':p.stat().st_size,'disposition':'available_not_reviewed','revision':'worktree-artifact'})
   except OSError as e:errors.append(str(e))
manifest['artifacts']=artifacts;manifest['inventory_errors']=errors
manifest['upstream_source_authority']={'repository':'upstream/pokeheartgold','revision':git('upstream/pokeheartgold','rev-parse','HEAD').strip(),'historical_commits_in_scope':[],'reason':'User excludes unrelated pokeheartgold history; source references retained where semantically relevant.'}
rules=json.loads((ROOT/'compiler/guest32/rules.json').read_text())['rules']
corrections=[]; laws=[]; links=[]; coverage=[]; unresolved=[]
def add(cid,lid,title,category,failure,construct,assumption,obligation,post,pre,evidence,impl,tests,commits=(),status='source_supported_untested',limits=()):
 c={'id':cid,'title':title,'classification':category,'original_failure':failure,'failure_recovery':'source/diff supported; original crash date not established','source_construct':construct,'architectural_assumption':assumption,'incorrect_host_behavior':failure,'implemented_correction':obligation,'invariant':post,'preconditions':pre,'postconditions':[post],'dependencies':[],'known_counterexamples':list(limits),'evidence':evidence,'commit_provenance':[{'repository':'.','commit':x} for x in commits],'current_implementation':impl,'implementation_status':status,'tests':tests,'test_results':'Not executed for this corpus; source presence does not establish a passing result.','law_ids':[lid]}
 corrections.append(c)
 l={'id':lid,'title':title,'semantic_category':category,'applicability':construct,'architectural_assumptions':[assumption],'invariant':post,'D':construct,'P':pre,'T':obligation,'Q':[post],'E':evidence,'V':{'existing_checks':tests,'execution_status':'not_run_in_this_audit','missing_obligations':['Review complete introducing and subsequent diffs; execute and inspect focused regressions; prove scope beyond fixtures.']},'C':{'dependencies':[],'incompatibilities':[],'ordering':[],'interactions':[]},'historical_correction_ids':[cid],'implementation_locations':impl,'evidence_status':'source_supported','verification_status':'not_verified_in_this_audit','confidence':'candidate','limitations':list(limits),'outstanding_verification':['No general semantic equivalence proof.']}
 laws.append(l);links.append({'id':cid+'--'+lid,'correction_id':cid,'law_id':lid})
# These are distinct correction candidates, not eleven newly proven laws.
for r in rules:
 op=r['operation']; lid='LAW-'+op.upper();cid='COR-G32-'+op.upper()
 add(cid,lid,r['id']+' representation contract','compiler_representation_change', 'Historical counterexample not independently reconstructed for this operation; existing RULES.md summarizes failures.',r['operation']+' operations in original ARM32 LLVM IR','Little-endian four-byte pointers and 32-bit indices',r['invariants'][0],r['invariants'][0],['Original frontend DataLayout established',*r['requires']], [ref('compiler/guest32/rules.json'),ref('compiler/guest32/rules.h'),ref('compiler/guest32/lower.cpp'),ref('compiler/guest32/RULES.md')],[ref('compiler/guest32/lower.cpp'),ref('compiler/guest32/abi.h'),ref('hardware_drivers/guest32.c')],[ref(t) for t in r['tests']],r['evidence'],status='implemented_family_scope_not_exhaustively_reviewed',limits=['Catalog evidence hashes are asserted provenance, not independently reviewed introducing hunks.','Original CodeWarrior ABI equivalence is not established by LLVM verification.'])
 coverage.append({'id':r['id'],'law_ids':[lid],'correction_ids':[cid],'catalog_status':r['status'],'audit_status':'partially_mapped','implementation':[ref('compiler/guest32/rules.h'),ref('compiler/guest32/lower.cpp')],'enforcement':'Closed operation gate checks facts and records applications; existing lowerer supplies transformations. Prose changes do not implement transformations.','covered_operations':op,'outside_coverage':['Provider ownership and physical image placement','General native ABI admission','Platform hardware semantics'],'test_evidence':[ref(t) for t in r['tests']],'gaps':['Individual historical corrections still require hunk review.','No test results independently executed or authenticated by this audit.']})
# Independently read historical fixes.
ball='8f31e966310ca78b109faf4a25b708353a9f95fc'
add('COR-BALL-MENU','LAW-CALLBACK','Ball capsule menu preserves callback identity','correctness_fix','Casting a native callback to int loses high address bits.','Menu integer selection transports a callback identity','Original code pointers fit a 32-bit menu word','Store bounded item index+1 and dispatch original table callback after range check.','Selection invokes exactly the original selected callback without truncating a native pointer.',['Original table and item range unchanged'],[ref('cmake/native_sources.py',revision=ball,locator='_adapt ball_capsule_editor')],[ref('cmake/native_sources.py')],[],[ball],status='historical_fix_current_branch_requires_review')
# Merge independently recovered callback correction into the existing law, preserving its narrower invariant.
base=next(l for l in laws if l['id']=='LAW-CALLBACK'); extra=laws.pop();base['historical_correction_ids'].append(extra['historical_correction_ids'][0]);base['E']+=extra['E'];base['limitations'].append('Ball menu index is a bounded implementation distinct from general guest code handles.')
# DWC observed failures: unresolved corrections, never described as admitted fixes.
game='upstream/pokeheartgold'; gp=git(game,'rev-parse','HEAD').strip()
dwc=[ref('lib/NitroDWC/src/ap_connect_control.c',game,gp,'DWC_AC_Create; allocation near 591 and p8 stores'),ref('lib/NitroDWC/src/ap_connect.c',game,gp,'DWCi_AC_StartNetCheck near 703'),ref('docs/NATIVE_LINK_CLOSURE.md'),ref('tests/test_dwc_ac_contract.py')]
def observed(cid,lid,title,failure,obligation,post,construct,evidence=dwc):
 add(cid,lid,title,'incomplete_correctness_attempt',failure,construct,'Original fixed ARM32 storage and register words; LP64 changes pointer-bearing objects',obligation,post,['Concrete original producer and consumer contracts recovered'],evidence,[],[ref('tests/test_dwc_ac_contract.py')],status='recognized_unresolved_production_boundary',limits=['Negative test specification is not production subsystem support.'])
 # Deduplicate only exactly shared invariant law targets; retain evidence and correction identity.
 same=[l for l in laws[:-1] if l['id']==lid]
 if same:
  new=laws.pop();same[0]['historical_correction_ids']+=new['historical_correction_ids'];same[0]['E']+=new['E']
observed('COR-DWC-CALLBACK-WIDTH','LAW-CALLBACK','AC callback record loses native code addresses','Three u32 stores truncate callbacks above 4 GiB; original 12-byte consumer becomes 24 bytes under native layout.','Preserve original callback identities across stores, copies and indirect dispatch; require a typed lifetime-safe native boundary.','Callback identity, signature and lifetime survive transport.','AC producer p8[0..2] and netcheck consumer')
observed('COR-DWC-CALLBACK-TYPE','LAW-CALLBACK-ARGUMENTS','Allocator tag arguments require semantic compatibility','AC callbacks accept int tags; NAS callbacks accept char* tags. Widening the record still rejects incompatible function pointers.','Recover and preserve observable argument meaning for both providers and all callers.','Dispatch preserves every observable callback argument and return convention.','Integer allocator kinds versus string allocator tags')
for name,guest,native in [('AUTH',5108,5392),('NETCHECK',4596,4880),('HTTP',7188,7856),('SERVICE',7200,7880)]:
 observed('COR-DWC-EXTENT-'+name,'LAW-ALLOCATION-COHERENCE',name+' storage extent coherence',f'Original allocation/clear is {guest} bytes; reported native type requires {native} bytes.','Coordinate allocation, clear, copy, field access and interior aliases in one representation.','Every accessed field lies within a live allocation and initialization covers required observable bytes.',name+' fixed-size work allocation')
 corrections[-1]['measurements']={'original_bytes':guest,'reported_native_bytes':native,'measurement_status':'documented; test source inspected; executable output not revalidated'}
asm=ref('lib/NitroDWC/asm/dwc_lib_rodata.s',game,gp,'gDwcNetCheckState through ov00_0221A6EC')
observed('COR-DWC-INTERIOR','LAW-INTERIOR-OWNERSHIP','Interior labels retain one authoritative base','Native member offsets differ from original assembly interior label addresses; resizing a root does not repair aliases.','Resolve aliases into the same owning allocation using original source coordinates or explicitly proven native member relations.','All aliases observe the same intended bytes in one owned object.','Shared assembly interior aliases',[asm,ref('tests/test_guest32_dwc_rules.py'),ref('docs/NATIVE_LINK_CLOSURE.md')])
corrections[-1]['measurements']={'source_derived_offsets':[24,52],'derivation':'0x4 + 0x14 = 0x18; then +0x1c = 0x34','earlier_document_offsets':[28,56],'reported_native_offsets':[32,72]}
observed('COR-DWC-BOUNDARY','LAW-BOUNDARY','Native/guest object admission requires typed representation','Compiling a complete guest32 DWC member does not make its native provider call ABI compatible.','Admit a provider only with proven signature, extent, ownership and coordinate conversion contracts.','Every cross-representation call preserves the actual ABI and observable storage.','Guest32/native DWC provider calls',[ref('compiler/guest32/abi.h'),ref('compiler/guest32/RULES.md'),ref('tests/test_guest32_dwc_rules.py')])
# Additional source-grounded laws outside eleven broad families. Historical extraction remains pending.
for cid,lid,title,path,domain,inv in [
 ('COR-PROVIDER-OWNERSHIP','LAW-PROVIDER-OWNERSHIP','Definition ownership precedes provider selection','cmake/native_provider_registry.py','Duplicate definitions and original main/overlay ownership','Each admitted symbol has an authoritative owner and ABI-compatible provider; matching spelling alone is insufficient.'),
 ('COR-OVERLAY-LIFETIME','LAW-OVERLAY-LIFETIME','Physical mapping and logical residency are distinct','hardware_drivers/os/overlay_native.c','Overlay load/start/unload and callback execution','An executable callback requires its owning logical image to be resident throughout invocation.'),
 ('COR-FRAME-RECLAMATION','LAW-FRAME-LIFETIME','Guest frame allocation records expire together','hardware_drivers/guest32.c','Stack frame exit and arena allocation ownership','Frame exit invalidates frame-owned extents and releases their bookkeeping without invalidating unrelated allocations.'),
 ('COR-DECLARATION-LIBC','LAW-CALL-DECLARATION','Native library declarations use the actual host ABI','cmake/native_sources.py','C++ lobby libc calls and va_list','A call declaration agrees with its linked provider signature, linkage and argument representation.'),
 ('COR-RULE-PRECONDITIONS','LAW-POSITIVE-ADMISSION','Unknown representation facts cannot authorize lowering','compiler/guest32/rules.h','Conditional compiler rule admission','Each applied operation has its required facts established in the correct scope; catalog prose supplies no new facts.')]:
 add(cid,lid,title,'runtime_semantic_adaptation' if 'hardware_drivers' in path else 'linker_or_provider_correction','Original failure not fully dated; current source encodes this obligation.',domain,'Original code/data ownership remains authoritative',inv,inv,['Original ownership and ABI evidence available'],[ref(path)],[ref(path)],[],status='source_inspected_historical_hunks_pending')
# Two complete single-purpose fork patches, directly inspected.
for short,cid,title,path,failure,obligation in [
 ('25788d0','COR-PXI-NATIVE-PAYLOAD','Simulator FIFO preserves host payload width','libraries/pxi/src/pxi_fifo.c','SDK_PORT executed hardware packed-word range checks and narrowing bitfield construction on native-width transport payloads.','In SDK_PORT transport uPtr payload unchanged; retain hardware packing/range contract for hardware builds.'),
 ('6a5c6a5','COR-PCM-NATIVE-PAYLOAD','PCM dispatch preserves host sample pointers','libraries/snd/src/snd_command.c','Unpacking 27 hardware address bits from a native PCM pointer loses high address bits.','For SDK_PORT and SDK_64BIT forward the complete uintptr_t pointer; retain hardware bit extraction otherwise.')]:
 commit=git('upstream/libntr','rev-parse',short).strip()
 add(cid,'LAW-HOST-PAYLOAD',title,'runtime_semantic_adaptation',failure,'Host simulator command payloads containing native pointers','Hardware packed address fields and host transport payloads have different representations',obligation,'Host transport preserves complete native pointer identity while hardware serialization retains its fixed bit contract.',['Host simulator transport explicitly selected'],[ref(path,'upstream/libntr',commit)],[ref(path,'upstream/libntr')],[],status='implemented_patch_reviewed_tests_not_authenticated')
 corrections[-1]['commit_provenance']=[{'repository':'upstream/libntr','commit':commit,'provenance_category':'porting-history'}]
 if len([l for l in laws if l['id']=='LAW-HOST-PAYLOAD'])>1:
  new=laws.pop();base=next(l for l in laws if l['id']==new['id']);base['historical_correction_ids']+=new['historical_correction_ids'];base['E']+=new['E']
 for change in changes:
  if change['repository']=='upstream/libntr' and change['commit']==commit:
   change.update(disposition='fully_reviewed',classification='runtime_semantic_adaptation',correction_ids=[cid],reason='Entire patch read; conditional host payload preservation. Test execution not established.')
 for rr in manifest['repositories']:
  for cr in rr['commits']:
   if cr['commit']==commit:cr['disposition']='fully_reviewed'
# Fine-grained corrections recovered from complete fork diffs 4cfdd66 and f4f9905.
def forkfix(short,cid,lid,title,paths,failure,domain,obligation,invariant,tests=()):
 commit=git('upstream/libntr','rev-parse',short).strip()
 add(cid,lid,title,'correctness_fix',failure,domain,'DS word widths and original SDK service behavior differ from LP64 host representation',obligation,invariant,['SDK_PORT selected where adaptation is conditional; inspect target-specific branches'],[ref(p,'upstream/libntr',commit) for p in paths],[ref(p,'upstream/libntr') for p in paths],[ref(p) for p in tests],status='historical_patch_inspected_verification_pending')
 corrections[-1]['commit_provenance']=[{'repository':'upstream/libntr','commit':commit,'provenance_category':'porting-history'}]
 matches=[l for l in laws[:-1] if l['id']==lid]
 if matches:
  new=laws.pop();matches[0]['historical_correction_ids']+=new['historical_correction_ids'];matches[0]['E']+=new['E']
 return commit
forkfix('4cfdd66','COR-SQRT-TRIAL-WIDTH','LAW-INTERMEDIATE-WIDTH','Square-root trial product requires an extra bit',['include/nitro/cp/sqrt.h'],'u32 trial product and shifting before widening discard the high bit for large 64-bit operands.','Software integer square root trial subtraction','Compute ((u64)res << 1)+1 in u64.','Intermediate arithmetic retains every bit required by the original arithmetic contract.')
forkfix('4cfdd66','COR-SQRT-CONTROL-MODE','LAW-MMIO-WRITE-EFFECT','Square-root parameter writes launch using current mode',['include/nitro/cp/sqrt.h'],'The helper selected operand mode from write width rather than current SQRTCNT and ignored retained high half.','32/64-bit parameter register writes','Read the complete parameter register after the write and launch using current SQRTCNT mode.','A register write preserves untouched bits and triggers computation from the actual control and parameter state.')
forkfix('4cfdd66','COR-SQRT-ENTRY-EFFECT','LAW-MMIO-WRITE-EFFECT','Immediate square-root setters trigger software execution',['include/nitro/cp/sqrt.h'],'Non-NS immediate helpers wrote host register storage without invoking software calculation.','Immediate square-root SDK setter entry points','Route SDK_PORT immediate helpers through the effectful NS implementation.','A register write preserves untouched bits and triggers computation from the actual control and parameter state.')
forkfix('4cfdd66','COR-DGT-WORD-WIDTH','LAW-FIXED-SCALAR-FORMAT','Hash state words retain 32 bits',['include/nitro/dgt/dgt.h'],'unsigned long grows to 64 bits on LP64, widening MD5 state and block words.','Cryptographic context state[4] and buffer32[16]','Use u32 for original state and block words.','Fixed original word arrays retain their specified widths, offsets and arithmetic interpretation.')
forkfix('4cfdd66','COR-BLEND-CONTIGUITY','LAW-REGISTER-CONTIGUITY','Blend register groups occupy contiguous aligned storage',['include/nitro/hw/X86/ioreg_G2.h','include/nitro/hw/X86/ioreg_G2S.h','libraries/sim/src/sim_vars.c'],'Separate globals do not guarantee adjacency or alignment needed by combined register accesses.','Main and sub display blend register groups','Allocate aligned three-element 16-bit arrays and alias individual register names to elements.','Adjacent hardware register views alias the same contiguous correctly aligned bytes.')
forkfix('4cfdd66','COR-OS-HEAP-ADDRESS','LAW-HOST-ADDRESS-ARITHMETIC','Heap range arithmetic preserves native addresses',['libraries/os/src/os_alloc.c'],'u32 range predicates truncate host addresses; integer masks may clear high address bits.','OS heap alignment, membership and overlap predicates','Use uintptr_t address type and masks in SDK_PORT; preserve u32 DS path.','Address predicates and alignment preserve full native address identity within the supplied allocation.')
forkfix('4cfdd66','COR-OS-HEAP-METADATA-ALIGN','LAW-NATIVE-ALIGNMENT','Heap metadata satisfies native alignment',['libraries/os/src/os_alloc.c'],'Four-byte aligned original arena may misalign LP64 heap metadata.','OS_InitAlloc metadata placement','Round arenaStart to _Alignof(OSHeapInfo) before reserving metadata within the supplied range.','Native object placement satisfies its alignment and remains inside the supplied extent.')
forkfix('4cfdd66','COR-METADATA-PROVIDER','LAW-PROVIDER-OWNERSHIP','Metadata marker belongs to ordinary SDK initialization',['libraries/init/src/crt0.c','libraries/os/src/os_init.c','include/nitro/misc.h'],'Linking CRT for a metadata reference also introduces empty startup/decompression providers.','OSi_ReferSymbol provider selection','Move const-qualified marker implementation from crt0 to os_init.','Each admitted symbol has an authoritative owner and ABI-compatible provider; matching spelling alone is insufficient.')
forkfix('4cfdd66','COR-DGT-EMPTY-PROVIDERS','LAW-PROVIDER-SEMANTICS','Hash names cannot be satisfied by empty providers',['libraries/math/src/dgt.c'],'SDK_PORT hash entry definitions return without performing hashing.','DGT hash provider definitions','Remove empty definitions so real implementation ownership remains a link obligation.','A symbol provider must implement its required behavior; resolution alone is insufficient.')
forkfix('4cfdd66','COR-GX-STATE-OWNER','LAW-SHARED-STATE-OWNER','Graphics bank selections have one shared owner',['libraries/sim/src/sim_main.cpp','libraries/sim/src/sim_vars.c'],'Shared bank state depended on linking the simulator rendering entry translation unit.','GXVRamTex and related shared variables','Move definitions to sim_vars; retain declarations for consumers.','All consumers of shared state observe one authoritative storage instance independent of optional entry-point ownership.')
forkfix('4cfdd66','COR-FORCE-EXPORT','LAW-SYMBOL-RETENTION','Original retention annotations survive host compilation',['include/nitro/types.h'],'SDK_PORT lacked a host equivalent for forced retention.','SDK_FORCE_EXPORT declarations','Map SDK_PORT force-export to __attribute__((used)).','Source-required definitions survive the compiler retention stage; final linker retention remains a separate obligation.')
forkfix('4cfdd66','COR-BOX-DECLARATION','LAW-CALL-DECLARATION','Box-test output declaration agrees across callers',['include/nitro/gx/g3x.h','libraries/gx/src/g3x.c'],'Signed output declaration disagreed with required unsigned register-result view.','G3X_GetBoxTestResult output','Coordinate u32 pointer declaration, definition and result cast.','A call declaration agrees with its linked provider signature, linkage and argument representation.')
forkfix('4cfdd66','COR-STRING-LENGTH-SIGN','LAW-CALL-DECLARATION','String-length return uses the original unsigned contract',['include/nitro/std/string.h','libraries/std/src/std_string.c'],'int declaration and loop counter differed from u32 length interface.','STD_GetStringLength','Use u32 return and counter in declaration and definition.','A call declaration agrees with its linked provider signature, linkage and argument representation.')
forkfix('f4f9905','COR-FS-NAMESPACE','LAW-RESOURCE-NAMESPACE','Resource lookup has deterministic precedence and failure',['libraries/fs/src/fs_file.c'],'FS_OpenFile depended on cwd and recursive extraction UI after failed opens.','SDK_PORT named resource open','Use HG_OpenResource with generated then extracted resource lookup; missing paths return failure.','Resource lookup resolves the selected logical path consistently and terminates with explicit failure when unavailable.')
forkfix('f4f9905','COR-FS-LENGTH','LAW-FILE-EXTENT','File extents are representable before publication',['libraries/fs/src/fs_file.c'],'Unchecked ftell/fseek converted negative or oversized host length to u32.','FSFile file bounds initialization','Check seek, length and UINT32_MAX bound; close on failure before publishing file status.','Published file bounds are valid nonnegative representable lengths with the cursor at the requested initial position.')
forkfix('f4f9905','COR-OVERLAY-LOAD','LAW-OVERLAY-LOAD','Native overlay loading reports actual host outcomes',['libraries/fs/src/fs_overlay.c','include/ntr_host.h'],'Original ROM transfer path interprets native images using guest addresses.','Synchronous and asynchronous original FS overlay requests','Use registered native image service for recognized images; initialize request/error state and retain fallback for others.','Overlay load completion and failure reflect the actual owning image transition rather than unconditional success.')
forkfix('f4f9905','COR-OVERLAY-INIT','LAW-IMAGE-INITIALIZATION','Native image initialization runs once in the selected image',['libraries/fs/src/fs_overlay.c'],'Original startup reads ARM addresses; duplicate start can repeat initializer effects.','FS_StartOverlay native image branch','Run preserved host initializer table via HG_StartOverlayImage; panic on reported failure.','Image initialization preserves initializer identity, ordering and exactly-once effects for the lifecycle contract.')
forkfix('f4f9905','COR-OVERLAY-DESTRUCTOR-OWNER','LAW-ADDRESS-OWNERSHIP','Overlay destructor ownership uses native image ranges',['libraries/fs/src/fs_overlay.c'],'u32 address comparisons misclassify native destructor/object ownership.','Original destructor-chain traversal','Keep chain traversal; change only membership predicate to HG_OverlayOwnsAddress for registered native images.','Destructor membership preserves the original ownership predicate using complete native image ranges.')
forkfix('f4f9905','COR-OVERLAY-UNLOAD-ORDER','LAW-OVERLAY-LIFETIME','Unload validates transition before destructor effects',['libraries/fs/src/fs_overlay.c'],'Unconditional unload success or late validation can run destructors for invalid transitions.','FS_UnloadOverlayImage native lifecycle','Check HG_OverlayCanUnload before FS_EndOverlay, then return actual unload result.','An executable callback requires its owning logical image to be resident throughout invocation.')
# Fully read fork files: retain build-only wrappers and API support changes too.
review_commits={git('upstream/libntr','rev-parse',s).strip() for s in ('4cfdd66','f4f9905')}
for change in changes:
 if change['repository']=='upstream/libntr' and change['commit'] in review_commits:
  matched=[c['id'] for c in corrections if any(e['repository']=='upstream/libntr' and e['revision']==change['commit'] and e['path']==change['path'] for e in c['evidence'])]
  change.update(disposition='fully_reviewed',classification='correctness_fix' if matched else 'build_system_or_tooling_correction',correction_ids=sorted(set(matched)),reason='Complete diff inspected. Unmatched files are forwarding include wrappers or missing GX enum declaration; no engine algorithm change inferred. Verification still pending.')
for rr in manifest['repositories']:
 for cr in rr['commits']:
  if cr['commit'] in review_commits:cr['disposition']='fully_reviewed'

# Existing diagnostics were inspected; their execution provenance is still incomplete.
for c in corrections:
 if c['id'].startswith('COR-DWC-'):
  c['evidence'] += [ref('build/dwc-ac-contract/'+p) for p in ('auth-layouts.json','result.json','native-type-rejection.log')]
  c['evidence'] += [ref('build/dwc-rule-tests/'+p) for p in ('results.json','commands.json','layouts.c','layouts.ll')]
  c['test_results']='Existing artifacts report native extents and rejection/truncation; read in this audit, not rerun. Commands/input hashes not fully authenticated.'
# Distinct precise relations; not executable rule graph.
composition={'schema':1,'relations':[{'from':'LAW-ALLOCATION-COHERENCE','to':'LAW-INTERIOR-OWNERSHIP','kind':'requires_joint_representation_decision','reason':'Resizing root storage alone does not relocate interior aliases.'},{'from':'LAW-CALLBACK','to':'LAW-CALLBACK-ARGUMENTS','kind':'requires','reason':'Identity preservation does not establish argument semantics.'},{'from':'LAW-CALLBACK','to':'LAW-OVERLAY-LIFETIME','kind':'requires','reason':'Code identity alone does not establish logical residency.'},{'from':'LAW-BOUNDARY','to':'LAW-PROVIDER-OWNERSHIP','kind':'requires','reason':'ABI-compatible signatures do not establish unique symbol ownership.'}],'conflicts':[{'id':'CONFLICT-DWC-INTERIOR-DOCUMENTS','law_ids':['LAW-INTERIOR-OWNERSHIP'],'status':'source_offsets_resolved_document_and_artifact_provenance_pending','claims':['docs/NATIVE_LINK_CLOSURE.md reports original +0x1c/+0x38','Original assembly and test_guest32_dwc_rules.py give +0x18/+0x34'],'base_analysis':'Assembly gDwcNetCheckState has first word at +0, redirected at +4 (ov00_0221A6BC), five words through http at +20, httpParams at +24 and authParams at +52. Header matches this sequence. Older report explicitly calls +28/+56 aliases of the same state; no alternate base is identified. A hypothetical base four bytes earlier would give those numbers but is unsupported.', 'resolution':'Assembly .space arithmetic directly supports +0x18/+0x34. Do not reuse older offsets as original authority; re-audit old diagnostic fixtures.'}],'duplicate_review':{'status':'partial','method':'Exact duplicate law IDs merged for shared callback, allocation and boundary invariants; broader semantic overlaps still require manual review.'}}
for l in laws:
 l['C']['interactions']=[r for r in composition['relations'] if l['id'] in (r['from'],r['to'])]
for cid in ['HISTORY','SNAPSHOTS','ARTIFACTS','TESTS','SUBSYSTEMS','UNREACHABLE']:
 unresolved.append({'id':'UNRESOLVED-'+cid,'status':'open','obligation':{'HISTORY':'Review every changes.jsonl record not fully_reviewed; root hunks in hunks.jsonl. Only libntr fork delta is in scope; unrelated upstream development is excluded by user instruction.','SNAPSHOTS':'Review all named tree snapshot files, compare each against appropriate commit/worktree, split meaningful changes and classify.','ARTIFACTS':'Read all manifest artifacts; authenticate test results with commands, inputs, hashes and revisions. Mere existence proves no pass.','TESTS':'Review current and historical test bodies and result artifacts; no tests executed in this audit.','SUBSYSTEMS':'Recover remaining OS scheduler/context, hardware, filesystem, save/input, audio/rendering, ARM7/ARM9, fixed-point, assembly, optimization, asset and build corrections individually. No subsystem support inferred from source presence.','UNREACHABLE':'Reachable refs and reflogs inventoried. Unreferenced object recovery, external histories and missing artifacts have not been investigated; no claim of inaccessible or absent material is justified yet.'}[cid]})
for r in corrections:
 unresolved.append({'id':'UNRESOLVED-'+r['id'],'status':'open','correction_id':r['id'],'obligation':'Review introducing and follow-up hunks; split candidate further where independent fixes exist; recover precise failure, dependencies and counterexamples; validate current implementation and test evidence.'})
# A bounded target-specific measurement, separate from general law verification.
layout_path=OUT/'dwc-layout-evidence.json'
if layout_path.exists():
 measured=json.loads(layout_path.read_text())
 e=ref('docs/semantic-law-corpus/dwc-layout-evidence.json');e['provenance_category']='diagnostic-evidence'
 for c in corrections:
  if c['id']=='COR-DWC-INTERIOR':
   c['evidence'].append(e)
   c['measurements'].update(arm32_compiler_offsets=[24,52],arm64_compiler_offsets=[32,72],alternate_assembly_base='gDwcHttpTestServer',offsets_from_alternate_base=[28,56],cause_of_older_claim='unresolved; native expansion explicitly ruled out for the measured exact original declarations')
   c['test_results']='Fresh target-specific compiler layout probe passed; exact original declarations verified in preprocessed output. ARM32 and ARM64 complete record dumps and LLVM constants retained. Older diagnostic derivation remains unresolved.'
 for l in laws:
  if l['id'] in ('LAW-LAYOUT','LAW-INTERIOR-OWNERSHIP'):
   l['E'].append(e);l['V']['existing_checks'].append(e)
   l['V']['focused_result']='DWC original NetCheckState, NasHttpParams and AuthParams measured under ARM32 and ARM64; record dumps and LLVM constants agree. This is not proof of all aggregate transformations.'
   l['verification_status']='focused_layout_check_passed_general_invariant_unverified'
 conflict=composition['conflicts'][0]
 conflict['status']='target_layouts_measured_older_claim_origin_unresolved'
 conflict['base_analysis']='Exact original NetCheckState: ARM32 fields httpParams/authParams at 24/52; ARM64 at 32/72. Assembly coordinates also give 28/56 relative to the preceding gDwcHttpTestServer, not gDwcNetCheckState. No diagnostic derivation confirms that alternate base was used.'
 conflict['resolution']='ARM64 expansion is not the source of 28/56 for these declarations. Preserve old claims; origin remains unresolved despite a numeric alternate-base match.'
 conflict['evidence']=[e]
 unresolved.append({'id':'UNRESOLVED-DWC-OLD-OFFSET-ORIGIN','status':'open','law_ids':['LAW-LAYOUT','LAW-INTERIOR-OWNERSHIP'],'evidence':[e],'obligation':'Recover the actual calculation that produced the hard-coded 28/56 in the older test and narrative. Current snapshots show claims but not derivation; native layouts are 32/72. Alternate preceding symbol base matches numerically but is not established provenance.'})

# Link candidate evidence to matching file changes without marking whole files reviewed.
for c in changes:
 ids=[r['id'] for r in corrections for e in r['evidence'] if e['repository']==c['repository'] and e['path']==c['path'] and e['revision']==c['commit']]
 c['correction_ids']=sorted(set(ids))
manifest['fork_scope_evidence']={'upstream_base':git('upstream/libntr','merge-base','macos-arm64','main').strip(),'base_ref':'refs/heads/main','remotes':git('upstream/libntr','remote','-v').splitlines(),'patch_comparison':git('upstream/libntr','cherry','-v','main','macos-arm64').splitlines(),'reflog_variant':git('upstream/libntr','rev-parse','34c593f6').strip(),'variant_relationship':'34c593f6 and 4780187 share parent b278476; range-diff differs only SDK_FROM_TOOL versus SDK_DATA_ONLY in nitro.h. Both are fork work; former is superseded.','excluded_feature_refs':'origin/features/* are unrelated upstream branches, excluded by ancestry.'}
manifest['reviewed_evidence']=sorted({json.dumps(e,sort_keys=True) for r in corrections for e in r['evidence']})
manifest['reviewed_evidence']=[json.loads(e) for e in manifest['reviewed_evidence']]
for c in corrections:
 c['record_kind']='catalog_hypothesis' if c['id'].startswith('COR-G32-') else 'observed_failure' if c['id'].startswith('COR-DWC-') else 'historical_correction' if c['commit_provenance'] else 'current_contract_pending_history'
 for p in c['commit_provenance']:p['provenance_category']='porting-history'
for h in hunks:
 c=next(c for c in changes if c['id']==h['change_id']);h['disposition']=c['disposition'];h['correction_ids']=c['correction_ids']
manifest['counts']={'commits_inventoried':sum(len(r['commits']) for r in manifest['repositories']),'commits_fully_reviewed':sum(c['disposition'].startswith('fully_reviewed') for r in manifest['repositories'] for c in r['commits']),'file_changes_inventoried':len(changes),'file_changes_fully_reviewed':sum(c['disposition']=='fully_reviewed' for c in changes),'in_scope_hunks_inventoried':len(hunks),'correction_candidates':len(corrections),'historical_corrections_extracted':sum(c['record_kind']=='historical_correction' for c in corrections),'catalog_hypotheses':sum(c['record_kind']=='catalog_hypothesis' for c in corrections),'observed_failures':sum(c['record_kind']=='observed_failure' for c in corrections),'current_contracts_pending_history':sum(c['record_kind']=='current_contract_pending_history' for c in corrections),'laws':len(laws),'existing_rules_partially_mapped':len(coverage),'artifacts_inventoried':len(artifacts),'worktree_changes_inventoried':len(workchanges),'worktree_changes_fully_reviewed':0}
manifest['resume']={'changes':'changes.jsonl','root_hunks':'hunks.jsonl','tree_snapshots':'repositories[].tree_snapshots[].files','current_material':'repositories[].worktree','artifacts':'artifacts[]','filter':'Every disposition other than fully_reviewed/fully_reviewed_nonsemantic needs review. Evidence read is not whole-change review.'}
lines('worktree-changes.jsonl',workchanges);write('history-manifest.json',manifest);lines('changes.jsonl',changes);lines('hunks.jsonl',hunks);lines('corrections.jsonl',corrections);lines('laws.jsonl',laws);lines('correction-law-links.jsonl',links);write('existing-rule-coverage.json',{'schema':1,'status':'partial','rules':coverage});write('composition.json',composition);lines('unresolved.jsonl',unresolved)
print(json.dumps(manifest['counts'],sort_keys=True))
