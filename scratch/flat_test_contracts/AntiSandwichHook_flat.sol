// SPDX-License-Identifier: MIT
pragma solidity 0.8.11;

// OpenZeppelin Uniswap Hooks (last updated v1.1.0) (src/general/AntiSandwichHook.sol)



// Internal imports

// OpenZeppelin Uniswap Hooks (last updated v0.1.0) (src/fee/BaseDynamicAfterFee.sol)




// OpenZeppelin Uniswap Hooks (last updated v0.1.0) (src/base/BaseHook.sol)






/// Modified from v4-core's IHooks interface.








// OpenZeppelin Contracts (last updated v5.4.0) (interfaces/IERC20.sol)




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



type Currency is address;

using {greaterThan as >, lessThan as <, greaterThanOrEqualTo as >=, equals as ==} for Currency global;
using CurrencyLibrary for Currency global;

function equals(Currency currency, Currency other) pure returns (bool) {
    return Currency.unwrap(currency) == Currency.unwrap(other);
}

function greaterThan(Currency currency, Currency other) pure returns (bool) {
    return Currency.unwrap(currency) > Currency.unwrap(other);
}

function lessThan(Currency currency, Currency other) pure returns (bool) {
    return Currency.unwrap(currency) < Currency.unwrap(other);
}

function greaterThanOrEqualTo(Currency currency, Currency other) pure returns (bool) {
    return Currency.unwrap(currency) >= Currency.unwrap(other);
}

/// @title CurrencyLibrary
/// @dev This library allows for transferring and holding native tokens and ERC20 tokens
library CurrencyLibrary {
    /// @notice Additional context for ERC-7751 wrapped error when a native transfer fails
    error NativeTransferFailed();

    /// @notice Additional context for ERC-7751 wrapped error when an ERC20 transfer fails
    error ERC20TransferFailed();

    /// @notice A constant to represent the native currency
    Currency public constant ADDRESS_ZERO = Currency.wrap(address(0));

    function transfer(Currency currency, address to, uint256 amount) internal {
        // altered from https://github.com/transmissions11/solmate/blob/44a9963d4c78111f77caa0e65d677b8b46d6f2e6/src/utils/SafeTransferLib.sol
        // modified custom error selectors

        bool success;
        if (currency.isAddressZero()) {
            assembly {
                // Transfer the ETH and revert if it fails.
                success := call(gas(), to, amount, 0, 0, 0, 0)
            }
            if (!success) {
                revert NativeTransferFailed();
            }
        } else {
            assembly {
                // Get a pointer to some free memory.
                let fmp := mload(0x40)

                // Write the abi-encoded calldata into memory, beginning with the function selector.
                mstore(fmp, 0xa9059cbb00000000000000000000000000000000000000000000000000000000)
                mstore(add(fmp, 4), and(to, 0xffffffffffffffffffffffffffffffffffffffff)) // Append and mask the "to" argument.
                mstore(add(fmp, 36), amount) // Append the "amount" argument. Masking not required as it's a full 32 byte type.

                success :=
                    and(
                        // Set success to whether the call reverted, if not we check it either
                        // returned exactly 1 (can't just be non-zero data), or had no return data.
                        or(and(eq(mload(0), 1), gt(returndatasize(), 31)), iszero(returndatasize())),
                        // We use 68 because the length of our calldata totals up like so: 4 + 32 * 2.
                        // We use 0 and 32 to copy up to 32 bytes of return data into the scratch space.
                        // Counterintuitively, this call must be positioned second to the or() call in the
                        // surrounding and() call or else returndatasize() will be zero during the computation.
                        call(gas(), currency, 0, fmp, 68, 0, 32)
                    )

                // Now clean the memory we used
                mstore(fmp, 0) // 4 byte `selector` and 28 bytes of `to` were stored here
                mstore(add(fmp, 0x20), 0) // 4 bytes of `to` and 28 bytes of `amount` were stored here
                mstore(add(fmp, 0x40), 0) // 4 bytes of `amount` were stored here
            }
            if (!success) {
                revert ERC20TransferFailed();
            }
        }
    }

    function balanceOfSelf(Currency currency) internal view returns (uint256) {
        if (currency.isAddressZero()) {
            return address(this).balance;
        } else {
            return IERC20(Currency.unwrap(currency)).balanceOf(address(this));
        }
    }

    function balanceOf(Currency currency, address owner) internal view returns (uint256) {
        if (currency.isAddressZero()) {
            return owner.balance;
        } else {
            return IERC20(Currency.unwrap(currency)).balanceOf(owner);
        }
    }

    function isAddressZero(Currency currency) internal pure returns (bool) {
        return Currency.unwrap(currency) == Currency.unwrap(ADDRESS_ZERO);
    }

    function toId(Currency currency) internal pure returns (uint256) {
        return uint160(Currency.unwrap(currency));
    }

    // If the upper 12 bytes are non-zero, they will be zero-ed out
    // Therefore, fromId() and toId() are not inverses of each other
    function fromId(uint256 id) internal pure returns (Currency) {
        return Currency.wrap(address(uint160(id)));
    }
}






type PoolId is bytes32;

/// @notice Library for computing the ID of a pool
library PoolIdLibrary {
    /// @notice Returns value equal to keccak256(abi.encode(poolKey))
    function toId(PoolKey memory poolKey) internal pure returns (PoolId poolId) {
        assembly {
            // 0x60 represents the total size of the poolKey struct (3 slots of 32 bytes)
            poolId := keccak256(poolKey, 0x60)
        }
    }
}


using PoolIdLibrary for PoolKey global;

/// @notice Returns the key for identifying a pool
struct PoolKey {
    /// @notice The lower currency of the pool, sorted numerically
    Currency currency0;
    /// @notice The higher currency of the pool, sorted numerically
    Currency currency1;
    /// @notice The pool LP fee, capped at 1_000_000. E.g., 0.3% = 3_000
    uint24 fee;
}







/// @title Safe casting methods
/// @notice Contains methods for safely casting between types
library SafeCast {
    error SafeCastOverflow();

    /**
     * @dev Cast a boolean (false or true) to a uint256 (0 or 1) with no jump.
     */
    function toUint(bool b) internal pure returns (uint256 u) {
        assembly {
            u := iszero(iszero(b))
        }
    }

    /// @notice Cast a uint256 to a uint160, revert on overflow
    /// @param x The uint256 to be downcasted
    /// @return y The downcasted integer, now type uint160
    function toUint160(uint256 x) internal pure returns (uint160 y) {
        y = uint160(x);
        if (y != x) revert SafeCastOverflow();
    }

    /// @notice Cast a uint256 to a uint128, revert on overflow
    /// @param x The uint256 to be downcasted
    /// @return y The downcasted integer, now type uint128
    function toUint128(uint256 x) internal pure returns (uint128 y) {
        y = uint128(x);
        if (x != y) revert SafeCastOverflow();
    }

    /// @notice Cast a int128 to a uint128, revert on overflow or underflow
    /// @param x The int128 to be casted
    /// @return y The casted integer, now type uint128
    function toUint128(int128 x) internal pure returns (uint128 y) {
        if (x < 0) revert SafeCastOverflow();
        y = uint128(x);
    }

    /// @notice Cast a int256 to a int128, revert on overflow or underflow
    /// @param x The int256 to be downcasted
    /// @return y The downcasted integer, now type int128
    function toInt128(int256 x) internal pure returns (int128 y) {
        y = int128(x);
        if (y != x) revert SafeCastOverflow();
    }

    /// @notice Cast a uint256 to a int256, revert on overflow
    /// @param x The uint256 to be casted
    /// @return y The casted integer, now type int256
    function toInt256(uint256 x) internal pure returns (int256 y) {
        y = int256(x);
        if (y < 0) revert SafeCastOverflow();
    }

    /// @notice Cast a uint256 to a int128, revert on overflow
    /// @param x The uint256 to be downcasted
    /// @return The downcasted integer, now type int128
    function toInt128(uint256 x) internal pure returns (int128) {
        if (x >= 1 << 127) revert SafeCastOverflow();
        return int128(int256(x));
    }
}


/// @dev Two `int128` values packed into a single `int256` where the upper 128 bits represent the amount0
/// and the lower 128 bits represent the amount1.
type BalanceDelta is int256;

using {add as +, sub as -, eq as ==, neq as !=} for BalanceDelta global;
using BalanceDeltaLibrary for BalanceDelta global;
using SafeCast for int256;

function toBalanceDelta(int128 _amount0, int128 _amount1) pure returns (BalanceDelta balanceDelta) {
    assembly {
        balanceDelta := or(shl(128, _amount0), and(sub(shl(128, 1), 1), _amount1))
    }
}

function add(BalanceDelta a, BalanceDelta b) pure returns (BalanceDelta) {
    int256 res0;
    int256 res1;
    assembly {
        let a0 := sar(128, a)
        let a1 := signextend(15, a)
        let b0 := sar(128, b)
        let b1 := signextend(15, b)
        res0 := add(a0, b0)
        res1 := add(a1, b1)
    }
    return toBalanceDelta(res0.toInt128(), res1.toInt128());
}

function sub(BalanceDelta a, BalanceDelta b) pure returns (BalanceDelta) {
    int256 res0;
    int256 res1;
    assembly {
        let a0 := sar(128, a)
        let a1 := signextend(15, a)
        let b0 := sar(128, b)
        let b1 := signextend(15, b)
        res0 := sub(a0, b0)
        res1 := sub(a1, b1)
    }
    return toBalanceDelta(res0.toInt128(), res1.toInt128());
}

function eq(BalanceDelta a, BalanceDelta b) pure returns (bool) {
    return BalanceDelta.unwrap(a) == BalanceDelta.unwrap(b);
}

function neq(BalanceDelta a, BalanceDelta b) pure returns (bool) {
    return BalanceDelta.unwrap(a) != BalanceDelta.unwrap(b);
}

/// @notice Library for getting the amount0 and amount1 deltas from the BalanceDelta type
library BalanceDeltaLibrary {
    /// @notice A BalanceDelta of 0
    BalanceDelta public constant ZERO_DELTA = BalanceDelta.wrap(0);

    function amount0(BalanceDelta balanceDelta) internal pure returns (int128 _amount0) {
        assembly {
            _amount0 := sar(128, balanceDelta)
        }
    }

    function amount1(BalanceDelta balanceDelta) internal pure returns (int128 _amount1) {
        assembly {
            _amount1 := signextend(15, balanceDelta)
        }
    }

    function diff(BalanceDelta balanceDelta) internal pure returns (int256 _diff) {
        assembly {
            let _amount0 := sar(128, balanceDelta)
            let _amount1 := signextend(15, balanceDelta)
            _diff := sub(_amount0, _amount1)
        }
    }
}

// Failed to resolve import: // Failed to resolve import: import {BeforeSwapDelta} from "v4-core/src/types/BeforeSwapDelta.sol";
// Failed to resolve import: import {ModifyLiquidityParams, SwapParams} from "v4-core/src/types/PoolOperation.sol";

interface IBeforeInitializeHook {
    /// @notice The hook called before the state of a pool is initialized
    /// @param sender The initial msg.sender for the initialize call
    /// @param key The key for the pool being initialized
    /// @param sqrtPriceX96 The sqrt(price) of the pool as a Q64.96
    /// @return bytes4 The function selector for the hook
    function beforeInitialize(address sender, PoolKey calldata key, uint160 sqrtPriceX96)
        external
        returns (bytes4);
}

interface IAfterInitializeHook {
    /// @notice The hook called after the state of a pool is initialized
    /// @param sender The initial msg.sender for the initialize call
    /// @param key The key for the pool being initialized
    /// @param sqrtPriceX96 The sqrt(price) of the pool as a Q64.96
    /// @param tick The current tick after the state of a pool is initialized
    /// @return bytes4 The function selector for the hook
    function afterInitialize(address sender, PoolKey calldata key, uint160 sqrtPriceX96, int24 tick)
        external
        returns (bytes4);
}

interface IBeforeAddLiquidityHook {
    /// @notice The hook called before liquidity is added
    /// @param sender The initial msg.sender for the add liquidity call
    /// @param key The key for the pool
    /// @param params The parameters for adding liquidity
    /// @param hookData Arbitrary data handed into the PoolManager by the liquidity provider to be passed on to the hook
    /// @return bytes4 The function selector for the hook
    function beforeAddLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        bytes calldata hookData
    ) external returns (bytes4);
}

interface IAfterAddLiquidityHook {
    /// @notice The hook called after liquidity is added
    /// @param sender The initial msg.sender for the add liquidity call
    /// @param key The key for the pool
    /// @param params The parameters for adding liquidity
    /// @param delta The caller's balance delta after adding liquidity
    /// @param feesAccrued The fees accrued since the last time fees were collected from this position
    /// @param hookData Arbitrary data handed into the PoolManager by the liquidity provider to be passed on to the hook
    /// @return bytes4 The function selector for the hook
    /// @return BalanceDelta The hook's delta in token0 and token1. Positive: the hook is owed/took currency, negative: the hook owes/sent currency
    function afterAddLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        BalanceDelta delta,
        BalanceDelta feesAccrued,
        bytes calldata hookData
    ) external returns (bytes4, BalanceDelta);
}

interface IBeforeRemoveLiquidityHook {
    /// @notice The hook called before liquidity is removed
    /// @param sender The initial msg.sender for the remove liquidity call
    /// @param key The key for the pool
    /// @param params The parameters for removing liquidity
    /// @param hookData Arbitrary data handed into the PoolManager by the liquidity provider to be be passed on to the hook
    /// @return bytes4 The function selector for the hook
    function beforeRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        bytes calldata hookData
    ) external returns (bytes4);
}

interface IAfterRemoveLiquidityHook {
    /// @notice The hook called after liquidity is removed
    /// @param sender The initial msg.sender for the remove liquidity call
    /// @param key The key for the pool
    /// @param params The parameters for removing liquidity
    /// @param delta The caller's balance delta after removing liquidity
    /// @param feesAccrued The fees accrued since the last time fees were collected from this position
    /// @param hookData Arbitrary data handed into the PoolManager by the liquidity provider to be be passed on to the hook
    /// @return bytes4 The function selector for the hook
    /// @return BalanceDelta The hook's delta in token0 and token1. Positive: the hook is owed/took currency, negative: the hook owes/sent currency
    function afterRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        BalanceDelta delta,
        BalanceDelta feesAccrued,
        bytes calldata hookData
    ) external returns (bytes4, BalanceDelta);
}

interface IBeforeSwapHook {
    /// @notice The hook called before a swap
    /// @param sender The initial msg.sender for the swap call
    /// @param key The key for the pool
    /// @param params The parameters for the swap
    /// @param hookData Arbitrary data handed into the PoolManager by the swapper to be be passed on to the hook
    /// @return bytes4 The function selector for the hook
    /// @return BeforeSwapDelta The hook's delta in specified and unspecified currencies. Positive: the hook is owed/took currency, negative: the hook owes/sent currency
    /// @return uint24 Optionally override the lp fee, only used if three conditions are met: 1. the Pool has a dynamic fee, 2. the value's 2nd highest bit is set (23rd bit, 0x400000), and 3. the value is less than or equal to the maximum fee (1 million)
    function beforeSwap(
        address sender,
        PoolKey calldata key,
        SwapParams calldata params,
        bytes calldata hookData
    ) external returns (bytes4, BeforeSwapDelta, uint24);
}

interface IAfterSwapHook {
    /// @notice The hook called after a swap
    /// @param sender The initial msg.sender for the swap call
    /// @param key The key for the pool
    /// @param params The parameters for the swap
    /// @param delta The amount owed to the caller (positive) or owed to the pool (negative)
    /// @param hookData Arbitrary data handed into the PoolManager by the swapper to be be passed on to the hook
    /// @return bytes4 The function selector for the hook
    /// @return int128 The hook's delta in unspecified currency. Positive: the hook is owed/took currency, negative: the hook owes/sent currency
    function afterSwap(
        address sender,
        PoolKey calldata key,
        SwapParams calldata params,
        BalanceDelta delta,
        bytes calldata hookData
    ) external returns (bytes4, int128);
}

interface IBeforeDonateHook {
    /// @notice The hook called before donate
    /// @param sender The initial msg.sender for the donate call
    /// @param key The key for the pool
    /// @param amount0 The amount of token0 being donated
    /// @param amount1 The amount of token1 being donated
    /// @param hookData Arbitrary data handed into the PoolManager by the donor to be be passed on to the hook
    /// @return bytes4 The function selector for the hook
    function beforeDonate(
        address sender,
        PoolKey calldata key,
        uint256 amount0,
        uint256 amount1,
        bytes calldata hookData
    ) external returns (bytes4);
}

interface IAfterDonateHook {
    /// @notice The hook called after donate
    /// @param sender The initial msg.sender for the donate call
    /// @param key The key for the pool
    /// @param amount0 The amount of token0 being donated
    /// @param amount1 The amount of token1 being donated
    /// @param hookData Arbitrary data handed into the PoolManager by the donor to be be passed on to the hook
    /// @return bytes4 The function selector for the hook
    function afterDonate(
        address sender,
        PoolKey calldata key,
        uint256 amount0,
        uint256 amount1,
        bytes calldata hookData
    ) external returns (bytes4);
}


// Failed to resolve import: // Failed to resolve import: // Failed to resolve import: import {Hooks} from "v4-core/src/libraries/Hooks.sol";







// Small library to handle fixed point number operations with 18 decimals with static typing support.




library MathLib {
    enum Rounding {
        Down, // Toward negative infinity
        Up, // Toward infinity
        Zero // Toward zero

    }

    error MulDiv_Overflow();
    error Uint8_Overflow();
    error Uint32_Overflow();
    error Uint64_Overflow();
    error Uint128_Overflow();
    error Int128_Overflow();

    uint256 public constant One27 = 10 ** 27;

    /// @notice Returns x^n with rounding precision of base
    ///
    /// @dev Source: https://github.com/makerdao/dss/blob/fa4f6630afb0624d04a003e920b0d71a00331d98/src/jug.sol#L62
    ///
    /// @param x The base value which should be exponentiated
    /// @param n The exponent
    /// @param base The scaling base, typically used for fix-point calculations
    function rpow(uint256 x, uint256 n, uint256 base) public pure returns (uint256 z) {
        assembly {
            switch x
            case 0 {
                switch n
                case 0 { z := base }
                default { z := 0 }
            }
            default {
                switch mod(n, 2)
                case 0 { z := base }
                default { z := x }
                let half := div(base, 2) // for rounding.
                for { n := div(n, 2) } n { n := div(n, 2) } {
                    let xx := mul(x, x)
                    if iszero(eq(div(xx, x), x)) { revert(0, 0) }
                    let xxRound := add(xx, half)
                    if lt(xxRound, xx) { revert(0, 0) }
                    x := div(xxRound, base)
                    if mod(n, 2) {
                        let zx := mul(z, x)
                        if and(iszero(iszero(x)), iszero(eq(div(zx, x), z))) { revert(0, 0) }
                        let zxRound := add(zx, half)
                        if lt(zxRound, zx) { revert(0, 0) }
                        z := div(zxRound, base)
                    }
                }
            }
        }
    }

    /// @notice Calculates floor(x * y / denominator) with full precision. Throws if result overflows a uint256 or
    ///         denominator == 0
    /// @dev    Original credit to Remco Bloemen under MIT license (https://xn--2-umb.com/21/muldiv)
    ///         with further edits by Uniswap Labs also under MIT license.
    // slither-disable-start divide-before-multiply
    function mulDiv(uint256 x, uint256 y, uint256 denominator) internal pure returns (uint256 result) {
        unchecked {
            // 512-bit multiply [prod1 prod0] = x * y. Compute the product mod 2^256 and mod 2^256 - 1, then use
            // use the Chinese Remainder Theorem to reconstruct the 512 bit result. The result is stored in two 256
            // variables such that product = prod1 * 2^256 + prod0.
            uint256 prod0; // Least significant 256 bits of the product
            uint256 prod1; // Most significant 256 bits of the product
            assembly {
                let mm := mulmod(x, y, not(0))
                prod0 := mul(x, y)
                prod1 := sub(sub(mm, prod0), lt(mm, prod0))
            }

            // Handle non-overflow cases, 256 by 256 division.
            if (prod1 == 0) {
                // Solidity will revert if denominator == 0, unlike the div opcode on its own.
                // The surrounding unchecked block does not change this fact.
                // See https://docs.soliditylang.org/en/latest/control-structures.html#checked-or-unchecked-arithmetic.
                return prod0 / denominator;
            }

            // Make sure the result is less than 2^256. Also prevents denominator == 0.
            if (!(denominator > prod1)) revert MulDiv_Overflow();

            ///////////////////////////////////////////////
            // 512 by 256 division.
            ///////////////////////////////////////////////

            // Make division exact by subtracting the remainder from [prod1 prod0].
            uint256 remainder;
            assembly {
                // Compute remainder using mulmod.
                remainder := mulmod(x, y, denominator)

                // Subtract 256 bit number from 512 bit number.
                prod1 := sub(prod1, gt(remainder, prod0))
                prod0 := sub(prod0, remainder)
            }

            // Factor powers of two out of denominator and compute largest power of two divisor of denominator.
            // Always >= 1.
            // See https://cs.stackexchange.com/q/138556/92363.

            // Does not overflow because the denominator cannot be zero at this stage in the function.
            uint256 twos = denominator & (~denominator + 1);
            assembly {
                // Divide denominator by twos.
                denominator := div(denominator, twos)

                // Divide [prod1 prod0] by twos.
                prod0 := div(prod0, twos)

                // Flip twos such that it is 2^256 / twos. If twos is zero, then it becomes one.
                twos := add(div(sub(0, twos), twos), 1)
            }

            // Shift in bits from prod1 into prod0.
            prod0 |= prod1 * twos;

            // Invert denominator mod 2^256. Now that denominator is an odd number, it has an inverse modulo 2^256 such
            // that denominator * inv = 1 mod 2^256. Compute the inverse by starting with a seed that is correct for
            // four bits. That is, denominator * inv = 1 mod 2^4.
            uint256 inverse = (3 * denominator) ^ 2;

            // Use the Newton-Raphson iteration to improve the precision. Thanks to Hensel's lifting lemma, this also
            // works
            // in modular arithmetic, doubling the correct bits in each step.
            inverse *= 2 - denominator * inverse; // inverse mod 2^8
            inverse *= 2 - denominator * inverse; // inverse mod 2^16
            inverse *= 2 - denominator * inverse; // inverse mod 2^32
            inverse *= 2 - denominator * inverse; // inverse mod 2^64
            inverse *= 2 - denominator * inverse; // inverse mod 2^128
            inverse *= 2 - denominator * inverse; // inverse mod 2^256

            // Because the division is now exact we can divide by multiplying with the modular inverse of denominator.
            // This will give us the correct result modulo 2^256. Since the preconditions guarantee that the outcome is
            // less than 2^256, this is the final result. We don't need to compute the high bits of the result and prod1
            // is no longer required.
            result = prod0 * inverse;
            return result;
        }
    }
    // slither-disable-end divide-before-multiply

    /// @notice Calculates x * y / denominator with full precision, following the selected rounding direction.
    function mulDiv(uint256 x, uint256 y, uint256 denominator, Rounding rounding) internal pure returns (uint256) {
        uint256 result = mulDiv(x, y, denominator);
        if (rounding == Rounding.Up && mulmod(x, y, denominator) > 0) {
            result += 1;
        }
        return result;
    }

    /// @notice Safe type conversion from uint256 to uint8.
    function toUint8(uint256 value) internal pure returns (uint8) {
        if (!(value <= type(uint8).max)) revert Uint8_Overflow();
        return uint8(value);
    }

    function toUint32(uint256 value) internal pure returns (uint32) {
        if (!(value <= type(uint32).max)) revert Uint32_Overflow();
        return uint32(value);
    }

    function toUint64(uint256 value) internal pure returns (uint64) {
        if (!(value <= type(uint64).max)) revert Uint64_Overflow();
        return uint64(value);
    }

    /// @notice Safe type conversion from uint256 to uint128.
    function toUint128(uint256 value) internal pure returns (uint128) {
        if (!(value <= type(uint128).max)) revert Uint128_Overflow();
        return uint128(value);
    }

    /// @notice Returns the smallest of two numbers.
    function min(uint256 a, uint256 b) internal pure returns (uint256) {
        return a > b ? b : a;
    }

    /// @notice Returns the largest of two numbers.
    function max(uint256 a, uint256 b) internal pure returns (uint256) {
        return a > b ? a : b;
    }
}


type D18 is uint128;

using MathLib for uint256;

/// @dev add two D18 types
function add(D18 d1, D18 d2) pure returns (D18) {
    return D18.wrap(D18.unwrap(d1) + D18.unwrap(d2));
}

/// @dev substract two D18 types
function sub(D18 d1, D18 d2) pure returns (D18) {
    return D18.wrap(D18.unwrap(d1) - D18.unwrap(d2));
}

/// @dev Divides one D18 by another one while retaining precision:
/// - nominator (decimal): 50e18
/// - denominator (decimal):  2e19
/// - result (decimal): 25e17
function divD18(D18 d1, D18 d2) pure returns (D18) {
    return D18.wrap(MathLib.mulDiv(D18.unwrap(d1), 1e18, D18.unwrap(d2)).toUint128());
}

/// @dev Multiplies one D18 with another one while retaining precision:
/// - value1 (decimal): 50e18
/// - value2 (decimal):  2e19
/// - result (decimal): 100e19
function mulD18(D18 d1, D18 d2) pure returns (D18) {
    return D18.wrap(MathLib.mulDiv(D18.unwrap(d1), D18.unwrap(d2), 1e18).toUint128());
}

/// @dev sugar for getting the inner representation of a D18
function inner(D18 d1) pure returns (uint128) {
    return D18.unwrap(d1);
}

/// @dev Returns the reciprocal of a D18 decimal, i.e. 1 / d.
///      Example: if d = 2.0 (2e18 internally), reciprocal(d) = 0.5 (5e17 internally).
function reciprocal(D18 d) pure returns (D18) {
    uint128 val = D18.unwrap(d);
    require(val != 0, "D18/division-by-zero");
    return d18(1e18, val);
}

/// @dev Multiplies a decimal by an integer. i.e:
/// - d (decimal):      1_500_000_000_000_000_000
/// - value (integer):  4_000_000_000_000_000_000
/// - result (integer): 6_000_000_000_000_000_000
function mulUint128(D18 d, uint128 value, MathLib.Rounding rounding) pure returns (uint128) {
    return MathLib.mulDiv(D18.unwrap(d), value, 1e18, rounding).toUint128();
}

/// @dev Multiplies a decimal by an integer. i.e:
/// - d (decimal):      1_500_000_000_000_000_000
/// - value (integer):  4_000_000_000_000_000_000
/// - result (integer): 6_000_000_000_000_000_000
function mulUint256(D18 d, uint256 value, MathLib.Rounding rounding) pure returns (uint256) {
    return MathLib.mulDiv(D18.unwrap(d), value, 1e18, rounding);
}

/// @dev  Divides an integer by a decimal, i.e.
/// @dev  Same as mulDiv for integers, i.e:
/// - d (decimal):      2_000_000_000_000_000_000
/// - value (integer):  100_000_000_000_000_000_000
/// - result (integer): 50_000_000_000_000_000_000
function reciprocalMulUint128(D18 d, uint128 value, MathLib.Rounding rounding) pure returns (uint128) {
    return MathLib.mulDiv(value, 1e18, d.inner(), rounding).toUint128();
}

/// @dev  Divides an integer by a decimal, i.e.
/// @dev  Same as mulDiv for integers, i.e:
/// - d (decimal):      2_000_000_000_000_000_000
/// - value (integer):  100_000_000_000_000_000_000
/// - result (integer): 50_000_000_000_000_000_000
function reciprocalMulUint256(D18 d, uint256 value, MathLib.Rounding rounding) pure returns (uint256) {
    return MathLib.mulDiv(value, 1e18, d.inner(), rounding);
}

/// @dev Easy way to construct a decimal number
function d18(uint128 value) pure returns (D18) {
    return D18.wrap(value);
}

/// @dev Easy way to construct a decimal number
function d18(uint128 num, uint128 den) pure returns (D18) {
    return D18.wrap(MathLib.mulDiv(num, 1e18, den).toUint128());
}

function eq(D18 a, D18 b) pure returns (bool) {
    return D18.unwrap(a) == D18.unwrap(b);
}

function raw(D18 d) pure returns (uint128) {
    return D18.unwrap(d);
}

using {
    add as +,
    sub as -,
    divD18 as /,
    inner,
    eq,
    mulD18 as *,
    mulUint128,
    mulUint256,
    reciprocalMulUint128,
    reciprocalMulUint256,
    reciprocal,
    raw
} for D18 global;








type ShareClassId is bytes16;

function isNull(ShareClassId scId) pure returns (bool) {
    return ShareClassId.unwrap(scId) == 0;
}

function equals(ShareClassId left, ShareClassId right) pure returns (bool) {
    return ShareClassId.unwrap(left) == ShareClassId.unwrap(right);
}

function raw(ShareClassId scId) pure returns (bytes16) {
    return ShareClassId.unwrap(scId);
}

function newShareClassId(PoolId poolId, uint32 index) pure returns (ShareClassId scId) {
    return ShareClassId.wrap(bytes16((uint128(PoolId.unwrap(poolId)) << 64) + index));
}

using {isNull, raw, equals as ==} for ShareClassId global;




/// @dev Composite Id of the centrifugeId (uint16) where the asset resides
///      and a local counter (uint64) that is part of the contract that registers the asset.
type AssetId is uint128;

function isNull(AssetId assetId) pure returns (bool) {
    return AssetId.unwrap(assetId) == 0;
}

function addr(AssetId assetId) pure returns (address) {
    return address(uint160(AssetId.unwrap(assetId)));
}

function raw(AssetId assetId) pure returns (uint128) {
    return AssetId.unwrap(assetId);
}

function centrifugeId(AssetId assetId) pure returns (uint16) {
    return uint16(AssetId.unwrap(assetId) >> 112);
}

function newAssetId(uint16 centrifugeId_, uint64 counter) pure returns (AssetId) {
    return AssetId.wrap((uint128(centrifugeId_) << 112) + counter);
}

function newAssetId(uint32 isoCode) pure returns (AssetId) {
    return AssetId.wrap(isoCode);
}

function eq(AssetId a, AssetId b) pure returns (bool) {
    return a.raw() == b.raw();
}

using {isNull, addr, raw, centrifugeId, eq} for AssetId global;









/**
 * @dev Interface of the ERC165 standard, as defined in the
 * https://eips.ethereum.org/EIPS/eip-165[EIP].
 *
 * Implementers can declare support of contract interfaces, which can then be
 * queried by others.
 */
