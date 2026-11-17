"""Run original destruction/task and pointer-storage consumers above 32 bits."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import re

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build',type=Path,required=True)
a=p.parse_args(); build=a.build.resolve();root=Path(__file__).resolve().parents[1]
work=build/'field-effect-abi-test';work.mkdir(parents=True,exist_ok=True)
entries=json.loads((build/'compile_commands.json').read_text())
entry=next(e for e in entries if e['file'].endswith('/native/src/field_effects.c'))
import shlex
args=entry.get('arguments') or shlex.split(entry['command'])
flags=[];skip=False
for flag in args[1:]:
    if skip:skip=False;continue
    if flag in ('-o','-MF','-MT','-MQ'):skip=True;continue
    if flag not in ('-c','-MD','-MMD',entry['file']):flags.append(flag)
# Keep Nintendo's assertion configuration; fixture failures terminate the test.
source=work/'test.c'
source.write_text((build/'native/src/field_effects.c').read_text()+'''
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <field_emote_mark.h>
#include <field_surf_mount.h>
#include <map_object_follow_internal.h>
#include <field/field_effect_manager_internal.h>
#include <field/field_3d_object_task.h>
#include <field/map_object_render_internal.h>
#include <field/encounter_effect.h>
#include <overlay_manager.h>
#include <stddef.h>
static void check(int good) { if (!good) abort(); }
void GF_AssertFail(void) { abort(); }
_Static_assert(sizeof(SavedMapObject)==80 && offsetof(SavedMapObject,movementData)==48,"fixed DS save format");
_Static_assert(sizeof(FieldEffectBasicTemplate)==40 && offsetof(FieldEffectBasicTemplate,init)==8,"native effect template");
_Static_assert(sizeof(FieldEffectRendererTemplate)==24 && offsetof(FieldEffectRendererTemplate,init)==8,"native renderer record");
_Static_assert(sizeof(Field3dObjectTaskTemplate)==40 && sizeof(((Field3dObjectTaskTemplate *)0)->dataSize)==2 && offsetof(Field3dObjectTaskTemplate,initFunc)==8,"native task record, fixed u16 size");
_Static_assert(sizeof(EncounterEffectState)==16 && offsetof(EncounterEffectState,effect)==8,"typed mutable BSS");
_Static_assert(sizeof(OverlayManagerTemplate)==32 && offsetof(OverlayManagerTemplate,ovy_id)==24,"native application template");
static FieldEffect *expected;
static int destroyed;
static void destroyed_effect(FieldEffect *effect, void *state) {
    check(effect==expected && (uintptr_t)state>UINT32_MAX);
    check(*(uintptr_t *)state==UINT64_C(0x12345678abcdef09));
    destroyed++;
}
static void task_callback(SysTask *task, void *data) { (void)task; (void)data; }
_Static_assert(_Generic(&EmoteMark_Spawn, struct FieldEffect *(*)(LocalMapObject *,int,int):1,default:0), "EmoteMark result ABI");
_Static_assert(_Generic(&SurfMountEffect_Create, struct FieldEffect *(*)(LocalMapObject *,u32,u32,u32,BOOL):1,default:0), "Surf result ABI");
_Static_assert(sizeof(HiddenObjectMovementState)<=16,"hidden native state fits unchanged work buffer");
int main(void) {
    MapObjectManager *manager=calloc(1,sizeof(*manager));check(manager!=NULL);
    LocalMapObject rendererObject={0};rendererObject.manager=manager;
    FieldSystem *expectedField=(FieldSystem *)&rendererObject;
    manager->objects=&rendererObject;manager->fieldSystem=expectedField;
    _Static_assert(_Generic(((MapObjectManager *)0)->render,struct MapObjectRender:1,default:0),"renderer is an embedded native object");
    MapObjectRender *render=MapObjectManager_GetRender(manager);
    check(render==&manager->render && (uintptr_t)render%_Alignof(MapObjectRender)==0);
    // Exercise the entire renderer footprint, including its final pointer.
    // The former DS-sized reservation overwrote both following members.
    memset(render,0x5a,sizeof(*render));render->manager=manager;
    check(manager->objects==&rendererObject && manager->fieldSystem==expectedField);
    check(MapObject_GetFieldSystem(&rendererObject)==expectedField);
    free(manager);
    FieldEffect *effect=calloc(1,sizeof(*effect));
    check(effect && (uintptr_t)effect>UINT32_MAX);
    expected=effect;
    FieldEffectPool pool={0}; pool.count=pool.activeCount=1;pool.effects=effect;
    void *arena=calloc(1,SysTaskQueue_GetArenaSize(1));check(arena!=NULL);
    SysTaskQueue *queue=SysTaskQueue_PlacementNew(1,arena);
    effect->task=SysTaskQueue_InsertTask(queue,task_callback,effect,0);
    check(effect->task!=NULL);
    effect->flags=FIELD_EFFECT_FLAG_ACTIVE|FIELD_EFFECT_FLAG_STARTED;
    effect->pool=&pool;effect->destroy=destroyed_effect;
    check((uintptr_t)effect->state % _Alignof(void *)==0);
    *(uintptr_t *)effect->state=UINT64_C(0x12345678abcdef09);
    PlayerAvatar avatar={0};
    PlayerAvatar_SetSurfMountEffect(&avatar,effect);
    check(PlayerAvatar_GetSurfMountEffect(&avatar)==effect);
    LocalMapObject object={0};
    HiddenObjectMovement_SetCoverEffect(&object,effect);
    check(HiddenObjectMovement_GetCoverEffect(&object)==effect);
    FieldEffectManager_DestroyEffect(effect);
    check(destroyed==1 && pool.activeCount==0 && queue->activeCount==0);
    check(!FieldEffect_IsActive(effect));
    for (unsigned i=0;i<sizeof(effect->state);i++)check(effect->state[i]==0);
    FieldEffect_Destroy(effect);check(destroyed==1);
    free(arena);free(effect);
    puts("Original field destruction/task unlink and native surf/hidden storage passed above 32 bits");
    return 0;
}
''')
paths=[source,build/'native/src/field/field_effect_manager.c',build/'native/src/player_avatar.c',
       build/'native/src/map_object_follow.c',build/'native/src/map_object.c',
       root/'upstream/pokeheartgold/src/sys_task.c',root/'upstream/pokeheartgold/src/sys_task_api.c']
objects=[]
commands=[]
def run(command):
    commands.append(command)
    result=subprocess.run(command,text=True,capture_output=True,cwd=entry['directory'])
    (work/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    with (work/'diagnostics.log').open('a') as f:f.write(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError(result.stderr[-6000:])
    return result.stdout
for i,path in enumerate(paths):
    obj=work/f'{i}.o';objects.append(str(obj))
    run([args[0],*flags,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all','-c',str(path),'-o',str(obj)])
# Both direct and recursive inclusion must expose the same complete layout.
for i,headers in enumerate([['map_object.h','field/map_object_render_internal.h'],
                          ['field/map_object_render_internal.h','map_object.h']]):
    probe=work/f'renderer_headers_{i}.c'
    probe.write_text(''.join(f'#include <{h}>\n' for h in headers)+
        '_Static_assert(sizeof(((MapObjectManager *)0)->render)==sizeof(struct MapObjectRender),"native embedded extent");\n')
    run([args[0],*flags,'-fsyntax-only',str(probe)])
run([args[0],'-arch','arm64','-fsanitize=address,undefined','-Wl,-dead_strip',*objects,'-o',str(work/'test')])
print(run([str(work/'test')]),end='')
# Check every original typed field-effect callback state against the native
# pool's storage, including states outside the newly converted data members.
sys.path.insert(0,str(root/'cmake'))
import native_sources
state_probes={}
game=root/'upstream/pokeheartgold'
for original in sorted((game/'src').rglob('*.c')):
    text=original.read_text()
    types=set(re.findall(r'FieldEffectBasicTemplate\s+\w+(?:\[[^]]*\])?\s*=\s*\{\s*sizeof\((\w+)\)',text))
    types.update(re.findall(r'(\w+)\s*\*\w+\s*=\s*FieldEffect_GetState\(',text))
    if original.is_relative_to(game/'src/field'):
        types.update(re.findall(r'\b(?:BOOL|void)\s+\w+\(FieldEffect \*\w+,\s*(\w+) \*\w+\)',text))
    types.discard('void')
    if not types: continue
    relative=original.relative_to(game).as_posix()
    actual=build/'native'/relative if relative in native_sources.OVERLAY_NATIVE_SOURCES else original
    probe=work/'states'/relative
    probe.parent.mkdir(parents=True,exist_ok=True)
    probe.write_text('#include '+json.dumps(str(actual))+'\n'+''.join(
        '_Static_assert(sizeof(%s)<=256 && _Alignof(%s)<=_Alignof(void *), "native effect state capacity/alignment");\n' % (name,name)
        for name in sorted(types)))
    run([args[0],*flags,'-iquote',str(original.parent),'-fsyntax-only',str(probe)])
    state_probes[relative]=sorted(types)
(work/'state-types.json').write_text(json.dumps(state_probes,indent=2)+'\n')
print('Native pool capacity/alignment checked for',sum(map(len,state_probes.values())),'original state types')
