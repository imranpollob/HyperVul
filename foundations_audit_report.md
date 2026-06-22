# HyperVul — Foundations Audit (Pre-Rebuild Viability Check)

> **Date**: 2026-06-20  **Mode**: read-only investigation (no model/extraction/augmentation/label/split code modified).
> **Rebuild under consideration**: isolated per-interaction hyperedges → shared contract-level hypergraph + gated cross-hyperedge propagation + MoE head.
> Evidence scripts live in `scratch/audit_*.py` (each imports the project's own AST helpers / checkpoints; nothing was rewritten).

---

## 0. Executive summary — what's BLOCKING

| # | Finding | Severity |
|---|---|---|
| **5** | **The rebuild's core mechanism cannot structurally reach most indirect-reentrancy cases it exists to fix.** Of 41 caller→state-mutating-helper relationships across the 23 test reentrancy positives, **26 (63%) point to a helper that is *not constructable* — it has no hyperedge at all**, so there is no node for cross-hyperedge propagation to touch. Among the 15 where the helper *is* a hyperedge, 5 share **zero** nodes with the caller. The caller→callee *invocation* relation is never modeled by either the current or the planned (shared-node) graph. | **BLOCKING** |

Everything else is DEGRADING or INFORMATIONAL. The single blocker is structural and is the heart of the rebuild's premise: **propagation over shared *data* nodes (state vars / callees) is the wrong connector for indirect reentrancy** — the connector that matters is the *call edge*, which is absent. The rebuild needs an explicit design decision (add call-graph edges + represent non-constructable state-mutating functions) before it can deliver on its motivating use case.

Two DEGRADING findings are close behind and will distort the rebuild if ignored: **phantom external calls** (Task 4d, confirmed on real Aave data) inflate connectivity and hyperedge size, and **FORGE per-type labels are unreliable** (Task 8).

---

## GROUP 1 — Representation capacity

### TASK 1 — Statement-order preservation through augmentation — **INFORMATIONAL (PASS)**

**Definitive answer: NO. No augmentation step can change the relative order of state reads / external calls / state writes.** Two independent guarantees:

1. **None of the four transforms reorder.** [augment_train_split.py:42-121](scripts/augment_train_split.py#L42-L121):
   - `clean_comments_and_whitespace` — strips comments, normalizes spaces; line order preserved.
   - `literal_substitution` — in-place token swaps (`0x0↔address(0)`, `uint↔uint256`).
   - `inject_inert_statement` — inserts `uint256 _inert_val_N = N + N+1;` immediately after `{` or before `}`; it references no state var and makes no call, so it never appears in the event sequence and cannot move a real event.
   - `rename_local_vars` — renames locals only (state vars, call receivers, builtins excluded).

2. **A hard sequence-equality gate discards any variant whose event order differs.** [augment_train_split.py:530-541](scripts/augment_train_split.py#L530-L541): `get_sequence_of_events` ([:181](scripts/augment_train_split.py#L181)) builds the ordered list of `("read"|"write"|"call", name)` tuples for original and variant (renamed vars mapped back), and `if mapped_var_seq != original_seq: discard`. The accept path is reachable only after this check passes. Constructability (check a), call-count + state-set + cross-contract (check b) are also re-verified per variant ([:514-528](scripts/augment_train_split.py#L514-L528)).

No action. Augmentation is order-safe.

### TASK 2 — Encoder context boundary — **DEGRADING**

**Per node, the encoder sees a single isolated span — no surrounding context — and real functions are being truncated.** [extract_features.py:249-286](scripts/extract_features.py#L249-L286):
- **Function node** = `nhs.node_text(func_node)` — *only the flagged function's own signature + body*. No sibling functions, no contract-level state-variable declarations, no inheritance-chain bodies. Encoded at `max_length=256, truncation=True`.
- **State-var node** = the string `"<type> <name>"` (e.g. `"IERC20 token"`) — declaration site context absent.
- **Callee node** = the raw `call_text` (e.g. `"IAToken(aToken).mint(...)"`), `max_length=64`.

**Literal example fed to the encoder** — `LendingPool.deposit` (test, SWC-107 positive), from `scratch/audit_task2_span.py`:
```
function deposit(address asset, uint256 amount, address onBehalfOf, uint16 referralCode) external override {
    _whenNotPaused();
    ReserveLogic.ReserveData storage reserve = _reserves[asset];
    ValidationLogic.validateDeposit(reserve, amount);
    ... reserve.updateState(); reserve.updateInterestRates(...);
    IAToken(aToken).mint(onBehalfOf, amount, reserve.liquidityIndex);
    IERC20(asset).safeTransferFrom(msg.sender, aToken, amount);   // <- the reentrancy-relevant transfer
    emit Deposit(...);
}
```
This span tokenizes to **299 tokens > 256 → it is truncated**: the trailing `safeTransferFrom` (and `emit`) are dropped from the function embedding. State-var nodes are just `_reserves`, `_usersConfig`.

**Implication for the rebuild:** all cross-function/relational signal must come from *graph structure*, because it is provably absent from the node embeddings. And ~the largest functions lose their tail to truncation regardless of graph design. (Diagnostic 2 in [run_diagnostics.py](scripts/run_diagnostics.py) already measures truncation on positives.)

---

## GROUP 2 — Construction algorithm correctness

### TASK 3 — Constructability gate — **INFORMATIONAL (PASS), with one DEGRADING edge case**

Gate: `constructable = has_state_access AND has_external_call` ([forge_hyperedge_ast_analysis.py:977](scripts/forge_hyperedge_ast_analysis.py#L977), [dappscan_hyperedge_ast_analysis.py:878](scripts/dappscan_hyperedge_ast_analysis.py#L878)). "State access" is **name-based**: `find_state_var_accesses` ([negative_hyperedge_sampling.py:506-523](scripts/negative_hyperedge_sampling.py#L506-L523)) counts any `identifier` whose name is a declared state var (inherited included).

Synthetic tests (`scratch/audit_gate_tests.py`) — all **caught**:

| Case | state_accessed | constructable |
|---|---|---|
| mapping write `balances[msg.sender] -= amt` | `balances`, `token` | ✅ True |
| nested struct field `userInfo[x].amount += 1` | `userInfo`, `pool` | ✅ True |
| array element `queue[0] = oracle.latestAnswer()` | `queue`, `oracle` | ✅ True |
| storage-pointer alias `Info storage s = userInfo[x]; s.amount = …` | `userInfo`, `pool` | ✅ True (constructable) |

The base identifier of a mapping/struct/array is the state-var name, so name-matching catches all of them. **Edge case (DEGRADING):** with a storage-pointer alias, the *write through the alias* (`s.amount = …`) is recorded against the local `s`, not the underlying state var; the only access logged for `userInfo` is the alias-creation **read**. Constructability still holds, but the read/write classification (used for reentrancy ordering) misattributes the mutation. Minor, but relevant to any order-aware rebuild.

### TASK 4 — Pattern handling — **DEGRADING** (verdicts from `scratch/audit_gate_tests.py`)

| Pattern | Verdict | Evidence |
|---|---|---|
| **a. Modifier state/calls** | ❌ **Not handled** | `nonReentrant` modifier reads/writes `locked`; analysis of `pull()` returns `state_accessed=['token']` — **`locked` absent**. Traversal is over `func_node` only; modifier bodies live in separate `modifier_definition` nodes and are never followed. Any state/call logic inside a modifier is invisible. |
| **b. Inline assembly** | ❌ **Not handled** | A function whose only external interaction is a Yul `call(...)` inside `assembly{}` returns `ext_calls=[]` → **`constructable=False`**, i.e. it is silently dropped from the dataset. `find_external_calls_ast` matches `call_expression` nodes; Yul calls are a different node type. Directly relevant to delegatecall/proxy patterns (note SWC-112 already has **0** test positives). |
| **c. Inheritance** | ✅ **Correct** | `resolve_all_state_vars` / `resolve_all_functions` ([:213-272](scripts/negative_hyperedge_sampling.py#L213-L272)) recurse through `base_names`; child overrides win (`result.update(info.functions)`). Synthetic child using parent's `vault`/`poolId` resolved correctly. |
| **d. `using X for Y` library calls** | ⚠️ **Heuristic, over-detects** | Classified by the same method-name allowlist + receiver-type guess, with no awareness of the `using` directive. A library method **not** in the allowlist on a value-typed receiver (`total.add(x)`) is correctly ignored; but a library/struct method whose name **is** in the allowlist, or any call on a receiver whose type merely starts uppercase, is flagged external. **Confirmed on real data:** `LendingPool.deposit` records `reserve.updateState()`, `ValidationLogic.validateDeposit(...)`, `reserve.updateInterestRates(...)` as external calls — these are library/struct calls, **phantom externals**. |
| **e. Multiple external calls** | ⚠️ **Collapsed, order lost** | `find_external_calls_ast` returns a list; the function becomes **one** hyperedge with multiple callee nodes pooled order-invariantly (`AttentionPooling`). `LendingPool.deposit` → 7 callee nodes in one edge. The localization head keeps `(state × callee)` pairs but still encodes **no ordering** between a state write and an external call — the exact thing reentrancy depends on. |

**Phantom externals (d) are not cosmetic:** they inflate hyperedge size (Task 7) and node-overlap (Task 6), and feed `is_cross_contract`. Recommend tightening `_classify_call`/`_is_interface_or_contract_type` ([:428-503](scripts/negative_hyperedge_sampling.py#L428-L503)) before trusting any post-rebuild connectivity numbers.

### TASK 5 — Indirect-reentrancy reachability — **BLOCKING** (CORE VIABILITY CHECK)

**Note on §3.7's "~3 missed":** that figure is checkpoint/threshold-specific, not a stable structural failure. Re-running the §3.7 base model (`iteration1_checkpoint.pt` + `threshold_config.json`, thr=0.1024) gives **100% recall on all 23 reentrancy positives** (`scratch/audit_task5_misses.py`). So "which 3 the model missed" is the wrong question; the right one is **whether the construction can even represent indirect reentrancy**. Answer below (`scratch/audit_task5_structural.py`).

For each test reentrancy positive I found every internal helper it calls that touches state, built the helper's own hyperedge, and checked node-sharing with the caller. **41 caller→state-mutating-helper relationships** across the 23 positives:

| Outcome | Count | Meaning for the rebuild |
|---|---:|---|
| Helper is **not constructable** (no external call of its own → **no hyperedge exists**) | **26 / 41** | Nothing in the contract graph represents this state mutation. Cross-hyperedge propagation has no node to reach. Of these, only 8 even share a state var with the caller. |
| Helper **is constructable** *and* shares ≥1 node with caller | 10 / 41 | Shared-node propagation *could* connect them (e.g. Liquity `BorrowerOperations._moveTokensAndETHfromAdjustment` → `_withdrawLUSD`/`_repayLUSD`, sharing `activePool`). |
| Helper **is constructable** but shares **no** node with caller | 5 / 41 | Even a node-sharing scheme misses it (e.g. `StopLimit.modifyOrder`→`handlePermit`; `StakingV2.deposit`→`_fundRebalanceSize`). |

**Worked example — the dominant cluster, `Box` (vfp_00189):** `flash`/`allocate`/`deallocate`/`reallocate` delegate their state mutations to nav-cache/slippage helpers (`_startNavCache`, `_endNavCache`, `_increaseSlippage`, `totalAssets`, …). **Every one of these helpers is non-constructable** (pure state mutation, no external call) → **none exists as a hyperedge** → a shared contract-level hypergraph built from constructable interactions contains *no representation of where Box actually mutates state*. Propagation cannot reach what isn't there.

**Definitive verdict:** the rebuild's planned connector — cross-hyperedge propagation over **shared data nodes among constructable hyperedges** — structurally cannot fix indirect reentrancy for the majority (≥26/41) of real helper-mutation relationships, and is unreliable (5/15) even when the helper is constructable. To make the mechanism reach its motivating cases the rebuild must **(1) materialize nodes/edges for state-mutating helpers regardless of constructability, and (2) add an explicit caller→callee call-graph edge type.** Shared-node propagation alone is insufficient. **This must be resolved in the design before the rebuild proceeds.**

---

## GROUP 3 — Structural connectivity (snapshot under CURRENT construction)

> ⚠️ These are computed under the present construction logic. Because of Task 4d (phantom externals) and 4b (dropped assembly), overlap and size are **likely overstated**; both must be **re-derived after the Task 4 fixes**. From `scratch/audit_task67.py`, on the 332 constructable positive interactions.

### TASK 6 — Hyperedge overlap — **INFORMATIONAL (good where it exists)**

Among contracts with ≥2 constructable interactions, a pair "overlaps" if it shares a state var or a callee:

| Split | Multi-interaction contracts | With ≥1 overlapping pair | Overlapping pairs / total |
|---|---:|---:|---:|
| train | 40 | 40 (100%) | 129/156 (82.7%) |
| val | 9 | 9 (100%) | 24/26 (92.3%) |
| test | 12 | 12 (100%) | 30/35 (85.7%) |
| **all** | **61** | **61 (100%)** | **183/217 (84.3%)** |

**Where a multi-interaction contract exists, it is essentially always connected** (100% of such contracts; 84% of all pairs). The caveat is from Task 1's density work: most contracts are singletons, so this richly-connected regime is the minority — and some of the 84% is driven by shared *phantom* callees (Task 4d), so treat 84% as an upper bound.

### TASK 7 — Hyperedge size — **INFORMATIONAL**

| Split | state vars (med/mean/max) | ext calls (med/mean/max) | combined (med/mean/max/p90) |
|---|---|---|---|
| train (234) | 3 / 3.33 / 11 | 2 / 2.89 / 13 | 5 / 6.23 / 19 / 11 |
| val (44) | 3 / 4.16 / 14 | 3 / 3.80 / 10 | 6 / 7.95 / 24 / 14 |
| test (50) | 2 / 2.94 / 9 | 2 / 2.74 / 10 | 5 / 5.68 / 18 / 10 |
| **all (332)** | **3 / 3.40 / 14** | **2 / 2.98 / 13** | **5 / 6.38 / 24 / 11** |

Tight core with a moderate tail (p90 combined = 11, max 24). Callee counts are inflated by phantom externals (Task 4d), so true sizes are somewhat smaller. Useful for sizing the localization `(S×C)` grid and any per-edge attention budget.

---

## GROUP 4 — Data & label quality

### TASK 8 — Label sourcing audit (15 random positives, seed 42, DUBIOUS excluded) — **DEGRADING** (`scratch/audit_task8.py`)

**DAppSCAN: 9/9 sound.** Each recorded SWC type matches an inline `// SWC-xxx` annotation in the source, and all 9 functions are **CONFIRMED** in `dappscan_label_review.md` (cross-checked by name). DAppSCAN labels derive directly from the auditors' in-source SWC annotations — reliable.

**FORGE: only ~2/6 type-correct, and ≥3 questionable as security positives.** Pulling each item's actual `finding_title` from `forge_ast_hyperedge_detailed.json`:

| Item | Recorded type | Actual finding(s) on that function | Verdict |
|---|---|---|---|
| DelegationMetaSwapAdapter.swapTokens (vfp_00288) | SWC-107 | "**Re-Entrancy Risk in swapTokens()**" | ✅ match |
| AntiSandwichHook._beforeSwap (vfp_00220/29) | SWC-114 | "Asymmetric First In-Block Swap Init → Stale State" (≈ tx-order) / "Infinite Loop in Tick Iteration" | ⚠️ partial |
| LikwidMarginPosition.modify (vfp_00058) | SWC-107 | "borrow level check blocks positive margin adjustments"; "inconsistent level check" | ❌ not reentrancy |
| OctoDistributor.withdrawAllAgentTokens (vfp_00084) | SWC-107 | "withdrawAllAgentTokens works incorrectly" | ❌ functional bug |
| OctoDistributor.transferHiringDistributions (vfp_00084) | SWC-107 | "doesn't work when agent token is address(0)" | ❌ functional bug |
| FlashLoans.flashLoan (vfp_00281) | SWC-107 | "Flashloan Functionality is Blocked"; "Does Not Follow ERC-3156" | ❌ **not a security vuln** |

**Two distinct problems:** (1) FORGE function-level **SWC type** labels are frequently wrong — they appear assigned from a VFP-level interaction/CWE mapping, not the function's specific finding — so the per-type recall table (report §3.6) is unreliable for FORGE. (2) At least **3 FORGE positives (flashLoan, both Octo)** are flagged on **functional/correctness** findings, not security vulnerabilities → they are questionable *binary* positives. Recommend a FORGE-wide finding→function→type re-audit before per-type claims, and review of functional-bug findings as positives. (Sample type-match rate: 11/15 lenient, 10/15 strict.)

### TASK 9 — `is_cross_contract` reliability — **INFORMATIONAL (reliable)** (`scratch/audit_task9.py`)

Recomputed via the same AST method as the ChainlinkPriceFeed case (`nhs.check_is_cross_contract`) for **all 1,234 resolvable items** (6 unresolved = the same items that fail feature extraction):

- **Disagreement rate: 0.16% (2 / 1234).**
  - `bVault.deposit` (test, label=1): recorded `False`, reconstruction `True` (calls `token.balanceOf`/`safeTransferFrom` on an `IERC20` — genuinely cross-contract; recorded value is the mislabel).
  - `Staking.withdrawHorseInStable` (test, label=0): recorded `True`, reconstruction `False`.
- Notably, the previously-flagged **ChainlinkPriceFeed item does *not* systemically disagree** under the consistent method — its earlier flag was bundle-sensitive. The field is trustworthy; no systemic correction needed.

---

## GROUP 5 — Design consistency

### TASK 10 — Negative sampling fit-for-purpose — **DEGRADING**

**Current strategy** ([negative_hyperedge_sampling.py:1087-1181](scripts/negative_hyperedge_sampling.py#L1087-L1181), `negative_sampling_report.md`): negatives are *constructable single-function hyperedges* (same gate as positives), sampled to a **3:1** neg:pos target (3 × 310 = 930), with the cross-contract ratio matched to the positives' ~47.4% (±tolerance), drawn **Tier-A first** (non-vulnerable functions in the *same file* as a positive; >90% difflib-similar duplicates excluded), then Tier-B (same project), then OZ — OZ dropped if "structurally atypical." Plus 600 clean library/Aave negatives. Pool available: **12,098** constructable codebase negatives (Tier-A 1,389 / Tier-B 10,709), sampled down to 930. **Today positives and negatives are constructed identically, so there is no mismatch.**

**The mismatch the rebuild introduces:** keeping **all** positive interactions per contract (embedded in a connected contract graph) while **sampling** negatives breaks construction symmetry. For the negative class to be built the same way, each negative hyperedge must also sit in its **own full contract graph**. Consequences:

- **Symmetric, interaction-level:** negatives grow **930 → up to 12,098 (~13×)**; class balance moves **3:1 → ~39:1** (or ~4.5:1 if restricted to Tier-A only). Severe imbalance for the MoE head.
- **Keep 3:1 by sampling, but give positives full-contract context:** then every *graph* the model trains on is built around a vulnerable contract, while sampled negatives are isolated → the model can learn **"this contract graph contains a positive"** as a shortcut (contract-level positivity leakage), inflating metrics.

**Required decision before the rebuild:** define the graph **unit** consistently for both classes. The clean option is *contract graph, classify each constituent hyperedge*, so positives and negatives in the **same** contract share one graph naturally — but then all-negative contracts must be included too (or their exclusion will bias the graph distribution). Including them pulls in the Tier-B 10,709; excluding them reintroduces the shortcut. This is a real fork, not a tuning detail.

---

## Appendix — severity roll-up

| Task | Severity | One-line |
|---|---|---|
| 1 | INFORMATIONAL | Augmentation is order-safe (no reordering transform + hard sequence gate). |
| 2 | DEGRADING | Nodes encoded in isolation; real functions truncated at 256 tokens. |
| 3 | INFORMATIONAL (+minor DEGRADING) | Gate catches mapping/struct/array; storage-alias write misattributed. |
| 4 | DEGRADING | Modifiers & assembly invisible; phantom externals (real data); multi-call order lost. |
| **5** | **BLOCKING** | Shared-node propagation can't reach ≥26/41 indirect-reentrancy helper mutations; call edge unmodeled. |
| 6 | INFORMATIONAL | 84% pair-overlap where multi-interaction contracts exist (upper bound; re-derive after Task 4 fix). |
| 7 | INFORMATIONAL | Hyperedge sizes modest (combined median 5, p90 11); inflated by phantom callees. |
| 8 | DEGRADING | FORGE per-type labels unreliable; ≥3 FORGE positives are non-security functional bugs. |
| 9 | INFORMATIONAL | `is_cross_contract` reliable (0.16% disagreement). |
| 10 | DEGRADING | Keep-all-positives vs sampled-negatives → construction mismatch; needs a unit decision. |
