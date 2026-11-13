"""Original OVY_74 initialization against the coalesced heap/work BSS region."""
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
sys.path.insert(0,str(ROOT/'compiler/guest32'))
from frontend import flags as original_flags
from native_data_layouts import recipe
from native_assembly_data import emit_reviewed,validate_object
from native_sources import adapt


class MainMenuStorage(unittest.TestCase):
    def test_original_initialize_and_aliases(self):
        build=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build')).resolve()
        game=ROOT/'upstream/pokeheartgold'
        entry=next(e for e in json.loads((build/'compile_commands.json').read_text())
                   if '/heartgold_main.dir/' in e.get('command','') and e['file'].endswith('/system.c'))
        flags=shlex.split(entry['command']);index=flags.index('-o');del flags[index:index+2]
        flags=[x for x in flags if x not in ('-c',entry['file'])]
        with tempfile.TemporaryDirectory(dir=build) as temp:
            work=Path(temp)
            def run(args):
                r=subprocess.run(list(map(str,args)),capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            objects=[]
            original=work/'original-layout.c'
            original.write_text('''#include "application/main_menu/main_menu_util.h"
_Static_assert(sizeof(MainMenuUtilWork)==3752,"original complete work extent");
_Static_assert(__builtin_offsetof(MainMenuUtilWork,sprites)==52,"original C prefix");
_Static_assert(__builtin_offsetof(MainMenuUtilWork,sprites.renderer)==56,"original renderer alias");
_Static_assert(__builtin_offsetof(MainMenuUtilWork,giftSprite)==520,"original gift alias");
_Static_assert(__builtin_offsetof(MainMenuUtilWork,vblankCallback)==3748,"original VBlank alias");
''')
            run([flags[0],*original_flags(game,build),'-fsyntax-only',original])
            for member in ('asm/main_menu_bss.o','asm/main_menu_data.o'):
                blocks=recipe(game,member);source=work/(Path(member).stem+'.S');source.write_text(emit_reviewed(blocks))
                obj=source.with_suffix('.o');run(['clang','-c',source,'-o',obj]);validate_object(obj,blocks)
                objects.append(obj)
            for name in ('main_menu_util','main_menu_shared'):
                relative='src/application/main_menu/'+name+'.c';source=work/(name+'.c')
                source.write_text(adapt(relative,(game/relative).read_text(),game));obj=source.with_suffix('.o')
                run([*flags,'-O2','-fsanitize=address,undefined','-fno-sanitize-recover=all','-c',source,'-o',obj]);objects.append(obj)
            source=work/'check.c';source.write_text('''
#include "application/main_menu/main_menu_util.h"
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"line %d: %s\\n",__LINE__,#x);abort();}}while(0)
extern MainMenuUtilWork gMainMenuUtilWork;
extern MainMenuUtilSprites gMainMenuUtilSprites;
extern G2dRenderer gMainMenuUtilRenderer;
extern unsigned char gMainMenuUtilGiftSpriteWork[];
extern void MainMenuUtil_InitWork(enum HeapID);
extern void MainMenuUtil_SetFadeWhite(u32);
int main(void){
 volatile uintptr_t sprites=(uintptr_t)&gMainMenuUtilSprites;
 volatile uintptr_t renderer=(uintptr_t)&gMainMenuUtilRenderer;
 _Static_assert(sizeof(MainMenuUtilWork)==4040,"native work extent");
 CHECK((void*)(&gMainMenuUtilCryptoHeapId+1)==(void*)&gMainMenuUtilWork);
 CHECK((uintptr_t)&gMainMenuUtilWork%8==0);
 CHECK(sprites==(uintptr_t)&gMainMenuUtilWork.sprites);
 CHECK(renderer==(uintptr_t)&gMainMenuUtilWork.sprites.renderer);
 CHECK(gMainMenuUtilGiftSpriteWork+8==(unsigned char*)&gMainMenuUtilWork.giftSprite);
 CHECK((unsigned char*)gMainMenuUtilVBlankWork+36==(unsigned char*)&gMainMenuUtilWork.vblankCallback);
 gMainMenuUtilCryptoHeapId=HEAP_ID_84;
 MainMenuUtil_InitWork(HEAP_ID_83);
 CHECK(gMainMenuUtilCryptoHeapId==HEAP_ID_84 && gMainMenuUtilWork.heapId==HEAP_ID_83);
 CHECK(gMainMenuUtilWork.unk_004==1 && !gMainMenuUtilWork.bgConfig);
 void *p=malloc(32);CHECK(p && (uintptr_t)p>UINT32_MAX);
 gMainMenuUtilWork.giftSprite=p;
 void *alias;memcpy(&alias,gMainMenuUtilGiftSpriteWork+8,8);CHECK(alias==p);
 gMainMenuUtilWork.sprites.spriteList=p;CHECK(*(void*volatile*)sprites==p);
 MainMenuUtil_SetFadeWhite(TRUE);CHECK(gMainMenuUtilWork.fadeWhite);
 MainMenuUtil_InitWork(HEAP_ID_84);
 CHECK(gMainMenuUtilCryptoHeapId==HEAP_ID_84 && gMainMenuUtilWork.heapId==HEAP_ID_84);
 CHECK(!gMainMenuUtilWork.giftSprite && !*(void*volatile*)sprites);
 CHECK(!gMainMenuUtilWork.vblankCallback && !gMainMenuUtilWork.fadeWhite);
 free(p);return 0;
}
''');exe=work/'check'
            run([*flags,'-O2','-fsanitize=address,undefined','-fno-sanitize-recover=all',source,*objects,'-Wl,-dead_strip','-o',exe]);run([exe])


if __name__=='__main__':unittest.main()
