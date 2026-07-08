#!/usr/bin/env python3
"""
Aggregate the per-seed/per-arm ablation artifacts written by model/train.py into a
multi-seed, statistically-grounded comparison for the paper (Tables T3/T4).

Reads  : experiments/results/ablation/{arm}_seed{seed}.json
Writes : experiments/results/ablation_summary.md  (and prints the same)

Produces:
  1. OOD-holdout FPR per arm: mean +/- std across seeds AND pooled 95% Wilson CI.
  2. Test metrics per arm: F1/Precision/Recall/F2/PR-AUC/ROC-AUC mean +/- std.
  3. Paired significance between arms (McNemar, exact binomial) on per-item holdout
     false-positive decisions, pooled over seeds — isolates whether +SCL and +Localization
     significantly change clean-code FP behavior.

No retraining: operates purely on the saved per-item probabilities.
"""
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

TARGET_RECALL = 0.90   # operating point for the matched-recall FPR comparison

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
ABLATION_DIR = PROJECT_ROOT / "experiments" / "latest1" / "ablation"
OUT_PATH = PROJECT_ROOT / "experiments" / "latest1" / "ablation_summary.md"

HOLDOUTS = ["OZ-Holdout", "MakerDAO", "Bancor", "Liquity"]
# Canonical arm display order (only those present are shown).
ARM_ORDER = ["baseline", "scl", "full", "secnone", "secsec", "secfull"]
TEST_METRICS = ["f1", "precision", "recall", "f2", "pr_auc", "roc_auc"]


def wilson(successes: int, total: int):
    if total == 0:
        return 0.0, 0.0, 0.0
    p = successes / total
    z = 1.96
    denom = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denom
    return p, max(0.0, center - spread), min(1.0, center + spread)


def mean_std(xs):
    if not xs:
        return 0.0, 0.0
    m = sum(xs) / len(xs)
    if len(xs) == 1:
        return m, 0.0
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return m, math.sqrt(var)


def load_artifacts():
    """Return {arm: {seed: artifact}}."""
    runs = defaultdict(dict)
    if not ABLATION_DIR.exists():
        return runs
    for fp in sorted(ABLATION_DIR.glob("*_seed*.json")):
        with open(fp) as fh:
            art = json.load(fh)
        runs[art["arm"]][int(art["seed"])] = art
    return runs


def preds_by_id(holdout_record):
    """id -> 0/1 false-positive decision at the run's own threshold."""
    thr = holdout_record["threshold"]
    return {i: int(p >= thr) for i, p in zip(holdout_record["ids"], holdout_record["probs"])}


def mcnemar_pooled(runs, arm_a, arm_b, holdout):
    """Pool discordant FP decisions over shared seeds/items; exact McNemar p-value.
    b = arm_a flags FP & arm_b clean ; c = arm_a clean & arm_b flags FP."""
    b = c = 0
    seeds = sorted(set(runs[arm_a]) & set(runs[arm_b]))
    for s in seeds:
        pa = preds_by_id(runs[arm_a][s]["holdouts"][holdout])
        pb = preds_by_id(runs[arm_b][s]["holdouts"][holdout])
        for i in pa.keys() & pb.keys():
            if pa[i] == 1 and pb[i] == 0:
                b += 1
            elif pa[i] == 0 and pb[i] == 1:
                c += 1
    n = b + c
    if n == 0:
        return b, c, 1.0
    p = binomtest(min(b, c), n=n, p=0.5, alternative="two-sided").pvalue
    return b, c, p


def thr_for_recall(probs, labels, target):
    """Highest threshold whose test recall >= target (matched operating point)."""
    probs = np.asarray(probs); labels = np.asarray(labels)
    pos = labels == 1
    if pos.sum() == 0:
        return 0.5
    best = 0.0
    for t in np.linspace(0, 1, 2001):
        rec = ((probs >= t) & pos).sum() / pos.sum()
        if rec >= target:
            best = t
    return best


def matched_recall_fpr(runs, arm, holdout, target):
    """Per-seed holdout FPR at the threshold that hits `target` test recall; returns list."""
    out = []
    for s in runs[arm]:
        art = runs[arm][s]
        thr = thr_for_recall(art["test"]["probs"], art["test"]["labels"], target)
        pr = np.asarray(art["holdouts"][holdout]["probs"])
        out.append(float((pr >= thr).mean()))
    return out


def fmt_arm(a):
    return {"baseline": "Baseline", "scl": "+SCL", "full": "+SCL+Loc",
            "secnone": "Sym:none", "secsec": "Sym:security", "secfull": "Sym:full"}.get(a, a)


