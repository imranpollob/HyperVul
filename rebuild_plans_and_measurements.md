# HyperVul Rebuild — Plans & Measurements (Tasks 5, 8, 10)

> **Date**: 2026-06-21  **Status**: Task 8 = completed read-only audit. Tasks 5 & 10 = **plans + real measured numbers**; no build code written, no schema/labels/splits/pipeline modified. Build awaits your confirmation.
> Evidence scripts: `scratch/audit_task8_full.py`, `scratch/audit_task5_measure.py`, `scratch/audit_task10_measure.py`. Full Task 8 list: `scratch/task8_full_output.txt`.

---

## TASK 8 — Full FORGE label re-audit (read-only, DONE)

### Root cause (mechanism)
FORGE per-function types come from `make_splits.classify_forge_type(title, desc)` ([make_splits.py:26-36](scripts/make_splits.py#L26-L36)) — a keyword matcher over `finding_title + description` with **a hard default to Reentrancy (SWC-107)** and only 4 recognized families:
```
reentrancy|re-entrancy|reentrant|callback → SWC-107
unchecked|call return                     → SWC-104
front-run|frontrun|sandwich|transaction order → SWC-114
delegatecall                              → SWC-112
else                                      → SWC-107   ← DEFAULT
```
It has no concept of DoS, access control, oracle manipulation, arithmetic, or "this isn't a security bug."

### Results across all 83 FORGE positives
| Category | Count | % |
|---|---:|---:|
| **TYPE-UNSUBSTANTIATED** — recorded SWC-107 *only* because the classifier defaulted (no keyword in finding) | **42 / 83** | **51%** |
| Type-substantiated — a real keyword matched | 41 / 83 | 49% |
| …of which the match is **incidental** (keyword appears in description but the finding is DoS/access-control/logic) | ~12 of 41 (manual) | — |
| Flagged **NON-SECURITY?** by functional-bug heuristic (conservative) | 5 | — |
| Recorded distribution | 56× SWC-107, 27× SWC-114 | (SWC-104=0, SWC-112=0 among FORGE) |

**The 42 defaulted items are not reentrancy.** A representative slice (full list in `scratch/task8_full_output.txt`):
- **DoS / unbounded iteration:** `Folio.{distributeFees,getRebalance,mint,startRebalance}` ("Unbounded Iteration"), `OracleLess._cancelOrder` ("…Leading to DoS").
- **Functional / revert bugs (questionable as *security* positives):** `FlashLoans.flashLoan` ("Functionality is Blocked" / "Does Not Follow ERC-3156"), `OctoDistributor.{withdrawAllAgentTokens,transferHiringDistributions}` ("works incorrectly" / "address(0)"), `MainFeeDistributor.swapLzToken` ("always revert because of interface mismatch"), `GenericERC4626WithdrawRequestManager.stakeTokens` ("USDT approve() reverts").
- **Logic / accounting:** `LikwidMarginPosition.{modify,_margin,_executeAddLeverage}` ("level check…"), `P2pResolvProxy.*` ("withdraws both principal and rewards"), `StakingManager.{stake,withdraw}` ("inflate rewards").
- **Access control mistyped as SWC-107:** `StopLimit.modifyOrder`/`OracleLess.procureTokens` ("Insecure Use of Recipient … Unauthorized Token Transfers").

**Even "substantiated" labels are unreliable:** `AntiSandwichHook._beforeSwap` → SWC-114 matched on *sandwich* but the finding is "Infinite Loop in Tick Iteration" (DoS); `BalancerFlashLoan.{makeFlashLoan,receiveFlashLoan}` → SWC-114 matched on *sandwich* but the finding is "Missing Access Control"; `MerkleDistributor.claim` → SWC-114 on *front-run* but finding is "Anyone can call claim for any account" (access control).

### Verdict (for human review — no labels changed)
1. **The per-vulnerability-type table (report §3.6) is not usable for FORGE** — at least 51% of types are classifier artifacts, and several "substantiated" ones are incidental keyword hits. Recommend treating FORGE per-type recall as **unreported** until re-typed.
2. **A subset of FORGE "positives" are not interaction vulnerabilities at all** (functional reverts, standards non-compliance, DoS). These contaminate the *binary* positive class. The 42 defaulted items are the human-review queue; `FlashLoans.flashLoan`, both `OctoDistributor` items, `MainFeeDistributor.swapLzToken` are the clearest non-security candidates.
3. Suggested follow-up (separate, with your sign-off): a proper finding→type re-classification (add DoS/access-control/oracle/arithmetic families; drop the SWC-107 default; route "no security keyword" to a `REVIEW` bucket instead of a positive). **DAppSCAN labels are unaffected** — they come from in-source auditor SWC annotations (9/9 CONFIRMED in the earlier audit).

---

## TASK 5 — Call-graph edge + helper-node design (plan + measured scale)

### Measured scale FIRST (what the schema change actually costs) — `scratch/audit_task5_measure.py`
For every constructable interaction in the splits (1,234 resolved), I found each direct (1-hop) internal/private callee that reads or writes state, and classified it as an **existing interaction** (→ call edge only) or a **new helper node**. Deduped per `(project, contract)`:

| Split | Contract-graphs | NEW helper nodes (total / median / max) | Call edges (total) | →existing / →new helper | Contracts gaining ≥1 helper |
|---|---:|---|---:|---|---:|
| train | 290 | 358 / 1 / 8 | 609 | 176 / 433 | 158 (54%) |
| val | 51 | 95 / 1 / 12 | 178 | 57 / 121 | 33 (65%) |
| test | 56 | 114 / 1 / 17 | 189 | 39 / 150 | 34 (61%) |
| **all** | **397** | **567 / 1 / 17** | **976** | **272 / 704** | **225 (57%)** |

**Read:** +567 helper nodes on top of ~1,234 interaction hyperedges (**≈ +46% nodes**), plus 976 directed call edges. It's a small, long-tailed addition — median 1 helper per contract, but a tail to 17 (the `Box`/vault NAV-cache cluster from the foundations audit). 57% of contracts gain at least one helper; the rest already express their callees as interactions. **This directly closes the Task-5 BLOCKING gap**: the 704 edges to *new* helpers are exactly the state-mutating functions that currently have no node at all.

### Proposed data-model / schema change (build pending)
Today each item is a standalone hyperedge (`function` span + `state_vars_accessed` + `external_calls`, with `node_types` ∈ {function, state, callee}; [src/models/ops.py](src/models/ops.py)). Proposed additions, kept **additive** so the existing intra-hyperedge classifier is untouched:

1. **New node type `NODE_HELPER`** (graph-level, not inside a hyperedge's pooled node set). Representation per the design: `function_embedding` (own span, **same SmartBERT-v3 encoder / max_length=256**) + `state_vars_accessed` (+ embeddings). **No `external_calls` field** (helpers are sub-constructability by definition).
2. **Contract-graph container** (new artifact, e.g. `*_contract_graphs.json`, not an edit to `*_features.json`):
   ```
   { graph_id: (project_key, contract),
     interactions: [hyperedge_id...],         # existing items (pos+neg)
     helpers:      [{function, emb, state_vars}...],
     edges: [ {src, dst, etype} ] }           # etype ∈ {call, shared_state, shared_callee}
   ```
3. **Directed call edges with a learnable edge-type/direction feature**, so G-HAN's gate *learns* direction-weighting rather than hard-coding caller→helper. Concretely: each edge carries `etype` + a direction bit; the gate consumes an edge-type embedding. Caller→helper and a reverse helper→caller edge are both emitted (reverse down-weightable), alongside the existing shared-data edges.
4. **Propagation placement:** helpers + call edges live in the **cross-hyperedge propagation layer** (the rebuild's G-HAN), feeding context into each interaction's pooled embedding *before* the MLP head — the per-hyperedge `AttentionPooling`/`LocalizationHead` path stays as-is.

**Measurement approach (already executed, reusable as the builder's validator):** 1-hop internal-callee resolution via `nhs.resolve_all_functions` + `find_state_var_accesses`; dedup per `(project_key, contract)`; the script doubles as a schema-population dry-run.

**Open question for you before build:** scope stays strictly 1-hop (as specified). Note 704/976 edges point to new helpers and 272 to existing interactions — confirm both edge kinds are wanted (interaction↔interaction call edges, not just interaction→helper).

---

## TASK 10 — Full contract-graph construction (plan + measured balance/size)

### Measured numbers FIRST — `scratch/audit_task10_measure.py` (regenerated the full pool; **validated 12,127 vs known 12,098**, the 29 gap = near-dup exclusions I intentionally skipped)

| Quantity | Value |
|---|---|
| Constructable **positives** | 310 |
| Constructable **negatives** (full pool, Tier-A 1,413 + Tier-B 10,714) | **12,127** |
| **Interaction-level class balance** | **1 : 39.1** (vs current sampled **3 : 1**) |
| Contract-graphs total | **1,980** |
| …with ≥1 positive | 214 |
| …**all-negative (zero positive)** | **1,766 (89%)** |
| Interactions per graph | min 1, median 4, mean 6.3, max 52, p90 16 |
| …with-positive graphs | median 6, mean 7.9, max 31 |
| …all-negative graphs | median 4, mean 6.1, max 52 |

**Two concrete red flags the real numbers expose (the audit's estimate did not):**
- **89% of contract-graphs are all-negative.** Building one graph per contract over the full pool means the model overwhelmingly trains on graphs with no positive — and if you *exclude* them you reintroduce the "graph contains a positive" shortcut. This is the central design fork, now quantified.
- **Test-scaffolding contamination.** The largest graphs are not real contracts: `console` (40, Hardhat console.sol), `ElementTest` (52), `TroveManagerTester` (32), `TestAMM` (30), `PerpetualProxy`/`CurveAMO_V2_Non_Impl` mocks. The Tier-B pool pulls in test/mock/console code. **A construction-time filter (drop `*Test`, `*Tester`, `console`, mock/interface-only contracts) is required before any Task-10 build** or these dominate the negative class.

### Proposed construction (build pending), integrated with Task 5
One graph per `(project, contract)` containing: **all** constructable interaction hyperedges (pos + neg) → **+ Task-5 helper nodes** → **+ call edges + shared-data edges**. Pipeline order: enumerate full constructable set (the validated 12,127 + 310) → apply scaffolding filter → attach helpers/edges (Task 5 builder) → emit `*_contract_graphs.json`. Splits stay project-disjoint (reuse existing Union-Find; **first resolve the `Box`/vfp_00189 leakage** from the foundations audit, since contract-level graphs make it active).

### Imbalance-handling — 3 options with tradeoffs (no pick; your call)

| Option | How | Pros | Cons / risks |
|---|---|---|---|
| **A. Weighted / focal loss** | Class weight ≈ 39:1 or focal-loss γ on the per-interaction BCE; every graph kept whole and used every epoch. | Simplest; zero sampling machinery; all data seen; graph completeness trivially preserved. | 39:1 weight → noisy, overconfident-negative gradients; heavy threshold re-tuning; MoE experts may still collapse to majority. |
| **B. Graph-level balanced batch sampling** | Always include all 214 with-positive graphs; per epoch sample a rotating subset of the 1,766 all-negative graphs to hit a target effective ratio (e.g. 3:1–10:1). **Never split a graph** — sampling is at graph granularity, each chosen graph stays complete. | Controls imbalance to a sane range; preserves every single graph's completeness (Task-5/10 integrity intact); positives seen every step. | All-negative graphs under-sampled → calibration drift on clean contracts (the OOD-FPR axis we care about); needs a coverage schedule so all negatives are eventually seen. |
| **C. MoE load-balancing tuned to 1:39** | Keep all data; size expert capacity factor + auxiliary load-balance loss for the real skew; optionally a positive-routing guarantee so ≥1 expert specializes on positives. | Uses the rebuild's MoE head directly; no data dropped; can co-exist with mild class weighting. | Most tuning-sensitive; experts can still collapse without a positive-routing constraint; balance-loss weight interacts with the 39:1 skew in non-obvious ways; hardest to debug. |

**Recommendation framing (not a decision):** B preserves the graph-completeness the rebuild is built on while keeping imbalance trainable, and is the cleanest to reason about for the OOD-FPR metric; A is the fastest to prototype as a baseline; C is the most aligned with the MoE head but the riskiest to land. A sensible sequence is **A as a baseline → B as the primary → C only if the MoE head needs it** — but all three depend first on the scaffolding filter and the `Box` leakage fix above.

---

## What needs your sign-off before any code
1. **Task 8 follow-up** (separate task): re-type FORGE with real SWC families + a `REVIEW` bucket, and adjudicate the 42 defaulted / non-security items. (Read-only audit done; changes not made.)
2. **Task 5 build**: the `NODE_HELPER` + contract-graph schema and the 1-hop call-edge builder (new files, not edits to `extract_features.py`).
3. **Task 10 build**: full-pool contract-graph construction **gated on** (a) a test/mock scaffolding filter and (b) the `Box`/vfp_00189 split-leakage fix, plus your choice of imbalance strategy (A/B/C).
