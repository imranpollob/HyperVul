# Hyperedge-Based Vulnerability Detection in Solidity Smart Contracts: Final Evaluation Data

## 1. Abstract
Deep learning-based smart contract vulnerability detectors frequently suffer from poor generalization and low precision when deployed on out-of-distribution (OOD) production-grade codebases. These issues stem from a combination of: (1) over-simplistic representation of smart contracts as sequential tokens or flattened graphs, which fails to capture external helper and multi-contract interactions; (2) severe class imbalance in real-world deployment; and (3) a critical "compilation-coverage gap" where standard static analysis tools fail to analyze more than 80% of real-world contracts due to unbundled npm/hardhat dependencies and compiler state errors.

In this work, we present **HyperVul**, a framework that models multi-contract interactions as hyperedges over a program dependency graph (PDG) and integrates symbolic safety invariants directly into node features. We address class imbalance via Asymmetric Loss (ASL) and calibrate predictions using Supervised Contrastive Learning (SCL). Furthermore, we model sequence order in execution steps using a sequence-aware LSTM encoder. 

We evaluate HyperVul on a project-disjoint split of curated DeFi contracts and real-world audits. In head-to-head comparison on the compilable subset of the test split, HyperVul achieves a **95.00% recall** and **41.55% precision**, significantly outperforming Slither's **62.50% recall** and **35.71% precision**. On the full test set, standard analyzers achieve only **11.11% recall** due to compilation failures, while HyperVul maintains **96.40% recall**, demonstrating high resilience to real-world deployment constraints.

---

## 2. Technical Contributions
1.  **Interaction-Level Hypergraph Representation:** Restructures contracts into shared hypergraphs connecting interactions, 1-hop state-mutating helper functions, and call/data edges, propagated via over-smoothing-resistant APPNP.
2.  **Sequence-Aware Interaction Encoder:** Replaces permutation-invariant attention pooling with a sequence-aware LSTM/Transformer encoder to preserve execution event ordering.
3.  **Security-Context Symbolic Features:** Projections of safety invariants (modifiers, reentrancy guards) directly into node embeddings.
4.  **Asymmetric Loss (ASL):** Handles the extreme 1:40 class imbalance of production-grade smart contracts.

---

## 3. Evaluation Tables

### Table I: Main Performance Comparison
*This table compares HyperVul against standard static analyzers on (a) the full test set (176 items: 45 positives, 131 negatives), representing the operational reality where compilation fails, and (b) the compilable subset (35 items: 8 positives, 27 negatives), providing a fair head-to-head comparison where compilation succeeds.*

#### A. Full Test Set Performance (Operational Reality)
| Method | Recall | Precision | F1-Score | F2-Score | PR-AUC | ROC-AUC | Compilation Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Static Analyzers** | | | | | | | |
| Slither (Global) | 11.11% | 35.71% | 16.95% | 12.89% | — | — | 19.35% (6/31) |
| **Hyperedge Ablations (Ours)** | | | | | | | |
| Sym:none (No Symbolic Features) | 93.80% ± 1.9% | 36.90% ± 2.9% | 52.90% ± 3.0% | 71.60% ± 2.3% | 53.20% ± 2.8% | 82.10% ± 1.7% | **100.00%** |
| Sym:security (Partial Symbolic) | 95.60% ± 1.6% | 37.80% ± 2.8% | 54.10% ± 2.7% | 73.10% ± 2.0% | 60.40% ± 6.3% | 84.30% ± 2.5% | **100.00%** |
| **HyperVul (Ours, Sym:full)** | **96.40% ± 1.2%** | **39.40% ± 1.8%** | **55.90% ± 1.8%** | **74.70% ± 1.3%** | **60.50% ± 6.2%** | **84.20% ± 2.4%** | **100.00%** |

#### B. Head-to-Head Comparison on Compilable Subset (35 items)
| Method | Recall | Precision | F1-Score |
| :--- | :---: | :---: | :---: |
| Slither | 62.50% | 35.71% | 45.45% |
| **HyperVul (Ours, Sym:full)** | **95.00% ± 10.0%** | **41.55% ± 9.0%** | **56.64% ± 7.6%** |

---

### Table II: Dataset Characterization and Split Statistics
*This table details the project-disjoint splits constructed using Union-Find to verify leakage controls and split integrity.*

| Metric / Attribute | Train | Validation | Test | Total |
| :--- | :---: | :---: | :---: | :---: |
| **Unique Projects/Audits** | 184 | 31 | 33 | 248 |
| **Solidity Contracts** | 1,583 | 159 | 138 | 1,880 |
| **Vulnerable Hyperedges (Positives)** | 219 | 38 | 41 | 298 |
| **Clean Hyperedges (Negatives)** | 10,263 | 793 | 732 | 11,788 |
| **Helper Nodes (State-Mutating)** | 1,480 | 140 | 170 | 1,790 |
| **Cross-Contract Interactions** | 50.0% | 50.0% | 38.8% | 47.4% |
| **Class Imbalance (Pos:Neg)** | ~1:47 | ~1:21 | ~1:18 | ~1:40 |

---

### Table III: Per-Vulnerability Category Detection Performance (Seed 42)
*This table breaks down recall and precision across specific SWC categories, demonstrating HyperVul's strengths on relational vulnerability types compared to Slither on the full test set.*

| SWC Class | Metric | Slither | HyperVul (Ours) |
| :--- | :---: | :---: | :---: |
| **SWC-107 (Reentrancy)** | Recall | 21.74% (5/23) | **86.96% (20/23)** |
| *(count = 23)* | Precision | 35.71% | **51.90%** |
| **SWC-114 (Front-running)**| Recall | 0.00% (0/15) | **100.00% (15/15)** |
| *(count = 15)* | Precision | 0.00% | **51.90%** |
| **SWC-104 (Unchecked Call)**| Recall | 0.00% (0/6) | **100.00% (6/6)** |
| *(count = 6)* | Precision | 0.00% | **51.90%** |

---

### Table IV: Cross-Contract vs. Intra-Contract Generalization (Seed 42)
*This table evaluates performance on vulnerabilities that remain within a single contract versus those that traverse external interfaces.*

| Evaluation Regime | Metric | Slither | HyperVul (Ours) |
| :--- | :--- | :---: | :---: |
| **Intra-Contract** | F1-Score | 26.32% (5/28) | **72.97%** |
| *(Local Calls)* | PR-AUC | — | **74.80%** |
| **Cross-Contract** | F1-Score | 0.00% (0/16) | **57.14%** |
| *(Cross-Interface Calls)*| PR-AUC | — | **62.03%** |
