"""Original resident script-table callback roots. MIT."""
import re
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'cmake'))
from native_image_graph import parse_manifest,ownership


def original_owners(game):
    """Project original static/autoload sections into the resident root domain."""
    images = parse_manifest(Path(game) / "main.lsf")
    owners = {}
    for obj, names in ownership(images).items():
        domains = {name if images[name]['kind'] == 'Overlay' else 'main' for name in names}
        if len(domains) != 1:
            raise ValueError("Conflicting original owner: " + obj)
        owners[obj] = domains.pop()
    return owners


def original_script_names(game):
    game = Path(game)
    decl = (game / "include/script.h").read_text()
    if not re.search(
        r"typedef\s+BOOL\s*\(\s*\*\s*ScrCmdFunc\s*\)"
        r"\s*\(\s*ScriptContext\s*\*\s*ctx\s*\)\s*;",
        decl,
    ):
        raise ValueError("Original script callback signature drift")

    source = (game / "src/data/fieldmap/script_cmd_table.h").read_text()
    match = re.search(
        r"const\s+ScrCmdFunc\s+gScriptCmdTable\s*\[\s*\]"
        r"\s*=\s*\{(.*?)\};", source, re.S,
    )
    if not match:
        raise ValueError("Original callback initializer unavailable")
    clean = re.sub(r"/\*.*?\*/|//[^\n]*", "", match.group(1), flags=re.S)
    names = [v.strip() for v in clean.split(",") if v.strip()]
    if not names or any(
        not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", n) for n in names
    ):
        raise ValueError("Original callback initializer requires review")
    return names


def resident_roots(game, definitions):
    """Return defining original main members, never overlay members.

    A definition is necessary but not sufficient for execution admission.
    """
    owners = original_owners(game)
    roots = set()
    verified = set()
    for name in original_script_names(game):
        candidates = [
            (member, desc)
            for member, desc in definitions.get(name, [])
            if owners.get(member) == "main"
        ]
        if not candidates:
            continue  # An overlay callback is not a main definition.
        if len(candidates) != 1:
            raise ValueError("Ambiguous resident callback: " + name)
        member, desc = candidates[0]
        if (desc.get("params") != ["ptr"] or
            desc.get("return") != "i32" or
            desc.get("varargs") or
            not desc.get("definition")):
            raise ValueError("Resident callback ABI mismatch: " + name)
        roots.add(member)
        verified.add(name)
    return roots, verified
