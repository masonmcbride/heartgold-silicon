import re
import subprocess
import sys
from pathlib import Path

cases = [
    ("MIC sample conversion", "build/hg_mic_capture_test", None),
    ("Original VCT sender", "build/vct-send-regression/vct-send-test", None),
    ("Production MIC API", "build/hg_mic_spi_test", None),
    ("Original codec 0", "build/vct-producer-minimal/test_vct_packet_contents", "858c3502"),
    ("Original codec 4", "build/vct-producer-minimal/test_vct_adpcm", "d24fc537"),
    ("Original ADPCM encode/decode", "build/vct-producer-minimal/test_vct_roundtrip", "09a84352"),
    ("Live microphone → original ADPCM", "build/vct-producer-minimal/test_vct_live_mic", "LIVE"),
]

failed = False
for name, path, expected in cases:
    exe = Path(path)
    print(f"\n=== {name} ===", flush=True)
    if not exe.is_file():
        print(f"FAIL missing executable: {path}")
        failed = True
        continue
    try:
        result = subprocess.run(
            [str(exe.resolve())],
            capture_output=True,
            text=True,
            timeout=20,
        )
        output = result.stdout + result.stderr
        good = result.returncode == 0
        if expected == "LIVE":
            match = re.search(r"Live PCM nonzero samples:\s*(\d+)", output)
            good &= bool(match and int(match.group(1)) > 0)
            good &= "codec 4 ADPCM selected" in output
            good &= "original packet preparation" in output
            print("Live PCM samples:", match.group(1) if match else "missing")
        elif expected:
            match = re.search(r"Decoded PCM FNV-1a:\s*([0-9a-fA-F]+)" if "roundtrip" in str(exe) else r"Payload FNV-1a:\s*([0-9a-fA-F]+)", output)
            good &= bool(match and match.group(1).lower() == expected)
            print("Checksum:", match.group(1) if match else "missing")
        print("PASS" if good else "FAIL")
        if not good:
            print("\n".join(output.splitlines()[-12:]))
        failed |= not good
    except subprocess.TimeoutExpired:
        print("FAIL timeout")
        failed = True

print("\nRESULT:", "FAIL" if failed else "ALL SEVEN REGRESSIONS PASSED")
sys.exit(int(failed))
