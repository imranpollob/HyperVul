# HyperVul — Iteration 1 Simple Attention Classifier Results

> **Model Checkpoint**: [iteration1_checkpoint.pt](file:///home/pollmix/Coding/HyperVul/model/iteration1_checkpoint.pt)  
> **Chosen Decision Threshold**: `0.2015` (Tuned on validation to achieve $\ge 95\%$ recall)  
> **Validation Recall**: `97.30%` (Validation positives: 38)

---

## Executive Summary
This report presents the performance metrics of Iteration 1, a deliberately simple model that utilizes attention-weighted pooling over frozen SmartBERT-v3 embeddings without multi-layer message passing. The model was trained on the augmented train split, tuned on the validation split, and evaluated on the untouched test split and OpenZeppelin clean negatives.

---

## 1. Overall Test Performance (at Tuned Validation Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 48 positives, 121 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 47.19% |
| **Recall** | 87.50% |
| **F1-Score** | 61.31% |
| **PR-AUC** | 63.02% |
| **ROC-AUC** | 80.54% |

---

## 2. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (19/60) | 35.71% | 78.95% | 49.18% | 60.49% | 75.18% |
| **Intra-Contract** | 90 (29/61) | 57.45% | 93.10% | 71.05% | 63.65% | 83.44% |

---

## 3. Generalization & False-Positive Rate (OpenZeppelin Clean Negatives)
We evaluated the model on the 600 clean OpenZeppelin negatives (representing real, complex clean production code the model never trained on) to assess generalization and false-alarm rate.

* **FPR on OZ Set**: **36.67%** (Classified **220** out of 600 clean items as vulnerable).

---

## 4. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 23 | 91.30% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 10 | 60.00% |
| Delegatecall (SWC-112) | 0 | 0.00% |

---

## 5. Summary and Architectural Next Steps
* **Core Takeaways**: The simple attention pooling on top of the frozen SmartBERT-v3 embeddings represents a strong baseline.
* **Identified Gaps**: Cross-contract vs. intra-contract divergence highlights the need for explicit relational information. This justifies progressing to G-HAN (Heterogeneous Attention Network) in Iteration 2 to perform message passing across contract boundaries.
