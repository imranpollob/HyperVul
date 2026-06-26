# HyperVul Fair Evaluation Implementation Plan

Status: planning only. No implementation code has been written in this folder yet.

This document is both the implementation plan and the coding step log for the new clean codebase. Every coding step should update the log at the end of this file with date, files changed, command run, and result.

---

## 1. Project Goal

The goal of this project is to build a fair, reviewer-defensible experimental codebase for evaluating **HyperVul**, a hyperedge-based smart contract vulnerability detector.

The central academic claim is:

> Vulnerabilities in Solidity smart contracts often arise from higher-order interactions among a function, accessed state variables, external calls, guards, and cross-contract context. A hyperedge representation preserves these n-ary interactions more faithfully than generic function-only, sequence, call-graph, or pairwise graph representations, leading to better vulnerability detection.

This new codebase will separate:

1. Generic literature-style baselines that do not use HyperVul hyperedges.
2. Controlled representation ablations that isolate the effect of hyperedge representation.
3. HyperVul component ablations that test the contribution of security/symbolic features.

---

## 2. Problem We Are Solving

Most machine learning vulnerability detectors represent code using one of these forms:

- single function embeddings
- function sequences
- AST, CFG, DFG, or call graphs
- pairwise graphs between program entities

These representations can lose information when a vulnerability depends on a joint relation such as:

```text
function f
+ shared state variable s
+ external call c
+ missing or weak guard g
+ cross-contract context x
```

A pairwise graph can encode relationships such as:

```text
f -- s
f -- c
s -- c
```

but this decomposes the original multi-way interaction into separate binary edges. The risk is that the model sees isolated pairwise signals but not the full interaction pattern that makes the behavior vulnerable.

The research problem is therefore:

> Can a hyperedge-based representation improve vulnerability detection by preserving higher-order interaction structure that generic baselines cannot naturally represent?

---

## 3. Proposed Solution

HyperVul will model each vulnerability-relevant interaction as a hyperedge containing multiple typed members:

```text
hyperedge e = {
  function node,
  state variable nodes,
  external call / callee nodes,
  optional guard/security context features,
  optional cross-contract context
}
```

The model will learn whether each interaction hyperedge is vulnerable.

The clean evaluation codebase will implement:

- a common data loading and split interface
- generic baseline builders that avoid HyperVul hyperedge construction
- HyperVul hyperedge builders used only for HyperVul and representation ablations
- consistent training loops, metrics, thresholding, and reporting across all models
- paper-ready result tables with mean/std across seeds and statistical tests where appropriate

---

## 4. Novelty

The novelty to be evaluated is not merely "using a neural model." The novelty is the **representation**:

1. **Interaction-level prediction**
   - Predict vulnerability at the interaction/function-risk unit rather than only contract-level labels.

2. **Higher-order hyperedge representation**
   - Preserve the joint relation among function, state variables, external calls, and security context.

3. **Typed interaction members**
   - Distinguish function, state, callee, guard, and cross-contract signals.

4. **Security-aware symbolic augmentation**
   - Add static/security features such as guard presence, nonReentrant-like protection, target kind, and cross-contract indicators.

5. **Localizable vulnerability evidence**
   - Support reporting which function-state-callee tuple contributes most to the prediction.

The experiments must prove these claims separately. In particular, generic baselines must not use the proposed hyperedge representation.

---

## 5. Dataset Plan

### 5.1 Source Datasets

The new codebase will reuse the existing project datasets where possible:

- `data/splits/train.json`
- `data/splits/val.json`
- `data/splits/test.json`
- `data/splits/train_augmented.json`
- `data/splits/val_features.json`
- `data/splits/test_features.json`
- `data/contract_graphs/train.json`
- `data/contract_graphs/val.json`
- `data/contract_graphs/test.json`
- clean-negative sources under `experiments/latest1/` or `experiments/results/`

Candidate external/clean-negative sources already present:

- OpenZeppelin clean contracts
- Aave clean contracts
- MakerDAO/Bancor external clean negatives
- Liquity clean negatives
- FORGE-curated vulnerable examples
- DAppSCAN-derived examples, if label quality is sufficient

### 5.2 Dataset Units

We will explicitly define three data views.

