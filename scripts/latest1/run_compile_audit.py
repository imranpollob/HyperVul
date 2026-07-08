"""Phase 1 compile-coverage audit.

Scales the flatten+import-resolution logic already proven in run_slither_harness.py
(previously only exercised on the 176-item test_features.json split for the Slither/Mythril
baseline comparison) across every unique source file referenced by the full train/val/test
splits used for that comparison. This does NOT touch data/contract_graphs or training data --
it only measures how many contracts can actually be flattened and compiled with solc, which is
the real constraint on running Slither/Mythril as baselines (see run_slither_harness.py,
run_mythril_harness.py, and experiments/run_baselines.py's docstring).

Output: reports/phase1_compile_audit.json and reports/phase1_compile_audit.md.
"""

import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT))

from scripts.latest1.run_slither_harness import (  # noqa: E402
    build_global_file_map,
    find_sol_file,
    determine_solc_version,
    flatten_solidity_file,
    get_installed_solc_versions,
)

SPLIT_FILES = ["data/splits/train.json", "data/splits/val_features.json", "data/splits/test_features.json"]
FLAT_DIR = PROJECT_ROOT / "scratch" / "flat_compile_audit"


def collect_unique_files() -> dict:
    """rel_path -> split name (first split it's seen in) for every referenced source file."""
    by_file = {}
    for split_rel in SPLIT_FILES:
        split_name = Path(split_rel).stem
        items = json.loads((PROJECT_ROOT / split_rel).read_text())
        for item in items:
            fp = item.get("file") or item.get("filePath")
            if fp and fp not in by_file:
                by_file[fp] = split_name
    return by_file


SOLCX_DIR = Path.home() / ".solcx"


def get_solcx_versions() -> list[str]:
    """Newer solc versions available via py-solc-x, e.g. '0.8.29' from 'solc-v0.8.29'."""
    if not SOLCX_DIR.exists():
        return []
    versions = []
    for p in SOLCX_DIR.iterdir():
        m = __import__("re").match(r"solc-v(\d+\.\d+\.\d+)", p.name)
        if m:
            versions.append(m.group(1))
    return sorted(versions, key=lambda v: [int(x) for x in v.split(".")])


