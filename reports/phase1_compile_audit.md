# Phase 1 Compile-Coverage Audit

Attempted to flatten + compile (solc-only, no Slither analysis) every unique source file referenced across `data/splits/{train.json,val_features.json,test_features.json}` -- the dataset the Slither/Mythril baseline-comparison harnesses run against.

**54/215 files compiled successfully (25.1%).**

## Failure reasons

| Reason | Count |
|---|---:|
| solc_error:Expected ';' but got '('|fallback_v0.8.0:solc_error:unknown_solc_error | 45 |
| solc_error:Expected ';' but got '(' | 13 |
| solc_error:Expected ')' but got identifier|fallback_v0.8.0:solc_error:unknown_solc_error | 13 |
| solc_error:Duplicate experimental feature name.|fallback_v0.8.0:solc_error:unknown_solc_error | 10 |
| solc_error:Expected ')' but got identifier|fallback_v0.8.16:solc_error:unknown_solc_error | 7 |
| solc_error:Expected ';' but got '{'|fallback_v0.8.0:solc_error:unknown_solc_error | 7 |
| solc_error:No visibility specified. Did you intend to add "public"?|fallback_v0.8.0:solc_error:unknown_solc_error | 6 |
| solc_error:Identifier not found or not unique.|fallback_v0.8.16:solc_error:unknown_solc_error | 4 |
| solc_error:Identifier not found or not unique.|fallback_v0.8.0:solc_error:unknown_solc_error | 4 |
| solc_error:Expected pragma, import directive or contract/interface/library definition.|fallback_v0.8.0:solc_error:unknown_solc_error | 3 |
| solc_error:Expected pragma, import directive or contract/interface/library/struct/enum/cons|fallback_v0.8.24:solc_error:Identifier is not a function name or not unique. | 2 |
| solc_error:unknown_solc_error|fallback_v0.8.20:solc_error:unknown_solc_error | 2 |
| solc_error:Expected ')' but got identifier | 2 |
| solc_error:Expected type name|fallback_v0.8.16:solc_error:unknown_solc_error | 2 |
| solc_error:Expected pragma, import directive or contract/interface/library/struct/enum/cons|fallback_v0.8.16:solc_error:unknown_solc_error | 2 |
| solc_error:Expected primary expression.|fallback_v0.8.0:solc_error:unknown_solc_error | 2 |
| solc_error:Undeclared identifier.|fallback_v0.8.0:solc_error:unknown_solc_error | 2 |
| solc_error:Expected identifier, got 'LParen'|fallback_v0.8.0:solc_error:unknown_solc_error | 2 |
| solc_error:Expected pragma, import directive or contract/interface/library/struct/enum/cons|fallback_v0.8.24:solc_error:Expected pragma, import directive or contract/interface/library/struct/enum/cons | 2 |
| solc_error:Expected pragma, import directive or contract/interface/library/struct/enum/cons|fallback_v0.8.24:solc_error:Identifier already declared. | 1 |
| solc_error:Expected pragma, import directive or contract/interface/library/struct/enum/cons|fallback_v0.8.28:solc_error:Undeclared identifier. | 1 |
| solc_error:Expected '{' but got ')'|fallback_v0.8.28:solc_error:Expected '{' but got ')' | 1 |
| solc_error:unknown_solc_error|fallback_v0.8.28:solc_error:true` (standard JSON) while enabling the optimizer. Otherwise, try removing loca | 1 |
| solc_error:Function "mcopy" not found.|fallback_v0.8.16:solc_error:unknown_solc_error | 1 |
| solc_error:Contract "LenderPool" should be marked as abstract.|fallback_v0.8.16:solc_error:unknown_solc_error | 1 |
| solc_error:Immutable variables cannot be read during contract creation time, which means th | 1 |
| solc_error:Expected ',' but got identifier|fallback_v0.8.0:solc_error:unknown_solc_error | 1 |
| solc_error:Definition of base has to precede definition of derived contract|fallback_v0.8.16:solc_error:unknown_solc_error | 1 |
| solc_error:Expected identifier, got 'Payable'|fallback_v0.8.0:solc_error:unknown_solc_error | 1 |
| solc_error:ABI coder has already been selected for this source unit.|fallback_v0.8.0:solc_error:unknown_solc_error | 1 |
| solc_error:unknown_solc_error|fallback_v0.8.16:solc_error:unknown_solc_error | 1 |
| solc_error:Contract "Vesting" should be marked as abstract.|fallback_v0.8.16:solc_error:unknown_solc_error | 1 |
| solc_error:Interfaces cannot inherit.|fallback_v0.8.0:solc_error:unknown_solc_error | 1 |
| solc_error:Contract "OKLGWithdrawable" should be marked as abstract.|fallback_v0.8.16:solc_error:unknown_solc_error | 1 |
| solc_error:Expected type name | 1 |
| solc_error:Undeclared identifier.|fallback_v0.8.16:solc_error:unknown_solc_error | 1 |
| solc_error:The state mutability modifier "constant" was removed in version 0.5.0. Use "view|fallback_v0.8.0:solc_error:unknown_solc_error | 1 |
| solc_error:ABI coder has already been selected for this source unit. | 1 |
| solc_error:oz-upgrades-unsafe-allow not valid for contracts.|fallback_v0.8.0:solc_error:unknown_solc_error | 1 |
| solc_error:Expected pragma, import directive or contract/interface/library/struct/enum/cons|fallback_v0.8.28:solc_error:Expected pragma, import directive or contract/interface/library/struct/enum/cons | 1 |
| solc_error:Member "checkTransfer" not found or not visible after argument-dependent lookup |fallback_v0.8.29:solc_error:Member "checkTransfer" not found or not visible after argument-dependent lookup  | 1 |
| solc_error:Expected pragma, import directive or contract/interface/library/struct/enum/cons|fallback_v0.8.26:solc_error:Member "toInt128" not found or not visible after argument-dependent lookup in ui | 1 |
| solc_error:Expected pragma, import directive or contract/interface/library/struct/enum/cons|fallback_v0.8.26:solc_error:true` (standard JSON) while enabling the optimizer. Otherwise, try removing loca | 1 |
| solc_error:Undeclared identifier.|fallback_v0.8.24:solc_error:Undeclared identifier. | 1 |
| solc_error:Expected primary expression.|fallback_v0.8.29:solc_error:Expected primary expression. | 1 |
| solc_error:Undeclared identifier.|fallback_v0.8.20:solc_error:unknown_solc_error | 1 |
| solc_error:Identifier not found or not unique.|fallback_v0.8.20:solc_error:unknown_solc_error | 1 |
| solc_error:Expected ')' but got identifier|fallback_v0.8.28:solc_error:Expected ')' but got identifier | 1 |
| solc_error:Expected identifier but got ','|fallback_v0.8.24:solc_error:Expected identifier but got ',' | 1 |
| solc_error:Definition of base has to precede definition of derived contract|fallback_v0.8.29:solc_error:Definition of base has to precede definition of derived contract | 1 |

## By split

| Split | Success | Total | Rate |
|---|---:|---:|---:|
| train | 43 | 157 | 27.4% |
| test_features | 10 | 30 | 33.3% |
| val_features | 1 | 28 | 3.6% |
