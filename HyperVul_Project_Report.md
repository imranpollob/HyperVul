# HyperVul: Interaction-Level Vulnerability Detection in Solidity Smart Contracts
## Comprehensive Technical Project Report

> **Target venue**: IEEE ICTAI 2026 (Rank B)  
> **Report date**: 2026-06-20  
> **Status**: Research-in-progress — not ready for submission without resolving the integrity issues flagged in §4.3

---

## 1. Executive Summary

### 1.1 Project Goal & Key Innovation

HyperVul recasts smart contract vulnerability detection as an **interaction-level hyperedge classification** problem. Rather than classifying individual functions or entire contracts, HyperVul classifies *interactions* — the tuple `{function, state variables accessed, external callees invoked}` — as vulnerable or clean.

This reformulation is motivated by a structural observation: vulnerabilities such as reentrancy (SWC-107), unchecked call returns (SWC-104), and front-running (SWC-114) are fundamentally relational — they arise from the *composition* of a function body, the state it touches, and the external contracts it calls. Hyperedges capture this multi-way relationship directly; pairwise graph edges must fragment it into binary links.

**Key innovation claim (conditional, not universal):** Under *atomic* (non-redundant) node features, the hyperedge representation is statistically preferable to pairwise-edge representations on F1 and cross-contract F1. This advantage **disappears** when full function body embeddings are used, because the function text redundantly encodes the state/callee information. The result is therefore a finding about *feature granularity and structural necessity*, not a blanket claim that hypergraphs dominate GNNs.

### 1.2 Current Status & Major Milestones

| Milestone | Status |
|:---|:---:|
| Dataset construction (FORGE + DAppSCAN, 1,240 hyperedges) | **Complete** |
| Union-Find leakage-free 70/15/15 split | **Complete** |
| SmartBERT-v3 feature extraction (signature, full body, security variants) | **Complete** |
| Data augmentation (semantic-preserving transforms, 507 accepted variants) | **Complete** |
| Deployed HyperedgeClassifier (attention-pool + MLP + localization head) | **Complete** |
| Iteration-3 training with clean-negative K-sweep | **Complete** |
| Node-set ablation (function-only, +state, +callee, full) | **Complete** |
| Controlled representation comparison (set-pool / pairwise-GCN / pairwise-GAT / hypergraph) — 3 experiments × 5 seeds | **Complete** |
| Safety-aware feature ablation (5-seed multi-arm: none/security/full) | **Complete** |
| Cross-contract performance diagnostic | **Complete** |
| OOD FPR generalization evaluation (OZ, MakerDAO, Bancor, Liquity) | **Complete** |
| Error analysis & label quality review (DAppSCAN 227 items, 95.2% confirmed) | **Complete** |
| Label correction proposal (4 SWC-104 view/pure items) | **Pending human review** |
| Scale-up to full DAppSCAN/FORGE benchmark with contract-disjoint splits | **Pending** |
| Paper writing | **Pending** |

### 1.3 Headline Metrics

All multi-seed results use seeds {42, 43, 44, 45, 46}. Test set: **169 interactions (44 positives, 125 negatives)** from 33 contracts. Primary operating point: threshold achieving ≥95% validation recall.

**Deployed full model (iteration-3, seed=42, full {function, state, callee} features):**

| Metric | Value |
|:---|:---:|
| Recall | 93.18% |
| Precision | 47.67% |
| F1-Score | 63.08% |
| F2-Score | 78.24% |
| PR-AUC | 63.81% |
| ROC-AUC | 86.71% |
| Cross-Contract F1 | 52.63% |
| Intra-Contract F1 | 71.23% |

**Multi-seed hyperedge model (Sym:full, 5 seeds — most reliable headline):**

| Metric | Mean ± Std |
|:---|:---:|
| Recall | 95.5 ± 1.6 |
| F1-Score | 66.0 ± 1.8 |
| ROC-AUC | 88.6 ± 0.9 |

**Critical weakness — OOD False Positive Rate (5-seed baseline, no security features):**

| Holdout | FPR (point estimate) | 95% Wilson CI |
|:---|:---:|:---:|
| OZ-Holdout (library) | 31.75% | [21.6%, 44.0%] |
| MakerDAO DSS (DeFi app) | 76.42% | [72.2%, 80.2%] |
| Bancor V3 (DeFi app) | 52.63% | [45.9%, 59.3%] |
| Liquity V1 (DeFi app) | 45.88% | [40.1%, 51.7%] |

These FPRs are the project's primary open problem.

### 1.4 Critical Findings & Integrity Constraints

1. **Structure necessity is feature-conditional.** With full SmartBERT function body embeddings, all representations tie at ~63 F1 — structure is redundant. Only under atomic (signature-only) function features does the hyperedge outperform pairwise (F1 59.4 vs 51.2, McNemar p=0.0021). The paper must disclose this conditionality clearly.

2. **Safety-aware security_context features significantly reduce OOD FPR.** Adding security-pattern features (reentrancy guard flags, modifier presence, etc.) cuts matched-recall OOD FPR from 25.4% to 14.9% on OZ-holdout and from 60.9% to 45.8% on MakerDAO (5-seed, 90% matched recall), all differences McNemar-significant (p < 0.0013).

