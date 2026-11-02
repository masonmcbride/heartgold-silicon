"""Read original image ownership; generate bounded CMake selection and registry."""
import argparse
import json
from pathlib import Path
import native_assembly_data as assembly_data


from native_image_graph import parse_manifest, representation, ownership, data_commands, image_policy


def select(images, names, game, native_dir=None, adapted_dir=None):
    selected = []
    for name in names:
        if name not in images or images[name]['kind'] != 'Overlay':
            raise ValueError('Unknown overlay: ' + name)
        image = dict(images[name])
        policy=image_policy(image)
        image['archive_target']=(policy or {}).get('archive_target',f"heartgold_overlay_{image['id']}")
        if policy and 'source' in policy:
            image['native_replacement']=policy['reason']
            image['sources']=[str((Path(__file__).resolve().parents[1]/policy['source']).resolve())]
            selected.append(image)
            continue
        sources = []
        data_members = []
        for obj in image['objects']:
            record = representation(game, obj, native_dir, adapted_dir)
            if record['status'] != 'available':
                raise ValueError(f"{name}: missing native C provider for {obj}; {record['reason']}")
            source = Path(record['native_source']) if record['native_source'] else game/(obj[:-2]+'.S')
            if record['kind'] == 'assembly': data_members.append(obj)
            other = [i['name'] for i in images.values() if obj in i['objects'] and i['name'] != name]
            if other:
                raise ValueError(f'{name}: shared original object ownership {obj}: {other}')
            sources.append(str(source.resolve()))
        if not sources:
            raise ValueError('No native providers in selected image: ' + name)
        image['sources'] = sources
        if data_members:
            image['data_members'] = data_members
        selected.append(image)
    return sorted(selected, key=lambda i: i['id'])


def generate(game, out, names, adapted_dir=None, supported=False):
    images = parse_manifest(game / 'main.lsf')
    if supported:
        # Keep every exclusion explicit; unsupported members never become empty objects.
        excluded = {}
        for name,image in images.items():
            if image['kind']!='Overlay' or name in names: continue
            records = [representation(game,obj) for obj in image['objects']]
            failures = [r for r in records if r['status']!='available']
            if not records:
                excluded[name]=[dict(status='empty original image',reason='No original source members')]
                continue
            if failures: excluded[name]=failures
            else: names.append(name)
        out.mkdir(parents=True,exist_ok=True)
        from native_image_graph import write
        write(out/'blocked-images.json',json.dumps(excluded,indent=2,sort_keys=True)+'\n')
    selected = select(images, list(dict.fromkeys(names)), game, out / 'data', adapted_dir)
    out.mkdir(parents=True, exist_ok=True)
    def write(name, text):
        path = out / name
        if not path.exists() or path.read_text() != text:
            path.write_text(text)
    write('selection.json', json.dumps(selected, indent=2) + '\n')
    cmake = ['# Generated from original main.lsf', 'set(hg_selected_overlay_ids ' + ' '.join(str(i['id']) for i in selected) + ')']
    for image in selected:
        commands,_=data_commands(game,out/'data',image.get('data_members',[]))
        cmake+=commands
        cmake += [f"set(hg_overlay_{image['id']}_target {image['archive_target']})",
                  f"set(hg_overlay_{image['id']}_name {image['name']})",
                  f"set(hg_overlay_{image['id']}_after {' '.join(image['after'])})",
                  f"set(hg_overlay_{image['id']}_sources"]
        for source in image['sources']:
            if ']====]' in source or ';' in source:
                raise ValueError('Unsupported CMake path delimiter')
            cmake.append('[====[' + source + ']====]')
        cmake.append(')')
    write('selection.cmake', '\n'.join(cmake) + '\n')
    write('registry.inc', ''.join(f"HG_NATIVE_OVERLAY({i['id']}) /* {i['name']}, After {' '.join(i['after'])} */\n" for i in selected))
    return selected


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--select', action='append', required=True)
    p.add_argument('--adapted-dir', type=Path)
    p.add_argument('--supported', action='store_true', help='Include every image with complete reviewed native representations')
    a = p.parse_args()
    generate(a.game, a.out, a.select, a.adapted_dir, a.supported)
