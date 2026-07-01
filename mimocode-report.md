# HyperVul: Comprehensive Codebase Review and Divergent Version Analysis

> **Date**: 2026-07-01
> **Review scope**: All Python source code across the repository. MD files used only for context, not as evidence.
> **Finding**: The project contains 3 divergent codebases, each built around different assumptions, and none achieving the claimed performance targets.

---

## 1. The Three Divergent Codebases

The repository contains three structurally distinct implementations that never converge into a single coherent system. Each represents a different architectural hypothesis about how to solve smart contract vulnerability detection.

### Codebase A: The Legacy Pipeline (`model/`, `src/`, `scripts/`, `experiments/`)

**Files**: `model/latest1/model.py`, `model/latest1/ghan.py`, `model/latest1/train.py`, `model/latest1/run_representation_comparison.py`, `model/latest1/run_unit_comparison.py`, `model/latest1/run_baselines.py`, `src/models/ops.py`, `src/models/symbolic.py`, `src/models/set_pool.py`, `src/models/gnn_zoo.py`, `src/models/hypergraph_nn.py`

**Architecture**: A modular but tightly coupled system built incrementally over 4 phases (0a through 1d). The core model (`HyperedgeClassifier` in `model/latest1/model.py`) implements:
- `AttentionPooling`: Simple learned attention over padded member nodes (768 -> 128 -> 1)
- `SequenceAwarePooling`: Bidirectional LSTM or Transformer encoder before attention pooling
- `HyperedgeClassifier`: Pool -> 2-layer MLP -> optional `LocalizationHead`
- `LocalizationHead` (in `src/models/ops.py`): Factorized additive 3-way interaction scoring (function x state x callee)
- `ProjectionHead` + `SupConLoss`: Supervised contrastive learning for calibration
- `AsymmetricLoss`: Focal-like loss with asymmetric gamma (gamma_neg=4, gamma_pos=1, clip=0.05)

**Additionally**, a separate G-HAN family exists in `model/latest1/ghan.py`:
- `GHAN`: Edge-gated message passing with 4 typed edges (call_forward, call_reverse, shared_state, shared_callee)
- `APPNP`: Approximate personalized propagation with root-feature blending
- `GatedResidualGHAN`: Near-identity initialization for safe propagation
- `MoEHead` / `PooledMoEModel`: Mixture-of-experts conditioned on 8-dim security context
- `PooledContractGraphModel`: Composed pool -> G-HAN/APPNP -> head pipeline

**Training**: `model/latest1/train.py` implements the main pipeline:
- SCL pre-training phase (15 epochs) before joint CE + contrastive training
- K_app sweep over Aave clean negatives (0-225) with fixed K_oz=100
- Threshold tuning: highest threshold achieving >=95% validation recall
- Early stopping with patience=20 on validation loss
- Evaluates on 4 OOD holdouts (OZ-Holdout, MakerDAO, Bancor, Liquity)
- Hardcoded paths: `PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")` (line 16)

**Comparison scripts**:
- `run_representation_comparison.py`: Set-pool vs pairwise-GCN vs pairwise-GAT vs HypergraphNN over contract-scoped hypergraphs (363 lines). Uses `build_contract_graphs` from `scripts/build_hypergraph.py`.
- `run_unit_comparison.py`: Function-only vs {Func,State} vs {Func,Callee} vs Full variants (419 lines). Redefines `SequenceAwarePooling` and `HyperedgeClassifier` inline (duplicating `model.py`).
- `run_baselines.py`: {Func,Callee} and {Func,State} ablations with 8-config grid search + contract-level baseline (830 lines). Redefines `AttentionPooling` and `HyperedgeClassifier` inline (third copy).

**Critical observation**: `run_unit_comparison.py` and `run_baselines.py` both re-implement `HyperedgeClassifier` and `AttentionPooling` from scratch rather than importing from `model.py`. The unit comparison version drops localization head entirely. The baseline version uses plain `AttentionPooling` (not `SequenceAwarePooling`). These are **silently different models** presented as variants of the same system.

### Codebase B: The Fair Evaluation Rewrite (`hypervul_fair_eval/`)

**Files**: 40+ Python files under `hypervul_fair_eval/src/fair_eval/` and `hypervul_fair_eval/scripts/`

**Architecture**: A clean rewrite organized around three research questions (RQ1/RQ2/RQ3) with strict import boundaries:

**Data layer** (`src/fair_eval/data/`):
- `schemas.py`: Typed dataclasses (`GraphEdge`, `GraphNode`, `ContractGraph`) with `from_dict` deserialization
- `load_existing.py`: Canonical JSON split loaders
- `splits.py`: Project-disjoint and contract-disjoint overlap checks
- `validation.py`: Dataset statistics and label distribution reports

