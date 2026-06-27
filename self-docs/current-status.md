## Project Summary

HyperVul is an AI tool for smart-contract vulnerability detection. The core research idea is that vulnerabilities often depend on higher-order interactions between:

```text
function + state variables + external calls + security/context signals
```

Generic baselines model code as functions, sequences, call graphs, or pairwise graphs. HyperVul instead models each vulnerable candidate as a typed hyperedge.

Current goal:

```text
Show that HyperVul’s hyperedge representation gives better vulnerability detection than strong generic baselines.
```

Current dataset:

```text
train: 10740 interactions, 215 positives, 10525 negatives
val:    844 interactions,   38 positives,   806 negatives
test:   773 interactions,   41 positives,   732 negatives
```

Major challenge:

```text
Extreme class imbalance and hard negative discrimination.
```

---

## Current Baseline Implementations

### 1. Function-MLP

Representation:

```text
single function embedding
```

Input:

```text
SmartBERT/function embedding only
```

Model:

```text
MLP classifier
```

Does not use hyperedges.

Purpose:

```text
semantic function-level lower bound
```

Current 5-seed result:

```text
Precision 15.34
Recall    64.88
F1        24.59
F2        38.84
PR-AUC    32.74
ROC-AUC   82.80
```

---

### 2. Function+Features MLP

Representation:

```text
function embedding + generic scalar features
```

Generic features include:

```text
state var count
external call count
has state var
has external call
cross-contract flag
source length
callgraph degree
```

Model:

```text
MLP classifier
```

Does not use hyperedges.

Current 5-seed result:

```text
Precision 15.63
Recall    72.20
F1        25.69
F2        41.86
PR-AUC    27.93
ROC-AUC   84.48
```

---

### 3. Sequence-BiGRU

Representation:

```text
contract/function sequence
```

Input:

```text
ordered function embeddings + generic scalar features
```

Model:

```text
bidirectional recurrent sequence model
per-interaction/function classification head
```

Does not use hyperedges.

Current best baseline.

Current 5-seed result:

```text
Precision 18.80
Recall    78.54
F1        30.24
F2        47.79
PR-AUC    28.29
ROC-AUC   87.45
```

---

### 4. CallGraph-GAT

Representation:

```text
generic function call graph
```

Input:

```text
function nodes
call edges
generic scalar features
```

Model:

```text
graph attention network
node classifier
```

Does not use hyperedges.

Current 5-seed result:

```text
Precision 17.89
Recall    65.85
F1        27.69
F2        41.85
PR-AUC    31.25
ROC-AUC   85.84
```

---

### 5. Pairwise-RGCN

Representation:

```text
generic pairwise program-relation graph
```

Input:

```text
function nodes
binary relation edges
typed edges
```

Generic edge types:

```text
call
shared_state
shared_callee
```

Model:

```text
relational GCN
node classifier
```

Does not use HyperVul hyperedges.

Current 5-seed result:

```text
Precision 13.89
Recall    73.17
F1        23.01
F2        38.41
PR-AUC    28.42
ROC-AUC   84.02
```

---

### 6. Pairwise-GAT

Representation:

```text
generic pairwise graph
```

Input:

```text
function/state/callee pairwise binary relations
```

Model:

```text
graph attention network
node classifier
```

Does not use HyperVul hyperedges.

Current 5-seed result:

```text
Precision 16.72
Recall    63.90
F1        26.39
F2        40.59
PR-AUC    30.11
ROC-AUC   84.90
```

---

## Current HyperVul Implementation

### HyperVul-Tool / HyperVul-Full

Representation:

```text
typed hyperedge
```

Each candidate interaction is represented as:

```text
function member
+ state variable members
+ external call/callee members
+ symbolic/security features
```

HyperVul-only symbolic features include:

```text
node type
function visibility
function mutability
nonReentrant-like signal
state type bucket
state access mode
callee target kind
low-level call flag
return-check flag
safe ERC20-like flag
cross-contract flag
```

Model currently uses:

```text
sequence-aware member encoding
attention pooling over hyperedge members
MLP classification head
localization head for function-state-callee tuple evidence
ASL loss
early stopping
threshold tuning
```

Does use hyperedges.

Current best balanced 5-seed result:

```text
Precision 37.50
Recall    40.49
F1        37.60
F2        39.03
PR-AUC    36.94
ROC-AUC   87.62
```

Current best max-F1 5-seed result:

```text
Precision 29.77
Recall    46.34
F1        35.69
F2        41.14
PR-AUC    36.94
ROC-AUC   87.62
```

---

## Current Result Interpretation

HyperVul currently wins on:

```text
Precision
F1
PR-AUC
ROC-AUC
```

Best HyperVul vs best baseline:

```text
F1:      37.60 vs 30.24
PR-AUC:  36.94 vs 32.74 / 31.25
ROC-AUC: 87.62 vs 87.45
```

HyperVul currently loses on:

```text
Recall
F2
```

Best baseline:

```text
Sequence-BiGRU
Recall 78.54
F2     47.79
```

Best HyperVul:

```text
Recall 46.34
F2     41.14
```

---

## Main Problems Identified

1. Extreme class imbalance.
2. Too few positive training examples.
3. Weak hard-negative discrimination.
4. HyperVul lacks contract-level/global context.
5. Current hyperedge encoder is not advanced enough.
6. Symbolic/security features are incomplete.
7. Threshold calibration is unstable.
8. Possible label noise.
9. Sequence baseline captures global signals HyperVul misses.
10. Interaction-level evaluation creates many false-positive opportunities.

---
