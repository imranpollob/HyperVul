# HyperVul — FORGE-Curated Positive Hyperedge AST Analysis Report

> **Date**: 2026-06-11  
> **Dataset**: FORGE-Curated (`data/FORGE-Curated/flatten/vfp-vuln/`)  
> **Method**: Tree-sitter Solidity AST Parser (`scripts/forge_hyperedge_ast_analysis.py`)

---

## Executive Summary

This report documents the results of the smart contract vulnerability hyperedge analysis using a proper Solidity AST parser (via `tree-sitter-solidity`) and compares it against the previous regex-based baseline.

| Metric | Regex Baseline | AST Parser (Changes #1-4) | Delta |
| :--- | :---: | :---: | :---: |
| Total VFPs Analysed | 303 | 303 | 0 |
| Total Findings | 695 | 695 | 0 |
| **Interaction-type Findings** (Step 1) | **212** | **212** | 0 |
| Findings with Function-Level Location (Step 2) | 148 | 148 | 0 |
| Locations with Source Code Found | 251 | 251 | 0 |
| Locations with External Call | 107 | 133 | +26 |
| Locations with State Variable Access | 108 | 116 | +8 |
| Locations with BOTH (Constructable) | 66 | 88 | +22 |
| **Constructable Positive Hyperedges** (Deduplicated) | **61** | **83** | **+22** |
| From Unique Findings | 47 | 63 | +16 |
| Across Unique VFPs | 30 | 40 | +10 |

> **Key Takeaway**: Transitioning to a principled AST parser increased the number of constructable positive hyperedges from **61 to 83 (+36% uplift)**. This was achieved by:
> 1. Resolving inheritance-based state variables (recovering 5 hyperedges that access parent contract storage).
> 2. Correctly resolving interface-typed local variables, index expressions, and inline casts.
> 3. Supporting Uniswap v4 / callback patterns (`unlock`, `settle`, `take`, `getSlot0`) which are missed by static regex.

---

## Dry-Run Evaluation: Change #5 (Keyword Fallback)

As requested, we evaluated a name-based keyword fallback (Change #5) to classify calls as external based on names like `token`, `vault`, `pool`, or `oracle` when the contract definition is not parsed (e.g., in base classes).

- **Official Constructable Hyperedges (Changes #1-4)**: **83**
- **Constructable Hyperedges with Change #5 Enabled**: **83**
- **Additional Hyperedges Contributed by Change #5**: **0**

> [NOTE]
> The keyword fallback (Change #5) contributed **exactly 0 additional hyperedges** once the principled AST improvements (Changes #1-4) were implemented. This indicates that adding standard DeFi interface methods (like `getSlot0`, `unlock`, `settle`, `take`) to `EXTERNAL_CALL_METHODS` and properly resolving file-specific contract definitions was sufficient to capture all valid cases without resorting to heuristic name-based guessing.

---

## Step-by-Step Pipeline Results

### Step 1 — Filter to Interaction-Type Vulnerabilities (Unchanged)
Spans **133 distinct VFPs** (43.9% of the dataset) using a CWE category tree filter and keyword matching:
- **Matched by CWE only**: 116
- **Matched by keyword only**: 65
- **Matched by both**: 31
- **Total**: 212

### Step 2 — Extract Function-Level Locations (Unchanged)
- **Findings with ≥1 function-level location**: 148
- **Findings with zero function-level locations**: 64
- **Total function location references**: 301

### Step 3 — AST Parser Statistics
- **Source code found**: 251 (83.4%)
- **Source code NOT found**: 50 (16.6%)
- **Contract not found**: 1
- **Function definition not in AST**: 50
- **Locations with external calls**: 133
- **Locations with state variable access**: 116
- **Locations with BOTH**: 88

### Step 4 — Deduplicated Hyperedges
After deduplicating locations by `(vfp_id, finding_id, function)`:
- **Official positive hyperedges**: **83**
- **Severity distribution**:
  - Critical: 9
  - High: 35
  - Medium: 39

---

## AST-Enabled Hyperedge Examples

### Example 1: `removeLiquidity` — Uniswap v4 Vault Interaction

| Field | Value |
|---|---|
| **VFP** | vfp_00058 |
| **Finding** | "The deadline check is missing in the increaseLiquidity and removeLiquidity" |
| **Severity** | Medium |
| **Contract** | `LikwidPairPosition` (inherits from `BasePositionManager`) |
| **Function** | `removeLiquidity` |

**Solidity Code (Excerpt):**
```solidity
function removeLiquidity(uint256 tokenId, uint128 liquidity, uint256 amount0Min, uint256 amount1Min)
    external
    returns (uint256 amount0, uint256 amount1)
{
    ...
    IVault.ModifyLiquidityParams memory params = IVault.ModifyLiquidityParams({
        amount0: 0,
        amount1: 0,
        liquidityDelta: -int128(liquidity),
        salt: bytes32(tokenId)
    });
    bytes memory callbackData = abi.encode(msg.sender, key, params, amount0Min, amount1Min);
    bytes memory data = abi.encode(Actions.MODIFY_LIQUIDITY, callbackData);

    bytes memory result = vault.unlock(data); // <-- External Call
    (, amount0, amount1) = abi.decode(result, (int128, uint256, uint256));
}
```

- **State Variables Accessed (Inherited)**: `poolIds`, `poolKeys` (defined in parent `BasePositionManager`)
- **External Call**: `vault.unlock(data)` (where `vault` is an inherited state variable of type `IVault` from parent `BasePositionManager`)
- **AST Uplift**:
  1. **Inheritance Mapping**: Successfully resolved parent contract state variables (`poolIds`, `poolKeys`, `vault`) from `BasePositionManager` which was defined in a separate file.
  2. **DeFi Vault Method Support**: Successfully classified `unlock()` as an external DeFi call on a contract-typed state variable.

---

### Example 2: `stakeTokens` — Inheritance & Inline Casts

| Field | Value |
|---|---|
| **VFP** | vfp_00032 |
| **Finding** | "USDT approve() reverts due to non-standard return value" |
| **Severity** | Critical |
| **Contract** | `GenericERC4626WithdrawRequestManager` |
| **Function** | `stakeTokens` |

**Solidity Code (Excerpt):**
```solidity
function stakeTokens(address depositToken, uint256 amount, bytes calldata data)
    external
    override
    onlyApprovedVault
    returns (uint256 yieldTokensMinted)
{
    uint256 initialYieldTokenBalance = ERC20(YIELD_TOKEN).balanceOf(address(this)); // <-- External Call
    ERC20(depositToken).safeTransferFrom(msg.sender, address(this), amount);       // <-- External Call
    ...
}
```

- **State Variables Accessed (Inherited)**: `YIELD_TOKEN` (defined in `AbstractWithdrawRequestManager`)
- **External Calls**: 
  - `ERC20(YIELD_TOKEN).balanceOf(...)` (Inline Cast)
  - `ERC20(depositToken).safeTransferFrom(...)` (SafeERC20 wrapper)
- **AST Uplift**:
  1. **Inheritance Mapping**: Resolved `YIELD_TOKEN` from abstract parent contract `AbstractWithdrawRequestManager`.
  2. **Cast Handling**: Parsed the `call_expression` representing the `ERC20(...)` cast, extracted its receiver and target method `balanceOf`, and correctly flagged it as external.

---

## Data Files

The final results are saved in the project structure:

- [forge_ast_hyperedge_summary.json](file:///home/pollmix/Coding/HyperVul/experiments/results/forge_ast_hyperedge_summary.json) — Summary metrics.
- [forge_ast_hyperedge_detailed.json](file:///home/pollmix/Coding/HyperVul/experiments/results/forge_ast_hyperedge_detailed.json) — Per-location results (301 entries).
- [forge_ast_constructable_hyperedges.json](file:///home/pollmix/Coding/HyperVul/experiments/results/forge_ast_constructable_hyperedges.json) — Deduplicated 83 positive hyperedges.
