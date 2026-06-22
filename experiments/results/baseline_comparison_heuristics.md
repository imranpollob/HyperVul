# HyperVul — Rule-Based Baseline Comparison (test split)

Test: **176** hyperedges (45 pos / 131 neg); bottleneck-joined 169/176.

> Slither/Mythril not run: FORGE/DAppSCAN contracts import unbundled @openzeppelin/@uniswap/node_modules deps and do not compile standalone (static-analyzer compilation-coverage gap). These rules emulate the static-analyzer family over identical features.

| Detector | Precision | Recall | F1 | F2 | Test-neg FPR | (tp/fp/fn) |
| :-- | :--: | :--: | :--: | :--: | :--: | :--: |
| AllPositive (floor) | 25.6 | 100.0 | 40.7 | 63.2 | 100.0 | 45/131/0 |
| HasLowLevel | 25.0 | 2.2 | 4.1 | 2.7 | 2.3 | 1/3/44 |
| UncheckedLowLevel (SWC-104) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0/0/45 |
| UnguardedExtWrite (SWC-107) | 24.4 | 24.4 | 24.4 | 24.4 | 26.0 | 11/34/34 |
| NotSafeERC20 | 75.0 | 20.0 | 31.6 | 23.4 | 2.3 | 9/3/36 |

> The hard-negative design makes every test hyperedge contain external calls, so a trivial 'flag any external call' detector is degenerate (≡ AllPositive). The interesting question is whether our model beats the security-pattern rules — i.e. learns more than a curated heuristic.