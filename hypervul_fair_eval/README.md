# HyperVul Fair Evaluation

Clean research/evaluation codebase for testing whether HyperVul's hyperedge representation improves smart-contract vulnerability detection over generic baselines.

This codebase is organized around three research questions:

1. **RQ1 Generic Neural Baselines:** Train baselines that do not use HyperVul hyperedges.
2. **RQ2 Representation Ablation:** Compare set, pairwise, and hyperedge encodings under identical candidate interactions.
3. **RQ3 HyperVul Ablation:** Measure the contribution of HyperVul security/context, localization, and contrastive components.

Static analyzer baselines, Slither and Mythril, are still in scope but deferred to a later compiler/toolchain pass.

## Canonical Data

The canonical splits are:

```text
data/contract_graphs/train.json
data/contract_graphs/val.json
data/contract_graphs/test.json
```

Dataset audit result:

```text
train: 1614 graphs, 10740 interactions, 215 positive, 10525 negative
val:    167 graphs,   844 interactions,  38 positive,   806 negative
test:   138 graphs,   773 interactions,  41 positive,   732 negative
```

The audit verifies project-disjoint and project-contract-disjoint splits.

## Quick Verification

Run these before a long evaluation if you changed code:

```bash
python3 -m py_compile $(find hypervul_fair_eval/src -name '*.py') $(find hypervul_fair_eval/scripts -name '*.py')

python3 hypervul_fair_eval/scripts/audit_dataset.py
python3 hypervul_fair_eval/scripts/check_import_boundaries.py
python3 hypervul_fair_eval/scripts/smoke_test_models.py
python3 hypervul_fair_eval/scripts/smoke_test_training_core.py
```

## Strong AI-Tool Evaluation Workflow

This workflow trains strong independent generic baselines and advanced HyperVul tool variants. Baselines are tuned independently, but they do not use HyperVul hyperedges. HyperVul is the only model family that uses advanced typed hyperedges.

### 1. Sanity Check

```bash
cd /home/pollmix/Coding/HyperVul

python3 -m py_compile $(find hypervul_fair_eval/src -name '*.py') $(find hypervul_fair_eval/scripts -name '*.py')

python3 hypervul_fair_eval/scripts/audit_dataset.py
python3 hypervul_fair_eval/scripts/check_import_boundaries.py
python3 hypervul_fair_eval/scripts/smoke_test_models.py
python3 hypervul_fair_eval/scripts/smoke_test_training_core.py
```

### 2. Strong Baseline Seed-42 Sweep

```bash
python3 hypervul_fair_eval/scripts/run_strong_baseline_sweep.py \
  --seeds 42 \
  --max-epochs 200 \
  --early-stop \
  --patience 20 \
  --threshold-policy max_f2
```

Output to paste back for review:

```bash
cat hypervul_fair_eval/outputs/strong_baselines/summary.md
```

### 3. HyperVul Seed-42 Quick Sweep

```bash
python3 hypervul_fair_eval/scripts/run_hypervul_quick_sweep.py \
  --seed 42 \
  --max-epochs 200 \
  --early-stop \
  --patience 20 \
  --threshold-policy max_f2
```

Output to paste back for review:

```bash
cat hypervul_fair_eval/outputs/quick_sweep/summary.md
```

### 4. Full Strong Baseline Run

```bash
python3 hypervul_fair_eval/scripts/run_strong_baseline_sweep.py \
  --seeds 42 43 44 45 46 \
  --models function-mlp function-features-mlp sequence-bigru callgraph-gat pairwise-rgcn pairwise-gat \
  --max-epochs 200 \
  --early-stop \
  --patience 20 \
  --threshold-policy max_f2
```

Output to paste back for review:

```bash
cat hypervul_fair_eval/outputs/strong_baselines/summary.md
```

### 5. Full HyperVul Tool Run

```bash
python3 hypervul_fair_eval/scripts/run_hypervul_tool_evaluation.py \
  --seeds 42 43 44 45 46 \
  --max-epochs 200 \
  --early-stop \
  --patience 20 \
  --symbolic-mode full \
  --loss asl \
  --scl-pretrain-epochs 15 \
  --scl-lambda 0.5 \
  --scl-hard-neg-weight 3.0 \
  --threshold-policy max_f2
```

Output to paste back for review:

```bash
cat hypervul_fair_eval/outputs/tool_eval/summary.md
```

### 6. Final Report

```bash
python3 hypervul_fair_eval/scripts/make_final_report.py
cat hypervul_fair_eval/outputs/final_report.md
```

