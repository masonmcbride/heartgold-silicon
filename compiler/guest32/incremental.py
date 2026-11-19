"""Content-validated local receipts for original guest compilation stages."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def file_identity(path):
    s=Path(path).stat()
    return s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns

def snapshot_tools(paths):
    result={}
    for path in paths:
        path=str(path);before=file_identity(path);sha=digest(path)
        if file_identity(path)!=before:raise ValueError('compiler changed during snapshot: '+path)
        result[path]=(before,sha)
    return result

def verify_tools(tools, kind='compiler'):
    for path,(identity,sha) in tools.items():
        if file_identity(path)!=identity or digest(path)!=sha or file_identity(path)!=identity:
            raise ValueError(kind+' changed during image compilation: '+path)


def dependency_paths(text):
    """Keep Make escaping, with a linear native fast path for plain paths."""
    _, separator, body = text.replace('\\\n', '').partition(':')
    if not separator:
        raise ValueError('compiler depfile lacks a target separator')
    # For ASCII without shell quoting or escapes, split and shlex have exactly
    # the same token boundaries. Exotic filenames retain the original parser.
    if body.isascii() and not any(char in body for char in ('\\', "'", '"', '\v', '\f', '\x1c', '\x1d', '\x1e', '\x1f')):
        return body.split()
    return shlex.split(body)


class Pending:
    """One validated, declared command awaiting execution or batch submission."""
    def __init__(self, command, finish):
        self.command, self.finish = command, finish

    def execute(self):
        started = time.perf_counter()
        result = subprocess.run(self.command, capture_output=True, text=True)
        return self.finish(result, time.perf_counter()-started)


def prepare(command, outputs, inputs=(), depfile=None, virtual_files=None, tool_snapshot=None, input_snapshot=None, resolved_paths=None):
    """Cache only successful commands, validating outputs as well as inputs.

    A failed command never receives a receipt. Existing successful outputs are
    not enough to bypass changed source, headers, compiler or ABI contracts.
    """
    started = time.perf_counter()
    def input_digest(path):
        if tool_snapshot is not None and str(path)==command[0]:
            identity,sha=tool_snapshot
            if file_identity(path)!=identity:raise ValueError('compiler changed: '+str(path))
            return sha
        if input_snapshot is not None:
            key=str(path);identity=file_identity(path)
            previous=input_snapshot.get(key)
            if previous is not None:
                if previous[0]!=identity:raise ValueError('input changed during image compilation: '+key)
                return previous[1]
            sha=digest(path)
            if file_identity(path)!=identity:raise ValueError('input changed while reading: '+key)
            if input_snapshot.setdefault(key,(identity,sha))!=(identity,sha):
                raise ValueError('input changed between compiler workers: '+key)
            return sha
        return digest(path)
    environment = {key: os.environ.get(key) for key in (
        'SDKROOT', 'MACOSX_DEPLOYMENT_TARGET', 'CPATH', 'C_INCLUDE_PATH',
        'CPLUS_INCLUDE_PATH', 'LIBRARY_PATH')}
    outputs = list(map(Path, outputs))
    receipt = outputs[0].with_name(outputs[0].name+'.receipt.json')
    dependencies = [Path(command[0]), *map(Path, inputs)]
    def resolved(path):
        if resolved_paths is None:
            return Path(path).resolve()
        key=str(path);identity=file_identity(path)
        previous=resolved_paths.get(key)
        if previous is not None and previous[0]==identity:
            return previous[1]
        value=Path(path).resolve()
        resolved_paths[key]=(identity,value)
        return value
    virtual_files={str(resolved(k)):Path(v) for k,v in (virtual_files or {}).items()}
    def effective(paths):
        if not virtual_files:return list(map(Path,paths))
        return [virtual_files.get(str(resolved(p)),Path(p)) for p in paths]
    def compiler_dependencies():
        return list(map(Path,dependency_paths(Path(depfile).read_text())))
    previous = json.loads(receipt.read_text()) if receipt.exists() else None
    if (previous and previous['command'] == command and
        previous.get('environment') == environment and previous.get('directory') == str(Path.cwd())):
        try:
            if virtual_files and depfile:
                # Clang's depfile keeps canonical virtual paths when VFS uses
                # use-external-name:false. Hash the effective bytes, not the
                # unchanged upstream header hidden behind those paths. Ignore
                # unrelated files from older coarse VFS receipts.
                dependencies=effective([*dependencies,*compiler_dependencies()])
            else:
                dependencies.extend(map(Path, previous['inputs']))
            current = {str(p): input_digest(p) for p in dependencies}
            matches=(all(previous['inputs'].get(k)==v for k,v in current.items())
                     if virtual_files else current==previous['inputs'])
            if (matches and
                {str(p): digest(p) for p in outputs} == previous['outputs']):
                result = subprocess.CompletedProcess(command, 0, previous['stdout'], previous['stderr'])
                result.cache_hit = True
                result.execution_seconds = 0.0
                result.validation_seconds = time.perf_counter()-started
                result.wall_seconds = result.validation_seconds
                return result
        except FileNotFoundError:
            pass
    dependencies = [Path(command[0]), *map(Path, inputs)]
    # Invalidate before invoking a command that might partially overwrite output.
    receipt.unlink(missing_ok=True)
    before = {str(p): input_digest(p) for p in effective(dependencies)}
    validation_seconds = time.perf_counter()-started
    def finish(result, execution_seconds):
        receipt_started = time.perf_counter()
        if result.returncode == 0:
            if any(input_digest(p) != sha for p, sha in before.items()):
                raise ValueError('input changed during declared compilation')
            paths = [*dependencies, *(compiler_dependencies() if depfile else [])]
            record = dict(command=command, environment=environment, directory=str(Path.cwd()),
                          inputs={str(p): input_digest(p) for p in effective(paths)},
                          outputs={str(p): digest(p) for p in outputs},
                          stdout=result.stdout, stderr=result.stderr)
            receipt.write_text(json.dumps(record, sort_keys=True)+'\n')
        result.cache_hit = False
        result.execution_seconds = execution_seconds
        result.validation_seconds = validation_seconds
        result.wall_seconds = validation_seconds+execution_seconds+time.perf_counter()-receipt_started
        return result
    return Pending(command, finish)


def run(*args, **kwargs):
    result = prepare(*args, **kwargs)
    return result.execute() if isinstance(result, Pending) else result
