# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_scl_seed44.pt`
> **Arm**: `scl` (SCL=ON, Localization=OFF) · **Seed**: `44`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.1734`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.5648** | **0.1734** | **97.30%** | **7.53%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 24 | 38.10% | [27.12%, 50.44%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 324 | 76.42% | [72.15%, 80.21%] |
| **Bancor V3** | External (DeFi Application) | 209 | 119 | 56.94% | [50.16%, 63.47%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 168 | 60.22% | [54.37%, 65.78%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 42.16% |
| **Recall** | 97.73% |
| **F1-Score** | 58.90% |
| **F2-Score** | 77.34% |
| **PR-AUC** | 65.19% |
| **ROC-AUC** | 86.82% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 30.19% | 100.00% | 46.38% | 68.38% | 62.30% | 87.10% |
| **Intra-Contract** | 90 (28/62) | 55.10% | 96.43% | 70.13% | 83.85% | 66.36% | 87.04% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 23 | 95.65% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 100.00% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=44**, arm=**scl** (SCL=ON, Localization=OFF), K_app=100 (fixed), threshold=0.1734.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 58.90%, Precision 42.16%, Recall 97.73%, PR-AUC 65.19%, ROC-AUC 86.82%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 38.10% [27.12%, 50.44%]
  - MakerDAO DSS: 76.42% [72.15%, 80.21%]
  - Bancor V3: 56.94% [50.16%, 63.47%]
  - Liquity V1: 60.22% [54.37%, 65.78%]
- **Cross- vs intra-contract (test)**: cross F1 46.38% (recall 100.00%), intra F1 70.13% (recall 96.43%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
