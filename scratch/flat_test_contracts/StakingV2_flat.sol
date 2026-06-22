// SPDX-License-Identifier: MIT
pragma solidity 0.6.10;


pragma experimental ABIEncoderV2;


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


// OpenZeppelin Contracts (last updated v5.6.0) (utils/math/Math.sol)




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
        assembly ("memory-safe") {
            mstore(0x00, 0x4e487b71)
            mstore(0x20, code)
            revert(0x1c, 0x24)
        }
    }
}


// OpenZeppelin Contracts (last updated v5.6.0) (utils/math/SafeCast.sol)
// This file was procedurally generated from scripts/generate/templates/SafeCast.js.



/**
 * @dev Wrappers over Solidity's uintXX/intXX/bool casting operators with added overflow
 * checks.
 *
 * Downcasting from uint256/int256 in Solidity does not revert on overflow. This can
 * easily result in undesired exploitation or bugs, since developers usually
 * assume that overflows raise errors. `SafeCast` restores this intuition by
 * reverting the transaction when such an operation overflows.
 *
 * Using this library instead of the unchecked operations eliminates an entire
 * class of bugs, so it's recommended to use it always.
 */
library SafeCast {
    /**
     * @dev Value doesn't fit in a uint of `bits` size.
     */
    error SafeCastOverflowedUintDowncast(uint8 bits, uint256 value);

    /**
     * @dev An int value doesn't fit in a uint of `bits` size.
     */
    error SafeCastOverflowedIntToUint(int256 value);

    /**
     * @dev Value doesn't fit in an int of `bits` size.
     */
    error SafeCastOverflowedIntDowncast(uint8 bits, int256 value);

    /**
     * @dev A uint value doesn't fit in an int of `bits` size.
     */
    error SafeCastOverflowedUintToInt(uint256 value);

    /**
     * @dev Returns the downcasted uint248 from uint256, reverting on
     * overflow (when the input is greater than largest uint248).
     *
     * Counterpart to Solidity's `uint248` operator.
     *
     * Requirements:
     *
     * - input must fit into 248 bits
     */
    function toUint248(uint256 value) internal pure returns (uint248) {
        if (value > type(uint248).max) {
            revert SafeCastOverflowedUintDowncast(248, value);
        }
        return uint248(value);
    }

    /**
     * @dev Returns the downcasted uint240 from uint256, reverting on
     * overflow (when the input is greater than largest uint240).
     *
     * Counterpart to Solidity's `uint240` operator.
     *
     * Requirements:
     *
     * - input must fit into 240 bits
     */
    function toUint240(uint256 value) internal pure returns (uint240) {
        if (value > type(uint240).max) {
            revert SafeCastOverflowedUintDowncast(240, value);
        }
        return uint240(value);
    }

    /**
     * @dev Returns the downcasted uint232 from uint256, reverting on
     * overflow (when the input is greater than largest uint232).
     *
     * Counterpart to Solidity's `uint232` operator.
     *
     * Requirements:
     *
     * - input must fit into 232 bits
     */
    function toUint232(uint256 value) internal pure returns (uint232) {
        if (value > type(uint232).max) {
            revert SafeCastOverflowedUintDowncast(232, value);
        }
        return uint232(value);
    }

    /**
     * @dev Returns the downcasted uint224 from uint256, reverting on
     * overflow (when the input is greater than largest uint224).
     *
     * Counterpart to Solidity's `uint224` operator.
     *
     * Requirements:
     *
     * - input must fit into 224 bits
     */
    function toUint224(uint256 value) internal pure returns (uint224) {
        if (value > type(uint224).max) {
            revert SafeCastOverflowedUintDowncast(224, value);
        }
        return uint224(value);
    }

    /**
     * @dev Returns the downcasted uint216 from uint256, reverting on
     * overflow (when the input is greater than largest uint216).
     *
     * Counterpart to Solidity's `uint216` operator.
     *
     * Requirements:
     *
     * - input must fit into 216 bits
     */
    function toUint216(uint256 value) internal pure returns (uint216) {
        if (value > type(uint216).max) {
            revert SafeCastOverflowedUintDowncast(216, value);
        }
        return uint216(value);
    }

    /**
     * @dev Returns the downcasted uint208 from uint256, reverting on
     * overflow (when the input is greater than largest uint208).
     *
     * Counterpart to Solidity's `uint208` operator.
     *
     * Requirements:
     *
     * - input must fit into 208 bits
     */
    function toUint208(uint256 value) internal pure returns (uint208) {
        if (value > type(uint208).max) {
            revert SafeCastOverflowedUintDowncast(208, value);
        }
        return uint208(value);
    }

    /**
     * @dev Returns the downcasted uint200 from uint256, reverting on
     * overflow (when the input is greater than largest uint200).
     *
     * Counterpart to Solidity's `uint200` operator.
     *
     * Requirements:
     *
     * - input must fit into 200 bits
     */
    function toUint200(uint256 value) internal pure returns (uint200) {
        if (value > type(uint200).max) {
            revert SafeCastOverflowedUintDowncast(200, value);
        }
        return uint200(value);
    }

    /**
     * @dev Returns the downcasted uint192 from uint256, reverting on
     * overflow (when the input is greater than largest uint192).
     *
     * Counterpart to Solidity's `uint192` operator.
     *
     * Requirements:
     *
     * - input must fit into 192 bits
     */
    function toUint192(uint256 value) internal pure returns (uint192) {
        if (value > type(uint192).max) {
            revert SafeCastOverflowedUintDowncast(192, value);
        }
        return uint192(value);
    }

    /**
     * @dev Returns the downcasted uint184 from uint256, reverting on
     * overflow (when the input is greater than largest uint184).
     *
     * Counterpart to Solidity's `uint184` operator.
     *
     * Requirements:
     *
     * - input must fit into 184 bits
     */
    function toUint184(uint256 value) internal pure returns (uint184) {
        if (value > type(uint184).max) {
            revert SafeCastOverflowedUintDowncast(184, value);
        }
        return uint184(value);
    }

    /**
     * @dev Returns the downcasted uint176 from uint256, reverting on
     * overflow (when the input is greater than largest uint176).
     *
     * Counterpart to Solidity's `uint176` operator.
     *
     * Requirements:
     *
     * - input must fit into 176 bits
     */
    function toUint176(uint256 value) internal pure returns (uint176) {
        if (value > type(uint176).max) {
            revert SafeCastOverflowedUintDowncast(176, value);
        }
        return uint176(value);
    }

    /**
     * @dev Returns the downcasted uint168 from uint256, reverting on
     * overflow (when the input is greater than largest uint168).
     *
     * Counterpart to Solidity's `uint168` operator.
     *
     * Requirements:
     *
     * - input must fit into 168 bits
     */
    function toUint168(uint256 value) internal pure returns (uint168) {
        if (value > type(uint168).max) {
            revert SafeCastOverflowedUintDowncast(168, value);
        }
        return uint168(value);
    }

    /**
     * @dev Returns the downcasted uint160 from uint256, reverting on
     * overflow (when the input is greater than largest uint160).
     *
     * Counterpart to Solidity's `uint160` operator.
     *
     * Requirements:
     *
     * - input must fit into 160 bits
     */
    function toUint160(uint256 value) internal pure returns (uint160) {
        if (value > type(uint160).max) {
            revert SafeCastOverflowedUintDowncast(160, value);
        }
        return uint160(value);
    }

    /**
     * @dev Returns the downcasted uint152 from uint256, reverting on
     * overflow (when the input is greater than largest uint152).
     *
     * Counterpart to Solidity's `uint152` operator.
     *
     * Requirements:
     *
     * - input must fit into 152 bits
     */
    function toUint152(uint256 value) internal pure returns (uint152) {
        if (value > type(uint152).max) {
            revert SafeCastOverflowedUintDowncast(152, value);
        }
        return uint152(value);
    }

    /**
     * @dev Returns the downcasted uint144 from uint256, reverting on
     * overflow (when the input is greater than largest uint144).
     *
     * Counterpart to Solidity's `uint144` operator.
     *
     * Requirements:
     *
     * - input must fit into 144 bits
     */
    function toUint144(uint256 value) internal pure returns (uint144) {
        if (value > type(uint144).max) {
            revert SafeCastOverflowedUintDowncast(144, value);
        }
        return uint144(value);
    }

    /**
     * @dev Returns the downcasted uint136 from uint256, reverting on
     * overflow (when the input is greater than largest uint136).
     *
     * Counterpart to Solidity's `uint136` operator.
     *
     * Requirements:
     *
     * - input must fit into 136 bits
     */
    function toUint136(uint256 value) internal pure returns (uint136) {
        if (value > type(uint136).max) {
            revert SafeCastOverflowedUintDowncast(136, value);
        }
        return uint136(value);
    }

    /**
     * @dev Returns the downcasted uint128 from uint256, reverting on
     * overflow (when the input is greater than largest uint128).
     *
     * Counterpart to Solidity's `uint128` operator.
     *
     * Requirements:
     *
     * - input must fit into 128 bits
     */
    function toUint128(uint256 value) internal pure returns (uint128) {
        if (value > type(uint128).max) {
            revert SafeCastOverflowedUintDowncast(128, value);
        }
        return uint128(value);
    }

    /**
     * @dev Returns the downcasted uint120 from uint256, reverting on
     * overflow (when the input is greater than largest uint120).
     *
     * Counterpart to Solidity's `uint120` operator.
     *
     * Requirements:
     *
     * - input must fit into 120 bits
     */
    function toUint120(uint256 value) internal pure returns (uint120) {
        if (value > type(uint120).max) {
            revert SafeCastOverflowedUintDowncast(120, value);
        }
        return uint120(value);
    }

    /**
     * @dev Returns the downcasted uint112 from uint256, reverting on
     * overflow (when the input is greater than largest uint112).
     *
     * Counterpart to Solidity's `uint112` operator.
     *
     * Requirements:
     *
     * - input must fit into 112 bits
     */
    function toUint112(uint256 value) internal pure returns (uint112) {
        if (value > type(uint112).max) {
            revert SafeCastOverflowedUintDowncast(112, value);
        }
        return uint112(value);
    }

    /**
     * @dev Returns the downcasted uint104 from uint256, reverting on
     * overflow (when the input is greater than largest uint104).
     *
     * Counterpart to Solidity's `uint104` operator.
     *
     * Requirements:
     *
     * - input must fit into 104 bits
     */
    function toUint104(uint256 value) internal pure returns (uint104) {
        if (value > type(uint104).max) {
            revert SafeCastOverflowedUintDowncast(104, value);
        }
        return uint104(value);
    }

    /**
     * @dev Returns the downcasted uint96 from uint256, reverting on
     * overflow (when the input is greater than largest uint96).
     *
     * Counterpart to Solidity's `uint96` operator.
     *
     * Requirements:
     *
     * - input must fit into 96 bits
     */
    function toUint96(uint256 value) internal pure returns (uint96) {
        if (value > type(uint96).max) {
            revert SafeCastOverflowedUintDowncast(96, value);
        }
        return uint96(value);
    }

    /**
     * @dev Returns the downcasted uint88 from uint256, reverting on
     * overflow (when the input is greater than largest uint88).
     *
     * Counterpart to Solidity's `uint88` operator.
     *
     * Requirements:
     *
     * - input must fit into 88 bits
     */
    function toUint88(uint256 value) internal pure returns (uint88) {
        if (value > type(uint88).max) {
            revert SafeCastOverflowedUintDowncast(88, value);
        }
        return uint88(value);
    }

    /**
     * @dev Returns the downcasted uint80 from uint256, reverting on
     * overflow (when the input is greater than largest uint80).
     *
     * Counterpart to Solidity's `uint80` operator.
     *
     * Requirements:
     *
     * - input must fit into 80 bits
     */
    function toUint80(uint256 value) internal pure returns (uint80) {
        if (value > type(uint80).max) {
            revert SafeCastOverflowedUintDowncast(80, value);
        }
        return uint80(value);
    }

    /**
     * @dev Returns the downcasted uint72 from uint256, reverting on
     * overflow (when the input is greater than largest uint72).
     *
     * Counterpart to Solidity's `uint72` operator.
     *
     * Requirements:
     *
     * - input must fit into 72 bits
     */
    function toUint72(uint256 value) internal pure returns (uint72) {
        if (value > type(uint72).max) {
            revert SafeCastOverflowedUintDowncast(72, value);
        }
        return uint72(value);
    }

    /**
     * @dev Returns the downcasted uint64 from uint256, reverting on
     * overflow (when the input is greater than largest uint64).
     *
     * Counterpart to Solidity's `uint64` operator.
     *
     * Requirements:
     *
     * - input must fit into 64 bits
     */
    function toUint64(uint256 value) internal pure returns (uint64) {
        if (value > type(uint64).max) {
            revert SafeCastOverflowedUintDowncast(64, value);
        }
        return uint64(value);
    }

    /**
     * @dev Returns the downcasted uint56 from uint256, reverting on
     * overflow (when the input is greater than largest uint56).
     *
     * Counterpart to Solidity's `uint56` operator.
     *
     * Requirements:
     *
     * - input must fit into 56 bits
     */
    function toUint56(uint256 value) internal pure returns (uint56) {
        if (value > type(uint56).max) {
            revert SafeCastOverflowedUintDowncast(56, value);
        }
        return uint56(value);
    }

    /**
     * @dev Returns the downcasted uint48 from uint256, reverting on
     * overflow (when the input is greater than largest uint48).
     *
     * Counterpart to Solidity's `uint48` operator.
     *
     * Requirements:
     *
     * - input must fit into 48 bits
     */
    function toUint48(uint256 value) internal pure returns (uint48) {
        if (value > type(uint48).max) {
            revert SafeCastOverflowedUintDowncast(48, value);
        }
        return uint48(value);
    }

    /**
     * @dev Returns the downcasted uint40 from uint256, reverting on
     * overflow (when the input is greater than largest uint40).
     *
     * Counterpart to Solidity's `uint40` operator.
     *
     * Requirements:
     *
     * - input must fit into 40 bits
     */
    function toUint40(uint256 value) internal pure returns (uint40) {
        if (value > type(uint40).max) {
            revert SafeCastOverflowedUintDowncast(40, value);
        }
        return uint40(value);
    }

    /**
     * @dev Returns the downcasted uint32 from uint256, reverting on
     * overflow (when the input is greater than largest uint32).
     *
     * Counterpart to Solidity's `uint32` operator.
     *
     * Requirements:
     *
     * - input must fit into 32 bits
     */
    function toUint32(uint256 value) internal pure returns (uint32) {
        if (value > type(uint32).max) {
            revert SafeCastOverflowedUintDowncast(32, value);
        }
        return uint32(value);
    }

    /**
     * @dev Returns the downcasted uint24 from uint256, reverting on
     * overflow (when the input is greater than largest uint24).
     *
     * Counterpart to Solidity's `uint24` operator.
     *
     * Requirements:
     *
     * - input must fit into 24 bits
     */
    function toUint24(uint256 value) internal pure returns (uint24) {
        if (value > type(uint24).max) {
            revert SafeCastOverflowedUintDowncast(24, value);
        }
        return uint24(value);
    }

    /**
     * @dev Returns the downcasted uint16 from uint256, reverting on
     * overflow (when the input is greater than largest uint16).
     *
     * Counterpart to Solidity's `uint16` operator.
     *
     * Requirements:
     *
     * - input must fit into 16 bits
     */
    function toUint16(uint256 value) internal pure returns (uint16) {
        if (value > type(uint16).max) {
            revert SafeCastOverflowedUintDowncast(16, value);
        }
        return uint16(value);
    }

    /**
     * @dev Returns the downcasted uint8 from uint256, reverting on
     * overflow (when the input is greater than largest uint8).
     *
     * Counterpart to Solidity's `uint8` operator.
     *
     * Requirements:
     *
     * - input must fit into 8 bits
     */
    function toUint8(uint256 value) internal pure returns (uint8) {
        if (value > type(uint8).max) {
            revert SafeCastOverflowedUintDowncast(8, value);
        }
        return uint8(value);
    }

    /**
     * @dev Converts a signed int256 into an unsigned uint256.
     *
     * Requirements:
     *
     * - input must be greater than or equal to 0.
     */
    function toUint256(int256 value) internal pure returns (uint256) {
        if (value < 0) {
            revert SafeCastOverflowedIntToUint(value);
        }
        return uint256(value);
    }

    /**
     * @dev Returns the downcasted int248 from int256, reverting on
     * overflow (when the input is less than smallest int248 or
     * greater than largest int248).
     *
     * Counterpart to Solidity's `int248` operator.
     *
     * Requirements:
     *
     * - input must fit into 248 bits
     */
    function toInt248(int256 value) internal pure returns (int248 downcasted) {
        downcasted = int248(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(248, value);
        }
    }

    /**
     * @dev Returns the downcasted int240 from int256, reverting on
     * overflow (when the input is less than smallest int240 or
     * greater than largest int240).
     *
     * Counterpart to Solidity's `int240` operator.
     *
     * Requirements:
     *
     * - input must fit into 240 bits
     */
    function toInt240(int256 value) internal pure returns (int240 downcasted) {
        downcasted = int240(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(240, value);
        }
    }

    /**
     * @dev Returns the downcasted int232 from int256, reverting on
     * overflow (when the input is less than smallest int232 or
     * greater than largest int232).
     *
     * Counterpart to Solidity's `int232` operator.
     *
     * Requirements:
     *
     * - input must fit into 232 bits
     */
    function toInt232(int256 value) internal pure returns (int232 downcasted) {
        downcasted = int232(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(232, value);
        }
    }

    /**
     * @dev Returns the downcasted int224 from int256, reverting on
     * overflow (when the input is less than smallest int224 or
     * greater than largest int224).
     *
     * Counterpart to Solidity's `int224` operator.
     *
     * Requirements:
     *
     * - input must fit into 224 bits
     */
    function toInt224(int256 value) internal pure returns (int224 downcasted) {
        downcasted = int224(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(224, value);
        }
    }

    /**
     * @dev Returns the downcasted int216 from int256, reverting on
     * overflow (when the input is less than smallest int216 or
     * greater than largest int216).
     *
     * Counterpart to Solidity's `int216` operator.
     *
     * Requirements:
     *
     * - input must fit into 216 bits
     */
    function toInt216(int256 value) internal pure returns (int216 downcasted) {
        downcasted = int216(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(216, value);
        }
    }

    /**
     * @dev Returns the downcasted int208 from int256, reverting on
     * overflow (when the input is less than smallest int208 or
     * greater than largest int208).
     *
     * Counterpart to Solidity's `int208` operator.
     *
     * Requirements:
     *
     * - input must fit into 208 bits
     */
    function toInt208(int256 value) internal pure returns (int208 downcasted) {
        downcasted = int208(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(208, value);
        }
    }

    /**
     * @dev Returns the downcasted int200 from int256, reverting on
     * overflow (when the input is less than smallest int200 or
     * greater than largest int200).
     *
     * Counterpart to Solidity's `int200` operator.
     *
     * Requirements:
     *
     * - input must fit into 200 bits
     */
    function toInt200(int256 value) internal pure returns (int200 downcasted) {
        downcasted = int200(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(200, value);
        }
    }

    /**
     * @dev Returns the downcasted int192 from int256, reverting on
     * overflow (when the input is less than smallest int192 or
     * greater than largest int192).
     *
     * Counterpart to Solidity's `int192` operator.
     *
     * Requirements:
     *
     * - input must fit into 192 bits
     */
    function toInt192(int256 value) internal pure returns (int192 downcasted) {
        downcasted = int192(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(192, value);
        }
    }

    /**
     * @dev Returns the downcasted int184 from int256, reverting on
     * overflow (when the input is less than smallest int184 or
     * greater than largest int184).
     *
     * Counterpart to Solidity's `int184` operator.
     *
     * Requirements:
     *
     * - input must fit into 184 bits
     */
    function toInt184(int256 value) internal pure returns (int184 downcasted) {
        downcasted = int184(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(184, value);
        }
    }

    /**
     * @dev Returns the downcasted int176 from int256, reverting on
     * overflow (when the input is less than smallest int176 or
     * greater than largest int176).
     *
     * Counterpart to Solidity's `int176` operator.
     *
     * Requirements:
     *
     * - input must fit into 176 bits
     */
    function toInt176(int256 value) internal pure returns (int176 downcasted) {
        downcasted = int176(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(176, value);
        }
    }

    /**
     * @dev Returns the downcasted int168 from int256, reverting on
     * overflow (when the input is less than smallest int168 or
     * greater than largest int168).
     *
     * Counterpart to Solidity's `int168` operator.
     *
     * Requirements:
     *
     * - input must fit into 168 bits
     */
    function toInt168(int256 value) internal pure returns (int168 downcasted) {
        downcasted = int168(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(168, value);
        }
    }

    /**
     * @dev Returns the downcasted int160 from int256, reverting on
     * overflow (when the input is less than smallest int160 or
     * greater than largest int160).
     *
     * Counterpart to Solidity's `int160` operator.
     *
     * Requirements:
     *
     * - input must fit into 160 bits
     */
    function toInt160(int256 value) internal pure returns (int160 downcasted) {
        downcasted = int160(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(160, value);
        }
    }

    /**
     * @dev Returns the downcasted int152 from int256, reverting on
     * overflow (when the input is less than smallest int152 or
     * greater than largest int152).
     *
     * Counterpart to Solidity's `int152` operator.
     *
     * Requirements:
     *
     * - input must fit into 152 bits
     */
    function toInt152(int256 value) internal pure returns (int152 downcasted) {
        downcasted = int152(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(152, value);
        }
    }

    /**
     * @dev Returns the downcasted int144 from int256, reverting on
     * overflow (when the input is less than smallest int144 or
     * greater than largest int144).
     *
     * Counterpart to Solidity's `int144` operator.
     *
     * Requirements:
     *
     * - input must fit into 144 bits
     */
    function toInt144(int256 value) internal pure returns (int144 downcasted) {
        downcasted = int144(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(144, value);
        }
    }

    /**
     * @dev Returns the downcasted int136 from int256, reverting on
     * overflow (when the input is less than smallest int136 or
     * greater than largest int136).
     *
     * Counterpart to Solidity's `int136` operator.
     *
     * Requirements:
     *
     * - input must fit into 136 bits
     */
    function toInt136(int256 value) internal pure returns (int136 downcasted) {
        downcasted = int136(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(136, value);
        }
    }

    /**
     * @dev Returns the downcasted int128 from int256, reverting on
     * overflow (when the input is less than smallest int128 or
     * greater than largest int128).
     *
     * Counterpart to Solidity's `int128` operator.
     *
     * Requirements:
     *
     * - input must fit into 128 bits
     */
    function toInt128(int256 value) internal pure returns (int128 downcasted) {
        downcasted = int128(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(128, value);
        }
    }

    /**
     * @dev Returns the downcasted int120 from int256, reverting on
     * overflow (when the input is less than smallest int120 or
     * greater than largest int120).
     *
     * Counterpart to Solidity's `int120` operator.
     *
     * Requirements:
     *
     * - input must fit into 120 bits
     */
    function toInt120(int256 value) internal pure returns (int120 downcasted) {
        downcasted = int120(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(120, value);
        }
    }

    /**
     * @dev Returns the downcasted int112 from int256, reverting on
     * overflow (when the input is less than smallest int112 or
     * greater than largest int112).
     *
     * Counterpart to Solidity's `int112` operator.
     *
     * Requirements:
     *
     * - input must fit into 112 bits
     */
    function toInt112(int256 value) internal pure returns (int112 downcasted) {
        downcasted = int112(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(112, value);
        }
    }

    /**
     * @dev Returns the downcasted int104 from int256, reverting on
     * overflow (when the input is less than smallest int104 or
     * greater than largest int104).
     *
     * Counterpart to Solidity's `int104` operator.
     *
     * Requirements:
     *
     * - input must fit into 104 bits
     */
    function toInt104(int256 value) internal pure returns (int104 downcasted) {
        downcasted = int104(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(104, value);
        }
    }

    /**
     * @dev Returns the downcasted int96 from int256, reverting on
     * overflow (when the input is less than smallest int96 or
     * greater than largest int96).
     *
     * Counterpart to Solidity's `int96` operator.
     *
     * Requirements:
     *
     * - input must fit into 96 bits
     */
    function toInt96(int256 value) internal pure returns (int96 downcasted) {
        downcasted = int96(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(96, value);
        }
    }

    /**
     * @dev Returns the downcasted int88 from int256, reverting on
     * overflow (when the input is less than smallest int88 or
     * greater than largest int88).
     *
     * Counterpart to Solidity's `int88` operator.
     *
     * Requirements:
     *
     * - input must fit into 88 bits
     */
    function toInt88(int256 value) internal pure returns (int88 downcasted) {
        downcasted = int88(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(88, value);
        }
    }

    /**
     * @dev Returns the downcasted int80 from int256, reverting on
     * overflow (when the input is less than smallest int80 or
     * greater than largest int80).
     *
     * Counterpart to Solidity's `int80` operator.
     *
     * Requirements:
     *
     * - input must fit into 80 bits
     */
    function toInt80(int256 value) internal pure returns (int80 downcasted) {
        downcasted = int80(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(80, value);
        }
    }

    /**
     * @dev Returns the downcasted int72 from int256, reverting on
     * overflow (when the input is less than smallest int72 or
     * greater than largest int72).
     *
     * Counterpart to Solidity's `int72` operator.
     *
     * Requirements:
     *
     * - input must fit into 72 bits
     */
    function toInt72(int256 value) internal pure returns (int72 downcasted) {
        downcasted = int72(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(72, value);
        }
    }

    /**
     * @dev Returns the downcasted int64 from int256, reverting on
     * overflow (when the input is less than smallest int64 or
     * greater than largest int64).
     *
     * Counterpart to Solidity's `int64` operator.
     *
     * Requirements:
     *
     * - input must fit into 64 bits
     */
    function toInt64(int256 value) internal pure returns (int64 downcasted) {
        downcasted = int64(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(64, value);
        }
    }

    /**
     * @dev Returns the downcasted int56 from int256, reverting on
     * overflow (when the input is less than smallest int56 or
     * greater than largest int56).
     *
     * Counterpart to Solidity's `int56` operator.
     *
     * Requirements:
     *
     * - input must fit into 56 bits
     */
    function toInt56(int256 value) internal pure returns (int56 downcasted) {
        downcasted = int56(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(56, value);
        }
    }

    /**
     * @dev Returns the downcasted int48 from int256, reverting on
     * overflow (when the input is less than smallest int48 or
     * greater than largest int48).
     *
     * Counterpart to Solidity's `int48` operator.
     *
     * Requirements:
     *
     * - input must fit into 48 bits
     */
    function toInt48(int256 value) internal pure returns (int48 downcasted) {
        downcasted = int48(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(48, value);
        }
    }

    /**
     * @dev Returns the downcasted int40 from int256, reverting on
     * overflow (when the input is less than smallest int40 or
     * greater than largest int40).
     *
     * Counterpart to Solidity's `int40` operator.
     *
     * Requirements:
     *
     * - input must fit into 40 bits
     */
    function toInt40(int256 value) internal pure returns (int40 downcasted) {
        downcasted = int40(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(40, value);
        }
    }

    /**
     * @dev Returns the downcasted int32 from int256, reverting on
     * overflow (when the input is less than smallest int32 or
     * greater than largest int32).
     *
     * Counterpart to Solidity's `int32` operator.
     *
     * Requirements:
     *
     * - input must fit into 32 bits
     */
    function toInt32(int256 value) internal pure returns (int32 downcasted) {
        downcasted = int32(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(32, value);
        }
    }

    /**
     * @dev Returns the downcasted int24 from int256, reverting on
     * overflow (when the input is less than smallest int24 or
     * greater than largest int24).
     *
     * Counterpart to Solidity's `int24` operator.
     *
     * Requirements:
     *
     * - input must fit into 24 bits
     */
    function toInt24(int256 value) internal pure returns (int24 downcasted) {
        downcasted = int24(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(24, value);
        }
    }

    /**
     * @dev Returns the downcasted int16 from int256, reverting on
     * overflow (when the input is less than smallest int16 or
     * greater than largest int16).
     *
     * Counterpart to Solidity's `int16` operator.
     *
     * Requirements:
     *
     * - input must fit into 16 bits
     */
    function toInt16(int256 value) internal pure returns (int16 downcasted) {
        downcasted = int16(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(16, value);
        }
    }

    /**
     * @dev Returns the downcasted int8 from int256, reverting on
     * overflow (when the input is less than smallest int8 or
     * greater than largest int8).
     *
     * Counterpart to Solidity's `int8` operator.
     *
     * Requirements:
     *
     * - input must fit into 8 bits
     */
    function toInt8(int256 value) internal pure returns (int8 downcasted) {
        downcasted = int8(value);
        if (downcasted != value) {
            revert SafeCastOverflowedIntDowncast(8, value);
        }
    }

    /**
     * @dev Converts an unsigned uint256 into a signed int256.
     *
     * Requirements:
     *
     * - input must be less than or equal to maxInt256.
     */
    function toInt256(uint256 value) internal pure returns (int256) {
        // Note: Unsafe cast below is okay because `type(int256).max` is guaranteed to be positive
        if (value > uint256(type(int256).max)) {
            revert SafeCastOverflowedUintToInt(value);
        }
        return int256(value);
    }

    /**
     * @dev Cast a boolean (false or true) to a uint256 (0 or 1) with no jump.
     */
    function toUint(bool b) internal pure returns (uint256 u) {
        assembly ("memory-safe") {
            u := iszero(iszero(b))
        }
    }
}


