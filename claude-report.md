# HyperVul — Divergent-Approaches Review

**Author:** Claude (code review)
**Date:** 2026-07-01
**Method:** This review is derived from the **code** (model definitions, training scripts, and the
machine-written per-seed JSON result files), not from the narrative `.md`/`.tex` write-ups. Where the
prose documents and the code/results disagree, that disagreement is itself one of the findings.

---

## 1. Executive summary

The repository is not one project; it is **six overlapping attempts** to make a hyperedge model beat
generic baselines, layered on top of each other without ever being consolidated. The attempts diverge on
three independent axes at once:

1. **Unit of prediction** — interaction-level vs contract-level (MIL).
2. **Model structure** — set-pool → sequence-pool → structural hypergraph message passing → contract-graph
   propagation (G-HAN/APPNP/MoE) → risk-vs-safety two-branch.
3. **Codebase** — the same ideas are re-implemented three times ([src/models/](src/models/),
   [model/latest1/](model/latest1/), and the clean rewrite [hypervul_fair_eval/](hypervul_fair_eval/)),
   each with its **own** re-implementation of the baselines.

**The single most important finding:** when the model is trained and evaluated on the *clean,
contract-disjoint* split with baselines retrained identically, **HyperVul does not beat the baselines.**
It ties them. The headline "64.34 F1 / 85 recall / 51.80 precision" in the paper and in
[self-docs/results.md](self-docs/results.md) comes **only** from the `shortcut_aug_bce:gated` variant,
which the project's own results file
([reports/final_comparison_tables.md](reports/final_comparison_tables.md)) labels
`shortcut_leaky_targeted_augmentation` and describes as *"performance-oriented and not clean final
evaluation."* The honest numbers are in §4.

---

## 2. The divergent approaches, reconstructed from code

Below, each "version" is identified by its actual model class and training entry point, with the results
that the code actually produced.

### V1 — Interaction-level attention/set-pool classifier (iterations 1–2)

- **Code:** the deployed `model/model.py` `AttentionPooling` (now only surviving as the re-expressed
  [src/models/set_pool.py](src/models/set_pool.py) `SetPoolClassifier` and referenced throughout).
  Checkpoints: `model/iteration1_checkpoint.pt`, `model/iteration2_checkpoint.pt`.
- **Structure:** frozen SmartBERT-v3 member embeddings → attention-pool over `{function, state, callee}`
  members → 2-layer MLP. **No message passing.** Threshold tuned on validation for ≥95% recall; a
  clean-negative ratio sweep over OpenZeppelin negatives ([experiments/results/iteration2_results.md](experiments/results/iteration2_results.md)).
- **Reported:** iteration-1 F1 63.16, ROC-AUC 87.05 ([experiments/results/iteration1_results.md](experiments/results/iteration1_results.md)).
- **Reality:** these numbers predate the leakage audit. They are on the *old* split with an
  *augmented* train set and a tiny test set (44 positives). Phase 0 later found split leakage and label
  noise, which is why every later phase re-baselines from scratch.

### V2 — Sequence-aware hyperedge classifier + localization + symbolic features (iteration 3)

- **Code:** [model/latest1/model.py](model/latest1/model.py) `HyperedgeClassifier` with
  `SequenceAwarePooling` (BiLSTM/Transformer over members) + `LocalizationHead` +
  learnable `loc_gate`; trained by [model/latest1/train.py](model/latest1/train.py) (802 lines).
  Symbolic schema in [src/models/symbolic.py](src/models/symbolic.py).
- **Structure:** members are ordered `function → state → callee`, encoded with a BiGRU/BiLSTM, attention
  pooled, classified by MLP; an additive tuple-localization head fuses a `(function,state,callee)`
  excitability logit on top of the pooled logit. Symbolic 8–37-d security block concatenated to the 768-d
  embedding, ablatable by `sym_mode ∈ {none, security, full}`.
