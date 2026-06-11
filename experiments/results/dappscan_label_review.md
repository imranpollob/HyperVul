# DAppSCAN Label Quality Review

This document presents evidence for human review of DAppSCAN positive hyperedges.
Each entry includes the SWC annotation, function source, hyperedge components,
and a pre-classification. **Human reviewers should verify each classification.**

## Summary

**Total items reviewed**: 227

| Classification | Count | % |
|---|---|---|
| CONFIRMED | 216 | 95.2% |
| MISLOCATED | 5 | 2.2% |
| COMMIT_DRIFT | 2 | 0.9% |
| DUBIOUS | 4 | 1.8% |

### By Group

| Group | Total | CONFIRMED | MISLOCATED | COMMIT_DRIFT | DUBIOUS |
|---|---|---|---|---|---|
| TEST Cross-Contract | 16 | 13 | 0 | 0 | 3 |
| VAL Cross-Contract | 14 | 14 | 0 | 0 | 0 |
| TRAIN Cross-Contract | 117 | 113 | 4 | 0 | 0 |
| TEST Intra-Contract | 9 | 8 | 0 | 0 | 1 |
| VAL Intra-Contract | 14 | 13 | 0 | 1 | 0 |
| TRAIN Intra-Contract | 57 | 55 | 1 | 1 | 0 |

---
## TEST Cross-Contract (16 items)

### UpgradeableToken.setUpgradeAgent

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: setUpgradeAgent
- **Line Range**: L373 - L394
- **File**: `DAppSCAN-source/contracts/Coinbae-TapCoins_Token_Contract/code/Etherscan-0x9F599410D207f3D2828a8712e5e543AC2E040382.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`setUpgradeAgent`, lines=`L373 - L394`

#### 2. Function Source Code
```solidity
function setUpgradeAgent(address agent) external {

      if(!canUpgrade()) {
        // The token is not yet in a state that we could think upgrading
        throw;
      }

      if (agent == 0x0) throw;
      // Only a master can designate the next agent
      if (msg.sender != upgradeMaster) throw;
      // Upgrade has already begun for an agent
      if (getUpgradeState() == UpgradeState.Upgrading) throw;

      upgradeAgent = UpgradeAgent(agent);

      // Bad interface
      if(!upgradeAgent.isUpgradeAgent()) throw;
      // Make sure that token supplies match in source and target
      if (upgradeAgent.originalSupply() != totalSupply) throw;

      UpgradeAgentSet(upgradeAgent);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['totalSupply', 'upgradeAgent', 'upgradeMaster']
- **External calls**: `upgradeAgent.originalSupply()` (method: originalSupply, receiver: upgradeAgent)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['totalSupply', 'upgradeAgent', 'upgradeMaster']
- **External calls**: `upgradeAgent.originalSupply()` (call on contract-typed state var 'upgradeAgent' (type: UpgradeAgent))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### BUSDVYNCSTAKE.unStake

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: unStake
- **Line Range**: L201
- **File**: `DAppSCAN-source/contracts/Hacken-VYNKSAFE/code/main.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`unStake`, lines=`L201`

#### 2. Function Source Code
(102 lines, showing first 30 + last 15)
```solidity
function unStake(uint256 amount, uint256 unstakeOption)
        external
        nonReentrant
    {
        require(
            unstakeOption > 0 && unstakeOption <= 3,
            "wrong unstakeOption, choose from 1,2,3"
        );
        uint256 lpAmountNeeded;
        uint256 pending = compoundedReward(msg.sender);
        uint256 stakeBalance = userInfo[msg.sender].stakeBalance;
        (, , uint256 up) = data.returnData(); // SWC-104-Unchecked Call Return Value: L201

        if (amount >= stakeBalance) {
            // withdraw all
            lpAmountNeeded = userInfo[msg.sender].lpAmount;
        } else {
            //calculate LP needed that corresponding with amount
            lpAmountNeeded = getLPTokenByAmount1(amount);
            if (lpAmountNeeded >= userInfo[msg.sender].lpAmount) {
                // if >= current lp, use all lp
                lpAmountNeeded = userInfo[msg.sender].lpAmount;
            }
        }

// SWC-135-Code With No Effects: L215 - L218
        require(
            userInfo[msg.sender].lpAmount >= lpAmountNeeded,
            "withdraw: not good"
        );
    // ... truncated ...
            userInfo[msg.sender].lpAmount = 0;
            userInfo[msg.sender].stakeBalanceWithReward = 0;
            userInfo[msg.sender].stakeBalance = 0;
            userInfo[msg.sender].isStaker = false;
            userInfo[msg.sender].totalClaimedReward = 0;
            userInfo[msg.sender].autoClaimWithStakeUnstake = 0;
            userInfo[msg.sender].lastCompoundedRewardWithStakeUnstakeClaim = 0;
        }

        if (userInfo[msg.sender].pendingRewardAfterFullyUnstake == 0) {
            userInfo[msg.sender].isClaimAferUnstake = false;
        }

        totalSupply = totalSupply.sub(lpAmountNeeded);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['busd', 'data', 'totalSupply', 'u', 'userInfo', 'vync']
- **External calls**: `data.returnData()` (method: returnData, receiver: data), `busd.transfer(msg.sender, _amount)` (method: transfer, receiver: busd), `busd.transfer(msg.sender, busdAmount)` (method: transfer, receiver: busd), `vync.transfer(msg.sender, _vyncAmount)` (method: transfer, receiver: vync), `vync.transfer(msg.sender, vyncAmount)` (method: transfer, receiver: vync)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['busd', 'data', 'totalSupply', 'u', 'userInfo', 'vync']
- **External calls**: `data.returnData()` (call on contract-typed state var 'data' (type: GetDataInterface)), `busd.transfer(msg.sender, _amount)` (low-level .transfer()), `busd.transfer(msg.sender, busdAmount)` (low-level .transfer()), `vync.transfer(msg.sender, _vyncAmount)` (low-level .transfer()), `vync.transfer(msg.sender, vyncAmount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Staking.depositStable

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: depositStable
- **Line Range**: L674
- **File**: `DAppSCAN-source/contracts/Inspex-Tokens, Farm & Shop/-SpeedStar-Audit-3e39d7acf9c1aa9f3a5511c161c2035ba7d6bc1f/contracts/farm/Staking.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`depositStable`, lines=`L674`

#### 2. Function Source Code
```solidity
function depositStable(uint256 _tokenId)
        external
        plotLimitStaking(_tokenId)
    {
        UserInfo storage user = userInfo[msg.sender];
        require(!user.ownedStable[_tokenId], "Already staking");

        updatePool();
        if (user.amount > 0) {
            uint256 pending = pendingSpeed(msg.sender); //.sub(user.rewardDebt);
            if (pending > 0) {
                payReward(user);
            }
        }

        uint256 multiplier = facility.multipliers(_tokenId);
        facility.transferFrom(address(msg.sender), address(this), _tokenId);

        Stable[] storage userStable = user.stables; //[]
        user.stableIndex[_tokenId] = userStable.length; //0

        mapping(uint256 => bool) storage userOwnerStable = user.ownedStable;
        userOwnerStable[_tokenId] = true;
        // 0
        userStable.push(); //1

        Stable storage newStable = userStable[user.stableIndex[_tokenId]];
        newStable.tokenId = _tokenId;
        newStable.multiplier = multiplier;

        userPlots[msg.sender] = userPlots[msg.sender].add(
            facility.size(_tokenId)
        );
        user.rewardDebt = user.amount.mul(poolInfo.accSpeedPerShare).div(1e12); //pendingSpeed(msg.sender);

        emit DepositStable(msg.sender, _tokenId);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['facility', 'poolInfo', 'userInfo', 'userPlots']
- **External calls**: `facility.multipliers(_tokenId)` (method: multipliers, receiver: facility), `facility.transferFrom(address(msg.sender), address(this), _tokenId)` (method: transferFrom, receiver: facility), `userStable.push()` (method: push, receiver: userStable), `facility.size(_tokenId)` (method: size, receiver: facility), `user.amount.mul(poolInfo.accSpeedPerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(poolInfo.accSpeedPerShare)` (method: mul, receiver: user)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['facility', 'poolInfo', 'userInfo', 'userPlots']
- **External calls**: `facility.multipliers(_tokenId)` (call on contract-typed state var 'facility' (type: IFacility)), `facility.transferFrom(address(msg.sender), address(this), _tokenId)` (call on contract-typed state var 'facility' (type: IFacility)), `userStable.push()` (call on contract-typed local var 'userStable' (type: Stable[])), `facility.size(_tokenId)` (call on contract-typed state var 'facility' (type: IFacility)), `user.amount.mul(poolInfo.accSpeedPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(poolInfo.accSpeedPerShare)` (call on contract-typed local var 'user' (type: UserInfo))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### BankingNode.collectFees

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: collectFees
- **Line Range**: L453-L470
- **File**: `DAppSCAN-source/contracts/PeckShield-BNPL/BNPL-0ee587a081668dcab166a3a275b8a6c4794ead4d/contracts/BankingNode.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`collectFees`, lines=`L453-L470`

#### 2. Function Source Code
```solidity
function collectFees() external {
        //requirement check for nonzero inside of _swap
        //33% to go to operator as baseToken
        address _baseToken = baseToken;
        address _bnpl = BNPL;
        address _operator = operator;
        uint256 _operatorFees = IERC20(_baseToken).balanceOf(address(this)) / 3;
        TransferHelper.safeTransfer(_baseToken, _operator, _operatorFees);
        //remainder (67%) is traded for staking rewards
        //no need for slippage on small trade
        uint256 _stakingRewards = _swapToken(
            _baseToken,
            _bnpl,
            0,
            IERC20(_baseToken).balanceOf(address(this))
        );
        emit feesCollected(_operatorFees, _stakingRewards);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['BNPL', 'baseToken', 'operator']
- **External calls**: `IERC20(_baseToken).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `TransferHelper.safeTransfer(_baseToken, _operator, _operatorFees)` (method: safeTransfer, receiver: TransferHelper), `IERC20(_baseToken).balanceOf(address(this))` (method: balanceOf, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['BNPL', 'baseToken', 'operator']
- **External calls**: `IERC20(_baseToken).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `TransferHelper.safeTransfer(_baseToken, _operator, _operatorFees)` (SafeERC20 .safeTransfer()), `IERC20(_baseToken).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### AbyssEth2Depositor.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L82
- **File**: `DAppSCAN-source/contracts/QuillAudits-Abyss Finance-Abyss Eth2 Depositor/abyss-eth2depositor-a2d58dea4d79846dc682fe93ac3e0eca02323d11/contracts/AbyssEth2Depositor.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L82`

#### 2. Function Source Code
```solidity
function deposit(
        bytes[] calldata pubkeys,
        bytes[] calldata withdrawal_credentials,
        bytes[] calldata signatures,
        bytes32[] calldata deposit_data_roots
    ) external payable whenNotPaused {

        uint256 nodesAmount = pubkeys.length;

        require(nodesAmount > 0 && nodesAmount <= 100, "AbyssEth2Depositor: you can deposit only 1 to 100 nodes per transaction");
        require(msg.value == SafeMath.mul(collateral, nodesAmount), "AbyssEth2Depositor: the amount of ETH does not match the amount of nodes");
        require(
            withdrawal_credentials.length == nodesAmount &&
            signatures.length == nodesAmount &&
            deposit_data_roots.length == nodesAmount,
            "AbyssEth2Depositor: amount of parameters do no match");

        for (uint256 i = 0; i < nodesAmount; ++i) {

            IDepositContract(address(depositContract)).deposit{value: collateral}(
                pubkeys[i],
                withdrawal_credentials[i],
                signatures[i],
                deposit_data_roots[i]
            );

        }

        emit DepositEvent(msg.sender, nodesAmount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['collateral', 'depositContract']
- **External calls**: `IDepositContract(address(depositContract)).deposit{value: collateral}(
                pubkeys[i],
                withd` (method: deposit, receiver: IDepositContract)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['collateral', 'depositContract']
- **External calls**: `IDepositContract(address(depositContract)).deposit{value: collateral}(
                pubkeys[i],
                withd` (inline cast call IDepositContract(...).deposit())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StakingRewardsV3.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L210 - L226
- **File**: `DAppSCAN-source/contracts/QuillAudits-Keep3r.Network-Keep3r.Network/StakingRewardsV3-13ecc6966ae1a413f62224382bfd4d64b1a22351/contracts/StakingRewardsV3-1.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L210 - L226`

#### 2. Function Source Code
```solidity
function deposit(uint tokenId) external update(tokenId) {
        (,,address token0,address token1,uint24 fee,int24 tickLower,int24 tickUpper,uint128 _liquidity,,,,) = nftManager.positions(tokenId);
        address _pool = PoolAddress.computeAddress(factory,PoolAddress.PoolKey({token0: token0, token1: token1, fee: fee}));

        require(pool == _pool);
        require(_liquidity > 0);

        (,int24 _tick,,,,,) = UniV3(_pool).slot0();
        require(tickLower < _tick && _tick < tickUpper);

        owners[tokenId] = msg.sender;
        tokenIds[msg.sender].push(tokenId);

        nftManager.transferFrom(msg.sender, address(this), tokenId);

        emit Deposit(msg.sender, tokenId, _liquidity);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['factory', 'nftManager', 'owners', 'pool', 'tokenIds']
- **External calls**: `nftManager.positions(tokenId)` (method: positions, receiver: nftManager), `PoolAddress.computeAddress(factory,PoolAddress.PoolKey({token0: token0, token1: token1, fee: fee}))` (method: computeAddress, receiver: PoolAddress), `PoolAddress.PoolKey({token0: token0, token1: token1, fee: fee})` (method: PoolKey, receiver: PoolAddress), `UniV3(_pool).slot0()` (method: slot0, receiver: UniV3), `nftManager.transferFrom(msg.sender, address(this), tokenId)` (method: transferFrom, receiver: nftManager)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['factory', 'nftManager', 'owners', 'pool', 'tokenIds']
- **External calls**: `nftManager.positions(tokenId)` (call on contract-typed state var 'nftManager' (type: PositionManagerV3)), `PoolAddress.computeAddress(factory,PoolAddress.PoolKey({token0: token0, token1: token1, fee: fee}))` (call on interface/contract type 'PoolAddress'), `PoolAddress.PoolKey({token0: token0, token1: token1, fee: fee})` (call on interface/contract type 'PoolAddress'), `UniV3(_pool).slot0()` (inline cast call UniV3(...).slot0()), `nftManager.transferFrom(msg.sender, address(this), tokenId)` (call on contract-typed state var 'nftManager' (type: PositionManagerV3))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### WstETH.wrap

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: wrap
- **Line Range**: L58
- **File**: `DAppSCAN-source/contracts/QuillAudits-Lido-WstETH/lido-dao-ea6fa222004b88e6a24b566a51e5b56b0079272d/contracts/0.6.12/WstETH.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`wrap`, lines=`L58`

#### 2. Function Source Code
```solidity
function wrap(uint256 _stETHAmount) external returns (uint256) {
        require(_stETHAmount > 0, "wstETH: can't wrap zero stETH");
        uint256 wstETHAmount = stETH.getSharesByPooledEth(_stETHAmount);
        _mint(msg.sender, wstETHAmount);
        // SWC-104-Unchecked Call Return Value: L58
        stETH.transferFrom(msg.sender, address(this), _stETHAmount);
        return wstETHAmount;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['stETH']
- **External calls**: `stETH.getSharesByPooledEth(_stETHAmount)` (method: getSharesByPooledEth, receiver: stETH), `stETH.transferFrom(msg.sender, address(this), _stETHAmount)` (method: transferFrom, receiver: stETH)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['stETH']
- **External calls**: `stETH.getSharesByPooledEth(_stETHAmount)` (call on contract-typed state var 'stETH' (type: IStETH)), `stETH.transferFrom(msg.sender, address(this), _stETHAmount)` (call on contract-typed state var 'stETH' (type: IStETH))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### WstETH.unwrap

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: unwrap
- **Line Range**: L75
- **File**: `DAppSCAN-source/contracts/QuillAudits-Lido-WstETH/lido-dao-ea6fa222004b88e6a24b566a51e5b56b0079272d/contracts/0.6.12/WstETH.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`unwrap`, lines=`L75`

#### 2. Function Source Code
```solidity
function unwrap(uint256 _wstETHAmount) external returns (uint256) {
        require(_wstETHAmount > 0, "wstETH: zero amount unwrap not allowed");
        uint256 stETHAmount = stETH.getPooledEthByShares(_wstETHAmount);
        _burn(msg.sender, _wstETHAmount);
        // SWC-104-Unchecked Call Return Value: L75
        stETH.transfer(msg.sender, stETHAmount);
        return stETHAmount;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['stETH']
- **External calls**: `stETH.getPooledEthByShares(_wstETHAmount)` (method: getPooledEthByShares, receiver: stETH), `stETH.transfer(msg.sender, stETHAmount)` (method: transfer, receiver: stETH)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['stETH']
- **External calls**: `stETH.getPooledEthByShares(_wstETHAmount)` (call on contract-typed state var 'stETH' (type: IStETH)), `stETH.transfer(msg.sender, stETHAmount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StrategyDAI3pool.balanceOfy3CRVinWant

**Pre-classification**: ❌ DUBIOUS
**Reason**: View/pure function with only read-only external calls — unchecked return has no state impact

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: balanceOfy3CRVinWant
- **Line Range**: L69
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Stablecoins 3pool/stablecoins-3pool-adeb776933c6cb3b8306239cc3357d4c6239a88d/contracts/StrategyDAI.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`balanceOfy3CRVinWant`, lines=`L69`

#### 2. Function Source Code
```solidity
function balanceOfy3CRVinWant() public view returns (uint256) {
        return balanceOfy3CRV()
                .mul(yvERC20(y3crv).getPricePerFullShare()).div(1e18)
                .mul(ICurveFi(_3pool).get_virtual_price()).div(1e18);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_3pool', 'y3crv']
- **External calls**: `yvERC20(y3crv).getPricePerFullShare()` (method: getPricePerFullShare, receiver: yvERC20), `ICurveFi(_3pool).get_virtual_price()` (method: get_virtual_price, receiver: ICurveFi)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['_3pool', 'y3crv']
- **External calls**: `yvERC20(y3crv).getPricePerFullShare()` (inline cast call yvERC20(...).getPricePerFullShare()), `ICurveFi(_3pool).get_virtual_price()` (inline cast call ICurveFi(...).get_virtual_price())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StrategyUSDC3pool.balanceOfy3CRVinWant

**Pre-classification**: ❌ DUBIOUS
**Reason**: View/pure function with only read-only external calls — unchecked return has no state impact

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: balanceOfy3CRVinWant
- **Line Range**: L69
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Stablecoins 3pool/stablecoins-3pool-adeb776933c6cb3b8306239cc3357d4c6239a88d/contracts/StrategyUSDC.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`balanceOfy3CRVinWant`, lines=`L69`

#### 2. Function Source Code
```solidity
function balanceOfy3CRVinWant() public view returns (uint256) {
        return balanceOfy3CRV()
                .mul(yvERC20(y3crv).getPricePerFullShare()).div(1e18)
                .mul(ICurveFi(_3pool).get_virtual_price()).div(1e30);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_3pool', 'y3crv']
- **External calls**: `yvERC20(y3crv).getPricePerFullShare()` (method: getPricePerFullShare, receiver: yvERC20), `ICurveFi(_3pool).get_virtual_price()` (method: get_virtual_price, receiver: ICurveFi)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['_3pool', 'y3crv']
- **External calls**: `yvERC20(y3crv).getPricePerFullShare()` (inline cast call yvERC20(...).getPricePerFullShare()), `ICurveFi(_3pool).get_virtual_price()` (inline cast call ICurveFi(...).get_virtual_price())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StrategyUSDT3pool.balanceOfy3CRVinWant

**Pre-classification**: ❌ DUBIOUS
**Reason**: View/pure function with only read-only external calls — unchecked return has no state impact

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: balanceOfy3CRVinWant
- **Line Range**: L69
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Stablecoins 3pool/stablecoins-3pool-adeb776933c6cb3b8306239cc3357d4c6239a88d/contracts/StrategyUSDT.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`balanceOfy3CRVinWant`, lines=`L69`

#### 2. Function Source Code
```solidity
function balanceOfy3CRVinWant() public view returns (uint256) {
        return balanceOfy3CRV()
                .mul(yvERC20(y3crv).getPricePerFullShare()).div(1e18)
                .mul(ICurveFi(_3pool).get_virtual_price()).div(1e30);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_3pool', 'y3crv']
- **External calls**: `yvERC20(y3crv).getPricePerFullShare()` (method: getPricePerFullShare, receiver: yvERC20), `ICurveFi(_3pool).get_virtual_price()` (method: get_virtual_price, receiver: ICurveFi)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['_3pool', 'y3crv']
- **External calls**: `yvERC20(y3crv).getPricePerFullShare()` (inline cast call yvERC20(...).getPricePerFullShare()), `ICurveFi(_3pool).get_virtual_price()` (inline cast call ICurveFi(...).get_virtual_price())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### BorrowerOperations._moveTokensAndETHfromAdjustment

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: _moveTokensAndETHfromAdjustment
- **Line Range**: L351
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-Liquity/dev-f0df3efa5a5f05b205752184cfce107c5bd6e06c/packages/contracts/contracts/BorrowerOperations.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`_moveTokensAndETHfromAdjustment`, lines=`L351`

#### 2. Function Source Code
```solidity
function _moveTokensAndETHfromAdjustment
    (
        address _borrower,
        uint _collChange,
        bool _isCollIncrease,
        uint _debtChange,
        bool _isDebtIncrease,
        uint _rawDebtChange
    )
        internal
    {
        if (_isDebtIncrease) {
            _withdrawLUSD(_borrower, _debtChange, _rawDebtChange);
        } else {
            _repayLUSD(_borrower, _debtChange);
        }

        if (_isCollIncrease) {
            _activePoolAddColl(_collChange);
        } else {
            // SWC-107-Reentrancy: L351
            activePool.sendETH(_borrower, _collChange);
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['activePool']
- **External calls**: `activePool.sendETH(_borrower, _collChange)` (method: sendETH, receiver: activePool)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['activePool']
- **External calls**: `activePool.sendETH(_borrower, _collChange)` (call on contract-typed state var 'activePool' (type: IPool))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### TroveManager.redeemCollateral

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: redeemCollateral
- **Line Range**: L920
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-Liquity/dev-f0df3efa5a5f05b205752184cfce107c5bd6e06c/packages/contracts/contracts/TroveManager.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`redeemCollateral`, lines=`L920`

#### 2. Function Source Code
(76 lines, showing first 30 + last 15)
```solidity
function redeemCollateral(
        uint _LUSDamount,
        address _firstRedemptionHint,
        address _partialRedemptionHint,
        uint _partialRedemptionHintICR,
        uint _maxIterations
    )
        external
        override
    {
        uint activeDebt = activePool.getLUSDDebt();
        uint defaultedDebt = defaultPool.getLUSDDebt();

        RedemptionTotals memory T;

        _requireAmountGreaterThanZero(_LUSDamount);
        _requireLUSDBalanceCoversRedemption(msg.sender, _LUSDamount);

        // Confirm redeemer's balance is less than total systemic debt
        assert(lusdToken.balanceOf(msg.sender) <= (activeDebt.add(defaultedDebt)));

        uint remainingLUSD = _LUSDamount;
        uint price = priceFeed.getPrice();
        address currentBorrower;

        if (_isValidFirstRedemptionHint(_firstRedemptionHint, price)) {
            currentBorrower = _firstRedemptionHint;
        } else {
            currentBorrower = sortedTroves.getLast();
            // Find the first trove with ICR >= MCR
    // ... truncated ...
        // Decay the baseRate due to time passed, and then increase it according to the size of this redemption
        _updateBaseRateFromRedemption(T.totalETHDrawn, price);

        // Calculate the ETH fee and send it to the LQTY staking contract
        T.ETHFee = _getRedemptionFee(T.totalETHDrawn);
        activePool.sendETH(lqtyStakingAddress, T.ETHFee);
        lqtyStaking.increaseF_ETH(T.ETHFee);

        T.ETHToSendToRedeemer = T.totalETHDrawn.sub(T.ETHFee);

        // Burn the total LUSD that is cancelled with debt, and send the redeemed ETH to msg.sender
        _activePoolRedeemCollateral(msg.sender, T.totalLUSDToRedeem, T.ETHToSendToRedeemer);

        emit Redemption(_LUSDamount, T.totalLUSDToRedeem, T.totalETHDrawn, T.ETHFee);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['MCR', 'activePool', 'defaultPool', 'lqtyStaking', 'lqtyStakingAddress', 'lusdToken', 'priceFeed', 'sortedTroves']
- **External calls**: `activePool.getLUSDDebt()` (method: getLUSDDebt, receiver: activePool), `defaultPool.getLUSDDebt()` (method: getLUSDDebt, receiver: defaultPool), `lusdToken.balanceOf(msg.sender)` (method: balanceOf, receiver: lusdToken), `priceFeed.getPrice()` (method: getPrice, receiver: priceFeed), `sortedTroves.getLast()` (method: getLast, receiver: sortedTroves), `sortedTroves.getPrev(currentBorrower)` (method: getPrev, receiver: sortedTroves), `sortedTroves.getPrev(currentBorrower)` (method: getPrev, receiver: sortedTroves), `T.totalLUSDToRedeem.add(V.LUSDLot)` (method: add, receiver: T), `T.totalETHDrawn.add(V.ETHLot)` (method: add, receiver: T), `activePool.sendETH(lqtyStakingAddress, T.ETHFee)` (method: sendETH, receiver: activePool), `lqtyStaking.increaseF_ETH(T.ETHFee)` (method: increaseF_ETH, receiver: lqtyStaking), `T.totalETHDrawn.sub(T.ETHFee)` (method: sub, receiver: T)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['MCR', 'activePool', 'defaultPool', 'lqtyStaking', 'lqtyStakingAddress', 'lusdToken', 'priceFeed', 'sortedTroves']
- **External calls**: `activePool.getLUSDDebt()` (call on contract-typed state var 'activePool' (type: IPool)), `defaultPool.getLUSDDebt()` (call on contract-typed state var 'defaultPool' (type: IPool)), `lusdToken.balanceOf(msg.sender)` (call on contract-typed state var 'lusdToken' (type: ILUSDToken)), `priceFeed.getPrice()` (call on contract-typed state var 'priceFeed' (type: IPriceFeed)), `sortedTroves.getLast()` (call on contract-typed state var 'sortedTroves' (type: ISortedTroves)), `sortedTroves.getPrev(currentBorrower)` (call on contract-typed state var 'sortedTroves' (type: ISortedTroves)), `sortedTroves.getPrev(currentBorrower)` (call on contract-typed state var 'sortedTroves' (type: ISortedTroves)), `T.totalLUSDToRedeem.add(V.LUSDLot)` (call on contract-typed local var 'T' (type: RedemptionTotals)), `T.totalETHDrawn.add(V.ETHLot)` (call on contract-typed local var 'T' (type: RedemptionTotals)), `activePool.sendETH(lqtyStakingAddress, T.ETHFee)` (call on contract-typed state var 'activePool' (type: IPool)), `lqtyStaking.increaseF_ETH(T.ETHFee)` (call on contract-typed state var 'lqtyStaking' (type: ILQTYStaking)), `T.totalETHDrawn.sub(T.ETHFee)` (call on contract-typed local var 'T' (type: RedemptionTotals))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### LendingPool.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L92-119
- **File**: `DAppSCAN-source/contracts/consensys-Aave_Protocol_V2/aave-protocol-v2-f756f44a8d6a328cd545335e46e7128939db88c4/contracts/lendingpool/LendingPool.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L92-119`

#### 2. Function Source Code
```solidity
function deposit(
    address asset,
    uint256 amount,
    address onBehalfOf,
    uint16 referralCode
  ) external override {
    _whenNotPaused();
    ReserveLogic.ReserveData storage reserve = _reserves[asset];

    ValidationLogic.validateDeposit(reserve, amount);

    address aToken = reserve.aTokenAddress;

    reserve.updateState();
    reserve.updateInterestRates(asset, aToken, amount, 0);

    bool isFirstDeposit = IAToken(aToken).balanceOf(onBehalfOf) == 0;
    if (isFirstDeposit) {
      _usersConfig[onBehalfOf].setUsingAsCollateral(reserve.id, true);
    }

    IAToken(aToken).mint(onBehalfOf, amount, reserve.liquidityIndex);

    //transfer to the aToken contract
    IERC20(asset).safeTransferFrom(msg.sender, aToken, amount);

    emit Deposit(asset, msg.sender, onBehalfOf, amount, referralCode);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_reserves', '_usersConfig']
- **External calls**: `ValidationLogic.validateDeposit(reserve, amount)` (method: validateDeposit, receiver: ValidationLogic), `reserve.updateState()` (method: updateState, receiver: reserve), `reserve.updateInterestRates(asset, aToken, amount, 0)` (method: updateInterestRates, receiver: reserve), `IAToken(aToken).balanceOf(onBehalfOf)` (method: balanceOf, receiver: IAToken), `_usersConfig[onBehalfOf].setUsingAsCollateral(reserve.id, true)` (method: setUsingAsCollateral, receiver: _usersConfig), `IAToken(aToken).mint(onBehalfOf, amount, reserve.liquidityIndex)` (method: mint, receiver: IAToken), `IERC20(asset).safeTransferFrom(msg.sender, aToken, amount)` (method: safeTransferFrom, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['_reserves', '_usersConfig']
- **External calls**: `ValidationLogic.validateDeposit(reserve, amount)` (call on interface/contract type 'ValidationLogic'), `reserve.updateState()` (call on contract-typed local var 'reserve' (type: ReserveLogic.ReserveData)), `reserve.updateInterestRates(asset, aToken, amount, 0)` (call on contract-typed local var 'reserve' (type: ReserveLogic.ReserveData)), `IAToken(aToken).balanceOf(onBehalfOf)` (inline cast call IAToken(...).balanceOf()), `_usersConfig[onBehalfOf].setUsingAsCollateral(reserve.id, true)` (call on contract-typed state var '_usersConfig' (type: mapping(address => UserConfiguration.Map))), `IAToken(aToken).mint(onBehalfOf, amount, reserve.liquidityIndex)` (inline cast call IAToken(...).mint()), `IERC20(asset).safeTransferFrom(msg.sender, aToken, amount)` (SafeERC20 .safeTransferFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### LendingPool.flashLoan

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: flashLoan
- **Line Range**: L579
- **File**: `DAppSCAN-source/contracts/consensys-Aave_Protocol_V2/aave-protocol-v2-f756f44a8d6a328cd545335e46e7128939db88c4/contracts/lendingpool/LendingPool.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`flashLoan`, lines=`L579`

#### 2. Function Source Code
```solidity
function flashLoan(
    address receiverAddress,
    address asset,
    uint256 amount,
    uint256 mode,
    bytes calldata params,
    uint16 referralCode
  ) external override {
    _whenNotPaused();
    ReserveLogic.ReserveData storage reserve = _reserves[asset];
    FlashLoanLocalVars memory vars;

    vars.aTokenAddress = reserve.aTokenAddress;

    vars.premium = amount.mul(FLASHLOAN_PREMIUM_TOTAL).div(10000);

    ValidationLogic.validateFlashloan(mode, vars.premium);

    ReserveLogic.InterestRateMode debtMode = ReserveLogic.InterestRateMode(mode);

    vars.receiver = IFlashLoanReceiver(receiverAddress);

    //transfer funds to the receiver
    IAToken(vars.aTokenAddress).transferUnderlyingTo(receiverAddress, amount);

    //execute action of the receiver
    vars.receiver.executeOperation(asset, amount, vars.premium, params);

    vars.amountPlusPremium = amount.add(vars.premium);

    if (debtMode == ReserveLogic.InterestRateMode.NONE) {
      // SWC-104-Unchecked Call Return Value: L579
      IERC20(asset).transferFrom(receiverAddress, vars.aTokenAddress, vars.amountPlusPremium);

      reserve.updateState();
      reserve.cumulateToLiquidityIndex(IERC20(vars.aTokenAddress).totalSupply(), vars.premium);
      reserve.updateInterestRates(asset, vars.aTokenAddress, vars.premium, 0);

      emit FlashLoan(receiverAddress, asset, amount, vars.premium, referralCode);
    } else {
      // If the transfer didn't succeed, the receiver either didn't return the funds, or didn't approve the transfer.
      _executeBorrow(
        ExecuteBorrowParams(
          asset,
          msg.sender,
          msg.sender,
          vars.amountPlusPremium,
          mode,
          vars.aTokenAddress,
          referralCode,
          false
        )
      );
    }
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['FLASHLOAN_PREMIUM_TOTAL', '_reserves']
- **External calls**: `ValidationLogic.validateFlashloan(mode, vars.premium)` (method: validateFlashloan, receiver: ValidationLogic), `ReserveLogic.InterestRateMode(mode)` (method: InterestRateMode, receiver: ReserveLogic), `IAToken(vars.aTokenAddress).transferUnderlyingTo(receiverAddress, amount)` (method: transferUnderlyingTo, receiver: IAToken), `vars.receiver.executeOperation(asset, amount, vars.premium, params)` (method: executeOperation, receiver: vars), `IERC20(asset).transferFrom(receiverAddress, vars.aTokenAddress, vars.amountPlusPremium)` (method: transferFrom, receiver: IERC20), `reserve.updateState()` (method: updateState, receiver: reserve), `reserve.cumulateToLiquidityIndex(IERC20(vars.aTokenAddress).totalSupply(), vars.premium)` (method: cumulateToLiquidityIndex, receiver: reserve), `IERC20(vars.aTokenAddress).totalSupply()` (method: totalSupply, receiver: IERC20), `reserve.updateInterestRates(asset, vars.aTokenAddress, vars.premium, 0)` (method: updateInterestRates, receiver: reserve)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['FLASHLOAN_PREMIUM_TOTAL', '_reserves']
- **External calls**: `ValidationLogic.validateFlashloan(mode, vars.premium)` (call on interface/contract type 'ValidationLogic'), `ReserveLogic.InterestRateMode(mode)` (call on interface/contract type 'ReserveLogic'), `IAToken(vars.aTokenAddress).transferUnderlyingTo(receiverAddress, amount)` (inline cast call IAToken(...).transferUnderlyingTo()), `vars.receiver.executeOperation(asset, amount, vars.premium, params)` (call on contract-typed local var 'vars' (type: FlashLoanLocalVars)), `IERC20(asset).transferFrom(receiverAddress, vars.aTokenAddress, vars.amountPlusPremium)` (inline cast call IERC20(...).transferFrom()), `reserve.updateState()` (call on contract-typed local var 'reserve' (type: ReserveLogic.ReserveData)), `reserve.cumulateToLiquidityIndex(IERC20(vars.aTokenAddress).totalSupply(), vars.premium)` (call on contract-typed local var 'reserve' (type: ReserveLogic.ReserveData)), `IERC20(vars.aTokenAddress).totalSupply()` (inline cast call IERC20(...).totalSupply()), `reserve.updateInterestRates(asset, vars.aTokenAddress, vars.premium, 0)` (call on contract-typed local var 'reserve' (type: ReserveLogic.ReserveData))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Moloch.sponsorProposal

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: sponsorProposal
- **Line Range**: L266-305
- **File**: `DAppSCAN-source/contracts/consensys-The_LAO/moloch-4bc443f4dad60279b47978fc6987bb978d3dfc58/contracts/Moloch.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`sponsorProposal`, lines=`L266-305`

#### 2. Function Source Code
```solidity
function sponsorProposal(uint256 proposalId) public nonReentrant onlyDelegate {
        // collect proposal deposit from sponsor and store it in the Moloch until the proposal is processed
        require(depositToken.transferFrom(msg.sender, address(this), proposalDeposit), "proposal deposit token transfer failed");

        Proposal storage proposal = proposals[proposalId];

        require(proposal.proposer != address(0), 'proposal must have been proposed');
        require(!proposal.flags[0], "proposal has already been sponsored");
        require(!proposal.flags[3], "proposal has been cancelled");
        require(members[proposal.applicant].jailed == 0, "proposal applicant must not be jailed");

        // whitelist proposal
        if (proposal.flags[4]) {
            require(!tokenWhitelist[address(proposal.tributeToken)], "cannot already have whitelisted the token");
            require(!proposedToWhitelist[address(proposal.tributeToken)], 'already proposed to whitelist');
            proposedToWhitelist[address(proposal.tributeToken)] = true;

        // guild kick proposal
        } else if (proposal.flags[5]) {
            require(!proposedToKick[proposal.applicant], 'already proposed to kick');
            proposedToKick[proposal.applicant] = true;
        }

        // compute startingPeriod for proposal
        uint256 startingPeriod = max(
            getCurrentPeriod(),
            proposalQueue.length == 0 ? 0 : proposals[proposalQueue[proposalQueue.length.sub(1)]].startingPeriod
        ).add(1);

        proposal.startingPeriod = startingPeriod;

        address memberAddress = memberAddressByDelegateKey[msg.sender];
        proposal.sponsor = memberAddress;

        proposal.flags[0] = true;

        // append proposal to the queue
        proposalQueue.push(proposalId);
        emit SponsorProposal(msg.sender, memberAddress, proposalId, proposalQueue.length.sub(1), startingPeriod);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['depositToken', 'memberAddressByDelegateKey', 'members', 'proposalDeposit', 'proposalQueue', 'proposals', 'proposedToKick', 'proposedToWhitelist', 'tokenWhitelist']
- **External calls**: `depositToken.transferFrom(msg.sender, address(this), proposalDeposit)` (method: transferFrom, receiver: depositToken)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['depositToken', 'memberAddressByDelegateKey', 'members', 'proposalDeposit', 'proposalQueue', 'proposals', 'proposedToKick', 'proposedToWhitelist', 'tokenWhitelist']
- **External calls**: `depositToken.transferFrom(msg.sender, address(this), proposalDeposit)` (call on contract-typed state var 'depositToken' (type: IERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

---
## VAL Cross-Contract (14 items)

### Graph._stake

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _stake
- **Line Range**: L82
- **File**: `DAppSCAN-source/contracts/Hacken-Tenderize/tender-core-1fd606141625171fe792045ae9233890262d2d62/contracts/tenderizer/integrations/graph/Graph.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_stake`, lines=`L82`

#### 2. Function Source Code
```solidity
function _stake(address _node, uint256 _amount) internal override {
        // check that there are enough tokens to stake
        uint256 amount = _amount;
        uint256 pendingWithdrawals = withdrawPool.getAmount();

        if (amount <= pendingWithdrawals) {
            return;
        }

        amount -= pendingWithdrawals;

        // if no _node is specified, return
        if (_node == address(0)) {
            return;
        }

        // approve amount to Graph protocol
        // SWC-104-Unchecked Call Return Value: L82
        steak.approve(address(graph), amount);

        // stake tokens
        // SWC-104-Unchecked Call Return Value: L86
        graph.delegate(_node, amount);

        emit Stake(_node, amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['graph', 'steak', 'withdrawPool']
- **External calls**: `withdrawPool.getAmount()` (method: getAmount, receiver: withdrawPool), `steak.approve(address(graph), amount)` (method: approve, receiver: steak), `graph.delegate(_node, amount)` (method: delegate, receiver: graph)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['graph', 'steak', 'withdrawPool']
- **External calls**: `withdrawPool.getAmount()` (call on contract-typed state var 'withdrawPool' (type: WithdrawalPools.Pool)), `steak.approve(address(graph), amount)` (call on contract-typed state var 'steak' (type: IERC20)), `graph.delegate(_node, amount)` (call on contract-typed state var 'graph' (type: IGraph))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Livepeer._withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _withdraw
- **Line Range**: L122
- **File**: `DAppSCAN-source/contracts/Hacken-Tenderize/tender-core-1fd606141625171fe792045ae9233890262d2d62/contracts/tenderizer/integrations/livepeer/Livepeer.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_withdraw`, lines=`L122`

#### 2. Function Source Code
```solidity
function _withdraw(address _account, uint256 _withdrawalID) internal override {
        uint256 amount = withdrawLocks.withdraw(_account, _withdrawalID);
 
        // Withdraw stake, transfers steak tokens to address(this)
        livepeer.withdrawStake(_withdrawalID);

        // Transfer amount from unbondingLock to _account
        // SWC-104-Unchecked Call Return Value: L122
        steak.transfer(_account, amount);

        emit Withdraw(_account, amount, _withdrawalID);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['livepeer', 'steak', 'withdrawLocks']
- **External calls**: `withdrawLocks.withdraw(_account, _withdrawalID)` (method: withdraw, receiver: withdrawLocks), `livepeer.withdrawStake(_withdrawalID)` (method: withdrawStake, receiver: livepeer), `steak.transfer(_account, amount)` (method: transfer, receiver: steak)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['livepeer', 'steak', 'withdrawLocks']
- **External calls**: `withdrawLocks.withdraw(_account, _withdrawalID)` (call on contract-typed state var 'withdrawLocks' (type: WithdrawalLocks.Locks)), `livepeer.withdrawStake(_withdrawalID)` (call on contract-typed state var 'livepeer' (type: ILivepeer)), `steak.transfer(_account, amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Livepeer._claimSecondaryRewards

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _claimSecondaryRewards
- **Line Range**: L162 - L164
- **File**: `DAppSCAN-source/contracts/Hacken-Tenderize/tender-core-1fd606141625171fe792045ae9233890262d2d62/contracts/tenderizer/integrations/livepeer/Livepeer.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_claimSecondaryRewards`, lines=`L162 - L164`

#### 2. Function Source Code
```solidity
function _claimSecondaryRewards() internal {
        uint256 ethFees = livepeer.pendingFees(address(this), MAX_ROUND);
        // First claim any fees that are not underlying tokens
        // withdraw fees
        if (ethFees >= ethFees_threshold) {
            livepeer.withdrawFees();

            // Wrap ETH
            uint256 bal = address(this).balance;
            WETH.deposit{ value: bal }();
            WETH.approve(address(uniswapRouter), bal);

            // swap ETH fees for LPT
            if (address(uniswapRouter) != address(0)) {
                ISwapRouter.ExactInputSingleParams memory params = ISwapRouter.ExactInputSingleParams({
                    tokenIn: address(WETH),
                    tokenOut: address(steak),
                    fee: UNISWAP_POOL_FEE,
                    recipient: address(this),
                    deadline: block.timestamp,
                    amountIn: bal,
                    amountOutMinimum: 0, // TODO: Set5% max slippage
                    sqrtPriceLimitX96: 0
                });
                // SWC-104-Unchecked Call Return Value: L162 - L164
                try uniswapRouter.exactInputSingle(params) returns (
                    uint256 /*_swappedLPT*/
                ) {} catch {}
            }
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['MAX_ROUND', 'UNISWAP_POOL_FEE', 'WETH', 'ethFees_threshold', 'livepeer', 'pendingFees', 'steak', 'uniswapRouter']
- **External calls**: `livepeer.pendingFees(address(this), MAX_ROUND)` (method: pendingFees, receiver: livepeer), `livepeer.withdrawFees()` (method: withdrawFees, receiver: livepeer), `WETH.deposit{ value: bal }()` (method: deposit, receiver: WETH), `WETH.approve(address(uniswapRouter), bal)` (method: approve, receiver: WETH), `ISwapRouter.ExactInputSingleParams({
                    tokenIn: address(WETH),
                    tokenOut: address(s` (method: ExactInputSingleParams, receiver: ISwapRouter), `uniswapRouter.exactInputSingle(params)` (method: exactInputSingle, receiver: uniswapRouter)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['MAX_ROUND', 'UNISWAP_POOL_FEE', 'WETH', 'ethFees_threshold', 'livepeer', 'pendingFees', 'steak', 'uniswapRouter']
- **External calls**: `livepeer.pendingFees(address(this), MAX_ROUND)` (call on contract-typed state var 'livepeer' (type: ILivepeer)), `livepeer.withdrawFees()` (call on contract-typed state var 'livepeer' (type: ILivepeer)), `WETH.deposit{ value: bal }()` (call on contract-typed state var 'WETH' (type: IWETH)), `WETH.approve(address(uniswapRouter), bal)` (call on contract-typed state var 'WETH' (type: IWETH)), `ISwapRouter.ExactInputSingleParams({
                    tokenIn: address(WETH),
                    tokenOut: address(s` (call on interface/contract type 'ISwapRouter'), `uniswapRouter.exactInputSingle(params)` (call on contract-typed state var 'uniswapRouter' (type: ISwapRouterWithWETH))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Matic._stake

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _stake
- **Line Range**: L94
- **File**: `DAppSCAN-source/contracts/Hacken-Tenderize/tender-core-1fd606141625171fe792045ae9233890262d2d62/contracts/tenderizer/integrations/matic/Matic.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_stake`, lines=`L94`

#### 2. Function Source Code
```solidity
function _stake(address _node, uint256 _amount) internal override {
        // if no amount is specified, stake all available tokens
        uint256 amount = _amount;

        if (amount == 0) {
            return;
            // TODO: revert ?
        }

        // if no _node is specified, return
        if (_node == address(0)) {
            return;
        }

        // use default validator share contract if _node isn't specified
        IMatic matic_ = matic;
        // SWC-135-Code With No Effects: L88 - L90
        if (_node != address(0)) {
            matic_ = IMatic(_node);
        }

        // approve tokens
        // SWC-104-Unchecked Call Return Value: L94
        steak.approve(maticStakeManager, amount);

        // stake tokens
        uint256 min = ((amount * _getExchangeRatePrecision(matic_)) / _getExchangeRate(matic_)) - 1;
        matic_.buyVoucher(amount, min);

        emit Stake(address(matic_), amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['matic', 'maticStakeManager', 'steak']
- **External calls**: `steak.approve(maticStakeManager, amount)` (method: approve, receiver: steak), `matic_.buyVoucher(amount, min)` (method: buyVoucher, receiver: matic_)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['matic', 'maticStakeManager', 'steak']
- **External calls**: `steak.approve(maticStakeManager, amount)` (call on contract-typed state var 'steak' (type: IERC20)), `matic_.buyVoucher(amount, min)` (call on contract-typed local var 'matic_' (type: IMatic))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Matic._withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _withdraw
- **Line Range**: L148
- **File**: `DAppSCAN-source/contracts/Hacken-Tenderize/tender-core-1fd606141625171fe792045ae9233890262d2d62/contracts/tenderizer/integrations/matic/Matic.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_withdraw`, lines=`L148`

#### 2. Function Source Code
```solidity
function _withdraw(address _account, uint256 _withdrawalID) internal override {
        withdrawLocks.withdraw(_account, _withdrawalID);

        // Check for any slashes during undelegation
        uint256 balBefore = steak.balanceOf(address(this));
        matic.unstakeClaimTokens_new(_withdrawalID);
        uint256 balAfter = steak.balanceOf(address(this));
        uint256 amount = balAfter >= balBefore ? balAfter - balBefore : 0;
        require(amount > 0, "ZERO_AMOUNT");

        // Transfer amount from unbondingLock to _account
        // SWC-104-Unchecked Call Return Value: L148
        steak.transfer(_account, amount);

        emit Withdraw(_account, amount, _withdrawalID);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['matic', 'steak', 'withdrawLocks']
- **External calls**: `withdrawLocks.withdraw(_account, _withdrawalID)` (method: withdraw, receiver: withdrawLocks), `steak.balanceOf(address(this))` (method: balanceOf, receiver: steak), `matic.unstakeClaimTokens_new(_withdrawalID)` (method: unstakeClaimTokens_new, receiver: matic), `steak.balanceOf(address(this))` (method: balanceOf, receiver: steak), `steak.transfer(_account, amount)` (method: transfer, receiver: steak)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['matic', 'steak', 'withdrawLocks']
- **External calls**: `withdrawLocks.withdraw(_account, _withdrawalID)` (call on contract-typed state var 'withdrawLocks' (type: WithdrawalLocks.Locks)), `steak.balanceOf(address(this))` (call on contract-typed state var 'steak' (type: IERC20)), `matic.unstakeClaimTokens_new(_withdrawalID)` (call on contract-typed state var 'matic' (type: IMatic)), `steak.balanceOf(address(this))` (call on contract-typed state var 'steak' (type: IERC20)), `steak.transfer(_account, amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### LimitOrderProtocol.fillOrderTo

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: fillOrderTo
- **Line Range**: L28 - L346
- **File**: `DAppSCAN-source/contracts/QuillAudits-1inch-Limit Order Protocol/limit-order-protocol-a14bde6a260458de5083cee117d734221e1cbc05/contracts/LimitOrderProtocol.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`fillOrderTo`, lines=`L28 - L346`

#### 2. Function Source Code
(67 lines, showing first 30 + last 15)
```solidity
function fillOrderTo(
        Order memory order,
        bytes calldata signature,
        uint256 makingAmount,
        uint256 takingAmount,
        uint256 thresholdAmount,
        address target
    ) public returns(uint256, uint256) {
        bytes32 orderHash = _hash(order);

        {  // Stack too deep
            uint256 remainingMakerAmount;
            { // Stack too deep
                bool orderExists;
                (orderExists, remainingMakerAmount) = _remaining[orderHash].trySub(1);
                if (!orderExists) {
                    // First fill: validate order and permit maker asset
                    _validate(order.makerAssetData, order.takerAssetData, signature, orderHash);
                    remainingMakerAmount = order.makerAssetData.decodeUint256(_AMOUNT_INDEX);
                    if (order.permit.length > 0) {
                        _permit(order.permit);
                        require(_remaining[orderHash] == 0, "LOP: reentrancy detected");
                    }
                }
            }

            // Check if order is valid
            if (order.predicate.length > 0) {
                require(checkPredicate(order), "LOP: predicate returned false");
            }
    // ... truncated ...
        // Taker => Maker
        _callTakerAssetTransferFrom(order.takerAsset, order.takerAssetData, takingAmount);

        // SWC-128-DoS With Block Gas Limit: L339
        // Maker can handle funds interactively
        if (order.interaction.length > 0) {
            InteractiveMaker(order.makerAssetData.decodeAddress(_FROM_INDEX))
                .notifyFillOrder(order.makerAsset, order.takerAsset, makingAmount, takingAmount, order.interaction);
        }

        // Maker => Taker
        _callMakerAssetTransferFrom(order.makerAsset, order.makerAssetData, target, makingAmount);

        return (makingAmount, takingAmount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_AMOUNT_INDEX', '_FROM_INDEX', '_remaining']
- **External calls**: `order.makerAssetData.decodeUint256(_AMOUNT_INDEX)` (method: decodeUint256, receiver: order), `InteractiveMaker(order.makerAssetData.decodeAddress(_FROM_INDEX))
                .notifyFillOrder(order.makerAsset, ord` (method: notifyFillOrder, receiver: InteractiveMaker), `order.makerAssetData.decodeAddress(_FROM_INDEX)` (method: decodeAddress, receiver: order)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['_AMOUNT_INDEX', '_FROM_INDEX', '_remaining']
- **External calls**: `order.makerAssetData.decodeUint256(_AMOUNT_INDEX)` (call on contract-typed local var 'order' (type: Order)), `InteractiveMaker(order.makerAssetData.decodeAddress(_FROM_INDEX))
                .notifyFillOrder(order.makerAsset, ord` (inline cast call InteractiveMaker(...).notifyFillOrder()), `order.makerAssetData.decodeAddress(_FROM_INDEX)` (call on contract-typed local var 'order' (type: Order))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### BaseParaSwapAdapter._pullAToken

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _pullAToken
- **Line Range**: L104
- **File**: `DAppSCAN-source/contracts/QuillAudits-AAVE-ParaSwap Adapter/aave-protocol-v2-14e2ab47d95f42ec5ee486f367067e78a7588878/contracts/adapters/BaseParaSwapAdapter.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`_pullAToken`, lines=`L79`

#### 2. Function Source Code
```solidity
function _pullAToken(
    address reserve,
    address reserveAToken,
    address user,
    uint256 amount,
    PermitSignature memory permitSignature
  ) internal {
    if (_usePermit(permitSignature)) {
      IERC20WithPermit(reserveAToken).permit(
        user,
        address(this),
        permitSignature.amount,
        permitSignature.deadline,
        permitSignature.v,
        permitSignature.r,
        permitSignature.s
      );
    }

    // transfer from user to adapter
    IERC20(reserveAToken).safeTransferFrom(user, address(this), amount);

    // SWC-104-Unchecked Call Return Value: L104
    // withdraw reserve
    LENDING_POOL.withdraw(reserve, amount, address(this));
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['LENDING_POOL']
- **External calls**: `IERC20WithPermit(reserveAToken).permit(
        user,
        address(this),
        permitSignature.amount,
        per` (method: permit, receiver: IERC20WithPermit), `IERC20(reserveAToken).safeTransferFrom(user, address(this), amount)` (method: safeTransferFrom, receiver: IERC20), `LENDING_POOL.withdraw(reserve, amount, address(this))` (method: withdraw, receiver: LENDING_POOL)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['LENDING_POOL']
- **External calls**: `IERC20WithPermit(reserveAToken).permit(
        user,
        address(this),
        permitSignature.amount,
        per` (inline cast call IERC20WithPermit(...).permit()), `IERC20(reserveAToken).safeTransferFrom(user, address(this), amount)` (SafeERC20 .safeTransferFrom()), `LENDING_POOL.withdraw(reserve, amount, address(this))` (call on contract-typed state var 'LENDING_POOL' (type: ILendingPool))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### LendingPair.short

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: short
- **Line Range**: L429
- **File**: `DAppSCAN-source/contracts/QuillAudits-SushiSwap-BentoBox/bentobox-c2e150b16b8764ebfe2e1e6e267ae14e10738065/contracts/LendingPair.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`short`, lines=`L429`

#### 2. Function Source Code
```solidity
function short(ISwapper swapper, uint256 assetAmount, uint256 minCollateralAmount) public {
        require(masterContract.swappers(swapper), "LendingPair: Invalid swapper");
        accrue();
        _addBorrowAmount(msg.sender, assetAmount);
        bentoBox.transferFrom(asset, address(this), address(swapper), assetAmount);

        // Swaps the borrowable asset for collateral
        // SWC-104-Unchecked Call Return Value: L429
        swapper.swap(asset, collateral, assetAmount, minCollateralAmount);
        uint256 returnedCollateralAmount = bentoBox.skim(collateral); // TODO: Reentrancy issue? Should we take a before and after balance?
        require(returnedCollateralAmount >= minCollateralAmount, "LendingPair: not enough");
        _addCollateralAmount(msg.sender, returnedCollateralAmount);

        require(isSolvent(msg.sender, false), "LendingPair: user insolvent");
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['asset', 'bentoBox', 'collateral', 'masterContract', 'swappers']
- **External calls**: `masterContract.swappers(swapper)` (method: swappers, receiver: masterContract), `bentoBox.transferFrom(asset, address(this), address(swapper), assetAmount)` (method: transferFrom, receiver: bentoBox), `swapper.swap(asset, collateral, assetAmount, minCollateralAmount)` (method: swap, receiver: swapper), `bentoBox.skim(collateral)` (method: skim, receiver: bentoBox)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['asset', 'bentoBox', 'collateral', 'masterContract', 'swappers']
- **External calls**: `masterContract.swappers(swapper)` (call on contract-typed state var 'masterContract' (type: LendingPair)), `bentoBox.transferFrom(asset, address(this), address(swapper), assetAmount)` (call on contract-typed state var 'bentoBox' (type: IBentoBox)), `swapper.swap(asset, collateral, assetAmount, minCollateralAmount)` (call on contract-typed local var 'swapper' (type: ISwapper)), `bentoBox.skim(collateral)` (call on contract-typed state var 'bentoBox' (type: IBentoBox))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### LendingPair.liquidate

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: liquidate
- **Line Range**: L499
- **File**: `DAppSCAN-source/contracts/QuillAudits-SushiSwap-BentoBox/bentobox-c2e150b16b8764ebfe2e1e6e267ae14e10738065/contracts/LendingPair.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`liquidate`, lines=`L499`

#### 2. Function Source Code
(74 lines, showing first 30 + last 15)
```solidity
function liquidate(address[] calldata users, uint256[] calldata borrowFractions, address to, ISwapper swapper, bool open) public {
        accrue();
        updateExchangeRate();

        uint256 allCollateralAmount;
        uint256 allBorrowAmount;
        uint256 allBorrowFraction;
        TokenTotals memory _totalBorrow = totalBorrow;
        for (uint256 i = 0; i < users.length; i++) {
            address user = users[i];
            if (!isSolvent(user, open)) {
                // Gets the user's amount of the total borrowed amount
                uint256 borrowFraction = borrowFractions[i];
                // Calculates the user's amount borrowed
                uint256 borrowAmount = borrowFraction.mul(_totalBorrow.amount) / _totalBorrow.fraction;
                // Calculates the amount of collateral that's going to be swapped for the asset
                uint256 collateralAmount = borrowAmount.mul(LIQUIDATION_MULTIPLIER).mul(exchangeRate) / 1e23;

                // Removes the amount of collateral from the user's balance
                userCollateralAmount[user] = userCollateralAmount[user].sub(collateralAmount);
                // Removes the amount of user's borrowed tokens from the user
                userBorrowFraction[user] = userBorrowFraction[user].sub(borrowFraction);
                emit LogRemoveCollateral(user, collateralAmount);
                emit LogRemoveBorrow(user, borrowAmount, borrowFraction);

                // Keep totals
                allCollateralAmount = allCollateralAmount.add(collateralAmount);
                allBorrowAmount = allBorrowAmount.add(borrowAmount);
                allBorrowFraction = allBorrowFraction.add(borrowFraction);
            }
    // ... truncated ...
            bentoBox.transferFrom(asset, msg.sender, address(this), allBorrowAmount);
            bentoBox.transfer(collateral, to, allCollateralAmount);
        } else {
            // Swap using a swapper freely chosen by the caller
            // Open (flash) liquidation: get proceeds first and provide the borrow after
            bentoBox.transferFrom(collateral, address(this), address(swapper), allCollateralAmount);
            // SWC-104-Unchecked Call Return Value: L522
            swapper.swap(collateral, asset, allCollateralAmount, allBorrowAmount);
            uint256 returnedAssetAmount = bentoBox.skim(asset); // TODO: Reentrancy issue? Should we take a before and after balance?
            uint256 extraAssetAmount = returnedAssetAmount.sub(allBorrowAmount);

            totalAsset.amount = totalAsset.amount.add(extraAssetAmount.to128());
            emit LogAddAsset(address(0), extraAssetAmount, 0);
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['LIQUIDATION_MULTIPLIER', 'PROTOCOL_FEE', 'accrueInfo', 'asset', 'bentoBox', 'collateral', 'exchangeRate', 'masterContract', 'swappers', 'totalAsset', 'totalBorrow', 'totalCollateralAmount', 'userBorrowFraction', 'userCollateralAmount']
- **External calls**: `_totalBorrow.amount.sub(allBorrowAmount.to128())` (method: sub, receiver: _totalBorrow), `_totalBorrow.fraction.sub(allBorrowFraction.to128())` (method: sub, receiver: _totalBorrow), `masterContract.swappers(swapper)` (method: swappers, receiver: masterContract), `bentoBox.transferFrom(collateral, address(this), address(swapper), allCollateralAmount)` (method: transferFrom, receiver: bentoBox), `swapper.swap(collateral, asset, allCollateralAmount, allBorrowAmount)` (method: swap, receiver: swapper), `bentoBox.skim(asset)` (method: skim, receiver: bentoBox), `accrueInfo.feesPendingAmount.add(feeAmount.to128())` (method: add, receiver: accrueInfo), `totalAsset.amount.add(extraAssetAmount.sub(feeAmount).to128())` (method: add, receiver: totalAsset), `bentoBox.deposit(asset, msg.sender, allBorrowAmount)` (method: deposit, receiver: bentoBox), `bentoBox.withdraw(collateral, to, allCollateralAmount)` (method: withdraw, receiver: bentoBox), `bentoBox.transferFrom(asset, msg.sender, address(this), allBorrowAmount)` (method: transferFrom, receiver: bentoBox), `bentoBox.transfer(collateral, to, allCollateralAmount)` (method: transfer, receiver: bentoBox), `bentoBox.transferFrom(collateral, address(this), address(swapper), allCollateralAmount)` (method: transferFrom, receiver: bentoBox), `swapper.swap(collateral, asset, allCollateralAmount, allBorrowAmount)` (method: swap, receiver: swapper), `bentoBox.skim(asset)` (method: skim, receiver: bentoBox), `totalAsset.amount.add(extraAssetAmount.to128())` (method: add, receiver: totalAsset)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['LIQUIDATION_MULTIPLIER', 'PROTOCOL_FEE', 'accrueInfo', 'asset', 'bentoBox', 'collateral', 'exchangeRate', 'masterContract', 'swappers', 'totalAsset', 'totalBorrow', 'totalCollateralAmount', 'userBorrowFraction', 'userCollateralAmount']
- **External calls**: `_totalBorrow.amount.sub(allBorrowAmount.to128())` (call on contract-typed local var '_totalBorrow' (type: TokenTotals)), `_totalBorrow.fraction.sub(allBorrowFraction.to128())` (call on contract-typed local var '_totalBorrow' (type: TokenTotals)), `masterContract.swappers(swapper)` (call on contract-typed state var 'masterContract' (type: LendingPair)), `bentoBox.transferFrom(collateral, address(this), address(swapper), allCollateralAmount)` (call on contract-typed state var 'bentoBox' (type: IBentoBox)), `swapper.swap(collateral, asset, allCollateralAmount, allBorrowAmount)` (call on contract-typed local var 'swapper' (type: ISwapper)), `bentoBox.skim(asset)` (call on contract-typed state var 'bentoBox' (type: IBentoBox)), `accrueInfo.feesPendingAmount.add(feeAmount.to128())` (call on contract-typed state var 'accrueInfo' (type: AccrueInfo)), `totalAsset.amount.add(extraAssetAmount.sub(feeAmount).to128())` (call on contract-typed state var 'totalAsset' (type: TokenTotals)), `bentoBox.deposit(asset, msg.sender, allBorrowAmount)` (call on contract-typed state var 'bentoBox' (type: IBentoBox)), `bentoBox.withdraw(collateral, to, allCollateralAmount)` (call on contract-typed state var 'bentoBox' (type: IBentoBox)), `bentoBox.transferFrom(asset, msg.sender, address(this), allBorrowAmount)` (call on contract-typed state var 'bentoBox' (type: IBentoBox)), `bentoBox.transfer(collateral, to, allCollateralAmount)` (low-level .transfer()), `bentoBox.transferFrom(collateral, address(this), address(swapper), allCollateralAmount)` (call on contract-typed state var 'bentoBox' (type: IBentoBox)), `swapper.swap(collateral, asset, allCollateralAmount, allBorrowAmount)` (call on contract-typed local var 'swapper' (type: ISwapper)), `bentoBox.skim(asset)` (call on contract-typed state var 'bentoBox' (type: IBentoBox)), `totalAsset.amount.add(extraAssetAmount.to128())` (call on contract-typed state var 'totalAsset' (type: TokenTotals))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### LidoBridge.wrapETH

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call present — unchecked return value plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: wrapETH
- **Line Range**: L115
- **File**: `DAppSCAN-source/contracts/Solidified-Aztec Lido Bridge/aztec-connect-bridges-d5aca13d4d0a17b21eeddf77f49f4c6613461fb0/src/bridges/lido/LidoBridge.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`wrapETH`, lines=`L115`

#### 2. Function Source Code
```solidity
function wrapETH(uint256 inputValue, AztecTypes.AztecAsset calldata outputAsset) private returns (uint256 outputValue) {
        require(
            outputAsset.assetType == AztecTypes.AztecAssetType.ERC20 && outputAsset.erc20Address == address(wrappedStETH),
            "LidoBridge: Invalid Output Token"
        );

        // the minimum should be 1ETH:1STETH
        uint256 minOutput = inputValue;

        // Check with curve to see if we can get better exchange rate than 1 ETH : 1 STETH
        // Yes: use curve
        // No: deposit to Lido correct

        uint256 curveStETHBalance = curvePool.get_dy(curveETHIndex, curveStETHIndex, inputValue);

        if (curveStETHBalance > minOutput) {
            // exchange via curve since we can get a better rate
            // SWC-104-Unchecked Call Return Value: L115
            curvePool.exchange{value: inputValue}(curveETHIndex, curveStETHIndex, inputValue, minOutput);
        } else {
            // deposit directly through lido since we cannot get better rate
            // SWC-104-Unchecked Call Return Value: L119
            lido.submit{value: inputValue}(referral);
        }

        // since stETH is a rebase token, lets wrap it to wstETH before sending it back to the rollupProcessor
        // SWC-104-Unchecked Call Return Value: L124
        uint256 outputStETHBalance = IERC20(address(lido)).balanceOf(address(this));

        IERC20(address(lido)).safeIncreaseAllowance(address(wrappedStETH), outputStETHBalance);
        outputValue = wrappedStETH.wrap(outputStETHBalance);

        // Give allowance for rollup processor to withdraw
        IERC20(address(wrappedStETH)).safeIncreaseAllowance(rollupProcessor, outputValue);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['curveETHIndex', 'curvePool', 'curveStETHIndex', 'lido', 'referral', 'rollupProcessor', 'wrappedStETH']
- **External calls**: `curvePool.get_dy(curveETHIndex, curveStETHIndex, inputValue)` (method: get_dy, receiver: curvePool), `curvePool.exchange{value: inputValue}(curveETHIndex, curveStETHIndex, inputValue, minOutput)` (method: exchange, receiver: curvePool), `lido.submit{value: inputValue}(referral)` (method: submit, receiver: lido), `IERC20(address(lido)).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IERC20(address(lido)).safeIncreaseAllowance(address(wrappedStETH), outputStETHBalance)` (method: safeIncreaseAllowance, receiver: IERC20), `wrappedStETH.wrap(outputStETHBalance)` (method: wrap, receiver: wrappedStETH), `IERC20(address(wrappedStETH)).safeIncreaseAllowance(rollupProcessor, outputValue)` (method: safeIncreaseAllowance, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['curveETHIndex', 'curvePool', 'curveStETHIndex', 'lido', 'referral', 'rollupProcessor', 'wrappedStETH']
- **External calls**: `curvePool.get_dy(curveETHIndex, curveStETHIndex, inputValue)` (call on contract-typed state var 'curvePool' (type: ICurvePool)), `curvePool.exchange{value: inputValue}(curveETHIndex, curveStETHIndex, inputValue, minOutput)` (call on contract-typed state var 'curvePool' (type: ICurvePool)), `lido.submit{value: inputValue}(referral)` (call on contract-typed state var 'lido' (type: ILido)), `IERC20(address(lido)).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IERC20(address(lido)).safeIncreaseAllowance(address(wrappedStETH), outputStETHBalance)` (SafeERC20 .safeIncreaseAllowance()), `wrappedStETH.wrap(outputStETHBalance)` (call on contract-typed state var 'wrappedStETH' (type: IWstETH)), `IERC20(address(wrappedStETH)).safeIncreaseAllowance(rollupProcessor, outputValue)` (SafeERC20 .safeIncreaseAllowance())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Vault.initialize

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: initialize
- **Line Range**: L175 - L189
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-CompliFi/complifi-protocol-v1-912e93014aa16a9b6987556d971ed2b599b8cba7/contracts/Vault.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`initialize`, lines=`L175 - L189`

#### 2. Function Source Code
```solidity
function initialize(int256[] calldata _underlyingStarts) external {
        require(state == State.Created, "Incorrect state.");

        underlyingStarts = _underlyingStarts;

        changeState(State.Live);

        (primaryToken, complementToken) = tokenBuilder.buildTokens(
            derivativeSpecification,
            settleTime,
            address(collateralToken)
        );

        emit LiveStateSet(address(primaryToken), address(complementToken));
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['collateralToken', 'complementToken', 'derivativeSpecification', 'primaryToken', 'settleTime', 'state', 'tokenBuilder', 'underlyingStarts']
- **External calls**: `tokenBuilder.buildTokens(
            derivativeSpecification,
            settleTime,
            address(collateralTok` (method: buildTokens, receiver: tokenBuilder)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['collateralToken', 'complementToken', 'derivativeSpecification', 'primaryToken', 'settleTime', 'state', 'tokenBuilder', 'underlyingStarts']
- **External calls**: `tokenBuilder.buildTokens(
            derivativeSpecification,
            settleTime,
            address(collateralTok` (call on contract-typed state var 'tokenBuilder' (type: ITokenBuilder))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Amp.swap

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: swap
- **Line Range**: L619
- **File**: `DAppSCAN-source/contracts/consensys-Amp/amp-token-contracts-6871b6c64c712835b332e515cc553308dcbbc539/contracts/Amp.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`swap`, lines=`L619`

#### 2. Function Source Code
```solidity
function swap(address _from) public {
        uint256 amount = swapToken.allowance(_from, address(this));
        require(amount > 0, EC_53_INSUFFICIENT_ALLOWANCE);
        // SWC-104-Unchecked Call Return Value: L619
        swapToken.transferFrom(_from, swapTokenGraveyard, amount);

        _mint(msg.sender, _from, amount, "");

        emit Swap(msg.sender, _from, amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['EC_53_INSUFFICIENT_ALLOWANCE', 'swapToken', 'swapTokenGraveyard']
- **External calls**: `swapToken.allowance(_from, address(this))` (method: allowance, receiver: swapToken), `swapToken.transferFrom(_from, swapTokenGraveyard, amount)` (method: transferFrom, receiver: swapToken)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['EC_53_INSUFFICIENT_ALLOWANCE', 'swapToken', 'swapTokenGraveyard']
- **External calls**: `swapToken.allowance(_from, address(this))` (call on contract-typed state var 'swapToken' (type: ISwapToken)), `swapToken.transferFrom(_from, swapTokenGraveyard, amount)` (call on contract-typed state var 'swapToken' (type: ISwapToken))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### UniProxy.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L75-82
- **File**: `DAppSCAN-source/contracts/consensys-Gamma/hypervisor-41fd4abf79864478523e87924d4e80d80df04879/contracts/UniProxy.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L75-82`

#### 2. Function Source Code
```solidity
function deposit(
    uint256 deposit0,
    uint256 deposit1,
    address to,
    address from,
    address pos
  ) external returns (uint256 shares) {
    require(positions[pos].version != 0, 'not added');
    // SWC-107-Reentrancy: L75-82
    if (twapCheck || positions[pos].twapOverride) {
      // check twap
      checkPriceChange(
        pos,
        (positions[pos].twapOverride ? positions[pos].twapInterval : twapInterval),
        (positions[pos].twapOverride ? positions[pos].priceThreshold : priceThreshold)
      );
    }

    if (!freeDeposit && !positions[pos].list[msg.sender] && !positions[pos].freeDeposit) {
      // freeDeposit off and hypervisor msg.sender not on list
      require(properDepositRatio(pos, deposit0, deposit1), "Improper ratio");
    }

    if (positions[pos].depositOverride) {
      if (positions[pos].deposit0Max > 0) {
        require(deposit0 <= positions[pos].deposit0Max, "token0 exceeds");
      }
      if (positions[pos].deposit1Max > 0) {
        require(deposit1 <= positions[pos].deposit1Max, "token1 exceeds");
      }
    }

    if (positions[pos].version < 3) {
      // requires asset transfer to proxy
      if (deposit0 != 0) {
        IHypervisor(pos).token0().transferFrom(msg.sender, address(this), deposit0);
      }
      if (deposit1 != 0) {
        IHypervisor(pos).token1().transferFrom(msg.sender, address(this), deposit1);
      }
      if (positions[pos].version < 2) {
        // requires lp token transfer from proxy to msg.sender
        shares = IHypervisor(pos).deposit(deposit0, deposit1, address(this));
        IHypervisor(pos).transfer(to, shares);
      }
      else{
        // transfer lp tokens direct to msg.sender
        shares = IHypervisor(pos).deposit(deposit0, deposit1, msg.sender);
      }
    }
    else {
      // transfer lp tokens direct to msg.sender
      shares = IHypervisor(pos).deposit(deposit0, deposit1, msg.sender, msg.sender);
    }

    if (positions[pos].depositOverride) {
      require(IHypervisor(pos).totalSupply() <= positions[pos].maxTotalSupply, "supply exceeds");
    }

  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['freeDeposit', 'positions', 'priceThreshold', 'twapCheck', 'twapInterval']
- **External calls**: `IHypervisor(pos).token0().transferFrom(msg.sender, address(this), deposit0)` (method: transferFrom, receiver: IHypervisor), `IHypervisor(pos).token0()` (method: token0, receiver: IHypervisor), `IHypervisor(pos).token1().transferFrom(msg.sender, address(this), deposit1)` (method: transferFrom, receiver: IHypervisor), `IHypervisor(pos).token1()` (method: token1, receiver: IHypervisor), `IHypervisor(pos).deposit(deposit0, deposit1, address(this))` (method: deposit, receiver: IHypervisor), `IHypervisor(pos).transfer(to, shares)` (method: transfer, receiver: IHypervisor), `IHypervisor(pos).deposit(deposit0, deposit1, msg.sender)` (method: deposit, receiver: IHypervisor), `IHypervisor(pos).deposit(deposit0, deposit1, msg.sender, msg.sender)` (method: deposit, receiver: IHypervisor), `IHypervisor(pos).totalSupply()` (method: totalSupply, receiver: IHypervisor)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['freeDeposit', 'positions', 'priceThreshold', 'twapCheck', 'twapInterval']
- **External calls**: `IHypervisor(pos).token0().transferFrom(msg.sender, address(this), deposit0)` (inline cast call IHypervisor(...).transferFrom()), `IHypervisor(pos).token0()` (inline cast call IHypervisor(...).token0()), `IHypervisor(pos).token1().transferFrom(msg.sender, address(this), deposit1)` (inline cast call IHypervisor(...).transferFrom()), `IHypervisor(pos).token1()` (inline cast call IHypervisor(...).token1()), `IHypervisor(pos).deposit(deposit0, deposit1, address(this))` (inline cast call IHypervisor(...).deposit()), `IHypervisor(pos).transfer(to, shares)` (low-level .transfer()), `IHypervisor(pos).deposit(deposit0, deposit1, msg.sender)` (inline cast call IHypervisor(...).deposit()), `IHypervisor(pos).deposit(deposit0, deposit1, msg.sender, msg.sender)` (inline cast call IHypervisor(...).deposit()), `IHypervisor(pos).totalSupply()` (inline cast call IHypervisor(...).totalSupply())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### FuelCrowdfund.closeCrowdfund

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call present — unchecked return value plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: closeCrowdfund
- **Line Range**: L84
- **File**: `DAppSCAN-source/contracts/openzeppelin-Fuel_Token/FUEL-Contracts-3717b751bb2fa57ae300776a93ee4d7d7beb2c07/FuelCrowdfund.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`closeCrowdfund`, lines=`L84`

#### 2. Function Source Code
```solidity
function closeCrowdfund() external onlyOwner returns (bool success) {
        AmountRaised(wallet, weiRaised);
        token.finalizeCrowdfund();
        return true;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['token', 'wallet', 'weiRaised']
- **External calls**: `token.finalizeCrowdfund()` (method: finalizeCrowdfund, receiver: token)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['token', 'wallet', 'weiRaised']
- **External calls**: `token.finalizeCrowdfund()` (call on contract-typed state var 'token' (type: FuelToken))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

---
## TRAIN Cross-Contract (117 items)

### ImpossibleWrappedToken.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L53-61
- **File**: `DAppSCAN-source/contracts/BlockSec-blocksec_impossible_finance_swap_v1.2/impossible-swap-core-29aaef89f996acdbee92b67c4d95fb608dc8b876/contracts/ImpossibleWrappedToken.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L53-61`

#### 2. Function Source Code
```solidity
function deposit(address dst) public override returns (uint256 transferAmt) {
        uint256 balance = IERC20(underlying).balanceOf(address(this));
        transferAmt = balance.sub(underlyingBalance);
        uint256 wad = transferAmt.mul(ratioNum).div(ratioDenom);
        _deposit(dst, wad);
        underlyingBalance = balance;
        emit Transfer(address(0), dst, wad);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['ratioDenom', 'ratioNum', 'underlying', 'underlyingBalance']
- **External calls**: `IERC20(underlying).transferFrom(msg.sender, address(this), transferAmt)` (method: transferFrom, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['balanceOf', 'ratioDenom', 'ratioNum', 'underlying', 'underlyingBalance']
- **External calls**: `IERC20(underlying).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ❌
- External calls match: ❌
- Cross-contract match: ✅

### ImpossibleWrappedToken.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L65-73
- **File**: `DAppSCAN-source/contracts/BlockSec-blocksec_impossible_finance_swap_v1.2/impossible-swap-core-29aaef89f996acdbee92b67c4d95fb608dc8b876/contracts/ImpossibleWrappedToken.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L53-61`

#### 2. Function Source Code
```solidity
function deposit(address dst) public override returns (uint256 transferAmt) {
        uint256 balance = IERC20(underlying).balanceOf(address(this));
        transferAmt = balance.sub(underlyingBalance);
        uint256 wad = transferAmt.mul(ratioNum).div(ratioDenom);
        _deposit(dst, wad);
        underlyingBalance = balance;
        emit Transfer(address(0), dst, wad);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['balanceOf', 'ratioDenom', 'ratioNum', 'underlying', 'underlyingBalance']
- **External calls**: `IERC20(underlying).balanceOf(address(this))` (method: balanceOf, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['balanceOf', 'ratioDenom', 'ratioNum', 'underlying', 'underlyingBalance']
- **External calls**: `IERC20(underlying).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### GenericAave.harvest

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: harvest
- **Line Range**: L104-134
- **File**: `DAppSCAN-source/contracts/Chainsecurity-Angle Protocol/angle-core-46e6d32837cbe97a4af0adb693e63afa0d01fc3e/contracts/genericLender/GenericAave.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`harvest`, lines=`L104-134`

#### 2. Function Source Code
```solidity
function harvest() external {
        require(_checkCooldown(), "conditions are not met");
        // redeem AAVE from stkAave
        uint256 stkAaveBalance = IERC20(address(stkAave)).balanceOf(address(this));
        if (stkAaveBalance > 0) {
            stkAave.redeem(address(this), stkAaveBalance);
        }

        // sell AAVE for want
        uint256 aaveBalance = IERC20(AAVE).balanceOf(address(this));
        _sellAAVEForWant(aaveBalance);

        // deposit want in lending protocol
        uint256 balance = want.balanceOf(address(this));
        if (balance > 0) {
            _deposit(balance);
        }

        // claim rewards
        address[] memory assets = new address[](1);
        assets[0] = address(aToken);
        uint256 pendingRewards = _incentivesController().getRewardsBalance(assets, address(this));
        if (pendingRewards > 0) {
            _incentivesController().claimRewards(assets, pendingRewards, address(this));
        }

        // request start of cooldown period
        if (IERC20(address(stkAave)).balanceOf(address(this)) > 0) {
            stkAave.cooldown();
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['AAVE', 'aToken', 'stkAave', 'want']
- **External calls**: `IERC20(address(stkAave)).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `stkAave.redeem(address(this), stkAaveBalance)` (method: redeem, receiver: stkAave), `IERC20(AAVE).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `want.balanceOf(address(this))` (method: balanceOf, receiver: want), `IERC20(address(stkAave)).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `stkAave.cooldown()` (method: cooldown, receiver: stkAave)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['AAVE', 'aToken', 'stkAave', 'want']
- **External calls**: `IERC20(address(stkAave)).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `stkAave.redeem(address(this), stkAaveBalance)` (call on contract-typed state var 'stkAave' (type: IStakedAave)), `IERC20(AAVE).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `want.balanceOf(address(this))` (call on contract-typed state var 'want' (type: IERC20)), `IERC20(address(stkAave)).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `stkAave.cooldown()` (call on contract-typed state var 'stkAave' (type: IStakedAave))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### VaultManager.liquidate

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call present — unchecked return value plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: liquidate
- **Line Range**: L692
- **File**: `DAppSCAN-source/contracts/Chainsecurity-Angle Protocol  Borrowing Module/angle-borrow-0363b6a137a44e22ee06b3187ba74f7798c1af08/contracts/vaultManager/VaultManager.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`liquidate`, lines=`L692`

#### 2. Function Source Code
(66 lines, showing first 30 + last 15)
```solidity
function liquidate(
        uint256[] memory vaultIDs,
        uint256[] memory amounts,
        address from,
        address to,
        address who,
        bytes memory data
    ) public whenNotPaused nonReentrant returns (LiquidatorData memory liqData) {
        if (vaultIDs.length != amounts.length || amounts.length == 0) revert IncompatibleLengths();
        // Stores all the data about an ongoing liquidation of multiple vaults
        liqData.oracleValue = oracle.read();
        liqData.newInterestAccumulator = _accrue();
        emit LiquidatedVaults(vaultIDs);
        for (uint256 i = 0; i < vaultIDs.length; i++) {
            Vault memory vault = vaultData[vaultIDs[i]];
            // Computing if liquidation can take place for a vault
            LiquidationOpportunity memory liqOpp = _checkLiquidation(
                vault,
                msg.sender,
                liqData.oracleValue,
                liqData.newInterestAccumulator
            );

            // Makes sure not to leave a dusty amount in the vault by either not liquidating too much
            // or everything
            if (
                (liqOpp.thresholdRepayAmount > 0 && amounts[i] > liqOpp.thresholdRepayAmount) ||
                amounts[i] > liqOpp.maxStablecoinAmountToRepay
            ) amounts[i] = liqOpp.maxStablecoinAmountToRepay;

    // ... truncated ...
                // SWC-104-Unchecked Call Return Value: L692
                _repayDebt(
                    vaultIDs[i],
                    (amounts[i] * liquidationSurcharge) / BASE_PARAMS,
                    liqData.newInterestAccumulator
                );
            }
            liqData.collateralAmountToGive += collateralReleased;
            liqData.stablecoinAmountToReceive += amounts[i];
        }
        // Normalization of good and bad debt is already handled in the `accrueInterestToTreasury` function
        surplus += (liqData.stablecoinAmountToReceive * (BASE_PARAMS - liquidationSurcharge)) / BASE_PARAMS;
        badDebt += liqData.badDebtFromLiquidation;
        _handleRepay(liqData.collateralAmountToGive, liqData.stablecoinAmountToReceive, from, to, who, data);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['BASE_PARAMS', '_collatBase', 'badDebt', 'liquidationSurcharge', 'oracle', 'surplus', 'totalNormalizedDebt', 'vaultData']
- **External calls**: `oracle.read()` (method: read, receiver: oracle)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['BASE_PARAMS', '_collatBase', 'badDebt', 'liquidationSurcharge', 'oracle', 'surplus', 'totalNormalizedDebt', 'vaultData']
- **External calls**: `oracle.read()` (call on contract-typed state var 'oracle' (type: IOracle))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### CToken._setComptroller

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: _setComptroller
- **Line Range**: L930-947
- **File**: `DAppSCAN-source/contracts/Chainsecurity-Compound  cToken unredacted/compound-protocol-4a54ec5c55b66ea67d44b76f3056f0ed7229db8c/contracts/CToken.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`_setComptroller`, lines=`L930-947`

#### 2. Function Source Code
```solidity
function _setComptroller(ComptrollerInterface newComptroller) override public returns (uint) {
        // Check caller is admin
        if (msg.sender != admin) {
            revert SetComptrollerOwnerCheck();
        }

        ComptrollerInterface oldComptroller = comptroller;
        // Ensure invoke comptroller.isComptroller() returns true
        require(newComptroller.isComptroller(), "marker method returned false");

        // Set market's comptroller to newComptroller
        comptroller = newComptroller;

        // Emit NewComptroller(oldComptroller, newComptroller)
        emit NewComptroller(oldComptroller, newComptroller);

        return NO_ERROR;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['NO_ERROR', 'admin', 'comptroller']
- **External calls**: `newComptroller.isComptroller()` (method: isComptroller, receiver: newComptroller)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['NO_ERROR', 'admin', 'comptroller']
- **External calls**: `newComptroller.isComptroller()` (call on contract-typed local var 'newComptroller' (type: ComptrollerInterface))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Comptroller.liquidateBorrowAllowed

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: liquidateBorrowAllowed
- **Line Range**: L465-501
- **File**: `DAppSCAN-source/contracts/Chainsecurity-Compound  cToken unredacted/compound-protocol-4a54ec5c55b66ea67d44b76f3056f0ed7229db8c/contracts/Comptroller.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`liquidateBorrowAllowed`, lines=`L465-501`

#### 2. Function Source Code
```solidity
function liquidateBorrowAllowed(
        address cTokenBorrowed,
        address cTokenCollateral,
        address liquidator,
        address borrower,
        uint repayAmount) override external returns (uint) {
        // Shh - currently unused
        liquidator;

        if (!markets[cTokenBorrowed].isListed || !markets[cTokenCollateral].isListed) {
            return uint(Error.MARKET_NOT_LISTED);
        }

        uint borrowBalance = CToken(cTokenBorrowed).borrowBalanceStored(borrower);

        /* allow accounts to be liquidated if the market is deprecated */
        if (isDeprecated(CToken(cTokenBorrowed))) {
            require(borrowBalance >= repayAmount, "Can not repay more than the total borrow");
        } else {
            /* The borrower must have shortfall in order to be liquidatable */
            (Error err, , uint shortfall) = getAccountLiquidityInternal(borrower);
            if (err != Error.NO_ERROR) {
                return uint(err);
            }

            if (shortfall == 0) {
                return uint(Error.INSUFFICIENT_SHORTFALL);
            }

            /* The liquidator may not repay more than what is allowed by the closeFactor */
            uint maxClose = mul_ScalarTruncate(Exp({mantissa: closeFactorMantissa}), borrowBalance);
            if (repayAmount > maxClose) {
                return uint(Error.TOO_MUCH_REPAY);
            }
        }
        return uint(Error.NO_ERROR);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['closeFactorMantissa', 'markets']
- **External calls**: `CToken(cTokenBorrowed).borrowBalanceStored(borrower)` (method: borrowBalanceStored, receiver: CToken)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['closeFactorMantissa', 'markets']
- **External calls**: `CToken(cTokenBorrowed).borrowBalanceStored(borrower)` (inline cast call CToken(...).borrowBalanceStored())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### MultiplyProxyActions.increaseMultipleDepositCollateral

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: increaseMultipleDepositCollateral
- **Line Range**: L172
- **File**: `DAppSCAN-source/contracts/Chainsecurity-Oasis  Multiply Smart Contracts/multiply-proxy-actions-e277ac1471a95138aaa93b39cf2c16c36c769740/contracts/multiply/MultiplyProxyActions.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`increaseMultipleDepositCollateral`, lines=`L172`

#### 2. Function Source Code
```solidity
function increaseMultipleDepositCollateral(
    ExchangeData calldata exchangeData,
    CdpData memory cdpData,
    AddressRegistry calldata addressRegistry
  )
    public
    payable
    logMethodName(
      "increaseMultipleDepositCollateral",
      cdpData,
      addressRegistry.multiplyProxyActions
    )
  { 
    // SWC-104-Unchecked Call Return Value: L172
    IGem gem = IJoin(cdpData.gemJoin).gem();

    if (address(gem) == WETH) {
      gem.deposit{value: msg.value}();
      if (cdpData.skipFL == false) {
        gem.transfer(addressRegistry.multiplyProxyActions, msg.value);
      }
    } else {
      if (cdpData.skipFL == false) {
        gem.transferFrom(
          msg.sender,
          addressRegistry.multiplyProxyActions,
          cdpData.depositCollateral
        );
      } else {
        gem.transferFrom(msg.sender, address(this), cdpData.depositCollateral);
      }
    }
    increaseMultipleInternal(exchangeData, cdpData, addressRegistry);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['WETH']
- **External calls**: `IJoin(cdpData.gemJoin).gem()` (method: gem, receiver: IJoin), `gem.deposit{value: msg.value}()` (method: deposit, receiver: gem), `gem.transfer(addressRegistry.multiplyProxyActions, msg.value)` (method: transfer, receiver: gem), `gem.transferFrom(
          msg.sender,
          addressRegistry.multiplyProxyActions,
          cdpData.depositCollate` (method: transferFrom, receiver: gem), `gem.transferFrom(msg.sender, address(this), cdpData.depositCollateral)` (method: transferFrom, receiver: gem)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['WETH']
- **External calls**: `IJoin(cdpData.gemJoin).gem()` (inline cast call IJoin(...).gem()), `gem.deposit{value: msg.value}()` (call on contract-typed local var 'gem' (type: IGem)), `gem.transfer(addressRegistry.multiplyProxyActions, msg.value)` (low-level .transfer()), `gem.transferFrom(
          msg.sender,
          addressRegistry.multiplyProxyActions,
          cdpData.depositCollate` (call on contract-typed local var 'gem' (type: IGem)), `gem.transferFrom(msg.sender, address(this), cdpData.depositCollateral)` (call on contract-typed local var 'gem' (type: IGem))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### FountainBase._depositAngel

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: _depositAngel
- **Line Range**: L290-291
- **File**: `DAppSCAN-source/contracts/Chainsulting-Furucombo-project2/trevi-b3f7fd332873321152db48c9d43fc23a60a29f1a/contracts/FountainBase.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`_depositAngel`, lines=`L290-291`

#### 2. Function Source Code
```solidity
function _depositAngel(
        address user,
        IAngel angel,
        uint256 amount
    ) internal nonReentrant {
        AngelInfo storage info = _angelInfos[angel];
        _requireMsg(
            info.isSet,
            "_depositAngel",
            "Fountain: not added by angel"
        );
        angel.deposit(info.pid, amount, user);
        info.totalBalance = info.totalBalance.add(amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_angelInfos']
- **External calls**: `angel.deposit(info.pid, amount, user)` (method: deposit, receiver: angel), `info.totalBalance.add(amount)` (method: add, receiver: info)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['_angelInfos']
- **External calls**: `angel.deposit(info.pid, amount, user)` (call on contract-typed local var 'angel' (type: IAngel)), `info.totalBalance.add(amount)` (call on contract-typed local var 'info' (type: AngelInfo))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### FountainBase._withdrawAngel

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: _withdrawAngel
- **Line Range**: L295-L308
- **File**: `DAppSCAN-source/contracts/Chainsulting-Furucombo-project2/trevi-b3f7fd332873321152db48c9d43fc23a60a29f1a/contracts/FountainBase.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`_withdrawAngel`, lines=`L295-L308`

#### 2. Function Source Code
```solidity
function _withdrawAngel(
        address user,
        IAngel angel,
        uint256 amount
    ) internal nonReentrant {
        AngelInfo storage info = _angelInfos[angel];
        _requireMsg(
            info.isSet,
            "_withdrawAngel",
            "Fountain: not added by angel"
        );
        angel.withdraw(info.pid, amount, user);
        info.totalBalance = info.totalBalance.sub(amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_angelInfos']
- **External calls**: `angel.withdraw(info.pid, amount, user)` (method: withdraw, receiver: angel), `info.totalBalance.sub(amount)` (method: sub, receiver: info)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['_angelInfos']
- **External calls**: `angel.withdraw(info.pid, amount, user)` (call on contract-typed local var 'angel' (type: IAngel)), `info.totalBalance.sub(amount)` (call on contract-typed local var 'info' (type: AngelInfo))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### ERC20Permit.permit

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: permit
- **Line Range**: L53
- **File**: `DAppSCAN-source/contracts/QuillAudits-1inch-token/1inch-token-99fd056f91005ca521a02a005f7bcd8f77e06afc/contracts/ERC20Permit.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`permit`, lines=`L53`

#### 2. Function Source Code
```solidity
function permit(address owner, address spender, uint256 amount, uint256 deadline, uint8 v, bytes32 r, bytes32 s) public virtual override {
        // solhint-disable-next-line not-rely-on-time
        require(block.timestamp <= deadline, "ERC20Permit: expired deadline");

        bytes32 structHash = keccak256(
            abi.encode(
                _PERMIT_TYPEHASH,
                owner,
                spender,
                amount,
                _nonces[owner].current(),
                deadline
            )
        );

        bytes32 hash = _hashTypedDataV4(structHash);

        address signer = ECDSA.recover(hash, v, r, s);
        require(signer == owner, "ERC20Permit: invalid signature");

        _nonces[owner].increment();
        // SWC-114-Transaction Order Dependence: L53
        _approve(owner, spender, amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_PERMIT_TYPEHASH', '_nonces']
- **External calls**: `_nonces[owner].current()` (method: current, receiver: _nonces), `ECDSA.recover(hash, v, r, s)` (method: recover, receiver: ECDSA), `_nonces[owner].increment()` (method: increment, receiver: _nonces)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['_PERMIT_TYPEHASH', '_nonces']
- **External calls**: `_nonces[owner].current()` (call on contract-typed state var '_nonces' (type: mapping (address => Counters.Counter))), `ECDSA.recover(hash, v, r, s)` (call on interface/contract type 'ECDSA'), `_nonces[owner].increment()` (call on contract-typed state var '_nonces' (type: mapping (address => Counters.Counter)))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### CommunityVault.setAllowance

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: setAllowance
- **Line Range**: L19
- **File**: `DAppSCAN-source/contracts/Coinbae-Barnbridge_Vault/CommunityVault0xA3C299eEE1998F45c20010276684921EBE6423D9/contracts/CommunityVault.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`setAllowance`, lines=`L19`

#### 2. Function Source Code
```solidity
function setAllowance(address spender, uint amount) public onlyOwner {
        // SWC-107-Reentrancy: L19
        _bond.approve(spender, amount);

        emit SetAllowance(msg.sender, spender, amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_bond']
- **External calls**: `_bond.approve(spender, amount)` (method: approve, receiver: _bond)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['_bond']
- **External calls**: `_bond.approve(spender, amount)` (call on contract-typed state var '_bond' (type: IERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### MasterChef.withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdraw
- **Line Range**: L272 - L306
- **File**: `DAppSCAN-source/contracts/Coinbae-Pud.Fi Masterchef_Audit/MasterChef0x15Bee180BB39eE5c0166E63313C33984376930Db/contracts/MasterChef.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdraw`, lines=`L272 - L306`

#### 2. Function Source Code
```solidity
function withdraw(uint256 _pid, uint256 _shares) public {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];

        require(user.shares >= _shares, "withdraw: not good");
        updatePool(_pid);

        uint256 r = (balance(_pid).mul(_shares)).div(pool.totalShares);        
        uint256 pending =
            user.shares.mul(pool.accPudPerShare).div(1e12).sub(
                user.rewardDebt
            );

        safePudTransfer(msg.sender, pending);
        user.shares = user.shares.sub(_shares);
        user.rewardDebt = user.shares.mul(pool.accPudPerShare).div(1e12);
        pool.totalShares = pool.totalShares.sub(_shares); //minus shares in pool

        // Check balance
        if (r > 0) {
            uint256 b = pool.lpToken.balanceOf(address(this));

            IStrategy(pool.strategy).withdraw(r);
            uint256 _after = pool.lpToken.balanceOf(address(this));
            uint256 _diff = _after.sub(b);
            if (_diff < r) {
                r = b.add(_diff);
            }

            pool.lpToken.safeTransfer(address(msg.sender), r);

        }

        emit Withdraw(msg.sender, _pid, r);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.shares.mul(pool.accPudPerShare).div(1e12).sub(
                user.rewardDebt
            )` (method: sub, receiver: user), `user.shares.mul(pool.accPudPerShare).div(1e12)` (method: div, receiver: user), `user.shares.mul(pool.accPudPerShare)` (method: mul, receiver: user), `user.shares.sub(_shares)` (method: sub, receiver: user), `user.shares.mul(pool.accPudPerShare).div(1e12)` (method: div, receiver: user), `user.shares.mul(pool.accPudPerShare)` (method: mul, receiver: user), `pool.totalShares.sub(_shares)` (method: sub, receiver: pool), `pool.lpToken.balanceOf(address(this))` (method: balanceOf, receiver: pool), `IStrategy(pool.strategy).withdraw(r)` (method: withdraw, receiver: IStrategy), `pool.lpToken.balanceOf(address(this))` (method: balanceOf, receiver: pool), `pool.lpToken.safeTransfer(address(msg.sender), r)` (method: safeTransfer, receiver: pool)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.shares.mul(pool.accPudPerShare).div(1e12).sub(
                user.rewardDebt
            )` (call on contract-typed local var 'user' (type: UserInfo)), `user.shares.mul(pool.accPudPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.shares.mul(pool.accPudPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `user.shares.sub(_shares)` (call on contract-typed local var 'user' (type: UserInfo)), `user.shares.mul(pool.accPudPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.shares.mul(pool.accPudPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `pool.totalShares.sub(_shares)` (call on contract-typed local var 'pool' (type: PoolInfo)), `pool.lpToken.balanceOf(address(this))` (call on contract-typed local var 'pool' (type: PoolInfo)), `IStrategy(pool.strategy).withdraw(r)` (inline cast call IStrategy(...).withdraw()), `pool.lpToken.balanceOf(address(this))` (call on contract-typed local var 'pool' (type: PoolInfo)), `pool.lpToken.safeTransfer(address(msg.sender), r)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### MasterChef.emergencyWithdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: emergencyWithdraw
- **Line Range**: L310 - L329
- **File**: `DAppSCAN-source/contracts/Coinbae-Pud.Fi Masterchef_Audit/MasterChef0x15Bee180BB39eE5c0166E63313C33984376930Db/contracts/MasterChef.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`emergencyWithdraw`, lines=`L310 - L329`

#### 2. Function Source Code
```solidity
function emergencyWithdraw(uint256 _pid) public {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        uint256 r = (balance(_pid).mul(user.shares)).div(pool.totalShares);

        // Check balance
        uint256 b = pool.lpToken.balanceOf(address(this));

        IStrategy(pool.strategy).withdraw(r);
        uint256 _after = pool.lpToken.balanceOf(address(this));
        uint256 _diff = _after.sub(b);
        if (_diff < r) {
            r = b.add(_diff);
        }

        pool.lpToken.safeTransfer(address(msg.sender), r);
        emit EmergencyWithdraw(msg.sender, _pid, user.shares);
        user.shares = 0;
        user.rewardDebt = 0;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `pool.lpToken.balanceOf(address(this))` (method: balanceOf, receiver: pool), `IStrategy(pool.strategy).withdraw(r)` (method: withdraw, receiver: IStrategy), `pool.lpToken.balanceOf(address(this))` (method: balanceOf, receiver: pool), `pool.lpToken.safeTransfer(address(msg.sender), r)` (method: safeTransfer, receiver: pool)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `pool.lpToken.balanceOf(address(this))` (call on contract-typed local var 'pool' (type: PoolInfo)), `IStrategy(pool.strategy).withdraw(r)` (inline cast call IStrategy(...).withdraw()), `pool.lpToken.balanceOf(address(this))` (call on contract-typed local var 'pool' (type: PoolInfo)), `pool.lpToken.safeTransfer(address(msg.sender), r)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### MasterChef.safePudTransfer

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: safePudTransfer
- **Line Range**: L333 - L340
- **File**: `DAppSCAN-source/contracts/Coinbae-Pud.Fi Masterchef_Audit/MasterChef0x15Bee180BB39eE5c0166E63313C33984376930Db/contracts/MasterChef.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`safePudTransfer`, lines=`L333 - L340`

#### 2. Function Source Code
```solidity
function safePudTransfer(address _to, uint256 _amount) internal {
        uint256 pudBal = pud.balanceOf(address(this));
        if (_amount > pudBal) {
            pud.transfer(_to, pudBal);
        } else {
            pud.transfer(_to, _amount);
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['pud']
- **External calls**: `pud.balanceOf(address(this))` (method: balanceOf, receiver: pud), `pud.transfer(_to, pudBal)` (method: transfer, receiver: pud), `pud.transfer(_to, _amount)` (method: transfer, receiver: pud)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['pud']
- **External calls**: `pud.balanceOf(address(this))` (call on contract-typed state var 'pud' (type: PudToken)), `pud.transfer(_to, pudBal)` (low-level .transfer()), `pud.transfer(_to, _amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### MasterChef.balance

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: balance
- **Line Range**: L378 - L381
- **File**: `DAppSCAN-source/contracts/Coinbae-Pud.Fi Masterchef_Audit/MasterChef0x15Bee180BB39eE5c0166E63313C33984376930Db/contracts/MasterChef.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`balance`, lines=`L378 - L381`

#### 2. Function Source Code
```solidity
function balance(uint256 _pid) public view returns (uint256) {
        PoolInfo storage pool = poolInfo[_pid];
        return IStrategy(pool.strategy).balanceOf();
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo']
- **External calls**: `IStrategy(pool.strategy).balanceOf()` (method: balanceOf, receiver: IStrategy)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['poolInfo']
- **External calls**: `IStrategy(pool.strategy).balanceOf()` (inline cast call IStrategy(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### MasterChef.setPoolStrategy

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call present — unchecked return value plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: setPoolStrategy
- **Line Range**: L384 - L389
- **File**: `DAppSCAN-source/contracts/Coinbae-Pud.Fi Masterchef_Audit/MasterChef0x15Bee180BB39eE5c0166E63313C33984376930Db/contracts/MasterChef.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`setPoolStrategy`, lines=`L384 - L389`

#### 2. Function Source Code
```solidity
function setPoolStrategy(uint256 _pid,address _strategy) public onlyOwner {
        PoolInfo storage pool = poolInfo[_pid];
        IStrategy(pool.strategy).harvest();
        IStrategy(pool.strategy).withdrawAll(_strategy);        
        pool.strategy = _strategy;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo']
- **External calls**: `IStrategy(pool.strategy).harvest()` (method: harvest, receiver: IStrategy), `IStrategy(pool.strategy).withdrawAll(_strategy)` (method: withdrawAll, receiver: IStrategy)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['poolInfo']
- **External calls**: `IStrategy(pool.strategy).harvest()` (inline cast call IStrategy(...).harvest()), `IStrategy(pool.strategy).withdrawAll(_strategy)` (inline cast call IStrategy(...).withdrawAll())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StrategyBase._swapUniswap

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _swapUniswap
- **Line Range**: L237 - L268
- **File**: `DAppSCAN-source/contracts/Coinbae-Pud.Fi Strategy_Bacdai/StrategyBasisBacDaiLp0x31dfcB1C5dF01A27F8b0b5F9cD1585FE92C7970e/contracts/strategies/strategy-base.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_swapUniswap`, lines=`L237 - L268`

#### 2. Function Source Code
```solidity
function _swapUniswap(
        address _from,
        address _to,
        uint256 _amount
    ) internal {
        require(_to != address(0));

        // Swap with uniswap
        IERC20(_from).safeApprove(univ2Router2, 0);
        IERC20(_from).safeApprove(univ2Router2, _amount);

        address[] memory path;

        if (_from == weth || _to == weth) {
            path = new address[](2);
            path[0] = _from;
            path[1] = _to;
        } else {
            path = new address[](3);
            path[0] = _from;
            path[1] = weth;
            path[2] = _to;
        }

        UniswapRouterV2(univ2Router2).swapExactTokensForTokens(
            _amount,
            0,
            path,
            address(this),
            now.add(60)
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['univ2Router2', 'weth']
- **External calls**: `IERC20(_from).safeApprove(univ2Router2, 0)` (method: safeApprove, receiver: IERC20), `IERC20(_from).safeApprove(univ2Router2, _amount)` (method: safeApprove, receiver: IERC20), `UniswapRouterV2(univ2Router2).swapExactTokensForTokens(
            _amount,
            0,
            path,
          ` (method: swapExactTokensForTokens, receiver: UniswapRouterV2)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['univ2Router2', 'weth']
- **External calls**: `IERC20(_from).safeApprove(univ2Router2, 0)` (SafeERC20 .safeApprove()), `IERC20(_from).safeApprove(univ2Router2, _amount)` (SafeERC20 .safeApprove()), `UniswapRouterV2(univ2Router2).swapExactTokensForTokens(
            _amount,
            0,
            path,
          ` (inline cast call UniswapRouterV2(...).swapExactTokensForTokens())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StrategyBase._swapUniswapWithPath

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _swapUniswapWithPath
- **Line Range**: L271 - L288
- **File**: `DAppSCAN-source/contracts/Coinbae-Pud.Fi Strategy_Bacdai/StrategyBasisBacDaiLp0x31dfcB1C5dF01A27F8b0b5F9cD1585FE92C7970e/contracts/strategies/strategy-base.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_swapUniswapWithPath`, lines=`L271 - L288`

#### 2. Function Source Code
```solidity
function _swapUniswapWithPath(
        address[] memory path,
        uint256 _amount
    ) internal {
        require(path[1] != address(0));

        // Swap with uniswap
        IERC20(path[0]).safeApprove(univ2Router2, 0);
        IERC20(path[0]).safeApprove(univ2Router2, _amount);
        
        UniswapRouterV2(univ2Router2).swapExactTokensForTokens(
            _amount,
            0,
            path,
            address(this),
            now.add(60)
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['univ2Router2']
- **External calls**: `IERC20(path[0]).safeApprove(univ2Router2, 0)` (method: safeApprove, receiver: IERC20), `IERC20(path[0]).safeApprove(univ2Router2, _amount)` (method: safeApprove, receiver: IERC20), `UniswapRouterV2(univ2Router2).swapExactTokensForTokens(
            _amount,
            0,
            path,
          ` (method: swapExactTokensForTokens, receiver: UniswapRouterV2)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['univ2Router2']
- **External calls**: `IERC20(path[0]).safeApprove(univ2Router2, 0)` (SafeERC20 .safeApprove()), `IERC20(path[0]).safeApprove(univ2Router2, _amount)` (SafeERC20 .safeApprove()), `UniswapRouterV2(univ2Router2).swapExactTokensForTokens(
            _amount,
            0,
            path,
          ` (inline cast call UniswapRouterV2(...).swapExactTokensForTokens())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StrategyBase._swapSushiswap

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _swapSushiswap
- **Line Range**: L291 - L322
- **File**: `DAppSCAN-source/contracts/Coinbae-Pud.Fi Strategy_Bacdai/StrategyBasisBacDaiLp0x31dfcB1C5dF01A27F8b0b5F9cD1585FE92C7970e/contracts/strategies/strategy-base.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_swapSushiswap`, lines=`L291 - L322`

#### 2. Function Source Code
```solidity
function _swapSushiswap(
        address _from,
        address _to,
        uint256 _amount
    ) internal {
        require(_to != address(0));

        // Swap with uniswap
        IERC20(_from).safeApprove(sushiRouter, 0);
        IERC20(_from).safeApprove(sushiRouter, _amount);

        address[] memory path;

        if (_from == weth || _to == weth) {
            path = new address[](2);
            path[0] = _from;
            path[1] = _to;
        } else {
            path = new address[](3);
            path[0] = _from;
            path[1] = weth;
            path[2] = _to;
        }

        UniswapRouterV2(sushiRouter).swapExactTokensForTokens(
            _amount,
            0,
            path,
            address(this),
            now.add(60)
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['sushiRouter', 'weth']
- **External calls**: `IERC20(_from).safeApprove(sushiRouter, 0)` (method: safeApprove, receiver: IERC20), `IERC20(_from).safeApprove(sushiRouter, _amount)` (method: safeApprove, receiver: IERC20), `UniswapRouterV2(sushiRouter).swapExactTokensForTokens(
            _amount,
            0,
            path,
           ` (method: swapExactTokensForTokens, receiver: UniswapRouterV2)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['sushiRouter', 'weth']
- **External calls**: `IERC20(_from).safeApprove(sushiRouter, 0)` (SafeERC20 .safeApprove()), `IERC20(_from).safeApprove(sushiRouter, _amount)` (SafeERC20 .safeApprove()), `UniswapRouterV2(sushiRouter).swapExactTokensForTokens(
            _amount,
            0,
            path,
           ` (inline cast call UniswapRouterV2(...).swapExactTokensForTokens())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StrategyBase._swapSushiswapWithPath

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _swapSushiswapWithPath
- **Line Range**: L325 - L342
- **File**: `DAppSCAN-source/contracts/Coinbae-Pud.Fi Strategy_Bacdai/StrategyBasisBacDaiLp0x31dfcB1C5dF01A27F8b0b5F9cD1585FE92C7970e/contracts/strategies/strategy-base.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_swapSushiswapWithPath`, lines=`L325 - L342`

#### 2. Function Source Code
```solidity
function _swapSushiswapWithPath(
        address[] memory path,
        uint256 _amount
    ) internal {
        require(path[1] != address(0));

        // Swap with uniswap
        IERC20(path[0]).safeApprove(sushiRouter, 0);
        IERC20(path[0]).safeApprove(sushiRouter, _amount);
        
        UniswapRouterV2(sushiRouter).swapExactTokensForTokens(
            _amount,
            0,
            path,
            address(this),
            now.add(60)
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['sushiRouter']
- **External calls**: `IERC20(path[0]).safeApprove(sushiRouter, 0)` (method: safeApprove, receiver: IERC20), `IERC20(path[0]).safeApprove(sushiRouter, _amount)` (method: safeApprove, receiver: IERC20), `UniswapRouterV2(sushiRouter).swapExactTokensForTokens(
            _amount,
            0,
            path,
           ` (method: swapExactTokensForTokens, receiver: UniswapRouterV2)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['sushiRouter']
- **External calls**: `IERC20(path[0]).safeApprove(sushiRouter, 0)` (SafeERC20 .safeApprove()), `IERC20(path[0]).safeApprove(sushiRouter, _amount)` (SafeERC20 .safeApprove()), `UniswapRouterV2(sushiRouter).swapExactTokensForTokens(
            _amount,
            0,
            path,
           ` (inline cast call UniswapRouterV2(...).swapExactTokensForTokens())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StrategyBasisFarmBase.harvest

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: harvest
- **Line Range**: L78 - L152
- **File**: `DAppSCAN-source/contracts/Coinbae-Pud.Fi Strategy_Bacdai/StrategyBasisBacDaiLp0x31dfcB1C5dF01A27F8b0b5F9cD1585FE92C7970e/contracts/strategies/strategy-basis-farm-base.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`harvest`, lines=`L78 - L152`

#### 2. Function Source Code
(75 lines, showing first 30 + last 15)
```solidity
function harvest() public override onlyBenevolent {
        // Anyone can harvest it at any given time.
        // I understand the possibility of being frontrun
        // But ETH is a dark forest, and I wanna see how this plays out
        // i.e. will be be heavily frontrunned?
        //      if so, a new strategy will be deployed.
        address[] memory _path = new address[](2);

        // Collects Rewards tokens
        IStakingRewards(pool).claimReward(poolId);
        uint256 _rewards = IERC20(rewards).balanceOf(address(this));
        uint256 _token1 = 0;

        if (_rewards > 0) {
            // x % is locked up for future gov
            uint256 _keepRewards =
                _rewards.mul(keepRewards).div(keepRewardsMax);
            IERC20(rewards).safeTransfer(
                IController(controller).treasury(),
                _keepRewards
            );
            
            if (rewards == token1){
                _token1 = _rewards.sub(_keepRewards);
            } else {
                //swap rewards to token1
                _swapUniswapWithPath(path, _rewards.sub(_keepRewards));
                _token1 = IERC20(token1).balanceOf(address(this));
            }
        }
    // ... truncated ...

            // Donates DUST
            IERC20(token1).transfer(
                IController(controller).treasury(),
                IERC20(token1).balanceOf(address(this))
            );
            IERC20(token2).safeTransfer(
                IController(controller).treasury(),
                IERC20(token2).balanceOf(address(this))
            );
        }

        // We want to get back BAS LP tokens
        _distributePerformanceFeesAndDeposit();
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['controller', 'keepRewards', 'keepRewardsMax', 'path', 'pool', 'poolId', 'rewards', 'token1', 'token2', 'univ2Router2']
- **External calls**: `IStakingRewards(pool).claimReward(poolId)` (method: claimReward, receiver: IStakingRewards), `IERC20(rewards).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IERC20(rewards).safeTransfer(
                IController(controller).treasury(),
                _keepRewards
         ` (method: safeTransfer, receiver: IERC20), `IController(controller).treasury()` (method: treasury, receiver: IController), `IERC20(token1).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IERC20(token1).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IERC20(token2).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IERC20(token1).safeApprove(univ2Router2, 0)` (method: safeApprove, receiver: IERC20), `IERC20(token1).safeApprove(univ2Router2, _token1)` (method: safeApprove, receiver: IERC20), `IERC20(token2).safeApprove(univ2Router2, 0)` (method: safeApprove, receiver: IERC20), `IERC20(token2).safeApprove(univ2Router2, _token2)` (method: safeApprove, receiver: IERC20), `UniswapRouterV2(univ2Router2).addLiquidity(
                token1,
                token2,
                _token1,
   ` (method: addLiquidity, receiver: UniswapRouterV2), `IERC20(token1).transfer(
                IController(controller).treasury(),
                IERC20(token1).balanceOf(ad` (method: transfer, receiver: IERC20), `IController(controller).treasury()` (method: treasury, receiver: IController), `IERC20(token1).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IERC20(token2).safeTransfer(
                IController(controller).treasury(),
                IERC20(token2).balanceO` (method: safeTransfer, receiver: IERC20), `IController(controller).treasury()` (method: treasury, receiver: IController), `IERC20(token2).balanceOf(address(this))` (method: balanceOf, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['controller', 'keepRewards', 'keepRewardsMax', 'path', 'pool', 'poolId', 'rewards', 'token1', 'token2', 'univ2Router2']
- **External calls**: `IStakingRewards(pool).claimReward(poolId)` (inline cast call IStakingRewards(...).claimReward()), `IERC20(rewards).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IERC20(rewards).safeTransfer(
                IController(controller).treasury(),
                _keepRewards
         ` (SafeERC20 .safeTransfer()), `IController(controller).treasury()` (inline cast call IController(...).treasury()), `IERC20(token1).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IERC20(token1).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IERC20(token2).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IERC20(token1).safeApprove(univ2Router2, 0)` (SafeERC20 .safeApprove()), `IERC20(token1).safeApprove(univ2Router2, _token1)` (SafeERC20 .safeApprove()), `IERC20(token2).safeApprove(univ2Router2, 0)` (SafeERC20 .safeApprove()), `IERC20(token2).safeApprove(univ2Router2, _token2)` (SafeERC20 .safeApprove()), `UniswapRouterV2(univ2Router2).addLiquidity(
                token1,
                token2,
                _token1,
   ` (inline cast call UniswapRouterV2(...).addLiquidity()), `IERC20(token1).transfer(
                IController(controller).treasury(),
                IERC20(token1).balanceOf(ad` (low-level .transfer()), `IController(controller).treasury()` (inline cast call IController(...).treasury()), `IERC20(token1).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IERC20(token2).safeTransfer(
                IController(controller).treasury(),
                IERC20(token2).balanceO` (SafeERC20 .safeTransfer()), `IController(controller).treasury()` (inline cast call IController(...).treasury()), `IERC20(token2).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### MintingFactoryV2.mintBatchEdition

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: mintBatchEdition
- **Line Range**: L93 - L112
- **File**: `DAppSCAN-source/contracts/Coinfabrik-MintingFactoryV2, BaseUpgradableMarketplace & KODAV3UpgradableGatedMarketplace/known-origin-contracts-v3-d592c5f4fa4e0b6fc65a1fce43e302706aedf607/contracts/minter/MintingFactoryV2.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`mintBatchEdition`, lines=`L93 - L112`

#### 2. Function Source Code
```solidity
function mintBatchEdition(
        SaleType _saleType,
        uint16 _editionSize,
        uint128 _startDate,
        uint128 _basePrice,
        uint128 _stepPrice,
        string calldata _uri,
        uint256 _merkleIndex,
        bytes32[] calldata _merkleProof,
        address _deployedRoyaltiesHandler
    ) canMintAgain(_msgSender()) external {
        require(accessControls.isVerifiedArtist(_merkleIndex, _msgSender(), _merkleProof), "Caller must have minter role");

        // Make tokens & edition
        uint256 editionId = koda.mintBatchEdition(_editionSize, _msgSender(), _uri);

        _setupSalesMechanic(editionId, _saleType, _startDate, _basePrice, _stepPrice);
        _recordSuccessfulMint(_msgSender());
        _setupRoyalties(editionId, _deployedRoyaltiesHandler);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['accessControls', 'koda']
- **External calls**: `accessControls.isVerifiedArtist(_merkleIndex, _msgSender(), _merkleProof)` (method: isVerifiedArtist, receiver: accessControls), `koda.mintBatchEdition(_editionSize, _msgSender(), _uri)` (method: mintBatchEdition, receiver: koda)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['accessControls', 'koda']
- **External calls**: `accessControls.isVerifiedArtist(_merkleIndex, _msgSender(), _merkleProof)` (call on contract-typed state var 'accessControls' (type: IKOAccessControlsLookup)), `koda.mintBatchEdition(_editionSize, _msgSender(), _uri)` (call on contract-typed state var 'koda' (type: IKODAV3Minter))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Vault.execute

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: execute
- **Line Range**: L513 - L548
- **File**: `DAppSCAN-source/contracts/Coinspect-Incognito Audit/bridge-eth-4879219669a38d601265582f815596b6775855b6/bridge/contracts/vault.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`execute`, lines=`L513 - L548`

#### 2. Function Source Code
```solidity
function execute(
        address token,
        uint amount,
        address recipientToken,
        address exchangeAddress,
        bytes calldata callData,
        bytes calldata timestamp,
        bytes calldata signData
    ) external payable nonReentrant {
        //verify ower signs data from input
        address verifier = verifySignData(abi.encode(exchangeAddress, callData, timestamp, amount), signData);

        // migrate from preVault
        migrateBalance(verifier, token);
        require(withdrawRequests[verifier][token] >= amount, errorToString(Errors.WITHDRAW_REQUEST_TOKEN_NOT_ENOUGH));

        // update balance of verifier
        totalDepositedToSCAmount[token] = totalDepositedToSCAmount[token].safeSub(amount);
        withdrawRequests[verifier][token] = withdrawRequests[verifier][token].safeSub(amount);

        // define number of eth spent for forwarder.
        uint ethAmount = msg.value;
        if (token == ETH_TOKEN) {
            ethAmount = ethAmount.safeAdd(amount);
        } else {
            // transfer token to exchangeAddress.
            require(IERC20(token).balanceOf(address(this)) >= amount, errorToString(Errors.TOKEN_NOT_ENOUGH));
            IERC20(token).transfer(exchangeAddress, amount);
            require(checkSuccess(), errorToString(Errors.INTERNAL_TX_ERROR));
        }
        uint returnedAmount = callExtFunc(recipientToken, ethAmount, callData, exchangeAddress);

        // update withdrawRequests
        withdrawRequests[verifier][recipientToken] = withdrawRequests[verifier][recipientToken].safeAdd(returnedAmount);
        totalDepositedToSCAmount[recipientToken] = totalDepositedToSCAmount[recipientToken].safeAdd(returnedAmount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['ETH_TOKEN', 'totalDepositedToSCAmount', 'withdrawRequests']
- **External calls**: `IERC20(token).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IERC20(token).transfer(exchangeAddress, amount)` (method: transfer, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['ETH_TOKEN', 'totalDepositedToSCAmount', 'withdrawRequests']
- **External calls**: `IERC20(token).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IERC20(token).transfer(exchangeAddress, amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### CDEXStakingPool.stake

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: stake
- **Line Range**: L362 - L391
- **File**: `DAppSCAN-source/contracts/Hacken-Codex on Althash/Codex-Rewards-Platform-d364d0ef9258dd468f8202a352c58724d6b65638/contracts/CDEX_rewards.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`stake`, lines=`L362 - L391`

#### 2. Function Source Code
```solidity
function stake(uint256 amount)
        external
        nonReentrant
        notPaused
        updateReward(msg.sender)
    {
        require(amount > 0);
        /// Increments the total staked balance
        _totalSupply = _totalSupply.add(amount);
        
        if(_balances[msg.sender] == 0) {
            /// Increments the totalMembers if the sending address didn't have any previous balance
            totalMembers += 1;
            /// Adds the user address to the ranking tree
            CDEXRanking.insert(amount, msg.sender);
        } else {
            /// Removes the user address from its current ranking node in the tree
            CDEXRanking.remove(_balances[msg.sender], msg.sender);
            /// Adds it again with the new value
            CDEXRanking.insert(_balances[msg.sender].add(amount), msg.sender);
        }
        /// Increments the sender's staked balance
        _balances[msg.sender] = _balances[msg.sender].add(amount);
        /// Transfer the tokens from the sender's balance into the contract
        /// The amount needs to be previously approved in the token contract
        CDEXToken.transferFrom(msg.sender, address(this), amount);
        /// Emits the event
        emit Staked(msg.sender, amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['CDEXRanking', 'CDEXToken', '_balances', '_totalSupply', 'totalMembers']
- **External calls**: `CDEXRanking.insert(amount, msg.sender)` (method: insert, receiver: CDEXRanking), `CDEXRanking.remove(_balances[msg.sender], msg.sender)` (method: remove, receiver: CDEXRanking), `CDEXRanking.insert(_balances[msg.sender].add(amount), msg.sender)` (method: insert, receiver: CDEXRanking), `CDEXToken.transferFrom(msg.sender, address(this), amount)` (method: transferFrom, receiver: CDEXToken)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['CDEXRanking', 'CDEXToken', '_balances', '_totalSupply', 'totalMembers']
- **External calls**: `CDEXRanking.insert(amount, msg.sender)` (call on contract-typed state var 'CDEXRanking' (type: CDEXRankingContract)), `CDEXRanking.remove(_balances[msg.sender], msg.sender)` (call on contract-typed state var 'CDEXRanking' (type: CDEXRankingContract)), `CDEXRanking.insert(_balances[msg.sender].add(amount), msg.sender)` (call on contract-typed state var 'CDEXRanking' (type: CDEXRankingContract)), `CDEXToken.transferFrom(msg.sender, address(this), amount)` (call on contract-typed state var 'CDEXToken' (type: CDEXTokenContract))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### CDEXStakingPool.withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: withdraw
- **Line Range**: L395 - L420
- **File**: `DAppSCAN-source/contracts/Hacken-Codex on Althash/Codex-Rewards-Platform-d364d0ef9258dd468f8202a352c58724d6b65638/contracts/CDEX_rewards.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`withdraw`, lines=`L395 - L420`

#### 2. Function Source Code
```solidity
function withdraw(uint256 amount)
        public
        nonReentrant
        updateReward(msg.sender)
    {
        require(amount > 0);
        /// Decrements the total staked balance
        _totalSupply = _totalSupply.sub(amount);
        /// Removes the user address from its current ranking node in the tree
        CDEXRanking.remove(_balances[msg.sender], msg.sender);
        /// Decrements the sender's staked balance
        _balances[msg.sender] = _balances[msg.sender].sub(amount);
        /// If the balance is zero after decremented, decrements the totalMembers
        if(_balances[msg.sender] == 0) {
            totalMembers -= 1;
        } else {
            /// If not, adds the user address back into the ranking tree with the new balance
            CDEXRanking.insert(_balances[msg.sender], msg.sender);
        }
        /// Transfers the tokens into the sender's address
        // SWC-104-Unchecked Call Return Value: L418
        CDEXToken.transfer(msg.sender, amount);
        /// Emits the event
        emit Withdrawn(msg.sender, amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['CDEXRanking', 'CDEXToken', '_balances', '_totalSupply', 'totalMembers']
- **External calls**: `CDEXRanking.remove(_balances[msg.sender], msg.sender)` (method: remove, receiver: CDEXRanking), `CDEXRanking.insert(_balances[msg.sender], msg.sender)` (method: insert, receiver: CDEXRanking), `CDEXToken.transfer(msg.sender, amount)` (method: transfer, receiver: CDEXToken)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['CDEXRanking', 'CDEXToken', '_balances', '_totalSupply', 'totalMembers']
- **External calls**: `CDEXRanking.remove(_balances[msg.sender], msg.sender)` (call on contract-typed state var 'CDEXRanking' (type: CDEXRankingContract)), `CDEXRanking.insert(_balances[msg.sender], msg.sender)` (call on contract-typed state var 'CDEXRanking' (type: CDEXRankingContract)), `CDEXToken.transfer(msg.sender, amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### CDEXStakingPool.depositTokens

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: depositTokens
- **Line Range**: L486 - L498
- **File**: `DAppSCAN-source/contracts/Hacken-Codex on Althash/Codex-Rewards-Platform-d364d0ef9258dd468f8202a352c58724d6b65638/contracts/CDEX_rewards.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`depositTokens`, lines=`L486 - L498`

#### 2. Function Source Code
```solidity
function depositTokens(uint256 amount) public onlyOwner {
        /// Adding the decimal places to the amount
        amount = amount.mul(1e8);
        /// Calculating the total loyalty bonus percentage from the total
        depositedLoyaltyBonus = depositedLoyaltyBonus.add(amount.mul(loyaltyBonusTotal).div(10000));
        /// Increasing the total deposited tokens with the amount
        depositedRewardTokens = depositedRewardTokens.add(amount);
        /// Transferring the whole amount to the contract
        CDEXToken.transferFrom(owner, address(this), amount);
        /// Emits the event
        emit RewardsDeposited(owner, address(this), amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['CDEXToken', 'depositedLoyaltyBonus', 'depositedRewardTokens', 'loyaltyBonusTotal', 'owner']
- **External calls**: `CDEXToken.transferFrom(owner, address(this), amount)` (method: transferFrom, receiver: CDEXToken)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['CDEXToken', 'depositedLoyaltyBonus', 'depositedRewardTokens', 'loyaltyBonusTotal', 'owner']
- **External calls**: `CDEXToken.transferFrom(owner, address(this), amount)` (call on contract-typed state var 'CDEXToken' (type: CDEXTokenContract))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### HyksosCyberkongz.depositErc20

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: depositErc20
- **Line Range**: L39-46
- **File**: `DAppSCAN-source/contracts/Hacken-Hyksos/hyksos-contracts-audit/HyksosCyberkongz.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`depositErc20`, lines=`L39-46`

#### 2. Function Source Code
```solidity
function depositErc20(uint256 _amount) external override {
        require(_amount >= MIN_DEPOSIT, "Deposit amount too small.");
        erc20BalanceMap[msg.sender] += _amount;
        pushDeposit(_amount, msg.sender);
        totalErc20Balance += _amount;
        require(erc20.transferFrom(msg.sender, address(this), _amount));
        emit Erc20Deposit(msg.sender, _amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['MIN_DEPOSIT', 'erc20', 'erc20BalanceMap', 'totalErc20Balance']
- **External calls**: `erc20.transferFrom(msg.sender, address(this), _amount)` (method: transferFrom, receiver: erc20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['MIN_DEPOSIT', 'erc20', 'erc20BalanceMap', 'totalErc20Balance']
- **External calls**: `erc20.transferFrom(msg.sender, address(this), _amount)` (call on contract-typed state var 'erc20' (type: IBananas))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### PowerBombAvaxCurve.claimReward

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: claimReward
- **Line Range**: L269-293
- **File**: `DAppSCAN-source/contracts/Hacken-Powerbomb-V1/powerbomb-lite-0f86ff1eecdd723be733a9b33ff4ffa3bbdadcee/hardhat/contracts/PowerBombAvaxCurve.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`claimReward`, lines=`L269-293`

#### 2. Function Source Code
```solidity
function claimReward(address account) public virtual {
        _harvest(false);

        User storage user = userInfo[account];
        if (user.lpTokenBalance > 0) {
            // Calculate user reward
            uint ibRewardTokenAmt = (user.lpTokenBalance * accRewardPerlpToken / 1e36) - user.rewardStartAt;
            if (ibRewardTokenAmt > 0) {
                user.rewardStartAt += ibRewardTokenAmt;

                // Withdraw ibRewardToken to rewardToken
                lendingPool.withdraw(address(rewardToken), ibRewardTokenAmt, address(this));

                // Update lastIbRewardTokenAmt
                lastIbRewardTokenAmt -= ibRewardTokenAmt;

                // Transfer rewardToken to user
                uint rewardTokenAmt = rewardToken.balanceOf(address(this));
                rewardToken.safeTransfer(account, rewardTokenAmt);
                userAccReward[account] += rewardTokenAmt;

                emit ClaimReward(account, ibRewardTokenAmt, rewardTokenAmt);
            }
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['accRewardPerlpToken', 'lastIbRewardTokenAmt', 'lendingPool', 'rewardToken', 'userAccReward', 'userInfo']
- **External calls**: `lendingPool.withdraw(address(rewardToken), ibRewardTokenAmt, address(this))` (method: withdraw, receiver: lendingPool), `rewardToken.balanceOf(address(this))` (method: balanceOf, receiver: rewardToken), `rewardToken.safeTransfer(account, rewardTokenAmt)` (method: safeTransfer, receiver: rewardToken)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['accRewardPerlpToken', 'lastIbRewardTokenAmt', 'lendingPool', 'rewardToken', 'userAccReward', 'userInfo']
- **External calls**: `lendingPool.withdraw(address(rewardToken), ibRewardTokenAmt, address(this))` (call on contract-typed state var 'lendingPool' (type: ILendingPool)), `rewardToken.balanceOf(address(this))` (call on contract-typed state var 'rewardToken' (type: IERC20Upgradeable)), `rewardToken.safeTransfer(account, rewardTokenAmt)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StakingPool.ownerSetPoolRewards

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: ownerSetPoolRewards
- **Line Range**: L132
- **File**: `DAppSCAN-source/contracts/Hacken-TrustSwap-V1/code/StakingPool.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`ownerSetPoolRewards`, lines=`L132`

#### 2. Function Source Code
```solidity
function ownerSetPoolRewards(uint256 _rewardAmount) external onlyOwner {
        require(poolStartTime == 0, "Pool rewards already set");
        require(_rewardAmount > 0, "Cannot create pool with zero amount");
        
        //set total rewards value
        totalRewards = _rewardAmount;
        
        poolStartTime = now;
        poolEndTime = now + poolDuration;
        
        //transfer tokens to contract
        // SWC-104-Unchecked Call Return Value: L132
        rewardToken.transferFrom(msg.sender, this, _rewardAmount);
        emit OwnerSetReward(_rewardAmount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolDuration', 'poolEndTime', 'poolStartTime', 'rewardToken', 'totalRewards']
- **External calls**: `rewardToken.transferFrom(msg.sender, this, _rewardAmount)` (method: transferFrom, receiver: rewardToken)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['poolDuration', 'poolEndTime', 'poolStartTime', 'rewardToken', 'totalRewards']
- **External calls**: `rewardToken.transferFrom(msg.sender, this, _rewardAmount)` (call on contract-typed state var 'rewardToken' (type: Ierc20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### LenderPool._swapExactTokens

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: _swapExactTokens
- **Line Range**: L375-L391
- **File**: `DAppSCAN-source/contracts/ImmuneBytes-PolyTrade-Audit Report(Lender Portal)/lender-portal-contracts-dev/contracts/LenderPool.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`_swapExactTokens`, lines=`L375-L391`

#### 2. Function Source Code
```solidity
function _swapExactTokens(
        address lender,
        uint roundId,
        uint16 rewardAPY,
        uint amountOutMin
    ) private returns (uint) {
        uint amountStable = _calculateRewards(lender, roundId, rewardAPY);
        uint amountTrade = router.swapExactTokensForTokens(
            amountStable,
            amountOutMin,
            _getPath(),
            lender,
            block.timestamp
        )[2];
        emit Swapped(amountStable, amountTrade);
        return amountTrade;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['router']
- **External calls**: `router.swapExactTokensForTokens(
            amountStable,
            amountOutMin,
            _getPath(),
           ` (method: swapExactTokensForTokens, receiver: router)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['router']
- **External calls**: `router.swapExactTokensForTokens(
            amountStable,
            amountOutMin,
            _getPath(),
           ` (call on contract-typed state var 'router' (type: IUniswapV2Router))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### PancakeByalanLP.harvest

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: harvest
- **Line Range**: L1342
- **File**: `DAppSCAN-source/contracts/Inspex-AutoCompound/auto-compound-v2-92626a1dcfc55a28afdf4f996d600fe8bbfd6efd/PancakeByalanLP.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`harvest`, lines=`L1342`

#### 2. Function Source Code
```solidity
function harvest() external override whenNotPaused onlyEOA onlyHarvester gasThrottle {
        IMasterChef(MASTERCHEF).deposit(pid, 0);
        chargeFees();
        addLiquidity();
        deposit();

        emit Harvest(msg.sender);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['MASTERCHEF', 'pid']
- **External calls**: `IMasterChef(MASTERCHEF).deposit(pid, 0)` (method: deposit, receiver: IMasterChef)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['MASTERCHEF', 'pid']
- **External calls**: `IMasterChef(MASTERCHEF).deposit(pid, 0)` (inline cast call IMasterChef(...).deposit())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StrategyWardenLP.harvest

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: harvest
- **Line Range**: L129-L136
- **File**: `DAppSCAN-source/contracts/Inspex-Vault/aleswap-vault-efd3f777b2e9aaa2c635d3d0f463f1884e998112/contracts/strategies/Warden/StrategyWardenLP.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`harvest`, lines=`L129-L136`

#### 2. Function Source Code
```solidity
function harvest() external whenNotPaused onlyEOA {
        IMasterChef(masterchef).deposit(poolId, 0);
        chargeFees();
        addLiquidity();
        deposit();

        emit StratHarvest(msg.sender);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['masterchef', 'poolId']
- **External calls**: `IMasterChef(masterchef).deposit(poolId, 0)` (method: deposit, receiver: IMasterChef)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['masterchef', 'poolId']
- **External calls**: `IMasterChef(masterchef).deposit(poolId, 0)` (inline cast call IMasterChef(...).deposit())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### SpookyswapWorker.reinvest

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: reinvest
- **Line Range**: L139
- **File**: `DAppSCAN-source/contracts/Inspex-FairLaunch, Token, Vault & Workers/Meow-Finance-4a4f13efaf5e5fbed74c0ed23b665751e655d715/contracts/protocol/workers/SpookyswapWorker.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`reinvest`, lines=`L139`

#### 2. Function Source Code
```solidity
function reinvest() external override onlyEOA onlyReinvestor nonReentrant {
    // 1. Approve tokens
    boo.safeApprove(address(router), uint256(-1));
    address(lpToken).safeApprove(address(masterChef), uint256(-1));
    // 2. Withdraw all the rewards.
    masterChef.withdraw(pid, 0);
    uint256 reward = boo.balanceOf(address(this));
    if (reward == 0) return;
    // 3. Send the reward bounty to the caller.
    uint256 bounty = reward.mul(reinvestBountyBps) / 10000;
    if (bounty > 0) boo.safeTransfer(msg.sender, bounty);
    // 4. Convert all the remaining rewards to BaseToken via Native for liquidity.
    address[] memory path;
    if (baseToken != boo) {
      if (baseToken == wNative) {
        path = new address[](2);
        path[0] = address(boo);
        path[1] = address(wNative);
      } else {
        path = new address[](3);
        path[0] = address(boo);
        path[1] = address(wNative);
        path[2] = address(baseToken);
      }
    }
    router.swapExactTokensForTokens(reward.sub(bounty), 0, path, address(this), now);

    // 5. Use add Token strategy to convert all BaseToken to LP tokens.
    baseToken.safeTransfer(address(addStrat), baseToken.myBalance());
    addStrat.execute(address(0), 0, abi.encode(0));
    // 6. Mint more LP tokens and stake them for more rewards.
    masterChef.deposit(pid, lpToken.balanceOf(address(this)));
    // 7. Reset approve
    boo.safeApprove(address(router), 0);
    address(lpToken).safeApprove(address(masterChef), 0);
    emit Reinvest(msg.sender, reward, bounty);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['addStrat', 'baseToken', 'boo', 'lpToken', 'masterChef', 'pid', 'reinvestBountyBps', 'router', 'wNative']
- **External calls**: `boo.safeApprove(address(router), uint256(-1))` (method: safeApprove, receiver: boo), `address(lpToken).safeApprove(address(masterChef), uint256(-1))` (method: safeApprove, receiver: (complex)), `masterChef.withdraw(pid, 0)` (method: withdraw, receiver: masterChef), `boo.balanceOf(address(this))` (method: balanceOf, receiver: boo), `boo.safeTransfer(msg.sender, bounty)` (method: safeTransfer, receiver: boo), `router.swapExactTokensForTokens(reward.sub(bounty), 0, path, address(this), now)` (method: swapExactTokensForTokens, receiver: router), `baseToken.safeTransfer(address(addStrat), baseToken.myBalance())` (method: safeTransfer, receiver: baseToken), `addStrat.execute(address(0), 0, abi.encode(0))` (method: execute, receiver: addStrat), `masterChef.deposit(pid, lpToken.balanceOf(address(this)))` (method: deposit, receiver: masterChef), `lpToken.balanceOf(address(this))` (method: balanceOf, receiver: lpToken), `boo.safeApprove(address(router), 0)` (method: safeApprove, receiver: boo), `address(lpToken).safeApprove(address(masterChef), 0)` (method: safeApprove, receiver: (complex))
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['addStrat', 'baseToken', 'boo', 'lpToken', 'masterChef', 'pid', 'reinvestBountyBps', 'router', 'wNative']
- **External calls**: `boo.safeApprove(address(router), uint256(-1))` (SafeERC20 .safeApprove()), `address(lpToken).safeApprove(address(masterChef), uint256(-1))` (SafeERC20 .safeApprove()), `masterChef.withdraw(pid, 0)` (call on contract-typed state var 'masterChef' (type: ISpookyMasterChef)), `boo.balanceOf(address(this))` (known ERC-like method .balanceOf() on 'boo'), `boo.safeTransfer(msg.sender, bounty)` (SafeERC20 .safeTransfer()), `router.swapExactTokensForTokens(reward.sub(bounty), 0, path, address(this), now)` (call on contract-typed state var 'router' (type: IUniswapV2Router02)), `baseToken.safeTransfer(address(addStrat), baseToken.myBalance())` (SafeERC20 .safeTransfer()), `addStrat.execute(address(0), 0, abi.encode(0))` (call on contract-typed state var 'addStrat' (type: IStrategy)), `masterChef.deposit(pid, lpToken.balanceOf(address(this)))` (call on contract-typed state var 'masterChef' (type: ISpookyMasterChef)), `lpToken.balanceOf(address(this))` (call on contract-typed state var 'lpToken' (type: IUniswapV2Pair)), `boo.safeApprove(address(router), 0)` (SafeERC20 .safeApprove()), `address(lpToken).safeApprove(address(masterChef), 0)` (SafeERC20 .safeApprove())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### PancakeswapV2Worker02.work

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: work
- **Line Range**: L218
- **File**: `DAppSCAN-source/contracts/Inspex-Optimized Worker/bsc-alpaca-contract-1aee2ceec77e3fd3162b74858c846cdc5692928d/contracts/6/protocol/workers/pcs/PancakeswapV2Worker02.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`work`, lines=`L218`

#### 2. Function Source Code
```solidity
function work(
    uint256 id,
    address user,
    uint256 debt,
    bytes calldata data
  ) external override onlyOperator nonReentrant {
    // 1. If a treasury bounty or an account have a default value (0 bps or address(0)), use reinvestBountyBps and default treasury address instead
    if (treasuryBountyBps == 0) treasuryBountyBps = reinvestBountyBps;
    if (treasuryAccount == address(0)) treasuryAccount = address(0xC44f82b07Ab3E691F826951a6E335E1bC1bB0B51);
    // 2. Reinvest and send portion of reward to treasury account.
    _reinvest(treasuryAccount, treasuryBountyBps, baseToken.myBalance());
    // 3. Convert this position back to LP tokens.
    _removeShare(id);
    // 4. Perform the worker strategy; sending LP tokens + BaseToken; expecting LP tokens + BaseToken.
    (address strat, bytes memory ext) = abi.decode(data, (address, bytes));
    require(okStrats[strat], "PancakeswapWorker::work:: unapproved work strategy");
    require(
      lpToken.transfer(strat, lpToken.balanceOf(address(this))),
      "PancakeswapWorker::work:: unable to transfer lp to strat"
    );
    baseToken.safeTransfer(strat, baseToken.myBalance());
    IStrategy(strat).execute(user, debt, ext);
    // 5. Add LP tokens back to the farming pool.
    _addShare(id);
    // 6. Return any remaining BaseToken back to the operator.
    baseToken.safeTransfer(msg.sender, baseToken.myBalance());
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['baseToken', 'lpToken', 'okStrats', 'reinvestBountyBps', 'treasuryAccount', 'treasuryBountyBps']
- **External calls**: `lpToken.transfer(strat, lpToken.balanceOf(address(this)))` (method: transfer, receiver: lpToken), `lpToken.balanceOf(address(this))` (method: balanceOf, receiver: lpToken), `baseToken.safeTransfer(strat, baseToken.myBalance())` (method: safeTransfer, receiver: baseToken), `IStrategy(strat).execute(user, debt, ext)` (method: execute, receiver: IStrategy), `baseToken.safeTransfer(msg.sender, baseToken.myBalance())` (method: safeTransfer, receiver: baseToken)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['baseToken', 'lpToken', 'okStrats', 'reinvestBountyBps', 'treasuryAccount', 'treasuryBountyBps']
- **External calls**: `lpToken.transfer(strat, lpToken.balanceOf(address(this)))` (low-level .transfer()), `lpToken.balanceOf(address(this))` (call on contract-typed state var 'lpToken' (type: IPancakePair)), `baseToken.safeTransfer(strat, baseToken.myBalance())` (SafeERC20 .safeTransfer()), `IStrategy(strat).execute(user, debt, ext)` (inline cast call IStrategy(...).execute()), `baseToken.safeTransfer(msg.sender, baseToken.myBalance())` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### SpookySwapStrategyAddBaseTokenOnly.execute

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: execute
- **Line Range**: L59-L105
- **File**: `DAppSCAN-source/contracts/Inspex-SpookySwap Integration & Fantom Expansion/bsc-alpaca-contract-4553a34a6dcfcfbf7aebc693bb5c5c6074c73129/contracts/6/protocol/strategies/spookyswap/SpookySwapStrategyAddBaseTokenOnly.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`execute`, lines=`L59-L105`

#### 2. Function Source Code
```solidity
function execute(
    address, /* user */
    uint256, /* debt */
    bytes calldata data
  ) external override onlyWhitelistedWorkers nonReentrant {
    // 1. Find out what farming token we are dealing with and min additional LP tokens.
    uint256 minLPAmount = abi.decode(data, (uint256));
    IWorker03 worker = IWorker03(msg.sender);
    address baseToken = worker.baseToken();
    address farmingToken = worker.farmingToken();
    ISwapPairLike lpToken = worker.lpToken();
    // 2. Approve router to do their stuffs
    baseToken.safeApprove(address(router), uint256(-1));
    farmingToken.safeApprove(address(router), uint256(-1));
    // 3. Compute the optimal amount of baseToken to be converted to farmingToken.
    uint256 balance = baseToken.myBalance();
    (uint256 r0, uint256 r1, ) = lpToken.getReserves();
    uint256 rIn = lpToken.token0() == baseToken ? r0 : r1;
    // find how many baseToken need to be converted to farmingToken
    // Constants come from
    // 2-f = 2-0.002 = 1.998
    // 4(1-f) = 4*998*1000 = 3992000, where f = 0.0020 and 1,000 is a way to avoid floating point
    // 1998^2 = 3992004
    // 998*2 = 1996
    uint256 aIn = AlpacaMath.sqrt(rIn.mul(balance.mul(3992000).add(rIn.mul(3992004)))).sub(rIn.mul(1998)) / 1996;
    // 4. Convert that portion of baseToken to farmingToken.
    address[] memory path = new address[](2);
    path[0] = baseToken;
    path[1] = farmingToken;
    router.swapExactTokensForTokens(aIn, 0, path, address(this), now);
    // 5. Mint more LP tokens and return all LP tokens to the sender.
    (, , uint256 moreLPAmount) = router.addLiquidity(
      baseToken,
      farmingToken,
      baseToken.myBalance(),
      farmingToken.myBalance(),
      0,
      0,
      address(this),
      now
    );
    require(moreLPAmount >= minLPAmount, "insufficient LP tokens received");
    address(lpToken).safeTransfer(msg.sender, lpToken.balanceOf(address(this)));
    // 6. Reset approval for safety reason
    baseToken.safeApprove(address(router), 0);
    farmingToken.safeApprove(address(router), 0);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['router']
- **External calls**: `worker.baseToken()` (method: baseToken, receiver: worker), `worker.farmingToken()` (method: farmingToken, receiver: worker), `worker.lpToken()` (method: lpToken, receiver: worker), `baseToken.safeApprove(address(router), uint256(-1))` (method: safeApprove, receiver: baseToken), `farmingToken.safeApprove(address(router), uint256(-1))` (method: safeApprove, receiver: farmingToken), `lpToken.getReserves()` (method: getReserves, receiver: lpToken), `lpToken.token0()` (method: token0, receiver: lpToken), `AlpacaMath.sqrt(rIn.mul(balance.mul(3992000).add(rIn.mul(3992004)))).sub(rIn.mul(1998))` (method: sub, receiver: AlpacaMath), `AlpacaMath.sqrt(rIn.mul(balance.mul(3992000).add(rIn.mul(3992004))))` (method: sqrt, receiver: AlpacaMath), `router.swapExactTokensForTokens(aIn, 0, path, address(this), now)` (method: swapExactTokensForTokens, receiver: router), `router.addLiquidity(
      baseToken,
      farmingToken,
      baseToken.myBalance(),
      farmingToken.myBalance(),
 ` (method: addLiquidity, receiver: router), `address(lpToken).safeTransfer(msg.sender, lpToken.balanceOf(address(this)))` (method: safeTransfer, receiver: (complex)), `lpToken.balanceOf(address(this))` (method: balanceOf, receiver: lpToken), `baseToken.safeApprove(address(router), 0)` (method: safeApprove, receiver: baseToken), `farmingToken.safeApprove(address(router), 0)` (method: safeApprove, receiver: farmingToken)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['router']
- **External calls**: `worker.baseToken()` (call on contract-typed local var 'worker' (type: IWorker03)), `worker.farmingToken()` (call on contract-typed local var 'worker' (type: IWorker03)), `worker.lpToken()` (call on contract-typed local var 'worker' (type: IWorker03)), `baseToken.safeApprove(address(router), uint256(-1))` (SafeERC20 .safeApprove()), `farmingToken.safeApprove(address(router), uint256(-1))` (SafeERC20 .safeApprove()), `lpToken.getReserves()` (call on contract-typed local var 'lpToken' (type: ISwapPairLike)), `lpToken.token0()` (call on contract-typed local var 'lpToken' (type: ISwapPairLike)), `AlpacaMath.sqrt(rIn.mul(balance.mul(3992000).add(rIn.mul(3992004)))).sub(rIn.mul(1998))` (inline cast call AlpacaMath(...).sub()), `AlpacaMath.sqrt(rIn.mul(balance.mul(3992000).add(rIn.mul(3992004))))` (call on interface/contract type 'AlpacaMath'), `router.swapExactTokensForTokens(aIn, 0, path, address(this), now)` (call on contract-typed state var 'router' (type: ISwapRouter02Like)), `router.addLiquidity(
      baseToken,
      farmingToken,
      baseToken.myBalance(),
      farmingToken.myBalance(),
 ` (call on contract-typed state var 'router' (type: ISwapRouter02Like)), `address(lpToken).safeTransfer(msg.sender, lpToken.balanceOf(address(this)))` (SafeERC20 .safeTransfer()), `lpToken.balanceOf(address(this))` (call on contract-typed local var 'lpToken' (type: ISwapPairLike)), `baseToken.safeApprove(address(router), 0)` (SafeERC20 .safeApprove()), `farmingToken.safeApprove(address(router), 0)` (SafeERC20 .safeApprove())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### SpookyWorker03._reinvest

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: _reinvest
- **Line Range**: L208-L246
- **File**: `DAppSCAN-source/contracts/Inspex-SpookySwap Integration & Fantom Expansion/bsc-alpaca-contract-4553a34a6dcfcfbf7aebc693bb5c5c6074c73129/contracts/6/protocol/workers/spookyswap/SpookyWorker03.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`_reinvest`, lines=`L208-L246`

#### 2. Function Source Code
```solidity
function _reinvest(
    address _treasuryAccount,
    uint256 _treasuryBountyBps,
    uint256 _callerBalance,
    uint256 _reinvestThreshold
  ) internal {
    // 1. Withdraw all the rewards. Return if reward <= _reinvestThershold.
    spookyMasterChef.withdraw(pid, 0);
    uint256 reward = boo.balanceOf(address(this));
    if (reward <= _reinvestThreshold) return;

    // 2. Approve tokens
    boo.safeApprove(address(router), uint256(-1));
    address(lpToken).safeApprove(address(spookyMasterChef), uint256(-1));

    // 3. Send the reward bounty to the _treasuryAccount.
    uint256 bounty = reward.mul(_treasuryBountyBps) / 10000;
    if (bounty > 0) {
      uint256 beneficialVaultBounty = bounty.mul(beneficialVaultBountyBps) / 10000;
      if (beneficialVaultBounty > 0) _rewardToBeneficialVault(beneficialVaultBounty, _callerBalance);
      boo.safeTransfer(_treasuryAccount, bounty.sub(beneficialVaultBounty));
    }

    // 4. Convert all the remaining rewards to BTOKEN.
    router.swapExactTokensForTokens(reward.sub(bounty), 0, getReinvestPath(), address(this), now);

    // 5. Use add Token strategy to convert all BaseToken without both caller balance and buyback amount to LP tokens.
    baseToken.safeTransfer(address(addStrat), actualBaseTokenBalance().sub(_callerBalance));
    addStrat.execute(address(0), 0, abi.encode(0));

    // 6. Stake LPs for more rewards
    spookyMasterChef.deposit(pid, lpToken.balanceOf(address(this)));

    // 7. Reset approvals
    boo.safeApprove(address(router), 0);
    address(lpToken).safeApprove(address(spookyMasterChef), 0);

    emit Reinvest(_treasuryAccount, reward, bounty);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['addStrat', 'baseToken', 'beneficialVaultBountyBps', 'boo', 'lpToken', 'pid', 'router', 'spookyMasterChef']
- **External calls**: `spookyMasterChef.withdraw(pid, 0)` (method: withdraw, receiver: spookyMasterChef), `boo.balanceOf(address(this))` (method: balanceOf, receiver: boo), `boo.safeApprove(address(router), uint256(-1))` (method: safeApprove, receiver: boo), `address(lpToken).safeApprove(address(spookyMasterChef), uint256(-1))` (method: safeApprove, receiver: (complex)), `boo.safeTransfer(_treasuryAccount, bounty.sub(beneficialVaultBounty))` (method: safeTransfer, receiver: boo), `router.swapExactTokensForTokens(reward.sub(bounty), 0, getReinvestPath(), address(this), now)` (method: swapExactTokensForTokens, receiver: router), `baseToken.safeTransfer(address(addStrat), actualBaseTokenBalance().sub(_callerBalance))` (method: safeTransfer, receiver: baseToken), `addStrat.execute(address(0), 0, abi.encode(0))` (method: execute, receiver: addStrat), `spookyMasterChef.deposit(pid, lpToken.balanceOf(address(this)))` (method: deposit, receiver: spookyMasterChef), `lpToken.balanceOf(address(this))` (method: balanceOf, receiver: lpToken), `boo.safeApprove(address(router), 0)` (method: safeApprove, receiver: boo), `address(lpToken).safeApprove(address(spookyMasterChef), 0)` (method: safeApprove, receiver: (complex))
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['addStrat', 'baseToken', 'beneficialVaultBountyBps', 'boo', 'lpToken', 'pid', 'router', 'spookyMasterChef']
- **External calls**: `spookyMasterChef.withdraw(pid, 0)` (call on contract-typed state var 'spookyMasterChef' (type: ISpookyMasterChef)), `boo.balanceOf(address(this))` (known ERC-like method .balanceOf() on 'boo'), `boo.safeApprove(address(router), uint256(-1))` (SafeERC20 .safeApprove()), `address(lpToken).safeApprove(address(spookyMasterChef), uint256(-1))` (SafeERC20 .safeApprove()), `boo.safeTransfer(_treasuryAccount, bounty.sub(beneficialVaultBounty))` (SafeERC20 .safeTransfer()), `router.swapExactTokensForTokens(reward.sub(bounty), 0, getReinvestPath(), address(this), now)` (call on contract-typed state var 'router' (type: ISwapRouter02Like)), `baseToken.safeTransfer(address(addStrat), actualBaseTokenBalance().sub(_callerBalance))` (SafeERC20 .safeTransfer()), `addStrat.execute(address(0), 0, abi.encode(0))` (call on contract-typed state var 'addStrat' (type: IStrategy)), `spookyMasterChef.deposit(pid, lpToken.balanceOf(address(this)))` (call on contract-typed state var 'spookyMasterChef' (type: ISpookyMasterChef)), `lpToken.balanceOf(address(this))` (call on contract-typed state var 'lpToken' (type: ISwapPairLike)), `boo.safeApprove(address(router), 0)` (SafeERC20 .safeApprove()), `address(lpToken).safeApprove(address(spookyMasterChef), 0)` (SafeERC20 .safeApprove())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StratAlpaca.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: deposit
- **Line Range**: L191-L205
- **File**: `DAppSCAN-source/contracts/Inspex-StakingPool, Vault, Strategy & VotingEscrow/scientix-contract-main/contracts/vaults/StratAlpaca.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`deposit`, lines=`L191-L205`

#### 2. Function Source Code
```solidity
function deposit(uint256 _wantAmt)
        external
        override
        onlyVault
        nonReentrantAndUnpaused
    {
        IERC20(wantToken).safeTransferFrom(
            address(msg.sender),
            address(this),
            _wantAmt
        );

        alpacaVault.deposit(_wantAmt);
        fairLaunch.deposit(address(this), poolId, alpacaVault.balanceOf(address(this)));
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['alpacaVault', 'fairLaunch', 'poolId', 'wantToken']
- **External calls**: `IERC20(wantToken).safeTransferFrom(
            address(msg.sender),
            address(this),
            _wantAmt
   ` (method: safeTransferFrom, receiver: IERC20), `alpacaVault.deposit(_wantAmt)` (method: deposit, receiver: alpacaVault), `fairLaunch.deposit(address(this), poolId, alpacaVault.balanceOf(address(this)))` (method: deposit, receiver: fairLaunch), `alpacaVault.balanceOf(address(this))` (method: balanceOf, receiver: alpacaVault)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['alpacaVault', 'fairLaunch', 'poolId', 'wantToken']
- **External calls**: `IERC20(wantToken).safeTransferFrom(
            address(msg.sender),
            address(this),
            _wantAmt
   ` (SafeERC20 .safeTransferFrom()), `alpacaVault.deposit(_wantAmt)` (call on contract-typed state var 'alpacaVault' (type: IAlpacaVault)), `fairLaunch.deposit(address(this), poolId, alpacaVault.balanceOf(address(this)))` (call on contract-typed state var 'fairLaunch' (type: IFairLaunch)), `alpacaVault.balanceOf(address(this))` (call on contract-typed state var 'alpacaVault' (type: IAlpacaVault))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### WUSDMaster.stake

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: stake
- **Line Range**: L703-728
- **File**: `DAppSCAN-source/contracts/Inspex-WUSDMaster/WUSD-91c541c2f1c0ac781ddcfb2be6a62555a5e1e8d1/WUSDMaster.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`stake`, lines=`L703-728`

#### 2. Function Source Code
```solidity
function stake(uint256 amount) external nonReentrant {
        require(amount > 0, 'amount cant be zero');
        require(wusdClaimAmount[msg.sender] == 0, 'you have to claim first');
        require(amount <= maxStakeAmount, 'amount too high');
        
        usdt.safeTransferFrom(msg.sender, address(this), amount);
        if(feePermille > 0) {
            uint256 feeAmount = amount * feePermille / 1000;
            usdt.safeTransfer(treasury, feeAmount);
            amount = amount - feeAmount;
        }
        uint256 wexAmount = amount * wexPermille / 1000;
        usdt.approve(address(wswapRouter), wexAmount);
        wswapRouter.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            wexAmount,
            0,
            swapPath,
            address(this),
            block.timestamp
        );
        
        wusdClaimAmount[msg.sender] = amount;
        wusdClaimBlock[msg.sender] = block.number;
        
        emit Stake(msg.sender, amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['feePermille', 'maxStakeAmount', 'swapPath', 'treasury', 'usdt', 'wexPermille', 'wswapRouter', 'wusdClaimAmount', 'wusdClaimBlock']
- **External calls**: `usdt.safeTransferFrom(msg.sender, address(this), amount)` (method: safeTransferFrom, receiver: usdt), `usdt.safeTransfer(treasury, feeAmount)` (method: safeTransfer, receiver: usdt), `usdt.approve(address(wswapRouter), wexAmount)` (method: approve, receiver: usdt), `wswapRouter.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            wexAmount,
            0,
            swa` (method: swapExactTokensForTokensSupportingFeeOnTransferTokens, receiver: wswapRouter)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['feePermille', 'maxStakeAmount', 'swapPath', 'treasury', 'usdt', 'wexPermille', 'wswapRouter', 'wusdClaimAmount', 'wusdClaimBlock']
- **External calls**: `usdt.safeTransferFrom(msg.sender, address(this), amount)` (SafeERC20 .safeTransferFrom()), `usdt.safeTransfer(treasury, feeAmount)` (SafeERC20 .safeTransfer()), `usdt.approve(address(wswapRouter), wexAmount)` (call on contract-typed state var 'usdt' (type: IERC20)), `wswapRouter.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            wexAmount,
            0,
            swa` (call on contract-typed state var 'wswapRouter' (type: IWswapRouter))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Wrapper.swap

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: swap
- **Line Range**: L152
- **File**: `DAppSCAN-source/contracts/PeckShield-AirSwap/airswap-protocols-b87d292aaf6e28ede564b7ea28ece39219994607/source/wrapper/contracts/Wrapper.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`swap`, lines=`L152`

#### 2. Function Source Code
```solidity
function swap(
    Types.Order calldata order
  ) external payable notPaused {

    // Ensure msg.sender is sender wallet.
    require(order.sender.wallet == msg.sender,
      "MSG_SENDER_MUST_BE_ORDER_SENDER");

    // Ensure that the signature is present.
    // It will be explicitly checked in Swap.
    require(order.signature.v != 0,
      "SIGNATURE_MUST_BE_SENT");

    // The sender is sending ether that must be wrapped.
    if (order.sender.token == address(wethContract)) {

      // Ensure message value is sender param.
      require(order.sender.param == msg.value,
        "VALUE_MUST_BE_SENT");

      // Wrap (deposit) the ether.
      wethContract.deposit.value(msg.value)();

      // Transfer the WETH from the wrapper to sender.
      wethContract.transfer(order.sender.wallet, order.sender.param);

    } else {

      // Ensure no unexpected ether is sent.
      require(msg.value == 0,
        "VALUE_MUST_BE_ZERO");

    }

    // Perform the swap.
    swapContract.swap(order);

    // The sender is receiving ether that must be unwrapped.
    if (order.signer.token == address(wethContract)) {

      // Transfer from the sender to the wrapper.
      wethContract.transferFrom(order.sender.wallet, address(this), order.signer.param);

      // Unwrap (withdraw) the ether.
      wethContract.withdraw(order.signer.param);

      // Transfer ether to the user.
      // solium-disable-next-line security/no-call-value
      // SWC-104-Unchecked Call Return Value: L152
      msg.sender.call.value(order.signer.param)("");
    }
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['swapContract', 'wethContract']
- **External calls**: `wethContract.deposit.value(msg.value)` (method: value, receiver: wethContract), `wethContract.transfer(order.sender.wallet, order.sender.param)` (method: transfer, receiver: wethContract), `swapContract.swap(order)` (method: swap, receiver: swapContract), `wethContract.transferFrom(order.sender.wallet, address(this), order.signer.param)` (method: transferFrom, receiver: wethContract), `wethContract.withdraw(order.signer.param)` (method: withdraw, receiver: wethContract)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['swapContract', 'wethContract']
- **External calls**: `wethContract.deposit.value(msg.value)` (call on contract-typed state var 'wethContract' (type: IWETH)), `wethContract.transfer(order.sender.wallet, order.sender.param)` (low-level .transfer()), `swapContract.swap(order)` (call on contract-typed state var 'swapContract' (type: ISwap)), `wethContract.transferFrom(order.sender.wallet, address(this), order.signer.param)` (call on contract-typed state var 'wethContract' (type: IWETH)), `wethContract.withdraw(order.signer.param)` (call on contract-typed state var 'wethContract' (type: IWETH))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### D_Swap.Impl_Delivery

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: Impl_Delivery
- **Line Range**: L360-L380
- **File**: `DAppSCAN-source/contracts/PeckShield-Arche/Arche_v1.0_Eros-909f35e0064d636aaf61954a6026fda7b2bade7f/Swap_Factory_Future.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`Impl_Delivery`, lines=`L360-L380`

#### 2. Function Source Code
```solidity
function Impl_Delivery(address user) internal
    {
       
        uint256 head_amount_back=m_Future_Balance_Tail[user];
    
        if(head_amount_back>=1)
        {
            Charging_Transfer_ERC20(m_Token_Head,user,head_amount_back);
        } 
        m_Amount_Head_Deliveryed=m_Amount_Head_Deliveryed.add(head_amount_back);
        m_Total_Future_Balance_Tail=m_Total_Future_Balance_Tail.sub(head_amount_back);
        m_Future_Balance_Tail[user]=0;
        
        uint256 tail_amount_back=0;
        tail_amount_back=m_Future_Balance_Head;
        m_Future_Balance_Head=0;
        Charging_Transfer_ERC20(m_Token_Tail,owner,tail_amount_back);
        m_Amount_Tail_Deliveryed+=tail_amount_back;
        
        D_Swap_Main(m_DSwap_Main_Address).Triger_Claim_For_Delivery( address(this) , user);
    
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['m_Amount_Head_Deliveryed', 'm_Amount_Tail_Deliveryed', 'm_DSwap_Main_Address', 'm_Future_Balance_Head', 'm_Future_Balance_Tail', 'm_Token_Head', 'm_Token_Tail', 'm_Total_Future_Balance_Tail', 'owner']
- **External calls**: `D_Swap_Main(m_DSwap_Main_Address).Triger_Claim_For_Delivery( address(this) , user)` (method: Triger_Claim_For_Delivery, receiver: D_Swap_Main)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['m_Amount_Head_Deliveryed', 'm_Amount_Tail_Deliveryed', 'm_DSwap_Main_Address', 'm_Future_Balance_Head', 'm_Future_Balance_Tail', 'm_Token_Head', 'm_Token_Tail', 'm_Total_Future_Balance_Tail', 'owner']
- **External calls**: `D_Swap_Main(m_DSwap_Main_Address).Triger_Claim_For_Delivery( address(this) , user)` (inline cast call D_Swap_Main(...).Triger_Claim_For_Delivery())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### AToken.borrowFresh

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: borrowFresh
- **Line Range**: L738-L802
- **File**: `DAppSCAN-source/contracts/PeckShield-Atlantis/atlantis-protocol-bsc-766acebba9316eced1c15abf6158b31f470a947f/contracts/AToken.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`borrowFresh`, lines=`L738-L802`

#### 2. Function Source Code
(65 lines, showing first 30 + last 15)
```solidity
function borrowFresh(address payable borrower, uint borrowAmount) internal returns (uint) {
        /* Fail if borrow not allowed */
        uint allowed = comptroller.borrowAllowed(address(this), borrower, borrowAmount);
        if (allowed != 0) {
            return failOpaque(Error.COMPTROLLER_REJECTION, FailureInfo.BORROW_COMPTROLLER_REJECTION, allowed);
        }

        /* Verify market's block number equals current block number */
        if (accrualBlockNumber != getBlockNumber()) {
            return fail(Error.MARKET_NOT_FRESH, FailureInfo.BORROW_FRESHNESS_CHECK);
        }

        /* Fail gracefully if protocol has insufficient underlying cash */
        if (getCashPrior() < borrowAmount) {
            return fail(Error.TOKEN_INSUFFICIENT_CASH, FailureInfo.BORROW_CASH_NOT_AVAILABLE);
        }

        BorrowLocalVars memory vars;

        /*
         * We calculate the new borrower and total borrow balances, failing on overflow:
         *  accountBorrowsNew = accountBorrows + borrowAmount
         *  totalBorrowsNew = totalBorrows + borrowAmount
         */
        (vars.mathErr, vars.accountBorrows) = borrowBalanceStoredInternal(borrower);
        if (vars.mathErr != MathError.NO_ERROR) {
            return failOpaque(Error.MATH_ERROR, FailureInfo.BORROW_ACCUMULATED_BALANCE_CALCULATION_FAILED, uint(vars.mathErr));
        }

        (vars.mathErr, vars.accountBorrowsNew) = addUInt(vars.accountBorrows, borrowAmount);
    // ... truncated ...

        /* We write the previously calculated values into storage */
        accountBorrows[borrower].principal = vars.accountBorrowsNew;
        accountBorrows[borrower].interestIndex = borrowIndex;
        totalBorrows = vars.totalBorrowsNew;

        /* We emit a Borrow event */
        emit Borrow(borrower, borrowAmount, vars.accountBorrowsNew, vars.totalBorrowsNew);

        /* We call the defense hook */
        // unused function
        // comptroller.borrowVerify(address(this), borrower, borrowAmount);

        return uint(Error.NO_ERROR);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['accountBorrows', 'accrualBlockNumber', 'borrowIndex', 'comptroller', 'totalBorrows']
- **External calls**: `comptroller.borrowAllowed(address(this), borrower, borrowAmount)` (method: borrowAllowed, receiver: comptroller)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['accountBorrows', 'accrualBlockNumber', 'borrowIndex', 'comptroller', 'totalBorrows']
- **External calls**: `comptroller.borrowAllowed(address(this), borrower, borrowAmount)` (call on contract-typed state var 'comptroller' (type: ComptrollerInterface))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### RToken.borrowFresh

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: borrowFresh
- **Line Range**: L738-L802
- **File**: `DAppSCAN-source/contracts/PeckShield-Rikkei/rifi-protocol-b33243fb3a218cc195f0727fe1499cb57f5ea0b2/contracts/RToken.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`borrowFresh`, lines=`L738-L802`

#### 2. Function Source Code
(65 lines, showing first 30 + last 15)
```solidity
function borrowFresh(address payable borrower, uint borrowAmount) internal returns (uint) {
        /* Fail if borrow not allowed */
        uint allowed = cointroller.borrowAllowed(address(this), borrower, borrowAmount);
        if (allowed != 0) {
            return failOpaque(Error.COINTROLLER_REJECTION, FailureInfo.BORROW_COINTROLLER_REJECTION, allowed);
        }

        /* Verify market's block number equals current block number */
        if (accrualBlockNumber != getBlockNumber()) {
            return fail(Error.MARKET_NOT_FRESH, FailureInfo.BORROW_FRESHNESS_CHECK);
        }

        /* Fail gracefully if protocol has insufficient underlying cash */
        if (getCashPrior() < borrowAmount) {
            return fail(Error.TOKEN_INSUFFICIENT_CASH, FailureInfo.BORROW_CASH_NOT_AVAILABLE);
        }

        BorrowLocalVars memory vars;

        /*
         * We calculate the new borrower and total borrow balances, failing on overflow:
         *  accountBorrowsNew = accountBorrows + borrowAmount
         *  totalBorrowsNew = totalBorrows + borrowAmount
         */
        (vars.mathErr, vars.accountBorrows) = borrowBalanceStoredInternal(borrower);
        if (vars.mathErr != MathError.NO_ERROR) {
            return failOpaque(Error.MATH_ERROR, FailureInfo.BORROW_ACCUMULATED_BALANCE_CALCULATION_FAILED, uint(vars.mathErr));
        }

        (vars.mathErr, vars.accountBorrowsNew) = addUInt(vars.accountBorrows, borrowAmount);
    // ... truncated ...

        /* We write the previously calculated values into storage */
        accountBorrows[borrower].principal = vars.accountBorrowsNew;
        accountBorrows[borrower].interestIndex = borrowIndex;
        totalBorrows = vars.totalBorrowsNew;

        /* We emit a Borrow event */
        emit Borrow(borrower, borrowAmount, vars.accountBorrowsNew, vars.totalBorrowsNew);

        /* We call the defense hook */
        // unused function
        // cointroller.borrowVerify(address(this), borrower, borrowAmount);

        return uint(Error.NO_ERROR);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['accountBorrows', 'accrualBlockNumber', 'borrowIndex', 'cointroller', 'totalBorrows']
- **External calls**: `cointroller.borrowAllowed(address(this), borrower, borrowAmount)` (method: borrowAllowed, receiver: cointroller)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['accountBorrows', 'accrualBlockNumber', 'borrowIndex', 'cointroller', 'totalBorrows']
- **External calls**: `cointroller.borrowAllowed(address(this), borrower, borrowAmount)` (call on contract-typed state var 'cointroller' (type: CointrollerInterface))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### BufferBNBOptions.create

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: create
- **Line Range**: L142-L189
- **File**: `DAppSCAN-source/contracts/PeckShield-Buffer/code/Buffer-Protocol-1c648bb35feca23bc801ce76aba63ca66af5917e/contracts/Options/BufferBNBOptions.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`create`, lines=`L142-L189`

#### 2. Function Source Code
```solidity
function create(
        uint256 period,
        uint256 amount,
        uint256 strike,
        OptionType optionType,
        address referrer
    ) external payable returns (uint256 optionID) {
        (uint256 totalFee, uint256 settlementFee, uint256 strikeFee, ) = fees(
            period,
            amount,
            strike,
            optionType
        );

        require(
            optionType == OptionType.Call || optionType == OptionType.Put,
            "Wrong option type"
        );
        require(period >= 1 days, "Period is too short");
        require(period <= 90 days, "Period is too long");
        require(amount > strikeFee, "Price difference is too large");
        require(msg.value >= totalFee, "Wrong value");
        if (msg.value > totalFee) {
            payable(msg.sender).transfer(msg.value - totalFee);
        }

        uint256 strikeAmount = amount - strikeFee;
        uint256 lockedAmount = ((strikeAmount * optionCollateralizationRatio) / 100) + strikeFee;

        Option memory option = Option(
            State.Active,
            strike,
            amount,
            lockedAmount,
            totalFee - settlementFee,
            block.timestamp + period,
            optionType
        );

        optionID = createOptionFor(msg.sender);
        options[optionID] = option;

        uint256 stakingAmount = distributeSettlementFee(settlementFee, referrer);

        pool.lock{value: option.premium}(optionID, option.lockedAmount);

        emit Create(optionID, msg.sender, stakingAmount, totalFee);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['optionCollateralizationRatio', 'options', 'pool']
- **External calls**: `payable(msg.sender).transfer(msg.value - totalFee)` (method: transfer, receiver: (complex)), `pool.lock{value: option.premium}(optionID, option.lockedAmount)` (method: lock, receiver: pool)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['optionCollateralizationRatio', 'options', 'pool']
- **External calls**: `payable(msg.sender).transfer(msg.value - totalFee)` (low-level .transfer()), `pool.lock{value: option.premium}(optionID, option.lockedAmount)` (call on contract-typed state var 'pool' (type: BufferBNBPool))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StakingProxyUniV3.lockAdditional

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: lockAdditional
- **Line Range**: L94-L113
- **File**: `DAppSCAN-source/contracts/PeckShield-Convex_Frax/frax-cvx-platform-2f8573ee796daa022c1050b4a749bf08049c439b/contracts/contracts/StakingProxyUniV3.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`lockAdditional`, lines=`L94-L113`

#### 2. Function Source Code
```solidity
function lockAdditional(uint256 _token_id, uint256 _token0_amt, uint256 _token1_amt) external onlyOwner{
        uint256 userLiq = IFraxFarmUniV3(stakingAddress).lockedLiquidityOf(address(this));

        if(_token_id > 0 && _token0_amt > 0 && _token1_amt > 0){
            address token0 = IFraxFarmUniV3(stakingAddress).uni_token0();
            address token1 = IFraxFarmUniV3(stakingAddress).uni_token1();
            //pull tokens directly to staking address
            IERC20(token0).safeTransferFrom(msg.sender, stakingAddress, _token0_amt);
            IERC20(token1).safeTransferFrom(msg.sender, stakingAddress, _token1_amt);

            //add stake - use balance of override,  min in is ignored when doing so
            IFraxFarmUniV3(stakingAddress).lockAdditional(_token_id, _token0_amt, _token1_amt, 0, 0, true);
        }
        
        //if rewards are active, checkpoint
        if(IRewards(rewards).active()){
            userLiq = IFraxFarmUniV3(stakingAddress).lockedLiquidityOf(address(this)) - userLiq;
            IRewards(rewards).deposit(owner,userLiq);
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['owner', 'rewards', 'stakingAddress']
- **External calls**: `IFraxFarmUniV3(stakingAddress).lockedLiquidityOf(address(this))` (method: lockedLiquidityOf, receiver: IFraxFarmUniV3), `IFraxFarmUniV3(stakingAddress).uni_token0()` (method: uni_token0, receiver: IFraxFarmUniV3), `IFraxFarmUniV3(stakingAddress).uni_token1()` (method: uni_token1, receiver: IFraxFarmUniV3), `IERC20(token0).safeTransferFrom(msg.sender, stakingAddress, _token0_amt)` (method: safeTransferFrom, receiver: IERC20), `IERC20(token1).safeTransferFrom(msg.sender, stakingAddress, _token1_amt)` (method: safeTransferFrom, receiver: IERC20), `IFraxFarmUniV3(stakingAddress).lockAdditional(_token_id, _token0_amt, _token1_amt, 0, 0, true)` (method: lockAdditional, receiver: IFraxFarmUniV3), `IRewards(rewards).active()` (method: active, receiver: IRewards), `IFraxFarmUniV3(stakingAddress).lockedLiquidityOf(address(this))` (method: lockedLiquidityOf, receiver: IFraxFarmUniV3), `IRewards(rewards).deposit(owner,userLiq)` (method: deposit, receiver: IRewards)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['owner', 'rewards', 'stakingAddress']
- **External calls**: `IFraxFarmUniV3(stakingAddress).lockedLiquidityOf(address(this))` (inline cast call IFraxFarmUniV3(...).lockedLiquidityOf()), `IFraxFarmUniV3(stakingAddress).uni_token0()` (inline cast call IFraxFarmUniV3(...).uni_token0()), `IFraxFarmUniV3(stakingAddress).uni_token1()` (inline cast call IFraxFarmUniV3(...).uni_token1()), `IERC20(token0).safeTransferFrom(msg.sender, stakingAddress, _token0_amt)` (SafeERC20 .safeTransferFrom()), `IERC20(token1).safeTransferFrom(msg.sender, stakingAddress, _token1_amt)` (SafeERC20 .safeTransferFrom()), `IFraxFarmUniV3(stakingAddress).lockAdditional(_token_id, _token0_amt, _token1_amt, 0, 0, true)` (inline cast call IFraxFarmUniV3(...).lockAdditional()), `IRewards(rewards).active()` (inline cast call IRewards(...).active()), `IFraxFarmUniV3(stakingAddress).lockedLiquidityOf(address(this))` (inline cast call IFraxFarmUniV3(...).lockedLiquidityOf()), `IRewards(rewards).deposit(owner,userLiq)` (inline cast call IRewards(...).deposit())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### DjinnAutoBuyer.buyTokenFromBnb

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: buyTokenFromBnb
- **Line Range**: L154-L169
- **File**: `DAppSCAN-source/contracts/PeckShield-Donut/crossroad-550a8c3c010dc8c1a46ea9191d3841462bd58d82/contracts/DjiinAutoBuyer.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`buyTokenFromBnb`, lines=`L154-L169`

#### 2. Function Source Code
```solidity
function buyTokenFromBnb(
        address _outTarget
        ) external payable
    {
        uint256 _amountOutBusd = amountOut(lpWbnbBusd, true, msg.value, SWAP_PERMILLION_PCS2);
        uint256 _amountOutDjinn = amountOut(lpDjinnBusd, false, _amountOutBusd, SWAP_PERMILLION_PCS1);

        // execute swap and transfer djinn to sender
        IWETH(wbnbToken).deposit{value: msg.value}();
        IWETH(wbnbToken).transfer(lpWbnbBusd, msg.value);
        IUniswapPool(lpWbnbBusd).swap(0, _amountOutBusd, lpDjinnBusd, new bytes(0));
        IUniswapPool(lpDjinnBusd).swap(_amountOutDjinn, 0, _outTarget, new bytes(0));

        emit BoughtToken(_amountOutDjinn);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['SWAP_PERMILLION_PCS1', 'SWAP_PERMILLION_PCS2', 'lpDjinnBusd', 'lpWbnbBusd', 'wbnbToken']
- **External calls**: `IWETH(wbnbToken).deposit{value: msg.value}()` (method: deposit, receiver: IWETH), `IWETH(wbnbToken).transfer(lpWbnbBusd, msg.value)` (method: transfer, receiver: IWETH), `IUniswapPool(lpWbnbBusd).swap(0, _amountOutBusd, lpDjinnBusd, new bytes(0))` (method: swap, receiver: IUniswapPool), `IUniswapPool(lpDjinnBusd).swap(_amountOutDjinn, 0, _outTarget, new bytes(0))` (method: swap, receiver: IUniswapPool)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['SWAP_PERMILLION_PCS1', 'SWAP_PERMILLION_PCS2', 'lpDjinnBusd', 'lpWbnbBusd', 'wbnbToken']
- **External calls**: `IWETH(wbnbToken).deposit{value: msg.value}()` (inline cast call IWETH(...).deposit()), `IWETH(wbnbToken).transfer(lpWbnbBusd, msg.value)` (low-level .transfer()), `IUniswapPool(lpWbnbBusd).swap(0, _amountOutBusd, lpDjinnBusd, new bytes(0))` (inline cast call IUniswapPool(...).swap()), `IUniswapPool(lpDjinnBusd).swap(_amountOutDjinn, 0, _outTarget, new bytes(0))` (inline cast call IUniswapPool(...).swap())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### DYTokenERC20.depositTo

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: depositTo
- **Line Range**: L29-L57
- **File**: `DAppSCAN-source/contracts/PeckShield-Duet/duet-collateral-contracts-92452dad092d6b5f76713484e30159b5fa75ea80/contracts/DYTokenERC20.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`depositTo`, lines=`L29-L57`

#### 2. Function Source Code
```solidity
function depositTo(address _to, uint _amount, address _toVault) public override {
    uint total = underlyingTotal();
    IERC20 underlyingToken = IERC20(underlying);

    uint before = underlyingToken.balanceOf(address(this));
    underlyingToken.safeTransferFrom(msg.sender, address(this), _amount);
    uint realAmount = underlyingToken.balanceOf(address(this)) - before; // Additional check for deflationary tokens
    require(realAmount >= _amount, "illegal amount"); 
    
    uint shares = 0;
    if (totalSupply() == 0) {
      require(_amount >= 10000, "too small");
      shares = _amount;
    } else {
      shares = _amount * totalSupply() / total;
    }

    require(shares > 0, "ZERO_SHARE");
    
    if(_toVault != address(0)) {
      require(_toVault == IController(controller).dyTokenVaults(address(this)), "mismatch dToken vault");
      _mint(_toVault, shares);
      IDepositVault(_toVault).syncDeposit(address(this), shares, _to);
    } else {
      _mint(_to, shares);
    }
    
    earn();
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['controller', 'underlying']
- **External calls**: `underlyingToken.balanceOf(address(this))` (method: balanceOf, receiver: underlyingToken), `underlyingToken.safeTransferFrom(msg.sender, address(this), _amount)` (method: safeTransferFrom, receiver: underlyingToken), `underlyingToken.balanceOf(address(this))` (method: balanceOf, receiver: underlyingToken), `IDepositVault(_toVault).syncDeposit(address(this), shares, _to)` (method: syncDeposit, receiver: IDepositVault)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['controller', 'underlying']
- **External calls**: `underlyingToken.balanceOf(address(this))` (call on contract-typed local var 'underlyingToken' (type: IERC20)), `underlyingToken.safeTransferFrom(msg.sender, address(this), _amount)` (SafeERC20 .safeTransferFrom()), `underlyingToken.balanceOf(address(this))` (call on contract-typed local var 'underlyingToken' (type: IERC20)), `IDepositVault(_toVault).syncDeposit(address(this), shares, _to)` (inline cast call IDepositVault(...).syncDeposit())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### PikaPerpV2.closePositionWithId

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: closePositionWithId
- **Line Range**: L402-459
- **File**: `DAppSCAN-source/contracts/PeckShield-PikaPerpV2/PikaPerpV2-4a0965ff90ed099b7e2d3e8dda47cd589ee8e3a2/contracts/perp/PikaPerpV2.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`closePositionWithId`, lines=`L402-459`

#### 2. Function Source Code
```solidity
function closePositionWithId(
        uint256 positionId,
        uint256 margin
    ) public {
        // Check params
        require(margin >= minMargin, "!margin");

        // Check position
        Position storage position = positions[positionId];
        require(msg.sender == position.owner, "!owner");

        // Check product
        Product storage product = products[uint256(position.productId)];

        bool isFullClose;
        if (margin >= uint256(position.margin)) {
            margin = uint256(position.margin);
            isFullClose = true;
        }
        uint256 maxExposure = uint256(vault.balance).mul(uint256(product.weight)).mul(exposureMultiplier).div(uint256(totalWeight)).div(10**4);
        uint256 price = _calculatePrice(product.feed, !position.isLong, product.openInterestLong, product.openInterestShort,
            maxExposure, uint256(product.reserve), margin * position.leverage / 10**8);

        bool isLiquidatable;
        int256 pnl = _getPnl(position, margin, price);
        if (pnl < 0 && uint256(-1 * pnl) >= margin.mul(uint256(product.liquidationThreshold)).div(10**4)) {
            margin = uint256(position.margin);
            pnl = -1 * int256(uint256(position.margin));
            isLiquidatable = true;
        } else {
            // front running protection: if oracle price up change is smaller than threshold and minProfitTime has not passed, the pnl is be set to 0
            if (pnl > 0 && !_canTakeProfit(position, IOracle(oracle).getPrice(product.feed), product.minPriceChange)) {
                pnl = 0;
            }
        }

        uint256 totalFee = _updateVaultAndGetFee(pnl, position, margin, uint256(product.fee), uint256(product.interest));
        _updateOpenInterest(uint256(position.productId), margin.mul(uint256(position.leverage)).div(BASE), position.isLong, false);

        emit ClosePosition(
            positionId,
            position.owner,
            uint256(position.productId),
            price,
            uint256(position.price),
            margin,
            uint256(position.leverage),
            totalFee,
            pnl,
            isLiquidatable
        );

        if (isFullClose) {
            delete positions[positionId];
        } else {
            position.margin -= uint64(margin);
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['BASE', 'exposureMultiplier', 'minMargin', 'oracle', 'owner', 'positions', 'products', 'totalWeight', 'vault']
- **External calls**: `IOracle(oracle).getPrice(product.feed)` (method: getPrice, receiver: IOracle)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['BASE', 'exposureMultiplier', 'minMargin', 'oracle', 'owner', 'positions', 'products', 'totalWeight', 'vault']
- **External calls**: `IOracle(oracle).getPrice(product.feed)` (inline cast call IOracle(...).getPrice())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### PMintBurn.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L48-L63
- **File**: `DAppSCAN-source/contracts/PeckShield-PlutosV1/plutos-eth-contract-0777815/contracts/PMintBurn.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L48-L63`

#### 2. Function Source Code
```solidity
function deposit(uint256 _amount) public returns(bytes32){
    bytes32 hash = hash_from_address(msg.sender);
    IPMBParams param = IPMBParams(dispatcher.getTarget(param_key));

    require(_amount >= param.minimum_deposit_amount(), "need to be more than minimum amount");

    uint256 prev = IERC20(target_token).balanceOf(pool);
    IERC20(target_token).safeTransferFrom(msg.sender, pool, _amount);
    uint256 amount = IERC20(target_token).balanceOf(pool).safeSub(prev);

    deposits[hash].from = msg.sender;
    deposits[hash].exist = true;
    deposits[hash].target_token_amount = deposits[hash].target_token_amount.safeAdd(amount);
    emit PDeposit(msg.sender, hash, amount, deposits[hash].target_token_amount);
    return hash;
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['deposits', 'dispatcher', 'param_key', 'pool', 'target_token']
- **External calls**: `dispatcher.getTarget(param_key)` (method: getTarget, receiver: dispatcher), `IERC20(target_token).balanceOf(pool)` (method: balanceOf, receiver: IERC20), `IERC20(target_token).safeTransferFrom(msg.sender, pool, _amount)` (method: safeTransferFrom, receiver: IERC20), `IERC20(target_token).balanceOf(pool).safeSub(prev)` (method: safeSub, receiver: IERC20), `IERC20(target_token).balanceOf(pool)` (method: balanceOf, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['deposits', 'dispatcher', 'param_key', 'pool', 'target_token']
- **External calls**: `dispatcher.getTarget(param_key)` (call on contract-typed state var 'dispatcher' (type: IPDispatcher)), `IERC20(target_token).balanceOf(pool)` (inline cast call IERC20(...).balanceOf()), `IERC20(target_token).safeTransferFrom(msg.sender, pool, _amount)` (SafeERC20 .safeTransferFrom()), `IERC20(target_token).balanceOf(pool).safeSub(prev)` (inline cast call IERC20(...).safeSub()), `IERC20(target_token).balanceOf(pool)` (inline cast call IERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### RobotLiabilityLib.finalize

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: finalize
- **Line Range**: L104
- **File**: `DAppSCAN-source/contracts/PepperSec-Aira-Robonomic/robonomics_contracts-cc35a91de187072214d215262d8371f0159c2498/contracts/robonomics/RobotLiabilityLib.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`finalize`, lines=`L104`

#### 2. Function Source Code
```solidity
function finalize(
        bytes _result,
        bytes _signature,
        bool  _agree
    )
        external
        returns (bool)
    {
        uint256 gasinit = gasleft();
        require(!isFinalized);

        address resultSender = keccak256(abi.encodePacked(this, _result))
            .toEthSignedMessageHash()
            .recover(_signature);
        require(resultSender == promisor);

        if (validator == 0) {
            require(factory.isLighthouse(msg.sender));
            require(token.transfer(promisor, cost));
        } else {
            require(msg.sender == validator);

            isConfirmed = _agree;
            if (isConfirmed)
                require(token.transfer(promisor, cost));
            else
                require(token.transfer(promisee, cost));

            if (validatorFee > 0)
                require(factory.xrt().transfer(validator, validatorFee));
        }

        result = _result;
        isFinalized = true;

        require(factory.liabilityFinalized(gasinit));
        return true;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['cost', 'factory', 'isConfirmed', 'isFinalized', 'promisee', 'promisor', 'result', 'token', 'validator', 'validatorFee']
- **External calls**: `factory.isLighthouse(msg.sender)` (method: isLighthouse, receiver: factory), `token.transfer(promisor, cost)` (method: transfer, receiver: token), `token.transfer(promisor, cost)` (method: transfer, receiver: token), `token.transfer(promisee, cost)` (method: transfer, receiver: token), `factory.xrt().transfer(validator, validatorFee)` (method: transfer, receiver: factory), `factory.xrt()` (method: xrt, receiver: factory), `factory.liabilityFinalized(gasinit)` (method: liabilityFinalized, receiver: factory)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['cost', 'factory', 'isConfirmed', 'isFinalized', 'promisee', 'promisor', 'result', 'token', 'validator', 'validatorFee']
- **External calls**: `factory.isLighthouse(msg.sender)` (call on contract-typed state var 'factory' (type: LiabilityFactory)), `token.transfer(promisor, cost)` (low-level .transfer()), `token.transfer(promisor, cost)` (low-level .transfer()), `token.transfer(promisee, cost)` (low-level .transfer()), `factory.xrt().transfer(validator, validatorFee)` (low-level .transfer()), `factory.xrt()` (call on contract-typed state var 'factory' (type: LiabilityFactory)), `factory.liabilityFinalized(gasinit)` (call on contract-typed state var 'factory' (type: LiabilityFactory))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### AlgoVestStaking.AVSTokenDonation

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: AVSTokenDonation
- **Line Range**: L74 - L84
- **File**: `DAppSCAN-source/contracts/QuillAudits-Algovest/AlgoVestStaking0x090e69e7F48AFC059e480F297042DEA396B971e7/srv/tecmie/algovest/AVS-staking/contracts/stakin_contract.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`AVSTokenDonation`, lines=`L74 - L84`

#### 2. Function Source Code
```solidity
function AVSTokenDonation(uint256 amount) external {
        address sender = _msgSender();
        require(
            avsAddress.transferFrom(sender, address(this), amount),
            "StakingAVS: Could not get AVS tokens"
        );
        allAVSTokens = allAVSTokens.add(amount);
        unfreezedAVSTokens = unfreezedAVSTokens.add(amount);
        emit AVSTokenIncome(sender, amount, _currentDay());
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['allAVSTokens', 'avsAddress', 'unfreezedAVSTokens']
- **External calls**: `avsAddress.transferFrom(sender, address(this), amount)` (method: transferFrom, receiver: avsAddress)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['allAVSTokens', 'avsAddress', 'unfreezedAVSTokens']
- **External calls**: `avsAddress.transferFrom(sender, address(this), amount)` (call on contract-typed state var 'avsAddress' (type: IERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### CurveV1Adapter.exchange

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: exchange
- **Line Range**: L49 - L85
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/adapters/CurveV1.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`exchange`, lines=`L49 - L85`

#### 2. Function Source Code
```solidity
function exchange(
        int128 i,
        int128 j,
        uint256 dx,
        uint256 min_dy
    ) external override {
        address creditAccount = creditManager.getCreditAccountOrRevert(
            msg.sender
        );

        address tokenIn = curvePool.coins(uint256(i));
        address tokenOut = curvePool.coins(uint256(j));

        creditManager.provideCreditAccountAllowance(
            creditAccount,
            address(curvePool),
            tokenIn
        ); // T:[CVA-3]

        bytes memory data = abi.encodeWithSelector(
            bytes4(0x3df02124), // "exchange(int128,int128,uint256,uint256)",
            i,
            j,
            dx,
            min_dy
        ); // T:[CVA-3]

        creditManager.executeOrder(msg.sender, address(curvePool), data); // T:[CVA-3]

        creditFilter.checkCollateralChange(
            creditAccount,
            tokenIn,
            tokenOut,
            dx,
            min_dy
        ); // T:[CVA-2]
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['creditFilter', 'creditManager', 'curvePool']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (method: getCreditAccountOrRevert, receiver: creditManager), `curvePool.coins(uint256(i))` (method: coins, receiver: curvePool), `curvePool.coins(uint256(j))` (method: coins, receiver: curvePool), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            address(curvePool),
            toke` (method: provideCreditAccountAllowance, receiver: creditManager), `creditManager.executeOrder(msg.sender, address(curvePool), data)` (method: executeOrder, receiver: creditManager), `creditFilter.checkCollateralChange(
            creditAccount,
            tokenIn,
            tokenOut,
            dx` (method: checkCollateralChange, receiver: creditFilter)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['creditFilter', 'creditManager', 'curvePool']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `curvePool.coins(uint256(i))` (call on contract-typed state var 'curvePool' (type: ICurvePool)), `curvePool.coins(uint256(j))` (call on contract-typed state var 'curvePool' (type: ICurvePool)), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            address(curvePool),
            toke` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditManager.executeOrder(msg.sender, address(curvePool), data)` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditFilter.checkCollateralChange(
            creditAccount,
            tokenIn,
            tokenOut,
            dx` (call on contract-typed state var 'creditFilter' (type: ICreditFilter))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### UniswapV2Adapter.swapTokensForExactTokens

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: swapTokensForExactTokens
- **Line Range**: L56
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/adapters/UniswapV2.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`swapTokensForExactTokens`, lines=`L56`

#### 2. Function Source Code
```solidity
function swapTokensForExactTokens(
        uint256 amountOut,
        uint256 amountInMax,
        address[] calldata path,
        address,
        uint256 deadline
    ) external override returns (uint256[] memory amounts) {
        address creditAccount = creditManager.getCreditAccountOrRevert(
            msg.sender
        );

        creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            path[0]
        );

        bytes memory data = abi.encodeWithSelector(
            bytes4(0x8803dbee), // "swapTokensForExactTokens(uint256,uint256,address[],address,uint256)",
            amountOut,
            amountInMax,
            path,
            creditAccount,
            deadline
        );

        amounts = abi.decode(
            creditManager.executeOrder(msg.sender, swapContract, data),
            (uint256[])
        );


        creditFilter.checkCollateralChange(
            creditAccount,
            path[0],
            path[path.length - 1],
            amounts[0],
            amounts[amounts.length - 1]
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['creditFilter', 'creditManager', 'swapContract']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (method: getCreditAccountOrRevert, receiver: creditManager), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            path[0]
  ` (method: provideCreditAccountAllowance, receiver: creditManager), `creditManager.executeOrder(msg.sender, swapContract, data)` (method: executeOrder, receiver: creditManager), `creditFilter.checkCollateralChange(
            creditAccount,
            path[0],
            path[path.length - 1],
 ` (method: checkCollateralChange, receiver: creditFilter)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['creditFilter', 'creditManager', 'swapContract']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            path[0]
  ` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditManager.executeOrder(msg.sender, swapContract, data)` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditFilter.checkCollateralChange(
            creditAccount,
            path[0],
            path[path.length - 1],
 ` (call on contract-typed state var 'creditFilter' (type: ICreditFilter))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### UniswapV2Adapter.swapExactTokensForTokens

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: swapExactTokensForTokens
- **Line Range**: L110
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/adapters/UniswapV2.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`swapExactTokensForTokens`, lines=`L110`

#### 2. Function Source Code
```solidity
function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address,
        uint256 deadline
    ) external override returns (uint256[] memory amounts) {
        // SWC-107-Reentrancy: L110
        address creditAccount = creditManager.getCreditAccountOrRevert(
            msg.sender
        );

        creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            path[0]
        );

        bytes memory data = abi.encodeWithSelector(
            bytes4(0x38ed1739), // "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)",
            amountIn,
            amountOutMin,
            path,
            creditAccount,
            deadline
        );

        amounts = abi.decode(
            creditManager.executeOrder(msg.sender, swapContract, data),
            (uint256[])
        );

        creditFilter.checkCollateralChange(
            creditAccount,
            path[0],
            path[path.length - 1],
            amounts[0],
            amounts[amounts.length - 1]
        ); // ToDo: CHECK(!)
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['creditFilter', 'creditManager', 'swapContract']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (method: getCreditAccountOrRevert, receiver: creditManager), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            path[0]
  ` (method: provideCreditAccountAllowance, receiver: creditManager), `creditManager.executeOrder(msg.sender, swapContract, data)` (method: executeOrder, receiver: creditManager), `creditFilter.checkCollateralChange(
            creditAccount,
            path[0],
            path[path.length - 1],
 ` (method: checkCollateralChange, receiver: creditFilter)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['creditFilter', 'creditManager', 'swapContract']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            path[0]
  ` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditManager.executeOrder(msg.sender, swapContract, data)` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditFilter.checkCollateralChange(
            creditAccount,
            path[0],
            path[path.length - 1],
 ` (call on contract-typed state var 'creditFilter' (type: ICreditFilter))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### UniswapV3Adapter.exactInputSingle

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: exactInputSingle
- **Line Range**: L52
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/adapters/UniswapV3.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`exactInputSingle`, lines=`L52`

#### 2. Function Source Code
```solidity
function exactInputSingle(ExactInputSingleParams calldata params)
        external
        payable
        override
        returns (uint256 amountOut)
    {
        // SWC-107-Reentrancy: L52
        address creditAccount = creditManager.getCreditAccountOrRevert(
            msg.sender
        );

        creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            params.tokenIn
        );

        ExactInputSingleParams memory paramsUpdate = params;
        paramsUpdate.recipient = creditAccount;

        // 0x414bf389 = exactInputSingle((address,address,uint24,address,uint256,uint256,uint256,uint160))
        bytes memory data = abi.encodeWithSelector(
            bytes4(0x414bf389), // +
            paramsUpdate
        );

        uint256 balanceBefore = IERC20(paramsUpdate.tokenIn).balanceOf(
            creditAccount
        );

        // ToDo: Check for partial execution
        bytes memory result = creditManager.executeOrder(
            msg.sender,
            swapContract,
            data
        );
        (amountOut) = abi.decode(result, (uint256));

        creditFilter.checkCollateralChange(
            creditAccount,
            params.tokenIn,
            params.tokenOut,
            balanceBefore.sub(
                IERC20(paramsUpdate.tokenIn).balanceOf(creditAccount)
            ),
            amountOut
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['creditFilter', 'creditManager', 'swapContract']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (method: getCreditAccountOrRevert, receiver: creditManager), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            params.tok` (method: provideCreditAccountAllowance, receiver: creditManager), `IERC20(paramsUpdate.tokenIn).balanceOf(
            creditAccount
        )` (method: balanceOf, receiver: IERC20), `creditManager.executeOrder(
            msg.sender,
            swapContract,
            data
        )` (method: executeOrder, receiver: creditManager), `creditFilter.checkCollateralChange(
            creditAccount,
            params.tokenIn,
            params.tokenOut,
` (method: checkCollateralChange, receiver: creditFilter), `IERC20(paramsUpdate.tokenIn).balanceOf(creditAccount)` (method: balanceOf, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['creditFilter', 'creditManager', 'swapContract']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            params.tok` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `IERC20(paramsUpdate.tokenIn).balanceOf(
            creditAccount
        )` (inline cast call IERC20(...).balanceOf()), `creditManager.executeOrder(
            msg.sender,
            swapContract,
            data
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditFilter.checkCollateralChange(
            creditAccount,
            params.tokenIn,
            params.tokenOut,
` (call on contract-typed state var 'creditFilter' (type: ICreditFilter)), `IERC20(paramsUpdate.tokenIn).balanceOf(creditAccount)` (inline cast call IERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### UniswapV3Adapter.exactInput

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: exactInput
- **Line Range**: L106
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/adapters/UniswapV3.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`exactInput`, lines=`L106`

#### 2. Function Source Code
```solidity
function exactInput(ExactInputParams calldata params)
        external
        payable
        override
        returns (uint256 amountOut)
    {
        // SWC-107-Reentrancy: L106
        address creditAccount = creditManager.getCreditAccountOrRevert(
            msg.sender
        );

        // SWC-124-Write to Arbitrary Storage Location: L105
        (address tokenIn, address tokenOut) = _extractTokens(params.path);

        creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            tokenIn
        );

        ExactInputParams memory paramsUpdate = params;
        paramsUpdate.recipient = creditAccount;

        // 0xc04b8d59 = exactInput((bytes,address,uint256,uint256,uint256))
        bytes memory data = abi.encodeWithSelector(
            bytes4(0xc04b8d59), // +
            paramsUpdate
        );

        uint256 balanceBefore = IERC20(tokenIn).balanceOf(creditAccount);

        bytes memory result = creditManager.executeOrder(
            msg.sender,
            swapContract,
            data
        );
        (amountOut) = abi.decode(result, (uint256));

        creditFilter.checkCollateralChange(
            creditAccount,
            tokenIn,
            tokenOut,
            balanceBefore.sub(IERC20(tokenIn).balanceOf(creditAccount)),
            amountOut
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['creditFilter', 'creditManager', 'swapContract']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (method: getCreditAccountOrRevert, receiver: creditManager), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            tokenIn
  ` (method: provideCreditAccountAllowance, receiver: creditManager), `IERC20(tokenIn).balanceOf(creditAccount)` (method: balanceOf, receiver: IERC20), `creditManager.executeOrder(
            msg.sender,
            swapContract,
            data
        )` (method: executeOrder, receiver: creditManager), `creditFilter.checkCollateralChange(
            creditAccount,
            tokenIn,
            tokenOut,
            ba` (method: checkCollateralChange, receiver: creditFilter), `IERC20(tokenIn).balanceOf(creditAccount)` (method: balanceOf, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['creditFilter', 'creditManager', 'swapContract']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            tokenIn
  ` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `IERC20(tokenIn).balanceOf(creditAccount)` (inline cast call IERC20(...).balanceOf()), `creditManager.executeOrder(
            msg.sender,
            swapContract,
            data
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditFilter.checkCollateralChange(
            creditAccount,
            tokenIn,
            tokenOut,
            ba` (call on contract-typed state var 'creditFilter' (type: ICreditFilter)), `IERC20(tokenIn).balanceOf(creditAccount)` (inline cast call IERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### UniswapV3Adapter.exactOutputSingle

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: exactOutputSingle
- **Line Range**: L153
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/adapters/UniswapV3.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`exactOutputSingle`, lines=`L153`

#### 2. Function Source Code
```solidity
function exactOutputSingle(ExactOutputSingleParams calldata params)
        external
        payable
        override
        returns (uint256 amountIn)
    {
        // SWC-107-Reentrancy: L153
        address creditAccount = creditManager.getCreditAccountOrRevert(
            msg.sender
        );

        // SWC-107-Reentrancy: L154
        creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            params.tokenIn
        );

        ExactOutputSingleParams memory paramsUpdate = params;
        paramsUpdate.recipient = creditAccount;

        //
        bytes memory data = abi.encodeWithSelector(
            bytes4(0xdb3e2198), //+
            paramsUpdate
        );

        uint256 balanceBefore = IERC20(paramsUpdate.tokenOut).balanceOf(
            creditAccount
        );

        bytes memory result = creditManager.executeOrder(
            msg.sender,
            swapContract,
            data
        );
        (amountIn) = abi.decode(result, (uint256));

        creditFilter.checkCollateralChange(
            creditAccount,
            params.tokenIn,
            params.tokenOut,
            amountIn,
            IERC20(paramsUpdate.tokenOut).balanceOf(creditAccount).sub(
                balanceBefore
            )
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['creditFilter', 'creditManager', 'swapContract']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (method: getCreditAccountOrRevert, receiver: creditManager), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            params.tok` (method: provideCreditAccountAllowance, receiver: creditManager), `IERC20(paramsUpdate.tokenOut).balanceOf(
            creditAccount
        )` (method: balanceOf, receiver: IERC20), `creditManager.executeOrder(
            msg.sender,
            swapContract,
            data
        )` (method: executeOrder, receiver: creditManager), `creditFilter.checkCollateralChange(
            creditAccount,
            params.tokenIn,
            params.tokenOut,
` (method: checkCollateralChange, receiver: creditFilter), `IERC20(paramsUpdate.tokenOut).balanceOf(creditAccount).sub(
                balanceBefore
            )` (method: sub, receiver: IERC20), `IERC20(paramsUpdate.tokenOut).balanceOf(creditAccount)` (method: balanceOf, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['creditFilter', 'creditManager', 'swapContract']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            params.tok` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `IERC20(paramsUpdate.tokenOut).balanceOf(
            creditAccount
        )` (inline cast call IERC20(...).balanceOf()), `creditManager.executeOrder(
            msg.sender,
            swapContract,
            data
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditFilter.checkCollateralChange(
            creditAccount,
            params.tokenIn,
            params.tokenOut,
` (call on contract-typed state var 'creditFilter' (type: ICreditFilter)), `IERC20(paramsUpdate.tokenOut).balanceOf(creditAccount).sub(
                balanceBefore
            )` (inline cast call IERC20(...).sub()), `IERC20(paramsUpdate.tokenOut).balanceOf(creditAccount)` (inline cast call IERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### UniswapV3Adapter.exactOutput

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: exactOutput
- **Line Range**: L210
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/adapters/UniswapV3.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`exactOutput`, lines=`L210`

#### 2. Function Source Code
```solidity
function exactOutput(ExactOutputParams calldata params)
        external
        payable
        override
        returns (uint256 amountIn)
    {
        address creditAccount = creditManager.getCreditAccountOrRevert(
            msg.sender
        );

        // SWC-124-Write to Arbitrary Storage Location: L206
        (address tokenOut, address tokenIn) = _extractTokens(params.path);

        console.log(tokenIn);
        console.log(tokenOut);

        // SWC-107-Reentrancy: L210
        creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            tokenIn
        );

        ExactOutputParams memory paramsUpdate = params;
        paramsUpdate.recipient = creditAccount;

        bytes memory data = abi.encodeWithSelector(
            bytes4(0xf28c0498), // exactOutput((bytes,address,uint256,uint256,uint256))
            paramsUpdate
        );

        uint256 balanceBefore = IERC20(tokenOut).balanceOf(creditAccount);

        {
            bytes memory result = creditManager.executeOrder(
                msg.sender,
                swapContract,
                data
            );
            (amountIn) = abi.decode(result, (uint256));
        }

        console.log("balanceBefore");
        console.log(balanceBefore);
        console.log(IERC20(tokenOut).balanceOf(creditAccount));

        creditFilter.checkCollateralChange(
            creditAccount,
            tokenIn,
            tokenOut,
            amountIn,
            IERC20(tokenOut).balanceOf(creditAccount).sub(balanceBefore)
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['creditFilter', 'creditManager', 'swapContract']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (method: getCreditAccountOrRevert, receiver: creditManager), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            tokenIn
  ` (method: provideCreditAccountAllowance, receiver: creditManager), `IERC20(tokenOut).balanceOf(creditAccount)` (method: balanceOf, receiver: IERC20), `creditManager.executeOrder(
                msg.sender,
                swapContract,
                data
            )` (method: executeOrder, receiver: creditManager), `IERC20(tokenOut).balanceOf(creditAccount)` (method: balanceOf, receiver: IERC20), `creditFilter.checkCollateralChange(
            creditAccount,
            tokenIn,
            tokenOut,
            am` (method: checkCollateralChange, receiver: creditFilter), `IERC20(tokenOut).balanceOf(creditAccount).sub(balanceBefore)` (method: sub, receiver: IERC20), `IERC20(tokenOut).balanceOf(creditAccount)` (method: balanceOf, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['creditFilter', 'creditManager', 'swapContract']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            swapContract,
            tokenIn
  ` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `IERC20(tokenOut).balanceOf(creditAccount)` (inline cast call IERC20(...).balanceOf()), `creditManager.executeOrder(
                msg.sender,
                swapContract,
                data
            )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `IERC20(tokenOut).balanceOf(creditAccount)` (inline cast call IERC20(...).balanceOf()), `creditFilter.checkCollateralChange(
            creditAccount,
            tokenIn,
            tokenOut,
            am` (call on contract-typed state var 'creditFilter' (type: ICreditFilter)), `IERC20(tokenOut).balanceOf(creditAccount).sub(balanceBefore)` (inline cast call IERC20(...).sub()), `IERC20(tokenOut).balanceOf(creditAccount)` (inline cast call IERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### YearnAdapter._deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: _deposit
- **Line Range**: L78
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/adapters/YearnV2.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`_deposit`, lines=`L78`

#### 2. Function Source Code
```solidity
function _deposit(bytes memory data) internal returns (uint256 shares) {
        address creditAccount = creditManager.getCreditAccountOrRevert(
            msg.sender
        );

        // SWC-107-Reentrancy: L78
        creditManager.provideCreditAccountAllowance(
            creditAccount,
            yVault,
            token
        );

        uint256 balanceBefore = ERC20(token).balanceOf(creditAccount);

        shares = abi.decode(
            creditManager.executeOrder(msg.sender, yVault, data),
            (uint256)
        );

        creditFilter.checkCollateralChange(
            creditAccount,
            token,
            yVault,
            balanceBefore.sub(ERC20(token).balanceOf(creditAccount)),
            shares
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['creditFilter', 'creditManager', 'token', 'yVault']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (method: getCreditAccountOrRevert, receiver: creditManager), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            yVault,
            token
        )` (method: provideCreditAccountAllowance, receiver: creditManager), `ERC20(token).balanceOf(creditAccount)` (method: balanceOf, receiver: ERC20), `creditManager.executeOrder(msg.sender, yVault, data)` (method: executeOrder, receiver: creditManager), `creditFilter.checkCollateralChange(
            creditAccount,
            token,
            yVault,
            balanc` (method: checkCollateralChange, receiver: creditFilter), `ERC20(token).balanceOf(creditAccount)` (method: balanceOf, receiver: ERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['creditFilter', 'creditManager', 'token', 'yVault']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            yVault,
            token
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `ERC20(token).balanceOf(creditAccount)` (inline cast call ERC20(...).balanceOf()), `creditManager.executeOrder(msg.sender, yVault, data)` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditFilter.checkCollateralChange(
            creditAccount,
            token,
            yVault,
            balanc` (call on contract-typed state var 'creditFilter' (type: ICreditFilter)), `ERC20(token).balanceOf(creditAccount)` (inline cast call ERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### YearnAdapter.withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdraw
- **Line Range**: L132
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/adapters/YearnV2.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdraw`, lines=`L132`

#### 2. Function Source Code
```solidity
function withdraw(
        uint256 maxShares,
        address,
        uint256 maxLoss
    ) public override returns (uint256 shares) {
        address creditAccount = creditManager.getCreditAccountOrRevert(
            msg.sender
        );

        // SWC-135-Code With No Effects: L132
        // SWC-107-Reentrancy: L132
        creditManager.provideCreditAccountAllowance(
            creditAccount,
            yVault,
            token
        );

        bytes memory data = abi.encodeWithSelector(
            bytes4(0x2e1a7d4d), //"withdraw(uint256,address,uint256)",
            maxShares,
            creditAccount,
            maxLoss
        );

        uint256 balance = ERC20(token).balanceOf(creditAccount);

        shares = abi.decode(
            creditManager.executeOrder(msg.sender, yVault, data),
            (uint256)
        );

        creditFilter.checkCollateralChange(
            creditAccount,
            yVault,
            token,
            shares,
            ERC20(token).balanceOf(creditAccount).sub(balance)
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['creditFilter', 'creditManager', 'token', 'yVault']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (method: getCreditAccountOrRevert, receiver: creditManager), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            yVault,
            token
        )` (method: provideCreditAccountAllowance, receiver: creditManager), `ERC20(token).balanceOf(creditAccount)` (method: balanceOf, receiver: ERC20), `creditManager.executeOrder(msg.sender, yVault, data)` (method: executeOrder, receiver: creditManager), `creditFilter.checkCollateralChange(
            creditAccount,
            yVault,
            token,
            shares` (method: checkCollateralChange, receiver: creditFilter), `ERC20(token).balanceOf(creditAccount).sub(balance)` (method: sub, receiver: ERC20), `ERC20(token).balanceOf(creditAccount)` (method: balanceOf, receiver: ERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['creditFilter', 'creditManager', 'token', 'yVault']
- **External calls**: `creditManager.getCreditAccountOrRevert(
            msg.sender
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditManager.provideCreditAccountAllowance(
            creditAccount,
            yVault,
            token
        )` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `ERC20(token).balanceOf(creditAccount)` (inline cast call ERC20(...).balanceOf()), `creditManager.executeOrder(msg.sender, yVault, data)` (call on contract-typed state var 'creditManager' (type: ICreditManager)), `creditFilter.checkCollateralChange(
            creditAccount,
            yVault,
            token,
            shares` (call on contract-typed state var 'creditFilter' (type: ICreditFilter)), `ERC20(token).balanceOf(creditAccount).sub(balance)` (inline cast call ERC20(...).sub()), `ERC20(token).balanceOf(creditAccount)` (inline cast call ERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### WETHGateway.addLiquidityETH

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: addLiquidityETH
- **Line Range**: L98 - L112
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/core/WETHGateway.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`addLiquidityETH`, lines=`L98 - L112`

#### 2. Function Source Code
```solidity
function addLiquidityETH(
        address pool,
        address onBehalfOf,
        uint16 referralCode
    )
        external
        payable
        override
        wethPoolOnly(pool) // T:[WG-1, 2]
    {
        IWETH(wethAddress).deposit{value: msg.value}(); // T:[WG-8]

        _checkAllowance(pool, msg.value); // T:[WG-8]
        IPoolService(pool).addLiquidity(msg.value, onBehalfOf, referralCode); // T:[WG-8]
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['wethAddress']
- **External calls**: `IWETH(wethAddress).deposit{value: msg.value}()` (method: deposit, receiver: IWETH), `IPoolService(pool).addLiquidity(msg.value, onBehalfOf, referralCode)` (method: addLiquidity, receiver: IPoolService)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['wethAddress']
- **External calls**: `IWETH(wethAddress).deposit{value: msg.value}()` (inline cast call IWETH(...).deposit()), `IPoolService(pool).addLiquidity(msg.value, onBehalfOf, referralCode)` (inline cast call IPoolService(...).addLiquidity())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### WETHGateway.openCreditAccountETH

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: openCreditAccountETH
- **Line Range**: L151 - L171
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/core/WETHGateway.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`openCreditAccountETH`, lines=`L151 - L171`

#### 2. Function Source Code
```solidity
function openCreditAccountETH(
        address creditManager,
        address payable onBehalfOf,
        uint256 leverageFactor,
        uint256 referralCode
    )
        external
        payable
        override
        wethCreditManagerOnly(creditManager) // T:[WG-3, 4]
    {
        _checkAllowance(creditManager, msg.value); // T:[WG-10]

        IWETH(wethAddress).deposit{value: msg.value}(); // T:[WG-10]
        ICreditManager(creditManager).openCreditAccount(
            msg.value,
            onBehalfOf,
            leverageFactor,
            referralCode
        ); // T:[WG-10]
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['wethAddress']
- **External calls**: `IWETH(wethAddress).deposit{value: msg.value}()` (method: deposit, receiver: IWETH), `ICreditManager(creditManager).openCreditAccount(
            msg.value,
            onBehalfOf,
            leverageFact` (method: openCreditAccount, receiver: ICreditManager)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['wethAddress']
- **External calls**: `IWETH(wethAddress).deposit{value: msg.value}()` (inline cast call IWETH(...).deposit()), `ICreditManager(creditManager).openCreditAccount(
            msg.value,
            onBehalfOf,
            leverageFact` (inline cast call ICreditManager(...).openCreditAccount())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### WETHGateway.repayCreditAccountETH

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: repayCreditAccountETH
- **Line Range**: L179 - L199
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/core/WETHGateway.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`repayCreditAccountETH`, lines=`L179 - L199`

#### 2. Function Source Code
```solidity
function repayCreditAccountETH(address creditManager, address to)
        external
        payable
        override
        wethCreditManagerOnly(creditManager) // T:[WG-3, 4]
    {
        uint256 amount = msg.value; // T: [WG-11]

        IWETH(wethAddress).deposit{value: amount}(); // T: [WG-11]
//        address pool = ICreditManager(creditManager).poolService(); // T: [WG-11]
        _checkAllowance(creditManager, amount); // T: [WG-11]

        // This function is protected from reentrant attack
        uint256 repayAmount = ICreditManager(creditManager)
        .repayCreditAccountETH(msg.sender, to); // T: [WG-11, 13]

        if (amount > repayAmount) {
            IWETH(wethAddress).withdraw(amount.sub(repayAmount));
            msg.sender.sendValue(amount.sub(repayAmount)); // T: [WG-12]
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['wethAddress']
- **External calls**: `IWETH(wethAddress).deposit{value: amount}()` (method: deposit, receiver: IWETH), `ICreditManager(creditManager)
        .repayCreditAccountETH(msg.sender, to)` (method: repayCreditAccountETH, receiver: ICreditManager), `IWETH(wethAddress).withdraw(amount.sub(repayAmount))` (method: withdraw, receiver: IWETH)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['wethAddress']
- **External calls**: `IWETH(wethAddress).deposit{value: amount}()` (inline cast call IWETH(...).deposit()), `ICreditManager(creditManager)
        .repayCreditAccountETH(msg.sender, to)` (inline cast call ICreditManager(...).repayCreditAccountETH()), `IWETH(wethAddress).withdraw(amount.sub(repayAmount))` (inline cast call IWETH(...).withdraw())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Strategy.adjustPosition

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: adjustPosition
- **Line Range**: L400
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Generic Lender/yearnV2-generic-lender-strat-979ef2f0e5da39ca59a5907c37ba2064fcd6be82/contracts/Strategy.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`adjustPosition`, lines=`L400`

#### 2. Function Source Code
```solidity
function adjustPosition(uint256 _debtOutstanding) internal override {
        //we just keep all money in want if we dont have any lenders
        if (lenders.length == 0) {
            return;
        }

        _debtOutstanding; //ignored. we handle it in prepare return
        //emergency exit is dealt with at beginning of harvest
        if (emergencyExit) {
            return;
        }

        (uint256 lowest, uint256 lowestApr, uint256 highest, uint256 potential) = estimateAdjustPosition();

        if (potential > lowestApr) {
            //apr should go down after deposit so wont be withdrawing from self
            // SWC-104-Unchecked Call Return Value: L400
            lenders[lowest].withdrawAll();
        }

        uint256 bal = want.balanceOf(address(this));
        if (bal > 0) {
            want.safeTransfer(address(lenders[highest]), bal);
            lenders[highest].deposit();
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['lenders']
- **External calls**: `lenders[lowest].withdrawAll()` (method: withdrawAll, receiver: lenders), `want.balanceOf(address(this))` (method: balanceOf, receiver: want), `want.safeTransfer(address(lenders[highest]), bal)` (method: safeTransfer, receiver: want), `lenders[highest].deposit()` (method: deposit, receiver: lenders)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['lenders']
- **External calls**: `lenders[lowest].withdrawAll()` (call on contract-typed state var 'lenders' (type: IGenericLender[])), `want.balanceOf(address(this))` (known ERC-like method .balanceOf() on 'want'), `want.safeTransfer(address(lenders[highest]), bal)` (SafeERC20 .safeTransfer()), `lenders[highest].deposit()` (call on contract-typed state var 'lenders' (type: IGenericLender[]))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Strategy.manualAllocation

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: manualAllocation
- **Line Range**: L422
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Generic Lender/yearnV2-generic-lender-strat-979ef2f0e5da39ca59a5907c37ba2064fcd6be82/contracts/Strategy.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`manualAllocation`, lines=`L422`

#### 2. Function Source Code
```solidity
function manualAllocation(lenderRatio[] memory _newPositions) public onlyAuthorized {
        uint256 share = 0;

        // SWC-128-DoS With Block Gas Limit: L421 - L424
        for (uint256 i = 0; i < lenders.length; i++) {
            // SWC-104-Unchecked Call Return Value: L422
            lenders[i].withdrawAll();
        }

        uint256 assets = want.balanceOf(address(this));

        for (uint256 i = 0; i < _newPositions.length; i++) {
            bool found = false;

            //might be annoying and expensive to do this second loop but worth it for safety
            for (uint256 j = 0; j < lenders.length; j++) {
                if (address(lenders[j]) == _newPositions[j].lender) {
                    found = true;
                }
            }
            require(found, "NOT LENDER");

            // SWC-101-Integer Overflow and Underflow: 437
            share += _newPositions[i].share;
            uint256 toSend = assets.mul(_newPositions[i].share).div(1000);
            want.safeTransfer(_newPositions[i].lender, toSend);
            IGenericLender(_newPositions[i].lender).deposit();
        }

        require(share == 1000, "SHARE!=1000");
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['lenders']
- **External calls**: `lenders[i].withdrawAll()` (method: withdrawAll, receiver: lenders), `want.balanceOf(address(this))` (method: balanceOf, receiver: want), `want.safeTransfer(_newPositions[i].lender, toSend)` (method: safeTransfer, receiver: want), `IGenericLender(_newPositions[i].lender).deposit()` (method: deposit, receiver: IGenericLender)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['lenders']
- **External calls**: `lenders[i].withdrawAll()` (call on contract-typed state var 'lenders' (type: IGenericLender[])), `want.balanceOf(address(this))` (known ERC-like method .balanceOf() on 'want'), `want.safeTransfer(_newPositions[i].lender, toSend)` (SafeERC20 .safeTransfer()), `IGenericLender(_newPositions[i].lender).deposit()` (inline cast call IGenericLender(...).deposit())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### yWETH.depositETH

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: depositETH
- **Line Range**: L90 - L104
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Yearn Protocol V1/yearn-protocol-9ff0dc0ea73642c529383d0675930a41bf033295/contracts/vaults/yWETH.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`depositETH`, lines=`L90 - L104`

#### 2. Function Source Code
```solidity
function depositETH() public payable {
        uint _pool = balance();
        uint _before = token.balanceOf(address(this));
        uint _amount = msg.value;
        WETH(address(token)).deposit.value(_amount)();
        uint _after = token.balanceOf(address(this));
        _amount = _after.sub(_before); // Additional check for deflationary tokens
        uint shares = 0;
        if (totalSupply() == 0) {
            shares = _amount;
        } else {
            shares = (_amount.mul(totalSupply())).div(_pool);
        }
        _mint(msg.sender, shares);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['token']
- **External calls**: `token.balanceOf(address(this))` (method: balanceOf, receiver: token), `WETH(address(token)).deposit.value(_amount)` (method: value, receiver: WETH), `token.balanceOf(address(this))` (method: balanceOf, receiver: token)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['token']
- **External calls**: `token.balanceOf(address(this))` (call on contract-typed state var 'token' (type: IERC20)), `WETH(address(token)).deposit.value(_amount)` (call on interface/contract type 'WETH'), `token.balanceOf(address(this))` (call on contract-typed state var 'token' (type: IERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### yWETH.withdrawETH

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdrawETH
- **Line Range**: L144 - L162
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Yearn Protocol V1/yearn-protocol-9ff0dc0ea73642c529383d0675930a41bf033295/contracts/vaults/yWETH.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdrawETH`, lines=`L144 - L162`

#### 2. Function Source Code
```solidity
function withdrawETH(uint _shares) public {
        uint r = (balance().mul(_shares)).div(totalSupply());
        _burn(msg.sender, _shares);

        // Check balance
        uint b = token.balanceOf(address(this));
        if (b < r) {
            uint _withdraw = r.sub(b);
            Controller(controller).withdraw(address(token), _withdraw);
            uint _after = token.balanceOf(address(this));
            uint _diff = _after.sub(b);
            if (_diff < _withdraw) {
                r = b.add(_diff);
            }
        }

        WETH(address(token)).withdraw(r);
        address(msg.sender).transfer(r);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['controller', 'token']
- **External calls**: `token.balanceOf(address(this))` (method: balanceOf, receiver: token), `Controller(controller).withdraw(address(token), _withdraw)` (method: withdraw, receiver: Controller), `token.balanceOf(address(this))` (method: balanceOf, receiver: token), `WETH(address(token)).withdraw(r)` (method: withdraw, receiver: WETH), `address(msg.sender).transfer(r)` (method: transfer, receiver: (complex))
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['controller', 'token']
- **External calls**: `token.balanceOf(address(this))` (call on contract-typed state var 'token' (type: IERC20)), `Controller(controller).withdraw(address(token), _withdraw)` (inline cast call Controller(...).withdraw()), `token.balanceOf(address(this))` (call on contract-typed state var 'token' (type: IERC20)), `WETH(address(token)).withdraw(r)` (inline cast call WETH(...).withdraw()), `address(msg.sender).transfer(r)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### BaseWrapper._deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _deposit
- **Line Range**: L138
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Yearn Vaults V3/yearn-vaults-e390c2a6b2ba6e2ecc8f3a72a1ea4adfabd17544/contracts/BaseWrapper.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_deposit`, lines=`L138`

#### 2. Function Source Code
```solidity
function _deposit(
        address depositor,
        address receiver,
        uint256 amount, // if `MAX_UINT256`, just deposit everything
        bool pullFunds // If true, funds need to be pulled from `depositor` via `transferFrom`
    ) internal returns (uint256 deposited) {
        VaultAPI _bestVault = bestVault();

        if (pullFunds) {
            token.safeTransferFrom(depositor, address(this), amount);
        }

        if (token.allowance(address(this), address(_bestVault)) < amount) {
            token.safeApprove(address(_bestVault), UNLIMITED_APPROVAL); // Vaults are trusted
        }

        // Depositing returns number of shares deposited
        // NOTE: Shortcut here is assuming the number of tokens deposited is equal to the
        //       number of shares credited, which helps avoid an occasional multiplication
        //       overflow if trying to adjust the number of shares by the share price.
        uint256 beforeBal = token.balanceOf(address(this));
        if (receiver != address(this)) {
            _bestVault.deposit(amount, receiver);
        } else if (amount != DEPOSIT_EVERYTHING) {
            _bestVault.deposit(amount);
        } else {
            _bestVault.deposit();
        }

        uint256 afterBal = token.balanceOf(address(this));
        deposited = beforeBal.sub(afterBal);
        // `receiver` now has shares of `_bestVault` as balance, converted to `token` here
        // Issue a refund if not everything was deposited
        // SWC-104-Unchecked Call Return Value: L138
        if (depositor != address(this) && afterBal > 0) token.transfer(depositor, afterBal);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['DEPOSIT_EVERYTHING', 'UNLIMITED_APPROVAL', 'token']
- **External calls**: `token.safeTransferFrom(depositor, address(this), amount)` (method: safeTransferFrom, receiver: token), `token.allowance(address(this), address(_bestVault))` (method: allowance, receiver: token), `token.safeApprove(address(_bestVault), UNLIMITED_APPROVAL)` (method: safeApprove, receiver: token), `token.balanceOf(address(this))` (method: balanceOf, receiver: token), `_bestVault.deposit(amount, receiver)` (method: deposit, receiver: _bestVault), `_bestVault.deposit(amount)` (method: deposit, receiver: _bestVault), `_bestVault.deposit()` (method: deposit, receiver: _bestVault), `token.balanceOf(address(this))` (method: balanceOf, receiver: token), `token.transfer(depositor, afterBal)` (method: transfer, receiver: token)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['DEPOSIT_EVERYTHING', 'UNLIMITED_APPROVAL', 'token']
- **External calls**: `token.safeTransferFrom(depositor, address(this), amount)` (SafeERC20 .safeTransferFrom()), `token.allowance(address(this), address(_bestVault))` (call on contract-typed state var 'token' (type: IERC20)), `token.safeApprove(address(_bestVault), UNLIMITED_APPROVAL)` (SafeERC20 .safeApprove()), `token.balanceOf(address(this))` (call on contract-typed state var 'token' (type: IERC20)), `_bestVault.deposit(amount, receiver)` (call on contract-typed local var '_bestVault' (type: VaultAPI)), `_bestVault.deposit(amount)` (call on contract-typed local var '_bestVault' (type: VaultAPI)), `_bestVault.deposit()` (call on contract-typed local var '_bestVault' (type: VaultAPI)), `token.balanceOf(address(this))` (call on contract-typed state var 'token' (type: IERC20)), `token.transfer(depositor, afterBal)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### BaseWrapper._withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _withdraw
- **Line Range**: L174
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Yearn Vaults V3/yearn-vaults-e390c2a6b2ba6e2ecc8f3a72a1ea4adfabd17544/contracts/BaseWrapper.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_withdraw`, lines=`L174`

#### 2. Function Source Code
(70 lines, showing first 30 + last 15)
```solidity
function _withdraw(
        address sender,
        address receiver,
        uint256 amount, // if `MAX_UINT256`, just withdraw everything
        bool withdrawFromBest // If true, also withdraw from `_bestVault`
    ) internal returns (uint256 withdrawn) {
        VaultAPI _bestVault = bestVault();

        VaultAPI[] memory vaults = allVaults();
        _updateVaultCache(vaults);

        // SWC-128-DoS With Block Gas Limit: L152 - L192
        for (uint256 id = 0; id < vaults.length; id++) {
            if (!withdrawFromBest && vaults[id] == _bestVault) {
                continue; // Don't withdraw from the best
            }

            // Start with the total shares that `sender` has
            uint256 availableShares = vaults[id].balanceOf(sender);

            // Restrict by the allowance that `sender` has to this contract
            // NOTE: No need for allowance check if `sender` is this contract
            if (sender != address(this)) {
                availableShares = Math.min(availableShares, vaults[id].allowance(sender, address(this)));
            }

            // Limit by maximum withdrawal size from each vault
            availableShares = Math.min(availableShares, vaults[id].maxAvailableShares());

            if (availableShares > 0) {
    // ... truncated ...
        // If we have extra, deposit back into `_bestVault` for `sender`
        // NOTE: Invariant is `withdrawn <= amount`
        if (withdrawn > amount) {
            // Don't forget to approve the deposit
            if (token.allowance(address(this), address(_bestVault)) < withdrawn.sub(amount)) {
                token.safeApprove(address(_bestVault), UNLIMITED_APPROVAL); // Vaults are trusted
            }

            _bestVault.deposit(withdrawn.sub(amount), sender);
            withdrawn = amount;
        }

        // `receiver` now has `withdrawn` tokens as balance
        if (receiver != address(this)) token.safeTransfer(receiver, withdrawn);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['UNLIMITED_APPROVAL', 'WITHDRAW_EVERYTHING', 'token']
- **External calls**: `vaults[id].balanceOf(sender)` (method: balanceOf, receiver: vaults), `vaults[id].allowance(sender, address(this))` (method: allowance, receiver: vaults), `vaults[id].maxAvailableShares()` (method: maxAvailableShares, receiver: vaults), `vaults[id].transferFrom(sender, address(this), availableShares)` (method: transferFrom, receiver: vaults), `vaults[id].decimals()` (method: decimals, receiver: vaults), `vaults[id].pricePerShare()` (method: pricePerShare, receiver: vaults), `vaults[id].withdraw(shares)` (method: withdraw, receiver: vaults), `vaults[id].withdraw()` (method: withdraw, receiver: vaults), `token.allowance(address(this), address(_bestVault))` (method: allowance, receiver: token), `token.safeApprove(address(_bestVault), UNLIMITED_APPROVAL)` (method: safeApprove, receiver: token), `_bestVault.deposit(withdrawn.sub(amount), sender)` (method: deposit, receiver: _bestVault), `token.safeTransfer(receiver, withdrawn)` (method: safeTransfer, receiver: token)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['UNLIMITED_APPROVAL', 'WITHDRAW_EVERYTHING', 'token']
- **External calls**: `vaults[id].balanceOf(sender)` (call on contract-typed local var 'vaults' (type: VaultAPI[])), `vaults[id].allowance(sender, address(this))` (call on contract-typed local var 'vaults' (type: VaultAPI[])), `vaults[id].maxAvailableShares()` (call on contract-typed local var 'vaults' (type: VaultAPI[])), `vaults[id].transferFrom(sender, address(this), availableShares)` (call on contract-typed local var 'vaults' (type: VaultAPI[])), `vaults[id].decimals()` (call on contract-typed local var 'vaults' (type: VaultAPI[])), `vaults[id].pricePerShare()` (call on contract-typed local var 'vaults' (type: VaultAPI[])), `vaults[id].withdraw(shares)` (call on contract-typed local var 'vaults' (type: VaultAPI[])), `vaults[id].withdraw()` (call on contract-typed local var 'vaults' (type: VaultAPI[])), `token.allowance(address(this), address(_bestVault))` (call on contract-typed state var 'token' (type: IERC20)), `token.safeApprove(address(_bestVault), UNLIMITED_APPROVAL)` (SafeERC20 .safeApprove()), `_bestVault.deposit(withdrawn.sub(amount), sender)` (call on contract-typed local var '_bestVault' (type: VaultAPI)), `token.safeTransfer(receiver, withdrawn)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### yWETH.withdrawETH

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdrawETH
- **Line Range**: L187
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Yearn Vaults V3/yearn-vaults-e390c2a6b2ba6e2ecc8f3a72a1ea4adfabd17544/contracts/yToken.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdrawETH`, lines=`L187`

#### 2. Function Source Code
```solidity
function withdrawETH(uint256 amount) external returns (uint256 withdrawn) {
        // NOTE: Need to use different method to withdraw than `yToken`
        withdrawn = _withdraw(msg.sender, address(this), amount, true); // `true` = withdraw from `bestVault`
        // NOTE: `BaseWrapper.token` is WETH
        // SWC-107-Reentrancy: L187
        IWETH(address(token)).withdraw(withdrawn);
        // NOTE: Any unintentionally
        msg.sender.sendValue(address(this).balance);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['token']
- **External calls**: `IWETH(address(token)).withdraw(withdrawn)` (method: withdraw, receiver: IWETH)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['token']
- **External calls**: `IWETH(address(token)).withdraw(withdrawn)` (inline cast call IWETH(...).withdraw())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Keep3rV1Oracle._swap

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _swap
- **Line Range**: L849
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Yoracle.Link/yoracle.link-faf1309cbe7a05f70b338351315039eb8e5b9c09/contracts/Keep3rV1Oracle.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_swap`, lines=`L849`

#### 2. Function Source Code
```solidity
function _swap(uint _amount) internal returns (uint) {
        // SWC-104-Unchecked Call Return Value: L849
        KP3R.approve(address(UNI), _amount);

        address[] memory path = new address[](2);
        path[0] = address(KP3R);
        path[1] = address(WETH);

        uint[] memory amounts = UNI.swapExactTokensForTokens(_amount, uint256(0), path, address(this), now.add(1800));
        WETH.withdraw(amounts[1]);
        return amounts[1];
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['KP3R', 'UNI', 'WETH']
- **External calls**: `KP3R.approve(address(UNI), _amount)` (method: approve, receiver: KP3R), `UNI.swapExactTokensForTokens(_amount, uint256(0), path, address(this), now.add(1800))` (method: swapExactTokensForTokens, receiver: UNI), `WETH.withdraw(amounts[1])` (method: withdraw, receiver: WETH)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['KP3R', 'UNI', 'WETH']
- **External calls**: `KP3R.approve(address(UNI), _amount)` (call on contract-typed state var 'KP3R' (type: IKeep3rV1)), `UNI.swapExactTokensForTokens(_amount, uint256(0), path, address(this), now.add(1800))` (call on contract-typed state var 'UNI' (type: IUniswapV2Router)), `WETH.withdraw(amounts[1])` (call on contract-typed state var 'WETH' (type: WETH9))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Main.createBallot

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: createBallot
- **Line Range**: L51
- **File**: `DAppSCAN-source/contracts/QuillAudits-coalichain/CoaliSC-3f0920d650467279f7ceee08776bd74ecadd3237/Main.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`createBallot`, lines=`L51`

#### 2. Function Source Code
```solidity
function createBallot(address[] candidates, uint256 correlationId) public returns (bool){
    
        Voting bl = new Voting(msg.sender, candidates, owner, correlationId);
        // SWC-107-Reentrancy: L51
        ballotAddresses.push(bl);

		emit balloutCreated(bl, correlationId);
		
		    bool isSuccessful = ZuzToken.transferFrom(
            msg.sender,
           owner,
            prices[uint(Types.Service.CREATE_BALLOT)]
        );

        require(isSuccessful == true);
		
		return true;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['ZuzToken', 'ballotAddresses', 'owner', 'prices']
- **External calls**: `ZuzToken.transferFrom(
            msg.sender,
           owner,
            prices[uint(Types.Service.CREATE_BALLOT)]
 ` (method: transferFrom, receiver: ZuzToken)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['ZuzToken', 'ballotAddresses', 'owner', 'prices']
- **External calls**: `ZuzToken.transferFrom(
            msg.sender,
           owner,
            prices[uint(Types.Service.CREATE_BALLOT)]
 ` (call on contract-typed state var 'ZuzToken' (type: CoalichainToken))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### YVaultAssetProxy.reserveDeposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: reserveDeposit
- **Line Range**: L49 - L80
- **File**: `DAppSCAN-source/contracts/Runtime_Vеrification-ElementFinance/elf-contracts-637c6f959315cbb11a164555e588520c7d89122b/contracts/YVaultAssetProxy.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`reserveDeposit`, lines=`L49 - L80`

#### 2. Function Source Code
```solidity
function reserveDeposit(uint256 _amount) external {
        // Transfer from user, note variable 'token' is the immutable
        // inherited from the abstract WrappedPosition contract.
        token.transferFrom(msg.sender, address(this), _amount);
        // Load the reserves
        (uint256 localUnderlying, uint256 localShares) = _getReserves();
        // Calculate the total reserve value
        uint256 totalValue = localUnderlying;
        totalValue += _underlying(localShares);
        // If this is the first deposit we need different logic
        uint256 localReserveSupply = reserveSupply;
        uint256 mintAmount;
        if (localReserveSupply == 0) {
            // If this is the first mint the tokens are exactly the supplied underlying
            mintAmount = _amount;
        } else {
            // Otherwise we mint the proportion that this increases the value held by this contract
            mintAmount = (localReserveSupply * _amount) / totalValue;
        }

        // This hack means that the contract will never have zero balance of underlying
        // which levels the gas expenditure of the transfer to this contract. Permanently locks
        // the smallest possible unit of the underlying.
        if (localUnderlying == 0 && localShares == 0) {
            _amount -= 1;
        }
        // Set the reserves that this contract has more underlying
        _setReserves(localUnderlying + _amount, localShares);
        // Note that the sender has deposited and increase reserveSupply
        reserveBalances[msg.sender] += mintAmount;
        reserveSupply = localReserveSupply + mintAmount;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['reserveBalances', 'reserveSupply', 'token']
- **External calls**: `token.transferFrom(msg.sender, address(this), _amount)` (method: transferFrom, receiver: token)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['reserveBalances', 'reserveSupply', 'token']
- **External calls**: `token.transferFrom(msg.sender, address(this), _amount)` (call on contract-typed state var 'token' (type: IERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### BatchDeposit.batchDeposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: batchDeposit
- **Line Range**: L86 - L122
- **File**: `DAppSCAN-source/contracts/Runtime_Vеrification-Stakefish_BatchDeposit/eth2-batch-deposit-a4912b2d839305da8447b7cec6b2f09238b90e37/contracts/BatchDeposits.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`batchDeposit`, lines=`L86 - L122`

#### 2. Function Source Code
```solidity
function batchDeposit(
        bytes calldata pubkeys, 
        bytes calldata withdrawal_credentials, 
        bytes calldata signatures, 
        bytes32[] calldata deposit_data_roots
    ) 
        external payable whenNotPaused 
    {
        // sanity checks
        require(msg.value % 1 gwei == 0, "BatchDeposit: Deposit value not multiple of GWEI");
        require(msg.value >= DEPOSIT_AMOUNT, "BatchDeposit: Amount is too low");

        uint256 count = deposit_data_roots.length;
        require(count > 0, "BatchDeposit: You should deposit at least one validator");
        require(count <= MAX_VALIDATORS, "BatchDeposit: You can deposit max 100 validators at a time");

        require(pubkeys.length == count * PUBKEY_LENGTH, "BatchDeposit: Pubkey count don't match");
        require(signatures.length == count * SIGNATURE_LENGTH, "BatchDeposit: Signatures count don't match");
        require(withdrawal_credentials.length == 1 * CREDENTIALS_LENGTH, "BatchDeposit: Withdrawal Credentials count don't match");

        uint256 expectedAmount = _fee.add(DEPOSIT_AMOUNT).mul(count);
        require(msg.value == expectedAmount, "BatchDeposit: Amount is not aligned with pubkeys number");

        emit FeeCollected(msg.sender, _fee.mul(count));

        for (uint256 i = 0; i < count; ++i) {
            bytes memory pubkey = bytes(pubkeys[i*PUBKEY_LENGTH:(i+1)*PUBKEY_LENGTH]);
            bytes memory signature = bytes(signatures[i*SIGNATURE_LENGTH:(i+1)*SIGNATURE_LENGTH]);

            IDepositContract(depositContract).deposit{value: DEPOSIT_AMOUNT}(
                pubkey,
                withdrawal_credentials,
                signature,
                deposit_data_roots[i]
            );
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['CREDENTIALS_LENGTH', 'DEPOSIT_AMOUNT', 'MAX_VALIDATORS', 'PUBKEY_LENGTH', 'SIGNATURE_LENGTH', '_fee', 'depositContract']
- **External calls**: `IDepositContract(depositContract).deposit{value: DEPOSIT_AMOUNT}(
                pubkey,
                withdrawal_cre` (method: deposit, receiver: IDepositContract)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['CREDENTIALS_LENGTH', 'DEPOSIT_AMOUNT', 'MAX_VALIDATORS', 'PUBKEY_LENGTH', 'SIGNATURE_LENGTH', '_fee', 'depositContract']
- **External calls**: `IDepositContract(depositContract).deposit{value: DEPOSIT_AMOUNT}(
                pubkey,
                withdrawal_cre` (inline cast call IDepositContract(...).deposit())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### PoolCommitter.commit

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: commit
- **Line Range**: L139-L181
- **File**: `DAppSCAN-source/contracts/Runtime_Vеrification-Tracer_Perpetual_Pools_V2/perpetual-pools-contracts-846bbf62652d7c83aee1cf3766275c4d08b00c8a/contracts/implementation/PoolCommitter.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`commit`, lines=`L139-L181`

#### 2. Function Source Code
```solidity
function commit(
        CommitType commitType,
        uint256 amount,
        bool fromAggregateBalance
    ) external override updateBalance {
        require(amount > 0, "Amount must not be zero");
        ILeveragedPool pool = ILeveragedPool(leveragedPool);
        uint256 updateInterval = pool.updateInterval();
        uint256 lastPriceTimestamp = pool.lastPriceTimestamp();
        uint256 frontRunningInterval = pool.frontRunningInterval();

        uint256 appropriateUpdateIntervalId = PoolSwapLibrary.appropriateUpdateIntervalId(
            block.timestamp,
            lastPriceTimestamp,
            frontRunningInterval,
            updateInterval,
            updateIntervalId
        );
        TotalCommitment storage totalCommit = totalPoolCommitments[appropriateUpdateIntervalId];
        UserCommitment storage userCommit = userCommitments[msg.sender][appropriateUpdateIntervalId];

        userCommit.updateIntervalId = appropriateUpdateIntervalId;

        uint256 length = unAggregatedCommitments[msg.sender].length;
        if (length == 0 || unAggregatedCommitments[msg.sender][length - 1] < appropriateUpdateIntervalId) {
            unAggregatedCommitments[msg.sender].push(appropriateUpdateIntervalId);
        }

        if (commitType == CommitType.LongMint || commitType == CommitType.ShortMint) {
            // minting: pull in the quote token from the committer
            // Do not need to transfer if minting using aggregate balance tokens, since the leveraged pool already owns these tokens.
            if (!fromAggregateBalance) {
                pool.quoteTokenTransferFrom(msg.sender, leveragedPool, amount);
            } else {
                // Want to take away from their balance's settlement tokens
                userAggregateBalance[msg.sender].settlementTokens -= amount;
            }
        }

        applyCommitment(pool, commitType, amount, fromAggregateBalance, userCommit, totalCommit);

        emit CreateCommit(msg.sender, amount, commitType);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['leveragedPool', 'totalPoolCommitments', 'unAggregatedCommitments', 'updateIntervalId', 'userAggregateBalance', 'userCommitments']
- **External calls**: `pool.updateInterval()` (method: updateInterval, receiver: pool), `pool.lastPriceTimestamp()` (method: lastPriceTimestamp, receiver: pool), `pool.frontRunningInterval()` (method: frontRunningInterval, receiver: pool), `PoolSwapLibrary.appropriateUpdateIntervalId(
            block.timestamp,
            lastPriceTimestamp,
            fr` (method: appropriateUpdateIntervalId, receiver: PoolSwapLibrary), `pool.quoteTokenTransferFrom(msg.sender, leveragedPool, amount)` (method: quoteTokenTransferFrom, receiver: pool)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['leveragedPool', 'totalPoolCommitments', 'unAggregatedCommitments', 'updateIntervalId', 'userAggregateBalance', 'userCommitments']
- **External calls**: `pool.updateInterval()` (call on contract-typed local var 'pool' (type: ILeveragedPool)), `pool.lastPriceTimestamp()` (call on contract-typed local var 'pool' (type: ILeveragedPool)), `pool.frontRunningInterval()` (call on contract-typed local var 'pool' (type: ILeveragedPool)), `PoolSwapLibrary.appropriateUpdateIntervalId(
            block.timestamp,
            lastPriceTimestamp,
            fr` (call on interface/contract type 'PoolSwapLibrary'), `pool.quoteTokenTransferFrom(msg.sender, leveragedPool, amount)` (call on contract-typed local var 'pool' (type: ILeveragedPool))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### PoolCommitter.claim

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: claim
- **Line Range**: L187-L201
- **File**: `DAppSCAN-source/contracts/Runtime_Vеrification-Tracer_Perpetual_Pools_V2/perpetual-pools-contracts-846bbf62652d7c83aee1cf3766275c4d08b00c8a/contracts/implementation/PoolCommitter.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`claim`, lines=`L187-L201`

#### 2. Function Source Code
```solidity
function claim(address user) external override updateBalance {
        Balance memory balance = userAggregateBalance[user];
        ILeveragedPool pool = ILeveragedPool(leveragedPool);
        if (balance.settlementTokens > 0) {
            pool.quoteTokenTransfer(user, balance.settlementTokens);
        }
        if (balance.longTokens > 0) {
            pool.poolTokenTransfer(true, user, balance.longTokens);
        }
        if (balance.shortTokens > 0) {
            pool.poolTokenTransfer(false, user, balance.shortTokens);
        }
        delete userAggregateBalance[user];
        emit Claim(user);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['leveragedPool', 'userAggregateBalance']
- **External calls**: `pool.quoteTokenTransfer(user, balance.settlementTokens)` (method: quoteTokenTransfer, receiver: pool), `pool.poolTokenTransfer(true, user, balance.longTokens)` (method: poolTokenTransfer, receiver: pool), `pool.poolTokenTransfer(false, user, balance.shortTokens)` (method: poolTokenTransfer, receiver: pool)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['leveragedPool', 'userAggregateBalance']
- **External calls**: `pool.quoteTokenTransfer(user, balance.settlementTokens)` (call on contract-typed local var 'pool' (type: ILeveragedPool)), `pool.poolTokenTransfer(true, user, balance.longTokens)` (call on contract-typed local var 'pool' (type: ILeveragedPool)), `pool.poolTokenTransfer(false, user, balance.shortTokens)` (call on contract-typed local var 'pool' (type: ILeveragedPool))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StakefishERC721Wrapper.mintTo

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: mintTo
- **Line Range**: L53-L71
- **File**: `DAppSCAN-source/contracts/Runtime_Vеrification-stakefish_ethereum_staking_audit_report/eth2-validation-services-contract-d91928f3a270f6115831fe3a21a69eb98bf57b26/contracts/StakefishERC721Wrapper.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`mintTo`, lines=`L53-L71`

#### 2. Function Source Code
```solidity
function mintTo(address servicesContract, address to, uint256 amount) public nonReentrant returns (uint256) {
        require(amount > 0, "Amount can't be 0");

        uint256 tokenId = _safeMint(to, "");

        _servicesContracts[tokenId] = servicesContract;
        _deposits[tokenId] = amount;

        bool success = IStakefishServicesContract(payable(servicesContract)).transferDepositFrom(
            msg.sender,
            address(this),
            amount
        );
        require(success, "Transfer deposit failed");

        emit Mint(servicesContract, msg.sender, to, amount, tokenId);
        
        return tokenId;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_deposits', '_servicesContracts']
- **External calls**: `IStakefishServicesContract(payable(servicesContract)).transferDepositFrom(
            msg.sender,
            address(t` (method: transferDepositFrom, receiver: IStakefishServicesContract)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['_deposits', '_servicesContracts']
- **External calls**: `IStakefishServicesContract(payable(servicesContract)).transferDepositFrom(
            msg.sender,
            address(t` (inline cast call IStakefishServicesContract(...).transferDepositFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StrategyMDex.updatePool

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: updatePool
- **Line Range**: L241
- **File**: `DAppSCAN-source/contracts/SlowMist-Booster-Protocol_智能安全审计报告/boosterProtocol-946b15629c410d706856584f3aa04001d6a55bd2/contracts/strategies/StrategyMDex.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`updatePool`, lines=`L241`

#### 2. Function Source Code
```solidity
function updatePool(uint256 _pid) public override {
        PoolInfo storage pool = poolInfo[_pid];
        if(pool.lastRewardsBlock == block.number || 
            pool.totalLPAmount.add(pool.totalLPReinvest) == 0) {
            pool.lastRewardsBlock = block.number;
            return ;
        }

        if(address(actionPool) != address(0)) {
            actionPool.onAcionUpdate(_pid);
        }

        pool.lastRewardsBlock = block.number;

        address token0 = pool.collateralToken[0];
        address token1 = pool.collateralToken[1];
        (uint256 uBalanceBefore0, uint256 uBalanceBefore1) = getTokenBalance_this(token0, token1);
        uint256 newRewards = poolClaim(pool.poolId);
        if(newRewards < pool.miniRewardAmount) {
            return ;
        }

        address rewardToken = poolRewardToken(pool.poolId);
        if(utils.getAmountIn(rewardToken, newRewards, pool.baseToken) <= 0) {
            return ;
        }

        // SWC-114-Transaction Order Dependence: L241
        uint256 newRewardBase = utils.getTokenIn(rewardToken, newRewards, pool.baseToken);

        // reinvestment fee
        utils.makeRefundFee(_pid, newRewardBase);

        // balance quantity
        (uint256 uBalanceAfter0, uint256 uBalanceAfter1) = getTokenBalance_this(token0, token1);

        makeBalanceOptimalLiquidityByAmount(_pid, 
                                uBalanceAfter0.sub(uBalanceBefore0), 
                                uBalanceAfter1.sub(uBalanceBefore1));

        (uBalanceAfter0, uBalanceAfter1) = getTokenBalance_this(token0, token1);

        // add liquidity and deposit to mdex pool
        uint256 lpAmount = makeLiquidityAndDepositByAmount(_pid,
                        uBalanceAfter0.sub(uBalanceBefore0), 
                        uBalanceAfter1.sub(uBalanceBefore1));
        (uBalanceAfter0, uBalanceAfter1) = getTokenBalance_this(token0, token1);
        
        pool.totalLPReinvest = pool.totalLPReinvest.add(lpAmount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['actionPool', 'poolInfo', 'utils']
- **External calls**: `actionPool.onAcionUpdate(_pid)` (method: onAcionUpdate, receiver: actionPool), `utils.getAmountIn(rewardToken, newRewards, pool.baseToken)` (method: getAmountIn, receiver: utils), `utils.getTokenIn(rewardToken, newRewards, pool.baseToken)` (method: getTokenIn, receiver: utils), `utils.makeRefundFee(_pid, newRewardBase)` (method: makeRefundFee, receiver: utils), `pool.totalLPReinvest.add(lpAmount)` (method: add, receiver: pool)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['actionPool', 'poolInfo', 'utils']
- **External calls**: `actionPool.onAcionUpdate(_pid)` (call on contract-typed state var 'actionPool' (type: IActionPools)), `utils.getAmountIn(rewardToken, newRewards, pool.baseToken)` (call on contract-typed state var 'utils' (type: StrategyUtils)), `utils.getTokenIn(rewardToken, newRewards, pool.baseToken)` (call on contract-typed state var 'utils' (type: StrategyUtils)), `utils.makeRefundFee(_pid, newRewardBase)` (call on contract-typed state var 'utils' (type: StrategyUtils)), `pool.totalLPReinvest.add(lpAmount)` (call on contract-typed local var 'pool' (type: PoolInfo))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StrategyUtils.getAmountOut

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: getAmountOut
- **Line Range**: L345
- **File**: `DAppSCAN-source/contracts/SlowMist-Booster-Protocol_智能安全审计报告/boosterProtocol-946b15629c410d706856584f3aa04001d6a55bd2/contracts/strategies/StrategyUtils.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`getAmountOut`, lines=`L345`

#### 2. Function Source Code
```solidity
function getAmountOut(address _tokenIn, address _tokenOut, uint256 _amountOut)
            public virtual view returns (uint256) {
        if(_tokenIn == _tokenOut) {
            return _amountOut;
        }
        address[] memory path = new address[](2);
        path[0] = _tokenIn;
        path[1] = _tokenOut;
        // SWC-114-Transaction Order Dependence: L345
        uint256[] memory result = router.getAmountsIn(_amountOut, path);
        if(result.length == 0) {
            return 0;
        }
        return result[0];
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['router']
- **External calls**: `router.getAmountsIn(_amountOut, path)` (method: getAmountsIn, receiver: router)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['router']
- **External calls**: `router.getAmountsIn(_amountOut, path)` (call on contract-typed state var 'router' (type: IMdexRouter))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### StrategyUtils.getTokenInTo

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: getTokenInTo
- **Line Range**: L395
- **File**: `DAppSCAN-source/contracts/SlowMist-Booster-Protocol_智能安全审计报告/boosterProtocol-946b15629c410d706856584f3aa04001d6a55bd2/contracts/strategies/StrategyUtils.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`getTokenInTo`, lines=`L395`

#### 2. Function Source Code
```solidity
function getTokenInTo(address _toAddress, address _tokenIn, uint256 _amountIn, address _tokenOut) 
            internal virtual returns (uint256 value) {
        if(_tokenIn == _tokenOut) {
            value = _amountIn;
            return value;
        }
        address[] memory path = new address[](2);
        path[0] = _tokenIn;
        path[1] = _tokenOut;
        uint256 amountOutMin = 0;
        IERC20(_tokenIn).approve(address(router), uint256(-1));
        require(IERC20(_tokenIn).balanceOf(address(this)) >= _amountIn, 'getTokenInTo not amount in');
        // SWC-114-Transaction Order Dependence: L395
        uint256[] memory result = router.swapExactTokensForTokens(_amountIn, amountOutMin, path, _toAddress, block.timestamp.add(60));
        if(result.length == 0) {
            value = 0;
        } else {
            value = result[result.length-1];
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['router']
- **External calls**: `IERC20(_tokenIn).approve(address(router), uint256(-1))` (method: approve, receiver: IERC20), `IERC20(_tokenIn).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `router.swapExactTokensForTokens(_amountIn, amountOutMin, path, _toAddress, block.timestamp.add(60))` (method: swapExactTokensForTokens, receiver: router)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['router']
- **External calls**: `IERC20(_tokenIn).approve(address(router), uint256(-1))` (inline cast call IERC20(...).approve()), `IERC20(_tokenIn).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `router.swapExactTokensForTokens(_amountIn, amountOutMin, path, _toAddress, block.timestamp.add(60))` (call on contract-typed state var 'router' (type: IMdexRouter))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### BuybackBooToken.buyback

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: buyback
- **Line Range**: L66
- **File**: `DAppSCAN-source/contracts/SlowMist-Booster-Protocol_智能安全审计报告/boosterProtocol-946b15629c410d706856584f3aa04001d6a55bd2/contracts/utils/BuybackBooToken.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`buyback`, lines=`L66`

#### 2. Function Source Code
```solidity
function buyback(address _token, uint256 _value) external override returns (uint256 value) {
        uint256 decimals = uint256(ERC20(_token).decimals());
        if(_value < (10**decimals.div(4))) {
            return 0;
        }

        if(booToken == address(0)) {
            return 0;
        }

        address[] memory path;
        if (USDT != _token) {
            path = new address[](3);
            path[0] = _token;
            path[1] = USDT;
            path[2] = booToken;
        } else {
            path = new address[](2);
            path[0] = _token;
            path[1] = booToken;
        }

        uint256[] memory result;
        result = router.getAmountsOut(_value, path);
        if(result.length == 0 || result[result.length-1] <= 0) {
            return 0;
        }

        IERC20(_token).safeTransferFrom(msg.sender, address(this), _value);
        IERC20(_token).approve(address(router), _value);

        // SWC-114-Transaction Order Dependence: L66
        result = router.swapExactTokensForTokens(_value, 0, path, address(this), block.timestamp.add(60));
        if(result.length == 0) {
            return 0;
        }

        uint256 valueOut = TenMath.min(result[result.length-1],
                                IERC20(booToken).balanceOf(address(this)));

        burnSource[_token] = burnSource[_token].add(_value);
        burnAmount[_token] = burnAmount[_token].add(valueOut);

        IERC20(booToken).transfer(lockedAddr, valueOut);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['USDT', 'booToken', 'burnAmount', 'burnSource', 'lockedAddr', 'router']
- **External calls**: `ERC20(_token).decimals()` (method: decimals, receiver: ERC20), `router.getAmountsOut(_value, path)` (method: getAmountsOut, receiver: router), `IERC20(_token).safeTransferFrom(msg.sender, address(this), _value)` (method: safeTransferFrom, receiver: IERC20), `IERC20(_token).approve(address(router), _value)` (method: approve, receiver: IERC20), `router.swapExactTokensForTokens(_value, 0, path, address(this), block.timestamp.add(60))` (method: swapExactTokensForTokens, receiver: router), `TenMath.min(result[result.length-1],
                                IERC20(booToken).balanceOf(address(this)))` (method: min, receiver: TenMath), `IERC20(booToken).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IERC20(booToken).transfer(lockedAddr, valueOut)` (method: transfer, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['USDT', 'booToken', 'burnAmount', 'burnSource', 'lockedAddr', 'router']
- **External calls**: `ERC20(_token).decimals()` (inline cast call ERC20(...).decimals()), `router.getAmountsOut(_value, path)` (call on contract-typed state var 'router' (type: IMdexRouter)), `IERC20(_token).safeTransferFrom(msg.sender, address(this), _value)` (SafeERC20 .safeTransferFrom()), `IERC20(_token).approve(address(router), _value)` (inline cast call IERC20(...).approve()), `router.swapExactTokensForTokens(_value, 0, path, address(this), block.timestamp.add(60))` (call on contract-typed state var 'router' (type: IMdexRouter)), `TenMath.min(result[result.length-1],
                                IERC20(booToken).balanceOf(address(this)))` (call on interface/contract type 'TenMath'), `IERC20(booToken).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IERC20(booToken).transfer(lockedAddr, valueOut)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### CFVaultV2.withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdraw
- **Line Range**: L121 - L153
- **File**: `DAppSCAN-source/contracts/SlowMist-CFFv2 Smart Contract Security Audit Report/cff-contract-v2-c86bef3f13c7585f547f9cd0ca900f94664e96b7/contracts/core/CFVault.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdraw`, lines=`L121 - L153`

#### 2. Function Source Code
```solidity
function withdraw(uint256 _amount) public{
    require(controller != CFControllerInterface(0x0) && controller.get_current_pool() != ICurvePool(0x0), "paused");
    require(slip != 0, "Slippage not set");
    uint256 amount = IERC20(lp_token).balanceOf(msg.sender);
    require(amount >= _amount, "no enough LP tokens");

    uint LP_token_amount = _amount.safeMul(controller.get_current_pool().get_lp_token_balance()).safeDiv(IERC20(lp_token).totalSupply());

    uint dec = uint(10)**(TransferableToken.decimals(target_token));
    uint vir = controller.get_current_pool().get_virtual_price();
    uint min_amount = LP_token_amount.safeMul(vir).safeMul(slip).safeMul(dec).safeDiv(uint(1e40));

    uint256 _before = TransferableToken.balanceOfAddr(target_token, address(this));
    controller.withdraw(LP_token_amount);
    uint256 _after = TransferableToken.balanceOfAddr(target_token, address(this));
    uint256 target_amount = _after.safeSub(_before);

    require(target_amount >= min_amount, "Slippage");


    if(withdraw_fee_ratio != 0 && fee_pool != address(0x0)){
      uint256 f = target_amount.safeMul(withdraw_fee_ratio).safeDiv(ratio_base);
      uint256 r = target_amount.safeSub(f);
      TransferableToken.transfer(target_token, msg.sender, r);
      TransferableToken.transfer(target_token, fee_pool, f);
      TokenInterfaceERC20(lp_token).destroyTokens(msg.sender, _amount);
      emit CFFWithdraw(msg.sender, r, _amount, f, get_virtual_price());
    }else{
      TransferableToken.transfer(target_token, msg.sender, target_amount);
      TokenInterfaceERC20(lp_token).destroyTokens(msg.sender, _amount);
      emit CFFWithdraw(msg.sender, target_amount, _amount, 0, get_virtual_price());
    }
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['controller', 'fee_pool', 'lp_token', 'ratio_base', 'slip', 'target_token', 'withdraw_fee_ratio']
- **External calls**: `IERC20(lp_token).balanceOf(msg.sender)` (method: balanceOf, receiver: IERC20), `controller.get_current_pool().get_lp_token_balance()` (method: get_lp_token_balance, receiver: controller), `controller.get_current_pool()` (method: get_current_pool, receiver: controller), `IERC20(lp_token).totalSupply()` (method: totalSupply, receiver: IERC20), `TransferableToken.decimals(target_token)` (method: decimals, receiver: TransferableToken), `controller.get_current_pool().get_virtual_price()` (method: get_virtual_price, receiver: controller), `controller.get_current_pool()` (method: get_current_pool, receiver: controller), `LP_token_amount.safeMul(vir).safeMul(slip).safeMul(dec).safeDiv(uint(1e40))` (method: safeDiv, receiver: LP_token_amount), `LP_token_amount.safeMul(vir).safeMul(slip).safeMul(dec)` (method: safeMul, receiver: LP_token_amount), `LP_token_amount.safeMul(vir).safeMul(slip)` (method: safeMul, receiver: LP_token_amount), `TransferableToken.balanceOfAddr(target_token, address(this))` (method: balanceOfAddr, receiver: TransferableToken), `controller.withdraw(LP_token_amount)` (method: withdraw, receiver: controller), `TransferableToken.balanceOfAddr(target_token, address(this))` (method: balanceOfAddr, receiver: TransferableToken), `TransferableToken.transfer(target_token, msg.sender, r)` (method: transfer, receiver: TransferableToken), `TransferableToken.transfer(target_token, fee_pool, f)` (method: transfer, receiver: TransferableToken), `TokenInterfaceERC20(lp_token).destroyTokens(msg.sender, _amount)` (method: destroyTokens, receiver: TokenInterfaceERC20), `TransferableToken.transfer(target_token, msg.sender, target_amount)` (method: transfer, receiver: TransferableToken), `TokenInterfaceERC20(lp_token).destroyTokens(msg.sender, _amount)` (method: destroyTokens, receiver: TokenInterfaceERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['controller', 'fee_pool', 'lp_token', 'ratio_base', 'slip', 'target_token', 'withdraw_fee_ratio']
- **External calls**: `IERC20(lp_token).balanceOf(msg.sender)` (inline cast call IERC20(...).balanceOf()), `controller.get_current_pool().get_lp_token_balance()` (call on contract-typed state var 'controller' (type: CFControllerInterface)), `controller.get_current_pool()` (call on contract-typed state var 'controller' (type: CFControllerInterface)), `IERC20(lp_token).totalSupply()` (inline cast call IERC20(...).totalSupply()), `TransferableToken.decimals(target_token)` (call on interface/contract type 'TransferableToken'), `controller.get_current_pool().get_virtual_price()` (call on contract-typed state var 'controller' (type: CFControllerInterface)), `controller.get_current_pool()` (call on contract-typed state var 'controller' (type: CFControllerInterface)), `LP_token_amount.safeMul(vir).safeMul(slip).safeMul(dec).safeDiv(uint(1e40))` (inline cast call LP_token_amount(...).safeDiv()), `LP_token_amount.safeMul(vir).safeMul(slip).safeMul(dec)` (inline cast call LP_token_amount(...).safeMul()), `LP_token_amount.safeMul(vir).safeMul(slip)` (inline cast call LP_token_amount(...).safeMul()), `TransferableToken.balanceOfAddr(target_token, address(this))` (call on interface/contract type 'TransferableToken'), `controller.withdraw(LP_token_amount)` (call on contract-typed state var 'controller' (type: CFControllerInterface)), `TransferableToken.balanceOfAddr(target_token, address(this))` (call on interface/contract type 'TransferableToken'), `TransferableToken.transfer(target_token, msg.sender, r)` (low-level .transfer()), `TransferableToken.transfer(target_token, fee_pool, f)` (low-level .transfer()), `TokenInterfaceERC20(lp_token).destroyTokens(msg.sender, _amount)` (inline cast call TokenInterfaceERC20(...).destroyTokens()), `TransferableToken.transfer(target_token, msg.sender, target_amount)` (low-level .transfer()), `TokenInterfaceERC20(lp_token).destroyTokens(msg.sender, _amount)` (inline cast call TokenInterfaceERC20(...).destroyTokens())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### PRA.lock

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: lock
- **Line Range**: L66 - L80
- **File**: `DAppSCAN-source/contracts/SlowMist-ForTube2.0 Smart Contract Security Audit Report/bond-854527d0ea7ad2ddd3504b4d4ae3fcb57cb6445d/contracts/PRA.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`lock`, lines=`L66 - L80`

#### 2. Function Source Code
```solidity
function lock() external {
        address who = msg.sender;
        require(deposits[who].amount == 0, "sender already locked");
        require(
            IERC20(gov).allowance(who, address(this)) >= line,
            "insufficient allowance to lock"
        );
        require(
            IERC20(gov).balanceOf(who) >= line,
            "insufficient balance to lock"
        );
        deposits[who].amount = line;
        IERC20(gov).safeTransferFrom(who, address(this), line);
        emit MonitorEvent(who, address(0), "lock", abi.encodePacked(line));
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['deposits', 'gov', 'line']
- **External calls**: `IERC20(gov).allowance(who, address(this))` (method: allowance, receiver: IERC20), `IERC20(gov).balanceOf(who)` (method: balanceOf, receiver: IERC20), `IERC20(gov).safeTransferFrom(who, address(this), line)` (method: safeTransferFrom, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['deposits', 'gov', 'line']
- **External calls**: `IERC20(gov).allowance(who, address(this))` (inline cast call IERC20(...).allowance()), `IERC20(gov).balanceOf(who)` (inline cast call IERC20(...).balanceOf()), `IERC20(gov).safeTransferFrom(who, address(this), line)` (SafeERC20 .safeTransferFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### AlianaMinting._depositFrom

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _depositFrom
- **Line Range**: L254
- **File**: `DAppSCAN-source/contracts/SlowMist-Starcrazy Smart Contract Security Audit Report/starcrazy-contracts-e9e11d234ac065726e108a73dfcd5efbad26f2c5/contract/AlianaMinting.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_depositFrom`, lines=`L254`

#### 2. Function Source Code
```solidity
function _depositFrom(address _from, uint256 _tokenId)
        internal
        whenNotPaused
    {
        require(
            aliana.ownerOf(_tokenId) == _from,
            "AlianaMinting: must be the owner"
        );
        UserInfo storage user = userInfo[_from];
        if (maxMintingNumPerAddress > 0) {
            require(
                user.amountToken.size < maxMintingNumPerAddress,
                "AlianaMinting: too much mining at the same time"
            );
        }
        (, , , , uint256 _amount) = aliana.getAliana(_tokenId);
        require(_amount > 0, "AlianaMinting: gene _amount must > 0");

        updateBlockReward();
        uint256 takePending;
        if (user.amount > 0) {
            uint256 pending = user.amount.mul(accGFTPerShare).div(1e12).sub(
                user.rewardDebt
            );
            if (pending > 0) {
                safeGFTTransfer(_from, pending);
            }
            takePending = pending;
        }

        aliana.transferFrom(address(_from), address(this), _tokenId);
        // SWC-104-Unchecked Call Return Value: L254
        insert(user.amountToken, _tokenId, _amount);
        user.balance = user.balance.add(1);

        user.amount = user.amount.add(_amount);
        labor = labor.add(_amount);

        user.rewardDebt = user.amount.mul(accGFTPerShare).div(1e12);
        emit Deposit(_from, _tokenId, _amount, takePending);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['accGFTPerShare', 'aliana', 'labor', 'maxMintingNumPerAddress', 'userInfo']
- **External calls**: `aliana.ownerOf(_tokenId)` (method: ownerOf, receiver: aliana), `aliana.getAliana(_tokenId)` (method: getAliana, receiver: aliana), `user.amount.mul(accGFTPerShare).div(1e12).sub(
                user.rewardDebt
            )` (method: sub, receiver: user), `user.amount.mul(accGFTPerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(accGFTPerShare)` (method: mul, receiver: user), `aliana.transferFrom(address(_from), address(this), _tokenId)` (method: transferFrom, receiver: aliana), `user.balance.add(1)` (method: add, receiver: user), `user.amount.add(_amount)` (method: add, receiver: user), `user.amount.mul(accGFTPerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(accGFTPerShare)` (method: mul, receiver: user)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['accGFTPerShare', 'aliana', 'labor', 'maxMintingNumPerAddress', 'userInfo']
- **External calls**: `aliana.ownerOf(_tokenId)` (call on contract-typed state var 'aliana' (type: IAliana)), `aliana.getAliana(_tokenId)` (call on contract-typed state var 'aliana' (type: IAliana)), `user.amount.mul(accGFTPerShare).div(1e12).sub(
                user.rewardDebt
            )` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(accGFTPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(accGFTPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `aliana.transferFrom(address(_from), address(this), _tokenId)` (call on contract-typed state var 'aliana' (type: IAliana)), `user.balance.add(1)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.add(_amount)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(accGFTPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(accGFTPerShare)` (call on contract-typed local var 'user' (type: UserInfo))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### ElementBridge.convert

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: convert
- **Line Range**: L463
- **File**: `DAppSCAN-source/contracts/Solidified-Aztec Element Bridge/aztec-connect-bridges-ac2e7194b5887ea11a607b4cf8de0547b3d7fdd0/src/bridges/element/ElementBridge.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`convert`, lines=`L463`

#### 2. Function Source Code
(88 lines, showing first 30 + last 15)
```solidity
function convert(
        AztecTypes.AztecAsset calldata inputAssetA,
        AztecTypes.AztecAsset calldata,
        AztecTypes.AztecAsset calldata outputAssetA,
        AztecTypes.AztecAsset calldata,
        uint256 totalInputValue,
        uint256 interactionNonce,
        uint64 auxData,
        address
    )
        external
        payable
        override
        returns (
            uint256 outputValueA,
            uint256 outputValueB,
            bool isAsync
        )
    {
        // ### INITIALIZATION AND SANITY CHECKS
        if (msg.sender != rollupProcessor) {
            revert INVALID_CALLER();
        }
        if (inputAssetA.id != outputAssetA.id) {
            revert ASSET_IDS_NOT_EQUAL();
        }
        if (inputAssetA.assetType != AztecTypes.AztecAssetType.ERC20) {
            revert ASSET_NOT_ERC20();
        }
        if (interactions[interactionNonce].expiry != 0) {
    // ... truncated ...
        newInteraction.failed = false;
        newInteraction.finalised = false;
        newInteraction.quantityPT = principalTokensAmount;
        newInteraction.trancheAddress = pool.trancheAddress;
        // add the nonce and expiry to our expiry heap
        addNonceAndExpiry(interactionNonce, trancheExpiry);
        // increase our tranche account deposits and holdings
        // other members are left as their initial values (all zeros)
        TrancheAccount storage trancheAccount = trancheAccounts[newInteraction.trancheAddress];
        trancheAccount.numDeposits++;
        trancheAccount.quantityTokensHeld += newInteraction.quantityPT;
        emit Convert(interactionNonce, totalInputValue);
        finaliseExpiredInteractions(MIN_GAS_FOR_FUNCTION_COMPLETION);       
        // we need to get here with MIN_GAS_FOR_FUNCTION_COMPLETION gas to exit.
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['MIN_GAS_FOR_FUNCTION_COMPLETION', 'balancerAddress', 'interactions', 'pools', 'rollupProcessor', 'trancheAccounts']
- **External calls**: `tranche.unlockTimestamp()` (method: unlockTimestamp, receiver: tranche), `ERC20(inputAssetA.erc20Address).approve(balancerAddress, totalInputValue)` (method: approve, receiver: ERC20), `IVault(balancerAddress).swap(
            IVault.SingleSwap({
                poolId: pool.poolId,
                kind:` (method: swap, receiver: IVault), `IVault.SingleSwap({
                poolId: pool.poolId,
                kind: IVault.SwapKind.GIVEN_IN,
               ` (method: SingleSwap, receiver: IVault), `IVault.FundManagement({
                sender: address(this), // the bridge has already received the tokens from the ro` (method: FundManagement, receiver: IVault)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['MIN_GAS_FOR_FUNCTION_COMPLETION', 'balancerAddress', 'interactions', 'pools', 'rollupProcessor', 'trancheAccounts']
- **External calls**: `tranche.unlockTimestamp()` (call on contract-typed local var 'tranche' (type: ITranche)), `ERC20(inputAssetA.erc20Address).approve(balancerAddress, totalInputValue)` (inline cast call ERC20(...).approve()), `IVault(balancerAddress).swap(
            IVault.SingleSwap({
                poolId: pool.poolId,
                kind:` (inline cast call IVault(...).swap()), `IVault.SingleSwap({
                poolId: pool.poolId,
                kind: IVault.SwapKind.GIVEN_IN,
               ` (call on interface/contract type 'IVault'), `IVault.FundManagement({
                sender: address(this), // the bridge has already received the tokens from the ro` (call on interface/contract type 'IVault')
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### FraxPool.mint1t1FRAX

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: mint1t1FRAX
- **Line Range**: L204
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-FraxFinance/frax-solidity-3f0993a70e3496fd27887db7754d68709c84015e/contracts/Frax/Pools/FraxPool.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`mint1t1FRAX`, lines=`L204`

#### 2. Function Source Code
```solidity
function mint1t1FRAX(uint256 collateral_amount, uint256 FRAX_out_min) external notMintPaused {
        uint256 collateral_amount_d18 = collateral_amount * (10 ** missing_decimals);

        require(FRAX.global_collateral_ratio() >= COLLATERAL_RATIO_MAX, "Collateral ratio must be >= 1");
        require((collateral_token.balanceOf(address(this))).sub(unclaimedPoolCollateral).add(collateral_amount) <= pool_ceiling, "[Pool's Closed]: Ceiling reached");
        
        (uint256 frax_amount_d18) = FraxPoolLibrary.calcMint1t1FRAX(
            getCollateralPrice(),
            collateral_amount_d18
        ); //1 FRAX for each $1 worth of collateral

        frax_amount_d18 = (frax_amount_d18.mul(uint(1e6).sub(minting_fee))).div(1e6); //remove precision at the end
        require(FRAX_out_min <= frax_amount_d18, "Slippage limit reached");

        // SWC-104-Unchecked Call Return Value: L204
        collateral_token.transferFrom(msg.sender, address(this), collateral_amount);
        FRAX.pool_mint(msg.sender, frax_amount_d18);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['COLLATERAL_RATIO_MAX', 'FRAX', 'collateral_token', 'minting_fee', 'missing_decimals', 'pool_ceiling', 'unclaimedPoolCollateral']
- **External calls**: `FRAX.global_collateral_ratio()` (method: global_collateral_ratio, receiver: FRAX), `collateral_token.balanceOf(address(this))` (method: balanceOf, receiver: collateral_token), `FraxPoolLibrary.calcMint1t1FRAX(
            getCollateralPrice(),
            collateral_amount_d18
        )` (method: calcMint1t1FRAX, receiver: FraxPoolLibrary), `collateral_token.transferFrom(msg.sender, address(this), collateral_amount)` (method: transferFrom, receiver: collateral_token), `FRAX.pool_mint(msg.sender, frax_amount_d18)` (method: pool_mint, receiver: FRAX)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['COLLATERAL_RATIO_MAX', 'FRAX', 'collateral_token', 'minting_fee', 'missing_decimals', 'pool_ceiling', 'unclaimedPoolCollateral']
- **External calls**: `FRAX.global_collateral_ratio()` (call on contract-typed state var 'FRAX' (type: FRAXStablecoin)), `collateral_token.balanceOf(address(this))` (call on contract-typed state var 'collateral_token' (type: ERC20)), `FraxPoolLibrary.calcMint1t1FRAX(
            getCollateralPrice(),
            collateral_amount_d18
        )` (call on interface/contract type 'FraxPoolLibrary'), `collateral_token.transferFrom(msg.sender, address(this), collateral_amount)` (call on contract-typed state var 'collateral_token' (type: ERC20)), `FRAX.pool_mint(msg.sender, frax_amount_d18)` (call on contract-typed state var 'FRAX' (type: FRAXStablecoin))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### FraxPool.mintFractionalFRAX

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: mintFractionalFRAX
- **Line Range**: L250
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-FraxFinance/frax-solidity-3f0993a70e3496fd27887db7754d68709c84015e/contracts/Frax/Pools/FraxPool.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`mintFractionalFRAX`, lines=`L250`

#### 2. Function Source Code
```solidity
function mintFractionalFRAX(uint256 collateral_amount, uint256 fxs_amount, uint256 FRAX_out_min) external notMintPaused {
        uint256 fxs_price = FRAX.fxs_price();
        uint256 global_collateral_ratio = FRAX.global_collateral_ratio();

        require(global_collateral_ratio < COLLATERAL_RATIO_MAX && global_collateral_ratio > 0, "Collateral ratio needs to be between .000001 and .999999");
        require(collateral_token.balanceOf(address(this)).sub(unclaimedPoolCollateral).add(collateral_amount) <= pool_ceiling, "Pool ceiling reached, no more FRAX can be minted with this collateral");

        uint256 collateral_amount_d18 = collateral_amount * (10 ** missing_decimals);
        FraxPoolLibrary.MintFF_Params memory input_params = FraxPoolLibrary.MintFF_Params(
            fxs_price,
            getCollateralPrice(),
            fxs_amount,
            collateral_amount_d18,
            global_collateral_ratio
        );

        (uint256 mint_amount, uint256 fxs_needed) = FraxPoolLibrary.calcMintFractionalFRAX(input_params);

        mint_amount = (mint_amount.mul(uint(1e6).sub(minting_fee))).div(1e6);
        require(FRAX_out_min <= mint_amount, "Slippage limit reached");
        require(fxs_needed <= fxs_amount, "Not enough FXS inputted");

        // SWC-104-Unchecked Call Return Value: L250
        FXS.pool_burn_from(msg.sender, fxs_needed);
        collateral_token.transferFrom(msg.sender, address(this), collateral_amount);
        FRAX.pool_mint(msg.sender, mint_amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['COLLATERAL_RATIO_MAX', 'FRAX', 'FXS', 'collateral_token', 'minting_fee', 'missing_decimals', 'pool_ceiling', 'unclaimedPoolCollateral']
- **External calls**: `FRAX.fxs_price()` (method: fxs_price, receiver: FRAX), `FRAX.global_collateral_ratio()` (method: global_collateral_ratio, receiver: FRAX), `collateral_token.balanceOf(address(this)).sub(unclaimedPoolCollateral).add(collateral_amount)` (method: add, receiver: collateral_token), `collateral_token.balanceOf(address(this)).sub(unclaimedPoolCollateral)` (method: sub, receiver: collateral_token), `collateral_token.balanceOf(address(this))` (method: balanceOf, receiver: collateral_token), `FraxPoolLibrary.MintFF_Params(
            fxs_price,
            getCollateralPrice(),
            fxs_amount,
        ` (method: MintFF_Params, receiver: FraxPoolLibrary), `FraxPoolLibrary.calcMintFractionalFRAX(input_params)` (method: calcMintFractionalFRAX, receiver: FraxPoolLibrary), `FXS.pool_burn_from(msg.sender, fxs_needed)` (method: pool_burn_from, receiver: FXS), `collateral_token.transferFrom(msg.sender, address(this), collateral_amount)` (method: transferFrom, receiver: collateral_token), `FRAX.pool_mint(msg.sender, mint_amount)` (method: pool_mint, receiver: FRAX)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['COLLATERAL_RATIO_MAX', 'FRAX', 'FXS', 'collateral_token', 'minting_fee', 'missing_decimals', 'pool_ceiling', 'unclaimedPoolCollateral']
- **External calls**: `FRAX.fxs_price()` (call on contract-typed state var 'FRAX' (type: FRAXStablecoin)), `FRAX.global_collateral_ratio()` (call on contract-typed state var 'FRAX' (type: FRAXStablecoin)), `collateral_token.balanceOf(address(this)).sub(unclaimedPoolCollateral).add(collateral_amount)` (call on contract-typed state var 'collateral_token' (type: ERC20)), `collateral_token.balanceOf(address(this)).sub(unclaimedPoolCollateral)` (call on contract-typed state var 'collateral_token' (type: ERC20)), `collateral_token.balanceOf(address(this))` (call on contract-typed state var 'collateral_token' (type: ERC20)), `FraxPoolLibrary.MintFF_Params(
            fxs_price,
            getCollateralPrice(),
            fxs_amount,
        ` (call on interface/contract type 'FraxPoolLibrary'), `FraxPoolLibrary.calcMintFractionalFRAX(input_params)` (call on interface/contract type 'FraxPoolLibrary'), `FXS.pool_burn_from(msg.sender, fxs_needed)` (call on contract-typed state var 'FXS' (type: FRAXShares)), `collateral_token.transferFrom(msg.sender, address(this), collateral_amount)` (call on contract-typed state var 'collateral_token' (type: ERC20)), `FRAX.pool_mint(msg.sender, mint_amount)` (call on contract-typed state var 'FRAX' (type: FRAXStablecoin))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### FraxPool.recollateralizeFRAX

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: recollateralizeFRAX
- **Line Range**: L401
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-FraxFinance/frax-solidity-3f0993a70e3496fd27887db7754d68709c84015e/contracts/Frax/Pools/FraxPool.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`recollateralizeFRAX`, lines=`L401`

#### 2. Function Source Code
```solidity
function recollateralizeFRAX(uint256 collateral_amount, uint256 FXS_out_min) external {
        require(recollateralizePaused == false, "Recollateralize is paused");
        uint256 collateral_amount_d18 = collateral_amount * (10 ** missing_decimals);
        uint256 fxs_price = FRAX.fxs_price();
        uint256 frax_total_supply = FRAX.totalSupply();
        uint256 global_collateral_ratio = FRAX.global_collateral_ratio();
        uint256 global_collat_value = FRAX.globalCollateralValue();

        (uint256 collateral_units, uint256 amount_to_recollat) = FraxPoolLibrary.calcRecollateralizeFRAXInner(
            collateral_amount_d18,
            getCollateralPrice(),
            global_collat_value,
            frax_total_supply,
            global_collateral_ratio
        ); 

        uint256 collateral_units_precision = collateral_units.div(10 ** missing_decimals);

        uint256 fxs_paid_back = amount_to_recollat.mul(uint(1e6).add(bonus_rate).sub(recollat_fee)).div(fxs_price);

        require(FXS_out_min <= fxs_paid_back, "Slippage limit reached");
        // SWC-104-Unchecked Call Return Value: L401
        collateral_token.transferFrom(msg.sender, address(this), collateral_units_precision);
        FXS.pool_mint(msg.sender, fxs_paid_back);
        
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['FRAX', 'FXS', 'bonus_rate', 'collateral_token', 'missing_decimals', 'recollat_fee', 'recollateralizePaused']
- **External calls**: `FRAX.fxs_price()` (method: fxs_price, receiver: FRAX), `FRAX.totalSupply()` (method: totalSupply, receiver: FRAX), `FRAX.global_collateral_ratio()` (method: global_collateral_ratio, receiver: FRAX), `FRAX.globalCollateralValue()` (method: globalCollateralValue, receiver: FRAX), `FraxPoolLibrary.calcRecollateralizeFRAXInner(
            collateral_amount_d18,
            getCollateralPrice(),
     ` (method: calcRecollateralizeFRAXInner, receiver: FraxPoolLibrary), `collateral_token.transferFrom(msg.sender, address(this), collateral_units_precision)` (method: transferFrom, receiver: collateral_token), `FXS.pool_mint(msg.sender, fxs_paid_back)` (method: pool_mint, receiver: FXS)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['FRAX', 'FXS', 'bonus_rate', 'collateral_token', 'missing_decimals', 'recollat_fee', 'recollateralizePaused']
- **External calls**: `FRAX.fxs_price()` (call on contract-typed state var 'FRAX' (type: FRAXStablecoin)), `FRAX.totalSupply()` (call on contract-typed state var 'FRAX' (type: FRAXStablecoin)), `FRAX.global_collateral_ratio()` (call on contract-typed state var 'FRAX' (type: FRAXStablecoin)), `FRAX.globalCollateralValue()` (call on contract-typed state var 'FRAX' (type: FRAXStablecoin)), `FraxPoolLibrary.calcRecollateralizeFRAXInner(
            collateral_amount_d18,
            getCollateralPrice(),
     ` (call on interface/contract type 'FraxPoolLibrary'), `collateral_token.transferFrom(msg.sender, address(this), collateral_units_precision)` (call on contract-typed state var 'collateral_token' (type: ERC20)), `FXS.pool_mint(msg.sender, fxs_paid_back)` (call on contract-typed state var 'FXS' (type: FRAXShares))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### TWAMM.provideLiquidity

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: provideLiquidity
- **Line Range**: L135-L136
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-FraxQ42021/frax-solidity-bd40775e283923aa9e32a107abd426430a99835e/src/hardhat/contracts/FPI/TWAMM.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`provideLiquidity`, lines=`L135-L136`

#### 2. Function Source Code
```solidity
function provideLiquidity(uint256 lpTokenAmount) external {
        require(totalSupply() != 0, 'EC3');

        //execute virtual orders 
        longTermOrders.executeVirtualOrdersUntilCurrentBlock(reserveMap);

        //the ratio between the number of underlying tokens and the number of lp tokens must remain invariant after mint 
        uint256 amountAIn = lpTokenAmount * reserveMap[tokenA] / totalSupply();
        uint256 amountBIn = lpTokenAmount * reserveMap[tokenB] / totalSupply();
        // SWC-104-Unchecked Call Return Value: L135-L136
        ERC20(tokenA).transferFrom(msg.sender, address(this), amountAIn);
        ERC20(tokenB).transferFrom(msg.sender, address(this), amountBIn);

        reserveMap[tokenA] += amountAIn;
        reserveMap[tokenB] += amountBIn;

        _mint(msg.sender, lpTokenAmount);

        emit LiquidityProvided(msg.sender, lpTokenAmount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['longTermOrders', 'reserveMap', 'tokenA', 'tokenB']
- **External calls**: `longTermOrders.executeVirtualOrdersUntilCurrentBlock(reserveMap)` (method: executeVirtualOrdersUntilCurrentBlock, receiver: longTermOrders), `ERC20(tokenA).transferFrom(msg.sender, address(this), amountAIn)` (method: transferFrom, receiver: ERC20), `ERC20(tokenB).transferFrom(msg.sender, address(this), amountBIn)` (method: transferFrom, receiver: ERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['longTermOrders', 'reserveMap', 'tokenA', 'tokenB']
- **External calls**: `longTermOrders.executeVirtualOrdersUntilCurrentBlock(reserveMap)` (call on contract-typed state var 'longTermOrders' (type: LongTermOrdersLib.LongTermOrders)), `ERC20(tokenA).transferFrom(msg.sender, address(this), amountAIn)` (inline cast call ERC20(...).transferFrom()), `ERC20(tokenB).transferFrom(msg.sender, address(this), amountBIn)` (inline cast call ERC20(...).transferFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### FujiVault.deposit

**Pre-classification**: ⚠️ MISLOCATED
**Reason**: No delegatecall in function — vulnerability may be in a different function

#### 1. SWC Annotation
- **Category**: SWC-112-Delegatecall to Untrusted Callee
- **SWC Code**: SWC-112
- **Annotated Function**: deposit
- **Line Range**: L177 - L178
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-FujiProtocol/fuji-protocol-933ea57b11889d87744efa23e95c90b7bf589402/contracts/FujiVault.sol`
- **Original SWC entry**: category=`SWC-112-Delegatecall to Untrusted Callee`, function=`deposit`, lines=`L177 - L178`

#### 2. Function Source Code
```solidity
function deposit(uint256 _collateralAmount) public payable override {
    if (vAssets.collateralAsset == ETH) {
      require(msg.value == _collateralAmount && _collateralAmount != 0, Errors.VL_AMOUNT_ERROR);
    } else {
      require(_collateralAmount != 0, Errors.VL_AMOUNT_ERROR);
      IERC20Upgradeable(vAssets.collateralAsset).safeTransferFrom(
        msg.sender,
        address(this),
        _collateralAmount
      );
    }

    // Delegate Call Deposit to current provider
    // SWC-112-Delegatecall to Untrusted Callee: L177 - L178
    _deposit(_collateralAmount, address(activeProvider));

    // Collateral Management
    IFujiERC1155(fujiERC1155).mint(msg.sender, vAssets.collateralID, _collateralAmount, "");

    emit Deposit(msg.sender, vAssets.collateralAsset, _collateralAmount);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['ETH', 'activeProvider', 'fujiERC1155', 'vAssets']
- **External calls**: `IERC20Upgradeable(vAssets.collateralAsset).safeTransferFrom(
        msg.sender,
        address(this),
        _collate` (method: safeTransferFrom, receiver: IERC20Upgradeable), `IFujiERC1155(fujiERC1155).mint(msg.sender, vAssets.collateralID, _collateralAmount, "")` (method: mint, receiver: IFujiERC1155)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['ETH', 'activeProvider', 'fujiERC1155', 'vAssets']
- **External calls**: `IERC20Upgradeable(vAssets.collateralAsset).safeTransferFrom(
        msg.sender,
        address(this),
        _collate` (SafeERC20 .safeTransferFrom()), `IFujiERC1155(fujiERC1155).mint(msg.sender, vAssets.collateralID, _collateralAmount, "")` (inline cast call IFujiERC1155(...).mint())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### FujiVault.withdraw

**Pre-classification**: ⚠️ MISLOCATED
**Reason**: No delegatecall in function — vulnerability may be in a different function

#### 1. SWC Annotation
- **Category**: SWC-112-Delegatecall to Untrusted Callee
- **SWC Code**: SWC-112
- **Annotated Function**: withdraw
- **Line Range**: L227
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-FujiProtocol/fuji-protocol-933ea57b11889d87744efa23e95c90b7bf589402/contracts/FujiVault.sol`
- **Original SWC entry**: category=`SWC-112-Delegatecall to Untrusted Callee`, function=`withdraw`, lines=`L227`

#### 2. Function Source Code
```solidity
function withdraw(int256 _withdrawAmount) public override nonReentrant {
    // Logic used when called by Normal User
    updateF1155Balances();

    // Get User Collateral in this Vault
    uint256 providedCollateral = IFujiERC1155(fujiERC1155).balanceOf(
      msg.sender,
      vAssets.collateralID
    );

    // Check User has collateral
    require(providedCollateral > 0, Errors.VL_INVALID_COLLATERAL);

    // Get Required Collateral with Factors to maintain debt position healthy
    uint256 neededCollateral = getNeededCollateralFor(
      IFujiERC1155(fujiERC1155).balanceOf(msg.sender, vAssets.borrowID),
      true
    );

    uint256 amountToWithdraw = _withdrawAmount < 0
      ? providedCollateral - neededCollateral
      : uint256(_withdrawAmount);

    // Check Withdrawal amount, and that it will not fall undercollaterized.
    require(
      amountToWithdraw != 0 && providedCollateral - amountToWithdraw >= neededCollateral,
      Errors.VL_INVALID_WITHDRAW_AMOUNT
    );

    // Collateral Management before Withdraw Operation
    IFujiERC1155(fujiERC1155).burn(msg.sender, vAssets.collateralID, amountToWithdraw);

    // Delegate Call Withdraw to current provider
    // SWC-112-Delegatecall to Untrusted Callee: L227
    _withdraw(amountToWithdraw, address(activeProvider));

    // Transer Assets to User
    IERC20Upgradeable(vAssets.collateralAsset).univTransfer(payable(msg.sender), amountToWithdraw);

    emit Withdraw(msg.sender, vAssets.collateralAsset, amountToWithdraw);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['activeProvider', 'fujiERC1155', 'vAssets']
- **External calls**: `IFujiERC1155(fujiERC1155).balanceOf(
      msg.sender,
      vAssets.collateralID
    )` (method: balanceOf, receiver: IFujiERC1155), `IFujiERC1155(fujiERC1155).balanceOf(msg.sender, vAssets.borrowID)` (method: balanceOf, receiver: IFujiERC1155), `IFujiERC1155(fujiERC1155).burn(msg.sender, vAssets.collateralID, amountToWithdraw)` (method: burn, receiver: IFujiERC1155), `IERC20Upgradeable(vAssets.collateralAsset).univTransfer(payable(msg.sender), amountToWithdraw)` (method: univTransfer, receiver: IERC20Upgradeable)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['activeProvider', 'fujiERC1155', 'vAssets']
- **External calls**: `IFujiERC1155(fujiERC1155).balanceOf(
      msg.sender,
      vAssets.collateralID
    )` (inline cast call IFujiERC1155(...).balanceOf()), `IFujiERC1155(fujiERC1155).balanceOf(msg.sender, vAssets.borrowID)` (inline cast call IFujiERC1155(...).balanceOf()), `IFujiERC1155(fujiERC1155).burn(msg.sender, vAssets.collateralID, amountToWithdraw)` (inline cast call IFujiERC1155(...).burn()), `IERC20Upgradeable(vAssets.collateralAsset).univTransfer(payable(msg.sender), amountToWithdraw)` (inline cast call IERC20Upgradeable(...).univTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### FujiVault.borrow

**Pre-classification**: ⚠️ MISLOCATED
**Reason**: No delegatecall in function — vulnerability may be in a different function

#### 1. SWC Annotation
- **Category**: SWC-112-Delegatecall to Untrusted Callee
- **SWC Code**: SWC-112
- **Annotated Function**: borrow
- **Line Range**: L291
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-FujiProtocol/fuji-protocol-933ea57b11889d87744efa23e95c90b7bf589402/contracts/FujiVault.sol`
- **Original SWC entry**: category=`SWC-112-Delegatecall to Untrusted Callee`, function=`borrow`, lines=`L291`

#### 2. Function Source Code
```solidity
function borrow(uint256 _borrowAmount) public override nonReentrant {
    updateF1155Balances();

    uint256 providedCollateral = IFujiERC1155(fujiERC1155).balanceOf(
      msg.sender,
      vAssets.collateralID
    );

    uint256 debtPrincipal = IFujiERC1155(fujiERC1155).balanceOf(msg.sender, vAssets.borrowID);
    uint256 totalBorrow = _borrowAmount + debtPrincipal;
    // Get Required Collateral with Factors to maintain debt position healthy
    uint256 neededCollateral = getNeededCollateralFor(totalBorrow, true);

    // Check Provided Collateral is not Zero, and greater than needed to maintain healthy position
    require(
      _borrowAmount != 0 && providedCollateral > neededCollateral,
      Errors.VL_INVALID_BORROW_AMOUNT
    );

    // Update timestamp for fee calculation

    uint256 userFee = (debtPrincipal *
      (block.timestamp - _userFeeTimestamps[msg.sender]) *
      protocolFee.a) /
      protocolFee.b /
      ONE_YEAR;

    _userFeeTimestamps[msg.sender] =
      block.timestamp -
      (userFee * ONE_YEAR * protocolFee.a) /
      protocolFee.b /
      totalBorrow;

    // Debt Management
    // SWC-112-Delegatecall to Untrusted Callee: L291
    IFujiERC1155(fujiERC1155).mint(msg.sender, vAssets.borrowID, _borrowAmount, "");

    // Delegate Call Borrow to current provider
    _borrow(_borrowAmount, address(activeProvider));

    // Transer Assets to User
    IERC20Upgradeable(vAssets.borrowAsset).univTransfer(payable(msg.sender), _borrowAmount);

    emit Borrow(msg.sender, vAssets.borrowAsset, _borrowAmount);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['ONE_YEAR', '_userFeeTimestamps', 'activeProvider', 'fujiERC1155', 'protocolFee', 'vAssets']
- **External calls**: `IFujiERC1155(fujiERC1155).balanceOf(
      msg.sender,
      vAssets.collateralID
    )` (method: balanceOf, receiver: IFujiERC1155), `IFujiERC1155(fujiERC1155).balanceOf(msg.sender, vAssets.borrowID)` (method: balanceOf, receiver: IFujiERC1155), `IFujiERC1155(fujiERC1155).mint(msg.sender, vAssets.borrowID, _borrowAmount, "")` (method: mint, receiver: IFujiERC1155), `IERC20Upgradeable(vAssets.borrowAsset).univTransfer(payable(msg.sender), _borrowAmount)` (method: univTransfer, receiver: IERC20Upgradeable)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['ONE_YEAR', '_userFeeTimestamps', 'activeProvider', 'fujiERC1155', 'protocolFee', 'vAssets']
- **External calls**: `IFujiERC1155(fujiERC1155).balanceOf(
      msg.sender,
      vAssets.collateralID
    )` (inline cast call IFujiERC1155(...).balanceOf()), `IFujiERC1155(fujiERC1155).balanceOf(msg.sender, vAssets.borrowID)` (inline cast call IFujiERC1155(...).balanceOf()), `IFujiERC1155(fujiERC1155).mint(msg.sender, vAssets.borrowID, _borrowAmount, "")` (inline cast call IFujiERC1155(...).mint()), `IERC20Upgradeable(vAssets.borrowAsset).univTransfer(payable(msg.sender), _borrowAmount)` (inline cast call IERC20Upgradeable(...).univTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### FujiVault.payback

**Pre-classification**: ⚠️ MISLOCATED
**Reason**: No delegatecall in function — vulnerability may be in a different function

#### 1. SWC Annotation
- **Category**: SWC-112-Delegatecall to Untrusted Callee
- **SWC Code**: SWC-112
- **Annotated Function**: payback
- **Line Range**: L340
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-FujiProtocol/fuji-protocol-933ea57b11889d87744efa23e95c90b7bf589402/contracts/FujiVault.sol`
- **Original SWC entry**: category=`SWC-112-Delegatecall to Untrusted Callee`, function=`payback`, lines=`L340`

#### 2. Function Source Code
```solidity
function payback(int256 _repayAmount) public payable override {
    // Logic used when called by normal user
    updateF1155Balances();

    uint256 debtBalance = IFujiERC1155(fujiERC1155).balanceOf(msg.sender, vAssets.borrowID);
    uint256 userFee = _userProtocolFee(msg.sender, debtBalance);

    // Check User Debt is greater than Zero and amount is not Zero
    require(uint256(_repayAmount) > userFee && debtBalance > 0, Errors.VL_NO_DEBT_TO_PAYBACK);

    // TODO: Get => corresponding amount of BaseProtocol Debt and FujiDebt

    // If passed argument amount is negative do MAX
    uint256 amountToPayback = _repayAmount < 0 ? debtBalance + userFee : uint256(_repayAmount);

    if (vAssets.borrowAsset == ETH) {
      require(msg.value >= amountToPayback, Errors.VL_AMOUNT_ERROR);
      if (msg.value > amountToPayback) {
        IERC20Upgradeable(vAssets.borrowAsset).univTransfer(
          payable(msg.sender),
          msg.value - amountToPayback
        );
      }
    } else {
      // Check User Allowance
      require(
        IERC20Upgradeable(vAssets.borrowAsset).allowance(msg.sender, address(this)) >=
          amountToPayback,
        Errors.VL_MISSING_ERC20_ALLOWANCE
      );

      // Transfer Asset from User to Vault
      // SWC-112-Delegatecall to Untrusted Callee: L340
      IERC20Upgradeable(vAssets.borrowAsset).safeTransferFrom(
        msg.sender,
        address(this),
        amountToPayback
      );
    }

    // Delegate Call Payback to current provider
    _payback(amountToPayback - userFee, address(activeProvider));

    // Debt Management
    IFujiERC1155(fujiERC1155).burn(msg.sender, vAssets.borrowID, amountToPayback - userFee);

    // Update protocol fees
    _userFeeTimestamps[msg.sender] = block.timestamp;
    remainingProtocolFee += userFee;

    emit Payback(msg.sender, vAssets.borrowAsset, debtBalance);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['ETH', '_userFeeTimestamps', 'activeProvider', 'fujiERC1155', 'remainingProtocolFee', 'vAssets']
- **External calls**: `IFujiERC1155(fujiERC1155).balanceOf(msg.sender, vAssets.borrowID)` (method: balanceOf, receiver: IFujiERC1155), `IERC20Upgradeable(vAssets.borrowAsset).univTransfer(
          payable(msg.sender),
          msg.value - amountToPaybac` (method: univTransfer, receiver: IERC20Upgradeable), `IERC20Upgradeable(vAssets.borrowAsset).allowance(msg.sender, address(this))` (method: allowance, receiver: IERC20Upgradeable), `IERC20Upgradeable(vAssets.borrowAsset).safeTransferFrom(
        msg.sender,
        address(this),
        amountToPayb` (method: safeTransferFrom, receiver: IERC20Upgradeable), `IFujiERC1155(fujiERC1155).burn(msg.sender, vAssets.borrowID, amountToPayback - userFee)` (method: burn, receiver: IFujiERC1155)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['ETH', '_userFeeTimestamps', 'activeProvider', 'fujiERC1155', 'remainingProtocolFee', 'vAssets']
- **External calls**: `IFujiERC1155(fujiERC1155).balanceOf(msg.sender, vAssets.borrowID)` (inline cast call IFujiERC1155(...).balanceOf()), `IERC20Upgradeable(vAssets.borrowAsset).univTransfer(
          payable(msg.sender),
          msg.value - amountToPaybac` (inline cast call IERC20Upgradeable(...).univTransfer()), `IERC20Upgradeable(vAssets.borrowAsset).allowance(msg.sender, address(this))` (inline cast call IERC20Upgradeable(...).allowance()), `IERC20Upgradeable(vAssets.borrowAsset).safeTransferFrom(
        msg.sender,
        address(this),
        amountToPayb` (SafeERC20 .safeTransferFrom()), `IFujiERC1155(fujiERC1155).burn(msg.sender, vAssets.borrowID, amountToPayback - userFee)` (inline cast call IFujiERC1155(...).burn())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Governor._queueOrRevert

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call present — unchecked return value plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _queueOrRevert
- **Line Range**: L158 - L172
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-OriginDollar/origin-dollar-81431fd3b2aa4c518ffc389844f9708c00b516f0/contracts/contracts/governance/Governor.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_queueOrRevert`, lines=`L158 - L172`

#### 2. Function Source Code
```solidity
function _queueOrRevert(
        address target,
        uint256 value,
        string memory signature,
        bytes memory data,
        uint256 eta
    ) internal {
        require(
            !timelock.queuedTransactions(
                keccak256(abi.encode(target, value, signature, data, eta))
            ),
            "Governor::_queueOrRevert: proposal action already queued at eta"
        );
        timelock.queueTransaction(target, value, signature, data, eta);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['timelock']
- **External calls**: `timelock.queueTransaction(target, value, signature, data, eta)` (method: queueTransaction, receiver: timelock)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['timelock']
- **External calls**: `timelock.queueTransaction(target, value, signature, data, eta)` (call on contract-typed state var 'timelock' (type: ITimelock))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Governor.execute

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call present — unchecked return value plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: execute
- **Line Range**: L175 - L192
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-OriginDollar/origin-dollar-81431fd3b2aa4c518ffc389844f9708c00b516f0/contracts/contracts/governance/Governor.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`execute`, lines=`L175 - L192`

#### 2. Function Source Code
```solidity
function execute(uint256 proposalId) public payable {
        require(
            state(proposalId) == ProposalState.Queued,
            "Governor::execute: proposal can only be executed if it is queued"
        );
        Proposal storage proposal = proposals[proposalId];
        proposal.executed = true;
        for (uint256 i = 0; i < proposal.targets.length; i++) {
            timelock.executeTransaction.value(proposal.values[i])(
                proposal.targets[i],
                proposal.values[i],
                proposal.signatures[i],
                proposal.calldatas[i],
                proposal.eta
            );
        }
        emit ProposalExecuted(proposalId);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['proposals', 'timelock']
- **External calls**: `timelock.executeTransaction.value(proposal.values[i])` (method: value, receiver: timelock)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['proposals', 'timelock']
- **External calls**: `timelock.executeTransaction.value(proposal.values[i])` (call on contract-typed state var 'timelock' (type: ITimelock))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Governor.__queueSetTimelockPendingAdmin

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call present — unchecked return value plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: __queueSetTimelockPendingAdmin
- **Line Range**: L217 - L232
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-OriginDollar/origin-dollar-81431fd3b2aa4c518ffc389844f9708c00b516f0/contracts/contracts/governance/Governor.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`__queueSetTimelockPendingAdmin`, lines=`L217 - L232`

#### 2. Function Source Code
```solidity
function __queueSetTimelockPendingAdmin(
        address newPendingAdmin,
        uint256 eta
    ) public {
        require(
            msg.sender == guardian,
            "Governor::__queueSetTimelockPendingAdmin: sender must be gov guardian"
        );
        timelock.queueTransaction(
            address(timelock),
            0,
            "setPendingAdmin(address)",
            abi.encode(newPendingAdmin),
            eta
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['guardian', 'timelock']
- **External calls**: `timelock.queueTransaction(
            address(timelock),
            0,
            "setPendingAdmin(address)",
       ` (method: queueTransaction, receiver: timelock)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['guardian', 'timelock']
- **External calls**: `timelock.queueTransaction(
            address(timelock),
            0,
            "setPendingAdmin(address)",
       ` (call on contract-typed state var 'timelock' (type: ITimelock))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Governor.__executeSetTimelockPendingAdmin

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call present — unchecked return value plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: __executeSetTimelockPendingAdmin
- **Line Range**: L235 - L250
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-OriginDollar/origin-dollar-81431fd3b2aa4c518ffc389844f9708c00b516f0/contracts/contracts/governance/Governor.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`__executeSetTimelockPendingAdmin`, lines=`L235 - L250`

#### 2. Function Source Code
```solidity
function __executeSetTimelockPendingAdmin(
        address newPendingAdmin,
        uint256 eta
    ) public {
        require(
            msg.sender == guardian,
            "Governor::__executeSetTimelockPendingAdmin: sender must be gov guardian"
        );
        timelock.executeTransaction(
            address(timelock),
            0,
            "setPendingAdmin(address)",
            abi.encode(newPendingAdmin),
            eta
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['guardian', 'timelock']
- **External calls**: `timelock.executeTransaction(
            address(timelock),
            0,
            "setPendingAdmin(address)",
     ` (method: executeTransaction, receiver: timelock)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['guardian', 'timelock']
- **External calls**: `timelock.executeTransaction(
            address(timelock),
            0,
            "setPendingAdmin(address)",
     ` (call on contract-typed state var 'timelock' (type: ITimelock))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### CompoundStrategy.liquidate

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: liquidate
- **Line Range**: L79
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-OriginDollar/origin-dollar-81431fd3b2aa4c518ffc389844f9708c00b516f0/contracts/contracts/strategies/CompoundStrategy.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`liquidate`, lines=`L79`

#### 2. Function Source Code
```solidity
function liquidate() external onlyVaultOrGovernor {
        for (uint256 i = 0; i < assetsMapped.length; i++) {
            // Redeem entire balance of cToken
            ICERC20 cToken = _getCTokenFor(assetsMapped[i]);
            if (cToken.balanceOf(address(this)) > 0) {
                // SWC-104-Unchecked Call Return Value: L79
                cToken.redeem(cToken.balanceOf(address(this)));
                // Transfer entire balance to Vault
                IERC20 asset = IERC20(assetsMapped[i]);
                asset.safeTransfer(
                    vaultAddress,
                    asset.balanceOf(address(this))
                );
            }
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['assetsMapped', 'vaultAddress']
- **External calls**: `cToken.balanceOf(address(this))` (method: balanceOf, receiver: cToken), `cToken.redeem(cToken.balanceOf(address(this)))` (method: redeem, receiver: cToken), `cToken.balanceOf(address(this))` (method: balanceOf, receiver: cToken), `asset.safeTransfer(
                    vaultAddress,
                    asset.balanceOf(address(this))
               ` (method: safeTransfer, receiver: asset), `asset.balanceOf(address(this))` (method: balanceOf, receiver: asset)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['assetsMapped', 'vaultAddress']
- **External calls**: `cToken.balanceOf(address(this))` (call on contract-typed local var 'cToken' (type: ICERC20)), `cToken.redeem(cToken.balanceOf(address(this)))` (call on contract-typed local var 'cToken' (type: ICERC20)), `cToken.balanceOf(address(this))` (call on contract-typed local var 'cToken' (type: ICERC20)), `asset.safeTransfer(
                    vaultAddress,
                    asset.balanceOf(address(this))
               ` (SafeERC20 .safeTransfer()), `asset.balanceOf(address(this))` (call on contract-typed local var 'asset' (type: IERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### VaultAdmin._harvest

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _harvest
- **Line Range**: L266 - L298
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-OriginDollar/origin-dollar-81431fd3b2aa4c518ffc389844f9708c00b516f0/contracts/contracts/vault/VaultAdmin.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_harvest`, lines=`L266 - L298`

#### 2. Function Source Code
```solidity
function _harvest(address _strategyAddr) internal {
        IStrategy strategy = IStrategy(_strategyAddr);
        address rewardTokenAddress = strategy.rewardTokenAddress();
        if (rewardTokenAddress != address(0)) {
            strategy.collectRewardToken();

            if (uniswapAddr != address(0)) {
                IERC20 rewardToken = IERC20(strategy.rewardTokenAddress());
                uint256 rewardTokenAmount = rewardToken.balanceOf(
                    address(this)
                );
                if (rewardTokenAmount > 0) {
                    // Give Uniswap full amount allowance
                    rewardToken.safeApprove(uniswapAddr, 0);
                    rewardToken.safeApprove(uniswapAddr, rewardTokenAmount);

                    // Uniswap redemption path
                    address[] memory path = new address[](3);
                    path[0] = strategy.rewardTokenAddress();
                    path[1] = IUniswapV2Router(uniswapAddr).WETH();
                    path[2] = allAssets[1]; // USDT

                    IUniswapV2Router(uniswapAddr).swapExactTokensForTokens(
                        rewardTokenAmount,
                        uint256(0),
                        path,
                        address(this),
                        now.add(1800)
                    );
                }
            }
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['allAssets', 'uniswapAddr']
- **External calls**: `strategy.rewardTokenAddress()` (method: rewardTokenAddress, receiver: strategy), `strategy.collectRewardToken()` (method: collectRewardToken, receiver: strategy), `strategy.rewardTokenAddress()` (method: rewardTokenAddress, receiver: strategy), `rewardToken.balanceOf(
                    address(this)
                )` (method: balanceOf, receiver: rewardToken), `rewardToken.safeApprove(uniswapAddr, 0)` (method: safeApprove, receiver: rewardToken), `rewardToken.safeApprove(uniswapAddr, rewardTokenAmount)` (method: safeApprove, receiver: rewardToken), `strategy.rewardTokenAddress()` (method: rewardTokenAddress, receiver: strategy), `IUniswapV2Router(uniswapAddr).WETH()` (method: WETH, receiver: IUniswapV2Router), `IUniswapV2Router(uniswapAddr).swapExactTokensForTokens(
                        rewardTokenAmount,
                     ` (method: swapExactTokensForTokens, receiver: IUniswapV2Router)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['allAssets', 'uniswapAddr']
- **External calls**: `strategy.rewardTokenAddress()` (call on contract-typed local var 'strategy' (type: IStrategy)), `strategy.collectRewardToken()` (call on contract-typed local var 'strategy' (type: IStrategy)), `strategy.rewardTokenAddress()` (call on contract-typed local var 'strategy' (type: IStrategy)), `rewardToken.balanceOf(
                    address(this)
                )` (call on contract-typed local var 'rewardToken' (type: IERC20)), `rewardToken.safeApprove(uniswapAddr, 0)` (SafeERC20 .safeApprove()), `rewardToken.safeApprove(uniswapAddr, rewardTokenAmount)` (SafeERC20 .safeApprove()), `strategy.rewardTokenAddress()` (call on contract-typed local var 'strategy' (type: IStrategy)), `IUniswapV2Router(uniswapAddr).WETH()` (inline cast call IUniswapV2Router(...).WETH()), `IUniswapV2Router(uniswapAddr).swapExactTokensForTokens(
                        rewardTokenAmount,
                     ` (inline cast call IUniswapV2Router(...).swapExactTokensForTokens())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### VaultCore.mintMultiple

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: mintMultiple
- **Line Range**: L88 - L128
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-OriginDollar/origin-dollar-81431fd3b2aa4c518ffc389844f9708c00b516f0/contracts/contracts/vault/VaultCore.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`mintMultiple`, lines=`L88 - L128`

#### 2. Function Source Code
```solidity
function mintMultiple(
        address[] calldata _assets,
        uint256[] calldata _amounts
    ) external whenNotDepositPaused {
        require(_assets.length == _amounts.length, "Parameter length mismatch");

        uint256 priceAdjustedTotal = 0;
        uint256[] memory assetPrices = _getAssetPrices(false);
        for (uint256 i = 0; i < allAssets.length; i++) {
            for (uint256 j = 0; j < _assets.length; j++) {
                if (_assets[j] == allAssets[i]) {
                    if (_amounts[j] > 0) {
                        uint256 assetDecimals = Helpers.getDecimals(
                            allAssets[i]
                        );
                        uint256 price = assetPrices[i];
                        if (price > 1e18) {
                            price = 1e18;
                        }
                        priceAdjustedTotal += _amounts[j].mulTruncateScale(
                            price,
                            10**assetDecimals
                        );
                    }
                }
            }
        }
        // Rebase must happen before any transfers occur.
        if (priceAdjustedTotal > rebaseThreshold && !rebasePaused) {
            rebase(true);
        }

        for (uint256 i = 0; i < _assets.length; i++) {
            IERC20 asset = IERC20(_assets[i]);
            asset.safeTransferFrom(msg.sender, address(this), _amounts[i]);
        }

        oUSD.mint(msg.sender, priceAdjustedTotal);
        emit Mint(msg.sender, priceAdjustedTotal);

        if (priceAdjustedTotal >= autoAllocateThreshold) {
            allocate();
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['allAssets', 'autoAllocateThreshold', 'oUSD', 'rebasePaused', 'rebaseThreshold']
- **External calls**: `Helpers.getDecimals(
                            allAssets[i]
                        )` (method: getDecimals, receiver: Helpers), `asset.safeTransferFrom(msg.sender, address(this), _amounts[i])` (method: safeTransferFrom, receiver: asset), `oUSD.mint(msg.sender, priceAdjustedTotal)` (method: mint, receiver: oUSD)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['allAssets', 'autoAllocateThreshold', 'oUSD', 'rebasePaused', 'rebaseThreshold']
- **External calls**: `Helpers.getDecimals(
                            allAssets[i]
                        )` (call on interface/contract type 'Helpers'), `asset.safeTransferFrom(msg.sender, address(this), _amounts[i])` (SafeERC20 .safeTransferFrom()), `oUSD.mint(msg.sender, priceAdjustedTotal)` (call on contract-typed state var 'oUSD' (type: OUSD))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### VaultCore._redeem

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _redeem
- **Line Range**: L142 - L184
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-OriginDollar/origin-dollar-81431fd3b2aa4c518ffc389844f9708c00b516f0/contracts/contracts/vault/VaultCore.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_redeem`, lines=`L142 - L184`

#### 2. Function Source Code
```solidity
function _redeem(uint256 _amount) internal {
        require(_amount > 0, "Amount must be greater than 0");

        // Calculate redemption outputs
        uint256[] memory outputs = _calculateRedeemOutputs(_amount);
        // Send outputs
        for (uint256 i = 0; i < allAssets.length; i++) {
            if (outputs[i] == 0) continue;

            IERC20 asset = IERC20(allAssets[i]);

            if (asset.balanceOf(address(this)) >= outputs[i]) {
                // Use Vault funds first if sufficient
                asset.safeTransfer(msg.sender, outputs[i]);
            } else {
                address strategyAddr = _selectWithdrawStrategyAddr(
                    allAssets[i],
                    outputs[i]
                );

                if (strategyAddr != address(0)) {
                    // Nothing in Vault, but something in Strategy, send from there
                    IStrategy strategy = IStrategy(strategyAddr);
                    strategy.withdraw(msg.sender, allAssets[i], outputs[i]);
                } else {
                    // Cant find funds anywhere
                    revert("Liquidity error");
                }
            }
        }

        oUSD.burn(msg.sender, _amount);

        // Until we can prove that we won't affect the prices of our assets
        // by withdrawing them, this should be here.
        // It's possible that a strategy was off on its asset total, perhaps
        // a reward token sold for more or for less than anticipated.
        if (_amount > rebaseThreshold && !rebasePaused) {
            rebase(true);
        }

        emit Redeem(msg.sender, _amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['allAssets', 'oUSD', 'rebasePaused', 'rebaseThreshold']
- **External calls**: `asset.balanceOf(address(this))` (method: balanceOf, receiver: asset), `asset.safeTransfer(msg.sender, outputs[i])` (method: safeTransfer, receiver: asset), `strategy.withdraw(msg.sender, allAssets[i], outputs[i])` (method: withdraw, receiver: strategy), `oUSD.burn(msg.sender, _amount)` (method: burn, receiver: oUSD)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['allAssets', 'oUSD', 'rebasePaused', 'rebaseThreshold']
- **External calls**: `asset.balanceOf(address(this))` (call on contract-typed local var 'asset' (type: IERC20)), `asset.safeTransfer(msg.sender, outputs[i])` (SafeERC20 .safeTransfer()), `strategy.withdraw(msg.sender, allAssets[i], outputs[i])` (call on contract-typed local var 'strategy' (type: IStrategy)), `oUSD.burn(msg.sender, _amount)` (call on contract-typed state var 'oUSD' (type: OUSD))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### VaultCore._allocate

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _allocate
- **Line Range**: L210 - L293
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-OriginDollar/origin-dollar-81431fd3b2aa4c518ffc389844f9708c00b516f0/contracts/contracts/vault/VaultCore.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_allocate`, lines=`L210 - L293`

#### 2. Function Source Code
(84 lines, showing first 30 + last 15)
```solidity
function _allocate() internal {
        uint256 vaultValue = _totalValueInVault();
        // Nothing in vault to allocate
        if (vaultValue == 0) return;
        uint256 strategiesValue = _totalValueInStrategies();
        // We have a method that does the same as this, gas optimisation
        uint256 totalValue = vaultValue + strategiesValue;

        // We want to maintain a buffer on the Vault so calculate a percentage
        // modifier to multiply each amount being allocated by to enforce the
        // vault buffer
        uint256 vaultBufferModifier;
        if (strategiesValue == 0) {
            // Nothing in Strategies, allocate 100% minus the vault buffer to
            // strategies
            vaultBufferModifier = 1e18 - vaultBuffer;
        } else {
            vaultBufferModifier = vaultBuffer.mul(totalValue).div(vaultValue);
            if (1e18 > vaultBufferModifier) {
                // E.g. 1e18 - (1e17 * 10e18)/5e18 = 8e17
                // (5e18 * 8e17) / 1e18 = 4e18 allocated from Vault
                vaultBufferModifier = 1e18 - vaultBufferModifier;
            } else {
                // We need to let the buffer fill
                return;
            }
        }
        if (vaultBufferModifier == 0) return;

        // Iterate over all assets in the Vault and allocate the the appropriate
    // ... truncated ...
                    // Check balance against liquidation threshold
                    // Note some strategies don't hold the reward token balance
                    // on their contract so the liquidation threshold should be
                    // set to 0
                    IERC20 rewardToken = IERC20(rewardTokenAddress);
                    uint256 rewardTokenAmount = rewardToken.balanceOf(
                        allStrategies[i]
                    );
                    if (rewardTokenAmount >= liquidationThreshold) {
                        IVault(address(this)).harvest(allStrategies[i]);
                    }
                }
            }
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['allAssets', 'allStrategies', 'vaultBuffer']
- **External calls**: `asset.balanceOf(address(this))` (method: balanceOf, receiver: asset), `asset.safeTransfer(address(strategy), allocateAmount)` (method: safeTransfer, receiver: asset), `strategy.deposit(address(asset), allocateAmount)` (method: deposit, receiver: strategy), `strategy.rewardTokenAddress()` (method: rewardTokenAddress, receiver: strategy), `strategy
                    .rewardLiquidationThreshold()` (method: rewardLiquidationThreshold, receiver: strategy), `IVault(address(this)).harvest(allStrategies[i])` (method: harvest, receiver: IVault), `rewardToken.balanceOf(
                        allStrategies[i]
                    )` (method: balanceOf, receiver: rewardToken), `IVault(address(this)).harvest(allStrategies[i])` (method: harvest, receiver: IVault)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['allAssets', 'allStrategies', 'vaultBuffer']
- **External calls**: `asset.balanceOf(address(this))` (call on contract-typed local var 'asset' (type: IERC20)), `asset.safeTransfer(address(strategy), allocateAmount)` (SafeERC20 .safeTransfer()), `strategy.deposit(address(asset), allocateAmount)` (call on contract-typed local var 'strategy' (type: IStrategy)), `strategy.rewardTokenAddress()` (call on contract-typed local var 'strategy' (type: IStrategy)), `strategy
                    .rewardLiquidationThreshold()` (call on contract-typed local var 'strategy' (type: IStrategy)), `IVault(address(this)).harvest(allStrategies[i])` (inline cast call IVault(...).harvest()), `rewardToken.balanceOf(
                        allStrategies[i]
                    )` (call on contract-typed local var 'rewardToken' (type: IERC20)), `IVault(address(this)).harvest(allStrategies[i])` (inline cast call IVault(...).harvest())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### VaultCore.rebase

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call present — unchecked return value plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: rebase
- **Line Range**: L308 - L319
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-OriginDollar/origin-dollar-81431fd3b2aa4c518ffc389844f9708c00b516f0/contracts/contracts/vault/VaultCore.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`rebase`, lines=`L308 - L319`

#### 2. Function Source Code
```solidity
function rebase(bool sync) internal whenNotRebasePaused returns (uint256) {
        if (oUSD.totalSupply() == 0) return 0;
        uint256 oldTotalSupply = oUSD.totalSupply();
        uint256 newTotalSupply = _totalValue();
        // Only rachet upwards
        if (newTotalSupply > oldTotalSupply) {
            oUSD.changeSupply(newTotalSupply);
            if (rebaseHooksAddr != address(0)) {
                IRebaseHooks(rebaseHooksAddr).postRebase(sync);
            }
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['oUSD', 'rebaseHooksAddr']
- **External calls**: `oUSD.totalSupply()` (method: totalSupply, receiver: oUSD), `oUSD.totalSupply()` (method: totalSupply, receiver: oUSD), `oUSD.changeSupply(newTotalSupply)` (method: changeSupply, receiver: oUSD), `IRebaseHooks(rebaseHooksAddr).postRebase(sync)` (method: postRebase, receiver: IRebaseHooks)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['oUSD', 'rebaseHooksAddr']
- **External calls**: `oUSD.totalSupply()` (call on contract-typed state var 'oUSD' (type: OUSD)), `oUSD.totalSupply()` (call on contract-typed state var 'oUSD' (type: OUSD)), `oUSD.changeSupply(newTotalSupply)` (call on contract-typed state var 'oUSD' (type: OUSD)), `IRebaseHooks(rebaseHooksAddr).postRebase(sync)` (inline cast call IRebaseHooks(...).postRebase())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### PrimitiveEngine.allocate

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: allocate
- **Line Range**: L238 - L270
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-Primitive/rmm-core-5dcf4306fc32fb9a4e3c154deb86f6b9d513c344/contracts/PrimitiveEngine.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`allocate`, lines=`L238 - L270`

#### 2. Function Source Code
```solidity
function allocate(
        bytes32 poolId,
        address recipient,
        uint256 delRisky,
        uint256 delStable,
        bool fromMargin,
        bytes calldata data
    ) external override lock returns (uint256 delLiquidity) {
        if (delRisky == 0 || delStable == 0) revert ZeroDeltasError();
        Reserve.Data storage reserve = reserves[poolId];
        if (reserve.blockTimestamp == 0) revert UninitializedError();
        uint32 timestamp = _blockTimestamp();
        if (timestamp > calibrations[poolId].maturity) revert PoolExpiredError();

        uint256 liquidity0 = (delRisky * reserve.liquidity) / uint256(reserve.reserveRisky);
        uint256 liquidity1 = (delStable * reserve.liquidity) / uint256(reserve.reserveStable);
        delLiquidity = liquidity0 < liquidity1 ? liquidity0 : liquidity1;
        if (delLiquidity == 0) revert ZeroLiquidityError();

        liquidity[recipient][poolId] += delLiquidity; // increase position liquidity
        reserve.allocate(delRisky, delStable, delLiquidity, timestamp); // increase reserves and liquidity

        if (fromMargin) {
            margins.withdraw(delRisky, delStable); // removes tokens from `msg.sender` margin account
        } else {
            (uint256 balRisky, uint256 balStable) = (balanceRisky(), balanceStable());
            IPrimitiveLiquidityCallback(msg.sender).allocateCallback(delRisky, delStable, data); // agnostic payment
            checkRiskyBalance(balRisky + delRisky);
            checkStableBalance(balStable + delStable);
        }

        emit Allocate(msg.sender, recipient, poolId, delRisky, delStable);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['calibrations', 'liquidity', 'margins', 'reserves']
- **External calls**: `reserve.allocate(delRisky, delStable, delLiquidity, timestamp)` (method: allocate, receiver: reserve), `margins.withdraw(delRisky, delStable)` (method: withdraw, receiver: margins), `IPrimitiveLiquidityCallback(msg.sender).allocateCallback(delRisky, delStable, data)` (method: allocateCallback, receiver: IPrimitiveLiquidityCallback)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['calibrations', 'liquidity', 'margins', 'reserves']
- **External calls**: `reserve.allocate(delRisky, delStable, delLiquidity, timestamp)` (call on contract-typed local var 'reserve' (type: Reserve.Data)), `margins.withdraw(delRisky, delStable)` (call on contract-typed state var 'margins' (type: mapping(address => Margin.Data))), `IPrimitiveLiquidityCallback(msg.sender).allocateCallback(delRisky, delStable, data)` (inline cast call IPrimitiveLiquidityCallback(...).allocateCallback())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### PrimitiveEngine.swap

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: swap
- **Line Range**: L304 - L403
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-Primitive/rmm-core-5dcf4306fc32fb9a4e3c154deb86f6b9d513c344/contracts/PrimitiveEngine.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`swap`, lines=`L304 - L403`

#### 2. Function Source Code
(100 lines, showing first 30 + last 15)
```solidity
function swap(
        address recipient,
        bytes32 poolId,
        bool riskyForStable,
        uint256 deltaIn,
        uint256 deltaOut,
        bool fromMargin,
        bool toMargin,
        bytes calldata data
    ) external override lock {
        if (deltaIn == 0) revert DeltaInError();
        if (deltaOut == 0) revert DeltaOutError();

        SwapDetails memory details = SwapDetails({
            recipient: recipient,
            poolId: poolId,
            deltaIn: deltaIn,
            deltaOut: deltaOut,
            riskyForStable: riskyForStable,
            fromMargin: fromMargin,
            toMargin: toMargin,
            timestamp: _blockTimestamp()
        });

        uint32 lastTimestamp = _updateLastTimestamp(details.poolId); // updates lastTimestamp of `poolId`
        if (details.timestamp > lastTimestamp + BUFFER) revert PoolExpiredError(); // 120s buffer to allow final swaps
        int128 invariantX64 = invariantOf(details.poolId); // stored in memory to perform the invariant check

        {
            // swap scope, avoids stack too deep errors
    // ... truncated ...
                uint256 balStable = balanceStable();
                IPrimitiveSwapCallback(msg.sender).swapCallback(0, details.deltaIn, data); // agnostic transfer in
                checkStableBalance(balStable + details.deltaIn);
            }
        }

        emit Swap(
            msg.sender,
            details.recipient,
            details.poolId,
            details.riskyForStable,
            details.deltaIn,
            details.deltaOut
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['BUFFER', 'PRECISION', 'calibrations', 'liquidity', 'margins', 'reserves', 'risky', 'scaleFactorRisky', 'scaleFactorStable', 'stable']
- **External calls**: `ReplicationMath.calcInvariant(
                scaleFactorRisky,
                scaleFactorStable,
                adju` (method: calcInvariant, receiver: ReplicationMath), `reserve.swap(details.riskyForStable, details.deltaIn, details.deltaOut, details.timestamp)` (method: swap, receiver: reserve), `margins[details.recipient].deposit(0, details.deltaOut)` (method: deposit, receiver: margins), `IERC20(stable).safeTransfer(details.recipient, details.deltaOut)` (method: safeTransfer, receiver: IERC20), `margins.withdraw(details.deltaIn, 0)` (method: withdraw, receiver: margins), `IPrimitiveSwapCallback(msg.sender).swapCallback(details.deltaIn, 0, data)` (method: swapCallback, receiver: IPrimitiveSwapCallback), `margins[details.recipient].deposit(details.deltaOut, 0)` (method: deposit, receiver: margins), `IERC20(risky).safeTransfer(details.recipient, details.deltaOut)` (method: safeTransfer, receiver: IERC20), `margins.withdraw(0, details.deltaIn)` (method: withdraw, receiver: margins), `IPrimitiveSwapCallback(msg.sender).swapCallback(0, details.deltaIn, data)` (method: swapCallback, receiver: IPrimitiveSwapCallback)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['BUFFER', 'PRECISION', 'calibrations', 'liquidity', 'margins', 'reserves', 'risky', 'scaleFactorRisky', 'scaleFactorStable', 'stable']
- **External calls**: `ReplicationMath.calcInvariant(
                scaleFactorRisky,
                scaleFactorStable,
                adju` (call on interface/contract type 'ReplicationMath'), `reserve.swap(details.riskyForStable, details.deltaIn, details.deltaOut, details.timestamp)` (call on contract-typed local var 'reserve' (type: Reserve.Data)), `margins[details.recipient].deposit(0, details.deltaOut)` (call on contract-typed state var 'margins' (type: mapping(address => Margin.Data))), `IERC20(stable).safeTransfer(details.recipient, details.deltaOut)` (SafeERC20 .safeTransfer()), `margins.withdraw(details.deltaIn, 0)` (call on contract-typed state var 'margins' (type: mapping(address => Margin.Data))), `IPrimitiveSwapCallback(msg.sender).swapCallback(details.deltaIn, 0, data)` (inline cast call IPrimitiveSwapCallback(...).swapCallback()), `margins[details.recipient].deposit(details.deltaOut, 0)` (call on contract-typed state var 'margins' (type: mapping(address => Margin.Data))), `IERC20(risky).safeTransfer(details.recipient, details.deltaOut)` (SafeERC20 .safeTransfer()), `margins.withdraw(0, details.deltaIn)` (call on contract-typed state var 'margins' (type: mapping(address => Margin.Data))), `IPrimitiveSwapCallback(msg.sender).swapCallback(0, details.deltaIn, data)` (inline cast call IPrimitiveSwapCallback(...).swapCallback())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### UniswapV3Pool.initialize

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: initialize
- **Line Range**: L195 - L213
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-UniswapV3Core/v3-core-99223f33fd69a9e024f00bd8eea17b029d3f8f2d/contracts/UniswapV3Pool.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`initialize`, lines=`L195 - L213`

#### 2. Function Source Code
```solidity
function initialize(uint160 sqrtPriceX96) external override {
        require(slot0.sqrtPriceX96 == 0, 'AI');

        int24 tick = TickMath.getTickAtSqrtRatio(sqrtPriceX96);

        (uint16 cardinality, uint16 cardinalityNext) = observations.initialize(_blockTimestamp());

        slot0 = Slot0({
            sqrtPriceX96: sqrtPriceX96,
            tick: tick,
            observationIndex: 0,
            observationCardinality: cardinality,
            observationCardinalityNext: cardinalityNext,
            feeProtocol: 0,
            unlocked: true
        });

        emit Initialize(sqrtPriceX96, tick);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['observations', 'slot0']
- **External calls**: `TickMath.getTickAtSqrtRatio(sqrtPriceX96)` (method: getTickAtSqrtRatio, receiver: TickMath), `observations.initialize(_blockTimestamp())` (method: initialize, receiver: observations)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['observations', 'slot0']
- **External calls**: `TickMath.getTickAtSqrtRatio(sqrtPriceX96)` (call on interface/contract type 'TickMath'), `observations.initialize(_blockTimestamp())` (call on contract-typed state var 'observations' (type: Oracle.Observation[65535]))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### MarketOracle.getPriceAnd24HourVolume

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: getPriceAnd24HourVolume
- **Line Range**: L34 - L60
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-ampleforth/market-oracle-888fccaf05786f3f7f49e18ff040f911d44906f4/contracts/MarketOracle.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`getPriceAnd24HourVolume`, lines=`L34 - L60`

#### 2. Function Source Code
```solidity
function getPriceAnd24HourVolume()
        external
        returns (uint256, uint256)
    {
        uint256 volumeWeightedSum = 0;
        uint256 volumeSum = 0;
        uint256 partialRate = 0;
        uint256 partialVolume = 0;
        bool isSourceFresh = false;

        for (uint256 i = 0; i < _whitelist.length; i++) {
            (isSourceFresh, partialRate, partialVolume) = _whitelist[i].getReport();

            if (!isSourceFresh) {
                emit LogSourceExpired(_whitelist[i]);
                continue;
            }

            volumeWeightedSum = volumeWeightedSum.add(partialRate.mul(partialVolume));
            volumeSum = volumeSum.add(partialVolume);
        }

        // No explicit fixed point normalization is done as dividing by volumeSum normalizes
        // to exchangeRate's format.
        uint256 exchangeRate = volumeWeightedSum.div(volumeSum);
        return (exchangeRate, volumeSum);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_whitelist']
- **External calls**: `_whitelist[i].getReport()` (method: getReport, receiver: _whitelist)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['_whitelist']
- **External calls**: `_whitelist[i].getReport()` (call on contract-typed state var '_whitelist' (type: MarketSource[]))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### ExchangeExecution.executeExchangeOrders

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: executeExchangeOrders
- **Line Range**: L76
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-setprotocol/set-protocol-contracts-b4acf144c10b1d9f3ecde4ee2820931df1cb8e4a/contracts/core/modules/lib/ExchangeExecution.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`executeExchangeOrders`, lines=`L76`

#### 2. Function Source Code
(67 lines, showing first 30 + last 15)
```solidity
function executeExchangeOrders(
        bytes memory _orderData
    )
        internal
    {
        // Bitmask integer of called exchanges. Acts as a lock so that duplicate exchange headers are not passed in.
        uint256 calledExchanges = 0;
        
        uint256 scannedBytes = 0;
        while (scannedBytes < _orderData.length) {
            // Parse exchange header based on scannedBytes
            ExchangeHeaderLibrary.ExchangeHeader memory header = ExchangeHeaderLibrary.parseExchangeHeader(
                _orderData,
                scannedBytes
            );

            // Get exchange address from state mapping based on header exchange info
            address exchangeWrapper = coreInstance.exchangeIds(header.exchange);

            // Verify exchange address is registered
            require(
                exchangeWrapper != address(0),
                "ExchangeExecution.executeExchangeOrders: Invalid or disabled Exchange address"
            );

            // Verify exchange has not already been called
            // SWC-101-Integer Overflow and Underflow: L76
            // SWC-114-Transaction Order Dependence: L76
            uint256 exchangeBitIndex = CommonMath.safePower(2, header.exchange);
            require(
    // ... truncated ...
            // Execute orders using the appropriate exchange wrappers
            ExchangeWrapperLibrary.callExchange(
                core,
                exchangeData,
                exchangeWrapper,
                bodyData
            );

            // Update scanned bytes with header and body lengths
            scannedBytes = scannedBytes.add(exchangeDataLength);

            // Increment bit of current exchange to ensure non-duplicate entries
            calledExchanges = calledExchanges.add(exchangeBitIndex);
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['core', 'coreInstance']
- **External calls**: `ExchangeHeaderLibrary.parseExchangeHeader(
                _orderData,
                scannedBytes
            )` (method: parseExchangeHeader, receiver: ExchangeHeaderLibrary), `coreInstance.exchangeIds(header.exchange)` (method: exchangeIds, receiver: coreInstance), `CommonMath.safePower(2, header.exchange)` (method: safePower, receiver: CommonMath), `header.orderDataBytesLength.add(
                ExchangeHeaderLibrary.EXCHANGE_HEADER_LENGTH()
            )` (method: add, receiver: header), `ExchangeHeaderLibrary.EXCHANGE_HEADER_LENGTH()` (method: EXCHANGE_HEADER_LENGTH, receiver: ExchangeHeaderLibrary), `ExchangeHeaderLibrary.sliceBodyData(
                _orderData,
                scannedBytes,
                exchangeD` (method: sliceBodyData, receiver: ExchangeHeaderLibrary), `ExchangeWrapperLibrary.ExchangeData({
                caller: msg.sender,
                orderCount: header.orderCount
` (method: ExchangeData, receiver: ExchangeWrapperLibrary), `ExchangeWrapperLibrary.callExchange(
                core,
                exchangeData,
                exchangeWrapper` (method: callExchange, receiver: ExchangeWrapperLibrary)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['core', 'coreInstance']
- **External calls**: `ExchangeHeaderLibrary.parseExchangeHeader(
                _orderData,
                scannedBytes
            )` (call on interface/contract type 'ExchangeHeaderLibrary'), `coreInstance.exchangeIds(header.exchange)` (call on contract-typed state var 'coreInstance' (type: ICore)), `CommonMath.safePower(2, header.exchange)` (call on interface/contract type 'CommonMath'), `header.orderDataBytesLength.add(
                ExchangeHeaderLibrary.EXCHANGE_HEADER_LENGTH()
            )` (call on contract-typed local var 'header' (type: ExchangeHeaderLibrary.ExchangeHeader)), `ExchangeHeaderLibrary.EXCHANGE_HEADER_LENGTH()` (call on interface/contract type 'ExchangeHeaderLibrary'), `ExchangeHeaderLibrary.sliceBodyData(
                _orderData,
                scannedBytes,
                exchangeD` (call on interface/contract type 'ExchangeHeaderLibrary'), `ExchangeWrapperLibrary.ExchangeData({
                caller: msg.sender,
                orderCount: header.orderCount
` (call on interface/contract type 'ExchangeWrapperLibrary'), `ExchangeWrapperLibrary.callExchange(
                core,
                exchangeData,
                exchangeWrapper` (call on interface/contract type 'ExchangeWrapperLibrary')
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### TransactionManager.removeLiquidity

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: removeLiquidity
- **Line Range**: L229 - L254
- **File**: `DAppSCAN-source/contracts/consensys-Connext NXTP — Noncustodial Xchain Transfer Protocol/nxtp-0656436d654cfe0313fa3c2bbc81aa86232ade16/packages/contracts/contracts/TransactionManager.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`removeLiquidity`, lines=`L229 - L254`

#### 2. Function Source Code
```solidity
function removeLiquidity(
    uint256 amount,
    address assetId,
    address payable recipient
  ) external override nonReentrant {
    // Sanity check: recipient is sensible
    require(recipient != address(0), "#RL:007");

    // Sanity check: nonzero amounts
    require(amount > 0, "#RL:002");

    uint256 routerBalance = routerBalances[msg.sender][assetId];
    // Sanity check: amount can be deducted for the router
    require(routerBalance >= amount, "#RL:008");

    // Update router balances
    unchecked {
      routerBalances[msg.sender][assetId] = routerBalance - amount;
    }

    // Transfer from contract to specified recipient
    LibAsset.transferAsset(assetId, recipient, amount);

    // Emit event
    emit LiquidityRemoved(msg.sender, assetId, amount, recipient);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['routerBalances']
- **External calls**: `LibAsset.transferAsset(assetId, recipient, amount)` (method: transferAsset, receiver: LibAsset)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['routerBalances']
- **External calls**: `LibAsset.transferAsset(assetId, recipient, amount)` (call on interface/contract type 'LibAsset')
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### CompHelper.enterMarket

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call present — unchecked return value plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: enterMarket
- **Line Range**: L27-138
- **File**: `DAppSCAN-source/contracts/consensys-DeFi_Saver/defisaver-v3-contracts-cb29669a84c2d6fffaf2231c0938eb407c060919/contracts/actions/compound/helpers/CompHelper.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`enterMarket`, lines=`L27-138`

#### 2. Function Source Code
```solidity
function enterMarket(address _cTokenAddr) public {
        address[] memory markets = new address[](1);
        markets[0] = _cTokenAddr;

        IComptroller(COMPTROLLER_ADDR).enterMarkets(markets);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['COMPTROLLER_ADDR']
- **External calls**: `IComptroller(COMPTROLLER_ADDR).enterMarkets(markets)` (method: enterMarkets, receiver: IComptroller)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['COMPTROLLER_ADDR']
- **External calls**: `IComptroller(COMPTROLLER_ADDR).enterMarkets(markets)` (inline cast call IComptroller(...).enterMarkets())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### FLAaveV2.executeOperation

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: executeOperation
- **Line Range**: L106-137
- **File**: `DAppSCAN-source/contracts/consensys-DeFi_Saver/defisaver-v3-contracts-cb29669a84c2d6fffaf2231c0938eb407c060919/contracts/actions/flashloan/FLAaveV2.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`executeOperation`, lines=`L106-137`

#### 2. Function Source Code
```solidity
function executeOperation(
        address[] memory _assets,
        uint256[] memory _amounts,
        uint256[] memory _fees,
        address _initiator,
        bytes memory _params
    ) public returns (bool) {
        require(msg.sender == AAVE_LENDING_POOL, ERR_ONLY_AAVE_CALLER);
        require(_initiator == address(this), ERR_SAME_CALLER);

        (Task memory currTask, address proxy) = abi.decode(_params, (Task, address));

        // Send FL amounts to user proxy
        for (uint256 i = 0; i < _assets.length; ++i) {
            _assets[i].withdrawTokens(proxy, _amounts[i]);
        }

        address payable taskExecutor = payable(registry.getAddr(TASK_EXECUTOR_ID));

        // call Action execution
        IDSProxy(proxy).execute{value: address(this).balance}(
            taskExecutor,
            abi.encodeWithSelector(CALLBACK_SELECTOR, currTask, bytes32(_amounts[0] + _fees[0]))
        );

        // return FL
        for (uint256 i = 0; i < _assets.length; i++) {
            _assets[i].approveToken(address(AAVE_LENDING_POOL), _amounts[i] + _fees[i]);
        }

        return true;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['AAVE_LENDING_POOL', 'CALLBACK_SELECTOR', 'ERR_ONLY_AAVE_CALLER', 'ERR_SAME_CALLER', 'TASK_EXECUTOR_ID', 'registry']
- **External calls**: `registry.getAddr(TASK_EXECUTOR_ID)` (method: getAddr, receiver: registry), `IDSProxy(proxy).execute{value: address(this).balance}(
            taskExecutor,
            abi.encodeWithSelector(CALL` (method: execute, receiver: IDSProxy)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['AAVE_LENDING_POOL', 'CALLBACK_SELECTOR', 'ERR_ONLY_AAVE_CALLER', 'ERR_SAME_CALLER', 'TASK_EXECUTOR_ID', 'registry']
- **External calls**: `registry.getAddr(TASK_EXECUTOR_ID)` (call on contract-typed state var 'registry' (type: DFSRegistry)), `IDSProxy(proxy).execute{value: address(this).balance}(
            taskExecutor,
            abi.encodeWithSelector(CALL` (inline cast call IDSProxy(...).execute())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### ETHRegistrarController.register

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: register
- **Line Range**: L56-L65
- **File**: `DAppSCAN-source/contracts/consensys-ENS_Permanent_Registrar/ethregistrar-e52abfc2799ac361364aca6135fc20f9175a29fd/contracts/ETHRegistrarController.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`register`, lines=`L56-L65`

#### 2. Function Source Code
```solidity
function register(string calldata name, address owner, uint duration, bytes32 secret) external payable {
        // Require a valid commitment
        bytes32 commitment = makeCommitment(name, secret);
        require(commitments[commitment] + MIN_COMMITMENT_AGE <= now);

        // If the commitment is too old, or the name is registered, stop
        if(commitments[commitment] + MAX_COMMITMENT_AGE < now || !available(name))  {
            msg.sender.transfer(msg.value);
            return;
        }
        delete(commitments[commitment]);

        uint cost = rentPrice(name, duration);
        require(duration >= MIN_REGISTRATION_DURATION);
        require(msg.value >= cost);

        bytes32 label = keccak256(bytes(name));
        uint expires = base.register(uint256(label), owner, duration);
        emit NameRegistered(name, owner, cost, expires);

        if(msg.value > cost) {
            msg.sender.transfer(msg.value - cost);
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['MAX_COMMITMENT_AGE', 'MIN_COMMITMENT_AGE', 'MIN_REGISTRATION_DURATION', 'base', 'commitments']
- **External calls**: `msg.sender.transfer(msg.value)` (method: transfer, receiver: msg), `base.register(uint256(label), owner, duration)` (method: register, receiver: base), `msg.sender.transfer(msg.value - cost)` (method: transfer, receiver: msg)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['MAX_COMMITMENT_AGE', 'MIN_COMMITMENT_AGE', 'MIN_REGISTRATION_DURATION', 'base', 'commitments']
- **External calls**: `msg.sender.transfer(msg.value)` (low-level call on msg.sender/tx.origin), `base.register(uint256(label), owner, duration)` (call on contract-typed state var 'base' (type: BaseRegistrar)), `msg.sender.transfer(msg.value - cost)` (low-level call on msg.sender/tx.origin)
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### BalancerLBPSwapper.init

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: init
- **Line Range**: L108-118
- **File**: `DAppSCAN-source/contracts/consensys-Fei_Protocol_v2_Phase_1/fei-protocol-core-5e3e2ab889f06831f4fe2e8460066ded40ccf0a8/contracts/pcv/balancer/BalancerLBPSwapper.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`init`, lines=`L108-118`

#### 2. Function Source Code
```solidity
function init(IWeightedPool _pool) external {
        require(address(pool) == address(0), "BalancerLBPSwapper: initialized");

        pool = _pool;
        IVault _vault = _pool.getVault();

        vault = _vault;

        // Check ownership
        require(_pool.getOwner() == address(this), "BalancerLBPSwapper: contract not pool owner");

        // Check correct pool token components
        bytes32 _pid = _pool.getPoolId();
        pid = _pid;
        (IERC20[] memory tokens,,) = _vault.getPoolTokens(_pid);
        require(tokens.length == 2, "BalancerLBPSwapper: pool does not have 2 tokens");
        require(
            tokenSpent == address(tokens[0]) || 
            tokenSpent == address(tokens[1]), 
            "BalancerLBPSwapper: tokenSpent not in pool"
        );        
        require(
            tokenReceived == address(tokens[0]) || 
            tokenReceived == address(tokens[1]), 
            "BalancerLBPSwapper: tokenReceived not in pool"
        );

        // Set the asset array and target weights
        assets = new IAsset[](2);
        assets[0] = IAsset(address(tokens[0]));
        assets[1] = IAsset(address(tokens[1]));

        bool tokenSpentAtIndex0 = tokenSpent == address(tokens[0]);
        initialWeights = new uint[](2);
        endWeights = new uint[](2);

        if (tokenSpentAtIndex0) {
            initialWeights[0] = NINETY_NINE_PERCENT;
            initialWeights[1] = ONE_PERCENT;

            endWeights[0] = ONE_PERCENT;
            endWeights[1] = NINETY_NINE_PERCENT;
        }  else {
            initialWeights[0] = ONE_PERCENT;
            initialWeights[1] = NINETY_NINE_PERCENT;

            endWeights[0] = NINETY_NINE_PERCENT;
            endWeights[1] = ONE_PERCENT;
        }
        
        // Approve pool tokens for vault
        _pool.approve(address(_vault), type(uint256).max);
        IERC20(tokenSpent).approve(address(_vault), type(uint256).max);
        IERC20(tokenReceived).approve(address(_vault), type(uint256).max);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['NINETY_NINE_PERCENT', 'ONE_PERCENT', 'assets', 'endWeights', 'initialWeights', 'pid', 'pool', 'tokenReceived', 'tokenSpent', 'vault']
- **External calls**: `_pool.getVault()` (method: getVault, receiver: _pool), `_pool.getOwner()` (method: getOwner, receiver: _pool), `_pool.getPoolId()` (method: getPoolId, receiver: _pool), `_vault.getPoolTokens(_pid)` (method: getPoolTokens, receiver: _vault), `_pool.approve(address(_vault), type(uint256).max)` (method: approve, receiver: _pool), `IERC20(tokenSpent).approve(address(_vault), type(uint256).max)` (method: approve, receiver: IERC20), `IERC20(tokenReceived).approve(address(_vault), type(uint256).max)` (method: approve, receiver: IERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['NINETY_NINE_PERCENT', 'ONE_PERCENT', 'assets', 'endWeights', 'initialWeights', 'pid', 'pool', 'tokenReceived', 'tokenSpent', 'vault']
- **External calls**: `_pool.getVault()` (call on contract-typed local var '_pool' (type: IWeightedPool)), `_pool.getOwner()` (call on contract-typed local var '_pool' (type: IWeightedPool)), `_pool.getPoolId()` (call on contract-typed local var '_pool' (type: IWeightedPool)), `_vault.getPoolTokens(_pid)` (call on contract-typed local var '_vault' (type: IVault)), `_pool.approve(address(_vault), type(uint256).max)` (call on contract-typed local var '_pool' (type: IWeightedPool)), `IERC20(tokenSpent).approve(address(_vault), type(uint256).max)` (inline cast call IERC20(...).approve()), `IERC20(tokenReceived).approve(address(_vault), type(uint256).max)` (inline cast call IERC20(...).approve())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### Exchange.convertFundsFromInput

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: convertFundsFromInput
- **Line Range**: L80-90
- **File**: `DAppSCAN-source/contracts/consensys-GrowthDeFi WHEAT/wheat-v1-core-8360ac0a537589bb974e8a5a169bb3e7c95d2857/contracts/Exchange.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`convertFundsFromInput`, lines=`L80-90`

#### 2. Function Source Code
```solidity
function convertFundsFromInput(address _from, address _to, uint256 _inputAmount, uint256 _minOutputAmount) external override returns (uint256 _outputAmount)
	{
		address _sender = msg.sender;
		Transfers._pullFunds(_from, _sender, _inputAmount);
		_inputAmount = Math._min(_inputAmount, Transfers._getBalance(_from)); // deals with potential transfer tax
		_outputAmount = UniswapV2ExchangeAbstraction._convertFundsFromInput(router, _from, _to, _inputAmount, _minOutputAmount);
		_outputAmount = Math._min(_outputAmount, Transfers._getBalance(_to)); // deals with potential transfer tax
		Transfers._pushFunds(_to, _sender, _outputAmount);
		return _outputAmount;
	}
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['router']
- **External calls**: `Transfers._pullFunds(_from, _sender, _inputAmount)` (method: _pullFunds, receiver: Transfers), `Math._min(_inputAmount, Transfers._getBalance(_from))` (method: _min, receiver: Math), `Transfers._getBalance(_from)` (method: _getBalance, receiver: Transfers), `UniswapV2ExchangeAbstraction._convertFundsFromInput(router, _from, _to, _inputAmount, _minOutputAmount)` (method: _convertFundsFromInput, receiver: UniswapV2ExchangeAbstraction), `Math._min(_outputAmount, Transfers._getBalance(_to))` (method: _min, receiver: Math), `Transfers._getBalance(_to)` (method: _getBalance, receiver: Transfers), `Transfers._pushFunds(_to, _sender, _outputAmount)` (method: _pushFunds, receiver: Transfers)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['router']
- **External calls**: `Transfers._pullFunds(_from, _sender, _inputAmount)` (call on interface/contract type 'Transfers'), `Math._min(_inputAmount, Transfers._getBalance(_from))` (call on interface/contract type 'Math'), `Transfers._getBalance(_from)` (call on interface/contract type 'Transfers'), `UniswapV2ExchangeAbstraction._convertFundsFromInput(router, _from, _to, _inputAmount, _minOutputAmount)` (call on interface/contract type 'UniswapV2ExchangeAbstraction'), `Math._min(_outputAmount, Transfers._getBalance(_to))` (call on interface/contract type 'Math'), `Transfers._getBalance(_to)` (call on interface/contract type 'Transfers'), `Transfers._pushFunds(_to, _sender, _outputAmount)` (call on interface/contract type 'Transfers')
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### AMM.mintShareTokenTo

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call present — unchecked return value plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: mintShareTokenTo
- **Line Range**: L500-502
- **File**: `DAppSCAN-source/contracts/consensys-MCDEX_Mai_Protocol_V2/mai-protocol-v2-4b198083ec4ae2d6851e101fc44ea333eaa3cd92/contracts/liquidity/AMM.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`mintShareTokenTo`, lines=`L500-502`

#### 2. Function Source Code
```solidity
function mintShareTokenTo(address guy, uint256 amount) internal {
        shareToken.mint(guy, amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['shareToken']
- **External calls**: `shareToken.mint(guy, amount)` (method: mint, receiver: shareToken)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['shareToken']
- **External calls**: `shareToken.mint(guy, amount)` (call on contract-typed state var 'shareToken' (type: ShareToken))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### EternalHeroesFactory._buy

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: _buy
- **Line Range**: L279-285
- **File**: `DAppSCAN-source/contracts/consensys-Skyweaver/Skyweaver-contracts-bde0c184db6168bf86656a48b12d5747950b54d9/contracts/shop/EternalHeroesFactory.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`_buy`, lines=`L279-285`

#### 2. Function Source Code
(76 lines, showing first 30 + last 15)
```solidity
function _buy(
    uint256[] memory _ids,
    uint256[] memory _amounts,
    uint256[] memory _expectedTiers,
    uint256 _arcAmount,
    address _recipient)
    internal
  {
    // Input validation
    uint256 nTokens = _ids.length;
    uint256 tier_size = tierSize;

    // Load tokens to purchase supplies
    uint256[] memory current_supplies = factoryManager.getCurrentSupplies(_ids);

    // Total amount of card to purchase
    uint256 total_cost = 0;

    // Keep track of amount for each hero the user actually purchases.
    // While less efficient in case of amounts reduced to 0,
    // it keeps the code simpler.
    uint256[] memory amounts_to_mint = new uint256[](nTokens);

    // Validate purchase and count # of cards to purchase
    for (uint256 i = 0; i < nTokens; i++) {
      uint256 id = _ids[i];
      uint256 supply = current_supplies[i];
      uint256 to_mint = 0;
      uint256 amount = _amounts[i];

    // ... truncated ...

    // Check if enough ARC was sent and refund exceeding amount
    // .sub() will revert if insufficient amount received for purchase
    // SWC-107-Reentrancy: L279-285
    uint256 refundAmount = _arcAmount.sub(total_cost);
    if (refundAmount > 0) {
      arcadeumCoin.safeTransferFrom(address(this), _recipient, arcadeumCoinID, refundAmount, "");
    }

    // Mint tokens to recipient
    factoryManager.batchMint(_recipient, _ids, amounts_to_mint, "");

    // Emit event
    emit AssetsPurchased(_recipient, _ids, amounts_to_mint, total_cost);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['arcadeumCoin', 'arcadeumCoinID', 'factoryManager', 'floorPrice', 'isPurchasable', 'priceIncrement', 'tierSize']
- **External calls**: `factoryManager.getCurrentSupplies(_ids)` (method: getCurrentSupplies, receiver: factoryManager), `arcadeumCoin.safeTransferFrom(address(this), _recipient, arcadeumCoinID, refundAmount, "")` (method: safeTransferFrom, receiver: arcadeumCoin), `factoryManager.batchMint(_recipient, _ids, amounts_to_mint, "")` (method: batchMint, receiver: factoryManager)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['arcadeumCoin', 'arcadeumCoinID', 'factoryManager', 'floorPrice', 'isPurchasable', 'priceIncrement', 'tierSize']
- **External calls**: `factoryManager.getCurrentSupplies(_ids)` (call on contract-typed state var 'factoryManager' (type: ISWSupplyManager)), `arcadeumCoin.safeTransferFrom(address(this), _recipient, arcadeumCoinID, refundAmount, "")` (SafeERC20 .safeTransferFrom()), `factoryManager.batchMint(_recipient, _ids, amounts_to_mint, "")` (call on contract-typed state var 'factoryManager' (type: ISWSupplyManager))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### OVM_L1ERC20Gateway._handleInitiateDeposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _handleInitiateDeposit
- **Line Range**: L76-L81
- **File**: `DAppSCAN-source/contracts/openzeppelin-Optimism/contracts-18e128343731b9bde23812ce932e24d81440b6b7/contracts/optimistic-ethereum/OVM/bridge/tokens/OVM_L1ERC20Gateway.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_handleInitiateDeposit`, lines=`L76-L81`

#### 2. Function Source Code
```solidity
function _handleInitiateDeposit(
        address _from,
        address, // _to,
        uint256 _amount
    )
        internal
        override
    {
         // Hold on to the newly deposited funds
         //SWC-104-Unchecked Call Return Value: L76-L81
        l1ERC20.transferFrom(
            _from,
            address(this),
            _amount
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['l1ERC20']
- **External calls**: `l1ERC20.transferFrom(
            _from,
            address(this),
            _amount
        )` (method: transferFrom, receiver: l1ERC20)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['l1ERC20']
- **External calls**: `l1ERC20.transferFrom(
            _from,
            address(this),
            _amount
        )` (call on contract-typed state var 'l1ERC20' (type: iOVM_ERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

### AdminImpl._setPriceOracle

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: _setPriceOracle
- **Line Range**: L258-L275
- **File**: `DAppSCAN-source/contracts/openzeppelin-Solo_Margin_Protocol/solo-17df84db351d5438e1b7437572722b4f52c8b2b4/contracts/protocol/impl/AdminImpl.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`_setPriceOracle`, lines=`L258-L275`

#### 2. Function Source Code
```solidity
function _setPriceOracle(
        Storage.State storage state,
        uint256 marketId,
        IPriceOracle priceOracle
    )
        private
    {
        state.markets[marketId].priceOracle = priceOracle;

        // require oracle can return non-zero price
        address token = state.markets[marketId].token;

        Require.that(
            priceOracle.getPrice(token).value != 0,
            FILE,
            "Invalid oracle price"
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['FILE']
- **External calls**: `Require.that(
            priceOracle.getPrice(token).value != 0,
            FILE,
            "Invalid oracle price"
 ` (method: that, receiver: Require), `priceOracle.getPrice(token)` (method: getPrice, receiver: priceOracle)
- **Cross-contract**: True

**Reconstructed from current AST:**
- **State variables**: ['FILE']
- **External calls**: `Require.that(
            priceOracle.getPrice(token).value != 0,
            FILE,
            "Invalid oracle price"
 ` (call on interface/contract type 'Require'), `priceOracle.getPrice(token)` (call on contract-typed local var 'priceOracle' (type: IPriceOracle))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ✅

---
## TEST Intra-Contract (9 items)

### BUSDVYNCSTAKE.stake

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: stake
- **Line Range**: L154
- **File**: `DAppSCAN-source/contracts/Hacken-VYNKSAFE/code/main.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`stake`, lines=`L154`

#### 2. Function Source Code
(69 lines, showing first 30 + last 15)
```solidity
function stake(uint256 amount) external nonReentrant {
        busd.transferFrom(msg.sender, address(this), amount);
        userInfo[msg.sender]
            .lastCompoundedRewardWithStakeUnstakeClaim = lastCompoundedReward(
            msg.sender
        );

        if (userInfo[msg.sender].isStaker == true) {
            uint256 _pendingReward = compoundedReward(msg.sender);
            uint256 cpending = cPendingReward(msg.sender);
            userInfo[msg.sender].stakeBalanceWithReward =
                userInfo[msg.sender].stakeBalanceWithReward +
                _pendingReward;
            userInfo[msg.sender].autoClaimWithStakeUnstake =
                userInfo[msg.sender].autoClaimWithStakeUnstake +
                _pendingReward;
            userInfo[msg.sender].totalClaimedReward = 0;
            if (
                block.timestamp <
                userInfo[msg.sender].nextCompoundDuringStakeUnstake
            ) {
                userInfo[msg.sender].stakeBalanceWithReward =
                    userInfo[msg.sender].stakeBalanceWithReward +
                    cpending;
                userInfo[msg.sender].autoClaimWithStakeUnstake =
                    userInfo[msg.sender].autoClaimWithStakeUnstake +
                    cpending;
            }
        }

    // ... truncated ...
            (busdAdded + amountToSwap);
        userInfo[msg.sender].stakeBalance =
            userInfo[msg.sender].stakeBalance +
            (busdAdded + amountToSwap);
        userInfo[msg.sender].lastStakeUnstakeTimestamp = block.timestamp;
        userInfo[msg.sender].nextCompoundDuringStakeUnstake = nextCompound();
        userInfo[msg.sender].isStaker = true;

        // trasnfer back amount left
        if (amount > busdAdded + amountToSwap) {
            busd.transfer(msg.sender, amount - (busdAdded + amountToSwap));
        }
        s = s + busdAdded + amountToSwap;
        emit Stake(msg.sender, (busdAdded + amountToSwap));
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['busd', 'router', 's', 'totalSupply', 'userInfo', 'vync']
- **External calls**: `busd.transferFrom(msg.sender, address(this), amount)` (method: transferFrom, receiver: busd), `router.addLiquidity(
            address(vync),
            address(busd),
            vyncOut,
            amountLeft,
` (method: addLiquidity, receiver: router), `busd.transfer(msg.sender, amount - (busdAdded + amountToSwap))` (method: transfer, receiver: busd)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['busd', 'router', 's', 'totalSupply', 'userInfo', 'vync']
- **External calls**: `busd.transferFrom(msg.sender, address(this), amount)` (call on contract-typed state var 'busd' (type: IERC20)), `router.addLiquidity(
            address(vync),
            address(busd),
            vyncOut,
            amountLeft,
` (call on contract-typed state var 'router' (type: IUniswapV2Router02)), `busd.transfer(msg.sender, amount - (busdAdded + amountToSwap))` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### BankingNode.unstake

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: unstake
- **Line Range**: L615-L637
- **File**: `DAppSCAN-source/contracts/PeckShield-BNPL/BNPL-0ee587a081668dcab166a3a275b8a6c4794ead4d/contracts/BankingNode.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`unstake`, lines=`L615-L637`

#### 2. Function Source Code
```solidity
function unstake() external {
        uint256 _userAmount = unbondingShares[msg.sender];
        if (_userAmount == 0) {
            revert ZeroInput();
        }
        //assuming 13s block, 46523 blocks for 1 week
        if (block.number < unbondBlock[msg.sender] + 46523) {
            revert LoanStillUnbonding();
        }
        uint256 _unbondingAmount = unbondingAmount;
        uint256 _totalUnbondingShares = totalUnbondingShares;
        address _bnpl = BNPL;
        //safe div: if user amount > 0, then totalUnbondingShares always > 0
        uint256 _what = (_userAmount * _unbondingAmount) /
            _totalUnbondingShares;
        //transfer the tokens to user
        TransferHelper.safeTransfer(_bnpl, msg.sender, _what);
        //update the balances
        unbondingShares[msg.sender] = 0;
        unbondingAmount -= _what;

        emit bnplWithdrawn(msg.sender, _what);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['BNPL', 'totalUnbondingShares', 'unbondBlock', 'unbondingAmount', 'unbondingShares']
- **External calls**: `TransferHelper.safeTransfer(_bnpl, msg.sender, _what)` (method: safeTransfer, receiver: TransferHelper)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['BNPL', 'totalUnbondingShares', 'unbondBlock', 'unbondingAmount', 'unbondingShares']
- **External calls**: `TransferHelper.safeTransfer(_bnpl, msg.sender, _what)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### C98MSiG.vote

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: vote
- **Line Range**: L181
- **File**: `DAppSCAN-source/contracts/PeckShield-COIN98/code/code.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`vote`, lines=`L181`

#### 2. Function Source Code
```solidity
function vote()
        isOwner(msg.sender)
        public override returns (bool) {
        VoteProgress memory progress = _voteProgress;
        require(progress.requestId > 0, "C98MSiG: No pending request");
        if (_votes[msg.sender] < progress.requestId) {
            _votes[msg.sender] = progress.requestId;
            progress.currentVote += _votePowers[msg.sender];
            _voteProgress = progress;
            emit Voted(msg.sender, progress.requestId, progress.currentVote, progress.requiredVote);
        }
        if (progress.currentVote >= progress.requiredVote) {
            Request memory req = _request;
            (bool success,) = req.destination.call{value: req.value}(req.data);
            if (success) {
                delete _request;
                delete _voteProgress;
                Executed(true, progress.requestId, req.destination, req.value, req.data);
            }
            else {
                Executed(false, progress.requestId, req.destination, req.value, req.data);
            }
        }
        return true;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_request', '_votePowers', '_voteProgress', '_votes']
- **External calls**: `req.destination.call{value: req.value}(req.data)` (method: call, receiver: req)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['_request', '_votePowers', '_voteProgress', '_votes']
- **External calls**: `req.destination.call{value: req.value}(req.data)` (low-level .call())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### StakingV2.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L340-L359
- **File**: `DAppSCAN-source/contracts/PeckShield-TranchessV1.1/contract-core-68a86350313c1cb9e5467e791d3e9efaf228a0df/contracts/exchange/StakingV2.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L340-L359`

#### 2. Function Source Code
```solidity
function deposit(uint256 tranche, uint256 amount) public whenNotPaused {
        uint256 rebalanceSize = _fundRebalanceSize();
        _checkpoint(rebalanceSize);
        _userCheckpoint(msg.sender, rebalanceSize);
        if (tranche == TRANCHE_M) {
            tokenM.safeTransferFrom(msg.sender, address(this), amount);
        } else if (tranche == TRANCHE_A) {
            tokenA.safeTransferFrom(msg.sender, address(this), amount);
        } else {
            tokenB.safeTransferFrom(msg.sender, address(this), amount);
        }
        _availableBalances[msg.sender][tranche] = _availableBalances[msg.sender][tranche].add(
            amount
        );
        _totalSupplies[tranche] = _totalSupplies[tranche].add(amount);

        _updateWorkingBalance(msg.sender);

        emit Deposited(tranche, msg.sender, amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['TRANCHE_A', 'TRANCHE_M', '_availableBalances', '_totalSupplies', 'tokenA', 'tokenB', 'tokenM']
- **External calls**: `tokenM.safeTransferFrom(msg.sender, address(this), amount)` (method: safeTransferFrom, receiver: tokenM), `tokenA.safeTransferFrom(msg.sender, address(this), amount)` (method: safeTransferFrom, receiver: tokenA), `tokenB.safeTransferFrom(msg.sender, address(this), amount)` (method: safeTransferFrom, receiver: tokenB)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['TRANCHE_A', 'TRANCHE_M', '_availableBalances', '_totalSupplies', 'tokenA', 'tokenB', 'tokenM']
- **External calls**: `tokenM.safeTransferFrom(msg.sender, address(this), amount)` (SafeERC20 .safeTransferFrom()), `tokenA.safeTransferFrom(msg.sender, address(this), amount)` (SafeERC20 .safeTransferFrom()), `tokenB.safeTransferFrom(msg.sender, address(this), amount)` (SafeERC20 .safeTransferFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### bVault.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L357-L375
- **File**: `DAppSCAN-source/contracts/PeckShield-btdotfinance/bt-finance-6300bc1271b73a1755fae02594d25fdf6fa39a9c/contracts/vault/bVault.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L357-L375`

#### 2. Function Source Code
```solidity
function deposit(uint _amount) public onlyRestrictContractCall {
		require(_amount > 0, "Cannot deposit 0");
        uint _pool = balance();
        uint _before = token.balanceOf(address(this));
        token.safeTransferFrom(msg.sender, address(this), _amount);
        uint _after = token.balanceOf(address(this));
        _amount = _after.sub(_before); // Additional check for deflationary tokens
        uint shares = 0;
        if (totalSupply() == 0) {
            shares = _amount;
        } else {
            shares = (_amount.mul(totalSupply())).div(_pool);
        }
        _mint(msg.sender, shares);
        userDepoistTime[msg.sender] = now;
        if (token.balanceOf(address(this))>earnLowerlimit){
          earn();
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['earnLowerlimit', 'userDepoistTime']
- **External calls**: `token.balanceOf(address(this))` (method: balanceOf, receiver: token), `token.safeTransferFrom(msg.sender, address(this), _amount)` (method: safeTransferFrom, receiver: token), `token.balanceOf(address(this))` (method: balanceOf, receiver: token), `token.balanceOf(address(this))` (method: balanceOf, receiver: token)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['earnLowerlimit', 'token', 'userDepoistTime']
- **External calls**: `token.balanceOf(address(this))` (call on contract-typed state var 'token' (type: IERC20)), `token.safeTransferFrom(msg.sender, address(this), _amount)` (SafeERC20 .safeTransferFrom()), `token.balanceOf(address(this))` (call on contract-typed state var 'token' (type: IERC20)), `token.balanceOf(address(this))` (call on contract-typed state var 'token' (type: IERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ❌
- External calls match: ✅
- Cross-contract match: ❌

### FeeCollector.trade

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: trade
- **Line Range**: L361
- **File**: `DAppSCAN-source/contracts/QuillAudits-1inch-Fee Collector/fee-collector-3c2626763fd829500496f15476d5e98fbdf4f574/contracts/FeeCollector.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`trade`, lines=`L361`

#### 2. Function Source Code
```solidity
function trade(IERC20 erc20, uint256 amount) external {
        TokenInfo storage _token = tokenInfo[erc20];
        uint256 currentEpoch = _token.currentEpoch;
        uint256 firstUnprocessedEpoch = _token.firstUnprocessedEpoch;
        EpochBalance storage epochBalance = _token.epochBalance[firstUnprocessedEpoch];
        EpochBalance storage currentEpochBalance = _token.epochBalance[currentEpoch];

        uint256 currentEpochStored = currentEpoch;

        uint256 unprocessedTotalSupply = epochBalance.totalSupply;
        uint256 unprocessedTokenBalance = unprocessedTotalSupply - epochBalance.tokenSpent;
        uint256 tokenBalance = unprocessedTokenBalance;
        if (firstUnprocessedEpoch != currentEpoch) {
            tokenBalance += currentEpochBalance.totalSupply - currentEpochBalance.tokenSpent;
        }

        // SWC-114-Transaction Order Dependence: L361
        uint256 returnAmount = amount * tokenBalance / value(erc20);
        require(tokenBalance >= returnAmount, "not enough tokens");

        if (firstUnprocessedEpoch == currentEpoch) {
            currentEpoch += 1;
        }

        _updateTokenState(erc20, -int256(returnAmount), currentEpochStored, firstUnprocessedEpoch);

        if (returnAmount <= unprocessedTokenBalance) {
            if (returnAmount == unprocessedTokenBalance) {
                _token.firstUnprocessedEpoch += 1;
            }

            epochBalance.tokenSpent += returnAmount;
            epochBalance.inchBalance += amount;
        } else {
            uint256 amountPart = unprocessedTokenBalance * amount / returnAmount;

            epochBalance.tokenSpent = unprocessedTotalSupply;
            epochBalance.inchBalance += amountPart;

            currentEpochBalance.tokenSpent += returnAmount - unprocessedTokenBalance;
            currentEpochBalance.inchBalance += amount - amountPart;

            _token.firstUnprocessedEpoch += 1;
            currentEpoch += 1;
        }

        if (currentEpoch != currentEpochStored) {
            _token.currentEpoch = currentEpoch;
        }

        token.safeTransferFrom(msg.sender, address(this), amount);
        erc20.safeTransfer(msg.sender, returnAmount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['token', 'tokenInfo']
- **External calls**: `token.safeTransferFrom(msg.sender, address(this), amount)` (method: safeTransferFrom, receiver: token), `erc20.safeTransfer(msg.sender, returnAmount)` (method: safeTransfer, receiver: erc20)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['token', 'tokenInfo']
- **External calls**: `token.safeTransferFrom(msg.sender, address(this), amount)` (SafeERC20 .safeTransferFrom()), `erc20.safeTransfer(msg.sender, returnAmount)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### StrategyCurveSCRVv4_1.harvest

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: harvest
- **Line Range**: L153-197
- **File**: `DAppSCAN-source/contracts/QuillAudits-Pickle Finance-Strategy-Curve-scrv-v4_1/protocol-master/strategy-curve-scrv-v4_1.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`harvest`, lines=`L153-197`

#### 2. Function Source Code
```solidity
function harvest() public override onlyBenevolent {
        // Anyone can harvest it at any given time.
        // I understand the possibility of being frontrun / sandwiched
        // But ETH is a dark forest, and I wanna see how this plays out
        // i.e. will be be heavily frontrunned/sandwiched?
        //      if so, a new strategy will be deployed.

        // stablecoin we want to convert to
        (address to, uint256 toIndex) = getMostPremium();

        // Collects crv tokens
        // Don't bother voting in v1
        SCRVVoter(scrvVoter).harvest(gauge);
        uint256 _crv = IERC20(crv).balanceOf(address(this));
        if (_crv > 0) {
            // How much CRV to keep to restake?
            uint256 _keepCRV = _crv.mul(keepCRV).div(keepCRVMax);
            IERC20(crv).safeTransfer(address(crvLocker), _keepCRV);

            // How much CRV to swap?
            _crv = _crv.sub(_keepCRV);
            _swapUniswap(crv, to, _crv);
        }

        // Collects SNX tokens
        SCRVVoter(scrvVoter).claimRewards();
        uint256 _snx = IERC20(snx).balanceOf(address(this));
        if (_snx > 0) {
            _swapUniswap(snx, to, _snx);
        }

        // Adds liquidity to curve.fi's susd pool
        // to get back want (scrv)
        uint256 _to = IERC20(to).balanceOf(address(this));
        if (_to > 0) {
            IERC20(to).safeApprove(curve, 0);
            IERC20(to).safeApprove(curve, _to);
            uint256[4] memory liquidity;
            liquidity[toIndex] = _to;
            ICurveFi_4(curve).add_liquidity(liquidity, 0);
        }

        // We want to get back sCRV
        _distributePerformanceFeesAndDeposit();
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['crv', 'crvLocker', 'curve', 'gauge', 'keepCRV', 'keepCRVMax', 'scrvVoter', 'snx']
- **External calls**: `SCRVVoter(scrvVoter).harvest(gauge)` (method: harvest, receiver: SCRVVoter), `IERC20(crv).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IERC20(crv).safeTransfer(address(crvLocker), _keepCRV)` (method: safeTransfer, receiver: IERC20), `SCRVVoter(scrvVoter).claimRewards()` (method: claimRewards, receiver: SCRVVoter), `IERC20(snx).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IERC20(to).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IERC20(to).safeApprove(curve, 0)` (method: safeApprove, receiver: IERC20), `IERC20(to).safeApprove(curve, _to)` (method: safeApprove, receiver: IERC20), `ICurveFi_4(curve).add_liquidity(liquidity, 0)` (method: add_liquidity, receiver: ICurveFi_4)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['crv', 'crvLocker', 'curve', 'gauge', 'keepCRV', 'keepCRVMax', 'scrvVoter', 'snx']
- **External calls**: `SCRVVoter(scrvVoter).harvest(gauge)` (inline cast call SCRVVoter(...).harvest()), `IERC20(crv).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IERC20(crv).safeTransfer(address(crvLocker), _keepCRV)` (SafeERC20 .safeTransfer()), `SCRVVoter(scrvVoter).claimRewards()` (inline cast call SCRVVoter(...).claimRewards()), `IERC20(snx).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IERC20(to).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IERC20(to).safeApprove(curve, 0)` (SafeERC20 .safeApprove()), `IERC20(to).safeApprove(curve, _to)` (SafeERC20 .safeApprove()), `ICurveFi_4(curve).add_liquidity(liquidity, 0)` (inline cast call ICurveFi_4(...).add_liquidity())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### ChainlinkPriceFeed._getLatestRoundData

**Pre-classification**: ❌ DUBIOUS
**Reason**: View/pure function with only read-only external calls — unchecked return has no state impact

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _getLatestRoundData
- **Line Range**: L96 -L100
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-PerpetualProtocolV2/perp-oracle-contract-ba78a5b87098dcffb7285fc585afff1001a87232/contracts/ChainlinkPriceFeed.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_getLatestRoundData`, lines=`L96 -L100`

#### 2. Function Source Code
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

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_aggregator']
- **External calls**: `_aggregator.latestRoundData()` (method: latestRoundData, receiver: _aggregator)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['_aggregator']
- **External calls**: `_aggregator.latestRoundData()` (call on contract-typed state var '_aggregator' (type: AggregatorV3Interface))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### Fund.finalizeGrant

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: finalizeGrant
- **Line Range**: L119-134
- **File**: `DAppSCAN-source/contracts/openzeppelin-Endaoment/endaoment-contracts-f60aa253d3d869ad6460877f23e6092acb313add/Fund.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`finalizeGrant`, lines=`L119-134`

#### 2. Function Source Code
```solidity
function finalizeGrant(uint index, address tokenAddress, address adminContractAddress) public onlyAdminOrRole(adminContractAddress, IEndaomentAdmin.Role.ACCOUNTANT){
        EndaomentAdmin endaomentAdmin = EndaomentAdmin(adminContractAddress);
        admin = endaomentAdmin.getRoleAddress(IEndaomentAdmin.Role.ADMIN);
        Grant storage grant = grants[index];
        require(grant.complete == false);
        ERC20 t = ERC20(tokenAddress);

        //Process fees:
        uint256 fee = (grant.value)/100;
        uint256 finalGrant = (grant.value * 99)/100;
        t.transfer(admin, fee);

        t.transfer(grant.recipient, finalGrant);

        grant.complete = true;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['admin', 'grants']
- **External calls**: `endaomentAdmin.getRoleAddress(IEndaomentAdmin.Role.ADMIN)` (method: getRoleAddress, receiver: endaomentAdmin), `t.transfer(admin, fee)` (method: transfer, receiver: t), `t.transfer(grant.recipient, finalGrant)` (method: transfer, receiver: t)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['admin', 'grants']
- **External calls**: `endaomentAdmin.getRoleAddress(IEndaomentAdmin.Role.ADMIN)` (call on contract-typed local var 'endaomentAdmin' (type: EndaomentAdmin)), `t.transfer(admin, fee)` (low-level .transfer()), `t.transfer(grant.recipient, finalGrant)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

---
## VAL Intra-Contract (14 items)

### Graph._withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _withdraw
- **Line Range**: L136
- **File**: `DAppSCAN-source/contracts/Hacken-Tenderize/tender-core-1fd606141625171fe792045ae9233890262d2d62/contracts/tenderizer/integrations/graph/Graph.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_withdraw`, lines=`L136`

#### 2. Function Source Code
```solidity
function _withdraw(address _account, uint256 _withdrawalID) internal override {
        uint256 amount = withdrawPool.withdraw(_withdrawalID, _account);

        // Transfer amount from unbondingLock to _account
        // SWC-104-Unchecked Call Return Value: L136
        try steak.transfer(_account, amount) {} catch {
            // Account for roundoff errors in shares calculations
            uint256 steakBal = steak.balanceOf(address(this));
            if (amount > steakBal) {
                steak.transfer(_account, steakBal);
            }
        }

        emit Withdraw(_account, amount, _withdrawalID);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['steak', 'withdrawPool']
- **External calls**: `withdrawPool.withdraw(_withdrawalID, _account)` (method: withdraw, receiver: withdrawPool), `steak.transfer(_account, amount)` (method: transfer, receiver: steak), `steak.balanceOf(address(this))` (method: balanceOf, receiver: steak), `steak.transfer(_account, steakBal)` (method: transfer, receiver: steak)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['steak', 'withdrawPool']
- **External calls**: `withdrawPool.withdraw(_withdrawalID, _account)` (call on contract-typed state var 'withdrawPool' (type: WithdrawalPools.Pool)), `steak.transfer(_account, amount)` (low-level .transfer()), `steak.balanceOf(address(this))` (call on contract-typed state var 'steak' (type: IERC20)), `steak.transfer(_account, steakBal)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MdexWorker02._reinvest

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: _reinvest
- **Line Range**: L234
- **File**: `DAppSCAN-source/contracts/Inspex-MDEX Integration/bsc-alpaca-contract-a3a14d27a4803afebdcf783c9ce8764b65f5587d/MdexWorker02.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`_reinvest`, lines=`L234`

#### 2. Function Source Code
```solidity
function _reinvest(
    address _treasuryAccount,
    uint256 _treasuryBountyBps,
    uint256 _callerBalance,
    uint256 _reinvestThreshold
  ) internal {
    // 1. Withdraw all the rewards. Return if reward <= _reinvestThreshold.
    bscPool.withdraw(pid, 0);
    uint256 reward = mdx.balanceOf(address(this));
    if (reward <= _reinvestThreshold) return;

    // 2. Approve tokens
    mdx.safeApprove(address(router), uint256(-1));
    address(lpToken).safeApprove(address(bscPool), uint256(-1));
//SWC-114-Transaction Order Dependence:L234
    // 3. Send the reward bounty to the _treasuryAccount.
    uint256 bounty = reward.mul(_treasuryBountyBps) / 10000;
    if (bounty > 0) {
      uint256 beneficialVaultBounty = bounty.mul(beneficialVaultBountyBps) / 10000;
      if (beneficialVaultBounty > 0) _rewardToBeneficialVault(beneficialVaultBounty, _callerBalance);
      mdx.safeTransfer(_treasuryAccount, bounty.sub(beneficialVaultBounty));
    }
//SWC-114-Transaction Order Dependence:L239、242、243
    // 4. Convert all the remaining rewards to BaseToken according to config path.
    router.swapExactTokensForTokens(reward.sub(bounty), 0, getReinvestPath(), address(this), now);

    // 5. Use add Token strategy to convert all BaseToken without both caller balance and buyback amount to LP tokens.
    baseToken.safeTransfer(address(addStrat), actualBaseTokenBalance().sub(_callerBalance));
    addStrat.execute(address(0), 0, abi.encode(0));

    // 6. Stake LPs for more rewards
    bscPool.deposit(pid, lpToken.balanceOf(address(this)));

    // 7. Reset approval
    mdx.safeApprove(address(router), 0);
    address(lpToken).safeApprove(address(bscPool), 0);

    emit Reinvest(_treasuryAccount, reward, bounty);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['addStrat', 'baseToken', 'beneficialVaultBountyBps', 'bscPool', 'lpToken', 'mdx', 'pid', 'router']
- **External calls**: `bscPool.withdraw(pid, 0)` (method: withdraw, receiver: bscPool), `mdx.balanceOf(address(this))` (method: balanceOf, receiver: mdx), `mdx.safeApprove(address(router), uint256(-1))` (method: safeApprove, receiver: mdx), `address(lpToken).safeApprove(address(bscPool), uint256(-1))` (method: safeApprove, receiver: (complex)), `mdx.safeTransfer(_treasuryAccount, bounty.sub(beneficialVaultBounty))` (method: safeTransfer, receiver: mdx), `router.swapExactTokensForTokens(reward.sub(bounty), 0, getReinvestPath(), address(this), now)` (method: swapExactTokensForTokens, receiver: router), `baseToken.safeTransfer(address(addStrat), actualBaseTokenBalance().sub(_callerBalance))` (method: safeTransfer, receiver: baseToken), `addStrat.execute(address(0), 0, abi.encode(0))` (method: execute, receiver: addStrat), `bscPool.deposit(pid, lpToken.balanceOf(address(this)))` (method: deposit, receiver: bscPool), `lpToken.balanceOf(address(this))` (method: balanceOf, receiver: lpToken), `mdx.safeApprove(address(router), 0)` (method: safeApprove, receiver: mdx), `address(lpToken).safeApprove(address(bscPool), 0)` (method: safeApprove, receiver: (complex))
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['addStrat', 'baseToken', 'beneficialVaultBountyBps', 'bscPool', 'lpToken', 'mdx', 'pid', 'router']
- **External calls**: `bscPool.withdraw(pid, 0)` (call on contract-typed state var 'bscPool' (type: IBSCPool)), `mdx.balanceOf(address(this))` (known ERC-like method .balanceOf() on 'mdx'), `mdx.safeApprove(address(router), uint256(-1))` (SafeERC20 .safeApprove()), `address(lpToken).safeApprove(address(bscPool), uint256(-1))` (SafeERC20 .safeApprove()), `mdx.safeTransfer(_treasuryAccount, bounty.sub(beneficialVaultBounty))` (SafeERC20 .safeTransfer()), `router.swapExactTokensForTokens(reward.sub(bounty), 0, getReinvestPath(), address(this), now)` (call on contract-typed state var 'router' (type: IMdexRouter)), `baseToken.safeTransfer(address(addStrat), actualBaseTokenBalance().sub(_callerBalance))` (SafeERC20 .safeTransfer()), `addStrat.execute(address(0), 0, abi.encode(0))` (call on contract-typed state var 'addStrat' (type: IStrategy)), `bscPool.deposit(pid, lpToken.balanceOf(address(this)))` (call on contract-typed state var 'bscPool' (type: IBSCPool)), `lpToken.balanceOf(address(this))` (call on contract-typed state var 'lpToken' (type: IPancakePair)), `mdx.safeApprove(address(router), 0)` (SafeERC20 .safeApprove()), `address(lpToken).safeApprove(address(bscPool), 0)` (SafeERC20 .safeApprove())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MdexWorker02._rewardToBeneficialVault

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: _rewardToBeneficialVault
- **Line Range**: L345-346、352
- **File**: `DAppSCAN-source/contracts/Inspex-MDEX Integration/bsc-alpaca-contract-a3a14d27a4803afebdcf783c9ce8764b65f5587d/MdexWorker02.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`_rewardToBeneficialVault`, lines=`L345-346、352`

#### 2. Function Source Code
```solidity
function _rewardToBeneficialVault(uint256 _beneficialVaultBounty, uint256 _callerBalance) internal {
    /// 1. read base token from beneficialVault
    address beneficialVaultToken = beneficialVault.token();
    /// 2. swap reward token to beneficialVaultToken
    uint256[] memory amounts =
      router.swapExactTokensForTokens(_beneficialVaultBounty, 0, rewardPath, address(this), now);
    /// 3. if beneficialvault token not equal to baseToken regardless of a caller balance, can directly transfer to beneficial vault
    /// otherwise, need to keep it as a buybackAmount,
    /// since beneficial vault is the same as the calling vault, it will think of this reward as a `back` amount to paydebt/ sending back to a position owner
    if (beneficialVaultToken != baseToken) {
      buybackAmount = 0;
      beneficialVaultToken.safeTransfer(address(beneficialVault), beneficialVaultToken.myBalance());
      emit BeneficialVaultTokenBuyback(msg.sender, beneficialVault, amounts[amounts.length - 1]);
    } else {
      buybackAmount = beneficialVaultToken.myBalance().sub(_callerBalance);
    }
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['baseToken', 'beneficialVault', 'buybackAmount', 'rewardPath', 'router']
- **External calls**: `beneficialVault.token()` (method: token, receiver: beneficialVault), `router.swapExactTokensForTokens(_beneficialVaultBounty, 0, rewardPath, address(this), now)` (method: swapExactTokensForTokens, receiver: router), `beneficialVaultToken.safeTransfer(address(beneficialVault), beneficialVaultToken.myBalance())` (method: safeTransfer, receiver: beneficialVaultToken)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['baseToken', 'beneficialVault', 'buybackAmount', 'rewardPath', 'router']
- **External calls**: `beneficialVault.token()` (call on contract-typed state var 'beneficialVault' (type: IVault)), `router.swapExactTokensForTokens(_beneficialVaultBounty, 0, rewardPath, address(this), now)` (call on contract-typed state var 'router' (type: IMdexRouter)), `beneficialVaultToken.safeTransfer(address(beneficialVault), beneficialVaultToken.myBalance())` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### BaseRewards.getReward

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: getReward
- **Line Range**: L75
- **File**: `DAppSCAN-source/contracts/Iosiro-1inch Exchange Staking Rewards Smart Contract Audit/liquidity-protocol-c9c8bc600e8e7897f70f84b006de601d4f4bcbe3/BaseRewards.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`getReward`, lines=`L75`

#### 2. Function Source Code
```solidity
function getReward(uint i) public updateReward(msg.sender) {
        TokenRewards storage tr = tokenRewards[i];
        uint256 reward = tr.rewards[msg.sender];
        if (reward > 0) {
            tr.rewards[msg.sender] = 0;
            tr.gift.transfer(msg.sender, reward);
            emit RewardPaid(msg.sender, reward);
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['tokenRewards']
- **External calls**: `tr.gift.transfer(msg.sender, reward)` (method: transfer, receiver: tr)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['tokenRewards']
- **External calls**: `tr.gift.transfer(msg.sender, reward)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### SNXFlashLoanTool.swap

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: swap
- **Line Range**: L143
- **File**: `DAppSCAN-source/contracts/Iosiro-SNX FlashBurn Smart Contract Audit/flashburn-3aa02a3d63d9e0110a5b6669a4a4011ceee3cf2b/packages/contracts/contracts/SNXFlashLoanTool.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`swap`, lines=`L143`

#### 2. Function Source Code
```solidity
function swap(
        uint256 amount,
        address exchange,
        bytes memory data
    ) internal returns (uint256) {
        snx.safeApprove(exchange, amount);
        // Security check to prevent a reentrancy attack or an attacker pulling approved tokens
        require(
            exchange != address(LENDING_POOL) && exchange != address(synthetix) && exchange != address(snx),
            "SNXFlashLoanTool: Unauthorized address"
        );
        // SWC-107-Reentrancy: L143
        (bool success, ) = exchange.call(data);
        require(success, "SNXFlashLoanTool: Swap failed");
        return sUSD.balanceOf(address(this));
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['LENDING_POOL', 'sUSD', 'snx', 'synthetix']
- **External calls**: `snx.safeApprove(exchange, amount)` (method: safeApprove, receiver: snx), `exchange.call(data)` (method: call, receiver: exchange), `sUSD.balanceOf(address(this))` (method: balanceOf, receiver: sUSD)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['LENDING_POOL', 'sUSD', 'snx', 'synthetix']
- **External calls**: `snx.safeApprove(exchange, amount)` (SafeERC20 .safeApprove()), `exchange.call(data)` (low-level .call()), `sUSD.balanceOf(address(this))` (call on contract-typed state var 'sUSD' (type: IERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### Holdefi.repayBorrowInternal 

**Pre-classification**: 🔄 COMMIT_DRIFT
**Reason**: Function not found in current source file

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: repayBorrowInternal 
- **Line Range**: L1292-L1344
- **File**: `DAppSCAN-source/contracts/PeckShield-Holdefi/Holdefi-5a1e6e0d582120142e8a531f6806eba6665ef2f4/contracts/Holdefi.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`repayBorrowInternal `, lines=`L1292-L1344`

#### 2. Function Source Code
> ⚠️ **Function source not found** — possible commit drift or file restructuring

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['borrows', 'collaterals', 'ethAddress', 'marketAssets']
- **External calls**: `borrowData.balance.add(borrowData.interest)` (method: add, receiver: borrowData), `borrowData.interest.sub(transferAmount)` (method: sub, receiver: borrowData), `borrowData.balance.sub(remaining)` (method: sub, receiver: borrowData), `marketAssets[market].totalBorrow.sub(remaining)` (method: sub, receiver: marketAssets)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: []
- **External calls**: None
- **Cross-contract**: False
- **Hyperedge constructable**: False

**Consistency checks:**
- State vars match: ❌
- External calls match: ❌
- Cross-contract match: ❌

### MasterChef.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L196 - L208
- **File**: `DAppSCAN-source/contracts/PeckShield-KaoyaSwap/contracts-8273073f1d6914f372790399378f177573c52e37/masterchef.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L196 - L208`

#### 2. Function Source Code
```solidity
function deposit(uint256 _pid, uint256 _amount) public {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        updatePool(_pid);
        if (user.amount > 0) {
            uint256 pending = user.amount.mul(pool.accKaoyaPerShare).div(1e12).sub(user.rewardDebt);
            safeKaoyaTransfer(msg.sender, pending);
        }
        pool.lpToken.safeTransferFrom(address(msg.sender), address(this), _amount);
        user.amount = user.amount.add(_amount);
        user.rewardDebt = user.amount.mul(pool.accKaoyaPerShare).div(1e12);
        emit Deposit(msg.sender, _pid, _amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.amount.mul(pool.accKaoyaPerShare).div(1e12).sub(user.rewardDebt)` (method: sub, receiver: user), `user.amount.mul(pool.accKaoyaPerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(pool.accKaoyaPerShare)` (method: mul, receiver: user), `pool.lpToken.safeTransferFrom(address(msg.sender), address(this), _amount)` (method: safeTransferFrom, receiver: pool), `user.amount.add(_amount)` (method: add, receiver: user), `user.amount.mul(pool.accKaoyaPerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(pool.accKaoyaPerShare)` (method: mul, receiver: user)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.amount.mul(pool.accKaoyaPerShare).div(1e12).sub(user.rewardDebt)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accKaoyaPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accKaoyaPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `pool.lpToken.safeTransferFrom(address(msg.sender), address(this), _amount)` (SafeERC20 .safeTransferFrom()), `user.amount.add(_amount)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accKaoyaPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accKaoyaPerShare)` (call on contract-typed local var 'user' (type: UserInfo))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MasterChef.withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdraw
- **Line Range**: L219-L230
- **File**: `DAppSCAN-source/contracts/PeckShield-SushiSwap/sushiswap-180bc9b642bba79c1ee4a63f71a3a0d36e64aa63/contracts/MasterChef.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdraw`, lines=`L219-L230`

#### 2. Function Source Code
```solidity
function withdraw(uint256 _pid, uint256 _amount) public {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        require(user.amount >= _amount, "withdraw: not good");
        updatePool(_pid);
        uint256 pending = user.amount.mul(pool.accSushiPerShare).div(1e12).sub(user.rewardDebt);
        safeSushiTransfer(msg.sender, pending);
        user.amount = user.amount.sub(_amount);
        user.rewardDebt = user.amount.mul(pool.accSushiPerShare).div(1e12);
        pool.lpToken.safeTransfer(address(msg.sender), _amount);
        emit Withdraw(msg.sender, _pid, _amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.amount.mul(pool.accSushiPerShare).div(1e12).sub(user.rewardDebt)` (method: sub, receiver: user), `user.amount.mul(pool.accSushiPerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(pool.accSushiPerShare)` (method: mul, receiver: user), `user.amount.sub(_amount)` (method: sub, receiver: user), `user.amount.mul(pool.accSushiPerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(pool.accSushiPerShare)` (method: mul, receiver: user), `pool.lpToken.safeTransfer(address(msg.sender), _amount)` (method: safeTransfer, receiver: pool)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.amount.mul(pool.accSushiPerShare).div(1e12).sub(user.rewardDebt)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accSushiPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accSushiPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.sub(_amount)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accSushiPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accSushiPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `pool.lpToken.safeTransfer(address(msg.sender), _amount)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MTGYTokenLocker.withdrawLockedTokens

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdrawLockedTokens
- **Line Range**: L126
- **File**: `DAppSCAN-source/contracts/Solidity_Finance-OKLG - Smart Contract/contracts-e167d0d742d21bcc62d7a5b770a1f0ed1cf31eca/contracts/OKLGTokenLocker.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdrawLockedTokens`, lines=`L126`

#### 2. Function Source Code
```solidity
function withdrawLockedTokens(uint16 _idx, uint256 _amountOrTokenId)
    external
  {
    Locker storage _locker = lockers[_idx];
    require(
      _locker.amountWithdrawn < _locker.amountSupply,
      'All tokens have been withdrawn from this locker.'
    );

    bool _isWithdrawableUser = msg.sender == _locker.owner;
    if (!_isWithdrawableUser) {
      for (uint256 _i = 0; _i < _locker.withdrawable.length; _i++) {
        if (_locker.withdrawable[_i] == msg.sender) {
          _isWithdrawableUser = true;
          break;
        }
      }
    }
    require(
      _isWithdrawableUser,
      'Must be locker owner or a withdrawable wallet.'
    );

    // SWC-107-Reentrancy: L126
    _locker.amountWithdrawn += _locker.isNft ? 1 : _amountOrTokenId;

    if (_locker.isNft) {
      require(
        block.timestamp > _locker.end,
        'Must wait until locker expires to withdraw.'
      );
      IERC721 _token = IERC721(_locker.token);
      _token.transferFrom(address(this), msg.sender, _amountOrTokenId);
    } else {
      uint256 _maxAmount = maxWithdrawableTokens(_idx);
      require(
        _amountOrTokenId > 0 && _amountOrTokenId <= _maxAmount,
        'Make sure you enter a valid withdrawable amount and not more than has vested.'
      );
      IERC20 _token = IERC20(_locker.token);
      _token.transferFrom(address(this), msg.sender, _amountOrTokenId);
    }
    emit WithdrawTokens(_idx, msg.sender, _amountOrTokenId);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['lockers']
- **External calls**: `_token.transferFrom(address(this), msg.sender, _amountOrTokenId)` (method: transferFrom, receiver: _token), `_token.transferFrom(address(this), msg.sender, _amountOrTokenId)` (method: transferFrom, receiver: _token)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['lockers']
- **External calls**: `_token.transferFrom(address(this), msg.sender, _amountOrTokenId)` (call on contract-typed state var '_token' (type: IERC20)), `_token.transferFrom(address(this), msg.sender, _amountOrTokenId)` (call on contract-typed state var '_token' (type: IERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### Hypervisor.withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdraw
- **Line Range**: L175-216
- **File**: `DAppSCAN-source/contracts/consensys-Gamma/hypervisor-41fd4abf79864478523e87924d4e80d80df04879/contracts/Hypervisor.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdraw`, lines=`L175-216`

#### 2. Function Source Code
```solidity
function withdraw(
        uint256 shares,
        address to,
        address from
    ) external override returns (uint256 amount0, uint256 amount1) {
        require(shares > 0, "shares");
        require(to != address(0), "to");

        // Withdraw liquidity from Uniswap pool
        (uint256 base0, uint256 base1) = _burnLiquidity(
            baseLower,
            baseUpper,
            _liquidityForShares(baseLower, baseUpper, shares),
            to,
            false
        );
        (uint256 limit0, uint256 limit1) = _burnLiquidity(
            limitLower,
            limitUpper,
            _liquidityForShares(limitLower, limitUpper, shares),
            to,
            false
        );

        // Push tokens proportional to unused balances
        uint256 totalSupply = totalSupply();
        uint256 unusedAmount0 = token0.balanceOf(address(this)).mul(shares).div(totalSupply);
        uint256 unusedAmount1 = token1.balanceOf(address(this)).mul(shares).div(totalSupply);
        if (unusedAmount0 > 0) token0.safeTransfer(to, unusedAmount0);
        if (unusedAmount1 > 0) token1.safeTransfer(to, unusedAmount1);

        amount0 = base0.add(limit0).add(unusedAmount0);
        amount1 = base1.add(limit1).add(unusedAmount1);

        require(
            from == msg.sender || IUniversalVault(from).owner() == msg.sender,
            "Sender must own the tokens"
        );
        _burn(from, shares);

        emit Withdraw(from, to, shares, amount0, amount1);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['baseLower', 'baseUpper', 'limitLower', 'limitUpper', 'owner', 'token0', 'token1']
- **External calls**: `token0.balanceOf(address(this)).mul(shares).div(totalSupply)` (method: div, receiver: token0), `token0.balanceOf(address(this)).mul(shares)` (method: mul, receiver: token0), `token0.balanceOf(address(this))` (method: balanceOf, receiver: token0), `token1.balanceOf(address(this)).mul(shares).div(totalSupply)` (method: div, receiver: token1), `token1.balanceOf(address(this)).mul(shares)` (method: mul, receiver: token1), `token1.balanceOf(address(this))` (method: balanceOf, receiver: token1), `token0.safeTransfer(to, unusedAmount0)` (method: safeTransfer, receiver: token0), `token1.safeTransfer(to, unusedAmount1)` (method: safeTransfer, receiver: token1)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['baseLower', 'baseUpper', 'limitLower', 'limitUpper', 'owner', 'token0', 'token1']
- **External calls**: `token0.balanceOf(address(this)).mul(shares).div(totalSupply)` (call on contract-typed state var 'token0' (type: IERC20)), `token0.balanceOf(address(this)).mul(shares)` (call on contract-typed state var 'token0' (type: IERC20)), `token0.balanceOf(address(this))` (call on contract-typed state var 'token0' (type: IERC20)), `token1.balanceOf(address(this)).mul(shares).div(totalSupply)` (call on contract-typed state var 'token1' (type: IERC20)), `token1.balanceOf(address(this)).mul(shares)` (call on contract-typed state var 'token1' (type: IERC20)), `token1.balanceOf(address(this))` (call on contract-typed state var 'token1' (type: IERC20)), `token0.safeTransfer(to, unusedAmount0)` (SafeERC20 .safeTransfer()), `token1.safeTransfer(to, unusedAmount1)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### IdleCDO._deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: _deposit
- **Line Range**: L242-258
- **File**: `DAppSCAN-source/contracts/consensys-Idle_Finance/idle-tranches-d94ee7194e8cb17db13b16c338f3e780b62f5435/contracts/IdleCDO.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`_deposit`, lines=`L242-258`

#### 2. Function Source Code
```solidity
function _deposit(uint256 _amount, address _tranche) internal returns (uint256 _minted) {
    // check that we are not depositing more than the contract available limit
    _guarded(_amount);
    // set _lastCallerBlock hash
    _updateCallerBlock();
    // check if strategyPrice decreased
    _checkDefault();
    // interest accrued since last mint/redeem/harvest is splitted between AA and BB
    // according to trancheAPRSplitRatio. NAVs of AA and BB are so updated and tranche
    // prices adjusted accordingly
    _updatePrices();
    // NOTE: mint of shares should be done before transferring funds
    // mint tranches tokens according to the current prices
    _minted = _mintShares(_amount, msg.sender, _tranche);
    // get underlyings from sender
    IERC20Detailed(token).safeTransferFrom(msg.sender, address(this), _amount);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['token']
- **External calls**: `IERC20Detailed(token).safeTransferFrom(msg.sender, address(this), _amount)` (method: safeTransferFrom, receiver: IERC20Detailed)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['token']
- **External calls**: `IERC20Detailed(token).safeTransferFrom(msg.sender, address(this), _amount)` (SafeERC20 .safeTransferFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### Pod.depositTo

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: depositTo
- **Line Range**: L275-282
- **File**: `DAppSCAN-source/contracts/consensys-PoolTogether_Pods/pods-v3-contracts-879dc8b911fc506dd6bead1f36eade919ccfea57/contracts/Pod.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`depositTo`, lines=`L275-282`

#### 2. Function Source Code
```solidity
function depositTo(address to, uint256 tokenAmount)
        external
        override
        returns (uint256)
    {
        require(tokenAmount > 0, "Pod:invalid-amount");

        // Allocate Shares from Deposit To Amount
        // SWC-107-Reentrancy: L275-282
        uint256 shares = _deposit(to, tokenAmount);

        // Transfer Token Transfer Message Sender
        // SWC-104-Unchecked Call Return Value: L279
        IERC20Upgradeable(token).transferFrom(
            msg.sender,
            address(this),
            tokenAmount
        );

        // Emit Deposited
        emit Deposited(to, tokenAmount, shares);

        // Return Shares Minted
        return shares;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['token']
- **External calls**: `IERC20Upgradeable(token).transferFrom(
            msg.sender,
            address(this),
            tokenAmount
      ` (method: transferFrom, receiver: IERC20Upgradeable)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['token']
- **External calls**: `IERC20Upgradeable(token).transferFrom(
            msg.sender,
            address(this),
            tokenAmount
      ` (inline cast call IERC20Upgradeable(...).transferFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### TokenDrop.claim

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: claim
- **Line Range**: L141-155
- **File**: `DAppSCAN-source/contracts/consensys-PoolTogether_Pods/pods-v3-contracts-879dc8b911fc506dd6bead1f36eade919ccfea57/contracts/TokenDrop.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`claim`, lines=`L141-155`

#### 2. Function Source Code
```solidity
function claim(address user) external returns (uint256) {
        drop();
        _captureNewTokensForUser(user);
        uint256 balance = userStates[user].balance;
        userStates[user].balance = 0;
        totalUnclaimed = uint256(totalUnclaimed).sub(balance).toUint112();

        // Transfer asset/reward token to user
        asset.transfer(user, balance);

        // Emit Claimed
        emit Claimed(user, balance);

        return balance;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['asset', 'totalUnclaimed', 'userStates']
- **External calls**: `asset.transfer(user, balance)` (method: transfer, receiver: asset)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['asset', 'totalUnclaimed', 'userStates']
- **External calls**: `asset.transfer(user, balance)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### YearnV2YieldSource.supplyTokenTo

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: supplyTokenTo
- **Line Range**: L118-L129
- **File**: `DAppSCAN-source/contracts/consensys-PoolTogether_Sushi_and_Yearn_V2_Yield_Sources/pooltogether-yearnv2-yield-source-a34857f1555908a6263d2ebd189f0cb40e1858da/contracts/yield-source/YearnV2YieldSource.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`supplyTokenTo`, lines=`L118-L129`

#### 2. Function Source Code
```solidity
function supplyTokenTo(uint256 _amount, address to) override external {
        uint256 shares = _tokenToShares(_amount);

        _mint(to, shares);

        // NOTE: we have to deposit after calculating shares to mint
        token.safeTransferFrom(msg.sender, address(this), _amount);

        _depositInVault();

        emit SuppliedTokenTo(msg.sender, shares, _amount, to);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['token']
- **External calls**: `token.safeTransferFrom(msg.sender, address(this), _amount)` (method: safeTransferFrom, receiver: token)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['token']
- **External calls**: `token.safeTransferFrom(msg.sender, address(this), _amount)` (SafeERC20 .safeTransferFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

---
## TRAIN Intra-Contract (57 items)

### ve.withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdraw
- **Line Range**: L1097-1104
- **File**: `DAppSCAN-source/contracts/BlockSec-blocksec_multichain_vemult_v1.0_signed/veMULTI-bac804399d1ea280e5bd8cdc9488b6fa6a0a7fcc/contracts/ve.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdraw`, lines=`L1097-1104`

#### 2. Function Source Code
```solidity
function withdraw(uint _tokenId) external nonreentrant {
        assert(_isApprovedOrOwner(msg.sender, _tokenId));
        require(attachments[_tokenId] == 0 && !voted[_tokenId], "attached");

        LockedBalance memory _locked = locked[_tokenId];
        require(block.timestamp >= _locked.end, "The lock didn't expire");
        uint value = uint(int256(_locked.amount));

        locked[_tokenId] = LockedBalance(0,0);
        uint supply_before = supply;
        supply = supply_before - value;

        // old_locked can have either expired <= timestamp or zero end
        // _locked has only 0 end
        // Both can have >= 0 amount
        _checkpoint(_tokenId, _locked, LockedBalance(0,0));
        // SWC-107-Reentrancy: L1097-1104
        assert(IERC20(token).transfer(msg.sender, value));

        // Burn the NFT
        _burn(_tokenId);

        emit Withdraw(msg.sender, _tokenId, value, block.timestamp);
        emit Supply(supply_before, supply_before - value);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['attachments', 'locked', 'supply', 'token', 'voted']
- **External calls**: `IERC20(token).transfer(msg.sender, value)` (method: transfer, receiver: IERC20)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['attachments', 'locked', 'supply', 'token', 'voted']
- **External calls**: `IERC20(token).transfer(msg.sender, value)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### wHakka.stake

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: stake
- **Line Range**: L556 - L573
- **File**: `DAppSCAN-source/contracts/Coinbae-Hakka_Finance_wHakka/code/wHakka.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`stake`, lines=`L556 - L573`

#### 2. Function Source Code
```solidity
function stake(address to, uint256 amount, uint256 time) public returns (uint256 wAmount) {
        vault storage v = vaults[to][vaultCount[to]];
        wAmount = getStakingRate(time).mul(amount).div(1e18);
        require(wAmount > 0, "invalid lockup");

        v.hakkaAmount = amount;
        v.wAmount = wAmount;
        v.unlockTime = block.timestamp.add(time);
        
        stakedHakka[to] = stakedHakka[to].add(amount);
        votingPower[to] = votingPower[to].add(wAmount);
        vaultCount[to]++;

        _mint(to, wAmount);
        Hakka.safeTransferFrom(msg.sender, address(this), amount);

        emit Stake(to, msg.sender, amount, wAmount, time);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['Hakka', 'stakedHakka', 'vaultCount', 'vaults', 'votingPower']
- **External calls**: `Hakka.safeTransferFrom(msg.sender, address(this), amount)` (method: safeTransferFrom, receiver: Hakka)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['Hakka', 'stakedHakka', 'vaultCount', 'vaults', 'votingPower']
- **External calls**: `Hakka.safeTransferFrom(msg.sender, address(this), amount)` (SafeERC20 .safeTransferFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### wHakka.unstake

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: unstake
- **Line Range**: L576 - L592
- **File**: `DAppSCAN-source/contracts/Coinbae-Hakka_Finance_wHakka/code/wHakka.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`unstake`, lines=`L576 - L592`

#### 2. Function Source Code
```solidity
function unstake(address to, uint256 index, uint256 wAmount) public returns (uint256 amount) {
        vault storage v = vaults[msg.sender][index];
        // SWC-116-Block values as a proxy for time: L580
        require(block.timestamp >= v.unlockTime, "locked");
        require(wAmount <= v.wAmount, "exceed locked amount");
        amount = wAmount.mul(v.hakkaAmount).div(v.wAmount);

        v.hakkaAmount = v.hakkaAmount.sub(amount);
        v.wAmount = v.wAmount.sub(wAmount);

        stakedHakka[msg.sender] = stakedHakka[msg.sender].sub(amount);
        votingPower[msg.sender] = votingPower[msg.sender].sub(wAmount);

        _burn(msg.sender, wAmount);
        Hakka.safeTransfer(to, amount);
        
        emit Unstake(msg.sender, to, amount, wAmount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['Hakka', 'stakedHakka', 'vaults', 'votingPower']
- **External calls**: `Hakka.safeTransfer(to, amount)` (method: safeTransfer, receiver: Hakka)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['Hakka', 'stakedHakka', 'vaults', 'votingPower']
- **External calls**: `Hakka.safeTransfer(to, amount)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MasterChef.add

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: add
- **Line Range**: L105 - L127
- **File**: `DAppSCAN-source/contracts/Coinbae-Pud.Fi Masterchef_Audit/MasterChef0x15Bee180BB39eE5c0166E63313C33984376930Db/contracts/MasterChef.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`add`, lines=`L105 - L127`

#### 2. Function Source Code
```solidity
function add(
        uint256 _allocPoint,
        IERC20 _lpToken,
        bool _withUpdate,
        address _strategy
    ) public onlyOwner {
        if (_withUpdate) {
            massUpdatePools();
        }
        uint256 lastRewardBlock =
            block.number > startBlock ? block.number : startBlock;
        totalAllocPoint = totalAllocPoint.add(_allocPoint);
        poolInfo.push(
            PoolInfo({
                lpToken: _lpToken,
                allocPoint: _allocPoint,
                lastRewardBlock: lastRewardBlock,
                accPudPerShare: 0,
                strategy: _strategy,
                totalShares: 0
            })
        );
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'startBlock', 'totalAllocPoint']
- **External calls**: `poolInfo.push(
            PoolInfo({
                lpToken: _lpToken,
                allocPoint: _allocPoint,
      ` (method: push, receiver: poolInfo)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'startBlock', 'totalAllocPoint']
- **External calls**: `poolInfo.push(
            PoolInfo({
                lpToken: _lpToken,
                allocPoint: _allocPoint,
      ` (call on contract-typed state var 'poolInfo' (type: PoolInfo[]))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MasterChef.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L227 - L266
- **File**: `DAppSCAN-source/contracts/Coinbae-Pud.Fi Masterchef_Audit/MasterChef0x15Bee180BB39eE5c0166E63313C33984376930Db/contracts/MasterChef.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L227 - L266`

#### 2. Function Source Code
```solidity
function deposit(uint256 _pid, uint256 _amount) public {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];

        updatePool(_pid);
        if (user.shares > 0) {
            uint256 pending =
                user.shares.mul(pool.accPudPerShare).div(1e12).sub(
                    user.rewardDebt
                );
            safePudTransfer(msg.sender, pending);
        }

        //
        uint256 _pool = balance(_pid); //get _pid lptoken balance
        if (_amount > 0) {
            uint256 _before = pool.lpToken.balanceOf(pool.strategy);
            // SWC-107-Reentrancy: L247 - L251
            pool.lpToken.safeTransferFrom(
                address(msg.sender),
                pool.strategy,
                _amount
            );

            uint256 _after = pool.lpToken.balanceOf(pool.strategy);
            _amount = _after.sub(_before); // Additional check for deflationary tokens
        }
        uint256 shares = 0;
        if (pool.totalShares == 0) {
            shares = _amount;
        } else {
            shares = (_amount.mul(pool.totalShares)).div(_pool);
        }

        user.shares = user.shares.add(shares); //add shares instead of amount
        user.rewardDebt = user.shares.mul(pool.accPudPerShare).div(1e12);
        pool.totalShares = pool.totalShares.add(shares); //add shares in pool

        emit Deposit(msg.sender, _pid, _amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.shares.mul(pool.accPudPerShare).div(1e12).sub(
                    user.rewardDebt
                )` (method: sub, receiver: user), `user.shares.mul(pool.accPudPerShare).div(1e12)` (method: div, receiver: user), `user.shares.mul(pool.accPudPerShare)` (method: mul, receiver: user), `pool.lpToken.balanceOf(pool.strategy)` (method: balanceOf, receiver: pool), `pool.lpToken.safeTransferFrom(
                address(msg.sender),
                pool.strategy,
                _amou` (method: safeTransferFrom, receiver: pool), `pool.lpToken.balanceOf(pool.strategy)` (method: balanceOf, receiver: pool), `user.shares.add(shares)` (method: add, receiver: user), `user.shares.mul(pool.accPudPerShare).div(1e12)` (method: div, receiver: user), `user.shares.mul(pool.accPudPerShare)` (method: mul, receiver: user), `pool.totalShares.add(shares)` (method: add, receiver: pool)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.shares.mul(pool.accPudPerShare).div(1e12).sub(
                    user.rewardDebt
                )` (call on contract-typed local var 'user' (type: UserInfo)), `user.shares.mul(pool.accPudPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.shares.mul(pool.accPudPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `pool.lpToken.balanceOf(pool.strategy)` (call on contract-typed local var 'pool' (type: PoolInfo)), `pool.lpToken.safeTransferFrom(
                address(msg.sender),
                pool.strategy,
                _amou` (SafeERC20 .safeTransferFrom()), `pool.lpToken.balanceOf(pool.strategy)` (call on contract-typed local var 'pool' (type: PoolInfo)), `user.shares.add(shares)` (call on contract-typed local var 'user' (type: UserInfo)), `user.shares.mul(pool.accPudPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.shares.mul(pool.accPudPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `pool.totalShares.add(shares)` (call on contract-typed local var 'pool' (type: PoolInfo))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### WOOPStake.processReward

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: processReward
- **Line Range**: L743 - L769
- **File**: `DAppSCAN-source/contracts/Coinfabrik-Woonkly Security Audit (DEX STAKE)/STAKESmartContractPreRelease-main/woonklyPOS.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`processReward`, lines=`L743 - L769`

#### 2. Function Source Code
```solidity
function processReward(address sc, uint256 amount)
        public
        nonReentrant
        Active
        hasApprovedTokens(sc, _msgSender(), amount)
        ProviderHasToken(sc, amount)
        returns (bool)
    {
        if (!ERC20Exist(sc)) {
            newERC20(sc);
        }

        processRewardInfo memory slot;

        IERC20 _token = IERC20(sc);
        _processReward_1(_token, _msgSender(), amount);

        slot.dealed = _processReward_2(sc, amount);

        uint256 leftover = amount.sub(slot.dealed);
        if (leftover > 0) {
            require(_token.transfer(_remainder, leftover), "WO:trf");
            emit NewLeftover(sc, _remainder, leftover);
        }

        return true;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['_remainder']
- **External calls**: `_token.transfer(_remainder, leftover)` (method: transfer, receiver: _token)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['_remainder']
- **External calls**: `_token.transfer(_remainder, leftover)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### CDEXStakingPool.getReward

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: getReward
- **Line Range**: L424 - L456
- **File**: `DAppSCAN-source/contracts/Hacken-Codex on Althash/Codex-Rewards-Platform-d364d0ef9258dd468f8202a352c58724d6b65638/contracts/CDEX_rewards.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`getReward`, lines=`L424 - L456`

#### 2. Function Source Code
```solidity
function getReward() 
        public 
        nonReentrant 
        updateReward(msg.sender) 
    {
        uint256 reward = rewards[msg.sender];
        uint256 loyaltyBonus;
        /// Sanity checks
        if (reward > 0 && depositedRewardTokens >= reward) {
            /// The withdraw is always for the full accrued reward amount
            rewards[msg.sender] = 0;
            /// Decrements the deposited reward tokens balance
            depositedRewardTokens = depositedRewardTokens.sub(reward);
            /// Defines the bonus amount based on the sender's reward tier
            if (_balances[msg.sender] >= loyaltyTier1) {
                loyaltyBonus = reward.mul(loyaltyTier1Bonus).div(10000);
            } else if (_balances[msg.sender] >= loyaltyTier2) {
                loyaltyBonus = reward.mul(loyaltyTier2Bonus).div(10000);
            } else if (_balances[msg.sender] >= loyaltyTier3) {
                loyaltyBonus = reward.mul(loyaltyTier3Bonus).div(10000);
            }
            /// Decrements the deposited loyalty bonus balance
            depositedLoyaltyBonus = depositedLoyaltyBonus.sub(loyaltyBonus);
            /// Transfers the total accrued rewards plus the calculated bonus amount
            CDEXToken.transfer(msg.sender, reward.add(loyaltyBonus));
            /// Emits the event
            emit RewardPaid(msg.sender, reward);
            /// If any loytaly bonus was paid, emits the event
            if(loyaltyBonus > 0) {
                emit LoyaltyBonusPaid(msg.sender, loyaltyBonus);
            }
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['CDEXToken', '_balances', 'depositedLoyaltyBonus', 'depositedRewardTokens', 'loyaltyTier1', 'loyaltyTier1Bonus', 'loyaltyTier2', 'loyaltyTier2Bonus', 'loyaltyTier3', 'loyaltyTier3Bonus', 'rewards']
- **External calls**: `CDEXToken.transfer(msg.sender, reward.add(loyaltyBonus))` (method: transfer, receiver: CDEXToken)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['CDEXToken', '_balances', 'depositedLoyaltyBonus', 'depositedRewardTokens', 'loyaltyTier1', 'loyaltyTier1Bonus', 'loyaltyTier2', 'loyaltyTier2Bonus', 'loyaltyTier3', 'loyaltyTier3Bonus', 'rewards']
- **External calls**: `CDEXToken.transfer(msg.sender, reward.add(loyaltyBonus))` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### IDO.claim

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: claim
- **Line Range**: L86 - L110
- **File**: `DAppSCAN-source/contracts/Hacken-Ground Zero/code/IDO.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`claim`, lines=`L86 - L110`

#### 2. Function Source Code
```solidity
function claim() external {
        require(block.timestamp > idoFinish, "The IDO is not finished yet");
        require(pool[msg.sender].start != 0, "You're not participating in IDO");
        require(
            (block.timestamp - pool[msg.sender].claimedLastTime) > cooldownToClaim,
            "You are not allowed to claime more at this time"
        );
        require(!pool[msg.sender].hasClaimed, "You already claimed");

        if (
            (pool[msg.sender].claimedAmount < pool[msg.sender].amountToClaim) &&
            ((pool[msg.sender].amountToClaim - pool[msg.sender].claimedAmount) >= allowedAmountToClaim)
        ) {
            // SWC-104-Unchecked Call Return Value: L97
            GZT.transfer(msg.sender, allowedAmountToClaim);
            pool[msg.sender].claimedLastTime = block.timestamp;
        } else if (
            (pool[msg.sender].claimedAmount < pool[msg.sender].amountToClaim) &&
            ((pool[msg.sender].amountToClaim - pool[msg.sender].claimedAmount) < allowedAmountToClaim)
        ) {
            GZT.transfer(msg.sender, (pool[msg.sender].amountToClaim - pool[msg.sender].claimedAmount));
            pool[msg.sender].claimedLastTime = block.timestamp;
            pool[msg.sender].hasClaimed = true;
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['GZT', 'allowedAmountToClaim', 'cooldownToClaim', 'idoFinish', 'pool']
- **External calls**: `GZT.transfer(msg.sender, allowedAmountToClaim)` (method: transfer, receiver: GZT), `GZT.transfer(msg.sender, (pool[msg.sender].amountToClaim - pool[msg.sender].claimedAmount))` (method: transfer, receiver: GZT)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['GZT', 'allowedAmountToClaim', 'cooldownToClaim', 'idoFinish', 'pool']
- **External calls**: `GZT.transfer(msg.sender, allowedAmountToClaim)` (low-level .transfer()), `GZT.transfer(msg.sender, (pool[msg.sender].amountToClaim - pool[msg.sender].claimedAmount))` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### IDO.claimTheInvestments

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: claimTheInvestments
- **Line Range**: L153
- **File**: `DAppSCAN-source/contracts/Hacken-Ground Zero/code/IDO.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`claimTheInvestments`, lines=`L153`

#### 2. Function Source Code
```solidity
function claimTheInvestments(IERC20 token, uint256 amount) external onlyOwner {
        require(block.timestamp > idoFinish, "The IDO is not finished yet");

    // SWC-104-Unchecked Call Return Value: L153
        token.transfer(msg.sender, amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['idoFinish']
- **External calls**: `token.transfer(msg.sender, amount)` (method: transfer, receiver: token)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['idoFinish']
- **External calls**: `token.transfer(msg.sender, amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### HyksosCyberkongz.payErc20

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: payErc20
- **Line Range**: L35-37
- **File**: `DAppSCAN-source/contracts/Hacken-Hyksos/hyksos-contracts-audit/HyksosCyberkongz.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`payErc20`, lines=`L35-37`

#### 2. Function Source Code
```solidity
function payErc20(address _receiver, uint256 _amount) internal override {
        require(erc20.transfer(_receiver, _amount));
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['erc20']
- **External calls**: `erc20.transfer(_receiver, _amount)` (method: transfer, receiver: erc20)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['erc20']
- **External calls**: `erc20.transfer(_receiver, _amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### HyksosCyberkongz.withdrawErc20

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: withdrawErc20
- **Line Range**: L48-54
- **File**: `DAppSCAN-source/contracts/Hacken-Hyksos/hyksos-contracts-audit/HyksosCyberkongz.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`withdrawErc20`, lines=`L48-54`

#### 2. Function Source Code
```solidity
function withdrawErc20(uint256 _amount) external override {
        require(_amount <= erc20BalanceMap[msg.sender], "Withdrawal amount too big.");
        totalErc20Balance -= _amount;
        erc20BalanceMap[msg.sender] -= _amount;
        require(erc20.transfer(msg.sender, _amount));
        emit Erc20Withdrawal(msg.sender, _amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['erc20', 'erc20BalanceMap', 'totalErc20Balance']
- **External calls**: `erc20.transfer(msg.sender, _amount)` (method: transfer, receiver: erc20)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['erc20', 'erc20BalanceMap', 'totalErc20Balance']
- **External calls**: `erc20.transfer(msg.sender, _amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### Staking.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: deposit
- **Line Range**: L80
- **File**: `DAppSCAN-source/contracts/Hacken-The Next War/Contracts-334fe81ea7282ac4f768de077c37a7932c0302de/contracts/Staking.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`deposit`, lines=`L80`

#### 2. Function Source Code
```solidity
function deposit(uint256 amount) external {
        // Refresh rewards
        updatePool();

        UserInfo storage user = userInfo[msg.sender];
        UserStakeInfo storage stakeInfo = userStakeInfo[user.stakeRecords][msg.sender];
        require(tngToken.balanceOf(msg.sender) >= amount, "Insufficient tokens");

        // set user info
        user.totalAmount = user.totalAmount.add(amount);
        user.rewardDebt = user.rewardDebt.add(amount.mul(accTngPerShare) / ACC_TNG_PRECISION);
        user.stakeRecords = user.stakeRecords.add(1);

        // set staking info
        stakeInfo.amount = amount;
        stakeInfo.stakedTime = block.timestamp;
        stakeInfo.unlockTime = block.timestamp + lockTime;

        // Tracking
        lpTokenDeposited = lpTokenDeposited.add(amount);

        // Transfer token into the contract
// SWC-104-Unchecked Call Return Value: L80
        lpToken.transferFrom(msg.sender, address(this), amount);
        
        emit Deposit(msg.sender, amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['ACC_TNG_PRECISION', 'accTngPerShare', 'lockTime', 'lpToken', 'lpTokenDeposited', 'tngToken', 'userInfo', 'userStakeInfo']
- **External calls**: `tngToken.balanceOf(msg.sender)` (method: balanceOf, receiver: tngToken), `user.totalAmount.add(amount)` (method: add, receiver: user), `user.rewardDebt.add(amount.mul(accTngPerShare) / ACC_TNG_PRECISION)` (method: add, receiver: user), `user.stakeRecords.add(1)` (method: add, receiver: user), `lpToken.transferFrom(msg.sender, address(this), amount)` (method: transferFrom, receiver: lpToken)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['ACC_TNG_PRECISION', 'accTngPerShare', 'lockTime', 'lpToken', 'lpTokenDeposited', 'tngToken', 'userInfo', 'userStakeInfo']
- **External calls**: `tngToken.balanceOf(msg.sender)` (call on contract-typed state var 'tngToken' (type: IERC20)), `user.totalAmount.add(amount)` (call on contract-typed local var 'user' (type: UserInfo)), `user.rewardDebt.add(amount.mul(accTngPerShare) / ACC_TNG_PRECISION)` (call on contract-typed local var 'user' (type: UserInfo)), `user.stakeRecords.add(1)` (call on contract-typed local var 'user' (type: UserInfo)), `lpToken.transferFrom(msg.sender, address(this), amount)` (call on contract-typed state var 'lpToken' (type: IERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### Staking.payTngReward

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: payTngReward
- **Line Range**: L177
- **File**: `DAppSCAN-source/contracts/Hacken-The Next War/Contracts-334fe81ea7282ac4f768de077c37a7932c0302de/contracts/Staking.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`payTngReward`, lines=`L177`

#### 2. Function Source Code
```solidity
function payTngReward(uint256 _pendingTng, address _to) internal {
        // SWC-104-Unchecked Call Return Value: L177
        tngToken.transfer(_to, _pendingTng);
        pendingTngRewards = pendingTngRewards.sub(_pendingTng);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['pendingTngRewards', 'tngToken']
- **External calls**: `tngToken.transfer(_to, _pendingTng)` (method: transfer, receiver: tngToken)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['pendingTngRewards', 'tngToken']
- **External calls**: `tngToken.transfer(_to, _pendingTng)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### StakingPool.withdrawStaking

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: withdrawStaking
- **Line Range**: L262
- **File**: `DAppSCAN-source/contracts/Hacken-TrustSwap-V1/code/StakingPool.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`withdrawStaking`, lines=`L262`

#### 2. Function Source Code
(61 lines, showing first 30 + last 15)
```solidity
function withdrawStaking(uint256 amount) external {
        require(amount > 0, "Amount can not be zero");
        require(userTotalStaking[msg.sender].totalStaking >= amount, "You are trying to withdaw more than your stake");
        
        // 1. User Accounting
        Stake[] storage accountStakes = userStaking[msg.sender];
        
        // Redeem from most recent stake and go backwards in time.
        uint256 sharesLeftToBurn = amount;
        uint256 rewardAmount = 0;
        while (sharesLeftToBurn > 0) {
            Stake storage lastStake = accountStakes[accountStakes.length - 1];
            uint256 stakeTimeSec;
            //check if current time is more than pool ending time
            if (now > poolEndTime) {
                stakeTimeSec = poolEndTime.sub(lastStake.stakingTime);
                if(lastStake.lastWithdrawTime != 0){
                    stakeTimeSec = poolEndTime.sub(lastStake.lastWithdrawTime);
                }
            } else {
                stakeTimeSec = now.sub(lastStake.stakingTime);
                if(lastStake.lastWithdrawTime != 0){
                    stakeTimeSec = now.sub(lastStake.lastWithdrawTime);
                }
            }
            
            if (lastStake.amount <= sharesLeftToBurn) {
                // fully redeem a past stake
                rewardAmount = computeNewReward(rewardAmount, lastStake.amount, stakeTimeSec);
                sharesLeftToBurn = sharesLeftToBurn.sub(lastStake.amount);
    // ... truncated ...
        //update user rewards info
        userRewardInfo[msg.sender].totalWithdrawn = userRewardInfo[msg.sender].totalWithdrawn.add(rewardAmount);
        userRewardInfo[msg.sender].lastWithdrawTime = now;
        
        //update total rewards withdrawn
        rewardsWithdrawn = rewardsWithdrawn.add(rewardAmount);
        
        //transfer rewards and tokens
        // SWC-104-Unchecked Call Return Value: L262
        rewardToken.transfer(msg.sender, rewardAmount);
        tswap.transfer(msg.sender, amount);
        
        emit RewardWithdrawal(msg.sender, rewardAmount);
        emit StakingWithdrawal(msg.sender, amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolEndTime', 'rewardToken', 'rewardsWithdrawn', 'totalStaked', 'tswap', 'userRewardInfo', 'userStaking', 'userTotalStaking']
- **External calls**: `lastStake.amount.sub(sharesLeftToBurn)` (method: sub, receiver: lastStake), `userTotalStaking[msg.sender].totalStaking.sub(amount)` (method: sub, receiver: userTotalStaking), `userRewardInfo[msg.sender].totalWithdrawn.add(rewardAmount)` (method: add, receiver: userRewardInfo), `rewardToken.transfer(msg.sender, rewardAmount)` (method: transfer, receiver: rewardToken), `tswap.transfer(msg.sender, amount)` (method: transfer, receiver: tswap)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolEndTime', 'rewardToken', 'rewardsWithdrawn', 'totalStaked', 'tswap', 'userRewardInfo', 'userStaking', 'userTotalStaking']
- **External calls**: `lastStake.amount.sub(sharesLeftToBurn)` (call on contract-typed local var 'lastStake' (type: Stake)), `userTotalStaking[msg.sender].totalStaking.sub(amount)` (call on contract-typed state var 'userTotalStaking' (type: mapping (address => UserTotals))), `userRewardInfo[msg.sender].totalWithdrawn.add(rewardAmount)` (call on contract-typed state var 'userRewardInfo' (type: mapping(address => Ris3Rewards))), `rewardToken.transfer(msg.sender, rewardAmount)` (low-level .transfer()), `tswap.transfer(msg.sender, amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MasterChef.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L262
- **File**: `DAppSCAN-source/contracts/ImmuneBytes-Bird Money(MasterChef)-Audit Report/bird-farm-contracts-dfd2502b73c8f54c9081682c3eb070fcd3c00629/contracts/MasterChef.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L262`

#### 2. Function Source Code
```solidity
function deposit(uint256 _pid, uint256 _amount) public {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        updatePool(_pid);
        if (user.amount > 0) {
            uint256 pending =
                user.amount.mul(pool.accRewardTokenPerShare).div(1e12).sub(
                    user.rewardDebt
                );
            if (now > user.unstakeTime)
                safeRewardTokenTransfer(msg.sender, pending);
        }
        pool.lpToken.safeTransferFrom(
            address(msg.sender),
            address(this),
            _amount
        );
        user.unstakeTime = now + unstakeFrozenTime;
        user.amount = user.amount.add(_amount);
        user.rewardDebt = user.amount.mul(pool.accRewardTokenPerShare).div(
            1e12
        );
        emit Deposit(msg.sender, _pid, _amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'unstakeFrozenTime', 'userInfo']
- **External calls**: `user.amount.mul(pool.accRewardTokenPerShare).div(1e12).sub(
                    user.rewardDebt
                )` (method: sub, receiver: user), `user.amount.mul(pool.accRewardTokenPerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(pool.accRewardTokenPerShare)` (method: mul, receiver: user), `pool.lpToken.safeTransferFrom(
            address(msg.sender),
            address(this),
            _amount
        )` (method: safeTransferFrom, receiver: pool), `user.amount.add(_amount)` (method: add, receiver: user), `user.amount.mul(pool.accRewardTokenPerShare).div(
            1e12
        )` (method: div, receiver: user), `user.amount.mul(pool.accRewardTokenPerShare)` (method: mul, receiver: user)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'unstakeFrozenTime', 'userInfo']
- **External calls**: `user.amount.mul(pool.accRewardTokenPerShare).div(1e12).sub(
                    user.rewardDebt
                )` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accRewardTokenPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accRewardTokenPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `pool.lpToken.safeTransferFrom(
            address(msg.sender),
            address(this),
            _amount
        )` (SafeERC20 .safeTransferFrom()), `user.amount.add(_amount)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accRewardTokenPerShare).div(
            1e12
        )` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accRewardTokenPerShare)` (call on contract-typed local var 'user' (type: UserInfo))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MasterChef.emergencyWithdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: emergencyWithdraw
- **Line Range**: L311
- **File**: `DAppSCAN-source/contracts/ImmuneBytes-Bird Money(MasterChef)-Audit Report/bird-farm-contracts-dfd2502b73c8f54c9081682c3eb070fcd3c00629/contracts/MasterChef.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`emergencyWithdraw`, lines=`L311`

#### 2. Function Source Code
```solidity
function emergencyWithdraw(uint256 _pid) public {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        pool.lpToken.safeTransfer(address(msg.sender), user.amount);
        emit EmergencyWithdraw(msg.sender, _pid, user.amount);
        user.amount = 0;
        user.rewardDebt = 0;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `pool.lpToken.safeTransfer(address(msg.sender), user.amount)` (method: safeTransfer, receiver: pool)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `pool.lpToken.safeTransfer(address(msg.sender), user.amount)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MasterChef.withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdraw
- **Line Range**: L287-306
- **File**: `DAppSCAN-source/contracts/ImmuneBytes-Bird Money-Final Audit Report/bird-farm-contracts-dfd2502b73c8f54c9081682c3eb070fcd3c00629/contracts/MasterChef.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdraw`, lines=`L287-306`

#### 2. Function Source Code
```solidity
function withdraw(uint256 _pid, uint256 _amount) public {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        require(user.amount >= _amount, "withdraw: not good");

        if (now > user.unstakeTime) {
            updatePool(_pid);
            uint256 pending =
                user.amount.mul(pool.accRewardTokenPerShare).div(1e12).sub(
                    user.rewardDebt
                );
            safeRewardTokenTransfer(msg.sender, pending);
            user.amount = user.amount.sub(_amount);
            user.rewardDebt = user.amount.mul(pool.accRewardTokenPerShare).div(
                1e12
            );
            pool.lpToken.safeTransfer(address(msg.sender), _amount);
            emit Withdraw(msg.sender, _pid, _amount);
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.amount.mul(pool.accRewardTokenPerShare).div(1e12).sub(
                    user.rewardDebt
                )` (method: sub, receiver: user), `user.amount.mul(pool.accRewardTokenPerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(pool.accRewardTokenPerShare)` (method: mul, receiver: user), `user.amount.sub(_amount)` (method: sub, receiver: user), `user.amount.mul(pool.accRewardTokenPerShare).div(
                1e12
            )` (method: div, receiver: user), `user.amount.mul(pool.accRewardTokenPerShare)` (method: mul, receiver: user), `pool.lpToken.safeTransfer(address(msg.sender), _amount)` (method: safeTransfer, receiver: pool)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.amount.mul(pool.accRewardTokenPerShare).div(1e12).sub(
                    user.rewardDebt
                )` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accRewardTokenPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accRewardTokenPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.sub(_amount)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accRewardTokenPerShare).div(
                1e12
            )` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accRewardTokenPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `pool.lpToken.safeTransfer(address(msg.sender), _amount)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### SportsIconPrivateVesting.claim

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: claim
- **Line Range**: L60
- **File**: `DAppSCAN-source/contracts/ImmuneBytes-SportsIcon-Audit Report/SportsIcon-Vesting-8a26ed5c3a52b7a4d1b22a38b40dd80783ecc6a3/SportsIconPrivateVesting.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`claim`, lines=`L60`

#### 2. Function Source Code
```solidity
function claim() external override returns (uint256) {
        uint256 tokens = freeTokens(msg.sender);
        claimedOf[msg.sender] = claimedOf[msg.sender].add(tokens);
//SWC-104-Unchecked Call Return Value:L60
        token.transfer(msg.sender, tokens);

        emit LogTokensClaimed(msg.sender, tokens);

        return tokens;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['claimedOf', 'token']
- **External calls**: `token.transfer(msg.sender, tokens)` (method: transfer, receiver: token)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['claimedOf', 'token']
- **External calls**: `token.transfer(msg.sender, tokens)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### StrategyCommonChefLP._harvest

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: _harvest
- **Line Range**: L137-149
- **File**: `DAppSCAN-source/contracts/Inspex-AutoCompoundVault/mondayclub-9ec29e0bb41a6bbef5484976502c924f4557ca02/StrategyCommonChefLP.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`_harvest`, lines=`L137-149`

#### 2. Function Source Code
```solidity
function _harvest(address callFeeRecipient) internal whenNotPaused {
        IMasterChef(chef).deposit(poolId, 0);
        uint256 outputBal = IERC20(output).balanceOf(address(this));
        if (outputBal > 0) {
            chargeFees(callFeeRecipient);
            addLiquidity();
            uint256 wantHarvested = balanceOfWant();
            deposit();

            lastHarvest = block.timestamp;
            emit StratHarvest(msg.sender, wantHarvested, balanceOf());
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['chef', 'lastHarvest', 'output', 'poolId']
- **External calls**: `IMasterChef(chef).deposit(poolId, 0)` (method: deposit, receiver: IMasterChef), `IERC20(output).balanceOf(address(this))` (method: balanceOf, receiver: IERC20)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['chef', 'lastHarvest', 'output', 'poolId']
- **External calls**: `IMasterChef(chef).deposit(poolId, 0)` (inline cast call IMasterChef(...).deposit()), `IERC20(output).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### StrategyCommonChefLP.addLiquidity

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: addLiquidity
- **Line Range**: L169-183
- **File**: `DAppSCAN-source/contracts/Inspex-AutoCompoundVault/mondayclub-9ec29e0bb41a6bbef5484976502c924f4557ca02/StrategyCommonChefLP.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`addLiquidity`, lines=`L169-183`

#### 2. Function Source Code
```solidity
function addLiquidity() internal {
        uint256 outputHalf = IERC20(output).balanceOf(address(this)).div(2);

        if (lpToken0 != output) {
            IUniswapRouterETH(unirouter).swapExactTokensForTokens(outputHalf, 0, outputToLp0Route, address(this), block.timestamp);
        }

        if (lpToken1 != output) {
            IUniswapRouterETH(unirouter).swapExactTokensForTokens(outputHalf, 0, outputToLp1Route, address(this), block.timestamp);
        }

        uint256 lp0Bal = IERC20(lpToken0).balanceOf(address(this));
        uint256 lp1Bal = IERC20(lpToken1).balanceOf(address(this));
        IUniswapRouterETH(unirouter).addLiquidity(lpToken0, lpToken1, lp0Bal, lp1Bal, 1, 1, address(this), block.timestamp);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['lpToken0', 'lpToken1', 'output', 'outputToLp0Route', 'outputToLp1Route']
- **External calls**: `IERC20(output).balanceOf(address(this)).div(2)` (method: div, receiver: IERC20), `IERC20(output).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IUniswapRouterETH(unirouter).swapExactTokensForTokens(outputHalf, 0, outputToLp0Route, address(this), block.timestamp)` (method: swapExactTokensForTokens, receiver: IUniswapRouterETH), `IUniswapRouterETH(unirouter).swapExactTokensForTokens(outputHalf, 0, outputToLp1Route, address(this), block.timestamp)` (method: swapExactTokensForTokens, receiver: IUniswapRouterETH), `IERC20(lpToken0).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IERC20(lpToken1).balanceOf(address(this))` (method: balanceOf, receiver: IERC20), `IUniswapRouterETH(unirouter).addLiquidity(lpToken0, lpToken1, lp0Bal, lp1Bal, 1, 1, address(this), block.timestamp)` (method: addLiquidity, receiver: IUniswapRouterETH)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['lpToken0', 'lpToken1', 'output', 'outputToLp0Route', 'outputToLp1Route']
- **External calls**: `IERC20(output).balanceOf(address(this)).div(2)` (inline cast call IERC20(...).div()), `IERC20(output).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IUniswapRouterETH(unirouter).swapExactTokensForTokens(outputHalf, 0, outputToLp0Route, address(this), block.timestamp)` (inline cast call IUniswapRouterETH(...).swapExactTokensForTokens()), `IUniswapRouterETH(unirouter).swapExactTokensForTokens(outputHalf, 0, outputToLp1Route, address(this), block.timestamp)` (inline cast call IUniswapRouterETH(...).swapExactTokensForTokens()), `IERC20(lpToken0).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IERC20(lpToken1).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf()), `IUniswapRouterETH(unirouter).addLiquidity(lpToken0, lpToken1, lp0Bal, lp1Bal, 1, 1, address(this), block.timestamp)` (inline cast call IUniswapRouterETH(...).addLiquidity())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### CakeMaxiWorker.reinvest

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: reinvest
- **Line Range**: L150-186
- **File**: `DAppSCAN-source/contracts/Inspex-CakeMaxi/bsc-alpaca-contract-20c4c545a0323b71d2969fd79db8316e60bc7d76/CakeMaxiWorker.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`reinvest`, lines=`L150-186`

#### 2. Function Source Code
```solidity
function reinvest() external override onlyEOA onlyReinvestor nonReentrant {
    // 1. Approve tokens
    farmingToken.safeApprove(address(masterChef), uint256(-1));
    // 2. reset all reward balance since all rewards will be reinvested
    rewardBalance = 0;
    // 3. Withdraw all the rewards.
    masterChef.leaveStaking(0);
    uint256 reward = farmingToken.myBalance();
    if (reward == 0) return;
    // 4. Send the reward bounty to the caller.
    uint256 bounty = reward.mul(reinvestBountyBps) / 10000;
    if (bounty > 0) {
      uint256 beneficialVaultBounty = bounty.mul(beneficialVaultBountyBps) / 10000;
      if (beneficialVaultBounty > 0) _rewardToBeneficialVault(beneficialVaultBounty, farmingToken);
      farmingToken.safeTransfer(_msgSender(), bounty.sub(beneficialVaultBounty));
    }
    // 5. re stake the farming token to get more rewards
    masterChef.enterStaking(reward.sub(bounty));
    // 6. Reset approval
    farmingToken.safeApprove(address(masterChef), 0);
    emit Reinvest(_msgSender(), reward, bounty);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['beneficialVaultBountyBps', 'farmingToken', 'masterChef', 'reinvestBountyBps', 'rewardBalance']
- **External calls**: `farmingToken.safeApprove(address(masterChef), uint256(-1))` (method: safeApprove, receiver: farmingToken), `masterChef.leaveStaking(0)` (method: leaveStaking, receiver: masterChef), `farmingToken.safeTransfer(_msgSender(), bounty.sub(beneficialVaultBounty))` (method: safeTransfer, receiver: farmingToken), `masterChef.enterStaking(reward.sub(bounty))` (method: enterStaking, receiver: masterChef), `farmingToken.safeApprove(address(masterChef), 0)` (method: safeApprove, receiver: farmingToken)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['beneficialVaultBountyBps', 'farmingToken', 'masterChef', 'reinvestBountyBps', 'rewardBalance']
- **External calls**: `farmingToken.safeApprove(address(masterChef), uint256(-1))` (SafeERC20 .safeApprove()), `masterChef.leaveStaking(0)` (call on contract-typed state var 'masterChef' (type: IPancakeMasterChef)), `farmingToken.safeTransfer(_msgSender(), bounty.sub(beneficialVaultBounty))` (SafeERC20 .safeTransfer()), `masterChef.enterStaking(reward.sub(bounty))` (call on contract-typed state var 'masterChef' (type: IPancakeMasterChef)), `farmingToken.safeApprove(address(masterChef), 0)` (SafeERC20 .safeApprove())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### Synthetix.exchange

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: exchange
- **Line Range**: L434-440
- **File**: `DAppSCAN-source/contracts/Iosiro-Synthetix Phase 2 Smart Contract Audit/synthetix-fdd4782ebebd7b4892c8a68000f76708d5d1aa7b/Synthetix.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`exchange`, lines=`L434-440`

#### 2. Function Source Code
```solidity
function exchange(bytes32 sourceCurrencyKey, uint sourceAmount, bytes32 destinationCurrencyKey, address destinationAddress)
        external
        optionalProxy
        // Note: We don't need to insist on non-stale rates because effectiveValue will do it for us.
        returns (bool)
    {
        require(sourceCurrencyKey != destinationCurrencyKey, "Must use different synths");
        require(sourceAmount > 0, "Zero amount");

        // verify gas price limit
        gasPriceLimit.validateGasPrice(tx.gasprice);
//SWC-114-Transaction Order Dependence:L434-440
        //  If protectionCircuit is true then we burn the synths through _internalLiquidation()
        if (protectionCircuit) {
            return _internalLiquidation(
                messageSender,
                sourceCurrencyKey,
                sourceAmount
            );
        } else {
            // Pass it along, defaulting to the sender as the recipient.
            return _internalExchange(
                messageSender,
                sourceCurrencyKey,
                sourceAmount,
                destinationCurrencyKey,
                messageSender,
                true // Charge fee on the exchange
            );
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['gasPriceLimit', 'protectionCircuit']
- **External calls**: `gasPriceLimit.validateGasPrice(tx.gasprice)` (method: validateGasPrice, receiver: gasPriceLimit)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['gasPriceLimit', 'protectionCircuit']
- **External calls**: `gasPriceLimit.validateGasPrice(tx.gasprice)` (call on contract-typed state var 'gasPriceLimit' (type: IExchangeGasPriceLimit))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MasterChef.withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdraw
- **Line Range**: L249-L267
- **File**: `DAppSCAN-source/contracts/PeckShield-BabySwap/code/baby-swap-contract-cac289bf978d969c95721c2adb9f199cee72ffa6/contracts/farm/MasterChef.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdraw`, lines=`L249-L267`

#### 2. Function Source Code
```solidity
function withdraw(uint256 _pid, uint256 _amount) public {

        require (_pid != 0, 'withdraw CAKE by unstaking');
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        require(user.amount >= _amount, "withdraw: not good");

        updatePool(_pid);
        uint256 pending = user.amount.mul(pool.accCakePerShare).div(1e12).sub(user.rewardDebt);
        if(pending > 0) {
            safeCakeTransfer(msg.sender, pending);
        }
        if(_amount > 0) {
            user.amount = user.amount.sub(_amount);
            pool.lpToken.safeTransfer(address(msg.sender), _amount);
        }
        user.rewardDebt = user.amount.mul(pool.accCakePerShare).div(1e12);
        emit Withdraw(msg.sender, _pid, _amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.amount.mul(pool.accCakePerShare).div(1e12).sub(user.rewardDebt)` (method: sub, receiver: user), `user.amount.mul(pool.accCakePerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(pool.accCakePerShare)` (method: mul, receiver: user), `user.amount.sub(_amount)` (method: sub, receiver: user), `pool.lpToken.safeTransfer(address(msg.sender), _amount)` (method: safeTransfer, receiver: pool), `user.amount.mul(pool.accCakePerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(pool.accCakePerShare)` (method: mul, receiver: user)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.amount.mul(pool.accCakePerShare).div(1e12).sub(user.rewardDebt)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accCakePerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accCakePerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.sub(_amount)` (call on contract-typed local var 'user' (type: UserInfo)), `pool.lpToken.safeTransfer(address(msg.sender), _amount)` (SafeERC20 .safeTransfer()), `user.amount.mul(pool.accCakePerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accCakePerShare)` (call on contract-typed local var 'user' (type: UserInfo))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### CryptoHeroesUniverse.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L175 - L203
- **File**: `DAppSCAN-source/contracts/PeckShield-CryptoHeroes/cryptoheroes-6cb0eaf8c88fdaab89d2b4c83535a189c7793001/CryptoHeroesUniverse.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L175 - L203`

#### 2. Function Source Code
```solidity
function deposit(uint256 _pid, uint256 _amount) public {


    PoolInfo storage pool = poolInfo[_pid];
    UserInfo storage user = userInfo[_pid][msg.sender];

    updatePool(_pid);

    if(pool.NFTisNeeded == true)
    {
        require(pool.acceptedNFT.balanceOf(address(msg.sender))>0,"requires NTF token!");
    }
    
    if (user.amount > 0) {
      uint256 pending = user.amount.mul(pool.accCheroesPerShare).div(1e12).sub(user.rewardDebt);
      if(pending > 0) {
        safeCheroesTransfer(msg.sender, pending);
      }
    }

    if(_amount > 0) {
      pool.lpToken.safeTransferFrom(address(msg.sender), address(this), _amount);
      user.amount = user.amount.add(_amount);
    }

    user.rewardDebt = user.amount.mul(pool.accCheroesPerShare).div(1e12);

    emit Deposit(msg.sender, _pid, _amount);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `pool.acceptedNFT.balanceOf(address(msg.sender))` (method: balanceOf, receiver: pool), `user.amount.mul(pool.accCheroesPerShare).div(1e12).sub(user.rewardDebt)` (method: sub, receiver: user), `user.amount.mul(pool.accCheroesPerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(pool.accCheroesPerShare)` (method: mul, receiver: user), `pool.lpToken.safeTransferFrom(address(msg.sender), address(this), _amount)` (method: safeTransferFrom, receiver: pool), `user.amount.add(_amount)` (method: add, receiver: user), `user.amount.mul(pool.accCheroesPerShare).div(1e12)` (method: div, receiver: user), `user.amount.mul(pool.accCheroesPerShare)` (method: mul, receiver: user)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `pool.acceptedNFT.balanceOf(address(msg.sender))` (call on contract-typed local var 'pool' (type: PoolInfo)), `user.amount.mul(pool.accCheroesPerShare).div(1e12).sub(user.rewardDebt)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accCheroesPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accCheroesPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `pool.lpToken.safeTransferFrom(address(msg.sender), address(this), _amount)` (SafeERC20 .safeTransferFrom()), `user.amount.add(_amount)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accCheroesPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accCheroesPerShare)` (call on contract-typed local var 'user' (type: UserInfo))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### SinglePool.emergencyWithdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: emergencyWithdraw
- **Line Range**: L202-L214
- **File**: `DAppSCAN-source/contracts/PeckShield-DSG/core-6f607f77698936e132e4e9b5cb4d75580636d919/contracts/pools/SinglePool.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`emergencyWithdraw`, lines=`L202-L214`

#### 2. Function Source Code
```solidity
function emergencyWithdraw() public {
        PoolInfo storage pool = poolInfo[0];
        UserInfo storage user = userInfo[msg.sender];
        pool.lpToken.safeTransfer(address(msg.sender), user.amount);
        if(totalDeposit >= user.amount) {
            totalDeposit = totalDeposit.sub(user.amount);
        } else {
            totalDeposit = 0;
        }
        user.amount = 0;
        user.rewardDebt = 0;
        emit EmergencyWithdraw(msg.sender, user.amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'totalDeposit', 'userInfo']
- **External calls**: `pool.lpToken.safeTransfer(address(msg.sender), user.amount)` (method: safeTransfer, receiver: pool)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'totalDeposit', 'userInfo']
- **External calls**: `pool.lpToken.safeTransfer(address(msg.sender), user.amount)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### SkyRewardPool.withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdraw
- **Line Range**: L217-L234
- **File**: `DAppSCAN-source/contracts/PeckShield-DarkCrypto/darkcrypto-contracts-fee5be8d36459aebed2b84e6493875b3dc0366fd/contracts/distribution/SkyRewardPool.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdraw`, lines=`L217-L234`

#### 2. Function Source Code
```solidity
function withdraw(uint256 _pid, uint256 _amount) public {
        address _sender = msg.sender;
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][_sender];
        require(user.amount >= _amount, "withdraw: not good");
        updatePool(_pid);
        uint256 _pending = user.amount.mul(pool.accSkyPerShare).div(1e18).sub(user.rewardDebt);
        if (_pending > 0) {
            safeSkyTransfer(_sender, _pending);
            emit RewardPaid(_sender, _pending);
        }
        if (_amount > 0) {
            user.amount = user.amount.sub(_amount);
            pool.token.safeTransfer(_sender, _amount);
        }
        user.rewardDebt = user.amount.mul(pool.accSkyPerShare).div(1e18);
        emit Withdraw(_sender, _pid, _amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.amount.mul(pool.accSkyPerShare).div(1e18).sub(user.rewardDebt)` (method: sub, receiver: user), `user.amount.mul(pool.accSkyPerShare).div(1e18)` (method: div, receiver: user), `user.amount.mul(pool.accSkyPerShare)` (method: mul, receiver: user), `user.amount.sub(_amount)` (method: sub, receiver: user), `pool.token.safeTransfer(_sender, _amount)` (method: safeTransfer, receiver: pool), `user.amount.mul(pool.accSkyPerShare).div(1e18)` (method: div, receiver: user), `user.amount.mul(pool.accSkyPerShare)` (method: mul, receiver: user)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.amount.mul(pool.accSkyPerShare).div(1e18).sub(user.rewardDebt)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accSkyPerShare).div(1e18)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accSkyPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.sub(_amount)` (call on contract-typed local var 'user' (type: UserInfo)), `pool.token.safeTransfer(_sender, _amount)` (SafeERC20 .safeTransfer()), `user.amount.mul(pool.accSkyPerShare).div(1e18)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.mul(pool.accSkyPerShare)` (call on contract-typed local var 'user' (type: UserInfo))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### HegicPool.provideFrom

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: provideFrom
- **Line Range**: L373 - L409
- **File**: `DAppSCAN-source/contracts/PeckShield-Hegic(v8888)/Hegic-v8888-2dcd44dc1ae07881e94d52fa618f9704bfd4ffda/contracts/Pool/HegicPool.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`provideFrom`, lines=`L373 - L409`

#### 2. Function Source Code
```solidity
function provideFrom(
        address account,
        uint256 amount,
        bool hedged,
        uint256 minShare
    ) external override returns (uint256 share) {
        uint256 totalShare = hedged ? hedgedShare : unhedgedShare;
        uint256 balance = hedged ? hedgedBalance : unhedgedBalance;
        share = totalShare > 0 && balance > 0
            ? (amount * totalShare) / balance
            : amount * INITIAL_RATE;
        uint256 limit =
            hedged
                ? maxHedgedDepositAmount - hedgedBalance
                : maxDepositAmount - hedgedBalance - unhedgedBalance;
        require(share >= minShare, "Pool Error: The mint limit is too large");
        require(share > 0, "Pool Error: The amount is too small");
        require(
            amount <= limit,
            "Pool Error: Depositing into the pool is not available"
        );

        if (hedged) {
            hedgedShare += share;
            hedgedBalance += amount;
        } else {
            unhedgedShare += share;
            unhedgedBalance += amount;
        }

        uint256 trancheID = tranches.length;
        tranches.push(
            Tranche(TrancheState.Open, share, amount, block.timestamp, hedged)
        );
        _safeMint(account, trancheID);
        token.safeTransferFrom(_msgSender(), address(this), amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['INITIAL_RATE', 'hedgedBalance', 'hedgedShare', 'maxDepositAmount', 'maxHedgedDepositAmount', 'token', 'tranches', 'unhedgedBalance', 'unhedgedShare']
- **External calls**: `tranches.push(
            Tranche(TrancheState.Open, share, amount, block.timestamp, hedged)
        )` (method: push, receiver: tranches), `token.safeTransferFrom(_msgSender(), address(this), amount)` (method: safeTransferFrom, receiver: token)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['INITIAL_RATE', 'hedgedBalance', 'hedgedShare', 'maxDepositAmount', 'maxHedgedDepositAmount', 'token', 'tranches', 'unhedgedBalance', 'unhedgedShare']
- **External calls**: `tranches.push(
            Tranche(TrancheState.Open, share, amount, block.timestamp, hedged)
        )` (call on contract-typed state var 'tranches' (type: Tranche[])), `token.safeTransferFrom(_msgSender(), address(this), amount)` (SafeERC20 .safeTransferFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MasterMilker.emergencyWithdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: emergencyWithdraw
- **Line Range**: L237-L244
- **File**: `DAppSCAN-source/contracts/PeckShield-MilkySwap/milkyswap-59f163e9959cf8bae4a521a9648219b553312e07/contracts/MasterMilker.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`emergencyWithdraw`, lines=`L237-L244`

#### 2. Function Source Code
```solidity
function emergencyWithdraw(uint256 _pid) public {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        emit EmergencyWithdraw(msg.sender, _pid, user.amount);
        pool.lpToken.safeTransfer(address(msg.sender), user.amount);
        user.amount = 0;
        user.rewardDebt = 0;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `pool.lpToken.safeTransfer(address(msg.sender), user.amount)` (method: safeTransfer, receiver: pool)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `pool.lpToken.safeTransfer(address(msg.sender), user.amount)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MasterShiba.withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdraw
- **Line Range**: L339 - L341
- **File**: `DAppSCAN-source/contracts/PeckShield-ShibaNova/Contracts-b6b1ce1fcaff83d360df8944309f49958842b7b8/shibanova/contracts/MasterShiba.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdraw`, lines=`L339 - L341`

#### 2. Function Source Code
```solidity
function withdraw(uint256 _pid, uint256 _amount) external validatePool(_pid) {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        require(user.amount >= _amount, "withdraw: not good");

        updatePool(_pid);
        uint256 pending = user.amountWithBonus.mul(pool.accNovaPerShare).div(1e12).sub(user.rewardDebt);
        if(pending > 0) {
            if(pool.isSNovaRewards){
                safeSNovaTransfer(msg.sender, pending);
            }
            else{
                safeNovaTransfer(msg.sender, pending);
            }
        }
        if(_amount > 0) {
            user.amount = user.amount.sub(_amount);
            uint256 _bonusAmount = _amount.mul(userBonus(_pid, msg.sender).add(10000)).div(10000);
            user.amountWithBonus = user.amountWithBonus.sub(_bonusAmount);
            // SWC-107-Reentrancy: L339 - L341
            pool.lpToken.safeTransfer(address(msg.sender), _amount);
            pool.lpSupply = pool.lpSupply.sub(_bonusAmount);
        }
        user.rewardDebt = user.amountWithBonus.mul(pool.accNovaPerShare).div(1e12);
        emit Withdraw(msg.sender, _pid, _amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.amountWithBonus.mul(pool.accNovaPerShare).div(1e12).sub(user.rewardDebt)` (method: sub, receiver: user), `user.amountWithBonus.mul(pool.accNovaPerShare).div(1e12)` (method: div, receiver: user), `user.amountWithBonus.mul(pool.accNovaPerShare)` (method: mul, receiver: user), `user.amount.sub(_amount)` (method: sub, receiver: user), `user.amountWithBonus.sub(_bonusAmount)` (method: sub, receiver: user), `pool.lpToken.safeTransfer(address(msg.sender), _amount)` (method: safeTransfer, receiver: pool), `pool.lpSupply.sub(_bonusAmount)` (method: sub, receiver: pool), `user.amountWithBonus.mul(pool.accNovaPerShare).div(1e12)` (method: div, receiver: user), `user.amountWithBonus.mul(pool.accNovaPerShare)` (method: mul, receiver: user)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `user.amountWithBonus.mul(pool.accNovaPerShare).div(1e12).sub(user.rewardDebt)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amountWithBonus.mul(pool.accNovaPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amountWithBonus.mul(pool.accNovaPerShare)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amount.sub(_amount)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amountWithBonus.sub(_bonusAmount)` (call on contract-typed local var 'user' (type: UserInfo)), `pool.lpToken.safeTransfer(address(msg.sender), _amount)` (SafeERC20 .safeTransfer()), `pool.lpSupply.sub(_bonusAmount)` (call on contract-typed local var 'pool' (type: PoolInfo)), `user.amountWithBonus.mul(pool.accNovaPerShare).div(1e12)` (call on contract-typed local var 'user' (type: UserInfo)), `user.amountWithBonus.mul(pool.accNovaPerShare)` (call on contract-typed local var 'user' (type: UserInfo))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### LPGauge.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L75-L89
- **File**: `DAppSCAN-source/contracts/PeckShield-StackerVC/StackerVC_VentureFund001-3cfb98b21f4731dfd62993feb7c7d1540837f59b/contracts/Token/LPGauge.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L75-L89`

#### 2. Function Source Code
```solidity
function deposit(uint256 _amount) nonReentrant external {
    	require(block.number <= endBlock, "LPGAUGE: distribution over");

    	_claimSTACK(msg.sender);

    	IERC20(token).safeTransferFrom(msg.sender, address(this), _amount);

    	DepositState memory _state = balances[msg.sender];
    	_state.balance = _state.balance.add(_amount);
    	deposited = deposited.add(_amount);

    	emit Deposit(msg.sender, _amount);

    	balances[msg.sender] = _state;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['balances', 'deposited', 'endBlock', 'token']
- **External calls**: `IERC20(token).safeTransferFrom(msg.sender, address(this), _amount)` (method: safeTransferFrom, receiver: IERC20), `_state.balance.add(_amount)` (method: add, receiver: _state)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['balances', 'deposited', 'endBlock', 'token']
- **External calls**: `IERC20(token).safeTransferFrom(msg.sender, address(this), _amount)` (SafeERC20 .safeTransferFrom()), `_state.balance.add(_amount)` (call on contract-typed local var '_state' (type: DepositState))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### LiquidityStaking.deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: deposit
- **Line Range**: L60-L69
- **File**: `DAppSCAN-source/contracts/PeckShield-Tranchessv1.0/contract-core-5ac3d997da3ef37b0135565a11c5ebcc519862aa/contracts/governance/LiquidityStaking.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`deposit`, lines=`L60-L69`

#### 2. Function Source Code
```solidity
function deposit(uint256 amount) external {
        userCheckpoint(msg.sender);

        require(
            IERC20(stakedToken).transferFrom(msg.sender, address(this), amount),
            "Staked transferFrom failed"
        );
        totalStakes = totalStakes.add(amount);
        stakes[msg.sender] = stakes[msg.sender].add(amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['stakedToken', 'stakes', 'totalStakes']
- **External calls**: `IERC20(stakedToken).transferFrom(msg.sender, address(this), amount)` (method: transferFrom, receiver: IERC20)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['stakedToken', 'stakes', 'totalStakes']
- **External calls**: `IERC20(stakedToken).transferFrom(msg.sender, address(this), amount)` (inline cast call IERC20(...).transferFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### LighthouseLib.withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: withdraw
- **Line Range**: L24
- **File**: `DAppSCAN-source/contracts/PepperSec-Aira-Robonomic/robonomics_contracts-cc35a91de187072214d215262d8371f0159c2498/contracts/robonomics/LighthouseLib.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`withdraw`, lines=`L24`

#### 2. Function Source Code
```solidity
function withdraw(uint256 _value) external {
        require(balances[msg.sender] >= _value);
        //SWC-107-Reentrancy: L24
        require(xrt.transfer(msg.sender, _value));
        balances[msg.sender] -= _value;

        // Drop member if quota go to zero
        if (quotaOf(msg.sender) == 0) {
            require(xrt.transfer(msg.sender, balances[msg.sender])); 
            balances[msg.sender] = 0;
            
            uint256 senderIndex = indexOf[msg.sender];
            uint256 lastIndex = members.length - 1;
            if (senderIndex < lastIndex)
                members[senderIndex] = members[lastIndex];
            members.length -= 1;
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['balances', 'indexOf', 'members', 'xrt']
- **External calls**: `xrt.transfer(msg.sender, _value)` (method: transfer, receiver: xrt), `xrt.transfer(msg.sender, balances[msg.sender])` (method: transfer, receiver: xrt)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['balances', 'indexOf', 'members', 'xrt']
- **External calls**: `xrt.transfer(msg.sender, _value)` (low-level .transfer()), `xrt.transfer(msg.sender, balances[msg.sender])` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### FixedRateSwap.depositFor

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: depositFor
- **Line Range**: L137
- **File**: `DAppSCAN-source/contracts/QuillAudits-1inch-Fixed Rate Swap/fixed-rate-swap-0b5a75e9f56e7d21c290dd28c59dc140dcbcc1d5/contracts/FixedRateSwap.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`depositFor`, lines=`L137`

#### 2. Function Source Code
```solidity
function depositFor(uint256 token0Amount, uint256 token1Amount, address to) public returns(uint256 share) {
        (uint256 token0VirtualAmount, uint256 token1VirtualAmount) = _getVirtualAmountsForDeposit(token0Amount, token1Amount);

        uint256 inputAmount = token0VirtualAmount + token1VirtualAmount;
        require(inputAmount > 0, "Empty deposit is not allowed");
        require(to != address(this), "Deposit to this is forbidden");
        // _mint also checks require(to != address(0))

        uint256 _totalSupply = totalSupply();
        if (_totalSupply > 0) {
            uint256 totalBalance = token0.balanceOf(address(this)) + token1.balanceOf(address(this)) +
                                   token0Amount + token1Amount - inputAmount;
            share = inputAmount * _totalSupply / totalBalance;
        } else {
            share = inputAmount;
        }

        if (token0Amount > 0) {
            // SWC-107-Reentrancy: L137
            token0.safeTransferFrom(msg.sender, address(this), token0Amount);
        }
        if (token1Amount > 0) {
            token1.safeTransferFrom(msg.sender, address(this), token1Amount);
        }
        _mint(to, share);
        emit Deposit(to, token0Amount, token1Amount, share);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['token0', 'token1']
- **External calls**: `token0.balanceOf(address(this))` (method: balanceOf, receiver: token0), `token0.safeTransferFrom(msg.sender, address(this), token0Amount)` (method: safeTransferFrom, receiver: token0), `token1.safeTransferFrom(msg.sender, address(this), token1Amount)` (method: safeTransferFrom, receiver: token1)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['token0', 'token1']
- **External calls**: `token0.balanceOf(address(this))` (call on contract-typed state var 'token0' (type: IERC20)), `token0.safeTransferFrom(msg.sender, address(this), token0Amount)` (SafeERC20 .safeTransferFrom()), `token1.safeTransferFrom(msg.sender, address(this), token1Amount)` (SafeERC20 .safeTransferFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### MasterChef.emergencyWithdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: emergencyWithdraw
- **Line Range**: L163 - L171
- **File**: `DAppSCAN-source/contracts/QuillAudits-Alium Finance Smart Contract/alium-farm-e37d6af39af68049c2684085f025385407b4bd55/contracts/MasterChef.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`emergencyWithdraw`, lines=`L163 - L171`

#### 2. Function Source Code
```solidity
function emergencyWithdraw(uint256 _pid) external {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        uint userBalance = user.amount;
        user.amount = 0;
        user.rewardDebt = 0;
        pool.lpToken.safeTransfer(address(msg.sender), userBalance);
        emit EmergencyWithdraw(msg.sender, _pid, userBalance);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `pool.lpToken.safeTransfer(address(msg.sender), userBalance)` (method: safeTransfer, receiver: pool)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['poolInfo', 'userInfo']
- **External calls**: `pool.lpToken.safeTransfer(address(msg.sender), userBalance)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### BCubePublicSale.buyBcubeUsingUSDT

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: buyBcubeUsingUSDT
- **Line Range**: L264 - L278
- **File**: `DAppSCAN-source/contracts/QuillAudits-BCUBE Smart Contract/b-cube-ico-13f9f8a991a65f3e0ca60a2078121fdd5a921fb0/contracts/BCubePublicSale.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`buyBcubeUsingUSDT`, lines=`L264 - L278`

#### 2. Function Source Code
```solidity
function buyBcubeUsingUSDT(uint256 incomingUsdt)
    external
    onlyWhitelisted
    onlyWhileOpen
    tokensRemaining
    nonReentrant
  {
    uint256 allocation;
    uint256 usdtPrice = uint256(fetchUSDTPrice());
    uint256 dollarUnits = usdtPrice.mul(incomingUsdt).div(1e6);
    allocation = executeAllocation(dollarUnits);
    usdt.safeTransferFrom(_msgSender(), wallet, incomingUsdt);
    
    emit LogBcubeBuyUsingUsdt(_msgSender(), incomingUsdt, allocation);
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['usdt', 'wallet']
- **External calls**: `usdt.safeTransferFrom(_msgSender(), wallet, incomingUsdt)` (method: safeTransferFrom, receiver: usdt)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['usdt', 'wallet']
- **External calls**: `usdt.safeTransferFrom(_msgSender(), wallet, incomingUsdt)` (SafeERC20 .safeTransferFrom())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### ProfitSplitter._payToRecipients

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: _payToRecipients
- **Line Range**: L228
- **File**: `DAppSCAN-source/contracts/QuillAudits-Bond Appetit-Bond Appetit/bondappetit-protocol-355180f0aca0b29d60d808f761052956b7a3a159/contracts/profit/ProfitSplitter.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`_payToRecipients`, lines=`L228`

#### 2. Function Source Code
```solidity
function _payToRecipients() internal returns (bool) {
        uint256 splitterIncomingBalance = incoming.balanceOf(address(this));
        if (splitterIncomingBalance == 0) return false;

        for (uint256 i = 0; i < recipientsIndex.length(); i++) {
            address recipient = recipientsIndex.at(i);
            uint256 share = shares[recipient];

            uint256 amount = splitterIncomingBalance.mul(10**SHARE_ACCURACY).mul(share).div(10**SHARE_ACCURACY.add(SHARE_DIGITS));
            incoming.safeTransfer(recipient, amount);

            emit PayToRecipient(recipient, amount);
        }

        return true;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['SHARE_ACCURACY', 'SHARE_DIGITS', 'incoming', 'recipientsIndex', 'shares']
- **External calls**: `incoming.balanceOf(address(this))` (method: balanceOf, receiver: incoming), `recipientsIndex.at(i)` (method: at, receiver: recipientsIndex), `incoming.safeTransfer(recipient, amount)` (method: safeTransfer, receiver: incoming)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['SHARE_ACCURACY', 'SHARE_DIGITS', 'incoming', 'recipientsIndex', 'shares']
- **External calls**: `incoming.balanceOf(address(this))` (call on contract-typed state var 'incoming' (type: ERC20)), `recipientsIndex.at(i)` (call on contract-typed state var 'recipientsIndex' (type: EnumerableSet.AddressSet)), `incoming.safeTransfer(recipient, amount)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### TimeLock.release

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: release
- **Line Range**: L132
- **File**: `DAppSCAN-source/contracts/QuillAudits-Citrus Smart Contract/CitrusTechContract-e50a2a983928c10b76e6bc374ae6267f51af99b6/CitrusToken.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`release`, lines=`L132`

#### 2. Function Source Code
```solidity
function release() public returns (bool) {
        LockedAccounts storage lockedAccount = lock[msg.sender];
//        SWC-104-Unchecked Call Return Value: L132
        for(uint i = 0; i < lockedAccount.locked.length; i++) {
            Locked storage loc = lockedAccount.locked[i];
            require(block.timestamp >= (loc.time + loc.lockedAt), "TimeLock: Release time not reached");
            uint amount = loc.amount;
            BEP(address(this)).transfer(msg.sender, amount);
            loc.amount = 0;
            loc.time = 0;
            loc.lockedAt = 0;
        }
        return true;
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['lock']
- **External calls**: `BEP(address(this)).transfer(msg.sender, amount)` (method: transfer, receiver: BEP)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['lock']
- **External calls**: `BEP(address(this)).transfer(msg.sender, amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### PoolService.lendCreditAccount

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: lendCreditAccount
- **Line Range**: L238 - L258
- **File**: `DAppSCAN-source/contracts/QuillAudits-GearBox Protocol-GearBox Protocol/gearbox-contracts-0ac33ba87212ce056ac6b6357ad74161d417158a/contracts/pool/PoolService.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`lendCreditAccount`, lines=`L238 - L258`

#### 2. Function Source Code
```solidity
function lendCreditAccount(uint256 borrowedAmount, address creditAccount)
        external
        override
        whenNotPaused // T:[PS-4]
    {
        require(
            creditManagersCanBorrow[msg.sender],
            Errors.POOL_CREDIT_MANAGERS_ONLY
        ); // T:[PS-12, 13]

        // Transfer funds to credit account
        IERC20(underlyingToken).safeTransfer(creditAccount, borrowedAmount); // T:[PS-14]

        // Update borrow Rate
        _updateBorrowRate(); // T:[PS-17]

        // Increase total borrowed amount
        totalBorrowed = totalBorrowed.add(borrowedAmount); // T:[PS-16]

        emit Borrow(msg.sender, creditAccount, borrowedAmount); // T:[PS-15]
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['creditManagersCanBorrow', 'totalBorrowed', 'underlyingToken']
- **External calls**: `IERC20(underlyingToken).safeTransfer(creditAccount, borrowedAmount)` (method: safeTransfer, receiver: IERC20)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['creditManagersCanBorrow', 'totalBorrowed', 'underlyingToken']
- **External calls**: `IERC20(underlyingToken).safeTransfer(creditAccount, borrowedAmount)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### LTOTokenSale.clear

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: clear
- **Line Range**: L238 - L245
- **File**: `DAppSCAN-source/contracts/QuillAudits-LTO Network-Token Sale/lto-erc20-token-02fa2620aef4c854675230b6544461961d47f968/contracts/LTOTokenSale.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`clear`, lines=`L238 - L245`

#### 2. Function Source Code
```solidity
function clear(uint256 tokenAmount, uint256 etherAmount) payable public purchasersAllWithdrawn onlyClearTime onlyOwner {
    if (tokenAmount > 0) {
      token.transfer(receiverAddr, tokenAmount);
    }
    if (etherAmount > 0) {
      receiverAddr.transfer(etherAmount);
    }
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['receiverAddr', 'token']
- **External calls**: `token.transfer(receiverAddr, tokenAmount)` (method: transfer, receiver: token), `receiverAddr.transfer(etherAmount)` (method: transfer, receiver: receiverAddr)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['receiverAddr', 'token']
- **External calls**: `token.transfer(receiverAddr, tokenAmount)` (low-level .transfer()), `receiverAddr.transfer(etherAmount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### GenericLenderBase.sweep

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: sweep
- **Line Range**: L56
- **File**: `DAppSCAN-source/contracts/QuillAudits-Yearn Finance-Generic Lender/yearnV2-generic-lender-strat-979ef2f0e5da39ca59a5907c37ba2064fcd6be82/contracts/GenericLender/GenericLenderBase.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`sweep`, lines=`L56`

#### 2. Function Source Code
```solidity
function sweep(address _token) external virtual override management {
        address[] memory _protectedTokens = protectedTokens();
        for (uint256 i; i < _protectedTokens.length; i++) require(_token != _protectedTokens[i], "!protected");
        // SWC-104-Unchecked Call Return Value: L56
        IERC20(_token).transfer(vault.governance(), IERC20(_token).balanceOf(address(this)));
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['vault']
- **External calls**: `IERC20(_token).transfer(vault.governance(), IERC20(_token).balanceOf(address(this)))` (method: transfer, receiver: IERC20), `vault.governance()` (method: governance, receiver: vault), `IERC20(_token).balanceOf(address(this))` (method: balanceOf, receiver: IERC20)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['vault']
- **External calls**: `IERC20(_token).transfer(vault.governance(), IERC20(_token).balanceOf(address(this)))` (low-level .transfer()), `vault.governance()` (call on contract-typed state var 'vault' (type: VaultAPI)), `IERC20(_token).balanceOf(address(this))` (inline cast call IERC20(...).balanceOf())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### CoreVoting.execute

**Pre-classification**: ✅ CONFIRMED
**Reason**: Reentrancy pattern present: external call + state modification in function

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: execute
- **Line Range**: L238 - L277
- **File**: `DAppSCAN-source/contracts/Runtime_Vеrification-Element_Finance_Governance_Security_Audit_Report/council-3d751c959b42573c78ccd0bccbc80424bf6d9a90/contracts/CoreVoting.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`execute`, lines=`L238 - L277`

#### 2. Function Source Code
```solidity
function execute(
        uint256 proposalId,
        address[] memory targets,
        bytes[] memory calldatas
    ) external {
        require(block.number >= proposals[proposalId].unlock, "not unlocked");
        // If executed the proposal will be deleted and this will be zero
        require(proposals[proposalId].unlock != 0, "Previously executed");

        // ensure the data matches the hash
        require(
            keccak256(abi.encodePacked(targets, abi.encode(calldatas))) ==
                proposals[proposalId].proposalHash,
            "hash mismatch"
        );

        uint128[3] memory results = proposals[proposalId].votingPower;
        // if there are enough votes to meet quorum and there are more yes votes than no votes
        // then the proposal is executed
        bool passesQuorum =
            results[0] + results[1] + results[2] >=
                proposals[proposalId].quorum;
        bool majorityInFavor = results[0] > results[1];

        require(passesQuorum && majorityInFavor, "Cannot execute");

        // Execute a package of low level calls
        // SECURITY - WILL NOT REVERT IF A SINGLE CALL FAILS, PROPOSALS MUST BE CONSTRUCTED
        //            WITH THIS IN MIND
        for (uint256 i = 0; i < targets.length; i++) {
            targets[i].call(calldatas[i]);
        }
        // Notification of proposal execution
        emit ProposalExecuted(proposalId);

        // delete proposal for some gas savings,
        // Proposals are only deleted when they are actually executed, failed proposals
        // are never deleted
        delete proposals[proposalId];
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['proposals']
- **External calls**: `targets[i].call(calldatas[i])` (method: call, receiver: targets)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['proposals']
- **External calls**: `targets[i].call(calldatas[i])` (low-level .call())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### Vesting.rug

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: rug
- **Line Range**: L160
- **File**: `DAppSCAN-source/contracts/Runtime_Vеrification-Tracer_Perpetual_Pools_V2/vesting-a02cbd5e73e629b5d80c0af0202a3ee6f18d0216/contracts/Vesting.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`rug`, lines=`L160`

#### 2. Function Source Code
```solidity
function rug(address account, uint256 scheduleId) external onlyOwner {
        Schedule storage schedule = schedules[account][scheduleId];
        require(!schedule.isFixed, "Vesting: Account is fixed");
        uint256 outstandingAmount = schedule.totalAmount -
            schedule.claimedAmount;
        require(outstandingAmount != 0, "Vesting: no outstanding tokens");
        schedule.totalAmount = 0;
        locked[schedule.asset] = locked[schedule.asset] - outstandingAmount;
        require(IERC20(schedule.asset).transfer(owner(), outstandingAmount), "Vesting: transfer failed");
        emit Cancelled(account);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['locked', 'schedules']
- **External calls**: `IERC20(schedule.asset).transfer(owner(), outstandingAmount)` (method: transfer, receiver: IERC20)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['locked', 'schedules']
- **External calls**: `IERC20(schedule.asset).transfer(owner(), outstandingAmount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### xMPH._deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _deposit
- **Line Range**: L178
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-88mph/88mph-contracts-76cd9d1fc45e65f5d0f686621fe6af85c40aa140/contracts/rewards/xMPH.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_deposit`, lines=`L178`

#### 2. Function Source Code
```solidity
function _deposit(uint256 _mphAmount)
        internal
        virtual
        returns (uint256 shareAmount)
    {
        require(_mphAmount > 0, "xMPH: amount");
        shareAmount = _mphAmount.decdiv(getPricePerFullShare());
        _mint(msg.sender, shareAmount);
        // SWC-104-Unchecked Call Return Value: L178
        mph.transferFrom(msg.sender, address(this), _mphAmount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['mph']
- **External calls**: `mph.transferFrom(msg.sender, address(this), _mphAmount)` (method: transferFrom, receiver: mph)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['mph']
- **External calls**: `mph.transferFrom(msg.sender, address(this), _mphAmount)` (call on contract-typed state var 'mph' (type: ERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### xMPH._withdraw

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _withdraw
- **Line Range**: L196
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-88mph/88mph-contracts-76cd9d1fc45e65f5d0f686621fe6af85c40aa140/contracts/rewards/xMPH.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_withdraw`, lines=`L196`

#### 2. Function Source Code
```solidity
function _withdraw(uint256 _shareAmount)
        internal
        virtual
        returns (uint256 mphAmount)
    {
        require(
            totalSupply() >= _shareAmount + MIN_AMOUNT && _shareAmount > 0,
            "xMPH: amount"
        );
        mphAmount = _shareAmount.decmul(getPricePerFullShare());
        _burn(msg.sender, _shareAmount);
        // SWC-104-Unchecked Call Return Value: L196
        mph.transfer(msg.sender, mphAmount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['MIN_AMOUNT', 'mph']
- **External calls**: `mph.transfer(msg.sender, mphAmount)` (method: transfer, receiver: mph)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['MIN_AMOUNT', 'mph']
- **External calls**: `mph.transfer(msg.sender, mphAmount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### xMPH._distributeReward

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _distributeReward
- **Line Range**: L212
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-88mph/88mph-contracts-76cd9d1fc45e65f5d0f686621fe6af85c40aa140/contracts/rewards/xMPH.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_distributeReward`, lines=`L212`

#### 2. Function Source Code
```solidity
function _distributeReward(uint256 rewardAmount) internal {
        require(totalSupply() >= MIN_AMOUNT, "xMPH: supply");
        require(rewardAmount >= MIN_AMOUNT, "xMPH: reward");
        require(
            rewardAmount < type(uint256).max / PRECISION,
            "xMPH: rewards too large, would lock"
        );
        require(hasRole(DISTRIBUTOR_ROLE, msg.sender), "xMPH: not distributor");

        // transfer rewards from sender
        // SWC-104-Unchecked Call Return Value: L212
        mph.transferFrom(msg.sender, address(this), rewardAmount);

        if (block.timestamp >= currentUnlockEndTimestamp) {
            // start new reward period
            currentUnlockEndTimestamp = block.timestamp + rewardUnlockPeriod;
            lastRewardTimestamp = block.timestamp;
            lastRewardAmount = rewardAmount;
        } else {
            // add rewards to current reward period
            uint256 lockedRewardAmount =
                (lastRewardAmount *
                    (currentUnlockEndTimestamp - block.timestamp)) /
                    (currentUnlockEndTimestamp - lastRewardTimestamp);
            lastRewardTimestamp = block.timestamp;
            lastRewardAmount = rewardAmount + lockedRewardAmount;
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['DISTRIBUTOR_ROLE', 'MIN_AMOUNT', 'PRECISION', 'currentUnlockEndTimestamp', 'lastRewardAmount', 'lastRewardTimestamp', 'mph', 'rewardUnlockPeriod']
- **External calls**: `mph.transferFrom(msg.sender, address(this), rewardAmount)` (method: transferFrom, receiver: mph)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['DISTRIBUTOR_ROLE', 'MIN_AMOUNT', 'PRECISION', 'currentUnlockEndTimestamp', 'lastRewardAmount', 'lastRewardTimestamp', 'mph', 'rewardUnlockPeriod']
- **External calls**: `mph.transferFrom(msg.sender, address(this), rewardAmount)` (call on contract-typed state var 'mph' (type: ERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### CurveAMO.giveCollatBack

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: giveCollatBack
- **Line Range**: L371
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-FraxFinance/frax-solidity-3f0993a70e3496fd27887db7754d68709c84015e/contracts/Curve/CurveAMO.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`giveCollatBack`, lines=`L371`

#### 2. Function Source Code
```solidity
function giveCollatBack(uint256 amount) public onlyByOwnerOrGovernance {
        // SWC-104-Unchecked Call Return Value: L371
        collateral_token.transfer(address(pool), amount);
        returned_collat_historical = returned_collat_historical.add(amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['collateral_token', 'pool', 'returned_collat_historical']
- **External calls**: `collateral_token.transfer(address(pool), amount)` (method: transfer, receiver: collateral_token)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['collateral_token', 'pool', 'returned_collat_historical']
- **External calls**: `collateral_token.transfer(address(pool), amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### FraxPool.collectRedemption

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: collectRedemption
- **Line Range**: L366
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-FraxFinance/frax-solidity-3f0993a70e3496fd27887db7754d68709c84015e/contracts/Frax/Pools/FraxPool.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`collectRedemption`, lines=`L366`

#### 2. Function Source Code
```solidity
function collectRedemption() external {
        require((lastRedeemed[msg.sender].add(redemption_delay)) <= block.number, "Must wait for redemption_delay blocks before collecting redemption");
        bool sendFXS = false;
        bool sendCollateral = false;
        uint FXSAmount;
        uint CollateralAmount;

        // Use Checks-Effects-Interactions pattern
        if(redeemFXSBalances[msg.sender] > 0){
            FXSAmount = redeemFXSBalances[msg.sender];
            redeemFXSBalances[msg.sender] = 0;
            unclaimedPoolFXS = unclaimedPoolFXS.sub(FXSAmount);

            sendFXS = true;
        }
        
        if(redeemCollateralBalances[msg.sender] > 0){
            CollateralAmount = redeemCollateralBalances[msg.sender];
            redeemCollateralBalances[msg.sender] = 0;
            unclaimedPoolCollateral = unclaimedPoolCollateral.sub(CollateralAmount);

            sendCollateral = true;
        }

        if(sendFXS == true){
            // SWC-104-Unchecked Call Return Value: L366
            FXS.transfer(msg.sender, FXSAmount);
        }
        if(sendCollateral == true){
            // SWC-104-Unchecked Call Return Value: L370
            collateral_token.transfer(msg.sender, CollateralAmount);
        }
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['FXS', 'collateral_token', 'lastRedeemed', 'redeemCollateralBalances', 'redeemFXSBalances', 'redemption_delay', 'unclaimedPoolCollateral', 'unclaimedPoolFXS']
- **External calls**: `FXS.transfer(msg.sender, FXSAmount)` (method: transfer, receiver: FXS), `collateral_token.transfer(msg.sender, CollateralAmount)` (method: transfer, receiver: collateral_token)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['FXS', 'collateral_token', 'lastRedeemed', 'redeemCollateralBalances', 'redeemFXSBalances', 'redemption_delay', 'unclaimedPoolCollateral', 'unclaimedPoolFXS']
- **External calls**: `FXS.transfer(msg.sender, FXSAmount)` (low-level .transfer()), `collateral_token.transfer(msg.sender, CollateralAmount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### InvestorAMO_V2.giveCollatBack

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: giveCollatBack
- **Line Range**: L263
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-FraxFinance/frax-solidity-3f0993a70e3496fd27887db7754d68709c84015e/contracts/Misc_AMOs/InvestorAMO_V2.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`giveCollatBack`, lines=`L263`

#### 2. Function Source Code
```solidity
function giveCollatBack(uint256 amount) public onlyByOwnerOrGovernance {
        // Still paying back principal
        if (amount <= borrowed_balance) {
            borrowed_balance = borrowed_balance.sub(amount);
        }
        // Pure profits
        else {
            borrowed_balance = 0;
        }
        paid_back_historical = paid_back_historical.add(amount);
        // SWC-104-Unchecked Call Return Value: L263
        collateral_token.transfer(address(pool), amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['borrowed_balance', 'collateral_token', 'paid_back_historical', 'pool']
- **External calls**: `collateral_token.transfer(address(pool), amount)` (method: transfer, receiver: collateral_token)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['borrowed_balance', 'collateral_token', 'paid_back_historical', 'pool']
- **External calls**: `collateral_token.transfer(address(pool), amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### Liquidator.liquidatePortion

**Pre-classification**: ✅ CONFIRMED
**Reason**: External call + state access present; state-write-after-call ordering not verified from source alone

#### 1. SWC Annotation
- **Category**: SWC-107-Reentrancy
- **SWC Code**: SWC-107
- **Annotated Function**: liquidatePortion
- **Line Range**: L41-L51
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-MapleFinance/liquidations-35c628e5ab45fbffaab7aef43a030a98b712a94a/contracts/Liquidator.sol`
- **Original SWC entry**: category=`SWC-107-Reentrancy`, function=`liquidatePortion`, lines=`L41-L51`

#### 2. Function Source Code
```solidity
function liquidatePortion(uint256 swapAmount_, bytes calldata data_) external override {
        ERC20Helper.transfer(collateralAsset, msg.sender, swapAmount_);

        msg.sender.call(data_);

        uint256 returnAmount = getExpectedAmount(swapAmount_);

        require(ERC20Helper.transferFrom(fundsAsset, msg.sender, destination, returnAmount), "LIQ:LP:TRANSFER_FROM");

        emit PortionLiquidated(swapAmount_, returnAmount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['collateralAsset', 'destination', 'fundsAsset']
- **External calls**: `ERC20Helper.transfer(collateralAsset, msg.sender, swapAmount_)` (method: transfer, receiver: ERC20Helper), `msg.sender.call(data_)` (method: call, receiver: msg), `ERC20Helper.transferFrom(fundsAsset, msg.sender, destination, returnAmount)` (method: transferFrom, receiver: ERC20Helper)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['collateralAsset', 'destination', 'fundsAsset']
- **External calls**: `ERC20Helper.transfer(collateralAsset, msg.sender, swapAmount_)` (low-level .transfer()), `msg.sender.call(data_)` (low-level call on msg.sender/tx.origin), `ERC20Helper.transferFrom(fundsAsset, msg.sender, destination, returnAmount)` (known ERC-like method .transferFrom() on 'ERC20Helper')
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### PrimitiveEngine.withdraw

**Pre-classification**: ⚠️ MISLOCATED
**Reason**: No delegatecall in function — vulnerability may be in a different function

#### 1. SWC Annotation
- **Category**: SWC-112-Delegatecall to Untrusted Callee
- **SWC Code**: SWC-112
- **Annotated Function**: withdraw
- **Line Range**: L223 - L233
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-Primitive/rmm-core-5dcf4306fc32fb9a4e3c154deb86f6b9d513c344/contracts/PrimitiveEngine.sol`
- **Original SWC entry**: category=`SWC-112-Delegatecall to Untrusted Callee`, function=`withdraw`, lines=`L223 - L233`

#### 2. Function Source Code
```solidity
function withdraw(
        address recipient,
        uint256 delRisky,
        uint256 delStable
    ) external override lock {
        if (delRisky == 0 && delStable == 0) revert ZeroDeltasError();
        margins.withdraw(delRisky, delStable); // state update
        if (delRisky != 0) IERC20(risky).safeTransfer(recipient, delRisky);
        if (delStable != 0) IERC20(stable).safeTransfer(recipient, delStable);
        emit Withdraw(msg.sender, recipient, delRisky, delStable);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['margins', 'risky', 'stable']
- **External calls**: `margins.withdraw(delRisky, delStable)` (method: withdraw, receiver: margins), `IERC20(risky).safeTransfer(recipient, delRisky)` (method: safeTransfer, receiver: IERC20), `IERC20(stable).safeTransfer(recipient, delStable)` (method: safeTransfer, receiver: IERC20)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['margins', 'risky', 'stable']
- **External calls**: `margins.withdraw(delRisky, delStable)` (call on contract-typed state var 'margins' (type: mapping(address => Margin.Data))), `IERC20(risky).safeTransfer(recipient, delRisky)` (SafeERC20 .safeTransfer()), `IERC20(stable).safeTransfer(recipient, delStable)` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### Pool.init

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: init
- **Line Range**: L87 - L99
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-YieldProtocol/fyDai-4422fda75931f2bfea49f5041ec90dc026e5c03d/contracts/pool/Pool.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`init`, lines=`L87 - L99`

#### 2. Function Source Code
```solidity
function init(uint128 daiIn)
        external
        beforeMaturity
    {
        require(
            totalSupply() == 0,
            "Pool: Already initialized"
        );
        // no yDai transferred, because initial yDai deposit is entirely virtual
        dai.transferFrom(msg.sender, address(this), daiIn);
        _mint(msg.sender, daiIn);
        emit Liquidity(maturity, msg.sender, msg.sender, -toInt256(daiIn), 0, toInt256(daiIn));
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['dai', 'maturity']
- **External calls**: `dai.transferFrom(msg.sender, address(this), daiIn)` (method: transferFrom, receiver: dai)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['dai', 'maturity']
- **External calls**: `dai.transferFrom(msg.sender, address(this), daiIn)` (call on contract-typed state var 'dai' (type: IERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### Ladle.ality coded in a module, to be used with batch

**Pre-classification**: 🔄 COMMIT_DRIFT
**Reason**: Function not found in current source file

#### 1. SWC Annotation
- **Category**: SWC-112-Delegatecall to Untrusted Callee
- **SWC Code**: SWC-112
- **Annotated Function**: ality coded in a module, to be used with batch
- **Line Range**: L187 - L198
- **File**: `DAppSCAN-source/contracts/Trail_of_Bits-YieldV2/vault-v2-819a713416249da92c44eb629ed26a49425a4656/contracts/Ladle.sol`
- **Original SWC entry**: category=`SWC-112-Delegatecall to Untrusted Callee`, function=`ality coded in a module, to be used with batch`, lines=`L187 - L198`

#### 2. Function Source Code
> ⚠️ **Function source not found** — possible commit drift or file restructuring

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['modules']
- **External calls**: `module.delegatecall(data)` (method: delegatecall, receiver: module)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: []
- **External calls**: None
- **Cross-contract**: False
- **Hyperedge constructable**: False

**Consistency checks:**
- State vars match: ❌
- External calls match: ❌
- Cross-contract match: ❌

### EthUniswapPCVController._swapEth

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _swapEth
- **Line Range**: L123
- **File**: `DAppSCAN-source/contracts/consensys-Fei_Protocol/fei-protocol-core-ff892c5d0b9697f249d713bbb2b3bd1da7980ed2/contracts/pcv/EthUniswapPCVController.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_swapEth`, lines=`L123`

#### 2. Function Source Code
```solidity
function _swapEth(uint amountEth, uint ethReserves, uint feiReserves) internal {
		uint balance = address(this).balance;
		uint amount = Math.min(amountEth, balance);
		
		uint amountOut = UniswapV2Library.getAmountOut(amount, ethReserves, feiReserves);
		
		IWETH weth = IWETH(router.WETH());
		weth.deposit{value: amount}();
		// SWC-104-Unchecked Call Return Value: L123
		weth.transfer(address(pair), amount);

		(uint amount0Out, uint amount1Out) = pair.token0() == address(weth) ? (uint(0), amountOut) : (amountOut, uint(0));
		pair.swap(amount0Out, amount1Out, address(this), new bytes(0));
	}
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['pair', 'router']
- **External calls**: `router.WETH()` (method: WETH, receiver: router), `weth.deposit{value: amount}()` (method: deposit, receiver: weth), `weth.transfer(address(pair), amount)` (method: transfer, receiver: weth), `pair.token0()` (method: token0, receiver: pair), `pair.swap(amount0Out, amount1Out, address(this), new bytes(0))` (method: swap, receiver: pair)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['pair', 'router']
- **External calls**: `router.WETH()` (call on contract-typed state var 'router' (type: IUniswapV2Router02)), `weth.deposit{value: amount}()` (call on contract-typed local var 'weth' (type: IWETH)), `weth.transfer(address(pair), amount)` (low-level .transfer()), `pair.token0()` (call on contract-typed state var 'pair' (type: IUniswapV2Pair)), `pair.swap(amount0Out, amount1Out, address(this), new bytes(0))` (call on contract-typed state var 'pair' (type: IUniswapV2Pair))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### Pool._deposit

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _deposit
- **Line Range**: L121
- **File**: `DAppSCAN-source/contracts/consensys-Fei_Protocol/fei-protocol-core-ff892c5d0b9697f249d713bbb2b3bd1da7980ed2/contracts/pool/Pool.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_deposit`, lines=`L121`

#### 2. Function Source Code
```solidity
function _deposit(address from, address to, uint amount) internal {
		require(initialized, "Pool: Uninitialized");
		require(amount <= stakedToken.balanceOf(from), "Pool: Balance too low to stake");
		// SWC-104-Unchecked Call Return Value: L121
		stakedToken.transferFrom(from, address(this), amount);

		stakedBalance[to] += amount;
		_incrementStaked(amount);
		
		uint poolTokens = _twfb(amount);
		require(poolTokens != 0, "Pool: Window has ended");

		_mint(to, poolTokens);
	}
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['initialized', 'stakedBalance', 'stakedToken']
- **External calls**: `stakedToken.transferFrom(from, address(this), amount)` (method: transferFrom, receiver: stakedToken)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['initialized', 'stakedBalance', 'stakedToken']
- **External calls**: `stakedToken.transferFrom(from, address(this), amount)` (call on contract-typed state var 'stakedToken' (type: IERC20))
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### DynamicLiquidTokenConverter.reduceWeight

**Pre-classification**: ✅ CONFIRMED
**Reason**: State-dependent external call present — front-running plausible

#### 1. SWC Annotation
- **Category**: SWC-114-Transaction Order Dependence
- **SWC Code**: SWC-114
- **Annotated Function**: reduceWeight
- **Line Range**: L124-L132
- **File**: `DAppSCAN-source/contracts/consensys-Zer0_zBanc/zBanc-48da0ac1eebbe31a74742f1ae4281b156f03a4bc/solidity/contracts/converter/types/liquid-token/DynamicLiquidTokenConverter.sol`
- **Original SWC entry**: category=`SWC-114-Transaction Order Dependence`, function=`reduceWeight`, lines=`L124-L132`

#### 2. Function Source Code
```solidity
function reduceWeight(IERC20Token _reserveToken)
        public
        validReserve(_reserveToken)
        ownerOnly
    {
        _protected();
        uint256 currentMarketCap = getMarketCap(_reserveToken);
        require(currentMarketCap > (lastWeightAdjustmentMarketCap.add(marketCapThreshold)), "ERR_MARKET_CAP_BELOW_THRESHOLD");

        Reserve storage reserve = reserves[_reserveToken];
        uint256 newWeight = uint256(reserve.weight).sub(stepWeight);
        uint32 oldWeight = reserve.weight;
        require(newWeight >= minimumWeight, "ERR_INVALID_RESERVE_WEIGHT");

        uint256 percentage = uint256(PPM_RESOLUTION).sub(newWeight.mul(PPM_RESOLUTION).div(reserve.weight));

        uint32 weight = uint32(newWeight);
        reserve.weight = weight;
        reserveRatio = weight;

        uint256 balance = reserveBalance(_reserveToken).mul(percentage).div(PPM_RESOLUTION);

        lastWeightAdjustmentMarketCap = currentMarketCap;

        if (_reserveToken == ETH_RESERVE_ADDRESS)
          msg.sender.transfer(balance);
        else
          safeTransfer(_reserveToken, msg.sender, balance);

        syncReserveBalance(_reserveToken);

        emit ReserveTokenWeightUpdate(oldWeight, weight, percentage, reserve.balance);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['ETH_RESERVE_ADDRESS', 'PPM_RESOLUTION', 'lastWeightAdjustmentMarketCap', 'marketCapThreshold', 'minimumWeight', 'reserveRatio', 'reserves', 'stepWeight']
- **External calls**: `msg.sender.transfer(balance)` (method: transfer, receiver: msg)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['ETH_RESERVE_ADDRESS', 'PPM_RESOLUTION', 'lastWeightAdjustmentMarketCap', 'marketCapThreshold', 'minimumWeight', 'reserveRatio', 'reserves', 'stepWeight']
- **External calls**: `msg.sender.transfer(balance)` (low-level call on msg.sender/tx.origin)
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌

### WMasterChef.burn

**Pre-classification**: ✅ CONFIRMED
**Reason**: Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: burn
- **Line Range**: L63
- **File**: `DAppSCAN-source/contracts/openzeppelin-Alpha_Finance_Homora_V2/alpha-homora-v2-contract-5efa332f2ecf8e9705c326cffda5305bc6f752f7/WMasterChef.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`burn`, lines=`L63`

#### 2. Function Source Code
```solidity
function burn(uint id, uint amount) external nonReentrant returns (uint) {
    if (amount == uint(-1)) {
      amount = balanceOf(msg.sender, id);
    }
    (uint pid, uint stSushiPerShare) = decodeId(id);
    _burn(msg.sender, id, amount);
    chef.withdraw(pid, amount);
    (address lpToken, , , uint enSushiPerShare) = chef.poolInfo(pid);
    IERC20(lpToken).safeTransfer(msg.sender, amount);
    uint stSushi = stSushiPerShare.mul(amount).divCeil(1e12);
    uint enSushi = enSushiPerShare.mul(amount).div(1e12);
    if (enSushi > stSushi) {
      sushi.safeTransfer(msg.sender, enSushi.sub(stSushi));
    }
    return pid;
  }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['chef']
- **External calls**: `chef.poolInfo(pid)` (method: poolInfo, receiver: chef), `IERC20(lpToken).safeTransferFrom(msg.sender, address(this), amount)` (method: safeTransferFrom, receiver: IERC20), `IERC20(lpToken).allowance(address(this), address(chef))` (method: allowance, receiver: IERC20), `IERC20(lpToken).approve(address(chef), uint(-1))` (method: approve, receiver: IERC20), `chef.deposit(pid, amount)` (method: deposit, receiver: chef), `chef.poolInfo(pid)` (method: poolInfo, receiver: chef)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['chef', 'sushi']
- **External calls**: `chef.withdraw(pid, amount)` (call on contract-typed state var 'chef' (type: IMasterChef)), `chef.poolInfo(pid)` (call on contract-typed state var 'chef' (type: IMasterChef)), `IERC20(lpToken).safeTransfer(msg.sender, amount)` (SafeERC20 .safeTransfer()), `sushi.safeTransfer(msg.sender, enSushi.sub(stSushi))` (SafeERC20 .safeTransfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ❌
- External calls match: ❌
- Cross-contract match: ❌

### OVM_L1ERC20Gateway._handleFinalizeWithdrawal

**Pre-classification**: ✅ CONFIRMED
**Reason**: Low-level call found — unchecked return value vulnerability plausible

#### 1. SWC Annotation
- **Category**: SWC-104-Unchecked Call Return Value
- **SWC Code**: SWC-104
- **Annotated Function**: _handleFinalizeWithdrawal
- **Line Range**: L100
- **File**: `DAppSCAN-source/contracts/openzeppelin-Optimism/contracts-18e128343731b9bde23812ce932e24d81440b6b7/contracts/optimistic-ethereum/OVM/bridge/tokens/OVM_L1ERC20Gateway.sol`
- **Original SWC entry**: category=`SWC-104-Unchecked Call Return Value`, function=`_handleFinalizeWithdrawal`, lines=`L100`

#### 2. Function Source Code
```solidity
function _handleFinalizeWithdrawal(
        address _to,
        uint _amount
    )
        internal
        override
    {
        // Transfer withdrawn funds out to withdrawer
        //SWC-104-Unchecked Call Return Value: L100
        l1ERC20.transfer(_to, _amount);
    }
```

#### 3. Hyperedge Components

**Recorded in dataset:**
- **State variables**: ['l1ERC20']
- **External calls**: `l1ERC20.transfer(_to, _amount)` (method: transfer, receiver: l1ERC20)
- **Cross-contract**: False

**Reconstructed from current AST:**
- **State variables**: ['l1ERC20']
- **External calls**: `l1ERC20.transfer(_to, _amount)` (low-level .transfer())
- **Cross-contract**: True
- **Hyperedge constructable**: True

**Consistency checks:**
- State vars match: ✅
- External calls match: ✅
- Cross-contract match: ❌
