# HyperVul — Train Split Augmentation Report

> **Date**: 2026-06-11  
> **Original Train Set**: 874 (223 Positives / 651 Negatives)  
> **Augmented Train Set**: 1381 (552 Positives / 829 Negatives)  
> **Ratio**: 552:829 (0.67:1)

---

## Executive Summary
This report documents the training data expansion using semantic-preserving transforms on the `train.json` split. The validation (`val.json`) and test (`test.json`) splits were preserved as untouched evaluation data. Node features were re-extracted using the frozen `web3se/SmartBERT-v3` encoder for both original items and accepted variants.

---

## Gating, Verification, and Discard Metrics

We enforced strict tree-sitter AST validation checks to ensure semantic identity was preserved:
1. **Check a (Constructability)**: External call present AND state variable access present.
2. **Check b (Structural Preservation)**: Same number of external calls, same state variable accesses, and same cross-contract vs. intra-contract classification.
3. **Check c (Sequence Ordering)**: Relative order of `{state read, external call, state write}` within the function remains identical.
4. **Leakage check**: No variant's hash matches any hash in validation or test splits.

### Discard Statistics
* **Total Variants Generated**: 2417
* **Accepted Variants**: 507
* **Discarded Variants**: 1910

### Discard Reasons
- **sequence_order_changed**: 973 variants
- **duplicate_variant**: 932 variants
- **state_vars_mismatch**: 5 variants


---

## Leakage Check Result
* **Val/Test Leakage Violations**: **0**

---

## Feature Scheme Specification (CHANGE 1 Choice)

To guarantee consistency and avoid mismatch errors during G-HAN downstream architectures, we applied the **768-d uniform feature scheme**:
1. **Function nodes**: CLS token embedding from SmartBERT-v3 ($d=768$).
2. **State variable nodes**: CLS token embedding of `f"{var_type} {var_name}"` ($d=768$).
3. **Call site nodes**: CLS token embedding of `call_text` ($d=768$). Opcode flags (6-d) are omitted here and deferred to the downstream graph classification layers to keep the node embedding space uniform.

---

## Dataset Files
* [train_augmented.json](file:///home/pollmix/Coding/HyperVul/data/splits/train_augmented.json) — Final augmented train set containing original items + variants with metadata, provenance, and node features.