def _run_solc_binary(solc_path: Path, flat_path: Path, needs_cancun: bool) -> tuple[bool, str]:
    cmd = [str(solc_path), "--bin", str(flat_path)]
    if needs_cancun:
        cmd += ["--evm-version", "cancun"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return False, "solc_timeout"
    except Exception as e:
        return False, f"solc_exec_error:{type(e).__name__}"
    if res.returncode == 0:
        return True, ""
    err_lines = [l for l in res.stderr.splitlines() if "Error" in l]
    reason = err_lines[0].split(":")[-1].strip()[:80] if err_lines else "unknown_solc_error"
    return False, f"solc_error:{reason}"


def _version_key(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def solc_compile_check(
    src_path: Path, flat_path: Path, solc_ver: str, raw_pragma_ver: str, solcx_versions: list[str],
) -> tuple[bool, str]:
    """Compile check that first tries the (possibly version-capped) solc-select binary
    (flattened with pragma pinned to `solc_ver`), and, if that fails, re-flattens the same
    source with a newer py-solc-x-managed version when the file's actual pragma requires more
    than solc-select has installed (capped at 0.8.11 here). A flattened file's pragma must match
    whichever binary compiles it, so the fallback re-flattens rather than reusing `flat_path`.
    Returns (success, reason)."""
    solc_path = Path.home() / f".solc-select/artifacts/solc-{solc_ver}/solc-{solc_ver}"
    if solc_path.exists():
        ok, reason = _run_solc_binary(solc_path, flat_path, needs_cancun=False)
        if ok:
            return True, ""
    else:
        reason = f"solc_version_not_installed:{solc_ver}"

    # Fallback: if the pragma wants something newer than the solc-select cap, re-flatten with
    # the closest installed py-solc-x version instead of giving up.
    req_versions = [v for v in __import__("re").findall(r"\d+\.\d+\.\d+", raw_pragma_ver or "")]
    if req_versions and solcx_versions:
        wanted = _version_key(req_versions[0])
        candidates = sorted((v for v in solcx_versions if _version_key(v) >= wanted), key=_version_key)
        newer_ver = candidates[0] if candidates else max(solcx_versions, key=_version_key)
        newer_path = SOLCX_DIR / f"solc-v{newer_ver}"
        if newer_path.exists() and newer_ver != solc_ver:
            newer_flat_path = flat_path.with_name(flat_path.stem + f"_v{newer_ver}.sol")
            try:
                flatten_solidity_file(src_path, newer_flat_path, newer_ver)
            except Exception as e:
                return False, f"flatten_error_fallback:{type(e).__name__}"
            ok2, reason2 = _run_solc_binary(newer_path, newer_flat_path, needs_cancun=True)
            if ok2:
                return True, ""
            reason = f"{reason}|fallback_v{newer_ver}:{reason2}"
    return False, reason


def main() -> int:
    print("Building global file map...")
    build_global_file_map()

    by_file = collect_unique_files()
    print(f"Unique source files across train/val/test splits: {len(by_file)}")

    limit = None
    if len(sys.argv) > 1 and sys.argv[1] == "--limit":
        limit = int(sys.argv[2])
        by_file = dict(list(sorted(by_file.items()))[:limit])
        print(f"(--limit applied: auditing only {len(by_file)} files)")

    installed_versions = get_installed_solc_versions()
    solcx_versions = get_solcx_versions()
    print(f"solc-select versions: {len(installed_versions)}; py-solc-x fallback versions: {solcx_versions}")
    FLAT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    reason_counter = Counter()
    split_counter = defaultdict(lambda: Counter())

    for idx, (rel_path, split_name) in enumerate(sorted(by_file.items()), 1):
        print(f"[{idx}/{len(by_file)}] {rel_path}")
        full_path = find_sol_file(rel_path)
        if not full_path:
            reason = "file_not_locatable"
            results.append({"file": rel_path, "split": split_name, "success": False, "reason": reason})
            reason_counter[reason] += 1
            split_counter[split_name][reason] += 1
            continue

        try:
            content = full_path.read_text(errors="ignore")
        except Exception as e:
            reason = f"read_error:{type(e).__name__}"
            results.append({"file": rel_path, "split": split_name, "success": False, "reason": reason})
            reason_counter[reason] += 1
            split_counter[split_name][reason] += 1
            continue

        solc_ver = determine_solc_version(content, installed_versions)
        flat_path = FLAT_DIR / f"{full_path.stem}_flat.sol"
        try:
            flatten_solidity_file(full_path, flat_path, solc_ver)
        except Exception as e:
            reason = f"flatten_error:{type(e).__name__}"
            results.append({"file": rel_path, "split": split_name, "success": False, "reason": reason, "solc_version": solc_ver})
            reason_counter[reason] += 1
            split_counter[split_name][reason] += 1
            continue

        pragma_match = __import__("re").search(r"pragma\s+solidity\s+([^;]+);", content)
        raw_pragma_ver = pragma_match.group(1).strip() if pragma_match else ""
        success, reason = solc_compile_check(full_path, flat_path, solc_ver, raw_pragma_ver, solcx_versions)
        results.append({
            "file": rel_path, "split": split_name, "success": success,
            "reason": reason, "solc_version": solc_ver,
        })
        reason_counter[reason if not success else "success"] += 1
        split_counter[split_name][reason if not success else "success"] += 1

    total = len(results)
    successes = sum(r["success"] for r in results)
    print(f"\nCompiled successfully: {successes}/{total} ({successes/total*100:.1f}%)")

    summary = {
        "total_files": total,
        "compiled_successfully": successes,
        "compile_success_rate": successes / total if total else 0.0,
        "failure_reasons": dict(reason_counter.most_common()),
        "by_split": {k: dict(v) for k, v in split_counter.items()},
    }

    out_json = PROJECT_ROOT / "reports" / "phase1_compile_audit.json"
    with open(out_json, "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)
    print(f"Wrote {out_json}")

    md_lines = [
        "# Phase 1 Compile-Coverage Audit",
        "",
        f"Attempted to flatten + compile (solc-only, no Slither analysis) every unique source "
        f"file referenced across `data/splits/{{train.json,val_features.json,test_features.json}}` "
        f"-- the dataset the Slither/Mythril baseline-comparison harnesses run against.",
        "",
        f"**{successes}/{total} files compiled successfully ({successes/total*100:.1f}%).**",
        "",
        "## Failure reasons",
        "",
        "| Reason | Count |",
        "|---|---:|",
    ]
    for reason, count in reason_counter.most_common():
        if reason == "success":
            continue
        md_lines.append(f"| {reason} | {count} |")
    md_lines += ["", "## By split", "", "| Split | Success | Total | Rate |", "|---|---:|---:|---:|"]
    for split_name, counts in split_counter.items():
        s = counts.get("success", 0)
        t = sum(counts.values())
        md_lines.append(f"| {split_name} | {s} | {t} | {s/t*100:.1f}% |")

    out_md = PROJECT_ROOT / "reports" / "phase1_compile_audit.md"
    out_md.write_text("\n".join(md_lines) + "\n")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
