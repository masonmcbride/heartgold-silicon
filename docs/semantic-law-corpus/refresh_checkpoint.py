#!/usr/bin/env python3
"""Refresh research accounting and relationships without reinventorying or reviewing code."""
import hashlib,json,subprocess
from collections import Counter
from pathlib import Path
from review_updates import HERE,ROOT,get,rows,save,savelines,git
m=get('history-manifest.json');cs=rows('corrections.jsonl');ls=rows('laws.jsonl');links=rows('correction-law-links.jsonl');changes=rows('changes.jsonl');wt=rows('worktree-changes.jsonl')
# A current source reference is a location, never a historical-introduction claim.
for c in cs:
 if c['record_kind']=='current_contract_pending_history':
  for e in c['evidence']:
   if e['revision']=='worktree' and e['provenance_category']=='porting-history' and e not in c['current_implementation']:
    c['current_implementation'].append(e)
 c.setdefault('unresolved_obligations',[])
 for obligation in c.get('known_counterexamples',[]):
  if obligation not in c['unresolved_obligations']:c['unresolved_obligations'].append(obligation)
 if c['record_kind']=='historical_correction':
  text='Trace current survival or supersession before treating this historical implementation as current.'
  if text not in c['unresolved_obligations']:c['unresolved_obligations'].append(text)
 # Pin matching historical test sources where available. Current test refs remain separately useful.
 historical=[]
 for p in c['commit_provenance']:
  for t in c['tests']:
   if t['repository']!=p['repository']:continue
   available=subprocess.run(['git','-C',str(ROOT/p['repository']),'cat-file','-e',p['commit']+':'+t['path']],capture_output=True)
   if available.returncode:continue
   historical.append({'repository':p['repository'],'revision':p['commit'],'path':t['path'],'provenance_category':'regression-evidence'})
 for e in historical:
  if e not in c['tests']:c['tests'].append(e)
# Preserve individual records while expressing genuine multiple obligations.
additional={
 'COR-WT-INDIRECT-RESULT-ABI':['LAW-FRAME-LIFETIME'],
 'COR-WT-RESULT-HOME-LIFETIME':['LAW-ARM-INDIRECT-RESULT'],
 'COR-WT-CALLBACK-RESIDENCY':['LAW-CODE-IDENTITY-DOMAIN'],
 'COR-WT-SLOT-LAYOUT':['LAW-REPRESENTATION-SEPARATION'],
 'COR-WT-SLOT-OBSERVATIONS':['LAW-LAYOUT-PRESERVING-PROMOTION'],
 'COR-WT-SLOT-LIFETIME':['LAW-POINTER-REPRESENTATION-OBSERVATION'],
 'COR-REPRO-SOUND-ALIASES':['LAW-SOURCE-OWNERSHIP','LAW-NATIVE-AGGREGATE-COHERENCE'],
 'COR-LOBBY-SPLIT-RESULT':['LAW-NATIVE-AGGREGATE-COHERENCE'],
 'COR-LOBBY-SPLIT-OWNERSHIP':['LAW-NATIVE-AGGREGATE-COHERENCE'],
 'COR-REPRO-WIFI-ARCHIVE':['LAW-NATIVE-ALIGNMENT'],
}
for c in cs:
 for law in additional.get(c['id'],[]):
  if law not in c['law_ids']:c['law_ids'].append(law)
 c['law_ids']=sorted(c['law_ids'])
 for law in c['law_ids']:
  key=c['id']+'--'+law
  if not any(x['id']==key for x in links):links.append({'id':key,'correction_id':c['id'],'law_id':law,'relationship':'additional_required_obligation'})
for link in links:
 if link['correction_id']=='COR-REPRO-FIELD-SKIP':link['relationship']='unsupported_historical_attempt_counterexample_not_admission'
for l in ls:
 l['historical_correction_ids']=sorted({c['id'] for c in cs if l['id'] in c['law_ids']})
 for c in cs:
  if l['id'] not in c['law_ids']:continue
  for e in c['current_implementation']:
   if e not in l['implementation_locations']:l['implementation_locations'].append(e)