interface IERC165 {
    /**
     * @dev Returns true if this contract implements the interface defined by
     * `interfaceId`. See the corresponding
     * https://eips.ethereum.org/EIPS/eip-165#how-interfaces-are-identified[EIP section]
     * to learn more about how these ids are created.
     *
     * This function call must use less than 30 000 gas.
     */
    function supportsInterface(bytes4 interfaceId) external view returns (bool);
}

interface IERC7575 is IERC165 {
    event Deposit(address indexed sender, address indexed owner, uint256 assets, uint256 shares);
    event Withdraw(
        address indexed sender, address indexed receiver, address indexed owner, uint256 assets, uint256 shares
    );

    /**
     * @dev Returns the address of the underlying token used for the Vault for accounting, depositing, and withdrawing.
     *
     * - MUST be an ERC-20 token contract.
     * - MUST NOT revert.
     */
    function asset() external view returns (address assetTokenAddress);

    /**
     * @dev Returns the address of the share token
     *
     * - MUST be an ERC-20 token contract.
     * - MUST NOT revert.
     */
    function share() external view returns (address shareTokenAddress);

    /**
     * @dev Returns the amount of shares that the Vault would exchange for the amount of assets provided, in an ideal
     * scenario where all the conditions are met.
     *
     * - MUST NOT be inclusive of any fees that are charged against assets in the Vault.
     * - MUST NOT show any variations depending on the caller.
     * - MUST NOT reflect slippage or other on-chain conditions, when performing the actual exchange.
     * - MUST NOT revert.
     *
     * NOTE: This calculation MAY NOT reflect the “per-user” price-per-share, and instead should reflect the
     * “average-user’s” price-per-share, meaning what the average user should expect to see when exchanging to and
     * from.
     */
    function convertToShares(uint256 assets) external view returns (uint256 shares);

    /**
     * @dev Returns the amount of assets that the Vault would exchange for the amount of shares provided, in an ideal
     * scenario where all the conditions are met.
     *
     * - MUST NOT be inclusive of any fees that are charged against assets in the Vault.
     * - MUST NOT show any variations depending on the caller.
     * - MUST NOT reflect slippage or other on-chain conditions, when performing the actual exchange.
     * - MUST NOT revert.
     *
     * NOTE: This calculation MAY NOT reflect the “per-user” price-per-share, and instead should reflect the
     * “average-user’s” price-per-share, meaning what the average user should expect to see when exchanging to and
     * from.
     */
    function convertToAssets(uint256 shares) external view returns (uint256 assets);

    /**
     * @dev Returns the total amount of the underlying asset that is “managed” by Vault.
     *
     * - SHOULD include any compounding that occurs from yield.
     * - MUST be inclusive of any fees that are charged against assets in the Vault.
     * - MUST NOT revert.
     */
    function totalAssets() external view returns (uint256 totalManagedAssets);

    /**
     * @dev Returns the maximum amount of the underlying asset that can be deposited into the Vault for the receiver,
     * through a deposit call.
     *
     * - MUST return a limited value if receiver is subject to some deposit limit.
     * - MUST return 2 ** 256 - 1 if there is no limit on the maximum amount of assets that may be deposited.
     * - MUST NOT revert.
     */
    function maxDeposit(address receiver) external view returns (uint256 maxAssets);

    /**
     * @dev Allows an on-chain or off-chain user to simulate the effects of their deposit at the current block, given
     * current on-chain conditions.
     *
     * - MUST return as close to and no more than the exact amount of Vault shares that would be minted in a deposit
     *   call in the same transaction. I.e. deposit should return the same or more shares as previewDeposit if called
     *   in the same transaction.
     * - MUST NOT account for deposit limits like those returned from maxDeposit and should always act as though the
     *   deposit would be accepted, regardless if the user has enough tokens approved, etc.
     * - MUST be inclusive of deposit fees. Integrators should be aware of the existence of deposit fees.
     * - MUST NOT revert.
     *
     * NOTE: any unfavorable discrepancy between convertToShares and previewDeposit SHOULD be considered slippage in
     * share price or some other type of condition, meaning the depositor will lose assets by depositing.
     */
    function previewDeposit(uint256 assets) external view returns (uint256 shares);

    /**
     * @dev Mints shares Vault shares to receiver by depositing exactly amount of underlying tokens.
     *
     * - MUST emit the Deposit event.
     * - MAY support an additional flow in which the underlying tokens are owned by the Vault contract before the
     *   deposit execution, and are accounted for during deposit.
     * - MUST revert if all of assets cannot be deposited (due to deposit limit being reached, slippage, the user not
     *   approving enough underlying tokens to the Vault contract, etc).
     *
     * NOTE: most implementations will require pre-approval of the Vault with the Vault’s underlying asset token.
     */
    function deposit(uint256 assets, address receiver) external returns (uint256 shares);

    /**
     * @dev Returns the maximum amount of the Vault shares that can be minted for the receiver, through a mint call.
     * - MUST return a limited value if receiver is subject to some mint limit.
     * - MUST return 2 ** 256 - 1 if there is no limit on the maximum amount of shares that may be minted.
     * - MUST NOT revert.
     */
    function maxMint(address receiver) external view returns (uint256 maxShares);

    /**
     * @dev Allows an on-chain or off-chain user to simulate the effects of their mint at the current block, given
     * current on-chain conditions.
     *
     * - MUST return as close to and no fewer than the exact amount of assets that would be deposited in a mint call
     *   in the same transaction. I.e. mint should return the same or fewer assets as previewMint if called in the
     *   same transaction.
     * - MUST NOT account for mint limits like those returned from maxMint and should always act as though the mint
     *   would be accepted, regardless if the user has enough tokens approved, etc.
     * - MUST be inclusive of deposit fees. Integrators should be aware of the existence of deposit fees.
     * - MUST NOT revert.
     *
     * NOTE: any unfavorable discrepancy between convertToAssets and previewMint SHOULD be considered slippage in
     * share price or some other type of condition, meaning the depositor will lose assets by minting.
     */
    function previewMint(uint256 shares) external view returns (uint256 assets);

    /**
     * @dev Mints exactly shares Vault shares to receiver by depositing amount of underlying tokens.
     *
     * - MUST emit the Deposit event.
     * - MAY support an additional flow in which the underlying tokens are owned by the Vault contract before the mint
     *   execution, and are accounted for during mint.
     * - MUST revert if all of shares cannot be minted (due to deposit limit being reached, slippage, the user not
     *   approving enough underlying tokens to the Vault contract, etc).
     *
     * NOTE: most implementations will require pre-approval of the Vault with the Vault’s underlying asset token.
     */
    function mint(uint256 shares, address receiver) external returns (uint256 assets);

    /**
     * @dev Returns the maximum amount of the underlying asset that can be withdrawn from the owner balance in the
     * Vault, through a withdraw call.
     *
     * - MUST return a limited value if owner is subject to some withdrawal limit or timelock.
     * - MUST NOT revert.
     */
    function maxWithdraw(address owner) external view returns (uint256 maxAssets);

    /**
     * @dev Allows an on-chain or off-chain user to simulate the effects of their withdrawal at the current block,
     * given current on-chain conditions.
     *
     * - MUST return as close to and no fewer than the exact amount of Vault shares that would be burned in a withdraw
     *   call in the same transaction. I.e. withdraw should return the same or fewer shares as previewWithdraw if
     *   called
     *   in the same transaction.
     * - MUST NOT account for withdrawal limits like those returned from maxWithdraw and should always act as though
     *   the withdrawal would be accepted, regardless if the user has enough shares, etc.
     * - MUST be inclusive of withdrawal fees. Integrators should be aware of the existence of withdrawal fees.
     * - MUST NOT revert.
     *
     * NOTE: any unfavorable discrepancy between convertToShares and previewWithdraw SHOULD be considered slippage in
     * share price or some other type of condition, meaning the depositor will lose assets by depositing.
     */
    function previewWithdraw(uint256 assets) external view returns (uint256 shares);

    /**
     * @dev Burns shares from owner and sends exactly assets of underlying tokens to receiver.
     *
     * - MUST emit the Withdraw event.
     * - MAY support an additional flow in which the underlying tokens are owned by the Vault contract before the
     *   withdraw execution, and are accounted for during withdraw.
     * - MUST revert if all of assets cannot be withdrawn (due to withdrawal limit being reached, slippage, the owner
     *   not having enough shares, etc).
     *
     * Note that some implementations will require pre-requesting to the Vault before a withdrawal may be performed.
     * Those methods should be performed separately.
     */
    function withdraw(uint256 assets, address receiver, address owner) external returns (uint256 shares);

    /**
     * @dev Returns the maximum amount of Vault shares that can be redeemed from the owner balance in the Vault,
     * through a redeem call.
     *
     * - MUST return a limited value if owner is subject to some withdrawal limit or timelock.
     * - MUST return balanceOf(owner) if owner is not subject to any withdrawal limit or timelock.
     * - MUST NOT revert.
     */
    function maxRedeem(address owner) external view returns (uint256 maxShares);

    /**
     * @dev Allows an on-chain or off-chain user to simulate the effects of their redeemption at the current block,
     * given current on-chain conditions.
     *
     * - MUST return as close to and no more than the exact amount of assets that would be withdrawn in a redeem call
     *   in the same transaction. I.e. redeem should return the same or more assets as previewRedeem if called in the
     *   same transaction.
     * - MUST NOT account for redemption limits like those returned from maxRedeem and should always act as though the
     *   redemption would be accepted, regardless if the user has enough shares, etc.
     * - MUST be inclusive of withdrawal fees. Integrators should be aware of the existence of withdrawal fees.
     * - MUST NOT revert.
     *
     * NOTE: any unfavorable discrepancy between convertToAssets and previewRedeem SHOULD be considered slippage in
     * share price or some other type of condition, meaning the depositor will lose assets by redeeming.
     */
    function previewRedeem(uint256 shares) external view returns (uint256 assets);

    /**
     * @dev Burns exactly shares from owner and sends assets of underlying tokens to receiver.
     *
     * - MUST emit the Withdraw event.
     * - MAY support an additional flow in which the underlying tokens are owned by the Vault contract before the
     *   redeem execution, and are accounted for during redeem.
     * - MUST revert if all of shares cannot be redeemed (due to withdrawal limit being reached, slippage, the owner
     *   not having enough shares, etc).
     *
     * NOTE: some implementations will require pre-requesting to the Vault before a withdrawal may be performed.
     * Those methods should be performed separately.
     */
    function redeem(uint256 shares, address receiver, address owner) external returns (uint256 assets);
}

interface IERC7575Share is IERC165 {
    event VaultUpdate(address indexed asset, address vault);

    /**
     * @dev Returns the address of the Vault for the given asset.
     *
     * @param asset the ERC-20 token to deposit with into the Vault
     */
    function vault(address asset) external view returns (address);
}


interface IERC1404 {
    /// @notice Detects if a transfer will be reverted and if so returns an appropriate reference code
    /// @param from Sending address
    /// @param to Receiving address
    /// @param value Amount of tokens being transferred
    /// @return Code by which to reference message for rejection reasoning
    /// @dev Overwrite with your custom transfer restriction logic
    function detectTransferRestriction(address from, address to, uint256 value) external view returns (uint8);

    /// @notice Returns a human-readable message for a given restriction code
    /// @param restrictionCode Identifier for looking up a message
    /// @return Text showing the restriction's reasoning
    /// @dev Overwrite with your custom message and restrictionCode handling
    function messageForTransferRestriction(uint8 restrictionCode) external view returns (string memory);
}

interface IShareToken is IERC20Metadata, IERC7575Share, IERC1404 {
    // --- Events ---
    event File(bytes32 indexed what, address data);
    event SetHookData(address indexed user, bytes16 data);

    // --- Errors ---
    error NotAuthorizedOrHook();
    error ExceedsMaxSupply();
    error RestrictionsFailed();

    struct Balance {
        /// @dev The user balance is limited to uint128. This is safe because the decimals are limited to 18,
        ///      thus the max balance is 2^128-1 / 10**18 = 3.40 * 10**20. This is also enforced on mint.
        uint128 amount;
        /// @dev There are 16 bytes that are used to store hook data (e.g. restrictions for users).
        bytes16 hookData;
    }

    // --- Administration ---
    /// @notice returns the hook that transfers perform callbacks to
    /// @dev    MUST comply to `IHook` interface
    function hook() external view returns (address);

    /// @notice Updates a contract parameter
    /// @param what Accepts a bytes32 representation of 'name', 'symbol'
    function file(bytes32 what, string memory data) external;

    /// @notice Updates a contract parameter
    /// @param what Accepts a bytes32 representation of 'hook'
    function file(bytes32 what, address data) external;

    /// @notice updates the vault for a given `asset`
    function updateVault(address asset, address vault_) external;

    // --- ERC20 overrides ---
    /// @notice returns the 16 byte hook data of the given `user`.
    /// @dev    Stored in the 128 most significant bits of the user balance
    function hookDataOf(address user) external view returns (bytes16);

    /// @notice update the 16 byte hook data of the given `user`
    function setHookData(address user, bytes16 hookData) external;

    /// @notice Function to mint tokens
    function mint(address user, uint256 value) external;

    /// @notice Function to burn tokens
    function burn(address user, uint256 value) external;

    /// @notice Checks if the tokens can be transferred given the input values
    function checkTransferRestriction(address from, address to, uint256 value) external view returns (bool);

    /// @notice Performs an authorized transfer, with `sender` as the given sender.
    /// @dev    Requires allowance if `sender` != `from`
    function authTransferFrom(address sender, address from, address to, uint256 amount) external returns (bool);
}




















interface IAuth {
    event Rely(address indexed user);
    event Deny(address indexed user);

    error NotAuthorized();

    /// @notice Returns whether the target is a ward (has admin access)
    function wards(address target) external view returns (uint256);

    /// @notice Make user a ward (give them admin access)
    function rely(address user) external;

    /// @notice Remove user as a ward (remove admin access)
    function deny(address user) external;
}


/// @title  Auth
/// @notice Simple authentication pattern
/// @author Based on code from https://github.com/makerdao/dss
abstract contract Auth is IAuth {
    /// @inheritdoc IAuth
    mapping(address => uint256) public wards;

    constructor(address initialWard) {
        wards[initialWard] = 1;
        emit Rely(initialWard);
    }

    /// @dev Check if the msg.sender has permissions
    modifier auth() {
        if (!(wards[msg.sender] == 1)) revert NotAuthorized();
        _;
    }

    /// @inheritdoc IAuth
    function rely(address user) public auth {
        wards[user] = 1;
        emit Rely(user);
    }

    /// @inheritdoc IAuth
    function deny(address user) public auth {
        wards[user] = 0;
        emit Deny(user);
    }
}







/* Duplicate interface IERC165 removed */                                                                                                                                                                                                                                                                                                                                                                                                                                                     


interface IERC6909 is IERC165 {
    error EmptyOwner();
    error EmptyAmount();
    error InvalidTokenId();
    error InsufficientBalance(address owner, uint256 tokenId);
    error InsufficientAllowance(address sender, uint256 tokenId);

    event OperatorSet(address indexed owner, address indexed operator, bool approved);
    event Approval(address indexed owner, address indexed spender, uint256 indexed tokenId, uint256 amount);
    event Transfer(address caller, address indexed from, address indexed to, uint256 indexed tokenId, uint256 amount);

    /// @notice           Owner balance of a tokenId.
    /// @param owner      The address of the owner.
    /// @param tokenId    The id of the token.
    /// @return amount    The balance of the token.
    function balanceOf(address owner, uint256 tokenId) external view returns (uint256 amount);

    /// @notice           Spender allowance of a tokenId.
    /// @param owner      The address of the owner.
    /// @param spender    The address of the spender.
    /// @param tokenId    The id of the token.
    /// @return amount    The allowance of the token.
    function allowance(address owner, address spender, uint256 tokenId) external view returns (uint256 amount);

    /// @notice           Checks if a spender is approved by an owner as an operator.
    /// @param owner      The address of the owner.
    /// @param spender    The address of the spender.
    /// @return approved  The approval status.
    function isOperator(address owner, address spender) external view returns (bool approved);

    /// @notice           Transfers an amount of a tokenId from the caller to a receiver.
    /// @param receiver   The address of the receiver.
    /// @param tokenId    The id of the token.
    /// @param amount     The amount of the token.
    /// @return bool      True, always, unless the function reverts.
    function transfer(address receiver, uint256 tokenId, uint256 amount) external returns (bool);

    /// @notice           Transfers an amount of a tokenId from a sender to a receiver.
    /// @param sender     The address of the sender.
    /// @param receiver   The address of the receiver.
    /// @param tokenId    The id of the token.
    /// @param amount     The amount of the token.
    /// @return bool      True, always, unless the function reverts.
    function transferFrom(address sender, address receiver, uint256 tokenId, uint256 amount) external returns (bool);

    /// @notice           Approves an amount of a tokenId to a spender.
    /// @param spender    The address of the spender.
    /// @param tokenId    The id of the token.
    /// @param amount     The amount of the token.
    /// @return bool      True, always.
    function approve(address spender, uint256 tokenId, uint256 amount) external returns (bool);

    /// @notice           Sets or removes an operator for the caller.
    /// @param operator   The address of the operator.
    /// @param approved   The approval status.
    /// @return bool      True, always.
    function setOperator(address operator, bool approved) external returns (bool);
}

interface IERC6909URIExt {
    event TokenURISet(uint256 indexed tokenId, string uri);
    event ContractURISet(address indexed target, string uri);

    error EmptyURI();

    /// @return uri     Returns the common token URI.
    function contractURI() external view returns (string memory);

    /// @dev            Returns empty string if tokenId does not exist.
    ///                 MAY implemented to throw MissingURI(tokenId) error.
    /// @param tokenId  The token to query URI for.
    /// @return uri     A string representing the uri for the specific tokenId.
    function tokenURI(uint256 tokenId) external view returns (string memory);
}

interface IERC6909NFT is IERC6909, IERC6909URIExt {
    error UnknownTokenId(address owner, uint256 tokenId);
    error LessThanMinimalDecimal(uint8 minimal, uint8 actual);

    /// @notice             Provide URI for a specific tokenId.
    /// @param tokenId      Token Id.
    /// @param URI          URI to a document defining the collection as a whole.
    function setTokenURI(uint256 tokenId, string memory URI) external;

    /// @dev                Optional method to set up the contract URI if needed.
    /// @param URI          URI to a document defining the collection as a whole.
    function setContractURI(string memory URI) external;

    /// @notice             Mint new tokens for a given owner and sets tokenURI.
    /// @dev                For non-fungible tokens, call with amount = 1, for fungible it could be any amount.
    ///                     TokenId is auto incremented by one.
    ///
    /// @param owner        Creates supply of a given tokenId by amount for owner.
    /// @param tokenURI     URI fortestBurningToken the newly minted token.
    /// @return tokenId     Id of the newly minted token.
    function mint(address owner, string memory tokenURI) external returns (uint256 tokenId);

    /// @notice             Destroy supply of a given tokenId by amount.
    /// @dev                The msg.sender MUST be the owner.
    ///
    /// @param tokenId      Item which have reduced supply.
    function burn(uint256 tokenId) external;
}

/// @notice Extension of ERC6909 Standard for tracking total supply
interface IERC6909TotalSupplyExt {
    /// @notice         The totalSupply for a token id.
    ///
    /// @param tokenId  Id of the token
    /// @return supply  Total supply for a given `tokenId`
    function totalSupply(uint256 tokenId) external returns (uint256 supply);
}

interface IERC6909Decimals {
    /// @notice             Used to retrieve the decimals of an asset
    /// @dev                address is used but the value corresponds to a AssetId
    function decimals(uint256 assetId) external view returns (uint8);
}

interface IERC6909MetadataExt is IERC6909Decimals {
    /// @notice             Used to retrieve the decimals of an asset
    /// @dev                address is used but the value corresponds to a AssetId
    function decimals(uint256 assetId) external view returns (uint8);

    /// @notice             Used to retrieve the name of an asset
    /// @dev                address is used but the value corresponds to a AssetId
    function name(uint256 assetId) external view returns (string memory);

    /// @notice             Used to retrieve the symbol of an asset
    /// @dev                address is used but the value corresponds to a AssetId
    function symbol(uint256 assetId) external view returns (string memory);
}

interface IERC6909Fungible is IERC6909 {
    /// @notice             Mint new tokens for a specific tokenid and assign them to an owner
    ///
    /// @param owner        Creates supply of a given `tokenId` by `amount` for owner.
    /// @param tokenId      Id of the item
    /// @param amount       Adds `amount` to the total supply of the given `tokenId`
    function mint(address owner, uint256 tokenId, uint256 amount) external;

    /// @notice             Destroy supply of a given tokenId by amount.
    /// @dev                The msg.sender MUST be the owner.
    ///
    /// @param owner        Owner of the `tokenId`
    /// @param tokenId      Id of the item.
    /// @param amount       Subtract `amount` from the total supply of the given `tokenId`
    function burn(address owner, uint256 tokenId, uint256 amount) external;

    /// @notice             Enforces a transfer from `spender` point of view.
    ///
    ///
    /// @param sender       The owner of the `tokenId`
    /// @param receiver     Address of the receiving party
    /// @param tokenId      Token Id
    /// @param amount       Amount to be transferred
    function authTransferFrom(address sender, address receiver, uint256 tokenId, uint256 amount)
        external
        returns (bool);
}

/// @dev  A factory contract to deploy new collateral contracts implementing IERC6909.
interface IERC6909Factory {
    /// Events
    event NewTokenDeployment(address indexed owner, address instance);

    /// @notice       Deploys new install of a contract that implements IERC6909.
    /// @dev          Factory should deploy deterministically if possible.
    ///
    /// @param owner  Owner of the deployed collateral contract which has initial full rights.
    /// @param salt   Used to make a deterministic deployment.
    /// @return       An address of the newly deployed contract.
    function deploy(address owner, bytes32 salt) external returns (address);

    /// @notice       Generates a new deterministic address based on the owner and the salt.
    ///
    /// @param owner  Owner of the deployed collateral contract which has initial full rights.
    /// @param salt   Used to make a deterministic deployment.
    /// @return       An address of the newly deployed contract.
    function previewAddress(address owner, bytes32 salt) external returns (address);
}






/// @title  Safe Transfer Lib
/// @author Modified from Uniswap v3 Periphery (libraries/TransferHelper.sol)
library SafeTransferLib {
    error NoCode();
    error SafeTransferFromFailed();
    error SafeTransferFailed();
    error SafeApproveFailed();
    error SafeTransferEthFailed();

    /// @notice Transfers tokens from the targeted address to the given destination
    /// @notice Errors if transfer fails
    /// @param token The contract address of the token to be transferred
    /// @param from The originating address from which the tokens will be transferred
    /// @param to The destination address of the transfer
    /// @param value The amount to be transferred
    function safeTransferFrom(address token, address from, address to, uint256 value) internal {
        if (!(address(token).code.length > 0)) revert NoCode();

        (bool success, bytes memory data) = token.call(abi.encodeWithSelector(IERC20.transferFrom.selector, from, to, value));
        if (!(success && (data.length == 0 || abi.decode(data, (bool))))) revert SafeTransferFromFailed();
    }

    /// @notice Transfers tokens from msg.sender to a recipient
    /// @dev Errors if transfer fails
    /// @param token The contract address of the token which will be transferred
    /// @param to The recipient of the transfer
    /// @param value The value of the transfer
    function safeTransfer(address token, address to, uint256 value) internal {
        if (!(address(token).code.length > 0)) revert NoCode();

        (bool success, bytes memory data) = token.call(abi.encodeWithSelector(IERC20.transfer.selector, to, value));
        if (!(success && (data.length == 0 || abi.decode(data, (bool))))) revert SafeTransferFailed();
    }

    /// @notice Approves the stipulated contract to spend the given allowance in the given token
    /// @dev Errors if approval fails
    /// @param token The contract address of the token to be approved
    /// @param to The target of the approval
    /// @param value The amount of the given token the target will be allowed to spend
    function safeApprove(address token, address to, uint256 value) internal {
        if (!(address(token).code.length > 0)) revert NoCode();

        (bool success, bytes memory data) = token.call(abi.encodeWithSelector(IERC20.approve.selector, to, value));
        if (!(success && (data.length == 0 || abi.decode(data, (bool))))) revert SafeApproveFailed();
    }

    /// @notice Transfers ETH to the recipient address
    /// @dev Fails with `STE`
    /// @dev Make sure that method that is using this function is protected from reentrancy
    /// @param to The destination of the transfer
    /// @param value The value to be transferred
    function safeTransferETH(address to, uint256 value) internal {
        (bool success,) = to.call{value: value}(new bytes(0));
        if (!(success)) revert SafeTransferEthFailed();
    }
}





address constant ETH_ADDRESS = address(0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE);

interface IRecoverable {
    /// @notice Used to recover any ERC-20 token.
    /// @dev    This method is called only by authorized entities
    /// @param  token It could be 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    ///         to recover locked native ETH or token compatible with ERC20.
    /// @param  to Receiver of the funds
    /// @param  amount Amount to send to the receiver.
    function recoverTokens(address token, address to, uint256 amount) external;

    /// @notice Used to recover any ERC-20 or ERC-6909 token.
    /// @dev    This method is called only by authorized entities
    /// @param  token It could be 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    ///         to recover locked native ETH or token compatible with ERC20 or ERC6909.
    /// @param  tokenId The token id, i.e. non-zero if the underlying token is ERC6909 and else zero.
    /// @param  to Receiver of the funds
    /// @param  amount Amount to send to the receiver.
    function recoverTokens(address token, uint256 tokenId, address to, uint256 amount) external;
}


abstract contract Recoverable is Auth, IRecoverable {
    /// @inheritdoc IRecoverable
    function recoverTokens(address token, address receiver, uint256 amount) public auth {
        if (token == ETH_ADDRESS) {
            SafeTransferLib.safeTransferETH(receiver, amount);
        } else {
            SafeTransferLib.safeTransfer(token, receiver, amount);
        }
    }

    /// @inheritdoc IRecoverable
    function recoverTokens(address token, uint256 tokenId, address receiver, uint256 amount) external auth {
        if (tokenId == 0) {
            recoverTokens(token, receiver, amount);
        } else {
            IERC6909(token).transfer(receiver, tokenId, amount);
        }
    }
}





/// @title  Escrow for holding assets
interface IEscrow {
    // --- Events ---
    /// @notice Emitted when an authTransferTo is made
    /// @dev Needed as allowances increase attack surface
    event AuthTransferTo(address indexed asset, uint256 indexed tokenId, address reciver, uint256 value);

    /// @notice Emitted when the escrow has insufficient balance for an action - virtual or actual balance
    error InsufficientBalance(address asset, uint256 tokenId, uint256 value, uint256 balance);

    /// @notice
    function authTransferTo(address asset, uint256 tokenId, address receiver, uint256 value) external;

    /// @notice
    function authTransferTo(address asset, address receiver, uint256 value) external;
}

struct Holding {
    uint128 total;
    uint128 reserved;
}

/// @title PerPoolEscrow separating funds by pool and share class
interface IPoolEscrow is IEscrow, IRecoverable {
    // --- Events ---
    /// @notice Emitted when a deposit is made
    /// @param asset The address of the deposited asset
    /// @param tokenId The id of the asset - 0 for ERC20
    /// @param poolId The id of the pool
    /// @param scId The id of the share class
    /// @param value The amount deposited
    event Deposit(
        address indexed asset, uint256 indexed tokenId, PoolId indexed poolId, ShareClassId scId, uint128 value
    );

    /// @notice Emitted when an amount is reserved
    /// @param asset The address of the reserved asset
    /// @param tokenId The id of the asset - 0 for ERC20
    /// @param poolId The id of the pool
    /// @param scId The id of the share class
    /// @param value The delta amount reserved
    /// @param value The new absolute amount reserved
    event IncreaseReserve(
        address indexed asset,
        uint256 indexed tokenId,
        PoolId indexed poolId,
        ShareClassId scId,
        uint256 delta,
        uint128 value
    );

    /// @notice Emitted when an amount is unreserved
    /// @param asset The address of the reserved asset
    /// @param tokenId The id of the asset - 0 for ERC20
    /// @param poolId The id of the pool
    /// @param scId The id of the share class
    /// @param value The delta amount unreserved
    /// @param value The new absolute amount reserved
    event DecreaseReserve(
        address indexed asset,
        uint256 indexed tokenId,
        PoolId indexed poolId,
        ShareClassId scId,
        uint256 delta,
        uint128 value
    );

    /// @notice Emitted when a withdraw is made
    /// @param asset The address of the withdrawn asset
    /// @param tokenId The id of the asset - 0 for ERC20
    /// @param poolId The id of the pool
    /// @param scId The id of the share class
    /// @param value The amount withdrawn
    event Withdraw(
        address indexed asset, uint256 indexed tokenId, PoolId indexed poolId, ShareClassId scId, uint128 value
    );

    // --- Errors ---
    /// @notice Dispatched when the balance of the escrow did not increase sufficiently
    error InsufficientDeposit();

    /// @notice Dispatched when the outstanding reserved amount is insufficient for the decrease
    error InsufficientReservedAmount();

    // --- Functions ---
    /// @notice Deposits `value` of `asset` in underlying `poolId` and given `scId`
    ///
    /// @dev NOTE: Must ensure balance sufficiency, i.e. that the depositing amount does not exceed the balance of
    /// escrow
    ///
    /// @param scId The id of the share class
    /// @param asset The address of the asset to be deposited
    /// @param tokenId The id of the asset - 0 for ERC20
    /// @param value The amount to deposit
    function deposit(ShareClassId scId, address asset, uint256 tokenId, uint128 value) external;

    /// @notice Withdraws `value` of `asset` in underlying `poolId` and given `scId`
    /// @dev MUST ensure that reserved amounts are not withdrawn
    /// @param scId The id of the share class
    /// @param asset The address of the asset to be withdrawn
    /// @param tokenId The id of the asset - 0 for ERC20
    /// @param value The amount to withdraw
    function withdraw(ShareClassId scId, address asset, uint256 tokenId, uint128 value) external;

    /// @notice Increases the reserved amount of `value` for `asset` in underlying `poolId` and given `scId`
    /// @dev MUST prevent the reserved amount from being withdrawn
    /// @param scId The id of the share class
    /// @param asset The address of the asset to be reserved
    /// @param tokenId The id of the asset - 0 for ERC20
    /// @param value The amount to reserve
    function reserveIncrease(ShareClassId scId, address asset, uint256 tokenId, uint128 value) external;

    /// @notice Decreases the reserved amount of `value` for `asset` in underlying `poolId` and given `scId`
    /// @dev MUST fail if `value` is greater than the current reserved amount
    /// @param scId The id of the share class
    /// @param asset The address of the asset to be reserved
    /// @param tokenId The id of the asset - 0 for ERC20
    /// @param value The amount to decrease
    function reserveDecrease(ShareClassId scId, address asset, uint256 tokenId, uint128 value) external;

