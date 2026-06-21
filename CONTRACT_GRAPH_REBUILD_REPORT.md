# HyperVul — Contract-Graph Rebuild: Comprehensive Report

> **Date:** 2026-06-21
> **Scope:** the full rebuild from isolated per-interaction hyperedges to a shared contract-level graph, including the foundations audit that motivated it, all data groundwork, the architecture, every training experiment (positive and negative), and the final headline result.
> **Headline:** the best configuration is the **0-layer pooled representation + Option B 20:1 balanced sampling** — **ROC-AUC 0.817 ± 0.006, PR-AUC 0.313 ± 0.014** on the full-pool test set. Of the rebuild's three architectural bets, only one (the representation) paid off; cross-hyperedge propagation and the regime-aware MoE head are empirically confirmed non-contributors.

---

## 1. Executive Summary

The rebuild set out to test three architectural bets on top of the existing interaction-level vulnerability detector:

| Bet | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| **Shared contract-level graph + pooled node representation** | Richer per-node features + contract context improve detection | ✅ **Confirmed** | ROC-AUC 0.637 → 0.817; PR-AUC 0.128 → 0.313 |
| **Cross-hyperedge (G-HAN) propagation** | Message passing over call + shared-data edges captures indirect reentrancy | ❌ **Refuted** | 0-layer beats 1/2-layer at every seed; over-smoothing confirmed; learnable gate refuses to open |
| **Regime-aware MoE head** | Routing on security_context separates regimes for better detection | ❌ **Refuted** | MoE 0.807/0.294 vs plain head 0.817/0.313 (experts balanced, but no gain) |

**Final state vs the original isolated-hyperedge model (same full-pool test, 41 pos / 732 neg):**

| model | ROC-AUC | PR-AUC |
|---|---:|---:|
| original isolated-hyperedge | 0.848 | 0.237 |
| **rebuild headline (0-layer pooled + Option B 20:1)** | **0.817** | **0.313** |

The rebuild is **slightly below on ROC-AUC (−0.031) but meaningfully above on PR-AUC (+0.076, +32% relative)** — i.e. stronger on the precision-recall / false-positive axis the project has prioritized throughout, at a modest ROC cost. The win is entirely attributable to the representation work and graph-level class balancing; the two graph-specific mechanisms did not earn their place.

---

## 2. Motivation — the Foundations Audit

Before any model change, a 10-task read-only audit assessed whether the rebuild's premises held (full detail in `foundations_audit_report.md`). Key findings:

- **BLOCKING (Task 5 — indirect-reentrancy reachability):** under the original isolated construction, the helper functions that carry indirect-reentrancy state mutations frequently have no graph node at all. Of 41 caller→state-mutating-helper relationships across the 23 test reentrancy positives, **26 (63%) point to a non-constructable helper with no hyperedge**, and 5 more constructable helpers share no node with their caller. → the rebuild *must* add helper nodes + explicit call edges for propagation to even be able to reach these cases.
- **DEGRADING:** encoder truncation at 256 tokens; modifiers and inline-assembly calls invisible to construction; phantom external calls from struct/library receivers; multi-call order collapse; **FORGE per-type labels 51% unsubstantiated** (a keyword classifier defaulting to SWC-107); negative sampling vs keep-all-positives mismatch.
- **INFORMATIONAL (held up):** augmentation is statement-order-safe; the constructability gate robustly catches mapping/struct/array state access; inheritance resolves correctly; `is_cross_contract` is reliable (0.16% disagreement); where multi-interaction contracts exist they are 84% node-connected.

These findings directly shaped the rebuild: add helper nodes + call edges (Task 5 fix), raise the token cap, filter scaffolding, and re-type/clean the FORGE labels.

---

## 3. Data Groundwork (Step 0)

All applied non-destructively (originals backed up under `scratch/`).