| View | Used By | Unit | Uses HyperVul Hyperedge? |
|---|---|---:|---:|
| Function view | Function MLP, Function+Features MLP | function | No |
| Generic graph view | CallGraph-GNN, PairwiseGraph-GNN | function/state/call graph | No |
| Hyperedge view | HyperVul, representation ablation | interaction hyperedge | Yes |

This distinction is mandatory. The code should make accidental leakage hard by using separate builder modules.

### 5.3 Split Policy

The default split should be project/contract-disjoint where possible:

- train
- validation
- test

The split report must include:

- number of contracts
- number of functions/interactions
- positive count
- negative count
- positive rate
- source distribution
- duplicate/near-duplicate checks if available

No model may tune on the test set.

### 5.4 Label Policy

Labels should be documented at the interaction/function level:

- `1`: vulnerable interaction/function
- `0`: clean interaction/function

Potential risk: some "clean" examples may be unlabeled vulnerable code. The evaluation should therefore report robustness on curated clean-negative subsets separately.

---

## 6. Class Imbalance Strategy

Smart contract vulnerability datasets are usually highly imbalanced. The plan should handle this explicitly rather than relying only on accuracy.

### 6.1 Training-Time Handling

Use one or more of the following, consistently across comparable neural models:

- positive class weighting in BCE/ASL loss
- balanced mini-batch sampling where each batch contains positives when possible
- fixed clean-negative sampling budget for controlled experiments
- optional focal/asymmetric loss only in a clearly labeled ablation

Default recommendation:

```text
Use weighted BCE or asymmetric loss with pos_weight = #negative / #positive.
Keep the same loss across baselines in RQ1 and RQ2 unless the baseline requires otherwise.
```

### 6.2 Evaluation-Time Handling

Do not rely on accuracy. Report:

- precision
- recall
- F1
- F2, because missing vulnerabilities is expensive
- PR-AUC, because the positive class is rare
- ROC-AUC, as a secondary ranking metric
- false positive rate on clean-negative corpora

Use a validation-selected threshold:

```text
Select the highest threshold that reaches target validation recall, e.g. 95%.
Evaluate once on test using that threshold.
```

Also report threshold-free PR-AUC and ROC-AUC.

---

## 7. Project Architecture

The new codebase should live under:

```text
hypervul_fair_eval/
```

Proposed structure:

```text
hypervul_fair_eval/
  IMPLEMENTATION_PLAN.md
  README.md
  configs/
    data.yaml
    rq1_generic_baselines.yaml
    rq2_representation_ablation.yaml
    rq3_hypervul_ablation.yaml
  src/
    data/
      schemas.py
      splits.py
      load_existing.py
      validation.py
    features/
      embeddings.py
      scalar_features.py
      symbolic_security.py
    builders/
      function_view.py
      callgraph_view.py
      pairwise_graph_view.py
      hyperedge_view.py
    models/
      function_mlp.py
      sequence_model.py
      callgraph_gnn.py
      pairwise_gnn.py
      hyperedge_nn.py
      hypervul.py
    training/
      losses.py
      trainer.py
      thresholding.py
      metrics.py
      seeds.py
    reporting/
      aggregate.py
      tables.py
      significance.py
  scripts/
    rq1_run_generic_baselines.py
    rq2_run_representation_ablation.py
    rq3_run_hypervul_ablation.py
    make_final_report.py
  outputs/
    .gitkeep
```

### 7.1 Design Rules

1. RQ1 generic baselines must not import or call the hyperedge builder.
2. RQ2 representation ablation may use the hyperedge builder because the purpose is to compare encodings of the same candidate interactions.
3. RQ3 HyperVul ablation may use full HyperVul inputs and vary only one component at a time.
4. Every runner must write JSON and Markdown output.
5. Every result must include config, seed, split paths, model name, threshold rule, and git commit if available.

---

## 8. Baseline Plan

### 8.1 RQ1: Generic Literature-Style Baselines

RQ1 question:

> Does full HyperVul outperform generic vulnerability detection baselines that do not use HyperVul hyperedges?

Recommended minimum baselines:

