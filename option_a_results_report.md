# Option A Baseline — Training Results + 512-Token Stratified Breakdown

> **Date**: 2026-06-21. Re-encoded at `max_length=512`; G-HAN contract-graph model; Option A weighted-loss baseline (3 seeds: 42/43/44). Test = full contract-graph test split (41 pos / 732 neg). Results: `scratch/option_a_results.json`.

## 1. Re-encode at 512 — confirmed
Truncation rate on positives at 512 **matches the prediction exactly**: **38.9% truncated / 31.9% lose a CALL or STATE-WRITE**. Graphs/schema/model dims untouched; embeddings re-encoded (25.8 MB).

## 2. Test-positive 512 tags
41 test positives: **20 fit ≤512 tokens, 21 exceed 512.** Exceeds-512 list (full): `unStake`(1869), `modifyOrder`(1736), `redeemCollateral`(1394), `stake`(1386), `receiveFlashLoan`(1128), `performUpkeep`(1080), `_afterSwap`(1021), `allocate`(907), `_createOrder`(880), `trade`(875), `harvest`(817), `_finalizeBundle`(754), `reallocate`(704), `flashLoan`(698), `deallocate`(667), `makeFlashLoan`(656), `fillOrder`(605), `requestImage`(590), `sponsorProposal`(579), `depositStable`(577), `_getTargetOutput`(536).

## 3. Training run — two findings up front

**(a) Option A at full `pos_weight` (≈47) collapses to all-positive.** Threshold→0, recall 1.0, precision 0.054 (= base rate). The exact "extreme-weight collapse" risk flagged for Option A. The ≥95%-recall threshold rule is uninformative there (it sits at 0, so every group's recall is trivially 1.0).

**(b) Softened `sqrt` weighting (`pos_weight≈6.8`) trains without collapse, but the baseline is weak.** Aggregate test metrics at the val-F1-optimal threshold (mean±std over 3 seeds):

| metric | value |
|---|---|
| precision | 0.191 ± 0.050 |
| recall | 0.122 ± 0.020 |
| F1 | 0.148 ± 0.029 |
| PR-AUC | 0.128 ± 0.006 |
| **ROC-AUC** | **0.637 ± 0.016** |

For reference the original isolated-hyperedge model reported test ROC-AUC ≈0.89. **The rebuild's first end-to-end baseline ranks positives substantially worse.** Caveats on the comparison: this test is the *full* pool (1:18 pos:neg incl. all Tier-B hard negatives) vs the original's sampled 3:1 set, so absolute precision/F1/PR-AUC aren't directly comparable — but ROC-AUC is base-rate-independent, and the 0.89→0.64 drop is real. Likely drivers: (i) each node is a **single function-body CLS** vs the original's pooled function+state+callee multi-embedding; (ii) 1:47 train imbalance; (iii) untuned G-HAN/training. None of these is truncation.

## 4. Stratified breakdown — the evidence you asked for

| signal | fits ≤512 (n=20) | exceeds 512 (n=21) |
|---|---|---|
| recall @ F1-opt threshold | 0.117 ± 0.024 | **0.127 ± 0.022** |
| recall @ 95%-recall threshold | 1.000 | 1.000 |
| mean predicted probability | 0.301 ± 0.047 | **0.382 ± 0.046** |

**The still-truncated (exceeds-512) positives are NOT where the model's errors concentrate.** Recall is equal-to-slightly-higher for the exceeds group, and their mean predicted probability is *higher*, not lower. If truncation were the bottleneck we'd expect the exceeds-512 group to be systematically under-predicted — the opposite is observed.

A plausible mechanism, consistent with the foundations audit's "external-call-detector" finding: longer functions have more external calls, and the model keys on call density (a surface feature that survives truncation) rather than the fine-grained post-call state-write ordering that truncation removes. So truncating the tail doesn't change predictions the model was never using that signal to make.

## 5. My read — which way the evidence points

**The evidence does NOT support building chunked/hierarchical encoding next.** Truncation is real (32% of positives still lose events at 512), but it is **not** where this model fails — the exceeds-512 group is detected as well or better than the fits group. Spending effort on >512 chunking would optimize a part of the pipeline that isn't the bottleneck.

**The honest headline is bigger than truncation:** the Option A baseline itself is weak (ROC-AUC 0.64, recall 0.12), and full-weight Option A collapses. Before truncation is worth revisiting, the priorities the data points to are:
1. **Node features** — restore the pooled function+state+callee representation per node (the single-CLS node is the most likely cause of the ROC-AUC drop).
2. **Imbalance** — full-weight collapses and sqrt-weight underfits positives; this is where **Option B (graph-level balanced sampling)** should be tried next, as planned.
3. Then, and only then, re-measure the 512-stratified gap — if a *strong* model still shows an exceeds-512 deficit, chunking becomes worth it. Right now it isn't.

**Caveat I won't hide:** with ROC-AUC 0.64 and recall 0.12, the model is weak enough that the stratified comparison carries real noise. The finding "truncation is not the bottleneck" is well-supported directionally (equal recall + higher mean-prob for exceeds), but it should be re-confirmed once the baseline is stronger — not treated as final. I did **not** build chunked encoding; per your instruction this was a measurement only.
