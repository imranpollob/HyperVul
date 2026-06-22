// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

// SWC-103-Floating Pragma: L3



// OpenZeppelin Contracts (last updated v5.4.0) (token/ERC20/IERC20.sol)



/**
 * @dev Interface of the ERC-20 standard as defined in the ERC.
 */
interface IERC20 {
    /**
     * @dev Emitted when `value` tokens are moved from one account (`from`) to
     * another (`to`).
     *
     * Note that `value` may be zero.
     */
    event Transfer(address indexed from, address indexed to, uint256 value);

    /**
     * @dev Emitted when the allowance of a `spender` for an `owner` is set by
     * a call to {approve}. `value` is the new allowance.
     */
    event Approval(address indexed owner, address indexed spender, uint256 value);

    /**
     * @dev Returns the value of tokens in existence.
     */
    function totalSupply() external view returns (uint256);

    /**
     * @dev Returns the value of tokens owned by `account`.
     */
    function balanceOf(address account) external view returns (uint256);

    /**
     * @dev Moves a `value` amount of tokens from the caller's account to `to`.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transfer(address to, uint256 value) external returns (bool);

    /**
     * @dev Returns the remaining number of tokens that `spender` will be
     * allowed to spend on behalf of `owner` through {transferFrom}. This is
     * zero by default.
     *
     * This value changes when {approve} or {transferFrom} are called.
     */
    function allowance(address owner, address spender) external view returns (uint256);

    /**
     * @dev Sets a `value` amount of tokens as the allowance of `spender` over the
     * caller's tokens.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * IMPORTANT: Beware that changing an allowance with this method brings the risk
     * that someone may use both the old and the new allowance by unfortunate
     * transaction ordering. One possible solution to mitigate this race
     * condition is to first reduce the spender's allowance to 0 and set the
     * desired value afterwards:
     * https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
     *
     * Emits an {Approval} event.
     */
    function approve(address spender, uint256 value) external returns (bool);

