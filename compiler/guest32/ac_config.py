"""Original AC configuration span: guest words and complete source bytes. MIT."""
import hashlib
from pathlib import Path
import re
from native_data_ir import parse, raw_layout

INPUTS = {'lib/NitroDWC/src/ap_connect.c': 'c18173889587609b14cc993dc51c4982b4abf0a8a4693b0b068f29112e9d4601', 'lib/NitroDWC/src/ap_connect_control.c': '232d1850ab8e956a77926dd4ebe4214ad1e236766156ba8712431b8c2d096ff5', 'lib/NitroDWC/asm/dwc_lib_rodata.s': '005b06c27607825c74e17a436136ed908881b3de9f96142503f92ed2662fd75c'}


def contract(game, placements):
    for source,digest in INPUTS.items():
        if hashlib.sha256((game/source).read_bytes()).hexdigest()!=digest:
            raise ValueError('AC socket configuration source drift: '+source)
    source=(game/'lib/NitroDWC/src/ap_connect.c').read_text()
    control=(game/'lib/NitroDWC/src/ap_connect_control.c').read_text()
    copy=re.search(r'MI_CpuCopy8\(DWCi_AC_SocketConfigTemplate, cfg, (0x[0-9a-f]+)\)',source)
    size=int(copy[1],16)
    allocation=re.search(r'DWCi_AC_Globals\.p4 = DWCi_AC_Alloc\(4, (0x[0-9a-f]+)\)',control)
    if not allocation or int(allocation[1],16)!=size:
        raise ValueError('AC command allocation/copy extent mismatch')
    if 'return DWCi_AC_Globals.p4;' not in control:
        raise ValueError('AC destination ownership changed')
    raw,labels,refs=raw_layout(parse(game/'lib/NitroDWC/asm/dwc_lib_rodata.s'))
    section,start=labels['DWCi_AC_SocketConfigTemplate']
    next_label=min(p for s,p in labels.values() if s==section and p>start)
    adjacent=labels['ov00_022160F0']
    if next_label-start!=72 or adjacent!=(section,next_label) or size!=88:
        raise ValueError('AC original template/adjacent record extent changed')
    if refs.get((section,next_label))!=('sStr_NINTENDO_DS',4):
        raise ValueError('AC adjacent original guest pointer target changed')
    if placements['ov00_022160F0']['offset']-placements['DWCi_AC_SocketConfigTemplate']['offset']!=72:
        raise ValueError('AC guest source records are no longer contiguous')
    if start+size>len(raw[section]):raise ValueError('AC copy source is incomplete')
    prefix=re.search(r'typedef struct SocCfg \{(.*?)\} SocCfg;',source,re.S)[1]
    fields=re.findall(r'u32\s+(\w+)\s*;',prefix)
    if len(fields)!=9:raise ValueError('AC scalar prefix requires a new layout proof')
    return dict(representation='original guest32; no native pointer widening',
                template_size=72,allocation_size=size,copy_size=size,
                declared_scalar_prefix_size=4*len(fields),
                adjacent_record='ov00_022160F0',adjacent_bytes_copied=16,
                adjacent_pointer='sStr_NINTENDO_DS',pointer_width=4,
                unrelocated_span_sha256=hashlib.sha256(raw[section][start:start+size]).hexdigest(),
                native_SOC_Startup_admitted=False,source_hashes=INPUTS)
