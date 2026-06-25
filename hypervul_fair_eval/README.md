# HyperVul Fair Evaluation

Clean research/evaluation codebase for testing whether HyperVul's hyperedge representation improves smart-contract vulnerability detection over generic baselines.

The new codebase is organized around three research questions:

1. **RQ1 Generic Baselines:** Compare full HyperVul against generic baselines that do not use HyperVul hyperedges.
2. **RQ2 Representation Ablation:** Compare set, pairwise, and hyperedge encodings under identical candidate interactions.
3. **RQ3 HyperVul Ablation:** Measure the contribution of symbolic/security and model components inside HyperVul.

Current status:

- Dataset audit is implemented and passed.
- Existing `data/contract_graphs/{train,val,test}.json` are the canonical project-disjoint splits.
- Model training is not implemented yet.

Run the dataset audit:

```bash
python3 hypervul_fair_eval/scripts/audit_dataset.py
```

Outputs:

- `hypervul_fair_eval/outputs/dataset_audit.md`
- `hypervul_fair_eval/outputs/dataset_audit.json`

