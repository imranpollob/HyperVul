# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secfull_seed46.pt`
> **Arm**: `secfull` (SCL=ON, Localization=ON) · **Seed**: `46`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.4705`  
> **Validation Recall**: `97.37%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.1153** | **0.4705** | **97.37%** | **8.60%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 19 | 30.16% | [20.24%, 42.36%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 332 | 78.30% | [74.13%, 81.96%] |
| **Bancor V3** | External (DeFi Application) | 209 | 90 | 43.06% | [36.53%, 49.84%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 95 | 34.05% | [28.74%, 39.79%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (176 items: 45 positives, 131 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 42.16% |
| **Recall** | 95.56% |
| **F1-Score** | 58.50% |
| **F2-Score** | 76.24% |
| **PR-AUC** | 64.97% |
| **ROC-AUC** | 85.07% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 33.33% | 93.75% | 49.18% | 68.81% | 65.00% | 83.43% |
| **Intra-Contract** | 97 (29/68) | 49.12% | 96.55% | 65.12% | 80.92% | 63.84% | 84.23% |

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
> Single run: **seed=46**, arm=**secfull** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.4705.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 58.50%, Precision 42.16%, Recall 95.56%, PR-AUC 64.97%, ROC-AUC 85.07%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 30.16% [20.24%, 42.36%]
  - MakerDAO DSS: 78.30% [74.13%, 81.96%]
  - Bancor V3: 43.06% [36.53%, 49.84%]
  - Liquity V1: 34.05% [28.74%, 39.79%]
- **Cross- vs intra-contract (test)**: cross F1 49.18% (recall 93.75%), intra F1 65.12% (recall 96.55%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