**Feature processing** (`src/fair_eval/features/`):
- `embeddings.py`: SHA-256 hash-based embedding lookup from `node_embeddings.pt` and `member_embeddings.pt`
- `symbolic.py`: Regex-based extraction of visibility, mutability, nonReentrant, state access, target kinds

**View builders** (the key architectural separation):
- `builders/function_view.py`: Function-only (no hyperedges)
- `builders/sequence_view.py`: Ordered function sequences per contract
- `builders/callgraph_view.py`: Function-call graph edges
- `builders/pairwise_graph_view.py`: Clique expansion from hyperedge members
- `builders/hyperedge_view.py`: Isolated hyperedge construction (only for RQ2/RQ3)

**Models**:
- `models/function_mlp.py`: `FunctionMLP` and `FunctionFeaturesMLP`
- `models/sequence_model.py`: Bidirectional GRU
- `models/graph_models.py`: `MeanGraphConv`, `EdgeTypeGraphConv` (R-GCN), `GraphAttentionLayer` (single-head GAT)
- `models/representation_models.py`: `SetPoolClassifier`, `PairwiseMemberGNNClassifier`
- `models/hyperedge_nn.py`: Node-hyperedge message passing with `SegmentAttentionPool` and LayerNorm residual
- `models/hypervul.py`: `HyperVulModel` with bidirectional GRU, attention readout, optional `TupleLocalizationHead`, ablation flags

**Training infrastructure**:
- `training/trainer.py`: Generic `train_one_epoch()` and `predict()` with model-specific `step_fn` callables
- `training/losses.py`: `AsymmetricLoss` (duplicated from train.py), `bce_with_logits_for_labels`
- `training/metrics.py`: `binary_metrics()` with precision/recall/F1/F2/PR-AUC/ROC-AUC/FPR/specificity
- `training/thresholding.py`: Grid search over policies (max_f1, max_f2, target_recall, target_precision)
- `training/seeds.py`: Deterministic seed control

**Critical observation**: The fair eval codebase implements `AsymmetricLoss` independently in `training/losses.py`, duplicating the one in `model/latest1/train.py`. The `SegmentAttentionPool` is re-implemented in `hyperedge_nn.py` and again in `hypervul.py`. The `TupleLocalizationHead` in `hypervul.py` is a simplified version of `LocalizationHead` in `ops.py` (no `loc_gate`, no `out` linear layer for interaction context). These are structurally different models claiming to be the same HyperVul.

### Codebase C: The Baseline Zoo (`hypervul_fair_eval/scripts/`)

**Files**: `rq1_run_generic_baselines.py`, `rq2_run_representation_ablation.py`, `rq3_run_hypervul_ablation.py`, `run_strong_baseline_sweep.py`, `run_hypervul_quick_sweep.py`, `run_hypervul_tool_evaluation.py`

This is not a separate codebase but a set of runner scripts that expose the configuration space. Key observation: each runner independently defines its own training loop, data loading, and metric computation. The "strong baseline sweep" (`run_strong_baseline_sweep.py`) and the "hypervul tool evaluation" (`run_hypervul_tool_evaluation.py`) are parallel entry points that duplicate logic from the RQ runners but with different default hyperparameters (200 epochs vs 20 epochs, early stopping, SCL pre-training).

---

## 2. Performance Comparison Across Versions

### What the actual code produces (from `hypervul_fair_eval/outputs/final_report.md`)

**RQ1 Generic Baselines (5 seeds)**:

| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|
| function-mlp | 17.31 | 64.39 | 26.95 | 40.92 | 31.38 | 83.08 |
| function-features-mlp | 17.31 | 67.80 | 27.53 | 42.70 | 33.43 | 83.88 |
| sequence | 15.00 | 69.76 | 24.26 | 39.13 | 22.73 | 83.06 |
| callgraph-gcn | 17.17 | 63.41 | 26.45 | 39.88 | 27.83 | 83.23 |
| pairwise-gcn | 13.57 | 51.71 | 21.18 | 32.33 | 19.50 | 80.49 |
| pairwise-gat | 14.46 | 72.68 | 24.03 | 39.99 | 29.19 | 83.16 |
| **HyperVul-Full** | **17.35** | **70.24** | **27.62** | **43.12** | **20.42** | **82.95** |

**RQ2 Representation Ablation (5 seeds)**:

| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|
| set-pool | 13.42 | 65.85 | 22.25 | 36.83 | 22.95 | 79.79 |
| pairwise-gcn | 13.37 | 54.15 | 21.24 | 33.11 | 21.40 | 78.93 |
| pairwise-gat | 15.16 | 59.51 | 24.01 | 37.19 | 27.99 | 80.16 |
| hyperedge-nn | 17.65 | 59.02 | 27.08 | 39.97 | 26.45 | 81.08 |

**RQ3 HyperVul Component Ablation (5 seeds)**:

| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|
| emb-only | 18.28 | 61.46 | 28.09 | 41.56 | 22.99 | 83.46 |
| security | 17.35 | 70.24 | 27.62 | 43.12 | 20.42 | 82.95 |
| full | 17.35 | 70.24 | 27.62 | 43.12 | 20.42 | 82.95 |
| no-localize | 15.77 | 58.54 | 24.37 | 36.82 | 20.01 | 81.84 |
| no-contrastive | 18.68 | 54.15 | 26.70 | 37.39 | 21.58 | 82.93 |

### What `self-docs/current-status.md` reports (from the legacy codebase)

The legacy codebase reports **wildly different numbers**:

| Metric | HyperVul (legacy claim) | HyperVul (fair eval actual) |
|---|---|---|
| Precision | 37.50 | 17.35 |
| Recall | 40.49 | 70.24 |
| F1 | 37.60 | 27.62 |
| PR-AUC | 36.94 | 20.42 |
| ROC-AUC | 87.62 | 82.95 |

These are **not the same model evaluated differently**. The legacy codebase's reported numbers (Precision 37.50, Recall 40.49) appear to come from a different training configuration that is not reproducible from the code. The fair eval numbers (Precision 17.35, Recall 70.24) come from a model trained with only 20 epochs and default ASL loss. Neither matches the demo tables in `IMPLEMENTATION_PLAN.md` which show HyperVul-Full at F1=78.2%.

### What `self-docs/results.md` claims

This file contains tables with numbers that **do not appear anywhere in the actual code output**:
- HyperVul precision 51.80, recall 85.00, F1 64.34 (Table 1)
- HyperVul localization top-1 hit 82.50% (Table 2)
- These numbers are presented as measured results but are labeled as "demo placeholders" in the implementation plan

---

## 3. Why Each Divergent Version Failed

### Failure Analysis: Legacy Codebase (Codebase A)

**Problem 1: Inconsistent model definitions across files**

Three different files define `HyperedgeClassifier`:
1. `model/latest1/model.py` (line 106): Full version with localization head, SequenceAwarePooling, loc_gate
2. `model/latest1/run_unit_comparison.py` (line 122): Stripped version, SequenceAwarePooling only, no localization
3. `model/latest1/run_baselines.py` (line 40): Another stripped version, plain AttentionPooling, no localization

Similarly, `AttentionPooling` is defined in:
1. `model/latest1/model.py` (line 14)
2. `model/latest1/run_baselines.py` (line 24)
3. `src/models/ops.py` (line 8) as `SegmentAttentionPool`

And `AsymmetricLoss` is defined in:
1. `model/latest1/train.py` (line 74)
2. `model/latest1/run_representation_comparison.py` (line 39)
3. `model/latest1/run_unit_comparison.py` (line 53)

Each copy has identical logic but the mere fact of duplication means any bug fix or improvement must be applied in 3+ places. The codebase evolved by copy-pasting and modifying, creating an inconsistency surface.

**Problem 2: The G-HAN family is unused**

`model/latest1/ghan.py` defines 260 lines of carefully designed graph neural network components (EdgeGatedLayer, APPNP, GatedResidualGHAN, MoEHead, PooledContractGraphModel, PooledMoEModel). These are imported nowhere in the training pipeline. The `PooledContractGraphModel` at line 208 imports from `model.model` (note: no `latest1`), suggesting it was written for an earlier project structure and never integrated.

**Problem 3: Hardcoded paths and manual data wiring**

`train.py` (line 16): `PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")` - hardcoded absolute path.
`train.py` (line 237-244): Hardcoded paths to 6 separate data files:
```
results_dir / "eval_clean_negatives_oz_features.json"
results_dir / "eval_clean_negatives_external.json"
results_dir / "eval_clean_negatives_aave_split.json"
results_dir / "eval_clean_negatives_liquity.json"
```
`scratch/latest1/oz_split_mapping.json` (line 271) - path to scratch directory for split mapping.

The data pipeline requires manual file generation in a specific order, with no automated orchestration.

**Problem 4: The comparison experiments are not truly controlled**

`run_baselines.py` trains {Func,Callee} and {Func,State} ablations with an 8-config hyperparameter grid search (line 239-243: lr in [1e-3, 5e-4], dropout in [0.2, 0.3], hidden_dim in [128, 256]). But "Ours" (the HyperVul row in the output report at line 788) is hardcoded as a prior result:
```python
"| **Interaction-Level (Ours)** | 93.18% | 43.62% | 59.42% | 75.93% | 61.88% | 85.00% | 52.17% | 63.64% |"
```
This is not a re-trained model; it's a stitched row from a previous iteration. The baselines are trained fresh with grid search, but "Ours" is stale. The `run_unit_comparison.py` file (line 14) explicitly acknowledges this:
```
This replaces the invalid comparison in run_baselines.py, where "Ours" was a
stale/stitched row from older iterations and the ablations were trained on
different data with an 8-config grid search.
```

