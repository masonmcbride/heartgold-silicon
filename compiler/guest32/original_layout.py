"""Recover data section coordinates from agreeing original address labels.

An After relationship establishes placement order, not a numeric address. Never
infer an unanchored section from its neighbour or pack it at a synthetic offset.
"""
import re
import hashlib
import subprocess

MAIN_BASE = 0x02000000
MAIN_SIZE = 0x00400000


def overlay_id_constants(game, images):
    """Resolve the authoritative assembly SDK macro using original image IDs."""
    header = (game/'lib/include/nitro/fs/overlay.h').read_text()
    if not re.search(r'(?m)^#define\s+FS_OVERLAY_ID\(name\)\s+SDK_OVERLAY_##name##_ID\s*$', header):
        raise ValueError('original assembly overlay-ID macro changed')
    return {'FS_OVERLAY_ID('+name+')':image['id'] for name,image in images.items()
            if image['kind']=='Overlay'}


def overlay_id_symbols(game, images):
    """C's address expression denotes the original linker's absolute ID value."""
    header = (game/'lib/include/nitro/fs/overlay.h').read_text()
    if not re.search(r'#define\s+FS_OVERLAY_ID\(name\)\s+\(\(u32\)&\(SDK_OVERLAY_\s*##\s*name\s*##\s*_ID\)\)', header):
        raise ValueError('original C overlay-ID macro changed')
    constants = overlay_id_constants(game, images)
    return {'SDK_OVERLAY_'+name+'_ID': constants['FS_OVERLAY_ID('+name+')']
            for name,image in images.items() if image['kind']=='Overlay'}


def annotated_sections(text, raw, labels):
    """Recover main-image placement only from agreeing original numeric labels.

    Named labels retain address comments after source naming. Every available
    anchor in a section must agree; adjacency is never placement evidence.
    """
    anchors = {}
    for name, address in re.findall(r'^([A-Za-z_][A-Za-z_0-9]*):\s*;\s*0x([0-9A-Fa-f]{8})', text, re.M):
        if name in labels:
            section, offset = labels[name]
            anchors.setdefault(section, []).append((name, int(address, 16)-offset))
    for name, (section, offset) in labels.items():
        if re.fullmatch(r'_[0-9A-Fa-f]{8}', name):
            anchors.setdefault(section, []).append((name, int(name[1:], 16)-offset))
    result = {}
    for section, entries in anchors.items():
        bases = {base for _, base in entries}
        if len(bases) != 1:
            raise ValueError('inconsistent original address annotations: '+repr(entries))
        base = bases.pop()
        if base < MAIN_BASE or len(raw[section]) > MAIN_BASE+MAIN_SIZE-base:
            raise ValueError('original section outside DS main RAM: '+section)
        result[section] = dict(address=base, size=len(raw[section]), anchors=[n for n, _ in entries])
    return result


def anchored_sections(raw, labels, image_id):
    result = {}
    for section, data in raw.items():
        anchors = []
        for name, (owner, offset) in labels.items():
            match = re.fullmatch(r'ov(\d+)_([0-9A-Fa-f]{8})', name)
            if owner == section and match and int(match[1]) == image_id:
                anchors.append((name, int(match[2], 16) - offset))
        if not anchors:
            continue
        bases = {base for _, base in anchors}
        if len(bases) != 1:
            raise ValueError('inconsistent original address anchors: ' + repr(anchors))
        base = bases.pop()
        if base < MAIN_BASE or len(data) > MAIN_BASE + MAIN_SIZE - base:
            raise ValueError('original section outside DS main RAM: ' + section)
        result[section] = dict(address=base, size=len(data), anchors=[name for name, _ in anchors])
    return result


def verified_sections(raw, labels, references, proof):
    """Validate historical numeric placement against every byte and relocation."""
    from native_data_ir import integer
    result = {}
    for section, record in proof['sections'].items():
        data = raw[section]; base = record['address']
        if (len(data) != record['size'] or hashlib.sha256(data).hexdigest() != record['bytes_sha256'] or
                base < MAIN_BASE or len(data) > MAIN_BASE+MAIN_SIZE-base):
            raise ValueError('historical original section bytes/extent changed: '+section)
        known = {name:base+off for name,(owner,off) in labels.items() if owner==section}
        actual = {}
        for (owner,off),(expr,width) in references.items():
            if owner!=section:continue
            try:value=integer(expr,known)
            except ValueError:value=expr
            actual[off]=(value,width)
        expected = {r['offset']:(r.get('address',r.get('expression')),r['width']) for r in record['relocations']}
        if actual != expected:raise ValueError('historical original section relocations changed: '+section)
        result[section] = dict(address=base,size=len(data),provenance=proof['provenance'])
    return result