    /**
     * @dev Moves a `value` amount of tokens from `from` to `to` using the
     * allowance mechanism. `value` is then deducted from the caller's
     * allowance.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transferFrom(address from, address to, uint256 value) external returns (bool);
}

// Failed to resolve import: import "./interfaces/IUniswapV2Router.sol";
// Failed to resolve import: import "./interfaces/IUniswapV2Factory.sol";
// Failed to resolve import: import "./interfaces/IUniswapV2Pair.sol";
// Failed to resolve import: import "@openzeppelin/contracts/utils/math/SafeMath.sol";

// OpenZeppelin Contracts (last updated v5.5.0) (utils/ReentrancyGuard.sol)




// OpenZeppelin Contracts (last updated v5.1.0) (utils/StorageSlot.sol)
// This file was procedurally generated from scripts/generate/templates/StorageSlot.js.



/**
 * @dev Library for reading and writing primitive types to specific storage slots.
 *
 * Storage slots are often used to avoid storage conflict when dealing with upgradeable contracts.
 * This library helps with reading and writing to such slots without the need for inline assembly.
 *
 * The functions in this library return Slot structs that contain a `value` member that can be used to read or write.
 *
 * Example usage to set ERC-1967 implementation slot:
 * ```solidity
 * contract ERC1967 {
 *     // Define the slot. Alternatively, use the SlotDerivation library to derive the slot.
 *     bytes32 internal constant _IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
 *
 *     function _getImplementation() internal view returns (address) {
 *         return StorageSlot.getAddressSlot(_IMPLEMENTATION_SLOT).value;
 *     }
 *
 *     function _setImplementation(address newImplementation) internal {
 *         require(newImplementation.code.length > 0);
 *         StorageSlot.getAddressSlot(_IMPLEMENTATION_SLOT).value = newImplementation;
 *     }
 * }
 * ```
 *
 * TIP: Consider using this library along with {SlotDerivation}.
 */
library StorageSlot {
    struct AddressSlot {
        address value;
    }

    struct BooleanSlot {
        bool value;
    }

    struct Bytes32Slot {
        bytes32 value;
    }

    struct Uint256Slot {
        uint256 value;
    }

    struct Int256Slot {
        int256 value;
    }

    struct StringSlot {
        string value;
    }

    struct BytesSlot {
        bytes value;
    }

    /**
     * @dev Returns an `AddressSlot` with member `value` located at `slot`.
     */
    function getAddressSlot(bytes32 slot) internal pure returns (AddressSlot storage r) {
        assembly ("memory-safe") {
            r.slot := slot
        }
    }

    /**
     * @dev Returns a `BooleanSlot` with member `value` located at `slot`.
     */
    function getBooleanSlot(bytes32 slot) internal pure returns (BooleanSlot storage r) {
        assembly ("memory-safe") {
            r.slot := slot
        }
    }

    /**
     * @dev Returns a `Bytes32Slot` with member `value` located at `slot`.
     */
    function getBytes32Slot(bytes32 slot) internal pure returns (Bytes32Slot storage r) {
        assembly ("memory-safe") {
            r.slot := slot
        }
    }

    /**
     * @dev Returns a `Uint256Slot` with member `value` located at `slot`.
     */
    function getUint256Slot(bytes32 slot) internal pure returns (Uint256Slot storage r) {
        assembly ("memory-safe") {
            r.slot := slot
        }
    }

    /**
     * @dev Returns a `Int256Slot` with member `value` located at `slot`.
     */
    function getInt256Slot(bytes32 slot) internal pure returns (Int256Slot storage r) {
        assembly ("memory-safe") {
            r.slot := slot
        }
    }

    /**
     * @dev Returns a `StringSlot` with member `value` located at `slot`.
     */
    function getStringSlot(bytes32 slot) internal pure returns (StringSlot storage r) {
        assembly ("memory-safe") {
            r.slot := slot
        }
    }

    /**
     * @dev Returns an `StringSlot` representation of the string storage pointer `store`.
     */
    function getStringSlot(string storage store) internal pure returns (StringSlot storage r) {
        assembly ("memory-safe") {
            r.slot := store.slot
        }
    }

    /**
     * @dev Returns a `BytesSlot` with member `value` located at `slot`.
     */
    function getBytesSlot(bytes32 slot) internal pure returns (BytesSlot storage r) {
        assembly ("memory-safe") {
            r.slot := slot
        }
    }

    /**
     * @dev Returns an `BytesSlot` representation of the bytes storage pointer `store`.
     */
    function getBytesSlot(bytes storage store) internal pure returns (BytesSlot storage r) {
        assembly ("memory-safe") {
            r.slot := store.slot
        }
    }
}


/**
 * @dev Contract module that helps prevent reentrant calls to a function.
 *
 * Inheriting from `ReentrancyGuard` will make the {nonReentrant} modifier
 * available, which can be applied to functions to make sure there are no nested
 * (reentrant) calls to them.
 *
 * Note that because there is a single `nonReentrant` guard, functions marked as
 * `nonReentrant` may not call one another. This can be worked around by making
 * those functions `private`, and then adding `external` `nonReentrant` entry
 * points to them.
 *
 * TIP: If EIP-1153 (transient storage) is available on the chain you're deploying at,
 * consider using {ReentrancyGuardTransient} instead.
 *
 * TIP: If you would like to learn more about reentrancy and alternative ways
 * to protect against it, check out our blog post
 * https://blog.openzeppelin.com/reentrancy-after-istanbul/[Reentrancy After Istanbul].
 *
 * IMPORTANT: Deprecated. This storage-based reentrancy guard will be removed and replaced
 * by the {ReentrancyGuardTransient} variant in v6.0.
 *
 * @custom:stateless
 */
abstract contract ReentrancyGuard {
    using StorageSlot for bytes32;

    // keccak256(abi.encode(uint256(keccak256("openzeppelin.storage.ReentrancyGuard")) - 1)) & ~bytes32(uint256(0xff))
    bytes32 private constant REENTRANCY_GUARD_STORAGE =
        0x9b779b17422d0df92223018b32b4d1fa46e071723d6817e2486d003becc55f00;

    // Booleans are more expensive than uint256 or any type that takes up a full
    // word because each write operation emits an extra SLOAD to first read the
    // slot's contents, replace the bits taken up by the boolean, and then write
    // back. This is the compiler's defense against contract upgrades and
    // pointer aliasing, and it cannot be disabled.

    // The values being non-zero value makes deployment a bit more expensive,
    // but in exchange the refund on every call to nonReentrant will be lower in
    // amount. Since refunds are capped to a percentage of the total
    // transaction's gas, it is best to keep them low in cases like this one, to
    // increase the likelihood of the full refund coming into effect.
    uint256 private constant NOT_ENTERED = 1;
    uint256 private constant ENTERED = 2;

    /**
     * @dev Unauthorized reentrant call.
     */
    error ReentrancyGuardReentrantCall();

    constructor() {
        _reentrancyGuardStorageSlot().getUint256Slot().value = NOT_ENTERED;
    }

    /**
     * @dev Prevents a contract from calling itself, directly or indirectly.
     * Calling a `nonReentrant` function from another `nonReentrant`
     * function is not supported. It is possible to prevent this from happening
     * by making the `nonReentrant` function external, and making it call a
     * `private` function that does the actual work.
     */
    modifier nonReentrant() {
        _nonReentrantBefore();
        _;
        _nonReentrantAfter();
    }

    /**
     * @dev A `view` only version of {nonReentrant}. Use to block view functions
     * from being called, preventing reading from inconsistent contract state.
     *
     * CAUTION: This is a "view" modifier and does not change the reentrancy
     * status. Use it only on view functions. For payable or non-payable functions,
     * use the standard {nonReentrant} modifier instead.
     */
    modifier nonReentrantView() {
        _nonReentrantBeforeView();
        _;
    }

    function _nonReentrantBeforeView() private view {
        if (_reentrancyGuardEntered()) {
            revert ReentrancyGuardReentrantCall();
        }
    }

    function _nonReentrantBefore() private {
        // On the first call to nonReentrant, _status will be NOT_ENTERED
        _nonReentrantBeforeView();

        // Any calls to nonReentrant after this point will fail
        _reentrancyGuardStorageSlot().getUint256Slot().value = ENTERED;
    }

    function _nonReentrantAfter() private {
        // By storing the original value once again, a refund is triggered (see
        // https://eips.ethereum.org/EIPS/eip-2200)
        _reentrancyGuardStorageSlot().getUint256Slot().value = NOT_ENTERED;
    }

    /**
     * @dev Returns true if the reentrancy guard is currently set to "entered", which indicates there is a
     * `nonReentrant` function in the call stack.
     */
    function _reentrancyGuardEntered() internal view returns (bool) {
        return _reentrancyGuardStorageSlot().getUint256Slot().value == ENTERED;
    }

    function _reentrancyGuardStorageSlot() internal pure virtual returns (bytes32) {
        return REENTRANCY_GUARD_STORAGE;
    }
}


// OpenZeppelin Contracts (last updated v5.0.0) (access/Ownable.sol)




// OpenZeppelin Contracts (last updated v5.0.1) (utils/Context.sol)



/**
 * @dev Provides information about the current execution context, including the
 * sender of the transaction and its data. While these are generally available
 * via msg.sender and msg.data, they should not be accessed in such a direct
 * manner, since when dealing with meta-transactions the account sending and
 * paying for execution may not be the actual sender (as far as an application
 * is concerned).
 *
 * This contract is only required for intermediate, library-like contracts.
 */
abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes calldata) {
        return msg.data;
    }

    function _contextSuffixLength() internal view virtual returns (uint256) {
        return 0;
    }
}