**Problem 5: Loss function inconsistency**

`run_baselines.py` uses `nn.BCEWithLogitsLoss` (line 279, 442, 608).
`train.py` uses `AsymmetricLoss` by default (line 362).
`run_unit_comparison.py` uses `AsymmetricLoss` (line 247).
`run_representation_comparison.py` uses `AsymmetricLoss` (line 214).

The baselines are disadvantaged because they use a simpler loss function while HyperVul uses a focal-like asymmetric loss. This is not a fair comparison.

### Failure Analysis: Fair Eval Codebase (Codebase B)

**Problem 1: Epoch count too low for meaningful training**

The `run_full_evaluation.py` defaults to `--epochs 20` (line 31). The strong baseline sweep supports `--max-epochs 200` but the default evaluation pipeline uses 20. With 20 epochs, complex models like HyperVul (which has a BiGRU + attention + localization head + SCL pre-training) cannot converge. The reported F1 of 27.62 for HyperVul-Full is likely an underfit result.

**Problem 2: The `security` and `full` variants are identical**

From `final_report.md` (line 69):
```
`security` and `full` in RQ3 both use the canonical 8-d security context available in `data/contract_graphs`.
```

This means the RQ3 ablation table is meaningless for the security vs full comparison because the code path is identical. The `symbolic_mode` parameter exists but the underlying data only provides 8-d security context vectors, so the "full" symbolic features are not actually available through the fair eval pipeline.

**Problem 3: PR-AUC is lower than baselines**

HyperVul-Full achieves PR-AUC 20.42, which is **lower** than function-mlp (31.38), function-features-mlp (33.43), callgraph-gcn (27.83), and pairwise-gat (29.19). The model with the most sophisticated representation is performing worse than a simple function embedding MLP on the ranking metric.

**Problem 4: No localization evaluation in fair eval**

The fair eval codebase implements `TupleLocalizationHead` in `hypervul.py` but the evaluation scripts (`rq3_run_hypervul_ablation.py`) never evaluate localization quality. The legacy codebase's `model.py` has `flag_tuples()` for inference-time localization, but the fair eval has no equivalent evaluation. The localization claim (Table 2 in `self-docs/results.md`) has no backing code in the fair eval.

**Problem 5: Clean-negative FPR evaluation is missing**

The fair eval `run_full_evaluation.py` does not evaluate FPR on OOD clean-negative corpora (OZ-Holdout, MakerDAO, Bancor, Liquity). This is explicitly noted as missing in `final_report.md` (line 70). The legacy `train.py` does evaluate FPR on these holdouts but the fair eval doesn't. The entire motivation for the project (reducing false positives on clean code) is not validated in the "fair" evaluation.

**Problem 6: Import boundary violation risk**

The `check_import_boundaries.py` script exists to verify RQ1 scripts don't import the hyperedge builder. However, the fair eval's `rq1_run_generic_baselines.py` shares the same data loading infrastructure as the RQ2/RQ3 runners. The boundary is enforced by convention (a script), not by the module system.

### Failure Analysis: The Overall System

**Problem 1: No end-to-end pipeline**

There is no single script that takes raw Solidity contracts and produces a trained HyperVul model. The data pipeline requires:
1. AST parsing with `negative_hyperedge_sampling.py` (tree-sitter-solidity)
2. Contract graph construction with `build_contract_graphs.py`
3. SmartBERT embedding extraction with `extract_features.py`
4. Symbolic feature generation with `build_security_features.py`
5. Security context generation with `build_security_context.py`
6. Split assignment (project-disjoint)
7. Clean negative construction from 4 external repos

Each step produces intermediate files that must be in the correct location. The `run_all.sh` master script skips steps 1-6 entirely and assumes pre-processed data exists.

**Problem 2: Three separate reporting systems**

1. `model/latest1/train.py` writes `iteration3_results*.md` with hardcoded markdown tables
2. `hypervul_fair_eval/scripts/make_final_report.py` writes `final_report.md` and `final_report.json`
3. `scripts/latest1/generate_final_paper_tables.py` writes `final-evaluation-results.md`

These three systems produce different tables with different numbers because they evaluate different model configurations.

**Problem 3: The demo data problem**

`self-docs/results.md` and `IMPLEMENTATION_PLAN.md` tables 1-6 contain numbers that are explicitly labeled as "demo placeholders" but are presented in the same format as real results. The actual code output (`final_report.md`) shows drastically different numbers. Anyone reading the project documentation would form incorrect expectations about system performance.

**Problem 4: No statistical rigor in legacy results**

