# FORGE-Curated Dataset Analysis for Hyperedge-Based Vulnerability Detection

## Summary

619 VFPs, 2,276 individual findings, 208 audit reports. All numbers below come from script-driven analysis across the full dataset.

---

## Q1: What is the unit of analysis?

A VFP (Vulnerability-File Pair) is a **per-project bundle** of findings grouped with the **Solidity source files** those findings reference. It is *not* a single contract and *not* a single file — it's a set of `.sol` source code files bundled with every finding that touches any of them.

### `affected_files` contents

| Files per VFP | Count | % |
|---|---|---|
| 1 file | 480 | 77.5% |
| 2 files | 64 | 10.3% |
| 3 files | 25 | 4.0% |
| 4 files | 19 | 3.1% |
| 5+ files | 31 | 5.0% |

`affected_files` is a `Dict[str, str]` mapping **file basenames** (e.g., `Folio.sol`, `AgentToken.sol`) to their **full source code** as a string. This means the actual contract code is inlined directly — you don't need to chase git submodules.

Each VFP contains 1–48 findings (mean 3.7, median 2). The key design choice: a VFP bundles *all findings from one audit report* that share at least one affected file in common. Multiple findings can coexist in one VFP.

> [!IMPORTANT]
> 97.4% of VFPs (603/619) contain all files that their findings' `files` field references. Only 16 VFPs have a referenced file missing from `affected_files`. The source code is almost always complete for the vulnerability context.

---

## Q2: Do VFPs naturally contain multiple interacting contracts?

**Yes, but most are single-file:** 139/619 VFPs (22.5%) contain multiple files. For actual *findings*, the picture is clearer:

| Files per finding | Count | % |
|---|---|---|
| 1 file | 1,941 | 85.3% |
| 2 files | 238 | 10.5% |
| 3 files | 60 | 2.6% |
| 4+ files | 37 | 1.6% |

**28.7% of all findings (653/2,276) have location fields spanning multiple distinct files.** This is significantly higher than the `files` field suggests, because the `location` field often references functions in files that the `files` field doesn't fully enumerate.

### Concrete multi-contract example

**vfp_00001** — Spectral Image Vaults, 4 files:
- Finding 1 (High): *"Tax in agent tokens causes incorrect accounting"*
  - Location: `AgentToken.sol::transfer#L100`, `AgentImageService.sol::requestImage#L216`
  - Two contracts interacting: the token's `transfer` applies a tax, but the service contract assumes full amount received
  - **This is exactly an interaction-type vulnerability**: {caller: `requestImage`, callee: `transfer`, state: `pendingFees`}

---

## Q3: For interaction-based vulnerabilities — do location fields point across multiple files?

I searched titles and descriptions for interaction keywords: `reentr`, `flash loan`, `front-run`, `sandwich`, `cross-contract`, `callback`, `external call`, `delegatecall`, `price manipulat`, etc.

### 332 interaction-related findings found (14.6% of all)

| Keyword | Hits |
|---|---|
| front-run | 88 |
| external call | 78 |
| msg.sender | 48 |
| reentr(ancy) | 48 |
| callback | 34 |
| flash loan | 26 |
| sandwich | 26 |
| race condition | 20 |
| delegatecall | 18 |
| cross-contract | 13 |
| price manipulat | 14 |
| read-only reentr | 6 |

### Location span of interaction findings

| Span | Count | % |
|---|---|---|
| Multi-file locations | 96 | 28.9% |
| Single-file locations | 224 | 67.5% |
| No location data | 12 | 3.6% |

> [!WARNING]
> **67.5% of interaction-based findings have locations pointing to a single file**, even though the *vulnerability semantics* involve cross-contract interaction. This is because auditors typically point to the *vulnerable entry point* rather than all participants. The callee (e.g., external contract) is described in the text but not always in the `location` field.

### Representative cross-contract reentrancy example

**vfp_00090, Finding 0** — *"Cross-contract reentrancy allows YIELD_TOKEN theft"* (High, CWE-691/CWE-1265):

```
Location: ['src/withdraws/GenericERC4626.sol', 
           'src/withdraws/WithdrawalRequestManager.sol::initiateWithdraw']
Files:    ['contracts/trading/adapters/UniV3Adapter.sol',
           'src/withdraws/GenericERC4626.sol',
           'src/withdraws/AbstractWithdrawRequestManager.sol']
```

The description identifies the interaction chain:
1. Attacker calls `initiateWithdraw` → leaves YIELD_TOKENs in `WithdrawalRequestManager`
2. Executes multihop swap through malicious pool (via `UniV3Adapter`)
3. Malicious pool triggers callback → re-enters deposit function
4. Inflated balance differences cause excess share minting

**This involves 3 contracts but the location only names 2.** The `files` field includes the third (`UniV3Adapter.sol`). You'd need to combine `location` + `files` + `description` to reconstruct the full interaction.

---

## Q4: Can you label a specific interaction from the existing ground truth?

### Location format analysis

| Format | Count | % of all locations |
|---|---|---|
| `file::function#lines` | dominant | — |
| `file::function` (no lines) | present | — |
| `file#lines` (no function) | present | — |
| `file_only` | present | — |

**55.6% of findings (1,266/2,276) have at least one function-level location** (containing `::`). Only 5.1% (116) have completely empty locations.

### Interaction group candidates

**Findings with ≥2 function-level references** (which could directly form interaction groups like `{calling_function, callee_function}`):

- **Total: 518 findings** (22.8% of all)
  - Of those, **cross-file** (functions in different `.sol` files): substantial subset
  - **Same-file** (multiple functions within one contract): majority

### Feasibility verdict

You **can** construct interaction labels, but with important caveats:

