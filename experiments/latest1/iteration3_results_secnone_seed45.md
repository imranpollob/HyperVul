# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secnone_seed45.pt`
> **Arm**: `secnone` (SCL=ON, Localization=ON) · **Seed**: `45`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.5305`  
> **Validation Recall**: `97.37%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.1241** | **0.5305** | **97.37%** | **11.83%** |

---

## 2. Final Negative Training Set Composition
*   **Total Positives in Training**: 539 (Base Codebase Positives: 539)
*   **Total Negatives in Training**: 1019 (100% of negative class)
    *   *Codebase (Tier-A) Hard Negatives*: 819 (80.37%)
    *   *Clean Library (OpenZeppelin) Negatives*: 100 (9.81%)
    *   *Clean Application (Aave V3) Negatives*: 100 (9.81%)

---

## 3. Generalization on Disjoint Holdout Sets
These results represent the final, single-evaluation run on all mathematically isolated holdout sets. **FPRs are reported with 95% Wilson Score binomial confidence intervals**:

| Holdout Set | Type | Size | False Positives | FPR (Point Estimate) | 95% Wilson Confidence Interval |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OZ-Holdout** | Internal (Library) | 63 | 25 | 39.68% | [28.53%, 52.02%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 292 | 68.87% | [64.31%, 73.09%] |
| **Bancor V3** | External (DeFi Application) | 209 | 105 | 50.24% | [43.52%, 56.95%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 108 | 38.71% | [33.18%, 44.54%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (176 items: 45 positives, 131 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 41.58% |
| **Recall** | 93.33% |
| **F1-Score** | 57.53% |
| **F2-Score** | 74.73% |
| **PR-AUC** | 54.42% |
| **ROC-AUC** | 83.72% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 31.82% | 87.50% | 46.67% | 64.81% | 58.17% | 81.75% |
| **Intra-Contract** | 97 (29/68) | 49.12% | 96.55% | 65.12% | 80.92% | 52.21% | 83.22% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 24 | 91.67% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 83.33% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=45**, arm=**secnone** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.5305.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 57.53%, Precision 41.58%, Recall 93.33%, PR-AUC 54.42%, ROC-AUC 83.72%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 39.68% [28.53%, 52.02%]
  - MakerDAO DSS: 68.87% [64.31%, 73.09%]
  - Bancor V3: 50.24% [43.52%, 56.95%]
  - Liquity V1: 38.71% [33.18%, 44.54%]
- **Cross- vs intra-contract (test)**: cross F1 46.67% (recall 87.50%), intra F1 65.12% (recall 96.55%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
