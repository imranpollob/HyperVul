# HyperVul — Pre-Rebuild Investigation Report

> **Date**: 2026-06-20  
> **Scope**: Read-only investigation of four open questions from the project report.  
> No model code, labels, or split files were modified.

---

## Task 1 — Real Interaction Density per Contract

Two separate measurements as requested. These numbers come directly from the AST detail files; they are the ground truth, not approximations.

### 1(a) — Primary: True interaction density (before any sampling decisions)

Source files: `experiments/results/forge_ast_hyperedge_detailed.json` (301 entries) and `experiments/results/dappscan_ast_detailed.json` (333 entries). Constructability gate = `constructable == True` in both files.

**FORGE — all 88 constructable locations from 303 VFPs:**

| Grouping | (vfp_id, contract) pairs with ≥1 constructable interaction |
|:---|:---:|
| Total groups | 48 |
| Distribution | 1 interaction: 28 groups (58%) · 2: 12 · 3: 2 · 4: 3 · 5: 1 · 6: 1 · 7: 1 |
| Min / Median / Mean / Max | 1 / 1 / **1.8** / 7 |

**DAppSCAN — all 244 constructable locations from 333 audit findings:**

| Grouping | (project_root, contract) pairs with ≥1 constructable interaction |
|:---|:---:|
| Total groups | 170 |
| Distribution | 1 interaction: 129 groups (76%) · 2: 23 · 3: 10 · 4: 4 · 5: 3 · 8: 1 |
| Min / Median / Mean / Max | 1 / 1 / **1.4** / 8 |

**Broken out by which split the VFP/project ended up in:**

| Source | Split | Constructable interactions | (vfp/proj, contract) groups | Groups with >1 | Median | Mean | Max |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| FORGE | train | 53 | 34 | 10 | 1 | 1.6 | 7 |
| FORGE | val | 10 | 5 | 2 | 1 | 2.0 | 5 |
| FORGE | test | 25 | 9 | 8 | 2 | 2.8 | 6 |
| DAppSCAN | train | 182 | 123 | 30 | 1 | 1.5 | 8 |
| DAppSCAN | val | 34 | 23 | 7 | 1 | 1.5 | 3 |
| DAppSCAN | test | 25 | 21 | 4 | 1 | 1.2 | 2 |
| DAppSCAN | none (not in splits) | 3 | — | — | — | — | — |

Top multi-interaction contracts by density:

| Contract | Source | Split | Constructable interactions |
|:---|:---|:---|:---:|
| LimitOrderHook (vfp_00221) | FORGE | train | 7 |
| MasterChef | DAppSCAN | train | 8 |
| AntiSandwichHook (vfp_00220) | FORGE | test | 6 |
| CDEXStakingPool, UniswapV3Adapter, FraxPool | DAppSCAN | train | 5 |
| HyperCoreFlowExecutor (vfp_00156) | FORGE | val | 5 |
| Box (vfp_00189) | FORGE | test | 4 |
| Folio (vfp_00007), LikwidMarginPosition (vfp_00058) | FORGE | train | 4 |

**Bottom line for the rebuild:** The majority of contracts have exactly **1 constructable interaction**. Specifically: 58% of FORGE groups and 76% of DAppSCAN groups are singletons. Only **10/34 FORGE groups in train** (29%) and **30/123 DAppSCAN groups in train** (24%) have more than one interaction — meaning connected cross-edge message passing is only meaningful for about a quarter of the training contracts. The test split is especially thin: 4/21 DAppSCAN test groups (19%) and 8/9 FORGE test groups (89%) have >1 interaction, but the DAppSCAN test max is only 2. A shared-graph architecture will produce trivially disconnected graphs for most training contracts.

---

### 1(b) — Secondary: Sampled coverage

| Source | Constructable total (a) | In splits (positives only) | Coverage |
|:---|:---:|:---:|:---:|
| FORGE | 83 (deduplicated) | 83 | **100.0%** |
| DAppSCAN | 244 | 223 | **91.4%** |
| Codebase negatives | 12,098 (from sampling report) | 930 | **7.7%** |

FORGE: every constructable positive is in the splits — nothing was excluded.

DAppSCAN: 21 constructable positives (8.6%) did not make it into any split. These are not missing data; they were excluded during the leakage-constrained split construction.

