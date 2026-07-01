# Phase 0 Dataset Audit and Validity Check

## Executive Summary

Final decision: **FAIL**.

The current primary dataset is `data/contract_graphs/{train,val,test}.json`. Its row unit is a **contract graph**; each graph contains interaction/hyperedge nodes with binary labels. This supports deriving contract-level labels (`contract_label = any positive interaction`) and gives vulnerable interaction nodes for top-k localization. However, the current artifacts are not ready for Phase 1 augmentation because the audit found split/duplication and label-provenance risks that must be fixed or explicitly waived first.

Proceed to augmentation now: **No**. Rebuild or validate splits first, then regenerate graph files with provenance fields embedded in each interaction node.

## Dataset Structure

Primary files:

- `data/contract_graphs/train.json`: 1614 contract graphs
- `data/contract_graphs/val.json`: 167 contract graphs
- `data/contract_graphs/test.json`: 138 contract graphs

Provenance files used for reconstruction:

- `data/splits_clean/{train,val,test}.json`
- `experiments/results/forge_ast_constructable_hyperedges.json`
- `experiments/results/dappscan_ast_constructable_hyperedges.json`
- `data/FORGE-Curated/flatten/vfp-vuln/*.json`

Available graph fields: `contract, edges, graph_id, n_edges, n_helper, n_neg, n_pos, nodes, project, source, split`.

Available interaction fields: `callee_texts, external_calls, function, function_source, id, is_cross_contract, kind, label, sec, state_texts, state_vars_accessed, tier`.

Every interaction can be grouped by contract: **True**.

Graph-native source path/span available: **False**. Positive provenance was reconstructed for 294/294 positives by joining to split/provenance files. Source file or location was recovered for 294/294 positives, but this metadata is not stored in the graph dataset itself.

## Split Integrity Findings

|Severity|Finding|Description|
|---|---|---|
|NONE|same_contract_graph_id|No graph_id values appear in multiple splits.|
|NONE|same_project_id|No project values appear in multiple splits.|
|MEDIUM|exact_duplicate_function_source_across_splits|149 exact normalized interaction/function source hashes appear in multiple splits; 0 include at least one positive label.|
|HIGH|duplicate_interactions_conflicting_labels|10 exact normalized function sources have both positive and negative labels.|
|NONE|same_train_positive_source_pattern_in_val_or_test|0 train-positive function hashes also appear in val/test.|
|HIGH|exact_duplicate_contract_interaction_set_across_splits|27 exact duplicate contract interaction-source sets appear across splits.|
|HIGH|same_contract_name_near_duplicate_interaction_code|42 same contract-name graph pairs across splits share >=80% exact interaction function hashes.|

Concrete examples are written to `reports/phase0_split_leakage.csv`. Selected examples:

