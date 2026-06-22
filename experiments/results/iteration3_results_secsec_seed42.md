# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secsec_seed42.pt`
> **Arm**: `secsec` (SCL=ON, Localization=ON) · **Seed**: `42`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.4040`  
> **Validation Recall**: `97.37%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.1265** | **0.4040** | **97.37%** | **10.75%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 26 | 41.27% | [29.96%, 53.58%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 364 | 85.85% | [82.21%, 88.85%] |
| **Bancor V3** | External (DeFi Application) | 209 | 126 | 60.29% | [53.53%, 66.68%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 190 | 68.10% | [62.42%, 73.29%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (176 items: 45 positives, 131 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 34.96% |
| **Recall** | 95.56% |
| **F1-Score** | 51.19% |
| **F2-Score** | 70.96% |
| **PR-AUC** | 62.42% |
| **ROC-AUC** | 84.66% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 25.86% | 93.75% | 40.54% | 61.48% | 64.55% | 80.95% |
| **Intra-Contract** | 97 (29/68) | 43.08% | 96.55% | 59.57% | 77.35% | 61.92% | 85.04% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 24 | 91.67% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 100.00% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=42**, arm=**secsec** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.4040.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 51.19%, Precision 34.96%, Recall 95.56%, PR-AUC 62.42%, ROC-AUC 84.66%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 41.27% [29.96%, 53.58%]
  - MakerDAO DSS: 85.85% [82.21%, 88.85%]
  - Bancor V3: 60.29% [53.53%, 66.68%]
  - Liquity V1: 68.10% [62.42%, 73.29%]
- **Cross- vs intra-contract (test)**: cross F1 40.54% (recall 93.75%), intra F1 59.57% (recall 96.55%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