def recover_sections(current, historical, historical_text, image_id):
    """Prove retained sections against an anchored original source snapshot.

    Whole identical sections may retain renamed labels. A smaller retained range
    requires agreeing common labels; content similarity alone never places it.
    Every relocation must preserve its target, including interior aliases.
    """
    from native_data_ir import integer
    raw,labels,refs=current
    old,old_labels,old_refs=historical
    anchors=anchored_sections(old,old_labels,image_id)
    for section,proof in annotated_sections(historical_text,old,old_labels).items():
        if section in anchors and anchors[section]['address']!=proof['address']:
            raise ValueError('historical anchor disagreement: '+section)
        anchors[section]=proof
    result={}
    for section,data in raw.items():
        if section not in anchors:continue
        candidates={old_labels[n][1]-offset for n,(s,offset) in labels.items()
                    if s==section and n in old_labels and old_labels[n][0]==section}
        if not candidates and data==old[section]:candidates={0}
        if len(candidates)!=1:continue
        delta=candidates.pop()
        if delta<0 or delta+len(data)>len(old[section]):continue
        if data!=old[section][delta:delta+len(data)]:continue
        base=anchors[section]['address']+delta
        known={n:base+o for n,(s,o) in labels.items() if s==section}
        old_known={n:anchors[section]['address']+o for n,(s,o) in old_labels.items() if s==section}
        def target(expr,names):
            try:return integer(expr,names)
            except ValueError:return expr
        before={off-delta:(target(expr,old_known),width) for (s,off),(expr,width) in old_refs.items()
                if s==section and delta<=off<delta+len(data)}
        after={off:(target(expr,known),width) for (s,off),(expr,width) in refs.items() if s==section}
        if before!=after:continue
        if any(off<0 or off+width>len(data) for off,(_,width) in after.items()):
            raise ValueError('relocation straddles retained source range')
        result[section]=dict(address=base,size=len(data),historical_offset=delta,
            bytes_sha256=hashlib.sha256(data).hexdigest(),relocations=[
                dict(offset=off,width=width,**({'address':value} if isinstance(value,int) else {'expression':value}))
                for off,(value,width) in sorted(after.items())])
    spans=sorted((r['address'],r['address']+r['size']) for r in result.values())
    if any(end>next_start for (_,end),(next_start,_) in zip(spans,spans[1:])):
        raise ValueError('overlapping recovered original sections')
    return result


def verify_recovery(game, source, current, proof, constants):
    """Reproduce new historical proofs; a catalog number is not evidence."""
    provenance=proof['provenance']
    if provenance.get('rule')!='anchored-retained-range-v1':return
    from native_image_graph import parse_manifest,source_record,ownership
    images=parse_manifest(game/'main.lsf')
    image=next((v for v in images.values() if v['kind']=='Overlay' and v['id']==proof['image_id']),None)
    relative=str(source.resolve().relative_to(game.resolve()))
    members=[] if image is None else [m for m in image['objects'] if source_record(game,m)['source']==relative]
    if len(members)!=1 or ownership(images)[members[0]]!=[image['name']]:
        raise ValueError('historical placement has no unique original image owner: '+relative)
    from native_data_ir import parse,raw_layout
    result=subprocess.run(['git','-C',str(game),'show',provenance['commit']+':'+provenance['path']],
                          capture_output=True)
    if result.returncode or hashlib.sha256(result.stdout).hexdigest()!=provenance['sha256']:
        raise ValueError('missing or changed historical placement evidence: '+str(source))
    text=result.stdout.decode()
    recovered=recover_sections(current,raw_layout(parse(source,text=text,constants=constants)),text,proof['image_id'])
    if recovered!=proof['sections']:
        raise ValueError('historical placement proof does not reproduce: '+str(source))
