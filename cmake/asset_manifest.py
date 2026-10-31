"""Read the inspected subset of original archive Make manifests, never run Make.

The plan feeds existing CMake resource commands and Nintendo's original packers.
Unknown expressions, changed recipes, and missing original inputs are errors.
"""
import argparse
import glob
import hashlib
import json
from pathlib import Path
import re

# Manifest selection, not resource indices. Full hashes guard recipe semantics.
ARCHIVES = {
    'application/zukanlist/zkn_data/zukan_hw_data': ('files/application/zukanlist/zkn_data/zukan_hw_data.mk', 'target:ZUKAN_HW_DATA_NARC', '9c7f57841c44252de3f59e07b10ff8c05f9128b6a4ee54785271e2a58d6064dc', '41caec0725bd667b851c2cf6ee6d31cbbde7bfbea3e8b77f2944a24373471c45'),
    'application/annon/puzzle_gra': ('files/application/annon/puzzle_gra.mk', 'ALPH_PUZZLE_FILES', 'bb08490bf4c5d8a0db7702ae875779faa738ea472c0c31d440e0a622f0257ba8', '349d047bf727d2f538329ef02c2e1c3c9f0ad2e2eb49e6f141ee208f6cef8e3c'),
    'application/choose_starter/choose_starter_main_res': ('files/application/choose_starter/choose_starter.mk', 'target:CHOOSE_STARTER_MAIN_NARC', 'ebecf593025a69a099744c87c546f3cd4b2e4a427f48751c8ad8416f0c65d740', '162129ead6313ec877eb26b4a3c18b561172559e9d5428468c49f9cc2a0872a9'),
    'application/choose_starter/choose_starter_sub_res': ('files/application/choose_starter/choose_starter.mk', 'target:CHOOSE_STARTER_SUB_NARC', 'ebecf593025a69a099744c87c546f3cd4b2e4a427f48751c8ad8416f0c65d740', '281639e342bdb370ef7b938af5b7a7d8c4c22b02598bf7eda487a0b3a9c23d1e'),
    'application/guinness': ('files/application/guinness.mk', 'GUINNESS_FILES', '6be1b9ea0a4851d908d9a6642f900573ab7d0c6ee904de5dfcf3eb9ae0908003', '278fe0a74cdcb1489381c9cb2b2bc9d61b2aaf9d658cb871f6327d35841790cc'),
    'application/pokegear/pgear_gra': ('files/application/pokegear/pgear_gra.mk', 'PGEAR_GRA_FILES', 'c6aa8cdcd3a091bedabeee552fcd108a69bbcde99fc74e7b3bcbfce288166052', '8a7be56c9a609fb7a416200769bc9a2edbe0bdb35c994546ae36dd7cc79f8587'),
    'application/pokegear/configure/pgconf_gra': ('files/application/pokegear/configure/pgconf_gra.mk', 'PGCONF_GRA_FILES', 'c73f29b7ddd2fba36379a645cd8ae520d682fe435b184ca5f8857d39a8fda07f', 'ba1dd2218128a79282fbc9a0372e4c7a0b048abf9355186c731835ed6d6aebae'),
    'application/pokegear/map/pgmap_gra': ('files/application/pokegear/map/pgmap_gra.mk', 'PGMAP_GRA_FILES', '998d72576c3eba64fd2b60ba32212faaca6ad5a28929942f0b2234d79202b698', '414feaab712d883406ee192e6cb47ca7d2f99c133d5802f060a543dd9a97d20c'),
    'application/pokegear/phone/pgphone_gra': ('files/application/pokegear/phone/pgphone_gra.mk', 'PGPHONE_GRA_FILES', 'f3f9a47b3ecdcd8b4b72a6cc729fda53724119225e8f32dc6abcd78e00e2bc26', '3f5110f62c768cda420ae5f3ac9bb4ccecfdbb5248757a58767aa629d39587fc'),
    'application/pokegear/radio/pgradio_gra': ('files/application/pokegear/radio/pgradio_gra.mk', 'PGRADIO_GRA_FILES', '1e10323bbbdc530f20f9fb7329110a1e0800d2022558ebc1e4e34f0091628d9c', '69d7f2c06d3f7f278255f6b7ad7e1cb9540a1fd1dc03bc6b62a4f0814622b7f6'),
    'application/voltorb_flip': ('files/application/voltorb_flip.mk', 'VOLTORB_FLIP_FILES', '676daab3f050617997a5c105c64f68676428e01fbee58126a39abda4ab9417cc', '71f46d1de98042666c423a07bd3960d66d163b20cea09797989ddf2d97a42163'),
    'data/mmodel/mmodel': ('files/data/mmodel/mmodel.mk', 'target:MMODEL_NARC', 'e907f8a08a4796a2a2c0599e132d30db9ad444ab7ab2b3a2337fe67a3f09d606', '5b3cea8503731d90af1104dcd7949cb59360cefcc35694f7aad599d6447945eb'),
    'demo/intro/intro': ('files/demo/intro/intro.mk', 'INTRO_DEMO_FILES', '256d82a1c7da551abbef8b3f4c36fcc8bcb82d93688d597cc9e2bf3f3735d27a', 'a23513fa97bb4add3124e11fe2f6b0b15b9735a4ab877dce928da8ea2808745a'),
    'demo/legend': ('files/demo/legend.mk', 'LEGEND_DEMO_FILES', '92addb43a4ce7b01c3d024a544a7369cfb7924e0c3e0063231c18cc58b05b351', '90046f155b4fb76fcfb90d0a947ec351c3d0918fe427548cc0d53db5eb557348'),
    'graphic/zukan_gra': ('files/graphic/zukan_gra.mk', 'ZUKAN_GRA_FILES', '014197293442f2f141b1ee49dbf16dd095301b12c5cb035dd52f89562b3ab05a', '9150fc1f0e4fad7eb0f85b1cb98652658e8637ffae85dd5fd71fda63b7c831a1'),
    'poketool/pokefoot/pokefoot': ('files/poketool/pokefoot/pokefoot.mk', 'POKEFOOT_FILES', 'e73e9c8149d06c4de8e0101ce6f9551f860411fec97d71b920aaa13e521d4984', 'a2e3bb4fdaa5a860aa703136cd96d7a2309e097b8bdfa9103f979965e14f5324'),
}
RULES_SHA256 = 'bf4168ecf7ee62072347b82a1a74bdfa66e28ad0ddcfc1061ca060be8502e0f8'


