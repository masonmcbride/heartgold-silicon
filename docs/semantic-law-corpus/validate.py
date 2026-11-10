#!/usr/bin/env python3
"""Validate research references and accounting without invoking production tests."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
errors=[];warnings=[]
def check(ok,msg):
 if not ok:errors.append(msg)
def read(name):return json.loads((HERE/name).read_text())
def rows(name):return [json.loads(s) for s in (HERE/name).read_text().splitlines()]
def git(repo,*args):return subprocess.check_output(['git','-C',str(ROOT/repo),*args],stderr=subprocess.PIPE).decode().strip()
def ids(rs,label):
 result={r['id'] for r in rs};check(len(result)==len(rs),'duplicate '+label+' IDs');return result
m=read('history-manifest.json');cs=rows('corrections.jsonl');ls=rows('laws.jsonl');links=rows('correction-law-links.jsonl');changes=rows('changes.jsonl');hunks=rows('hunks.jsonl');wt=rows('worktree-changes.jsonl');unresolved=rows('unresolved.jsonl')
cids=ids(cs,'correction');lids=ids(ls,'law');chids=ids(changes,'change');ids(hunks,'hunk');ids(wt,'worktree');ids(unresolved,'unresolved')
commits={};valid_refs=set()
for repo in m['repositories']:
 name=repo['path'];commits[name]={c['commit'] for c in repo['commits']}
 check(name!='upstream/pokeheartgold','Original-source history must not be in porting denominator')
 tips=[]
 for r in repo['refs']:
  try:
   check(git(name,'cat-file','-t',r['object'])==r['type'],'ref object type changed')
   if r['type']=='commit':tips.append(r['object'])
   elif r['type']=='tag':tips.append(git(name,'rev-parse',r['object']+'^{commit}'))
  except subprocess.CalledProcessError:errors.append('missing ref '+r['object'])
 tips+=git(name,'reflog','--all','--format=%H').splitlines()
 expected=set(git(name,'rev-list',*sorted(set(tips)),*repo['excluded_ancestry']).splitlines())
 check(expected==commits[name],name+' commit coverage mismatch')
 for c in repo['commits']:
  check(bool(c['disposition']),'missing commit disposition')
 for s in repo['tree_snapshots']:
  check(bool(s['disposition']),'missing snapshot disposition')
  check(all(f.get('disposition') for f in s['files']),'missing snapshot file disposition')
 for w in repo['worktree']:check(bool(w.get('disposition')),'worktree missing disposition')
# Snapshot reference validation with caching; evidence categories stay distinct.
allowed={'porting-history','original-source-contract','hardware-or-sdk-reference','diagnostic-evidence','regression-evidence'}
def evidence(e):
 key=json.dumps(e,sort_keys=True)
 if key in valid_refs:return
 valid_refs.add(key);check(e.get('provenance_category') in allowed,'missing provenance category '+str(e))
 repo=e['repository'];path=e['path'];rev=e['revision']
 check(not Path(path).is_absolute() and '..' not in Path(path).parts,'nonrelative evidence path')
 try:
  if rev=='worktree':
   check(hashlib.sha256((ROOT/repo/path).read_bytes()).hexdigest()==e['sha256'],'worktree evidence changed '+path)
  else:
   git(repo,'cat-file','-e',rev+'^{commit}');git(repo,'cat-file','-e',rev+':'+path)
 except (OSError,subprocess.CalledProcessError):errors.append('unavailable evidence without unavailable marker '+str(e))
for c in cs:
 check(bool(c.get('invariant')),'empty correction invariant')
 check(all(l in lids for l in c['law_ids']),'unknown correction law')
 check(any(l['correction_id']==c['id'] for l in links) or any(u.get('correction_id')==c['id'] for u in unresolved),'unmapped correction')
 for p in c['commit_provenance']:
  try:check(git(p['repository'],'cat-file','-t',p['commit'])=='commit','bad commit provenance')
  except subprocess.CalledProcessError:errors.append('unavailable commit '+p['commit'])
 for e in c['evidence']+c['current_implementation']+c['tests']:evidence(e)
for l in ls:
 check(bool(l['applicability']) and bool(l['invariant']),'empty law applicability/invariant')
 check(all(l.get(k) for k in ('D','P','T','Q','E','V','C')),'missing formal law components '+l['id'])
 check('evidence_status' in l and 'verification_status' in l,'conflated evidence/verification')
 if l['verification_status']=='formally_proven':check(bool(l.get('proof_evidence')),'unsupported formal proof')
 for e in l['E']+l['implementation_locations']+l['V']['existing_checks']:evidence(e)
for link in links:check(link['correction_id'] in cids and link['law_id'] in lids,'dangling correction-law link')
for c in cs:
 check(set(c['law_ids'])=={x['law_id'] for x in links if x['correction_id']==c['id']},'correction links disagree '+c['id'])
for l in ls:
 check(set(l['historical_correction_ids'])=={x['correction_id'] for x in links if x['law_id']==l['id']},'law reverse links disagree '+l['id'])
for c in changes:
 check(c['commit'] in commits[c['repository']],'out-of-scope change')
 check(bool(c['disposition']),'change missing disposition')
 check(all(x in cids for x in c['correction_ids']),'dangling change correction')
for h in hunks:check(h['change_id'] in chids and bool(h['disposition']),'invalid hunk')
for w in wt:
 source=ROOT/w['repository']/w['path']
 observed=hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
 check(observed==w['sha256'],'inventoried current content changed '+w['path'])
 check(all(x in cids for x in w.get('correction_ids',[])),'dangling current correction')
for repo in m['repositories']:
 for commit in repo['commits']:
  files=[c for c in changes if c['repository']==repo['path'] and c['commit']==commit['commit']]
  check(not commit['disposition'].startswith('fully_reviewed') or all(c['disposition']=='fully_reviewed' for c in files),'commit marked reviewed with pending files')
check(m['counts']['file_changes_inventoried']==len(changes),'change count mismatch')
check(m['counts']['commits_inventoried']==sum(map(len,commits.values())),'commit denominator mismatch')
coverage=read('existing-rule-coverage.json')['rules'];check(len(coverage)==11,'existing rule mapping not eleven')
for r in coverage:check(all(l in lids for l in r['law_ids']) and all(c in cids for c in r['correction_ids']),'dangling existing rule mapping')
composition=read('composition.json')
for rel in composition['relations']:check(rel['from'] in lids and rel['to'] in lids,'dangling composition relation')
# Conservative duplicate screen: semantic equivalence needs human review.
seen={}
for l in ls:
 norm=' '.join(l['invariant'].lower().split())
 if norm in seen: warnings.append('Potential duplicate invariants: '+seen[norm]+' / '+l['id'])
 seen[norm]=l['id']
pending=sum(c['disposition']!='fully_reviewed' for c in changes)
pending_current=sum(c['disposition']!='fully_reviewed' for c in wt)
check(m['counts']['file_changes_fully_reviewed']==len(changes)-pending,'reviewed historical count mismatch')
check(m['counts']['worktree_changes_fully_reviewed']==len(wt)-pending_current,'reviewed current count mismatch')
queue=read('pending-review.json')
check(set(queue['historical_change_ids'])=={c['id'] for c in changes if c['disposition']!='fully_reviewed'},'pending historical queue mismatch')
check(set(queue['worktree_change_ids'])=={c['id'] for c in wt if c['disposition']!='fully_reviewed'},'pending current queue mismatch')
check(m['completeness']=='incomplete' or pending==0,'false completeness claim')
warnings+=['Semantic equivalence/overlap review incomplete; exact-text screen is not deduplication proof.',f'{pending} historical file changes and {pending_current} current changes remain on review queue.','Named tree snapshots and diagnostic artifact inventory still need review.','DWC measured layouts and alternate-base match are preserved; older diagnostic derivation remains unresolved.']
layout_path=HERE/'dwc-layout-evidence.json'
if layout_path.exists():
 layout=json.loads(layout_path.read_text());header=layout['header']
 check(hashlib.sha256((ROOT/header['repository']/header['path']).read_bytes()).hexdigest()==header['sha256'],'DWC original header changed since measurement')
 for target,expected in [('arm32',[24,52]),('arm64',[32,72])]:
  record=layout['layouts'][target];values=record['values']
  check([values['NetCheckState.httpParams'],values['NetCheckState.authParams']]==expected,'DWC offset measurement inconsistent')
  check(record['original_definitions_preprocessor_verified'] and len(record['complete_record_layouts'])==3,'DWC exact definitions/layouts missing')
 for claim in layout['claim_provenance']:
  for snap in claim['tree_snapshots']:
   check(git('.', 'rev-parse',snap['tree']+':'+claim['path'])==snap['blob'],'DWC snapshot provenance mismatch')

result={'schema':1,'result':'PASS' if not errors else 'FAIL','meaning':'Structural/reference validation only; historical reconstruction remains incomplete.','errors':errors,'warnings':warnings,'counts':m['counts'],'evidence_references_checked':len(valid_refs),'conflicts_reported':[c['id'] for c in composition['conflicts']]}
(HERE/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