Codebase negatives: 930/12,098 = 7.7% sampled. If the negative sampling gate were removed and all constructable codebase interactions kept, the negative pool would grow by ~13×. This is the growth headroom for a shared-graph approach that uses ALL interactions per contract rather than a 3:1 sampled subset.

> **Limitation note:** The 12,098 figure for codebase negatives is taken from `experiments/results/negative_sampling_report.md`. The pre-sampling full negative list is not stored on disk; only the 930 sampled items are in `negatives_in_codebase.json`. The 7.7% figure is a report-derived statistic, not recomputed from a stored file.

---

## Task 2 — Split Safety for Shared-Graph Requirement

**Contract-level three-way intersection check:** `train.json`, `val.json`, `test.json` were each iterated. Every item was keyed by `(project_root, contract)` for DAppSCAN old-format positives and `(vfp_id, contract)` for FORGE positives. Items without either key were keyed by `(source, file, contract)`.

**Result: 1 violation found.**

| Violation | Detail |
|:---|:---|
| Contract | `Box` |
| Split membership | TRAIN (6 items) **and** TEST (8 items) |
| Root cause | FORGE VFP `vfp_00189` / `Box.sol` — positives went to test; negatives were stored without `vfp_id` and went to train |

**Evidence:**

Train Box items (label=0, source=FORGE, file=Box.sol, no vfp_id):
- `maxWithdraw`, `removeFunding`, `addFunding`, `_debtBalance`, `addToken`, `maxRedeem`

Test Box items from vfp_00189:
- Positives (label=1): `flash`, `allocate`, `deallocate`, `reallocate`
- Negatives (label=0): `_withdrawRedeem`, `skim`, `_depositMint`, `_nav`

Confirmed: `vfp_00189.json` lists exactly `Box.sol` and `FundingAave.sol` as its affected files. The train negatives (`maxWithdraw`, etc.) are non-vulnerable functions from the **same** `Box.sol` as the test positives (`flash`, `allocate`, etc.).

**Why the Union-Find missed this:** The FORGE negatives from `Box.sol` were stored without a `vfp_id` field. The Union-Find and source-hash leakage checks in `make_splits.py` could not link these negatives to `vfp_00189` because there is no identifier tying them together. The normalized-source-hash check confirmed no function's source text appears in two splits — which is correct (different functions) — but does not detect that different functions from the same contract file are across the boundary.

**Impact under the current isolated-hyperedge model:** Limited. The model sees `Box.maxWithdraw` (train) and `Box.flash` (test) as completely independent items; there is no shared state or message passing between them during inference. The normalized source hashes are different so there is no direct feature leakage.

**Impact under a shared-graph rebuild:** High. If all interactions from `Box.sol` are embedded into a shared contract graph, the model would be trained on 6 of the contract's edges and then evaluated on 4 different edges from the same contract. The contract-level representation learned in training will directly inform the test evaluation — a clean generalization violation.

**All other contract pairs: no violations.** The 334 other (grouping-key, contract) combinations each appear in exactly one split.

---

## Task 3 — The 49 → 44 Positive Discrepancy, Resolved

There are **two separate steps** in the chain, not one. The discrepancy compounds from two independent causes.

### Step 1: split_report.md → test.json (49 → 45 positives; 127 → 131 negatives)

**What changed:** 4 SWC-104 items were relabeled from `label=1` to `label=0` directly in `test.json`. Total items remain 176.

**Evidence:** `test.json` contains exactly 4 items with `vtype='Unchecked Call Return (SWC-104)'` and `label=0`. These are the three `balanceOfy3CRVinWant` functions (StrategyDAI3pool, StrategyUSDC3pool, StrategyUSDT3pool) and `ChainlinkPriceFeed._getLatestRoundData`. All four have `file=N/A` — their source paths were also cleared when the correction was applied.

**Contradiction with documentation:** `experiments/results/label_correction_proposal.md` explicitly states on its header: *"No labels have been modified. The full list of affected items is presented for human confirmation before any changes are applied."* This statement is **false** — the labels were modified in test.json. The proposal was written before the correction was applied, but the data was changed without updating or superseding the proposal document.

**Impact on evaluation:** The 4 relabeled items ARE present in `test_features.json` (they survived feature extraction because their `normalized_source_hash` values matched items that had already been embedded in a prior feature-extraction run). They appear as negatives in the evaluated test set. The model assigns them P < 0.08 — well below every threshold tried — so they are evaluated correctly as true negatives under the current label. The label correction was effectively the right call; the documentation trail is the problem.

