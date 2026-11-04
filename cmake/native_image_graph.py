"""Original image membership and native source provenance, shared by build and audits.

After is original placement metadata, never a native symbol dependency.
"""
import argparse
import json
from pathlib import Path, PurePosixPath
import re

def parse_manifest(path, validate_ids=True):
    images = {}
    current = None
    next_id = 0
    for raw in path.read_text().splitlines():
        line = raw.split('#', 1)[0].strip()
        header = re.fullmatch(r'(Static|Overlay|Autoload)\s+(\w+)', line)
        if header:
            kind, name = header.groups()
            if name in images:
                raise ValueError('Duplicate image: ' + name)
            image_id = next_id if kind == 'Overlay' else None
            if kind == 'Overlay':
                if validate_ids and name.startswith('OVY_') and name != f'OVY_{next_id}':
                    raise ValueError('Original numeric ID mismatch: ' + name)
                next_id += 1
            current = images[name] = dict(name=name, kind=kind, id=image_id, objects=[], after=[])
        elif line.startswith('Object ' ) or re.match(r'Object\s', line):
            if current is None:
                raise ValueError('Object outside image')
            obj = line.split()[1:]
            if not obj or not obj[0].endswith('.o') or '..' in PurePosixPath(obj[0]).parts or obj[0].startswith('/'):
                raise ValueError('Unsupported object directive: ' + line)
            if len(obj) > 1:
                if current['kind'] == 'Overlay':
                    raise ValueError('Unsupported overlay section selection: ' + line)
                current.setdefault('section_directives', []).append(line)
            if obj[0] in current['objects']:
                if current['kind'] == 'Overlay':
                    raise ValueError('Duplicate object: ' + obj[0])
            else:
                current['objects'].append(obj[0])
        elif re.match(r'After\s', line):
            current['after'].extend(line.split()[1:])
        elif line == '}':
            current = None
        elif current and current['kind'] == 'Overlay' and line not in ('', '{'):
            raise ValueError('Unsupported overlay directive: ' + line)
    for image in images.values():
        if any(name not in images for name in image['after']):
            raise ValueError('Unknown After relationship: ' + image['name'])
    return images



def image_policy(image):
    import hashlib
    policies=json.loads(Path(__file__).with_name('native_image_policy.json').read_text())
    policy=policies.get(image['name'])
    if policy and hashlib.sha256('\n'.join(image['objects']).encode()).hexdigest()!=policy['membership_sha256']:
        raise ValueError('Native image policy membership changed: '+image['name'])
    return policy


def ownership(images):
    result = {}
    for image in images.values():
        for original in image['objects']:
            result.setdefault(original, []).append(image['name'])
    return result


def source_record(game, original):
    candidates = [game / (original[:-2] + suffix) for suffix in ('.c', '.cpp', '.s')]
    found = [p for p in candidates if p.is_file()]
    if len(found) != 1:
        return dict(object=original, kind='ambiguous' if found else 'missing',
                    candidates=[str(p.relative_to(game)) for p in found])
    path = found[0]
    kind = {'.c':'C', '.cpp':'C++', '.s':'assembly'}[path.suffix]
    return dict(object=original, source=str(path.relative_to(game)), kind=kind)


def representation(game, original, native_dir=None, adapted_dir=None):
    """One source-to-native decision used by selection and whole-graph diagnostics."""
    import native_sources
    import native_assembly_data as assembly
    record = source_record(game, original)
    kind = record['kind']
    if kind in ('C','C++'):
        relative = record['source']
        adapted = adapted_dir and relative in native_sources.OVERLAY_NATIVE_SOURCES
        record.update(status='available', conversion='validated C adaptation' if adapted else 'original '+kind,
                      native_source=str((adapted_dir if adapted else game)/relative),
                      dependencies=[str(game/relative)])
    elif kind == 'assembly':
        try:
            assembly.recipe(game, original)
        except (ValueError, FileNotFoundError) as error:
            record.update(status='blocked', conversion='unavailable assembly representation', reason=str(error),
                          classification=assembly.classify(game/record['source']))
        else:
            record.update(status='available', conversion='source-validated data',
                          native_source=str(native_dir/(original[:-2]+'.S')) if native_dir else None,
                          dependencies=[str(game/dep) for dep in assembly.recipe_dependencies(original)],
                          conversion_dependencies=assembly.recipe_script_dependencies(original))
    else:
        record.update(status='blocked', reason='Native representation requires review: '+kind)
    return record


# These identities have no object/library directives in the original LSF.
# The independently checked ROM checksums prove linker-generated padding only.
EMPTY_OVERLAYS = {9: 'OVY_6', 11: 'main', 66: 'main', 77: 'main',
                  79: 'OVY_42', 107: 'main', 125: 'ds_protect',
                  126: 'ds_protect', 127: 'ds_protect', 128: 'ds_protect'}