    /// @notice Provides the available balance of `asset` in underlying `poolId` and given `scId`
    /// @dev MUST return the balance minus the reserved amount
    /// @param scId The id of the share class
    /// @param asset The address of the asset to be checked
    /// @param tokenId The id of the asset - 0 for ERC20
    /// @return The available balance
    function availableBalanceOf(ShareClassId scId, address asset, uint256 tokenId) external view returns (uint128);
}











interface IERC7540Operator {
    /**
     * @dev The event emitted when an operator is set.
     *
     * @param controller The address of the controller.
     * @param operator The address of the operator.
     * @param approved The approval status.
     */
    event OperatorSet(address indexed controller, address indexed operator, bool approved);

    /**
     * @dev Sets or removes an operator for the caller.
     *
     * @param operator The address of the operator.
     * @param approved The approval status.
     * @return Whether the call was executed successfully or not
     */
    function setOperator(address operator, bool approved) external returns (bool);

    /**
     * @dev Returns `true` if the `operator` is approved as an operator for an `controller`.
     *
     * @param controller The address of the controller.
     * @param operator The address of the operator.
     * @return status The approval status
     */
    function isOperator(address controller, address operator) external view returns (bool status);
}

interface IERC7540Deposit is IERC7540Operator {
    event DepositRequest(
        address indexed controller, address indexed owner, uint256 indexed requestId, address sender, uint256 assets
    );
    /**
     * @dev Transfers assets from sender into the Vault and submits a Request for asynchronous deposit.
     *
     * - MUST support ERC-20 approve / transferFrom on asset as a deposit Request flow.
     * - MUST revert if all of assets cannot be requested for deposit.
     * - owner MUST be msg.sender unless some unspecified explicit approval is given by the caller,
     *    approval of ERC-20 tokens from owner to sender is NOT enough.
     *
     * @param assets the amount of deposit assets to transfer from owner
     * @param controller the controller of the request who will be able to operate the request
     * @param owner the source of the deposit assets
     *
     * NOTE: most implementations will require pre-approval of the Vault with the Vault's underlying asset token.
     */

    function requestDeposit(uint256 assets, address controller, address owner) external returns (uint256 requestId);

    /**
     * @dev Returns the amount of requested assets in Pending state.
     *
     * - MUST NOT include any assets in Claimable state for deposit or mint.
     * - MUST NOT show any variations depending on the caller.
     * - MUST NOT revert unless due to integer overflow caused by an unreasonably large input.
     */
    function pendingDepositRequest(uint256 requestId, address controller)
        external
        view
        returns (uint256 pendingAssets);

    /**
     * @dev Returns the amount of requested assets in Claimable state for the controller to deposit or mint.
     *
     * - MUST NOT include any assets in Pending state.
     * - MUST NOT show any variations depending on the caller.
     * - MUST NOT revert unless due to integer overflow caused by an unreasonably large input.
     */
    function claimableDepositRequest(uint256 requestId, address controller)
        external
        view
        returns (uint256 claimableAssets);

    /**
     * @dev Mints shares Vault shares to receiver by claiming the Request of the controller.
     *
     * - MUST emit the Deposit event.
     * - controller MUST equal msg.sender unless the controller has approved the msg.sender as an operator.
     */
    function deposit(uint256 assets, address receiver, address controller) external returns (uint256 shares);

    /**
     * @dev Mints exactly shares Vault shares to receiver by claiming the Request of the controller.
     *
     * - MUST emit the Deposit event.
     * - controller MUST equal msg.sender unless the controller has approved the msg.sender as an operator.
     */
    function mint(uint256 shares, address receiver, address controller) external returns (uint256 assets);
}

interface IERC7540Redeem is IERC7540Operator {
    event RedeemRequest(
        address indexed controller, address indexed owner, uint256 indexed requestId, address sender, uint256 assets
    );

    /**
     * @dev Assumes control of shares from sender into the Vault and submits a Request for asynchronous redeem.
     *
     * - MUST support a redeem Request flow where the control of shares is taken from sender directly
     *   where msg.sender has ERC-20 approval over the shares of owner.
     * - MUST revert if all of shares cannot be requested for redeem.
     *
     * @param shares the amount of shares to be redeemed to transfer from owner
     * @param controller the controller of the request who will be able to operate the request
     * @param owner the source of the shares to be redeemed
     *
     * NOTE: most implementations will require pre-approval of the Vault with the Vault's share token.
     */
    function requestRedeem(uint256 shares, address controller, address owner) external returns (uint256 requestId);

    /**
     * @dev Returns the amount of requested shares in Pending state.
     *
     * - MUST NOT include any shares in Claimable state for redeem or withdraw.
     * - MUST NOT show any variations depending on the caller.
     * - MUST NOT revert unless due to integer overflow caused by an unreasonably large input.
     */
    function pendingRedeemRequest(uint256 requestId, address controller)
        external
        view
        returns (uint256 pendingShares);

    /**
     * @dev Returns the amount of requested shares in Claimable state for the controller to redeem or withdraw.
     *
     * - MUST NOT include any shares in Pending state for redeem or withdraw.
     * - MUST NOT show any variations depending on the caller.
     * - MUST NOT revert unless due to integer overflow caused by an unreasonably large input.
     */
    function claimableRedeemRequest(uint256 requestId, address controller)
        external
        view
        returns (uint256 claimableShares);
}

interface IERC7887Deposit {
    event CancelDepositRequest(address indexed controller, uint256 indexed requestId, address sender);
    event CancelDepositClaim(
        address indexed controller, address indexed receiver, uint256 indexed requestId, address sender, uint256 assets
    );

    /**
     * @dev Submits a Request for cancelling the pending deposit Request
     *
     * - controller MUST be msg.sender unless some unspecified explicit approval is given by the caller,
     *    approval of ERC-20 tokens from controller to sender is NOT enough.
     * - MUST set pendingCancelDepositRequest to `true` for the returned requestId after request
     * - MUST increase claimableCancelDepositRequest for the returned requestId after fulfillment
     * - SHOULD be claimable using `claimCancelDepositRequest`
     * Note: while `pendingCancelDepositRequest` is `true`, `requestDeposit` cannot be called
     */
    function cancelDepositRequest(uint256 requestId, address controller) external;

    /**
     * @dev Returns whether the deposit Request is pending cancelation
     *
     * - MUST NOT show any variations depending on the caller.
     */
    function pendingCancelDepositRequest(uint256 requestId, address controller)
        external
        view
        returns (bool isPending);

    /**
     * @dev Returns the amount of assets that were canceled from a deposit Request, and can now be claimed.
     *
     * - MUST NOT show any variations depending on the caller.
     */
    function claimableCancelDepositRequest(uint256 requestId, address controller)
        external
        view
        returns (uint256 claimableAssets);

    /**
     * @dev Claims the canceled deposit assets, and removes the pending cancelation Request
     *
     * - controller MUST be msg.sender unless some unspecified explicit approval is given by the caller,
     *    approval of ERC-20 tokens from controller to sender is NOT enough.
     * - MUST set pendingCancelDepositRequest to `false` for the returned requestId after request
     * - MUST set claimableCancelDepositRequest to 0 for the returned requestId after fulfillment
     */
    function claimCancelDepositRequest(uint256 requestId, address receiver, address controller)
        external
        returns (uint256 assets);
}

interface IERC7887Redeem {
    event CancelRedeemRequest(address indexed controller, uint256 indexed requestId, address sender);
    event CancelRedeemClaim(
        address indexed controller, address indexed receiver, uint256 indexed requestId, address sender, uint256 shares
    );

    /**
     * @dev Submits a Request for cancelling the pending redeem Request
     *
     * - controller MUST be msg.sender unless some unspecified explicit approval is given by the caller,
     *    approval of ERC-20 tokens from controller to sender is NOT enough.
     * - MUST set pendingCancelRedeemRequest to `true` for the returned requestId after request
     * - MUST increase claimableCancelRedeemRequest for the returned requestId after fulfillment
     * - SHOULD be claimable using `claimCancelRedeemRequest`
     * Note: while `pendingCancelRedeemRequest` is `true`, `requestRedeem` cannot be called
     */
    function cancelRedeemRequest(uint256 requestId, address controller) external;

    /**
     * @dev Returns whether the redeem Request is pending cancelation
     *
     * - MUST NOT show any variations depending on the caller.
     */
    function pendingCancelRedeemRequest(uint256 requestId, address controller) external view returns (bool isPending);

    /**
     * @dev Returns the amount of shares that were canceled from a redeem Request, and can now be claimed.
     *
     * - MUST NOT show any variations depending on the caller.
     */
    function claimableCancelRedeemRequest(uint256 requestId, address controller)
        external
        view
        returns (uint256 claimableShares);

    /**
     * @dev Claims the canceled redeem shares, and removes the pending cancelation Request
     *
     * - controller MUST be msg.sender unless some unspecified explicit approval is given by the caller,
     *    approval of ERC-20 tokens from controller to sender is NOT enough.
     * - MUST set pendingCancelRedeemRequest to `false` for the returned requestId after request
     * - MUST set claimableCancelRedeemRequest to 0 for the returned requestId after fulfillment
     */
    function claimCancelRedeemRequest(uint256 requestId, address receiver, address controller)
        external
        returns (uint256 shares);
}

interface IERC7741 {
    /**
     * @dev Grants or revokes permissions for `operator` to manage Requests on behalf of the
     *      `msg.sender`, using an [EIP-712](./eip-712.md) signature.
     */
    function authorizeOperator(
        address controller,
        address operator,
        bool approved,
        bytes32 nonce,
        uint256 deadline,
        bytes memory signature
    ) external returns (bool);

    /**
     * @dev Revokes the given `nonce` for `msg.sender` as the `owner`.
     */
    function invalidateNonce(bytes32 nonce) external;

    /**
     * @dev Returns whether the given `nonce` has been used for the `controller`.
     */
    function authorizations(address controller, bytes32 nonce) external view returns (bool used);

    /**
     * @dev Returns the `DOMAIN_SEPARATOR` as defined according to EIP-712. The `DOMAIN_SEPARATOR
     *      should be unique to the contract and chain to prevent replay attacks from other domains,
     *      and satisfy the requirements of EIP-712, but is otherwise unconstrained.
     */
    function DOMAIN_SEPARATOR() external view returns (bytes32);
}

interface IERC7714 {
    /**
     * @dev Returns `true` if the `user` is permissioned to interact with the contract.
     */
    function isPermissioned(address controller) external view returns (bool);
}














interface IBaseInvestmentManager {
    // --- Events ---
    event File(bytes32 indexed what, address data);

    error FileUnrecognizedParam();
    error SenderNotVault();
    error AssetNotAllowed();
    error ExceedsMaxDeposit();

    /// @notice Updates contract parameters of type address.
    /// @param what The bytes32 representation of 'gateway' or 'poolManager'.
    /// @param data The new contract address.
    function file(bytes32 what, address data) external;

    /// @notice Converts the assets value to share decimals.
    function convertToShares(IBaseVault vault, uint256 _assets) external view returns (uint256 shares);

    /// @notice Converts the shares value to assets decimals.
    function convertToAssets(IBaseVault vault, uint256 _shares) external view returns (uint256 assets);

    /// @notice Returns the timestamp of the last share price update for a vaultAddr.
    function priceLastUpdated(IBaseVault vault) external view returns (uint64 lastUpdated);

    /// @notice Returns the PoolManager contract address.
    function poolManager() external view returns (IPoolManager poolManager);

    /// @notice The global escrow used for funds that are not yet free to be used for a specific pool
    function globalEscrow() external view returns (IEscrow escrow);

    /// @notice Escrow per pool. Funds are associated to a specific pool
    function poolEscrow(PoolId poolId) external view returns (IPoolEscrow);
}










interface IRedeemManager is IBaseInvestmentManager {
    event TriggerRedeemRequest(
        uint64 indexed poolId,
        bytes16 indexed scId,
        address user,
        address indexed asset,
        uint256 tokenId,
        uint128 shares
    );

    /// @notice Processes owner's share redemption after the epoch has been executed on the corresponding CP instance
    /// and the redeem order
    ///         has been successfully processed (partial fulfillment possible).
    ///         Assets are transferred from the escrow to the receiver. Amount of assets is computed based of the amount
    ///         of shares and the owner's share price.
    /// @dev    The shares required to fulfill the redemption were already locked in escrow on requestRedeem and burned
    ///         on fulfillRedeemRequest.
    ///         The assets required to fulfill the redemption have already been reserved in escrow on
    ///         fulfillRedeemtRequest.
    function redeem(IBaseVault vault, uint256 shares, address receiver, address owner)
        external
        returns (uint256 assets);

    /// @notice Processes owner's asset withdrawal after the epoch has been executed on the corresponding CP instance
    /// and the redeem order
    ///         has been successfully processed (partial fulfillment possible).
    ///         Assets are transferred from the escrow to the receiver. Amount of shares is computed based of the amount
    ///         of shares and the owner's share price.
    /// @dev    The shares required to fulfill the withdrawal were already locked in escrow on requestRedeem and burned
    ///         on fulfillRedeemRequest.
    ///         The assets required to fulfill the withdrawal have already been reserved in escrow on
    ///         fulfillRedeemtRequest.
    function withdraw(IBaseVault vault, uint256 assets, address receiver, address owner)
        external
        returns (uint256 shares);

    /// @notice Returns the max amount of shares based on the unclaimed number of assets after at least one successful
    ///         redeem order fulfillment on the corresponding CP instance.
    function maxRedeem(IBaseVault vault, address user) external view returns (uint256 shares);

    /// @notice Returns the max amount of assets a user can claim after at least one successful redeem order fulfillment
    ///         on the corresponding CP instance.
    function maxWithdraw(IBaseVault vault, address user) external view returns (uint256 assets);
}









enum VaultKind {
    /// @dev Refers to AsyncVault
    Async,
    /// @dev not yet supported
    Sync,
    /// @dev Refers to SyncDepositVault
    SyncDepositAsyncRedeem
}

/// @title  IVaultManager Interface
/// @notice Interface for the vault manager contract, needed to link/unlink vaults correctly.
/// @dev Must be implemented by all vault managers
interface IVaultManager {
    /// @notice Adds new vault for `poolId`, `scId` and `asset`.
    function addVault(PoolId poolId, ShareClassId scId, IBaseVault vault, address asset, AssetId assetId) external;

    /// @notice Removes `vault` from `who`'s authorized callers
    function removeVault(PoolId poolId, ShareClassId scId, IBaseVault vault, address asset, AssetId assetId) external;

    /// @notice Returns the address of the vault for a given pool, share class and asset
    function vaultByAssetId(PoolId poolId, ShareClassId scId, AssetId assetId)
        external
        view
        returns (IBaseVault vault);

    /// @notice Checks whether the vault is partially (a)synchronous and if so returns the address of the secondary
    /// manager.
    ///
    /// @param vault The address of vault that is checked
    /// @return vaultKind_ The kind of the vault
    /// @return secondaryManager The address of the secondary manager if the vault is partially (a)synchronous, else
    /// points to zero address
    function vaultKind(IBaseVault vault) external view returns (VaultKind vaultKind_, address secondaryManager);
}



interface IAsyncRedeemManager is IRedeemManager, IVaultManager {
    /// @notice Requests share redemption. Vaults have to request redemptions
    ///         from Centrifuge before actual asset payouts can be done. The redemption
    ///         requests are added to the order book on the corresponding CP instance. Once the next epoch is
    ///         executed on the corresponding CP instance, vaults can proceed with asset payouts
    ///         in case the order got fulfilled.
    /// @dev    The shares required to fulfill the redemption request have to be locked and are transferred from the
    ///         owner to the escrow, even though the asset payout can only happen after epoch execution.
    ///         The receiver becomes the owner of redeem request fulfillment.
    /// @param  source Deprecated
    function requestRedeem(IBaseVault vault, uint256 shares, address receiver, address owner, address source)
        external
        returns (bool);

    /// @notice Requests the cancellation of an pending redeem request. Vaults have to request the
    ///         cancellation of outstanding requests from Centrifuge before actual shares can be unlocked and
    ///         transferred to the owner.
    ///         While users have outstanding cancellation requests no new redeem requests can be submitted (exception:
    ///         trigger through governance).
    ///         Once the next epoch is executed on the corresponding CP instance, vaults can proceed with share payouts
    ///         if the orders could be cancelled successfully.
    /// @dev    The cancellation request might fail in case the pending redeem order already got fulfilled on
    ///         Centrifuge.
    function cancelRedeemRequest(IBaseVault vault, address owner, address source) external;

    /// @notice Processes owner's redeem request cancellation after the epoch has been executed on the corresponding CP
    /// instance and the
    ///         redeem order cancellation has been successfully processed (partial fulfillment possible).
    ///         Shares are transferred from the escrow to the receiver.
    /// @dev    The shares required to fulfill the claim have already been reserved for the owner in escrow on
    ///         fulfillCancelRedeemRequest.
    ///         Receiver has to pass all the share token restrictions in order to receive the shares.
    function claimCancelRedeemRequest(IBaseVault vault, address receiver, address owner)
        external
        returns (uint256 shares);

    /// @notice Indicates whether a user has pending redeem requests and returns the total share request value.
    function pendingRedeemRequest(IBaseVault vault, address user) external view returns (uint256 shares);

    /// @notice Indicates whether a user has pending redeem request cancellations.
    function pendingCancelRedeemRequest(IBaseVault vault, address user) external view returns (bool isPending);

    /// @notice Indicates whether a user has claimable redeem request cancellation and returns the total claim
    ///         value in shares.
    function claimableCancelRedeemRequest(IBaseVault vault, address user) external view returns (uint256 shares);
}


/// @notice Interface for the all vault contracts
/// @dev Must be implemented by all vaults
interface IBaseVault is IERC7540Operator, IERC7741, IERC7714, IERC7575, IRecoverable {
    error FileUnrecognizedParam();
    error NotEndorsed();
    error CannotSetSelfAsOperator();
    error ExpiredAuthorization();
    error AlreadyUsedAuthorization();
    error InvalidAuthorization();
    error InvalidController();
    error InsufficientBalance();
    error RequestRedeemFailed();
    error TransferFromFailed();

    event File(bytes32 indexed what, address data);

    /// @notice Identifier of the Centrifuge pool
    function poolId() external view returns (PoolId);

    /// @notice Identifier of the share class of the Centrifuge pool
    function scId() external view returns (ShareClassId);

    /// @notice Set msg.sender as operator of owner, to `approved` status
    /// @dev    MUST be called by endorsed sender
    function setEndorsedOperator(address owner, bool approved) external;

    /// @notice Returns the base investment manager contract handling the vault.
    /// @dev This naming MUST NOT change due to requirements of legacy vaults (v2)
    /// @return IBaseInvestmentManager The address of the manager contract that is between vault and gateway
    function manager() external view returns (IBaseInvestmentManager);
}

/**
 * @title  IAsyncRedeemVault
 * @dev    This is the specific set of interfaces used by the Centrifuge implementation of ERC7540,
 *         as a fully asynchronous Vault, with cancellation support, and authorize operator signature support.
 */
interface IAsyncRedeemVault is IERC7540Redeem, IERC7887Redeem, IBaseVault {
    event RedeemClaimable(address indexed controller, uint256 indexed requestId, uint256 assets, uint256 shares);
    event CancelRedeemClaimable(address indexed controller, uint256 indexed requestId, uint256 shares);

    /// @notice Callback when a redeem Request is triggered externally;
    function onRedeemRequest(address controller, address owner, uint256 shares) external;

    /// @notice Callback when a redeem Request becomes claimable
    function onRedeemClaimable(address owner, uint256 assets, uint256 shares) external;

    /// @notice Callback when a claim redeem Request becomes claimable
    function onCancelRedeemClaimable(address owner, uint256 shares) external;

    /// @notice Retrieve the asynchronous redeem manager
    function asyncRedeemManager() external view returns (IAsyncRedeemManager);
}

interface IAsyncVault is IERC7540Deposit, IERC7887Deposit, IAsyncRedeemVault {
    event DepositClaimable(address indexed controller, uint256 indexed requestId, uint256 assets, uint256 shares);
    event CancelDepositClaimable(address indexed controller, uint256 indexed requestId, uint256 assets);

    error InvalidOwner();
    error RequestDepositFailed();

    /// @notice Callback when a deposit Request becomes claimable
    function onDepositClaimable(address owner, uint256 assets, uint256 shares) external;

    /// @notice Callback when a claim deposit Request becomes claimable
    function onCancelDepositClaimable(address owner, uint256 assets) external;
}


interface IVaultFactory {
    error UnsupportedTokenId();

    /// @notice Deploys new vault for `poolId`, `scId` and `asset`.
    ///
    /// @param poolId Id of the pool. Id is one of the already supported pools.
    /// @param scId Id of the share class token. Id is one of the already supported share class tokens.
    /// @param asset Address of the underlying asset that is getting deposited inside the pool.
    /// @param asset Token id of the underlying asset that is getting deposited inside the pool. I.e. zero if asset
    /// corresponds to ERC20 or non-zero if asset corresponds to ERC6909.
    /// @param token Address of the share class token that is getting issues against the deposited asset.
    /// @param wards_ Address which can call methods behind authorized only.
    function newVault(
        PoolId poolId,
        ShareClassId scId,
        address asset,
        uint256 tokenId,
        IShareToken token,
        address[] calldata wards_
    ) external returns (IBaseVault);
}



/// @dev Centrifuge pools
struct Pool {
    uint256 createdAt;
    mapping(ShareClassId => ShareClassDetails) shareClasses;
}

/// @dev Each Centrifuge pool is associated to 1 or more shar classes
struct ShareClassDetails {
    IShareToken shareToken;
    /// @dev Each share class has an individual price per share class unit in pool denomination (POOL_UNIT/SHARE_UNIT)
    Price pricePoolPerShare;
    /// @dev Each share class can have multiple vaults deployed,
    ///      multiple vaults can be linked to the same asset.
    ///      A vault in this storage DOES NOT mean the vault can be used
    mapping(address => mapping(uint256 => IBaseVault[])) vaults;
    /// @dev For each share class, we store the price per pool unit in asset denomination (POOL_UNIT/ASSET_UNIT)
    mapping(address => mapping(uint256 => Price)) pricePoolPerAsset;
}

/// @dev Price struct that contains a price, the timestamp at which it was computed and the max age of the price.
struct Price {
    uint128 price;
    uint64 computedAt;
    uint64 maxAge;
}

/// @dev Checks if a price is valid. Returns false if price is 0 or computedAt is 0. Otherwise checks for block
/// timestamp <= computedAt + maxAge
function isValid(Price memory price) view returns (bool) {
    if (price.computedAt != 0 && price.price != 0) {
        return block.timestamp <= price.computedAt + price.maxAge;
    } else {
        return false;
    }
}

/// @dev Retrieves the price as an D18 from the struct
function asPrice(Price memory price) pure returns (D18) {
    return d18(price.price);
}

using {isValid, asPrice} for Price global;

struct VaultDetails {
    /// @dev AssetId of the asset
    AssetId assetId;
    /// @dev Address of the asset
    address asset;
    /// @dev TokenId of the asset - zero if asset is ERC20, non-zero if asset is ERC6909
    uint256 tokenId;
    /// @dev Whether this wrapper conforms to the IERC20Wrapper interface
    bool isWrapper;
    /// @dev Whether the vault is linked to a share class atm
    bool isLinked;
}

struct AssetIdKey {
    /// @dev The address of the asset
    address asset;
    /// @dev The ERC6909 token id or 0, if the underlying asset is an ERC20
    uint256 tokenId;
}

interface IPoolManager {
    event File(bytes32 indexed what, address data);
    event RegisterAsset(
        AssetId indexed assetId,
        address indexed asset,
        uint256 indexed tokenId,
        string name,
        string symbol,
        uint8 decimals
    );
    event File(bytes32 indexed what, address factory, bool status);
    event AddPool(PoolId indexed poolId);
    event AddShareClass(PoolId indexed poolId, ShareClassId indexed scId, IShareToken token);
    event DeployVault(
        PoolId indexed poolId,
        ShareClassId indexed scId,
        address indexed asset,
        uint256 tokenId,
        IVaultFactory factory,
        IBaseVault vault
    );
    event PriceUpdate(
        PoolId indexed poolId,
        ShareClassId indexed scId,
        address indexed asset,
        uint256 tokenId,
        uint256 price,
        uint64 computedAt
    );
    event PriceUpdate(PoolId indexed poolId, ShareClassId indexed scId, uint256 price, uint64 computedAt);
    event TransferShares(
        uint16 centrifugeId,
        PoolId indexed poolId,
        ShareClassId indexed scId,
        address indexed sender,
        bytes32 destinationAddress,
        uint128 amount
    );
    event UpdateContract(PoolId indexed poolId, ShareClassId indexed scId, address target, bytes payload);
    event LinkVault(
        PoolId indexed poolId, ShareClassId indexed scId, address indexed asset, uint256 tokenId, IBaseVault vault
    );
    event UnlinkVault(
        PoolId indexed poolId, ShareClassId indexed scId, address indexed asset, uint256 tokenId, IBaseVault vault
    );
    event UpdateMaxSharePriceAge(PoolId indexed poolId, ShareClassId indexed scId, uint64 maxPriceAge);
    event UpdateMaxAssetPriceAge(
        PoolId indexed poolId, ShareClassId indexed scId, address indexed asset, uint256 tokenId, uint64 maxPriceAge
    );

    error FileUnrecognizedParam();
    error TooFewDecimals();
    error TooManyDecimals();
    error PoolAlreadyAdded();
    error InvalidPool();
    error ShareClassAlreadyRegistered();
    error InvalidHook();
    error OldMetadata();
    error CannotSetOlderPrice();
    error OldHook();
    error UnknownVault();
    error UnknownAsset();
    error MalformedVaultUpdateMessage();
    error UnknownToken();
    error InvalidFactory();
    error InvalidPrice();
    error AssetMissingDecimals();
    error ShareTokenDoesNotExist();
    error CrossChainTransferNotAllowed();
    error ShareTokenTransferFailed();
    error TransferFromFailed();

    /// @notice Returns the asset address and tokenId associated with a given asset id.
    /// @dev Reverts if asset id does not exist
    ///
    /// @param assetId The underlying internal uint128 assetId.
    /// @return asset The address of the asset linked to the given asset id.
    /// @return tokenId The token id corresponding to the asset, i.e. zero if ERC20 or non-zero if ERC6909.
    function idToAsset(AssetId assetId) external view returns (address asset, uint256 tokenId);

    /// @notice Returns assetId given the asset address and tokenId.
    /// @dev Reverts if asset id does not exist
    ///
    /// @param asset The address of the asset linked to the given asset id.
    /// @param tokenId The token id corresponding to the asset, i.e. zero if ERC20 or non-zero if ERC6909.
    /// @return assetId The underlying internal uint128 assetId.
    function assetToId(address asset, uint256 tokenId) external view returns (AssetId assetId);

    /// @notice Updates a contract parameter
    /// @param what Accepts a bytes32 representation of 'gateway', 'investmentManager', 'tokenFactory',
    ///                'vaultFactory', or 'gasService'
    function file(bytes32 what, address data) external;

    /// @notice Updates a contract parameter
    /// @param what Accepts a bytes32 representation of 'vaultFactory'
    function file(bytes32 what, address factory, bool status) external;

    /// @notice transfers share class tokens to a cross-chain recipient address
    /// @dev    To transfer to evm chains, pad a 20 byte evm address with 12 bytes of 0
    /// @param  centrifugeId The destination chain id
    /// @param  poolId The centrifuge pool id
    /// @param  scId The share class id
    /// @param  receiver A bytes32 representation of the receiver address
    /// @param  amount The amount of tokens to transfer
    function transferShares(uint16 centrifugeId, PoolId poolId, ShareClassId scId, bytes32 receiver, uint128 amount)
        external
        payable;

    /// @notice Registers an ERC-20 or ERC-6909 asset in another chain.
    /// @dev `decimals()` MUST return a `uint8` value between 2 and 18.
    /// @dev `name()` and `symbol()` MAY return no values.
    ///
    /// @param centrifugeId The centrifuge id of chain to where the shares are transferred
    /// @param asset The address of the asset to be registered
    /// @param tokenId The token id corresponding to the asset, i.e. zero if ERC20 or non-zero if ERC6909.
    /// @return assetId The underlying internal uint128 assetId.
    function registerAsset(uint16 centrifugeId, address asset, uint256 tokenId)
        external
        payable
        returns (AssetId assetId);

    /// @notice Deploys a new vault
    ///
    /// @param poolId The pool id
    /// @param scId The share class id
    /// @param assetId The asset id for which we want to deploy a vault
    /// @param factory The address of the corresponding vault factory
    /// @return address The address of the deployed vault
    function deployVault(PoolId poolId, ShareClassId scId, AssetId assetId, IVaultFactory factory)
        external
        returns (IBaseVault);

    /// @notice Links a deployed vault to the given pool, share class and asset.
    ///
    /// @param poolId The pool id
    /// @param scId The share class id
    /// @param assetId The asset id for which we want to deploy a vault
    /// @param vault The address of the deployed vault
    function linkVault(PoolId poolId, ShareClassId scId, AssetId assetId, IBaseVault vault) external;

    /// @notice Removes the link between a vault and the given pool, share class and asset.
    ///
    /// @param poolId The pool id
    /// @param scId The share class id
    /// @param assetId The asset id for which we want to deploy a vault
    /// @param vault The address of the deployed vault
    function unlinkVault(PoolId poolId, ShareClassId scId, AssetId assetId, IBaseVault vault) external;

    /// @notice Returns whether the given pool id is active
    function isPoolActive(PoolId poolId) external view returns (bool);

    /// @notice Returns the share class token for a given pool and share class id.
    /// @dev Reverts if share class does not exists
    ///
    /// @param poolId The pool id
    /// @param scId The share class id
    /// @return address The address of the share token
    function shareToken(PoolId poolId, ShareClassId scId) external view returns (IShareToken);

    /// @notice Function to get the details of a vault
    /// @dev    Reverts if vault does not exist
    ///
    /// @param vault The address of the vault to be checked for
    /// @return details The details of the vault including the underlying asset address, token id, asset id
    function vaultDetails(IBaseVault vault) external view returns (VaultDetails memory details);

    /// @notice Checks whether a given asset-vault pair is eligible for investing into a share class of a pool
    ///
    /// @param poolId The pool id
    /// @param scId The share class id
    /// @param asset The address of the asset
    /// @param vault The address of the vault
    /// @return bool Whether vault is to a share class
    function isLinked(PoolId poolId, ShareClassId scId, address asset, IBaseVault vault) external view returns (bool);

