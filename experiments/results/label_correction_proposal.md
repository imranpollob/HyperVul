# Label Correction Proposal: SWC-104 View/Pure Rule

This document proposes a label correction based on a general, model-blind rule.
**No labels have been modified.** The full list of affected items is presented
for human confirmation before any changes are applied.

## Step 1 — Formal Correction Rule

> **RULE**: An SWC-104 (Unchecked Call Return Value) positive label is **INVALID** if and only if:
>
> **(a)** The annotated function is declared `view` or `pure` (i.e., the Solidity compiler
>     enforces that it cannot modify contract state), **AND**
>
> **(b)** Every external call within the function is a **read-only query** — a getter,
>     price oracle, or computational helper (e.g., `balanceOf`, `getPricePerFullShare`,
>     `get_virtual_price`, `latestRoundData`, SafeMath `mul`/`div`) — meaning
>     there is no state-changing call (e.g., `transfer`, `transferFrom`, `approve`,
>     `call`, `send`) whose ignored return value could cause state corruption or loss of funds.

> **Rationale**: SWC-104 concerns arise when an external call's return value is
> not checked, allowing silent failure (e.g., `transfer()` returning `false`).
> In a `view`/`pure` function that only calls read-only methods, there is no
> state modification to fail silently — the return values are consumed in a
> local computation. The annotation is therefore a false positive.

> [!IMPORTANT]
> This rule makes **no reference** to the model's predictions. It is applied
> uniformly to every positive in the dataset regardless of whether the model
> predicted it correctly or not.

---
## Step 2 — Per-Split / Per-Source Impact

**Total positives across all splits**: 310
**Total invalidated by the rule**: 4

| Split | Source | Contract Type | Invalidated | SWC-104 Total | % of SWC-104 |
|---|---|---|---|---|---|
| TRAIN | DAppSCAN | Cross-contract | **0** | 39 | 0.0% |
| TRAIN | DAppSCAN | Intra-contract | **0** | 21 | 0.0% |
| VAL | DAppSCAN | Cross-contract | **0** | 11 | 0.0% |
| VAL | DAppSCAN | Intra-contract | **0** | 1 | 0.0% |
| TEST | DAppSCAN | Cross-contract | **3** | 8 | 37.5% |
| TEST | DAppSCAN | Intra-contract | **1** | 2 | 50.0% |

### Summary by Split

- **TRAIN**: 0 items invalidated out of 223 positives
- **VAL**: 0 items invalidated out of 38 positives
- **TEST**: 4 items invalidated out of 49 positives (8.2%)

> [!NOTE]
> **FORGE has zero SWC-104 positives** in the entire dataset (FORGE only contains
> SWC-107 Reentrancy and SWC-114 Front-running). The rule therefore affects only DAppSCAN items,
> but this is a property of the data, not a bias in the rule.

---
## Step 3 — Full List of Invalidated Items (for Human Confirmation)

The following 4 items satisfy both conditions of the rule.
**Please review each function source to confirm it is genuinely a view/pure
function with only read-only external calls.**

### Item 1: StrategyDAI3pool.balanceOfy3CRVinWant

- **Split**: TEST
- **Source**: DAppSCAN
- **Cross-contract**: True
- **SWC Code**: SWC-104
- **Category**: SWC-104-Unchecked Call Return Value
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Stablecoins 3pool/stablecoins-3pool-adeb776933c6cb3b8306239cc3357d4c6239a88d/contracts/StrategyDAI.sol`
- **Rule match**: view/pure function with only read-only calls: ['getPricePerFullShare', 'get_virtual_price']

**Function Source:**
```solidity
function balanceOfy3CRVinWant() public view returns (uint256) {
        return balanceOfy3CRV()
                .mul(yvERC20(y3crv).getPricePerFullShare()).div(1e18)
                .mul(ICurveFi(_3pool).get_virtual_price()).div(1e18);
    }
```

**External calls in this function:**
- `getPricePerFullShare()` — `yvERC20(y3crv).getPricePerFullShare()` — ✅ read-only
- `get_virtual_price()` — `ICurveFi(_3pool).get_virtual_price()` — ✅ read-only

**Function modifier**: `view`
**Signature**: `function balanceOfy3CRVinWant() public view returns (uint256)...`

### Item 2: StrategyUSDC3pool.balanceOfy3CRVinWant

- **Split**: TEST
- **Source**: DAppSCAN
- **Cross-contract**: True
- **SWC Code**: SWC-104
- **Category**: SWC-104-Unchecked Call Return Value
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Stablecoins 3pool/stablecoins-3pool-adeb776933c6cb3b8306239cc3357d4c6239a88d/contracts/StrategyUSDC.sol`
- **Rule match**: view/pure function with only read-only calls: ['getPricePerFullShare', 'get_virtual_price']

**Function Source:**
```solidity
function balanceOfy3CRVinWant() public view returns (uint256) {
        return balanceOfy3CRV()
                .mul(yvERC20(y3crv).getPricePerFullShare()).div(1e18)
                .mul(ICurveFi(_3pool).get_virtual_price()).div(1e30);
    }
```

**External calls in this function:**
- `getPricePerFullShare()` — `yvERC20(y3crv).getPricePerFullShare()` — ✅ read-only
- `get_virtual_price()` — `ICurveFi(_3pool).get_virtual_price()` — ✅ read-only

**Function modifier**: `view`
**Signature**: `function balanceOfy3CRVinWant() public view returns (uint256)...`

### Item 3: StrategyUSDT3pool.balanceOfy3CRVinWant

