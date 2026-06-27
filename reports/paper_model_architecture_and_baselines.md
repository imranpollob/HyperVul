# HyperVul: Project Goal, Architecture, and Baselines

## Project Goal

HyperVul targets smart-contract vulnerability detection under severe class imbalance. The original project framed the task as strict interaction-level binary classification: each candidate interaction or hyperedge was classified as vulnerable or non-vulnerable. Phase 0 audits showed that this setup creates too many false-positive opportunities, especially when a single contract contains many risky-looking external calls.

The revised task is:

1. **Contract-level vulnerability detection**: predict whether a contract contains a vulnerability.
2. **Top-k interaction localization**: rank suspicious interaction hyperedges inside vulnerable contracts.
3. **Reentrancy-focused evaluation**: prioritize reentrancy because it naturally matches HyperVul's interaction representation: external calls, state variables, callees, and call ordering.

## Problem

Smart-contract vulnerability detection is difficult because the vulnerable class is rare and because many safe contracts contain risky-looking patterns. Reentrancy is a representative example: an external call alone is not sufficient evidence of vulnerability. The model must distinguish:

- external call before critical state update,
- attacker-controlled callee,
- missing effective reentrancy guard,
- CEI-protected execution,
- `nonReentrant` protection,
- trusted/fixed callees,
- owner-only rescue paths.

In the better-labeled reentrancy view, the interaction-level training split remains highly imbalanced before augmentation:

| Split | Positive Interactions | Negative Interactions | Neg:Pos |
|---|---:|---:|---:|
| train | 108 | 8467 | 78.40 |
| val | 35 | 1389 | 39.69 |
| test | 20 | 1051 | 52.55 |

This motivates contract-level detection and top-k localization rather than relying only on strict interaction-level classification.

## Proposed Solution

HyperVul represents each candidate interaction as a hyperedge connecting:

- the function containing the interaction,
- accessed state variables,
- external callees or call targets,
- symbolic security features.

The model scores candidate interactions and then aggregates interaction evidence to produce a contract-level vulnerability score. This lets HyperVul support both:

- **detection**: vulnerable or non-vulnerable contract,
- **localization**: top-ranked suspicious interactions.

The strongest current variant uses:

```text
HyperVul-Aug = targeted reentrancy augmentation + gated risk-vs-safety HyperVul
```

## Novelty

HyperVul differs from standard baselines in four main ways.

1. **Interaction Hyperedges**
   HyperVul models vulnerability-relevant interactions directly instead of treating each function as an isolated sequence or node.

2. **State-Callee-Function Tuple Reasoning**
   Reentrancy depends on the relationship between state variables, external calls, and the enclosing function. HyperVul explicitly represents this tuple.

3. **Contract-Level MIL Objective**
   A contract is vulnerable if at least one interaction is vulnerable. HyperVul uses multi-instance learning-style aggregation over interaction scores.

4. **Risk-vs-Safety Scoring**
   The risk branch detects vulnerable interaction structure, while the safety branch learns protection evidence such as `nonReentrant`, CEI ordering, safe wrappers, and checked calls. The gated variant suppresses risk scores when safety evidence is strong.

## HyperVul Architecture

### Input Representation

For each candidate interaction hyperedge, HyperVul receives:

| Component | Description |
|---|---|
| Function embedding | Semantic embedding of the enclosing function |
| State members | State variables read or written by the interaction |
| Callee members | External calls, transfer targets, or called contracts |
| Symbolic risk features | External call, state access, low-level call, cross-contract signal |
| Safety/context features | `nonReentrant`, return-value checked, safe wrapper, try/catch, guard-before-call, state update order, access control |

### Base HyperVul Encoder

The base HyperVul encoder processes hyperedge members in the order:

```text
function -> state variables -> callees
```

It uses:

- a bidirectional GRU over hyperedge members,
- attention pooling over hyperedge members,
- an MLP classifier for interaction scoring,
- an optional tuple-localization head over function-state-callee combinations.

The tuple-localization head estimates which state/callee combination contributes most to the vulnerability score. This is important for top-k explanation.