    /// @notice Returns the price per share for a given pool, share class, asset, and asset id. The provided price is
    /// defined as ASSET_UNIT/SHARE_UNIT.
    /// @dev Conditionally checks if price is valid.
    ///
    /// @dev NOTE: Should never be used for calculating amounts due to precision loss. Instead, please refer to
    /// conversion relying on pricePoolPerShare and pricePoolPerAsset. See PricingLib for more information.
    ///
    /// @param poolId The pool id
    /// @param scId The share class id
    /// @param assetId The asset id for which we want to know the ASSET_UNIT/SHARE_UNIT price
    /// @param checkValidity Whether to check if the price is valid
    /// @return price The asset price per share
    /// @return computedAt The timestamp at which the price was computed
    function priceAssetPerShare(PoolId poolId, ShareClassId scId, AssetId assetId, bool checkValidity)
        external
        view
        returns (D18 price, uint64 computedAt);

    /// @notice Returns the price per share for a given pool and share class. The Provided price is defined as
    /// POOL_UNIT/SHARE_UNIT.
    /// @dev Conditionally checks if price is valid.
    ///
    /// @param poolId The pool id
    /// @param scId The share class id
    /// @param checkValidity Whether to check if the price is valid
    /// @return price The pool price per share
    /// @return computedAt The timestamp at which the price was computed
    function pricePoolPerShare(PoolId poolId, ShareClassId scId, bool checkValidity)
        external
        view
        returns (D18 price, uint64 computedAt);

    /// @notice Returns the price per asset for a given pool, share class and the underlying asset id. The Provided
    /// price is defined as POOL_UNIT/ASSET_UNIT.
    /// @dev Conditionally checks if price is valid.
    ///
    /// @param poolId The pool id
    /// @param scId The share class id
    /// @param assetId The asset id for which we want to know the POOL_UNIT/ASSET_UNIT.
    /// @param checkValidity Whether to check if the price is valid
    /// @return price The pool price per asset unit
    /// @return computedAt The timestamp at which the price was computed
    function pricePoolPerAsset(PoolId poolId, ShareClassId scId, AssetId assetId, bool checkValidity)
        external
        view
        returns (D18 price, uint64 computedAt);

    /// @notice Returns the both prices per pool for a given pool, share class and the underlying asset id. The Provided
    /// prices is defined as POOL_UNIT/ASSET_UNIT and POOL_UNIT/SHARE_UNIT.
    /// @dev Conditionally checks if prices are valid.
    ///
    /// @param poolId The pool id
    /// @param scId The share class id
    /// @param assetId The asset id for which we want to know pool price per asset
    /// @param checkValidity Whether to check if the prices are valid
    /// @return pricePoolPerAsset The pool price per asset unit, i.e. POOL_UNIT/ASSET_UNIT
    /// @return pricePoolPerShare The pool price per share unit, i.e. POOL_UNIT/SHARE_UNIT
    function pricesPoolPer(PoolId poolId, ShareClassId scId, AssetId assetId, bool checkValidity)
        external
        view
        returns (D18 pricePoolPerAsset, D18 pricePoolPerShare);
}

// Failed to resolve import: import {BeforeSwapDelta} from "v4-core/src/types/BeforeSwapDelta.sol";

/**
 * @dev Base hook implementation.
 *
 * This contract defines all hook entry points, as well as security and permission helpers.
 * Based on the https://github.com/Uniswap/v4-periphery/blob/main/src/base/hooks/BaseHook.sol[Uniswap v4 periphery implementation].
 *
 * NOTE: Hook entry points must be overiden and implemented by the inheriting hook to be used. Their respective
 * flags must be set to true in the `getHookPermissions` function as well.
 *
 * WARNING: This is experimental software and is provided on an "as is" and "as available" basis. We do
 * not give any warranties and will not be liable for any losses incurred through any use of this code
 * base.
 *
 * _Available since v0.1.0_
 */
abstract contract BaseHook is IHooks {
    IPoolManager public immutable poolManager;

    /**
     * @dev The hook is not the caller.
     */
    error NotSelf();

    /**
     * @dev The pool is not authorized to use this hook.
     */
    error InvalidPool();

    /**
     * @dev The hook function is not implemented.
     */
    error HookNotImplemented();

    /**
     * @notice Thrown when calling unlockCallback where the caller is not `PoolManager`.
     */
    error NotPoolManager();

    /**
     * @dev Set the pool manager and check that the hook address matches the expected permissions and flags.
     */
    constructor(IPoolManager _poolManager) {
        poolManager = _poolManager;
        validateHookAddress(this);
    }

    /**
     * @notice Only allow calls from the `PoolManager` contract
     */
    modifier onlyPoolManager() {
        if (msg.sender != address(poolManager)) revert NotPoolManager();
        _;
    }

    /**
     * @dev Restrict the function to only be callable by the hook itself.
     */
    modifier onlySelf() {
        if (msg.sender != address(this)) revert NotSelf();
        _;
    }

    /**
     * @dev Restrict the function to only be called for a valid pool.
     */
    modifier onlyValidPools(IHooks hooks) {
        if (hooks != this) revert InvalidPool();
        _;
    }

    /**
     * @dev Get the hook permissions to signal which hook functions are to be implemented.
     *
     * Used at deployment to validate the address correctly represents the expected permissions.
     *
     * @return permissions The hook permissions.
     */
    function getHookPermissions() public pure virtual returns (Hooks.Permissions memory permissions);

    /**
     * @dev Validate the hook address against the expected permissions.
     */
    function validateHookAddress(BaseHook hook) internal pure {
        Hooks.validateHookPermissions(hook, getHookPermissions());
    }

    /**
     * @inheritdoc IHooks
     */
    function beforeInitialize(address sender, PoolKey calldata key, uint160 sqrtPriceX96)
        external
        virtual
        onlyPoolManager
        returns (bytes4)
    {
        return _beforeInitialize(sender, key, sqrtPriceX96);
    }

    /**
     * @dev Hook implementation for `beforeInitialize`, to be overriden by the inheriting hook. The
     * flag must be set to true in the `getHookPermissions` function.
     */
    function _beforeInitialize(address, PoolKey calldata, uint160) internal virtual returns (bytes4) {
        revert HookNotImplemented();
    }

    /**
     * @inheritdoc IHooks
     */
    function afterInitialize(address sender, PoolKey calldata key, uint160 sqrtPriceX96, int24 tick)
        external
        virtual
        onlyPoolManager
        returns (bytes4)
    {
        return _afterInitialize(sender, key, sqrtPriceX96, tick);
    }

    /**
     * @dev Hook implementation for `afterInitialize`, to be overriden by the inheriting hook. The
     * flag must be set to true in the `getHookPermissions` function.
     */
    function _afterInitialize(address, PoolKey calldata, uint160, int24) internal virtual returns (bytes4) {
        revert HookNotImplemented();
    }

    /**
     * @inheritdoc IHooks
     */
    function beforeAddLiquidity(
        address sender,
        PoolKey calldata key,
        IPoolManager.ModifyLiquidityParams calldata params,
        bytes calldata hookData
    ) external virtual onlyPoolManager returns (bytes4) {
        return _beforeAddLiquidity(sender, key, params, hookData);
    }

    /**
     * @dev Hook implementation for `beforeAddLiquidity`, to be overriden by the inheriting hook. The
     * flag must be set to true in the `getHookPermissions` function.
     */
    function _beforeAddLiquidity(address, PoolKey calldata, IPoolManager.ModifyLiquidityParams calldata, bytes calldata)
        internal
        virtual
        returns (bytes4)
    {
        revert HookNotImplemented();
    }

    /**
     * @inheritdoc IHooks
     */
    function beforeRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        IPoolManager.ModifyLiquidityParams calldata params,
        bytes calldata hookData
    ) external virtual onlyPoolManager returns (bytes4) {
        return _beforeRemoveLiquidity(sender, key, params, hookData);
    }

    /**
     * @dev Hook implementation for `beforeRemoveLiquidity`, to be overriden by the inheriting hook. The
     * flag must be set to true in the `getHookPermissions` function.
     */
    function _beforeRemoveLiquidity(
        address,
        PoolKey calldata,
        IPoolManager.ModifyLiquidityParams calldata,
        bytes calldata
    ) internal virtual returns (bytes4) {
        revert HookNotImplemented();
    }

    /**
     * @inheritdoc IHooks
     */
    function afterAddLiquidity(
        address sender,
        PoolKey calldata key,
        IPoolManager.ModifyLiquidityParams calldata params,
        BalanceDelta delta0,
        BalanceDelta delta1,
        bytes calldata hookData
    ) external virtual onlyPoolManager returns (bytes4, BalanceDelta) {
        return _afterAddLiquidity(sender, key, params, delta0, delta1, hookData);
    }

    /**
     * @dev Hook implementation for `afterAddLiquidity`, to be overriden by the inheriting hook. The
     * flag must be set to true in the `getHookPermissions` function.
     */
    function _afterAddLiquidity(
        address,
        PoolKey calldata,
        IPoolManager.ModifyLiquidityParams calldata,
        BalanceDelta,
        BalanceDelta,
        bytes calldata
    ) internal virtual returns (bytes4, BalanceDelta) {
        revert HookNotImplemented();
    }

    /**
     * @inheritdoc IHooks
     */
    function afterRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        IPoolManager.ModifyLiquidityParams calldata params,
        BalanceDelta delta0,
        BalanceDelta delta1,
        bytes calldata hookData
    ) external virtual onlyPoolManager returns (bytes4, BalanceDelta) {
        return _afterRemoveLiquidity(sender, key, params, delta0, delta1, hookData);
    }

    /**
     * @dev Hook implementation for `afterRemoveLiquidity`, to be overriden by the inheriting hook. The
     * flag must be set to true in the `getHookPermissions` function.
     */
    function _afterRemoveLiquidity(
        address,
        PoolKey calldata,
        IPoolManager.ModifyLiquidityParams calldata,
        BalanceDelta,
        BalanceDelta,
        bytes calldata
    ) internal virtual returns (bytes4, BalanceDelta) {
        revert HookNotImplemented();
    }

    /**
     * @inheritdoc IHooks
     */
    function beforeSwap(
        address sender,
        PoolKey calldata key,
        IPoolManager.SwapParams calldata params,
        bytes calldata hookData
    ) external virtual onlyPoolManager returns (bytes4, BeforeSwapDelta, uint24) {
        return _beforeSwap(sender, key, params, hookData);
    }

    /**
     * @dev Hook implementation for `beforeSwap`, to be overriden by the inheriting hook. The
     * flag must be set to true in the `getHookPermissions` function.
     */
    function _beforeSwap(address, PoolKey calldata, IPoolManager.SwapParams calldata, bytes calldata)
        internal
        virtual
        returns (bytes4, BeforeSwapDelta, uint24)
    {
        revert HookNotImplemented();
    }

    /**
     * @inheritdoc IHooks
     */
    function afterSwap(
        address sender,
        PoolKey calldata key,
        IPoolManager.SwapParams calldata params,
        BalanceDelta delta,
        bytes calldata hookData
    ) external virtual onlyPoolManager returns (bytes4, int128) {
        return _afterSwap(sender, key, params, delta, hookData);
    }

    /**
     * @dev Hook implementation for `afterSwap`, to be overriden by the inheriting hook. The
     * flag must be set to true in the `getHookPermissions` function.
     */
    function _afterSwap(address, PoolKey calldata, IPoolManager.SwapParams calldata, BalanceDelta, bytes calldata)
        internal
        virtual
        returns (bytes4, int128)
    {
        revert HookNotImplemented();
    }

    /**
     * @inheritdoc IHooks
     */
    function beforeDonate(
        address sender,
        PoolKey calldata key,
        uint256 amount0,
        uint256 amount1,
        bytes calldata hookData
    ) external virtual onlyPoolManager returns (bytes4) {
        return _beforeDonate(sender, key, amount0, amount1, hookData);
    }

    /**
     * @dev Hook implementation for `beforeDonate`, to be overriden by the inheriting hook. The
     * flag must be set to true in the `getHookPermissions` function.
     */
    function _beforeDonate(address, PoolKey calldata, uint256, uint256, bytes calldata)
        internal
        virtual
        returns (bytes4)
    {
        revert HookNotImplemented();
    }

    /**
     * @inheritdoc IHooks
     */
    function afterDonate(
        address sender,
        PoolKey calldata key,
        uint256 amount0,
        uint256 amount1,
        bytes calldata hookData
    ) external virtual onlyPoolManager returns (bytes4) {
        return _afterDonate(sender, key, amount0, amount1, hookData);
    }

    /**
     * @dev Hook implementation for `afterDonate`, to be overriden by the inheriting hook. The
     * flag must be set to true in the `getHookPermissions` function.
     */
    function _afterDonate(address, PoolKey calldata, uint256, uint256, bytes calldata)
        internal
        virtual
        returns (bytes4)
    {
        revert HookNotImplemented();
    }
}


// Failed to resolve import: // Failed to resolve import: import {Hooks} from "v4-core/src/libraries/Hooks.sol";




// Failed to resolve import: // Failed to resolve import: import {BeforeSwapDelta, BeforeSwapDeltaLibrary} from "v4-core/src/types/BeforeSwapDelta.sol";

// OpenZeppelin Uniswap Hooks (last updated v0.1.0) (src/utils/CurrencySettler.sol)















/**
 * @dev Collection of functions related to the address type
 */