- **Ablation matrix (the 16 checkpoints in [model/](model/)):** `baseline / scl / secnone / secsec /
  secfull` × seeds 42–46, plus supervised-contrastive (SCL) pretraining and hard-negative weighting.
- **Reality:** this is where your saved memory
  ([safety-aware features reduce OOD FPR], [SCL localization FPR did not replicate]) came from. Symbolic
  security features gave a small, real gain; the SCL loss trick did **not** replicate across seeds.

### V3 — Structural representation ablation ("fair adjudicator")

- **Code:** [src/models/hypergraph_nn.py](src/models/hypergraph_nn.py) `HypergraphNN` (two-stage
  attention hyperedge message passing, "ours"), [src/models/gnn_zoo.py](src/models/gnn_zoo.py)
  `GNNClassifier` (`gcn`/`gat`/`hyper` sharing one skeleton),
  [src/baselines/pairwise_gnn.py](src/baselines/pairwise_gnn.py) `PairwiseGNN` (clique expansion), and
  [src/models/set_pool.py](src/models/set_pool.py).
- **Structure:** this is the *cleanest* comparison in the repo — identical skeleton, only the convolution
  operator changes, so hyperedge-vs-pairwise is isolated fairly. It answers RQ2 ("does the hyperedge
  representation beat pairwise/set given the same candidates?").
- **Reality:** in the clean rewrite (§4) the hyperedge model wins RQ2 by only **~3–5 F1 points with
  p ≈ 0.06–0.19** — i.e. not significant at 5 seeds.

### V4 — Contract-graph propagation: G-HAN / APPNP / gated-residual / MoE

- **Code:** [model/latest1/ghan.py](model/latest1/ghan.py) — `GHAN` (edge-typed, direction-aware gated
  message passing across interaction nodes at the **contract** level), `APPNP`, `GatedResidualGHAN`
  (gate initialized near-closed so the model must *learn* to propagate), `MoEHead` (regime-aware
  mixture-of-experts routed on the security-context vector), `PooledContractGraphModel`.
- **Motivation (from [self-docs/current-status.md](self-docs/current-status.md) issue #4):** "HyperVul
  lacks contract-level/global context." V4 tries to inject cross-interaction context.
- **Reality:** the gate initialized near-closed is a tell — the code was written expecting propagation to
  *hurt* and hoping the model would keep it shut. There is no results file showing V4 beating V2; it reads
  as an abandoned branch (multiple competing propagation schemes, none promoted to the final tables).

### V5 — Phase reframing: contract-level MIL + risk-vs-safety + augmentation (phase0–phase1d)

- **Code:** [scripts/run_phase0e_native_contract_mil.py](scripts/run_phase0e_native_contract_mil.py),
  [scripts/run_phase1b_risk_safety_architecture.py](scripts/run_phase1b_risk_safety_architecture.py)
  (risk branch − safety branch, gated), [scripts/run_phase1c_label_cleanup.py](scripts/run_phase1c_label_cleanup.py),
  [scripts/run_phase1d_shortcut_augmentation.py](scripts/run_phase1d_shortcut_augmentation.py),
  [scripts/run_phase1d_contrastive_reentrancy.py](scripts/run_phase1d_contrastive_reentrancy.py).
- **Structure:** abandons strict interaction classification for "contract vulnerable iff ≥1 interaction
  vulnerable" (MIL), adds a safety branch that suppresses risk when `nonReentrant`/CEI/safe-wrapper
  evidence is present, and adds targeted reentrancy augmentation.
- **Reality:** this is where the leak entered. `phase1d_shortcut_augmentation` is the source of the
  64.34 F1 headline, and the repo itself tags it `shortcut_leaky_targeted_augmentation`. The clean
  risk-vs-safety model (`phase1b`, no augmentation) scores **F1 36.75** — barely above baselines.

### V6 — Clean-room rewrite ([hypervul_fair_eval/](hypervul_fair_eval/))

- **Code:** [hypervul_fair_eval/src/fair_eval/](hypervul_fair_eval/src/fair_eval/) — isolated view
  builders (function / callgraph / pairwise / sequence / hyperedge), a **third** independent
  re-implementation of every baseline and of HyperVul
  ([models/hypervul.py](hypervul_fair_eval/src/fair_eval/models/hypervul.py)), with an explicit
  import-boundary check so RQ1 baselines cannot touch the hyperedge builder.
- **Purpose:** the right instinct — one loader, one trainer, one metric, one threshold policy, view
  isolation to prevent leakage.
- **Reality:** it is honest and it shows the tie (§4). But it is *another* parallel codebase rather than
  the replacement of the others, and its own [IMPLEMENTATION_PLAN.md](hypervul_fair_eval/IMPLEMENTATION_PLAN.md)
  §10 ships **demo placeholder tables** (F1 78.2 for HyperVul-Full) right next to the real ones — exactly
  the "assumes/demo data" problem you flagged.

---

## 3. How the baselines were built — and why that is a problem

The baselines are **re-implemented at least three times, differently**, and that inconsistency invalidates
cross-version comparison:

| Where | Baseline set | Built how |
|---|---|---|
| V1–V2 (iterations) | Slither, Mythril, simple MLPs | external tools + ad-hoc scripts, old leaky split |
| V3 ([src/models/](src/models/)) | set-pool, pairwise-GCN/GAT (clique), HypergraphConv | one shared skeleton — the *only* fair set |
| V5 ([scripts/run_phase0d_clean_baselines.py](scripts/run_phase0d_clean_baselines.py)) | Function-MLP, Function+Features, Sequence-BiGRU, CallGraph-GAT, Pairwise-RGCN, Pairwise-GAT | phase-specific re-implementation |
| V6 ([hypervul_fair_eval/](hypervul_fair_eval/)) | same six names again | third independent re-implementation |

Consequences:
- The "baseline" F1 for, say, Sequence-BiGRU is **31.13** in
  [reports/final_comparison_tables.md](reports/final_comparison_tables.md), **24.26** in
  [hypervul_fair_eval/outputs/final_report.md](hypervul_fair_eval/outputs/final_report.md), and **41.86**
  in [self-docs/results.md](self-docs/results.md). Three different "same" baselines.
- Your own memory note [[baseline-comparison-must-retrain-ours]] records that a stale "Ours" row once
  *inverted* a result. That failure mode is baked into the repo structure: nothing forces all rows in a
  table to come from the same run.

---

## 4. The documentation-vs-code discrepancy (the core issue)

Three different "final" numbers exist for the same model. Only one is clean.

| Source | HyperVul F1 | Best baseline F1 | Verdict |
|---|---:|---:|---|
| Paper [hypervul_ictai_draft.tex:715](paper/hypervul_ictai_draft.tex#L715) & [self-docs/results.md](self-docs/results.md) | **64.34** | 50.00 | **leaky** — this is `shortcut_aug_bce:gated` |
| [reports/final_comparison_tables.md](reports/final_comparison_tables.md) clean row | **35.40 ± 3.46** | 31.6–33.6 | marginal / within noise |
| [hypervul_fair_eval/outputs/final_report.md](hypervul_fair_eval/outputs/final_report.md) | **27.62 ± 2.17** | 27.53 (func+feat) | **tie; loses PR-AUC 20.42 vs 33.43** |

Evidence that the 64.34 number is leaky, straight from the repo:
- [reports/final_comparison_tables.md:3](reports/final_comparison_tables.md#L3): *"Rows marked
  `shortcut_leaky_targeted_augmentation` are performance-oriented and not clean final evaluation."*
- The only rows reaching ~60 F1 are all tagged `shortcut_leaky_targeted_augmentation`.
- The clean `risk-vs-safety / gated` row is F1 **36.75**; the clean `Current HyperVul` row is F1 **35.40**.
- In the fully clean rewrite, HyperVul-Full **loses PR-AUC** (20.42) to the plainest Function-MLP
  baselines (31–33).

**So:** the paper's central empirical claim is currently supported only by a leaky training trick, and the
honest evaluations show parity, not superiority. The `.md`/`.tex` files present the leaky/demo numbers as
the result; the JSON files and the clean comparison table tell the true story.

---

## 5. Why the divergent versions failed — root causes

1. **The signal may not be there at the interaction level.** Across *every* clean codebase (V3, V5-clean,
   V6), the hyperedge model ties generic baselines. When four independent implementations all land on "tie,"
   the honest reading is that a frozen-SmartBERT interaction embedding + pooling carries most of the signal,
   and the hyperedge structure adds little **on this data**.

2. **Data too small and too imbalanced to resolve small gains.** Clean split: **215 train positives**,
   38 val, 41 test ([hypervul_fair_eval/outputs/final_report.md](hypervul_fair_eval/outputs/final_report.md)).
   A 3–5 F1 gap with ±2–4 std over 5 seeds and 41 test positives cannot be called significant — and the RQ2
   permutation test agrees (p ≈ 0.06–0.19).

3. **Divergence instead of iteration.** The [self-docs/steps.md](self-docs/steps.md) roadmap explicitly
   says "do not blindly stack methods; one phase, one report, decide next from evidence." The repo did the
   opposite: six architectures and three codebases coexist, none retired.

4. **Baseline drift.** Because baselines were rebuilt per phase (§3), "wins" were often against a weaker
   re-implementation, not a fixed strong baseline — the exact trap in [[baseline-comparison-must-retrain-ours]].

5. **Leak-to-win pressure.** When clean numbers stayed flat, the project reached for targeted augmentation
   that leaked reentrancy patterns (V5/phase1d) and reported those as the headline. This is the terminal
   failure mode: the model didn't get better, the evaluation got easier.

6. **Docs written ahead of results.** Demo/placeholder tables (IMPLEMENTATION_PLAN §10, results.md, paper)
   were written as if achieved. Anyone reading the prose gets a materially wrong picture of performance.

---

## 6. Consolidated issue list

- [ ] **Headline result is leaky.** 64.34 F1 = `shortcut_leaky_targeted_augmentation`. Must not appear in a paper.
- [ ] **Three conflicting "final" numbers** for the same model/baselines; no single source of truth.
- [ ] **Baselines re-implemented 3×**, never fixed — comparisons are not apples-to-apples.
- [ ] **Six live model families / three codebases**; no promotion/retirement discipline.
- [ ] **Demo/placeholder tables** interleaved with real ones in plan, results, and paper.
- [ ] **Tiny test set** (41 positives) → no statistical power; observed gaps are within noise.
- [ ] **Label noise acknowledged but unresolved** (phase1c cleaned some; SWC-104 view/pure fixes in V1).
- [ ] **Unit-of-prediction keeps changing** (interaction ↔ contract-MIL) — metrics not comparable across phases.
- [ ] **PR-AUC regression** ignored: clean HyperVul-Full loses ranking quality to the simplest baseline.
- [ ] **V4 (G-HAN/APPNP/MoE) is dead code** with no promoted result — either evaluate it or delete it.

---

## 7. If starting over: the clean plan (data → labels → model → baselines → ablation)

The goal is a *defensible* claim, which may be "hyperedges give a small, significant gain" rather than a
64-F1 headline. Keep **one** codebase — [hypervul_fair_eval/](hypervul_fair_eval/) is the right base;
delete or archive V1–V5 to `legacy/`.

### 7.1 Data collection
- Fix the vulnerability scope to **reentrancy first** (it matches the interaction story and has the least
  label noise). Add a second CWE only after reentrancy is defensible.
- Grow positives before touching architecture. 215 train positives is the binding constraint. Target
  ≥1,000 real positives by pulling from SmartBugs-Curated, SolidiFI-injected, the FORGE-Curated set already
  vendored in [data/FORGE-Curated/](data/FORGE-Curated/), and audited DAppSCAN findings — **with provenance
  recorded per example**.
- Keep a permanently held-out **clean-negative** corpus (OpenZeppelin/Aave/Liquity already cloned in
  [scratch/clones/](scratch/clones/)) for FPR reporting only — never train on it.

### 7.2 Labeling
- Label at the **function/interaction** level with a written rubric (external call, state-write ordering,
  guard presence). Store the rubric and the raw tool/human evidence next to each label.
- Do a two-pass review with an explicit **inter-annotator agreement** number. Quarantine disagreements
  (the phase1c machinery already does this — [scripts/run_phase1c_label_cleanup.py](scripts/run_phase1c_label_cleanup.py)).
- Freeze labels and version them (`labels_v2/`) before any training. No label edits after freeze.

### 7.3 Splits
- **Project/contract-disjoint** splits, decided once, checked with an automated leakage test, committed.
- Report the split table (contracts, interactions, pos/neg, pos-rate, source mix) and never re-split to
  chase numbers.

### 7.4 Model — the architecture to standardize on
Adopt the [src/models/](src/models/) shared-skeleton discipline as the *only* model interface:

```
member embeddings (768) ⊕ symbolic block
      → [encoder]            # swap ONLY this block per experiment
      → attention pool over members
      → MLP head (+ optional additive localization head)
```

- **Ours = `HypergraphNN`** ([src/models/hypergraph_nn.py](src/models/hypergraph_nn.py)): two-stage
  attention hyperedge message passing. This is already the cleanest hyperedge encoder.
- Keep symbolic features (they gave the one *replicated* gain — [[safety-aware-features-reduce-ood-fpr]]).
- Drop the leaky augmentation, the SCL loss trick ([[scl-localization-fpr-did-not-replicate]]), and the
  contract-graph G-HAN/MoE branch until the interaction-level claim is settled.
- Only after RQ2 is significant, revisit **contract-level MIL** as a *deployment* aggregation, reported
  separately — not as the thing that produces the headline.

### 7.5 Baselines — build once, freeze
- One baseline module, one trainer, one loss (weighted BCE or ASL), one threshold policy
  (validation-selected recall target), 5 seeds. Every table row comes from the **same run**.
- RQ1 (generic: Function-MLP, +Features, Sequence, CallGraph-GNN, Pairwise-GNN) must never import the
  hyperedge builder — keep V6's import-boundary check.
- RQ2 (set-pool / pairwise-clique / hyperedge) share the V3 skeleton so only the operator differs.

### 7.6 Ablation & reporting
- Report mean ± std over seeds 42–46 **and** a paired significance test (McNemar or seed-paired
  permutation, already in V6). State p-values; do not claim wins at p > 0.05.
- Primary metrics under imbalance: **PR-AUC + F2 + recall at a fixed validation threshold**; ROC-AUC
  secondary. Always include clean-negative FPR.
- One `final_report.md`, generated by one script, is the **only** results artifact. Delete every other
  results `.md`. No hand-written numbers, ever. No demo/placeholder tables in any committed file.

### 7.7 Decision gate
If, after §7.1–7.6, HyperGraphNN does not beat the strongest baseline on PR-AUC with p < 0.05, the honest
paper is: *"higher-order representation gives localization quality (Top-k/MRR) and FPR benefits at parity
detection,"* which the localization tables actually support more strongly than the detection tables do.
That is a real, publishable, non-leaky claim — pivot to it rather than leaking to inflate detection F1.

---

## 8. One-paragraph verdict

The engineering is competent (the shared-skeleton ablation and the fair-eval rewrite are genuinely good),
but the project mistook **motion for progress**: six architectures, three baseline re-implementations, and
a stack of narrative docs that quote leaky or demo numbers. On clean, contract-disjoint data with baselines
retrained identically, HyperVul **ties** the baselines and **loses PR-AUC** to the simplest one; the only
"win" is a leak the repo itself flags. Consolidate to the fair-eval codebase, grow the positives, freeze
labels and baselines, and either earn a *significant* PR-AUC win or pivot the paper to the localization/FPR
claim the data actually supports.
