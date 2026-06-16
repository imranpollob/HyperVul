# HyperVul — Iteration 2 Retrained Classifier Results

> **Model Checkpoint**: [iteration2_checkpoint.pt](file:///home/pollmix/Coding/HyperVul/model/iteration2_checkpoint.pt)  
> **Best Clean Negative Training Count K**: `100` (Re-selected from the stable region [80, 100, 120] to avoid small-val noise artifacts)  
> **Chosen Decision Threshold**: `0.1024`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative OpenZeppelin contracts added to training:

| K (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | OZ-Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| 0 | 0.4919 | 0.2015 | 97.30% | 18.52% |
| 20 | 0.5343 | 0.2610 | 97.30% | 22.22% |
| 40 | 0.4812 | 0.1431 | 97.30% | 18.52% |
| 60 | 0.5300 | 0.0679 | 97.30% | 25.93% |
| 80 | 0.5425 | 0.1379 | 97.30% | 14.81% |
| **100** | **0.5321** | **0.1024** | **97.30%** | **14.81%** |
| 120 | 0.5824 | 0.2057 | 97.30% | 14.81% |
| 140 | 0.6001 | 0.2925 | 97.30% | 3.70% |
| 160 | 0.5523 | 0.1215 | 97.30% | 14.81% |

---

## 2. FPR Gap & Generalization on Disjoint Holdout Sets
These results represent the final, single-evaluation run on the mathematically isolated holdout sets. **FPRs are reported with 95% Wilson Score binomial confidence intervals**:

| Holdout Set | Type | Size | False Positives | FPR (Point Estimate) | 95% Wilson Confidence Interval |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OZ-Holdout** | Internal (Library) | 63 | 24 | 38.10% | [27.12%, 50.44%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 299 | 70.52% | [66.01%, 74.66%] |
| **Bancor V3** | External (DeFi Application) | 209 | 122 | 58.37% | [51.60%, 64.85%] |

---

## 3. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 43.62% |
| **Recall** | 93.18% |
| **F1-Score** | 59.42% |
| **F2-Score** | 75.93% |
| **PR-AUC** | 61.88% |
| **ROC-AUC** | 85.00% |

---

## 4. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 31.25% | 93.75% | 46.88% | 66.96% | 66.38% | 86.71% |
| **Intra-Contract** | 90 (28/62) | 56.52% | 92.86% | 70.27% | 82.28% | 61.01% | 84.50% |

---

## 5. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 23 | 86.96% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 100.00% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 6. Interpretation of Results & Findings
- **Stable Optimum Selection**: Sourced the final model from the stable validation region ($K = 100$). The $K = 140$ drop in validation FPR to 3.70% (1 FP out of 27 items) was a small-sample noise artifact (knife-edge threshold risk) that vanished at $K = 160$.
- **The Honest Generalization Story**: The point-estimate FPR on internal library code is high (38.10%), but it fails entirely to generalize to external DeFi applications, exhibiting an FPR of 70.52% on MakerDAO DSS and 58.37% on Bancor V3. The confidence intervals are non-overlapping, confirming a significant performance drop.
- **Clean Negatives Addition Did Not Reduce FPR**: The intervention of adding clean library-grade negatives to the training set did not successfully reduce the false positive rate in-distribution (OZ-Val remained at 14.81% across the stable region, and OZ-Holdout FPR was high at 38.10%) or out-of-distribution (where it remains above 58%). This suggests that clean-negative addition on library code does not offer an in-distribution or out-of-distribution FPR fix.
- **External Call Detector Behavior**: The low cross-contract test precision of 31.25% and the high external FPR on DeFi applications (70.52% on MakerDAO DSS and 58.37% on Bancor V3) are the same phenomenon. Because the model relies on local node features without understanding safety invariants (such as the presence of reentrancy guards or check-effects-interactions order), the presence of any interaction with an external callee triggers a positive prediction regardless of whether it is safe or vulnerable.
- **Rejection of G-HAN Hypothesis**: Cross-contract recall (93.75%) and ROC-AUC (86.71%) on the test set are higher than or comparable to intra-contract metrics. Thus, there is no cross-contract relational performance gap to close. Transitioning to G-HAN is not supported by this data, as changing the encoder architecture does not address the fundamental behavior of the model over-flagging external calls.
- **Future Work Hypothesis**: Addressing this false-positive rate may require a training-data-coverage intervention (e.g., training on clean, production-grade DeFi application-level interaction negatives), but this remains a hypothesis for future work.
