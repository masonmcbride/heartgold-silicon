"""Production LLVM pointer-slot promotion and real original task-queue regression.

The runtime fixture uses the original accessor and task queue, with controlled
pointer producers/consumers in separate TUs. A test-only integer-slot fixture
retains promotion coverage; production sources already carry the pointer ABI.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'compiler/guest32'))
from semantic_slots import canonical, PRODUCTION_TARGET, lifetime_provider_sources, dependency_paths, identity, launch
for depfile in ('unit.o: one.h two.h\n', 'unit.o: one.h \\\n two.h\n',
                'unit.o: path\\ with\\ spaces.h\n',
                'unit.o: "quoted header.h"\n', 'unit.o: unicode\u00a0name.h\n',
                'unit.o: vertical\vtab.h\n', 'unit.o: form\ffeed.h\n',
                'unit.o: record\x1eseparator.h\n'):
    assert dependency_paths(depfile) == shlex.split(depfile.replace('\\\n', '').split(':', 1)[1])
sys.path.insert(0, str(ROOT / 'cmake'))
from native_sources import adapt

# A provider remains in the census when CMake selects its native adaptation.
# A same-named generated file alone must never establish original ownership.
game = ROOT / 'upstream/pokeheartgold'
heap = game / 'src/heap.c'
with tempfile.TemporaryDirectory() as temporary:
    binary = Path(temporary)
    generated = binary / 'native/src/heap.c'
    generated.parent.mkdir(parents=True)
    assert lifetime_provider_sources(heap, binary, game) == {heap.resolve()}
    generated.write_text('#line 1 ' + json.dumps(str(heap)) + '\n'
                         + adapt('src/heap.c', heap.read_text(), game))
    assert generated.resolve() in lifetime_provider_sources(heap, binary, game)
    generated.write_text(generated.read_text() + '\n/* undeclared change */\n')
    try:
        lifetime_provider_sources(heap, binary, game)
    except ValueError:
        pass
    else:
        raise AssertionError('modified lifetime provider was admitted')

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--lowerer', type=Path, required=True)
p.add_argument('--llvm-bin', type=Path)
a = p.parse_args()
build = a.build.resolve()
out = build / 'semantic-slot-tests'
out.mkdir(parents=True, exist_ok=True)
lowerer = a.lowerer.resolve()
production = json.loads((build / 'semantic-slots/plan.json').read_text())
db = json.loads((build / 'compile_commands.json').read_text())
participating = [e for e in db if Path(e['file']).suffix in ('.c', '.cpp', '.cc')
                 and re.search(r'CMakeFiles/' + PRODUCTION_TARGET + r'\.dir/',
                               ' '.join(e.get('arguments') or shlex.split(e['command'])))]
assert production['translation_units'] == len(participating)
# The first census must wait for every generated participant, before objects
# exist to carry compiler depfiles. A warmed binary directory hides this edge.
census_rules = build / 'CMakeFiles/heartgold_semantic_slots.dir/build.make'
if census_rules.exists():
    rules = census_rules.read_text()
    for entry in participating:
        source = Path(entry['file'])
        if source.is_relative_to(build):
            assert str(source.relative_to(build)) in rules, source
assert not any(r['struct'] == 'struct.EngagedTrainer' for r in production['slots'])
registry_path = build / 'semantic-slots/registry.json'
registry = json.loads(registry_path.read_text())
assert {row['source'] for row in registry.values()} == {e['file'] for e in participating}
ninja_dependencies = None
for row in registry.values():
    _, _, output = canonical(row['command'])
    obj = Path(row['directory']) / output
    depfile = Path(str(obj) + '.d')
    if depfile.exists():
        dependencies = dependency_paths(depfile.read_text())
    else:
        # Ninja consumes compiler depfiles into its persistent dependency log.
        if ninja_dependencies is None:
            ninja = re.search(r'^CMAKE_MAKE_PROGRAM:[^=]+=(.+)$',
                              (build / 'CMakeCache.txt').read_text(), re.M)[1]
            recorded = subprocess.check_output(
                [ninja, '-C', str(build), '-t', 'deps'], text=True)
            ninja_dependencies = {}
            current = None
            for line in recorded.splitlines():
                if ': #deps ' in line:
                    current = line.split(': #deps ', 1)[0]
                    ninja_dependencies[current] = []
                elif line.startswith('    ') and current is not None:
                    ninja_dependencies[current].append(line[4:])
        dependencies = ninja_dependencies[str(obj.relative_to(build))]
    approval=Path(row['ir']).with_name('codegen.json')
    assert str(approval) in dependencies, obj
    assert str(registry_path) not in dependencies, obj
    assert str(registry_path.with_name('plan.json')) not in dependencies, obj
    effective_ir=row['native_ir'] if row['transformed'] else row['ir']
    assert effective_ir in dependencies, obj
    if not row['transformed']:
        continue
    _, _, output = canonical(row['command'])
    obj = Path(row['directory']) / output
    receipt = json.loads(Path(str(obj) + '.semantic-slot.json').read_text())
    assert receipt['object_sha256'] == hashlib.sha256(obj.read_bytes()).hexdigest(), obj
    assert receipt['native_sha256'] == row['native_sha256'], obj
    assert receipt['approval_sha256'] == hashlib.sha256(approval.read_bytes()).hexdigest(), obj
# Shared original heap sources must not inherit production-only plan edges.
heap_rules = build / 'CMakeFiles/test_heap.dir'
for rules in heap_rules.glob('*.make'):
    assert 'semantic-slots/plan.json' not in rules.read_text(), rules

if a.llvm_bin:
    llvm = a.llvm_bin.resolve()
else:
    llvm_dir = re.search(r'^HEARTGOLD_GUEST32_LLVM_DIR:PATH=(.+)$', (build / 'CMakeCache.txt').read_text(), re.M)[1]
    llvm = Path(llvm_dir).parents[2] / 'bin'
db = json.loads((build / 'compile_commands.json').read_text())

def run(command):
    r = subprocess.run(list(map(str, command)), capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(' '.join(map(str, command)) + '\n' + r.stdout + r.stderr)
    return r.stdout


def original(name):
    entry = next(e for e in participating if e['file'].endswith('/src/' + name))
    command = entry.get('arguments') or shlex.split(entry['command'])
    flags, source, _ = canonical(command)
    ir = out / (name + '.ll')
    run([*flags, '-O0', '-g0', '-Xclang', '-disable-O0-optnone', '-Xclang', '-disable-llvm-passes', '-S', '-emit-llvm', source, '-o', ir])
    return ir, flags

battle, flags = original('scrcmd_battle.c')
manager, _ = original('script_manager.c')
behavior, _ = original('map_object_behavior.c')
queue, _ = original('sys_task.c')
plan_path = build / 'semantic-slots/plan.json'
plan = json.loads(plan_path.read_text())
def has_task_slot(report):
    return any(r['struct'] == 'struct.EngagedTrainer' and r['field'] == 6 for r in report['slots'])

assert not has_task_slot(plan), 'the pinned source already declares a task pointer'
for source in (battle, manager):
    run([lowerer, '--semantic-slots', 'apply', plan_path, source, source.with_suffix('.promoted.ll')])
promoted = battle.with_suffix('.promoted.ll').read_text()
produce = re.search(r'define [^\n]*@ScrCmd_GetTrainerPathToPlayer\(.*?^}', promoted, re.S | re.M)[0]
consume = re.search(r'define [^\n]*@ScrCmd_TrainerStepTowardsPlayer\(.*?^}', promoted, re.S | re.M)[0]
assert re.search(r'call ptr @TrainerApproach_Start', produce)
assert re.findall(r'declare ptr @TrainerApproach_Start[^\n]*', promoted) == re.findall(r'declare ptr @TrainerApproach_Start[^\n]*', battle.read_text()), 'retain the original argument ABI'
assert re.search(r'store ptr %[^,]+, ptr', produce)
assert 'ptrtoint' not in produce
assert re.search(r'load ptr, ptr', consume)
assert re.search(r'call void @TrainerApproach_Delete\(ptr', consume)
assert re.search(r'call i32 @TrainerApproach_IsDone\(ptr', consume), 'preserve the pinned task argument'
assert not re.search(r'load i32, ptr %\.0', consume)
# Exact original accessor implementation, not a handwritten selector table.
accessor = out / 'accessor.ll'
run([llvm / 'llvm-extract', '-S', '--func=FieldSysGetAttrAddrInternal', manager.with_suffix('.promoted.ll'), '-o', accessor])
original_accessor = out / 'original-accessor.ll'
run([llvm / 'llvm-extract', '-S', '--func=FieldSysGetAttrAddrInternal', manager, '-o', original_accessor])

# Test-only legacy representation: preserve the old promotion/negative corpus
# without changing the now pointer-typed original production sources.
header = ROOT / 'upstream/pokeheartgold/include/script.h'
legacy_header = out / 'legacy-script.h'
header_text = header.read_text()
assert header_text.count('SysTask *approachTask;') == 1
legacy_header.write_text(header_text.replace('SysTask *approachTask;', 'int approachTask;'))
vfs = out / 'legacy-header-vfs.json'
vfs.write_text(json.dumps(dict(version=0, roots=[
    {'type': 'file', 'name': str(path), 'external-contents': str(legacy_header),
     'use-external-name': False}
    for path in (header, build / 'native/include/script.h')
])))
legacy_manager = out / 'legacy-manager.ll'
manager_entry = next(e for e in db if e['file'].endswith('/src/script_manager.c'))
manager_flags, manager_source, _ = canonical(manager_entry.get('arguments') or shlex.split(manager_entry['command']))
run([*manager_flags, '-ivfsoverlay', vfs, '-O0', '-g0', '-Xclang', '-disable-O0-optnone',
     '-Xclang', '-disable-llvm-passes', '-S', '-emit-llvm', manager_source, '-o', legacy_manager])
run([llvm / 'llvm-extract', '-S', '--func=FieldSysGetAttrAddrInternal', legacy_manager, '-o', original_accessor])

fixture = out / 'slots.c'
fixture.write_text(r'''
#include "script.h"
#include <stddef.h>
extern void *FieldSysGetAttrAddrInternal(ScriptEnvironment *, int);
extern int make_task(int);
extern void consume_task(int);
extern void *direct_task(int);
typedef struct LinkSlots { void *anchor; int first; void *middle; int second; } LinkSlots;
void linked_create(LinkSlots *p) { p->first = (int)direct_task(0); p->second = p->first; p->first = 0; }
void linked_consume(LinkSlots *p) { consume_task(p->second); p->second = 0; }
static void *byte_selector(ScriptEnvironment *env, int selector) {
    switch ((unsigned char)selector) {
    case SCRIPTENV_ENGAGED_TRAINER_0_FIELD_18: return FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_0_FIELD_18);
    case SCRIPTENV_ENGAGED_TRAINER_1_FIELD_18: return FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_1_FIELD_18);
    default: return 0;
    }
}
void create_slots(ScriptEnvironment *env) {
    int *a = byte_selector(env, 256 + SCRIPTENV_ENGAGED_TRAINER_0_FIELD_18);
    int *b = byte_selector(env, 256 + SCRIPTENV_ENGAGED_TRAINER_1_FIELD_18);
    *a = make_task(0); *b = make_task(1);
}
void create_slots_direct(ScriptEnvironment *env) {
    int *a = FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_0_FIELD_18);
    int *b = FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_1_FIELD_18);
    *a = (int)direct_task(0); *b = (int)direct_task(1);
}
static int *alias(int *a) { return a; }
void release_slots(ScriptEnvironment *env) {
    int *a = alias(FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_0_FIELD_18));
    int *b = alias(FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_1_FIELD_18));
    consume_task(*a); *a = 0;
    consume_task(*b); *b = 0;
}
size_t native_record_size(void) { return sizeof(EngagedTrainer); }
size_t native_environment_size(void) { return sizeof(ScriptEnvironment); }
size_t native_slot_offset(void) { return offsetof(EngagedTrainer, approachTask); }
''')
provider = out / 'tasks.c'
provider.write_text(r'''
#include "script.h"
#include "sys_task.h"
#define assert(condition) do { if (!(condition)) { __builtin_printf("failed line %d: %s\n", __LINE__, #condition); exit(1); } } while (0)
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
void GF_AssertFail(void) { abort(); }
static SysTaskQueue *queue;
static SysTask *created[2];
static unsigned runs[2], removed;
static void tick(SysTask *task, void *arg) { unsigned i = *(unsigned *)arg; assert(task == created[i]); ++runs[i]; }
SysTask *make_task(int i) { static unsigned ids[2] = {0, 1}; created[i] = SysTaskQueue_InsertTask(queue, tick, &ids[i], i); assert((uintptr_t)created[i] > UINT32_MAX); return created[i]; }
SysTask *direct_task(int i) { return make_task(i); }
void consume_task(SysTask *task) { assert(task == created[removed]); assert(*(unsigned *)SysTask_GetData(task) == removed); assert(SysTask_Unlink(task)); ++removed; }
extern void create_slots(ScriptEnvironment *);
extern void create_slots_direct(ScriptEnvironment *);
extern void release_slots(ScriptEnvironment *);
typedef struct LinkSlots { void *anchor; int first; void *middle; int second; } LinkSlots;
extern void linked_create(LinkSlots *), linked_consume(LinkSlots *);
extern void *FieldSysGetAttrAddrInternal(ScriptEnvironment *, int);
extern size_t native_record_size(void), native_slot_offset(void), native_environment_size(void);
int main(void) {
    void *arena = calloc(1, SysTaskQueue_GetArenaSize(4)); assert(arena);
    queue = SysTaskQueue_PlacementNew(4, arena);
    ScriptEnvironment *env = calloc(1, sizeof(*env)); assert(env);
    assert(native_record_size() == sizeof(EngagedTrainer));
    assert(native_slot_offset() == offsetof(EngagedTrainer, approachTask));
    assert(native_environment_size() == sizeof(*env));
    assert(sizeof(EngagedTrainer) == 40 && offsetof(EngagedTrainer, approachTask) == 32);
    env->engagedTrainers[0].trainerId = 1234; env->engagedTrainers[1].trainerId = 5678;
    env->specialVars[0] = 0xBEEF;
    create_slots(env);
    void **a = FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_0_FIELD_18);
    void **b = FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_1_FIELD_18);
    assert(*a == created[0] && *b == created[1] && *a != *b);
    assert((char *)b - (char *)a == sizeof(EngagedTrainer));
    SysTaskQueue_RunTasks(queue); SysTaskQueue_RunTasks(queue);
    assert(runs[0] && runs[1]);
    release_slots(env);
    assert(!*a && !*b && removed == 2 && queue->activeCount == 0);
    removed = 0;
    LinkSlots linked = {0};
    linked_create(&linked);
    assert(*(void **)((char *)&linked + offsetof(LinkSlots, first)) == 0);
    assert(*(void **)((char *)&linked + offsetof(LinkSlots, second)) == created[0]);
    linked_consume(&linked);
    assert(removed == 1 && queue->activeCount == 0);
    assert(env->engagedTrainers[0].trainerId == 1234 && env->engagedTrainers[1].trainerId == 5678 && env->specialVars[0] == 0xBEEF);
    removed = 0;
    create_slots_direct(env);
    assert(*a == created[0] && *b == created[1]);
    release_slots(env);
    assert(!*a && !*b && removed == 2 && queue->activeCount == 0);
    free(env); free(arena); return 0;
}
''')

def emit(source, binary=False):
    ir = source.with_suffix('.bc' if binary else '.ll')
    run([*flags, '-ivfsoverlay', vfs, '-O0', '-g0', '-Xclang', '-disable-O0-optnone', '-Xclang', '-disable-llvm-passes', '-c' if binary else '-S', '-emit-llvm', source, '-o', ir])
    return ir

fixture_ir, provider_ir = emit(fixture), emit(provider)
# Keep the oracle's deliberate native byte-offset observations outside the
# program under transformation; retain the actual producer/consumer bodies.
provider_analysis = out / 'task-providers.ll'
run([llvm / 'llvm-extract', '-S', '--func=make_task', '--func=direct_task', '--func=consume_task', provider_ir, '-o', provider_analysis])
manifest = out / 'fixture-inputs.json'
manifest.write_text(json.dumps(list(map(str, (fixture_ir, provider_analysis, original_accessor, queue)))))
fixture_plan = out / 'fixture-plan.json'
run([lowerer, '--semantic-slots', 'analyze', manifest, fixture_plan])
assert has_task_slot(json.loads(fixture_plan.read_text()))
fixture_native = out / 'slots.promoted.ll'
run([lowerer, '--semantic-slots', 'apply', fixture_plan, fixture_ir, fixture_native])
# Production census now transports Apple-emitted bitcode. Apply the same plan
# through both readers and execute the bitcode-derived result below.
fixture_bc = emit(fixture, binary=True)
fixture_bc_native = out / 'slots.from-bitcode.ll'
run([lowerer, '--semantic-slots', 'apply', fixture_plan, fixture_bc, fixture_bc_native])
def without_module_id(path):
    text = path.read_text()
    # LLVM 23 upgrades Apple's older bitcode with explicit defaults for these
    # nonnative address spaces. This fixture uses none of them. Require all
    # other layout fields and every instruction to remain exactly equal.
    assert not re.search(r'addrspace\((270|271|272)\)', text)
    text = text.replace('-p270:32:32-p271:32:32-p272:64:64', '')
    return '\n'.join(line for line in text.splitlines() if not line.startswith('; ModuleID ='))
assert without_module_id(fixture_native) == without_module_id(fixture_bc_native)
run([llvm / 'llvm-diff', fixture_native, fixture_bc_native])
fixture_native = fixture_bc_native
forged_provider = out / 'forged-provider.c'
forged_provider.write_text('int forged_task(void) { return 7; }\n')
forged_ir = emit(forged_provider)
negative_results = []
for name, body in {
    'raw_copy': 'void observe(ScriptEnvironment *env, void *dst) { env->engagedTrainers[0].trainerId = 9; __builtin_memcpy(dst, env, sizeof(*env)); }',
    'fixed_offset': 'void *observe(ScriptEnvironment *env) { return (char *)FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_0_FIELD_18) + 1; }',
    'integer_observation': 'int observe(ScriptEnvironment *env) { return *(int *)FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_0_FIELD_18) + 1; }',
    'unknown_alias': 'extern void external_bytes(void *); void observe(ScriptEnvironment *env) { external_bytes(FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_0_FIELD_18)); }',
    'unknown_owner': 'extern void external_bytes(void *); void observe(ScriptEnvironment *env) { env->engagedTrainers[0].trainerId = 9; external_bytes(env); }',
    'shared_subtype_owner': 'struct Pair { ScriptEnvironment first, second; }; struct Owner { struct Pair branches[2]; }; extern void external_bytes(void *); void observe(struct Owner *p) { p->branches[0].first.engagedTrainers[0].trainerId = 9; external_bytes(p); }',
    'integer_carried_owner': 'extern void external_bytes(void *); void observe(ScriptEnvironment *env) { env->engagedTrainers[0].trainerId = 9; __UINTPTR_TYPE__ address = (__UINTPTR_TYPE__)env; external_bytes((void *)(address + 4)); }',
    'partial_clear': 'void observe(ScriptEnvironment *env) { env->engagedTrainers[0].trainerId = 9; __builtin_memset(env, 0, sizeof(*env)-1); }',
    'nonzero_clear': 'void observe(ScriptEnvironment *env) { env->engagedTrainers[0].trainerId = 9; __builtin_memset(env, 255, sizeof(*env)); }',
    'logical_guest_word': 'void observe(ScriptEnvironment *env) { *(int *)FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_0_FIELD_18) = (int)(void *)(__UINTPTR_TYPE__)0x02000100u; }',
    'conflicting_return': 'extern void *forged_task(void); void observe(ScriptEnvironment *env) { *(int *)FieldSysGetAttrAddrInternal(env, SCRIPTENV_ENGAGED_TRAINER_0_FIELD_18) = (int)forged_task(); }',
    'constant_alias': 'extern ScriptEnvironment global_environment; static int *slot_alias = &global_environment.engagedTrainers[0].approachTask; int observe(void) { return *slot_alias + 1; }',
}.items():
    source = out / (name + '.c')
    source.write_text('#include "script.h"\nextern void *FieldSysGetAttrAddrInternal(ScriptEnvironment *, int);\n' + body + '\n')
    ir = emit(source)
    manifest.write_text(json.dumps(list(map(str, (fixture_ir, provider_analysis, original_accessor, queue, forged_ir, ir)))))
    rejected = out / (name + '.plan.json')
    run([lowerer, '--semantic-slots', 'analyze', manifest, rejected])
    report = json.loads(rejected.read_text())
    assert not has_task_slot(report), name
    assert any(r['struct'] == 'struct.EngagedTrainer' and r['reasons'] for r in report['blocked']), name
    negative_results.append(name)
source = out / 'component_observation.c'
source.write_text('typedef struct LinkSlots { void *anchor; int first; void *middle; int second; } LinkSlots;\nint observe(LinkSlots *p) { return p->second + 1; }\n')
ir = emit(source)
manifest.write_text(json.dumps(list(map(str, (fixture_ir, provider_analysis, original_accessor, queue, ir)))))
rejected = out / 'component_observation.plan.json'
run([lowerer, '--semantic-slots', 'analyze', manifest, rejected])
report = json.loads(rejected.read_text())
assert has_task_slot(report), 'an independent storage component stays admissible'
assert not any(r['struct'] == 'struct.LinkSlots' for r in report['slots'])
assert len([r for r in report['blocked'] if r['struct'] == 'struct.LinkSlots']) == 2
negative_results.append('connected_component_observation')
# The guest frontend receives the same untouched original header. Its logical
# record extent and slot offset must stay DS-sized, independently of native IR.
ds = out / 'ds_layout.c'
ds.write_text('#include "script.h"\n_Static_assert(sizeof(EngagedTrainer)==28,"DS extent");\n_Static_assert(__builtin_offsetof(EngagedTrainer,approachTask)==24,"DS slot");\n')
from frontend import flags as guest_flags
run([llvm / 'clang', *guest_flags(ROOT / 'upstream/pokeheartgold', build), '-fsyntax-only', ds])
results = []
for optimization in ('O0', 'O2'):
    objects = []
    for i, ir in enumerate((fixture_native, provider_ir, accessor, queue)):
        obj = out / (optimization + '.' + str(i) + '.o')
        run([flags[0], '-' + optimization, '-c', ir, '-o', obj])
        objects.append(obj)
    exe = out / ('tasks.' + optimization)
    run([flags[0], '-' + optimization, '-Wl,-dead_strip', *objects, '-o', exe])
    run([exe])
    # Validate optimized production IR as well as executing the separate-TU
    # original-accessor/task-queue lifetime fixture.
    optimized = out / ('battle.' + optimization + '.ll')
    run([llvm / 'opt', '-' + optimization, '-S', battle.with_suffix('.promoted.ll'), '-o', optimized])
    text = optimized.read_text()
    assert 'ptrtoint ptr' not in re.search(r'define [^\n]*@ScrCmd_GetTrainerPathToPlayer\(.*?^}', text, re.S | re.M)[0]
    results.append(dict(optimization=optimization, original_accessor=True, original_task_queue=True, task_lifetime=True, ds_layout_preserved=True))
(out / 'results.json').write_text(json.dumps(dict(execution=results, rejected=negative_results), indent=2) + '\n')
print('PASS: original accessor, both native pointer slots, real task queue/lifetime and DS layout at O0/O2')

# The source frontend is shared with production codegen. Optimization-dependent
# preprocessing, a native record passed by value, varargs and debug information
# must survive that handoff; a changed bitcode receipt must reject codegen.
handoff = out / 'frontend-handoff.c'
handoff.write_text(r'''
typedef struct Native { long integer; double real; void *pointer; } Native;
static long payload=17;
static __attribute__((noinline)) long evaluate(Native value, ...) {
    __builtin_va_list args; __builtin_va_start(args,value);
    long extra=__builtin_va_arg(args,long); __builtin_va_end(args);
    return value.integer+(long)value.real+*(long *)value.pointer+extra;
}
int main(void) {
    Native value={3,5.0,&payload};
    if(evaluate(value,7L)!=32)return 1;
#ifdef __OPTIMIZE__
    return EXPECT_OPTIMIZED!=1;
#else
    return EXPECT_OPTIMIZED!=0;
#endif
}
''')
for level in ('O0', 'O2'):
    common=[flags[0], '-'+level, '-g', '-fPIC', '-DEXPECT_OPTIMIZED='+str(int(level=='O2'))]
    for option in ('-arch','-isysroot','-target'):
        if option in flags:
            index=flags.index(option);common+=flags[index:index+2]
    source_object=out/('handoff.source.'+level+'.o')
    ir_object=out/('handoff.ir.'+level+'.o')
    bitcode=out/('handoff.'+level+'.bc')
    run([*common,'-c',handoff,'-o',source_object])
    run([*common,'-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes',
         '-emit-llvm','-c',handoff,'-o',bitcode])
    command=list(map(str,[*common,'-c',handoff,'-o',ir_object]))
    receipt=out/('handoff.'+level+'.json')
    receipt.write_text(json.dumps({identity(command):dict(source=str(handoff),
        transformed=False,ir=str(bitcode),ir_sha256=hashlib.sha256(bitcode.read_bytes()).hexdigest())}))
    assert launch(receipt,command)==0
    for kind,obj in [('source',source_object),('ir',ir_object)]:
        exe=out/('handoff.'+kind+'.'+level)
        run([*common,obj,'-o',exe]);run([exe])
    original=bitcode.read_bytes();object_hash=hashlib.sha256(ir_object.read_bytes()).hexdigest()
    bitcode.write_bytes(original+b'changed')
    try:
        launch(receipt,command)
    except RuntimeError as error:
        assert 'IR receipt changed' in str(error)
    else:
        raise AssertionError('changed bitcode reached production codegen')
    finally:
        bitcode.write_bytes(original)
    assert hashlib.sha256(ir_object.read_bytes()).hexdigest()==object_hash
print('PASS: one native frontend, optimization macros, record/varargs ABI and corrupted-bitcode rejection')