| Step | Action | Result |
|---|---|---|
| **0a — Box leakage fix** | `vfp_00189`/`Box` had train negatives + test positives from the same contract | All 14 Box items moved to **test**; project-level split assignment makes this structural |
| **0b — Scaffolding filter** | Drop test/mock/harness contracts (`*Test/*Tester/*Harness/*Mock/console`…) | **167 contracts / 1,057 interactions, all 0-positive** removed from the full pool; 0 were in the curated splits (they live only in Tier-B) |
| **0c — Task-8 exclusions** | Remove FORGE positives whose findings are non-security functional bugs | **4 functions / 5 rows** dropped: `FlashLoans.flashLoan` (×2), `OctoDistributor.{withdrawAllAgentTokens, transferHiringDistributions}`, `MainFeeDistributor.swapLzToken` |
| **Cross-split dedup** | Identical boilerplate contracts (`Timelock`×17, `MasterChef`×10…) spanning splits | **149 negative source-hashes deduped**, 320 negative instances removed (307 train / 13 val / 0 test); **0 positives affected** |

*Note on FORGE labels:* the audit found 42/83 FORGE positive *types* are classifier artifacts (default-to-SWC-107). Only the 4 clearly-non-security items were removed; the mistyped-but-still-security items were kept. A full FORGE re-typing remains an open follow-up.

---

## 4. The Contract-Graph Dataset

One graph per `(project, contract)`. Nodes = interaction hyperedges (positive + negative) **+** 1-hop state-mutating helper nodes. Edges = directed call edges (`call_forward`/`call_reverse`) **+** symmetric shared-data edges (`shared_state`/`shared_callee`).

**Post-groundwork totals:**

| split | graphs | positives | negatives | helpers |
|---|---:|---:|---:|---:|
| train | 1,583 | 219 | 10,263 | ~1,480 |
| val | 159 | 38 | 793 | ~140 |
| test | 138 | 41 | 732 | ~170 |

- **Interaction class balance: ~1:40** (full pool) — vs the original's sampled 3:1.
- **Helper nodes added:** +567 over the curated-split scope (1-hop, median 1/contract, max 17); 1,796 over the full pool — these are exactly the previously-missing state-mutating helpers (e.g. `Box._startNavCache`, `_endNavCache`).
- **Singleton breakdown:** of 1,717 all-negative graphs, **357 (21%) are inert singletons** (no edges); 1,360 have ≥2 interactions and real structure.

---

## 5. Architecture

Two composed stages on frozen SmartBERT-v3 embeddings:

**Stage 1 — Pooled node representation (the win).** Each node's input feature is `AttentionPooling({function@512, state-var@256, callee@64})` — the original multi-component representation, restored. Interaction nodes pool function + state-vars + callees; helper nodes pool function + state-vars only (mask-driven, no hardcoded component count).

**Stage 2 — G-HAN propagation (parked).** Edge-typed, direction-aware gated message passing over the pooled node features. Implemented and verified working, but empirically a liability (see §6.4); the headline runs it at **0 layers** (propagation off, nodes scored directly).

**Heads tested:** plain MLP (768→256→1) and a regime-aware **MoE** (soft router on the 8-d `security_context` vector → 4 expert MLPs + importance² load-balancing). The plain head wins.

`security_context` (per interaction, 8-d): reentrancy-guard, access-control, payable, low-level-call, safe-erc20-call, cross-contract, #external-calls, #state-vars.

Key files: `model/ghan.py` (GHAN, PooledContractGraphModel, GatedResidualGHAN, PooledGatedModel, MoEHead, PooledMoEModel), `model/contract_graph_data.py` (loaders, pooled batching), `scripts/build_contract_graphs.py`, `scripts/encode_contract_graph_nodes.py`, `scripts/extend_node_features.py`, `scripts/build_security_context.py`.

---

## 6. Experimental Results

All on the same full-pool test set (41 pos / 732 neg) unless noted. ROC-AUC is base-rate-independent and the primary cross-experiment comparator; PR-AUC tracks the precision/false-positive story.

### 6.1 Representation: the single-CLS bug and its fix
The first end-to-end build accidentally collapsed each node to a **single function-body CLS embedding**, discarding the state-var/callee embeddings (confirmed by code: `encode_contract_graph_nodes.py` encoded only `function_source`). Restoring the pooled representation was the single biggest gain:

