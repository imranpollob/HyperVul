# HyperVul — Representation Comparison: Consolidated Findings

All experiments: identical data (base + 100 OZ + 100 Aave), identical config
(hidden=256, dropout=0.3, lr=1e-3, 2 layers), identical threshold rule (highest thr
with ≥95% val recall), 5 seeds (42–46), test = 169 interactions (44 pos). Harness:
[model/run_representation_comparison.py](../../model/run_representation_comparison.py).
Set-pool reproduces the deployed full model (F1 63.2 ≈ validated 63.08) → harness trusted.

## Experiment 1 — Full SmartBERT function embeddings (current features)
| model | F1 | PR-AUC | ROC-AUC | cross-F1 | intra-F1 |
| :-- | :--: | :--: | :--: | :--: | :--: |
| **set-pool (no edges)** | **63.2±1.2** | 66.0±1.3 | 87.4±0.9 | **52.6±0.8** | **71.4±2.3** |
| pairwise-gcn (clique) | 62.7±2.6 | 65.7±4.7 | 88.0±1.2 | 51.4±3.3 | 71.1±2.4 |
| pairwise-gat (clique) | 60.5±4.8 | 67.5±6.0 | 89.1±1.3 | 51.2±6.2 | 67.7±3.7 |
| hypergraph (ours) | 58.5±3.0 | 65.6±5.1 | 87.6±0.8 | 48.0±2.4 | 67.0±3.5 |

→ **Structure is redundant.** No structural model beats the structure-free set-pool; all
are within noise. Cause: each function node = SmartBERT embedding of the full function
source, which already textually contains the call/state info.

## Experiment 2 — Atomic features (function node dropped; only state + callee nodes)
Fair unified skeleton (`src/models/gnn_zoo.py`): in_proj → L×[conv+residual+LayerNorm] →
attention-pool members → MLP. Only the conv operator differs (GCNConv / GATConv on the
clique graph; PyG HypergraphConv on the incidence). No skip shortcuts.

| model | F1 | PR-AUC | ROC-AUC | cross-F1 | intra-F1 |
| :-- | :--: | :--: | :--: | :--: | :--: |
| set-pool (no edges) | 44.3±3.1 | 51.2±4.4 | 71.0±2.9 | 35.5±3.6 | 51.7±3.0 |
| **pairwise-gcn (clique)** | **55.2±4.8** | 54.3±4.2 | **80.6±1.0** | **48.7±7.0** | **60.4±4.7** |
| pairwise-gat (clique) | 52.5±2.7 | 57.9±10.4 | 80.5±3.4 | 45.0±5.7 | 58.8±1.7 |
| hypergraph (ours) | 50.4±2.5 | 52.6±3.2 | 76.4±1.0 | 41.9±4.0 | 58.4±2.3 |

McNemar (hypergraph vs pairwise-gcn, seed 42): pairwise-only-correct=20,
hypergraph-only-correct=3, **p=0.0008**.

→ **Structure becomes essential** (set-pool 44.3 → pairwise-gcn 55.2, +10.9 F1; ROC 71→81).
→ **But pairwise beats the hypergraph**, significantly, including on the cross-contract subset.

## Verdict (honest)
1. **Supported & novel:** *when* graph structure helps for LM-embedded Solidity depends
   on feature granularity — rich function embeddings make structure redundant; atomic
   node features make it essential. Robust across seeds.
2. **NOT supported:** the central "hyperedge > pairwise-edge" claim. Pairwise-GCN equals
   or beats the hypergraph in BOTH feature regimes, with statistical significance under
   atomic features. The per-function interactions here appear pairwise-decomposable.

Remaining untested levers (do not pursue without deciding direction, to avoid result-shopping):
deeper layers; genuinely n-ary / non-decomposable path-level hyperedges; the larger
DAppSCAN/FORGE benchmark for power; full signature/skeleton re-embedding (vs hard drop).