### Step 2: test.json → test_features.json (45 → 44 positives; 131 → 125 negatives)

**What changed:** 7 items are silently dropped in `scripts/extract_features.py` via `continue` statements. The function never logs which items were dropped or why.

**The 7 dropped items:**

| Label | Contract | Function | Drop reason |
|:---|:---|:---|:---|
| **POS** | Fund | finalizeGrant | **BUG** — misclassified as OpenZeppelin |
| NEG | bVault | depositETH | Function not found in source file |
| NEG | bVault | withdrawETH | Function not found in source file |
| NEG | Staking | emergencyWithdrawHorse | Function not found in source file |
| NEG | Staking | withdrawStar | Function not found in source file |
| NEG | Staking | safeSpeedTransfer | Function not found in source file |
| NEG | StakingRewardsV3 | _getSecondsInside | Function not found in source file |

**Root cause 1 — Bug (Fund.finalizeGrant):**  
`extract_features.py:193–198` determines `source_type` by checking if `'openzeppelin'` appears anywhere in the file path string. `Fund.sol`'s path is:
```
DAppSCAN-source/contracts/openzeppelin-Endaoment/endaoment-contracts-.../Fund.sol
```
The project is an OpenZeppelin-audited protocol named "openzeppelin-Endaoment". The string `'openzeppelin'` appears in the audit firm prefix of the directory name, not because the file is from the OpenZeppelin library. `extract_features.py` misclassifies it as `source_type = "OpenZeppelin"` and looks for the file at `PROJECT_ROOT / filepath` instead of `DAPPSCAN_ROOT / filepath`. The correct path exists; the wrong-prefixed path does not. The item is dropped with `"Warning: OpenZeppelin file ... not found."` in the logs. This is a real bug — Fund.finalizeGrant is a valid reentrancy positive that is silently excluded.

**Root cause 2 — Stale file paths (6 negatives):**  
For the 6 DAppSCAN negatives, `DAPPSCAN_ROOT / file` exists on disk. The file is found. But the target function name does not appear in the file's AST:
- `bVault.depositETH` / `bVault.withdrawETH`: the stored file (`bt-finance/bVault.sol`) contains only ERC20 interface functions, not the vault logic. Wrong Solidity file recorded for this function.
- `Staking.emergencyWithdrawHorse` / `Staking.withdrawStar` / `Staking.safeSpeedTransfer`: the stored file (`SpeedStar/flatten/Staking.sol`) starts with Hardhat console logging boilerplate; grep confirms `emergencyWithdrawHorse` is absent from the top-level function list. These functions are in a different compilation unit within the project.
- `StakingRewardsV3._getSecondsInside`: stored file is a Uniswap V3 adapter, not the staking rewards contract.

In all six cases, `nhs.resolve_all_functions(contract, merged_contracts)` returns the function as absent → `"Warning: Function X not found in Y"` → `continue`. These are data pipeline recording errors (wrong file path stored in `negatives_in_codebase.json`), not a correctness issue with the dataset's labels.

**Summary of the full chain:**

```
split_report.md:  49 pos / 127 neg / 176 total   (written before label correction)
      ↓  4 SWC-104 relabeled pos→neg in test.json (undocumented in label_correction_proposal.md)
test.json:        45 pos / 131 neg / 176 total
      ↓  7 items silently dropped in extract_features.py
            1 positive:  Fund.finalizeGrant (BUG — OpenZeppelin misclassification)
            6 negatives: function-not-found-in-file (stale paths)
test_features.json: 44 pos / 125 neg / 169 total   (what every evaluation script uses)
```

**Is the exclusion correct or a bug?**

- The 4 SWC-104 relabeled items: The label correction is substantively correct (view/pure functions with read-only calls cannot have exploitable SWC-104). The `label_correction_proposal.md` document is incorrect in claiming "no labels modified."
- Fund.finalizeGrant: **This is a bug.** The item is a valid reentrancy positive, its source file exists at the correct DAppSCAN path, the function is confirmed present in the file (verified separately). It is excluded due to a string-matching false positive in `extract_features.py`'s source-type detector. The current evaluation on test_features.json is missing one positive.
- 6 dropped negatives: Stale/wrong file paths in the negative sampling output. The functions don't exist in the recorded Solidity files. The exclusion is a symptom of a data pipeline recording error; the items cannot be recovered without re-running negative sampling with corrected paths.

