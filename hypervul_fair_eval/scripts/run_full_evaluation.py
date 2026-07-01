#!/usr/bin/env python3
"""Run the complete fair-evaluation pipeline and generate the final report."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


RQ1_MODELS = ("function-mlp", "function-features-mlp", "sequence", "callgraph-gcn", "pairwise-gcn", "pairwise-gat")
RQ2_MODELS = ("set-pool", "pairwise-gcn", "pairwise-gat", "hyperedge-nn")
RQ3_MODELS = ("emb-only", "security", "full", "no-localize", "no-contrastive")


def run_step(name: str, cmd: list[str], dry_run: bool) -> None:
    print(f"\n== {name} ==")
    print(" ".join(cmd))
    if dry_run:
        return
    subprocess.run(cmd, check=True)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=repo_root)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--rq1-batch-size", type=int, default=64)
    parser.add_argument("--rq2-batch-size", type=int, default=128)
    parser.add_argument("--rq3-batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--threshold-policy", choices=["target_recall", "target_precision", "max_f1", "max_f2"], default="max_f2")
    parser.add_argument("--target-recall", type=float, default=0.90)
    parser.add_argument("--target-precision", type=float, default=0.70)
    parser.add_argument("--scl-lambda", type=float, default=0.2)
    parser.add_argument("--skip-smoke", action="store_true", help="Skip compile/import smoke checks before training.")
    parser.add_argument("--skip-audit", action="store_true", help="Skip dataset audit before training.")
    parser.add_argument("--dry-run", action="store_true", help="Print the commands without executing them.")
    args = parser.parse_args()

    py = sys.executable
    scripts = Path(__file__).resolve().parent
    seed_args = [str(seed) for seed in args.seeds]
    common = [
        "--project-root",
        str(args.project_root),
        "--seeds",
        *seed_args,
        "--epochs",
        str(args.epochs),
        "--lr",
        str(args.lr),
        "--dropout",
        str(args.dropout),
        "--threshold-policy",
        args.threshold_policy,
        "--target-recall",
        str(args.target_recall),
        "--target-precision",
        str(args.target_precision),
    ]

    if not args.skip_smoke:
        run_step(
            "Compile Python sources",
            [
                py,
                "-m",
                "compileall",
                "-q",
                str(args.project_root / "hypervul_fair_eval" / "src"),
                str(args.project_root / "hypervul_fair_eval" / "scripts"),
            ],
            args.dry_run,
        )
        run_step("Check import boundaries", [py, str(scripts / "check_import_boundaries.py")], args.dry_run)
        run_step("Model smoke tests", [py, str(scripts / "smoke_test_models.py")], args.dry_run)
        run_step("Training-core smoke tests", [py, str(scripts / "smoke_test_training_core.py")], args.dry_run)

    if not args.skip_audit:
        run_step("Dataset audit", [py, str(scripts / "audit_dataset.py"), "--project-root", str(args.project_root)], args.dry_run)

    run_step(
        "RQ1 generic baselines",
        [
            py,
            str(scripts / "rq1_run_generic_baselines.py"),
            "--models",
            *RQ1_MODELS,
            "--batch-size",
            str(args.rq1_batch_size),
            *common,
        ],
        args.dry_run,
    )
    run_step(
        "RQ2 representation ablation",
        [
            py,
            str(scripts / "rq2_run_representation_ablation.py"),
            "--models",
            *RQ2_MODELS,
            "--batch-size",
            str(args.rq2_batch_size),
            *common,
        ],
        args.dry_run,
    )
    run_step(
        "Refresh RQ2 summary",
        [py, str(scripts / "rq2_run_representation_ablation.py"), "--summarize-only"],
        args.dry_run,
    )
    run_step(
        "RQ3 HyperVul ablation",
        [
            py,
            str(scripts / "rq3_run_hypervul_ablation.py"),
            "--models",
            *RQ3_MODELS,
            "--batch-size",
            str(args.rq3_batch_size),
            "--scl-lambda",
            str(args.scl_lambda),
            *common,
        ],
        args.dry_run,
    )
    run_step(
        "Refresh RQ3 summary",
        [py, str(scripts / "rq3_run_hypervul_ablation.py"), "--summarize-only"],
        args.dry_run,
    )
    run_step("Final report", [py, str(scripts / "make_final_report.py")], args.dry_run)

    if not args.dry_run:
        print("\nComplete. Final report: hypervul_fair_eval/outputs/final_report.md")


if __name__ == "__main__":
    main()