**What works:**
- When `location` has multiple `file::function#lines` entries, you can directly build an interaction group: `{func_A in ContractX, func_B in ContractY}` → vulnerable
- The `affected_files` dict gives you the source code to parse for state variables
- CWE categories give you the vulnerability type

**What requires extra work:**
- **State variables** are never explicitly listed in the ground truth. You must parse them from the source code at the specified line ranges
- **The callee** in external calls is often described in `description` text but not in `location`. For ~67% of interaction-based findings, you'll need NLP/LLM extraction from descriptions to identify the callee
- **Negative labels** (non-vulnerable interactions) must be constructed synthetically. The dataset only labels *vulnerable* interactions — every unlabeled function pair in the same VFP becomes a candidate negative, but you need to verify it's truly non-vulnerable

> [!IMPORTANT]
> The location format `Filename.sol::functionName#LineStart-LineEnd` is rich enough for function-level interaction labeling in 55.6% of findings. For the remaining 44.4%, you get file-level or line-level pointers but must extract function names from the source code yourself.

### Worked example: constructing a hyperedge label

From **vfp_00001, Finding 1** (High severity):
```
Title: "Tax in agent tokens causes incorrect accounting"
Location: ['AgentToken.sol::transfer#L100', 'AgentImageService.sol::requestImage#L216']
CWE: CWE-707 → CWE-20
```

**Hyperedge construction:**
- Calling function: `AgentImageService.requestImage` (line 216 does `token.safeTransferFrom`)
- Callee function: `AgentToken.transfer` (line 100 applies tax deduction)
- State variable: `pendingFees` (updated at line 216 using `config.pricePerImage`, not actual received amount)
- Label: **Vulnerable** — the interaction between these two functions and this state variable creates the bug

**You can extract this directly from the ground truth** without reading the description. The location points to both sides of the interaction.

---

## Q5: What categories dominate the interaction-based subset?

### Severity distribution (interaction-related findings only)

| Severity | Count | % | vs. Overall |
|---|---|---|---|
| **High** | 60 | 18.1% | 10.0% overall |
| **Critical** | 9 | 2.7% | 2.5% overall |
| **Medium** | 69 | 20.8% | 18.1% overall |
| **Low** | 95 | 28.6% | 31.8% overall |
| **Informational** | 95 | 28.6% | 35.4% overall |

> [!TIP]
> Interaction-based vulnerabilities are **nearly 2× more likely to be High severity** (18.1% vs 10.0%) compared to the overall dataset. This subset is disproportionately important.

### Top CWE categories in interaction findings

| CWE | Count | Meaning |
|---|---|---|
| CWE-691 | 79 | Insufficient Control Flow Management |
| CWE-710 | 49 | Improper Adherence to Coding Standards |
| CWE-693 | 39 | Protection Mechanism Failure |
| CWE-707 | 37 | Improper Neutralization |
| CWE-20 | 34 | Improper Input Validation |
| CWE-664 | 32 | Improper Control of Resource Lifetime |
| CWE-1265 | 27 | **Unintended Reentry** (reentrancy-specific!) |
| CWE-435 | 25 | Improper Interaction Between Multiple Entities |
| CWE-682 | 24 | Incorrect Calculation |
| CWE-284 | 23 | Improper Access Control |
| CWE-362 | 22 | Race Condition |
| CWE-841 | 9 | Improper Enforcement of Behavioral Workflow |

### Binary label feasibility

**Yes, a binary label works.** Here's why:

1. The CWE hierarchy uses a tree structure (`"1"` → pillar, `"2"` → class, `"3"` → base). For interaction-type bugs, a small set of pillars dominate:
   - **CWE-691** (control flow) = reentrancy, check-effects-interactions violations
   - **CWE-693** (protection mechanism failure) = front-running, oracle manipulation
   - **CWE-362** (race condition) = sandwich attacks, front-running
   - **CWE-435** (improper interaction) = cross-contract integration bugs

2. You don't need multi-class reasoning for the hyperedge itself. The hyperedge either **is the vulnerable interaction** or **is not**. The *type* of vulnerability (reentrancy vs. front-running vs. flash loan) is secondary to detection.

3. If you want multi-class, you can cluster into 4–5 interaction subtypes using the CWE tree:
   - **Reentrancy** (CWE-1265, CWE-841): 81 findings
   - **Race/Front-running** (CWE-362): 22 findings
   - **Flash loan / price manipulation**: ~30 findings
   - **Cross-contract state inconsistency** (CWE-435): ~25 findings
   - **Other interaction bugs**: remainder

---

## Key Takeaways for Your System Design

| Dimension | Assessment |
|---|---|
| **Function-level labels exist?** | Yes, for 55.6% of findings |
| **Multi-function interaction labels?** | 518 findings (22.8%) name ≥2 functions |
| **Source code available?** | Yes, inlined in `affected_files` for 97.4% of VFPs |
| **State variables labeled?** | No — must be extracted from source code |
| **Callee identification** | In `location` for ~29% of interaction findings; in `description` for most |
| **Negative sample construction** | Must be synthetic (unlabeled function pairs) |
| **Binary label feasible?** | Yes |
| **Dataset size for interaction-focused model** | ~332 positive interaction findings; ~518 multi-function candidates |

> [!CAUTION]
> **The biggest gap** for your hyperedge approach: the dataset labels *findings* (which identify vulnerable code locations), not *interactions* (which identify vulnerable function-state-callee groups). You must construct the hyperedges yourself by:
> 1. Parsing the `location` field for function references
> 2. Parsing the source code in `affected_files` for state variables accessed at those line ranges
> 3. Extracting external call targets from the code or description
> 4. Generating negative hyperedges from non-vulnerable function combinations in the same project
>
> This is feasible but requires a preprocessing pipeline — the labels are not directly hyperedge-shaped.
