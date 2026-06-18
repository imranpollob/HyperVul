# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secfull_seed46.pt`
> **Arm**: `secfull` (SCL=OFF, Localization=OFF) · **Seed**: `46`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.1842`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.5764** | **0.1842** | **97.30%** | **3.23%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 10 | 15.87% | [8.86%, 26.81%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 261 | 61.56% | [56.84%, 66.06%] |
| **Bancor V3** | External (DeFi Application) | 209 | 83 | 39.71% | [33.32%, 46.47%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 93 | 33.33% | [28.06%, 39.06%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 49.43% |
| **Recall** | 97.73% |
| **F1-Score** | 65.65% |
| **F2-Score** | 81.75% |
| **PR-AUC** | 67.11% |
| **ROC-AUC** | 87.35% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 39.02% | 100.00% | 56.14% | 76.19% | 66.90% | 87.60% |
| **Intra-Contract** | 90 (28/62) | 58.70% | 96.43% | 72.97% | 85.44% | 67.94% | 86.69% |

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
> Single run: **seed=46**, arm=**secfull** (SCL=OFF, Localization=OFF), K_app=100 (fixed), threshold=0.1842.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 65.65%, Precision 49.43%, Recall 97.73%, PR-AUC 67.11%, ROC-AUC 87.35%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 15.87% [8.86%, 26.81%]
  - MakerDAO DSS: 61.56% [56.84%, 66.06%]
  - Bancor V3: 39.71% [33.32%, 46.47%]
  - Liquity V1: 33.33% [28.06%, 39.06%]
- **Cross- vs intra-contract (test)**: cross F1 56.14% (recall 100.00%), intra F1 72.97% (recall 96.43%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
