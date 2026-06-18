# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secfull_seed42.pt`
> **Arm**: `secfull` (SCL=OFF, Localization=OFF) · **Seed**: `42`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.3154`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.5821** | **0.3154** | **97.30%** | **3.23%** |

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
| **MakerDAO DSS** | External (DeFi Application) | 424 | 248 | 58.49% | [53.74%, 63.08%] |
| **Bancor V3** | External (DeFi Application) | 209 | 73 | 34.93% | [28.79%, 41.61%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 92 | 32.97% | [27.72%, 38.69%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 51.85% |
| **Recall** | 95.45% |
| **F1-Score** | 67.20% |
| **F2-Score** | 81.71% |
| **PR-AUC** | 71.64% |
| **ROC-AUC** | 89.07% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 41.67% | 93.75% | 57.69% | 75.00% | 64.27% | 87.50% |
| **Intra-Contract** | 90 (28/62) | 60.00% | 96.43% | 73.97% | 85.99% | 78.28% | 90.38% |

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
> Single run: **seed=42**, arm=**secfull** (SCL=OFF, Localization=OFF), K_app=100 (fixed), threshold=0.3154.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 67.20%, Precision 51.85%, Recall 95.45%, PR-AUC 71.64%, ROC-AUC 89.07%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 23.81% [14.99%, 35.64%]
  - MakerDAO DSS: 58.49% [53.74%, 63.08%]
  - Bancor V3: 34.93% [28.79%, 41.61%]
  - Liquity V1: 32.97% [27.72%, 38.69%]
- **Cross- vs intra-contract (test)**: cross F1 57.69% (recall 93.75%), intra F1 73.97% (recall 96.43%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
