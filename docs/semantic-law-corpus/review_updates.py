#!/usr/bin/env python3
"""Apply explicit incremental research batches; never reinventory or regenerate prior work."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
def get(name):return json.loads((HERE/name).read_text())
def rows(name):return [json.loads(x) for x in (HERE/name).read_text().splitlines()]
def save(name,value):
 (HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
def savelines(name,value):
 (HERE/name).write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in sorted(value,key=lambda x:x['id'])))
def git(repo,*args):return subprocess.check_output(['git','-C',str(ROOT/repo),*args],text=True).strip()
def reference(path,repo='.',commit=None,locator=None):
 r={'repository':repo,'path':path,'revision':commit or 'worktree','provenance_category':'porting-history' if commit else 'regression-evidence' if path.startswith('tests/') else 'hardware-or-sdk-reference' if repo!='.' else 'porting-history'}
 if not commit:r['sha256']=hashlib.sha256((ROOT/repo/path).read_bytes()).hexdigest()
 if locator:r['locator']=locator
 return r
class Batch:
 def __init__(self,id):self.data={'id':id,'corrections':[],'laws':[],'change_reviews':[],'worktree_reviews':[],'unresolved':[]}
 def correction(self,id,law,title,repo,rev,paths,failure,fix,invariant,domain,pre,tests=(),category='correctness_fix',limits=()):
  rev=git(repo,'rev-parse',rev) if rev else None
  evidence=[reference(p,repo,rev,loc) for p,loc in paths]
  testrefs=[reference(p) for p in tests]
  c={'id':id,'record_kind':'historical_correction' if rev else 'current_contract_pending_history','title':title,'classification':category,'original_failure':failure,'failure_recovery':'Recovered from changed code and its old/new behavior; original crash/run evidence not established unless separately cited.','source_construct':domain,'architectural_assumption':pre,'incorrect_host_behavior':failure,'implemented_correction':fix,'invariant':invariant,'preconditions':[pre],'postconditions':[invariant],'dependencies':[],'known_counterexamples':list(limits),'evidence':evidence,'commit_provenance':[{'repository':repo,'commit':rev,'provenance_category':'porting-history'}] if rev else [],'current_implementation':[],'implementation_status':'historical_patch_reviewed_current_status_requires_followup' if rev else 'worktree_implementation_reviewed_not_executed','tests':testrefs,'test_results':'Test source referenced where identified; no tests rerun for this review batch.','law_ids':[law]}
  self.data['corrections'].append(c)
  if law not in {r['id'] for r in rows('laws.jsonl')} and law not in {r['id'] for r in self.data['laws']}:
   self.data['laws'].append({'id':law,'title':title,'semantic_category':category,'applicability':domain,'architectural_assumptions':[pre],'invariant':invariant,'D':domain,'P':[pre],'T':fix,'Q':[invariant],'E':evidence,'V':{'existing_checks':testrefs,'execution_status':'not_run_in_this_audit','missing_obligations':['Compare complete original service/algorithm behavior and inspect recorded test results.']},'C':{'dependencies':[],'incompatibilities':[],'ordering':[],'interactions':[]},'historical_correction_ids':[],'implementation_locations':[],'evidence_status':'source_and_diff_supported','verification_status':'source_review_only','confidence':'candidate','limitations':list(limits),'outstanding_verification':['General equivalence and composition are not proved.']})
  return id
 def review(self,repo,rev,path,classification,reason,corrections=()):
  rev=git(repo,'rev-parse',rev) if rev else None
  rs=rows('changes.jsonl' if rev else 'worktree-changes.jsonl')
  matches=[r for r in rs if r['repository']==repo and r['path']==path and (not rev or r['commit']==rev)]
  assert matches,(repo,rev,path)
  for r in matches:self.data['change_reviews' if rev else 'worktree_reviews'].append({'id':r['id'],'disposition':'fully_reviewed','classification':classification,'reason':reason,'correction_ids':list(corrections)})
 def emit(self):save(self.data['id']+'.json',self.data)
def apply(path):
 batch=json.loads(Path(path).read_text());m=get('history-manifest.json'); cs=rows('corrections.jsonl');ls=rows('laws.jsonl');links=rows('correction-law-links.jsonl');changes=rows('changes.jsonl');wt=rows('worktree-changes.jsonl');hs=rows('hunks.jsonl');us=rows('unresolved.jsonl')
 for incoming,target in [(batch['corrections'],cs),(batch['laws'],ls),(batch['unresolved'],us)]:
  index={x['id']:x for x in target}
  for row in incoming:
   if row['id'] not in index:target.append(copy.deepcopy(row))
 for incoming,target in [(batch['change_reviews'],changes),(batch['worktree_reviews'],wt)]:
  index={x['id']:x for x in target}
  for r in incoming:
   assert r['id'] in index
   if target is wt:
    original=index[r['id']]; source=ROOT/original['repository']/original['path']
    observed=hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
    assert observed==original['sha256'], 'Current content changed since inventory: '+original['path']
   index[r['id']].update(r,review_batch=batch['id'])
 for c in batch['corrections']:
  for law in c['law_ids']:
   l=next(x for x in ls if x['id']==law)
   if c['id'] not in l['historical_correction_ids']:l['historical_correction_ids'].append(c['id']);l['historical_correction_ids'].sort()
   for e in c['evidence']:
    if e not in l['E']:l['E'].append(e)
   key=c['id']+'--'+law
   if not any(r['id']==key for r in links):links.append({'id':key,'correction_id':c['id'],'law_id':law})
 for h in hs:
  c=next(c for c in changes if c['id']==h['change_id'])
  if c.get('review_batch')==batch['id']:h.update(disposition=c['disposition'],classification=c['classification'],correction_ids=c['correction_ids'],review_batch=batch['id'])
 for repo in m['repositories']:
  for commit in repo['commits']:
   files=[c for c in changes if c['repository']==repo['path'] and c['commit']==commit['commit']]
   if all(c['disposition']=='fully_reviewed' for c in files):commit['disposition']='fully_reviewed'
 m.setdefault('review_batches',[])
 if batch['id'] not in m['review_batches']:m['review_batches'].append(batch['id']);m['review_batches'].sort()
 m['counts'].update(commits_fully_reviewed=sum(c['disposition'].startswith('fully_reviewed') for r in m['repositories'] for c in r['commits']),file_changes_fully_reviewed=sum(c['disposition']=='fully_reviewed' for c in changes),worktree_changes_fully_reviewed=sum(c['disposition']=='fully_reviewed' for c in wt),correction_candidates=len(cs),historical_corrections_extracted=sum(c['record_kind']=='historical_correction' for c in cs),current_contracts_pending_history=sum(c['record_kind']=='current_contract_pending_history' for c in cs),laws=len(ls))
 for name,value in [('corrections.jsonl',cs),('laws.jsonl',ls),('correction-law-links.jsonl',links),('changes.jsonl',changes),('worktree-changes.jsonl',wt),('hunks.jsonl',hs),('unresolved.jsonl',us)]:savelines(name,value)
 save('history-manifest.json',m)
 pending={'id':'PENDING-REVIEW','completeness':'incomplete','historical_change_ids':[c['id'] for c in changes if c['disposition']!='fully_reviewed'],'worktree_change_ids':[c['id'] for c in wt if c['disposition']!='fully_reviewed'],'other_queues':['history-manifest.json repositories[].tree_snapshots','history-manifest.json artifacts','unresolved.jsonl']}
 save('pending-review.json',pending);print(json.dumps(m['counts'],sort_keys=True))
if __name__=='__main__':apply(sys.argv[1])
