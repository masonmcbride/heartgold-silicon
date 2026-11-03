"""Original data bytes, relocation bindings and native consumer layout regressions."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / 'upstream/pokeheartgold'
sys.path.insert(0, str(ROOT / 'cmake'))
import native_assembly_data as assembly
from native_data_ir import parse, raw_layout, native_blocks

MEMBERS = (
    'pokeathlon_course_data', 'pokeathlon_event_data',
    'pokeathlon_hurdle_dash_rodata', 'pokeathlon_relay_run_map_rodata',
    'pokeathlon_pennant_capture_rodata', 'pokeathlon_disc_catch_rodata',
    'pokeathlon_disc_catch_cpu_rodata', 'pokeathlon_goal_roll_rodata',
    'pokeathlon_goal_roll_cpu_rodata', 'pokeathlon_ring_drop_rodata',
    'wobbuffet_pop_data', 'wobbuffet_pop_balloon_mesh_data',
    'wobbuffet_pop_scene_data', 'record_mixing_data',
    'nintendo_wfc_connect_unused_data', 'wifi_plaza_lobby_data',
    'plaza_game_data', 'battle_main_data', 'battle_controller_opponent_data',
    'overlay_12_battle_command', 'battle_anim_data', 'battle_menu_data',
    'wifi_plaza_map_rodata', 'lock_capsule_card_data', 'nitrocrypto_data',
)

class ClosureDataTests(unittest.TestCase):
    def work(self):
        binary = Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT / 'build'))
        temporary = tempfile.TemporaryDirectory(dir=binary)
        self.addCleanup(temporary.cleanup)
        return Path(temporary.name)

    def test_addends_require_explicit_review_and_preserve_relocations(self):
        directory = self.work()
        source = directory / 'addends.s'
        source.write_text('.rodata\nlocal:\n.byte 1,2,3,4\n'
                          '.data\n.public table\ntable:\n.word local + 3, external - 2\n')
        layout = {'table': {'pointers': [0, 4]}}
        with self.assertRaisesRegex(ValueError, 'addend requires ABI review'):
            native_blocks(source, layout)
        layout['table']['pointer_addends'] = {'0': 3, '4': -2}
        blocks = native_blocks(source, layout)
        source.write_text(assembly.emit_reviewed(blocks))
        obj = source.with_suffix('.o')
        subprocess.run(['clang', '-arch', 'arm64', '-c', str(source), '-o', str(obj)], check=True)
        self.assertTrue(assembly.validate_object(obj, blocks)['validated'])
        source.write_text('.data\ntable:\n.word external + 4, external - 2\n')
        with self.assertRaisesRegex(ValueError, 'addend requires ABI review'):
            native_blocks(source, layout)

    def test_original_members_emit_and_validate(self):
        directory = self.work()
        for member in MEMBERS:
            with self.subTest(member=member):
                original = 'asm/' + member + '.o'
                blocks = assembly.recipe(GAME, original)
                source = directory / (member + '.S')
                obj = source.with_suffix('.o')
                source.write_text(assembly.emit_reviewed(blocks))
                subprocess.run(['clang', '-arch', 'arm64', '-c', str(source), '-o', str(obj)], check=True)
                self.assertTrue(assembly.validate_object(obj, blocks)['validated'])

    def test_numeric_pokeathlon_tables_retain_all_original_bytes(self):
        for member in MEMBERS[2:10]:
            original = GAME / ('asm/' + member + '.s')
            sections, _, references = raw_layout(parse(original))
            self.assertFalse(references)
            blocks = assembly.recipe(GAME, 'asm/' + member + '.o')
            self.assertEqual(bytes(v for b in blocks for v in b['bytes']), bytes(sections['.rodata']))
            self.assertFalse(any(b['pointers'] for b in blocks))

    def test_native_consumer_structures(self):
        binary = Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT / 'build'))
        entries = json.loads((binary / 'compile_commands.json').read_text())
        entry = next(e for e in entries if e['file'].endswith('/pokeathlon/pokeathlon_course.c'))
        args = entry.get('arguments') or shlex.split(entry['command'])
        command = []
        skip = False
        for arg in args:
            if skip:
                skip = False
            elif arg == '-o':
                skip = True
            elif arg != '-c' and arg != entry['file']:
                command.append(arg)
        directory = self.work()
        source = directory / 'consumer.c'
        source.write_text('''#include <stddef.h>
#include "overlay_manager.h"
#include "pokeathlon/pokeathlon_course_internal.h"
#include "pokeathlon/pokeathlon_circle_push.h"
#include "communication_command.h"
#include "record_mixing/record_mixing_exchange.h"
#include "application/main_menu/wonder_card_album.h"
_Static_assert(sizeof(WonderCardTextBox) == 56, "card box stride");
_Static_assert(offsetof(WonderCardTextBox, func) == 40, "card callback");
_Static_assert(sizeof(OverlayManagerTemplate) == 32, "overlay template");
_Static_assert(offsetof(OverlayManagerTemplate, ovy_id) == 24, "overlay ID");
_Static_assert(sizeof(PokeathlonCourseEvent) == 40, "course event");
_Static_assert(offsetof(PokeathlonCourseEvent, sendsOwnResult) == 32, "result flag");
_Static_assert(sizeof(PokeathlonCourseCmd) == 24, "course command");
_Static_assert(sizeof(CommCommand) == 24, "communication command");
_Static_assert(sizeof(RecordMixingHandler) == 24, "record mixing handler");
_Static_assert(sizeof(PokeathlonCirclePushContact) == 24, "contact stride");
_Static_assert(sizeof(gPokeathlonCirclePushContacts) == 3456, "contact storage");
''')
        subprocess.run([*command, '-fsyntax-only', str(source)], cwd=entry['directory'], check=True, capture_output=True)

if __name__ == '__main__':
    unittest.main()