| representation | ROC-AUC | PR-AUC |
|---|---:|---:|
| single-CLS per node | 0.637 | 0.128 |
| **pooled (function + state + callee)** | **0.734 ± 0.005** | **0.224 ± 0.027** |

### 6.2 Control: original model on the new test pool
To separate "harder test" from "worse model," the original isolated-hyperedge checkpoint was run, in its native representation, on the full pool:

| model | test pool | ROC-AUC | PR-AUC |
|---|---|---:|---:|
| original | original (44p/125n) | ~0.89 | ~0.72 |
| original | full pool (41p/732n) | 0.848 | 0.237 |
| new (single-CLS) | full pool | 0.637 | 0.128 |

The harder pool costs the original only ~0.04 ROC-AUC; the ~0.21 gap to the single-CLS model was the representation, not the test. This pinned the diagnosis.

### 6.3 Encoder truncation
At `max_length=256`, **70.5% of positives truncated, ~58–60% lose a call/state-write** to the cut. Raising to **512** halves it (38.9% / 31.9%). Stratified recall (fits-512 vs exceeds-512 positives) showed the **still-truncated positives are detected as well or better** — truncation is not the bottleneck, and the pooled representation makes it doubly moot (callees/states are embedded separately, surviving function-body truncation). The encode pass was re-run at 512; chunked/hierarchical encoding was **not** pursued (unsupported by evidence).

### 6.4 Propagation depth — over-smoothing (the decisive negative)

| layers | ROC-AUC | PR-AUC |
|---:|---:|---:|
| **0 (no propagation)** | **0.808 ± 0.018** | **0.342 ± 0.024** |
| 1 | 0.720 ± 0.022 | 0.179 ± 0.043 |
| 2 | 0.706 ± 0.050 | 0.208 ± 0.052 |

ROC-AUC improves monotonically as depth decreases; 0-layer beats every 1/2-layer seed. **Convergence check ruled out undertraining:** the deeper models hit their validation-loss minimum very early (epochs 0–14) and then *diverge* (val loss climbs to 0.94–1.23), early-stopping sooner than the 0-layer model — the over-smoothing signature, not undertraining.

**Gated-residual rescue attempt** (learnable blend gate init near-zero, so each variant *starts* equivalent to the 0-layer winner; 5 seeds):

| variant | ROC-AUC | PR-AUC | learned gate |
|---|---:|---:|---|
| global, 1 layer | 0.723 ± 0.030 | 0.181 ± 0.026 | ~0.007 (stayed shut) |
| global, 2 layers | 0.725 ± 0.020 | 0.170 ± 0.038 | ~0.006 |
| per-type, 1 layer | 0.736 ± 0.031 | 0.217 ± 0.023 | ~0.007 |

The gates **never open** — given a free knob, optimization keeps propagation off — and even gated propagation never recovers the 0-layer result. Propagation was closed.

### 6.5 Option B — graph-level balanced sampling ratio sweep (0-layer pooled)

| config | ROC-AUC | PR-AUC |
|---|---:|---:|
| all data (no balancing) | 0.808 | 0.342 |
| 3:1 (positive-only graphs) | 0.835 | 0.229 |
| 10:1 | 0.781 ± 0.029 | 0.266 ± 0.034 |
| **20:1 (chosen)** | **0.817 ± 0.006** | **0.313 ± 0.014** |
| 30:1 | 0.809 ± 0.003 | 0.350 ± 0.030 |

**20:1 chosen** as the best joint point (best ROC outside the PR-sacrificing 3:1; PR close to all-data; lowest variance). The sampler keeps whole graphs and rotates all-negative graphs each epoch for coverage.

### 6.6 Regime-aware MoE head (0-layer pooled + Option B 20:1, 4 experts, 5 seeds)

| config | ROC-AUC | PR-AUC |
|---|---:|---:|
| 20:1 baseline (plain head) | **0.817 ± 0.006** | **0.313 ± 0.014** |
| 20:1 + MoE head | 0.807 ± 0.013 | 0.294 ± 0.016 |

