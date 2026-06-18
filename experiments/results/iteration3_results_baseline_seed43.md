# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_baseline_seed43.pt`
> **Arm**: `baseline` (SCL=OFF, Localization=OFF) · **Seed**: `43`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.0948`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.6166** | **0.0948** | **97.30%** | **8.60%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 22 | 34.92% | [24.33%, 47.25%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 201 | 47.41% | [42.70%, 52.16%] |
| **Bancor V3** | External (DeFi Application) | 209 | 119 | 56.94% | [50.16%, 63.47%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 152 | 54.48% | [48.62%, 60.22%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 43.16% |
| **Recall** | 93.18% |
| **F1-Score** | 58.99% |
| **F2-Score** | 75.65% |
| **PR-AUC** | 65.10% |
| **ROC-AUC** | 85.27% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 31.11% | 87.50% | 45.90% | 64.22% | 61.75% | 83.73% |
| **Intra-Contract** | 90 (28/62) | 54.00% | 96.43% | 69.23% | 83.33% | 66.88% | 85.94% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 23 | 91.30% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 83.33% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=43**, arm=**baseline** (SCL=OFF, Localization=OFF), K_app=100 (fixed), threshold=0.0948.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 58.99%, Precision 43.16%, Recall 93.18%, PR-AUC 65.10%, ROC-AUC 85.27%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 34.92% [24.33%, 47.25%]
  - MakerDAO DSS: 47.41% [42.70%, 52.16%]
  - Bancor V3: 56.94% [50.16%, 63.47%]
  - Liquity V1: 54.48% [48.62%, 60.22%]
- **Cross- vs intra-contract (test)**: cross F1 45.90% (recall 87.50%), intra F1 69.23% (recall 96.43%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
