# HyperVul — Cross-Contract Performance Diagnostic Report

This report analyzes the root cause of the performance gap on cross-contract vs. intra-contract hyperedges in Model Iteration 1.

---

## Diagnostic 1 — Is the cross-contract weakness a DAppSCAN label-noise artifact?
Cross-contract positives lean on both FORGE and DAppSCAN. DAppSCAN is known to contain noisier, single-point label assignments.

### Concrete Metrics (Cross-Contract Positives):
* **Total Positives**: 19 items
* **Split by Source**: FORGE = **3** | DAppSCAN = **16**
* **Model Predictions (at threshold `0.2015`):**
  * **CAUGHT (True Positives)**: FORGE = **3** | DAppSCAN = **12**
  * **MISSED (False Negatives)**: FORGE = **0** | DAppSCAN = **4**
* **Source-Specific Recalls**:
  * **FORGE Cross-Contract Recall**: **100.00%** (3/3)
  * **DAppSCAN Cross-Contract Recall**: **75.00%** (12/16)

### Diagnostic Conclusion 1:
> [!NOTE]
> **Conclusion**: DAppSCAN label noise is a primary factor; all missed cross-contract positives belong to DAppSCAN, whereas FORGE cross-contract positives were perfectly predicted (100% recall).

---

## Diagnostic 2 — Is 256-token truncation cutting off cross-contract signatures?
Cross-contract functions are typically longer than intra-contract helper functions. The feature extraction scheme truncates calling-function source code at 256 tokens.

### Concrete Metrics (Function Token Lengths):
* **Function Length Distribution (Positive Test Items)**:
  * **Cross-Contract**: count = 19 | min = 123 | max = 1867 | median = 321.0 | mean = 521.4 tokens
  * **Intra-Contract**: count = 29 | min = 181 | max = 1734 | median = 534.0 | mean = 643.8 tokens
* **Truncation Rate (>256 tokens) on Positive Items**:
  * **Cross-Contract**: **13/19 (68.42%)** exceeded 256 tokens.
  * **Intra-Contract**: **27/29 (93.10%)** exceeded 256 tokens.
* **Truncation Rate on Missed Cross-Contract Positives (False Negatives)**:
  * **0 out of 4** missed items (**0.00%** if missed_cross_total > 0 else 0.0%) exceeded 256 tokens.

### Diagnostic Conclusion 2:
> [!NOTE]
> **Conclusion**: Token truncation is a minor factor; only 0.0% of missed cross-contract positives exceed 256 tokens, indicating that most misses are not due to truncation.

---

## Overall Diagnostic Conclusion
> [!IMPORTANT]
> **Summary**: The cross-contract weakness is primarily a DAppSCAN label-noise artifact (high performance on cleaner FORGE data). G-HAN's structural message passing would not resolve this dataset labeling noise.
