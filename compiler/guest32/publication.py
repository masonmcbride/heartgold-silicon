"""Transactional, single-writer publication of guest32 closure generations. MIT."""
import ctypes
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def exchange(left, right):
    """Exchange complete directories atomically; fail closed without OS support."""
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == 'darwin':
        fn = libc.renamex_np
        fn.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        args = (os.fsencode(left), os.fsencode(right), 2)  # RENAME_SWAP
    elif sys.platform.startswith('linux'):
        fn = libc.renameat2
        fn.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                       ctypes.c_char_p, ctypes.c_uint)
        args = (-100, os.fsencode(left), -100, os.fsencode(right), 2)
    else:
        raise RuntimeError('Atomic directory exchange unavailable')
    if fn(*args):
        raise OSError(ctypes.get_errno(), 'Atomic closure publication failed')


def relocate(directory, old, new):
    """Rebase generated text, never object bytes; invalidate compilation receipts.

    Receipts hash effective source and ABI bytes. Rewriting their paths cannot
    establish those hashes, so the next invocation must validate by rebuilding.
    """
    for path in directory.rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        if path.name.endswith('.receipt.json'):
            path.unlink()
        elif path.suffix in ('.json', '.ll', '.c', '.d', '.log', '.txt'):
            data = path.read_bytes()
            changed = data.replace(os.fsencode(old), os.fsencode(new))
            if changed != data:
                path.write_bytes(changed)


def require_successful_compilations(results):
    failed=[r['member'] for r in results
            if not (r['compiled'] or r.get('hardware_adapted')) and r.get('attempted',True)]
    if failed:
        raise ValueError('Failed compilations cannot be published: '+str(sorted(failed)))


def publish(out, worker):
    """Run in an independent generation. Exceptions never change the published tree."""
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with (out.parent / (out.name + '.publication.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        stage = Path(tempfile.mkdtemp(prefix=out.name + '.pending-', dir=out.parent))
        try:
            if out.exists():
                # APFS clone-on-write avoids hard links: compiler truncation must
                # never modify the previous generation's inodes.
                if sys.platform == 'darwin':
                    subprocess.run(['cp', '-cR', str(out) + '/.', str(stage)], check=True)
                else:
                    shutil.copytree(out, stage, dirs_exist_ok=True)
                relocate(stage, out, stage)
            worker(stage)
            relocate(stage, stage, out)
            if out.exists():
                exchange(stage, out)
                previous = stage.with_name(stage.name.replace('.pending-', '.previous-', 1))
                stage.rename(previous)
            else:
                stage.rename(out)
        except BaseException as error:
            # Keep diagnostics and every last valid canonical byte untouched.
            (stage / 'publication-failure.json').write_text(json.dumps({
                'published': False, 'canonical': str(out),
                'error': str(error), 'type': type(error).__name__,
            }, indent=2) + '\n')
            print('Closure not published; diagnostics: ' + str(stage), file=sys.stderr)
            raise
