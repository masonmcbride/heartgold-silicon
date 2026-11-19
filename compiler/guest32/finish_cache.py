"""Local, filesystem-identity receipt for an unchanged provider generation.

This receipt is deliberately not portable: inode, ctime and nanosecond mtime
must all match. A cache miss retains the full content-validating build. Walk
directories again on every check so additions and removals invalidate too.
"""
import json
import os
from pathlib import Path
import sys
import time


def identity(path):
    try:
        s = os.stat(path)
    except FileNotFoundError:
        return None
    return [s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def tree(root):
    result = {}
    if not root.exists():
        return {str(root): None}
    for directory, dirs, files in os.walk(root, followlinks=True):
        dirs[:] = sorted(d for d in dirs if d not in ('.git', '__pycache__', 'build'))
        for name in sorted(files):
            if name.endswith('.pyc'):
                continue
            path = os.path.join(directory, name)
            result[path] = identity(path)
    return result


class FinishCache:
    def __init__(self, args, root):
        self.args, self.root = args, root
        self.path = args.out.with_name(args.out.name + '.finish-receipt.json')
        self.started = time.perf_counter()
        self.before = None

    def inputs(self):
        a = self.args
        paths = [self.root/'CMakeLists.txt', a.provider_plan, a.lowerer,
                 a.codegen, Path(a.compiler), Path(sys.executable),
                 Path('/usr/bin/otool'), Path('/usr/bin/xcrun')]
        paths += [a.llvm_bin/name for name in ('clang', 'llvm-ar', 'llvm-nm')]
        contract = a.build/'guest32-compiler/codegen-inputs.json'
        paths.append(contract)
        if contract.exists():
            paths.extend(map(Path, json.loads(contract.read_text())['libraries']))
        paths.extend(a.build.glob('libheartgold_guest32_*.a'))
        registry = a.build/'native-overlays/provider-registry.json'
        paths.append(registry)
        if registry.exists():
            paths.extend(Path(d['artifact']) for d in json.loads(registry.read_text())['definitions']
                         if d['image_owner'] == 'main' and d['abi_representation'] == 'native-arm64')
        result = {str(p): identity(p) for p in paths}
        # Full source/recipe trees are conservative, including new headers and
        # source-selection contracts; stable backend caches are not inputs.
        for directory in (a.game, self.root/'compiler', self.root/'cmake',
                          self.root/'hardware_drivers', a.build/'include',
                          a.build/'generated/files', a.image_root,
                          *(a.build/('guest32-'+n) for n in ('account', 'crc', 'std', 'mi'))):
            result.update(tree(directory))
        return result

    def context(self):
        return dict(arguments={k: str(v) if isinstance(v, Path) else v
                               for k, v in vars(self.args).items()},
                    directory=os.getcwd(), environment={k: os.environ.get(k) for k in (
                        'SDKROOT', 'DEVELOPER_DIR', 'MACOSX_DEPLOYMENT_TARGET',
                        'CPATH', 'C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'LIBRARY_PATH',
                        'PATH', 'DYLD_LIBRARY_PATH', 'DYLD_FRAMEWORK_PATH')})

    def reuse(self, out):
        self.before = self.inputs()
        try:
            previous = json.loads(self.path.read_text())
        except (OSError, ValueError):
            previous = None
        # User-supplied search paths can add undeclared external headers/libs.
        external = any(os.environ.get(k) for k in (
            'CPATH', 'C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'LIBRARY_PATH',
            'DYLD_LIBRARY_PATH', 'DYLD_FRAMEWORK_PATH'))
        if (not external and previous and previous.get('version') == 1 and
                previous['context'] == self.context() and
                previous['inputs'] == self.before and
                (out/'complete.stamp').is_file() and previous['outputs'] == tree(out)):
            print(f'Provider finish: unchanged generation verified in {time.perf_counter()-self.started:.3f}s', flush=True)
            return True
        self.path.unlink(missing_ok=True)
        return False

    def record(self):
        # Called under the same publication lock, after the atomic exchange.
        if self.inputs() != self.before:
            # Publication succeeded, but changing inputs cannot earn reuse.
            return
        record = dict(version=1, context=self.context(), inputs=self.before,
                      outputs=tree(self.args.out))
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(record, separators=(',', ':'))+'\n')
        temporary.replace(self.path)