The legacy `run_representation_comparison.py` implements bootstrap CIs and McNemar tests (lines 250-263), but the other legacy scripts (`train.py`, `run_baselines.py`) produce single-seed results with no confidence intervals. The fair eval uses 5 seeds with mean +/- std, which is better but still lacks bootstrap CIs for F1/F2 and paired significance tests.

---

## 4. Root Cause: Why Performance Is Poor

### 4.1 Extreme class imbalance (2% positive rate)

The dataset has 10,740 training interactions with only 215 positives (2.00%). This is stated in the code at multiple locations:
- `train.py` line 349: `pos_upweight = neg_count / pos_count`
- `final_report.md` line 11: `Pos Rate: 2.00%`

The model is essentially learning to predict "not vulnerable" for everything. With threshold tuning at 95% recall, the model achieves recall ~70% but precision ~17% because there are simply too few positives to learn meaningful patterns.

### 4.2 Inadequate embedding strategy

All models use SmartBERT-v3 embeddings (768-dim) as frozen features. The embedding was trained for code similarity, not vulnerability detection. The LoRA adapter defined in `model.py` (line 88-98) is never used in any training script. The embeddings are never fine-tuned.

### 4.3 The localization head degrades classification

The `LocalizationHead` adds a factorized additive interaction term to the logits (line 146 in `model.py`): `logits = logits + self.loc_gate * loc_logit`. The `loc_gate` is initialized to 1.0 (line 130). This means the localization head's output is fully active from the start, adding noise to the classification signal. The model must simultaneously learn to classify AND learn which tuples are important, with no tuple-level supervision.

### 4.4 Contract-level context is lost

The HyperVul model classifies each interaction independently. It does not see other interactions in the same contract. The sequence-aware pooling within a hyperedge captures function-state-callee relationships for one interaction but misses the contract-level pattern: "this function interacts with these other functions that also touch shared state." The G-HAN components in `ghan.py` were designed to solve this but were never integrated.

### 4.5 The clean negative strategy is unstable

The training data mixes base codebase negatives with OZ (100) and Aave (0-225) clean negatives. The K_app sweep (lines 322-491 in `train.py`) tries different numbers of Aave negatives, but:
- The OZ train subset is sampled randomly with `random.sample(sorted_oz_train, 100)` (line 305) - only reproducible if seed is set
- The Aave subset is similarly randomly sampled (line 336)
- The sweep selects "best" based on combined validation FPR, not on test performance
- With only 215 positives, adding 100+ clean negatives changes the class distribution significantly

### 4.6 Threshold calibration is the dominant factor

All models are evaluated at a validation-selected threshold (highest achieving >=95% recall). The actual model outputs (logits) may be poorly calibrated. The PR-AUC (threshold-free) tells the real story:
- HyperVul-Full PR-AUC: 20.42
- Function-MLP PR-AUC: 31.38
- The threshold-free ranking metric shows HyperVul is WORSE than the simplest baseline

This means the model's raw probability outputs are less informative than a function embedding MLP. The threshold tuning is compensating for poor ranking by lowering the decision boundary.

---

## 5. How to Start from Scratch: A Complete Pipeline

### Phase 1: Data Collection and Labeling

**Step 1.1: Curate a larger, higher-quality dataset**

Current dataset: 1919 contracts, ~12K interactions, 294 positives. This is too small for any neural approach to learn generalizable patterns.

Actions:
- Expand to include ALL known vulnerable contracts from DAppSCAN, FORGE, SWC Registry, and Rekt.news
- Target: 500+ vulnerable contracts, 2000+ vulnerable interactions
- Ensure vulnerability type diversity: reentrancy, front-running, unchecked calls, access control, integer overflow, flash loan attacks
- Each vulnerability must have: source code, vulnerability location (function + state vars + callees), vulnerability type, root cause description

**Step 1.2: Label at the interaction level, not contract level**

Current labeling: contract-level vulnerable/clean, propagated to interactions via heuristic. This creates label noise because a contract may have 10 functions but only 1 is vulnerable.

