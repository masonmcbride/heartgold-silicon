"""Required sprite registration must survive the production assertion settings."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build', type=Path, required=True)
build = p.parse_args().build.resolve()
work = build / 'sprite-registration-test'
work.mkdir(parents=True, exist_ok=True)
entries = json.loads((build / 'compile_commands.json').read_text())

def arguments(entry):
    return entry.get('arguments') or shlex.split(entry['command'])

# Overlays inherit the same original game definition as the resident image.
game_entries = [e for e in entries if '-DHEARTGOLD' in arguments(e)]
assert game_entries
for entry in game_entries:
    assert '-DPM_KEEP_ASSERTS' in arguments(entry), entry['file']

entry = next(e for e in game_entries if e['file'].endswith('/src/sprite_transfer.c'))
args = arguments(entry)
flags = []
skip = False
for arg in args[1:]:
    if skip:
        skip = False
        continue
    if arg in ('-o', '-MF', '-MT', '-MQ'):
        skip = True
        continue
    if arg not in ('-c', '-MD', '-MMD', entry['file']):
        flags.append(arg)

pairs = {
    'SpriteTransfer_CreateAllCharTransferTasks': 'SpriteTransfer_CreateCharTransferTask',
    'SpriteTransfer_CreateAllCharTransferTasks_AllocAtEnd': 'SpriteTransfer_CreateCharTransferTask_AllocAtEnd',
    'SpriteTransfer_SpriteTransfer_CreateAllCharTransferTasks_UpdateMappingTypeFromHW_AllocAtEnd':
        'SpriteTransfer_CreateCharTransferTask_UpdateMappingTypeFromHW_AllocAtEnd',
    'SpriteTransfer_CreateAllExtPlttTransferTasks': 'SpriteTransfer_CreateExtPlttTransferTask',
    'SpriteTransfer_CreateAllPlttTransferTasks': 'SpriteTransfer_CreatePlttTransferTask',
}
for enabled in (True, False):
    output = work / ('production.ll' if enabled else 'without-asserts.ll')
    cmd = [args[0], *flags, *([] if enabled else ['-UPM_KEEP_ASSERTS']),
           '-O0', '-S', '-emit-llvm', entry['file'], '-o', str(output)]
    subprocess.run(cmd, cwd=entry['directory'], check=True, capture_output=True, text=True)
    ir = output.read_text()
    for batch, single in pairs.items():
        body = re.search(r'^define[^\n]*@' + batch + r'\(.*?^}', ir, re.M | re.S)
        assert body, batch
        calls = bool(re.search(r'\bcall\b[^\n]*@' + single + r'\(', body[0]))
        assert calls == enabled, (batch, enabled)
print('All five original sprite-registration loops retain their calls; disabled-assert control reproduces the omission.')