class Manifest:
    def __init__(self, root, text):
        self.root = root.resolve()
        self.text = text.replace('\\\n', ' ')
        self.variables = {'WORK_DIR': '.', 'shortname': 'gold'}
        for name, op, value in re.findall(r'^(\w+)\s*(:=|\+=)\s*([^\n]*)', self.text, re.M):
            self.variables[name] = (self.variables.get(name, '') + ' ' if op == '+=' else '') + value.strip()

    def expand(self, text, active=()):
        def expression(body):
            if ' ' in body:
                function, args = body.split(' ', 1)
                if function == 'wildcard':
                    pattern = self.expand(args, active)
                    return ' '.join(Path(p).relative_to(self.root).as_posix()
                                    for p in sorted(glob.glob(str(self.root / pattern))))
                if function == 'notdir':
                    return ' '.join(Path(p).name for p in self.expand(args, active).split())
                if function in ('addprefix', 'filter'):
                    first, values = self.expand(args, active).split(',', 1)
                    if function == 'addprefix':
                        return ' '.join(first + value for value in values.split())
                    pattern = re.escape(first).replace('%', '.*')
                    return ' '.join(value for value in values.split() if re.fullmatch(pattern, value))
                raise ValueError('Unsupported Make function: ' + body)
            name, colon, substitution = body.partition(':')
            if name in active or name not in self.variables:
                raise ValueError('Unknown/recursive Make variable: ' + name)
            value = self.expand(self.variables[name], (*active, name))
            if colon:
                old, new = substitution.split('=')
                pattern = re.escape(old).replace('%', '(.*)')
                def sub(word):
                    match = re.fullmatch(pattern, word)
                    return new.replace('%', match[1]) if match else word
                value = ' '.join(sub(word) for word in value.split())
            return value

        result = ''
        while '$(' in text:
            start = text.index('$(')
            level, end = 1, start + 2
            while level and end < len(text):
                if text.startswith('$(', end):
                    level += 1
                    end += 2
                elif text[end] == ')':
                    level -= 1
                    end += 1
                else:
                    end += 1
            if level:
                raise ValueError('Unclosed Make expression')
            result += text[:start] + expression(text[start + 2:end - 1])
            text = text[end:]
        if '$' in text:
            raise ValueError('Unsupported Make expansion: ' + text)
        return result + text

    def members(self, selector):
        if selector.startswith('target:'):
            variable = selector.removeprefix('target:')
            matches = re.findall(r'^\$\(' + re.escape(variable) + r'\): ([^\n]+)', self.text, re.M)
            if len(matches) != 1:
                raise ValueError('Ambiguous archive prerequisite list: ' + variable)
            value = self.expand(matches[0])
        else:
            value = self.expand('$(' + selector + ')')
        return [Path(p).name for p in value.split()]


