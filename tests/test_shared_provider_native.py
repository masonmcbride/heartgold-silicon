"""Native original provider arithmetic and reproducible unsupported consumer views."""
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/'upstream/pokeheartgold'
sys.path.insert(0,str(ROOT/'cmake'))
import native_sources as native
import native_assembly_data as assembly
from native_data_ir import native_blocks, parse, raw_layout


def block(text,start):
    begin=text.index(start);brace=text.index('{',begin);depth=1;end=brace+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[begin:end]+'\n'

class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.build=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build')).resolve()
        temp=tempfile.TemporaryDirectory(dir=self.build);self.addCleanup(temp.cleanup);self.work=Path(temp.name)
        entry=next(e for e in json.loads((self.build/'compile_commands.json').read_text()) if e['file'].endswith('/soc_inet.c'))
        args=entry.get('arguments') or shlex.split(entry['command']);i=args.index('-o');del args[i:i+2]
        self.flags=[a for a in args if a not in ['-c',entry['file']] and not a.startswith('-std=')]

    def run_code(self,text,cpp=False,extras=()):
        source=self.work/('probe.cpp' if cpp else 'probe.c');source.write_text(text.replace("int main(", "#define CHECK(x) do { if (!(x)) __builtin_trap(); } while (0)\nint main("));exe=self.work/'probe'
        command=[*self.flags,'-x','c++' if cpp else 'c','-std=c++17' if cpp else '-std=c11',str(source),'-x','none',*map(str,extras),'-o',str(exe),'-Wl,-dead_strip','-fsanitize=address,undefined','-fno-sanitize-recover=all']
        r=subprocess.run(command,cwd=self.build,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        r=subprocess.run([str(exe)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        return r.stdout

    def test_original_cps_arithmetic_and_arm_helpers(self):
        relative='lib/libCPS/src/cps_bignum.c';source=self.work/'cps.c'
        source.write_text(native.adapt(relative,(GAME/relative).read_text(),GAME))
        wcm='lib/NitroWiFi/src/wcm_control.c';text=native.adapt(wcm,(GAME/wcm).read_text(),GAME)
        code='#include <assert.h>\n#include <stdint.h>\n#include <nitro/types.h>\n'
        code+='u64 get48bits_2(const u16 *); u64 get48bits_3(const u16 *); u64 get64bits(const u16 *);\n'
        code+='void CPSi_big_div(u16 *,const u16 *,const u16 *,u16 *,int,u16 *);\n'
        code+=block(text,'u32 WcmCountBits(')+block(text,'u32 WcmCountLeadingZero(')
        code+='''int main(void) {
 u16 v[]={0x1234,0x5678,0x9abc,0xdef0};
 CHECK(get48bits_2(v+3)==UINT64_C(0xdef09abc0000));
 CHECK(get48bits_3(v+3)==UINT64_C(0xdef09abc5678));
 CHECK(get64bits(v+3)==UINT64_C(0xdef09abc56781234));
 u32 state=1;
 for(int i=0;i<10000;i++) {
  state=state*1664525u+1013904223u; u32 a=state;
  state=state*1664525u+1013904223u; u32 b=state|1;
  u64 n=((u64)a<<32)|state;
  u16 numerator[8]={0},denominator[8]={0},q[8]={0},r[8]={0},scratch[24]={0};
  for(int k=0;k<4;k++) numerator[k]=(u16)(n>>(k*16));
  denominator[0]=(u16)b;denominator[1]=(u16)(b>>16);
  CPSi_big_div(q,numerator,denominator,r,8,scratch);
  u64 quotient=0,remainder=0;
  for(int k=3;k>=0;k--){quotient=(quotient<<16)|q[k];remainder=(remainder<<16)|r[k];}
  CHECK(quotient==n/b && remainder==n%b);
  u32 bits=0,leading=32;
  for(int k=0;k<32;k++)if(a&(1u<<k)){bits++;leading=31-k;}
  CHECK(WcmCountBits(a)==bits && WcmCountLeadingZero(a)==leading);
 }
 CHECK(WcmCountBits(0)==0 && WcmCountLeadingZero(0)==32);
 return 0;
}'''
        # Compile the complete original arithmetic provider, using genuine MI routines.
        obj=self.work/'cps.o'
        r=subprocess.run([*self.flags,'-c',str(source),'-o',str(obj),'-fsanitize=address,undefined','-fno-sanitize-recover=all'],cwd=self.build,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.run_code(code,extras=[obj,self.build/'libntr/libntr_mi.a',self.build/'libntr/libntr_sim_state.a'])

    def test_new_data_members_and_size_annotations(self):
        for original in ['asm/pokedex_rodata.o','lib/NitroDWC/asm/dwc_lobby_data.o']:
            blocks=assembly.recipe(GAME,original);source=self.work/'data.S';obj=self.work/'data.o'
            source.write_text(assembly.emit_reviewed(blocks))
            subprocess.run(['clang','-arch','arm64','-c',str(source),'-o',str(obj)],check=True,capture_output=True)
            self.assertTrue(assembly.validate_object(obj,blocks)['validated'])
        source=self.work/'bad.s';source.write_text('.rodata\nx:\n.byte 1\n.size other,.-x\n')
        with self.assertRaisesRegex(ValueError,'unsupported symbol size'):
            native_blocks(source)
        self.run_code('''#include "global.h"
#include "lobby_chat_internal.h"
#include "ppw_lobby_work.h"
int main(void) {
 CHECK(sizeof(gLobbyMemReserve)==16);
 CHECK(sizeof(gLobbyMemOutOfMemoryHandler)==8);
 CHECK(sizeof(gPPWLobbyWork)==8);
 return 0;
}''')

        self.run_code('''#include "global.h"
#include "dwc/chat_internal.h"
int main(void) {CHECK(sizeof(ChatChannelMode)==32);return 0;}''')

    def test_bounded_original_compiler_operations(self):
        relative='src/wifi_plaza/wifi_plaza_instrument.c'
        original=(GAME/relative).read_text();adapted=native.adapt(relative,original,GAME)
        self.assertNotRegex(adapted,r'\b_(?:fadd|fflt|ffix|ll_mul)\(')
        code='#include <stdint.h>\n#include <string.h>\n#include <nitro/types.h>\n'
        multiply=next(new for old,new,_ in native.COMPILER_BOUNDED_OPERATIONS[relative][1] if old.startswith('_ll_mul('))
        code+='s64 mul(int frame,int delta) {return '+multiply+';}\nint main(void) {\n'
        for old,new,_ in native.COMPILER_BOUNDED_OPERATIONS[relative][1]:
            match=re.fullmatch(r'_fadd\(0x3F000000, _fflt\((\d+) << (\d+)\)\)',old)
            if not match:continue
            value=int(match[1])<<int(match[2])
            bits=struct.unpack('<I',struct.pack('<f',value+0.5))[0]
            code+='{f32 v='+new+';u32 bits;memcpy(&bits,&v,4);CHECK(bits=='+str(bits)+'u);CHECK((s32)v=='+str(value)+');}\n'
        code+='''for(int frame=-100;frame<=100;frame++) {
 const int delta[]={INT32_MIN,-1,0,1,INT32_MAX};
 for(int i=0;i<5;i++) CHECK(mul(frame,delta[i])==((s64)frame*4096)*delta[i]);
}return 0;}'''
        self.run_code(code)

    def test_dwc_and_plaza_consumer_views_remain_unsupported(self):
        # Use the original private view, not a reconstructed native declaration.
        text=(GAME/'src/lobby/lobby_chat_remove_channel.cpp').read_text()
        view=block(text,'struct MapNode {').rstrip()+';\n'
        code='''#include <stddef.h>
#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "global.h"
#include "dwc/match_internal.h"
#include "lobby_chat_manager.h"
struct SetNode;
'''+view+'''
int main() {
 size_t actual=offsetof(LobbyChannelMapNode,entry)+offsetof(LobbyChannelMapEntry,channel)+offsetof(LobbyChannel,users);
 CHECK(sizeof(MatchKeyEntry)==24);
 CHECK(offsetof(MatchKeyEntry,value)==16);
 CHECK(154*sizeof(MatchKeyEntry)==3696 && 1848<3696);
 CHECK(offsetof(MapNode,isize)!=actual);
 printf("unsupported: DWC stride 12 -> %zu; Plaza count offset %zu -> %zu\\n",sizeof(MatchKeyEntry),offsetof(MapNode,isize),actual);
 // Original ((int *)&pointer)[1] overwrites pointer bits, not trailing error storage.
 struct {uintptr_t pointer;int error;} slot={UINT64_C(0x123456789abc),0};
 int error=7; memcpy((char *)&slot.pointer+4,&error,4);
 CHECK(slot.pointer!=UINT64_C(0x123456789abc) && slot.error==0);
 return 0;
}'''
        output=self.run_code(code,cpp=True)
        self.assertIn('unsupported:',output)
        print(output.strip())

    def test_source_drift_rejected(self):
        for relative in [*native.ARM_INLINE_OPERATIONS,*native.COMPILER_BOUNDED_OPERATIONS]:
            with self.assertRaisesRegex(ValueError,'source drift'):
                native.adapt(relative,(GAME/relative).read_text()+'\n',GAME)

    def test_original_ca_pointer_and_scalar_layout(self):
        original=GAME/'lib/NitroDWC/asm/dwc_lib_data.s'
        lines=original.read_text().splitlines();records=parse(original)
        _,labels,refs=raw_layout(records)
        checked=0
        for i,record in enumerate(records):
            if not record.symbol.startswith('gDwcCa'):continue
            section,start=labels[record.symbol]
            offsets={offset-start for sec,offset in refs if sec==section and start<=offset<start+20}
            if offsets!={0,8,16}:continue
            checked+=1
            stop=records[i+1].line-1
            source=self.work/'ca.s';source.write_text('.data\n.public '+record.symbol+'\n'+'\n'.join(lines[record.line-1:stop])+'\n')
            layout={record.symbol:dict(source_size=20,pointers=[0,8,16],padding={8:4,16:4})}
            blocks=native_blocks(source,layout)
            asm=self.work/'ca.S';obj=self.work/'ca.o';asm.write_text(assembly.emit_reviewed(blocks))
            subprocess.run(['clang','-arch','arm64','-c',str(asm),'-o',str(obj)],check=True,capture_output=True)
            self.assertTrue(assembly.validate_object(obj,blocks)['validated'])
            self.assertEqual(sum(8 if k=='pointer' else len(v) for k,v in blocks[0]['native_items']),40)
        self.assertEqual(checked,12)
        self.run_code('''#include <stddef.h>
#include "cps/cps_ssl_internal.h"
int main(void) {
 CHECK(sizeof(CpsRootCa)==40);
 CHECK(offsetof(CpsRootCa,modulusLength)==8 && offsetof(CpsRootCa,modulus)==16);
 CHECK(offsetof(CpsRootCa,exponentLength)==24 && offsetof(CpsRootCa,exponent)==32);
 return 0;
}''')

    def test_original_query_report_callback_abi_is_incompatible(self):
        initializer=(GAME/'lib/NitroDWC/src/query_report_init.c').read_text()
        consumer=(GAME/'lib/NitroDWC/src/server_report.c').read_text()
        code='#include <stddef.h>\n#include <stdio.h>\n#include "global.h"\n'
        code+=block(initializer,'typedef struct QueryReport {').rstrip()+' QueryReport;\n'
        for name in ['SockAddr','QRBuffer','QRKeyList']:
            code+=block(consumer,'typedef struct '+name+' {').rstrip()+' '+name+';\n'
        code+='\n'.join(re.findall(r'(?m)^typedef .*\(\*QR\w+Callback\).*;',consumer))+'\n'
        code+=block(consumer,'typedef struct QRRecord {').rstrip()+' QRRecord;\n'
        code+='''int main(void) {
 CHECK(sizeof(QueryReport)!=sizeof(QRRecord));
 CHECK(sizeof(((QueryReport *)0)->callbacks[0])==4);
 CHECK(sizeof(((QRRecord *)0)->serverKeyCallback)==8);
 CHECK(offsetof(QueryReport,lastHeartbeatTime)!=offsetof(QRRecord,lastHeartbeatTime));
 printf("unsupported: original QueryReport %zu bytes, QRRecord %zu; heartbeat offsets %zu / %zu\\n",sizeof(QueryReport),sizeof(QRRecord),offsetof(QueryReport,lastHeartbeatTime),offsetof(QRRecord,lastHeartbeatTime));
 return 0;
}'''
        print(self.run_code(code).strip())

    def test_original_plaza_member_pointer_layout(self):
        original=(GAME/'src/lobby/ppw_lobby_players_all_have_profiles.cpp').read_text()
        code='#include <stddef.h>\n#include <stdio.h>\n#include "global.h"\n#include "lobby_chat_request.h"\n'
        code+=block(original,'struct Value {').rstrip()+';\n'
        code+=re.search(r'typedef bool \(Value::\*Pmf\)\(\);',original)[0]+'\n'
        code+=block(original,'struct Holder {').rstrip()+';\n'
        code+='''int main() {
 CHECK(sizeof(Pmf)==16 && sizeof(Holder)==24 && offsetof(Holder,pmf)==8);
 CHECK(sizeof(LobbyRequestVtable)==32);
 CHECK(offsetof(LobbyRequestVtable,getId)==16 && offsetof(LobbyRequestVtable,getParam)==24);
 printf("unsupported: original Plaza Holder data 12 bytes / PMF offset 4; native %zu / %zu\\n",sizeof(Holder),offsetof(Holder,pmf));
 return 0;
}'''
        print(self.run_code(code,cpp=True).strip())

if __name__=='__main__':unittest.main()
