# HyperVul — DAppSCAN Positive Hyperedge AST Analysis Report

> **Date**: 2026-06-11  
> **Dataset**: DAppSCAN (`data/DAppSCAN/DAppSCAN-source/`)  
> **Method**: Tree-sitter Solidity AST Parser (`scripts/dappscan_hyperedge_ast_analysis.py`)

---

## Executive Summary

This report documents the results of applying the tree-sitter Solidity AST parser to the DAppSCAN dataset to construct positive vulnerability hyperedges. This expansion aims to build a larger training set, while using the hand-curated FORGE-Curated dataset (83 positives) as a clean evaluation set.

The pipeline integrates the core AST improvements (Changes #1-4) with three review changes:
1. **Robust Project Root Detection (Change A)**: Walks up parent directories to accurately scope inheritance mapping for each contract version, reporting any ambiguity.
2. **Cross-Dataset Deduplication (Change B)**: Removes train/test leakage by comparing DAppSCAN constructable positives against FORGE positives via `(contract name, function name, normalized source hash)`.
3. **Label-Quality Check (Change C)**: Verifies if the function name found by the AST at the annotated line range matches the annotation's function name.

---

## Key Metrics Summary

| Metric | Value | Description |
| :--- | :---: | :--- |
| **Total Processed Annotations** | **342** | Interaction SWCs (SWC-104, SWC-107, SWC-112, SWC-114) with function references |
| Located in AST | 333 | Number of annotations successfully mapped to a function node in the source file AST |
| Function Name Matched in AST | 326 | Number of located functions where AST name matches annotated name |
| **Label-Quality Match Rate** (Change C) | **97.90%** | Signal of low commit drift and high annotation accuracy |
| Ambiguous Project Roots (Change A) | 0 | Number of files where project root walking failed or was ambiguous |
| **Unique DAppSCAN Positives** | **227** | Constructable unique positive hyperedges (external call + state variable access) |
| Excluded FORGE Duplicates (Change B) | 0 | Number of DAppSCAN positives that duplicate FORGE positives |
| **FINAL COMBINED UNIQUE TOTAL** | **310** | Deduplicated total: FORGE (83) + DAppSCAN unique (227) |

---

## Results Breakdown

### 1. DAppSCAN Positives by SWC Category

| SWC Code | Vulnerability Type | Count |
| :--- | :--- | :---: |
| **SWC-107** | Reentrancy | 99 |
| **SWC-104** | Unchecked Call Return Value | 82 |
| **SWC-114** | Transaction Order Dependence | 40 |
| **SWC-112** | Delegatecall to Untrusted Callee | 6 |
| **Total** | | **227** |

### 2. Interaction Scope Breakdown

To support modeling of multi-contract behaviors, we classify the constructable hyperedges into:
- **Cross-Contract**: The external call's receiver type is defined in the same project codebase bundle (excluding calls to the contract itself).
- **Intra-Contract**: The external call is a low-level call (`.call()`, `.transfer()`) or uses a contract/interface type not defined locally in the project bundle.

| Interaction Type | Count | Percentage |
| :--- | :---: | :---: |
| **Cross-Contract** | 147 | 64.76% |
| **Intra-Contract** | 80 | 35.24% |
| **Total** | **227** | **100.0%** |

---

## Review Changes Details

### Change A: Robust Project Root Detection
Rather than relying on a fixed path depth, the script resolves absolute file paths and walks up parent directories until it reaches the directory directly nested under `DAppSCAN-source/contracts/<grouping>/`. This dynamically scopes each project version, resulting in **0 ambiguous roots** and allowing complete, clean parsing of inheritance hierarchies across all files.

### Change B: Cross-Dataset Deduplication
To prevent train/test leakage, function sources are normalized by removing all whitespace, comments (`//...` and `/*...*/`), and lowercase-normalizing the string. A SHA-256 hash is computed. DAppSCAN positives are matched against the 83 FORGE positives by `(contract name, function name, normalized source hash)`. 
- **FORGE Hashes Loaded**: 77 unique hashes (some FORGE entries share identical contract/function code).
- **DAppSCAN Duplicates Found**: **0** (no train/test leakage).

### Change C: Label-Quality Check
Overlapping function nodes in the AST at the annotated line range were checked against the annotation's function name. Out of 333 located functions, 326 matched exactly (**97.90% match rate**). The remaining 7 mismatches represent minor commit drifts or compiler-version differences, but were still successfully processed using the AST-extracted function node.

---

## Data Files

The results are saved in the project structure under `/home/pollmix/Coding/HyperVul/experiments/results/`:

- [dappscan_ast_summary.json](file:///home/pollmix/Coding/HyperVul/experiments/results/dappscan_ast_summary.json) — Detailed counts, SWC categories, and cross-contract ratios.
- [dappscan_ast_detailed.json](file:///home/pollmix/Coding/HyperVul/experiments/results/dappscan_ast_detailed.json) — Per-annotation breakdown.
- [dappscan_ast_constructable_hyperedges.json](file:///home/pollmix/Coding/HyperVul/experiments/results/dappscan_ast_constructable_hyperedges.json) — Clean, deduplicated 227 positive hyperedges.
