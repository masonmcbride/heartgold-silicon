"""Keep source-reviewed callback registration metadata with its owner.

Other image plans have no reviewed registration specification yet.
Do not borrow OVY_0's edges or infer that unreviewed callbacks are safe.
"""

REVIEWED = frozenset(("OVY_0", "OVY_38"))


def validate_machine_edges(game, spec):
    """Validate adjacent ARM call evidence before LLVM register recovery."""
    import hashlib,re,subprocess
    p=spec.get('provenance',{})
    rule=spec.get('machine_rule')
    if rule not in ('adjacent-call-result-v1','arm-call-contracts-v1'):return
    blob=subprocess.check_output(['git','-C',str(game),'show',p['commit']+':'+p['path']])
    if hashlib.sha256(blob).hexdigest()!=p['sha256']:raise ValueError('changed ARM register evidence')
    text=blob.decode()
    for rename in spec.get('renames',[]):
        diff=subprocess.check_output(['git','-C',str(game),'show',rename['commit'],'--',rename['path'],*([rename['previous_path']] if rename.get('previous_path') else [])],text=True)
        if not all(s in diff for s in rename['evidence']):raise ValueError('unproved historical callee rename')
    for e in spec['edges']:
        proof=spec['original_functions'][e['function']]
        if proof not in text or e['evidence'] not in proof:raise ValueError('unproved ARM function or call edge')
        target=e.get('arm_target',e['target'])
        if rule=='arm-call-contracts-v1':
            if e['mode']=='indirect-result':
                offset=e['arm_result_offset']
                pattern=(r"\tadd r0, sp, #"+re.escape(offset)+r"\n"
                    r"(?:\tstr r[0-9]+, \[sp(?:, #[^\]]+)?\]\n)*"
                    r"\tbl "+re.escape(target)+r"\n\tldr r[0-9]+, \[sp, #"+re.escape(offset)+r"\]")
                if e.get('result_bytes')!=4 or not re.fullmatch(pattern,e['evidence']):
                    raise ValueError('unproved ARM indirect result home')
                provider=spec['original_functions'][e['target']]
                if provider not in text or not re.search(r'\tstr r[0-9]+, \[r0\]',provider):
                    raise ValueError('unproved ARM indirect result store')
            elif e['mode']=='dominating-global':
                label=e['arm_continuation'];literal=e['arm_literal']
                required='\tldr r0, '+literal+' @ ='+e['arm_global_address']+'\n\tldr r0, [r0]\n\tcmp r0, #0\n\tbne '+label
                if e['evidence']!=required or label+':\n\tbl '+target not in proof:
                    raise ValueError('unproved ARM tested global continuation')
            else:raise ValueError('unsupported ARM call contract mode')
            if target!=e['target'] and not any(r['old']==target and r['new']==e['target'] for r in spec.get('renames',[])):
                raise ValueError('unknown ARM call identity')
            continue
        previous=e.get('arm_previous',e['previous'])
        if e['mode']!='previous-result' or e.get('argument',0)!=0:
            raise ValueError('unsupported ARM register evidence shape')
        if e['evidence']!='\tbl '+previous+'\n\tbl '+target:
            raise ValueError('ARM result is not preserved by adjacent direct calls')
        for old,new in ((target,e['target']),(previous,e['previous'])):
            if old!=new and not any(r['old']==old and r['new']==new for r in spec.get('renames',[])):
                raise ValueError('unknown ARM call identity')


def scoped_spec(owner, spec):
    if (spec.get('owner')==owner or (owner in REVIEWED and 'owner' not in spec)):
        return spec

    def empty(value):
        if isinstance(value, dict):
            return {key: empty(item) for key, item in value.items()}
        if isinstance(value, list):
            return []
        return value

    return empty(spec)
