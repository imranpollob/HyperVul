# HyperVul — Dataset Splitting and Stratification Report

> **Date**: 2026-06-11  
> **Target Splits**: ~70% Train / ~15% Val / ~15% Test (by positive count)  
> **Leakage Prevention**: Project-level grouping and shared hash connected-components

---

## Executive Summary
This report documents the split of the HyperVul smart contract vulnerability dataset (310 positives and 930 codebase negatives) into Train, Validation, and Test sets. To satisfy **CRITICAL SPLITTING RULE 1** (zero leakage), splits were generated at the project-group level using Union-Find on project IDs and shared normalized source hashes. 

To satisfy **FIX 3**, we softened the search optimization: rather than cherry-picking a globally optimal extreme partition, we filtered partitions to those satisfying all **HARD** constraints (correct size, correct FORGE counts, zero leakage) and selected a representative partition.

---

## Split Metrics & Source Balance

| Split | Positives Count | Negatives Count | Pos/Neg Ratio | FORGE Pos | DAppSCAN Pos |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Train** | 223 (71.9%) | 651 (70.0%) | 223:651 (1:2.92) | 49 | 174 |
| **Val** | 38 (12.3%) | 152 (16.3%) | 38:152 (1:4.00) | 10 | 28 |
| **Test** | 49 (15.8%) | 127 (13.7%) | 49:127 (1:2.59) | 24 | 25 |

### Clean Evaluation Set Biasing (FIX 2 & FIX 3)
*   **ACTUAL FORGE-positives-in-test Count Achieved**: **24** (out of 83 total FORGE positives).
*   This represents **28.9%** of the high-confidence FORGE clean evaluation set biased specifically into the Test split, ensuring robust post-training generalization evaluation.

---

## Stratification Analysis

### 1. Cross-Contract Ratio (FIX 1 Confirmed Definition)
The cross-contract ratio for both positives and negatives was recomputed using the confirmed definition (checking if the callee resolves to another contract in the bundle). The global positive cross-contract ratio is verified at exactly **50.00%** (155/310), and the global negative ratio is verified at **50.00%** (465/930).

*   **Train Cross-Contract Ratio**:
    *   Positives: **52.91%**
    *   Negatives: **49.77%**
*   **Val Cross-Contract Ratio**:
    *   Positives: **47.37%**
    *   Negatives: **50.66%**
*   **Test Cross-Contract Ratio**:
    *   Positives: **38.78%**
    *   Negatives: **50.39%**

### 2. Vulnerability Type Distribution

| Vulnerability Type | Train Count (%) | Val Count (%) | Test Count (%) | Global Count (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Reentrancy (SWC-107)** | 110 (49.3%) | 21 (55.3%) | 24 (49.0%) | 155 (50.0%) |
| **Unchecked Call Return (SWC-104)** | 60 (26.9%) | 12 (31.6%) | 10 (20.4%) | 82 (26.5%) |
| **Front-running / Tx Order (SWC-114)** | 47 (21.1%) | 5 (13.2%) | 15 (30.6%) | 67 (21.6%) |
| **Delegatecall (SWC-112)** | 6 (2.7%) | 0 (0.0%) | 0 (0.0%) | 6 (1.9%) |

---

## Leakage Verification Checks

We ran rigorous leakage tests on the generated splits:

1.  **Project Overlap Check**:
    *   **Result**: **0** violations.
    *   *Explanation*: Checked that no project ID (`vfp_id` or DAppSCAN `project_root`) is shared across different splits.
2.  **Normalized Source Hash Collision Check**:
    *   **Result**: **0** violations.
    *   *Explanation*: Checked that no `normalized_source_hash` of a function is shared between splits, ensuring no near-identical code leakages exist.

---

## Data Split Files
*   [train.json](file:///home/pollmix/Coding/HyperVul/data/splits/train.json) — Train split (positives and negatives).
*   [val.json](file:///home/pollmix/Coding/HyperVul/data/splits/val.json) — Validation split (positives and negatives).
*   [test.json](file:///home/pollmix/Coding/HyperVul/data/splits/test.json) — Test split (positives and negatives).