## Full Evaluation Commands

Run from the repository root:

```bash
cd /home/pollmix/Coding/HyperVul
```

### One-Command Full Pipeline

This command runs verification checks, audits the dataset, trains RQ1/RQ2/RQ3, refreshes summaries, and regenerates the final report dynamically:

```bash
python3 hypervul_fair_eval/scripts/run_full_evaluation.py
```

Useful variants:

```bash
# Print the full command sequence without training.
python3 hypervul_fair_eval/scripts/run_full_evaluation.py --dry-run

# Fast smoke run for checking that the pipeline works end to end.
python3 hypervul_fair_eval/scripts/run_full_evaluation.py \
  --seeds 42 \
  --epochs 1

# Full run with the current paper settings.
python3 hypervul_fair_eval/scripts/run_full_evaluation.py \
  --seeds 42 43 44 45 46 \
  --epochs 20 \
  --threshold-policy max_f2
```

The final consolidated output is regenerated at:

```text
hypervul_fair_eval/outputs/final_report.md
hypervul_fair_eval/outputs/final_report.json
```

The individual commands below are useful for partial reruns or debugging.

### 1. Dataset Audit

```bash
python3 hypervul_fair_eval/scripts/audit_dataset.py
```

Outputs:

```text
hypervul_fair_eval/outputs/dataset_audit.md
hypervul_fair_eval/outputs/dataset_audit.json
```

### 2. RQ1: Generic Neural Baselines

These baselines do not use the HyperVul hyperedge builder.

```bash
python3 hypervul_fair_eval/scripts/rq1_run_generic_baselines.py \
  --models function-mlp function-features-mlp sequence callgraph-gcn pairwise-gcn pairwise-gat \
  --seeds 42 43 44 45 46 \
  --epochs 20 \
  --batch-size 64 \
  --threshold-policy max_f2
```

Outputs:

```text
hypervul_fair_eval/outputs/rq1/
hypervul_fair_eval/outputs/rq1/rq1_generic_baselines_summary.md
hypervul_fair_eval/outputs/rq1/rq1_generic_baselines_summary.json
```

### 3. RQ2: Representation Ablation

All models use the same candidate interactions and member embeddings. Only the representation encoder changes.

```bash
python3 hypervul_fair_eval/scripts/rq2_run_representation_ablation.py \
  --models set-pool pairwise-gcn pairwise-gat hyperedge-nn \
  --seeds 42 43 44 45 46 \
  --epochs 20 \
  --batch-size 128 \
  --threshold-policy max_f2
```

To regenerate the RQ2 summary from existing per-seed files:

```bash
python3 hypervul_fair_eval/scripts/rq2_run_representation_ablation.py --summarize-only
```

Outputs:

```text
hypervul_fair_eval/outputs/rq2/
hypervul_fair_eval/outputs/rq2/rq2_representation_ablation_summary.md
hypervul_fair_eval/outputs/rq2/rq2_representation_ablation_summary.json
```

### 4. RQ3: HyperVul Component Ablation

```bash
python3 hypervul_fair_eval/scripts/rq3_run_hypervul_ablation.py \
  --models emb-only security full no-localize no-contrastive \
  --seeds 42 43 44 45 46 \
  --epochs 20 \
  --batch-size 128 \
  --threshold-policy max_f2
```

To regenerate the RQ3 summary from existing per-seed files:

```bash
python3 hypervul_fair_eval/scripts/rq3_run_hypervul_ablation.py --summarize-only
```

Outputs:

```text
hypervul_fair_eval/outputs/rq3/
hypervul_fair_eval/outputs/rq3/rq3_hypervul_ablation_summary.md
hypervul_fair_eval/outputs/rq3/rq3_hypervul_ablation_summary.json
```

Note: in the canonical `contract_graphs` view, `security` and `full` both use the available 8-dimensional security context.

### 5. Final Consolidated Report

```bash
python3 hypervul_fair_eval/scripts/make_final_report.py
```

Outputs:

```text
hypervul_fair_eval/outputs/final_report.md
hypervul_fair_eval/outputs/final_report.json
```

## Current Main Outputs

- [Dataset audit](outputs/dataset_audit.md)
- [RQ1 generic baselines](outputs/rq1/rq1_generic_baselines_summary.md)
- [RQ2 representation ablation](outputs/rq2/rq2_representation_ablation_summary.md)
- [RQ3 HyperVul ablation](outputs/rq3/rq3_hypervul_ablation_summary.md)
- [Final report](outputs/final_report.md)
