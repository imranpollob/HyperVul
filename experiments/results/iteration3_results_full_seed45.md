# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_full_seed45.pt`
> **Arm**: `full` (SCL=ON, Localization=ON) · **Seed**: `45`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.0613`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.5421** | **0.0613** | **97.30%** | **12.90%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 30 | 47.62% | [35.78%, 59.73%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 339 | 79.95% | [75.88%, 83.49%] |
| **Bancor V3** | External (DeFi Application) | 209 | 113 | 54.07% | [47.30%, 60.69%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 166 | 59.50% | [53.65%, 65.09%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 40.00% |
| **Recall** | 95.45% |
| **F1-Score** | 56.38% |
| **F2-Score** | 74.73% |
| **PR-AUC** | 65.54% |
| **ROC-AUC** | 86.20% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 29.41% | 93.75% | 44.78% | 65.22% | 61.83% | 84.62% |
| **Intra-Contract** | 90 (28/62) | 50.00% | 96.43% | 65.85% | 81.33% | 67.13% | 86.58% |

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
> Single run: **seed=45**, arm=**full** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.0613.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 56.38%, Precision 40.00%, Recall 95.45%, PR-AUC 65.54%, ROC-AUC 86.20%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 47.62% [35.78%, 59.73%]
  - MakerDAO DSS: 79.95% [75.88%, 83.49%]
  - Bancor V3: 54.07% [47.30%, 60.69%]
  - Liquity V1: 59.50% [53.65%, 65.09%]
- **Cross- vs intra-contract (test)**: cross F1 44.78% (recall 93.75%), intra F1 65.85% (recall 96.43%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
