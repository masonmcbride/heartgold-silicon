"""Original socket and bucket functions mutate one measured native BSS span."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cmake'))
import native_sources as native
import dwc_native_data as dwc
from native_assembly_data import emit_reviewed,validate_object


class SocketStorage(unittest.TestCase):
    def test_original_consumers(self):
        build=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build')).resolve()
        game=ROOT/'upstream/pokeheartgold'
        entry=next(e for e in json.loads((build/'compile_commands.json').read_text())
                   if e['file'].endswith('/native/lib/NitroDWC/src/gs_platform.c'))
        flags=shlex.split(entry['command']);index=flags.index('-o');del flags[index:index+2]
        flags=[f for f in flags if f not in ('-c',entry['file'])]
        abi=dwc.read_abi(build/'CMakeFiles/heartgold_dwc_data_abi.dir/dwc-native/abi.c.o')
        blocks,report=dwc.make(game,abi)
        region=next(r for r in report['regions'] if r.get('bss')=='ov00_0221B1AC')
        self.assertEqual(region['original_aliases'],dict(ov00_0221B1AC=0,ov00_0221B1B4=8,
                         ov00_0221B1C4=24,ov00_0221B1D8=44,ov00_0221B1F0=68,ov00_0221B1F8=76))
        self.assertEqual(region['native_aliases'],dict(ov00_0221B1AC=0,ov00_0221B1B4=16,
                         ov00_0221B1C4=48,ov00_0221B1D8=72,ov00_0221B1F0=104,ov00_0221B1F8=120))
        self.assertEqual(region['native_size'],128)
        selected=[b for b in blocks['OVY_0'] if b['symbol'] in region['native_aliases']]
        self.assertEqual(len(selected),6)
        with tempfile.TemporaryDirectory(dir=build) as temp:
            work=Path(temp)
            def run(args):
                r=subprocess.run(list(map(str,args)),capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            assembly=work/'storage.S';assembly.write_text(emit_reviewed(selected))
            obj=work/'storage.o';run(['clang','-c',assembly,'-o',obj]);validate_object(obj,selected)
            objects=[obj]
            for name in ('gs_platform','gp_api','persist_data'):
                relative='lib/NitroDWC/src/'+name+'.c';source=work/(name+'.c')
                source.write_text(native.adapt(relative,(game/relative).read_text(),game))
                output=source.with_suffix('.o')
                run([*flags,'-O2','-fsanitize=address,undefined','-fno-sanitize-recover=all','-c',source,'-o',output]);objects.append(output)
            # Use the real original IPv4 conversion, with deterministic host-ID
            # input at its hardware boundary. No production behavior is mocked.
            source=work/'soc.c';source.write_text((game/'lib/NitroWiFi/src/soc_inet.c').read_text())
            output=source.with_suffix('.o');run([*flags,'-c',source,'-o',output]);objects.append(output)
            declaration=native.native_socket_state((game/'lib/NitroDWC/src/gs_platform.c').read_text())[1]
            code='#include <stdint.h>\n#include <stddef.h>\n#include <assert.h>\n#include <string.h>\n#include <stdlib.h>\ntypedef int16_t s16;typedef uint32_t u32;typedef uint8_t u8;\n'+declaration
            code+='''
#include <dwc/persist_internal.h>
#define assert(x) do { if (!(x)) __builtin_trap(); } while (0)
extern Ov00SocketState ov00_0221B1AC;
extern char ov00_0221B1B4[],ov00_0221B1C4[],ov00_0221B1D8[],ov00_0221B1F8[];
extern BucketGlobals ov00_0221B1F0;
char sStr_localhost[]="localhost";
static u32 host=0x7f000001;
u32 SOCL_GetHostID(void){return host;}
extern void *getlocalhost(void);
extern int gsSocketCheckResult(int,int),gsSocketGetLastError(void);
extern int *bint(int);extern double *bdouble(double);
int main(void){
 assert((uintptr_t)&ov00_0221B1AC>UINT32_MAX);
 assert((void*)ov00_0221B1B4==(void*)&ov00_0221B1AC.hName);
 assert((void*)ov00_0221B1C4==(void*)&ov00_0221B1AC.addr);
 assert((void*)ov00_0221B1D8==(void*)ov00_0221B1AC.addrList);
 assert((void*)ov00_0221B1F8==(void*)&ov00_0221B1F0.doubleValue);
 assert(ov00_0221B1AC.aliases[0]==NULL);
 assert(gsSocketCheckResult(-9,-1)==-1 && gsSocketGetLastError()==-9);
 assert(getlocalhost()==ov00_0221B1B4);
 assert(*(char**)ov00_0221B1B4==sStr_localhost);
 assert(ov00_0221B1AC.hAliases==ov00_0221B1AC.aliases && !*ov00_0221B1AC.hAliases);
 assert(gsSocketGetLastError()==-9);
 assert(ov00_0221B1AC.hAddrType==2 && ov00_0221B1AC.hLength==4);
 assert(ov00_0221B1AC.hAddrList==ov00_0221B1AC.addrList);
 assert(ov00_0221B1AC.addrList[0]==ov00_0221B1C4 && !ov00_0221B1AC.addrList[1]);
 assert(!memcmp(ov00_0221B1C4,"\\x7f\\0\\0\\1",4));
 assert(bint(137)==&ov00_0221B1F0.intValue && *bint(-42)==-42);
 assert(bdouble(2.75)==&ov00_0221B1F0.doubleValue);
 double v;memcpy(&v,ov00_0221B1F8,8);assert(v==2.75);
 v=4.5;memcpy(ov00_0221B1F8,&v,8);assert(ov00_0221B1F0.doubleValue==4.5);
 char *high=malloc(8);assert((uintptr_t)high>UINT32_MAX);
 ov00_0221B1AC.addrList[0]=high;assert(*(char**)ov00_0221B1D8==high);free(high);
 host=0;assert(getlocalhost()==NULL && ov00_0221B1AC.addr==0);
 memset(&ov00_0221B1AC,0,sizeof ov00_0221B1AC);
 assert(!*(char**)ov00_0221B1B4 && !*(char**)ov00_0221B1D8 && gsSocketGetLastError()==0);
 host=0x01020304;assert(getlocalhost()==ov00_0221B1B4);
 assert(!memcmp(ov00_0221B1C4,"\\1\\2\\3\\4",4));return 0;
}
'''
            source=work/'check.c';source.write_text(code);exe=work/'check'
            run([*flags,'-O2','-fsanitize=address,undefined','-fno-sanitize-recover=all',source,*objects,'-Wl,-dead_strip','-o',exe]);run([exe])


if __name__=='__main__':unittest.main()