| Baseline | Representation | Input Unit | Uses Hyperedge? | Purpose |
|---|---|---:|---:|---|
| Function-MLP | function embedding only | function | No | Semantic lower bound |
| Function+Features MLP | function embedding + generic counts | function | No | Tests simple metadata gain |
| Function Sequence Model | ordered function embeddings per contract | function/contract | No | Tests sequential context |
| CallGraph-GCN | functions as nodes, call edges | graph | No | Standard software graph baseline |
| PairwiseGraph-GCN | function-state/callee binary edges | graph | No | Strong non-hyperedge structural baseline |
| Static Analyzer: Slither | rules/static analysis | contract/function | No | Non-ML practical baseline |
| Static Analyzer: Mythril | symbolic/security analysis | contract/function | No | Non-ML practical baseline |

Important: the pairwise graph baseline should be built from generic binary program relations, not from first constructing HyperVul hyperedges and then flattening them.

### 8.2 RQ2: Controlled Representation Ablation

RQ2 question:

> Given the same candidate interaction information, does preserving it as a hyperedge outperform set pooling and pairwise graph reductions?

Models:

| Model | Same Candidates? | Representation | Purpose |
|---|---:|---|---|
| Set-Pool | Yes | bag of interaction members | No-structure control |
| Pairwise-GCN | Yes | hyperedge members flattened to pairwise edges | Binary graph reduction |
| Pairwise-GAT | Yes | pairwise edges with attention | Stronger binary graph reduction |
| HyperedgeNN | Yes | true hyperedge incidence | Tests representational novelty |

This experiment should be presented as an internal representation ablation, not as generic literature baselines.

### 8.3 RQ3: HyperVul Component Ablation

RQ3 question:

> Which HyperVul components contribute to final performance?

Variants:

| Variant | Hyperedge Representation | Symbolic Features | Localization | Purpose |
|---|---:|---:|---:|---|
| HyperVul-EmbOnly | Yes | No | Optional | Hyperedge-only core |
| HyperVul-Security | Yes | Security subset | Yes | Tests security guard/context features |
| HyperVul-Full | Yes | Full | Yes | Proposed model |
| HyperVul-NoLocalize | Yes | Full | No | Tests localization head contribution |
| HyperVul-NoContrastive | Yes | Full | Yes | Tests contrastive calibration contribution |

---

## 9. Evaluation Plan

### 9.1 Seeds

Run each neural model over:

```text
42, 43, 44, 45, 46
```

Report mean and standard deviation. Include per-seed JSON files.

### 9.2 Metrics

Primary metrics:

- F1
- F2
- recall at validation-selected threshold
- precision at validation-selected threshold
- PR-AUC

Secondary metrics:

- ROC-AUC
- false positive rate on clean-negative corpora
- cross-contract F1 if labels support it
- intra-contract F1 if labels support it
- training time and inference time if feasible

### 9.3 Statistical Testing

Use paired tests where possible:

- McNemar test for paired classification correctness on the same test examples
- bootstrap confidence intervals for F1/F2/PR-AUC
- paired seed-level comparison as a secondary summary

For paper claims, avoid claiming superiority from one seed.

---

## 10. Planned Paper Tables

The numeric values below are **demo placeholders** used to show the intended paper-table shape. They are not achieved results and should not be treated as targets to reproduce. The measured values are generated dynamically in `hypervul_fair_eval/outputs/final_report.md`.

### Table 1: Dataset Statistics

| Split | Contracts | Functions | Interactions | Positives | Negatives | Positive Rate |
|---|---:|---:|---:|---:|---:|---:|
| Train | 820 | 14,500 | 18,900 | 1,120 | 17,780 | 5.9% |
| Validation | 105 | 1,780 | 2,260 | 135 | 2,125 | 6.0% |
| Test | 110 | 1,920 | 2,410 | 148 | 2,262 | 6.1% |

### Table 2: RQ1 Generic Baselines vs HyperVul-Full

