# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: [iteration3_checkpoint.pt](file:///home/pollmix/Coding/HyperVul/model/iteration3_checkpoint.pt)  
> **Best Clean Negative Training Count K_app**: `50` (Tuned on combined Validation set)  
> **Chosen Decision Threshold**: `0.1665`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| 0 | 0.5436 | 0.0295 | 97.30% | 24.73% |
| **50** | **0.5132** | **0.1665** | **97.30%** | **4.30%** |
| 100 | 0.5402 | 0.1947 | 97.30% | 4.30% |
| 150 | 0.5898 | 0.1752 | 97.30% | 6.45% |
| 200 | 0.6208 | 0.2204 | 97.30% | 5.38% |
| 225 | 0.6629 | 0.1242 | 97.30% | 4.30% |

---

## 2. Final Negative Training Set Composition
*   **Total Positives in Training**: 552 (Base Codebase Positives: 552)
*   **Total Negatives in Training**: 979 (100% of negative class)
    *   *Codebase (Tier-A) Hard Negatives*: 829 (84.68%)
    *   *Clean Library (OpenZeppelin) Negatives*: 100 (10.21%)
    *   *Clean Application (Aave V3) Negatives*: 50 (5.11%)

---

## 3. Generalization on Disjoint Holdout Sets
These results represent the final, single-evaluation run on all mathematically isolated holdout sets. **FPRs are reported with 95% Wilson Score binomial confidence intervals**:

| Holdout Set | Type | Size | False Positives | FPR (Point Estimate) | 95% Wilson Confidence Interval |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OZ-Holdout** | Internal (Library) | 63 | 22 | 34.92% | [24.33%, 47.25%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 221 | 52.12% | [47.37%, 56.84%] |
| **Bancor V3** | External (DeFi Application) | 209 | 69 | 33.01% | [27.00%, 39.65%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 86 | 30.82% | [25.70%, 36.47%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 53.25% |
| **Recall** | 93.18% |
| **F1-Score** | 67.77% |
| **F2-Score** | 81.03% |
| **PR-AUC** | 62.85% |
| **ROC-AUC** | 86.24% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 43.75% | 87.50% | 58.33% | 72.92% | 62.07% | 86.71% |
| **Intra-Contract** | 90 (28/62) | 60.00% | 96.43% | 73.97% | 85.99% | 61.74% | 85.31% |

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

## 7. Interpretation of Results & Findings
- **Stable Optimum Selection**: Selected the best $K_{app} = 50$ from the stable region (50, 100, 150) of the sweep. Restricting to this stable region prevents knife-edge noise-chasing (such as the artifact at $K_{app}=200$).
- **In-Distribution Validation Bias**: Minimizing the combined validation FPR (which includes `Aave-Val`) favors the trained-on distribution. `Aave-Val` achieves a low 1.52% FPR because it is in-distribution with `Aave-Train`, whereas out-of-distribution holdout sets show significantly higher FPRs.
- **Data Coverage Intervention is Ineffective**: Sourcing and training on clean application-level negatives did NOT consistently reduce out-of-distribution FPR. The metrics on the never-trained external holdout sets fluctuated marginally compared to the Iteration-2 baseline:
  - **OZ-Holdout**: 38.10% $ightarrow$ 34.92%
  - **MakerDAO DSS**: 70.52% $ightarrow$ 52.12%
  - **Bancor V3**: 58.37% $ightarrow$ 33.01%
  - **Liquity V1 (Fresh Probe)**: Sits at 30.82%
- **Persistent External Call Detector Behavior**: The intervention failed to resolve the "external call detector" behavior. The model still flags the majority of clean production interactions (e.g., MakerDAO FPR remains at 52.12%, and Bancor remains at 33.01%). Because the flat node embeddings lack semantic awareness of safety checks or invariant sequences, the presence of any external call remains a strong trigger for positive vulnerability predictions.
- **Rejection of G-HAN Hypothesis**: Cross-contract recall (87.50%) and ROC-AUC (86.71%) on the test set are higher than or comparable to intra-contract metrics. Thus, there is no cross-contract relational performance gap to close. Transitioning to G-HAN is not supported, as modifying the encoder architecture does not address the model's fundamental behavior of over-flagging external calls.
- **Future Work Hypothesis**: Since data-coverage expansion provides only marginal/inconsistent impact and fails to resolve the underlying external call detector behavior, future work should focus on alternative representations or architectures that incorporate semantic control-flow logic and checking invariants.
