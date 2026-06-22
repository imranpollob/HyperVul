# HyperVul: Interaction-Level Vulnerability Detection in Solidity Smart Contracts

This repository contains the official implementation of **HyperVul**, a framework that reformulates smart contract vulnerability detection as an interaction-level hyperedge classification problem.

---

## 🚀 Step-by-Step Evaluation & Training Pipeline

To fully train the baselines, train the HyperVul models across multiple seeds, and reproduce the tables for the paper, execute the steps below in order.

### ⚡ Automated Master Script

For convenience, you can run the entire pipeline sequentially using the provided master script. The script uses `set -e` to abort immediately and inform you if any error occurs:

```bash
./run_all.sh
```

### Step 1: Run Static Analysis Benchmarks
Run the Slither and Mythril analysis harnesses on the test split. The harnesses automatically resolve imports, determine Solidity compiler versions, apply syntax transpilation to fix early `0.8.x` compatibility, compile contracts, and evaluate performance.

```bash
# Run Slither evaluation
python3 scripts/latest1/run_slither_harness.py

# Run Mythril evaluation (falls back to proxy mode if Mythril is not installed)
python3 scripts/latest1/run_mythril_harness.py
```

### Step 2: Train GNN Baselines
Train and evaluate GNN representation baselines (Set-Pooling, Pairwise-GCN, Pairwise-GAT, and Hypergraph) across 5 seeds (42–46). This generates `experiments/latest1/representation_comparison.json`.

```bash
python3 model/latest1/run_representation_comparison.py --seeds 42 43 44 45 46
```

### Step 3: Train the Proposed HyperVul Models (Ablation Seeds)
Train the proposed HyperVul model variants across 5 seeds (42–46) to support the ablation study.
* `--sym-mode none`: Zeroed symbolic features (Baseline ablation)
* `--sym-mode security`: Safety/guard features only
* `--sym-mode full`: Full symbolic features (Proposed model)

Run the following commands for each of the seeds:

```bash
# 1. Train the baseline ablation (secnone)
for seed in 42 43 44 45 46; do
  python3 model/latest1/train.py --seed $seed --sym-mode none --out-tag secnone --fix-k 100
done

# 2. Train the safety-only ablation (secsec)
for seed in 42 43 44 45 46; do
  python3 model/latest1/train.py --seed $seed --sym-mode security --out-tag secsec --fix-k 100
done

# 3. Train the full proposed HyperVul model (secfull)
for seed in 42 43 44 45 46; do
  python3 model/latest1/train.py --seed $seed --sym-mode full --out-tag secfull --fix-k 100
done
```

### Step 4: Aggregate Ablation Results
Run the aggregation script to compile the per-seed results from `experiments/latest1/ablation/` and output `experiments/latest1/ablation_summary.md` showing mean metrics and statistical significance.

```bash
python3 experiments/aggregate_ablation.py
```

### Step 5: Generate Final Paper Tables
Run the final formatting script to assemble the benchmark tables and generate `final-evaluation-results.md`.

```bash
python3 scripts/latest1/generate_final_paper_tables.py
```