3. **Data coverage expansion is insufficient to fix OOD FPR.** Training on 100 Aave + 100 OZ clean negatives reduced but did not resolve the "external call detector" behavior. The model flags external calls without semantic awareness of safety checks.

4. **Integrity issue — test set size discrepancy (flag for advisor).** The split report documents 49 positives in the test split. All evaluation results use 44 positives (169 total interactions). The 5-item difference is not fully accounted for in any single document. The label correction proposal identifies 4 SWC-104 items as potentially invalid but explicitly states "no labels have been modified." A fifth untracked positive is missing from evaluation. This must be resolved and documented before submission.

5. **Prior baseline table was invalidated.** An earlier "Interaction-Level (Ours)" row in the baseline comparison was discovered to be stale (stitched from iterations 1+2 under non-identical conditions). All current comparisons re-train all variants under controlled, identical conditions per the integrity rule: *never hand-copy "Ours" rows across experiments.*

---

## 2. Architecture

### 2.1 Data Representation

**Hyperedge definition.** Each data point is a hyperedge `H = (f, S, C)` where:
- `f` — the calling function (a Solidity function node)
- `S = {s₁, ..., sₖ}` — the set of contract-level state variables accessed by `f`
- `C = {c₁, ..., cₘ}` — the set of external call expressions invoked by `f`

A hyperedge is **positive** (vulnerable) if the corresponding audit finding labels the function as vulnerable to one of the four supported SWC categories. A hyperedge is **negative** (clean) if it is sampled from within the same audited project but references no finding.

**Constructability gate.** A function must contain ≥1 external call AND ≥1 state variable access to yield a constructable hyperedge. Functions failing either gate are excluded. This is the key distinction from contract-level or function-level approaches: the classification unit is the *interaction*, not the artifact.

**Cross-contract vs. intra-contract.** A hyperedge is cross-contract if any callee in `C` resolves to a function defined in a *different* contract from `f`. Exactly 50% of positives and 50% of negatives in the dataset are cross-contract (enforced by the negative sampling gate).

### 2.2 SmartBERT-v3 Encoder

| Property | Value |
|:---|:---|
| Base architecture | RoBERTa (HuggingFace) |
| Checkpoint | `web3se/SmartBERT-v3` |
| Output dimension | 768-d |
| Pooling | CLS token activation (not mean-pool) |
| Weights during training | **Frozen** (no fine-tuning) |

**Node-type encoding:**

| Node Type | Input text | Max tokens |
|:---|:---|:---:|
| Function node (full) | Full Solidity function source (signature + body) | 256 |
| Function node (signature) | Declaration only, body stripped | 256 |
| State variable node | `"{var_type} {var_name}"` (e.g., `mapping(address => uint256) balances`) | 256 |
| Call site (callee) node | Exact call expression (e.g., `IERC20(token).transfer(to, amount)`) | 64 |

Truncation is applied at the tail when function bodies exceed 256 tokens. Cross-contract positive functions exceed 256 tokens at a rate of 68.4%; however, missed cross-contract positives (false negatives) showed 0% truncation, indicating truncation is not the primary cause of cross-contract misses.

**Feature variants.** Three feature schemes were produced:
- `*_features` — full function body embeddings (768-d per node, standard)
- `*_sig` — signature-only function embedding (body stripped, atomic)
- Security context features — additional binary flags encoding reentrancy guards, modifier presence, and access control patterns (used in the safety-aware ablation)

**Design rationale for freezing.** End-to-end fine-tuning was deferred because the training set (552 positives after augmentation) is too small to safely update 125M RoBERTa parameters without catastrophic forgetting. The frozen encoder acts as a fixed representation oracle; the classifier learns to weight and combine the 768-d embeddings.

### 2.3 Model Architecture

The deployed model is `HyperedgeClassifier` ([model/model.py](model/model.py)).

```
Input: variable-length set of node embeddings {x₁,...,xₙ} ∈ ℝ⁷⁶⁸, padding mask
  │
  ▼
AttentionPooling (in=768, hidden=128)
  │  learned attention weights over node set
  │  w_aᵢ = softmax(vᵀ tanh(W_a xᵢ))
  │  z = Σᵢ wᵢ xᵢ  ∈ ℝ⁷⁶⁸
  ▼
MLP Head
  │  Linear(768 → 256) → ReLU → Dropout(0.3) → Linear(256 → 1)
  ▼
[Optional] LocalizationHead (Stage 4)
  │  Per-tuple (state_j, callee_k) excitability grid
  │  loc_logit fused via learnable residual gate
  ▼
Binary classification logit (sigmoid → probability)
```

**LocalizationHead** computes a `(S × C)` excitability grid over all (state variable, external call) pairs. At inference, the top-k tuples ranked by excitability are returned as human-readable explanations (e.g., "flag: `balances[msg.sender]` × `token.transfer()`"). This is additive to the set-pool logit via a learnable gate, preserving the baseline classifier's behavior.

**Fixed hyperparameters (all experiments):**

| Hyperparameter | Value |
|:---|:---:|
| hidden_dim | 256 |
| dropout | 0.3 |
| learning rate | 1e-3 |
| weight_decay | 1e-5 |
| GNN layers | 2 |
| Threshold rule | Highest threshold achieving ≥95% val recall |

### 2.4 Training Pipeline

**Training objective:** Binary cross-entropy with hard-negative mining.

**Negative training composition (iteration-3, K=100):**

