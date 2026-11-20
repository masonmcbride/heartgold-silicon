"""Content-validated sharing of identical original guest frontend emissions."""
import json
from pathlib import Path

def compile_shared(command, output, build, *, inputs, depfile, virtual_files, **validation):
    """Emit identical guest frontends once, retaining each image's own receipt.

    Only output locations and equivalent private VFS locations are normalized.
    Target/language flags, working directory, environment, tools and transitive
    dependency contents still participate in the ordinary receipt validation.
    """
    import fcntl
    import hashlib
    import subprocess
    import time
    from incremental import Pending, prepare, run
    started = time.perf_counter()
    operation = prepare(command, [output], inputs=[*inputs,*virtual_files.values()], depfile=depfile,
                        virtual_files=virtual_files, **validation)
    if not isinstance(operation, Pending):
        operation.shared_frontend_hit = False
        return operation
    normalized = list(command)
    for flag in ('-o', '-MF'):
        normalized[normalized.index(flag)+1] = flag + ':output'
    overlay = None
    if '-ivfsoverlay' in normalized:
        index = normalized.index('-ivfsoverlay')+1
        overlay = json.loads(Path(command[index]).read_text())
        expected = dict(version=0, roots=[dict(type='file', name=name,
            **{'external-contents':str(path), 'use-external-name':False})
            for name,path in virtual_files.items()])
        if overlay != expected:
            # Unknown VFS semantics keep the original compile path.
            return operation.execute()
        normalized[index] = '-ivfsoverlay:private'
    virtual = [(name, Path(path).read_bytes()) for name,path in virtual_files.items()]
    key = hashlib.sha256(json.dumps([normalized, str(Path.cwd()),
        [(name, hashlib.sha256(data).hexdigest()) for name,data in virtual]],
        sort_keys=True).encode()).hexdigest()
    directory = Path(build)/'guest32-frontend'/key
    directory.mkdir(parents=True, exist_ok=True)
    def write_bytes(path, data):
        if not path.exists() or path.read_bytes() != data:
            pending = path.with_name(path.name+'.pending')
            pending.write_bytes(data)
            pending.replace(path)
    with (directory/'compile.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        shared_command = list(command)
        shared_ir, shared_dep = directory/'guest.bc', directory/'guest.d'
        shared_command[shared_command.index('-o')+1] = str(shared_ir)
        shared_command[shared_command.index('-MF')+1] = str(shared_dep)
        shared_virtual = {}
        shared_inputs = list(inputs)
        if overlay is not None:
            for i, (name, data) in enumerate(virtual):
                path = directory/f'virtual-{i}'
                write_bytes(path, data)
                shared_virtual[name] = path
                overlay['roots'][i]['external-contents'] = str(path)
            overlay_path = directory/'frontend.json'
            write_bytes(overlay_path, json.dumps(overlay).encode())
            shared_command[shared_command.index('-ivfsoverlay')+1] = str(overlay_path)
            shared_inputs.append(overlay_path)
        result = run(shared_command, [shared_ir], inputs=shared_inputs,
                     depfile=shared_dep, virtual_files=shared_virtual, **validation)
        if result.returncode == 0:
            write_bytes(Path(output), shared_ir.read_bytes())
            # Compiler prerequisites retain original virtual names. Each image
            # owns its depfile target and its normal content-validated receipt.
            _, separator, prerequisites = shared_dep.read_text().partition(':')
            if not separator:
                raise ValueError('shared frontend depfile lacks a target')
            target = str(output).replace('\\','\\\\').replace(' ','\\ ').replace('#','\\#').replace('$','$$')
            write_bytes(Path(depfile), (target+':'+prerequisites).encode())
        reused = result.cache_hit
        result = operation.finish(subprocess.CompletedProcess(command, result.returncode,
            result.stdout, result.stderr), result.execution_seconds)
        result.shared_frontend_hit = reused
        result.wall_seconds = time.perf_counter()-started
        return result