/**
 * @dev Contract module which provides a basic access control mechanism, where
 * there is an account (an owner) that can be granted exclusive access to
 * specific functions.
 *
 * The initial owner is set to the address provided by the deployer. This can
 * later be changed with {transferOwnership}.
 *
 * This module is used through inheritance. It will make available the modifier
 * `onlyOwner`, which can be applied to your functions to restrict their use to
 * the owner.
 */
abstract contract Ownable is Context {
    address private _owner;

    /**
     * @dev The caller account is not authorized to perform an operation.
     */
    error OwnableUnauthorizedAccount(address account);

    /**
     * @dev The owner is not a valid owner account. (eg. `address(0)`)
     */
    error OwnableInvalidOwner(address owner);

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    /**
     * @dev Initializes the contract setting the address provided by the deployer as the initial owner.
     */
    constructor(address initialOwner) {
        if (initialOwner == address(0)) {
            revert OwnableInvalidOwner(address(0));
        }
        _transferOwnership(initialOwner);
    }

    /**
     * @dev Throws if called by any account other than the owner.
     */
    modifier onlyOwner() {
        _checkOwner();
        _;
    }

    /**
     * @dev Returns the address of the current owner.
     */
    function owner() public view virtual returns (address) {
        return _owner;
    }

    /**
     * @dev Throws if the sender is not the owner.
     */
    function _checkOwner() internal view virtual {
        if (owner() != _msgSender()) {
            revert OwnableUnauthorizedAccount(_msgSender());
        }
    }

    /**
     * @dev Leaves the contract without owner. It will not be possible to call
     * `onlyOwner` functions. Can only be called by the current owner.
     *
     * NOTE: Renouncing ownership will leave the contract without an owner,
     * thereby disabling any functionality that is only available to the owner.
     */
    function renounceOwnership() public virtual onlyOwner {
        _transferOwnership(address(0));
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Can only be called by the current owner.
     */
    function transferOwnership(address newOwner) public virtual onlyOwner {
        if (newOwner == address(0)) {
            revert OwnableInvalidOwner(address(0));
        }
        _transferOwnership(newOwner);
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Internal function without access restriction.
     */
    function _transferOwnership(address newOwner) internal virtual {
        address oldOwner = _owner;
        _owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}


interface GetDataInterface {
    function returnData()
        external
        view
        returns (
            uint256,
            uint256,
            uint256
        );
}

interface TreasuryInterface{
    function send(address,uint256) external;
}

contract BUSDVYNCSTAKE is ReentrancyGuard, Ownable {
    using SafeMath for uint256;

    address public dataAddress = 0x994Bde430BA69b96Ce14824c7d848c996A09Ba67;
    GetDataInterface data = GetDataInterface(dataAddress);
    address public TreasuryAddress= 0xA4FE6E8150770132c32e4204C2C1Ff59783eDfA0;
    TreasuryInterface treasury = TreasuryInterface(TreasuryAddress);

    struct stakeInfoData {
        uint256 compoundStart;
        bool isCompoundStartSet;
    }

    struct userInfoData {
        uint256 lpAmount;
        uint256 stakeBalanceWithReward;
        uint256 stakeBalance;
        uint256 lastClaimedReward;
        uint256 lastStakeUnstakeTimestamp;
        uint256 lastClaimTimestamp;
        bool isStaker;
        uint256 totalClaimedReward;
        uint256 autoClaimWithStakeUnstake;
        uint256 pendingRewardAfterFullyUnstake;
        bool isClaimAferUnstake;
        uint256 nextCompoundDuringStakeUnstake;
        uint256 nextCompoundDuringClaim;
        uint256 lastCompoundedRewardWithStakeUnstakeClaim;
    }

    IERC20 public vync = IERC20(0x71BE9BA58e0271b967a980eD8e59C07fF2108C85);
    IERC20 public busd = IERC20(0xB57ab40Db50284f9F9e7244289eD57537262e147);
    IUniswapV2Router02 public router =
        IUniswapV2Router02(0x9Ac64Cc6e4415144C455BD8E4837Fea55603e5c3);
    IUniswapV2Factory public factory =
        IUniswapV2Factory(0xB7926C0430Afb07AA7DEfDE6DA862aE0Bde767bc);

    address lpToken = 0x265c77B2FbD3e10A2Ce3f7991854c80F3eCc9089;
    uint256 public constant MAX_INT =
        115792089237316195423570985008687907853269984665640564039457584007913129639935;
    mapping(address => userInfoData) public userInfo;
    stakeInfoData public stakeInfo;
    uint256 s; // total staking amount
    uint256 u; //total unstaking amount
    uint256 public totalSupply;

    event rewardClaim(address indexed user, uint256 rewards);
    event Stake(address account, uint256 stakeAmount);
    event UnStake(address account, uint256 unStakeAmount);

    constructor() {
        stakeInfo.compoundStart = block.timestamp;
    }

    function set_compoundStart(uint256 _blocktime) public onlyOwner {
        require(stakeInfo.isCompoundStartSet == false, "already set once");
        stakeInfo.compoundStart = _blocktime;
        stakeInfo.isCompoundStartSet = true;
    }

    function set_data(address _data) public onlyOwner {
        dataAddress = _data;
        data = GetDataInterface(_data);
    }

    function set_treasuryAddress(address _treasury) public onlyOwner{
        TreasuryAddress= _treasury;
        treasury = TreasuryInterface(_treasury);
    }

    function nextCompound() public view returns (uint256 _nextCompound) {
        (, uint256 compoundRate, ) = data.returnData();
        uint256 interval = block.timestamp - stakeInfo.compoundStart;
        interval = interval / compoundRate;
        _nextCompound =
            stakeInfo.compoundStart +
            compoundRate +
            interval *
            compoundRate;
    }

    function approve() public {
        vync.approve(address(router), MAX_INT);
        busd.approve(address(router), MAX_INT);
        getSwappingPair().approve(address(router), MAX_INT);
    }



    
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

        (, uint256 res1, ) = getSwappingPair().getReserves();
        uint256 amountToSwap = calculateSwapInAmount(res1, amount);

        uint256 vyncOut = swapBusdToVync(amountToSwap);
        uint256 amountLeft = amount.sub(amountToSwap);
        // SWC-104-Unchecked Call Return Value: L154
        (, uint256 busdAdded, uint256 liquidityAmount) = router.addLiquidity(
            address(vync),
            address(busd),
            vyncOut,
            amountLeft,
            0,
            0,
            address(this),
            block.timestamp
        );

        //update state
        userInfo[msg.sender].lpAmount = userInfo[msg.sender].lpAmount.add(
            liquidityAmount
        );
        totalSupply = totalSupply.add(liquidityAmount);
        userInfo[msg.sender].stakeBalanceWithReward =
            userInfo[msg.sender].stakeBalanceWithReward +
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
        //remove liquidity
        (uint256 amountVync, uint256 amountBusd) = removeLiquidity(
            lpAmountNeeded
        );

        uint256 _amount = swapVyncToBusd(amountVync).add(amountBusd);

        if (unstakeOption == 1) {
            busd.transfer(msg.sender, _amount);
        } else if (unstakeOption == 2) {
            uint256 busdAmount = (_amount * up) / 100;
            uint256 vyncAmount = _amount - busdAmount;

            uint256 _vyncAmount = swapBusdToVync(vyncAmount);
            busd.transfer(msg.sender, busdAmount);
            vync.transfer(msg.sender, _vyncAmount);
        } else if (unstakeOption == 3) {
            uint256 vyncAmount = swapBusdToVync(_amount);
            vync.transfer(msg.sender, vyncAmount);
        }

        emit UnStake(msg.sender, amount);

        // reward update
        if (amount < stakeBalance) {
            uint256 _pendingReward = compoundedReward(msg.sender);

            userInfo[msg.sender]
                .lastCompoundedRewardWithStakeUnstakeClaim = lastCompoundedReward(
                msg.sender
            );

            userInfo[msg.sender].autoClaimWithStakeUnstake = _pendingReward;

            // update state

            userInfo[msg.sender].lastStakeUnstakeTimestamp = block.timestamp;
            userInfo[msg.sender]
                .nextCompoundDuringStakeUnstake = nextCompound();
            userInfo[msg.sender].totalClaimedReward = 0;

            userInfo[msg.sender].lpAmount = userInfo[msg.sender].lpAmount.sub(
                lpAmountNeeded
            );
            userInfo[msg.sender].stakeBalanceWithReward = userInfo[msg.sender]
                .stakeBalanceWithReward
                .sub(_amount);
            userInfo[msg.sender].stakeBalance = userInfo[msg.sender]
                .stakeBalance
                .sub(amount);
            u = u + amount;
        }

        if (amount >= stakeBalance) {
            u = u + stakeBalance;
            userInfo[msg.sender].pendingRewardAfterFullyUnstake = pending;
            userInfo[msg.sender].isClaimAferUnstake = true;
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



    function cPendingReward(address user)
        internal
        view
        returns (uint256 _compoundedReward)
    {
        uint256 reward;
        if (
            userInfo[user].lastClaimTimestamp <
            userInfo[user].nextCompoundDuringStakeUnstake &&
            userInfo[user].lastStakeUnstakeTimestamp <
            userInfo[user].nextCompoundDuringStakeUnstake
        ) {
            (uint256 a, , ) = data.returnData();
            (, uint256 compoundRate, ) = data.returnData();
            a = a / compoundRate;
            uint256 tsec = userInfo[user].nextCompoundDuringStakeUnstake -
                userInfo[user].lastStakeUnstakeTimestamp;
            uint256 stakeSec = block.timestamp -
                userInfo[user].lastStakeUnstakeTimestamp;
            uint256 sec = tsec > stakeSec ? stakeSec : tsec;
            uint256 balance = userInfo[user].stakeBalanceWithReward;
            reward = (balance.mul(a)).div(100);
            reward = reward / 1e18;
            _compoundedReward = reward * sec;
        }
    }



    function compoundedReward(address user)
        public
        view
        returns (uint256 _compoundedReward)
    {
        uint256 nextcompound = userInfo[user].nextCompoundDuringStakeUnstake;
        (, uint256 compoundRate, ) = data.returnData();
        uint256 compoundTime = block.timestamp > nextcompound
            ? block.timestamp - nextcompound
            : 0;
        uint256 loopRound = compoundTime / compoundRate;
        uint256 reward = 0;
        if (userInfo[user].isStaker == false) {
            loopRound = 0;
        }
        (uint256 a, , ) = data.returnData();
        _compoundedReward = 0;
        uint256 cpending = cPendingReward(user);
        uint256 balance = userInfo[user].stakeBalanceWithReward + cpending;

        for (uint256 i = 1; i <= loopRound; i++) {
            uint256 amount = balance.add(reward);
            reward = (amount.mul(a)).div(100);
            reward = reward / 1e18;
            _compoundedReward = _compoundedReward.add(reward);
            balance = amount;
        }

        if (_compoundedReward != 0) {
            uint256 sum = _compoundedReward +
                userInfo[user].autoClaimWithStakeUnstake;
            _compoundedReward = sum > userInfo[user].totalClaimedReward
                ? sum - userInfo[user].totalClaimedReward
                : 0;
            _compoundedReward = _compoundedReward + cPendingReward(user);
        }

        if (_compoundedReward == 0) {
            _compoundedReward = userInfo[user].autoClaimWithStakeUnstake;

            if (
                block.timestamp > userInfo[user].nextCompoundDuringStakeUnstake
            ) {
                _compoundedReward = _compoundedReward + cPendingReward(user);
            }
        }

        if (userInfo[user].isClaimAferUnstake == true) {
            _compoundedReward =
                _compoundedReward +
                userInfo[user].pendingRewardAfterFullyUnstake;
        }
    }

    function compoundedRewardInVync(address user)
        public
        view
        returns (uint256 _compoundedVyncReward)
    {
        uint256 reward;
        reward = compoundedReward(user);
        reward = reward * vyncPerBusd();
        _compoundedVyncReward = reward / 1e18;
    }



    function pendingReward(address user)
        public
        view
        returns (uint256 _pendingReward)
    {
        uint256 nextcompound = userInfo[user].nextCompoundDuringStakeUnstake;
        (, uint256 compoundRate, ) = data.returnData();
        uint256 compoundTime = block.timestamp > nextcompound
            ? block.timestamp - nextcompound
            : 0;
        uint256 loopRound = compoundTime / compoundRate;
        uint256 reward = 0;
        (uint256 a, , ) = data.returnData();
        if (userInfo[user].isStaker == false) {
            loopRound = 0;
        }
        _pendingReward = 0;
        uint256 cpending = cPendingReward(user);
        uint256 balance = userInfo[user].stakeBalanceWithReward + cpending;

        for (uint256 i = 1; i <= loopRound + 1; i++) {
            uint256 amount = balance.add(reward);
            reward = (amount.mul(a)).div(100);
            reward = reward / 1e18;
            _pendingReward = _pendingReward.add(reward);
            balance = amount;
        }

        if (_pendingReward != 0) {
            _pendingReward =
                _pendingReward -
                userInfo[user].totalClaimedReward +
                userInfo[user].autoClaimWithStakeUnstake +
                cPendingReward(user);

            if (
                block.timestamp < userInfo[user].nextCompoundDuringStakeUnstake
            ) {
                _pendingReward =
                    userInfo[user].autoClaimWithStakeUnstake +
                    cPendingReward(user);
            }
        }

        if (userInfo[user].isClaimAferUnstake == true) {
            _pendingReward =
                _pendingReward +
                userInfo[user].pendingRewardAfterFullyUnstake;
        }

        _pendingReward = _pendingReward - compoundedReward(user);
    }

    function pendingRewardInVync(address user)
        public
        view
        returns (uint256 _pendingVyncReward)
    {
        uint256 reward;
        reward = pendingReward(user);
        reward = reward * vyncPerBusd();
        _pendingVyncReward = reward / 1e18;
    }



    function lastCompoundedReward(address user)
        public
        view
        returns (uint256 _compoundedReward)
    {
        uint256 nextcompound = userInfo[user].nextCompoundDuringStakeUnstake;
        (, uint256 compoundRate, ) = data.returnData();
        uint256 compoundTime = block.timestamp > nextcompound
            ? block.timestamp - nextcompound
            : 0;
        compoundTime = compoundTime > compoundRate
            ? compoundTime - compoundRate
            : 0;
        uint256 loopRound = compoundTime / compoundRate;
        uint256 reward = 0;
        if (userInfo[user].isStaker == false) {
            loopRound = 0;
        }
        (uint256 a, , ) = data.returnData();
        _compoundedReward = 0;
        uint256 cpending = cPendingReward(user);
        uint256 balance = userInfo[user].stakeBalanceWithReward + cpending;

        for (uint256 i = 1; i <= loopRound; i++) {
            uint256 amount = balance.add(reward);
            reward = (amount.mul(a)).div(100);
            reward = reward / 1e18;
            _compoundedReward = _compoundedReward.add(reward);
            balance = amount;
        }

        if (_compoundedReward != 0) {
            uint256 sum = _compoundedReward +
                userInfo[user].autoClaimWithStakeUnstake;
            _compoundedReward = sum > userInfo[user].totalClaimedReward
                ? sum - userInfo[user].totalClaimedReward
                : 0;
            _compoundedReward = _compoundedReward + cPendingReward(user);
        }

        if (_compoundedReward == 0) {
            _compoundedReward = userInfo[user].autoClaimWithStakeUnstake;

            if (
                block.timestamp >
                userInfo[user].nextCompoundDuringStakeUnstake + compoundRate
            ) {
                _compoundedReward = _compoundedReward + cPendingReward(user);
            }
        }

        if (userInfo[user].isClaimAferUnstake == true) {
            _compoundedReward =
                _compoundedReward +
                userInfo[user].pendingRewardAfterFullyUnstake;
        }

        uint256 result = compoundedReward(user) - _compoundedReward;

        if (
            block.timestamp < userInfo[user].nextCompoundDuringStakeUnstake ||
            block.timestamp < userInfo[user].nextCompoundDuringClaim
        ) {
            result =
                result +
                userInfo[user].lastCompoundedRewardWithStakeUnstakeClaim;
        }

        _compoundedReward = result;
    }



    function rewardCalculation(address user) internal {
        (, uint256 compoundRate, ) = data.returnData();
        uint256 nextcompound = userInfo[user].nextCompoundDuringStakeUnstake;
        uint256 compoundTime = block.timestamp > nextcompound
            ? block.timestamp - nextcompound
            : 0;
        uint256 loopRound = compoundTime / compoundRate;
        (uint256 a, , ) = data.returnData();
        uint256 reward;
        if (userInfo[user].isStaker == false) {
            loopRound = 0;
        }
        uint256 totalReward;
        uint256 cpending = cPendingReward(user);
        uint256 balance = userInfo[user].stakeBalanceWithReward + cpending;

        for (uint256 i = 1; i <= loopRound; i++) {
            uint256 amount = balance.add(reward);
            reward = (amount.mul(a)).div(100);
            reward = reward / 1e18;
            totalReward = totalReward.add(reward);
            balance = amount;
        }

        if (userInfo[user].isClaimAferUnstake == true) {
            totalReward =
                totalReward +
                userInfo[user].pendingRewardAfterFullyUnstake;
        }
        totalReward = totalReward + cPendingReward(user);
        userInfo[user].lastClaimedReward =
            totalReward -
            userInfo[user].totalClaimedReward;
        userInfo[user].totalClaimedReward =
            userInfo[user].totalClaimedReward +
            userInfo[user].lastClaimedReward -
            cPendingReward(user);
    }



    
    function claim() public nonReentrant {
        require(
            userInfo[msg.sender].isStaker == true ||
                userInfo[msg.sender].isClaimAferUnstake == true,
            "user not staked"
        );
        userInfo[msg.sender]
            .lastCompoundedRewardWithStakeUnstakeClaim = lastCompoundedReward(
            msg.sender
        );

        rewardCalculation(msg.sender);
        uint256 reward = userInfo[msg.sender].lastClaimedReward +
            userInfo[msg.sender].autoClaimWithStakeUnstake;
        require(reward > 0, "can't reap zero reward");
        uint256 _vyncPerBusd = vyncPerBusd();
        reward = reward * _vyncPerBusd;
        reward = reward / 1e18;

        treasury.send(msg.sender,reward);
        emit rewardClaim(msg.sender, reward);
        userInfo[msg.sender].autoClaimWithStakeUnstake = 0;
        userInfo[msg.sender].lastClaimTimestamp = block.timestamp;
        userInfo[msg.sender].nextCompoundDuringClaim = nextCompound();

        if (
            userInfo[msg.sender].isClaimAferUnstake == true &&
            userInfo[msg.sender].isStaker == false
        ) {
            userInfo[msg.sender].lastStakeUnstakeTimestamp = 0;
            userInfo[msg.sender].lastClaimedReward = 0;
            userInfo[msg.sender].totalClaimedReward = 0;
        }

        if (
            userInfo[msg.sender].isClaimAferUnstake == true &&
            userInfo[msg.sender].isStaker == true
        ) {
            userInfo[msg.sender].totalClaimedReward =
                userInfo[msg.sender].totalClaimedReward -
                userInfo[msg.sender].pendingRewardAfterFullyUnstake;
        }
        bool isClaim = userInfo[msg.sender].isClaimAferUnstake;
        if (isClaim == true) {
            userInfo[msg.sender].pendingRewardAfterFullyUnstake = 0;
            userInfo[msg.sender].isClaimAferUnstake = false;
        }
    }




    function vyncPerBusd() public view returns (uint256 _vyncPerBusd) {
        uint256 _busd = busd.balanceOf(lpToken);
        uint256 _vync = vync.balanceOf(lpToken);
        _vync = _vync * 1e18;

        _vyncPerBusd = _vync / _busd;
    }

    function vyncRateInBusd() public view returns (uint256 _vyncRateInBusd) {
        uint256 _busd = busd.balanceOf(lpToken);
        uint256 _vync = vync.balanceOf(lpToken);
        _vync = _vync / 1e4;

        _vyncRateInBusd = _busd / _vync;
    }

    function totalStake() external view returns (uint256 stakingAmount) {
        stakingAmount = s;
    }

    function totalUnstake() external view returns (uint256 unstakingAmount) {
        unstakingAmount = u;
    }

    function transferAnyERC20Token(address _tokenAddress, address _to, uint _amount) public onlyOwner {
        require(_tokenAddress != lpToken, "can't withdraw lp tokens");
        IERC20(_tokenAddress).transfer(_to, _amount);
    }

    function getSwappingPair() internal view returns (IUniswapV2Pair) {
        return IUniswapV2Pair(factory.getPair(address(vync), address(busd)));
    }

    // following: https://blog.alphafinance.io/onesideduniswap/ zzb
    // applying f = 0.25% in PancakeSwap
    // we got these numbers

    function calculateSwapInAmount(uint256 reserveIn, uint256 userIn)
        internal
        pure
        returns (uint256)
    {
        return
            sqrt(
                reserveIn.mul(userIn.mul(399000000) + reserveIn.mul(399000625))
            ).sub(reserveIn.mul(19975)) / 19950;
    }

    function sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
        // else z = 0
    }

    function swapBusdToVync(uint256 amountToSwap)
        internal
        returns (uint256 amountOut)
    {
        uint256 vyncBalanceBefore = vync.balanceOf(address(this));
        router.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            amountToSwap,
            0,
            getBusdVyncRoute(),
            address(this),
            block.timestamp
        );
        amountOut = vync.balanceOf(address(this)).sub(vyncBalanceBefore);
    }

    function swapVyncToBusd(uint256 amountToSwap)
        internal
        returns (uint256 amountOut)
    {
        uint256 busdBalanceBefore = busd.balanceOf(address(this)); // remove for testing
        router.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            amountToSwap,
            0,
            getVyncBusdRoute(),
            address(this),
            block.timestamp
        );
        amountOut = busd.balanceOf(address(this)).sub(busdBalanceBefore);
    }

    function getBusdVyncRoute() private view returns (address[] memory paths) {
        paths = new address[](2);
        paths[0] = address(busd);
        paths[1] = address(vync);
    }

    function getVyncBusdRoute() private view returns (address[] memory paths) {
        paths = new address[](2);
        paths[0] = address(vync);
        paths[1] = address(busd);
    }

    function getReserveInAmount1ByLP(uint256 lp)
        private
        view
        returns (uint256 amount)
    {
        IUniswapV2Pair pair = getSwappingPair();
        uint256 balance0 = vync.balanceOf(address(pair));
        uint256 balance1 = busd.balanceOf(address(pair));
        uint256 _totalSupply = pair.totalSupply();
        uint256 amount0 = lp.mul(balance0) / _totalSupply;
        uint256 amount1 = lp.mul(balance1) / _totalSupply;
        // convert amount0 -> amount1
        amount = amount1.add(amount0.mul(balance1).div(balance0));
    }

    function balanceOf(address user) public view returns (uint256) {
        return getReserveInAmount1ByLP(userInfo[user].lpAmount);
    }

    function getLPTokenByAmount1(uint256 amount)
        internal
        view
        returns (uint256 lpNeeded)
    {
        (, uint256 res1, ) = getSwappingPair().getReserves();
        lpNeeded = amount.mul(getSwappingPair().totalSupply()).div(res1).div(2);
    }

    function removeLiquidity(uint256 lpAmount)
        internal
        returns (uint256 amountVync, uint256 amountBusd)
    {
        uint256 vyncBalanceBefore = vync.balanceOf(address(this));
        (, amountBusd) = router.removeLiquidity(
            address(vync),
            address(busd),
            lpAmount,
            0,
            0,
            address(this),
            block.timestamp
        );
        amountVync = vync.balanceOf(address(this)).sub(vyncBalanceBefore);
    }
}