# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_run_seed42.pt`
> **Arm**: `run` (SCL=ON, Localization=ON) · **Seed**: `42`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.4076`  
> **Validation Recall**: `97.37%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.1189** | **0.4076** | **97.37%** | **22.58%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 29 | 46.03% | [34.31%, 58.21%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 369 | 87.03% | [83.49%, 89.90%] |
| **Bancor V3** | External (DeFi Application) | 209 | 132 | 63.16% | [56.44%, 69.41%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 195 | 69.89% | [64.27%, 74.98%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (176 items: 45 positives, 131 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 36.07% |
| **Recall** | 97.78% |
| **F1-Score** | 52.69% |
| **F2-Score** | 72.85% |
| **PR-AUC** | 62.28% |
| **ROC-AUC** | 85.34% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 27.27% | 93.75% | 42.25% | 63.03% | 60.22% | 81.45% |
| **Intra-Contract** | 97 (29/68) | 43.28% | 100.00% | 60.42% | 79.23% | 63.68% | 86.66% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 24 | 95.83% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 100.00% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=42**, arm=**run** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.4076.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 52.69%, Precision 36.07%, Recall 97.78%, PR-AUC 62.28%, ROC-AUC 85.34%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 46.03% [34.31%, 58.21%]
  - MakerDAO DSS: 87.03% [83.49%, 89.90%]
  - Bancor V3: 63.16% [56.44%, 69.41%]
  - Liquity V1: 69.89% [64.27%, 74.98%]
- **Cross- vs intra-contract (test)**: cross F1 42.25% (recall 93.75%), intra F1 60.42% (recall 100.00%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