---

## Task 4 — DUBIOUS DAppSCAN Items for Your Decision

There are 4 DUBIOUS items. **Important context before you review them:** all 4 have already been relabeled `label=0` in `test.json` (see Task 3, Step 1). The label_correction_proposal that documents them says "no labels modified" — that statement is wrong. If you confirm them as invalid, the current test.json is already correct. If you decide any should be retained as a valid positive, test.json needs to be patched back.

The 3 DUBIOUS items from the TEST Cross-Contract group all share the same finding context (same Yearn Finance 3pool audit). One item is from TEST Intra-Contract (recorded as intra-contract, but AST reconstruction finds it is cross-contract — consistency mismatch flagged).

---

### DUBIOUS Item 1: StrategyDAI3pool.balanceOfy3CRVinWant

| Field | Value |
|:---|:---|
| **Current label in test.json** | `0` (relabeled — was originally positive) |
| **SWC annotation** | SWC-104-Unchecked Call Return Value |
| **Line range** | L69 |
| **Group** | TEST Cross-Contract |
| **File** | `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Stablecoins 3pool/stablecoins-3pool-adeb776933c6cb3b8306239cc3357d4c6239a88d/contracts/StrategyDAI.sol` |

**Function source:**
```solidity
function balanceOfy3CRVinWant() public view returns (uint256) {
    return balanceOfy3CRV()
            .mul(yvERC20(y3crv).getPricePerFullShare()).div(1e18)
            .mul(ICurveFi(_3pool).get_virtual_price()).div(1e18);
}
```

**Hyperedge:** state vars `['_3pool', 'y3crv']`, calls `yvERC20(y3crv).getPricePerFullShare()` + `ICurveFi(_3pool).get_virtual_price()`. Cross-contract: True.

**DUBIOUS rationale:** `view` function. Both external calls are read-only price getters. There is no state write and no value transfer. Even if these return values are "unchecked," there is nothing to exploit — the function only computes a balance estimate.

**Decision needed:** Confirm invalid (label=0 correct) or reclassify?

---

### DUBIOUS Item 2: StrategyUSDC3pool.balanceOfy3CRVinWant

| Field | Value |
|:---|:---|
| **Current label in test.json** | `0` (relabeled) |
| **SWC annotation** | SWC-104-Unchecked Call Return Value |
| **Line range** | L69 |
| **Group** | TEST Cross-Contract |
| **File** | `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Stablecoins 3pool/stablecoins-3pool-adeb776933c6cb3b8306239cc3357d4c6239a88d/contracts/StrategyUSDC.sol` |

**Function source:**
```solidity
function balanceOfy3CRVinWant() public view returns (uint256) {
    return balanceOfy3CRV()
            .mul(yvERC20(y3crv).getPricePerFullShare()).div(1e18)
            .mul(ICurveFi(_3pool).get_virtual_price()).div(1e30);
}
```

**Hyperedge:** state vars `['_3pool', 'y3crv']`, same two read-only calls. Cross-contract: True.

**DUBIOUS rationale:** Identical pattern to Item 1 — different contract (`StrategyUSDC` vs `StrategyDAI`), same audit finding. Only difference from Item 1: divisor is `1e30` not `1e18` in the final multiplication.

**Decision needed:** Confirm invalid (label=0 correct) or reclassify?

---

### DUBIOUS Item 3: StrategyUSDT3pool.balanceOfy3CRVinWant

| Field | Value |
|:---|:---|
| **Current label in test.json** | `0` (relabeled) |
| **SWC annotation** | SWC-104-Unchecked Call Return Value |
| **Line range** | L69 |
| **Group** | TEST Cross-Contract |
| **File** | `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Stablecoins 3pool/stablecoins-3pool-adeb776933c6cb3b8306239cc3357d4c6239a88d/contracts/StrategyUSDT.sol` |

**Function source:**
```solidity
function balanceOfy3CRVinWant() public view returns (uint256) {
    return balanceOfy3CRV()
            .mul(yvERC20(y3crv).getPricePerFullShare()).div(1e18)
            .mul(ICurveFi(_3pool).get_virtual_price()).div(1e30);
}
```