/**
 * @dev Standard math utilities missing in the Solidity language.
 */
library Math {
    enum Rounding {
        Floor, // Toward negative infinity
        Ceil, // Toward positive infinity
        Trunc, // Toward zero
        Expand // Away from zero
    }

    /**
     * @dev Return the 512-bit addition of two uint256.
     *
     * The result is stored in two 256 variables such that sum = high * 2²⁵⁶ + low.
     */
    function add512(uint256 a, uint256 b) internal pure returns (uint256 high, uint256 low) {
        assembly ("memory-safe") {
            low := add(a, b)
            high := lt(low, a)
        }
    }

    /**
     * @dev Return the 512-bit multiplication of two uint256.
     *
     * The result is stored in two 256 variables such that product = high * 2²⁵⁶ + low.
     */
    function mul512(uint256 a, uint256 b) internal pure returns (uint256 high, uint256 low) {
        // 512-bit multiply [high low] = x * y. Compute the product mod 2²⁵⁶ and mod 2²⁵⁶ - 1, then use
        // the Chinese Remainder Theorem to reconstruct the 512 bit result. The result is stored in two 256
        // variables such that product = high * 2²⁵⁶ + low.
        assembly ("memory-safe") {
            let mm := mulmod(a, b, not(0))
            low := mul(a, b)
            high := sub(sub(mm, low), lt(mm, low))
        }
    }

    /**
     * @dev Returns the addition of two unsigned integers, with a success flag (no overflow).
     */
    function tryAdd(uint256 a, uint256 b) internal pure returns (bool success, uint256 result) {
        unchecked {
            uint256 c = a + b;
            success = c >= a;
            result = c * SafeCast.toUint(success);
        }
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, with a success flag (no overflow).
     */
    function trySub(uint256 a, uint256 b) internal pure returns (bool success, uint256 result) {
        unchecked {
            uint256 c = a - b;
            success = c <= a;
            result = c * SafeCast.toUint(success);
        }
    }

    /**
     * @dev Returns the multiplication of two unsigned integers, with a success flag (no overflow).
     */
    function tryMul(uint256 a, uint256 b) internal pure returns (bool success, uint256 result) {
        unchecked {
            uint256 c = a * b;
            assembly ("memory-safe") {
                // Only true when the multiplication doesn't overflow
                // (c / a == b) || (a == 0)
                success := or(eq(div(c, a), b), iszero(a))
            }
            // equivalent to: success ? c : 0
            result = c * SafeCast.toUint(success);
        }
    }

    /**
     * @dev Returns the division of two unsigned integers, with a success flag (no division by zero).
     */
    function tryDiv(uint256 a, uint256 b) internal pure returns (bool success, uint256 result) {
        unchecked {
            success = b > 0;
            assembly ("memory-safe") {
                // The `DIV` opcode returns zero when the denominator is 0.
                result := div(a, b)
            }
        }
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers, with a success flag (no division by zero).
     */
    function tryMod(uint256 a, uint256 b) internal pure returns (bool success, uint256 result) {
        unchecked {
            success = b > 0;
            assembly ("memory-safe") {
                // The `MOD` opcode returns zero when the denominator is 0.
                result := mod(a, b)
            }
        }
    }

    /**
     * @dev Unsigned saturating addition, bounds to `2²⁵⁶ - 1` instead of overflowing.
     */
    function saturatingAdd(uint256 a, uint256 b) internal pure returns (uint256) {
        (bool success, uint256 result) = tryAdd(a, b);
        return ternary(success, result, type(uint256).max);
    }

    /**
     * @dev Unsigned saturating subtraction, bounds to zero instead of overflowing.
     */
    function saturatingSub(uint256 a, uint256 b) internal pure returns (uint256) {
        (, uint256 result) = trySub(a, b);
        return result;
    }

    /**
     * @dev Unsigned saturating multiplication, bounds to `2²⁵⁶ - 1` instead of overflowing.
     */
    function saturatingMul(uint256 a, uint256 b) internal pure returns (uint256) {
        (bool success, uint256 result) = tryMul(a, b);
        return ternary(success, result, type(uint256).max);
    }

    /**
     * @dev Branchless ternary evaluation for `condition ? a : b`. Gas costs are constant.
     *
     * IMPORTANT: This function may reduce bytecode size and consume less gas when used standalone.
     * However, the compiler may optimize Solidity ternary operations (i.e. `condition ? a : b`) to only compute
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
        unchecked {
            // (a + b) / 2 can overflow.
            return (a & b) + (a ^ b) / 2;
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

    /**
     * @dev Calculates floor(x * y / denominator) with full precision. Throws if result overflows a uint256 or
     * denominator == 0.
     *
     * Original credit to Remco Bloemen under MIT license (https://xn--2-umb.com/21/muldiv) with further edits by
     * Uniswap Labs also under MIT license.
     */
    function mulDiv(uint256 x, uint256 y, uint256 denominator) internal pure returns (uint256 result) {
        unchecked {
            (uint256 high, uint256 low) = mul512(x, y);

            // Handle non-overflow cases, 256 by 256 division.
            if (high == 0) {
                // Solidity will revert if denominator == 0, unlike the div opcode on its own.
                // The surrounding unchecked block does not change this fact.
                // See https://docs.soliditylang.org/en/latest/control-structures.html#checked-or-unchecked-arithmetic.
                return low / denominator;
            }

            // Make sure the result is less than 2²⁵⁶. Also prevents denominator == 0.
            if (denominator <= high) {
                Panic.panic(ternary(denominator == 0, Panic.DIVISION_BY_ZERO, Panic.UNDER_OVERFLOW));
            }

            ///////////////////////////////////////////////
            // 512 by 256 division.
            ///////////////////////////////////////////////

            // Make division exact by subtracting the remainder from [high low].
            uint256 remainder;
            assembly ("memory-safe") {
                // Compute remainder using mulmod.
                remainder := mulmod(x, y, denominator)

                // Subtract 256 bit number from 512 bit number.
                high := sub(high, gt(remainder, low))
                low := sub(low, remainder)
            }

            // Factor powers of two out of denominator and compute largest power of two divisor of denominator.
            // Always >= 1. See https://cs.stackexchange.com/q/138556/92363.

            uint256 twos = denominator & (0 - denominator);
            assembly ("memory-safe") {
                // Divide denominator by twos.
                denominator := div(denominator, twos)

                // Divide [high low] by twos.
                low := div(low, twos)

                // Flip twos such that it is 2²⁵⁶ / twos. If twos is zero, then it becomes one.
                twos := add(div(sub(0, twos), twos), 1)
            }

            // Shift in bits from high into low.
            low |= high * twos;

            // Invert denominator mod 2²⁵⁶. Now that denominator is an odd number, it has an inverse modulo 2²⁵⁶ such
            // that denominator * inv ≡ 1 mod 2²⁵⁶. Compute the inverse by starting with a seed that is correct for
            // four bits. That is, denominator * inv ≡ 1 mod 2⁴.
            uint256 inverse = (3 * denominator) ^ 2;

            // Use the Newton-Raphson iteration to improve the precision. Thanks to Hensel's lifting lemma, this also
            // works in modular arithmetic, doubling the correct bits in each step.
            inverse *= 2 - denominator * inverse; // inverse mod 2⁸
            inverse *= 2 - denominator * inverse; // inverse mod 2¹⁶
            inverse *= 2 - denominator * inverse; // inverse mod 2³²
            inverse *= 2 - denominator * inverse; // inverse mod 2⁶⁴
            inverse *= 2 - denominator * inverse; // inverse mod 2¹²⁸
            inverse *= 2 - denominator * inverse; // inverse mod 2²⁵⁶

            // Because the division is now exact we can divide by multiplying with the modular inverse of denominator.
            // This will give us the correct result modulo 2²⁵⁶. Since the preconditions guarantee that the outcome is
            // less than 2²⁵⁶, this is the final result. We don't need to compute the high bits of the result and high
            // is no longer required.
            result = low * inverse;
            return result;
        }
    }

    /**
     * @dev Calculates x * y / denominator with full precision, following the selected rounding direction.
     */
    function mulDiv(uint256 x, uint256 y, uint256 denominator, Rounding rounding) internal pure returns (uint256) {
        return mulDiv(x, y, denominator) + SafeCast.toUint(unsignedRoundsUp(rounding) && mulmod(x, y, denominator) > 0);
    }

    /**
     * @dev Calculates floor(x * y >> n) with full precision. Throws if result overflows a uint256.
     */
    function mulShr(uint256 x, uint256 y, uint8 n) internal pure returns (uint256 result) {
        unchecked {
            (uint256 high, uint256 low) = mul512(x, y);
            if (high >= 1 << n) {
                Panic.panic(Panic.UNDER_OVERFLOW);
            }
            return (high << (256 - n)) | (low >> n);
        }
    }

    /**
     * @dev Calculates x * y >> n with full precision, following the selected rounding direction.
     */
    function mulShr(uint256 x, uint256 y, uint8 n, Rounding rounding) internal pure returns (uint256) {
        return mulShr(x, y, n) + SafeCast.toUint(unsignedRoundsUp(rounding) && mulmod(x, y, 1 << n) > 0);
    }

    /**
     * @dev Calculate the modular multiplicative inverse of a number in Z/nZ.
     *
     * If n is a prime, then Z/nZ is a field. In that case all elements are inversible, except 0.
     * If n is not a prime, then Z/nZ is not a field, and some elements might not be inversible.
     *
     * If the input value is not inversible, 0 is returned.
     *
     * NOTE: If you know for sure that n is (big) a prime, it may be cheaper to use Fermat's little theorem and get the
     * inverse using `Math.modExp(a, n - 2, n)`. See {invModPrime}.
     */
    function invMod(uint256 a, uint256 n) internal pure returns (uint256) {
        unchecked {
            if (n == 0) return 0;

            // The inverse modulo is calculated using the Extended Euclidean Algorithm (iterative version)
            // Used to compute integers x and y such that: ax + ny = gcd(a, n).
            // When the gcd is 1, then the inverse of a modulo n exists and it's x.
            // ax + ny = 1
            // ax = 1 + (-y)n
            // ax ≡ 1 (mod n) # x is the inverse of a modulo n

            // If the remainder is 0 the gcd is n right away.
            uint256 remainder = a % n;
            uint256 gcd = n;

            // Therefore the initial coefficients are:
            // ax + ny = gcd(a, n) = n
            // 0a + 1n = n
            int256 x = 0;
            int256 y = 1;

            while (remainder != 0) {
                uint256 quotient = gcd / remainder;

                (gcd, remainder) = (
                    // The old remainder is the next gcd to try.
                    remainder,
                    // Compute the next remainder.
                    // Can't overflow given that (a % gcd) * (gcd // (a % gcd)) <= gcd
                    // where gcd is at most n (capped to type(uint256).max)
                    gcd - remainder * quotient
                );

                (x, y) = (
                    // Increment the coefficient of a.
                    y,
                    // Decrement the coefficient of n.
                    // Can overflow, but the result is casted to uint256 so that the
                    // next value of y is "wrapped around" to a value between 0 and n - 1.
                    x - y * int256(quotient)
                );
            }

            if (gcd != 1) return 0; // No inverse exists.
            return ternary(x < 0, n - uint256(-x), uint256(x)); // Wrap the result if it's negative.
        }
    }

    /**
     * @dev Variant of {invMod}. More efficient, but only works if `p` is known to be a prime greater than `2`.
     *
     * From https://en.wikipedia.org/wiki/Fermat%27s_little_theorem[Fermat's little theorem], we know that if p is
     * prime, then `a**(p-1) ≡ 1 mod p`. As a consequence, we have `a * a**(p-2) ≡ 1 mod p`, which means that
     * `a**(p-2)` is the modular multiplicative inverse of a in Fp.
     *
     * NOTE: this function does NOT check that `p` is a prime greater than `2`.
     */
    function invModPrime(uint256 a, uint256 p) internal view returns (uint256) {
        unchecked {
            return Math.modExp(a, p - 2, p);
        }
    }

    /**
     * @dev Returns the modular exponentiation of the specified base, exponent and modulus (b ** e % m)
     *
     * Requirements:
     * - modulus can't be zero
     * - underlying staticcall to precompile must succeed
     *
     * IMPORTANT: The result is only valid if the underlying call succeeds. When using this function, make
     * sure the chain you're using it on supports the precompiled contract for modular exponentiation
     * at address 0x05 as specified in https://eips.ethereum.org/EIPS/eip-198[EIP-198]. Otherwise,
     * the underlying function will succeed given the lack of a revert, but the result may be incorrectly
     * interpreted as 0.
     */
    function modExp(uint256 b, uint256 e, uint256 m) internal view returns (uint256) {
        (bool success, uint256 result) = tryModExp(b, e, m);
        if (!success) {
            Panic.panic(Panic.DIVISION_BY_ZERO);
        }
        return result;
    }

    /**
     * @dev Returns the modular exponentiation of the specified base, exponent and modulus (b ** e % m).
     * It includes a success flag indicating if the operation succeeded. Operation will be marked as failed if trying
     * to operate modulo 0 or if the underlying precompile reverted.
     *
     * IMPORTANT: The result is only valid if the success flag is true. When using this function, make sure the chain
     * you're using it on supports the precompiled contract for modular exponentiation at address 0x05 as specified in
     * https://eips.ethereum.org/EIPS/eip-198[EIP-198]. Otherwise, the underlying function will succeed given the lack
     * of a revert, but the result may be incorrectly interpreted as 0.
     */
    function tryModExp(uint256 b, uint256 e, uint256 m) internal view returns (bool success, uint256 result) {
        if (m == 0) return (false, 0);
        assembly ("memory-safe") {
            let ptr := mload(0x40)
            // | Offset    | Content    | Content (Hex)                                                      |
            // |-----------|------------|--------------------------------------------------------------------|
            // | 0x00:0x1f | size of b  | 0x0000000000000000000000000000000000000000000000000000000000000020 |
            // | 0x20:0x3f | size of e  | 0x0000000000000000000000000000000000000000000000000000000000000020 |
            // | 0x40:0x5f | size of m  | 0x0000000000000000000000000000000000000000000000000000000000000020 |
            // | 0x60:0x7f | value of b | 0x<.............................................................b> |
            // | 0x80:0x9f | value of e | 0x<.............................................................e> |
            // | 0xa0:0xbf | value of m | 0x<.............................................................m> |
            mstore(ptr, 0x20)
            mstore(add(ptr, 0x20), 0x20)
            mstore(add(ptr, 0x40), 0x20)
            mstore(add(ptr, 0x60), b)
            mstore(add(ptr, 0x80), e)
            mstore(add(ptr, 0xa0), m)

            // Given the result < m, it's guaranteed to fit in 32 bytes,
            // so we can use the memory scratch space located at offset 0.
            success := staticcall(gas(), 0x05, ptr, 0xc0, 0x00, 0x20)
            result := mload(0x00)
        }
    }

    /**
     * @dev Variant of {modExp} that supports inputs of arbitrary length.
     */
    function modExp(bytes memory b, bytes memory e, bytes memory m) internal view returns (bytes memory) {
        (bool success, bytes memory result) = tryModExp(b, e, m);
        if (!success) {
            Panic.panic(Panic.DIVISION_BY_ZERO);
        }
        return result;
    }

    /**
     * @dev Variant of {tryModExp} that supports inputs of arbitrary length.
     */
    function tryModExp(
        bytes memory b,
        bytes memory e,
        bytes memory m
    ) internal view returns (bool success, bytes memory result) {
        if (_zeroBytes(m)) return (false, new bytes(0));

        uint256 mLen = m.length;

        // Encode call args in result and move the free memory pointer
        result = abi.encodePacked(b.length, e.length, mLen, b, e, m);

        assembly ("memory-safe") {
            let dataPtr := add(result, 0x20)
            // Write result on top of args to avoid allocating extra memory.
            success := staticcall(gas(), 0x05, dataPtr, mload(result), dataPtr, mLen)
            // Overwrite the length.
            // result.length > returndatasize() is guaranteed because returndatasize() == m.length
            mstore(result, mLen)
            // Set the memory pointer after the returned data.
            mstore(0x40, add(dataPtr, mLen))
        }
    }

    /**
     * @dev Returns whether the provided byte array is zero.
     */
    function _zeroBytes(bytes memory buffer) private pure returns (bool) {
        uint256 chunk;
        for (uint256 i = 0; i < buffer.length; i += 0x20) {
            // See _unsafeReadBytesOffset from utils/Bytes.sol
            assembly ("memory-safe") {
                chunk := mload(add(add(buffer, 0x20), i))
            }
            if (chunk >> (8 * saturatingSub(i + 0x20, buffer.length)) != 0) {
                return false;
            }
        }
        return true;
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
     * @dev Calculates sqrt(a), following the selected rounding direction.
     */
    function sqrt(uint256 a, Rounding rounding) internal pure returns (uint256) {
        unchecked {
            uint256 result = sqrt(a);
            return result + SafeCast.toUint(unsignedRoundsUp(rounding) && result * result < a);
        }
    }

    /**
     * @dev Return the log in base 2 of a positive value rounded towards zero.
     * Returns 0 if given 0.
     */
    function log2(uint256 x) internal pure returns (uint256 r) {
        // If value has upper 128 bits set, log2 result is at least 128
        r = SafeCast.toUint(x > 0xffffffffffffffffffffffffffffffff) << 7;
        // If upper 64 bits of 128-bit half set, add 64 to result
        r |= SafeCast.toUint((x >> r) > 0xffffffffffffffff) << 6;
        // If upper 32 bits of 64-bit half set, add 32 to result
        r |= SafeCast.toUint((x >> r) > 0xffffffff) << 5;
        // If upper 16 bits of 32-bit half set, add 16 to result
        r |= SafeCast.toUint((x >> r) > 0xffff) << 4;
        // If upper 8 bits of 16-bit half set, add 8 to result
        r |= SafeCast.toUint((x >> r) > 0xff) << 3;
        // If upper 4 bits of 8-bit half set, add 4 to result
        r |= SafeCast.toUint((x >> r) > 0xf) << 2;

        // Shifts value right by the current result and use it as an index into this lookup table:
        //
        // | x (4 bits) |  index  | table[index] = MSB position |
        // |------------|---------|-----------------------------|
        // |    0000    |    0    |        table[0] = 0         |
        // |    0001    |    1    |        table[1] = 0         |
        // |    0010    |    2    |        table[2] = 1         |
        // |    0011    |    3    |        table[3] = 1         |
        // |    0100    |    4    |        table[4] = 2         |
        // |    0101    |    5    |        table[5] = 2         |
        // |    0110    |    6    |        table[6] = 2         |
        // |    0111    |    7    |        table[7] = 2         |
        // |    1000    |    8    |        table[8] = 3         |
        // |    1001    |    9    |        table[9] = 3         |
        // |    1010    |   10    |        table[10] = 3        |
        // |    1011    |   11    |        table[11] = 3        |
        // |    1100    |   12    |        table[12] = 3        |
        // |    1101    |   13    |        table[13] = 3        |
        // |    1110    |   14    |        table[14] = 3        |
        // |    1111    |   15    |        table[15] = 3        |
        //
        // The lookup table is represented as a 32-byte value with the MSB positions for 0-15 in the first 16 bytes (most significant half).
        assembly ("memory-safe") {
            r := or(r, byte(shr(r, x), 0x0000010102020202030303030303030300000000000000000000000000000000))
        }
    }

    /**
     * @dev Return the log in base 2, following the selected rounding direction, of a positive value.
     * Returns 0 if given 0.
     */
    function log2(uint256 value, Rounding rounding) internal pure returns (uint256) {
        unchecked {
            uint256 result = log2(value);
            return result + SafeCast.toUint(unsignedRoundsUp(rounding) && 1 << result < value);
        }
    }

    /**
     * @dev Return the log in base 10 of a positive value rounded towards zero.
     * Returns 0 if given 0.
     */
    function log10(uint256 value) internal pure returns (uint256) {
        uint256 result = 0;
        unchecked {
            if (value >= 10 ** 64) {
                value /= 10 ** 64;
                result += 64;
            }
            if (value >= 10 ** 32) {
                value /= 10 ** 32;
                result += 32;
            }
            if (value >= 10 ** 16) {
                value /= 10 ** 16;
                result += 16;
            }
            if (value >= 10 ** 8) {
                value /= 10 ** 8;
                result += 8;
            }
            if (value >= 10 ** 4) {
                value /= 10 ** 4;
                result += 4;
            }
            if (value >= 10 ** 2) {
                value /= 10 ** 2;
                result += 2;
            }
            if (value >= 10 ** 1) {
                result += 1;
            }
        }
        return result;
    }

    /**
     * @dev Return the log in base 10, following the selected rounding direction, of a positive value.
     * Returns 0 if given 0.
     */
    function log10(uint256 value, Rounding rounding) internal pure returns (uint256) {
        unchecked {
            uint256 result = log10(value);
            return result + SafeCast.toUint(unsignedRoundsUp(rounding) && 10 ** result < value);
        }
    }

    /**
     * @dev Return the log in base 256 of a positive value rounded towards zero.
     * Returns 0 if given 0.
     *
     * Adding one to the result gives the number of pairs of hex symbols needed to represent `value` as a hex string.
     */
    function log256(uint256 x) internal pure returns (uint256 r) {
        // If value has upper 128 bits set, log2 result is at least 128
        r = SafeCast.toUint(x > 0xffffffffffffffffffffffffffffffff) << 7;
        // If upper 64 bits of 128-bit half set, add 64 to result
        r |= SafeCast.toUint((x >> r) > 0xffffffffffffffff) << 6;
        // If upper 32 bits of 64-bit half set, add 32 to result
        r |= SafeCast.toUint((x >> r) > 0xffffffff) << 5;
        // If upper 16 bits of 32-bit half set, add 16 to result
        r |= SafeCast.toUint((x >> r) > 0xffff) << 4;
        // Add 1 if upper 8 bits of 16-bit half set, and divide accumulated result by 8
        return (r >> 3) | SafeCast.toUint((x >> r) > 0xff);
    }

    /**
     * @dev Return the log in base 256, following the selected rounding direction, of a positive value.
     * Returns 0 if given 0.
     */
    function log256(uint256 value, Rounding rounding) internal pure returns (uint256) {
        unchecked {
            uint256 result = log256(value);
            return result + SafeCast.toUint(unsignedRoundsUp(rounding) && 1 << (result << 3) < value);
        }
    }

    /**
     * @dev Returns whether a provided rounding mode is considered rounding up for unsigned integers.
     */
    function unsignedRoundsUp(Rounding rounding) internal pure returns (bool) {
        return uint8(rounding) % 2 == 1;
    }

    /**
     * @dev Counts the number of leading zero bits in a uint256.
     */
    function clz(uint256 x) internal pure returns (uint256) {
        return ternary(x == 0, 256, 255 - log2(x));
    }
}

// Failed to resolve import: import "@openzeppelin/contracts/math/SafeMath.sol";

// OpenZeppelin Contracts (last updated v5.5.0) (token/ERC20/utils/SafeERC20.sol)





// OpenZeppelin Contracts (last updated v5.4.0) (interfaces/IERC1363.sol)




// OpenZeppelin Contracts (last updated v5.4.0) (interfaces/IERC20.sol)






// OpenZeppelin Contracts (last updated v5.4.0) (interfaces/IERC165.sol)




// OpenZeppelin Contracts (last updated v5.4.0) (utils/introspection/IERC165.sol)



/**
 * @dev Interface of the ERC-165 standard, as defined in the
 * https://eips.ethereum.org/EIPS/eip-165[ERC].
 *
 * Implementers can declare support of contract interfaces, which can then be
 * queried by others ({ERC165Checker}).
 *
 * For an implementation, see {ERC165}.
 */
interface IERC165 {
    /**
     * @dev Returns true if this contract implements the interface defined by
     * `interfaceId`. See the corresponding
     * https://eips.ethereum.org/EIPS/eip-165#how-interfaces-are-identified[ERC section]
     * to learn more about how these ids are created.
     *
     * This function call must use less than 30 000 gas.
     */
    function supportsInterface(bytes4 interfaceId) external view returns (bool);
}



/**
 * @title IERC1363
 * @dev Interface of the ERC-1363 standard as defined in the https://eips.ethereum.org/EIPS/eip-1363[ERC-1363].
 *
 * Defines an extension interface for ERC-20 tokens that supports executing code on a recipient contract
 * after `transfer` or `transferFrom`, or code on a spender contract after `approve`, in a single transaction.
 */
interface IERC1363 is IERC20, IERC165 {
    /*
     * Note: the ERC-165 identifier for this interface is 0xb0202a11.
     * 0xb0202a11 ===
     *   bytes4(keccak256('transferAndCall(address,uint256)')) ^
     *   bytes4(keccak256('transferAndCall(address,uint256,bytes)')) ^
     *   bytes4(keccak256('transferFromAndCall(address,address,uint256)')) ^
     *   bytes4(keccak256('transferFromAndCall(address,address,uint256,bytes)')) ^
     *   bytes4(keccak256('approveAndCall(address,uint256)')) ^
     *   bytes4(keccak256('approveAndCall(address,uint256,bytes)'))
     */

    /**
     * @dev Moves a `value` amount of tokens from the caller's account to `to`
     * and then calls {IERC1363Receiver-onTransferReceived} on `to`.
     * @param to The address which you want to transfer to.
     * @param value The amount of tokens to be transferred.
     * @return A boolean value indicating whether the operation succeeded unless throwing.
     */
    function transferAndCall(address to, uint256 value) external returns (bool);

    /**
     * @dev Moves a `value` amount of tokens from the caller's account to `to`
     * and then calls {IERC1363Receiver-onTransferReceived} on `to`.
     * @param to The address which you want to transfer to.
     * @param value The amount of tokens to be transferred.
     * @param data Additional data with no specified format, sent in call to `to`.
     * @return A boolean value indicating whether the operation succeeded unless throwing.
     */
    function transferAndCall(address to, uint256 value, bytes calldata data) external returns (bool);

    /**
     * @dev Moves a `value` amount of tokens from `from` to `to` using the allowance mechanism
     * and then calls {IERC1363Receiver-onTransferReceived} on `to`.
     * @param from The address which you want to send tokens from.
     * @param to The address which you want to transfer to.
     * @param value The amount of tokens to be transferred.
     * @return A boolean value indicating whether the operation succeeded unless throwing.
     */
    function transferFromAndCall(address from, address to, uint256 value) external returns (bool);

    /**
     * @dev Moves a `value` amount of tokens from `from` to `to` using the allowance mechanism
     * and then calls {IERC1363Receiver-onTransferReceived} on `to`.
     * @param from The address which you want to send tokens from.
     * @param to The address which you want to transfer to.
     * @param value The amount of tokens to be transferred.
     * @param data Additional data with no specified format, sent in call to `to`.
     * @return A boolean value indicating whether the operation succeeded unless throwing.
     */
    function transferFromAndCall(address from, address to, uint256 value, bytes calldata data) external returns (bool);

    /**
     * @dev Sets a `value` amount of tokens as the allowance of `spender` over the
     * caller's tokens and then calls {IERC1363Spender-onApprovalReceived} on `spender`.
     * @param spender The address which will spend the funds.
     * @param value The amount of tokens to be spent.
     * @return A boolean value indicating whether the operation succeeded unless throwing.
     */
    function approveAndCall(address spender, uint256 value) external returns (bool);

    /**
     * @dev Sets a `value` amount of tokens as the allowance of `spender` over the
     * caller's tokens and then calls {IERC1363Spender-onApprovalReceived} on `spender`.
     * @param spender The address which will spend the funds.
     * @param value The amount of tokens to be spent.
     * @param data Additional data with no specified format, sent in call to `spender`.
     * @return A boolean value indicating whether the operation succeeded unless throwing.
     */
    function approveAndCall(address spender, uint256 value, bytes calldata data) external returns (bool);
}


// OpenZeppelin Contracts (last updated v5.4.0) (interfaces/IERC20Metadata.sol)




// OpenZeppelin Contracts (last updated v5.4.0) (token/ERC20/extensions/IERC20Metadata.sol)





/**
 * @dev Interface for the optional metadata functions from the ERC-20 standard.
 */
interface IERC20Metadata is IERC20 {
    /**
     * @dev Returns the name of the token.
     */
    function name() external view returns (string memory);

    /**
     * @dev Returns the symbol of the token.
     */
    function symbol() external view returns (string memory);

    /**
     * @dev Returns the decimals places of the token.
     */
    function decimals() external view returns (uint8);
}



/**
 * @title SafeERC20
 * @dev Wrappers around ERC-20 operations that throw on failure (when the token
 * contract returns false). Tokens that return no value (and instead revert or
 * throw on failure) are also supported, non-reverting calls are assumed to be
 * successful.
 * To use this library you can add a `using SafeERC20 for IERC20;` statement to your contract,
 * which allows you to call the safe operations as `token.safeTransfer(...)`, etc.
 */
library SafeERC20 {
    /**
     * @dev An operation with an ERC-20 token failed.
     */
    error SafeERC20FailedOperation(address token);

    /**
     * @dev Indicates a failed `decreaseAllowance` request.
     */
    error SafeERC20FailedDecreaseAllowance(address spender, uint256 currentAllowance, uint256 requestedDecrease);

    /**
     * @dev Transfer `value` amount of `token` from the calling contract to `to`. If `token` returns no value,
     * non-reverting calls are assumed to be successful.
     */
    function safeTransfer(IERC20 token, address to, uint256 value) internal {
        if (!_safeTransfer(token, to, value, true)) {
            revert SafeERC20FailedOperation(address(token));
        }
    }

    /**
     * @dev Transfer `value` amount of `token` from `from` to `to`, spending the approval given by `from` to the
     * calling contract. If `token` returns no value, non-reverting calls are assumed to be successful.
     */
    function safeTransferFrom(IERC20 token, address from, address to, uint256 value) internal {
        if (!_safeTransferFrom(token, from, to, value, true)) {
            revert SafeERC20FailedOperation(address(token));
        }
    }

    /**
     * @dev Variant of {safeTransfer} that returns a bool instead of reverting if the operation is not successful.
     */
    function trySafeTransfer(IERC20 token, address to, uint256 value) internal returns (bool) {
        return _safeTransfer(token, to, value, false);
    }

    /**
     * @dev Variant of {safeTransferFrom} that returns a bool instead of reverting if the operation is not successful.
     */
    function trySafeTransferFrom(IERC20 token, address from, address to, uint256 value) internal returns (bool) {
        return _safeTransferFrom(token, from, to, value, false);
    }

    /**
     * @dev Increase the calling contract's allowance toward `spender` by `value`. If `token` returns no value,
     * non-reverting calls are assumed to be successful.
     *
     * IMPORTANT: If the token implements ERC-7674 (ERC-20 with temporary allowance), and if the "client"
     * smart contract uses ERC-7674 to set temporary allowances, then the "client" smart contract should avoid using
     * this function. Performing a {safeIncreaseAllowance} or {safeDecreaseAllowance} operation on a token contract
     * that has a non-zero temporary allowance (for that particular owner-spender) will result in unexpected behavior.
     */
    function safeIncreaseAllowance(IERC20 token, address spender, uint256 value) internal {
        uint256 oldAllowance = token.allowance(address(this), spender);
        forceApprove(token, spender, oldAllowance + value);
    }

    /**
     * @dev Decrease the calling contract's allowance toward `spender` by `requestedDecrease`. If `token` returns no
     * value, non-reverting calls are assumed to be successful.
     *
     * IMPORTANT: If the token implements ERC-7674 (ERC-20 with temporary allowance), and if the "client"
     * smart contract uses ERC-7674 to set temporary allowances, then the "client" smart contract should avoid using
     * this function. Performing a {safeIncreaseAllowance} or {safeDecreaseAllowance} operation on a token contract
     * that has a non-zero temporary allowance (for that particular owner-spender) will result in unexpected behavior.
     */
    function safeDecreaseAllowance(IERC20 token, address spender, uint256 requestedDecrease) internal {
        unchecked {
            uint256 currentAllowance = token.allowance(address(this), spender);
            if (currentAllowance < requestedDecrease) {
                revert SafeERC20FailedDecreaseAllowance(spender, currentAllowance, requestedDecrease);
            }
            forceApprove(token, spender, currentAllowance - requestedDecrease);
        }
    }

    /**
     * @dev Set the calling contract's allowance toward `spender` to `value`. If `token` returns no value,
     * non-reverting calls are assumed to be successful. Meant to be used with tokens that require the approval
     * to be set to zero before setting it to a non-zero value, such as USDT.
     *
     * NOTE: If the token implements ERC-7674, this function will not modify any temporary allowance. This function
     * only sets the "standard" allowance. Any temporary allowance will remain active, in addition to the value being
     * set here.
     */
    function forceApprove(IERC20 token, address spender, uint256 value) internal {
        if (!_safeApprove(token, spender, value, false)) {
            if (!_safeApprove(token, spender, 0, true)) revert SafeERC20FailedOperation(address(token));
            if (!_safeApprove(token, spender, value, true)) revert SafeERC20FailedOperation(address(token));
        }
    }

    /**
     * @dev Performs an {ERC1363} transferAndCall, with a fallback to the simple {ERC20} transfer if the target has no
     * code. This can be used to implement an {ERC721}-like safe transfer that relies on {ERC1363} checks when
     * targeting contracts.
     *
     * Reverts if the returned value is other than `true`.
     */
    function transferAndCallRelaxed(IERC1363 token, address to, uint256 value, bytes memory data) internal {
        if (to.code.length == 0) {
            safeTransfer(token, to, value);
        } else if (!token.transferAndCall(to, value, data)) {
            revert SafeERC20FailedOperation(address(token));
        }
    }

    /**
     * @dev Performs an {ERC1363} transferFromAndCall, with a fallback to the simple {ERC20} transferFrom if the target
     * has no code. This can be used to implement an {ERC721}-like safe transfer that relies on {ERC1363} checks when
     * targeting contracts.
     *
     * Reverts if the returned value is other than `true`.
     */
    function transferFromAndCallRelaxed(
        IERC1363 token,
        address from,
        address to,
        uint256 value,
        bytes memory data
    ) internal {
        if (to.code.length == 0) {
            safeTransferFrom(token, from, to, value);
        } else if (!token.transferFromAndCall(from, to, value, data)) {
            revert SafeERC20FailedOperation(address(token));
        }
    }

    /**
     * @dev Performs an {ERC1363} approveAndCall, with a fallback to the simple {ERC20} approve if the target has no
     * code. This can be used to implement an {ERC721}-like safe transfer that rely on {ERC1363} checks when
     * targeting contracts.
     *
     * NOTE: When the recipient address (`to`) has no code (i.e. is an EOA), this function behaves as {forceApprove}.
     * Oppositely, when the recipient address (`to`) has code, this function only attempts to call {ERC1363-approveAndCall}
     * once without retrying, and relies on the returned value to be true.
     *
     * Reverts if the returned value is other than `true`.
     */
    function approveAndCallRelaxed(IERC1363 token, address to, uint256 value, bytes memory data) internal {
        if (to.code.length == 0) {
            forceApprove(token, to, value);
        } else if (!token.approveAndCall(to, value, data)) {
            revert SafeERC20FailedOperation(address(token));
        }
    }

    /// @dev Attempts to fetch the token decimals. A return value of false indicates that the attempt failed in some way.
    function tryGetDecimals(IERC20 token) internal view returns (bool success, uint8 decimals) {
        bytes4 selector = IERC20Metadata.decimals.selector;
        assembly ("memory-safe") {
            mstore(0x00, selector)
            success := staticcall(gas(), token, 0x00, 4, 0x00, 0x20)
            success := and(and(success, gt(returndatasize(), 0x1f)), lt(mload(0x00), 0x100))
            decimals := mul(success, mload(0x00))
        }
    }

    /**
     * @dev Imitates a Solidity `token.transfer(to, value)` call, relaxing the requirement on the return value: the
     * return value is optional (but if data is returned, it must not be false).
     *
     * @param token The token targeted by the call.
     * @param to The recipient of the tokens
     * @param value The amount of token to transfer
     * @param bubble Behavior switch if the transfer call reverts: bubble the revert reason or return a false boolean.
     */
    function _safeTransfer(IERC20 token, address to, uint256 value, bool bubble) private returns (bool success) {
        bytes4 selector = IERC20.transfer.selector;

        assembly ("memory-safe") {
            let fmp := mload(0x40)
            mstore(0x00, selector)
            mstore(0x04, and(to, shr(96, not(0))))
            mstore(0x24, value)
            success := call(gas(), token, 0, 0x00, 0x44, 0x00, 0x20)
            // if call success and return is true, all is good.
            // otherwise (not success or return is not true), we need to perform further checks
            if iszero(and(success, eq(mload(0x00), 1))) {
                // if the call was a failure and bubble is enabled, bubble the error
                if and(iszero(success), bubble) {
                    returndatacopy(fmp, 0x00, returndatasize())
                    revert(fmp, returndatasize())
                }
                // if the return value is not true, then the call is only successful if:
                // - the token address has code
                // - the returndata is empty
                success := and(success, and(iszero(returndatasize()), gt(extcodesize(token), 0)))
            }
            mstore(0x40, fmp)
        }
    }

    /**
     * @dev Imitates a Solidity `token.transferFrom(from, to, value)` call, relaxing the requirement on the return
     * value: the return value is optional (but if data is returned, it must not be false).
     *
     * @param token The token targeted by the call.
     * @param from The sender of the tokens
     * @param to The recipient of the tokens
     * @param value The amount of token to transfer
     * @param bubble Behavior switch if the transfer call reverts: bubble the revert reason or return a false boolean.
     */
    function _safeTransferFrom(
        IERC20 token,
        address from,
        address to,
        uint256 value,
        bool bubble
    ) private returns (bool success) {
        bytes4 selector = IERC20.transferFrom.selector;

        assembly ("memory-safe") {
            let fmp := mload(0x40)
            mstore(0x00, selector)
            mstore(0x04, and(from, shr(96, not(0))))
            mstore(0x24, and(to, shr(96, not(0))))
            mstore(0x44, value)
            success := call(gas(), token, 0, 0x00, 0x64, 0x00, 0x20)
            // if call success and return is true, all is good.
            // otherwise (not success or return is not true), we need to perform further checks
            if iszero(and(success, eq(mload(0x00), 1))) {
                // if the call was a failure and bubble is enabled, bubble the error
                if and(iszero(success), bubble) {
                    returndatacopy(fmp, 0x00, returndatasize())
                    revert(fmp, returndatasize())
                }
                // if the return value is not true, then the call is only successful if:
                // - the token address has code
                // - the returndata is empty
                success := and(success, and(iszero(returndatasize()), gt(extcodesize(token), 0)))
            }
            mstore(0x40, fmp)
            mstore(0x60, 0)
        }
    }

    /**
     * @dev Imitates a Solidity `token.approve(spender, value)` call, relaxing the requirement on the return value:
     * the return value is optional (but if data is returned, it must not be false).
     *
     * @param token The token targeted by the call.
     * @param spender The spender of the tokens
     * @param value The amount of token to transfer
     * @param bubble Behavior switch if the transfer call reverts: bubble the revert reason or return a false boolean.
     */
    function _safeApprove(IERC20 token, address spender, uint256 value, bool bubble) private returns (bool success) {
        bytes4 selector = IERC20.approve.selector;

        assembly ("memory-safe") {
            let fmp := mload(0x40)
            mstore(0x00, selector)
            mstore(0x04, and(spender, shr(96, not(0))))
            mstore(0x24, value)
            success := call(gas(), token, 0, 0x00, 0x44, 0x00, 0x20)
            // if call success and return is true, all is good.
            // otherwise (not success or return is not true), we need to perform further checks
            if iszero(and(success, eq(mload(0x00), 1))) {
                // if the call was a failure and bubble is enabled, bubble the error
                if and(iszero(success), bubble) {
                    returndatacopy(fmp, 0x00, returndatasize())
                    revert(fmp, returndatasize())
                }
                // if the return value is not true, then the call is only successful if:
                // - the token address has code
                // - the returndata is empty
                success := and(success, and(iszero(returndatasize()), gt(extcodesize(token), 0)))
            }
            mstore(0x40, fmp)
        }
    }
}





// Failed to resolve import: import "@openzeppelin/contracts/math/SafeMath.sol";

library SafeDecimalMath {
    using SafeMath for uint256;

    /* Number of decimal places in the representations. */
    uint256 private constant decimals = 18;
    uint256 private constant highPrecisionDecimals = 27;

    /* The number representing 1.0. */
    uint256 private constant UNIT = 10**uint256(decimals);

    /* The number representing 1.0 for higher fidelity numbers. */
    uint256 private constant PRECISE_UNIT = 10**uint256(highPrecisionDecimals);
    uint256 private constant UNIT_TO_HIGH_PRECISION_CONVERSION_FACTOR =
        10**uint256(highPrecisionDecimals - decimals);

    /**
     * @return The result of multiplying x and y, interpreting the operands as fixed-point
     * decimals.
     *
     * @dev A unit factor is divided out after the product of x and y is evaluated,
     * so that product must be less than 2**256. As this is an integer division,
     * the internal division always rounds down. This helps save on gas. Rounding
     * is more expensive on gas.
     */
    function multiplyDecimal(uint256 x, uint256 y) internal pure returns (uint256) {
        /* Divide by UNIT to remove the extra factor introduced by the product. */
        return x.mul(y).div(UNIT);
    }

    function multiplyDecimalPrecise(uint256 x, uint256 y) internal pure returns (uint256) {
        /* Divide by UNIT to remove the extra factor introduced by the product. */
        return x.mul(y).div(PRECISE_UNIT);
    }

    /**
     * @return The result of safely dividing x and y. The return value is a high
     * precision decimal.
     *
     * @dev y is divided after the product of x and the standard precision unit
     * is evaluated, so the product of x and UNIT must be less than 2**256. As
     * this is an integer division, the result is always rounded down.
     * This helps save on gas. Rounding is more expensive on gas.
     */
    function divideDecimal(uint256 x, uint256 y) internal pure returns (uint256) {
        /* Reintroduce the UNIT factor that will be divided out by y. */
        return x.mul(UNIT).div(y);
    }

    function divideDecimalPrecise(uint256 x, uint256 y) internal pure returns (uint256) {
        /* Reintroduce the UNIT factor that will be divided out by y. */
        return x.mul(PRECISE_UNIT).div(y);
    }

    /**
     * @dev Convert a standard decimal representation to a high precision one.
     */
    function decimalToPreciseDecimal(uint256 i) internal pure returns (uint256) {
        return i.mul(UNIT_TO_HIGH_PRECISION_CONVERSION_FACTOR);
    }

    /**
     * @dev Convert a high precision decimal to a standard decimal representation.
     */
    function preciseDecimalToDecimal(uint256 i) internal pure returns (uint256) {
        uint256 quotientTimesTen = i.mul(10).div(UNIT_TO_HIGH_PRECISION_CONVERSION_FACTOR);

        if (quotientTimesTen % 10 >= 5) {
            quotientTimesTen = quotientTimesTen.add(10);
        }

        return quotientTimesTen.div(10);
    }

    /**
     * @dev Returns the multiplication of two unsigned integers, and the max value of
     * uint256 on overflow.
     */
    function saturatingMul(uint256 a, uint256 b) internal pure returns (uint256) {
        if (a == 0) {
            return 0;
        }
        uint256 c = a * b;
        return c / a != b ? type(uint256).max : c;
    }

    function saturatingMultiplyDecimal(uint256 x, uint256 y) internal pure returns (uint256) {
        /* Divide by UNIT to remove the extra factor introduced by the product. */
        return saturatingMul(x, y).div(UNIT);
    }
}




// Failed to resolve import: import "@openzeppelin/contracts/math/SafeMath.sol";

abstract contract CoreUtility {
    using SafeMath for uint256;

    /// @dev UTC time of a day when the fund settles.
    uint256 internal constant SETTLEMENT_TIME = 14 hours;

    /// @dev Return end timestamp of the trading week containing a given timestamp.
    ///
    ///      A trading week starts at UTC time `SETTLEMENT_TIME` on a Thursday (inclusive)
    ///      and ends at the same time of the next Thursday (exclusive).
    /// @param timestamp The given timestamp
    /// @return End timestamp of the trading week.
    function _endOfWeek(uint256 timestamp) internal pure returns (uint256) {
        return ((timestamp.add(1 weeks) - SETTLEMENT_TIME) / 1 weeks) * 1 weeks + SETTLEMENT_TIME;
    }
}




/**
 * @dev Contract of an emergency stop mechanism that can be triggered by an authorized account.
 *
 * This module is modified based on Pausable in OpenZeppelin v3.3.0, adding public functions to
 * pause, unpause and manage the pauser role. It is also designed to be used by upgradable
 * contracts, like PausableUpgradable but with compact storage slots and no dependencies.
 */
abstract contract ManagedPausable {
    /**
     * @dev Emitted when the pause is triggered by `account`.
     */
    event Paused(address account);

    /**
     * @dev Emitted when the pause is lifted by `account`.
     */
    event Unpaused(address account);

    event PauserRoleTransferred(address indexed previousPauser, address indexed newPauser);

    uint256 private constant FALSE = 0;
    uint256 private constant TRUE = 1;

    uint256 private _initialized;

    uint256 private _paused;

    address private _pauser;

    function _initializeManagedPausable(address pauser_) internal {
        require(_initialized == FALSE);
        _initialized = TRUE;
        _paused = FALSE;
        _pauser = pauser_;
    }

    /**
     * @dev Returns true if the contract is paused, and false otherwise.
     */
    function paused() public view returns (bool) {
        return _paused != FALSE;
    }

    function pauser() public view returns (address) {
        return _pauser;
    }

    function renouncePauserRole() external onlyPauser {
        emit PauserRoleTransferred(_pauser, address(0));
        _pauser = address(0);
    }

    function transferPauserRole(address newPauser) external onlyPauser {
        require(newPauser != address(0));
        emit PauserRoleTransferred(_pauser, newPauser);
        _pauser = newPauser;
    }

    modifier onlyPauser() {
        require(_pauser == msg.sender, "Pausable: only pauser");
        _;
    }

    /**
     * @dev Modifier to make a function callable only when the contract is not paused.
     *
     * Requirements:
     *
     * - The contract must not be paused.
     */
    modifier whenNotPaused() {
        require(_paused == FALSE, "Pausable: paused");
        _;
    }

    /**
     * @dev Modifier to make a function callable only when the contract is paused.
     *
     * Requirements:
     *
     * - The contract must be paused.
     */
    modifier whenPaused() {
        require(_paused != FALSE, "Pausable: not paused");
        _;
    }

    /**
     * @dev Triggers stopped state.
     *
     * Requirements:
     *
     * - The contract must not be paused.
     */
    function pause() external onlyPauser whenNotPaused {
        _paused = TRUE;
        emit Paused(msg.sender);
    }

    /**
     * @dev Returns to normal state.
     *
     * Requirements:
     *
     * - The contract must be paused.
     */
    function unpause() external onlyPauser whenPaused {
        _paused = FALSE;
        emit Unpaused(msg.sender);
    }
}




pragma experimental ABIEncoderV2;




interface ITwapOracle {
    function getTwap(uint256 timestamp) external view returns (uint256);
}


interface IFund {
    /// @notice A linear transformation matrix that represents a rebalance.
    ///
    ///         ```
    ///             [ ratioM          0        0 ]
    ///         R = [ ratioA2M  ratioAB        0 ]
    ///             [ ratioB2M        0  ratioAB ]
    ///         ```
    ///
    ///         Amounts of the three tranches `m`, `a` and `b` can be rebalanced by multiplying the matrix:
    ///
    ///         ```
    ///         [ m', a', b' ] = [ m, a, b ] * R
    ///         ```
    struct Rebalance {
        uint256 ratioM;
        uint256 ratioA2M;
        uint256 ratioB2M;
        uint256 ratioAB;
        uint256 timestamp;
    }

    function trancheWeights() external pure returns (uint256 weightA, uint256 weightB);

    function tokenUnderlying() external view returns (address);

    function tokenM() external view returns (address);

    function tokenA() external view returns (address);

    function tokenB() external view returns (address);

    function underlyingDecimalMultiplier() external view returns (uint256);

    function twapOracle() external view returns (ITwapOracle);

    function feeCollector() external view returns (address);

    function endOfDay(uint256 timestamp) external pure returns (uint256);

    function shareTotalSupply(uint256 tranche) external view returns (uint256);

    function shareBalanceOf(uint256 tranche, address account) external view returns (uint256);

    function allShareBalanceOf(address account)
        external
        view
        returns (
            uint256,
            uint256,
            uint256
        );

    function shareBalanceVersion(address account) external view returns (uint256);

    function shareAllowance(
        uint256 tranche,
        address owner,
        address spender
    ) external view returns (uint256);

    function shareAllowanceVersion(address owner, address spender) external view returns (uint256);

    function getRebalanceSize() external view returns (uint256);

    function getRebalance(uint256 index) external view returns (Rebalance memory);

    function getRebalanceTimestamp(uint256 index) external view returns (uint256);

    function currentDay() external view returns (uint256);

    function fundActivityStartTime() external view returns (uint256);

    function exchangeActivityStartTime() external view returns (uint256);

    function isFundActive(uint256 timestamp) external view returns (bool);

    function isPrimaryMarketActive(address primaryMarket, uint256 timestamp)
        external
        view
        returns (bool);

    function isExchangeActive(uint256 timestamp) external view returns (bool);

    function getTotalShares() external view returns (uint256);

    function extrapolateNav(uint256 timestamp, uint256 price)
        external
        view
        returns (
            uint256,
            uint256,
            uint256
        );

    function calculateNavB(uint256 navM, uint256 navA) external pure returns (uint256);

    function doRebalance(
        uint256 amountM,
        uint256 amountA,
        uint256 amountB,
        uint256 index
    )
        external
        view
        returns (
            uint256 newAmountM,
            uint256 newAmountA,
            uint256 newAmountB
        );

    function batchRebalance(
        uint256 amountM,
        uint256 amountA,
        uint256 amountB,
        uint256 fromIndex,
        uint256 toIndex
    )
        external
        view
        returns (
            uint256 newAmountM,
            uint256 newAmountA,
            uint256 newAmountB
        );

    function refreshBalance(address account, uint256 targetVersion) external;

    function refreshAllowance(
        address owner,
        address spender,
        uint256 targetVersion
    ) external;

    function mint(
        uint256 tranche,
        address account,
        uint256 amount
    ) external;

    function burn(
        uint256 tranche,
        address account,
        uint256 amount
    ) external;

    function transfer(
        uint256 tranche,
        address sender,
        address recipient,
        uint256 amount
    ) external;

    function transferFrom(
        uint256 tranche,
        address spender,
        address sender,
        address recipient,
        uint256 amount
    ) external returns (uint256 newAllowance);

    function increaseAllowance(
        uint256 tranche,
        address sender,
        address spender,
        uint256 addedValue
    ) external returns (uint256 newAllowance);

    function decreaseAllowance(
        uint256 tranche,
        address sender,
        address spender,
        uint256 subtractedValue
    ) external returns (uint256 newAllowance);

    function approve(
        uint256 tranche,
        address owner,
        address spender,
        uint256 amount
    ) external;

    event RebalanceTriggered(
        uint256 indexed index,
        uint256 indexed day,
        uint256 ratioM,
        uint256 ratioA2M,
        uint256 ratioB2M,
        uint256 ratioAB
    );
    event Settled(uint256 indexed day, uint256 navM, uint256 navA, uint256 navB);
    event InterestRateUpdated(uint256 baseInterestRate, uint256 floatingInterestRate);
}




interface IChessController {
    function getFundRelativeWeight(address account, uint256 timestamp)
        external
        view
        returns (uint256);
}




interface IChessSchedule {
    function getRate(uint256 timestamp) external view returns (uint256);

    function mint(address account, uint256 amount) external;

    function addMinter(address account) external;
}




/// @notice Amounts of Token M, A and B are sometimes stored in a `uint256[3]` array. This contract
///         defines index of each tranche in this array.
///
///         Solidity does not allow constants to be defined in interfaces. So this contract follows
///         the naming convention of interfaces but is implemented as an `abstract contract`.
abstract contract ITrancheIndex {
    uint256 internal constant TRANCHE_M = 0;
    uint256 internal constant TRANCHE_A = 1;
    uint256 internal constant TRANCHE_B = 2;

    uint256 internal constant TRANCHE_COUNT = 3;
}




interface IPrimaryMarket {
    function claim(address account)
        external
        returns (uint256 createdShares, uint256 redeemedUnderlying);

    function settle(
        uint256 day,
        uint256 fundTotalShares,
        uint256 fundUnderlying,
        uint256 underlyingPrice,
        uint256 previousNav
    )
        external
        returns (
            uint256 sharesToMint,
            uint256 sharesToBurn,
            uint256 creationUnderlying,
            uint256 redemptionUnderlying,
            uint256 fee
        );
}



pragma experimental ABIEncoderV2;

interface IVotingEscrow {
    struct LockedBalance {
        uint256 amount;
        uint256 unlockTime;
    }

    function token() external view returns (address);

    function maxTime() external view returns (uint256);

    function balanceOf(address account) external view returns (uint256);

    function totalSupply() external view returns (uint256);

    function balanceOfAtTimestamp(address account, uint256 timestamp)
        external
        view
        returns (uint256);

    function getTimestampDropBelow(address account, uint256 threshold)
        external
        view
        returns (uint256);

    function getLockedBalance(address account) external view returns (LockedBalance memory);
}


/// @notice Chess locking snapshot used in calculating working balance of an account.
/// @param veProportion The account's veCHESS divided by the total veCHESS supply.
/// @param veLocked Locked CHESS and unlock time, which is synchronized from VotingEscrow.
struct VESnapshot {
    uint256 veProportion;
    IVotingEscrow.LockedBalance veLocked;
}

abstract contract StakingV2 is ITrancheIndex, CoreUtility, ManagedPausable {
    /// @dev Reserved storage slots for future sibling contract upgrades
    uint256[29] private _reservedSlots;

    using Math for uint256;
    using SafeMath for uint256;
    using SafeDecimalMath for uint256;
    using SafeERC20 for IERC20;

    event Deposited(uint256 tranche, address account, uint256 amount);
    event Withdrawn(uint256 tranche, address account, uint256 amount);

    uint256 private constant MAX_ITERATIONS = 500;

    uint256 private constant REWARD_WEIGHT_A = 4;
    uint256 private constant REWARD_WEIGHT_B = 2;
    uint256 private constant REWARD_WEIGHT_M = 3;
    uint256 private constant MAX_BOOSTING_FACTOR = 3e18;

    IFund public immutable fund;
    IERC20 private immutable tokenM;
    IERC20 private immutable tokenA;
    IERC20 private immutable tokenB;

    /// @notice The Chess release schedule contract.
    IChessSchedule public immutable chessSchedule;

    uint256 public immutable guardedLaunchStart;

    uint256 private _rate;

    /// @notice The controller contract.
    IChessController public immutable chessController;

    /// @notice Quote asset for the exchange. Each exchange only handles one quote asset
    address public immutable quoteAssetAddress;

    /// @dev Total amount of user shares, i.e. sum of all entries in `_availableBalances` and
    ///      `_lockedBalances`. Note that these values can be smaller than the amount of
    ///      share tokens held by this contract, because shares locked in unsettled trades
    ///      are not included in total supplies or any user's balance.
    uint256[TRANCHE_COUNT] private _totalSupplies;

    /// @dev Rebalance version of `_totalSupplies`.
    uint256 private _totalSupplyVersion;

    /// @dev Amount of shares that can be withdrawn or traded by each user.
    mapping(address => uint256[TRANCHE_COUNT]) private _availableBalances;

    /// @dev Amount of shares that are locked in ask orders.
    mapping(address => uint256[TRANCHE_COUNT]) private _lockedBalances;

    /// @dev Rebalance version mapping for `_availableBalances`.
    mapping(address => uint256) private _balanceVersions;

    /// @dev 1e27 * ∫(rate(t) / totalWeight(t) dt) from the latest rebalance till checkpoint.
    uint256 private _invTotalWeightIntegral;

    /// @dev Final `_invTotalWeightIntegral` before each rebalance.
    ///      These values are accessed in a loop in `_userCheckpoint()` with bounds checking.
    ///      So we store them in a fixed-length array, in order to make compiler-generated
    ///      bounds checking on every access cheaper. The actual length of this array is stored in
    ///      `_historicalIntegralSize` and should be explicitly checked when necessary.
    uint256[65535] private _historicalIntegrals;

    /// @dev Actual length of the `_historicalIntegrals` array, which always equals to the number of
    ///      historical rebalances after `checkpoint()` is called.
    uint256 private _historicalIntegralSize;

    /// @dev Timestamp when checkpoint() is called.
    uint256 private _checkpointTimestamp;

    /// @dev Snapshot of `_invTotalWeightIntegral` per user.
    mapping(address => uint256) private _userIntegrals;

    /// @dev Mapping of account => claimable rewards.
    mapping(address => uint256) private _claimableRewards;

    IVotingEscrow private immutable _votingEscrow;
    uint256 private _workingSupply;
    mapping(address => uint256) private _workingBalances;
    mapping(address => VESnapshot) private _veSnapshots;

    constructor(
        address fund_,
        address chessSchedule_,
        address chessController_,
        address quoteAssetAddress_,
        uint256 guardedLaunchStart_,
        address votingEscrow_
    ) public {
        fund = IFund(fund_);
        tokenM = IERC20(IFund(fund_).tokenM());
        tokenA = IERC20(IFund(fund_).tokenA());
        tokenB = IERC20(IFund(fund_).tokenB());
        chessSchedule = IChessSchedule(chessSchedule_);
        chessController = IChessController(chessController_);
        quoteAssetAddress = quoteAssetAddress_;
        guardedLaunchStart = guardedLaunchStart_;
        _votingEscrow = IVotingEscrow(votingEscrow_);
    }

    function _initializeStaking() internal {
        require(_checkpointTimestamp == 0);
        _checkpointTimestamp = block.timestamp;
        _rate = IChessSchedule(chessSchedule).getRate(block.timestamp);
    }

    function _initializeStakingV2(address pauser_) internal {
        _initializeManagedPausable(pauser_);
    }

    /// @notice Return weight of given balance with respect to rewards.
    /// @param amountM Amount of Token M
    /// @param amountA Amount of Token A
    /// @param amountB Amount of Token B
    /// @return Rewarding weight of the balance
    function weightedBalance(
        uint256 amountM,
        uint256 amountA,
        uint256 amountB
    ) public pure returns (uint256) {
        return
            amountM.mul(REWARD_WEIGHT_M).add(amountA.mul(REWARD_WEIGHT_A)).add(
                amountB.mul(REWARD_WEIGHT_B)
            ) / REWARD_WEIGHT_M;
    }

    function totalSupply(uint256 tranche) external view returns (uint256) {
        uint256 totalSupplyM = _totalSupplies[TRANCHE_M];
        uint256 totalSupplyA = _totalSupplies[TRANCHE_A];
        uint256 totalSupplyB = _totalSupplies[TRANCHE_B];

        uint256 version = _totalSupplyVersion;
        uint256 rebalanceSize = _fundRebalanceSize();
        if (version < rebalanceSize) {
            (totalSupplyM, totalSupplyA, totalSupplyB) = _fundBatchRebalance(
                totalSupplyM,
                totalSupplyA,
                totalSupplyB,
                version,
                rebalanceSize
            );
        }

        if (tranche == TRANCHE_M) {
            return totalSupplyM;
        } else if (tranche == TRANCHE_A) {
            return totalSupplyA;
        } else {
            return totalSupplyB;
        }
    }

    function availableBalanceOf(uint256 tranche, address account) external view returns (uint256) {
        uint256 amountM = _availableBalances[account][TRANCHE_M];
        uint256 amountA = _availableBalances[account][TRANCHE_A];
        uint256 amountB = _availableBalances[account][TRANCHE_B];

        if (tranche == TRANCHE_M) {
            if (amountM == 0 && amountA == 0 && amountB == 0) return 0;
        } else if (tranche == TRANCHE_A) {
            if (amountA == 0) return 0;
        } else {
            if (amountB == 0) return 0;
        }

        uint256 version = _balanceVersions[account];
        uint256 rebalanceSize = _fundRebalanceSize();
        if (version < rebalanceSize) {
            (amountM, amountA, amountB) = _fundBatchRebalance(
                amountM,
                amountA,
                amountB,
                version,
                rebalanceSize
            );
        }

        if (tranche == TRANCHE_M) {
            return amountM;
        } else if (tranche == TRANCHE_A) {
            return amountA;
        } else {
            return amountB;
        }
    }

    function lockedBalanceOf(uint256 tranche, address account) external view returns (uint256) {
        uint256 amountM = _lockedBalances[account][TRANCHE_M];
        uint256 amountA = _lockedBalances[account][TRANCHE_A];
        uint256 amountB = _lockedBalances[account][TRANCHE_B];

        if (tranche == TRANCHE_M) {
            if (amountM == 0 && amountA == 0 && amountB == 0) return 0;
        } else if (tranche == TRANCHE_A) {
            if (amountA == 0) return 0;
        } else {
            if (amountB == 0) return 0;
        }

        uint256 version = _balanceVersions[account];
        uint256 rebalanceSize = _fundRebalanceSize();
        if (version < rebalanceSize) {
            (amountM, amountA, amountB) = _fundBatchRebalance(
                amountM,
                amountA,
                amountB,
                version,
                rebalanceSize
            );
        }

        if (tranche == TRANCHE_M) {
            return amountM;
        } else if (tranche == TRANCHE_A) {
            return amountA;
        } else {
            return amountB;
        }
    }

    function balanceVersion(address account) external view returns (uint256) {
        return _balanceVersions[account];
    }

    function workingSupply() external view returns (uint256) {
        uint256 version = _totalSupplyVersion;
        uint256 rebalanceSize = _fundRebalanceSize();
        if (version < rebalanceSize) {
            (uint256 totalSupplyM, uint256 totalSupplyA, uint256 totalSupplyB) =
                _fundBatchRebalance(
                    _totalSupplies[TRANCHE_M],
                    _totalSupplies[TRANCHE_A],
                    _totalSupplies[TRANCHE_B],
                    version,
                    rebalanceSize
                );
            return weightedBalance(totalSupplyM, totalSupplyA, totalSupplyB);
        } else {
            return _workingSupply;
        }
    }

    function workingBalanceOf(address account) external view returns (uint256) {
        uint256 version = _balanceVersions[account];
        uint256 rebalanceSize = _fundRebalanceSize();
        if (version < rebalanceSize) {
            uint256[TRANCHE_COUNT] storage available = _availableBalances[account];
            uint256[TRANCHE_COUNT] storage locked = _lockedBalances[account];
            (uint256 amountM, uint256 amountA, uint256 amountB) =
                _fundBatchRebalance(
                    available[TRANCHE_M].add(locked[TRANCHE_M]),
                    available[TRANCHE_A].add(locked[TRANCHE_A]),
                    available[TRANCHE_B].add(locked[TRANCHE_B]),
                    version,
                    rebalanceSize
                );
            return weightedBalance(amountM, amountA, amountB);
        } else {
            return _workingBalances[account];
        }
    }

    function veSnapshotOf(address account) external view returns (VESnapshot memory) {
        return _veSnapshots[account];
    }

    function _fundRebalanceSize() internal view returns (uint256) {
        return fund.getRebalanceSize();
    }

    function _fundDoRebalance(
        uint256 amountM,
        uint256 amountA,
        uint256 amountB,
        uint256 index
    )
        internal
        view
        returns (
            uint256,
            uint256,
            uint256
        )
    {
        return fund.doRebalance(amountM, amountA, amountB, index);
    }

    function _fundBatchRebalance(
        uint256 amountM,
        uint256 amountA,
        uint256 amountB,
        uint256 fromIndex,
        uint256 toIndex
    )
        internal
        view
        returns (
            uint256,
            uint256,
            uint256
        )
    {
        return fund.batchRebalance(amountM, amountA, amountB, fromIndex, toIndex);
    }

    /// @dev Deposit to get rewards
    /// @param tranche Tranche of the share
    /// @param amount The amount to deposit
    //SWC-107-Reentrancy: L340-L359
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

    /// @dev Claim settled Token M from the primary market and deposit to get rewards
    /// @param primaryMarket The primary market to claim shares from
    function claimAndDeposit(address primaryMarket) external {
        (uint256 createdShares, ) = IPrimaryMarket(primaryMarket).claim(msg.sender);
        deposit(TRANCHE_M, createdShares);
    }

    /// @dev Withdraw
    /// @param tranche Tranche of the share
    /// @param amount The amount to deposit
    function withdraw(uint256 tranche, uint256 amount) external whenNotPaused {
        uint256 rebalanceSize = _fundRebalanceSize();
        _checkpoint(rebalanceSize);
        _userCheckpoint(msg.sender, rebalanceSize);
        _availableBalances[msg.sender][tranche] = _availableBalances[msg.sender][tranche].sub(
            amount,
            "Insufficient balance to withdraw"
        );
        _totalSupplies[tranche] = _totalSupplies[tranche].sub(amount);
        if (tranche == TRANCHE_M) {
            tokenM.safeTransfer(msg.sender, amount);
        } else if (tranche == TRANCHE_A) {
            tokenA.safeTransfer(msg.sender, amount);
        } else {
            tokenB.safeTransfer(msg.sender, amount);
        }

        _updateWorkingBalance(msg.sender);

        emit Withdrawn(tranche, msg.sender, amount);
    }

    /// @notice Transform share balance to a given rebalance version, or to the latest version
    ///         if `targetVersion` is zero.
    /// @param account Account of the balance to rebalance
    /// @param targetVersion The target rebalance version, or zero for the latest version
    function refreshBalance(address account, uint256 targetVersion) external {
        uint256 rebalanceSize = _fundRebalanceSize();
        if (targetVersion == 0) {
            targetVersion = rebalanceSize;
        } else {
            require(targetVersion <= rebalanceSize, "Target version out of bound");
        }
        _checkpoint(rebalanceSize);
        _userCheckpoint(account, targetVersion);
    }

    /// @notice Return claimable rewards of an account till now.
    ///
    ///         This function should be call as a "view" function off-chain to get
    ///         the return value, e.g. using `contract.claimableRewards.call(account)` in web3
    ///         or `contract.callStatic.claimableRewards(account)` in ethers.js.
    /// @param account Address of an account
    /// @return Amount of claimable rewards
    function claimableRewards(address account) external returns (uint256) {
        uint256 rebalanceSize = _fundRebalanceSize();
        _checkpoint(rebalanceSize);
        _userCheckpoint(account, rebalanceSize);
        return _claimableRewards[account];
    }

    /// @notice Claim the rewards for an account.
    /// @param account Account to claim its rewards
    function claimRewards(address account) external whenNotPaused {
        require(
            block.timestamp >= guardedLaunchStart + 15 days,
            "Cannot claim during guarded launch"
        );
        uint256 rebalanceSize = _fundRebalanceSize();
        _checkpoint(rebalanceSize);
        _userCheckpoint(account, rebalanceSize);
        _claim(account);
    }

    /// @notice Synchronize an account's locked Chess with `VotingEscrow`
    ///         and update its working balance.
    /// @param account Address of the synchronized account
    function syncWithVotingEscrow(address account) external {
        uint256 rebalanceSize = _fundRebalanceSize();
        _checkpoint(rebalanceSize);
        _userCheckpoint(account, rebalanceSize);

        VESnapshot storage veSnapshot = _veSnapshots[account];
        IVotingEscrow.LockedBalance memory newLocked = _votingEscrow.getLockedBalance(account);
        if (
            newLocked.amount != veSnapshot.veLocked.amount ||
            newLocked.unlockTime != veSnapshot.veLocked.unlockTime ||
            newLocked.unlockTime < block.timestamp
        ) {
            veSnapshot.veLocked.amount = newLocked.amount;
            veSnapshot.veLocked.unlockTime = newLocked.unlockTime;
            veSnapshot.veProportion = _votingEscrow.balanceOf(account).divideDecimal(
                _votingEscrow.totalSupply()
            );
        }

        _updateWorkingBalance(account);
    }

    /// @dev Transfer shares from the sender to the contract internally
    /// @param tranche Tranche of the share
    /// @param sender Sender address
    /// @param amount The amount to transfer
    function _tradeAvailable(
        uint256 tranche,
        address sender,
        uint256 amount
    ) internal {
        uint256 rebalanceSize = _fundRebalanceSize();
        _checkpoint(rebalanceSize);
        _userCheckpoint(sender, rebalanceSize);
        _availableBalances[sender][tranche] = _availableBalances[sender][tranche].sub(amount);
        _totalSupplies[tranche] = _totalSupplies[tranche].sub(amount);
        _updateWorkingBalance(sender);
    }

    function _rebalanceAndClearTrade(
        address account,
        uint256 amountM,
        uint256 amountA,
        uint256 amountB,
        uint256 amountVersion
    )
        internal
        returns (
            uint256,
            uint256,
            uint256
        )
    {
        uint256 rebalanceSize = _fundRebalanceSize();
        _checkpoint(rebalanceSize);
        _userCheckpoint(account, rebalanceSize);
        if (amountVersion < rebalanceSize) {
            (amountM, amountA, amountB) = _fundBatchRebalance(
                amountM,
                amountA,
                amountB,
                amountVersion,
                rebalanceSize
            );
        }
        uint256[TRANCHE_COUNT] storage available = _availableBalances[account];
        if (amountM > 0) {
            available[TRANCHE_M] = available[TRANCHE_M].add(amountM);
            _totalSupplies[TRANCHE_M] = _totalSupplies[TRANCHE_M].add(amountM);
        }
        if (amountA > 0) {
            available[TRANCHE_A] = available[TRANCHE_A].add(amountA);
            _totalSupplies[TRANCHE_A] = _totalSupplies[TRANCHE_A].add(amountA);
        }
        if (amountB > 0) {
            available[TRANCHE_B] = available[TRANCHE_B].add(amountB);
            _totalSupplies[TRANCHE_B] = _totalSupplies[TRANCHE_B].add(amountB);
        }
        _updateWorkingBalance(account);

        return (amountM, amountA, amountB);
    }

    function _lock(
        uint256 tranche,
        address account,
        uint256 amount
    ) internal {
        uint256 rebalanceSize = _fundRebalanceSize();
        _checkpoint(rebalanceSize);
        _userCheckpoint(account, rebalanceSize);
        _availableBalances[account][tranche] = _availableBalances[account][tranche].sub(
            amount,
            "Insufficient balance to lock"
        );
        _lockedBalances[account][tranche] = _lockedBalances[account][tranche].add(amount);
    }

    function _rebalanceAndUnlock(
        address account,
        uint256 amountM,
        uint256 amountA,
        uint256 amountB,
        uint256 amountVersion
    ) internal {
        uint256 rebalanceSize = _fundRebalanceSize();
        _checkpoint(rebalanceSize);
        _userCheckpoint(account, rebalanceSize);
        if (amountVersion < rebalanceSize) {
            (amountM, amountA, amountB) = _fundBatchRebalance(
                amountM,
                amountA,
                amountB,
                amountVersion,
                rebalanceSize
            );
        }
        uint256[TRANCHE_COUNT] storage available = _availableBalances[account];
        uint256[TRANCHE_COUNT] storage locked = _lockedBalances[account];
        if (amountM > 0) {
            available[TRANCHE_M] = available[TRANCHE_M].add(amountM);
            locked[TRANCHE_M] = locked[TRANCHE_M].sub(amountM);
        }
        if (amountA > 0) {
            available[TRANCHE_A] = available[TRANCHE_A].add(amountA);
            locked[TRANCHE_A] = locked[TRANCHE_A].sub(amountA);
        }
        if (amountB > 0) {
            available[TRANCHE_B] = available[TRANCHE_B].add(amountB);
            locked[TRANCHE_B] = locked[TRANCHE_B].sub(amountB);
        }
    }

    function _tradeLocked(
        uint256 tranche,
        address account,
        uint256 amount
    ) internal {
        uint256 rebalanceSize = _fundRebalanceSize();
        _checkpoint(rebalanceSize);
        _userCheckpoint(account, rebalanceSize);
        _lockedBalances[account][tranche] = _lockedBalances[account][tranche].sub(amount);
        _totalSupplies[tranche] = _totalSupplies[tranche].sub(amount);
        _updateWorkingBalance(account);
    }

    /// @dev Transfer claimable rewards to an account. Rewards since the last user checkpoint
    ///      is not included. This function should always be called after `_userCheckpoint()`,
    ///      in order for the user to get all rewards till now.
    /// @param account Address of the account
    function _claim(address account) internal {
        chessSchedule.mint(account, _claimableRewards[account]);
        _claimableRewards[account] = 0;
    }

    /// @dev Transform total supplies to the latest rebalance version and make a global reward checkpoint.
    /// @param rebalanceSize The number of existing rebalances. It must be the same as
    ///                       `fund.getRebalanceSize()`.
    function _checkpoint(uint256 rebalanceSize) private {
        uint256 timestamp = _checkpointTimestamp;
        if (timestamp >= block.timestamp) {
            return;
        }

        uint256 integral = _invTotalWeightIntegral;
        uint256 endWeek = _endOfWeek(timestamp);
        uint256 weeklyPercentage =
            chessController.getFundRelativeWeight(address(this), endWeek - 1 weeks);
        uint256 version = _totalSupplyVersion;
        uint256 rebalanceTimestamp;
        if (version < rebalanceSize) {
            rebalanceTimestamp = fund.getRebalanceTimestamp(version);
        } else {
            rebalanceTimestamp = type(uint256).max;
        }
        uint256 rate = _rate;
        uint256 totalSupplyM = _totalSupplies[TRANCHE_M];
        uint256 totalSupplyA = _totalSupplies[TRANCHE_A];
        uint256 totalSupplyB = _totalSupplies[TRANCHE_B];
        uint256 weight = _workingSupply;
        if (weight == 0) {
            weight = weightedBalance(totalSupplyM, totalSupplyA, totalSupplyB);
            if (weight > 0) {
                // The contract was just upgraded from an old version without boosting
                _workingSupply = weight;
            }
        }
        uint256 timestamp_ = timestamp; // avoid stack too deep

        for (uint256 i = 0; i < MAX_ITERATIONS && timestamp_ < block.timestamp; i++) {
            uint256 endTimestamp = rebalanceTimestamp.min(endWeek).min(block.timestamp);

            if (weight > 0) {
                integral = integral.add(
                    rate
                        .mul(endTimestamp.sub(timestamp_))
                        .multiplyDecimal(weeklyPercentage)
                        .divideDecimalPrecise(weight)
                );
            }

            if (endTimestamp == rebalanceTimestamp) {
                uint256 oldSize = _historicalIntegralSize;
                _historicalIntegrals[oldSize] = integral;
                _historicalIntegralSize = oldSize + 1;

                integral = 0;
                (totalSupplyM, totalSupplyA, totalSupplyB) = _fundDoRebalance(
                    totalSupplyM,
                    totalSupplyA,
                    totalSupplyB,
                    version
                );

                version++;
                // Reset total weight boosting after the first rebalance
                weight = weightedBalance(totalSupplyM, totalSupplyA, totalSupplyB);

                if (version < rebalanceSize) {
                    rebalanceTimestamp = fund.getRebalanceTimestamp(version);
                } else {
                    rebalanceTimestamp = type(uint256).max;
                }
            }
            if (endTimestamp == endWeek) {
                rate = chessSchedule.getRate(endWeek);
                weeklyPercentage = chessController.getFundRelativeWeight(address(this), endWeek);
                endWeek += 1 weeks;
            }

            timestamp_ = endTimestamp;
        }

        _checkpointTimestamp = block.timestamp;
        _invTotalWeightIntegral = integral;
        if (_rate != rate) {
            _rate = rate;
        }
        if (_totalSupplyVersion != rebalanceSize) {
            _totalSupplies[TRANCHE_M] = totalSupplyM;
            _totalSupplies[TRANCHE_A] = totalSupplyA;
            _totalSupplies[TRANCHE_B] = totalSupplyB;
            _totalSupplyVersion = rebalanceSize;
            // Reset total working weight before any boosting if rebalance ever triggered
            _workingSupply = weight;
        }
    }

    /// @dev Transform a user's balance to a given rebalance version and update this user's rewards.
    ///
    ///      In most cases, the target version is the latest version and this function cumulates
    ///      rewards till now. When this function is called from `refreshBalance()`,
    ///      `targetVersion` can be an older version, in which case rewards are cumulated till
    ///      the end of that version (i.e. timestamp of the transaction triggering the rebalance
    ///      with index `targetVersion`).
    ///
    ///      This function should always be called after `_checkpoint()` is called, so that
    ///      the global reward checkpoint is guarenteed up to date.
    /// @param account Account to update
    /// @param targetVersion The target rebalance version
    function _userCheckpoint(address account, uint256 targetVersion) private {
        uint256 oldVersion = _balanceVersions[account];
        if (oldVersion > targetVersion) {
            return;
        }
        uint256 userIntegral = _userIntegrals[account];
        uint256 integral;
        // This scope is to avoid the "stack too deep" error.
        {
            // We assume that this function is always called immediately after `_checkpoint()`,
            // which guarantees that `_historicalIntegralSize` equals to the number of historical
            // rebalances.
            uint256 rebalanceSize = _historicalIntegralSize;
            integral = targetVersion == rebalanceSize
                ? _invTotalWeightIntegral
                : _historicalIntegrals[targetVersion];
        }
        if (userIntegral == integral && oldVersion == targetVersion) {
            // Return immediately when the user's rewards have already been updated to
            // the target version.
            return;
        }

        uint256 rewards = _claimableRewards[account];
        uint256[TRANCHE_COUNT] storage available = _availableBalances[account];
        uint256[TRANCHE_COUNT] storage locked = _lockedBalances[account];
        uint256 weight = _workingBalances[account];
        if (weight == 0) {
            // Loading available and locked is repeated to avoid "stake too deep" error.
            weight = weightedBalance(
                available[TRANCHE_M].add(locked[TRANCHE_M]),
                available[TRANCHE_A].add(locked[TRANCHE_A]),
                available[TRANCHE_B].add(locked[TRANCHE_B])
            );
            if (weight > 0) {
                // The contract was just upgraded from an old version without boosting
                _workingBalances[account] = weight;
            }
        }
        uint256 availableM = available[TRANCHE_M];
        uint256 availableA = available[TRANCHE_A];
        uint256 availableB = available[TRANCHE_B];
        uint256 lockedM = locked[TRANCHE_M];
        uint256 lockedA = locked[TRANCHE_A];
        uint256 lockedB = locked[TRANCHE_B];
        for (uint256 i = oldVersion; i < targetVersion; i++) {
            rewards = rewards.add(
                weight.multiplyDecimalPrecise(_historicalIntegrals[i].sub(userIntegral))
            );
            if (availableM != 0 || availableA != 0 || availableB != 0) {
                (availableM, availableA, availableB) = _fundDoRebalance(
                    availableM,
                    availableA,
                    availableB,
                    i
                );
            }
            if (lockedM != 0 || lockedA != 0 || lockedB != 0) {
                (lockedM, lockedA, lockedB) = _fundDoRebalance(lockedM, lockedA, lockedB, i);
            }
            userIntegral = 0;

            // Reset per-user weight boosting after the first rebalance
            weight = weightedBalance(
                availableM.add(lockedM),
                availableA.add(lockedA),
                availableB.add(lockedB)
            );
        }
        rewards = rewards.add(weight.multiplyDecimalPrecise(integral.sub(userIntegral)));
        address account_ = account; // Fix the "stack too deep" error
        _claimableRewards[account_] = rewards;
        _userIntegrals[account_] = integral;

        if (oldVersion < targetVersion) {
            if (available[TRANCHE_M] != availableM) {
                available[TRANCHE_M] = availableM;
            }
            if (available[TRANCHE_A] != availableA) {
                available[TRANCHE_A] = availableA;
            }
            if (available[TRANCHE_B] != availableB) {
                available[TRANCHE_B] = availableB;
            }
            if (locked[TRANCHE_M] != lockedM) {
                locked[TRANCHE_M] = lockedM;
            }
            if (locked[TRANCHE_A] != lockedA) {
                locked[TRANCHE_A] = lockedA;
            }
            if (locked[TRANCHE_B] != lockedB) {
                locked[TRANCHE_B] = lockedB;
            }
            _balanceVersions[account_] = targetVersion;
            _workingBalances[account_] = weight;
        }
    }

    /// @dev Calculate working balance, which depends on the amount of staked tokens and veCHESS.
    ///      Before this function is called, both `_checkpoint()` and `_userCheckpoint(account)`
    ///      should be called to update `_workingSupply` and `_workingBalances[account]` to
    ///      the latest rebalance version.
    /// @param account User address
    function _updateWorkingBalance(address account) private {
        uint256 weightedSupply =
            weightedBalance(
                _totalSupplies[TRANCHE_M],
                _totalSupplies[TRANCHE_A],
                _totalSupplies[TRANCHE_B]
            );
        uint256[TRANCHE_COUNT] storage available = _availableBalances[account];
        uint256[TRANCHE_COUNT] storage locked = _lockedBalances[account];
        uint256 weightedUserBalance =
            weightedBalance(
                available[TRANCHE_M].add(locked[TRANCHE_M]),
                available[TRANCHE_A].add(locked[TRANCHE_A]),
                available[TRANCHE_B].add(locked[TRANCHE_B])
            );

        uint256 newWorkingBalance = weightedUserBalance;
        uint256 veProportion = _veSnapshots[account].veProportion;
        if (veProportion > 0 && _veSnapshots[account].veLocked.unlockTime > block.timestamp) {
            newWorkingBalance = newWorkingBalance.add(
                weightedSupply.multiplyDecimal(veProportion).multiplyDecimal(
                    MAX_BOOSTING_FACTOR - 1e18
                )
            );
            newWorkingBalance = newWorkingBalance.min(
                weightedUserBalance.multiplyDecimal(MAX_BOOSTING_FACTOR)
            );
        }

        _workingSupply = _workingSupply.sub(_workingBalances[account]).add(newWorkingBalance);
        _workingBalances[account] = newWorkingBalance;
    }
}