library Address {
    /**
     * @dev Returns true if `account` is a contract.
     *
     * [IMPORTANT]
     * ====
     * It is unsafe to assume that an address for which this function returns
     * false is an externally-owned account (EOA) and not a contract.
     *
     * Among others, `isContract` will return false for the following
     * types of addresses:
     *
     *  - an externally-owned account
     *  - a contract in construction
     *  - an address where a contract will be created
     *  - an address where a contract lived, but was destroyed
     * ====
     */
    function isContract(address account) internal view returns (bool) {
        // This method relies on extcodesize, which returns 0 for contracts in
        // construction, since the code is only stored at the end of the
        // constructor execution.

        uint256 size;
        assembly {
            size := extcodesize(account)
        }
        return size > 0;
    }

    /**
     * @dev Replacement for Solidity's `transfer`: sends `amount` wei to
     * `recipient`, forwarding all available gas and reverting on errors.
     *
     * https://eips.ethereum.org/EIPS/eip-1884[EIP1884] increases the gas cost
     * of certain opcodes, possibly making contracts go over the 2300 gas limit
     * imposed by `transfer`, making them unable to receive funds via
     * `transfer`. {sendValue} removes this limitation.
     *
     * https://diligence.consensys.net/posts/2019/09/stop-using-soliditys-transfer-now/[Learn more].
     *
     * IMPORTANT: because control is transferred to `recipient`, care must be
     * taken to not create reentrancy vulnerabilities. Consider using
     * {ReentrancyGuard} or the
     * https://solidity.readthedocs.io/en/v0.5.11/security-considerations.html#use-the-checks-effects-interactions-pattern[checks-effects-interactions pattern].
     */
    function sendValue(address payable recipient, uint256 amount) internal {
        require(address(this).balance >= amount, "Address: insufficient balance");

        (bool success, ) = recipient.call{value: amount}("");
        require(success, "Address: unable to send value, recipient may have reverted");
    }

    /**
     * @dev Performs a Solidity function call using a low level `call`. A
     * plain `call` is an unsafe replacement for a function call: use this
     * function instead.
     *
     * If `target` reverts with a revert reason, it is bubbled up by this
     * function (like regular Solidity function calls).
     *
     * Returns the raw returned data. To convert to the expected return value,
     * use https://solidity.readthedocs.io/en/latest/units-and-global-variables.html?highlight=abi.decode#abi-encoding-and-decoding-functions[`abi.decode`].
     *
     * Requirements:
     *
     * - `target` must be a contract.
     * - calling `target` with `data` must not revert.
     *
     * _Available since v3.1._
     */
    function functionCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionCall(target, data, "Address: low-level call failed");
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`], but with
     * `errorMessage` as a fallback revert reason when `target` reverts.
     *
     * _Available since v3.1._
     */
    function functionCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal returns (bytes memory) {
        return functionCallWithValue(target, data, 0, errorMessage);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but also transferring `value` wei to `target`.
     *
     * Requirements:
     *
     * - the calling contract must have an ETH balance of at least `value`.
     * - the called Solidity function must be `payable`.
     *
     * _Available since v3.1._
     */
    function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value
    ) internal returns (bytes memory) {
        return functionCallWithValue(target, data, value, "Address: low-level call with value failed");
    }

    /**
     * @dev Same as {xref-Address-functionCallWithValue-address-bytes-uint256-}[`functionCallWithValue`], but
     * with `errorMessage` as a fallback revert reason when `target` reverts.
     *
     * _Available since v3.1._
     */
    function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value,
        string memory errorMessage
    ) internal returns (bytes memory) {
        require(address(this).balance >= value, "Address: insufficient balance for call");
        require(isContract(target), "Address: call to non-contract");

        (bool success, bytes memory returndata) = target.call{value: value}(data);
        return _verifyCallResult(success, returndata, errorMessage);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but performing a static call.
     *
     * _Available since v3.3._
     */
    function functionStaticCall(address target, bytes memory data) internal view returns (bytes memory) {
        return functionStaticCall(target, data, "Address: low-level static call failed");
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-string-}[`functionCall`],
     * but performing a static call.
     *
     * _Available since v3.3._
     */
    function functionStaticCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal view returns (bytes memory) {
        require(isContract(target), "Address: static call to non-contract");

        (bool success, bytes memory returndata) = target.staticcall(data);
        return _verifyCallResult(success, returndata, errorMessage);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but performing a delegate call.
     *
     * _Available since v3.4._
     */
    function functionDelegateCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionDelegateCall(target, data, "Address: low-level delegate call failed");
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-string-}[`functionCall`],
     * but performing a delegate call.
     *
     * _Available since v3.4._
     */
    function functionDelegateCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal returns (bytes memory) {
        require(isContract(target), "Address: delegate call to non-contract");

        (bool success, bytes memory returndata) = target.delegatecall(data);
        return _verifyCallResult(success, returndata, errorMessage);
    }

    function _verifyCallResult(
        bool success,
        bytes memory returndata,
        string memory errorMessage
    ) private pure returns (bytes memory) {
        if (success) {
            return returndata;
        } else {
            // Look for revert reason and bubble it up if present
            if (returndata.length > 0) {
                // The easiest way to bubble the revert reason is using memory via assembly

                assembly {
                    let returndata_size := mload(returndata)
                    revert(add(32, returndata), returndata_size)
                }
            } else {
                revert(errorMessage);
            }
        }
    }
}


/**
 * @title SafeERC20
 * @dev Wrappers around ERC20 operations that throw on failure (when the token
 * contract returns false). Tokens that return no value (and instead revert or
 * throw on failure) are also supported, non-reverting calls are assumed to be
 * successful.
 * To use this library you can add a `using SafeERC20 for IERC20;` statement to your contract,
 * which allows you to call the safe operations as `token.safeTransfer(...)`, etc.
 */
library SafeERC20 {
    using Address for address;

    function safeTransfer(
        IERC20 token,
        address to,
        uint256 value
    ) internal {
        _callOptionalReturn(token, abi.encodeWithSelector(token.transfer.selector, to, value));
    }

    function safeTransferFrom(
        IERC20 token,
        address from,
        address to,
        uint256 value
    ) internal {
        _callOptionalReturn(token, abi.encodeWithSelector(token.transferFrom.selector, from, to, value));
    }

    /**
     * @dev Deprecated. This function has issues similar to the ones found in
     * {IERC20-approve}, and its usage is discouraged.
     *
     * Whenever possible, use {safeIncreaseAllowance} and
     * {safeDecreaseAllowance} instead.
     */
    function safeApprove(
        IERC20 token,
        address spender,
        uint256 value
    ) internal {
        // safeApprove should only be called when setting an initial allowance,
        // or when resetting it to zero. To increase and decrease it, use
        // 'safeIncreaseAllowance' and 'safeDecreaseAllowance'
        require(
            (value == 0) || (token.allowance(address(this), spender) == 0),
            "SafeERC20: approve from non-zero to non-zero allowance"
        );
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, value));
    }

    function safeIncreaseAllowance(
        IERC20 token,
        address spender,
        uint256 value
    ) internal {
        uint256 newAllowance = token.allowance(address(this), spender) + value;
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, newAllowance));
    }

    function safeDecreaseAllowance(
        IERC20 token,
        address spender,
        uint256 value
    ) internal {
        unchecked {
            uint256 oldAllowance = token.allowance(address(this), spender);
            require(oldAllowance >= value, "SafeERC20: decreased allowance below zero");
            uint256 newAllowance = oldAllowance - value;
            _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, newAllowance));
        }
    }

    /**
     * @dev Imitates a Solidity high-level call (i.e. a regular function call to a contract), relaxing the requirement
     * on the return value: the return value is optional (but if data is returned, it must not be false).
     * @param token The token targeted by the call.
     * @param data The call data (encoded using abi.encode or one of its variants).
     */
    function _callOptionalReturn(IERC20 token, bytes memory data) private {
        // We need to perform a low level call here, to bypass Solidity's return data size checking mechanism, since
        // we're implementing it ourselves. We use {Address.functionCall} to perform this call, which verifies that
        // the target address contains contract code and also asserts for success in the low-level call.

        bytes memory returndata = address(token).functionCall(data, "SafeERC20: low-level call failed");
        if (returndata.length > 0) {
            // Return data is optional
            require(abi.decode(returndata, (bool)), "SafeERC20: ERC20 operation did not succeed");
        }
    }
}


/**
 * @dev Library used to interact with the `PoolManager` to settle any open deltas.
 * To settle a positive delta (a credit to the user), a user may take or mint.
 * To settle a negative delta (a debt on the user), a user may transfer or burn to pay off a debt.
 *
 * Based on the https://github.com/Uniswap/v4-core/blob/main/test/utils/CurrencySettler.sol[Uniswap v4 test utils implementation].
 *
 * NOTE: Deltas are synced before any ERC-20 transfers in {settle} function.
 */
library CurrencySettler {
    using SafeERC20 for IERC20;

    /**
     * @notice Settle (pay) a currency to the `PoolManager`
     * @param currency Currency to settle
     * @param poolManager `PoolManager` to settle to
     * @param payer Address of the payer, which can be the hook itself or an external address.
     * @param amount Amount to send
     * @param burn If true, burn the ERC-6909 token, otherwise transfer ERC-20 to the `PoolManager`
     */
    function settle(Currency currency, IPoolManager poolManager, address payer, uint256 amount, bool burn) internal {
        // Early return when amount is 0 given that some tokens may revert in this case
        if (amount == 0) return;

        // For native currencies or burns, calling sync is not required
        // Short circuit for ERC-6909 burns to support ERC-6909-wrapped native tokens
        if (burn) {
            poolManager.burn(payer, currency.toId(), amount);
        } else if (currency.isAddressZero()) {
            poolManager.sync(currency);
            poolManager.settle{value: amount}();
        } else {
            poolManager.sync(currency);
            if (payer != address(this)) {
                IERC20(Currency.unwrap(currency)).safeTransferFrom(payer, address(poolManager), amount);
            } else {
                IERC20(Currency.unwrap(currency)).safeTransfer(address(poolManager), amount);
            }
            poolManager.settle();
        }
    }

    /**
     * @notice Take (receive) a currency from the `PoolManager`
     * @param currency Currency to take
     * @param poolManager `PoolManager` to take from
     * @param recipient Address of the recipient of the ERC-6909 or ERC-20 token.
     * @param amount Amount to receive
     * @param claims If true, mint the ERC-6909 token, otherwise transfer ERC-20 from the `PoolManager` to recipient
     */
    function take(Currency currency, IPoolManager poolManager, address recipient, uint256 amount, bool claims)
        internal
    {
        // Early return when amount is 0 given that some tokens may revert in this case
        if (amount == 0) return;

        claims ? poolManager.mint(recipient, currency.toId(), amount) : poolManager.take(currency, recipient, amount);
    }
}



// OpenZeppelin Uniswap Hooks (last updated v0.1.0) (src/interfaces/IHookEvents.sol)



/**
 * @dev Interface for standard hook events emission.
 *
 * NOTE: Hooks should inherit from this interface to standardized event emission.
 */
interface IHookEvents {
    /**
     * @dev Event emitted when a swap is executed.
     */
    event HookSwap(
        bytes32 indexed id,
        address indexed sender,
        int128 amount0,
        int128 amount1,
        uint128 hookLPfeeAmount0,
        uint128 hookLPfeeAmount1
    );

    /**
     * @dev Event emitted when a fee is collected.
     */
    event HookFee(bytes32 indexed id, address indexed sender, uint128 feeAmount0, uint128 feeAmount1);

    /**
     * @dev Event emitted when a liquidity modification is executed.
     */
    event HookModifyLiquidity(bytes32 indexed id, address indexed sender, int128 amount0, int128 amount1);

    /**
     * @dev Event emitted when a bonus is added to a swap.
     */
    event HookBonus(bytes32 indexed id, uint128 amount0, uint128 amount1);
}


/**
 * @dev Base implementation for dynamic fees applied after swaps.
 *
 * In order to use this hook, the inheriting contract must define the {_getTargetOutput} and
 * {_afterSwapHandler} functions. The {_getTargetOutput} function returns the target output to
 * apply to the swap depending on the given apply flag. The {_afterSwapHandler} function is called
 * after the target output is applied to the swap and currency amount is received.
 *
 * WARNING: This is experimental software and is provided on an "as is" and "as available" basis. We do
 * not give any warranties and will not be liable for any losses incurred through any use of this code
 * base.
 *
 * _Available since v0.1.0_
 */
abstract contract BaseDynamicAfterFee is BaseHook, IHookEvents {
    using SafeCast for uint256;
    using CurrencySettler for Currency;

    uint256 internal _targetOutput;

    bool internal _applyTargetOutput;

    /**
     * @dev Target output exceeds swap amount.
     */
    error TargetOutputExceeds();

    /**
     * @dev Set the `PoolManager` address.
     */
    constructor(IPoolManager _poolManager) BaseHook(_poolManager) {}

    /**
     * @dev Sets the target output and apply flag to be used in the `afterSwap` hook.
     *
     * NOTE: The target output is reset to 0 in the `afterSwap` hook regardless of the apply flag.
     */
    function _beforeSwap(
        address sender,
        PoolKey calldata key,
        IPoolManager.SwapParams calldata params,
        bytes calldata hookData
    ) internal virtual override returns (bytes4, BeforeSwapDelta, uint24) {
        // Get the target output and apply flag
        (uint256 targetOutput, bool applyTargetOutput) = _getTargetOutput(sender, key, params, hookData);

        // Set the target output and apply flag, overriding any previous values.
        _applyTargetOutput = applyTargetOutput;
        _targetOutput = targetOutput;

        return (this.beforeSwap.selector, BeforeSwapDeltaLibrary.ZERO_DELTA, 0);
    }

    /**
     * @dev Apply the target output to the unspecified currency of the swap using fees.
     * The fees are minted as ERC-6909 tokens, which can then be redeemed in the
     * {_afterSwapHandler} function. Note that if the underlying unspecified currency
     * is native, the implementing contract must ensure that it can receive native tokens
     * when redeeming.
     *
     * NOTE: The target output is reset to 0, both when the apply flag is set to `false`
     * and when set to `true`.
     */
    function _afterSwap(
        address sender,
        PoolKey calldata key,
        IPoolManager.SwapParams calldata params,
        BalanceDelta delta,
        bytes calldata
    ) internal virtual override returns (bytes4, int128) {
        uint256 targetOutput = _targetOutput;

        // Reset storage target output to 0 and use one stored in memory
        _targetOutput = 0;

        // Skip if target output is not active
        if (!_applyTargetOutput) {
            return (this.afterSwap.selector, 0);
        }

        // Fee defined in the unspecified currency of the swap
        (Currency unspecified, int128 unspecifiedAmount) = (params.amountSpecified < 0 == params.zeroForOne)
            ? (key.currency1, delta.amount1())
            : (key.currency0, delta.amount0());

        // If fee is on output, get the absolute output amount
        if (unspecifiedAmount < 0) unspecifiedAmount = -unspecifiedAmount;

        // Revert if the target output exceeds the swap amount
        if (targetOutput > uint128(unspecifiedAmount)) revert TargetOutputExceeds();

        // Calculate the fee amount, which is the difference between the swap amount and the target output
        uint256 feeAmount = uint128(unspecifiedAmount) - targetOutput;

        // Mint ERC-6909 tokens for unspecified currency fee and call handler
        if (feeAmount > 0) {
            unspecified.take(poolManager, address(this), feeAmount, true);
            _afterSwapHandler(key, params, delta, targetOutput, feeAmount);
        }

        // Emit the swap event with the amounts ordered correctly
        if (unspecified == key.currency0) {
            emit HookFee(PoolId.unwrap(key.toId()), sender, feeAmount.toUint128(), 0);
        } else {
            emit HookFee(PoolId.unwrap(key.toId()), sender, 0, feeAmount.toUint128());
        }

        return (this.afterSwap.selector, feeAmount.toInt128());
    }

    /**
     * @dev Return the target output to be enforced by the `afterSwap` hook using fees.
     *
     * IMPORTANT: The swap will revert if the target output exceeds the output unspecified amount from the swap.
     * In order to consume all of the output from the swap, set the target output to equal the output unspecified
     * amount and set the apply flag to `true`.
     *
     * @return targetOutput The target output, defined in the unspecified currency of the swap.
     * @return applyTargetOutput The apply flag, which can be set to `false` to skip applying the target output.
     */
    function _getTargetOutput(
        address sender,
        PoolKey calldata key,
        IPoolManager.SwapParams calldata params,
        bytes calldata hookData
    ) internal virtual returns (uint256 targetOutput, bool applyTargetOutput);

    /**
     * @dev Handler called after applying the target output to a swap and receiving the currency amount.
     *
     * @param key The pool key.
     * @param params The swap parameters.
     * @param delta The balance delta from the swap.
     * @param targetOutput The target output, defined in the unspecified currency of the swap.
     * @param feeAmount The amount of the unspecified currency taken from the swap.
     */
    function _afterSwapHandler(
        PoolKey calldata key,
        IPoolManager.SwapParams calldata params,
        BalanceDelta delta,
        uint256 targetOutput,
        uint256 feeAmount
    ) internal virtual;

    /**
     * @dev Set the hook permissions, specifically {beforeSwap}, {afterSwap} and {afterSwapReturnDelta}.
     *
     * @return permissions The hook permissions.
     */
    function getHookPermissions() public pure virtual override returns (Hooks.Permissions memory permissions) {
        return Hooks.Permissions({
            beforeInitialize: false,
            afterInitialize: false,
            beforeAddLiquidity: false,
            afterAddLiquidity: false,
            beforeRemoveLiquidity: false,
            afterRemoveLiquidity: false,
            beforeSwap: true,
            afterSwap: true,
            beforeDonate: false,
            afterDonate: false,
            beforeSwapReturnDelta: false,
            afterSwapReturnDelta: true,
            afterAddLiquidityReturnDelta: false,
            afterRemoveLiquidityReturnDelta: false
        });
    }
}



// External imports








enum FeeTypes {
    SWAP,
    MARGIN,
    INTERESTS,
    MARGIN_SWAP,
    MARGIN_CLOSE_SWAP
}




enum MarginActions {
    MARGIN,
    REPAY,
    CLOSE,
    MODIFY,
    LIQUIDATE_BURN,
    LIQUIDATE_CALL
}




type MarginState is bytes32;

using MarginStateLibrary for MarginState global;

/// @notice Library for getting and setting values in the MarginState type
library MarginStateLibrary {
    uint24 internal constant MASK_24_BITS = 0xFFFFFF;

    uint8 internal constant USE_MIDDLE_LEVEL_OFFSET = 24;
    uint8 internal constant USE_HIGH_LEVEL_OFFSET = 48;
    uint8 internal constant M_LOW_OFFSET = 72;
    uint8 internal constant M_MIDDLE_OFFSET = 96;
    uint8 internal constant M_HIGH_OFFSET = 120;
    uint8 internal constant MAX_PRICE_MOVE_PER_SECOND_OFFSET = 144;
    uint8 internal constant STAGE_DURATION = 168;
    uint8 internal constant STAGE_SIZE = 192;
    uint8 internal constant STAGE_LEAVE_PART = 216;

    // #### GETTERS ####
    function rateBase(MarginState _packed) internal pure returns (uint24 _rateBase) {
        assembly {
            _rateBase := and(MASK_24_BITS, _packed)
        }
    }

    function useMiddleLevel(MarginState _packed) internal pure returns (uint24 _useMiddleLevel) {
        assembly {
            _useMiddleLevel := and(MASK_24_BITS, shr(USE_MIDDLE_LEVEL_OFFSET, _packed))
        }
    }

    function useHighLevel(MarginState _packed) internal pure returns (uint24 _useHighLevel) {
        assembly {
            _useHighLevel := and(MASK_24_BITS, shr(USE_HIGH_LEVEL_OFFSET, _packed))
        }
    }

    function mLow(MarginState _packed) internal pure returns (uint24 _mLow) {
        assembly {
            _mLow := and(MASK_24_BITS, shr(M_LOW_OFFSET, _packed))
        }
    }

    function mMiddle(MarginState _packed) internal pure returns (uint24 _mMiddle) {
        assembly {
            _mMiddle := and(MASK_24_BITS, shr(M_MIDDLE_OFFSET, _packed))
        }
    }

    function mHigh(MarginState _packed) internal pure returns (uint24 _mHigh) {
        assembly {
            _mHigh := and(MASK_24_BITS, shr(M_HIGH_OFFSET, _packed))
        }
    }

    function maxPriceMovePerSecond(MarginState _packed) internal pure returns (uint24 _maxPriceMovePerSecond) {
        assembly {
            _maxPriceMovePerSecond := and(MASK_24_BITS, shr(MAX_PRICE_MOVE_PER_SECOND_OFFSET, _packed))
        }
    }

    function stageDuration(MarginState _packed) internal pure returns (uint24 _stageDuration) {
        assembly {
            _stageDuration := and(MASK_24_BITS, shr(STAGE_DURATION, _packed))
        }
    }

    function stageSize(MarginState _packed) internal pure returns (uint24 _stageSize) {
        assembly {
            _stageSize := and(MASK_24_BITS, shr(STAGE_SIZE, _packed))
        }
    }

    function stageLeavePart(MarginState _packed) internal pure returns (uint24 _stageLeavePart) {
        assembly {
            _stageLeavePart := and(MASK_24_BITS, shr(STAGE_LEAVE_PART, _packed))
        }
    }

    // #### SETTERS ####
    function setRateBase(MarginState _packed, uint24 _rateBase) internal pure returns (MarginState _result) {
        assembly {
            _result := or(and(not(MASK_24_BITS), _packed), and(MASK_24_BITS, _rateBase))
        }
    }

    function setUseMiddleLevel(MarginState _packed, uint24 _useMiddleLevel)
        internal
        pure
        returns (MarginState _result)
    {
        assembly {
            _result :=
                or(
                    and(not(shl(USE_MIDDLE_LEVEL_OFFSET, MASK_24_BITS)), _packed),
                    shl(USE_MIDDLE_LEVEL_OFFSET, and(MASK_24_BITS, _useMiddleLevel))
                )
        }
    }

    function setUseHighLevel(MarginState _packed, uint24 _useHighLevel) internal pure returns (MarginState _result) {
        assembly {
            _result :=
                or(
                    and(not(shl(USE_HIGH_LEVEL_OFFSET, MASK_24_BITS)), _packed),
                    shl(USE_HIGH_LEVEL_OFFSET, and(MASK_24_BITS, _useHighLevel))
                )
        }
    }

    function setMLow(MarginState _packed, uint24 _mLow) internal pure returns (MarginState _result) {
        assembly {
            _result :=
                or(and(not(shl(M_LOW_OFFSET, MASK_24_BITS)), _packed), shl(M_LOW_OFFSET, and(MASK_24_BITS, _mLow)))
        }
    }

    function setMMiddle(MarginState _packed, uint24 _mMiddle) internal pure returns (MarginState _result) {
        assembly {
            _result :=
                or(and(not(shl(M_MIDDLE_OFFSET, MASK_24_BITS)), _packed), shl(M_MIDDLE_OFFSET, and(MASK_24_BITS, _mMiddle)))
        }
    }

    function setMHigh(MarginState _packed, uint24 _mHigh) internal pure returns (MarginState _result) {
        assembly {
            _result :=
                or(and(not(shl(M_HIGH_OFFSET, MASK_24_BITS)), _packed), shl(M_HIGH_OFFSET, and(MASK_24_BITS, _mHigh)))
        }
    }

    function setMaxPriceMovePerSecond(MarginState _packed, uint24 _maxPriceMovePerSecond)
        internal
        pure
        returns (MarginState _result)
    {
        assembly {
            _result :=
                or(
                    and(not(shl(MAX_PRICE_MOVE_PER_SECOND_OFFSET, MASK_24_BITS)), _packed),
                    shl(MAX_PRICE_MOVE_PER_SECOND_OFFSET, and(MASK_24_BITS, _maxPriceMovePerSecond))
                )
        }
    }

    function setStageDuration(MarginState _packed, uint24 _stageDuration) internal pure returns (MarginState _result) {
        assembly {
            _result :=
                or(
                    and(not(shl(STAGE_DURATION, MASK_24_BITS)), _packed),
                    shl(STAGE_DURATION, and(MASK_24_BITS, _stageDuration))
                )
        }
    }

    function setStageSize(MarginState _packed, uint24 _stageSize) internal pure returns (MarginState _result) {
        assembly {
            _result :=
                or(and(not(shl(STAGE_SIZE, MASK_24_BITS)), _packed), shl(STAGE_SIZE, and(MASK_24_BITS, _stageSize)))
        }
    }

    function setStageLeavePart(MarginState _packed, uint24 _stageLeavePart)
        internal
        pure
        returns (MarginState _result)
    {
        assembly {
            _result :=
                or(
                    and(not(shl(STAGE_SIZE, STAGE_LEAVE_PART)), _packed),
                    shl(STAGE_LEAVE_PART, and(MASK_24_BITS, _stageLeavePart))
                )
        }
    }
}







struct MarginBalanceDelta {
    MarginActions action;
    bool marginForOne;
    uint128 marginTotal;
    uint24 marginFee;
    uint256 swapFeeAmount;
    BalanceDelta marginDelta;
    BalanceDelta realDelta;
    BalanceDelta mirrorDelta;
    BalanceDelta pairDelta;
    BalanceDelta lendDelta;
    uint256 debtDepositCumulativeLast;
}









// OpenZeppelin Contracts (last updated v5.1.0) (utils/Panic.sol)



/**
 * @dev Helper library for emitting standardized panic codes.
 *
 * ```solidity
 * contract Example {
 *      using Panic for uint256;
 *
 *      // Use any of the declared internal constants
 *      function foo() { Panic.GENERIC.panic(); }
 *
 *      // Alternatively
 *      function foo() { Panic.panic(Panic.GENERIC); }
 * }
 * ```
 *
 * Follows the list from https://github.com/ethereum/solidity/blob/v0.8.24/libsolutil/ErrorCodes.h[libsolutil].
 *
 * _Available since v5.1._
 */
// slither-disable-next-line unused-state
library Panic {
    /// @dev generic / unspecified error
    uint256 internal constant GENERIC = 0x00;
    /// @dev used by the assert() builtin
    uint256 internal constant ASSERT = 0x01;
    /// @dev arithmetic underflow or overflow
    uint256 internal constant UNDER_OVERFLOW = 0x11;
    /// @dev division or modulo by zero
    uint256 internal constant DIVISION_BY_ZERO = 0x12;
    /// @dev enum conversion error
    uint256 internal constant ENUM_CONVERSION_ERROR = 0x21;
    /// @dev invalid encoding in storage
    uint256 internal constant STORAGE_ENCODING_ERROR = 0x22;
    /// @dev empty array pop
    uint256 internal constant EMPTY_ARRAY_POP = 0x31;
    /// @dev array out of bounds access
    uint256 internal constant ARRAY_OUT_OF_BOUNDS = 0x32;
    /// @dev resource error (too large allocation or too large array)
    uint256 internal constant RESOURCE_ERROR = 0x41;
    /// @dev calling invalid internal function
    uint256 internal constant INVALID_INTERNAL_FUNCTION = 0x51;

    /// @dev Reverts with a panic code. Recommended to use with
    /// the internal constants with predefined codes.
    function panic(uint256 code) internal pure {
        assembly {
            mstore(0x00, 0x4e487b71)
            mstore(0x20, code)
            revert(0x1c, 0x24)
        }
    }
}



library Math {
    /**
     * @dev Branchless ternary evaluation for `a ? b : c`. Gas costs are constant.
     *
     * IMPORTANT: This function may reduce bytecode size and consume less gas when used standalone.
     * However, the compiler may optimize Solidity ternary operations (i.e. `a ? b : c`) to only compute
     * one branch when needed, making this function more expensive.
     */
    function ternary(bool condition, uint256 a, uint256 b) internal pure returns (uint256) {
        unchecked {
            // branchless ternary works because:
            // b ^ (a ^ b) == a
            // b ^ 0 == b
            return b ^ ((a ^ b) * SafeCast.toUint(condition));
        }
    }

    /**
     * @dev Returns the largest of two numbers.
     */
    function max(uint256 a, uint256 b) internal pure returns (uint256) {
        return ternary(a > b, a, b);
    }

    /**
     * @dev Returns the smallest of two numbers.
     */
    function min(uint256 a, uint256 b) internal pure returns (uint256) {
        return ternary(a < b, a, b);
    }

    /**
     * @dev Returns the average of two numbers. The result is rounded towards
     * zero.
     */
    function average(uint256 a, uint256 b) internal pure returns (uint256) {
        // (a + b) / 2 can overflow.
        return (a & b) + (a ^ b) / 2;
    }

    /// @notice Calculates floor(a×b÷denominator) with full precision. Throws if result overflows a uint256 or denominator == 0
    /// @param a The multiplicand
    /// @param b The multiplier
    /// @param denominator The divisor
    /// @return result The 256-bit result
    /// @dev Credit to Remco Bloemen under MIT license https://xn--2-umb.com/21/muldiv
    function mulDiv(uint256 a, uint256 b, uint256 denominator) internal pure returns (uint256 result) {
        unchecked {
            // 512-bit multiply [prod1 prod0] = a * b
            // Compute the product mod 2**256 and mod 2**256 - 1
            // then use the Chinese Remainder Theorem to reconstruct
            // the 512 bit result. The result is stored in two 256
            // variables such that product = prod1 * 2**256 + prod0
            uint256 prod0 = a * b; // Least significant 256 bits of the product
            uint256 prod1; // Most significant 256 bits of the product
            assembly {
                let mm := mulmod(a, b, not(0))
                prod1 := sub(sub(mm, prod0), lt(mm, prod0))
            }

            // Make sure the result is less than 2**256.
            // Also prevents denominator == 0
            require(denominator > prod1);

            // Handle non-overflow cases, 256 by 256 division
            if (prod1 == 0) {
                assembly {
                    result := div(prod0, denominator)
                }
                return result;
            }

            ///////////////////////////////////////////////
            // 512 by 256 division.
            ///////////////////////////////////////////////

            // Make division exact by subtracting the remainder from [prod1 prod0]
            // Compute remainder using mulmod
            uint256 remainder;
            assembly {
                remainder := mulmod(a, b, denominator)
            }
            // Subtract 256 bit number from 512 bit number
            assembly {
                prod1 := sub(prod1, gt(remainder, prod0))
                prod0 := sub(prod0, remainder)
            }

            // Factor powers of two out of denominator
            // Compute largest power of two divisor of denominator.
            // Always >= 1.
            uint256 twos = (0 - denominator) & denominator;
            // Divide denominator by power of two
            assembly {
                denominator := div(denominator, twos)
            }

            // Divide [prod1 prod0] by the factors of two
            assembly {
                prod0 := div(prod0, twos)
            }
            // Shift in bits from prod1 into prod0. For this we need
            // to flip `twos` such that it is 2**256 / twos.
            // If twos is zero, then it becomes one
            assembly {
                twos := add(div(sub(0, twos), twos), 1)
            }
            prod0 |= prod1 * twos;

            // Invert denominator mod 2**256
            // Now that denominator is an odd number, it has an inverse
            // modulo 2**256 such that denominator * inv = 1 mod 2**256.
            // Compute the inverse by starting with a seed that is correct
            // correct for four bits. That is, denominator * inv = 1 mod 2**4
            uint256 inv = (3 * denominator) ^ 2;
            // Now use Newton-Raphson iteration to improve the precision.
            // Thanks to Hensel's lifting lemma, this also works in modular
            // arithmetic, doubling the correct bits in each step.
            inv *= 2 - denominator * inv; // inverse mod 2**8
            inv *= 2 - denominator * inv; // inverse mod 2**16
            inv *= 2 - denominator * inv; // inverse mod 2**32
            inv *= 2 - denominator * inv; // inverse mod 2**64
            inv *= 2 - denominator * inv; // inverse mod 2**128
            inv *= 2 - denominator * inv; // inverse mod 2**256

            // Because the division is now exact we can divide by multiplying
            // with the modular inverse of denominator. This will give us the
            // correct result modulo 2**256. Since the preconditions guarantee
            // that the outcome is less than 2**256, this is the final result.
            // We don't need to compute the high bits of the result and prod1
            // is no longer required.
            result = prod0 * inv;
            return result;
        }
    }

    /// @notice Calculates ceil(a×b÷denominator) with full precision. Throws if result overflows a uint256 or denominator == 0
    /// @param a The multiplicand
    /// @param b The multiplier
    /// @param denominator The divisor
    /// @return result The 256-bit result
    function mulDivRoundingUp(uint256 a, uint256 b, uint256 denominator) internal pure returns (uint256 result) {
        unchecked {
            result = mulDiv(a, b, denominator);
            if (mulmod(a, b, denominator) != 0) {
                require(++result > 0);
            }
        }
    }

    /**
     * @dev Returns the square root of a number. If the number is not a perfect square, the value is rounded
     * towards zero.
     *
     * This method is based on Newton's method for computing square roots; the algorithm is restricted to only
     * using integer operations.
     */
    function sqrt(uint256 a) internal pure returns (uint256) {
        unchecked {
            // Take care of easy edge cases when a == 0 or a == 1
            if (a <= 1) {
                return a;
            }

            // In this function, we use Newton's method to get a root of `f(x) := x² - a`. It involves building a
            // sequence x_n that converges toward sqrt(a). For each iteration x_n, we also define the error between
            // the current value as `ε_n = | x_n - sqrt(a) |`.
            //
            // For our first estimation, we consider `e` the smallest power of 2 which is bigger than the square root
            // of the target. (i.e. `2**(e-1) ≤ sqrt(a) < 2**e`). We know that `e ≤ 128` because `(2¹²⁸)² = 2²⁵⁶` is
            // bigger than any uint256.
            //
            // By noticing that
            // `2**(e-1) ≤ sqrt(a) < 2**e → (2**(e-1))² ≤ a < (2**e)² → 2**(2*e-2) ≤ a < 2**(2*e)`
            // we can deduce that `e - 1` is `log2(a) / 2`. We can thus compute `x_n = 2**(e-1)` using a method similar
            // to the msb function.
            uint256 aa = a;
            uint256 xn = 1;

            if (aa >= (1 << 128)) {
                aa >>= 128;
                xn <<= 64;
            }
            if (aa >= (1 << 64)) {
                aa >>= 64;
                xn <<= 32;
            }
            if (aa >= (1 << 32)) {
                aa >>= 32;
                xn <<= 16;
            }
            if (aa >= (1 << 16)) {
                aa >>= 16;
                xn <<= 8;
            }
            if (aa >= (1 << 8)) {
                aa >>= 8;
                xn <<= 4;
            }
            if (aa >= (1 << 4)) {
                aa >>= 4;
                xn <<= 2;
            }
            if (aa >= (1 << 2)) {
                xn <<= 1;
            }

            // We now have x_n such that `x_n = 2**(e-1) ≤ sqrt(a) < 2**e = 2 * x_n`. This implies ε_n ≤ 2**(e-1).
            //
            // We can refine our estimation by noticing that the middle of that interval minimizes the error.
            // If we move x_n to equal 2**(e-1) + 2**(e-2), then we reduce the error to ε_n ≤ 2**(e-2).
            // This is going to be our x_0 (and ε_0)
            xn = (3 * xn) >> 1; // ε_0 := | x_0 - sqrt(a) | ≤ 2**(e-2)

            // From here, Newton's method give us:
            // x_{n+1} = (x_n + a / x_n) / 2
            //
            // One should note that:
            // x_{n+1}² - a = ((x_n + a / x_n) / 2)² - a
            //              = ((x_n² + a) / (2 * x_n))² - a
            //              = (x_n⁴ + 2 * a * x_n² + a²) / (4 * x_n²) - a
            //              = (x_n⁴ + 2 * a * x_n² + a² - 4 * a * x_n²) / (4 * x_n²)
            //              = (x_n⁴ - 2 * a * x_n² + a²) / (4 * x_n²)
            //              = (x_n² - a)² / (2 * x_n)²
            //              = ((x_n² - a) / (2 * x_n))²
            //              ≥ 0
            // Which proves that for all n ≥ 1, sqrt(a) ≤ x_n
            //
            // This gives us the proof of quadratic convergence of the sequence:
            // ε_{n+1} = | x_{n+1} - sqrt(a) |
            //         = | (x_n + a / x_n) / 2 - sqrt(a) |
            //         = | (x_n² + a - 2*x_n*sqrt(a)) / (2 * x_n) |
            //         = | (x_n - sqrt(a))² / (2 * x_n) |
            //         = | ε_n² / (2 * x_n) |
            //         = ε_n² / | (2 * x_n) |
            //
            // For the first iteration, we have a special case where x_0 is known:
            // ε_1 = ε_0² / | (2 * x_0) |
            //     ≤ (2**(e-2))² / (2 * (2**(e-1) + 2**(e-2)))
            //     ≤ 2**(2*e-4) / (3 * 2**(e-1))
            //     ≤ 2**(e-3) / 3
            //     ≤ 2**(e-3-log2(3))
            //     ≤ 2**(e-4.5)
            //
            // For the following iterations, we use the fact that, 2**(e-1) ≤ sqrt(a) ≤ x_n:
            // ε_{n+1} = ε_n² / | (2 * x_n) |
            //         ≤ (2**(e-k))² / (2 * 2**(e-1))
            //         ≤ 2**(2*e-2*k) / 2**e
            //         ≤ 2**(e-2*k)
            xn = (xn + a / xn) >> 1; // ε_1 := | x_1 - sqrt(a) | ≤ 2**(e-4.5)  -- special case, see above
            xn = (xn + a / xn) >> 1; // ε_2 := | x_2 - sqrt(a) | ≤ 2**(e-9)    -- general case with k = 4.5
            xn = (xn + a / xn) >> 1; // ε_3 := | x_3 - sqrt(a) | ≤ 2**(e-18)   -- general case with k = 9
            xn = (xn + a / xn) >> 1; // ε_4 := | x_4 - sqrt(a) | ≤ 2**(e-36)   -- general case with k = 18
            xn = (xn + a / xn) >> 1; // ε_5 := | x_5 - sqrt(a) | ≤ 2**(e-72)   -- general case with k = 36
            xn = (xn + a / xn) >> 1; // ε_6 := | x_6 - sqrt(a) | ≤ 2**(e-144)  -- general case with k = 72

            // Because e ≤ 128 (as discussed during the first estimation phase), we know have reached a precision
            // ε_6 ≤ 2**(e-144) < 1. Given we're operating on integers, then we can ensure that xn is now either
            // sqrt(a) or sqrt(a) + 1.
            return xn - SafeCast.toUint(xn > a / xn);
        }
    }

    /**
     * @dev Returns the ceiling of the division of two numbers.
     *
     * This differs from standard division with `/` in that it rounds towards infinity instead
     * of rounding towards zero.
     */
    function ceilDiv(uint256 a, uint256 b) internal pure returns (uint256) {
        if (b == 0) {
            // Guarantee the same behavior as in a regular Solidity division.
            Panic.panic(Panic.DIVISION_BY_ZERO);
        }

        // The following calculation ensures accurate ceiling division without overflow.
        // Since a is non-zero, (a - 1) / b will not overflow.
        // The largest possible result occurs when (a - 1) / b is type(uint256).max,
        // but the largest value we can obtain is type(uint256).max - 1, which happens
        // when a = type(uint256).max and b = 1.
        unchecked {
            return SafeCast.toUint(a > 0) * ((a - 1) / b + 1);
        }
    }
}




/// @title FixedPoint96
/// @notice A library for handling binary fixed point numbers, see https://en.wikipedia.org/wiki/Q_(number_format)
/// @dev Used in SqrtPriceMath.sol
library FixedPoint96 {
    uint8 internal constant RESOLUTION = 96;
    uint256 internal constant Q96 = 0x1000000000000000000000000;
}



/// @dev Two `uint128` values packed into a single `uint256` where the upper 128 bits represent reserve0
/// and the lower 128 bits represent reserve1.
type Reserves is uint256;

using ReservesLibrary for Reserves global;

/// @notice Creates a Reserves object from two uint128 values.
/// @param _reserve0 The value for the upper 128 bits.
/// @param _reserve1 The value for the lower 128 bits.
/// @return A Reserves object.
function toReserves(uint128 _reserve0, uint128 _reserve1) pure returns (Reserves) {
    return Reserves.wrap((uint256(_reserve0) << 128) | _reserve1);
}

enum ReservesType {
    REAL,
    MIRROR,
    PAIR,
    LEND
}

/// @notice A library for handling the Reserves type, which packs two uint128 values into a single uint256.
library ReservesLibrary {
    struct UpdateParam {
        ReservesType _type;
        BalanceDelta delta;
    }

    error NotEnoughReserves();

    error InvalidReserves();

    /// @notice Retrieves the reserve0 value from a Reserves object.
    /// @param self The Reserves object.
    /// @return The reserve0 value (upper 128 bits).
    function reserve0(Reserves self) internal pure returns (uint128) {
        return uint128(Reserves.unwrap(self) >> 128);
    }

    /// @notice Retrieves the reserve1 value from a Reserves object.
    /// @param self The Reserves object.
    /// @return The reserve1 value (lower 128 bits).
    function reserve1(Reserves self) internal pure returns (uint128) {
        return uint128(Reserves.unwrap(self));
    }

    /// @notice Retrieves one of the reserves based on a boolean flag.
    /// @param self The Reserves object.
    /// @param forOne If true, returns reserve1; otherwise, returns reserve0.
    /// @return The selected reserve value.
    function reserve01(Reserves self, bool forOne) internal pure returns (uint128) {
        return forOne ? self.reserve1() : self.reserve0();
    }

    /// @notice Retrieves both reserve values from a Reserves object.
    /// @param self The Reserves object.
    /// @return _reserve0 The reserve0 value.
    /// @return _reserve1 The reserve1 value.
    function reserves(Reserves self) internal pure returns (uint128 _reserve0, uint128 _reserve1) {
        _reserve0 = self.reserve0();
        _reserve1 = self.reserve1();
    }

    /// @notice Updates the reserve0 value in a Reserves object.
    /// @param self The Reserves object to update.
    /// @param newReserve0 The new value for reserve0.
    /// @return The updated Reserves object.
    function updateReserve0(Reserves self, uint128 newReserve0) internal pure returns (Reserves) {
        return toReserves(newReserve0, self.reserve1());
    }

    /// @notice Updates the reserve1 value in a Reserves object.
    /// @param self The Reserves object to update.
    /// @param newReserve1 The new value for reserve1.
    /// @return The updated Reserves object.
    function updateReserve1(Reserves self, uint128 newReserve1) internal pure returns (Reserves) {
        return toReserves(self.reserve0(), newReserve1);
    }

    function applyDelta(Reserves self, BalanceDelta delta, bool enableOverflow) internal pure returns (Reserves) {
        (uint128 r0, uint128 r1) = self.reserves();
        int128 d0 = delta.amount0();
        int128 d1 = delta.amount1();

        unchecked {
            if (d0 > 0) {
                uint128 amount0 = uint128(d0);
                if (r0 < amount0) {
                    if (enableOverflow) {
                        r0 = amount0;
                    } else {
                        revert NotEnoughReserves();
                    }
                }
                r0 -= amount0;
            } else if (d0 < 0) {
                r0 += uint128(-d0);
            }

            if (d1 > 0) {
                uint128 amount1 = uint128(d1);
                if (r1 < amount1) {
                    if (enableOverflow) {
                        r1 = amount1;
                    } else {
                        revert NotEnoughReserves();
                    }
                }
                r1 -= amount1;
            } else if (d1 < 0) {
                r1 += uint128(-d1);
            }
        }

        return toReserves(r0, r1);
    }

    /// @notice Applies a balance delta to the reserves.
    /// @param self The Reserves object.
    /// @param delta The balance delta to apply.
    /// @return The updated Reserves object.
    function applyDelta(Reserves self, BalanceDelta delta) internal pure returns (Reserves) {
        return applyDelta(self, delta, false);
    }

    /// @notice Calculates the price of token0 in terms of token1, scaled by Q96.
    /// @param self The Reserves object.
    /// @return The price of token0, scaled by Q96.
    function getPrice0X96(Reserves self) internal pure returns (uint256) {
        (uint128 r0, uint128 r1) = self.reserves();
        if (r0 == 0 || r1 == 0) revert InvalidReserves();
        return Math.mulDiv(r1, FixedPoint96.Q96, r0);
    }

    /// @notice Calculates the price of token1 in terms of token0, scaled by Q96.
    /// @param self The Reserves object.
    /// @return The price of token1, scaled by Q96.
    function getPrice1X96(Reserves self) internal pure returns (uint256) {
        (uint128 r0, uint128 r1) = self.reserves();
        if (r0 == 0 || r1 == 0) revert InvalidReserves();
        return Math.mulDiv(r0, FixedPoint96.Q96, r1);
    }

    /// @notice Checks if both reserves are positive.
    /// @param self The Reserves object.
    /// @return True if both reserves are positive, false otherwise.
    function bothPositive(Reserves self) internal pure returns (bool) {
        (uint128 r0, uint128 r1) = self.reserves();
        return r0 > 0 && r1 > 0;
    }
}




type Slot0 is bytes32;

using Slot0Library for Slot0 global;

/// @notice Library for getting and setting values in the Slot0 type
library Slot0Library {
    uint128 internal constant MASK_128_BITS = 0x00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;
    uint32 internal constant MASK_32_BITS = 0xFFFFFFFF;
    uint24 internal constant MASK_24_BITS = 0xFFFFFF;

    uint8 internal constant LAST_UPDATED_OFFSET = 128;
    uint8 internal constant PROTOCOL_FEE_OFFSET = 160;
    uint8 internal constant LP_FEE_OFFSET = 184;
    uint8 internal constant MARGIN_FEE_OFFSET = 208;

    // #### GETTERS ####
    function totalSupply(Slot0 _packed) internal pure returns (uint128 _totalSupply) {
        assembly {
            _totalSupply := and(MASK_128_BITS, _packed)
        }
    }

    function lastUpdated(Slot0 _packed) internal pure returns (uint32 _timestampLast) {
        assembly {
            _timestampLast := and(MASK_32_BITS, shr(LAST_UPDATED_OFFSET, _packed))
        }
    }

    function protocolFee(Slot0 _packed) internal pure returns (uint24 _protocolFee) {
        assembly {
            _protocolFee := and(MASK_24_BITS, shr(PROTOCOL_FEE_OFFSET, _packed))
        }
    }

    function protocolFee(Slot0 _packed, uint24 defaultFee) internal pure returns (uint24 _protocolFee) {
        _protocolFee = protocolFee(_packed);
        _protocolFee = _protocolFee == 0 ? defaultFee : _protocolFee;
    }

    function lpFee(Slot0 _packed) internal pure returns (uint24 _lpFee) {
        assembly {
            _lpFee := and(MASK_24_BITS, shr(LP_FEE_OFFSET, _packed))
        }
    }

    function marginFee(Slot0 _packed) internal pure returns (uint24 _marginFee) {
        assembly {
            _marginFee := signextend(2, shr(MARGIN_FEE_OFFSET, _packed))
        }
    }

    // #### SETTERS ####
    function setTotalSupply(Slot0 _packed, uint128 _totalSupply) internal pure returns (Slot0 _result) {
        assembly {
            _result := or(and(not(MASK_128_BITS), _packed), and(MASK_128_BITS, _totalSupply))
        }
    }

    function setLastUpdated(Slot0 _packed, uint32 _lastUpdated) internal pure returns (Slot0 _result) {
        assembly {
            _result :=
                or(
                    and(not(shl(LAST_UPDATED_OFFSET, MASK_32_BITS)), _packed),
                    shl(LAST_UPDATED_OFFSET, and(MASK_32_BITS, _lastUpdated))
                )
        }
    }

    function setProtocolFee(Slot0 _packed, uint24 _protocolFee) internal pure returns (Slot0 _result) {
        assembly {
            _result :=
                or(
                    and(not(shl(PROTOCOL_FEE_OFFSET, MASK_24_BITS)), _packed),
                    shl(PROTOCOL_FEE_OFFSET, and(MASK_24_BITS, _protocolFee))
                )
        }
    }

    function setLpFee(Slot0 _packed, uint24 _lpFee) internal pure returns (Slot0 _result) {
        assembly {
            _result :=
                or(and(not(shl(LP_FEE_OFFSET, MASK_24_BITS)), _packed), shl(LP_FEE_OFFSET, and(MASK_24_BITS, _lpFee)))
        }
    }

    function setMarginFee(Slot0 _packed, uint24 _marginFee) internal pure returns (Slot0 _result) {
        assembly {
            _result :=
                or(
                    and(not(shl(MARGIN_FEE_OFFSET, MASK_24_BITS)), _packed),
                    shl(MARGIN_FEE_OFFSET, and(MASK_24_BITS, _marginFee))
                )
        }
    }
}




/// @title Library for reverting with custom errors efficiently
/// @notice Contains functions for reverting with custom errors with different argument types efficiently
/// @dev To use this library, declare `using CustomRevert for bytes4;` and replace `revert CustomError()` with
/// `CustomError.selector.revertWith()`
/// @dev The functions may tamper with the free memory pointer but it is fine since the call context is exited immediately
library CustomRevert {
    /// @dev ERC-7751 error for wrapping bubbled up reverts
    error WrappedError(address target, bytes4 selector, bytes reason, bytes details);

    /// @dev Reverts with the selector of a custom error in the scratch space
    function revertWith(bytes4 selector) internal pure {
        assembly {
            mstore(0, selector)
            revert(0, 0x04)
        }
    }

    /// @dev Reverts with a custom error with an address argument in the scratch space
    function revertWith(bytes4 selector, address addr) internal pure {
        assembly {
            mstore(0, selector)
            mstore(0x04, and(addr, 0xffffffffffffffffffffffffffffffffffffffff))
            revert(0, 0x24)
        }
    }

    /// @dev Reverts with a custom error with an int24 argument in the scratch space
    function revertWith(bytes4 selector, int24 value) internal pure {
        assembly {
            mstore(0, selector)
            mstore(0x04, signextend(2, value))
            revert(0, 0x24)
        }
    }

    /// @dev Reverts with a custom error with a uint160 argument in the scratch space
    function revertWith(bytes4 selector, uint160 value) internal pure {
        assembly {
            mstore(0, selector)
            mstore(0x04, and(value, 0xffffffffffffffffffffffffffffffffffffffff))
            revert(0, 0x24)
        }
    }

    /// @dev Reverts with a custom error with two int24 arguments
    function revertWith(bytes4 selector, int24 value1, int24 value2) internal pure {
        assembly {
            let fmp := mload(0x40)
            mstore(fmp, selector)
            mstore(add(fmp, 0x04), signextend(2, value1))
            mstore(add(fmp, 0x24), signextend(2, value2))
            revert(fmp, 0x44)
        }
    }

    /// @dev Reverts with a custom error with two uint160 arguments
    function revertWith(bytes4 selector, uint160 value1, uint160 value2) internal pure {
        assembly {
            let fmp := mload(0x40)
            mstore(fmp, selector)
            mstore(add(fmp, 0x04), and(value1, 0xffffffffffffffffffffffffffffffffffffffff))
            mstore(add(fmp, 0x24), and(value2, 0xffffffffffffffffffffffffffffffffffffffff))
            revert(fmp, 0x44)
        }
    }

    /// @dev Reverts with a custom error with two address arguments
    function revertWith(bytes4 selector, address value1, address value2) internal pure {
        assembly {
            let fmp := mload(0x40)
            mstore(fmp, selector)
            mstore(add(fmp, 0x04), and(value1, 0xffffffffffffffffffffffffffffffffffffffff))
            mstore(add(fmp, 0x24), and(value2, 0xffffffffffffffffffffffffffffffffffffffff))
            revert(fmp, 0x44)
        }
    }

    /// @notice bubble up the revert message returned by a call and revert with a wrapped ERC-7751 error
    /// @dev this method can be vulnerable to revert data bombs
    function bubbleUpAndRevertWith(
        address revertingContract,
        bytes4 revertingFunctionSelector,
        bytes4 additionalContext
    ) internal pure {
        bytes4 wrappedErrorSelector = WrappedError.selector;
        assembly {
            // Ensure the size of the revert data is a multiple of 32 bytes
            let encodedDataSize := mul(div(add(returndatasize(), 31), 32), 32)

            let fmp := mload(0x40)

            // Encode wrapped error selector, address, function selector, offset, additional context, size, revert reason
            mstore(fmp, wrappedErrorSelector)
            mstore(add(fmp, 0x04), and(revertingContract, 0xffffffffffffffffffffffffffffffffffffffff))
            mstore(
                add(fmp, 0x24),
                and(revertingFunctionSelector, 0xffffffff00000000000000000000000000000000000000000000000000000000)
            )
            // offset revert reason
            mstore(add(fmp, 0x44), 0x80)
            // offset additional context
            mstore(add(fmp, 0x64), add(0xa0, encodedDataSize))
            // size revert reason
            mstore(add(fmp, 0x84), returndatasize())
            // revert reason
            returndatacopy(add(fmp, 0xa4), 0, returndatasize())
            // size additional context
            mstore(add(fmp, add(0xa4, encodedDataSize)), 0x04)
            // additional context
            mstore(
                add(fmp, add(0xc4, encodedDataSize)),
                and(additionalContext, 0xffffffff00000000000000000000000000000000000000000000000000000000)
            )
            revert(fmp, add(0xe4, encodedDataSize))
        }
    }
}


// Likwid Contracts





// Likwid Contracts




library PerLibrary {
    error InvalidMillionth();

    uint256 public constant ONE_MILLION = 10 ** 6;
    uint256 public constant ONE_TRILLION = 10 ** 12;
    uint256 public constant YEAR_TRILLION_SECONDS = ONE_TRILLION * 365 * 24 * 3600;

    function mulMillion(uint256 x) internal pure returns (uint256 y) {
        y = x * ONE_MILLION;
    }

    function divMillion(uint256 x) internal pure returns (uint256 y) {
        y = x / ONE_MILLION;
    }

    function mulMillionDiv(uint256 x, uint256 y) internal pure returns (uint256 z) {
        z = Math.mulDiv(x, ONE_MILLION, y);
    }

    function mulDivMillion(uint256 x, uint256 y) internal pure returns (uint256 z) {
        z = Math.mulDiv(x, y, ONE_MILLION);
    }

    function upperMillion(uint256 x, uint256 per) internal pure returns (uint256 z) {
        z = Math.mulDiv(x, ONE_MILLION + per, ONE_MILLION);
    }

    function lowerMillion(uint256 x, uint256 per) internal pure returns (uint256 z) {
        if (per >= ONE_MILLION) {
            return z;
        }
        z = Math.mulDiv(x, ONE_MILLION - per, ONE_MILLION);
    }

    function isWithinTolerance(uint256 a, uint256 b, uint256 t) internal pure returns (bool) {
        return a >= b ? (a - b) <= t : (b - a) <= t;
    }
}


library FeeLibrary {
    function deductFrom(uint24 fee, uint256 amount) internal pure returns (uint256 amountWithoutFee) {
        uint256 ratio = PerLibrary.ONE_MILLION - fee;
        amountWithoutFee = Math.mulDiv(amount, ratio, PerLibrary.ONE_MILLION);
    }

    function deduct(uint24 fee, uint256 amount) internal pure returns (uint256 amountWithoutFee, uint256 feeAmount) {
        amountWithoutFee = deductFrom(fee, amount);
        feeAmount = amount - amountWithoutFee;
    }

    function attachFrom(uint24 fee, uint256 amount) internal pure returns (uint256 amountWithFee) {
        uint256 ratio = PerLibrary.ONE_MILLION - fee;
        amountWithFee = Math.mulDiv(amount, PerLibrary.ONE_MILLION, ratio);
    }

    function attach(uint24 fee, uint256 amount) internal pure returns (uint256 amountWithFee, uint256 feeAmount) {
        amountWithFee = attachFrom(fee, amount);
        feeAmount = amountWithFee - amount;
    }

    function part(uint24 fee, uint256 amount) internal pure returns (uint256 feeAmount) {
        feeAmount = Math.mulDiv(amount, uint256(fee), PerLibrary.ONE_MILLION);
    }

    function bound(uint24 fee, uint256 amount) internal pure returns (uint256 lower, uint256 upper) {
        lower = deductFrom(fee, amount);
        upper = attachFrom(fee, amount);
    }
}




// Likwid Contracts





// Likwid Contracts


/// @title PositionLibrary
/// @notice A library for creating unique identifiers for positions.
library PositionLibrary {
    /// @notice Calculates a unique position key for an owner and a salt.
    /// @param owner The owner of the position.
    /// @param salt A unique salt for the position.
    /// @return positionKey The unique identifier for the position.
    function calculatePositionKey(address owner, bytes32 salt) internal pure returns (bytes32 positionKey) {
        // This assembly block is a gas-optimized version of:
        // positionKey = keccak256(abi.encodePacked(owner, salt));
        assembly {
            let fmp := mload(0x40)
            // Place owner and salt sequentially into memory
            mstore(fmp, owner)
            mstore(add(fmp, 0x20), salt)
            // Hash the 20 bytes of owner and 32 bytes of salt.
            // An address is 20 bytes, but stored in a 32-byte word. It's right-aligned,
            // so we skip the first 12 zero bytes.
            // The total length to hash is 20 (owner) + 32 (salt) = 52 bytes (0x34).
            positionKey := keccak256(add(fmp, 0x0c), 0x34)

            // now clean the memory we used
            mstore(fmp, 0) // fmp held owner
            mstore(add(fmp, 0x20), 0) // fmp held salt
        }
    }

    function calculatePositionKey(address owner, bool isForOne, bytes32 salt)
        internal
        pure
        returns (bytes32 positionKey)
    {
        assembly {
            // Get a pointer to some free memory
            let ptr := mload(0x40)

            // abi.encodePacked(owner, isForOne, salt) is 53 bytes:
            // | owner (20 bytes) | isForOne (1 byte) | salt (32 bytes) |

            // We construct the first 32 bytes of the packed data:
            // | owner (20 bytes) | isForOne (1 byte) | salt (first 11 bytes) |
            // Shift owner left by 12 bytes (96 bits) to align it to the start of the word.
            let word1 := shl(96, owner)
            // Shift isForOne left by 11 bytes (88 bits) to place it right after the owner.
            word1 := or(word1, shl(88, isForOne))
            // Take the top 11 bytes (88 bits) of the salt and place them after isForOne.
            word1 := or(word1, shr(168, salt))

            // We construct the second 32 bytes of the packed data:
            // | salt (last 21 bytes) | padding (11 bytes) |
            // Shift the salt left by 88 bits to get the last 21 bytes at the start of the word.
            let word2 := shl(88, salt)

            // Store the two constructed words in memory
            mstore(ptr, word1)
            mstore(add(ptr, 0x20), word2)

            // Hash the 53 bytes of packed data
            positionKey := keccak256(ptr, 53)

            // Clean the memory that we used
            mstore(ptr, 0)
            mstore(add(ptr, 0x20), 0)
        }
    }
}




/// @title Math library for liquidity
library LiquidityMath {
    /// @notice Add a signed liquidity delta to liquidity and revert if it overflows or underflows
    /// @param x The liquidity before change
    /// @param y The delta by which liquidity should be changed
    /// @return z The liquidity delta
    function addDelta(uint128 x, int128 y) internal pure returns (uint128 z) {
        assembly {
            z := add(and(x, 0xffffffffffffffffffffffffffffffff), signextend(15, y))
            if shr(128, z) {
                // revert SafeCastOverflow()
                mstore(0, 0x93dafdf1)
                revert(0, 4)
            }
        }
    }

    function addInvestment(uint256 prev, int128 amount0, int128 amount1) internal pure returns (uint256 current) {
        assembly {
            // Unpack prev into two 128-bit values
            let prevAmount0 := shr(128, prev)
            let prevAmount1 := and(prev, 0xffffffffffffffffffffffffffffffff)

            // Add deltas, checking for int128 overflow
            let currentAmount0 := add(signextend(15, prevAmount0), signextend(15, amount0))
            if iszero(eq(signextend(15, currentAmount0), currentAmount0)) {
                // revert SafeCastOverflow()
                mstore(0, 0x93dafdf1)
                revert(0, 4)
            }

            let currentAmount1 := add(signextend(15, prevAmount1), signextend(15, amount1))
            if iszero(eq(signextend(15, currentAmount1), currentAmount1)) {
                // revert SafeCastOverflow()
                mstore(0, 0x93dafdf1)
                revert(0, 4)
            }

            // Pack the results back into a uint256
            current := or(
                shl(128, and(currentAmount0, 0xffffffffffffffffffffffffffffffff)),
                and(currentAmount1, 0xffffffffffffffffffffffffffffffff)
            )
        }
    }
}

/// @title PairPosition
/// @notice A library for managing liquidity positions in a pair.
/// @dev Positions represent an owner's liquidity contribution.
library PairPosition {
    using CustomRevert for bytes4;
    using PositionLibrary for address;

    error CannotUpdateEmptyPosition();

    /// @dev Represents the state of a liquidity position.
    struct State {
        // The amount of liquidity in the position.
        uint128 liquidity;
        // The total investment value, used for tracking returns.
        uint256 totalInvestment;
    }

    /// @notice Retrieves a position's state from storage.
    /// @param self The mapping of position keys to position states.
    /// @param owner The owner of the position.
    /// @param salt A unique salt for the position.
    /// @return position A storage pointer to the position's state.
    function get(mapping(bytes32 => State) storage self, address owner, bytes32 salt)
        internal
        view
        returns (State storage position)
    {
        bytes32 positionKey = owner.calculatePositionKey(salt);
        position = self[positionKey];
    }

    /// @notice Updates a position's state with new liquidity and investment amounts.
    /// @param self A storage pointer to the position's state to update.
    /// @param liquidityDelta The change in liquidity.
    /// @param delta The change in the balance of tokens.
    /// @return The updated total investment value.
    function update(State storage self, int128 liquidityDelta, BalanceDelta delta) internal returns (uint256) {
        // If there's no change in liquidity and the position is empty, revert.
        // This prevents creating empty positions or "poking" them without effect.
        if (liquidityDelta == 0 && self.liquidity == 0) {
            CannotUpdateEmptyPosition.selector.revertWith();
        }

        if (liquidityDelta != 0) {
            self.liquidity = LiquidityMath.addDelta(self.liquidity, liquidityDelta);
        }

        // Update the total investment and store it.
        self.totalInvestment = LiquidityMath.addInvestment(self.totalInvestment, delta.amount0(), delta.amount1());
        return self.totalInvestment;
    }
}


// Likwid Contracts








/// @title LendPosition
/// @notice Positions represent an owner address' lend tokens
library LendPosition {
    using CustomRevert for bytes4;
    using PositionLibrary for address;
    using SafeCast for *;

    error CannotUpdateEmptyPosition();

    error WithdrawOverflow();

    struct State {
        uint128 lendAmount;
        uint256 depositCumulativeLast;
    }

    function get(mapping(bytes32 => State) storage self, address owner, bool lendForOne, bytes32 salt)
        internal
        view
        returns (State storage position)
    {
        bytes32 positionKey = owner.calculatePositionKey(lendForOne, salt);
        position = self[positionKey];
    }

    function update(State storage self, bool lendForOne, uint256 depositCumulativeLast, BalanceDelta delta)
        internal
        returns (uint256)
    {
        int128 amount;
        if (lendForOne) {
            amount = delta.amount1();
        } else {
            amount = delta.amount0();
        }
        if ((delta == BalanceDeltaLibrary.ZERO_DELTA && self.lendAmount == 0) || amount == 0) {
            CannotUpdateEmptyPosition.selector.revertWith();
        }

        uint256 lendAmount;
        if (self.depositCumulativeLast != 0) {
            lendAmount = Math.mulDiv(self.lendAmount, depositCumulativeLast, self.depositCumulativeLast);
        }

        if (amount < 0) {
            // deposit
            lendAmount += uint128(-amount);
        } else {
            // withdraw
            if (uint128(amount) > lendAmount) {
                WithdrawOverflow.selector.revertWith();
            }
            lendAmount -= uint128(amount);
        }
        self.lendAmount = lendAmount.toUint128();
        self.depositCumulativeLast = depositCumulativeLast;

        return self.lendAmount;
    }
}









/// @notice A library for handling protocol fees represented as a packed uint24 value.
library ProtocolFeeLibrary {
    using CustomRevert for bytes4;

    error InvalidProtocolFee(uint8 fee);

    // Each fee is a uint8, representing a percentage of the total fee, scaled by FEE_DENOMINATOR.
    // For example, a value of 100 means 100/200 = 50% protocol fee.
    // The maximum value of 200 represents a 100% protocol fee.
    uint8 internal constant MAX_PROTOCOL_FEE = 200;
    uint256 internal constant FEE_DENOMINATOR = 200;

    uint24 internal constant SWAP_FEE_THRESHOLD = 201;
    uint24 internal constant MARGIN_FEE_THRESHOLD = 201 << 8;
    uint24 internal constant INTEREST_FEE_THRESHOLD = 201 << 16;

    function getProtocolSwapFee(uint24 self) internal pure returns (uint8) {
        return uint8(self & 0xff);
    }

    function getProtocolMarginFee(uint24 self) internal pure returns (uint8) {
        return uint8(self >> 8);
    }

    function getProtocolInterestFee(uint24 self) internal pure returns (uint8) {
        return uint8(self >> 16);
    }

    function isValidProtocolFee(uint24 self) internal pure returns (bool valid) {
        // Equivalent to: getProtocolSwapFee(self) <= MAX_PROTOCOL_FEE && getProtocolMarginFee(self) <= MAX_PROTOCOL_FEE && getProtocolInterestFee(self) <= MAX_PROTOCOL_FEE
        assembly {
            let isProtocolSwapFeeOk := lt(and(self, 0xff), SWAP_FEE_THRESHOLD)
            let isProtocolMarginFeeOk := lt(and(self, 0xff00), MARGIN_FEE_THRESHOLD)
            let isProtocolInterestFeeOk := lt(and(self, 0xff0000), INTEREST_FEE_THRESHOLD)
            valid := and(and(isProtocolSwapFeeOk, isProtocolMarginFeeOk), isProtocolInterestFeeOk)
        }
    }

    function getProtocolFee(uint24 self, FeeTypes feeType) internal pure returns (uint8) {
        if (feeType == FeeTypes.SWAP) {
            return getProtocolSwapFee(self);
        } else if (feeType == FeeTypes.MARGIN) {
            return getProtocolMarginFee(self);
        } else if (feeType == FeeTypes.INTERESTS) {
            return getProtocolInterestFee(self);
        }
        return 0; // Default case, should not happen
    }

    function setProtocolFee(uint24 self, FeeTypes feeType, uint8 newFee) internal pure returns (uint24) {
        if (newFee > MAX_PROTOCOL_FEE) {
            InvalidProtocolFee.selector.revertWith(newFee);
        }
        if (feeType == FeeTypes.SWAP) {
            return (self & 0xffff00) | newFee; // Set swap fee
        } else if (feeType == FeeTypes.MARGIN) {
            return (self & 0xff00ff) | (uint24(newFee) << 8); // Set margin fee
        } else if (feeType == FeeTypes.INTERESTS) {
            return (self & 0x00ffff) | (uint24(newFee) << 16); // Set interest fee
        }
        return self; // Default case, should not happen
    }

    function splitFee(uint24 self, FeeTypes feeType, uint256 feeAmount)
        internal
        pure
        returns (uint256 protocolFee, uint256 remainingFee)
    {
        uint8 protocolFeePercent = getProtocolFee(self, feeType);
        if (protocolFeePercent == 0) {
            return (0, feeAmount);
        }
        protocolFee = Math.mulDiv(feeAmount, protocolFeePercent, FEE_DENOMINATOR);
        remainingFee = feeAmount - protocolFee;
    }
}


// Likwid Contracts


library TimeLibrary {
    function getTimeElapsed(uint32 blockTimestampLast) internal view returns (uint256 timeElapsed) {
        uint32 blockTimestamp = uint32(block.timestamp);
        if (blockTimestampLast <= blockTimestamp) {
            timeElapsed = uint256(blockTimestamp - blockTimestampLast);
        } else {
            timeElapsed = uint256(2 ** 32 - blockTimestampLast + blockTimestamp);
        }
    }
}












library SwapMath {
    using CustomRevert for bytes4;
    using FeeLibrary for uint24;
    using PerLibrary for uint256;

    /// @notice The maximum swap fee in hundredths of a bip (1e6 = 100%).
    uint256 internal constant MAX_SWAP_FEE = 1e6;

    error InsufficientLiquidity();
    error InsufficientInputAmount();

    /**
     * @notice Calculates the absolute difference between two prices.
     * @param price The current price.
     * @param lastPrice The previous price.
     * @return priceDiff The absolute difference.
     */
    function differencePrice(uint256 price, uint256 lastPrice) internal pure returns (uint256 priceDiff) {
        priceDiff = price > lastPrice ? price - lastPrice : lastPrice - price;
    }

    /**
     * @notice Calculates the degree of price change caused by a swap, used for dynamic fee calculation.
     * @dev This function calculates price impact based on reserves and swap amounts.
     * @param pairReserves The current reserves of the pair.
     * @param truncatedReserves The reserves at the last fee calculation checkpoint.
     * @param lpFee The base liquidity provider fee.
     * @param zeroForOne The direction of the swap.
     * @param amountIn The amount of tokens being swapped in.
     * @param amountOut The amount of tokens being swapped out.
     * @return degree The calculated degree of price change.
     */
    function getPriceDegree(
        Reserves pairReserves,
        Reserves truncatedReserves,
        uint24 lpFee,
        bool zeroForOne,
        uint256 amountIn,
        uint256 amountOut
    ) internal pure returns (uint256 degree) {
        if (truncatedReserves.bothPositive()) {
            uint256 lastPrice0X96 = truncatedReserves.getPrice0X96();
            uint256 lastPrice1X96 = truncatedReserves.getPrice1X96();
            (uint256 _reserve0, uint256 _reserve1) = pairReserves.reserves();
            if (_reserve0 == 0 || _reserve1 == 0) {
                return degree;
            }
            if (amountIn > 0) {
                (amountOut,) = getAmountOut(pairReserves, lpFee, zeroForOne, amountIn);
            } else if (amountOut > 0) {
                (amountIn,) = getAmountIn(pairReserves, lpFee, zeroForOne, amountOut);
            }
            unchecked {
                if (zeroForOne) {
                    _reserve1 -= amountOut;
                    _reserve0 += amountIn;
                } else {
                    _reserve0 -= amountOut;
                    _reserve1 += amountIn;
                }
            }
            uint256 price0X96 = Math.mulDiv(_reserve1, FixedPoint96.Q96, _reserve0);
            uint256 price1X96 = Math.mulDiv(_reserve0, FixedPoint96.Q96, _reserve1);
            uint256 degree0 = differencePrice(price0X96, lastPrice0X96).mulMillionDiv(lastPrice0X96);
            uint256 degree1 = differencePrice(price1X96, lastPrice1X96).mulMillionDiv(lastPrice1X96);
            degree = Math.max(degree0, degree1);
        }
    }

    /**
     * @notice Calculates a dynamic fee based on the degree of price change.
     * @dev The fee increases with the price impact (degree).
     * @param swapFee The base swap fee.
     * @param degree The degree of price change.
     * @return _fee The calculated dynamic fee.
     */
    function dynamicFee(uint24 swapFee, uint256 degree) internal pure returns (uint24 _fee) {
        _fee = swapFee;
        if (degree > MAX_SWAP_FEE) {
            _fee = uint24(MAX_SWAP_FEE) - 10000;
        } else if (degree > 100000) {
            uint256 dFee = Math.mulDiv((degree * 10) ** 3, _fee, MAX_SWAP_FEE ** 3);
            if (dFee >= MAX_SWAP_FEE) {
                _fee = uint24(MAX_SWAP_FEE) - 10000;
            } else {
                _fee = uint24(dFee);
            }
        }
    }

    /**
     * @notice Calculates the output amount and fee for a given input amount and fixed fee.
     * @param pairReserves The reserves of the token pair.
     * @param lpFee The liquidity provider fee.
     * @param zeroForOne The direction of the swap.
     * @param amountIn The amount of input tokens.
     * @return amountOut The calculated amount of output tokens.
     * @return feeAmount The amount of fees paid.
     */
    function getAmountOut(Reserves pairReserves, uint24 lpFee, bool zeroForOne, uint256 amountIn)
        internal
        pure
        returns (uint256 amountOut, uint256 feeAmount)
    {
        if (amountIn == 0) InsufficientInputAmount.selector.revertWith();
        (uint128 _reserve0, uint128 _reserve1) = pairReserves.reserves();
        (uint256 reserveIn, uint256 reserveOut) = zeroForOne ? (_reserve0, _reserve1) : (_reserve1, _reserve0);
        if (reserveIn == 0 || reserveOut == 0) InsufficientLiquidity.selector.revertWith();
        uint256 amountInWithoutFee;
        (amountInWithoutFee, feeAmount) = lpFee.deduct(amountIn);
        uint256 numerator = amountInWithoutFee * reserveOut;
        uint256 denominator = reserveIn + amountInWithoutFee;
        amountOut = numerator / denominator;
    }

    /**
     * @notice Calculates the output amount using a dynamic fee based on price impact.
     * @param pairReserves The current reserves of the pair.
     * @param truncatedReserves The reserves at the last fee calculation checkpoint.
     * @param lpFee The base liquidity provider fee.
     * @param zeroForOne The direction of the swap.
     * @param amountIn The amount of input tokens.
     * @return amountOut The calculated amount of output tokens.
     * @return fee The dynamic fee applied.
     * @return feeAmount The amount of fees paid.
     */
    function getAmountOut(
        Reserves pairReserves,
        Reserves truncatedReserves,
        uint24 lpFee,
        bool zeroForOne,
        uint256 amountIn
    ) internal pure returns (uint256 amountOut, uint24 fee, uint256 feeAmount) {
        uint256 degree = getPriceDegree(pairReserves, truncatedReserves, lpFee, zeroForOne, amountIn, 0);
        fee = dynamicFee(lpFee, degree);
        (amountOut, feeAmount) = getAmountOut(pairReserves, fee, zeroForOne, amountIn);
    }

    /**
     * @notice Calculates the required input amount and fee for a given output amount and fixed fee.
     * @param pairReserves The reserves of the token pair.
     * @param lpFee The liquidity provider fee.
     * @param zeroForOne The direction of the swap.
     * @param amountOut The desired amount of output tokens.
     * @return amountIn The required amount of input tokens.
     * @return feeAmount The amount of fees paid from the input tokens.
     */
    function getAmountIn(Reserves pairReserves, uint24 lpFee, bool zeroForOne, uint256 amountOut)
        internal
        pure
        returns (uint256 amountIn, uint256 feeAmount)
    {
        (uint128 _reserve0, uint128 _reserve1) = pairReserves.reserves();
        (uint256 reserveIn, uint256 reserveOut) = zeroForOne ? (_reserve0, _reserve1) : (_reserve1, _reserve0);
        if (reserveIn == 0 || reserveOut == 0) InsufficientLiquidity.selector.revertWith();
        if (amountOut >= reserveOut) InsufficientLiquidity.selector.revertWith();

        uint256 amountInWithoutFee = Math.mulDiv(reserveIn, amountOut, reserveOut - amountOut) + 1;

        uint256 numerator = amountInWithoutFee * MAX_SWAP_FEE;
        uint256 denominator = MAX_SWAP_FEE - lpFee;
        amountIn = (numerator + denominator - 1) / denominator;
        feeAmount = amountIn - amountInWithoutFee;
    }

    /**
     * @notice Calculates the required input amount using a dynamic fee based on price impact.
     * @param pairReserves The current reserves of the pair.
     * @param truncatedReserves The reserves at the last fee calculation checkpoint.
     * @param lpFee The base liquidity provider fee.
     * @param zeroForOne The direction of the swap.
     * @param amountOut The desired amount of output tokens.
     * @return amountIn The required amount of input tokens.
     * @return fee The dynamic fee applied.
     * @return feeAmount The amount of fees paid.
     */
    function getAmountIn(
        Reserves pairReserves,
        Reserves truncatedReserves,
        uint24 lpFee,
        bool zeroForOne,
        uint256 amountOut
    ) internal pure returns (uint256 amountIn, uint24 fee, uint256 feeAmount) {
        (uint256 approxAmountIn,) = getAmountIn(pairReserves, lpFee, zeroForOne, amountOut);
        uint256 degree = getPriceDegree(pairReserves, truncatedReserves, lpFee, zeroForOne, approxAmountIn, amountOut);
        fee = dynamicFee(lpFee, degree);
        (amountIn, feeAmount) = getAmountIn(pairReserves, fee, zeroForOne, amountOut);
    }
}














library InterestMath {
    using CustomRevert for bytes4;
    using FeeLibrary for uint24;
    using PerLibrary for uint256;

    function getBorrowRateByReserves(MarginState marginState, uint256 borrowReserve, uint256 mirrorReserve)
        internal
        pure
        returns (uint256 rate)
    {
        rate = marginState.rateBase();
        if (mirrorReserve == 0) {
            return rate;
        }
        uint256 useLevel = Math.mulDiv(mirrorReserve, PerLibrary.ONE_MILLION, borrowReserve);
        if (useLevel >= marginState.useHighLevel()) {
            rate += uint256(useLevel - marginState.useHighLevel()) * marginState.mHigh() / 100;
            useLevel = marginState.useHighLevel();
        }
        if (useLevel >= marginState.useMiddleLevel()) {
            rate += uint256(useLevel - marginState.useMiddleLevel()) * marginState.mMiddle() / 100;
            useLevel = marginState.useMiddleLevel();
        }
        return rate + useLevel * marginState.mLow() / 100;
    }

    function getBorrowRateCumulativeLast(
        uint256 timeElapsed,
        uint256 rate0CumulativeBefore,
        uint256 rate1CumulativeBefore,
        MarginState marginState,
        Reserves realReserves,
        Reserves mirrorReserve
    ) internal pure returns (uint256 rate0CumulativeLast, uint256 rate1CumulativeLast) {
        if (timeElapsed == 0) {
            return (rate0CumulativeBefore, rate1CumulativeBefore);
        }
        (uint256 realReserve0, uint256 realReserve1) = realReserves.reserves();
        (uint256 mirrorReserve0, uint256 mirrorReserve1) = mirrorReserve.reserves();
        uint256 rate0 = getBorrowRateByReserves(marginState, realReserve0 + mirrorReserve0, mirrorReserve0);
        uint256 rate0LastYear = PerLibrary.YEAR_TRILLION_SECONDS + rate0 * timeElapsed * PerLibrary.ONE_MILLION;
        rate0CumulativeLast = Math.mulDiv(rate0CumulativeBefore, rate0LastYear, PerLibrary.YEAR_TRILLION_SECONDS);
        uint256 rate1 = getBorrowRateByReserves(marginState, realReserve1 + mirrorReserve1, mirrorReserve1);
        uint256 rate1LastYear = PerLibrary.YEAR_TRILLION_SECONDS + rate1 * timeElapsed * PerLibrary.ONE_MILLION;
        rate1CumulativeLast = Math.mulDiv(rate1CumulativeBefore, rate1LastYear, PerLibrary.YEAR_TRILLION_SECONDS);
    }

    struct InterestUpdateParams {
        uint256 mirrorReserve;
        uint256 borrowCumulativeLast;
        uint256 borrowCumulativeBefore;
        uint256 interestReserve;
        uint256 pairReserve;
        uint256 lendReserve;
        uint256 depositCumulativeLast;
        uint24 protocolFee;
    }

    struct InterestUpdateResult {
        uint256 newMirrorReserve;
        uint256 newPairReserve;
        uint256 newLendReserve;
        uint256 newInterestReserve;
        uint256 newDepositCumulativeLast;
        uint256 pairInterest;
        bool changed;
    }

    function updateInterestForOne(InterestUpdateParams memory params)
        internal
        pure
        returns (InterestUpdateResult memory result)
    {
        result.newMirrorReserve = params.mirrorReserve;
        result.newPairReserve = params.pairReserve;
        result.newLendReserve = params.lendReserve;
        result.newInterestReserve = params.interestReserve;
        result.newDepositCumulativeLast = params.depositCumulativeLast;

        if (params.mirrorReserve > 0 && params.borrowCumulativeLast > params.borrowCumulativeBefore) {
            uint256 allInterest = Math.mulDiv(
                params.mirrorReserve * FixedPoint96.Q96, params.borrowCumulativeLast, params.borrowCumulativeBefore
            ) - params.mirrorReserve * FixedPoint96.Q96 + params.interestReserve;

            (uint256 protocolInterest,) =
                ProtocolFeeLibrary.splitFee(params.protocolFee, FeeTypes.INTERESTS, allInterest);

            if (protocolInterest == 0 || protocolInterest > FixedPoint96.Q96) {
                uint256 allInterestNoQ96 = allInterest / FixedPoint96.Q96;
                allInterestNoQ96 -= protocolInterest / FixedPoint96.Q96;

                result.pairInterest =
                    Math.mulDiv(allInterestNoQ96, params.pairReserve, params.pairReserve + params.lendReserve);

                if (allInterestNoQ96 > result.pairInterest) {
                    uint256 lendingInterest = allInterestNoQ96 - result.pairInterest;
                    result.newDepositCumulativeLast = Math.mulDiv(
                        params.depositCumulativeLast, params.lendReserve + lendingInterest, params.lendReserve
                    );
                    result.newLendReserve += lendingInterest;
                }

                result.newMirrorReserve += allInterestNoQ96;
                result.newPairReserve += result.pairInterest;
                result.changed = true;
                result.newInterestReserve = 0;
            } else {
                result.newInterestReserve = allInterest;
            }
        }
    }
}


// Likwid Contracts







library PriceMath {
    using SafeCast for *;
    using PerLibrary for *;

    function transferReserves(
        Reserves originReserves,
        Reserves destReserves,
        uint256 timeElapsed,
        uint24 maxPriceMovePerSecond
    ) internal pure returns (Reserves result) {
        if (destReserves.bothPositive()) {
            if (!originReserves.bothPositive()) {
                result = destReserves;
            } else {
                (uint256 truncatedReserve0, uint256 truncatedReserve1) = originReserves.reserves();
                uint256 priceMoved = maxPriceMovePerSecond * (timeElapsed ** 2);
                uint128 newTruncatedReserve0 = 0;
                uint128 newTruncatedReserve1 = destReserves.reserve1();
                uint256 _reserve0 = destReserves.reserve0();

                uint256 reserve0Min =
                    Math.mulDiv(newTruncatedReserve1, truncatedReserve0.lowerMillion(priceMoved), truncatedReserve1);
                uint256 reserve0Max =
                    Math.mulDiv(newTruncatedReserve1, truncatedReserve0.upperMillion(priceMoved), truncatedReserve1);
                if (_reserve0 < reserve0Min) {
                    newTruncatedReserve0 = reserve0Min.toUint128();
                } else if (_reserve0 > reserve0Max) {
                    newTruncatedReserve0 = reserve0Max.toUint128();
                } else {
                    newTruncatedReserve0 = _reserve0.toUint128();
                }
                result = toReserves(newTruncatedReserve0, newTruncatedReserve1);
            }
        } else {
            result = destReserves;
        }
    }
}


/// @title A library for managing Likwid pools.
/// @notice This library contains all the functions for interacting with a Likwid pool.
library Pool {
    using CustomRevert for bytes4;
    using SafeCast for *;
    using SwapMath for *;
    using FeeLibrary for uint24;
    using PerLibrary for uint256;
    using TimeLibrary for uint32;
    using Pool for State;
    using PairPosition for PairPosition.State;
    using PairPosition for mapping(bytes32 => PairPosition.State);
    using LendPosition for LendPosition.State;
    using LendPosition for mapping(bytes32 => LendPosition.State);
    using ProtocolFeeLibrary for uint24;

    /// @notice Thrown when trying to initialize an already initialized pool
    error PoolAlreadyInitialized();

    /// @notice Thrown when trying to interact with a non-initialized pool
    error PoolNotInitialized();

    /// @notice Thrown when trying to remove more liquidity than available in the pool
    error InsufficientLiquidity();

    error InsufficientAmount();

    struct State {
        Slot0 slot0;
        /// @notice The cumulative borrow rate of the first currency in the pool.
        uint256 borrow0CumulativeLast;
        /// @notice The cumulative borrow rate of the second currency in the pool.
        uint256 borrow1CumulativeLast;
        /// @notice The cumulative deposit rate of the first currency in the pool.
        uint256 deposit0CumulativeLast;
        /// @notice The cumulative deposit rate of the second currency in the pool.
        uint256 deposit1CumulativeLast;
        Reserves realReserves;
        Reserves mirrorReserves;
        Reserves pairReserves;
        Reserves truncatedReserves;
        Reserves lendReserves;
        Reserves interestReserves;
        /// @notice The positions in the pool, mapped by a hash of the owner's address and a salt.
        mapping(bytes32 => PairPosition.State) positions;
        mapping(bytes32 => LendPosition.State) lendPositions;
    }

    struct ModifyLiquidityParams {
        // the address that owns the position
        address owner;
        uint256 amount0;
        uint256 amount1;
        // any change in liquidity
        int128 liquidityDelta;
        // used to distinguish positions of the same owner, at the same tick range
        bytes32 salt;
    }

    /// @notice Initializes the pool with a given fee
    /// @param self The pool state
    /// @param lpFee The initial fee for the pool
    function initialize(State storage self, uint24 lpFee) internal {
        if (self.borrow0CumulativeLast != 0) PoolAlreadyInitialized.selector.revertWith();

        self.slot0 = Slot0.wrap(bytes32(0)).setLastUpdated(uint32(block.timestamp)).setLpFee(lpFee);
        self.borrow0CumulativeLast = FixedPoint96.Q96;
        self.borrow1CumulativeLast = FixedPoint96.Q96;
        self.deposit0CumulativeLast = FixedPoint96.Q96;
        self.deposit1CumulativeLast = FixedPoint96.Q96;
    }

    /// @notice Sets the protocol fee for the pool
    /// @param self The pool state
    /// @param protocolFee The new protocol fee
    function setProtocolFee(State storage self, uint24 protocolFee) internal {
        self.checkPoolInitialized();
        self.slot0 = self.slot0.setProtocolFee(protocolFee);
    }

    /// @notice Sets the margin fee for the pool
    /// @param self The pool state
    /// @param marginFee The new margin fee
    function setMarginFee(State storage self, uint24 marginFee) internal {
        self.checkPoolInitialized();
        self.slot0 = self.slot0.setMarginFee(marginFee);
    }

    /// @notice Adds or removes liquidity from the pool
    /// @param self The pool state
    /// @param params The parameters for modifying liquidity
    /// @return delta The change in balances
    function modifyLiquidity(State storage self, ModifyLiquidityParams memory params)
        internal
        returns (BalanceDelta delta, int128 finalLiquidityDelta)
    {
        if (params.liquidityDelta == 0 && params.amount0 == 0 && params.amount1 == 0) {
            return (BalanceDelta.wrap(0), 0);
        }

        Slot0 _slot0 = self.slot0;
        Reserves _pairReserves = self.pairReserves;

        (uint128 _reserve0, uint128 _reserve1) = _pairReserves.reserves();
        uint128 totalSupply = _slot0.totalSupply();

        if (params.liquidityDelta < 0) {
            // --- Remove Liquidity ---
            uint256 liquidityToRemove = uint256(-int256(params.liquidityDelta));
            if (liquidityToRemove > totalSupply) InsufficientLiquidity.selector.revertWith();

            uint256 amount0Out = Math.mulDiv(liquidityToRemove, _reserve0, totalSupply);
            uint256 amount1Out = Math.mulDiv(liquidityToRemove, _reserve1, totalSupply);

            delta = toBalanceDelta(amount0Out.toInt128(), amount1Out.toInt128());
            self.slot0 = _slot0.setTotalSupply(totalSupply - liquidityToRemove.toUint128());
            finalLiquidityDelta = params.liquidityDelta;
        } else {
            // --- Add Liquidity ---
            uint256 amount0In;
            uint256 amount1In;
            uint256 liquidityAdded;

            if (totalSupply == 0) {
                amount0In = params.amount0;
                amount1In = params.amount1;
                liquidityAdded = Math.sqrt(amount0In * amount1In);
            } else {
                uint256 amount1FromAmount0 = Math.mulDiv(params.amount0, _reserve1, _reserve0);
                if (amount1FromAmount0 <= params.amount1) {
                    amount0In = params.amount0;
                    amount1In = amount1FromAmount0;
                } else {
                    amount0In = Math.mulDiv(params.amount1, _reserve0, _reserve1);
                    amount1In = params.amount1;
                }
                liquidityAdded = Math.min(
                    Math.mulDiv(amount0In, totalSupply, _reserve0), Math.mulDiv(amount1In, totalSupply, _reserve1)
                );
            }

            delta = toBalanceDelta(-amount0In.toInt128(), -amount1In.toInt128());

            self.slot0 = _slot0.setTotalSupply(totalSupply + liquidityAdded.toUint128());
            finalLiquidityDelta = liquidityAdded.toInt128();
        }
        ReservesLibrary.UpdateParam[] memory deltaParams = new ReservesLibrary.UpdateParam[](2);
        deltaParams[0] = ReservesLibrary.UpdateParam(ReservesType.REAL, delta);
        deltaParams[1] = ReservesLibrary.UpdateParam(ReservesType.PAIR, delta);
        self.updateReserves(deltaParams);

        self.positions.get(params.owner, params.salt).update(finalLiquidityDelta, delta);
    }

    struct SwapParams {
        address sender;
        // zeroForOne Whether to swap token0 for token1
        bool zeroForOne;
        // The amount to swap, negative for exact input, positive for exact output
        int256 amountSpecified;
        // Whether to use the mirror reserves for the swap
        bool useMirror;
        bytes32 salt;
    }

    /// @notice Swaps tokens in the pool
    /// @param self The pool state
    /// @param params The parameters for the swap
    /// @return swapDelta The change in balances
    /// @return amountToProtocol The amount of fees to be sent to the protocol
    /// @return swapFee The fee for the swap
    /// @return feeAmount The total fee amount for the swap.
    function swap(State storage self, SwapParams memory params, uint24 defaultProtocolFee)
        internal
        returns (BalanceDelta swapDelta, uint256 amountToProtocol, uint24 swapFee, uint256 feeAmount)
    {
        Reserves _pairReserves = self.pairReserves;
        Reserves _truncatedReserves = self.truncatedReserves;
        Slot0 _slot0 = self.slot0;
        uint24 _lpFee = _slot0.lpFee();

        bool exactIn = params.amountSpecified < 0;

        uint256 amountIn;
        uint256 amountOut;

        if (exactIn) {
            amountIn = uint256(-params.amountSpecified);
            (amountOut, swapFee, feeAmount) =
                SwapMath.getAmountOut(_pairReserves, _truncatedReserves, _lpFee, params.zeroForOne, amountIn);
        } else {
            amountOut = uint256(params.amountSpecified);
            (amountIn, swapFee, feeAmount) =
                SwapMath.getAmountIn(_pairReserves, _truncatedReserves, _lpFee, params.zeroForOne, amountOut);
        }

        (amountToProtocol, feeAmount) =
            ProtocolFeeLibrary.splitFee(_slot0.protocolFee(defaultProtocolFee), FeeTypes.SWAP, feeAmount);

        int128 amount0Delta;
        int128 amount1Delta;

        if (params.zeroForOne) {
            amount0Delta = -amountIn.toInt128();
            amount1Delta = amountOut.toInt128();
        } else {
            amount0Delta = amountOut.toInt128();
            amount1Delta = -amountIn.toInt128();
        }

        ReservesLibrary.UpdateParam[] memory deltaParams;
        swapDelta = toBalanceDelta(amount0Delta, amount1Delta);
        if (!params.useMirror) {
            deltaParams = new ReservesLibrary.UpdateParam[](2);
            deltaParams[0] = ReservesLibrary.UpdateParam(ReservesType.REAL, swapDelta);
            deltaParams[1] = ReservesLibrary.UpdateParam(ReservesType.PAIR, swapDelta);
        } else {
            deltaParams = new ReservesLibrary.UpdateParam[](3);
            BalanceDelta realDelta;
            BalanceDelta lendDelta;
            if (params.zeroForOne) {
                realDelta = toBalanceDelta(amount0Delta, 0);
                lendDelta = toBalanceDelta(0, -amount1Delta);
            } else {
                realDelta = toBalanceDelta(0, amount1Delta);
                lendDelta = toBalanceDelta(-amount0Delta, 0);
            }
            deltaParams[0] = ReservesLibrary.UpdateParam(ReservesType.REAL, realDelta);
            // pair MIRROR<=>lend MIRROR
            deltaParams[1] = ReservesLibrary.UpdateParam(ReservesType.LEND, lendDelta);
            deltaParams[2] = ReservesLibrary.UpdateParam(ReservesType.PAIR, swapDelta);
            uint256 depositCumulativeLast;
            if (params.zeroForOne) {
                depositCumulativeLast = self.deposit1CumulativeLast;
            } else {
                depositCumulativeLast = self.deposit0CumulativeLast;
            }
            self.lendPositions.get(params.sender, params.zeroForOne, params.salt).update(
                params.zeroForOne, depositCumulativeLast, lendDelta
            );
        }
        self.updateReserves(deltaParams);
    }

    struct LendParams {
        address sender;
        /// False if lend token0,true if lend token1
        bool lendForOne;
        /// The amount to lend, negative for deposit, positive for withdraw
        int128 lendAmount;
        bytes32 salt;
    }

    /// @notice Lends tokens to the pool.
    /// @param self The pool state.
    /// @param params The parameters for the lending operation.
    /// @return lendDelta The change in the lender's balance.
    /// @return depositCumulativeLast The last cumulative deposit rate.
    function lend(State storage self, LendParams memory params)
        internal
        returns (BalanceDelta lendDelta, uint256 depositCumulativeLast)
    {
        int128 amount0Delta;
        int128 amount1Delta;

        if (params.lendForOne) {
            amount1Delta = params.lendAmount;
            depositCumulativeLast = self.deposit1CumulativeLast;
        } else {
            amount0Delta = params.lendAmount;
            depositCumulativeLast = self.deposit0CumulativeLast;
        }

        lendDelta = toBalanceDelta(amount0Delta, amount1Delta);
        ReservesLibrary.UpdateParam[] memory deltaParams = new ReservesLibrary.UpdateParam[](2);
        deltaParams[0] = ReservesLibrary.UpdateParam(ReservesType.REAL, lendDelta);
        deltaParams[1] = ReservesLibrary.UpdateParam(ReservesType.LEND, lendDelta);
        self.updateReserves(deltaParams);

        self.lendPositions.get(params.sender, params.lendForOne, params.salt).update(
            params.lendForOne, depositCumulativeLast, lendDelta
        );
    }

    function margin(State storage self, MarginBalanceDelta memory params, uint24 defaultProtocolFee)
        internal
        returns (BalanceDelta marginDelta, uint256 amountToProtocol, uint256 feeAmount)
    {
        if (
            (params.action != MarginActions.CLOSE && params.action != MarginActions.LIQUIDATE_BURN)
                && params.marginDelta == BalanceDeltaLibrary.ZERO_DELTA
        ) {
            InsufficientAmount.selector.revertWith();
        }
        Slot0 _slot0 = self.slot0;
        if (params.action == MarginActions.MARGIN) {
            (, feeAmount) = params.marginFee.deduct(params.marginTotal);
            (amountToProtocol,) =
                ProtocolFeeLibrary.splitFee(_slot0.protocolFee(defaultProtocolFee), FeeTypes.MARGIN, feeAmount);
        }
        marginDelta = params.marginDelta;
        if (params.debtDepositCumulativeLast > 0) {
            if (params.marginForOne) {
                self.deposit0CumulativeLast = params.debtDepositCumulativeLast;
            } else {
                self.deposit1CumulativeLast = params.debtDepositCumulativeLast;
            }
        }
        ReservesLibrary.UpdateParam[] memory deltaParams = new ReservesLibrary.UpdateParam[](4);
        deltaParams[0] = ReservesLibrary.UpdateParam(ReservesType.REAL, marginDelta);
        deltaParams[1] = ReservesLibrary.UpdateParam(ReservesType.PAIR, params.pairDelta);
        deltaParams[2] = ReservesLibrary.UpdateParam(ReservesType.LEND, params.lendDelta);
        deltaParams[3] = ReservesLibrary.UpdateParam(ReservesType.MIRROR, params.mirrorDelta);
        self.updateReserves(deltaParams);
    }

    /// @notice Reverts if the given pool has not been initialized
    /// @param self The pool state
    function checkPoolInitialized(State storage self) internal view {
        if (self.borrow0CumulativeLast == 0) PoolNotInitialized.selector.revertWith();
    }

    /// @notice Updates the interest rates for the pool.
    /// @param self The pool state.
    /// @param marginState The current rate state.
    /// @return pairInterest0 The interest earned by the pair for token0.
    /// @return pairInterest1 The interest earned by the pair for token1.
    function updateInterests(State storage self, MarginState marginState, uint24 defaultProtocolFee)
        internal
        returns (uint256 pairInterest0, uint256 pairInterest1)
    {
        Slot0 _slot0 = self.slot0;
        uint256 timeElapsed = _slot0.lastUpdated().getTimeElapsed();
        if (timeElapsed == 0) return (0, 0);

        Reserves _realReserves = self.realReserves;
        Reserves _mirrorReserves = self.mirrorReserves;
        Reserves _interestReserves = self.interestReserves;
        Reserves _pairReserves = self.pairReserves;
        Reserves _lendReserves = self.lendReserves;

        uint256 borrow0CumulativeBefore = self.borrow0CumulativeLast;
        uint256 borrow1CumulativeBefore = self.borrow1CumulativeLast;

        (uint256 borrow0CumulativeLast, uint256 borrow1CumulativeLast) = InterestMath.getBorrowRateCumulativeLast(
            timeElapsed, borrow0CumulativeBefore, borrow1CumulativeBefore, marginState, _realReserves, _mirrorReserves
        );
        (uint256 pairReserve0, uint256 pairReserve1) = _pairReserves.reserves();
        (uint256 lendReserve0, uint256 lendReserve1) = _lendReserves.reserves();
        (uint256 mirrorReserve0, uint256 mirrorReserve1) = _mirrorReserves.reserves();
        (uint256 interestReserve0, uint256 interestReserve1) = _interestReserves.reserves();

        InterestMath.InterestUpdateResult memory result0 = InterestMath.updateInterestForOne(
            InterestMath.InterestUpdateParams({
                mirrorReserve: mirrorReserve0,
                borrowCumulativeLast: borrow0CumulativeLast,
                borrowCumulativeBefore: borrow0CumulativeBefore,
                interestReserve: interestReserve0,
                pairReserve: pairReserve0,
                lendReserve: lendReserve0,
                depositCumulativeLast: self.deposit0CumulativeLast,
                protocolFee: _slot0.protocolFee(defaultProtocolFee)
            })
        );

        if (result0.changed) {
            mirrorReserve0 = result0.newMirrorReserve;
            pairReserve0 = result0.newPairReserve;
            lendReserve0 = result0.newLendReserve;
            interestReserve0 = result0.newInterestReserve;
            self.deposit0CumulativeLast = result0.newDepositCumulativeLast;
            pairInterest0 = result0.pairInterest;
            self.borrow0CumulativeLast = borrow0CumulativeLast;
        }

        InterestMath.InterestUpdateResult memory result1 = InterestMath.updateInterestForOne(
            InterestMath.InterestUpdateParams({
                mirrorReserve: mirrorReserve1,
                borrowCumulativeLast: borrow1CumulativeLast,
                borrowCumulativeBefore: borrow1CumulativeBefore,
                interestReserve: interestReserve1,
                pairReserve: pairReserve1,
                lendReserve: lendReserve1,
                depositCumulativeLast: self.deposit1CumulativeLast,
                protocolFee: _slot0.protocolFee(defaultProtocolFee)
            })
        );

        if (result1.changed) {
            mirrorReserve1 = result1.newMirrorReserve;
            pairReserve1 = result1.newPairReserve;
            lendReserve1 = result1.newLendReserve;
            interestReserve1 = result1.newInterestReserve;
            self.deposit1CumulativeLast = result1.newDepositCumulativeLast;
            pairInterest1 = result1.pairInterest;
            self.borrow1CumulativeLast = borrow1CumulativeLast;
        }

        if (result0.changed || result1.changed) {
            self.mirrorReserves = toReserves(mirrorReserve0.toUint128(), mirrorReserve1.toUint128());
            self.pairReserves = toReserves(pairReserve0.toUint128(), pairReserve1.toUint128());
            self.lendReserves = toReserves(lendReserve0.toUint128(), lendReserve1.toUint128());
            Reserves _truncatedReserves = self.truncatedReserves;
            self.truncatedReserves = PriceMath.transferReserves(
                _truncatedReserves,
                _pairReserves,
                _slot0.lastUpdated().getTimeElapsed(),
                marginState.maxPriceMovePerSecond()
            );
        } else {
            self.truncatedReserves = _pairReserves;
        }

        self.interestReserves = toReserves(interestReserve0.toUint128(), interestReserve1.toUint128());
        self.slot0 = self.slot0.setLastUpdated(uint32(block.timestamp));
    }

    /// @notice Updates the reserves of the pool.
    /// @param self The pool state.
    /// @param params An array of parameters for updating the reserves.
    function updateReserves(State storage self, ReservesLibrary.UpdateParam[] memory params) internal {
        if (params.length == 0) return;
        Reserves _realReserves = self.realReserves;
        Reserves _mirrorReserves = self.mirrorReserves;
        Reserves _pairReserves = self.pairReserves;
        Reserves _lendReserves = self.lendReserves;
        for (uint256 i = 0; i < params.length; i++) {
            ReservesType _type = params[i]._type;
            BalanceDelta delta = params[i].delta;
            if (_type == ReservesType.REAL) {
                _realReserves = _realReserves.applyDelta(delta);
            } else if (_type == ReservesType.MIRROR) {
                _mirrorReserves = _mirrorReserves.applyDelta(delta, true);
            } else if (_type == ReservesType.PAIR) {
                _pairReserves = _pairReserves.applyDelta(delta);
            } else if (_type == ReservesType.LEND) {
                _lendReserves = _lendReserves.applyDelta(delta);
            }
        }
        self.realReserves = _realReserves;
        self.mirrorReserves = _mirrorReserves;
        self.pairReserves = _pairReserves;
        self.lendReserves = _lendReserves;
    }
}


// Failed to resolve import: import {Hooks} from "v4-core/src/libraries/Hooks.sol";


// Failed to resolve import: import {BeforeSwapDelta, BeforeSwapDeltaLibrary} from "v4-core/src/types/BeforeSwapDelta.sol";














/// @notice Interface for claims over a contract balance, wrapped as a ERC6909
interface IERC6909Claims {
    /*//////////////////////////////////////////////////////////////
                                 EVENTS
    //////////////////////////////////////////////////////////////*/

    event OperatorSet(address indexed owner, address indexed operator, bool approved);

    event Approval(address indexed owner, address indexed spender, uint256 indexed id, uint256 amount);

    event Transfer(address caller, address indexed from, address indexed to, uint256 indexed id, uint256 amount);

    /*//////////////////////////////////////////////////////////////
                                 FUNCTIONS
    //////////////////////////////////////////////////////////////*/

    /// @notice Owner balance of an id.
    /// @param owner The address of the owner.
    /// @param id The id of the token.
    /// @return amount The balance of the token.
    function balanceOf(address owner, uint256 id) external view returns (uint256 amount);

    /// @notice Spender allowance of an id.
    /// @param owner The address of the owner.
    /// @param spender The address of the spender.
    /// @param id The id of the token.
    /// @return amount The allowance of the token.
    function allowance(address owner, address spender, uint256 id) external view returns (uint256 amount);

    /// @notice Checks if a spender is approved by an owner as an operator
    /// @param owner The address of the owner.
    /// @param spender The address of the spender.
    /// @return approved The approval status.
    function isOperator(address owner, address spender) external view returns (bool approved);

    /// @notice Transfers an amount of an id from the caller to a receiver.
    /// @param receiver The address of the receiver.
    /// @param id The id of the token.
    /// @param amount The amount of the token.
    /// @return bool True, always, unless the function reverts
    function transfer(address receiver, uint256 id, uint256 amount) external returns (bool);

    /// @notice Transfers an amount of an id from a sender to a receiver.
    /// @param sender The address of the sender.
    /// @param receiver The address of the receiver.
    /// @param id The id of the token.
    /// @param amount The amount of the token.
    /// @return bool True, always, unless the function reverts
    function transferFrom(address sender, address receiver, uint256 id, uint256 amount) external returns (bool);

    /// @notice Approves an amount of an id to a spender.
    /// @param spender The address of the spender.
    /// @param id The id of the token.
    /// @param amount The amount of the token.
    /// @return bool True, always
    function approve(address spender, uint256 id, uint256 amount) external returns (bool);

    /// @notice Sets or removes an operator for the caller.
    /// @param operator The address of the operator.
    /// @param approved The approval status.
    /// @return bool True, always
    function setOperator(address operator, bool approved) external returns (bool);
}








/// @notice Interface for all interest-fee related functions in the pool manager
interface IMarginBase {
    error Unauthorized();

    event MarginControllerUpdated(address indexed marginController);

    /// @notice Emitted when the rate state is updated
    /// @param newMarginState The new rate state being set
    /// @dev This event is emitted when the rate state is updated, allowing external observers to
    event MarginStateUpdated(MarginState indexed newMarginState);

    /// @notice Sets the rate state for interest fees
    /// @param newMarginState The new rate state to set
    /// @dev This function allows the owner to update the rate state, which is used to
    /// calculate interest fees. It emits a MarginStateUpdated event upon success.
    /// @dev Only the owner can call this function.
    /// @dev Reverts if the caller is not the owner.
    function setMarginState(MarginState newMarginState) external;

    function marginState() external view returns (MarginState);

    function marginController() external view returns (address);
}




/// @notice Interface for functions to access any storage slot in a contract
interface IExtsload {
    /// @notice Called by external contracts to access granular pool state
    /// @param slot Key of slot to sload
    /// @return value The value of the slot as bytes32
    function extsload(bytes32 slot) external view returns (bytes32 value);

    /// @notice Called by external contracts to access granular pool state
    /// @param startSlot Key of slot to start sloading from
    /// @param nSlots Number of slots to load into return value
    /// @return values List of loaded values.
    function extsload(bytes32 startSlot, uint256 nSlots) external view returns (bytes32[] memory values);

    /// @notice Called by external contracts to access sparse pool state
    /// @param slots List of slots to SLOAD from.
    /// @return values List of loaded values.
    function extsload(bytes32[] calldata slots) external view returns (bytes32[] memory values);
}




/// @notice Interface for functions to access any   storage slot in a contract
interface IExttload {
    /// @notice Called by external contracts to access   storage of the contract
    /// @param slot Key of slot to tload
    /// @return value The value of the slot as bytes32
    function exttload(bytes32 slot) external view returns (bytes32 value);

    /// @notice Called by external contracts to access sparse   pool state
    /// @param slots List of slots to tload
    /// @return values List of loaded values
    function exttload(bytes32[] calldata slots) external view returns (bytes32[] memory values);
}


/// @notice Interface for the LikwidVault
interface IVault is IERC6909Claims, IMarginBase, IExtsload, IExttload {
    /// @notice Thrown when a currency is not netted out after the contract is unlocked
    error CurrencyNotSettled();

    /// @notice Thrown when trying to interact with a non-initialized pool
    error PoolNotInitialized();

    /// @notice Thrown when trying to initialize a pool that is already initialized
    error PoolAlreadyInitialized(PoolId id);

    /// @notice Thrown when unlock is called, but the contract is already unlocked
    error AlreadyUnlocked();

    /// @notice Thrown when a function is called that requires the contract to be unlocked, but it is not
    error VaultLocked();

    /// @notice PoolKey must have currencies where address(currency0) < address(currency1)
    error CurrenciesOutOfOrderOrEqual(address currency0, address currency1);

    /// @notice Thrown when trying to amount of 0
    error AmountCannotBeZero();

    ///@notice Thrown when native currency is passed to a non native settlement
    error NonzeroNativeValue();

    /// @notice Thrown when `clear` is called with an amount that is not exactly equal to the open currency delta.
    error MustClearExactPositiveDelta();

    /// @notice Emitted when a new pool is initialized
    /// @param id The abi encoded hash of the pool key struct for the new pool
    /// @param currency0 The first currency of the pool by address sort order
    /// @param currency1 The second currency of the pool by address sort order
    /// @param fee The fee collected upon every swap in the pool, denominated in hundredths of a bip
    event Initialize(PoolId indexed id, Currency indexed currency0, Currency indexed currency1, uint24 fee);

    /// @notice Emitted when a liquidity position is modified
    /// @param id The abi encoded hash of the pool key struct for the pool that was modified
    /// @param sender The address that modified the pool
    /// @param callerDelta The caller delta
    /// @param liquidityDelta The amount of liquidity that was added or removed
    /// @param salt The extra data to make positions unique
    event ModifyLiquidity(
        PoolId indexed id, address indexed sender, int256 callerDelta, int256 liquidityDelta, bytes32 salt
    );

    /// @notice Emitted for swaps between currency0 and currency1
    /// @param id The abi encoded hash of the pool key struct for the pool that was modified
    /// @param sender The address that initiated the swap call, and that received the callback
    /// @param amount0 The delta of the currency0 balance of the pool
    /// @param amount1 The delta of the currency1 balance of the pool
    /// @param fee The swap fee in hundredths of a bip
    event Swap(PoolId indexed id, address indexed sender, int128 amount0, int128 amount1, uint24 fee);

    /// @notice Emitted for fees
    /// @param id The abi encoded hash of the pool key struct for the pool that was modified
    /// @param currency The currency of the fee
    /// @param sender The address that paid the fee
    /// @param feeType The type of fee
    /// @param feeAmount The amount of the fee
    event Fees(PoolId indexed id, Currency indexed currency, address indexed sender, uint8 feeType, uint256 feeAmount);

    event Lend(
        PoolId indexed id,
        address indexed sender,
        bool lendingForOne,
        int128 lendingAmount,
        uint256 depositCumulativeLast,
        bytes32 salt
    );

    /// @notice All interactions on the contract that account deltas require unlocking. A caller that calls `unlock` must implement
    /// `IUnlockCallback(msg.sender).unlockCallback(data)`, where they interact with the remaining functions on this contract.
    /// @dev The only functions callable without an unlocking are `initialize`
    /// @param data Any data to pass to the callback, via `IUnlockCallback(msg.sender).unlockCallback(data)`
    /// @return The data returned by the call to `IUnlockCallback(msg.sender).unlockCallback(data)`
    function unlock(bytes calldata data) external returns (bytes memory);

    /// @notice Initialize the state for a given pool ID
    /// @dev A swap fee totaling MAX_SWAP_FEE (100%) makes exact output swaps impossible since the input is entirely consumed by the fee
    /// @param key The pool key for the pool to initialize
    function initialize(PoolKey memory key) external;

    struct ModifyLiquidityParams {
        uint256 amount0;
        uint256 amount1;
        // how to modify the liquidity
        int256 liquidityDelta;
        // a value to set if you want unique liquidity positions at the same range
        bytes32 salt;
    }

    /// @notice Modify the liquidity for the given pool
    /// @dev Poke by calling with a zero liquidityDelta
    /// @param key The pool to modify liquidity in
    /// @param params The parameters for modifying the liquidity
    /// @return callerDelta The balance delta of the caller of modifyLiquidity. This is the total of both principal, fee deltas, and hook deltas if applicable
    /// @return finalLiquidityDelta The actual change in liquidity of the pool after the modification
    function modifyLiquidity(PoolKey memory key, ModifyLiquidityParams memory params)
        external
        returns (BalanceDelta callerDelta, int128 finalLiquidityDelta);

    struct SwapParams {
        /// Whether to swap token0 for token1 or vice versa
        bool zeroForOne;
        /// The desired input amount if negative (exactIn), or the desired output amount if positive (exactOut)
        int256 amountSpecified;
        /// Whether to use the mirror reserves for the swap
        bool useMirror;
        bytes32 salt;
    }

    /// @notice Swap against the given pool
    /// @param key The pool to swap in
    /// @param params The parameters for swapping
    /// @return swapDelta The balance delta of the address swapping
    function swap(PoolKey memory key, SwapParams memory params)
        external
        returns (BalanceDelta swapDelta, uint24 swapFee, uint256 feeAmount);

    struct LendParams {
        /// False if lend token0,true if lend token1
        bool lendForOne;
        /// The amount to lend, negative for deposit, positive for withdraw
        int128 lendAmount;
        bytes32 salt;
    }

    /// @notice Lends tokens to a pool.
    /// @dev Allows a user to lend tokens to a pool and earn interest.
    /// @param key The key of the pool to lend to.
    /// @param params The parameters for the lending operation, including the amount to lend.
    /// @return lendDelta The change in the lender's balance.
    function lend(PoolKey memory key, LendParams memory params) external returns (BalanceDelta lendDelta);

    function marginBalance(PoolKey memory key, MarginBalanceDelta memory params)
        external
        returns (BalanceDelta marginDelta, uint256 feeAmount);

    /// @notice Writes the current ERC20 balance of the specified currency to   storage
    /// This is used to checkpoint balances for the manager and derive deltas for the caller.
    /// @dev This MUST be called before any ERC20 tokens are sent into the contract, but can be skipped
    /// for native tokens because the amount to settle is determined by the sent value.
    /// However, if an ERC20 token has been synced and not settled, and the caller instead wants to settle
    /// native funds, this function can be called with the native currency to then be able to settle the native currency
    function sync(Currency currency) external;

    /// @notice Called by the user to net out some value owed to the user
    /// @dev Will revert if the requested amount is not available, consider using `mint` instead
    /// @dev Can also be used as a mechanism for free flash loans
    /// @param currency The currency to withdraw from the pool manager
    /// @param to The address to withdraw to
    /// @param amount The amount of currency to withdraw
    function take(Currency currency, address to, uint256 amount) external;

    /// @notice Called by the user to pay what is owed
    /// @return paid The amount of currency settled
    function settle() external payable returns (uint256 paid);

    /// @notice Called by the user to pay on behalf of another address
    /// @param recipient The address to credit for the payment
    /// @return paid The amount of currency settled
    function settleFor(address recipient) external payable returns (uint256 paid);

    /// @notice WARNING - Any currency that is cleared, will be non-retrievable, and locked in the contract permanently.
    /// A call to clear will zero out a positive balance WITHOUT a corresponding transfer.
    /// @dev This could be used to clear a balance that is considered dust.
    /// Additionally, the amount must be the exact positive balance. This is to enforce that the caller is aware of the amount being cleared.
    function clear(Currency currency, uint256 amount) external;

    /// @notice Called by the user to move value into ERC6909 balance
    /// @param to The address to mint the tokens to
    /// @param id The currency address to mint to ERC6909s, as a uint256
    /// @param amount The amount of currency to mint
    /// @dev The id is converted to a uint160 to correspond to a currency address
    /// If the upper 12 bytes are not 0, they will be 0-ed out
    function mint(address to, uint256 id, uint256 amount) external;

    /// @notice Called by the user to move value from ERC6909 balance
    /// @param from The address to burn the tokens from
    /// @param id The currency address to burn from ERC6909s, as a uint256
    /// @param amount The amount of currency to burn
    /// @dev The id is converted to a uint160 to correspond to a currency address
    /// If the upper 12 bytes are not 0, they will be 0-ed out
    function burn(address from, uint256 id, uint256 amount) external;
}










struct PoolState {
    MarginState marginState;
    uint128 totalSupply;
    uint32 lastUpdated;
    uint24 lpFee;
    uint24 marginFee;
    uint24 protocolFee;
    uint256 borrow0CumulativeLast;
    uint256 borrow1CumulativeLast;
    uint256 deposit0CumulativeLast;
    uint256 deposit1CumulativeLast;
    Reserves realReserves;
    Reserves mirrorReserves;
    Reserves pairReserves;
    Reserves truncatedReserves;
    Reserves lendReserves;
    Reserves interestReserves;
}









/// @title A helper library to provide state getters for a Likwid pool
/// @notice This library provides functions to read the state of a Likwid pool from storage.
library StateLibrary {
    using SafeCast for *;
    using Slot0Library for Slot0;
    using ReservesLibrary for Reserves;
    using PositionLibrary for address;
    using TimeLibrary for uint32;

    /// @notice The storage slot of the `lastStageTimestampStore` mapping in the MarginBase contract.
    /// @dev This is an assumption. If the storage layout of MarginBase changes, this value needs to be updated.
    bytes32 public constant LAST_STAGE_TIMESTAMP_STORE_SLOT = bytes32(uint256(3));
    /// @notice The storage slot of the `liquidityLockedQueue` mapping in the MarginBase contract.
    /// @dev This is an assumption. If the storage layout of MarginBase changes, this value needs to be updated.
    bytes32 public constant LIQUIDITY_LOCKED_QUEUE_SLOT = bytes32(uint256(4));

    /// @notice The storage slot of the `_pools` mapping in the LikwidVault contract.
    bytes32 public constant POOLS_SLOT = bytes32(uint256(10));

    // Offsets for fields within the Pool.State struct
    uint256 internal constant BORROW_0_CUMULATIVE_LAST_OFFSET = 1;
    uint256 internal constant BORROW_1_CUMULATIVE_LAST_OFFSET = 2;
    uint256 internal constant DEPOSIT_0_CUMULATIVE_LAST_OFFSET = 3;
    uint256 internal constant DEPOSIT_1_CUMULATIVE_LAST_OFFSET = 4;
    uint256 internal constant REAL_RESERVES_OFFSET = 5;
    uint256 internal constant MIRROR_RESERVES_OFFSET = 6;
    uint256 internal constant PAIR_RESERVES_OFFSET = 7;
    uint256 internal constant TRUNCATED_RESERVES_OFFSET = 8;
    uint256 internal constant LEND_RESERVES_OFFSET = 9;
    uint256 internal constant INTEREST_RESERVES_OFFSET = 10;
    uint256 internal constant POSITIONS_OFFSET = 11;
    uint256 internal constant LEND_POSITIONS_OFFSET = 12;

    /**
     * @notice Get the unpacked Slot0 of the pool.
     * @dev Corresponds to pools[poolId].slot0
     * @param vault The vault contract.
     * @param poolId The ID of the pool.
     * @return totalSupply The total supply of liquidity tokens.
     * @return lastUpdated The timestamp of the last update.
     * @return protocolFee The protocol fee of the pool.
     * @return lpFee The swap fee of the pool.
     * @return marginFee The margin fee of the pool.
     */
    function getSlot0(IVault vault, PoolId poolId)
        internal
        view
        returns (uint128 totalSupply, uint32 lastUpdated, uint24 protocolFee, uint24 lpFee, uint24 marginFee)
    {
        bytes32 stateSlot = _getPoolStateSlot(poolId);
        Slot0 slot0 = Slot0.wrap(vault.extsload(stateSlot));
        totalSupply = slot0.totalSupply();
        lastUpdated = slot0.lastUpdated();
        protocolFee = slot0.protocolFee();
        lpFee = slot0.lpFee();
        marginFee = slot0.marginFee();
    }

    /**
     * @notice Retrieves the cumulative borrow and deposit rates of a pool.
     * @param vault The vault contract.
     * @param poolId The ID of the pool.
     * @return borrow0CumulativeLast The cumulative borrow rate for currency 0.
     * @return borrow1CumulativeLast The cumulative borrow rate for currency 1.
     * @return deposit0CumulativeLast The cumulative deposit rate for currency 0.
     * @return deposit1CumulativeLast The cumulative deposit rate for currency 1.
     */
    function getBorrowDepositCumulative(IVault vault, PoolId poolId)
        internal
        view
        returns (
            uint256 borrow0CumulativeLast,
            uint256 borrow1CumulativeLast,
            uint256 deposit0CumulativeLast,
            uint256 deposit1CumulativeLast
        )
    {
        bytes32 stateSlot = _getPoolStateSlot(poolId);
        bytes32 startSlot = bytes32(uint256(stateSlot) + BORROW_0_CUMULATIVE_LAST_OFFSET);

        bytes32[] memory data = vault.extsload(startSlot, 4);
        assembly {
            borrow0CumulativeLast := mload(add(data, 0x20))
            borrow1CumulativeLast := mload(add(data, 0x40))
            deposit0CumulativeLast := mload(add(data, 0x60))
            deposit1CumulativeLast := mload(add(data, 0x80))
        }
    }

    /**
     * @notice Retrieves the pair reserves of a pool.
     * @param vault The vault contract.
     * @param poolId The ID of the pool.
     * @return The packed pair reserves of the pool.
     */
    function getPairReserves(IVault vault, PoolId poolId) internal view returns (Reserves) {
        bytes32 slot = bytes32(uint256(_getPoolStateSlot(poolId)) + PAIR_RESERVES_OFFSET);
        return Reserves.wrap(uint256(vault.extsload(slot)));
    }

    /**
     * @notice Retrieves the real reserves of a pool.
     * @param vault The vault contract.
     * @param poolId The ID of the pool.
     * @return The packed real reserves of the pool.
     */
    function getRealReserves(IVault vault, PoolId poolId) internal view returns (Reserves) {
        bytes32 slot = bytes32(uint256(_getPoolStateSlot(poolId)) + REAL_RESERVES_OFFSET);
        return Reserves.wrap(uint256(vault.extsload(slot)));
    }

    /**
     * @notice Retrieves the mirror reserves of a pool.
     * @param vault The vault contract.
     * @param poolId The ID of the pool.
     * @return The packed mirror reserves of the pool.
     */
    function getMirrorReserves(IVault vault, PoolId poolId) internal view returns (Reserves) {
        bytes32 slot = bytes32(uint256(_getPoolStateSlot(poolId)) + MIRROR_RESERVES_OFFSET);
        return Reserves.wrap(uint256(vault.extsload(slot)));
    }

    /**
     * @notice Retrieves the truncated reserves of a pool.
     * @param vault The vault contract.
     * @param poolId The ID of the pool.
     * @return The packed truncated reserves of the pool.
     */
    function getTruncatedReserves(IVault vault, PoolId poolId) internal view returns (Reserves) {
        bytes32 slot = bytes32(uint256(_getPoolStateSlot(poolId)) + TRUNCATED_RESERVES_OFFSET);
        return Reserves.wrap(uint256(vault.extsload(slot)));
    }

    /**
     * @notice Retrieves the lending reserves of a pool.
     * @param vault The vault contract.
     * @param poolId The ID of the pool.
     * @return The packed lending reserves of the pool.
     */
    function getLendReserves(IVault vault, PoolId poolId) internal view returns (Reserves) {
        bytes32 slot = bytes32(uint256(_getPoolStateSlot(poolId)) + LEND_RESERVES_OFFSET);
        return Reserves.wrap(uint256(vault.extsload(slot)));
    }

    /**
     * @notice Retrieves the interest reserves of a pool.
     * @param vault The vault contract.
     * @param poolId The ID of the pool.
     * @return The packed interest reserves of the pool.
     */
    function getInterestReserves(IVault vault, PoolId poolId) internal view returns (Reserves) {
        bytes32 slot = bytes32(uint256(_getPoolStateSlot(poolId)) + INTEREST_RESERVES_OFFSET);
        return Reserves.wrap(uint256(vault.extsload(slot)));
    }

    function getLastStageTimestamp(IVault vault, PoolId poolId) internal view returns (uint256) {
        bytes32 slot = keccak256(abi.encodePacked(PoolId.unwrap(poolId), LAST_STAGE_TIMESTAMP_STORE_SLOT));
        return uint256(vault.extsload(slot));
    }

    function getPairPositionState(IVault vault, PoolId poolId, address owner, bytes32 salt)
        internal
        view
        returns (PairPosition.State memory _position)
    {
        bytes32 positionKey = owner.calculatePositionKey(salt);

        bytes32 poolStateSlot = _getPoolStateSlot(poolId);
        bytes32 positionsMappingSlot = bytes32(uint256(poolStateSlot) + POSITIONS_OFFSET);
        bytes32 positionSlot = keccak256(abi.encodePacked(positionKey, positionsMappingSlot));

        bytes32[] memory data = vault.extsload(positionSlot, 2);
        _position.liquidity = uint128(uint256(data[0]));
        _position.totalInvestment = uint256(data[1]);
    }

    function getLendPositionState(IVault vault, PoolId poolId, address owner, bool lendForOne, bytes32 salt)
        internal
        view
        returns (LendPosition.State memory _position)
    {
        bytes32 positionKey = owner.calculatePositionKey(lendForOne, salt);

        bytes32 poolStateSlot = _getPoolStateSlot(poolId);
        bytes32 positionsMappingSlot = bytes32(uint256(poolStateSlot) + LEND_POSITIONS_OFFSET);
        bytes32 positionSlot = keccak256(abi.encodePacked(positionKey, positionsMappingSlot));

        bytes32[] memory data = vault.extsload(positionSlot, 2);
        uint256 slot0 = uint256(data[0]);
        _position.lendAmount = uint128(slot0);
        _position.depositCumulativeLast = uint256(data[1]);
    }

    function getRawStageLiquidities(IVault vault, PoolId poolId) internal view returns (uint256[] memory liquidities) {
        bytes32 dequeSlot = keccak256(abi.encodePacked(PoolId.unwrap(poolId), LIQUIDITY_LOCKED_QUEUE_SLOT));
        bytes32 dequeValue = vault.extsload(dequeSlot);

        uint128 front;
        uint128 back;
        assembly {
            front := and(dequeValue, 0x00000000000000000000000000000000ffffffffffffffffffffffffffffffff)
            back := shr(128, dequeValue)
        }

        uint256 len = back - front;
        liquidities = new uint256[](len);
        bytes32 valuesSlot = bytes32(uint256(dequeSlot) + 1);

        for (uint256 i = 0; i < len; i++) {
            uint256 valueIndex = front + i;
            bytes32 valueSlot = keccak256(abi.encodePacked(valueIndex, valuesSlot));
            liquidities[i] = uint256(vault.extsload(valueSlot));
        }
    }

    /**
     * @notice Calculates the storage slot for a specific pool's state.
     * @param poolId The ID of the pool.
     * @return The storage slot of the Pool.State struct.
     */
    function _getPoolStateSlot(PoolId poolId) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PoolId.unwrap(poolId), POOLS_SLOT));
    }

    function getCurrentState(IVault vault, PoolId poolId) internal view returns (PoolState memory state) {
        bytes32 poolStateSlot = _getPoolStateSlot(poolId);

        // 1. Get slot0
        (state.totalSupply, state.lastUpdated, state.protocolFee, state.lpFee, state.marginFee) =
            getSlot0(vault, poolId);

        // 2. Get all other data in one call
        bytes32 startSlot = bytes32(uint256(poolStateSlot) + 1); // BORROW_0_CUMULATIVE_LAST_OFFSET
        bytes32[] memory data = vault.extsload(startSlot, 10); // read 10 slots

        uint256 borrow0CumulativeBefore = uint256(data[0]);
        uint256 borrow1CumulativeBefore = uint256(data[1]);
        uint256 deposit0CumulativeBefore = uint256(data[2]);
        uint256 deposit1CumulativeBefore = uint256(data[3]);
        state.realReserves = Reserves.wrap(uint256(data[4]));
        state.mirrorReserves = Reserves.wrap(uint256(data[5]));
        state.pairReserves = Reserves.wrap(uint256(data[6]));
        Reserves _truncatedReserves = Reserves.wrap(uint256(data[7]));
        state.lendReserves = Reserves.wrap(uint256(data[8]));
        state.interestReserves = Reserves.wrap(uint256(data[9]));

        // 3. Get marginState
        state.marginState = IMarginBase(address(vault)).marginState();

        // 4. Get timeElapsed
        uint256 timeElapsed = state.lastUpdated.getTimeElapsed();

        (uint256 mirrorReserve0, uint256 mirrorReserve1) = state.mirrorReserves.reserves();
        (uint256 pairReserve0, uint256 pairReserve1) = state.pairReserves.reserves();
        (uint256 lendReserve0, uint256 lendReserve1) = state.lendReserves.reserves();
        (uint256 interestReserve0, uint256 interestReserve1) = state.interestReserves.reserves();

        (uint256 borrow0CumulativeLast, uint256 borrow1CumulativeLast) = InterestMath.getBorrowRateCumulativeLast(
            timeElapsed,
            borrow0CumulativeBefore,
            borrow1CumulativeBefore,
            state.marginState,
            state.realReserves,
            state.mirrorReserves
        );

        InterestMath.InterestUpdateParams memory params0 = InterestMath.InterestUpdateParams({
            mirrorReserve: mirrorReserve0,
            borrowCumulativeLast: borrow0CumulativeLast,
            borrowCumulativeBefore: borrow0CumulativeBefore,
            interestReserve: interestReserve0,
            pairReserve: pairReserve0,
            lendReserve: lendReserve0,
            depositCumulativeLast: deposit0CumulativeBefore,
            protocolFee: state.protocolFee
        });

        InterestMath.InterestUpdateResult memory result0 = InterestMath.updateInterestForOne(params0);
        if (result0.changed) {
            mirrorReserve0 = result0.newMirrorReserve;
            pairReserve0 = result0.newPairReserve;
            lendReserve0 = result0.newLendReserve;
            interestReserve0 = result0.newInterestReserve;
        }
        state.deposit0CumulativeLast = result0.newDepositCumulativeLast;
        state.borrow0CumulativeLast = borrow0CumulativeLast;

        InterestMath.InterestUpdateParams memory params1 = InterestMath.InterestUpdateParams({
            mirrorReserve: mirrorReserve1,
            borrowCumulativeLast: borrow1CumulativeLast,
            borrowCumulativeBefore: borrow1CumulativeBefore,
            interestReserve: interestReserve1,
            pairReserve: pairReserve1,
            lendReserve: lendReserve1,
            depositCumulativeLast: deposit1CumulativeBefore,
            protocolFee: state.protocolFee
        });

        InterestMath.InterestUpdateResult memory result1 = InterestMath.updateInterestForOne(params1);
        if (result1.changed) {
            mirrorReserve1 = result1.newMirrorReserve;
            pairReserve1 = result1.newPairReserve;
            lendReserve1 = result1.newLendReserve;
            interestReserve1 = result1.newInterestReserve;
        }
        state.borrow1CumulativeLast = borrow1CumulativeLast;
        state.deposit1CumulativeLast = result1.newDepositCumulativeLast;

        if (result0.changed || result1.changed) {
            state.mirrorReserves = toReserves(mirrorReserve0.toUint128(), mirrorReserve1.toUint128());
            state.pairReserves = toReserves(pairReserve0.toUint128(), pairReserve1.toUint128());
            state.lendReserves = toReserves(lendReserve0.toUint128(), lendReserve1.toUint128());
            state.truncatedReserves = PriceMath.transferReserves(
                _truncatedReserves, state.pairReserves, timeElapsed, state.marginState.maxPriceMovePerSecond()
            );
        } else {
            state.truncatedReserves = state.pairReserves;
        }

        state.interestReserves = toReserves(interestReserve0.toUint128(), interestReserve1.toUint128());
    }
}



/**
 * @dev Sandwich-resistant hook, based on
 * https://github.com/cairoeth/sandwich-resistant-hook/blob/master/src/srHook.sol[this]
 * implementation.
 *
 * This hook implements the sandwich-resistant AMM design introduced
 * https://www.umbraresearch.xyz/writings/sandwich-resistant-amm[here]. Specifically,
 * this hook guarantees that no swaps get filled at a price better than the price at
 * the beginning of the slot window (i.e. one block).
 *
 * Within a slot window, swaps impact the pool asymmetrically for buys and sells.
 * When a buy order is executed, the offer on the pool increases in accordance with
 * the xy=k curve. However, the bid price remains constant, instead increasing the
 * amount of liquidity on the bid. Subsequent sells eat into this liquidity, while
 * decreasing the offer price according to xy=k.
 *
 * NOTE: Swaps in the other direction do not get the positive price difference
 * compared to the initial price before the first swap in the block.
 *
 * WARNING: This is experimental software and is provided on an "as is" and "as available" basis. We do
 * not give any warranties and will not be liable for any losses incurred through any use of this code
 * base.
 *
 * _Available since v1.1.0_
 */
contract AntiSandwichHook is BaseDynamicAfterFee {
    using Pool for *;
    using StateLibrary for IPoolManager;
    using CurrencySettler for Currency;

    /// @dev Represents a checkpoint of the pool state at the beginning of a block.
    struct Checkpoint {
        uint48 blockNumber;
        Slot0 slot0;
        Pool.State state;
    }

    mapping(PoolId => Checkpoint) private _lastCheckpoints;

    constructor(IPoolManager _poolManager) BaseDynamicAfterFee(_poolManager) {}

    /**
     * @dev Handles the before swap hook, setting up checkpoints at the beginning of blocks
     * and calculating target outputs for subsequent swaps.
     *
     * For the first swap in a block:
     * - Saves the current pool state as a checkpoint
     *
     * For subsequent swaps in the same block:
     * - Calculates a target output based on the beginning-of-block state
     * - Sets the inherited `_targetOutput` and `_applyTargetOutput` variables to enforce price limits
     *
     * NOTE: This implementation skips calling `super._beforeSwap` in the first swap of the block. Consider
     * execution side effects might be missed if there is more than one definition for this function.
     */
    function _beforeSwap(
        address sender,
        PoolKey calldata key,
        IPoolManager.SwapParams calldata params,
        bytes calldata hookData
    ) internal override returns (bytes4, BeforeSwapDelta, uint24) {
        PoolId poolId = key.toId();
        Checkpoint storage _lastCheckpoint = _lastCheckpoints[poolId];

        // update the top-of-block `slot0` if new block
        if (_lastCheckpoint.blockNumber != uint48(block.number)) {
            _lastCheckpoint.slot0 = Slot0.wrap(poolManager.extsload(StateLibrary._getPoolStateSlot(poolId)));
            return (this.beforeSwap.selector, BeforeSwapDeltaLibrary.ZERO_DELTA, 0);
        }

        return super._beforeSwap(sender, key, params, hookData);
    }

    /**
     * @dev Handles the after swap hook, initializing the full pool state checkpoint for the first
     * swap in a block and updating the target output if needed.
     *
     * For the first swap in a block:
     * - Saves a detailed checkpoint of the pool state including liquidity and tick information
     * - This checkpoint will be used for subsequent swaps to calculate fair execution prices
     *
     * For all swaps:
     * - Caps the target output to the actual swap amount to prevent excessive fee collection
     */
    function _afterSwap(
        address sender,
        PoolKey calldata key,
        IPoolManager.SwapParams calldata params,
        BalanceDelta delta,
        bytes calldata hookData
    ) internal override returns (bytes4, int128) {
        uint48 blockNumber = uint48(block.number);
        PoolId poolId = key.toId();
        Checkpoint storage _lastCheckpoint = _lastCheckpoints[poolId];

        // after the first swap in block, initialize the temporary pool state
        if (_lastCheckpoint.blockNumber != blockNumber) {
            _lastCheckpoint.blockNumber = blockNumber;

            // iterate over ticks
            (, int24 tickAfter,,) = poolManager.getSlot0(poolId);
            for (int24 tick = _lastCheckpoint.slot0.tick(); tick < tickAfter; tick += key.tickSpacing) {
                (
                    uint128 liquidityGross,
                    int128 liquidityNet,
                    uint256 feeGrowthOutside0X128,
                    uint256 feeGrowthOutside1X128
                ) = poolManager.getTickInfo(poolId, tick);

                _lastCheckpoint.state.ticks[tick].liquidityGross = liquidityGross;
                _lastCheckpoint.state.ticks[tick].liquidityNet = liquidityNet;
                _lastCheckpoint.state.ticks[tick].feeGrowthOutside0X128 = feeGrowthOutside0X128;
                _lastCheckpoint.state.ticks[tick].feeGrowthOutside1X128 = feeGrowthOutside1X128;
            }

            // deep copy only values that are used and change in fair delta calculation
            _lastCheckpoint.state.slot0 = Slot0.wrap(poolManager.extsload(StateLibrary._getPoolStateSlot(poolId)));
            (_lastCheckpoint.state.feeGrowthGlobal0X128, _lastCheckpoint.state.feeGrowthGlobal1X128) =
                poolManager.getFeeGrowthGlobals(poolId);
            _lastCheckpoint.state.liquidity = poolManager.getLiquidity(poolId);
        }
        int128 unspecifiedAmount = (params.amountSpecified < 0 == params.zeroForOne) ? delta.amount1() : delta.amount0();

        if (unspecifiedAmount < 0) {
            unspecifiedAmount = -unspecifiedAmount;
        }

        // update target output if it exceeds the swap amount
        if (_targetOutput > uint128(unspecifiedAmount)) {
            _targetOutput = uint128(unspecifiedAmount);
        }

        return super._afterSwap(sender, key, params, delta, hookData);
    }

    /**
     * @dev Calculates the fair output amount based on the pool state at the beginning of the block.
     * This prevents sandwich attacks by ensuring trades can't get better prices than what was available
     * at the start of the block.
     *
     * The anti-sandwich mechanism works by:
     * * For currency0 to currency1 swaps (zeroForOne = true): The pool behaves normally with xy=k curve
     * * For currency1 to currency0 swaps (zeroForOne = false): The price is fixed at the beginning-of-block
     *   price, which prevents attackers from manipulating the price within a block
     */
    function _getTargetOutput(address, PoolKey calldata key, IPoolManager.SwapParams calldata params, bytes calldata)
        internal
        override
        returns (uint256 targetOutput, bool applyTargetOutput)
    {
        PoolId poolId = key.toId();
        Checkpoint storage _lastCheckpoint = _lastCheckpoints[poolId];

        // constant bid price
        if (!params.zeroForOne) {
            _lastCheckpoint.state.slot0 = _lastCheckpoint.slot0;
        }

        // calculate target output
        // NOTE: this functions does not execute the swap, it only calculates the output of a swap in the given state
        (BalanceDelta targetDelta,,,) = Pool.swap(
            _lastCheckpoint.state,
            Pool.SwapParams({
                tickSpacing: key.tickSpacing,
                zeroForOne: params.zeroForOne,
                amountSpecified: params.amountSpecified,
                sqrtPriceLimitX96: params.sqrtPriceLimitX96,
                lpFeeOverride: 0
            })
        );

        int128 target =
            (params.amountSpecified < 0 == params.zeroForOne) ? targetDelta.amount1() : targetDelta.amount0();

        targetOutput = uint256(uint128(target));
        applyTargetOutput = true;
    }

    /**
     * @dev Handles the excess tokens collected during the swap due to the anti-sandwich mechanism.
     * When a swap executes at a worse price than what's currently available in the pool (due to
     * enforcing the beginning-of-block price), the excess tokens are donated back to the pool
     * to benefit all liquidity providers.
     */
    function _afterSwapHandler(
        PoolKey calldata key,
        IPoolManager.SwapParams calldata params,
        BalanceDelta,
        uint256,
        uint256 feeAmount
    ) internal override {
        Currency unspecified = (params.amountSpecified < 0 == params.zeroForOne) ? (key.currency1) : (key.currency0);
        (uint256 amount0, uint256 amount1) = unspecified == key.currency0
            ? (uint256(uint128(feeAmount)), uint256(0))
            : (uint256(0), uint256(uint128(feeAmount)));

        // reset apply flag
        _applyTargetOutput = false;

        // settle and donate execess tokens to the pool
        poolManager.donate(key, amount0, amount1, "");
        unspecified.settle(poolManager, address(this), feeAmount, true);
    }

    /**
     * @dev Set the hook permissions, specifically `beforeSwap`, `afterSwap`, and `afterSwapReturnDelta`.
     *
     * @return permissions The hook permissions.
     */
    function getHookPermissions() public pure virtual override returns (Hooks.Permissions memory permissions) {
        return Hooks.Permissions({
            beforeInitialize: false,
            afterInitialize: false,
            beforeAddLiquidity: false,
            afterAddLiquidity: false,
            beforeRemoveLiquidity: false,
            afterRemoveLiquidity: false,
            beforeSwap: true,
            afterSwap: true,
            beforeDonate: false,
            afterDonate: false,
            beforeSwapReturnDelta: false,
            afterSwapReturnDelta: true,
            afterAddLiquidityReturnDelta: false,
            afterRemoveLiquidityReturnDelta: false
        });
    }
}
