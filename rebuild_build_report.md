# HyperVul Rebuild — Step 0 / 1 / 2 Build Report

> **Date**: 2026-06-21  **Status**: groundwork + both builds executed. **No training run yet** — paused for your schema sanity-check (examples below) and one newly-found leakage decision before compute is spent.
> Originals untouched. New artifacts: `data/splits_clean/`, `data/contract_graphs/`, `scripts/build_contract_graphs.py`, `model/contract_graph_data.py`. Evidence/logs in `scratch/`.

---

## STEP 0 — Shared groundwork (done)

### 0a — Box / vfp_00189 leakage fix
6 train Box negatives moved to test; **test now holds all 14 Box items** (4 pos + 10 neg in the curated split). At the contract-graph level the whole `Box` contract resolves to **test** (positives define the project split), so the leakage is structurally closed. Moved: `maxWithdraw, removeFunding, addFunding, _debtBalance, addToken, maxRedeem`.

### 0b — Scaffolding filter (drop list applied)
**167 contracts / 1,057 interactions, every one with 0 positives** → removes only negatives. All match `*Test/*Tester/*Harness/*Fixture/*Stub/*Mock/*Fake/*Example` or `console`. Largest: `ElementTest`(52), `console`(40), `ComptrollerHarness`(35), `TroveManagerTester`(32), `EchidnaTester`(28). I checked for `Test`/`Mock` appearing inside real words — none caught. Full list: `scratch/scaffold_candidates.json`. **0 of these were in the existing curated splits** (mocks live only in the Tier-B full pool), so Step 0b affects only the Task-10 build.

### 0c — Task-8 non-security exclusions (removed, not relabeled)
5 rows / 4 functions dropped (`FlashLoans.flashLoan` appeared twice):

| Item | vfp | finding |
|---|---|---|
| FlashLoans.flashLoan (×2) | vfp_00281 | "Functionality is Blocked" / "Does Not Follow ERC-3156" |
| OctoDistributor.withdrawAllAgentTokens | vfp_00084 | "works incorrectly" |
| OctoDistributor.transferHiringDistributions | vfp_00084 | "doesn't work when agent token is address(0)" |
| MainFeeDistributor.swapLzToken | vfp_00237 | "always revert because of interface mismatch" |

I dropped **only these four explicitly-named clearly-functional items.** The other 38 defaulted FORGE items (DoS/access-control/economic) are mistyped-but-still-security and were **kept** (their *type* is wrong, not their positive status) — that re-typing is the separate Task-8 follow-up.

### Cleaned splits (`data/splits_clean/`)
| split | base pos/neg | clean pos/neg |
|---|---|---|
| train | 223 / 651 | **218 / 645** |
| val | 38 / 152 | 38 / 152 |
| test | 45 / 131 | **45 / 137** |

---

## STEP 1 — Task 5 build: NODE_HELPER + call-graph edges

