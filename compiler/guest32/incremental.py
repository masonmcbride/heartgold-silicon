"""Content-validated local receipts for original guest compilation stages."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command, outputs, inputs=(), depfile=None):
    """Cache only successful commands, validating outputs as well as inputs.

    A failed command never receives a receipt. Existing successful outputs are
    not enough to bypass changed source, headers, compiler or ABI contracts.
    """
    environment = {key: os.environ.get(key) for key in (
        'SDKROOT', 'MACOSX_DEPLOYMENT_TARGET', 'CPATH', 'C_INCLUDE_PATH',
        'CPLUS_INCLUDE_PATH', 'LIBRARY_PATH')}
    outputs = list(map(Path, outputs))
    receipt = outputs[0].with_name(outputs[0].name+'.receipt.json')
    dependencies = [Path(command[0]), *map(Path, inputs)]
    previous = json.loads(receipt.read_text()) if receipt.exists() else None
    if (previous and previous['command'] == command and
        previous.get('environment') == environment and previous.get('directory') == str(Path.cwd())):
        try:
            dependencies.extend(map(Path, previous['inputs']))
            current = {str(p): digest(p) for p in dependencies}
            if (current == previous['inputs'] and
                {str(p): digest(p) for p in outputs} == previous['outputs']):
                return subprocess.CompletedProcess(command, 0, previous['stdout'], previous['stderr'])
        except FileNotFoundError:
            pass
    dependencies = [Path(command[0]), *map(Path, inputs)]
    # Invalidate before invoking a command that might partially overwrite output.
    receipt.unlink(missing_ok=True)
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        if depfile:
            text = Path(depfile).read_text().replace('\\\n', '')
            dependencies.extend(map(Path, shlex.split(text.split(':', 1)[1])))
        record = dict(command=command, environment=environment, directory=str(Path.cwd()), inputs={str(p): digest(p) for p in dependencies},
                      outputs={str(p): digest(p) for p in outputs},
                      stdout=result.stdout, stderr=result.stderr)
        receipt.write_text(json.dumps(record, sort_keys=True)+'\n')
    return result