# Keep related specialized laws separate from actual existing gate enforcement.
related={
 'g32.layout':['LAW-NATIVE-AGGREGATE-COHERENCE','LAW-REPRESENTATION-SEPARATION','LAW-LAYOUT-PRESERVING-PROMOTION'],
 'g32.allocation':['LAW-ALLOCATION-COHERENCE','LAW-NATIVE-ALIGNMENT','LAW-FRAME-LIFETIME'],
 'g32.interior':['LAW-INTERIOR-OWNERSHIP','LAW-INTERIOR-ALIAS','LAW-ORIGINAL-PLACEMENT'],
 'g32.memory':['LAW-SSA-ELABORATION','LAW-SHARED-STATE-OWNER'],
 'g32.pointer-word':['LAW-HOST-PAYLOAD','LAW-POINTER-PREDICATE','LAW-POINTER-REPRESENTATION-OBSERVATION'],
 'g32.aggregate':['LAW-ARM-INDIRECT-RESULT','LAW-AGGREGATE-COPY','LAW-NATIVE-AGGREGATE-COHERENCE'],
 'g32.integer':['LAW-ARM-REGISTER-EDGE','LAW-ARM-REGISTER-PAIR','LAW-INTERMEDIATE-WIDTH','LAW-FIXED-SCALAR-FORMAT'],
 'g32.callback':['LAW-CALLBACK-ARGUMENTS','LAW-CALLBACK-LIFETIME','LAW-CODE-IDENTITY-DOMAIN','LAW-OVERLAY-LIFETIME'],
 'g32.bulk-memory':['LAW-BACKWARD-OVERLAP','LAW-POINTER-REPRESENTATION-OBSERVATION'],
 'g32.static-data':['LAW-ORIGINAL-PLACEMENT','LAW-INTERIOR-ALIAS','LAW-SOURCE-OWNERSHIP'],
 'g32.boundary':['LAW-CALL-DECLARATION','LAW-PROVIDER-OWNERSHIP','LAW-ARTIFACT-ADMISSION','LAW-FRONTEND-SEMANTICS']}
coverage=get('existing-rule-coverage.json')
for rule in coverage['rules']:
 rule['related_specialized_laws']=related[rule['id']]
 rule['related_correction_ids']=sorted(c['id'] for c in cs if set(c['law_ids']) & set(related[rule['id']]))
 rule['related_mapping_limit']='Semantic relationship only. A shared concern does not establish this gate enforces these specialized transformations or authorizes their native runtime domain.'
 rule['correction_relationships']=[{'correction_id':c['id'],'status':'catalog_hypothesis' if c['record_kind']=='initial_catalog_hypothesis' else 'source_related_gate_enforcement_requires_trace'} for c in cs if set(c['law_ids']) & set(rule['law_ids'])]
composition=get('composition.json')
for source,target,kind,reason in [
 ('LAW-INTERIOR-ALIAS','LAW-NATIVE-AGGREGATE-COHERENCE','requires','Member offsets and strides depend on the actual canonical owner layout.'),
 ('LAW-INTERIOR-ALIAS','LAW-SOURCE-OWNERSHIP','requires','An interior label must refer to one live original storage owner.'),
 ('LAW-ARM-INDIRECT-RESULT','LAW-FRAME-LIFETIME','requires','Hidden result homes must remain live through consumers and expire with the guest invocation.'),
 ('LAW-CALLBACK','LAW-CALLBACK-LIFETIME','requires','Correct identity and arguments do not establish callback-state lifetime.'),
 ('LAW-BOUNDARY','LAW-CALL-DECLARATION','requires','The native call boundary must agree with its actual provider declaration and result convention.'),
 ('LAW-LAYOUT-PRESERVING-PROMOTION','LAW-REPRESENTATION-SEPARATION','requires','Padding promotion is scoped to native-only runtime storage, never serialized or guest32 object formats.'),
 ('LAW-LAYOUT-PRESERVING-PROMOTION','LAW-POINTER-REPRESENTATION-OBSERVATION','requires','Unchanged aggregate extent alone does not preserve integer/raw-byte observations.'),
 ('LAW-LAYOUT-PRESERVING-PROMOTION','LAW-ALIAS-ANALYSIS-SCOPE','requires','Every reachable consumer must satisfy the admitted observation contract.'),
 ('LAW-LAYOUT-PRESERVING-PROMOTION','LAW-CONTENT-VALIDATED-ARTIFACTS','requires','The admission census must match the exact production inputs actually compiled.'),
 ('LAW-LIFETIME-BOUNDARY','LAW-POINTER-REPRESENTATION-OBSERVATION','requires','Opaque release is safe only when a source-proven contract excludes further payload observation.'),
 ('LAW-ARTIFACT-ADMISSION','LAW-POSITIVE-ADMISSION','requires','Successful staging/linking cannot replace positive semantic boundary facts.'),
 ('LAW-ORIGINAL-PLACEMENT','LAW-STATIC-DATA','requires','Anchors, retained section bytes and relocations jointly determine original data identity.'),
 ('LAW-OVERLAY-LIFETIME','LAW-OVERLAY-MEMORY-EXCLUSION','requires','Logical residency must respect mutually exclusive ownership of original RAM ranges.')]:
 rel={'from':source,'to':target,'kind':kind,'reason':reason}
 if rel not in composition['relations']:composition['relations'].append(rel)
