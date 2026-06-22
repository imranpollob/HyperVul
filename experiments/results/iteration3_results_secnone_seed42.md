# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secnone_seed42.pt`
> **Arm**: `secnone` (SCL=ON, Localization=ON) · **Seed**: `42`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.4658`  
> **Validation Recall**: `97.37%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.1216** | **0.4658** | **97.37%** | **8.60%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 23 | 36.51% | [25.72%, 48.85%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 336 | 79.25% | [75.13%, 82.83%] |
| **Bancor V3** | External (DeFi Application) | 209 | 106 | 50.72% | [43.99%, 57.42%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 148 | 53.05% | [47.19%, 58.82%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (176 items: 45 positives, 131 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 36.84% |
| **Recall** | 93.33% |
| **F1-Score** | 52.83% |
| **F2-Score** | 71.43% |
| **PR-AUC** | 51.72% |
| **ROC-AUC** | 81.31% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 26.42% | 87.50% | 40.58% | 59.83% | 60.69% | 81.55% |
| **Intra-Contract** | 97 (29/68) | 45.90% | 96.55% | 62.22% | 79.10% | 47.08% | 79.16% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 24 | 91.67% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 83.33% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=42**, arm=**secnone** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.4658.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 52.83%, Precision 36.84%, Recall 93.33%, PR-AUC 51.72%, ROC-AUC 81.31%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 36.51% [25.72%, 48.85%]
  - MakerDAO DSS: 79.25% [75.13%, 82.83%]
  - Bancor V3: 50.72% [43.99%, 57.42%]
  - Liquity V1: 53.05% [47.19%, 58.82%]
- **Cross- vs intra-contract (test)**: cross F1 40.58% (recall 87.50%), intra F1 62.22% (recall 96.55%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
