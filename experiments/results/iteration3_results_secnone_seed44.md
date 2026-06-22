# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secnone_seed44.pt`
> **Arm**: `secnone` (SCL=ON, Localization=ON) · **Seed**: `44`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.5180`  
> **Validation Recall**: `97.37%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.1185** | **0.5180** | **97.37%** | **5.38%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 16 | 25.40% | [16.28%, 37.34%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 294 | 69.34% | [64.79%, 73.54%] |
| **Bancor V3** | External (DeFi Application) | 209 | 105 | 50.24% | [43.52%, 56.95%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 78 | 27.96% | [23.02%, 33.50%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (176 items: 45 positives, 131 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 34.45% |
| **Recall** | 91.11% |
| **F1-Score** | 50.00% |
| **F2-Score** | 68.56% |
| **PR-AUC** | 49.52% |
| **ROC-AUC** | 79.49% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 25.45% | 87.50% | 39.44% | 58.82% | 54.95% | 79.76% |
| **Intra-Contract** | 97 (29/68) | 42.19% | 93.10% | 58.06% | 75.00% | 46.90% | 77.99% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 24 | 91.67% |
| Front-running / Tx Order (SWC-114) | 15 | 93.33% |
| Unchecked Call Return (SWC-104) | 6 | 83.33% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=44**, arm=**secnone** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.5180.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 50.00%, Precision 34.45%, Recall 91.11%, PR-AUC 49.52%, ROC-AUC 79.49%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 25.40% [16.28%, 37.34%]
  - MakerDAO DSS: 69.34% [64.79%, 73.54%]
  - Bancor V3: 50.24% [43.52%, 56.95%]
  - Liquity V1: 27.96% [23.02%, 33.50%]
- **Cross- vs intra-contract (test)**: cross F1 39.44% (recall 87.50%), intra F1 58.06% (recall 93.10%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