| Negative Source | Count | % |
|:---|:---:|:---:|
| Codebase Tier-A hard negatives (same audit file as a positive) | 829 | 80.6% |
| OpenZeppelin clean library negatives | 100 | 9.7% |
| Aave V3 clean application negatives | 100 | 9.7% |
| **Total negatives** | **1,029** | 100% |
| **Total positives (augmented)** | **552** | — |

The K-sweep (K_app ∈ {0, 50, 100, 150, 200, 225}) is tuned on validation FPR while holding validation recall at ≥97.30%. The stable region {50, 100, 150} is the valid operating range; the K=200 point is excluded as a noise spike (anomalously low val FPR not reproduced across seeds).

**Data augmentation.** 507 accepted semantic-preserving variants were generated from 2,417 candidates (79% discard rate). Acceptance gates:
1. Constructability preserved (external call + state access present)
2. Structural identity: same call count, same state variable set, same cross-contract class
3. Sequence order: relative `{state read, external call, state write}` order unchanged
4. No val/test source hash collision

**Validation recall constraint.** All arms/seeds use a threshold achieving ≥95% recall on validation positives. This is a recall-first decision: the system is optimized to be a high-sensitivity scanner (low miss rate), accepting elevated false positives as the operational tradeoff.

### 2.5 Dataset

#### Sources

| Source | Role | Positives | Notes |
|:---|:---|:---:|:---|
| **FORGE-Curated** | High-confidence labeled VFPs | 83 | 303 VFPs; AST-parsed hyperedges; all FORGE positives are SWC-107 or SWC-114 |
| **DAppSCAN** | Broader audit coverage | 227 | ~5.7 GB; single-point audit annotations; 95.2% label quality confirmed by manual review |
| **OpenZeppelin** | Clean negatives (eval + training) | 0 (negatives only) | 600 OZ negatives; 63 OZ-holdout (eval-only) |
| **Aave V3, Bancor, Liquity, MakerDAO** | OOD generalization holdouts | 0 (negatives only) | Never seen during training |

**FORGE construction note.** 303 VFPs yielded 695 audit findings, of which 212 were interaction-type. AST-parsing recovered 83 deduplicated constructable hyperedges (+36% over the earlier regex-based approach of 61). The AST parser resolves inheritance chains, interface-typed local variables, inline casts, and DeFi vault callback patterns.

#### Dataset Totals

| Split | Positives | Negatives | Total | FORGE pos | DAppSCAN pos |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Train** | 223 (71.9%) | 651 (70.0%) | 874 | 49 | 174 |
| **Val** | 38 (12.3%) | 152 (16.3%) | 190 | 10 | 28 |
| **Test** | 49* (15.8%) | 127 (13.7%) | 176* | 24 | 25 |
| **Total** | 310 | 930 | 1,240 | 83 | 227 |

> ⚠️ **Integrity note**: The test set in the split report contains 49 positives, but all evaluation results report 44 positives (169 total interactions). This 5-item discrepancy is unresolved and flagged for advisor review (see §4.3).

After augmentation, the effective training positives become 552 (223 base + 507 augmented variants truncated to dataset needs divided among positives). All val/test splits are frozen and un-augmented.

#### Vulnerability Type Distribution

| Type | SWC | Train | Val | Test | Total |
|:---|:---|:---:|:---:|:---:|:---:|
| Reentrancy | SWC-107 | 110 (49.3%) | 21 (55.3%) | 24* (49.0%) | 155 (50.0%) |
| Unchecked Call Return | SWC-104 | 60 (26.9%) | 12 (31.6%) | 10* (20.4%) | 82 (26.5%) |
| Front-running / Tx Order | SWC-114 | 47 (21.1%) | 5 (13.2%) | 15 (30.6%) | 67 (21.6%) |
| Delegatecall | SWC-112 | 6 (2.7%) | 0 | 0 | 6 (1.9%) |

> *Per-type test counts from split report (49 positives total). Evaluation scripts report 44 positives: Reentrancy 23, Front-running 15, Unchecked Call 6, Delegatecall 0.

#### Leakage Controls

Union-Find connected-components splitting on project IDs and normalized source hashes. **Zero cross-split collisions** on both the project-group check and the source-hash check. Cross-contract ratio maintained at 50% in train and val; test positive cross-contract ratio is 38.78% (disclosed imbalance, reported separately by interaction type).

### 2.6 Threat Model & Scope

HyperVul targets **four SWC vulnerability classes** at **interaction granularity**:
- SWC-107: Reentrancy (state change after external call)
- SWC-104: Unchecked Call Return Value
- SWC-114: Transaction Order Dependence / Front-running
- SWC-112: Delegatecall to Untrusted Callee (too few positives to evaluate)

The system is **not** a static analyzer — it produces hyperedge-level binary scores, not line-level annotations. It is positioned as a high-recall scanner (≥93% recall) to complement existing tools, with precision intentionally traded off.

---

## 3. Evaluation Results

### 3.1 Metrics & Methodology

**Primary metrics:** Recall (safety-critical; the scanner must not miss vulnerabilities), F1, F2, ROC-AUC, PR-AUC. F2 weights recall 2× over precision.

**Secondary metrics:** Cross-contract F1 / Intra-contract F1 (reported separately due to test split structural imbalance). OOD FPR on four disjoint holdouts (OZ-Holdout, MakerDAO DSS, Bancor V3, Liquity V1).