| Model | Uses Hyperedge? | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Slither | No | 41.2 | 52.7 | 46.2 | 49.9 | n/a | n/a |
| Mythril | No | 33.5 | 44.1 | 38.1 | 41.5 | n/a | n/a |
| Function-MLP | No | 54.0 +/- 2.1 | 71.2 +/- 3.0 | 61.4 +/- 2.4 | 66.9 +/- 2.6 | 63.8 +/- 2.2 | 84.0 +/- 1.5 |
| Function+Features MLP | No | 57.8 +/- 1.8 | 73.5 +/- 2.7 | 64.7 +/- 2.0 | 69.7 +/- 2.2 | 66.9 +/- 2.0 | 85.7 +/- 1.3 |
| Sequence Model | No | 59.4 +/- 2.0 | 75.1 +/- 2.5 | 66.3 +/- 2.1 | 71.3 +/- 2.0 | 68.4 +/- 1.8 | 86.5 +/- 1.2 |
| CallGraph-GCN | No | 61.0 +/- 1.9 | 76.0 +/- 2.4 | 67.7 +/- 1.9 | 72.5 +/- 2.1 | 70.2 +/- 1.7 | 87.3 +/- 1.1 |
| PairwiseGraph-GCN | No | 63.3 +/- 1.7 | 78.5 +/- 2.2 | 70.1 +/- 1.8 | 75.0 +/- 1.9 | 72.5 +/- 1.6 | 88.4 +/- 1.0 |
| HyperVul-Full | Yes | 72.5 +/- 1.5 | 84.8 +/- 1.9 | 78.2 +/- 1.6 | 82.0 +/- 1.7 | 82.7 +/- 1.4 | 93.1 +/- 0.8 |

### Table 3: RQ2 Controlled Representation Ablation

| Model | Candidate Interactions | Representation | Precision | Recall | F1 | F2 | PR-AUC |
|---|---:|---|---:|---:|---:|---:|---:|
| Set-Pool | Same | no edges | 60.5 +/- 2.0 | 77.0 +/- 2.4 | 67.8 +/- 2.1 | 73.0 +/- 2.2 | 70.1 +/- 1.9 |
| Pairwise-GCN | Same | pairwise clique | 64.2 +/- 1.8 | 79.1 +/- 2.2 | 70.9 +/- 1.9 | 75.8 +/- 1.8 | 73.3 +/- 1.7 |
| Pairwise-GAT | Same | pairwise attention | 65.7 +/- 1.7 | 80.0 +/- 2.0 | 72.1 +/- 1.8 | 76.8 +/- 1.7 | 74.8 +/- 1.6 |
| HyperedgeNN | Same | true hyperedge | 70.1 +/- 1.5 | 82.9 +/- 1.9 | 76.0 +/- 1.6 | 80.1 +/- 1.5 | 79.4 +/- 1.3 |

### Table 4: RQ3 HyperVul Component Ablation

| Variant | Symbolic Features | Localization | Contrastive | Precision | Recall | F1 | F2 | PR-AUC |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| HyperVul-EmbOnly | none | Yes | Yes | 68.2 +/- 1.8 | 81.5 +/- 2.1 | 74.3 +/- 1.9 | 78.8 +/- 1.8 | 77.5 +/- 1.6 |
| HyperVul-Security | security subset | Yes | Yes | 70.4 +/- 1.6 | 83.0 +/- 1.9 | 76.2 +/- 1.7 | 80.2 +/- 1.6 | 80.1 +/- 1.5 |
| HyperVul-Full | full | Yes | Yes | 72.5 +/- 1.5 | 84.8 +/- 1.9 | 78.2 +/- 1.6 | 82.0 +/- 1.7 | 82.7 +/- 1.4 |
| HyperVul-NoLocalize | full | No | Yes | 70.6 +/- 1.7 | 82.2 +/- 2.0 | 76.0 +/- 1.8 | 79.7 +/- 1.8 | 80.5 +/- 1.5 |
| HyperVul-NoContrastive | full | Yes | No | 69.9 +/- 1.8 | 81.8 +/- 2.1 | 75.4 +/- 1.9 | 79.2 +/- 1.9 | 79.8 +/- 1.6 |

### Table 5: Clean-Negative False Positive Rate

| Model | OpenZeppelin FPR | Aave FPR | MakerDAO/Bancor FPR | Liquity FPR | Mean Clean FPR |
|---|---:|---:|---:|---:|---:|
| Function-MLP | 16.8 | 19.4 | 22.1 | 18.7 | 19.3 |
| PairwiseGraph-GCN | 12.5 | 15.2 | 17.8 | 14.1 | 14.9 |
| HyperedgeNN | 9.8 | 12.0 | 13.5 | 11.2 | 11.6 |
| HyperVul-Full | 6.4 | 8.1 | 9.7 | 7.5 | 7.9 |

### Table 6: Statistical Significance Summary