def checked(path, digest):
    text = path.read_text()
    if hashlib.sha256(text.encode()).hexdigest() != digest:
        raise ValueError('Original asset recipe changed: ' + str(path))
    return text


def plan(root, relative):
    manifest_path, selector, digest, members_digest = ARCHIVES[relative]
    text = checked(root / manifest_path, digest)
    rules = checked(root / 'graphics_files_rules.mk', RULES_SHA256)
    manifest = Manifest(root, text)
    members = manifest.members(selector)
    aliases = {}
    # Original versioned archives may publish a selected binary under a neutral
    # member name. Stage a copy instead of creating the original in-tree symlink.
    for original, directory, neutral in re.findall(r'ln -sf (\S+) \$\((\w+)\)/(\S+)', text):
        original = manifest.expand(original)
        if (root / manifest.expand('$(' + directory + ')')).resolve() != root / 'files' / relative:
            raise ValueError('Versioned member uses an unexpected source directory')
        if original not in members:
            raise ValueError('Versioned member absent from prerequisites: ' + original)
        aliases[neutral] = original
        members[members.index(original)] = neutral
    if not members or len(set(members)) != len(members):
        raise ValueError('Empty/duplicate archive members: ' + relative)
    if hashlib.sha256("\n".join(members).encode()).hexdigest() != members_digest:
        raise ValueError("Original archive member inventory changed: " + relative)
    source = root / 'files' / relative
    steps = {}

    def flags(name, variable):
        found = []
        for group, options in re.findall(r'^\$\(([^)]+)\): ' + variable + r' = ([^\n]*)', rules, re.M):
            if group not in manifest.variables:
                continue
            paths = manifest.expand('$(' + group + ')').split()
            if name in [Path(p).name for p in paths]:
                found.append(options.split())
        if len(found) > 1:
            raise ValueError('Ambiguous conversion flags: ' + name)
        return found[0] if found else (['-nopad'] if variable == 'LZ_FLAGS' else [])

    def resource(name):
        if name in steps:
            return
        original = source / aliases.get(name, name)
        if original.is_file():
            step = {'name': name, 'kind': 'copy', 'input': str(original), 'flags': []}
        elif name.endswith('.lz'):
            raw = name[:-3]
            resource(raw)
            step = {'name': name, 'kind': 'gfx', 'input': raw, 'flags': flags(name, 'LZ_FLAGS'), 'generated': True}
        elif name.endswith(('.NCGR', '.NCLR')):
            candidates = [source / (name.rsplit('.', 1)[0] + ext) for ext in ('.png', '.pal')]
            candidates = [p for p in candidates if p.is_file() and (p.suffix != '.pal' or name.endswith('.NCLR'))]
            if len(candidates) != 1:
                raise ValueError('Missing/ambiguous original graphics input: ' + str(original))
            step = {'name': name, 'kind': 'gfx', 'input': str(candidates[0]), 'flags': flags(name, 'GFX_FLAGS')}
        elif name.endswith('.bin') and original.with_suffix('.json').is_file():
            template = source.with_suffix('.json.txt')
            if not template.is_file():
                raise ValueError('Missing original JSON template: ' + str(template))
            step = {'name': name, 'kind': 'json-asm', 'input': str(original.with_suffix('.json')), 'template': str(template), 'flags': []}
        else:
            raise ValueError('Missing original archive input: ' + str(original))
        steps[name] = step

    for name in members:
        resource(name)
    result = {'relative': relative, 'manifest': manifest_path, 'members': members, 'steps': list(steps.values())}
    if aliases:
        result['archive_relative'] = relative + '_gold'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps([plan(args.root.resolve(), relative) for relative in ARCHIVES]))


if __name__ == '__main__':
    main()