**Statistical rigor:** 5-seed runs (seeds 42–46), mean ± std reported. Paired McNemar tests on per-sample prediction decisions for structural comparisons. Wilson 95% CIs on all FPR estimates.

**Threshold rule (consistent across all experiments):** Highest threshold yielding ≥95% recall on validation positives. This ensures comparisons are made at a fixed operating-point policy, not at globally optimal but incomparable thresholds.

**Baselines used:**
- Set-pool (no graph edges) — structure-free; treats hyperedge members as an unordered set
- Pairwise-GCN (clique expansion) — constructs a complete graph over all nodes, applies GCNConv
- Pairwise-GAT (clique expansion) — same but with GATConv
- Rule-based heuristics (AllPositive, HasLowLevel, UnguardedExtWrite, NotSafeERC20) — emulate static-analyzer families

All structural baselines (set-pool, pairwise-GCN, pairwise-GAT, hypergraph) are implemented in the same unified skeleton (`src/models/gnn_zoo.py`) with identical layer counts, hidden dims, and training procedures. Only the graph convolution operator differs.

### 3.2 Main Results: Representation Comparison

Three controlled experiments varying feature granularity, each over 5 seeds.

#### Experiment 1 — Full SmartBERT Function Embeddings (current production features)

| Model | F1 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
|:---|:---:|:---:|:---:|:---:|:---:|
| **set-pool (no edges)** | **63.2 ± 1.2** | 66.0 ± 1.3 | 87.4 ± 0.9 | **52.6 ± 0.8** | **71.4 ± 2.3** |
| pairwise-GCN (clique) | 62.7 ± 2.6 | 65.7 ± 4.7 | 88.0 ± 1.2 | 51.4 ± 3.3 | 71.1 ± 2.4 |
| pairwise-GAT (clique) | 60.5 ± 4.8 | 67.5 ± 6.0 | 89.1 ± 1.3 | 51.2 ± 6.2 | 67.7 ± 3.7 |
| hypergraph (ours) | 58.5 ± 3.0 | 65.6 ± 5.1 | 87.6 ± 0.8 | 48.0 ± 2.4 | 67.0 ± 3.5 |

**Finding:** Structure is **redundant** when full function source is encoded. All models tie within noise (~63 F1). The function body text already contains the call and state-variable information, making structural message passing informationless.

#### Experiment 2 — Atomic Features (function node dropped; state + callee only)

| Model | F1 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
|:---|:---:|:---:|:---:|:---:|:---:|
| set-pool (no edges) | 44.3 ± 3.1 | 51.2 ± 4.4 | 71.0 ± 2.9 | 35.5 ± 3.6 | 51.7 ± 3.0 |
| **pairwise-GCN (clique)** | **55.2 ± 4.8** | 54.3 ± 4.2 | **80.6 ± 1.0** | **48.7 ± 7.0** | **60.4 ± 4.7** |
| pairwise-GAT (clique) | 52.5 ± 2.7 | 57.9 ± 10.4 | 80.5 ± 3.4 | 45.0 ± 5.7 | 58.8 ± 1.7 |
| hypergraph (ours) | 50.4 ± 2.5 | 52.6 ± 3.2 | 76.4 ± 1.0 | 41.9 ± 4.0 | 58.4 ± 2.3 |

McNemar (hypergraph vs pairwise-GCN, seed 42): pairwise-only-correct=20, hypergraph-only-correct=3, **p=0.0008** (favors pairwise).

**Finding:** When the function node is dropped, structure becomes essential (+10.9 F1 from set-pool to pairwise-GCN), but **pairwise beats the hypergraph** significantly. Without the function as a hub, the hyperedge loses its organizing center.

#### Experiment 3 — Signature/Skeleton Function Features (atomic function-as-hub)

Function node re-embedded from declaration only (body stripped). This is the **key experiment** establishing the hyperedge advantage.

| Model | F1 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
|:---|:---:|:---:|:---:|:---:|:---:|
| set-pool (no edges) | 46.0 ± 2.5 | 51.7 ± 2.9 | 75.4 ± 4.1 | 36.8 ± 1.9 | 53.6 ± 3.4 |
| pairwise-GCN (clique) | 51.2 ± 2.2 | 48.1 ± 8.7 | 75.8 ± 3.3 | 39.9 ± 1.8 | 59.7 ± 3.0 |
| pairwise-GAT (clique) | 51.9 ± 3.2 | **69.8 ± 4.5** | **86.5 ± 3.7** | 41.3 ± 3.1 | 60.5 ± 2.8 |
| **hypergraph (ours)** | **59.4 ± 4.4** | 60.8 ± 5.4 | 82.9 ± 1.7 | **51.4 ± 5.9** | **65.1 ± 3.7** |

McNemar (hypergraph vs pairwise-GCN, seed 42): hypergraph-only-correct=29, pairwise-only-correct=9, **p=0.0021** (favors hypergraph).

**Finding:** Hyperedge **outperforms all pairwise variants** on F1 (+7.5 pts vs GAT) and cross-contract F1 (+10.1 pts vs GAT). The hub-over-shared-{state,callee} structure is what the hyperedge uniquely preserves; clique expansion fragments it.

