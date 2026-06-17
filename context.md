# Project Context

## Project Overview
HyperVul is a research project (targeting IEEE ICTAI 2026, Rank B) for **interaction-level
vulnerability detection in Solidity smart contracts**. It models a multi-step interaction —
a function together with the state variables it accesses and the external contracts it calls —
as a **hyperedge** over {function, state vars, callees}, and tests whether this hypergraph
representation detects vulnerabilities (reentrancy SWC-107, front-running SWC-114, unchecked
calls SWC-104) better than pairwise-edge graph representations. Node features come from a
frozen SmartBERT-v3 code encoder (768-d).

## Current Status
- **Completed:**
  - Audited the prior baseline comparison; found the "Interaction-Level (Ours)" row in
    `experiments/results/baseline_results.md` was stale/stitched from iter1+iter2 (invalidated
    the earlier "ablations beat ours" conclusion).
  - Built a representation model zoo + a controlled multi-seed harness (CIs + McNemar).
  - Ran 3 representation experiments (see `experiments/results/representation_findings.md`):
    1. Full SmartBERT function embeddings → all representations tie (~63 F1); structure redundant.
    2. Drop function node (atomic state+callee) → structure essential, pairwise-GCN ≥ hypergraph (p=0.0008).
    3. Function-as-signature hub → **hypergraph > pairwise** (F1 59.4 vs 51.2; cross-F1 51.4 vs 41.3; McNemar p=0.0021).
  - Initialized DAppSCAN + FORGE-Curated git submodules (~5.7 GB; 303 FORGE VFPs).
  - Built signature/skeleton feature files for train/val/test/OZ/Aave.
- **In Progress:**
  - Deciding research direction (pivot decision paused by user): scale-up vs reframe vs FPR fix vs end-to-end fine-tune.
- **Next Steps:**
  - Scale to a real DAppSCAN/FORGE benchmark (contract-disjoint splits; audit label quality first).
  - Re-run Exp 3 with statistical power + cross-dataset generalization to confirm the hyperedge advantage.
  - Candidate pivots: reframe as a "when does structure help" feature-granularity study; reduce OOD FPR with safety-aware nodes + hard negatives; unfreeze the encoder for end-to-end training.

## Key Files & Architecture
- `model/model.py` — `HyperedgeClassifier` (attention pooling + MLP); the deployed model.
- `model/train.py` — iteration-3 training (clean-negative K-sweep aimed at FPR).
- `model/run_unit_comparison.py` — controlled node-set ablation (function/state/callee).
- `model/run_representation_comparison.py` — main harness: set-pool / pairwise-GCN / pairwise-GAT /
  hypergraph; multi-seed, bootstrap CIs, McNemar. Flags: `--sig`, `--drop-func`, `--seeds`.
- `src/models/ops.py` — shared `SegmentAttentionPool`, `MLPHead`.
- `src/models/set_pool.py` — structure-free baseline.
- `src/models/gnn_zoo.py` — unified GNN skeleton (GCN/GAT on clique graph; PyG `HypergraphConv` on incidence) — the fair adjudicator.
- `src/models/hypergraph_nn.py`, `src/baselines/pairwise_gnn.py` — earlier model variants (superseded by gnn_zoo).
- `scripts/build_hypergraph.py` — contract-scoped hypergraph constructor (`build_contract_graphs`, `drop_func`).
- `scripts/build_signature_features.py` — re-embeds function nodes as signatures (body stripped).
- `scripts/extract_features.py` — AST + SmartBERT feature extraction (OZ/DAppSCAN/FORGE resolvers).
- `scripts/negative_hyperedge_sampling.py` — AST utilities (`resolve_all_functions`, `node_text`, etc.).
- `data/splits/*.json` — datasets (`train_augmented`, `val_features`, `test_features`, `*_sig`).
- `experiments/results/representation_findings.md` — consolidated 3-experiment findings.
- `experiments/results/representation_comparison.{md,json}` — latest run output (overwritten per run).

## Tech Stack
- **Languages:** Python 3.12; Solidity (the analyzed code).
- **Frameworks/Libraries:** PyTorch 2.9.0+cu128, PyTorch Geometric 2.8.0, HuggingFace Transformers
  (SmartBERT-v3 `web3se/SmartBERT-v3`, RoBERTa), tree-sitter + tree-sitter-solidity, scikit-learn, scipy, numpy.
- **Tools:** Git + git submodules (OpenZeppelin, DAppSCAN, FORGE-Curated); CUDA GPU.

## Recent Changes
- Added the representation comparison harness + model zoo and ran 3 controlled experiments.
- Built the signature-feature pipeline; Exp 3 shows the hypergraph beats pairwise edges on
  F1/precision/cross-contract (p=0.0021) under atomic function-as-hub features (pairwise-GAT still
  leads threshold-free ranking PR-AUC/ROC).
- Initialized the DAppSCAN and FORGE-Curated submodules (previously empty).

## Environment Setup
- **Python version:** 3.12.12 (pyenv). CUDA available (`torch.cuda.is_available()` = True).
- **Dependencies:** torch==2.9.0+cu128, torch_geometric==2.8.0, transformers, tree_sitter,
  tree_sitter_solidity, scikit-learn, scipy, numpy.
- **How to run:**
  - Representation comparison: `python model/run_representation_comparison.py --seeds 42 43 44 45 46 [--sig | --drop-func]`
  - Node-set ablation: `python model/run_unit_comparison.py`
  - Build signature features: `python scripts/build_signature_features.py`
  - Submodules (one-time): `git submodule update --init --depth 1 data/DAppSCAN data/FORGE-Curated`

## Important Notes
- **Known issues:**
  - High out-of-distribution FPR on clean code (≈76% MakerDAO, 53% Bancor, 46% Liquity) — model
    over-flags external calls. Biggest practical weakness.
  - Tiny test set (44 positives / 33 contracts) → F1 variance ±4–5 across seeds; use ≥5 seeds + CIs + paired tests.
  - The hyperedge > pairwise result is **conditional** on atomic (signature) features; with full
    function embeddings structure is redundant.
- **Dependencies to watch:**
  - Submodules are large (~5.7 GB) and were previously uninitialized; val/test source resolution
    depends on them being populated.
  - `data/splits/train_augmented.json` is ~224 MB (was excluded from a prior commit due to size).
- **Configuration details:**
  - Fixed model config for fair comparison: hidden=256, dropout=0.3, lr=1e-3, weight_decay=1e-5, 2 layers, seed=42.
  - Threshold rule: highest threshold achieving ≥95% recall on validation positives.
  - Training composition: base + 100 OpenZeppelin + 100 Aave clean negatives.
- Never trust single-seed deltas or hand-copied "Ours" rows — always re-train/re-evaluate all
  variants under identical conditions (lesson from the invalidated baseline table).

## Last Updated
2026-06-17