**Hyperedge:** state vars `['_3pool', 'y3crv']`, same two read-only calls. Cross-contract: True.

**DUBIOUS rationale:** Identical pattern — third variant in the same Yearn 3pool audit, same logic, same limitation. The three `balanceOfy3CRVinWant` items are from three parallel strategy contracts (`StrategyDAI`, `StrategyUSDC`, `StrategyUSDT`) in the same codebase with the same function body.

**Decision needed:** Confirm invalid (label=0 correct) or reclassify?

---

### DUBIOUS Item 4: ChainlinkPriceFeed._getLatestRoundData

| Field | Value |
|:---|:---|
| **Current label in test.json** | `0` (relabeled) |
| **SWC annotation** | SWC-104-Unchecked Call Return Value |
| **Line range** | L96–L100 |
| **Recorded group** | TEST Intra-Contract |
| **AST-reconstructed group** | Cross-Contract ← **consistency mismatch** |
| **File** | `DAppSCAN-source/contracts/Trail_of_Bits-PerpetualProtocolV2/perp-oracle-contract-ba78a5b87098dcffb7285fc585afff1001a87232/contracts/ChainlinkPriceFeed.sol` |

**Function source:**
```solidity
function _getLatestRoundData()
    private
    view
    returns (uint80, uint256 finalPrice, uint256)
{
    (uint80 round, int256 latestPrice, , uint256 latestTimestamp, ) = _aggregator.latestRoundData();
    finalPrice = uint256(latestPrice);
    // SWC-104-Unchecked Call Return Value: L96 -L100
    if (latestPrice < 0) {
        _requireEnoughHistory(round);
        (round, finalDate, latestTimestamp) = _getRoundData(round - 1);
    }
    return (round, finalPrice, latestTimestamp);
}
```

**Hyperedge (recorded):** state vars `['_aggregator']`, call `_aggregator.latestRoundData()`. Recorded as intra-contract.  
**Hyperedge (AST-reconstructed):** same vars/calls, but AST resolves `_aggregator` as type `AggregatorV3Interface` → cross-contract = True. **Consistency mismatch on is_cross_contract.**

**DUBIOUS rationale:** `private view` function. `latestRoundData()` is a read-only oracle query. The SWC-104 annotation points to the `if (latestPrice < 0)` branch where a negative price could cause an incorrect computation — but this is a logic error, not a "failed external call return not checked" in the typical sense. There is no state modification and no value transfer in this function. The SWC-104 label on a `private view` function with a read-only oracle call is at minimum debatable.

**Additional flag:** The recorded `is_cross_contract=False` disagrees with the AST's finding (`AggregatorV3Interface` is an external contract). If you retain this item as a valid positive, the cross-contract field should also be corrected to `True`.

**Decision needed:** Confirm invalid (label=0 correct) or reclassify? If reclassify: also decide whether to correct `is_cross_contract` to `True`.

---

## Summary Table

| Task | Finding | Action required |
|:---|:---|:---|
| **1(a)** | 58% of FORGE and 76% of DAppSCAN contracts have only 1 constructable interaction. ~25% of training contracts have ≥2. | Decide whether single-interaction contracts get isolated nodes or are excluded from the shared graph. |
| **1(b)** | FORGE coverage 100%; DAppSCAN positive coverage 91.4%; negative sampling at 7.7% of codebase total. | No action; figures to inform rebuild scope. |
| **2** | One real leakage: `Box` (vfp_00189) — train negatives and test positives from same `Box.sol`. | For isolated-hyperedge model: low impact. For shared-graph rebuild: must move all Box items to one split before proceeding. |
| **3 Step 1** | 4 SWC-104 items relabeled pos→neg in test.json. Contradicts `label_correction_proposal.md` which claims "no labels modified." | Update label_correction_proposal.md to state corrections were applied. No data change needed. |
| **3 Step 2** | Fund.finalizeGrant (reentrancy positive) silently dropped by a bug in `extract_features.py` — "openzeppelin" in DAppSCAN audit firm name triggers wrong source-type classification. 6 negatives dropped for stale file paths. | Fix `extract_features.py:193–198` to check `source` key and `project_root` presence before falling back to string matching. The current evaluated test set is missing one legitimate positive. |
| **4** | All 4 DUBIOUS items are already label=0 in test.json. No decision is outstanding unless you want to un-correct one. | Confirm or reject for each item above. |
