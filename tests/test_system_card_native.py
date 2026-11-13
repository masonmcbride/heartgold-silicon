"""Original system-card operations use the SDK's existing native memory owners."""
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
from native_sources import adapt


class SystemCard(unittest.TestCase):
    def test_original_order_and_native_memory(self):
        build=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build')).resolve()
        game=ROOT/'upstream/pokeheartgold'
        entry=next(e for e in json.loads((build/'compile_commands.json').read_text())
                   if '/heartgold_main.dir/' in e.get('command','') and e['file'].endswith('/system.c'))
        flags=shlex.split(entry['command']);i=flags.index('-o');del flags[i:i+2]
        flags=[x for x in flags if x not in ('-c',entry['file'])]
        with tempfile.TemporaryDirectory(dir=build) as temporary:
            work=Path(temporary);source=work/'system_card.c'
            relative='src/system_card.c'
            source.write_text(adapt(relative,(game/relative).read_text(),game))
            test=work/'test.c'
            test.write_text('''
#include <nitro.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"line %d: %s\\n",__LINE__,#x);abort();}}while(0)
_Alignas(8) u8 s_HW_MAIN_MEM[0x800000];
_Alignas(8) u8 s_HW_MAIN_MEM_SYSTEM[0x400];
static FSArchive archive;
static unsigned cards,copies,opens,resets;
BOOL FS_IsAvailable(void){return TRUE;}
void OS_Terminate(void){abort();}
void CARD_Init(void){CHECK(copies==0);cards++;}
void MI_CpuCopy8(const void *src,void *dst,u32 bytes){
 CHECK(cards==1 && bytes==0x160);
 CHECK(src==(void*)HW_ROM_HEADER_BUF);
 CHECK(dst==s_HW_MAIN_MEM+(copies==0?0x7ff000:0x7ffa80));
 CHECK(copies<2);copies++;memcpy(dst,src,bytes);
}
FSArchive *FS_FindArchive(const char *name,int len){CHECK(len==3 && !memcmp(name,"rom",3));return &archive;}
void FS_InitFile(FSFile *file){memset(file,0,sizeof *file);}
BOOL FS_OpenFile(FSFile *file,const char *name){CHECK(!strcmp(name,"rom:/test"));opens++;file->prop.file.top=0x123456;return TRUE;}
void OS_ResetSystem(u32 value){CHECK(value==0);resets++;}
extern void SystemCard_InitRomArchive(void),SystemCard_RebootIntoFile(const char *);
int main(void){
 CHECK((uintptr_t)s_HW_MAIN_MEM>UINT32_MAX);
 u32 words[]={0x4a414441,0x3130};
 memcpy((void*)(HW_ROM_HEADER_BUF+12),words,6);
 u32 indices[]={0x200,0x90,0x300,0x80};
 memcpy((void*)(HW_ROM_HEADER_BUF+0x40),indices,sizeof indices);
 SystemCard_InitRomArchive();
 CHECK(cards==1 && copies==2);
 CHECK(!memcmp(s_HW_MAIN_MEM+0x7ff000,(void*)HW_ROM_HEADER_BUF,0x160));
 CHECK(!memcmp(s_HW_MAIN_MEM+0x7ffa80,(void*)HW_ROM_HEADER_BUF,0x160));
 CHECK(archive.fnt==0x200 && archive.fnt_size==0x90 && archive.fat==0x300 && archive.fat_size==0x80);
 SystemCard_InitRomArchive();CHECK(cards==1 && copies==2);
 SystemCard_RebootIntoFile("rom:/test");CHECK(opens==1 && resets==1);
 CHECK(*(u32*)HW_ROM_BASE_OFFSET_BUF==0x123456);
 return 0;
}
''');exe=work/'test'
            result=subprocess.run([*flags,'-O2','-fsanitize=address,undefined','-fno-sanitize-recover=all',source,test,'-o',exe],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([exe],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':unittest.main()
