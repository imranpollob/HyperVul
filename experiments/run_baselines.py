#!/usr/bin/env python3
"""
Rule-based baseline detectors on the test split — the achievable "where do we stand"
comparison. A faithful Slither/Mythril run is blocked: FORGE/DAppSCAN contracts import
external deps (@openzeppelin/@uniswap/node_modules) that the datasets do not bundle, so
they don't compile (documented in the report). Static analyzers are, at core, curated rule
sets; these heuristics emulate that family over the SAME features our model sees, so the
comparison is apples-to-apples and needs no compilation.

Heuristics (binary per test hyperedge):
  AllPositive        : always flag (precision floor; recall 100%)
  HasLowLevel        : flag if any callee is a low-level call (.call/.delegatecall/.send)
  UncheckedLowLevel  : flag if a low-level callee whose return is NOT checked (SWC-104 rule)
  UnguardedExtWrite   : flag if (external call) AND (state write) AND no nonReentrant guard
                        (reentrancy SWC-107 rule of thumb)
  NotSafeERC20        : flag if a token transfer that does NOT go through SafeERC20

Reports Precision/Recall/F1/F2 + clean-test-negative FPR, vs our model's mean test row.
"""
import json
from pathlib import Path
from statistics import mean, pstdev

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
SPLITS = PROJECT_ROOT / "data" / "splits"
RES = PROJECT_ROOT / "experiments" / "results"
OUT = RES / "baseline_comparison_heuristics.md"


def prf(preds, labels):
    tp = sum(1 for p, y in zip(preds, labels) if p == 1 and y == 1)
    fp = sum(1 for p, y in zip(preds, labels) if p == 1 and y == 0)
    fn = sum(1 for p, y in zip(preds, labels) if p == 0 and y == 1)
    tn = sum(1 for p, y in zip(preds, labels) if p == 0 and y == 0)
    P = tp / (tp + fp) if tp + fp else 0.0
    R = tp / (tp + fn) if tp + fn else 0.0
    F1 = 2 * P * R / (P + R) if P + R else 0.0
    F2 = 5 * P * R / (4 * P + R) if 4 * P + R else 0.0
    FPR = fp / (fp + tn) if fp + tn else 0.0
    return dict(P=P, R=R, F1=F1, F2=F2, FPR=FPR, tp=tp, fp=fp, fn=fn, tn=tn)


def load_joined():
    feat = json.load(open(SPLITS / "test_features.json"))
    bott = json.load(open(SPLITS / "test_bottleneck.json"))
    bmap = {(b.get("contract"), b.get("function") or b.get("ast_function")): b for b in bott}
    items = []
    for f in feat:
        key = (f.get("contract"), f.get("function") or f.get("ast_function"))
        items.append((f, bmap.get(key)))
    return items


def callees(b):
    return b.get("callee_nodes", []) if b else []


def has_state_write(b):
    return any(s.get("access") == "write" for s in (b.get("state_nodes", []) if b else []))


# ---- heuristic predictors: (feat_item, bottleneck_item) -> 0/1 ----
def h_all(f, b):
    return 1


def h_lowlevel(f, b):
    return int(any(c["security_context"]["low_level"] for c in callees(b)))


def h_unchecked_lowlevel(f, b):
    return int(any(c["security_context"]["low_level"] and not c["security_context"]["return_checked"]
                   for c in callees(b)))


def h_unguarded_ext_write(f, b):
    cs = callees(b)
    if not cs or not has_state_write(b):
        return 0
    guarded = any(c["security_context"]["nonReentrant"] for c in cs)
    return int(not guarded)


def h_not_safe_erc20(f, b):
    cs = callees(b)
    transferish = [c for c in cs if c["method"] in
                   ("transfer", "transferFrom", "safeTransfer", "safeTransferFrom")]
    if not transferish:
        return 0
    return int(any(not c["security_context"]["safe_erc20"] for c in transferish))


HEURISTICS = [
    ("AllPositive (floor)", h_all),
    ("HasLowLevel", h_lowlevel),
    ("UncheckedLowLevel (SWC-104)", h_unchecked_lowlevel),
    ("UnguardedExtWrite (SWC-107)", h_unguarded_ext_write),
    ("NotSafeERC20", h_not_safe_erc20),
]


def our_model_row():
    """Mean test P/R/F1/F2 across the baseline arm seeds, if artifacts exist."""
    arts = sorted((RES / "ablation").glob("baseline_seed*.json"))
    if not arts:
        return None
    rows = [json.load(open(a))["test"] for a in arts]
    def ms(k):
        xs = [r[k] for r in rows]
        return mean(xs), (pstdev(xs) if len(xs) > 1 else 0.0)
    return {k: ms(k) for k in ("precision", "recall", "f1", "f2")}, len(rows)


def main():
    items = load_joined()
    labels = [int(f.get("label", 0)) for f, _ in items]
    npos, nneg = sum(labels), len(labels) - sum(labels)
    n_joined = sum(1 for _, b in items if b is not None)

    lines = ["# HyperVul — Rule-Based Baseline Comparison (test split)\n"]
    lines.append(f"Test: **{len(items)}** hyperedges ({npos} pos / {nneg} neg); "
                 f"bottleneck-joined {n_joined}/{len(items)}.\n")
    lines.append("> Slither/Mythril not run: FORGE/DAppSCAN contracts import unbundled "
                 "@openzeppelin/@uniswap/node_modules deps and do not compile standalone "
                 "(static-analyzer compilation-coverage gap). These rules emulate the "
                 "static-analyzer family over identical features.\n")
    lines.append("| Detector | Precision | Recall | F1 | F2 | Test-neg FPR | (tp/fp/fn) |")
    lines.append("| :-- | :--: | :--: | :--: | :--: | :--: | :--: |")
    for name, fn in HEURISTICS:
        m = prf([fn(f, b) for f, b in items], labels)
        lines.append(f"| {name} | {m['P']*100:.1f} | {m['R']*100:.1f} | {m['F1']*100:.1f} | "
                     f"{m['F2']*100:.1f} | {m['FPR']*100:.1f} | {m['tp']}/{m['fp']}/{m['fn']} |")

    om = our_model_row()
    if om:
        stats, ns = om
        lines.append(f"| **Ours (set-pool, mean of {ns} seeds)** | "
                     f"**{stats['precision'][0]*100:.1f}±{stats['precision'][1]*100:.1f}** | "
                     f"**{stats['recall'][0]*100:.1f}±{stats['recall'][1]*100:.1f}** | "
                     f"**{stats['f1'][0]*100:.1f}±{stats['f1'][1]*100:.1f}** | "
                     f"**{stats['f2'][0]*100:.1f}±{stats['f2'][1]*100:.1f}** | — | — |")
    lines.append("")
    lines.append("> The hard-negative design makes every test hyperedge contain external "
                 "calls, so a trivial 'flag any external call' detector is degenerate "
                 "(≡ AllPositive). The interesting question is whether our model beats the "
                 "security-pattern rules — i.e. learns more than a curated heuristic.")

    report = "\n".join(lines)
    OUT.write_text(report)
    print(report)
    print(f"\nSaved -> {OUT}")


if __name__ == "__main__":
    main()
