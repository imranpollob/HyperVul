#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
# This ensures the script stops and informs the user if any error happens.
set -e

echo "============================================================"
echo "Starting HyperVul Full Evaluation & Training Pipeline"
echo "============================================================"

# echo ""
# echo "[Step 1/5] Running Static Analysis Benchmarks..."
# echo "-> Running Slither harness..."
# python3 scripts/latest1/run_slither_harness.py
# echo "-> Running Mythril harness..."
# python3 scripts/latest1/run_mythril_harness.py

echo ""
echo "[Step 2/5] Training and Evaluating GNN Baselines (Seeds 42-46)..."
python3 model/latest1/run_representation_comparison.py --seeds 42 43 44 45 46

echo ""
echo "[Step 3/5] Training Proposed HyperVul Models (Ablation Seeds 42-46)..."

echo "-> 3.1 Training baseline ablation (secnone)..."
for seed in 42 43 44 45 46; do
  echo "   Training seed $seed..."
  python3 model/latest1/train.py --seed $seed --sym-mode none --out-tag secnone --fix-k 100
done

echo "-> 3.2 Training safety-only ablation (secsec)..."
for seed in 42 43 44 45 46; do
  echo "   Training seed $seed..."
  python3 model/latest1/train.py --seed $seed --sym-mode security --out-tag secsec --fix-k 100
done

echo "-> 3.3 Training full proposed model (secfull)..."
for seed in 42 43 44 45 46; do
  echo "   Training seed $seed..."
  python3 model/latest1/train.py --seed $seed --sym-mode full --out-tag secfull --fix-k 100
done

echo ""
echo "[Step 4/5] Aggregating Ablation Results..."
python3 experiments/aggregate_ablation.py

echo ""
echo "[Step 5/5] Generating Final Paper Tables..."
python3 scripts/latest1/generate_final_paper_tables.py

echo ""
echo "============================================================"
echo "Pipeline completed successfully! All tables have been generated."
echo "Results are available in final-evaluation-results.md."
echo "============================================================"
