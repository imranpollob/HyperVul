# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secnone_seed43.pt`
> **Arm**: `secnone` (SCL=ON, Localization=ON) · **Seed**: `43`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.4477`  
> **Validation Recall**: `97.37%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.1191** | **0.4477** | **97.37%** | **17.20%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 31 | 49.21% | [37.27%, 61.24%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 340 | 80.19% | [76.13%, 83.70%] |
| **Bancor V3** | External (DeFi Application) | 209 | 126 | 60.29% | [53.53%, 66.68%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 178 | 63.80% | [58.01%, 69.22%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (176 items: 45 positives, 131 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 34.40% |
| **Recall** | 95.56% |
| **F1-Score** | 50.59% |
| **F2-Score** | 70.49% |
| **PR-AUC** | 56.99% |
| **ROC-AUC** | 83.38% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 24.56% | 87.50% | 38.36% | 57.85% | 62.53% | 81.15% |
| **Intra-Contract** | 97 (29/68) | 42.65% | 100.00% | 59.79% | 78.80% | 52.04% | 83.22% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 24 | 95.83% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 83.33% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=43**, arm=**secnone** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.4477.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 50.59%, Precision 34.40%, Recall 95.56%, PR-AUC 56.99%, ROC-AUC 83.38%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 49.21% [37.27%, 61.24%]
  - MakerDAO DSS: 80.19% [76.13%, 83.70%]
  - Bancor V3: 60.29% [53.53%, 66.68%]
  - Liquity V1: 63.80% [58.01%, 69.22%]
- **Cross- vs intra-contract (test)**: cross F1 38.36% (recall 87.50%), intra F1 59.79% (recall 100.00%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