def original_membership(game, image):
    if image['objects']:
        return dict(classification='nonempty original', verified_empty=False)
    result = dict(classification='unverified empty membership', verified_empty=False)
    if image['id'] not in EMPTY_OVERLAYS or image['kind'] != 'Overlay':
        return result
    # Synthetic/partial manifests are not authoritative original checkouts.
    if not (game/'heartgold.us/main.sha1').exists():
        return result
    import hashlib
    name = image['name']
    if name != f"OVY_{image['id']}" or image['after'] != [EMPTY_OVERLAYS[image['id']]]:
        raise ValueError('Empty overlay identity/placement changed: '+name)
    evidence = ['main.lsf', 'global.inc']
    if (game/'global.inc').read_text().splitlines().count(f'FS_EXTERN_OVERLAY({name})') != 1:
        raise ValueError('Missing/duplicate original overlay declaration: '+name)
    digest = hashlib.sha1(bytes(32)).hexdigest()
    for variant in ('heartgold.us', 'soulsilver.us'):
        relative = variant+'/main.sha1'
        expected = f'{digest} *build/{variant}/{name}.sbin'
        if (game/relative).read_text().splitlines().count(expected) != 1:
            raise ValueError('Empty overlay original checksum changed: '+name)
        evidence.append(relative)
    return dict(classification='verified empty original overlay', verified_empty=True,
                evidence=evidence, overlay_table_role=dict(id=image['id'], file_id=image['id'], after=image['after']),
                original_file_size=32, original_file_sha1=digest,
                original_file_content='null static-initializer terminator and alignment padding',
                native_representation='identity metadata only; no executable image',
                runtime_validation='not exercised; original ROM retains table entry and file')


def graph(game, binary=None):
    images = parse_manifest(game / 'main.lsf')
    owners=ownership(images)
    for image in images.values():
        image['original_membership'] = original_membership(game, image)
    return dict(schema=1, images=images, ownership=owners,
                members={obj:representation(game,obj,
                    (binary/('native-data' if owners[obj]==['main'] else 'native-overlays/data')) if binary else None,
                    binary/'native' if binary else None) for obj in owners})


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != content:
        path.write_text(content)


def data_commands(game, output_root, originals):
    import native_assembly_data as assembly
    script=Path(__file__).with_name('native_assembly_data.py').resolve()
    lines=[];outputs=[]
    for original in originals:
        output=(output_root/(original[:-2]+'.S')).resolve()
        outputs.append(str(output))
        dependencies=[str(script),*assembly.recipe_script_dependencies(original),
                      *(str(game/dep) for dep in assembly.recipe_dependencies(original))]
        def quote(value):
            value=str(value)
            if any(c in value for c in (';', '"', '\n', '$')):
                raise ValueError('Unsupported CMake path delimiter: '+value)
            return '"'+value+'"'
        lines += ['add_custom_command(OUTPUT '+quote(output),
                  'COMMAND "${Python3_EXECUTABLE}" -B '+quote(script)+' --game '+quote(game)+' --object '+quote(original)+' --output '+quote(output),
                  'COMMAND "${CMAKE_COMMAND}" -E touch_nocreate '+quote(output),
                  'DEPENDS '+' '.join(quote(p) for p in dependencies)+' VERBATIM)']
    return lines,outputs


def configure(game, out):
    model = graph(game,out.parent)
    write(out / 'images.json', json.dumps(model, indent=2, sort_keys=True)+'\n')
    lines = ['# Generated from main.lsf by native_image_graph.py', 'set(game_sources']
    inventory = ['group\tobject\timplementation']
    for image in model['images'].values():
        for obj in image['objects']:
            record = model['members'][obj]
            base = obj[:-2]
            policy=image_policy(model['images']['main'])
            approved=(base.startswith(tuple(policy['c_source_prefixes'])) or
                      base+'.c' in policy['c_sources'])
            if record['kind'] == 'C' and approved:
                kind = 'original C'
                if image['name'] == 'main':
                    path = str((game / record['source']).resolve())
                    if any(c in path for c in (';', '"', '\n')):
                        raise ValueError('Unsupported CMake path: '+path)
                    lines.append('"'+path+'"')
            elif base.startswith('lib/NitroSDK/'):
                kind = 'SDK: supplied separately by libntr; verify symbol coverage'
            else:
                kind = record['kind'] + ': requires native representation/ABI review'
            inventory.append(image['name']+'\t'+obj+'\t'+kind)
    lines += [')', 'list(REMOVE_DUPLICATES game_sources)',
              'set(hg_overlay_names '+ ' '.join(i['name'] for i in model['images'].values()
                                             if i['kind']=='Overlay')+')']
    for name,image in model['images'].items():
        lines.append('set(hg_original_image_'+name+'_sources')
        for obj in image['objects']:
            record=model['members'][obj]
            if record['kind'] in ('C','C++') and record['status']=='available':
                source=record['native_source']
                if any(c in source for c in (';', '"', '\n', '$')):
                    raise ValueError('Unsupported CMake path delimiter: '+source)
                lines.append('"'+source+'"')
        lines.append(')')
    main_data=[obj for obj in model['images']['main']['objects']
               if model['members'][obj]['kind']=='assembly' and model['members'][obj]['status']=='available']
    commands,outputs=data_commands(game,out.parent/'native-data',main_data)
    commands+=['set(hg_main_data_sources '+' '.join('"'+p+'"' for p in outputs)+')']
    write(out/'main-data.cmake','\n'.join(commands)+'\n')
    write(out/'sources.cmake', '\n'.join(lines)+'\n')
    write(out.parent/'arm9-sources.tsv', '\n'.join(inventory)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    configure(args.game.resolve(), args.out.resolve())