composition['relations'].sort(key=lambda x:(x['from'],x['to'],x['kind']))
composition['duplicate_review']['status']='partial_after_individual_extraction_incomplete_history'
composition['duplicate_review']['remaining']='123 candidate laws include specialized G3 operation contracts and broader representation families. Preserve all correction IDs before any semantic merge; exact text identity is not sufficient.'
for l in ls:
 for rel in composition['relations']:
  if rel['from']==l['id'] and rel['to'] not in l['C']['dependencies']:l['C']['dependencies'].append(rel['to'])
# Mirror changed-file dispositions only; unchanged current snapshot files remain separate queues.
for repo in m['repositories']:
 for w in repo['worktree']:
  changed=next((x for x in wt if x['repository']==repo['path'] and x['path']==w['path']),None)
  if changed:w.update(disposition=changed['disposition'],review_batch=changed.get('review_batch'),change_id=changed['id'])
m['resume'].update(changes='pending-review.json historical_change_ids -> changes.jsonl/hunks.jsonl',current_changes='pending-review.json worktree_change_ids -> worktree-changes.jsonl',incremental_batches='review-batch-*.json and review_updates.py; never rerun reconstruct.py over completed extraction')
for name,value in [('corrections.jsonl',cs),('laws.jsonl',ls),('correction-law-links.jsonl',links)]:savelines(name,value)
save('existing-rule-coverage.json',coverage);save('composition.json',composition);save('history-manifest.json',m)
pending=[c for c in changes if c['disposition']!='fully_reviewed'];pendingwt=[c for c in wt if c['disposition']!='fully_reviewed']
queue={'id':'PENDING-REVIEW','completeness':'incomplete','historical_change_ids':sorted(c['id'] for c in pending),'worktree_change_ids':sorted(c['id'] for c in pendingwt),'counts_by_commit':[{'repository':repo,'commit':commit,'remaining_file_changes':count} for (repo,commit),count in sorted(Counter((c['repository'],c['commit']) for c in pending).items())],'other_queues':['history-manifest.json repositories[].tree_snapshots','history-manifest.json artifacts','unresolved.jsonl'],'resume_rule':'No unreviewed file or large commit is completed by inventory, title, or line count. Examine exact old/new blobs and independent corrections before marking fully_reviewed.'}
save('pending-review.json',queue)
lines=['# Exact remaining review queue','','Reconstruction is incomplete. The queue below is a content-review queue, not an exclusion of these changes. Each ID resolves to exact old/new blobs in `changes.jsonl` and hunk dispositions in `hunks.jsonl`.','','Current changed files: '+str(len(wt)-len(pendingwt))+'/'+str(len(wt))+' reviewed. Named snapshots, diagnostic artifact relevance/contents, cross-law deduplication and current survival of historical patches remain separate obligations.','']
for item in queue['counts_by_commit']:
 lines += ['## '+item['repository']+' '+item['commit'],'',str(item['remaining_file_changes'])+' file changes remain.','']
 for c in sorted((c for c in pending if c['repository']==item['repository'] and c['commit']==item['commit']),key=lambda c:c['path']):lines.append('- `'+c['id']+'` — `'+c['path']+'`')
 lines.append('')
(HERE/'REMAINING.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'historical_pending':len(pending),'current_pending':len(pendingwt),'relationships':len(links),'composition_relations':len(composition['relations'])},sort_keys=True))