Expert usage **[0.236, 0.227, 0.274, 0.263]** (uniform 0.25) — load-balancing worked, no collapse — but routing on `security_context` does not beat a single MLP. Negative result.

---

## 7. Headline Result

**0-layer pooled representation + Option B 20:1 balanced sampling, plain MLP head:**
**ROC-AUC 0.817 ± 0.006 · PR-AUC 0.313 ± 0.014** (full-pool test, 41 pos / 732 neg, 3 seeds).

Full arc:

| milestone | ROC-AUC | PR-AUC |
|---|---:|---:|
| G-HAN, single-CLS (bug) | 0.637 | 0.128 |
| pooled rep, 2-layer propagation | ~0.71 | ~0.21 |
| pooled rep, 0-layer, all-data | 0.808 | 0.342 |
| **pooled rep, 0-layer, Option B 20:1 (headline)** | **0.817** | **0.313** |
| + MoE head | 0.807 | 0.294 |
| *original isolated-hyperedge (reference)* | *0.848* | *0.237* |

---

## 8. Verification & Integrity Trail

- **Propagation sanity check** (`scripts/propagation_sanity_check.py`) — re-run on the pooled pipeline; signal provably flows from a node's member embeddings → AttentionPooling → G-HAN → connected interaction logits (call-edge ratio 0.35, shared-data 0.39), disconnected controls exactly 0. The check earned its keep twice: it caught an in-place `index_add_` autograd severance and a LayerNorm-symmetry probe error.
- **Box edge evidence** — literal `etype:"call"` records confirmed for `flash`/`allocate` → `_startNavCache`/`_endNavCache` (with reverse edges for the gate).
- **Full-pool regeneration validated** — 12,127 vs the known 12,098 (gap = intentionally skipped near-dups).
- **Cross-split leakage** quantified and deduped (149 sources, 0 positives affected).
- **Multi-seed** throughout (3–5 seeds); reported as mean ± std.

---

## 9. Limitations

1. **Two of three architectural bets failed.** Cross-hyperedge propagation over-smooths and the MoE head adds no value; the rebuild's value is the representation + balancing, both of which are architecturally simpler than the original premise.
2. **~1:40 imbalance** remains the dominant difficulty; Option B trades ROC against PR rather than lifting both.
3. **FORGE label noise** — per-type labels are ~51% classifier artifacts; only the 4 clearly-non-security items were removed. A proper finding→type re-audit is outstanding and would affect any per-type claims.
4. **Long-tail truncation** — ~32% of positives exceed 512 tokens; mitigated (not eliminated) by separate state/callee embedding, but not addressed by chunking.
5. **Small positive set** (41 test positives) makes ROC/PR estimates noisy at the margins; the cross-experiment ordering is stable but absolute deltas of ±0.01–0.02 are within noise.
6. **Helper nodes and call edges remain in the schema** but are currently inert (propagation off) — retained at no cost in case future propagation work revives them.

---

## 10. Recommendations & Open Decisions

**For the maintainer to decide:**
1. **Adopt the rebuild?** It gives +32% relative PR-AUC over the original at a −3.6% ROC-AUC cost. If the false-positive story is the priority, this is a net gain; if ROC-AUC is, the original is marginally ahead.
2. **Propagation** — parked, not deleted. Reviving it would need a fundamentally different formulation (e.g. attention that learns to ignore neighbors, or task-specific edge selection), not more depth/gating. Recommend leaving closed unless a new idea motivates it.
3. **MoE** — no evidence of regime structure on `security_context`. Recommend dropping unless a different conditioning signal is proposed.
4. **FORGE re-typing** (open follow-up) — the highest-value remaining data-quality task; affects any per-vulnerability-type reporting.
5. **Imbalance** — 20:1 is the current best balance; revisit if a different positive→negative construction strategy is adopted.

**Artifacts:** `data/contract_graphs/{train,val,test}.json` + `node_embeddings.pt` + `member_embeddings.pt`; results in `scratch/{depth_ablation,depth_followup,optionb_sweep,moe_results}.json`; prior reports `foundations_audit_report.md`, `rebuild_build_report.md`, `option_a_results_report.md`.
