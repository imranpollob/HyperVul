# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secfull_seed44.pt`
> **Arm**: `secfull` (SCL=ON, Localization=ON) · **Seed**: `44`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.5379`  
> **Validation Recall**: `97.37%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.1244** | **0.5379** | **97.37%** | **6.45%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 15 | 23.81% | [14.99%, 35.64%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 306 | 72.17% | [67.72%, 76.22%] |
| **Bancor V3** | External (DeFi Application) | 209 | 115 | 55.02% | [48.25%, 61.62%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 92 | 32.97% | [27.72%, 38.69%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (176 items: 45 positives, 131 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 37.93% |
| **Recall** | 97.78% |
| **F1-Score** | 54.66% |
| **F2-Score** | 74.32% |
| **PR-AUC** | 52.37% |
| **ROC-AUC** | 81.44% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 29.63% | 100.00% | 45.71% | 67.80% | 64.61% | 83.13% |
| **Intra-Contract** | 97 (29/68) | 45.16% | 96.55% | 61.54% | 78.65% | 47.54% | 78.75% |

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
> Single run: **seed=44**, arm=**secfull** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.5379.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 54.66%, Precision 37.93%, Recall 97.78%, PR-AUC 52.37%, ROC-AUC 81.44%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 23.81% [14.99%, 35.64%]
  - MakerDAO DSS: 72.17% [67.72%, 76.22%]
  - Bancor V3: 55.02% [48.25%, 61.62%]
  - Liquity V1: 32.97% [27.72%, 38.69%]
- **Cross- vs intra-contract (test)**: cross F1 45.71% (recall 100.00%), intra F1 61.54% (recall 96.55%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
