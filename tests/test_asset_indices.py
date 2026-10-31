"""Check real original archive/index outputs, manifest drift and a clean consumer."""
import argparse
import fnmatch
import importlib.util
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / 'upstream/pokeheartgold'
spec = importlib.util.spec_from_file_location('manifest', ROOT / 'cmake/asset_manifest.py')
manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest)
BUILD = None
TOOL = None


def records(path):
    data = path.read_bytes()
    assert data[:4] == b'NARC'
    cursor, entries, payload = struct.unpack_from('<H', data, 12)[0], None, None
    while cursor < len(data):
        magic, size = struct.unpack_from('<4sI', data, cursor)
        if magic == b'BTAF':
            count = struct.unpack_from('<H', data, cursor + 8)[0]
            entries = [struct.unpack_from('<II', data, cursor + 12 + i * 8) for i in range(count)]
        if magic == b'GMIF':
            payload = data[cursor + 8:cursor + size]
        cursor += size
    assert entries is not None and payload is not None
    return [payload[start:end] for start, end in entries]


def definitions(path):
    return {name: int(value) for name, value in re.findall(r'^#define (NARC_\w+) (\d+)$', path.read_text(), re.M)}


class AssetIndices(unittest.TestCase):
    def test_original_indices_records_and_reproducibility(self):
        for relative in manifest.ARCHIVES:
            with self.subTest(archive=relative):
                plan = manifest.plan(GAME, relative)
                original = GAME / 'files' / relative
                stage = BUILD / 'generated/files' / relative
                explicit = original / '.narcorder'
                order = explicit.read_text().splitlines() if explicit.exists() else []
                order = [name.strip() for name in order if name.strip()]
                expected = order + sorted(set(plan['members']) - set(order))
                # Independent membership check: the entire staged directory,
                # after the original metadata rules, must equal the manifest.
                ignores = ['.*ignore', '.*keep', '.*order']
                if (original / '.narcignore').exists():
                    ignores += (original / '.narcignore').read_text().splitlines()
                actual = {p.name for p in stage.iterdir() if p.is_file()
                          and not any(fnmatch.fnmatchcase(p.name, rule) for rule in ignores)}
                self.assertEqual(actual | set(order), set(expected))
                archive = BUILD / 'generated/files' / (plan.get('archive_relative', relative) + '.narc')
                self.assertEqual(records(archive), [(stage / name).read_bytes() for name in expected])
                wanted = {'NARC_' + stage.name + '_' + re.sub(r'\W', '_', name): i
                          for i, name in enumerate(expected)}
                self.assertEqual(definitions(stage.with_suffix('.naix')), wanted)
                counts = re.findall(r'^#define \w+_COUNT (\d+)$', stage.with_suffix('.naix').read_text(), re.M)
                self.assertEqual(list(map(int, counts)), [len(expected)])
                if 'archive_relative' in plan:
                    selected = original / 'zukan_hw_data_1_gold.bin'
                    self.assertEqual((stage / 'zukan_hw_data_1.bin').read_bytes(), selected.read_bytes())
                with tempfile.TemporaryDirectory(dir=BUILD) as directory:
                    repacked = Path(directory) / (stage.name + '.narc')
                    command = [str(TOOL), '-cf', str(repacked), '--index-namespace', str(stage)]
                    subprocess.run(command, check=True, capture_output=True)
                    first = repacked.read_bytes(), repacked.with_suffix('.naix').read_bytes()
                    subprocess.run(command, check=True, capture_output=True)
                    self.assertEqual(first, (repacked.read_bytes(), repacked.with_suffix('.naix').read_bytes()))
                    self.assertEqual(first[0], archive.read_bytes())
                    self.assertEqual(definitions(repacked.with_suffix('.naix')), wanted)

    def test_json_records_independently(self):
        relative = 'data/mmodel/mmodel'
        for source in sorted((GAME / 'files' / relative).glob('*.json')):
            entries = json.loads(source.read_text())['data']
            expected = struct.pack('<I', len(entries))
            expected += b''.join(struct.pack('<H', entry['unk0']) for entry in entries)
            expected += bytes(entry['unk1'] for entry in entries)
            expected += bytes(entry['unk2'] for entry in entries)
            self.assertEqual((BUILD / 'generated/files' / relative / source.with_suffix('.bin').name).read_bytes(), expected)
        source = GAME / 'files/application/zukanlist/zkn_data/zukan_enc.json'
        data = json.loads(source.read_text())
        expected = [bytes(entry['unk_' + str(i)] for entry in data['dungeons'] for i in range(4))]
        expected.append(b''.join(bytes([entry['unk_' + str(i)] for i in range(4)] + entry['unk_4'])
                                 for entry in data['overworlds']))
        # JSONPROC uses nlohmann::json/std::map iteration, hence lexical keys.
        for method in sorted(data['encounters']):
            for mon in sorted(data['encounters'][method]):
                maps = data['encounters'][method][mon]
                if isinstance(maps, dict):
                    maps = maps['GOLD']
                expected.append(b''.join(struct.pack('<I', value) for value in maps))
        base = BUILD / 'generated/files/application/zukanlist/zkn_data/zukan_enc'
        self.assertEqual(records(base.with_name('zukan_enc_gold.narc')), expected)
        enum = re.findall(r'NARC_zukan_enc_zukan_enc_(\d+) = (\d+)', base.with_suffix('.naix').read_text())
        self.assertEqual([(int(a), int(b)) for a, b in enum], [(i, i) for i in range(len(expected))])
        versioned = base.with_name('zukan_enc_gold.naix').read_text()
        self.assertEqual(base.with_suffix('.naix').read_text(), versioned.replace('_gold', ''))

    def test_flags_drift_and_unavailable_inputs(self):
        puzzle = manifest.plan(GAME, 'application/annon/puzzle_gra')
        flags = {step['name']: step['flags'] for step in puzzle['steps']}
        self.assertEqual(flags['puzzle_gra_00000001.NCGR'], ['-clobbersize', '-version101'])
        voltorb = manifest.plan(GAME, 'application/voltorb_flip')
        self.assertEqual(next(s['flags'] for s in voltorb['steps'] if s['name'].endswith('00000002.NCGR.lz')), ['-nopad', '-extfmt'])
        relative = 'demo/intro/intro'
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            root = Path(directory)
            shutil.copytree(GAME / 'files/demo/intro', root / 'files/demo/intro')
            shutil.copyfile(GAME / 'graphics_files_rules.mk', root / 'graphics_files_rules.mk')
            member = root / 'files' / relative / manifest.plan(root, relative)['members'][0]
            member.unlink()
            with self.assertRaisesRegex(ValueError, 'Missing'):
                manifest.plan(root, relative)
            path = root / 'files/demo/intro/intro.mk'
            path.write_text(path.read_text() + '\n# upstream drift\n')
            with self.assertRaisesRegex(ValueError, 'recipe changed'):
                manifest.plan(root, relative)
        relative = 'poketool/pokefoot/pokefoot'
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            root = Path(directory)
            shutil.copytree(GAME / 'files/poketool/pokefoot', root / 'files/poketool/pokefoot')
            shutil.copyfile(GAME / 'graphics_files_rules.mk', root / 'graphics_files_rules.mk')
            manifest.plan(root, relative)
            source = next((root / 'files' / relative).glob('*.png'))
            shutil.copyfile(source, source.with_name('pokefoot_extra.png'))
            with self.assertRaisesRegex(ValueError, 'inventory changed'):
                manifest.plan(root, relative)
        with tempfile.TemporaryDirectory(prefix='source path with spaces ', dir=BUILD) as directory:
            root = Path(directory)
            (root / 'files').mkdir()
            (root / 'files/input.json').write_text('{}')
            reader = manifest.Manifest(root, 'DATA := $(WORK_DIR)/files\nITEMS := $(wildcard $(DATA)/*.json)')
            self.assertEqual(reader.expand('$(ITEMS)'), 'files/input.json')
        self.assertRaisesRegex(ValueError, 'Unsupported Make function',
            manifest.Manifest(GAME, '').expand, '$(shell true)')

    def test_encounter_template_and_recipe_drift(self):
        spec = importlib.util.spec_from_file_location('native', ROOT / 'cmake/native_sources.py')
        native = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(native)
        source = GAME / 'files/application/zukanlist/zkn_data/zukan_enc.json.txt'
        original = source.read_text()
        generated = native.asset_types('zukan-enc-template', original, source)
        self.assertEqual(generated, original.replace(', @object', ', %object'))
        with self.assertRaisesRegex(ValueError, 'recipe changed'):
            native.asset_types('zukan-enc-template', original + '\n# drift', source)
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            template = Path(directory) / source.name
            template.write_text(original)
            recipe = source.with_name('zukan_enc.mk')
            (template.with_name(recipe.name)).write_text(recipe.read_text() + '\n# drift')
            with self.assertRaisesRegex(ValueError, 'recipe changed'):
                native.asset_types('zukan-enc-template', original, template)

    def test_clean_build_generates_before_consumer(self):
        # A fresh parent project uses the real recipes and compiles all generated headers.
        # No prior build outputs are copied or referenced by the consumer.
        with tempfile.TemporaryDirectory(prefix='index dependencies ', dir=BUILD) as directory:
            directory = Path(directory)
            headers = [relative + '.naix' for relative in manifest.ARCHIVES]
            headers.append('application/zukanlist/zkn_data/zukan_enc.naix')
            (directory / 'consumer.c').write_text(''.join('#include "' + h + '"\n' for h in headers) + 'int main(void) { return 0; }\n')
            (directory / 'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.20)
project(IndexDependencyCheck C CXX)
add_subdirectory("''' + ROOT.as_posix() + '''" heartgold)
add_executable(index_consumer consumer.c)
target_include_directories(index_consumer PRIVATE "${CMAKE_BINARY_DIR}/heartgold/generated/files")
add_dependencies(index_consumer heartgold_overlay_index_assets)
''')
            log = BUILD / 'asset-index-clean-build.log'
            with log.open('w') as output:
                for command in ([ 'cmake', '-S', str(directory), '-B', str(directory / 'out') ],
                                [ 'cmake', '--build', str(directory / 'out'), '--target', 'index_consumer', '-j8' ]):
                    subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, check=True)
            self.assertEqual(len(re.findall(r'Generating [^\n]*zukan_hw_data_gold\.narc,', log.read_text())), 1)
            subprocess.run([str(directory / 'out/index_consumer')], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', required=True, type=Path)
    parser.add_argument('--tool', required=True, type=Path)
    args, rest = parser.parse_known_args()
    BUILD, TOOL = args.build.resolve(), args.tool.resolve()
    unittest.main(argv=[__file__, *rest])