| Comparison | Test | Statistic | p-value | Interpretation |
|---|---|---:|---:|---|
| HyperVul-Full vs PairwiseGraph-GCN | McNemar | 18.4 | 0.00002 | HyperVul improves paired correctness |
| HyperedgeNN vs Pairwise-GAT | McNemar | 9.7 | 0.0018 | Hyperedge representation improves over pairwise reduction |
| HyperVul-Full vs HyperVul-EmbOnly | bootstrap F1 delta | +3.9 | 0.004 | Symbolic features improve performance |

---

## 11. Step-by-Step Implementation Plan

### Step 0: Planning Approval

- [x] Create this implementation plan.
- [ ] Review plan with project owner.
- [ ] Freeze experimental claims and RQs before writing code.

### Step 1: Create Clean Project Skeleton

- [x] Add `README.md` for the new codebase.
- [x] Add `configs/`.
- [x] Add `src/` module layout.
- [x] Add `scripts/` runners.
- [x] Add `outputs/` for generated results.

### Step 2: Data Schemas and Split Validation

- [x] Define canonical data schemas for graph view.
- [x] Implement loaders for existing split files.
- [x] Implement split statistics report.
- [x] Implement label distribution and source distribution report.
- [x] Add duplicate/leakage checks if available from existing metadata.

### Step 3: Generic Baseline Builders

- [x] Build Function view without hyperedge construction.
- [x] Build Function+Features view with generic scalar features.
- [x] Build Sequence view per contract.
- [x] Build CallGraph view from function-call relations.
- [x] Build PairwiseGraph view from generic binary relations.

### Step 4: Hyperedge Builder

- [x] Build HyperVul hyperedge view.
- [x] Keep this builder isolated from RQ1 generic baselines.
- [x] Add validation that RQ1 scripts do not import this module.

### Step 5: Model Implementations

- [x] Implement Function-MLP.
- [x] Implement Function+Features MLP.
- [x] Implement Sequence model.
- [x] Implement CallGraph-GCN.
- [x] Implement PairwiseGraph-GCN/GAT.
- [x] Implement HyperedgeNN.
- [x] Implement HyperVul-Full and ablation flags.

### Step 6: Training and Evaluation Core

- [x] Implement shared seed control.
- [x] Implement class-weighted loss.
- [x] Implement threshold selection using validation recall.
- [x] Implement metrics.
- [x] Implement per-seed JSON output.
- [x] Implement Markdown report output.

### Step 7: RQ1 Generic Baseline Experiment

- [x] Implement and smoke-test generic baseline runner.
- [ ] Run static analyzer baselines or import existing results. Deferred until compiler/toolchain handling is stabilized; not abandoned.
- [x] Run Function-MLP over 5 seeds.
- [x] Run Function+Features MLP over 5 seeds.
- [x] Run Sequence model over 5 seeds.
- [x] Run CallGraph-GCN over 5 seeds.
- [x] Run PairwiseGraph-GCN over 5 seeds.
- [x] Run PairwiseGraph-GAT over 5 seeds.
- [ ] Compare against HyperVul-Full.

### Step 8: RQ2 Representation Ablation

- [x] Run Set-Pool over same interaction candidates.
- [x] Run Pairwise-GCN over same interaction candidates.
- [x] Run Pairwise-GAT over same interaction candidates.
- [x] Run HyperedgeNN over same interaction candidates.
- [x] Add paired significance tests.

### Step 9: RQ3 HyperVul Component Ablation

- [x] Run HyperVul-EmbOnly.
- [x] Run HyperVul-Security.
- [x] Run HyperVul-Full.
- [x] Run HyperVul-NoLocalize.
- [x] Run HyperVul-NoContrastive.
- [x] Aggregate deltas.

### Step 10: Final Report Generation

- [x] Generate dataset table.
- [x] Generate RQ1 table.
- [x] Generate RQ2 table.
- [x] Generate RQ3 table.
- [ ] Generate clean-negative FPR table.
- [x] Generate significance table.
- [x] Export `outputs/final_report.md` and `outputs/final_report.json`.

### Step 11: Reviewer Audit Checklist

- [ ] Confirm RQ1 generic baselines do not use HyperVul hyperedges.
- [ ] Confirm RQ2 is described as representation ablation, not generic baseline comparison.
- [ ] Confirm all neural models use same seeds and split.
- [ ] Confirm threshold is selected only on validation.
- [ ] Confirm no test examples leak into train/validation.
- [ ] Confirm class imbalance is addressed and metrics are appropriate.
- [ ] Confirm every table reports mean/std or confidence intervals.
- [ ] Confirm all claims are backed by a corresponding table.

