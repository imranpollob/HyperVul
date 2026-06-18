# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_baseline_seed42.pt`
> **Arm**: `baseline` (SCL=OFF, Localization=OFF) · **Seed**: `42`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.1826`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.5498** | **0.1826** | **97.30%** | **5.38%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 15 | 23.81% | [14.99%, 35.64%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 281 | 66.27% | [61.65%, 70.61%] |
| **Bancor V3** | External (DeFi Application) | 209 | 102 | 48.80% | [42.11%, 55.54%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 119 | 42.65% | [36.99%, 48.52%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 47.19% |
| **Recall** | 95.45% |
| **F1-Score** | 63.16% |
| **F2-Score** | 79.25% |
| **PR-AUC** | 64.01% |
| **ROC-AUC** | 86.75% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 34.09% | 93.75% | 50.00% | 69.44% | 63.33% | 86.41% |
| **Intra-Contract** | 90 (28/62) | 60.00% | 96.43% | 73.97% | 85.99% | 65.68% | 87.15% |

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
> Single run: **seed=42**, arm=**baseline** (SCL=OFF, Localization=OFF), K_app=100 (fixed), threshold=0.1826.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 63.16%, Precision 47.19%, Recall 95.45%, PR-AUC 64.01%, ROC-AUC 86.75%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 23.81% [14.99%, 35.64%]
  - MakerDAO DSS: 66.27% [61.65%, 70.61%]
  - Bancor V3: 48.80% [42.11%, 55.54%]
  - Liquity V1: 42.65% [36.99%, 48.52%]
- **Cross- vs intra-contract (test)**: cross F1 50.00% (recall 93.75%), intra F1 73.97% (recall 96.43%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
