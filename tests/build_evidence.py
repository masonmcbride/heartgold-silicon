"""Read production compile options across CMake generators."""
import json
from pathlib import Path
import shlex


def compile_options(build, target):
    entries = json.loads((Path(build) / 'compile_commands.json').read_text())
    marker = 'CMakeFiles/' + target + '.dir/'
    entry = next(e for e in entries if marker in
                 ' '.join(e.get('arguments') or shlex.split(e['command'])))
    command = entry.get('arguments') or shlex.split(entry['command'])
    options = []
    skip = False
    for value in command[1:]:
        if skip:
            skip = False
            continue
        if value in ('-o', '-MF', '-MT', '-MQ'):
            skip = True
            continue
        if value not in ('-c', '-MD', '-MMD', '-MP', entry['file']):
            options.append(value)
    return options