- **exact_duplicate_function_source_across_splits (MEDIUM)**: `{"source_hash": "4dae08a32cb7", "splits": "test|train", "labels": "0", "examples": "train:DAPP::DAppSCAN-source/contracts/PeckShield-AirSwap/airswap-protocols-b87d292aaf6e28ede564b7ea28ece39219994607::Migrations::upgrade[y=0] ; train:DAPP::DAppSCAN-source/contracts/consensys-Skyweaver/Skyweaver-contracts-bde0c184db6168bf86656a48b12d5747950b54d9::Migrations::upgrade[y=0] ; train:DAPP::DAppSCAN-source/contracts/PepperSec-Aira-Robonomic/robonomics_contracts-cc35a91de187072214d215262d8371f0159c2498::Migrations::upgrade[y=0] ; train:DAPP::DAppSCAN-source/contracts/SlowMist-CFFv2 Smart Contract Security Audit Report/cff-contract-v2-c86bef3f13c7585f547f9cd0ca900f94664e96b7::Migrations::upgrade[y=0]`
- **exact_duplicate_function_source_across_splits (MEDIUM)**: `{"source_hash": "25e5dc8ca7a8", "splits": "train|val", "labels": "0", "examples": "train:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-FraxQ42021/frax-solidity-bd40775e283923aa9e32a107abd426430a99835e::GovernorAlpha::_queueOrRevert[y=0] ; train:DAPP::DAppSCAN-source/contracts/PeckShield-Rikkei/rifi-protocol-b33243fb3a218cc195f0727fe1499cb57f5ea0b2::GovernorAlpha::_queueOrRevert[y=0] ; train:DAPP::DAppSCAN-source/contracts/PeckShield-Rikkei/rifi-protocol-b33243fb3a218cc195f0727fe1499cb57f5ea0b2::GovernorAlphaCertora::_queueOrRevert[y=0] ; train:DAPP::DAppSCAN-source/contracts/PeckShield-Atlantis/atlantis-protocol-bsc-766acebba9316eced1c15abf6158b31f470a947f::GovernorAlpha::_queueOrRevert[y=0]`
- **exact_duplicate_function_source_across_splits (MEDIUM)**: `{"source_hash": "f36a4485c188", "splits": "train|val", "labels": "0", "examples": "train:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-FraxQ42021/frax-solidity-bd40775e283923aa9e32a107abd426430a99835e::GovernorAlpha::state[y=0] ; train:DAPP::DAppSCAN-source/contracts/PeckShield-Rikkei/rifi-protocol-b33243fb3a218cc195f0727fe1499cb57f5ea0b2::GovernorAlpha::state[y=0] ; train:DAPP::DAppSCAN-source/contracts/PeckShield-Rikkei/rifi-protocol-b33243fb3a218cc195f0727fe1499cb57f5ea0b2::GovernorAlphaCertora::state[y=0] ; train:DAPP::DAppSCAN-source/contracts/PeckShield-Atlantis/atlantis-protocol-bsc-766acebba9316eced1c15abf6158b31f470a947f::GovernorAlpha::state[y=0] ; train:DAPP::DAppSCAN-source/contr`
- **duplicate_interactions_conflicting_labels (HIGH)**: `{"source_hash": "19c4099dff5f", "splits": "train", "examples": "train:FORGE::vfp_00032::AbstractStakingStrategy::mintShares[y=0] ; train:FORGE::vfp_00032::RewardManagerMixin::mintShares[y=0] ; train:FORGE::vfp_00032::AbstractYieldStrategy::mintShares[y=1] ; train:FORGE::vfp_00032::AbstractSingleSidedLP::mintShares[y=0] ; train:FORGE::vfp_00032::CurveConvex2Token::mintShares[y=0]"}`
- **duplicate_interactions_conflicting_labels (HIGH)**: `{"source_hash": "cb1b285f5f52", "splits": "train", "examples": "train:FORGE::vfp_00032::GenericERC4626WithdrawRequestManager::stakeTokens[y=1] ; train:FORGE::vfp_00032::AbstractWithdrawRequestManager::stakeTokens[y=0]"}`
- **duplicate_interactions_conflicting_labels (HIGH)**: `{"source_hash": "370b1da585e9", "splits": "val", "examples": "val:FORGE::vfp_00156::HyperCoreFlowExecutor::_initiateSwapFlow[y=1] ; val:FORGE::vfp_00156::DstOFTHandler::_initiateSwapFlow[y=0] ; val:FORGE::vfp_00156::SponsoredCCTPDstPeriphery::_initiateSwapFlow[y=0]"}`
- **exact_duplicate_contract_interaction_set_across_splits (HIGH)**: `{"signature": "ce98735ec8b8", "examples": "train:DAPP::DAppSCAN-source/contracts/PeckShield-AirSwap/airswap-protocols-b87d292aaf6e28ede564b7ea28ece39219994607::Migrations ; train:DAPP::DAppSCAN-source/contracts/consensys-Skyweaver/Skyweaver-contracts-bde0c184db6168bf86656a48b12d5747950b54d9::Migrations ; train:DAPP::DAppSCAN-source/contracts/PepperSec-Aira-Robonomic/robonomics_contracts-cc35a91de187072214d215262d8371f0159c2498::Migrations ; train:DAPP::DAppSCAN-source/contracts/SlowMist-CFFv2 Smart Contract Security Audit Report/cff-contract-v2-c86bef3f13c7585f547f9cd0ca900f94664e96b7::Migrations ; train:DAPP::DAppSCAN-source/contracts/consensys-MCDEX_Mai_Protocol_V2/mai-protocol-v2-4b198083`
- **exact_duplicate_contract_interaction_set_across_splits (HIGH)**: `{"signature": "e17100050ef6", "examples": "train:DAPP::DAppSCAN-source/contracts/PeckShield-DarkCrypto/darkcrypto-contracts-fee5be8d36459aebed2b84e6493875b3dc0366fd::Timelock ; train:DAPP::DAppSCAN-source/contracts/QuillAudits-Bond Appetit-Bond Appetit/bondappetit-protocol-355180f0aca0b29d60d808f761052956b7a3a159::Timelock ; train:DAPP::DAppSCAN-source/contracts/PeckShield-DSG/core-6f607f77698936e132e4e9b5cb4d75580636d919::Timelock ; test:DAPP::DAppSCAN-source/contracts/PeckShield-TranchessV1.1/contract-core-68a86350313c1cb9e5467e791d3e9efaf228a0df::Timelock"}`
- **exact_duplicate_contract_interaction_set_across_splits (HIGH)**: `{"signature": "a4170a1e4bf5", "examples": "train:DAPP::DAppSCAN-source/contracts/PeckShield-MilkySwap/milkyswap-59f163e9959cf8bae4a521a9648219b553312e07::UniswapV2Factory ; val:DAPP::DAppSCAN-source/contracts/PeckShield-SushiSwap/sushiswap-180bc9b642bba79c1ee4a63f71a3a0d36e64aa63::UniswapV2Factory"}`
- **same_contract_name_near_duplicate_interaction_code (HIGH)**: `{"jaccard": 1.0, "a": "train:DAPP::DAppSCAN-source/contracts/PeckShield-AirSwap/airswap-protocols-b87d292aaf6e28ede564b7ea28ece39219994607::Migrations", "b": "test:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-Liquity/dev-f0df3efa5a5f05b205752184cfce107c5bd6e06c::Migrations", "overlap": 1, "sizes": "1/1"}`
- **same_contract_name_near_duplicate_interaction_code (HIGH)**: `{"jaccard": 1.0, "a": "train:DAPP::DAppSCAN-source/contracts/consensys-Skyweaver/Skyweaver-contracts-bde0c184db6168bf86656a48b12d5747950b54d9::Migrations", "b": "test:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-Liquity/dev-f0df3efa5a5f05b205752184cfce107c5bd6e06c::Migrations", "overlap": 1, "sizes": "1/1"}`
- **same_contract_name_near_duplicate_interaction_code (HIGH)**: `{"jaccard": 1.0, "a": "train:DAPP::DAppSCAN-source/contracts/PepperSec-Aira-Robonomic/robonomics_contracts-cc35a91de187072214d215262d8371f0159c2498::Migrations", "b": "test:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-Liquity/dev-f0df3efa5a5f05b205752184cfce107c5bd6e06c::Migrations", "overlap": 1, "sizes": "1/1"}`

