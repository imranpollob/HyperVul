# HyperVul — Rule-Based Baseline Comparison (test split)

Test: **169** hyperedges (44 pos / 125 neg); bottleneck-joined 169/169.

> Slither/Mythril not run: FORGE/DAppSCAN contracts import unbundled @openzeppelin/@uniswap/node_modules deps and do not compile standalone (static-analyzer compilation-coverage gap). These rules emulate the static-analyzer family over identical features.

| Detector | Precision | Recall | F1 | F2 | Test-neg FPR | (tp/fp/fn) |
| :-- | :--: | :--: | :--: | :--: | :--: | :--: |
| AllPositive (floor) | 26.0 | 100.0 | 41.3 | 63.8 | 100.0 | 44/125/0 |
| HasLowLevel | 25.0 | 2.3 | 4.2 | 2.8 | 2.4 | 1/3/43 |
| UncheckedLowLevel (SWC-104) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0/0/44 |
| UnguardedExtWrite (SWC-107) | 24.4 | 25.0 | 24.7 | 24.9 | 27.2 | 11/34/33 |
| NotSafeERC20 | 75.0 | 20.5 | 32.1 | 23.9 | 2.4 | 9/3/35 |

> The hard-negative design makes every test hyperedge contain external calls, so a trivial 'flag any external call' detector is degenerate (≡ AllPositive). The interesting question is whether our model beats the security-pattern rules — i.e. learns more than a curated heuristic.