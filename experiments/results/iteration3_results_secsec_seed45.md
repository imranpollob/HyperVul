# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secsec_seed45.pt`
> **Arm**: `secsec` (SCL=ON, Localization=ON) · **Seed**: `45`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.4946`  
> **Validation Recall**: `97.37%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.1182** | **0.4946** | **97.37%** | **9.68%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 22 | 34.92% | [24.33%, 47.25%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 292 | 68.87% | [64.31%, 73.09%] |
| **Bancor V3** | External (DeFi Application) | 209 | 112 | 53.59% | [46.82%, 60.22%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 101 | 36.20% | [30.78%, 41.99%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (176 items: 45 positives, 131 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 41.58% |
| **Recall** | 93.33% |
| **F1-Score** | 57.53% |
| **F2-Score** | 74.73% |
| **PR-AUC** | 60.00% |
| **ROC-AUC** | 83.87% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 32.56% | 87.50% | 47.46% | 65.42% | 59.45% | 80.95% |
| **Intra-Contract** | 97 (29/68) | 48.28% | 96.55% | 64.37% | 80.46% | 58.58% | 83.52% |

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
> Single run: **seed=45**, arm=**secsec** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.4946.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 57.53%, Precision 41.58%, Recall 93.33%, PR-AUC 60.00%, ROC-AUC 83.87%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 34.92% [24.33%, 47.25%]
  - MakerDAO DSS: 68.87% [64.31%, 73.09%]
  - Bancor V3: 53.59% [46.82%, 60.22%]
  - Liquity V1: 36.20% [30.78%, 41.99%]
- **Cross- vs intra-contract (test)**: cross F1 47.46% (recall 87.50%), intra F1 64.37% (recall 96.55%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