## Class Imbalance Findings

|split|contracts|contract +|contract -|contract -/+|interactions|interaction +|interaction -|interaction -/+|
|---|---|---|---|---|---|---|---|---|
|train|1614|153|1461|9.55|10740|215|10525|48.95|
|val|167|28|139|4.96|844|38|806|21.21|
|test|138|25|113|4.52|773|41|732|17.85|

Contract-level imbalance is better than interaction-level imbalance in every split: {'train': True, 'val': True, 'test': True}.

## Interaction and Positive Density

|split|int/contract min|max|mean|median|p90|max +/positive contract|mean +/positive contract|contracts with >1 +|all-negative risky contracts|
|---|---|---|---|---|---|---|---|---|---|
|train|1|31|6.65|5.0|17|7|1.41|34|136|
|val|1|27|5.05|3|13|5|1.36|7|8|
|test|1|31|5.60|3.0|15|4|1.64|11|3|

## Vulnerability Type Distribution

|vulnerability type|all positives|train|val|test|
|---|---|---|---|---|
|Reentrancy (SWC-107)|146|102|21|23|
|Unchecked Call Return (SWC-104)|78|60|12|6|
|Front-running / Tx Order (SWC-114)|64|47|5|12|
|Delegatecall (SWC-112)|6|6|0|0|

## Label Quality Findings

Suspicious label rows written: **527** in `reports/phase0_suspicious_labels.csv`.

|issue|count|
|---|---|
|negative_contains_strong_low_level_call_pattern|210|
|negative_contract_many_risky_interactions|147|
|unchecked_call_positive_without_low_level_call_signal|77|
|front_running_positive_weak_fit_for_interaction_localization|64|
|exact_duplicate_source_conflicting_label|29|

Most serious examples:

- **HIGH negative_contains_strong_low_level_call_pattern**: `train:FORGE::vfp_00126::HubPool::executeRootBundle` label=0 type= details=Negative interaction contains low-level call/delegatecall/send/staticcall signal.
- **HIGH negative_contains_strong_low_level_call_pattern**: `train:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-FraxQ42021/frax-solidity-bd40775e283923aa9e32a107abd426430a99835e::SigRelayer2::relayBySigsGST` label=0 type= details=Negative interaction contains low-level call/delegatecall/send/staticcall signal.
- **HIGH negative_contains_strong_low_level_call_pattern**: `train:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-FraxQ42021/frax-solidity-bd40775e283923aa9e32a107abd426430a99835e::SigRelayer2::relayBySigs` label=0 type= details=Negative interaction contains low-level call/delegatecall/send/staticcall signal.
- **HIGH unchecked_call_positive_without_low_level_call_signal**: `train:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-FraxQ42021/frax-solidity-bd40775e283923aa9e32a107abd426430a99835e::TWAMM::provideLiquidity` label=1 type=Unchecked Call Return (SWC-104) details=Unchecked-call positive lacks obvious .call/.send/delegatecall/staticcall signal in function/callee text.
- **HIGH negative_contains_strong_low_level_call_pattern**: `train:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-FraxQ42021/frax-solidity-bd40775e283923aa9e32a107abd426430a99835e::CErc20Delegator::delegateAndReturn` label=0 type= details=Negative interaction contains low-level call/delegatecall/send/staticcall signal.
- **HIGH unchecked_call_positive_without_low_level_call_signal**: `train:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-88mph/88mph-contracts-76cd9d1fc45e65f5d0f686621fe6af85c40aa140::xMPH::_deposit` label=1 type=Unchecked Call Return (SWC-104) details=Unchecked-call positive lacks obvious .call/.send/delegatecall/staticcall signal in function/callee text.
- **HIGH unchecked_call_positive_without_low_level_call_signal**: `train:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-88mph/88mph-contracts-76cd9d1fc45e65f5d0f686621fe6af85c40aa140::xMPH::_withdraw` label=1 type=Unchecked Call Return (SWC-104) details=Unchecked-call positive lacks obvious .call/.send/delegatecall/staticcall signal in function/callee text.
- **HIGH unchecked_call_positive_without_low_level_call_signal**: `train:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-88mph/88mph-contracts-76cd9d1fc45e65f5d0f686621fe6af85c40aa140::xMPH::_distributeReward` label=1 type=Unchecked Call Return (SWC-104) details=Unchecked-call positive lacks obvious .call/.send/delegatecall/staticcall signal in function/callee text.
- **HIGH negative_contains_strong_low_level_call_pattern**: `train:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-YieldV2/vault-v2-819a713416249da92c44eb629ed26a49425a4656::Ladle::batch` label=0 type= details=Negative interaction contains low-level call/delegatecall/send/staticcall signal.
- **HIGH negative_contains_strong_low_level_call_pattern**: `train:DAPP::DAppSCAN-source/contracts/Trail_of_Bits-YieldV2/vault-v2-819a713416249da92c44eb629ed26a49425a4656::TLMModule::register` label=0 type= details=Negative interaction contains low-level call/delegatecall/send/staticcall signal.

## Leakage and Duplication Findings

Key leakage/duplication risks:

- Exact graph IDs and project IDs do not cross splits if marked `NONE` in the leakage table.
- Exact function-source duplicates across splits and same contract-name near-duplicates are still important because they can leak implementation patterns even when project IDs differ.
- Exact duplicate normalized functions with conflicting labels are a major validity risk for both binary detection and top-k ranking.

Full examples are in `reports/phase0_split_leakage.csv`.

## Contract-Level Task Suitability

Contract-level labels are recoverable because every graph contains `n_pos`/`n_neg` and interaction labels. The contract label can be derived as `n_pos > 0`.

All-split interaction neg:pos ratio: **41.03**.

All-split contract neg:pos ratio: **8.32**.

Assessment: contract-level detection is structurally supported and should reduce false-positive pressure because one clean contract is one negative decision instead of many negative interaction decisions. It is not safe to evaluate until split leakage and duplicate/conflicting labels are cleaned.

## Top-k Localization Suitability

Positive contracts: **206**.

Positive contracts with a single positive interaction: **154**.

Positive contracts with multiple positive interactions: **52**.

Top-k localization is partially supported: positive interaction labels identify vulnerable nodes inside positive contracts. The missing piece is graph-native localization provenance: source file, line span, finding id, vulnerability type, and finding title should be stored directly on positive nodes. Recommended metrics are **Top-k hit / Recall@k** and **MRR**. MAP is useful only after cleanup if enough positive contracts have multiple true positive interactions.

## Vulnerability-Specific Suitability