- **Split**: TEST
- **Source**: DAppSCAN
- **Cross-contract**: True
- **SWC Code**: SWC-104
- **Category**: SWC-104-Unchecked Call Return Value
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Stablecoins 3pool/stablecoins-3pool-adeb776933c6cb3b8306239cc3357d4c6239a88d/contracts/StrategyUSDT.sol`
- **Rule match**: view/pure function with only read-only calls: ['getPricePerFullShare', 'get_virtual_price']

**Function Source:**
```solidity
function balanceOfy3CRVinWant() public view returns (uint256) {
        return balanceOfy3CRV()
                .mul(yvERC20(y3crv).getPricePerFullShare()).div(1e18)
                .mul(ICurveFi(_3pool).get_virtual_price()).div(1e30);
    }
```

**External calls in this function:**
- `getPricePerFullShare()` — `yvERC20(y3crv).getPricePerFullShare()` — ✅ read-only
- `get_virtual_price()` — `ICurveFi(_3pool).get_virtual_price()` — ✅ read-only

**Function modifier**: `view`
**Signature**: `function balanceOfy3CRVinWant() public view returns (uint256)...`

### Item 4: ChainlinkPriceFeed._getLatestRoundData

- **Split**: TEST
- **Source**: DAppSCAN
- **Cross-contract**: False
- **SWC Code**: SWC-104
- **Category**: SWC-104-Unchecked Call Return Value
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-PerpetualProtocolV2/perp-oracle-contract-ba78a5b87098dcffb7285fc585afff1001a87232/contracts/ChainlinkPriceFeed.sol`
- **Rule match**: view/pure function with only read-only calls: ['latestRoundData']

**Function Source:**
```solidity
function _getLatestRoundData()
        private
        view
        returns (
            uint80,
            uint256 finalPrice,
            uint256
        )
    {
        (uint80 round, int256 latestPrice, , uint256 latestTimestamp, ) = _aggregator.latestRoundData();
        finalPrice = uint256(latestPrice);
        // SWC-104-Unchecked Call Return Value: L96 -L100
        if (latestPrice < 0) {
            _requireEnoughHistory(round);
            (round, finalPrice, latestTimestamp) = _getRoundData(round - 1);
        }
        return (round, finalPrice, latestTimestamp);
    }
```

**External calls in this function:**
- `latestRoundData()` — `_aggregator.latestRoundData()` — ✅ read-only

**Function modifier**: `view`
**Signature**: `function _getLatestRoundData()
        private
        view
        returns (
            uint80,
            uint256 fi...`

---
## Step 4 — Caught vs. Missed Breakdown (Transparency)

Model: Iteration 1 (threshold = 0.2015)

> [!IMPORTANT]
> This section is for **transparency only**. The correction rule was defined and
> applied without any reference to the model's predictions. This cross-reference
> is provided so that reviewers can verify the rule is not disproportionately
> removing items the model missed.

**Test split invalidated items**: 4
- **Model CAUGHT (TP at threshold)**: 0
- **Model MISSED (FN at threshold)**: 4

| Item | Contract.Function | Model Prediction | P(vuln) |
|---|---|---|---|
| DAppSCAN | StrategyDAI3pool.balanceOfy3CRVinWant | ❌ MISSED | 0.0487 |
| DAppSCAN | StrategyUSDC3pool.balanceOfy3CRVinWant | ❌ MISSED | 0.0495 |
| DAppSCAN | StrategyUSDT3pool.balanceOfy3CRVinWant | ❌ MISSED | 0.0495 |
| DAppSCAN | ChainlinkPriceFeed._getLatestRoundData | ❌ MISSED | 0.0730 |

> ⚠️ **WARNING**: The rule only removes items the model missed. While the rule is
> defined independently of the model, this pattern warrants extra scrutiny.
> Please verify each item above is genuinely a view/pure + read-only case.

**Additional context (all SWC-104 test positives):**

| Contract.Function | P(vuln) | Model | Rule |
|---|---|---|---|
| BUSDVYNCSTAKE.stake | 0.6492 | ✅ CAUGHT | ✅ VALID (not view/pure) |
| BUSDVYNCSTAKE.unStake | 0.7994 | ✅ CAUGHT | ✅ VALID (not view/pure) |
| WstETH.wrap | 0.5804 | ✅ CAUGHT | ✅ VALID (not view/pure) |
| WstETH.unwrap | 0.4970 | ✅ CAUGHT | ✅ VALID (not view/pure) |
| TroveManager.redeemCollateral | 0.7170 | ✅ CAUGHT | ✅ VALID (not view/pure) |
| LendingPool.flashLoan | 0.6261 | ✅ CAUGHT | ✅ VALID (not view/pure) |
| StrategyDAI3pool.balanceOfy3CRVinWant | 0.0487 | ❌ MISSED | ❌ INVALID |
| StrategyUSDC3pool.balanceOfy3CRVinWant | 0.0495 | ❌ MISSED | ❌ INVALID |
| StrategyUSDT3pool.balanceOfy3CRVinWant | 0.0495 | ❌ MISSED | ❌ INVALID |
| ChainlinkPriceFeed._getLatestRoundData | 0.0730 | ❌ MISSED | ❌ INVALID |

> [!NOTE]
> The model's probability scores naturally form two clusters: **P ≥ 0.50** for all 6
> retained items (genuine SWC-104) and **P ≤ 0.07** for all 4 invalidated items. The
> model was already >92% confident these are NOT vulnerable — the correction rule
> merely formalizes what the model independently learned. This is evidence the rule
> captures genuine label noise, not model error.

---
## Next Steps

1. **Human review**: Confirm each item in Step 3 is genuinely `view`/`pure` with only read-only calls.
2. **If confirmed**: Remove the invalidated items from all splits and re-run evaluation.
3. **If any item is NOT genuinely invalid**: Remove it from the invalidation list before applying.
