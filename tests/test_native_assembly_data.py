import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cmake'))
"""Whole-member native records, aliases, relocations and mutable source storage."""
import subprocess
import os
import tempfile
import unittest
from unittest.mock import patch
import native_assembly_data as assembly

GAME=ROOT/'upstream/pokeheartgold'

class NativeDataTests(unittest.TestCase):
    def test_every_complete_reviewed_member(self):
        with tempfile.TemporaryDirectory(dir=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build'))) as directory:
            for original in assembly.REVIEWED_INPUTS:
                with self.subTest(original=original):
                    blocks=assembly.recipe(GAME,original)
                    source=Path(directory)/'data.S';obj=source.with_suffix('.o')
                    source.write_text(assembly.emit(GAME,original))
                    subprocess.run(['clang','-arch','arm64','-c',str(source),'-o',str(obj)],check=True,capture_output=True)
                    evidence=assembly.validate_object(obj,blocks)
                    self.assertTrue(evidence['validated'])
                    # Independent object corruption must be rejected.
                    section=next((s for s in evidence['sections'] if s['size'] and s['name']!='__bss'), None)
                    raw=bytearray(obj.read_bytes())
                    if section:
                        raw[section['offset']]^=1
                        expected_error='numeric data'
                    else:
                        # Pure BSS has no file-backed bytes. Corrupt its Mach-O
                        # section type instead; zero-fill ownership must be checked.
                        import struct
                        cursor=32
                        while cursor < len(raw):
                            command,size=struct.unpack_from('<II',raw,cursor)
                            if command==0x19:
                                for i in range(struct.unpack_from('<I',raw,cursor+64)[0]):
                                    at=cursor+72+i*80
                                    if raw[at:at+16].rstrip(b'\0')==b'__bss':
                                        struct.pack_into('<I',raw,at+64,0)
                                break
                            cursor+=size
                        expected_error='storage section type'
                    obj.write_bytes(raw)
                    with self.assertRaisesRegex(ValueError,expected_error):
                        assembly.validate_object(obj,blocks)

    def test_mixed_native_records_preserve_numeric_fields(self):
        blocks={b['symbol']:b for b in assembly.recipe(GAME,'asm/field_move_effects_data.o')}
        phases=blocks['gFlyLandingPhases']
        self.assertEqual(phases['pointers'],['sFlyLandingIdleSteps','sFlyLandingSteps'])
        self.assertEqual(phases['bytes'],[1,0,0,0,15,0,0,0])
        self.assertEqual(len(blocks['sCutInFlyerTakeOffSteps']['pointers']),2)
        self.assertEqual(blocks['gHealingMachineBallOffsets']['section'],'__data')
        self.assertEqual(len(blocks['gHealingMachineBallOffsets']['bytes']),72)
        self.assertEqual(blocks['gFlyLandingEffectTemplate']['native_items'][0],('bytes',[144,0,0,0,0,0,0,0]))
        self.assertEqual(blocks['gWaterfallEffectTemplate']['native_items'][0],('bytes',[0,4,0,0,224,2,0,0]))
        renderers=assembly.recipe(GAME,'asm/field_effect_renderers_data.o')[-1]
        layout,labels=assembly.reviewed_layout([renderers])
        self.assertEqual(len(layout['__const']['data']),24*24)
        self.assertEqual(len(layout['__const']['relocations']),46)
        self.assertEqual(layout['__const']['data'][-24:],bytes([23])+bytes(23))

    def test_mutable_pointer_and_bss(self):
        factory=assembly.recipe(GAME,'asm/battle_factory_setup_data.o')[0]
        self.assertEqual((factory['section'],factory['alignment'],factory['bytes']),('__data',8,[0]*8))
        encounter=assembly.recipe(GAME,'asm/encounter_effect_data.o')[-1]
        self.assertEqual((encounter['section'],encounter['alignment'],encounter['native_items']),('__bss',8,[('bytes',[0]*16)]))

    def test_billboard_record_native_stride(self):
        blocks=assembly.recipe(GAME,'asm/overlay_01_sprite_data.o')
        billboard=next(b for b in blocks if b['symbol']=='gSpriteBillboardInfos')
        layout,_=assembly.reviewed_layout([billboard])
        data=layout['__const']
        count=len(billboard['pointers'])
        self.assertEqual(len(data['data']),count*16)
        self.assertEqual(sorted(data['relocations']),list(range(8,count*16,16)))
        for i in range(count):
            self.assertEqual(data['data'][i*16+4:i*16+8],bytes(4))

    def test_offline_image_callback_and_menu_records(self):
        def block(obj,name):
            return next(b for b in assembly.recipe(GAME,obj) if b['symbol']==name)
        bag='asm/bag_app_data.o'
        actions=block(bag,'gItemActionFuncs')
        layout,_=assembly.reviewed_layout([actions])
        data=layout[actions['section']]
        self.assertEqual(len(data['data']),16*8)
        self.assertEqual(len(data['relocations']),14)
        self.assertEqual(data['data'][11*8:12*8],bytes(8))
        self.assertEqual(data['data'][13*8:14*8],bytes(8))
        self.assertEqual(block(bag,'gItemMenuCursorButtons')['section'],'__data')
        template=block(bag,'gOverlayTemplate_Bag')
        layout,_=assembly.reviewed_layout([template])
        self.assertEqual(len(layout['__const']['data']),32)
        self.assertEqual(template['pointers'],['Bag_Init','Bag_Main','Bag_Exit'])
        for obj,name,count in [('asm/apricorn_box_screens_data.o','gApricornBoxListMenus',2),
                               ('asm/safari_decoration_data.o','gSafariDecorationObjectGroups',4)]:
            layout,_=assembly.reviewed_layout([block(obj,name)])
            self.assertEqual(len(layout['__const']['data']),count*16)
            self.assertEqual(sorted(layout['__const']['relocations']),list(range(8,count*16,16)))

    def test_original_main_movement_records(self):
        blocks=assembly.recipe(GAME,'asm/map_object_movement_tables.o')
        for block in blocks:
            if block['symbol'].startswith('s') and block['symbol'].endswith('MovementCallbacks'):
                layout,_=assembly.reviewed_layout([block])
                data=layout['__const']
                self.assertEqual(len(data['data']),40)
                self.assertEqual(sorted(data['relocations']),[8,16,24,32])
                self.assertEqual(data['data'][4:8],bytes(4))
        directions=next(b for b in blocks if b['symbol']=='gMovementsByDirection')
        layout,_=assembly.reviewed_layout([directions])
        self.assertEqual(len(layout['__const']['data']),23*8)
        self.assertEqual(layout['__const']['data'][-8:],bytes(8))

    def test_palpad_native_sprite_templates_and_alias(self):
        blocks={b['symbol']:b for b in assembly.recipe(GAME,'asm/palpad_data.o')}
        arrow=blocks['gPalPadArrowSpriteTemplates'];scale=blocks['gPalPadArrowTemplateScale']
        layout,labels=assembly.reviewed_layout([arrow,scale])
        self.assertEqual(len(layout['__data']['data']),2*56)
        self.assertEqual(labels['_gPalPadArrowTemplateScale'],('__data',28))
        self.assertEqual(layout['__data']['data'][:16],bytes(16))
        self.assertEqual(layout['__data']['data'][56:72],bytes(16))
        for name,size in [('gPalPadDeleteEffectSpriteTemplate',56),('gPalPadCursorSpriteTemplate',60)]:
            self.assertEqual(sum(len(v) for k,v in blocks[name]['native_items']),size)
        callbacks=blocks['gPalPadRosterScrollCallbacks']
        layout,_=assembly.reviewed_layout([callbacks])
        self.assertEqual(len(layout['__data']['data']),4*8)
        self.assertEqual(sorted(layout['__data']['relocations']),[0,16])

    def test_all_original_movement_step_arrays(self):
        blocks=[]
        for member in ['unk_data_020FD978','map_object_movement_command_steps']:
            blocks+=assembly.recipe(GAME,'asm/'+member+'.o')
        self.assertEqual({b['symbol'] for b in blocks},{'gMovementCmdSteps_%03d'%i for i in range(113)})
        for block in blocks:
            layout,_=assembly.reviewed_layout([block])
            data=layout['__const'];count=len(block['pointers'])
            self.assertGreaterEqual(count,2)
            self.assertEqual(len(data['data']),count*8)
            self.assertEqual(sorted(data['relocations']),list(range(0,count*8,8)))

    def test_source_drift_and_unsupported_expressions_fail(self):
        with patch.object(assembly,'digest',return_value='changed'):
            with self.assertRaisesRegex(ValueError,'source/consumer changed'):
                assembly.recipe(GAME,'asm/field_move_effects_data.o')
        for value in ['callback','call(1)','1 / 2','__import__("os")']:
            with self.assertRaises(ValueError):assembly.numeric_expression(value)

if __name__=='__main__':unittest.main()
