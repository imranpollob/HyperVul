#!/usr/bin/env python3
"""Check that RQ1 generic code does not import the HyperVul hyperedge builder."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


FORBIDDEN_IMPORTS = {
    "fair_eval.builders.hyperedge_view",
    "builders.hyperedge_view",
}

GENERIC_FILES = [
    "scripts/inspect_generic_views.py",
    "src/fair_eval/builders/common.py",
    "src/fair_eval/builders/function_view.py",
    "src/fair_eval/builders/sequence_view.py",
    "src/fair_eval/builders/callgraph_view.py",
    "src/fair_eval/builders/pairwise_graph_view.py",
    "src/fair_eval/builders/__init__.py",
]


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    violations = []
    for rel in GENERIC_FILES:
        path = root / rel
        if not path.exists():
            continue
        imports = imported_modules(path)
        bad = sorted(imports & FORBIDDEN_IMPORTS)
        if bad:
            violations.append((rel, bad))

    if violations:
        for rel, bad in violations:
            print(f"FORBIDDEN import in {rel}: {', '.join(bad)}")
        raise SystemExit(1)

    print("Import boundary check passed: RQ1 generic files do not import hyperedge_view.")


if __name__ == "__main__":
    main()

