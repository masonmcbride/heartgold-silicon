"""Package a complete guest32 image using exact manifest membership."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--coverage", type=Path, required=True)
    p.add_argument("--image-dir", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--ar", required=True)
    p.add_argument("--image-name", required=True)
    a = p.parse_args()

    d = json.loads(a.coverage.read_text())
    summary = d["summary"]

    if d["image"]["name"] != a.image_name:
        raise SystemExit("Incorrect original image")

    if not summary.get("complete_compilation") or summary.get("issues"):
        raise SystemExit("Guest compilation is incomplete")

    members = d["members"]
    names = [m["object"] for m in members]

    if (names != d["image"]["objects"]
            or len(names) != len(set(names))
            or len(names) != summary["c_total"] + summary["data_total"]):
        raise SystemExit("Original image membership mismatch")

    root = a.image_dir.resolve()
    objects = []

    for m in members:
        complete = (
            m.get("compiled", False)
            if m["kind"] == "C"
            else m.get("represented", False)
        )
        if not complete:
            raise SystemExit(f"Incomplete member: {m['object']}")

        obj = (root / m["object"] / "native.o").resolve()
        if (not obj.is_relative_to(root)
                or not obj.is_file()
                or obj.stat().st_size == 0):
            raise SystemExit(f"Invalid object: {m['object']}")

        objects.append(obj)

    a.archive.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="guest32-archive-",
        dir=a.archive.parent,
    ) as temp:
        temp = Path(temp)
        staged = []

        for i, obj in enumerate(objects):
            target = temp / f"member_{i:03d}.o"
            shutil.copyfile(obj, target)
            staged.append(target)

        archive = temp / "image.a"
        subprocess.run(
            [a.ar, "rcsD", str(archive), *map(str, staged)],
            check=True,
        )

        listing = subprocess.run(
            [a.ar, "t", str(archive)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()

        if listing != [obj.name for obj in staged]:
            raise SystemExit("Archive member verification failed")

        if not a.archive.exists() or a.archive.read_bytes() != archive.read_bytes():
            os.replace(archive, a.archive)

    print(f"PASS: {len(objects)} original members archived")
    print(f"Archive: {a.archive}")
    print("Guest ABI interface admission remains separate.")


if __name__ == "__main__":
    main()