Actions:
- Label each (function, state_var, external_call) tuple as vulnerable or clean
- Annotate the vulnerability type (SWC ID or custom taxonomy)
- Annotate the root cause category: missing guard, state inconsistency, call order dependency, etc.
- Use dual annotator protocol with inter-annotator agreement measurement (target: Cohen's kappa >= 0.8)
- Resolve disagreements through discussion or expert adjudication

**Step 1.3: Build a high-quality clean-negative corpus**

Current clean negatives: OpenZeppelin (library code, very different distribution from application code), Aave (application but DeFi-specific), MakerDAO/Bancor/Liquity (OOD holdouts).

Actions:
- Collect clean contracts from diverse domains: DeFi, NFT, DAO, GameFi, infrastructure
- Ensure clean contracts have similar structural complexity to vulnerable ones (same number of functions, state variables, external calls)
- Target: 5000+ clean interactions from 500+ contracts
- Split: 70% train, 15% val, 15% test (project-disjoint)

**Step 1.4: Establish proper train/val/test splits**

Current split: project-disjoint with 1614/167/138 contracts. The val set has only 38 positives (4.50%), the test set has 41 positives (5.30%).

Actions:
- Stratified project-disjoint split ensuring each split has >=100 positives
- No data leakage: verify no contract appears in multiple splits
- No near-duplicate leakage: verify no two contracts in different splits share >80% code similarity
- Document split statistics: contract count, interaction count, positive rate, source distribution, vulnerability type distribution

### Phase 2: Feature Engineering

**Step 2.1: Code embeddings**

Current: SmartBERT-v3 (768-dim) frozen embeddings. The LoRA adapter is defined but never used.

Actions:
- Use SmartBERT-v3 as the base encoder (it's pre-trained on Solidity code, which is good)
- Fine-tune with LoRA (rank 8, alpha 16) during training, not frozen
- The fine-tuning objective should be vulnerability-aware: use contrastive learning where positive pairs are (vulnerable interaction, its ground-truth cause) and negative pairs are (vulnerable interaction, random clean interaction)
- Alternatively: train a task-specific encoder from scratch on the vulnerability detection task if SmartBERT fine-tuning is too unstable

**Step 2.2: Structural features (the hyperedge)**

Current: Hyperedge = {function_embedding, state_var_embeddings, callee_embeddings}. Members are raw SmartBERT embeddings concatenated.

Actions:
- For each interaction, extract: function source code, state variable declarations, external call expressions
- Encode each member independently (fine-tuned SmartBERT or task-specific encoder)
- Add typed position encoding: function=0, state_var=1..S, callee=1..C
- Add structural features: call depth, state access pattern (read/write/read-write), call target type (interface/contract/library/address)
- The hyperedge representation should be: [function_emb; type_emb(0)] + [state_emb_i; type_emb(1); state_features_i] + [callee_emb_j; type_emb(2); callee_features_j]

**Step 2.3: Symbolic/security features**

Current: 35-dim one-hot vectors in `src/models/symbolic.py`. The fair eval only has 8-dim security context from `data/contract_graphs`.

Actions:
- Expand to include: function visibility, mutability, nonReentrant, payable, state variable type, state mutability (immutable/constant/transient), external call type (low-level/high-level), return value checked, gas limit specified
- Make these features available in the data pipeline, not as a separate sidecar
- Ensure the fair eval codebase can access the full symbolic features

### Phase 3: Model Architecture

**Step 3.1: The HyperVul interaction encoder**

Current: `HyperedgeClassifier` in `model/latest1/model.py` uses SequenceAwarePooling (BiLSTM) + attention pooling + MLP head. This is a weak encoder that treats the hyperedge as a sequence without structural inductive bias.

Proposed architecture:

```
Input: Hyperedge = {function, state_1..state_S, callee_1..callee_C}
Each member: [SmartBERT_emb(768) || structural_features(F) || type_embedding(T)]

1. Member Encoding:
   - Linear projection: 768+F+T -> hidden_dim (e.g., 256)
   - Optional: per-member MLP for non-linear feature interaction

2. Hyperedge Aggregation (the key architectural choice):
   Option A: Attention pooling (current approach, weak)
   Option B: Set Transformer (Lee et al. 2019) with ISAB for permutation-equivariant encoding
   Option C: Deep Sets (Zaheer et al. 2017) with sum pooling + per-element MLP
   Option D: Hypergraph neural network (current HypergraphNN approach, node-to-edge message passing)

   Recommendation: Use Set Transformer with ISAB for the interaction encoder.
   Rationale: The hyperedge has 1-10 members. ISAB with 4 inducing points captures
   pairwise interactions without O(n^2) cost. It's permutation-equivariant by design,
   which is correct because member order is arbitrary.

3. Classification Head:
   - 2-layer MLP: hidden_dim -> hidden_dim/2 -> 1
   - No localization head during initial training (add later with frozen encoder)

4. Loss:
   - AsymmetricLoss (gamma_neg=4, gamma_pos=1, clip=0.05) with pos_weight = neg/pos
   - No SCL pre-training initially (simplify first, add complexity later)
```

**Step 3.2: The contract-level context model (G-HAN integration)**

Current: `ghan.py` defines the G-HAN family but it's never integrated. The interaction encoder classifies each interaction independently.

Proposed: Two-stage architecture

```
Stage 1: Per-interaction encoding (as above)
   - Each interaction gets a pooled embedding from the Set Transformer

Stage 2: Contract-level message passing
   - Build a contract graph where nodes are interactions
   - Edge types: shared_state, shared_callee, call_order (function A calls function B)
   - Use the existing GatedResidualLayer from ghan.py
   - Gate initialization: sigmoid(-5) ~ 0.007, so propagation starts near-zero
   - The model learns to open the gate if contract-level context helps

Stage 3: Per-interaction classification
   - MLP on the refined interaction embedding
   - The contract-level context informs each interaction's prediction
```

This preserves the hyperedge representation (Stage 1) while adding contract-level context (Stage 2). The G-HAN components already exist in `ghan.py` and just need integration.

**Step 3.3: Remove the localization head initially**

The `LocalizationHead` adds complexity without clear benefit and may hurt classification. Train the classifier first, then add localization as a post-hoc analysis tool with frozen encoder.

### Phase 4: Training Pipeline

**Step 4.1: Single, unified training script**

Current: 6 different training scripts (`train.py`, `run_representation_comparison.py`, `run_unit_comparison.py`, `run_baselines.py`, plus 3 fair eval runners). Each duplicates data loading, loss computation, and evaluation.

Proposed: One training script with configuration-driven experiments:

```python
# train.py
config = {
    "model": "hypervul",  # or "function_mlp", "set_pool", "pairwise_gcn", etc.
    "data": {"train": "...", "val": "...", "test": "..."},
    "loss": "asl",  # or "bce"
    "optimizer": "adam",
    "lr": 1e-3,
    "epochs": 200,
    "patience": 20,
    "threshold_policy": "max_f2",
    "seeds": [42, 43, 44, 45, 46],
}
```

All models share the same training loop, data loading, and evaluation code. Only the model architecture differs.

**Step 4.2: Proper evaluation protocol**

Current: Threshold tuning on validation set to achieve >=95% recall. This is fragile because:
- The validation set has only 38 positives
- The threshold search grid has 10001 points
- Small changes in validation performance cause large threshold changes

Proposed:
- Use 5-fold cross-validation on the training+validation data for threshold selection
- Report threshold-free metrics (PR-AUC, ROC-AUC) as primary
- Report threshold-dependent metrics (F1, F2, precision, recall) at multiple operating points
- Always report 95% bootstrap confidence intervals (1000 bootstrap samples)
- Use paired McNemar test for model comparisons on the same test set

**Step 4.3: Clean negative handling**

Current: Randomly sample 100 OZ + variable Aave clean negatives. The sampling is seed-dependent and the Aave count is a hyperparameter.

Proposed:
- Fixed clean negative budget: 20% of training negatives are clean, 80% are from the base codebase
- The clean negative set is stratified by domain (library vs application)
- No K_app sweep - fix the ratio and report sensitivity analysis separately
- Evaluate FPR on OOD clean-negative corpora as a first-class metric, not an afterthought

### Phase 5: Baseline Comparison

**Step 5.1: Fair baseline definitions**

Current: The baselines are inconsistently defined:
- Some use BCEWithLogitsLoss, others use AsymmetricLoss
- Some have grid search, others use fixed hyperparameters
- The "Ours" row in `run_baselines.py` is a hardcoded prior result

Proposed: All baselines share:
- Same training loop
- Same loss function (AsymmetricLoss with same pos_weight)
- Same threshold selection protocol
- Same hyperparameter budget (each gets 20 random hyperparameter configurations, not a full grid)
- Same data (no clean negatives for baselines that don't use them, or same clean negatives for all)

**Step 5.2: The 6 baselines (from RQ1)**

1. **Function-MLP**: Function embedding (768) -> MLP (256) -> 1. Simplest possible.
2. **Function+Features MLP**: Function embedding (768) + scalar features (10) -> MLP (256) -> 1. Tests metadata gain.
3. **Sequence-BiGRU**: All function embeddings in a contract -> BiGRU -> per-function classification. Tests sequential context.
4. **CallGraph-GCN**: Function nodes + call edges -> GCN (2 layers) -> per-node classification. Tests graph structure.
5. **Pairwise-RGCN**: Function/state/callee nodes + typed edges -> R-GCN (2 layers) -> per-node classification. Tests relational structure.
6. **Pairwise-GAT**: Same as R-GCN but with attention. Tests attention over structure.

**Step 5.3: The representation ablation (RQ2)**

Given the same candidate interactions:
1. **Set-pool**: Mean pooling over members -> MLP. No structure.
2. **Pairwise-GCN**: Clique expansion -> GCN. Binary graph reduction.
3. **Pairwise-GAT**: Clique expansion -> GAT. Binary graph reduction with attention.
4. **HypergraphNN**: Node-to-edge message passing. True hyperedge representation.
5. **HyperVul (proposed)**: Set Transformer + contract-level G-HAN. Full architecture.

### Phase 6: The Absolute Hyper Structure for Performance

Based on the analysis of what exists and what's missing, the optimal architecture for this problem is:

```
HyperVul-v2 Architecture:

Input: Solidity smart contract

Pipeline:
1. Parse AST (tree-sitter-solidity) -> extract functions, state variables, external calls
2. Encode each entity with fine-tuned SmartBERT-v3 -> 768-dim vectors
3. For each labeled interaction (function + state vars + callees):
   a. Construct typed hyperedge with structural features
   b. Encode hyperedge with Set Transformer (ISAB, 4 inducing points, 2 layers)
   c. Produce interaction embedding (256-dim)

4. Build contract-level graph:
   - Nodes: all interactions in the contract
   - Edges: shared_state, shared_callee, call_order
   - 2-layer GatedResidualGHAN (from existing ghan.py)

5. Per-interaction classifier:
   - MLP: 256 -> 128 -> 1
   - AsymmetricLoss (gamma_neg=4, gamma_pos=1)
   - pos_weight = #neg / #pos

6. Threshold selection:
   - 5-fold CV on training+validation for threshold calibration
   - Report at multiple operating points (recall=90%, 95%, 99%)

7. Localization (post-hoc):
   - Freeze encoder and classifier
   - Train a lightweight TupleLocalizationHead on top
   - Evaluate localization quality separately
```

**Key differences from current implementation:**
1. Fine-tuned encoder (not frozen)
2. Set Transformer (not simple attention pooling)
3. Contract-level G-HAN (not independent classification)
4. Unified training loop (not 6 separate scripts)
5. Proper evaluation protocol (not single-threshold)
6. Larger dataset (not 294 positives)

---

## 6. Summary of Issues

| # | Issue | Severity | Location |
|---|---|---|---|
| 1 | Three divergent codebases never converge | Critical | `model/`, `src/`, `hypervul_fair_eval/` |
| 2 | Model definitions duplicated 3+ times with silent differences | Critical | `model.py`, `run_unit_comparison.py`, `run_baselines.py` |
| 3 | AsymmetricLoss duplicated 3+ times | High | `train.py:74`, `run_representation_comparison.py:39`, `run_unit_comparison.py:53` |
| 4 | G-HAN family defined but never integrated | High | `ghan.py` (260 lines, 0 imports) |
| 5 | "Ours" row in baseline report is hardcoded from prior run | Critical | `run_baselines.py:788` |
| 6 | Fair eval runs only 20 epochs (insufficient convergence) | High | `run_full_evaluation.py:31` |
| 7 | RQ3 security vs full ablation is identical (dead code path) | High | `final_report.md:69` |
| 8 | HyperVul PR-AUC lower than Function-MLP (20.42 vs 31.38) | Critical | `final_report.md:21-27` |
| 9 | Clean-negative FPR not evaluated in fair eval | High | `final_report.md:70` |
| 10 | Localization never evaluated in fair eval | Medium | No localization eval code |
| 11 | Demo placeholder numbers presented as real results | High | `self-docs/results.md`, `IMPLEMENTATION_PLAN.md` tables |
| 12 | Hardcoded absolute paths in training scripts | Medium | `train.py:16` |
| 13 | No end-to-end data pipeline | High | No single script from raw data to trained model |
| 14 | Loss function mismatch between baselines and HyperVul | High | `run_baselines.py` uses BCE, others use ASL |
| 15 | 294 positives too few for neural approach | Critical | Dataset size |
| 16 | Frozen embeddings never fine-tuned | High | LoRA defined but unused |
| 17 | Three separate reporting systems produce different numbers | Medium | `train.py`, `make_final_report.py`, `generate_final_paper_tables.py` |
| 18 | Contract-level context lost (interactions classified independently) | High | `model.py` architecture |
| 19 | Threshold tuning compensates for poor ranking (PR-AUC low) | High | Evaluation protocol |
| 20 | Validation set too small (38 positives) for reliable threshold selection | Medium | Dataset split |

---

## 7. Recommended Next Steps (Priority Order)

1. **Consolidate to one codebase**: Delete the legacy `model/`, `src/`, `scripts/` directories. Keep `hypervul_fair_eval/` as the single codebase. Migrate any unique components (G-HAN from `ghan.py`, LocalizationHead from `ops.py`) into it.

2. **Fix the dataset**: Expand positives to 500+ interactions. Proper interaction-level labeling with dual annotators. Ensure >=100 positives in test set.

3. **Simplify the model**: Start with Function-MLP + Set-pool + HyperedgeNN only. Get these three working correctly before adding complexity.

4. **Fix the training**: Single training script, 200+ epochs, early stopping, consistent loss function across all models.

5. **Fix the evaluation**: Threshold-free metrics as primary (PR-AUC, ROC-AUC). Bootstrap CIs. Paired significance tests. FPR on OOD clean-negative corpora.

6. **Add contract-level context**: Integrate G-HAN for inter-interaction message passing within contracts.

7. **Fine-tune embeddings**: Add LoRA fine-tuning for SmartBERT-v3 during training.

8. **Remove all demo/placeholder numbers**: Every number in documentation must come from actual code output.

---

*End of report.*
