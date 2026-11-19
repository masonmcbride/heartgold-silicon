"""Opt-in subprocess observation for a single build diagnostic. MIT."""
import os

if os.environ.get('HEARTGOLD_RUN_TRACE'):
    import json
    import subprocess
    import time
    from pathlib import Path

    _original = subprocess.Popen

    class _ObservedPopen(_original):
        def __init__(self, *args, **kwargs):
            self._trace_start = time.monotonic()
            self._trace_written = False
            self._trace_cwd = os.fsdecode(kwargs.get('cwd') or os.getcwd())
            super().__init__(*args, **kwargs)

        def _trace_finish(self):
            if self.returncode is None or self._trace_written:
                return
            self._trace_written = True
            end = time.monotonic()
            command = self.args
            if isinstance(command, (str, bytes)):
                command = [os.fsdecode(command)]
            else:
                command = [os.fsdecode(arg) for arg in command]
            record = dict(start=self._trace_start, end=end, pid=self.pid,
                parent_pid=os.getpid(), phase=os.environ.get('HEARTGOLD_TRACE_PHASE'),
                command=command, directory=self._trace_cwd, status=self.returncode)
            try:
                path = Path(os.environ['HEARTGOLD_RUN_TRACE']) / 'subprocesses'
                (path / f'{os.getpid()}-{self.pid}-{time.monotonic_ns()}.json').write_text(json.dumps(record)+'\n')
            except OSError as error:
                # Observation must not turn a successful tool into a failed tool.
                import sys
                print(f'Build trace write failed: {error}', file=sys.stderr)

        def poll(self):
            result = super().poll()
            self._trace_finish()
            return result

        def wait(self, timeout=None):
            try:
                return super().wait(timeout=timeout)
            finally:
                self._trace_finish()

    subprocess.Popen = _ObservedPopen
