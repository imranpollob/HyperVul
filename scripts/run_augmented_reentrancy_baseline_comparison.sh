#!/usr/bin/env bash
set -euo pipefail

SEEDS="${SEEDS:-42 43}"
EPOCHS="${EPOCHS:-5}"
BATCH_SIZE="${BATCH_SIZE:-128}"
LR="${LR:-0.001}"
DROPOUT="${DROPOUT:-0.3}"

cd "$(dirname "$0")/.."

python scripts/run_augmented_reentrancy_baseline_comparison.py \
  --seeds ${SEEDS} \
  --epochs "${EPOCHS}" \
  --batch-size "${BATCH_SIZE}" \
  --lr "${LR}" \
  --dropout "${DROPOUT}"

echo
echo "Wrote:"
echo "  reports/augmented_reentrancy_baseline_comparison.md"
echo "  reports/augmented_reentrancy_baseline_summary.csv"
echo "  reports/augmented_reentrancy_baseline_metrics_raw.csv"
echo "  reports/augmented_reentrancy_baseline_localization_summary.csv"
echo "  reports/augmented_reentrancy_baseline_localization_raw.csv"
echo "  reports/augmented_reentrancy_dataset_counts.csv"
