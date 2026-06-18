# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_scl_seed45.pt`
> **Arm**: `scl` (SCL=ON, Localization=OFF) · **Seed**: `45`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.1464`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.5986** | **0.1464** | **97.30%** | **7.53%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 24 | 38.10% | [27.12%, 50.44%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 187 | 44.10% | [39.45%, 48.86%] |
| **Bancor V3** | External (DeFi Application) | 209 | 115 | 55.02% | [48.25%, 61.62%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 112 | 40.14% | [34.56%, 45.99%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 42.00% |
| **Recall** | 95.45% |
| **F1-Score** | 58.33% |
| **F2-Score** | 76.09% |
| **PR-AUC** | 62.29% |
| **ROC-AUC** | 85.78% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 31.25% | 93.75% | 46.88% | 66.96% | 62.38% | 84.92% |
| **Intra-Contract** | 90 (28/62) | 51.92% | 96.43% | 67.50% | 82.32% | 63.89% | 86.00% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 23 | 91.30% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 100.00% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=45**, arm=**scl** (SCL=ON, Localization=OFF), K_app=100 (fixed), threshold=0.1464.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 58.33%, Precision 42.00%, Recall 95.45%, PR-AUC 62.29%, ROC-AUC 85.78%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 38.10% [27.12%, 50.44%]
  - MakerDAO DSS: 44.10% [39.45%, 48.86%]
  - Bancor V3: 55.02% [48.25%, 61.62%]
  - Liquity V1: 40.14% [34.56%, 45.99%]
- **Cross- vs intra-contract (test)**: cross F1 46.88% (recall 93.75%), intra F1 67.50% (recall 96.43%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