def main():
    runs = load_artifacts()
    arms = [a for a in ARM_ORDER if a in runs] + [a for a in runs if a not in ARM_ORDER]
    if not arms:
        print(f"No artifacts found in {ABLATION_DIR}. Run model/train.py first.")
        return

    lines = ["# HyperVul — Multi-Seed Ablation Summary\n"]
    seed_counts = {a: sorted(runs[a].keys()) for a in arms}
    lines.append("Seeds per arm: " + ", ".join(f"**{fmt_arm(a)}**={seed_counts[a]}" for a in arms))
    lines.append("")

    # ---- Table 1: OOD holdout FPR ----
    lines.append("## 1. OOD Holdout FPR (mean ± std across seeds; [pooled 95% Wilson CI])\n")
    header = "| Arm | " + " | ".join(HOLDOUTS) + " |"
    lines.append(header)
    lines.append("| :-- | " + " | ".join([":--:"] * len(HOLDOUTS)) + " |")
    for a in arms:
        cells = [fmt_arm(a)]
        for h in HOLDOUTS:
            fprs = [runs[a][s]["holdouts"][h]["fpr"] for s in runs[a]]
            tot_fp = sum(runs[a][s]["holdouts"][h]["fp"] for s in runs[a])
            tot_n = sum(runs[a][s]["holdouts"][h]["n"] for s in runs[a])
            m, sd = mean_std(fprs)
            _, lo, hi = wilson(tot_fp, tot_n)
            cells.append(f"{m*100:.1f}±{sd*100:.1f} [{lo*100:.0f},{hi*100:.0f}]")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")

    # ---- Table 2: Test metrics ----
    lines.append("## 2. Test Performance (mean ± std across seeds)\n")
    lines.append("| Arm | " + " | ".join(m.upper() for m in TEST_METRICS) + " |")
    lines.append("| :-- | " + " | ".join([":--:"] * len(TEST_METRICS)) + " |")
    for a in arms:
        cells = [fmt_arm(a)]
        for metric in TEST_METRICS:
            vals = [runs[a][s]["test"][metric] for s in runs[a]]
            m, sd = mean_std(vals)
            cells.append(f"{m*100:.1f}±{sd*100:.1f}")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")

    # ---- Table 3: Paired McNemar on holdout FP decisions ----
    lines.append("## 3. Paired Significance — McNemar on holdout FP decisions (pooled over seeds)\n")
    lines.append("`b` = first arm flags FP where second is clean; `c` = reverse. "
                 "p < 0.05 ⇒ the two arms make significantly different clean-code FP decisions.\n")
    pairs = [(arms[i], arms[j]) for i in range(len(arms)) for j in range(i + 1, len(arms))]
    lines.append("| Arm A vs Arm B | Holdout | b (A-only FP) | c (B-only FP) | p (McNemar) |")
    lines.append("| :-- | :-- | :--: | :--: | :--: |")
    for a, b_arm in pairs:
        for h in HOLDOUTS:
            bb, cc, p = mcnemar_pooled(runs, a, b_arm, h)
            sig = " **\\***" if p < 0.05 else ""
            lines.append(f"| {fmt_arm(a)} vs {fmt_arm(b_arm)} | {h} | {bb} | {cc} | {p:.4f}{sig} |")
    lines.append("")
    lines.append("> Lower-FPR arm = the one with the smaller own-only-FP count. A significant p with "
                 "c < b means Arm B fixed more clean-code false positives than it introduced.")

    # ---- Table 4: matched-recall FPR (the fair comparison) ----
    lines.append("")
    lines.append(f"## 4. OOD Holdout FPR at MATCHED test-recall ({TARGET_RECALL:.0%}) — mean ± std\n")
    lines.append("Fairer than §1: all-clean holdout FPR is threshold-driven, so each arm/seed is "
                 "evaluated at the threshold that yields the same test recall. Removes the "
                 "per-arm threshold-tuning confound.\n")
    lines.append("| Arm | " + " | ".join(HOLDOUTS) + " |")
    lines.append("| :-- | " + " | ".join([":--:"] * len(HOLDOUTS)) + " |")
    for a in arms:
        cells = [fmt_arm(a)]
        for h in HOLDOUTS:
            fprs = matched_recall_fpr(runs, a, h, TARGET_RECALL)
            m, sd = mean_std(fprs)
            cells.append(f"{m*100:.1f}±{sd*100:.1f}")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("> This is the operating-point-controlled view. Compare arms here, not in §1.")

    report = "\n".join(lines)
    OUT_PATH.write_text(report)
    print(report)
    print(f"\nSaved -> {OUT_PATH}")


if __name__ == "__main__":
    main()
