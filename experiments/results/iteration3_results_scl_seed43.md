# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_scl_seed43.pt`
> **Arm**: `scl` (SCL=ON, Localization=OFF) · **Seed**: `43`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.1333`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.6412** | **0.1333** | **97.30%** | **10.75%** |

---

## 2. Final Negative Training Set Composition
*   **Total Positives in Training**: 552 (Base Codebase Positives: 552)
*   **Total Negatives in Training**: 1029 (100% of negative class)
    *   *Codebase (Tier-A) Hard Negatives*: 829 (80.56%)
    *   *Clean Library (OpenZeppelin) Negatives*: 100 (9.72%)
    *   *Clean Application (Aave V3) Negatives*: 100 (9.72%)

---

## 3. Generalization on Disjoint Holdout Sets
These results represent the final, single-evaluation run on all mathematically isolated holdout sets. **FPRs are reported with 95% Wilson Score binomial confidence intervals**:

| Holdout Set | Type | Size | False Positives | FPR (Point Estimate) | 95% Wilson Confidence Interval |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OZ-Holdout** | Internal (Library) | 63 | 25 | 39.68% | [28.53%, 52.02%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 257 | 60.61% | [55.89%, 65.15%] |
| **Bancor V3** | External (DeFi Application) | 209 | 131 | 62.68% | [55.95%, 68.95%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 133 | 47.67% | [41.88%, 53.52%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 37.61% |
| **Recall** | 100.00% |
| **F1-Score** | 54.66% |
| **F2-Score** | 75.09% |
| **PR-AUC** | 55.95% |
| **ROC-AUC** | 84.33% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 27.59% | 100.00% | 43.24% | 65.57% | 53.10% | 83.73% |
| **Intra-Contract** | 90 (28/62) | 47.46% | 100.00% | 64.37% | 81.87% | 55.20% | 83.06% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 23 | 100.00% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 100.00% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=43**, arm=**scl** (SCL=ON, Localization=OFF), K_app=100 (fixed), threshold=0.1333.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 54.66%, Precision 37.61%, Recall 100.00%, PR-AUC 55.95%, ROC-AUC 84.33%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 39.68% [28.53%, 52.02%]
  - MakerDAO DSS: 60.61% [55.89%, 65.15%]
  - Bancor V3: 62.68% [55.95%, 68.95%]
  - Liquity V1: 47.67% [41.88%, 53.52%]
- **Cross- vs intra-contract (test)**: cross F1 43.24% (recall 100.00%), intra F1 64.37% (recall 100.00%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