### Contract-Level Aggregation

Each contract contains multiple candidate interaction hyperedges. HyperVul produces an interaction score for each hyperedge and aggregates them into a contract score.

The explored aggregation strategies are:

| Aggregation | Description |
|---|---|
| max pooling | contract score is the highest interaction score |
| top-k mean pooling | contract score is the mean of top-k interaction scores |
| attention pooling | learned attention over interaction scores |

For reentrancy-focused experiments, the strongest current direction uses contract-level scoring with interaction localization retained.

### Risk-vs-Safety HyperVul

The Phase 1B model separates risk and safety.

Risk branch:

- external call evidence,
- state access/update,
- callee/call type,
- low-level call,
- cross-contract interaction structure.

Safety branch:

- `nonReentrant`,
- return-value checked,
- safe ERC20 wrapper,
- try/catch,
- guard-before-call,
- state-update order,
- access-control signals.

The gated variant computes:

```text
final_logit = risk_logit * sigmoid(gate)
```

where safety evidence reduces the gate. This makes safety evidence suppress risky-looking but protected interactions.

The model also uses an auxiliary safety prediction loss for:

- has_nonreentrant,
- has_return_check,
- has_safe_wrapper,
- has_try_catch,
- has_guard_before_call.

## Baseline Architectures

The baselines are designed to test whether HyperVul's interaction-level hyperedge representation is necessary.

| Method | Input Unit | Main Representation | Architecture | Context Captured | Limitation |
|---|---|---|---|---|---|
| Function-MLP | Function | Function embedding | 2-layer MLP | Local function semantics | No state/callee structure, no graph context |
| Function+Features MLP | Function | Function embedding + scalar metadata | 2-layer MLP | Local semantics plus simple handcrafted features | Features are not organized around interactions |
| Sequence-BiGRU | Function sequence | Ordered functions in a contract | Bidirectional GRU + linear head | Sequential contract context | Does not explicitly model external-call/state-variable/callee tuples |
| CallGraph-GAT | Function/node | Call graph nodes and edges | 2-layer graph attention network | Function call dependencies | Call graph edges are coarse for reentrancy reasoning |
| Pairwise-RGCN | Pairwise graph node | Pairwise relation graph | Relational graph convolution | Typed pairwise relations | Relation types are still pairwise, not higher-order hyperedges |
| Pairwise-GAT | Pairwise graph node | Pairwise relation graph | Graph attention network | Attended pairwise neighborhood | Does not explicitly encode full function-state-callee interaction |
| Current HyperVul | Interaction hyperedge | Function + state + callee members | GRU + attention + tuple localization | Higher-order interaction structure | Original version treats contract metrics as wrappers over interaction predictions |
| HyperVul-RS | Contract bag of hyperedges | Risk branch + safety branch | Gated risk-vs-safety MIL | Interaction risk and protection evidence | Needs enough protected negatives and calibrated thresholds |
| HyperVul-Aug | Contract bag of hyperedges | Targeted reentrancy augmentation + HyperVul-RS | Gated risk-vs-safety MIL with augmented training | Reentrancy pattern families and protected-risk distinction | Performance-forward setting; must be described with augmentation protocol |

## Why HyperVul Should Work Better

### 1. Vulnerabilities Are Interactional

Reentrancy is not just a property of a function embedding. It depends on an interaction:

```text
external call -> state update ordering -> callee controllability -> protection mechanism
```

Function-level baselines can see function semantics but do not explicitly bind external calls to affected state variables. Graph baselines capture edges, but pairwise edges do not fully represent the higher-order tuple among function, state, and callee.

HyperVul directly models this tuple as a hyperedge.

### 2. Contract-Level Detection Matches Labels Better

Many labels are reliable at the contract or function level but noisy at the exact interaction level. HyperVul's contract-level aggregation matches the realistic audit question:

```text
Does this contract contain at least one vulnerability?
```

The model still produces interaction scores, enabling localization without forcing every candidate interaction to be perfectly classified.

