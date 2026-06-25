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

## Full Evaluation Commands

Run from the repository root:

```bash
cd /home/pollmix/Coding/HyperVul
```

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

