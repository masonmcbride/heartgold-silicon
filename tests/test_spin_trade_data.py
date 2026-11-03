"""Complete original provider data, relocations and actual native consumer layouts."""
from pathlib import Path
import struct
import subprocess
import sys
import unittest
import test_shared_provider_native as provider

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cmake'))
import native_assembly_data as assembly
from native_data_ir import parse,raw_layout

class DataTests(unittest.TestCase):
    setUp=provider.ProviderTests.setUp
    run_code=provider.ProviderTests.run_code

    def test_complete_members_and_unchanged_scalar_aliases(self):
        game=ROOT/'upstream/pokeheartgold'
        for original in ['asm/spin_trade_data.o','asm/spin_trade_flow_data.o','lib/NitroDWC/asm/dwc_account_data.o']:
            blocks=assembly.recipe(game,original)
            source=self.work/(Path(original).stem+'.S');source.write_text(assembly.emit_reviewed(blocks))
            obj=source.with_suffix('.o')
            subprocess.run(['clang','-arch','arm64','-c',str(source),'-o',str(obj)],check=True,capture_output=True)
            self.assertTrue(assembly.validate_object(obj,blocks)['validated'])
            if original=='asm/spin_trade_data.o':
                old_sections,labels,_=raw_layout(parse(game/'asm/spin_trade_data.s'))
                raw,sections,_=assembly.read_object(obj)
                # Independently inspect the two raw cross-label reads at +28/+32
                # performed by the original consumer at indices 7 and 8.
                section=next(s for s in sections if s['name']=='__const')
                data=raw[section['offset']:section['offset']+section['size']]
                old=old_sections['.rodata'];base=labels['gSpinTradeBonusRanges2P'][1]
                self.assertEqual(data[:44],old[base:base+44])
                self.assertEqual(struct.unpack_from('<2I',data,28),struct.unpack_from('<2I',old,base+28))
                # Complete member: every original label, including scalar-only
                # interior aliases, is present; no table-only partial provider.
                self.assertEqual({b['symbol'] for b in blocks},{b.symbol for b in parse(game/'asm/spin_trade_data.s')})

    def test_actual_native_layouts(self):
        game=ROOT/'upstream/pokeheartgold'
        app=(game/'src/application/spin_trade/spin_trade_app.c').read_text()
        types=provider.block(app,'typedef struct SpinTradeAngleRange {')+' SpinTradeAngleRange;\n'
        types+=provider.block(app,'typedef struct SpinTradeBonusAreas {')+' SpinTradeBonusAreas;\n'
        self.run_code('''#include "global.h"
#include "overlay_manager.h"
#include "bg_window.h"
#include "gf_gfx_planes.h"
#include "sprite_system.h"
#include <stddef.h>
'''+types+'''
_Static_assert(sizeof(OverlayManagerTemplate)==32 && offsetof(OverlayManagerTemplate,ovy_id)==24,"template");
_Static_assert(sizeof(SpinTradeBonusAreas)==16 && offsetof(SpinTradeBonusAreas,ranges)==8,"bonus record");
_Static_assert(sizeof(SpinTradeAngleRange)==4,"packed angle pair");
_Static_assert(sizeof(WindowTemplate)==8,"window bytes");
_Static_assert(sizeof(BgTemplate)==28,"background bytes");
_Static_assert(sizeof(GraphicsModes)==16 && sizeof(GraphicsBanks)==40,"graphics scalar bytes");
_Static_assert(sizeof(OamCharTransferParam)==20 && sizeof(OamManagerParam)==32,"OAM scalar bytes");
_Static_assert(sizeof(SpriteResourceCountsListUnion)==24,"resource count bytes");
int main(void){return 0;}
''')

if __name__=='__main__':unittest.main()