### 3. Safety Evidence Must Suppress Risk

Many false positives are protected reentrancy-like examples. These contain external calls and state access but are safe due to:

- `nonReentrant`,
- CEI ordering,
- trusted/fixed callee,
- safe wrapper,
- access control.

Standard baselines treat these signals as ordinary features. HyperVul-RS uses a dedicated safety branch to suppress the vulnerability score.

### 4. Top-k Localization Is Built In

The model ranks interaction hyperedges inside a contract. This supports:

- Top-1 localization,
- Top-3 localization,
- Top-5 localization,
- MRR,
- Recall@k.

This is closer to how a security auditor uses a vulnerability detector: the model should identify the contract and surface the suspicious interaction.

## Training Objectives

The strongest HyperVul variants use:

| Loss | Purpose |
|---|---|
| Contract-level BCE | Detect vulnerable contracts |
| Interaction auxiliary BCE | Keep interaction scores meaningful for localization |
| Safety auxiliary BCE | Force safety branch to learn protection evidence |
| Optional ranking/contrastive loss | Encourage vulnerable interactions to score above protected near-misses |

In current results, targeted augmentation with BCE and gated risk-vs-safety scoring works better than the contrastive shortcut.

## Evaluation Tasks

### Contract-Level Detection

Metrics:

- Precision,
- Recall,
- F1,
- F2,
- PR-AUC,
- ROC-AUC.

### Top-k Localization

Metrics:

- Top-1 hit,
- Top-3 hit,
- Top-5 hit,
- MRR,
- Recall@k.

### Threshold Policies

The project reports:

| Threshold Policy | Meaning |
|---|---|
| validation max-F1 | threshold selected on validation to maximize F1 |
| target recall 90 | threshold selected to reach high recall on validation |
| target precision 80 | threshold selected to favor high precision on validation |
| test-oracle max-F1 | optimistic upper bound selected on test predictions |

## Summary of Architectural Differences

| Model Family | Uses Function Semantics | Uses Scalar/Safety Features | Uses Graph Context | Uses Hyperedges | Contract-Level MIL | Localization |
|---|---:|---:|---:|---:|---:|---:|
| Function-MLP | Yes | No | No | No | No | Weak |
| Function+Features MLP | Yes | Yes | No | No | No | Weak |
| Sequence-BiGRU | Yes | Optional | Sequential | No | No | Moderate |
| CallGraph-GAT | Yes | Optional | Call graph | No | No | Moderate |
| Pairwise-RGCN | Yes | Optional | Typed pairwise graph | No | No | Moderate |
| Pairwise-GAT | Yes | Optional | Pairwise attention graph | No | No | Moderate |
| Current HyperVul | Yes | Yes | Hyperedge members | Yes | Post-hoc/wrapped | Strong |
| HyperVul-RS | Yes | Yes, separated | Hyperedge members | Yes | Yes | Strong |
| HyperVul-Aug | Yes | Yes, separated | Hyperedge members | Yes | Yes | Strong |

## Paper-Ready Method Names

Use concise names in tables:

| Internal Name | Paper Name |
|---|---|
| Function-MLP | Func-MLP |
| Function+Features MLP | Func+Feat MLP |
| Sequence-BiGRU | Seq-BiGRU |
| CallGraph-GAT | CallGraph-GAT |
| Pairwise-RGCN | Pairwise-RGCN |
| Pairwise-GAT | Pairwise-GAT |
| Current HyperVul | HyperVul |
| HyperVul-RiskSafety gated | HyperVul-RS |
| shortcut_aug_bce:gated | HyperVul-Aug |

## Suggested Paper Claim

The paper should emphasize:

> HyperVul improves over function-, sequence-, and graph-based baselines because it models vulnerability-relevant interactions as higher-order hyperedges and evaluates them at the contract level while retaining top-k localization. For reentrancy, targeted augmentation and gated risk-vs-safety scoring substantially improve both detection and localization by teaching the model to distinguish vulnerable external-call/state-update patterns from protected reentrancy-like interactions.

