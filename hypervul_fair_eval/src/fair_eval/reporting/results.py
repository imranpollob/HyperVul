"""Per-run result writers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json_result(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")


def write_markdown_result(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {result.get('title', 'Experiment Result')}",
        "",
        f"Model: `{result.get('model', 'unknown')}`",
        f"Seed: `{result.get('seed', 'unknown')}`",
        "",
    ]
    metrics = result.get("metrics", {})
    if metrics:
        lines.append("## Metrics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|---|---:|")
        for key, value in metrics.items():
            if isinstance(value, float):
                lines.append(f"| {key} | {value:.6f} |")
            else:
                lines.append(f"| {key} | {value} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")

