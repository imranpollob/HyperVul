# DAppSCAN Dataset Analysis for Interaction-Based Vulnerability Detection

## 1. Labeled Unit & Annotation Structure

### Labeled Unit: **Individual functions within individual files**

Each annotation is a JSON file located in [SWCsource/](file:///home/pollmix/Coding/datasets/DAppSCAN/DAppSCAN-source/SWCsource) that mirrors the project directory structure. The schema is:

```json
{
  "filePath": "DAppSCAN-source/contracts/<project>/<repo>/path/to/Contract.sol",
  "SWCs": [
    {
      "category": "SWC-107-Reentrancy",
      "function": "withdraw",
      "lineNumber": "L175-216"
    }
  ]
}
```

### Key Numbers

| Metric | Value |
|---|---|
| Total DApp projects | 608 |
| Total .sol files | 21,457 |
| Average files per project | 35.3 |
| **Total SWC annotations** | **1,646** |
| Unique files annotated | 948 |
| Projects with annotations | 606 |

### Annotation Granularity

| Field | Coverage |
|---|---|
| Function name specified | 1,224 / 1,646 (74.4%) |
| Line number specified | 1,646 / 1,646 (100%) |
| Single line references | 898 (54.6%) |
| Line range references | 682 (41.4%) |
| Cross-contract references | **0 — not in schema** |

> [!IMPORTANT]
> Each annotation is **single-file, single-function scoped**. There is no field for "related contract," "callee," or any cross-reference linking to the other side of an interaction. The annotation literally says "reentrancy exists in `withdraw()` at lines 175-216" — full stop.

---

## 2. Genuine Multi-Contract DApp Bundles vs Isolated Files

### These ARE genuine DApp bundles

The projects are real DApp codebases, not isolated files:

| Project Size | Count |
|---|---|
| 1 .sol file | 166 |
| 2-5 .sol files | 111 |
| 6-20 .sol files | 122 |
| 21-50 .sol files | 100 |
| 50+ .sol files | **109** |

**Cross-contract import analysis** (sampled the 50 largest projects):
- **50/50** projects have local cross-file imports
- Average **60.3 local imports** per project
- Most interconnected examples:
  - Synthetix Fomalhaut: 511 files, 169 local imports
  - Synthetix Aloith: 469 files, 150 local imports
  - Synthetix Shaula: 934 files, 148 local imports

> [!NOTE]
> The contracts are genuinely intertwined — they import each other, call each other's functions via interfaces, and form real DApp architectures. This is **not** a collection of isolated files under folder names.

### But annotations don't exploit this structure

Even though a project like GearBox has 15 reentrancy-annotated functions across `PoolService.sol`, `WETHGateway.sol`, `YearnV2.sol`, `CurveV1.sol`, `UniswapV2.sol`, and `UniswapV3.sol` — each annotation is independent. There's no annotation linking "the reentrancy in `PoolService.lendCreditAccount()` involves a callback via `WETHGateway`."

---

## 3. Reentrancy & Cross-Contract Annotations

### SWC-107 Reentrancy: 138 annotations

| Scope | Count |
|---|---|
| Projects with reentrancy in **one file** | 92 |
| Projects with reentrancy in **multiple files** | 9 |

### Representative Multi-File Reentrancy Projects

**GearBox Protocol** — the richest example:
```
PoolService.sol      :: lendCreditAccount()     @ L238-258
WETHGateway.sol      :: addLiquidityETH()       @ L98-112
WETHGateway.sol      :: removeLiquidityETH()    @ L120-140
WETHGateway.sol      :: openCreditAccountETH()  @ L151-171
WETHGateway.sol      :: repayCreditAccountETH() @ L179-199
YearnV2.sol          :: _deposit()              @ L78
CurveV1.sol          :: exchange()              @ L49-85
UniswapV2.sol        :: swapExactTokensForTokens() @ L110
UniswapV3.sol        :: exactInputSingle()      @ L52
```

**Compound cToken unredacted**:
```
Comptroller.sol      :: liquidateBorrowAllowed() @ L465-501
CToken.sol           :: _setComptroller()       @ L930-947
```

**GnosisSafe**:
```json
{
  "filePath": "...GnosisSafe.sol",
  "SWCs": [
    { "category": "SWC-107-Reentrancy", "function": "execTransaction", "lineNumber": "L70 - L105" }
  ]
}
```

> [!WARNING]
> Even in the best case (GearBox with 15 annotated reentrancy locations across 8 files), **each annotation is independent**. The annotations don't say "reentrancy in `UniswapV3.exactInputSingle()` re-enters `PoolService.lendCreditAccount()`." They just flag each function individually.

### Other Interaction-Relevant SWCs

| SWC | Name | Count |
|---|---|---|
| SWC-107 | Reentrancy | 138 |
| SWC-114 | Transaction Order Dependence (front-running) | 86 |
| SWC-104 | Unchecked Call Return Value | 116 |
| SWC-105 | Unprotected Ether Withdrawal | 42 |
| SWC-112 | Delegatecall to Untrusted Callee | 12 |
| **Total** | | **394** |

---

## 4. Granularity Comparison: DAppSCAN vs FORGE-Curated

| Dimension | DAppSCAN | FORGE-Curated |
|---|---|---|
| **Total findings** | 1,646 | 2,469 |
| **Total reports/projects** | 608 | 208 |
| **Taxonomy** | SWC-XXX codes (26 types) | CWE hierarchy (multi-level) |
| **Location format** | `function` + `lineNumber` (one file) | `location[]` + `files[]` (multiple entries) |
| **Multi-location findings** | 0% (schema doesn't support it) | **45.4%** have multiple locations |
| **Multi-file findings** | 0% (schema doesn't support it) | **14.4%** span multiple files |
| **Description richness** | Category label only | Full paragraphs: cause, exploit path, impact |
| **Reentrancy annotations** | 138 (single-point) | 49 (some with multi-file cross-references) |

### Concrete FORGE Reentrancy Example (Cross-Contract)

From [2025.07.18 - Final - Notional Exponent Audit Report.json](file:///home/pollmix/Coding/datasets/FORGE-Curated/dataset-curated/findings/2025.07.18%20-%20Final%20-%20Notional%20Exponent%20Audit%20Report.json):

```json
{
  "title": "Cross-contract reentrancy allows YIELD_TOKEN theft for the GenericERC4626 WithdrawalRequestManager variant",
  "severity": "High",
  "location": [
    "src/withdraws/GenericERC4626.sol",
    "src/withdraws/WithdrawalRequestManager.sol::initiateWithdraw"
  ],
  "files": [
    "UniV3Adapter.sol",
    "GenericERC4626.sol",
    "AbstractWithdrawRequestManager.sol"
  ],
  "description": "...initiateWithdraw → Uniswap swap → malicious pool callback → re-enters deposit → inflated YIELD_TOKEN minting..."
}
```

This finding explicitly identifies:
- **3 contracts** involved (`UniV3Adapter`, `GenericERC4626`, `AbstractWithdrawRequestManager`)
- **The specific function** entry point (`initiateWithdraw`)
- **The call chain** (withdraw → swap → malicious callback → deposit)
- **The exploit mechanism** (balance manipulation across contracts)

### Equivalent DAppSCAN Reentrancy Annotation

```json
{
  "filePath": "...GnosisSafe.sol",
  "SWCs": [
    { "category": "SWC-107-Reentrancy", "function": "execTransaction", "lineNumber": "L70 - L105" }
  ]
}
```

Just a flag on one function. No caller, no callee, no mechanism.

> [!CAUTION]
> **FORGE-Curated gives strictly finer-grained location information** for your use case. It has multi-file `location[]` and `files[]` arrays that can identify which contracts co-participate in a vulnerability. DAppSCAN annotations are fundamentally single-point.

---

## 5. Natural Mapping to "Vulnerable Interactions"

### DAppSCAN: No natural interaction mapping exists

The annotation schema `{filePath, [{category, function, lineNumber}]}` is a **per-file vulnerability flag**. To build an "interaction" from DAppSCAN, you would need to:

1. Take a reentrancy annotation like `GnosisSafe.sol::execTransaction @ L70-105`
2. Parse the Solidity source to find external calls in that line range
3. Resolve the call targets to other contracts in the project
4. Synthetically construct the interaction tuple `(caller, callee, state_variable)`

This is feasible but requires **full static analysis reconstruction** — the dataset provides the raw code and a single-point flag, but not the interaction.

### FORGE-Curated: Partial interaction mapping exists

14.4% of findings (356 findings) span multiple files, and the `location[]` + `files[]` arrays identify the specific contracts involved. Combined with the rich natural-language descriptions that often describe the call chain, you can extract:
- Entry point contract/function
- Intermediate contracts in the call chain
- The state variable or mechanism being exploited

### Practical Assessment

| Feature | DAppSCAN | FORGE-Curated |
|---|---|---|
| Can identify vulnerable function? | ✅ 74.4% of annotations | ✅ via `location[]` |
| Can identify vulnerable line range? | ✅ 100% of annotations | ✅ via `#L123-L456` syntax |
| Can identify multiple contracts in one vuln? | ❌ | ✅ 14.4% do natively |
| Can identify the call chain? | ❌ | ⚠️ In descriptions, not structured |
| Can identify the state variable? | ❌ | ⚠️ In descriptions, not structured |
| Provides the actual DApp codebase? | ✅ Full project bundles | ✅ Full project bundles |

> [!IMPORTANT]
> **Neither dataset provides a structured "interaction" annotation** in the form `{callerContract, callerFunction, calleeContract, calleeFunction, stateVariable, vulnerability_type}`. Both require post-processing. But FORGE-Curated gives you a **much better starting point** because:
> 1. Multi-file locations are already identified
> 2. Rich descriptions contain the call chain in natural language
> 3. CWE-1265 (Uncontrolled Reentrancy) specifically tags cross-contract cases
>
> DAppSCAN gives you the **scale** (1,646 annotations, 608 projects, 21K files) but requires **complete static analysis reconstruction** to identify what the other contracts in the interaction are.

---

## Summary Verdict

| Question | Answer |
|---|---|
| **Q1: Labeled unit** | Individual function within a single file, annotated with SWC category + line range |
| **Q2: Genuine bundles?** | Yes — real multi-contract DApp projects with heavy cross-imports (avg 35 files/project) |
| **Q3: Multi-contract annotations?** | No — annotations are single-function, single-file scoped, even for inherently multi-contract vuln types like reentrancy |
| **Q4: vs FORGE-Curated granularity** | FORGE-Curated is strictly finer: 45.4% multi-location findings, 14.4% multi-file findings, rich descriptions with call chains. DAppSCAN has 0% multi-location annotations. |
| **Q5: Natural interaction mapping?** | Neither has a structured interaction format. FORGE-Curated's multi-file `location[]`/`files[]` + descriptions are the closest existing structure. DAppSCAN would require full static analysis to reconstruct interactions from single-point flags. |
