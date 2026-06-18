# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secsec_seed45.pt`
> **Arm**: `secsec` (SCL=OFF, Localization=OFF) · **Seed**: `45`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.2821`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.6196** | **0.2821** | **97.30%** | **4.30%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 21 | 33.33% | [22.95%, 45.63%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 257 | 60.61% | [55.89%, 65.15%] |
| **Bancor V3** | External (DeFi Application) | 209 | 111 | 53.11% | [46.35%, 59.76%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 109 | 39.07% | [33.53%, 44.90%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 47.73% |
| **Recall** | 95.45% |
| **F1-Score** | 63.64% |
| **F2-Score** | 79.55% |
| **PR-AUC** | 68.24% |
| **ROC-AUC** | 89.38% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 38.46% | 93.75% | 54.55% | 72.82% | 69.59% | 90.97% |
| **Intra-Contract** | 90 (28/62) | 55.10% | 96.43% | 70.13% | 83.85% | 67.55% | 87.90% |

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
> Single run: **seed=45**, arm=**secsec** (SCL=OFF, Localization=OFF), K_app=100 (fixed), threshold=0.2821.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 63.64%, Precision 47.73%, Recall 95.45%, PR-AUC 68.24%, ROC-AUC 89.38%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 33.33% [22.95%, 45.63%]
  - MakerDAO DSS: 60.61% [55.89%, 65.15%]
  - Bancor V3: 53.11% [46.35%, 59.76%]
  - Liquity V1: 39.07% [33.53%, 44.90%]
- **Cross- vs intra-contract (test)**: cross F1 54.55% (recall 93.75%), intra F1 70.13% (recall 96.43%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
