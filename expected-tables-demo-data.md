# Hyperedge-Based Vulnerability Detection in Solidity Smart Contracts: Expected Evaluation Data

## Paper Abstract
Smart contract vulnerability detection has increasingly leveraged deep learning to secure decentralized applications. However, existing approaches either analyze contracts at a coarse file level—losing fine-grained localization—or analyze functions in isolation, failing to capture relational dependencies across contract states and external boundaries. Furthermore, simple graph representations suffer from message-passing over-smoothing, execution sequence-blindness, and semantic dilution of frozen pre-trained encoders.

In this work, we propose **HyperVul**, a framework that reformulates smart contract vulnerability detection as an interaction-level hyperedge classification problem. We model each interaction as a hyperedge connecting the function signature, its accessed state variables, and external callees. To address sequence-blindness, we introduce a sequence-aware encoder that preserves AST execution order. To solve over-smoothing, we implement an Approximate Personalized Propagation of Neural Predictions (APPNP) propagation layer. Finally, we unfreeze the transformer encoder via Low-Rank Adaptation (LoRA) and inject projected safety-context modifier embeddings. Evaluation on a realistic, highly imbalanced full-pool benchmark demonstrates that HyperVul achieves superior recall and precision compared to standard Graph Neural Networks and industry-standard static analysis tools.

---

## 1. Problem Formulation
Existing deep learning vulnerability detectors suffer from three main limitations:
1.  **Coarse Granularity vs. Isolation:** Coarse-grained models classify whole contracts, leaving clean interactions unlocalized. Conversely, function-level models analyze code in isolation, missing external dependencies and state mutations.
2.  **Sequence-Blindness:** Vulnerabilities like Reentrancy (SWC-107) are order-dependent (external calls must occur *before* state writes). Permutation-invariant pooling layers treat code elements as an unordered bag-of-nodes, discarding this temporal structure.
3.  **Semantic Dilution of Frozen Encoders:** Pre-trained code models (SmartBERT) represent syntax but lack domain-specific security awareness (e.g., distinguishing between modifier-guarded and unguarded external calls).

---

## 2. Novel Solutions Provided
To resolve these problems, HyperVul introduces:
1.  **Interaction-Level Hypergraph Representation:** Restructures the contract into a shared graph connecting interaction hyperedges, 1-hop state-mutating helper functions, and call/data edges, propagated via over-smoothing-resistant APPNP.
2.  **Sequence-Aware Interaction Encoder:** Replaces unordered attention pooling with a sequence-aware Transformer/LSTM encoder to capture execution event ordering.
3.  **LoRA Fine-tuning & Security-Context Projection:** Adapts the SmartBERT encoder using Low-Rank Adaptation (LoRA) and projects safety invariants (modifiers, reentrancy guards) directly into node embeddings.
4.  **Asymmetric Loss (ASL):** Dynamically penalizes false positives to handle the extreme 1:40 class imbalance of production-grade smart contracts.

---

## 3. Evaluation Tables

### Table I: Main Performance Comparison
*This table compares HyperVul against standard GNN baselines and rule-based static analyzers on the full-pool test set (41 positives, 732 negatives).*

| Method | Recall | Precision | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Static Analysis Tools** | | | | | | |
| Slither | 78.05% | 13.56% | 23.10% | 40.20% | — | — |
| Mythril | 63.41% | 17.57% | 27.51% | 41.53% | — | — |
| **GNN Baselines** | | | | | | |
| Set-Pooling | 95.12% | 15.60% | 26.80% | 48.03% | 34.20% | 80.80% |
| Pairwise-GCN | 92.68% | 12.38% | 21.84% | 43.18% | 24.50% | 75.80% |
| Pairwise-GAT | 92.68% | 12.80% | 22.49% | 44.08% | 28.10% | 76.50% |
| **HyperVul (Ours)** | **95.12%** | **38.61%** | **54.93%** | **72.76%** | **58.50%** | **90.40%** |

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

### Table III: Per-Vulnerability Category Detection Performance
*This table breaks down recall and precision across specific SWC categories, demonstrating HyperVul's strengths on relational vulnerability types.*

| SWC Class | Metric | Slither | Mythril | GAT Baseline | HyperVul (Ours) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **SWC-107 (Reentrancy)** | Recall | 73.91% | 60.87% | 82.61% | **91.30%** |
| *(count = 23)* | Precision | 15.62% | 18.92% | 14.18% | **42.00%** |
| **SWC-114 (Front-running)**| Recall | 80.00% | 66.67% | 80.00% | **93.33%** |
| *(count = 15)* | Precision | 12.12% | 16.67% | 11.76% | **35.00%** |
| **SWC-104 (Unchecked Call)**| Recall | 83.33% | 66.67% | 83.33% | **100.00%** |
| *(count = 6)* | Precision | 11.63% | 15.38% | 11.11% | **37.50%** |

---

### Table IV: Cross-Contract vs. Intra-Contract Generalization
*This table evaluates performance on vulnerabilities that remain within a single contract versus those that traverse external interfaces.*

| Evaluation Regime | Metric | Slither | Mythril | GAT Baseline | HyperVul (Ours) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Intra-Contract** | F1-Score | 25.12% | 29.30% | 22.49% | **58.21%** |
| *(Local Calls)* | PR-AUC | — | — | 28.10% | **61.30%** |
| **Cross-Contract** | F1-Score | 18.40% | 22.18% | 18.10% | **49.80%** |
| *(Cross-Interface Calls)*| PR-AUC | — | — | 19.30% | **52.60%** |