---

## 12. Coding Step Log

Use this section as the running implementation log.

| Date | Step | Files Changed | Command / Action | Result | Notes |
|---|---|---|---|---|---|
| 2026-06-25 | Planning | `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | Created implementation plan | Pending review | No code implemented |
| 2026-06-25 | Dataset audit | `hypervul_fair_eval/scripts/audit_dataset.py`, `hypervul_fair_eval/outputs/dataset_audit.json`, `hypervul_fair_eval/outputs/dataset_audit.md`, `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | `python3 hypervul_fair_eval/scripts/audit_dataset.py` | Passed: 0 failures, 0 warnings | Existing `data/contract_graphs` are suitable canonical project-disjoint splits; 1803 canonical clean negatives found across 4 pools |
| 2026-06-25 | Data layer skeleton | `hypervul_fair_eval/README.md`, `hypervul_fair_eval/configs/data.yaml`, `hypervul_fair_eval/src/fair_eval/**`, `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | `PYTHONPATH=hypervul_fair_eval/src python3 - <<'PY' ...`; `python3 -m py_compile ...` | Passed | Added typed graph schemas, existing-data loaders, split overlap utilities, validation statistics, and package skeleton |
| 2026-06-25 | Generic baseline builders | `hypervul_fair_eval/src/fair_eval/builders/**`, `hypervul_fair_eval/scripts/inspect_generic_views.py`, `hypervul_fair_eval/outputs/generic_view_inspection.json`, `hypervul_fair_eval/outputs/generic_view_inspection.md`, `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | `python3 hypervul_fair_eval/scripts/inspect_generic_views.py`; `python3 -m py_compile ...` | Passed | Built RQ1 function, function+generic-features, sequence, callgraph, and pairwise graph views without using HyperVul hyperedges |
| 2026-06-25 | Hyperedge builder | `hypervul_fair_eval/src/fair_eval/builders/hyperedge_view.py`, `hypervul_fair_eval/scripts/inspect_hyperedge_view.py`, `hypervul_fair_eval/scripts/check_import_boundaries.py`, `hypervul_fair_eval/outputs/hyperedge_view_inspection.json`, `hypervul_fair_eval/outputs/hyperedge_view_inspection.md`, `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | `python3 hypervul_fair_eval/scripts/check_import_boundaries.py`; `python3 hypervul_fair_eval/scripts/inspect_hyperedge_view.py`; `python3 -m py_compile ...` | Passed | Built isolated HyperVul hyperedge view for RQ2/RQ3; verified RQ1 generic files do not import it |
| 2026-06-25 | Model implementations | `hypervul_fair_eval/src/fair_eval/models/**`, `hypervul_fair_eval/scripts/smoke_test_models.py`, `hypervul_fair_eval/outputs/model_smoke_tests.json`, `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | `python3 hypervul_fair_eval/scripts/smoke_test_models.py`; `python3 -m py_compile ...` | Passed | Added FunctionMLP, FunctionFeaturesMLP, sequence baseline, GCN/R-GCN/GAT node classifiers, HyperedgeNN, and HyperVul variants with synthetic forward-pass checks |
| 2026-06-25 | Training/evaluation core | `hypervul_fair_eval/src/fair_eval/training/**`, `hypervul_fair_eval/src/fair_eval/reporting/results.py`, `hypervul_fair_eval/scripts/smoke_test_training_core.py`, `hypervul_fair_eval/outputs/training_core_smoke_tests.json`, `hypervul_fair_eval/outputs/training_core_smoke_result.json`, `hypervul_fair_eval/outputs/training_core_smoke_result.md`, `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | `python3 hypervul_fair_eval/scripts/smoke_test_training_core.py`; `python3 -m py_compile ...` | Passed | Added seed control, weighted BCE/ASL, threshold policies, binary metrics, reusable train/predict loops, and JSON/Markdown result writers |
| 2026-06-25 | RQ1 generic baseline runner | `hypervul_fair_eval/src/fair_eval/features/embeddings.py`, `hypervul_fair_eval/src/fair_eval/training/simple_datasets.py`, `hypervul_fair_eval/scripts/rq1_run_generic_baselines.py`, `hypervul_fair_eval/outputs/rq1/**`, `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | `python3 hypervul_fair_eval/scripts/rq1_run_generic_baselines.py --models function-mlp function-features-mlp sequence callgraph-gcn pairwise-gcn pairwise-gat --seeds 42 --epochs 1 --batch-size 64 --threshold-policy max_f2`; `python3 -m py_compile ...` | Passed smoke run | Added end-to-end RQ1 runner for six generic neural baselines; full 5-seed paper run remains open |
| 2026-06-25 | RQ1 neural 5-seed run | `hypervul_fair_eval/outputs/rq1/**`, `hypervul_fair_eval/src/fair_eval/models/graph_models.py`, `hypervul_fair_eval/scripts/rq1_run_generic_baselines.py`, `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | `python3 hypervul_fair_eval/scripts/rq1_run_generic_baselines.py --models function-mlp function-features-mlp sequence callgraph-gcn pairwise-gcn pairwise-gat --seeds 42 43 44 45 46 --epochs 20 --batch-size 64 --threshold-policy max_f2`; reran optimized `pairwise-gat` only after vectorizing GAT aggregation | Passed | Completed 5-seed neural generic baselines; static analyzers deferred; HyperVul-Full comparison remains for later clean HyperVul/RQ3 phase |
| 2026-06-25 | RQ2 representation ablation | `hypervul_fair_eval/src/fair_eval/models/representation_models.py`, `hypervul_fair_eval/src/fair_eval/training/representation_datasets.py`, `hypervul_fair_eval/src/fair_eval/models/common.py`, `hypervul_fair_eval/scripts/rq2_run_representation_ablation.py`, `hypervul_fair_eval/outputs/rq2/**`, `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | `python3 hypervul_fair_eval/scripts/rq2_run_representation_ablation.py --models set-pool pairwise-gcn pairwise-gat hyperedge-nn --seeds 42 43 44 45 46 --epochs 20 --batch-size 128 --threshold-policy max_f2`; `python3 hypervul_fair_eval/scripts/rq2_run_representation_ablation.py --summarize-only`; `python3 -m py_compile ...` | Passed | Completed 5-seed controlled representation ablation and seed-paired sign-flip significance tests; vectorized segment softmax for HyperedgeNN runtime |
| 2026-06-25 | RQ3 HyperVul ablation | `hypervul_fair_eval/src/fair_eval/training/hypervul_datasets.py`, `hypervul_fair_eval/src/fair_eval/models/hypervul.py`, `hypervul_fair_eval/scripts/rq3_run_hypervul_ablation.py`, `hypervul_fair_eval/outputs/rq3/**`, `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | `python3 hypervul_fair_eval/scripts/rq3_run_hypervul_ablation.py --models emb-only security full no-localize no-contrastive --seeds 42 43 44 45 46 --epochs 20 --batch-size 128 --threshold-policy max_f2`; `python3 -m py_compile ...` | Passed | Completed 5-seed HyperVul component ablation; canonical graph view provides only 8-d security context, so `security` and `full` are equivalent in this run |
| 2026-06-25 | Final report and README | `hypervul_fair_eval/scripts/make_final_report.py`, `hypervul_fair_eval/outputs/final_report.md`, `hypervul_fair_eval/outputs/final_report.json`, `hypervul_fair_eval/README.md`, `README.md`, `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | `python3 hypervul_fair_eval/scripts/make_final_report.py`; `python3 -m py_compile ...` | Passed | Generated consolidated RQ1/RQ2/RQ3 report and documented all evaluation commands; clean-negative FPR table remains future work |
| 2026-06-25 | Full evaluation orchestrator and Table 2 fix | `hypervul_fair_eval/scripts/run_full_evaluation.py`, `hypervul_fair_eval/scripts/make_final_report.py`, `hypervul_fair_eval/outputs/final_report.md`, `hypervul_fair_eval/README.md`, `README.md`, `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` | `python3 hypervul_fair_eval/scripts/run_full_evaluation.py --dry-run`; `python3 hypervul_fair_eval/scripts/make_final_report.py`; `python3 -m py_compile ...` | Passed | Added one-command full pipeline; final Table 2 now compares generic baselines against `HyperVul-Full`; clarified that implementation-plan numeric tables are demo placeholders |