`scripts/build_contract_graphs.py` implements the schema (additive `NODE_HELPER`, contract-graph container, **both** edge kinds — interaction→helper and interaction↔interaction call edges — with a learnable `direction` field for G-HAN's gate; 1-hop scope).

**Re-measured on post-Step-0 data (`scratch/audit_task5_measure.py data/splits_clean`):**

| Split | Contracts | NEW helper nodes (tot/med/max) | Call edges (tot) | →existing / →helper | ≥1 helper |
|---|---:|---|---:|---|---:|
| train | 287 | 358 / 1 / 8 | 609 | 176 / 433 | 55% |
| val | 51 | 95 / 1 / 12 | 178 | 57 / 121 | 65% |
| test | 56 | 114 / 1 / 17 | 189 | 39 / 150 | 61% |
| **all** | **394** | **567 / 1 / 17** | **976** | **272 / 704** | **57%** |

**The +567 estimate holds exactly** (Step-0 changes don't alter helper structure). Over the *sampled-split* scope it's 567 helpers; over the *full contract-graph* scope (Step 2) it's 1,796 (more interactions → more helpers).

---

## STEP 2 — Full contract-graph build

`data/contract_graphs/{train,val,test}.json`. Pipeline: scaffolding filter → full constructable pool → Task-8 exclusions → attach helpers + call edges + shared-data edges → project-level split.

### Built stats
| | graphs | pos | neg | helpers | edges |
|---|---:|---:|---:|---:|---:|
| **all** | **1,927** | **298** | **12,108** | **1,796** | **60,613** |
| train | 1,616 | 215 | 10,530 | 1,481 | 51,281 |
| val | 167 | 38 | 806 | 143 | 4,343 |
| test | 138 | 41 | 732 | 172 | 4,639 |
| unassigned* | 6 | 4 | 40 | 0 | 350 |

\* 6 contracts whose positive isn't present in the curated splits (so no project→split signal); default to train pending assignment — minor.

**Interaction class balance: 1 : 40.6** (matches the measured 1:39.1; the small delta is the Step-0 exclusions). Positive count reconciles exactly: **303 distinct positive keys − 4 Task-8 − 1 genuinely unresolvable** (`bVault.deposit`, the known extract-features "function-not-found" item) = **298**.

### Singleton vs multi (the Step-2 measurement you asked for)
| Graph class | count | singleton (1 interaction, **no edges**) | multi (≥2) |
|---|---:|---:|---:|
| **all-negative** | 1,717 | **357 (21%)** | 1,360 |
| with-positive | 210 | 15 | 195 |

So 21% of all-negative graphs are inert singletons (nothing to propagate over); 79% have ≥2 interactions and real shared-data structure.

### Imbalance handling
**Option A — implemented baseline** (`model/contract_graph_data.py`): weighted `BCEWithLogitsLoss`, `pos_weight = neg/pos`.
- train `pos_weight = 49.0` (full) → effective ~1:1; `sqrt` variant = 7.0 (softened); focal-loss switch included.

**Option B — structural stub (not tuned)**: graph-level balanced sampler, whole graphs only, rotating coverage of all-negative graphs. **Real finding from the stub:** the with-positive graphs *already* contain 944 negatives for 215 positives (**~1:4.4**), so a 3:1 target would exclude **every** all-negative graph. Practically, Option B's knob mostly decides *how many of the 1,766 all-negative graphs to admit*, from 0 (≈1:4.4) upward — useful context for tuning next.

---

## Example built graphs (schema sanity-check)

**EX1 — `FORGE::vfp_00189::Box` (test)** — 4 pos / 11 neg / **15 helpers** / 128 edges (call 62, shared_state 53, shared_callee 13). The reentrancy positives `flash, allocate, deallocate, reallocate` now co-reside with — and call-edge into — exactly the helpers the foundations audit flagged as previously **nonexistent nodes**:
```
[interaction] flash        label=1  states=[_cachedNavDepth]            (3 calls)
[interaction] allocate     label=1  states=[asset,isAllocator,maxSlippage,oracles]
[helper]      _startNavCache           states=[_cachedNav,_cachedNavDepth]
[helper]      _endNavCache             states=[_cachedNavDepth]
[helper]      _increaseSlippage        states=[accumulatedSlippage,maxSlippage,...]
[helper]      totalAssets              states=[_cachedNav,_cachedNavDepth]
[helper]      _winddownSlippageTolerance states=[shutdownSlippageDuration,...]
```
This is the Task-5 BLOCKING gap closed: `flash`→`_startNavCache`/`_endNavCache` (NAV-cache state mutation) now exists as nodes + call edges.

**EX2 — `DAPP::…Liquity…::TroveManager` (test)** — 1 pos / 30 neg / **17 helpers** / 339 edges. The positive `redeemCollateral` and `liquidateTroves` are call-wired into their internal state-mutating helpers:
```
liquidateTroves --call--> _redistributeDebtAndColl
liquidateTroves --call--> _updateSystemSnapshots_excludeCollRemainder
liquidateTroves --call--> _sendGasCompensation
getCurrentICR  --call--> getPendingLUSDDebtReward
```
Indirect-reentrancy reachability that was structurally impossible under isolated hyperedges.

(EX3 available on request — a tight multi-interaction DAppSCAN contract — but EX1/EX2 cover the Box cluster + helper-heavy cases you asked for.)

---

## ⚠️ One newly-found issue to decide before training

**Cross-split duplicate-source negatives.** Because contract-graphs are per-project (no global dedup), identical shared/boilerplate contracts (`Timelock`×17 projects, `MasterChef`×10, `GovernorAlpha`×9, `Vault`×8, ERC20s) appear in graphs across **different splits**. Measured: **149 distinct negative source-hashes span >1 split, touching 552 node instances (307 train / 111 val / 134 test). 0 positives are affected.**

This is the same class as the Box leakage, negative-side only. I did **not** auto-fix it (outside the Step-0 spec). Recommended one-pass fix before training: **dedup interaction nodes by normalized source-hash, assigning each unique source to a single split** (priority test > val > train, mirroring the Box rule) and pruning duplicates from the others. Low-stakes (no positives) but it removes a trivial-negative inflation from the eval split.

---

## Before training starts — prerequisites
1. **Your sign-off on the two example graphs above** (schema looks right?).
2. **Decide the cross-split dup-source dedup** (recommend: apply it).
3. **Embedding encode pass** — SmartBERT-v3 over each node's `function_source` (~14k interaction + 1.8k helper spans); structure is ready, the hook is in `contract_graph_data.py`.
4. **Assign the 6 unassigned graphs** (trivial).
5. **Build the G-HAN model** with the edge-direction gate (the next build) — then train Option A, then evaluate before tuning Option B.

I've paused here rather than spend encode/train compute, per your instruction to sanity-check the graphs first.