|type|train + int|val + int|test + int|train + contracts|val + contracts|test + contracts|low-level/delegate signal|HyperVul fit|experiment suitability|
|---|---|---|---|---|---|---|---|---|---|
|reentrancy|102|21|23|77|16|16|7|High: state plus external-call ordering is the intended interaction pattern.|Viable, but train/test duplication and missing graph-native spans must be fixed first.|
|unchecked low-level call|60|12|6|36|8|4|1|Medium: external-call evidence fits, but current labels often lack explicit low-level-call signals in graph text.|Potentially viable after auditing positives without low-level-call signal and rebuilding splits.|
|delegatecall|6|0|0|3|0|0|5|Medium: delegatecall is interaction-like, but label volume/split coverage is too small.|Not viable as standalone with current split: no val/test positives.|
|front-running|47|5|12|41|4|8|0|Low: often requires transaction-order/economic context outside the hyperedge representation.|Weak standalone target; use only as exploratory or remove from narrowed-scope core.|

## Top 10 Most Serious Risks

1. Split leakage/duplication risk is material: 0 train-positive function hashes also appear in val/test. 42 same contract-name graph pairs across splits share >=80% exact interaction function hashes.
2. Exact duplicate source label conflicts exist: 10 normalized function hashes have both positive and negative labels.
3. The graph dataset drops graph-native file path, line span, finding id, and vulnerability type; provenance can be reconstructed but is not embedded in `data/contract_graphs`.
4. Top-k localization has vulnerable-node labels, but graph-native source spans are absent; 294/294 positives have recovered line/raw-location metadata.
5. Contract-level imbalance improves over interaction-level imbalance but remains nontrivial: all-split contract neg:pos=8.32, interaction neg:pos=41.03.
6. Front-running labels are weakly aligned with the HyperVul interaction representation because transaction-order/economic context is often outside a single state-plus-call hyperedge.
7. Delegatecall has insufficient split coverage for standalone evaluation; current positives are train-only.
8. Negative labels include strong risky patterns: 210 negative interactions contain low-level/delegatecall/send/staticcall signals.
9. 147 all-negative contracts have many risky-looking interactions, creating likely false-positive pressure and label-review burden.
10. The original provenance split files have far fewer rows than the expanded graph interactions, so not every graph negative has source-path provenance for file-level leakage checks.

## Recommended Next Actions

1. Rebuild splits at project/contract-clone level before augmentation. Use exact normalized function hashes, graph signatures, and near-duplicate contract-name checks as gates.
2. Resolve exact duplicate function-source label conflicts manually or drop ambiguous duplicates.
3. Regenerate `data/contract_graphs` with provenance embedded per interaction: source file/path, line span, finding id, finding title, severity, vulnerability type, normalized source hash, and raw evidence pointer.
4. Narrow Phase 1 experiments to reentrancy first, with unchecked low-level call only after reviewing positives that lack low-level-call signal.
5. Exclude or quarantine delegatecall and front-running from the main narrowed-scope evaluation unless more split-balanced positives are added and manually validated.
6. Keep contract-level detection plus top-k localization as the redesigned objective, but evaluate only after split and label cleanup.

## Final Decision

**FAIL**.

Contract-level detection plus top-k interaction localization is conceptually supported by the current graph representation, but the current dataset state is not clean enough for augmentation or final evaluation. The highest-priority fix before Phase 1 is to rebuild leakage-safe splits and remove/resolve duplicate conflicting labels, then regenerate graph files with embedded provenance.


## Have you considered the original dappscan and forge-curated datasets

Yes, but in a specific way.

I treated `data/contract_graphs/{train,val,test}.json` as the **current model dataset**, then used the original datasets as **provenance sources** to validate labels and recover missing metadata:

- DAppSCAN:
  - `data/DAppSCAN/DAppSCAN-source/SWCsource/**/*.json`
  - `data/DAppSCAN/DAppSCAN-source/contracts/...`
  - `experiments/results/dappscan_ast_constructable_hyperedges.json`

- FORGE-Curated:
  - `data/FORGE-Curated/flatten/vfp-vuln/*.json`
  - `data/FORGE-Curated/dataset-curated/...`
  - `experiments/results/forge_ast_constructable_hyperedges.json`

The audit did **not** fully re-audit every raw DAppSCAN/FORGE contract independent of the generated graph dataset. It focused on whether the **currently materialized HyperVul graph splits** can support the redesigned task.

So the answer is:

- **Yes**, original DAppSCAN/FORGE-Curated were considered for label provenance, vulnerability type, source location, and evidence recovery.
- **No**, I did not run a separate raw-dataset-wide audit of all original contracts that never made it into `data/contract_graphs`.
- The report flags this distinction: the graph dataset drops provenance fields, so I reconstructed them from original sources rather than finding them natively in the graph JSON.

If we want Phase 0 to be stricter, the next useful addition is a raw-source coverage audit: original positives → constructable hyperedges → graph nodes, with counts for dropped findings and why they were dropped.