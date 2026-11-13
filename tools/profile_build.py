#!/usr/bin/env python3
"""Live CMake build progress and lightweight timing profiler."""

import argparse
import json
import re
import selectors
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--build", default="build")
parser.add_argument("--target", default="heartgold")
parser.add_argument("-j", "--jobs", type=int, default=8)
args = parser.parse_args()

root = Path(args.build)
root.mkdir(parents=True, exist_ok=True)

log_path = root / "profile-build.log"
report_path = root / "profile-build.json"

command = [
    "cmake", "--build", str(root),
    "--target", args.target,
    "--parallel", str(args.jobs),
]

progress_pattern = re.compile(r"\[\s*(\d+)%\]")
ninja_pattern = re.compile(r"\[(\d+)/(\d+)\]")

counts = Counter()
phase_times = Counter()
recent_errors = []
events = []
start = time.monotonic()
last_event_time = start
last_report = start
last_percent = None
phase = "Starting"
percent = None

def classify(line):
    s = line.lower()
    if "linking " in s or "linking c" in s:
        return "Linking"
    if "building c" in s or "compiling " in s:
        return "Compiling"
    if "generating " in s:
        return "Generating"
    if "built target " in s:
        return "Target completed"
    if "scanning dependencies" in s:
        return "Dependencies"
    if "error:" in s or "undefined symbols" in s:
        return "Error"
    return None

def display(force=False):
    global last_report
    now = time.monotonic()
    if not force and now - last_report < 12:
        return

    elapsed = now - start
    value = percent or 0
    filled = int(value / 5)
    bar = "█" * filled + "░" * (20 - filled)

    print(
        f"[{bar}] {value:3}% "
        f"| {elapsed:7.1f}s "
        f"| {phase:<16} "
        f"| compile {counts['Compiling']} "
        f"| link {counts['Linking']} "
        f"| generate {counts['Generating']}",
        flush=True,
    )
    last_report = now

print("=== HEARTGOLD BUILD PROFILER ===")
print("Command:", " ".join(command))
print("Log:", log_path)
print("Report:", report_path)
print("Progress is CMake/Make progress, not remaining-time prediction.")
print(flush=True)

with log_path.open("w") as log:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)

    try:
        while True:
            ready = selector.select(timeout=1.0)

            if not ready:
                display()
                if process.poll() is not None:
                    break
                continue

            line = process.stdout.readline()

            if not line:
                break

            log.write(line)
            log.flush()

            now = time.monotonic()
            new_phase = classify(line)

            if new_phase:
                phase_times[phase] += now - last_event_time
                phase = new_phase
                last_event_time = now
                counts[new_phase] += 1

                if len(events) < 100000:
                    events.append({
                        "seconds": round(now - start, 3),
                        "phase": phase,
                        "text": line.strip()[:240],
                    })

            match = progress_pattern.search(line)
            ninja_match = ninja_pattern.search(line)

            if ninja_match:
                done, total = map(int, ninja_match.groups())
                percent = int(100 * done / total)
            elif match:
                percent = int(match.group(1))

            if percent is not None:
                boundary = percent // 10
                if boundary != last_percent:
                    last_percent = boundary
                    display(force=True)

            if any(x in line.lower() for x in (
                "error:", "undefined symbols",
                "failed:", "no rule to make target",
            )):
                recent_errors.append(line.rstrip()[:240])
                recent_errors = recent_errors[-30:]

            display()

    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        raise

    finally:
        selector.close()

    returncode = process.wait()

elapsed = time.monotonic() - start
phase_times[phase] += time.monotonic() - last_event_time

report = {
    "timestamp": datetime.now().astimezone().isoformat(),
    "command": command,
    "exit_code": returncode,
    "elapsed_seconds": round(elapsed, 3),
    "observed_operation_counts": dict(counts),
    "time_between_observed_events_seconds": {
        k: round(v, 3) for k, v in phase_times.items()
    },
    "events": events,
}

report_path.write_text(json.dumps(report, indent=2) + "\n")

print()
print("=== BUILD PROFILE SUMMARY ===")
print("Result:", "SUCCESS" if returncode == 0 else "FAILED")
print(f"Total wall time: {elapsed:.2f}s")
print("Observed compilation events:", counts["Compiling"])
print("Observed link events:", counts["Linking"])
print("Observed generation events:", counts["Generating"])

print()
print("=== ERRORS ===")
if recent_errors:
    for line in recent_errors[-16:]:
        print(line)
else:
    print("No compiler/linker errors detected.")

print()
print("Full log:", log_path)
print("Timing report:", report_path)
print("Existing canonical checkpoint was not modified.")

sys.exit(returncode)
