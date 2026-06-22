# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secsec_seed46.pt`
> **Arm**: `secsec` (SCL=ON, Localization=ON) · **Seed**: `46`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.4494`  
> **Validation Recall**: `97.37%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.1212** | **0.4494** | **97.37%** | **12.90%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 30 | 47.62% | [35.78%, 59.73%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 330 | 77.83% | [73.64%, 81.52%] |
| **Bancor V3** | External (DeFi Application) | 209 | 122 | 58.37% | [51.60%, 64.85%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 170 | 60.93% | [55.10%, 66.47%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (176 items: 45 positives, 131 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 39.64% |
| **Recall** | 97.78% |
| **F1-Score** | 56.41% |
| **F2-Score** | 75.60% |
| **PR-AUC** | 65.93% |
| **ROC-AUC** | 86.96% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 30.00% | 93.75% | 45.45% | 65.79% | 64.31% | 83.43% |
| **Intra-Contract** | 97 (29/68) | 47.54% | 100.00% | 64.44% | 81.92% | 62.26% | 87.12% |

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
> Single run: **seed=46**, arm=**secsec** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.4494.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 56.41%, Precision 39.64%, Recall 97.78%, PR-AUC 65.93%, ROC-AUC 86.96%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 47.62% [35.78%, 59.73%]
  - MakerDAO DSS: 77.83% [73.64%, 81.52%]
  - Bancor V3: 58.37% [51.60%, 64.85%]
  - Liquity V1: 60.93% [55.10%, 66.47%]
- **Cross- vs intra-contract (test)**: cross F1 45.45% (recall 93.75%), intra F1 64.44% (recall 100.00%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
