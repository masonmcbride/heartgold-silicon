#!/usr/bin/env python3
"""HeartGold native symbol-closure analyzer. Standard library only.

Read-only. Does not modify sources, run a linker, or treat symbol matches as ABI proof.

  python3 -B cmake/native_link_evidence.py --build build \
      --link build/CMakeFiles/heartgold.dir/link.txt \
      --lsf upstream/pokeheartgold/main.lsf \
      --ledger docs/heartgold_linker_83_ledger.md \
      --out build/link-closure

For exact current failures, additionally pass --diagnostic PATH_TO_REAL_LINKER_LOG.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys


@dataclass
class Obj:
    key: str
    file: str
    member: str | None = None
    defs: dict[str, str] = field(default_factory=dict)
    undefs: set[str] = field(default_factory=set)
    weak_undefs: set[str] = field(default_factory=set)
    owner: str = "unknown"

    def display(self, base: Path) -> str:
        try:
            name = str(Path(self.file).relative_to(base))
        except ValueError:
            name = self.file
        return f"{name}[{self.member}]" if self.member else name


@dataclass(frozen=True)
class LinkInput:
    file: str
    kind: str  # object / archive
    force: bool = False


def normalize_symbol(s: str) -> str:
    # Keep Mach-O's leading underscore; C++ mangling / asm aliases are exact.
    return s.strip().strip('"')


def is_strong(kind: str) -> bool:
    return kind.upper() not in {"W", "V", "C", "I"}


def parse_nm(text: str, files: list[Path]) -> dict[str, Obj]:
    """Parse 'nm -g -P -A' from GNU nm, llvm-nm, and Darwin nm.

    Archive: /path/lib.a[member.o]: symbol T 0 0
    Object:  /path/main.o: symbol U
    """
    result: dict[str, Obj] = {}
    for raw in text.splitlines():
        if ": " not in raw:
            continue
        origin, payload = raw.split(": ", 1)
        match = re.match(r"^(.*\.a)\[(.*)\]$", origin)
        if not match:
            match = re.match(r"^(.*\.a)\((.*)\)$", origin)
        if match:
            file, member = match.group(1), match.group(2)
        else:
            file, member = origin, None
        # llvm-nm may return a file name without full path. Do not invent a
        # mapping if this is ambiguous: the scanner passes absolute paths.
        fp = Path(file)
        if not fp.is_absolute():
            candidates = [x for x in files if x.name == file]
            if len(candidates) == 1:
                file = str(candidates[0])
        pieces = payload.strip().split()
        if len(pieces) < 2:
            continue
        symbol, kind = normalize_symbol(pieces[0]), pieces[1]
        if len(kind) != 1 or not symbol or kind in {"-", "?"}:
            continue
        key = f"{file}::{member}" if member is not None else file
        obj = result.setdefault(key, Obj(key=key, file=file, member=member))
        if kind.upper() == "U":
            obj.undefs.add(symbol)
        elif kind in {"w", "v"}:
            obj.weak_undefs.add(symbol)
        else:
            obj.defs[symbol] = kind
    return result


def scan_binary_files(files: list[Path], nm: str, arch: str | None) -> tuple[dict[str, Obj], list[str]]:
    output: dict[str, Obj] = {}
    errors: list[str] = []
    archives = [p for p in files if p.suffix == ".a"]
    objects = [p for p in files if p.suffix == ".o"]
    batches = [[p] for p in archives]
    batches += [objects[i:i + 60] for i in range(0, len(objects), 60)]
    basename = Path(nm).name
    arch_opts = []
    if arch and sys.platform == "darwin":
        arch_opts = [f"--arch={arch}"] if "llvm-nm" in basename else ["-arch", arch]
    for paths in batches:
        cmd = [nm, "-g", "-P", "-A", *arch_opts, *map(str, paths)]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        except OSError as exc:
            raise RuntimeError(f"Cannot execute {nm}: {exc}") from exc
        if p.returncode:
            errors.append(f"nm failed on {', '.join(x.name for x in paths[:2])}: {p.stderr[:260]}")
        output.update(parse_nm(p.stdout, paths))
    return output, errors


def original_object_name(path: str) -> str:
    p = path.replace("\\", "/")
    if "/upstream/pokeheartgold/" in p:
        p = p.split("/upstream/pokeheartgold/", 1)[-1]
    for extension in (".cpp.o", ".cc.o", ".c.o", ".s.o", ".S.o", ".asm.o"):
        if p.endswith(extension):
            return p[: -len(extension)] + ".o"
    return p


def load_owners(lsf: Path | None) -> dict[str, str]:
    owners: dict[str, str] = {}
    if not lsf or not lsf.is_file():
        return owners
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from native_image_graph import parse_manifest, ownership
    for original, images in ownership(parse_manifest(lsf, validate_ids=False)).items():
        owners[original] = images[0] if len(images) == 1 else 'ambiguous'
    return owners


def assign_owners(objects: dict[str, Obj], owners: dict[str, str]) -> None:
    for obj in objects.values():
        basename = original_object_name(obj.member or obj.file)
        hits = {name for path, name in owners.items()
                if basename == path or basename.endswith("/" + path)
                or ("/" not in basename and path.endswith("/" + basename))}
        if len(hits) == 1:
            obj.owner = next(iter(hits))


def resolve_path(token: str, base: Path) -> Path:
    p = Path(token)
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def expand_response(tokens: list[str], cwd: Path, depth: int = 0) -> list[str]:
    if depth > 8:
        raise ValueError("Nested linker response files exceed depth 8")
    out: list[str] = []
    for token in tokens:
        if token.startswith("@"):
            response = resolve_path(token[1:], cwd)
            if not response.is_file():
                raise FileNotFoundError(f"Linker response file not found: {response}")
            out.extend(expand_response(shlex.split(response.read_text()), cwd, depth + 1))
        else:
            out.append(token)
    return out


def parse_link_command(link: Path, build: Path) -> tuple[list[LinkInput], list[str]]:
    """Only models explicit .o/.a inputs, in command order.

    Framework/dylib/system library resolution is intentionally out of scope.
    """
    if link.is_file():
        command = link.read_text(errors="replace")
    elif (build / 'build.ninja').is_file():
        target = link.parent.name.removesuffix('.dir')
        commands = subprocess.run(['ninja', '-C', str(build), '-t', 'commands', target],
                                  capture_output=True, text=True, check=True).stdout
        candidates = []
        for line in commands.splitlines():
            parts = shlex.split(line)
            if '-o' in parts and Path(parts[parts.index('-o') + 1]).name == target:
                candidates.append(parts)
        if len(candidates) != 1:
            raise ValueError('Expected one recorded Ninja link command for ' + target)
        tokens = candidates[0]
        if tokens[:2] == [':', '&&']:
            tokens = tokens[2:]
        if '&&' in tokens:
            tokens = tokens[:tokens.index('&&')]
        command = shlex.join(tokens)
    else:
        raise FileNotFoundError(link)
    tokens = expand_response(shlex.split(command), build)
    result: list[LinkInput] = []
    missing: list[str] = []
    all_load = False
    force_loads: set[str] = set()
    for i, tok in enumerate(tokens):
        if tok in {"-all_load", "-Wl,-all_load"} or "-all_load" in tok.split(","):
            all_load = True
        if tok == "-force_load" and i + 1 < len(tokens):
            force_loads.add(str(resolve_path(tokens[i + 1], build)))
        if tok.startswith("-Wl,-force_load,"):
            force_loads.add(str(resolve_path(tok.split(",", 2)[-1], build)))
    for i, tok in enumerate(tokens):
        if tok.startswith("-"):
            continue
        # Prevent double-counting the argument to -force_load.
        if i > 0 and tokens[i-1] == "-force_load":
            continue
        if not tok.endswith((".o", ".a")):
            continue
        p = resolve_path(tok, build)
        if not p.is_file():
            missing.append(str(p))
            continue
        kind = "archive" if p.suffix == ".a" else "object"
        result.append(LinkInput(str(p), kind, all_load or str(p) in force_loads))
    for p in sorted(force_loads):
        if Path(p).is_file() and not any(x.file == p for x in result):
            result.append(LinkInput(p, "archive", True))
    return result, missing


def provider_index(objects: dict[str, Obj]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = collections.defaultdict(list)
    for key, obj in objects.items():
        for symbol in obj.defs:
            index[symbol].append(key)
    return index


def undefined_of(selected: set[str], objects: dict[str, Obj]) -> set[str]:
    defined = set().union(*(objects[k].defs.keys() for k in selected)) if selected else set()
    used = set().union(*(objects[k].undefs for k in selected)) if selected else set()
    return used - defined


def model_extraction(inputs: list[LinkInput], objects: dict[str, Obj]) -> tuple[set[str], list[dict]]:
    """Simulate per-archive lazy member extraction to a least fixed point.

    Approximation: cross-archive extraction is link-order sensitive, and Darwin
    ld may rescan archives differently. This is not a replacement for ld.
    """
    members: dict[str, list[str]] = collections.defaultdict(list)
    for key, obj in objects.items():
        if obj.member is not None:
            members[obj.file].append(key)
    selected: set[str] = set()
    trace: list[dict] = []
    for link in inputs:
        if link.kind == "object":
            if link.file in objects:
                selected.add(link.file)
                trace.append({"file": link.file, "why": "explicit object"})
            continue
        archive_members = members[link.file]
        if link.force:
            for key in archive_members:
                if key not in selected:
                    selected.add(key)
                    trace.append({"file": key, "why": "force-loaded archive"})
            continue
        changed = True
        while changed:
            changed = False
            missing = undefined_of(selected, objects)
            for key in archive_members:
                if key in selected:
                    continue
                covered = missing.intersection(objects[key].defs)
                if covered:
                    selected.add(key)
                    trace.append({"file": key, "why": "archive demand", "satisfies": sorted(covered)[:12]})
                    changed = True
                    missing = undefined_of(selected, objects)
    return selected, trace


def load_ledger(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None or not path.is_file():
        return {}
    rows: dict[str, dict[str, str]] = {}
    if path.suffix.lower() == ".csv":
        with path.open(newline="") as fh:
            for row in csv.DictReader(fh):
                symbol = row.get("symbol", "") or row.get("Linker symbol", "")
                if symbol:
                    rows[normalize_symbol(symbol)] = row
    else:
        for line in path.read_text(errors="replace").splitlines():
            if not re.match(r"^\|\s*S\d+\s*\|", line):
                continue
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(cells) >= 6:
                rows[normalize_symbol(cells[1].strip("`"))] = {
                    "id": cells[0], "pkg": cells[2], "change": cells[3],
                    "test": cells[4], "status": cells[5]
                }
    return rows


def load_linker_diagnostic(path: Path | None) -> set[str]:
    if path is None or not path.is_file():
        return set()
    # Use the shared parser: only the final actual ld64 diagnostic is current.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "hg_link_symbols", Path(__file__).with_name("link_symbols.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return set(module.unresolved(path.read_text(errors="replace")))


def components(graph: dict[str, set[str]]) -> list[list[str]]:
    """Tarjan strongly connected components of the selected-object graph."""
    indices: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    active: set[str] = set()
    result: list[list[str]] = []
    counter = 0
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(graph) * 2 + 100))

    def visit(v: str) -> None:
        nonlocal counter
        indices[v] = low[v] = counter
        counter += 1
        stack.append(v)
        active.add(v)
        for w in graph.get(v, ()):
            if w not in indices:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in active:
                low[v] = min(low[v], indices[w])
        if low[v] == indices[v]:
            group = []
            while True:
                x = stack.pop()
                active.remove(x)
                group.append(x)
                if x == v:
                    break
            result.append(group)

    for node in graph:
        if node not in indices:
            visit(node)
    return sorted((g for g in result if len(g) > 1), key=lambda g: -len(g))


def graph_for_selected(selected: set[str], objects: dict[str, Obj]) -> dict[str, set[str]]:
    defs = provider_index({k: objects[k] for k in selected})
    graph: dict[str, set[str]] = {key: set() for key in selected}
    for key in selected:
        for symbol in objects[key].undefs:
            for provider in defs.get(symbol, ()):
                if provider != key:
                    graph[key].add(provider)
    return graph


def rank_provider(obj: Obj, selected: set[str], linked_archives: set[str]) -> str:
    if obj.key in selected:
        return "selected by modeled link"
    if obj.member is not None:
        return "linked archive, unextracted member" if obj.file in linked_archives else "unlinked archive"
    return "loose compiled object (not linked)"


def recommendation(providers: list[Obj], selected: set[str], linked_archives: set[str]) -> str:
    if not providers:
        return "NO EMITTED DEFINITION — inspect original source, ABI, or missing native implementation"
    if any(obj.key in selected for obj in providers):
        return "MODEL ALREADY HAS DEFINITION — inspect actual ld, architecture, visibility, or ABI"
    if any(obj.member is not None and obj.file in linked_archives for obj in providers):
        return "ARCHIVE EXTRACTION / ORDER — inspect ld's actual archive membership and extraction"
    owners = {p.owner for p in providers if p.owner != "unknown"}
    if owners and "main" not in owners and "Static" not in owners:
        return "CROSS-IMAGE BINDING — verify original overlay ownership and logical lifetime"
    if any(p.member is not None for p in providers):
        return "OMITTED ARCHIVE — inspect build target and native ABI before selecting"
    return "OMITTED OBJECT — verify ownership / add correct link selection, do not force-link whole overlay"


def output_table(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("symbol,package,action\n")
        return
    with path.open("w", newline="") as stream:
        w = csv.DictWriter(stream, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def run(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    build = resolve_path(args.build, project)
    link = resolve_path(args.link, project) if args.link else build / "CMakeFiles/heartgold.dir/link.txt"
    lsf = resolve_path(args.lsf, project) if args.lsf else None
    ledger = resolve_path(args.ledger, project) if args.ledger else None
    diagnostic = resolve_path(args.diagnostic, project) if args.diagnostic else None
    out = resolve_path(args.out, project)
    if not build.is_dir():
        raise FileNotFoundError(f"Build directory missing: {build}")
    if not link.is_file():
        raise FileNotFoundError(f"Actual link command missing: {link}")
    nm = args.nm or shutil.which("llvm-nm") or shutil.which("nm")
    if not nm:
        raise RuntimeError("Neither llvm-nm nor nm found. Supply --nm PATH")
    inputs, missing_link = parse_link_command(link, build)
    files = sorted((p.resolve() for p in build.rglob("*") if p.is_file() and p.suffix in {".a", ".o"}), key=str)
    # Link command can refer to archives outside build; always include them.
    files = sorted(set(files).union(Path(x.file) for x in inputs), key=str)
    print(f"Indexing {len(files)} build objects/archives using {nm} ...", flush=True)
    objects, nm_errors = scan_binary_files(files, nm, args.arch)
    assign_owners(objects, load_owners(lsf))
    selected, trace = model_extraction(inputs, objects)
    predicted = undefined_of(selected, objects)
    providers = provider_index(objects)
    ledger_rows = load_ledger(ledger)
    actual = load_linker_diagnostic(diagnostic)
    if diagnostic is not None and not actual:
        print("WARNING: no unresolved symbols parsed from supplied diagnostic; verify format", file=sys.stderr)
    if actual:
        tracked, basis = actual, "actual linker diagnostic"
    elif ledger_rows:
        tracked, basis = set(ledger_rows), "historical ledger (NOT verified current failures)"
    else:
        tracked, basis = predicted, "modeled undefineds (NOT actual linker results)"
    linked_archives = {t.file for t in inputs if t.kind == "archive"}
    all_references: dict[str, list[str]] = collections.defaultdict(list)
    for key, obj in objects.items():
        for symbol in obj.undefs:
            if symbol in tracked:
                all_references[symbol].append(key)
    rows = []
    machine = []
    strong_selected: dict[str, list[str]] = collections.defaultdict(list)
    for key in selected:
        for symbol, kind in objects[key].defs.items():
            if is_strong(kind):
                strong_selected[symbol].append(key)
    selected_conflicts = {s: ks for s, ks in strong_selected.items() if len(ks) > 1}
    for symbol in sorted(tracked):
        keys = sorted(providers.get(symbol, []), key=lambda k: (
            0 if k in selected else 1,
            0 if objects[k].file in linked_archives else 1,
            objects[k].display(project)))
        candidates = [objects[k] for k in keys]
        suggested = recommendation(candidates, selected, linked_archives)
        record = {
            "symbol": symbol,
            "package": ledger_rows.get(symbol, {}).get("pkg", ""),
            "owner_candidates": "; ".join(sorted({p.owner for p in candidates})),
            "reference_owners": "; ".join(sorted({objects[k].owner for k in all_references[symbol] if k in selected})),
            "potential_strong_definition_conflict": sum(is_strong(p.defs[symbol]) for p in candidates) > 1,
            "compiled_providers": len(candidates),
            "selected_providers": sum(p.key in selected for p in candidates),
            "linked_archive_candidates": sum(p.file in linked_archives for p in candidates),
            "proposed_action": suggested,
            "provider_paths": " | ".join(p.display(project) for p in candidates[:6]),
            "active_references": " | ".join(objects[k].display(project) for k in all_references[symbol] if k in selected)[:320],
            "ledger_action": ledger_rows.get(symbol, {}).get("change", "")[:450],
        }
        rows.append(record)
        machine.append({**record, "providers": [
            {"object": p.display(project), "owner": p.owner,
             "kind": p.defs[symbol], "link_state": rank_provider(p, selected, linked_archives),
             "extra_undefineds": sorted(p.undefs - predicted)[:100]}
            for p in candidates],
            "all_references": [objects[k].display(project) for k in all_references[symbol]]})
    graph = graph_for_selected(selected, objects)
    scc = components(graph)
    out.mkdir(parents=True, exist_ok=True)
    output_table(out / "symbols.csv", rows)
    (out / "analysis.json").write_text(json.dumps({
        "metadata": {"build": str(build), "link": str(link), "nm": nm,
                     "arch": args.arch, "tracked_source": basis,
                     "inputs": len(inputs), "indexed_files": len(files),
                     "indexed_objects": len(objects), "modeled_extracted": len(selected),
                     "modeled_unresolved": len(predicted), "tracked_symbols": len(tracked),
                     "nonmodeled_libraries": "system frameworks and dynamic imports not modeled"},
        "tracked_symbols": machine,
        "modeled_unresolved": sorted(predicted),
        "archive_selection_trace": trace,
        "cycles": [[objects[k].display(project) for k in g] for g in scc[:50]],
        "selected_strong_symbol_conflicts": {s: [objects[k].display(project) for k in ks]
                                             for s, ks in sorted(selected_conflicts.items())},
        "errors": {"nm": nm_errors, "missing_link_inputs": missing_link},
    }, indent=2) + "\n")
    categories = collections.Counter(row["proposed_action"].split(" — ")[0] for row in rows)
    headings = [
        "# HeartGold native symbol closure (read-only)", "",
        f"- **Tracked basis:** {basis}",
        f"- **Tracked symbols:** {len(tracked)}",
        f"- **Indexed archive/loose objects:** {len(objects)} from {len(files)} files",
        f"- **Modeled selected object units:** {len(selected)}",
        f"- **Modeled unresolved symbols:** {len(predicted)} (not the real ld result)",
        f"- **Missing explicit link inputs:** {len(missing_link)}",
        f"- **nm errors:** {len(nm_errors)}",
        f"- **Potential multiple strong definitions in modeled selection:** {len(selected_conflicts)}", "",
        "## Proposed action counts", "",
        "| Type | Tracked symbols |", "|---|---:|",
        *(f"| {k} | {v} |" for k, v in sorted(categories.items(), key=lambda x: -x[1])),
        "", "## Observations", "",
        "This report inventories **emitted symbols**, not source-code definitions.",
        "A name match does not establish correct ABI, original image ownership,",
        "safe overlay lifetime, valid ARM64 relocations, or platform behavior.",
        "The archive extraction simulation approximates linker behavior and",
        "does **not** model system frameworks, dead stripping, dylibs, or cross-image activation.",
        "Only a fresh real `heartgold` link can mark a symbol resolved.", "",
        "## Strongly connected object groups in modeled selection", "",
        f"Found {len(scc)} groups containing multiple objects. Top groups:", "",
        *(f"- {len(g)} objects: " + ", ".join(objects[x].display(project) for x in g[:4]) for g in scc[:10]),
        "", "## Outputs", "",
        "- `symbols.csv`: one row per tracked identity, with real emitted-provider candidates.",
        "- `analysis.json`: full machine-readable providers, modeled closure and extraction trace.",
    ]
    (out / "summary.md").write_text("\n".join(headings) + "\n")
    print("\n".join([
        f"Tracked: {len(tracked)} ({basis})",
        f"Modeled selected objects: {len(selected)}; modeled unresolved: {len(predicted)}",
        f"Indexed: {len(objects)} object units; nm failures: {len(nm_errors)}",
        f"Output: {out / 'summary.md'}",
        f"        {out / 'symbols.csv'}",
        f"        {out / 'analysis.json'}",
        "Note: only a fresh actual linker diagnostic confirms resolution.",
    ]))
    return 0 if not nm_errors and not missing_link else 2


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--project", default=".", help="project root (default current directory)")
    p.add_argument("--build", default="build", help="CMake build directory")
    p.add_argument("--link", help="heartgold.dir/link.txt; defaults to build/CMakeFiles/heartgold.dir/link.txt")
    p.add_argument("--lsf", help="original main.lsf overlay-ownership manifest")
    p.add_argument("--ledger", help="historical 83-row CSV or Markdown ledger (not ground truth)")
    p.add_argument("--diagnostic", help="actual current ld diagnostic (supersedes ledger for tracked symbols)")
    p.add_argument("--out", default="build/link-closure", help="output directory")
    p.add_argument("--nm", help="llvm-nm or nm executable (auto-detect by default)")
    p.add_argument("--arch", default="arm64", help="Mach-O architecture selection (default arm64)")
    args = p.parse_args()
    try:
        return run(args)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