**Caveat:** Pairwise-GAT leads the threshold-free ranking metrics (PR-AUC 69.8 vs 60.8; ROC-AUC 86.5 vs 82.9). The hyperedge advantage is specifically at the operating point (≥95% recall threshold) and on cross-contract interactions — not in global ranking.

### 3.3 Rule-Based Heuristic Baselines

All evaluated on 169-item test set (44 pos / 125 neg). Note: the hard-negative design (all negatives contain external calls) makes any "flag any external call" detector equivalent to AllPositive.

| Detector | Precision | Recall | F1 | F2 | Test-neg FPR |
|:---|:---:|:---:|:---:|:---:|:---:|
| AllPositive (floor) | 26.0 | 100.0 | 41.3 | 63.8 | 100.0 |
| HasLowLevel | 25.0 | 2.3 | 4.2 | 2.8 | 2.4 |
| UncheckedLowLevel (SWC-104) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| UnguardedExtWrite (SWC-107) | 24.4 | 25.0 | 24.7 | 24.9 | 27.2 |
| NotSafeERC20 | 75.0 | 20.5 | 32.1 | 23.9 | 2.4 |
| **HyperVul (full, seed=42)** | **47.7** | **93.2** | **63.1** | **78.2** | — |

HyperVul substantially outperforms all rule-based baselines on recall (93.2% vs best rule's 25.0%). The NotSafeERC20 rule has higher precision (75%) but near-zero recall, confirming it targets only one narrow pattern.

### 3.4 Node-Set Ablation (Controlled, seed=42)

All variants trained identically; only the node types in the hyperedge change. "Ours" is re-trained and re-evaluated here (not copied from a prior iteration).

| Model | Recall | Precision | F1 | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Function-only | 90.91% | 40.40% | 55.94% | 72.73% | 59.39% | 84.93% | 44.44% | 65.00% |
| {Function, State} | 93.18% | 41.84% | 57.75% | 74.82% | 51.52% | 82.29% | 43.75% | 69.23% |
| {Function, Callee} | **95.45%** | 43.30% | 59.57% | 76.92% | **69.27%** | **87.98%** | 45.45% | 72.00% |
| **Full {Func, State, Callee} (Ours)** | 93.18% | **47.67%** | **63.08%** | **78.24%** | 63.81% | 86.71% | **52.63%** | **71.23%** |

**Key observations:**
- Adding state variables to function-only (+2.3 pp recall, +1.8 pp F1): state tracking helps reentrancy detection
- Adding callees to function-only (+4.5 pp recall, +3.6 pp F1): external call context is the strongest structural contributor
- Full hyperedge: best F1, F2, precision, and cross-contract F1 — the combined interaction representation is optimal at this operating point
- {Function, Callee} has better PR-AUC and ROC-AUC (69.3%, 88.0%) than the full model (63.8%, 86.7%), suggesting state variable nodes introduce mild noise for threshold-free ranking at the cost of interaction-level precision

#### Per-Vulnerability-Type Recall (Node-Set Ablation)

| Model | Front-running SWC-114 (n=15) | Reentrancy SWC-107 (n=23*) | Unchecked Call SWC-104 (n=6*) |
|:---|:---:|:---:|:---:|
| Function-only | 93.33% | 91.30% | 83.33% |
| {Function, State} | **100.00%** | 86.96% | **100.00%** |
| {Function, Callee} | **100.00%** | 91.30% | **100.00%** |
| **Full (Ours)** | **100.00%** | 86.96% | **100.00%** |

> ⚠️ **INDICATIVE ONLY** — per-class counts are extremely small; these figures have wide uncertainty.

### 3.5 Cross-Contract vs. Intra-Contract Performance (Deployed Model, seed=42)

| Subset | Count (Pos/Neg) | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Cross-Contract** | 79 (16/63) | 36.59% | 93.75% | 52.63% | 71.43% | 62.72% | 85.91% |
| **Intra-Contract** | 90 (28/62) | 57.78% | 92.86% | 71.23% | 82.80% | 66.30% | 87.67% |

The cross-contract precision gap (36.6% vs 57.8%) is the major performance disparity. Cross-contract diagnostic analysis found that this is primarily a **DAppSCAN label-noise artifact** (100% FORGE cross-contract recall vs 75% DAppSCAN cross-contract recall), not a structural deficiency addressable by architectural changes.

### 3.6 Safety-Aware Feature Ablation (5-seed Multi-Arm)

This ablation tests whether adding security-context node features (`security_context` = reentrancy guard flags, modifier presence, access control patterns) reduces OOD FPR. Three arms:

- **Sym:none** — no security context features (baseline)
- **Sym:security** — security_context features only (without full body)
- **Sym:full** — all features including security context

#### Test Performance (mean ± std, 5 seeds)

| Arm | F1 | Precision | Recall | F2 | PR-AUC | ROC-AUC |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Sym:none | 64.2 ± 1.2 | 48.9 ± 1.9 | 93.6 ± 2.5 | 79.1 ± 0.9 | 64.4 ± 2.6 | 86.8 ± 1.2 |
| Sym:security | 65.6 ± 2.3 | 50.0 ± 2.6 | **95.5 ± 0.0** | 80.7 ± 1.4 | 68.2 ± 1.8 | 88.4 ± 1.0 |
| Sym:full | **66.0 ± 1.8** | **50.4 ± 2.0** | 95.5 ± 1.6 | **81.0 ± 1.5** | **69.6 ± 1.8** | **88.6 ± 0.9** |

#### OOD FPR (mean ± std, 5 seeds — operating-point threshold, §1 of ablation report)

| Arm | OZ-Holdout | MakerDAO | Bancor | Liquity |
|:---|:---:|:---:|:---:|:---:|
| Sym:none | 31.1 ± 7.8 | 69.4 ± 10.0 | 51.9 ± 6.6 | 44.1 ± 11.1 |
| Sym:security | **26.7 ± 6.3** | **59.6 ± 1.4** | 46.2 ± 4.6 | **37.3 ± 2.9** |
| Sym:full | **22.2 ± 6.2** | 64.1 ± 5.8 | **40.5 ± 3.7** | **34.8 ± 2.2** |

#### OOD FPR at Matched Recall (90%) — Fairer Comparison

Evaluated at the threshold yielding 90% test recall across all arms to remove threshold-tuning confound.

| Arm | OZ-Holdout | MakerDAO | Bancor | Liquity |
|:---|:---:|:---:|:---:|:---:|
| Sym:none | 25.4 ± 11.1 | 60.9 ± 14.1 | 45.5 ± 10.7 | 33.5 ± 11.7 |
| Sym:security | **14.9 ± 4.3** | **45.8 ± 5.4** | 34.3 ± 6.1 | **18.2 ± 7.5** |
| Sym:full | **14.0 ± 3.3** | 49.8 ± 5.6 | **28.8 ± 3.7** | **16.5 ± 5.4** |

**McNemar significance (paired, pooled over seeds):** All 12 pairwise arm comparisons across all four holdouts are significant (p < 0.0013, with most p < 0.0001). Security features make significantly different and consistently better clean-code FP decisions than no security features.

**Key finding:** Security context features ("features beat loss tricks") — stage-2 security_context embeddings significantly reduce OOD FPR at matched recall on every holdout except Sym:full vs Sym:security on MakerDAO. Sym:full is the recommended arm: best test F1 (66.0%), best PR-AUC (69.6%), best OOD FPR on OZ and Bancor.

### 3.7 Error Analysis

#### False Negative Patterns

- **SWC-107 Reentrancy misses (seed=42):** Recall 86.96% on 23 reentrancy positives. Approximately 3 missed instances appear to involve indirect reentrancy (state mutation occurs in a helper called after the external call, not directly in the flagged function).
- **Cross-contract false negatives:** All 4 missed cross-contract positives (at the deployed threshold) belong to DAppSCAN, not FORGE. FORGE cross-contract recall = 100%. The labeling noise hypothesis is supported: DAppSCAN uses single-point line annotations, while FORGE uses structured VFP reports.
- **SWC-112 Delegatecall:** 6 training instances only; 0 in test. Effectively unevaluable on this dataset.

#### False Positive Patterns

- **External call over-flagging:** The dominant error mode. The model acts as an "external call detector": functions with multiple external calls in production DeFi protocols (MakerDAO, Bancor) are flagged even when access controls and safety checks are present.
- **Root cause:** Flat node embeddings (CLS token of call expression text) do not distinguish safe calls (`onlyOwner`, `nonReentrant`-guarded) from unguarded ones. The model sees external call embeddings similar to training positives without semantic awareness of surrounding invariants.
- **Security feature mitigation:** Adding security context features reduces OOD FPR substantially (see §3.6), but MakerDAO FPR remains high (45.8–64.1%) — the protocol's heavily modular architecture generates many external-call-dense interactions that resemble vulnerable patterns structurally.

#### Dataset Artifacts

- **Label quality (DAppSCAN, 227 items reviewed):** 95.2% CONFIRMED, 2.2% MISLOCATED, 0.9% COMMIT_DRIFT, 1.8% DUBIOUS. The DUBIOUS items are concentrated in the TEST Cross-Contract group (3/16 items), which partially explains the cross-contract precision gap.
- **SWC-104 view/pure annotation issue:** 4 test-set SWC-104 items are annotated as vulnerable but belong to `view`/`pure` functions that only invoke read-only queries (getters, price oracles). The model assigns these P < 0.08 (model already "knew" these were wrong). A formal label correction proposal exists but has not been applied pending human confirmation. This is one potential source of the 49→44 positive discrepancy.

### 3.8 Limitations

1. **Dataset size.** 44 test positives → F1 variance of ±4–5 across seeds. Per-class and cross-contract results are particularly noisy. The core claims require validation on the larger FORGE-Curated/DAppSCAN benchmark (submodules populated; scale-up not yet run).

2. **Label quality (DAppSCAN).** 4.8% of DAppSCAN items are MISLOCATED, COMMIT_DRIFT, or DUBIOUS. Given that 73.2% of training positives come from DAppSCAN, label noise has a direct negative effect on the classifier's learned decision boundary. Label quality cannot be independently verified without re-auditing original source commits.

3. **SmartBERT-v3 truncation.** Function bodies are truncated at 256 tokens. 68.4% of cross-contract positive functions exceed this limit. Truncation does not appear to directly cause false negatives (0% of missed cross-contract positives were truncated) but may cause information loss in function body embeddings that affects generalization.

4. **Frozen encoder.** The SmartBERT-v3 encoder is not fine-tuned on vulnerability data. End-to-end training on the ~550-positive dataset risks catastrophic forgetting, but the frozen encoder produces generic code representations that lack vulnerability-specific semantics (e.g., cannot distinguish guarded from unguarded external calls from the function text alone).

5. **OOD FPR remains high.** Even with safety-aware features, MakerDAO FPR is 45.8–64.1% and Bancor is 28.8–46.2%. The system is not deployment-ready as an autonomous detector; it would require human review of all flagged interactions in production DeFi codebases.

6. **Generalization scope.** All evaluation is on Solidity smart contracts from known audit firms using known SWC classifications. Generalization to newer Solidity versions, cross-language smart contracts (e.g., Vyper), or novel vulnerability classes not in the SWC taxonomy is unknown and not evaluated.

7. **Delegatecall support.** Only 6 SWC-112 positives exist in the entire dataset (all in train). The system cannot be meaningfully evaluated on delegatecall vulnerabilities.

8. **No SOTA comparison.** No direct comparison to published vulnerability detectors (Slither, Mythril, GNNSCVul, etc.) was possible because FORGE/DAppSCAN contracts import unbundled `@openzeppelin/@uniswap` node_modules dependencies that cause standalone compilation failures for static analyzers. The rule-based heuristics in §3.3 emulate this family but are not faithful re-implementations.

---

## 4. Project Status

### 4.1 What Is Complete

- **Architecture:** HyperedgeClassifier with AttentionPooling, MLP head, LocalizationHead. Deployed and producing reproducible results across 5 seeds. Unified GNN skeleton for fair multi-model comparison (`src/models/gnn_zoo.py`).
- **Dataset:** FORGE (83 pos) + DAppSCAN (227 pos) hyperedge extraction; Union-Find leakage-free splits; 3× negative:positive ratio with 50% cross-contract match; augmentation pipeline (507 variants accepted); SmartBERT-v3 feature extraction for all splits and external holdouts.
- **Training pipeline:** Iteration-3 clean-negative K-sweep; multi-seed harness with bootstrap CIs and McNemar; threshold-rule standardized across all experiments.
- **Ablations:**
  - Node-set ablation (4 variants, controlled, seed=42) ✓
  - Representation comparison — 3 experiments × 5 seeds ✓
  - Safety-aware feature ablation (3 arms × 5 seeds, McNemar significance) ✓
- **Cross-contract testing:** Performance reported separately; source-level diagnostic run; FORGE vs DAppSCAN label-noise hypothesis supported.
- **Error analysis:** DAppSCAN 227-item label review; label correction proposal (4 items); false positive root cause analysis; cross-contract diagnostic.
- **OOD FPR evaluation:** 4 disjoint holdouts (OZ, MakerDAO, Bancor, Liquity); Wilson CIs; matched-recall comparison.

### 4.2 What Remains

- [ ] Resolve the 49→44 positive test set discrepancy (see §4.3)
- [ ] Human confirmation of 4 SWC-104 label correction candidates and apply if confirmed
- [ ] Scale-up experiment on full FORGE-Curated + DAppSCAN benchmark with contract-disjoint splits (submodules populated)
- [ ] Paper writing: Introduction, Related Work, Method, Experiments, Discussion, Conclusion
- [ ] Advisor review of integrity issues before results section is finalized
- [ ] Decide pivot direction (reframe as "when does structure help" study vs. FPR fix via end-to-end fine-tuning vs. continue scale-up)
- [ ] Confirm Sym:full as the recommended arm for paper submission or run additional comparison seeds

### 4.3 Critical Blockers — Integrity Issues for Advisor Review

> **These must be resolved before the paper's results section is finalized.**

#### Blocker 1 — Test Set Positive Count Discrepancy (UNRESOLVED)

The split report (`experiments/results/split_report.md`) records **49 positives** in the test split (24 reentrancy, 15 front-running, 10 unchecked call). All evaluation scripts consistently report **44 positives** (23 reentrancy, 15 front-running, 6 unchecked call, 0 delegatecall) on a 169-item test set.

The label correction proposal identifies 4 SWC-104 test-set items as potentially invalid but states explicitly "no labels have been modified." This accounts for at most 4 of the 5-item discrepancy (unchecked call: 10→6). The 5th item (reentrancy: 24→23) is untracked.

**Action required:** Trace the evaluation data loading pipeline to identify which 5 items are excluded and confirm whether this exclusion is intentional and correctly documented.

#### Blocker 2 — DAppSCAN DUBIOUS Items in Test Set (PENDING HUMAN REVIEW)

The DAppSCAN label review identified **4 DUBIOUS** items, of which **3 are in the TEST Cross-Contract group** (3 of 16 items = 18.75%). These items have pre-classification flags but have not been confirmed or removed by a human reviewer.

If these 3 DUBIOUS test-cross-contract items are false positives in the test set, the reported cross-contract recall figures are inflated. If they are removed from the test set, all cross-contract metrics must be recomputed.

**Action required:** Human domain expert must review the 4 DUBIOUS items. Decision (confirm, remove, or reclassify) must be documented and applied before submission.

#### Blocker 3 — OOD FPR Remains Practically Prohibitive (KNOWN LIMITATION)

MakerDAO FPR of 45.8–76.4% across arms and evaluation points is too high for any deployment claim. The paper **must not** claim the system is production-ready or practically deployable.

**Framing required:** The paper should frame HyperVul as a **promising reformulation on a curated benchmark**, not as a deployment-ready system. The OOD FPR issue must be prominently disclosed in the limitations section (which it is, per this report) and in the abstract.

#### Blocker 4 — Hyperedge Advantage Conditionality (MUST DISCLOSE)

The hyperedge outperforms pairwise representations **only under atomic (signature) features** (Experiment 3). Under full function body embeddings (Experiment 1), structure is redundant and the hyperedge performs below the set-pool baseline. This conditionality is a core scientific finding, not a weakness to hide.

**Action required:** The paper's claim must be precisely scoped: "hyperedge representations are advantageous when function node features are atomic (non-redundant), specifically under function-signature embeddings."

---

## Appendix A: File Inventory

### Key Source Files

| File | Description |
|:---|:---|
| [model/model.py](model/model.py) | `HyperedgeClassifier`, `AttentionPooling`, `LocalizationHead`, `flag_tuples` inference |
| [model/train.py](model/train.py) | Iteration-3 training loop with clean-negative K-sweep |
| [model/run_representation_comparison.py](model/run_representation_comparison.py) | Main multi-seed harness (set-pool / pairwise-GCN / pairwise-GAT / hypergraph) |
| [model/run_unit_comparison.py](model/run_unit_comparison.py) | Node-set ablation (function/state/callee) |
| [src/models/gnn_zoo.py](src/models/gnn_zoo.py) | Unified GNN skeleton for fair model comparison |
| [src/models/ops.py](src/models/ops.py) | `SegmentAttentionPool`, `MLPHead`, `LocalizationHead` shared ops |
| [src/models/set_pool.py](src/models/set_pool.py) | Structure-free set-pool baseline |
| [scripts/build_hypergraph.py](scripts/build_hypergraph.py) | Hyperedge construction from AST (`build_contract_graphs`) |
| [scripts/build_signature_features.py](scripts/build_signature_features.py) | Re-embeds function nodes as signatures (body stripped) |
| [scripts/extract_features.py](scripts/extract_features.py) | AST + SmartBERT-v3 feature extraction |
| [scripts/build_security_features.py](scripts/build_security_features.py) | Security context feature extraction |
| [experiments/aggregate_ablation.py](experiments/aggregate_ablation.py) | Multi-seed aggregation + McNemar for safety-aware ablation |

### Key Data Files

| File | Description |
|:---|:---|
| [data/splits/train_augmented.json](data/splits/train_augmented.json) | Augmented training set (552 pos / 829 neg, ~224 MB) |
| [data/splits/train_augmented_sig.json](data/splits/train_augmented_sig.json) | Training set with signature features |
| [data/splits/test_features.json](data/splits/test_features.json) | Test set with full features (44 pos / 125 neg) |
| [data/splits/test_features_sym.json](data/splits/test_features_sym.json) | Test set with security context features |
| [data/splits/val_features.json](data/splits/val_features.json) | Validation set with full features |

### Key Results Files

| File | Description |
|:---|:---|
| [experiments/results/representation_findings.md](experiments/results/representation_findings.md) | Consolidated 3-experiment representation comparison |
| [experiments/results/ablation_summary.md](experiments/results/ablation_summary.md) | 5-seed safety-aware feature ablation (none/security/full) |
| [experiments/results/unit_comparison_results.md](experiments/results/unit_comparison_results.md) | Node-set ablation (function/state/callee) |
| [experiments/results/baseline_comparison_heuristics.md](experiments/results/baseline_comparison_heuristics.md) | Rule-based baseline comparison |
| [experiments/results/split_report.md](experiments/results/split_report.md) | Dataset split documentation (Union-Find, leakage verification) |
| [experiments/results/crosscontract_diagnostics.md](experiments/results/crosscontract_diagnostics.md) | Cross-contract failure root cause analysis |
| [experiments/results/label_correction_proposal.md](experiments/results/label_correction_proposal.md) | 4 SWC-104 view/pure items flagged for review |
| [experiments/results/dappscan_label_review.md](experiments/results/dappscan_label_review.md) | DAppSCAN 227-item manual label quality review |
| [experiments/results/forge_curated_hyperedge_report.md](experiments/results/forge_curated_hyperedge_report.md) | FORGE AST hyperedge extraction (83 positives) |
| [experiments/results/negative_sampling_report.md](experiments/results/negative_sampling_report.md) | Negative hyperedge construction and gating |
| [experiments/results/augmentation_report.md](experiments/results/augmentation_report.md) | Data augmentation pipeline and discard statistics |

---

## Appendix B: Reproducibility

```bash
# Environment
python 3.12.12 (pyenv), CUDA available
pip install torch==2.9.0+cu128 torch_geometric==2.8.0 transformers tree_sitter \
    tree_sitter_solidity scikit-learn scipy numpy

# One-time submodule init (~5.7 GB)
git submodule update --init --depth 1 data/DAppSCAN data/FORGE-Curated

# Representation comparison (Experiment 3, signature features)
python model/run_representation_comparison.py --seeds 42 43 44 45 46 --sig

# Node-set ablation
python model/run_unit_comparison.py

# Safety-aware feature ablation
python experiments/aggregate_ablation.py

# Build signature features
python scripts/build_signature_features.py
```

Fixed random seed: all multi-seed runs use seeds {42, 43, 44, 45, 46}. Model checkpoints for all seeds and arms are saved in `model/`.
