"""Shared representation contracts and executable ARM64 ABI counterexamples."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/'upstream/pokeheartgold'
sys.path.insert(0,str(ROOT/'cmake'))
from native_abi import conflicts, require_consistent
from native_data_ir import native_blocks, parse
from native_data_layouts import contracts, recipe
import native_assembly_data as assembly
import test_shared_provider_native as provider


class AbiTests(unittest.TestCase):
    setUp=provider.ProviderTests.setUp

    def preserve(self,executable,output):
        directory=self.build/'abi-barrier/executables'/self._testMethodName
        directory.mkdir(parents=True,exist_ok=True)
        for path in self.work.iterdir():
            if path.suffix in ('.c','.cpp','.S') or path==executable:
                shutil.copy2(path,directory/path.name)
        (directory/'result.txt').write_text(output)

    def run_code(self,text,cpp=False,extras=()):
        result=provider.ProviderTests.run_code(self,text,cpp,extras)
        self.preserve(self.work/'probe',result)
        return result

    def test_coordinate_consistency_is_not_reference_counting(self):
        field=dict(guest=[4,4],native=[8,8],kind='pointer')
        views=[dict(object='record',consumer='typed producer',stride=[12,24],fields=[field]),
               dict(object='record',consumer='typed reader',stride=[12,24],fields=[field])]
        require_consistent(views)
        views.append(dict(object='record',consumer='raw offset reader',stride=[12,12],
                          fields=[dict(guest=[4,4],native=[4,8],kind='pointer')]))
        errors=conflicts(views)
        self.assertEqual(len(errors),2)
        self.assertEqual({e['reason'] for e in errors},{'inconsistent native stride','inconsistent native field coordinates or interpretation'})
        with self.assertRaisesRegex(ValueError,'consumer/call lowering'):
            require_consistent(views)

    def test_actual_blocked_member_contracts_are_enforced(self):
        for original, contract in contracts().items():
            if 'blocker' not in contract:
                continue
            with self.subTest(original=original):
                if contract.get('abi_views'):
                    self.assertTrue(conflicts(contract['abi_views']))
                with self.assertRaises(ValueError):
                    recipe(GAME,original)

    def test_member_pointer_emission_matches_native_compiler_and_calls(self):
        # Real C++ member declarations establish the encoding independently of
        # the emitter. Both use the original direct (object->*method)() operation.
        cpp=self.work/'members.cpp'
        cpp.write_text('''#include <cstring>
#include <cstdint>
#include <cstdlib>
struct Value {
 virtual void f0() { __builtin_trap(); }
 bool enabled;
 int called;
 bool predicate() __asm__("_HG_ABI_Predicate");
 void set(int value) __asm__("_HG_ABI_Set");
};
bool Value::predicate() { return enabled; }
void Value::set(int value) { called=value; }
using Pmf=bool(Value::*)();
struct Holder {uint32_t header;Pmf method;};
struct MemberTable {uint32_t header[2];void(Value::*method)(int);};
extern "C" Holder generated;
extern "C" MemberTable generated_with_arg;
Holder expected={1,&Value::predicate};
MemberTable expected_with_arg={{0x01000001,1},&Value::set};
struct Pred {Pmf f;bool operator()(Value *v) const {return (v->*f)();}};
int main() {
 static_assert(sizeof(Pmf)==16 && offsetof(Holder,method)==8 && sizeof(Holder)==24,"native PMF");
 if(generated.header!=1 || std::memcmp(&generated.method,&expected.method,sizeof(Pmf))) return 1;
 Value v;v.enabled=true;if(!Pred{generated.method}(&v))return 2;
 v.enabled=false;if(Pred{generated.method}(&v))return 3;
 if(std::memcmp(&generated_with_arg.method,&expected_with_arg.method,sizeof(Pmf)))return 4;
 (v.*generated_with_arg.method)(137);if(v.called!=137)return 5;
 return 0;
}''')
        source=self.work/'member.s';source.write_text('.data\n.public generated\ngenerated:\n.word 1, HG_ABI_Predicate, 0\n'
            '.public generated_with_arg\ngenerated_with_arg:\n.word 0x01000001, 1, HG_ABI_Set, 0\n')
        blocks=native_blocks(source,{'generated':dict(source_size=12,member_pointers=[4],padding={4:4}),
                                    'generated_with_arg':dict(source_size=16,member_pointers=[8])})
        asm=self.work/'member.S';obj=self.work/'member.o';asm.write_text(assembly.emit_reviewed(blocks))
        subprocess.run(['clang','-arch','arm64','-c',str(asm),'-o',str(obj)],check=True,capture_output=True)
        self.assertTrue(assembly.validate_object(obj,blocks)['validated'])
        exe=self.work/'member-call'
        r=subprocess.run(['clang++','-arch','arm64','-std=c++17','-O2','-fsanitize=address,undefined',
                          '-fno-sanitize-recover=all',str(cpp),str(obj),'-o',str(exe)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        r=subprocess.run([str(exe)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.preserve(exe,'PASS native PMF bytes match Clang and both member call signatures execute\n')

    def test_both_original_member_constants_keep_prefixes_and_relocations(self):
        original=GAME/'lib/NitroDWC/asm/dwc_lobby_chat_data.s';lines=original.read_text().splitlines();records=parse(original)
        layouts=contracts()['lib/NitroDWC/asm/dwc_lobby_chat_data.o']['layouts']
        for i,record in enumerate(records):
            if record.symbol not in layouts or not layouts[record.symbol].get('member_pointers'):continue
            text='.data\n.public '+record.symbol+'\n'+'\n'.join(lines[record.line-1:records[i+1].line-1])+'\n'
            source=self.work/(record.symbol+'.s');source.write_text(text)
            layout=dict(layouts[record.symbol]);layout['padding']={int(k):v for k,v in layout.get('padding',{}).items()}
            blocks=native_blocks(source,{record.symbol:layout})
            asm=source.with_suffix('.S');obj=source.with_suffix('.o');asm.write_text(assembly.emit_reviewed(blocks))
            subprocess.run(['clang','-arch','arm64','-c',str(asm),'-o',str(obj)],check=True,capture_output=True)
            self.assertTrue(assembly.validate_object(obj,blocks)['validated'])
            expected,_=assembly.reviewed_layout(blocks)
            self.assertEqual(len(expected['__data']['data']),24)
            prefix=bytes(expected['__data']['data'][:4 if record.symbol=='ov45_02255200' else 8])
            self.assertEqual(prefix,bytes([1,0,0,0]) if record.symbol=='ov45_02255200' else bytes([1,0,0,1,1,0,0,0]))

    def test_member_encoding_rejects_unreviewed_variants(self):
        source=self.work/'bad.s'
        for words in ['target, 1','target + 1, 0','1, 0']:
            source.write_text('.data\nx:\n.word '+words+'\n')
            with self.assertRaises(ValueError):native_blocks(source,{'x':dict(member_pointers=[0])})
        source.write_text('.data\nx:\n.word target, 0, 0\n')
        for layout in [dict(member_pointers=[0,4]),dict(member_pointers=[0],pointers=[0]),
                       dict(member_pointers=[0],padding={4:4}),dict(member_pointers=[0],alignment=4)]:
            with self.assertRaises(ValueError):native_blocks(source,{'x':layout})
        source.write_text('.data\nx:\n.word 1, target, 0\n')
        with self.assertRaisesRegex(ValueError,'eight-byte aligned'):
            native_blocks(source,{'x':dict(member_pointers=[4])})

    def test_original_callback_writes_cannot_populate_native_reader(self):
        initial=(GAME/'lib/NitroDWC/src/query_report_init.c').read_text()
        consumer=(GAME/'lib/NitroDWC/src/server_report.c').read_text()
        code='#include <stdint.h>\n#include <stddef.h>\n#include <stdio.h>\n#include <string.h>\n#include "global.h"\n'
        code+=provider.block(initial,'typedef struct QueryReport {').rstrip()+' QueryReport;\n'
        for name in ['SockAddr','QRBuffer','QRKeyList']:
            code+=provider.block(consumer,'typedef struct '+name+' {').rstrip()+' '+name+';\n'
        code+='\n'.join(re.findall(r'(?m)^typedef .*\(\*QR\w+Callback\).*;',consumer))+'\n'
        code+=provider.block(consumer,'typedef struct QRRecord {').rstrip()+' QRRecord;\n'
        assignments='\n'.join(re.findall(r'(?m)^    qr->(?:callbacks\[\d\]|userData) = \w+;',initial))
        self.assertEqual(len(assignments.splitlines()),7)
        code+='void original_stores(QueryReport *qr,u32 cb0,u32 cb1,u32 cb2,u32 cb3,u32 cb4,u32 cb5,u32 userData) {\n'+assignments+'\n}\n'
        code+='''static volatile u32 calls;
static void callback(u8 key,QRBuffer *buffer,void *param) {calls+=key;if(buffer)buffer->len++;(void)param;}
int main(void) {
 _Alignas(QRRecord) unsigned char storage[sizeof(QRRecord)]={0};
 uintptr_t original=(uintptr_t)&callback;
 CHECK(original>UINT32_MAX);
 original_stores((QueryReport *)storage,(u32)original,0,0,0,0,0,0x12345678);
 uintptr_t loaded=0;memcpy(&loaded,storage+offsetof(QRRecord,serverKeyCallback),sizeof(loaded));
 CHECK(loaded!=original && loaded==(u32)original);
 CHECK(offsetof(QueryReport,userData)!=offsetof(QRRecord,param));
 printf("BLOCKED original callback roundtrip: native=%llx stored/read=%llx; original u32 slot loses code-address bits\\n",(unsigned long long)original,(unsigned long long)loaded);
 return 0;
}'''
        print(self.run_code(code).strip())

    def test_intentional_aliases_conflict_with_native_pointer_loads(self):
        source=(GAME/'lib/NitroDWC/src/gs_platform.c').read_text()
        state=provider.block(source,'typedef struct Ov00SocketState {').rstrip()+' Ov00SocketState;\n'
        login=(GAME/'lib/NitroDWC/src/dwc_login.c').read_text()
        store=next(line.strip() for line in login.splitlines() if '((int *)&gDwcControl)[1] = error;' in line)
        code='#include <stdint.h>\n#include <string.h>\n#include <stdio.h>\n#include "global.h"\n'+state
        code+='void *gDwcControl;\n__attribute__((noinline)) void original_error_store(int error) {'+store+'}\n'
        code+='''int main(void) {
 uintptr_t original=UINT64_C(0x123456789abc);
 gDwcControl=(void *)original;original_error_store(7);
 uintptr_t changed;memcpy(&changed,&gDwcControl,sizeof(changed));
 CHECK(changed!=original && (u32)(changed>>32)==7);
 Ov00SocketState state={0};state.lastError=7;
 char *ov00_0221B1B4=(char *)&state.hName;
 uintptr_t alias;memcpy(&alias,ov00_0221B1B4-8,sizeof(alias));
 u32 guest_first;memcpy(&guest_first,&state,4);
 CHECK(guest_first==0 && alias!=0);
 printf("BLOCKED aliases: socket error corrupts native pointer; GameSpy null 32-bit alias becomes non-null 64-bit value\\n");
 return 0;
}'''
        print(self.run_code(code).strip())

    def test_original_match_key_operations_disagree_on_record_stride(self):
        source=(GAME/'lib/NitroDWC/src/match_browse.c').read_text()
        clear=next(line.strip() for line in source.splitlines() if 'MIi_CpuClear32(0, (u32 *)gDwcMatchKeys, 1848);' in line)
        scale=next(line.strip() for line in source.splitlines() if line.strip()=='index *= 12;')
        read='*((u8 *)gDwcMatchKeys + index)'
        self.assertIn(read,source)
        code='''#include <stdio.h>
#include "global.h"
#include "dwc/match_internal.h"
MatchKeyEntry gDwcMatchKeys[154];
int main(void) {
 for(int i=0;i<154;i++) gDwcMatchKeys[i].id=(u8)(100+i);
 int index=1;
'''+scale+'\n u8 raw='+read+';\n'+'''
 CHECK(raw!=gDwcMatchKeys[1].id);
'''+clear+'\n'+'''
 CHECK(gDwcMatchKeys[0].id==0 && gDwcMatchKeys[153].id==253);
 printf("BLOCKED original match keys: raw index selects different record; literal clear leaves native tail live\\n");
 return 0;
}'''
        print(self.run_code(code,extras=[self.build/'libntr/libntr_mi.a',self.build/'libntr/libntr_sim_state.a']).strip())

    def test_original_plaza_private_views_require_consumer_lowering(self):
        source=(GAME/'src/lobby/lobby_chat_remove_channel.cpp').read_text()
        code='''#include <stddef.h>
#include <stdio.h>
#include "global.h"
#include "lobby_chat_manager.h"
struct SetNode;
'''
        for name in ['MapNode','ChannelMap','Root']:
            code+=provider.block(source,'struct '+name+' {').rstrip()+';\n'
        code+='''int main() {
 size_t users=offsetof(LobbyChannelMapNode,entry)+offsetof(LobbyChannelMapEntry,channel)+offsetof(LobbyChannel,users);
 CHECK(users==48 && offsetof(MapNode,isize)==28);
 CHECK(users+offsetof(LobbyUserIdSet,root)==56 && offsetof(MapNode,hdr)==32);
 CHECK(users+offsetof(LobbyUserIdSet,first)==64 && offsetof(MapNode,first)==40);
 CHECK(offsetof(LobbyChatManager,channelMap)==184 && offsetof(Root,channels)==128);
 printf("BLOCKED Plaza private views: count/root/first 28/32/40 vs 48/56/64; channel map 128 vs 184\\n");
 return 0;
}'''
        print(self.run_code(code,cpp=True).strip())

if __name__=='__main__':unittest.main()
