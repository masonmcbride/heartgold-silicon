"""Complete original backup-manager members, byte layouts and pure operations.

No NVRAM, PXI, authentication or startup provider is fabricated. Unused effects
are removed by the ordinary linker for this bounded executable test only.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import test_shared_provider_native as provider

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'cmake'))
import native_assembly_data as assembly
from native_data_ir import parse, raw_layout


class BackupTests(unittest.TestCase):
    setUp = provider.ProviderTests.setUp
    run_code = provider.ProviderTests.run_code

    def test_original_complete_members_and_layout(self):
        game = ROOT/'upstream/pokeheartgold'
        original = 'lib/NitroDWC/asm/dwc_bm_data.o'
        blocks = assembly.recipe(game, original)
        source = self.work/'backup.S'
        source.write_text(assembly.emit_reviewed(blocks))
        obj = self.work/'backup.o'
        subprocess.run(['clang', '-arch', 'arm64', '-c', str(source), '-o', str(obj)], check=True, capture_output=True)
        self.assertTrue(assembly.validate_object(obj, blocks)['validated'])
        sections, labels, relocations = raw_layout(parse(game/(original[:-2]+'.s')))
        self.assertEqual(len(sections['.bss']), 88)
        self.assertEqual(len(sections['.rodata']), 28)
        self.assertEqual(labels['Wifi'][1], 12)
        self.assertEqual(labels['Work'][1], 56)
        self.assertFalse(relocations)
        objects = [obj]
        for stem in ['dwc_bm', 'dwc_bm_init']:
            output = self.work/(stem+'.o')
            command = [*self.flags, '-c', str(game/'lib/NitroDWC/src'/(stem+'.c')),
                       '-o', str(output), '-fsanitize=address,undefined', '-fno-sanitize-recover=all']
            r = subprocess.run(command, cwd=self.build, text=True, capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            objects.append(output)
        result = self.run_code('''#include "dwc/dwc_bm_internal.h"
#include <stddef.h>
#include <stdio.h>
_Static_assert(sizeof(DwcBackupPage)==256,"serialized page");
_Static_assert(offsetof(DwcBackupPage,crc)==254,"CRC range");
_Static_assert(offsetof(DwcBackupPage,wifiInfo)==240,"packed ID");
_Static_assert(sizeof(DwcBackupWork)==1792,"work allocation");
_Static_assert(sizeof(DwcBmNvramState)==12,"state extent");
_Static_assert(offsetof(DwcBmNvramState,ready)==4,"ready alias");
_Static_assert(offsetof(DwcBmNvramState,backupAddress)==8,"address alias");
_Static_assert(offsetof(DwcWiFiInfo,pseudoUserId)==8,"ID offset");
_Static_assert(offsetof(DwcWiFiInfo,random)==16,"random offset");
_Static_assert(offsetof(DwcWiFiInfo,salt)==18,"salt offset");
int main(void){
 unsigned rng=1;
 for(int i=0;i<10000;i++){
  rng=rng*1664525u+1013904223u;
  DwcWiFiInfo a={0},b={0};
  a.userId=(((u64)rng<<32)|~rng)&0x7ffffffffffULL;
  a.pseudoUserId=(((u64)~rng<<32)|rng)&0x7ffffffffffULL;
  a.random=rng&1023;a.salt=rng>>16;
  DWCi_BACKUPlConvWifiInfo(&a);DWCi_BM_GetWiFiInfo(&b);
  CHECK(a.userId==b.userId && a.pseudoUserId==b.pseudoUserId);
  CHECK(a.random==b.random && a.salt==b.salt);
  CHECK(DWCi_BACKUPlGetWifi()==Wifi);
 }
 for(unsigned cidr=0;cidr<32;cidr++){
  u8 mask[4];DWCi_BACKUPlConvMaskAddr(cidr,mask);
  CHECK(DWCi_BACKUPlConvMaskCidr(mask)==cidr);
 }
 for(int first=0;first<256;first++){
  u8 ip[4]={(u8)first,0,0,1};
  CHECK(!!DWC_BACKUPlCheckAddress(ip)==(first>=1 && first<=223 && first!=127));
 }
 u8 ssid[32]={0};CHECK(!DWC_BACKUPlCheckSsid(ssid));
 for(int i=0;i<32;i++){ssid[i]=1;CHECK(DWC_BACKUPlCheckSsid(ssid));ssid[i]=0;}
 DwcBackupWork work;memset(&work,0xa5,sizeof work);
 for(int page=0;page<4;page++){
  initPage(&work,page);
  for(int b=0;b<256;b++)CHECK(((u8*)&work.pages[page])[b]==(b==231?255:0));
 }
 for(int b=1024;b<sizeof work;b++)CHECK(((u8*)&work)[b]==0xa5);
 puts("PASS 10000 packed-ID roundtrips; 32 defined CIDRs; 256 address classes; four exact page clears");
 return 0;
}''', extras=[*objects, self.build/'libntr/libntr_mi.a', self.build/'libntr/libntr_sim_state.a'])
        # CIDR 32 is deliberately excluded: the original C shifts u32 by 32.
        # This test neither changes that algorithm nor certifies that input.
        directory = self.build/'dwc-backup-native'
        directory.mkdir(exist_ok=True)
        for path in self.work.iterdir():
            if path.is_file(): shutil.copy2(path, directory/path.name)
        (directory/'result.txt').write_text(result)
        self.assertIn('PASS 10000', result)


if __name__ == '__main__':
    unittest.main()
