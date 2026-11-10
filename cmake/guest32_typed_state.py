"""Source-derived field projections; unknown pointer roles never become bytes. MIT."""
import json
from pathlib import Path


def flat(guest,native,go=0,no=0,path=()):
    if guest['kind']!=native['kind']:raise ValueError('Guest/native field kinds differ')
    kind=guest['kind']
    if kind=='pointer':return [dict(guest_offset=go,native_offset=no,width=4,kind=3,path=path)]
    if kind in ('integer','float'):
        if guest!=native:raise ValueError('Scalar width requires a separate semantic proof')
        return [dict(guest_offset=go,native_offset=no,width=guest['size'],kind=0,path=path)]
    if kind=='array':
        if guest['count']!=native['count']:raise ValueError('Array element counts differ')
        if guest['element']==native['element'] and plain(guest):
            return [dict(guest_offset=go,native_offset=no,width=guest['size'],kind=0,path=path)]
        return [field for i in range(guest['count']) for field in flat(guest['element'],native['element'],go+i*guest['element']['size'],no+i*native['element']['size'],path+(i,))]
    if kind=='struct':
        if len(guest['fields'])!=len(native['fields']):raise ValueError('Native record has different fields')
        return [field for i,(g,n) in enumerate(zip(guest['fields'],native['fields']))
                for field in flat(g['type'],n['type'],go+g['offset'],no+n['offset'],path+(i,))]
    raise ValueError('Unverified aggregate representation')


def plain(shape):
    if shape['kind'] in ('integer','float'):return True
    if shape['kind']=='array':return plain(shape['element'])
    if shape['kind']=='struct':return all(plain(f['type']) for f in shape['fields'])
    return False


ROLE_INPUTS={'include/system.h': '5934b8f85966bb3a86b159d53008a6fbe2287d7482275e36f21b2292df1f8d76', 'include/main.h': '243e6fa876ab5d29475416b2b06decf2aae519db3f7e1d028e5ccf4914d92468', 'src/main.c': '12795237f5f62c01d8d75af3df9b8768155b44a6825d0b3fa6dd952b41e404fc'}


def prove_script_command_roles(game, guest, native, fields):
    """Classify original script-table entries; do not authorize execution."""
    import re

    declaration = (game / 'include/script.h').read_text()
    table = (game / 'src/data/fieldmap/script_cmd_table.h').read_text()

    if not re.search(
        r'typedef\s+BOOL\s*\(\s*\*\s*ScrCmdFunc\s*\)'
        r'\s*\(\s*ScriptContext\s*\*\s*ctx\s*\)\s*;',
        declaration
    ):
        raise ValueError('Original ScrCmdFunc callable signature unproven')

    match = re.search(
        r'const\s+ScrCmdFunc\s+gScriptCmdTable\[\s*\]\s*='
        r'\s*\{(.*?)\};',
        table, re.S
    )
    if not match:
        raise ValueError('Original script callback initializer missing')

    body = re.sub(r'/\*.*?\*/|//[^\n]*', '', match.group(1), flags=re.S)
    entries = [x.strip() for x in body.split(',') if x.strip()]

    if not entries or any(
        re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', x) is None
        for x in entries
    ):
        raise ValueError('Script table includes an unverified initializer')

    count = len(entries)
    if (len(fields) != count or guest['size'] != 4 * count
            or native['size'] != 8 * count):
        raise ValueError('Script callback table layout/count mismatch')

    for i, field in enumerate(fields):
        if (field['kind'] != 3 or field['width'] != 4
                or field['guest_offset'] != 4 * i
                or field['native_offset'] != 8 * i):
            raise ValueError('Script callback field projection mismatch')
        field['kind'] = 2

    return count


def plans(rows,game):
    import hashlib
    for source,digest in ROLE_INPUTS.items():
        if hashlib.sha256((game/source).read_bytes()).hexdigest()!=digest:raise ValueError('Typed field role source drift: '+source)
    result=[]
    for row in rows:
        if row['status']=='byte-compatible' or not row.get('native_shapes'):continue
        entry=dict(name=row['name'],original_member=row['original_member'],admitted=False)
        result.append(entry)
        try:
            native=row['native_shapes'][0];guest=row['guest_shape']
            fields=flat(guest,native)
            # These roles come from the original System and MainOverlayState
            # declarations. Their callbacks still need actual callable adapters.
            if row['name']=='gScriptCmdTable':
                entry['script_callback_count'] = prove_script_command_roles(
                    game, guest, native, fields)
            if row['name']=='gSystem':
                for f in fields:
                    if f['kind']:f['kind']=2 if f['path'][0] in (0,2,4,5) else 1
            elif row['name']=='gMainOverlayState':
                for f in fields:
                    if f['kind']:f['kind']=1
            for f in fields:
                f['pointee_bytes']=4 if row['name']=='gSystem' and f['kind']==1 and f['path'][0] in (10,len(guest['fields'])-1) else 0
            entry.update(guest_size=guest['size'],native_size=native['size'],fields=fields,
                         reason='Pointee/callable ownership and lifetime remain execution gates')
        except ValueError as error:entry['reason']=str(error)
    return result


def emit(selected,placements):
    c='#include "guest32.h"\n'
    for i,r in enumerate(selected):
        c+=f'extern unsigned char object_{i}[] __asm__("_{r["name"]}");\nstatic const G32_Field fields_{i}[]={{\n'
        for f in r['fields']:c+='{%d,%d,%d,%d,%d},\n'%(f['guest_offset'],f['native_offset'],f['width'],f['kind'],f['pointee_bytes'])
        c+='};\n'
    c+='int HG_Guest32BindTypedMainState(void *ram){const G32_TypedRange records[]={\n'
    for i,r in enumerate(selected):
        c+='{%du,%du,%du,object_%d,fields_%d,sizeof(fields_%d)/sizeof(*fields_%d)},\n'%(placements[r['name']]['offset'],r['guest_size'],r['native_size'],i,i,i,i)
    c+='};return g32_bind_typed_ranges(ram,records,sizeof(records)/sizeof(*records));}\n'
    return c
