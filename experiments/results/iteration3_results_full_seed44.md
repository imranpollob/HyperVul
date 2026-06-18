# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_full_seed44.pt`
> **Arm**: `full` (SCL=ON, Localization=ON) · **Seed**: `44`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.1820`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.5244** | **0.1820** | **97.30%** | **3.23%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 22 | 34.92% | [24.33%, 47.25%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 253 | 59.67% | [54.93%, 64.23%] |
| **Bancor V3** | External (DeFi Application) | 209 | 69 | 33.01% | [27.00%, 39.65%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 72 | 25.81% | [21.02%, 31.25%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 52.56% |
| **Recall** | 93.18% |
| **F1-Score** | 67.21% |
| **F2-Score** | 80.71% |
| **PR-AUC** | 66.63% |
| **ROC-AUC** | 87.20% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 43.75% | 87.50% | 58.33% | 72.92% | 64.90% | 87.50% |
| **Intra-Contract** | 90 (28/62) | 58.70% | 96.43% | 72.97% | 85.44% | 66.98% | 85.83% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 23 | 86.96% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 100.00% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=44**, arm=**full** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.1820.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 67.21%, Precision 52.56%, Recall 93.18%, PR-AUC 66.63%, ROC-AUC 87.20%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 34.92% [24.33%, 47.25%]
  - MakerDAO DSS: 59.67% [54.93%, 64.23%]
  - Bancor V3: 33.01% [27.00%, 39.65%]
  - Liquity V1: 25.81% [21.02%, 31.25%]
- **Cross- vs intra-contract (test)**: cross F1 58.33% (recall 87.50%), intra F1 72.97% (recall 96.43%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
