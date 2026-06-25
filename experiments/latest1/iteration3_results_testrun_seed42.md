# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_testrun_seed42.pt`
> **Arm**: `testrun` (SCL=ON, Localization=ON) · **Seed**: `42`
> **Clean Negative Training Count K_app**: `50` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.4239`  
> **Validation Recall**: `92.11%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **50** | **0.1013** | **0.4239** | **92.11%** | **11.83%** |

---

## 2. Final Negative Training Set Composition
*   **Total Positives in Training**: 539 (Base Codebase Positives: 539)
*   **Total Negatives in Training**: 969 (100% of negative class)
    *   *Codebase (Tier-A) Hard Negatives*: 819 (84.52%)
    *   *Clean Library (OpenZeppelin) Negatives*: 100 (10.32%)
    *   *Clean Application (Aave V3) Negatives*: 50 (5.16%)

---

## 3. Generalization on Disjoint Holdout Sets
These results represent the final, single-evaluation run on all mathematically isolated holdout sets. **FPRs are reported with 95% Wilson Score binomial confidence intervals**:

| Holdout Set | Type | Size | False Positives | FPR (Point Estimate) | 95% Wilson Confidence Interval |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OZ-Holdout** | Internal (Library) | 63 | 26 | 41.27% | [29.96%, 53.58%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 274 | 64.62% | [59.96%, 69.02%] |
| **Bancor V3** | External (DeFi Application) | 209 | 81 | 38.76% | [32.41%, 45.51%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 151 | 54.12% | [48.26%, 59.87%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (176 items: 45 positives, 131 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 43.30% |
| **Recall** | 93.33% |
| **F1-Score** | 59.15% |
| **F2-Score** | 75.81% |
| **PR-AUC** | 56.56% |
| **ROC-AUC** | 84.51% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 34.15% | 87.50% | 49.12% | 66.67% | 56.00% | 79.07% |
| **Intra-Contract** | 97 (29/68) | 50.00% | 96.55% | 65.88% | 81.40% | 59.45% | 86.26% |

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
> Single run: **seed=42**, arm=**testrun** (SCL=ON, Localization=ON), K_app=50 (fixed), threshold=0.4239.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 59.15%, Precision 43.30%, Recall 93.33%, PR-AUC 56.56%, ROC-AUC 84.51%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 41.27% [29.96%, 53.58%]
  - MakerDAO DSS: 64.62% [59.96%, 69.02%]
  - Bancor V3: 38.76% [32.41%, 45.51%]
  - Liquity V1: 54.12% [48.26%, 59.87%]
- **Cross- vs intra-contract (test)**: cross F1 49.12% (recall 87.50%), intra F1 65.88% (recall 96.55%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
