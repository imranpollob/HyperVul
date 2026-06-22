// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.6.8;


pragma experimental ABIEncoderV2;





/**
 * @dev Wrappers over Solidity's arithmetic operations with added overflow
 * checks.
 *
 * Arithmetic operations in Solidity wrap on overflow. This can easily result
 * in bugs, because programmers usually assume that an overflow raises an
 * error, which is the standard behavior in high level programming languages.
 * `SafeMath` restores this intuition by reverting the transaction when an
 * operation overflows.
 *
 * Using this library instead of the unchecked operations eliminates an entire
 * class of bugs, so it's recommended to use it always.
 */
library SafeMath {
    /**
     * @dev Returns the addition of two unsigned integers, reverting on
     * overflow.
     *
     * Counterpart to Solidity's `+` operator.
     *
     * Requirements:
     *
     * - Addition cannot overflow.
     */
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a, "SafeMath: addition overflow");

        return c;
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, reverting on
     * overflow (when the result is negative).
     *
     * Counterpart to Solidity's `-` operator.
     *
     * Requirements:
     *
     * - Subtraction cannot overflow.
     */
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        return sub(a, b, "SafeMath: subtraction overflow");
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, reverting with custom message on
     * overflow (when the result is negative).
     *
     * Counterpart to Solidity's `-` operator.
     *
     * Requirements:
     *
     * - Subtraction cannot overflow.
     */
    function sub(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
        require(b <= a, errorMessage);
        uint256 c = a - b;

        return c;
    }

    /**
     * @dev Returns the multiplication of two unsigned integers, reverting on
     * overflow.
     *
     * Counterpart to Solidity's `*` operator.
     *
     * Requirements:
     *
     * - Multiplication cannot overflow.
     */
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        // Gas optimization: this is cheaper than requiring 'a' not being zero, but the
        // benefit is lost if 'b' is also tested.
        // See: https://github.com/OpenZeppelin/openzeppelin-contracts/pull/522
        if (a == 0) {
            return 0;
        }

        uint256 c = a * b;
        require(c / a == b, "SafeMath: multiplication overflow");

        return c;
    }

    /**
     * @dev Returns the integer division of two unsigned integers. Reverts on
     * division by zero. The result is rounded towards zero.
     *
     * Counterpart to Solidity's `/` operator. Note: this function uses a
     * `revert` opcode (which leaves remaining gas untouched) while Solidity
     * uses an invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        return div(a, b, "SafeMath: division by zero");
    }

    /**
     * @dev Returns the integer division of two unsigned integers. Reverts with custom message on
     * division by zero. The result is rounded towards zero.
     *
     * Counterpart to Solidity's `/` operator. Note: this function uses a
     * `revert` opcode (which leaves remaining gas untouched) while Solidity
     * uses an invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function div(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
        require(b > 0, errorMessage);
        uint256 c = a / b;
        // assert(a == b * c + a % b); // There is no case in which this doesn't hold

        return c;
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers. (unsigned integer modulo),
     * Reverts when dividing by zero.
     *
     * Counterpart to Solidity's `%` operator. This function uses a `revert`
     * opcode (which leaves remaining gas untouched) while Solidity uses an
     * invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function mod(uint256 a, uint256 b) internal pure returns (uint256) {
        return mod(a, b, "SafeMath: modulo by zero");
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers. (unsigned integer modulo),
     * Reverts with custom message when dividing by zero.
     *
     * Counterpart to Solidity's `%` operator. This function uses a `revert`
     * opcode (which leaves remaining gas untouched) while Solidity uses an
     * invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function mod(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
        require(b != 0, errorMessage);
        return a % b;
    }
}


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




/**
 * @title VersionedInitializable
 *
 * @dev Helper contract to support initializer functions. To use it, replace
 * the constructor with a function that has the `initializer` modifier.
 * WARNING: Unlike constructors, initializer functions must be manually
 * invoked. This applies both to deploying an Initializable contract, as well
 * as extending an Initializable contract via inheritance.
 * WARNING: When used with inheritance, manual care must be taken to not invoke
 * a parent initializer twice, or ensure that all initializers are idempotent,
 * because this is not dealt with automatically as with constructors.
 *
 * @author Aave, inspired by the OpenZeppelin Initializable contract
 */
abstract contract VersionedInitializable {
  /**
   * @dev Indicates that the contract has been initialized.
   */
  uint256 private lastInitializedRevision = 0;

  /**
   * @dev Indicates that the contract is in the process of being initialized.
   */
  bool private initializing;

  /**
   * @dev Modifier to use in the initializer function of a contract.
   */
  modifier initializer() {
    uint256 revision = getRevision();
    require(
      initializing || isConstructor() || revision > lastInitializedRevision,
      'Contract instance has already been initialized'
    );

    bool isTopLevelCall = !initializing;
    if (isTopLevelCall) {
      initializing = true;
      lastInitializedRevision = revision;
    }

    _;

    if (isTopLevelCall) {
      initializing = false;
    }
  }

  /// @dev returns the revision number of the contract.
  /// Needs to be defined in the inherited class as a constant.
  function getRevision() internal virtual pure returns (uint256);

  /// @dev Returns true if and only if the function is running in the constructor
  function isConstructor() private view returns (bool) {
    // extcodesize checks the size of the code stored in an address, and
    // address returns the current address. Since the code is still not
    // deployed when running a constructor, any checks on its code size will
    // yield zero, making it an effective way to detect if a contract is
    // under construction or not.
    uint256 cs;
    //solium-disable-next-line
    assembly {
      cs := extcodesize(address())
    }
    return cs == 0;
  }

  // Reserved storage space to allow for layout changes in the future.
  uint256[50] private ______gap;
}




/**
@title ILendingPoolAddressesProvider interface
@notice provides the interface to fetch the Aave protocol address
 */

interface ILendingPoolAddressesProvider {
  //events
  event LendingPoolUpdated(address indexed newAddress);
  event AaveAdminUpdated(address indexed newAddress);
  event LendingPoolConfiguratorUpdated(address indexed newAddress);
  event LendingPoolCollateralManagerUpdated(address indexed newAddress);
  event EthereumAddressUpdated(address indexed newAddress);
  event PriceOracleUpdated(address indexed newAddress);
  event LendingRateOracleUpdated(address indexed newAddress);

  event ProxyCreated(bytes32 id, address indexed newAddress);

  function getLendingPool() external view returns (address);

  function setLendingPoolImpl(address pool) external;

  function getLendingPoolConfigurator() external view returns (address);

  function setLendingPoolConfiguratorImpl(address configurator) external;

  function getLendingPoolCollateralManager() external view returns (address);

  function setLendingPoolCollateralManager(address manager) external;

  function getAaveAdmin() external view returns (address);

  function setAaveAdmin(address aaveAdmin) external;

  function getPriceOracle() external view returns (address);

  function setPriceOracle(address priceOracle) external;

  function getLendingRateOracle() external view returns (address);

  function setLendingRateOracle(address lendingRateOracle) external;
}







/**
 * @dev Interface of the ERC20 standard as defined in the EIP.
 */
/* Duplicate interface IERC20 removed */                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    





interface IScaledBalanceToken {

  /**
   * @dev emitted after the mint action
   * @param from the address performing the mint
   * @param value the amount to be minted
   * @param index the last index of the reserve
   **/
  event Mint(address indexed from, uint256 value, uint256 index);

  /**
   * @dev mints aTokens to user
   * only lending pools can call this function
   * @param user the address receiving the minted tokens
   * @param amount the amount of tokens to mint
   * @param index the liquidity index
   */
  function mint(
    address user,
    uint256 amount,
    uint256 index
  ) external;

  /**
   * @dev returns the principal balance of the user. The principal balance is the last
   * updated stored balance, which does not consider the perpetually accruing interest.
   * @param user the address of the user
   * @return the principal balance of the user
   **/
  function scaledBalanceOf(address user) external view returns (uint256);

  /**
   * @dev returns the principal balance of the user and principal total supply.
   * @param user the address of the user
   * @return the principal balance of the user
   * @return the principal total supply
   **/
  function getScaledUserBalanceAndSupply(address user) external view returns (uint256, uint256);

  /**
   * @dev Returns the scaled total supply of the variable debt token. Represents sum(borrows/index)
   * @return the scaled total supply
   **/
  function scaledTotalSupply() external view returns (uint256);
}


interface IAToken is IERC20, IScaledBalanceToken {
  /**
   * @dev emitted after aTokens are burned
   * @param from the address performing the redeem
   * @param value the amount to be redeemed
   * @param index the last index of the reserve
   **/
  event Burn(
    address indexed from,
    address indexed target,
    uint256 value,
    uint256 index
  );
  /**
   * @dev emitted during the transfer action
   * @param from the address from which the tokens are being transferred
   * @param to the adress of the destination
   * @param value the amount to be minted
   * @param index the last index of the reserve
   **/
  event BalanceTransfer(
    address indexed from,
    address indexed to,
    uint256 value,
    uint256 index
  );
  /**
   * @dev burns the aTokens and sends the equivalent amount of underlying to the target.
   * only lending pools can call this function
   * @param amount the amount being burned
   * @param index the liquidity index
   **/
  function burn(
    address user,
    address underlyingTarget,
    uint256 amount,
    uint256 index
  ) external;

  /**
   * @dev mints aTokens to the reserve treasury
   * @param amount the amount to mint
   * @param index the liquidity index of the reserve
   **/
  function mintToTreasury(uint256 amount, uint256 index) external;

  /**
   * @dev transfers tokens in the event of a borrow being liquidated, in case the liquidators reclaims the aToken
   *      only lending pools can call this function
   * @param from the address from which transfer the aTokens
   * @param to the destination address
   * @param value the amount to transfer
   **/
  function transferOnLiquidation(
    address from,
    address to,
    uint256 value
  ) external;

  
  function isTransferAllowed(address user, uint256 amount) external view returns (bool);

  /**
   * @dev transfer the amount of the underlying asset to the user
   * @param user address of the user
   * @param amount the amount to transfer
   * @return the amount transferred
   **/
  function transferUnderlyingTo(address user, uint256 amount) external returns (uint256);


}











/*
 * @dev Provides information about the current execution context, including the
 * sender of the transaction and its data. While these are generally available
 * via msg.sender and msg.data, they should not be accessed in such a direct
 * manner, since when dealing with GSN meta-transactions the account sending and
 * paying for execution may not be the actual sender (as far as an application
 * is concerned).
 *
 * This contract is only required for intermediate, library-like contracts.
 */
abstract contract Context {
    function _msgSender() internal view virtual returns (address payable) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes memory) {
        this; // silence state mutability warning without generating bytecode - see https://github.com/ethereum/solidity/issues/2691
        return msg.data;
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
/* Duplicate abstract contract Context removed */                                                                                                                                                                                                                                                                                                 


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
















/**
 * @title Proxy
 * @dev Implements delegation of calls to other contracts, with proper
 * forwarding of return values and bubbling of failures.
 * It defines a fallback function that delegates all calls to the address
 * returned by the abstract _implementation() internal function.
 */
abstract contract Proxy {
  /**
   * @dev Fallback function.
   * Implemented entirely in `_fallback`.
   */
  fallback() external payable {
    _fallback();
  }

  /**
   * @return The Address of the implementation.
   */
  function _implementation() internal virtual view returns (address);

  /**
   * @dev Delegates execution to an implementation contract.
   * This is a low level function that doesn't return to its internal call site.
   * It will return to the external caller whatever the implementation returns.
   * @param implementation Address to delegate.
   */
  function _delegate(address implementation) internal {
    //solium-disable-next-line
    assembly {
      // Copy msg.data. We take full control of memory in this inline assembly
      // block because it will not return to Solidity code. We overwrite the
      // Solidity scratch pad at memory position 0.
      calldatacopy(0, 0, calldatasize())

      // Call the implementation.
      // out and outsize are 0 because we don't know the size yet.
      let result := delegatecall(gas(), implementation, 0, calldatasize(), 0, 0)

      // Copy the returned data.
      returndatacopy(0, 0, returndatasize())

      switch result
        // delegatecall returns 0 on error.
        case 0 {
          revert(0, returndatasize())
        }
        default {
          return(0, returndatasize())
        }
    }
  }

  /**
   * @dev Function that is run as the first thing in the fallback function.
   * Can be redefined in derived contracts to add functionality.
   * Redefinitions must call super._willFallback().
   */
  function _willFallback() internal virtual {}

  /**
   * @dev fallback implementation.
   * Extracted to enable manual triggering.
   */
  function _fallback() internal {
    _willFallback();
    _delegate(_implementation());
  }
}


// OpenZeppelin Contracts (last updated v5.5.0) (utils/Address.sol)




// OpenZeppelin Contracts (last updated v5.1.0) (utils/Errors.sol)



/**
 * @dev Collection of common custom errors used in multiple contracts
 *
 * IMPORTANT: Backwards compatibility is not guaranteed in future versions of the library.
 * It is recommended to avoid relying on the error API for critical functionality.
 *
 * _Available since v5.1._
 */
library Errors {
    /**
     * @dev The ETH balance of the account is not enough to perform the operation.
     */
    error InsufficientBalance(uint256 balance, uint256 needed);

    /**
     * @dev A call to an address target failed. The target may have reverted.
     */
    error FailedCall();

    /**
     * @dev The deployment failed.
     */
    error FailedDeployment();

    /**
     * @dev A necessary precompile is missing.
     */
    error MissingPrecompile(address);
}


// OpenZeppelin Contracts (last updated v5.6.0) (utils/LowLevelCall.sol)



/**
 * @dev Library of low level call functions that implement different calling strategies to deal with the return data.
 *
 * WARNING: Using this library requires an advanced understanding of Solidity and how the EVM works. It is recommended
 * to use the {Address} library instead.
 */
library LowLevelCall {
    /// @dev Performs a Solidity function call using a low level `call` and ignoring the return data.
    function callNoReturn(address target, bytes memory data) internal returns (bool success) {
        return callNoReturn(target, 0, data);
    }

    /// @dev Same as {callNoReturn-address-bytes}, but allows specifying the value to be sent in the call.
    function callNoReturn(address target, uint256 value, bytes memory data) internal returns (bool success) {
        assembly {
            success := call(gas(), target, value, add(data, 0x20), mload(data), 0x00, 0x00)
        }
    }

    /// @dev Performs a Solidity function call using a low level `call` and returns the first 64 bytes of the result
    /// in the scratch space of memory. Useful for functions that return a tuple with two single-word values.
    ///
    /// WARNING: Do not assume that the results are zero if `success` is false. Memory can be already allocated
    /// and this function doesn't zero it out.
    function callReturn64Bytes(
        address target,
        bytes memory data
    ) internal returns (bool success, bytes32 result1, bytes32 result2) {
        return callReturn64Bytes(target, 0, data);
    }

    /// @dev Same as {callReturn64Bytes-address-bytes}, but allows specifying the value to be sent in the call.
    function callReturn64Bytes(
        address target,
        uint256 value,
        bytes memory data
    ) internal returns (bool success, bytes32 result1, bytes32 result2) {
        assembly {
            success := call(gas(), target, value, add(data, 0x20), mload(data), 0x00, 0x40)
            result1 := mload(0x00)
            result2 := mload(0x20)
        }
    }

    /// @dev Performs a Solidity function call using a low level `staticcall` and ignoring the return data.
    function staticcallNoReturn(address target, bytes memory data) internal view returns (bool success) {
        assembly {
            success := staticcall(gas(), target, add(data, 0x20), mload(data), 0x00, 0x00)
        }
    }

    /// @dev Performs a Solidity function call using a low level `staticcall` and returns the first 64 bytes of the result
    /// in the scratch space of memory. Useful for functions that return a tuple with two single-word values.
    ///
    /// WARNING: Do not assume that the results are zero if `success` is false. Memory can be already allocated
    /// and this function doesn't zero it out.
    function staticcallReturn64Bytes(
        address target,
        bytes memory data
    ) internal view returns (bool success, bytes32 result1, bytes32 result2) {
        assembly {
            success := staticcall(gas(), target, add(data, 0x20), mload(data), 0x00, 0x40)
            result1 := mload(0x00)
            result2 := mload(0x20)
        }
    }

    /// @dev Performs a Solidity function call using a low level `delegatecall` and ignoring the return data.
    function delegatecallNoReturn(address target, bytes memory data) internal returns (bool success) {
        assembly {
            success := delegatecall(gas(), target, add(data, 0x20), mload(data), 0x00, 0x00)
        }
    }

    /// @dev Performs a Solidity function call using a low level `delegatecall` and returns the first 64 bytes of the result
    /// in the scratch space of memory. Useful for functions that return a tuple with two single-word values.
    ///
    /// WARNING: Do not assume that the results are zero if `success` is false. Memory can be already allocated
    /// and this function doesn't zero it out.
    function delegatecallReturn64Bytes(
        address target,
        bytes memory data
    ) internal returns (bool success, bytes32 result1, bytes32 result2) {
        assembly {
            success := delegatecall(gas(), target, add(data, 0x20), mload(data), 0x00, 0x40)
            result1 := mload(0x00)
            result2 := mload(0x20)
        }
    }

    /// @dev Returns the size of the return data buffer.
    function returnDataSize() internal pure returns (uint256 size) {
        assembly {
            size := returndatasize()
        }
    }

    /// @dev Returns a buffer containing the return data from the last call.
    function returnData() internal pure returns (bytes memory result) {
        assembly {
            result := mload(0x40)
            mstore(result, returndatasize())
            returndatacopy(add(result, 0x20), 0x00, returndatasize())
            mstore(0x40, add(result, add(0x20, returndatasize())))
        }
    }

    /// @dev Revert with the return data from the last call.
    function bubbleRevert() internal pure {
        assembly {
            let fmp := mload(0x40)
            returndatacopy(fmp, 0x00, returndatasize())
            revert(fmp, returndatasize())
        }
    }

    function bubbleRevert(bytes memory returndata) internal pure {
        assembly {
            revert(add(returndata, 0x20), mload(returndata))
        }
    }
}


/**
 * @dev Collection of functions related to the address type
 */
library Address {
    /**
     * @dev There's no code at `target` (it is not a contract).
     */
    error AddressEmptyCode(address target);

    /**
     * @dev Replacement for Solidity's `transfer`: sends `amount` wei to
     * `recipient`, forwarding all available gas and reverting on errors.
     *
     * https://eips.ethereum.org/EIPS/eip-1884[EIP1884] increases the gas cost
     * of certain opcodes, possibly making contracts go over the 2300 gas limit
     * imposed by `transfer`, making them unable to receive funds via
     * `transfer`. {sendValue} removes this limitation.
     *
     * https://consensys.net/diligence/blog/2019/09/stop-using-soliditys-transfer-now/[Learn more].
     *
     * IMPORTANT: because control is transferred to `recipient`, care must be
     * taken to not create reentrancy vulnerabilities. Consider using
     * {ReentrancyGuard} or the
     * https://solidity.readthedocs.io/en/v0.8.20/security-considerations.html#use-the-checks-effects-interactions-pattern[checks-effects-interactions pattern].
     */
    function sendValue(address payable recipient, uint256 amount) internal {
        if (address(this).balance < amount) {
            revert Errors.InsufficientBalance(address(this).balance, amount);
        }
        if (LowLevelCall.callNoReturn(recipient, amount, "")) {
            // call successful, nothing to do
            return;
        } else if (LowLevelCall.returnDataSize() > 0) {
            LowLevelCall.bubbleRevert();
        } else {
            revert Errors.FailedCall();
        }
    }

    /**
     * @dev Performs a Solidity function call using a low level `call`. A
     * plain `call` is an unsafe replacement for a function call: use this
     * function instead.
     *
     * If `target` reverts with a revert reason or custom error, it is bubbled
     * up by this function (like regular Solidity function calls). However, if
     * the call reverted with no returned reason, this function reverts with a
     * {Errors.FailedCall} error.
     *
     * Returns the raw returned data. To convert to the expected return value,
     * use https://solidity.readthedocs.io/en/latest/units-and-global-variables.html?highlight=abi.decode#abi-encoding-and-decoding-functions[`abi.decode`].
     *
     * Requirements:
     *
     * - `target` must be a contract.
     * - calling `target` with `data` must not revert.
     */
    function functionCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionCallWithValue(target, data, 0);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but also transferring `value` wei to `target`.
     *
     * Requirements:
     *
     * - the calling contract must have an ETH balance of at least `value`.
     * - the called Solidity function must be `payable`.
     */
    function functionCallWithValue(address target, bytes memory data, uint256 value) internal returns (bytes memory) {
        if (address(this).balance < value) {
            revert Errors.InsufficientBalance(address(this).balance, value);
        }
        bool success = LowLevelCall.callNoReturn(target, value, data);
        if (success && (LowLevelCall.returnDataSize() > 0 || target.code.length > 0)) {
            return LowLevelCall.returnData();
        } else if (success) {
            revert AddressEmptyCode(target);
        } else if (LowLevelCall.returnDataSize() > 0) {
            LowLevelCall.bubbleRevert();
        } else {
            revert Errors.FailedCall();
        }
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but performing a static call.
     */
    function functionStaticCall(address target, bytes memory data) internal view returns (bytes memory) {
        bool success = LowLevelCall.staticcallNoReturn(target, data);
        if (success && (LowLevelCall.returnDataSize() > 0 || target.code.length > 0)) {
            return LowLevelCall.returnData();
        } else if (success) {
            revert AddressEmptyCode(target);
        } else if (LowLevelCall.returnDataSize() > 0) {
            LowLevelCall.bubbleRevert();
        } else {
            revert Errors.FailedCall();
        }
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but performing a delegate call.
     */
    function functionDelegateCall(address target, bytes memory data) internal returns (bytes memory) {
        bool success = LowLevelCall.delegatecallNoReturn(target, data);
        if (success && (LowLevelCall.returnDataSize() > 0 || target.code.length > 0)) {
            return LowLevelCall.returnData();
        } else if (success) {
            revert AddressEmptyCode(target);
        } else if (LowLevelCall.returnDataSize() > 0) {
            LowLevelCall.bubbleRevert();
        } else {
            revert Errors.FailedCall();
        }
    }

    /**
     * @dev Tool to verify that a low level call to smart-contract was successful, and reverts if the target
     * was not a contract or bubbling up the revert reason (falling back to {Errors.FailedCall}) in case
     * of an unsuccessful call.
     *
     * NOTE: This function is DEPRECATED and may be removed in the next major release.
     */
    function verifyCallResultFromTarget(
        address target,
        bool success,
        bytes memory returndata
    ) internal view returns (bytes memory) {
        // only check if target is a contract if the call was successful and the return data is empty
        // otherwise we already know that it was a contract
        if (success && (returndata.length > 0 || target.code.length > 0)) {
            return returndata;
        } else if (success) {
            revert AddressEmptyCode(target);
        } else if (returndata.length > 0) {
            LowLevelCall.bubbleRevert(returndata);
        } else {
            revert Errors.FailedCall();
        }
    }

    /**
     * @dev Tool to verify that a low level call was successful, and reverts if it wasn't, either by bubbling the
     * revert reason or with a default {Errors.FailedCall} error.
     */
    function verifyCallResult(bool success, bytes memory returndata) internal pure returns (bytes memory) {
        if (success) {
            return returndata;
        } else if (returndata.length > 0) {
            LowLevelCall.bubbleRevert(returndata);
        } else {
            revert Errors.FailedCall();
        }
    }
}


/**
 * @title BaseUpgradeabilityProxy
 * @dev This contract implements a proxy that allows to change the
 * implementation address to which it will delegate.
 * Such a change is called an implementation upgrade.
 */
contract BaseUpgradeabilityProxy is Proxy {
  /**
   * @dev Emitted when the implementation is upgraded.
   * @param implementation Address of the new implementation.
   */
  event Upgraded(address indexed implementation);

  /**
   * @dev Storage slot with the address of the current implementation.
   * This is the keccak-256 hash of "eip1967.proxy.implementation" subtracted by 1, and is
   * validated in the constructor.
   */
  bytes32 internal constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;

  /**
   * @dev Returns the current implementation.
   * @return impl Address of the current implementation
   */
  function _implementation() internal override view returns (address impl) {
    bytes32 slot = IMPLEMENTATION_SLOT;
    //solium-disable-next-line
    assembly {
      impl := sload(slot)
    }
  }

  /**
   * @dev Upgrades the proxy to a new implementation.
   * @param newImplementation Address of the new implementation.
   */
  function _upgradeTo(address newImplementation) internal {
    _setImplementation(newImplementation);
    emit Upgraded(newImplementation);
  }

  /**
   * @dev Sets the implementation address of the proxy.
   * @param newImplementation Address of the new implementation.
   */
  function _setImplementation(address newImplementation) internal {
    require(
      Address.isContract(newImplementation),
      'Cannot set a proxy implementation to a non-contract address'
    );

    bytes32 slot = IMPLEMENTATION_SLOT;

    //solium-disable-next-line
    assembly {
      sstore(slot, newImplementation)
    }
  }
}


/**
 * @title UpgradeabilityProxy
 * @dev Extends BaseUpgradeabilityProxy with a constructor for initializing
 * implementation and init data.
 */
contract UpgradeabilityProxy is BaseUpgradeabilityProxy {
  /**
   * @dev Contract constructor.
   * @param _logic Address of the initial implementation.
   * @param _data Data to send as msg.data to the implementation to initialize the proxied contract.
   * It should include the signature and the parameters of the function to be called, as described in
   * https://solidity.readthedocs.io/en/v0.4.24/abi-spec.html#function-selector-and-argument-encoding.
   * This parameter is optional, if no data is given the initialization call to proxied contract will be skipped.
   */
  constructor(address _logic, bytes memory _data) public payable {
    assert(IMPLEMENTATION_SLOT == bytes32(uint256(keccak256('eip1967.proxy.implementation')) - 1));
    _setImplementation(_logic);
    if (_data.length > 0) {
      (bool success, ) = _logic.delegatecall(_data);
      require(success);
    }
  }
}


/**
 * @title BaseAdminUpgradeabilityProxy
 * @dev This contract combines an upgradeability proxy with an authorization
 * mechanism for administrative tasks.
 * All external functions in this contract must be guarded by the
 * `ifAdmin` modifier. See ethereum/solidity#3864 for a Solidity
 * feature proposal that would enable this to be done automatically.
 */
contract BaseAdminUpgradeabilityProxy is BaseUpgradeabilityProxy {
  /**
   * @dev Emitted when the administration has been transferred.
   * @param previousAdmin Address of the previous admin.
   * @param newAdmin Address of the new admin.
   */
  event AdminChanged(address previousAdmin, address newAdmin);

  /**
   * @dev Storage slot with the admin of the contract.
   * This is the keccak-256 hash of "eip1967.proxy.admin" subtracted by 1, and is
   * validated in the constructor.
   */
  bytes32 internal constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;

  /**
   * @dev Modifier to check whether the `msg.sender` is the admin.
   * If it is, it will run the function. Otherwise, it will delegate the call
   * to the implementation.
   */
  modifier ifAdmin() {
    if (msg.sender == _admin()) {
      _;
    } else {
      _fallback();
    }
  }

  /**
   * @return The address of the proxy admin.
   */
  function admin() external ifAdmin returns (address) {
    return _admin();
  }

  /**
   * @return The address of the implementation.
   */
  function implementation() external ifAdmin returns (address) {
    return _implementation();
  }

  /**
   * @dev Changes the admin of the proxy.
   * Only the current admin can call this function.
   * @param newAdmin Address to transfer proxy administration to.
   */
  function changeAdmin(address newAdmin) external ifAdmin {
    require(newAdmin != address(0), 'Cannot change the admin of a proxy to the zero address');
    emit AdminChanged(_admin(), newAdmin);
    _setAdmin(newAdmin);
  }

  /**
   * @dev Upgrade the backing implementation of the proxy.
   * Only the admin can call this function.
   * @param newImplementation Address of the new implementation.
   */
  function upgradeTo(address newImplementation) external ifAdmin {
    _upgradeTo(newImplementation);
  }

  /**
   * @dev Upgrade the backing implementation of the proxy and call a function
   * on the new implementation.
   * This is useful to initialize the proxied contract.
   * @param newImplementation Address of the new implementation.
   * @param data Data to send as msg.data in the low level call.
   * It should include the signature and the parameters of the function to be called, as described in
   * https://solidity.readthedocs.io/en/v0.4.24/abi-spec.html#function-selector-and-argument-encoding.
   */
  function upgradeToAndCall(address newImplementation, bytes calldata data)
    external
    payable
    ifAdmin
  {
    _upgradeTo(newImplementation);
    (bool success, ) = newImplementation.delegatecall(data);
    require(success);
  }

  /**
   * @return adm The admin slot.
   */
  function _admin() internal view returns (address adm) {
    bytes32 slot = ADMIN_SLOT;
    //solium-disable-next-line
    assembly {
      adm := sload(slot)
    }
  }

  /**
   * @dev Sets the address of the proxy admin.
   * @param newAdmin Address of the new proxy admin.
   */
  function _setAdmin(address newAdmin) internal {
    bytes32 slot = ADMIN_SLOT;
    //solium-disable-next-line
    assembly {
      sstore(slot, newAdmin)
    }
  }

  /**
   * @dev Only fall back when the sender is not the admin.
   */
  function _willFallback() internal virtual override {
    require(msg.sender != _admin(), 'Cannot call fallback function from the proxy admin');
    super._willFallback();
  }
}






/**
 * @title InitializableUpgradeabilityProxy
 * @dev Extends BaseUpgradeabilityProxy with an initializer for initializing
 * implementation and init data.
 */
contract InitializableUpgradeabilityProxy is BaseUpgradeabilityProxy {
  /**
   * @dev Contract initializer.
   * @param _logic Address of the initial implementation.
   * @param _data Data to send as msg.data to the implementation to initialize the proxied contract.
   * It should include the signature and the parameters of the function to be called, as described in
   * https://solidity.readthedocs.io/en/v0.4.24/abi-spec.html#function-selector-and-argument-encoding.
   * This parameter is optional, if no data is given the initialization call to proxied contract will be skipped.
   */
  function initialize(address _logic, bytes memory _data) public payable {
    require(_implementation() == address(0));
    assert(IMPLEMENTATION_SLOT == bytes32(uint256(keccak256('eip1967.proxy.implementation')) - 1));
    _setImplementation(_logic);
    if (_data.length > 0) {
      (bool success, ) = _logic.delegatecall(_data);
      require(success);
    }
  }
}


/**
 * @title InitializableAdminUpgradeabilityProxy
 * @dev Extends from BaseAdminUpgradeabilityProxy with an initializer for
 * initializing the implementation, admin, and init data.
 */
contract InitializableAdminUpgradeabilityProxy is
  BaseAdminUpgradeabilityProxy,
  InitializableUpgradeabilityProxy
{
  /**
   * Contract initializer.
   * @param logic address of the initial implementation.
   * @param admin Address of the proxy administrator.
   * @param data Data to send as msg.data to the implementation to initialize the proxied contract.
   * It should include the signature and the parameters of the function to be called, as described in
   * https://solidity.readthedocs.io/en/v0.4.24/abi-spec.html#function-selector-and-argument-encoding.
   * This parameter is optional, if no data is given the initialization call to proxied contract will be skipped.
   */
  function initialize(
    address logic,
    address admin,
    bytes memory data
  ) public payable {
    require(_implementation() == address(0));
    InitializableUpgradeabilityProxy.initialize(logic, data);
    assert(ADMIN_SLOT == bytes32(uint256(keccak256('eip1967.proxy.admin')) - 1));
    _setAdmin(admin);
  }

  /**
   * @dev Only fall back when the sender is not the admin.
   */
  function _willFallback() internal override(BaseAdminUpgradeabilityProxy, Proxy) {
    BaseAdminUpgradeabilityProxy._willFallback();
  }
}




/**
 * @title LendingPoolAddressesProvider contract
 * @notice Is the main registry of the protocol. All the different components of the protocol are accessible
 * through the addresses provider.
 * @author Aave
 **/

contract LendingPoolAddressesProvider is Ownable, ILendingPoolAddressesProvider {
  mapping(bytes32 => address) private _addresses;

  bytes32 private constant LENDING_POOL = 'LENDING_POOL';
  bytes32 private constant LENDING_POOL_CORE = 'LENDING_POOL_CORE';
  bytes32 private constant LENDING_POOL_CONFIGURATOR = 'LENDING_POOL_CONFIGURATOR';
  bytes32 private constant AAVE_ADMIN = 'AAVE_ADMIN';
  bytes32 private constant LENDING_POOL_COLLATERAL_MANAGER = 'COLLATERAL_MANAGER';
  bytes32 private constant LENDING_POOL_FLASHLOAN_PROVIDER = 'FLASHLOAN_PROVIDER';
  bytes32 private constant DATA_PROVIDER = 'DATA_PROVIDER';
  bytes32 private constant ETHEREUM_ADDRESS = 'ETHEREUM_ADDRESS';
  bytes32 private constant PRICE_ORACLE = 'PRICE_ORACLE';
  bytes32 private constant LENDING_RATE_ORACLE = 'LENDING_RATE_ORACLE';
  bytes32 private constant WALLET_BALANCE_PROVIDER = 'WALLET_BALANCE_PROVIDER';

  /**
   * @dev returns the address of the LendingPool proxy
   * @return the lending pool proxy address
   **/
  function getLendingPool() external override view returns (address) {
    return _addresses[LENDING_POOL];
  }

  /**
   * @dev updates the implementation of the lending pool
   * @param pool the new lending pool implementation
   **/
  function setLendingPoolImpl(address pool) external override onlyOwner {
    _updateImpl(LENDING_POOL, pool);
    emit LendingPoolUpdated(pool);
  }

  /**
   * @dev returns the address of the LendingPoolConfigurator proxy
   * @return the lending pool configurator proxy address
   **/
  function getLendingPoolConfigurator() external override view returns (address) {
    return _addresses[LENDING_POOL_CONFIGURATOR];
  }

  /**
   * @dev updates the implementation of the lending pool configurator
   * @param configurator the new lending pool configurator implementation
   **/
  function setLendingPoolConfiguratorImpl(address configurator) external override onlyOwner {
    _updateImpl(LENDING_POOL_CONFIGURATOR, configurator);
    emit LendingPoolConfiguratorUpdated(configurator);
  }

  /**
   * @dev returns the address of the LendingPoolCollateralManager. Since the manager is used
   * through delegateCall within the LendingPool contract, the proxy contract pattern does not work properly hence
   * the addresses are changed directly.
   * @return the address of the Lending pool collateral manager
   **/

  function getLendingPoolCollateralManager() external override view returns (address) {
    return _addresses[LENDING_POOL_COLLATERAL_MANAGER];
  }

  /**
   * @dev updates the address of the Lending pool collateral manager
   * @param manager the new lending pool collateral manager address
   **/
  function setLendingPoolCollateralManager(address manager) external override onlyOwner {
    _addresses[LENDING_POOL_COLLATERAL_MANAGER] = manager;
    emit LendingPoolCollateralManagerUpdated(manager);
  }

  /**
   * @dev the functions below are storing specific addresses that are outside the context of the protocol
   * hence the upgradable proxy pattern is not used
   **/

  function getAaveAdmin() external override view returns (address) {
    return _addresses[AAVE_ADMIN];
  }

  function setAaveAdmin(address aaveAdmin) external override onlyOwner {
    _addresses[AAVE_ADMIN] = aaveAdmin;
    emit AaveAdminUpdated(aaveAdmin);
  }

  function getPriceOracle() external override view returns (address) {
    return _addresses[PRICE_ORACLE];
  }

  function setPriceOracle(address priceOracle) external override onlyOwner {
    _addresses[PRICE_ORACLE] = priceOracle;
    emit PriceOracleUpdated(priceOracle);
  }

  function getLendingRateOracle() external override view returns (address) {
    return _addresses[LENDING_RATE_ORACLE];
  }

  function setLendingRateOracle(address lendingRateOracle) external override onlyOwner {
    _addresses[LENDING_RATE_ORACLE] = lendingRateOracle;
    emit LendingRateOracleUpdated(lendingRateOracle);
  }

  /**
   * @dev internal function to update the implementation of a specific component of the protocol
   * @param id the id of the contract to be updated
   * @param newAddress the address of the new implementation
   **/
  function _updateImpl(bytes32 id, address newAddress) internal {
    address payable proxyAddress = payable(_addresses[id]);

    InitializableAdminUpgradeabilityProxy proxy = InitializableAdminUpgradeabilityProxy(
      proxyAddress
    );
    bytes memory params = abi.encodeWithSignature('initialize(address)', address(this));

    if (proxyAddress == address(0)) {
      proxy = new InitializableAdminUpgradeabilityProxy();
      proxy.initialize(newAddress, address(this), params);
      _addresses[id] = address(proxy);
      emit ProxyCreated(id, address(proxy));
    } else {
      proxy.upgradeToAndCall(newAddress, params);
    }
  }
}





















/**
 * @title Errors library
 * @author Aave
 * @notice Implements error messages.
 */
/* Duplicate library Errors removed */                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    


/**
 * @title WadRayMath library
 * @author Aave
 * @dev Provides mul and div function for wads (decimal numbers with 18 digits precision) and rays (decimals with 27 digits)
 **/

library WadRayMath {
  uint256 internal constant WAD = 1e18;
  uint256 internal constant halfWAD = WAD / 2;

  uint256 internal constant RAY = 1e27;
  uint256 internal constant halfRAY = RAY / 2;

  uint256 internal constant WAD_RAY_RATIO = 1e9;

  /**
   * @return one ray, 1e27
   **/
  function ray() internal pure returns (uint256) {
    return RAY;
  }

  /**
   * @return one wad, 1e18
   **/

  function wad() internal pure returns (uint256) {
    return WAD;
  }

  /**
   * @return half ray, 1e27/2
   **/
  function halfRay() internal pure returns (uint256) {
    return halfRAY;
  }

  /**
   * @return half ray, 1e18/2
   **/
  function halfWad() internal pure returns (uint256) {
    return halfWAD;
  }

  /**
   * @dev multiplies two wad, rounding half up to the nearest wad
   * @param a wad
   * @param b wad
   * @return the result of a*b, in wad
   **/
  function wadMul(uint256 a, uint256 b) internal pure returns (uint256) {
    if (a == 0) {
      return 0;
    }

    uint256 result = a * b;

    require(result / a == b, Errors.MULTIPLICATION_OVERFLOW);

    result += halfWAD;

    require(result >= halfWAD, Errors.ADDITION_OVERFLOW);

    return result / WAD;
  }

  /**
   * @dev divides two wad, rounding half up to the nearest wad
   * @param a wad
   * @param b wad
   * @return the result of a/b, in wad
   **/
  function wadDiv(uint256 a, uint256 b) internal pure returns (uint256) {
    require(b != 0, Errors.DIVISION_BY_ZERO);

    uint256 halfB = b / 2;

    uint256 result = a * WAD;

    require(result / WAD == a, Errors.MULTIPLICATION_OVERFLOW);

    result += halfB;

    require(result >= halfB, Errors.ADDITION_OVERFLOW);

    return result / b;
  }

  /**
   * @dev multiplies two ray, rounding half up to the nearest ray
   * @param a ray
   * @param b ray
   * @return the result of a*b, in ray
   **/
  function rayMul(uint256 a, uint256 b) internal pure returns (uint256) {
    if (a == 0) {
      return 0;
    }

    uint256 result = a * b;

    require(result / a == b, Errors.MULTIPLICATION_OVERFLOW);

    result += halfRAY;

    require(result >= halfRAY, Errors.ADDITION_OVERFLOW);

    return result / RAY;
  }

  /**
   * @dev divides two ray, rounding half up to the nearest ray
   * @param a ray
   * @param b ray
   * @return the result of a/b, in ray
   **/
  function rayDiv(uint256 a, uint256 b) internal pure returns (uint256) {
    require(b != 0, Errors.DIVISION_BY_ZERO);

    uint256 halfB = b / 2;

    uint256 result = a * RAY;

    require(result / RAY == a, Errors.MULTIPLICATION_OVERFLOW);

    result += halfB;

    require(result >= halfB, Errors.ADDITION_OVERFLOW);

    return result / b;
  }

  /**
   * @dev casts ray down to wad
   * @param a ray
   * @return a casted to wad, rounded half up to the nearest wad
   **/
  function rayToWad(uint256 a) internal pure returns (uint256) {
    uint256 halfRatio = WAD_RAY_RATIO / 2;
    uint256 result = halfRatio + a;
    require(result >= halfRatio, Errors.ADDITION_OVERFLOW);

    return result / WAD_RAY_RATIO;
  }

  /**
   * @dev convert wad up to ray
   * @param a wad
   * @return a converted in ray
   **/
  function wadToRay(uint256 a) internal pure returns (uint256) {
    uint256 result = a * WAD_RAY_RATIO;
    require(result / WAD_RAY_RATIO == a, Errors.MULTIPLICATION_OVERFLOW);
    return result;
  }
}


library MathUtils {
  using SafeMath for uint256;
  using WadRayMath for uint256;

  uint256 internal constant SECONDS_PER_YEAR = 365 days;

  /**
   * @dev function to calculate the interest using a linear interest rate formula
   * @param rate the interest rate, in ray
   * @param lastUpdateTimestamp the timestamp of the last update of the interest
   * @return the interest rate linearly accumulated during the timeDelta, in ray
   **/

  function calculateLinearInterest(uint256 rate, uint40 lastUpdateTimestamp)
    internal
    view
    returns (uint256)
  {
    //solium-disable-next-line
    uint256 timeDifference = block.timestamp.sub(uint256(lastUpdateTimestamp));

    uint256 timeDelta = timeDifference.wadToRay().rayDiv(SECONDS_PER_YEAR.wadToRay());

    return rate.rayMul(timeDelta).add(WadRayMath.ray());
  }

  /**
   * @dev function to calculate the interest using a compounded interest rate formula.
   * To avoid expensive exponentiation, the calculation is performed using a binomial approximation:
   *
   *  (1+x)^n = 1+n*x+[n/2*(n-1)]*x^2+[n/6*(n-1)*(n-2)*x^3...
   *
   * The approximation slightly underpays liquidity providers, with the advantage of great gas cost reductions.
   * The whitepaper contains reference to the approximation and a table showing the margin of error per different time periods.
   *
   * @param rate the interest rate, in ray
   * @param lastUpdateTimestamp the timestamp of the last update of the interest
   * @return the interest rate compounded during the timeDelta, in ray
   **/
  function calculateCompoundedInterest(uint256 rate, uint40 lastUpdateTimestamp)
    internal
    view
    returns (uint256)
  {
    //solium-disable-next-line
    uint256 exp = block.timestamp.sub(uint256(lastUpdateTimestamp));

    if (exp == 0) {
      return WadRayMath.ray();
    }

    uint256 expMinusOne = exp - 1;

    uint256 expMinusTwo = exp > 2 ? exp - 2 : 0;

    uint256 ratePerSecond = rate / SECONDS_PER_YEAR;

    uint256 basePowerTwo = ratePerSecond.rayMul(ratePerSecond);
    uint256 basePowerThree = basePowerTwo.rayMul(ratePerSecond);

    uint256 secondTerm = exp.mul(expMinusOne).mul(basePowerTwo) / 2;
    uint256 thirdTerm = exp.mul(expMinusOne).mul(expMinusTwo).mul(basePowerThree) / 6;

    return WadRayMath.ray().add(ratePerSecond.mul(exp)).add(secondTerm).add(thirdTerm);
  }
}




/**
 * @title IPriceOracleGetter interface
 * @notice Interface for the Aave price oracle.
 **/

interface IPriceOracleGetter {
  /**
   * @dev returns the asset price in ETH
   * @param asset the address of the asset
   * @return the ETH price of the asset
   **/
  function getAssetPrice(address asset) external view returns (uint256);
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
    using SafeMath for uint256;
    using Address for address;

    function safeTransfer(IERC20 token, address to, uint256 value) internal {
        _callOptionalReturn(token, abi.encodeWithSelector(token.transfer.selector, to, value));
    }

    function safeTransferFrom(IERC20 token, address from, address to, uint256 value) internal {
        _callOptionalReturn(token, abi.encodeWithSelector(token.transferFrom.selector, from, to, value));
    }

    /**
     * @dev Deprecated. This function has issues similar to the ones found in
     * {IERC20-approve}, and its usage is discouraged.
     *
     * Whenever possible, use {safeIncreaseAllowance} and
     * {safeDecreaseAllowance} instead.
     */
    function safeApprove(IERC20 token, address spender, uint256 value) internal {
        // safeApprove should only be called when setting an initial allowance,
        // or when resetting it to zero. To increase and decrease it, use
        // 'safeIncreaseAllowance' and 'safeDecreaseAllowance'
        // solhint-disable-next-line max-line-length
        require((value == 0) || (token.allowance(address(this), spender) == 0),
            "SafeERC20: approve from non-zero to non-zero allowance"
        );
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, value));
    }

    function safeIncreaseAllowance(IERC20 token, address spender, uint256 value) internal {
        uint256 newAllowance = token.allowance(address(this), spender).add(value);
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, newAllowance));
    }

    function safeDecreaseAllowance(IERC20 token, address spender, uint256 value) internal {
        uint256 newAllowance = token.allowance(address(this), spender).sub(value, "SafeERC20: decreased allowance below zero");
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, newAllowance));
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
        if (returndata.length > 0) { // Return data is optional
            // solhint-disable-next-line max-line-length
            require(abi.decode(returndata, (bool)), "SafeERC20: ERC20 operation did not succeed");
        }
    }
}





/**
 * @title interface IStableDebtToken
 *
 * @notice defines the interface for the stable debt token
 *
 * @dev it does not inherit from IERC20 to save in code size
 *
 * @author Aave
 *
 **/

interface IStableDebtToken {
  /**
   * @dev emitted when new stable debt is minted
   * @param user the address of the user
   * @param amount the amount minted
   * @param previousBalance the previous balance of the user
   * @param currentBalance the current balance of the user
   * @param balanceIncrease the debt increase since the last update
   * @param newRate the rate of the debt after the minting
   **/
  event MintDebt(
    address user,
    uint256 amount,
    uint256 previousBalance,
    uint256 currentBalance,
    uint256 balanceIncrease,
    uint256 newRate
  );

  /**
   * @dev emitted when new stable debt is burned
   * @param user the address of the user
   * @param amount the amount minted
   * @param previousBalance the previous balance of the user
   * @param currentBalance the current balance of the user
   * @param balanceIncrease the debt increase since the last update
   **/
  event BurnDebt(
    address user,
    uint256 amount,
    uint256 previousBalance,
    uint256 currentBalance,
    uint256 balanceIncrease
  );

  /**
   * @dev mints debt token to the target user. The resulting rate is the weighted average
   * between the rate of the new debt and the rate of the previous debt
   * @param user the address of the user
   * @param amount the amount of debt tokens to mint
   * @param rate the rate of the debt being minted.
   **/
  function mint(
    address user,
    uint256 amount,
    uint256 rate
  ) external;

  /**
   * @dev burns debt of the target user.
   * @param user the address of the user
   * @param amount the amount of debt tokens to mint
   **/
  function burn(address user, uint256 amount) external;

  /**
   * @dev returns the average rate of all the stable rate loans.
   * @return the average stable rate
   **/
  function getAverageStableRate() external view returns (uint256);

  /**
   * @dev returns the stable rate of the user debt
   * @return the stable rate of the user
   **/
  function getUserStableRate(address user) external view returns (uint256);

  /**
   * @dev returns the timestamp of the last update of the user
   * @return the timestamp
   **/
  function getUserLastUpdated(address user) external view returns (uint40);

  /**
   * @dev returns the principal, the total supply and the average stable rate
   **/
  function getSupplyData() external view returns (uint256, uint256, uint256, uint40);

  /**
   * @dev returns the timestamp of the last update of the total supply
   * @return the timestamp
   **/
  function getTotalSupplyLastUpdated() external view returns (uint40);

  /**
   * @dev returns the total supply and the average stable rate
   **/
  function getTotalSupplyAndAvgRate() external view returns (uint256, uint256);

  /**
   * @dev Returns the principal debt balance of the user
   * @return The debt balance of the user since the last burn/mint action
   **/
  function principalBalanceOf(address user) external view returns (uint256);
}






/**
 * @title interface IVariableDebtToken
 * @author Aave
 * @notice defines the basic interface for a variable debt token.
 **/
interface IVariableDebtToken is IScaledBalanceToken {  
  
  /**
   * @dev emitted when variable debt is burnt
   * @param user the user which debt has been burned
   * @param amount the amount of debt being burned
   * @param index the index of the user
   **/
  event Burn(
    address indexed user,
    uint256 amount,
    uint256 index
  );

    /**
   * @dev burns user variable debt
   * @param user the user which debt is burnt
   * @param index the variable debt index of the reserve
   **/
  function burn(
    address user,
    uint256 amount,
    uint256 index
  ) external;
 
}





/**
@title IReserveInterestRateStrategyInterface interface
@notice Interface for the calculation of the interest rates.
*/

interface IReserveInterestRateStrategy {
  /**
   * @dev returns the base variable borrow rate, in rays
   */
  function baseVariableBorrowRate() external view returns (uint256);

  /**
   * @dev returns the maximum variable borrow rate
   */
  function getMaxVariableBorrowRate() external view returns (uint256);

  /**
   * @dev calculates the liquidity, stable, and variable rates depending on the current utilization rate
   *      and the base parameters
   *
   */
  function calculateInterestRates(
    address reserve,
    uint256 utilizationRate,
    uint256 totalStableDebt,
    uint256 totalVariableDebt,
    uint256 averageStableBorrowRate,
    uint256 reserveFactor
  )
    external
    view
    returns (
      uint256 liquidityRate,
      uint256 stableBorrowRate,
      uint256 variableBorrowRate
    );
}







/**
 * @title PercentageMath library
 * @author Aave
 * @notice Provides functions to calculate percentages.
 * @dev Percentages are defined by default with 2 decimals of precision (100.00). The precision is indicated by PERCENTAGE_FACTOR
 * @dev Operations are rounded half up
 **/

library PercentageMath {
  uint256 constant PERCENTAGE_FACTOR = 1e4; //percentage plus two decimals
  uint256 constant HALF_PERCENT = PERCENTAGE_FACTOR / 2;

  /**
   * @dev executes a percentage multiplication
   * @param value the value of which the percentage needs to be calculated
   * @param percentage the percentage of the value to be calculated
   * @return the percentage of value
   **/
  function percentMul(uint256 value, uint256 percentage) internal pure returns (uint256) {
    if (value == 0) {
      return 0;
    }

    uint256 result = value * percentage;

    require(result / value == percentage, Errors.MULTIPLICATION_OVERFLOW);

    result += HALF_PERCENT;

    require(result >= HALF_PERCENT, Errors.ADDITION_OVERFLOW);

    return result / PERCENTAGE_FACTOR;
  }

  /**
   * @dev executes a percentage division
   * @param value the value of which the percentage needs to be calculated
   * @param percentage the percentage of the value to be calculated
   * @return the value divided the percentage
   **/
  function percentDiv(uint256 value, uint256 percentage) internal pure returns (uint256) {
    require(percentage != 0, Errors.DIVISION_BY_ZERO);
    uint256 halfPercentage = percentage / 2;

    uint256 result = value * PERCENTAGE_FACTOR;

    require(result / PERCENTAGE_FACTOR == value, Errors.MULTIPLICATION_OVERFLOW);

    result += halfPercentage;

    require(result >= halfPercentage, Errors.ADDITION_OVERFLOW);

    return result / percentage;
  }
}



/**
 * @title ReserveLogic library
 * @author Aave
 * @notice Implements the logic to update the state of the reserves
 */
library ReserveLogic {
  using SafeMath for uint256;
  using WadRayMath for uint256;
  using PercentageMath for uint256;
  using SafeERC20 for IERC20;

  /**
   * @dev Emitted when the state of a reserve is updated
   * @param reserve the address of the reserve
   * @param liquidityRate the new liquidity rate
   * @param stableBorrowRate the new stable borrow rate
   * @param variableBorrowRate the new variable borrow rate
   * @param liquidityIndex the new liquidity index
   * @param variableBorrowIndex the new variable borrow index
   **/
  event ReserveDataUpdated(
    address indexed reserve,
    uint256 liquidityRate,
    uint256 stableBorrowRate,
    uint256 variableBorrowRate,
    uint256 liquidityIndex,
    uint256 variableBorrowIndex
  );

  using ReserveLogic for ReserveLogic.ReserveData;
  using ReserveConfiguration for ReserveConfiguration.Map;

  enum InterestRateMode {NONE, STABLE, VARIABLE}

  // refer to the whitepaper, section 1.1 basic concepts for a formal description of these properties.
  struct ReserveData {
    //stores the reserve configuration
    ReserveConfiguration.Map configuration;
    //the liquidity index. Expressed in ray
    uint128 liquidityIndex;
    //variable borrow index. Expressed in ray
    uint128 variableBorrowIndex;
    //the current supply rate. Expressed in ray
    uint128 currentLiquidityRate;
    //the current variable borrow rate. Expressed in ray
    uint128 currentVariableBorrowRate;
    //the current stable borrow rate. Expressed in ray
    uint128 currentStableBorrowRate;
    uint40 lastUpdateTimestamp;
    //tokens addresses
    address aTokenAddress;
    address stableDebtTokenAddress;
    address variableDebtTokenAddress;
    //address of the interest rate strategy
    address interestRateStrategyAddress;
    //the id of the reserve. Represents the position in the list of the active reserves
    uint8 id;
  }

  /**
   * @dev returns the ongoing normalized income for the reserve.
   * a value of 1e27 means there is no income. As time passes, the income is accrued.
   * A value of 2*1e27 means for each unit of assset two units of income have been accrued.
   * @param reserve the reserve object
   * @return the normalized income. expressed in ray
   **/
  function getNormalizedIncome(ReserveData storage reserve) internal view returns (uint256) {
    uint40 timestamp = reserve.lastUpdateTimestamp;

    //solium-disable-next-line
    if (timestamp == uint40(block.timestamp)) {
      //if the index was updated in the same block, no need to perform any calculation
      return reserve.liquidityIndex;
    }

    uint256 cumulated = MathUtils
      .calculateLinearInterest(reserve.currentLiquidityRate, timestamp)
      .rayMul(reserve.liquidityIndex);

    return cumulated;
  }

  /**
   * @dev returns the ongoing normalized variable debt for the reserve.
   * a value of 1e27 means there is no debt. As time passes, the income is accrued.
   * A value of 2*1e27 means that the debt of the reserve is double the initial amount.
   * @param reserve the reserve object
   * @return the normalized variable debt. expressed in ray
   **/
  function getNormalizedDebt(ReserveData storage reserve) internal view returns (uint256) {
    uint40 timestamp = reserve.lastUpdateTimestamp;

    //solium-disable-next-line
    if (timestamp == uint40(block.timestamp)) {
      //if the index was updated in the same block, no need to perform any calculation
      return reserve.variableBorrowIndex;
    }

    uint256 cumulated = MathUtils
      .calculateCompoundedInterest(reserve.currentVariableBorrowRate, timestamp)
      .rayMul(reserve.variableBorrowIndex);

    return cumulated;
  }

  /**
   * @dev returns an address of the debt token used for particular interest rate mode on asset.
   * @param reserve the reserve object
   * @param interestRateMode - STABLE or VARIABLE from ReserveLogic.InterestRateMode enum
   * @return an address of the corresponding debt token from reserve configuration
   **/
  function getDebtTokenAddress(ReserveLogic.ReserveData storage reserve, uint256 interestRateMode)
    external
    view
    returns (address)
  {
    require(
      ReserveLogic.InterestRateMode.STABLE == ReserveLogic.InterestRateMode(interestRateMode) ||
        ReserveLogic.InterestRateMode.VARIABLE == ReserveLogic.InterestRateMode(interestRateMode),
      Errors.INVALID_INTEREST_RATE_MODE_SELECTED
    );
    return
      ReserveLogic.InterestRateMode.STABLE == ReserveLogic.InterestRateMode(interestRateMode)
        ? reserve.stableDebtTokenAddress
        : reserve.variableDebtTokenAddress;
  }

  /**
   * @dev Updates the liquidity cumulative index Ci and variable borrow cumulative index Bvc. Refer to the whitepaper for
   * a formal specification.
   * @param reserve the reserve object
   **/
  function updateState(ReserveData storage reserve) external {
    address variableDebtToken = reserve.variableDebtTokenAddress;
    uint256 previousVariableBorrowIndex = reserve.variableBorrowIndex;
    uint256 previousLiquidityIndex = reserve.liquidityIndex;

    (uint256 newLiquidityIndex, uint256 newVariableBorrowIndex) = _updateIndexes(
      reserve,
      variableDebtToken,
      previousLiquidityIndex,
      previousVariableBorrowIndex
    );

    _mintToTreasury(
      reserve,
      variableDebtToken,
      previousVariableBorrowIndex,
      newLiquidityIndex,
      newVariableBorrowIndex
    );
  }

  /**
   * @dev accumulates a predefined amount of asset to the reserve as a fixed, one time income. Used for example to accumulate
   * the flashloan fee to the reserve, and spread it through the depositors.
   * @param reserve the reserve object
   * @param totalLiquidity the total liquidity available in the reserve
   * @param amount the amount to accomulate
   **/
  function cumulateToLiquidityIndex(
    ReserveData storage reserve,
    uint256 totalLiquidity,
    uint256 amount
  ) external {
    uint256 amountToLiquidityRatio = amount.wadToRay().rayDiv(totalLiquidity.wadToRay());

    uint256 result = amountToLiquidityRatio.add(WadRayMath.ray());

    result = result.rayMul(reserve.liquidityIndex);
    require(result < (1 << 128), Errors.LIQUIDITY_INDEX_OVERFLOW);

    reserve.liquidityIndex = uint128(result);
  }

  /**
   * @dev initializes a reserve
   * @param reserve the reserve object
   * @param aTokenAddress the address of the overlying atoken contract
   * @param interestRateStrategyAddress the address of the interest rate strategy contract
   **/
  function init(
    ReserveData storage reserve,
    address aTokenAddress,
    address stableDebtTokenAddress,
    address variableDebtTokenAddress,
    address interestRateStrategyAddress
  ) external {
    require(reserve.aTokenAddress == address(0), Errors.RESERVE_ALREADY_INITIALIZED);
    if (reserve.liquidityIndex == 0) {
      //if the reserve has not been initialized yet
      reserve.liquidityIndex = uint128(WadRayMath.ray());
    }

    if (reserve.variableBorrowIndex == 0) {
      reserve.variableBorrowIndex = uint128(WadRayMath.ray());
    }

    reserve.aTokenAddress = aTokenAddress;
    reserve.stableDebtTokenAddress = stableDebtTokenAddress;
    reserve.variableDebtTokenAddress = variableDebtTokenAddress;
    reserve.interestRateStrategyAddress = interestRateStrategyAddress;
  }

  struct UpdateInterestRatesLocalVars {
    address stableDebtTokenAddress;
    uint256 availableLiquidity;
    uint256 totalStableDebt;
    uint256 newLiquidityRate;
    uint256 newStableRate;
    uint256 newVariableRate;
    uint256 avgStableRate;
  }

  /**
   * @dev Updates the reserve current stable borrow rate Rf, the current variable borrow rate Rv and the current liquidity rate Rl.
   * Also updates the lastUpdateTimestamp value. Please refer to the whitepaper for further information.
   * @param reserve the address of the reserve to be updated
   * @param liquidityAdded the amount of liquidity added to the protocol (deposit or repay) in the previous action
   * @param liquidityTaken the amount of liquidity taken from the protocol (redeem or borrow)
   **/
  function updateInterestRates(
    ReserveData storage reserve,
    address reserveAddress,
    address aTokenAddress,
    uint256 liquidityAdded,
    uint256 liquidityTaken
  ) external {
    UpdateInterestRatesLocalVars memory vars;

    vars.stableDebtTokenAddress = reserve.stableDebtTokenAddress;

    (vars.totalStableDebt, vars.avgStableRate) = IStableDebtToken(vars.stableDebtTokenAddress)
      .getTotalSupplyAndAvgRate();

    vars.availableLiquidity = IERC20(reserveAddress).balanceOf(aTokenAddress);

    (
      vars.newLiquidityRate,
      vars.newStableRate,
      vars.newVariableRate
    ) = IReserveInterestRateStrategy(reserve.interestRateStrategyAddress).calculateInterestRates(
      reserveAddress,
      vars.availableLiquidity.add(liquidityAdded).sub(liquidityTaken),
      vars.totalStableDebt,
      IERC20(reserve.variableDebtTokenAddress).totalSupply(),
      vars.avgStableRate,
      reserve.configuration.getReserveFactor()
    );
    require(vars.newLiquidityRate < (1 << 128), 'ReserveLogic: Liquidity rate overflow');
    require(vars.newStableRate < (1 << 128), 'ReserveLogic: Stable borrow rate overflow');
    require(vars.newVariableRate < (1 << 128), 'ReserveLogic: Variable borrow rate overflow');

    reserve.currentLiquidityRate = uint128(vars.newLiquidityRate);
    reserve.currentStableBorrowRate = uint128(vars.newStableRate);
    reserve.currentVariableBorrowRate = uint128(vars.newVariableRate);

    emit ReserveDataUpdated(
      reserveAddress,
      vars.newLiquidityRate,
      vars.newStableRate,
      vars.newVariableRate,
      reserve.liquidityIndex,
      reserve.variableBorrowIndex
    );
  }

  struct MintToTreasuryLocalVars {
    uint256 currentStableDebt;
    uint256 principalStableDebt;
    uint256 previousStableDebt;
    uint256 currentVariableDebt;
    uint256 scaledVariableDebt;
    uint256 previousVariableDebt;
    uint256 avgStableRate;
    uint256 cumulatedStableInterest;
    uint256 totalDebtAccrued;
    uint256 amountToMint;
    uint256 reserveFactor;
    uint40 stableSupplyUpdatedTimestamp;
  }

  /**
   * @dev mints part of the repaid interest to the reserve treasury, depending on the reserveFactor for the
   * specific asset.
   * @param reserve the reserve reserve to be updated
   * @param variableDebtToken the debt token address
   * @param previousVariableBorrowIndex the variable borrow index before the last accumulation of the interest
   * @param newLiquidityIndex the new liquidity index
   * @param newVariableBorrowIndex the variable borrow index after the last accumulation of the interest
   **/
  function _mintToTreasury(
    ReserveData storage reserve,
    address variableDebtToken,
    uint256 previousVariableBorrowIndex,
    uint256 newLiquidityIndex,
    uint256 newVariableBorrowIndex
  ) internal {
    MintToTreasuryLocalVars memory vars;

    vars.reserveFactor = reserve.configuration.getReserveFactor();

    if (vars.reserveFactor == 0) {
      return;
    }

    //fetching the last scaled total variable debt
    vars.scaledVariableDebt = IVariableDebtToken(variableDebtToken).scaledTotalSupply();

    //fetching the principal, total stable debt and the avg stable rate
    (
      vars.principalStableDebt,
      vars.currentStableDebt,
      vars.avgStableRate,
      vars.stableSupplyUpdatedTimestamp
    ) = IStableDebtToken(reserve.stableDebtTokenAddress).getSupplyData();

    //calculate the last principal variable debt
    vars.previousVariableDebt = vars.scaledVariableDebt.rayMul(previousVariableBorrowIndex);

    //calculate the new total supply after accumulation of the index
    vars.currentVariableDebt = vars.scaledVariableDebt.rayMul(newVariableBorrowIndex);

    //calculate the stable debt until the last timestamp update
    vars.cumulatedStableInterest = MathUtils.calculateCompoundedInterest(
      vars.avgStableRate,
      vars.stableSupplyUpdatedTimestamp
    );

    vars.previousStableDebt = vars.principalStableDebt.rayMul(vars.cumulatedStableInterest);

    //debt accrued is the sum of the current debt minus the sum of the debt at the last update
    vars.totalDebtAccrued = vars
      .currentVariableDebt
      .add(vars.currentStableDebt)
      .sub(vars.previousVariableDebt)
      .sub(vars.previousStableDebt);

    vars.amountToMint = vars.totalDebtAccrued.percentMul(vars.reserveFactor);

    IAToken(reserve.aTokenAddress).mintToTreasury(vars.amountToMint, newLiquidityIndex);
  }

  /**
   * @dev updates the reserve indexes and the timestamp of the update
   * @param reserve the reserve reserve to be updated
   * @param variableDebtToken the debt token address
   * @param liquidityIndex the last stored liquidity index
   * @param variableBorrowIndex the last stored variable borrow index
   **/
  function _updateIndexes(
    ReserveData storage reserve,
    address variableDebtToken,
    uint256 liquidityIndex,
    uint256 variableBorrowIndex
  ) internal returns (uint256, uint256) {
    uint40 timestamp = reserve.lastUpdateTimestamp;

    uint256 currentLiquidityRate = reserve.currentLiquidityRate;

    uint256 newLiquidityIndex = liquidityIndex;
    uint256 newVariableBorrowIndex = variableBorrowIndex;

    //only cumulating if there is any income being produced
    if (currentLiquidityRate > 0) {
      uint256 cumulatedLiquidityInterest = MathUtils.calculateLinearInterest(
        currentLiquidityRate,
        timestamp
      );
      newLiquidityIndex = cumulatedLiquidityInterest.rayMul(liquidityIndex);
      require(newLiquidityIndex < (1 << 128), Errors.LIQUIDITY_INDEX_OVERFLOW);

      reserve.liquidityIndex = uint128(newLiquidityIndex);

      //as the liquidity rate might come only from stable rate loans, we need to ensure
      //that there is actual variable debt before accumulating
      if (IERC20(variableDebtToken).totalSupply() > 0) {
        uint256 cumulatedVariableBorrowInterest = MathUtils.calculateCompoundedInterest(
          reserve.currentVariableBorrowRate,
          timestamp
        );
        newVariableBorrowIndex = cumulatedVariableBorrowInterest.rayMul(variableBorrowIndex);
        require(newVariableBorrowIndex < (1 << 128), Errors.VARIABLE_BORROW_INDEX_OVERFLOW);
        reserve.variableBorrowIndex = uint128(newVariableBorrowIndex);
      }
    }

    //solium-disable-next-line
    reserve.lastUpdateTimestamp = uint40(block.timestamp);
    return (newLiquidityIndex, newVariableBorrowIndex);
  }
}




/**
 * @title ReserveConfiguration library
 * @author Aave
 * @notice Implements the bitmap logic to handle the reserve configuration
 */
library ReserveConfiguration {
  uint256 constant LTV_MASK = 0xFFFFFFFFFFFFFFFF0000;
  uint256 constant LIQUIDATION_THRESHOLD_MASK = 0xFFFFFFFFFFFF0000FFFF;
  uint256 constant LIQUIDATION_BONUS_MASK = 0xFFFFFFF0000FFFFFFFF;
  uint256 constant DECIMALS_MASK = 0xFFFFFF00FFFFFFFFFFFF;
  uint256 constant ACTIVE_MASK = 0xFFFFFEFFFFFFFFFFFFFF;
  uint256 constant FROZEN_MASK = 0xFFFFFDFFFFFFFFFFFFFF;
  uint256 constant BORROWING_MASK = 0xFFFFFBFFFFFFFFFFFFFF;
  uint256 constant STABLE_BORROWING_MASK = 0xFFFF07FFFFFFFFFFFFFF;
  uint256 constant RESERVE_FACTOR_MASK = 0xFFFFFFFFFFFFFFFF;

  struct Map {
    //bit 0-15: LTV
    //bit 16-31: Liq. threshold
    //bit 32-47: Liq. bonus
    //bit 48-55: Decimals
    //bit 56: Reserve is active
    //bit 57: reserve is freezed
    //bit 58: borrowing is enabled
    //bit 59: stable rate borrowing enabled
    //bit 64-79: reserve factor
    uint256 data;
  }

  /**
   * @dev sets the reserve factor of the reserve
   * @param self the reserve configuration
   * @param reserveFactor the reserve factor
   **/
  function setReserveFactor(ReserveConfiguration.Map memory self, uint256 reserveFactor) internal pure {
 
    self.data = (self.data & RESERVE_FACTOR_MASK) | reserveFactor << 64;
  }

  /**
   * @dev gets the reserve factor of the reserve
   * @param self the reserve configuration
   * @return the reserve factor
   **/
  function getReserveFactor(ReserveConfiguration.Map storage self) internal view returns (uint256) {
    return (self.data & ~RESERVE_FACTOR_MASK) >> 64;
  }
  /**
   * @dev sets the Loan to Value of the reserve
   * @param self the reserve configuration
   * @param ltv the new ltv
   **/
  function setLtv(ReserveConfiguration.Map memory self, uint256 ltv) internal pure {
    self.data = (self.data & LTV_MASK) | ltv;
  }

  /**
   * @dev gets the Loan to Value of the reserve
   * @param self the reserve configuration
   * @return the loan to value
   **/
  function getLtv(ReserveConfiguration.Map storage self) internal view returns (uint256) {
    return self.data & ~LTV_MASK;
  }

  /**
   * @dev sets the liquidation threshold of the reserve
   * @param self the reserve configuration
   * @param threshold the new liquidation threshold
   **/
  function setLiquidationThreshold(ReserveConfiguration.Map memory self, uint256 threshold)
    internal
    pure
  {
    self.data = (self.data & LIQUIDATION_THRESHOLD_MASK) | (threshold << 16);
  }

  /**
   * @dev gets the Loan to Value of the reserve
   * @param self the reserve configuration
   * @return the liquidation threshold
   **/
  function getLiquidationThreshold(ReserveConfiguration.Map storage self)
    internal
    view
    returns (uint256)
  {
    return (self.data & ~LIQUIDATION_THRESHOLD_MASK) >> 16;
  }

  /**
   * @dev sets the liquidation bonus of the reserve
   * @param self the reserve configuration
   * @param bonus the new liquidation bonus
   **/
  function setLiquidationBonus(ReserveConfiguration.Map memory self, uint256 bonus) internal pure {
    self.data = (self.data & LIQUIDATION_BONUS_MASK) | (bonus << 32);
  }

  /**
   * @dev gets the liquidation bonus of the reserve
   * @param self the reserve configuration
   * @return the liquidation bonus
   **/
  function getLiquidationBonus(ReserveConfiguration.Map storage self)
    internal
    view
    returns (uint256)
  {
    return (self.data & ~LIQUIDATION_BONUS_MASK) >> 32;
  }

  /**
   * @dev sets the decimals of the underlying asset of the reserve
   * @param self the reserve configuration
   * @param decimals the decimals
   **/
  function setDecimals(ReserveConfiguration.Map memory self, uint256 decimals) internal pure {
    self.data = (self.data & DECIMALS_MASK) | (decimals << 48);
  }

  /**
   * @dev gets the decimals of the underlying asset of the reserve
   * @param self the reserve configuration
   * @return the decimals of the asset
   **/
  function getDecimals(ReserveConfiguration.Map storage self) internal view returns (uint256) {
    return (self.data & ~DECIMALS_MASK) >> 48;
  }

  /**
   * @dev sets the active state of the reserve
   * @param self the reserve configuration
   * @param active the active state
   **/
  function setActive(ReserveConfiguration.Map memory self, bool active) internal pure {
    self.data = (self.data & ACTIVE_MASK) | (uint256(active ? 1 : 0) << 56);
  }

  /**
   * @dev gets the active state of the reserve
   * @param self the reserve configuration
   * @return the active state
   **/
  function getActive(ReserveConfiguration.Map storage self) internal view returns (bool) {
    return ((self.data & ~ACTIVE_MASK) >> 56) != 0;
  }

  /**
   * @dev sets the frozen state of the reserve
   * @param self the reserve configuration
   * @param frozen the frozen state
   **/
  function setFrozen(ReserveConfiguration.Map memory self, bool frozen) internal pure {
    self.data = (self.data & FROZEN_MASK) | (uint256(frozen ? 1 : 0) << 57);
  }

  /**
   * @dev gets the frozen state of the reserve
   * @param self the reserve configuration
   * @return the frozen state
   **/
  function getFrozen(ReserveConfiguration.Map storage self) internal view returns (bool) {
    return ((self.data & ~FROZEN_MASK) >> 57) != 0;
  }

  /**
   * @dev enables or disables borrowing on the reserve
   * @param self the reserve configuration
   * @param enabled true if the borrowing needs to be enabled, false otherwise
   **/
  function setBorrowingEnabled(ReserveConfiguration.Map memory self, bool enabled) internal pure {
    self.data = (self.data & BORROWING_MASK) | (uint256(enabled ? 1 : 0) << 58);
  }

  /**
   * @dev gets the borrowing state of the reserve
   * @param self the reserve configuration
   * @return the borrowing state
   **/
  function getBorrowingEnabled(ReserveConfiguration.Map storage self) internal view returns (bool) {
    return ((self.data & ~BORROWING_MASK) >> 58) != 0;
  }

  /**
   * @dev enables or disables stable rate borrowing on the reserve
   * @param self the reserve configuration
   * @param enabled true if the stable rate borrowing needs to be enabled, false otherwise
   **/
  function setStableRateBorrowingEnabled(ReserveConfiguration.Map memory self, bool enabled)
    internal pure
  {
    self.data = (self.data & STABLE_BORROWING_MASK) | (uint256(enabled ? 1 : 0) << 59);
  }

  /**
   * @dev gets the stable rate borrowing state of the reserve
   * @param self the reserve configuration
   * @return the stable rate borrowing state
   **/
  function getStableRateBorrowingEnabled(ReserveConfiguration.Map storage self)
    internal
    view
    returns (bool)
  {
    return ((self.data & ~STABLE_BORROWING_MASK) >> 59) != 0;
  }

  /**
   * @dev gets the configuration flags of the reserve
   * @param self the reserve configuration
   * @return the state flags representing active, freezed, borrowing enabled, stableRateBorrowing enabled
   **/
  function getFlags(ReserveConfiguration.Map storage self)
    internal
    view
    returns (
      bool,
      bool,
      bool,
      bool
    )
  {
    uint256 dataLocal = self.data;

    return (
      (dataLocal & ~ACTIVE_MASK) >> 56 != 0,
      (dataLocal & ~FROZEN_MASK) >> 57 != 0,
      (dataLocal & ~BORROWING_MASK) >> 58 != 0,
      (dataLocal & ~STABLE_BORROWING_MASK) >> 59 != 0
    );
  }

  /**
   * @dev gets the configuration paramters of the reserve
   * @param self the reserve configuration
   * @return the state params representing ltv, liquidation threshold, liquidation bonus, the reserve decimals
   **/
  function getParams(ReserveConfiguration.Map storage self)
    internal
    view
    returns (
      uint256,
      uint256,
      uint256,
      uint256
    )
  {
    uint256 dataLocal = self.data;

    return (
      dataLocal & ~LTV_MASK,
      (dataLocal & ~LIQUIDATION_THRESHOLD_MASK) >> 16,
      (dataLocal & ~LIQUIDATION_BONUS_MASK) >> 32,
      (dataLocal & ~DECIMALS_MASK) >> 48
    );
  }
}

pragma experimental ABIEncoderV2;

interface ILendingPool {
  /**
   * @dev emitted on deposit
   * @param reserve the address of the reserve
   * @param user the address of the user
   * @param amount the amount to be deposited
   * @param referral the referral number of the action
   **/
  event Deposit(
    address indexed reserve,
    address user,
    address indexed onBehalfOf,
    uint256 amount,
    uint16 indexed referral
  );

  /**
   * @dev emitted during a withdraw action.
   * @param reserve the address of the reserve
   * @param user the address of the user
   * @param amount the amount to be withdrawn
   **/
  event Withdraw(address indexed reserve, address indexed user, uint256 amount);

  event BorrowAllowanceDelegated(
    address indexed asset,
    address indexed fromUser,
    address indexed toUser,
    uint256 interestRateMode,
    uint256 amount
  );
  /**
   * @dev emitted on borrow
   * @param reserve the address of the reserve
   * @param user the address of the user
   * @param amount the amount to be deposited
   * @param borrowRateMode the rate mode, can be either 1-stable or 2-variable
   * @param borrowRate the rate at which the user has borrowed
   * @param referral the referral number of the action
   **/
  event Borrow(
    address indexed reserve,
    address user,
    address indexed onBehalfOf,
    uint256 amount,
    uint256 borrowRateMode,
    uint256 borrowRate,
    uint16 indexed referral
  );
  /**
   * @dev emitted on repay
   * @param reserve the address of the reserve
   * @param user the address of the user for which the repay has been executed
   * @param repayer the address of the user that has performed the repay action
   * @param amount the amount repaid
   **/
  event Repay(
    address indexed reserve,
    address indexed user,
    address indexed repayer,
    uint256 amount
  );
  /**
   * @dev emitted when a user performs a rate swap
   * @param reserve the address of the reserve
   * @param user the address of the user executing the swap
   **/
  event Swap(address indexed reserve, address indexed user);

  /**
   * @dev emitted when a user enables a reserve as collateral
   * @param reserve the address of the reserve
   * @param user the address of the user
   **/
  event ReserveUsedAsCollateralEnabled(address indexed reserve, address indexed user);

  /**
   * @dev emitted when a user disables a reserve as collateral
   * @param reserve the address of the reserve
   * @param user the address of the user
   **/
  event ReserveUsedAsCollateralDisabled(address indexed reserve, address indexed user);

  /**
   * @dev emitted when the stable rate of a user gets rebalanced
   * @param reserve the address of the reserve
   * @param user the address of the user for which the rebalance has been executed
   **/
  event RebalanceStableBorrowRate(address indexed reserve, address indexed user);
  /**
   * @dev emitted when a flashloan is executed
   * @param target the address of the flashLoanReceiver
   * @param reserve the address of the reserve
   * @param amount the amount requested
   * @param totalPremium the total fee on the amount
   * @param referralCode the referral code of the caller
   **/
  event FlashLoan(
    address indexed target,
    address indexed reserve,
    uint256 amount,
    uint256 totalPremium,
    uint16 referralCode
  );
  /**
   * @dev these events are not emitted directly by the LendingPool
   * but they are declared here as the LendingPoolCollateralManager
   * is executed using a delegateCall().
   * This allows to have the events in the generated ABI for LendingPool.
   **/

  /**
   * @dev emitted when a borrower is liquidated
   * @param collateral the address of the collateral being liquidated
   * @param reserve the address of the reserve
   * @param user the address of the user being liquidated
   * @param purchaseAmount the total amount liquidated
   * @param liquidatedCollateralAmount the amount of collateral being liquidated
   * @param accruedBorrowInterest the amount of interest accrued by the borrower since the last action
   * @param liquidator the address of the liquidator
   * @param receiveAToken true if the liquidator wants to receive aTokens, false otherwise
   **/
  event LiquidationCall(
    address indexed collateral,
    address indexed reserve,
    address indexed user,
    uint256 purchaseAmount,
    uint256 liquidatedCollateralAmount,
    uint256 accruedBorrowInterest,
    address liquidator,
    bool receiveAToken
  );
  /**
   * @dev Emitted when the pause is triggered.
   */
  event Paused();

  /**
   * @dev Emitted when the pause is lifted.
   */
  event Unpaused();

  /**
   * @dev deposits The underlying asset into the reserve. A corresponding amount of the overlying asset (aTokens)
   * is minted.
   * @param reserve the address of the reserve
   * @param amount the amount to be deposited
   * @param referralCode integrators are assigned a referral code and can potentially receive rewards.
   **/
  function deposit(
    address reserve,
    uint256 amount,
    address onBehalfOf,
    uint16 referralCode
  ) external;

  /**
   * @dev withdraws the assets of user.
   * @param reserve the address of the reserve
   * @param amount the underlying amount to be redeemed
   **/
  function withdraw(address reserve, uint256 amount) external;

  /**
   * @dev Sets allowance to borrow on a certain type of debt asset for a certain user address
   * @param asset The underlying asset of the debt token
   * @param user The user to give allowance to
   * @param interestRateMode Type of debt: 1 for stable, 2 for variable
   * @param amount Allowance amount to borrow
   **/
  function delegateBorrowAllowance(
    address asset,
    address user,
    uint256 interestRateMode,
    uint256 amount
  ) external;

  function getBorrowAllowance(
    address fromUser,
    address toUser,
    address asset,
    uint256 interestRateMode
  ) external view returns (uint256);

  /**
   * @dev Allows users to borrow a specific amount of the reserve currency, provided that the borrower
   * already deposited enough collateral.
   * @param reserve the address of the reserve
   * @param amount the amount to be borrowed
   * @param interestRateMode the interest rate mode at which the user wants to borrow. Can be 0 (STABLE) or 1 (VARIABLE)
   **/
  function borrow(
    address reserve,
    uint256 amount,
    uint256 interestRateMode,
    uint16 referralCode,
    address onBehalfOf
  ) external;

  /**
   * @notice repays a borrow on the specific reserve, for the specified amount (or for the whole amount, if uint256(-1) is specified).
   * @dev the target user is defined by onBehalfOf. If there is no repayment on behalf of another account,
   * onBehalfOf must be equal to msg.sender.
   * @param reserve the address of the reserve on which the user borrowed
   * @param amount the amount to repay, or uint256(-1) if the user wants to repay everything
   * @param onBehalfOf the address for which msg.sender is repaying.
   **/
  function repay(
    address reserve,
    uint256 amount,
    uint256 rateMode,
    address onBehalfOf
  ) external;

  /**
   * @dev borrowers can user this function to swap between stable and variable borrow rate modes.
   * @param reserve the address of the reserve on which the user borrowed
   * @param rateMode the rate mode that the user wants to swap
   **/
  function swapBorrowRateMode(address reserve, uint256 rateMode) external;

  /**
   * @dev rebalances the stable interest rate of a user if current liquidity rate > user stable rate.
   * this is regulated by Aave to ensure that the protocol is not abused, and the user is paying a fair
   * rate. Anyone can call this function.
   * @param reserve the address of the reserve
   * @param user the address of the user to be rebalanced
   **/
  function rebalanceStableBorrowRate(address reserve, address user) external;

  /**
   * @dev allows depositors to enable or disable a specific deposit as collateral.
   * @param reserve the address of the reserve
   * @param useAsCollateral true if the user wants to user the deposit as collateral, false otherwise.
   **/
  function setUserUseReserveAsCollateral(address reserve, bool useAsCollateral) external;

  /**
   * @dev users can invoke this function to liquidate an undercollateralized position.
   * @param reserve the address of the collateral to liquidated
   * @param reserve the address of the principal reserve
   * @param user the address of the borrower
   * @param purchaseAmount the amount of principal that the liquidator wants to repay
   * @param receiveAToken true if the liquidators wants to receive the aTokens, false if
   * he wants to receive the underlying asset directly
   **/
  function liquidationCall(
    address collateral,
    address reserve,
    address user,
    uint256 purchaseAmount,
    bool receiveAToken
  ) external;

  /**
   * @dev flashes the underlying collateral on an user to swap for the owed asset and repay
   * - Both the owner of the position and other liquidators can execute it
   * - The owner can repay with his collateral at any point, no matter the health factor
   * - Other liquidators can only use this function below 1 HF. To liquidate 50% of the debt > HF 0.98 or the whole below
   * @param collateral The address of the collateral asset
   * @param principal The address of the owed asset
   * @param user Address of the borrower
   * @param principalAmount Amount of the debt to repay. type(uint256).max to repay the maximum possible
   * @param receiver Address of the contract receiving the collateral to swap
   * @param params Variadic bytes param to pass with extra information to the receiver
   **/
  function repayWithCollateral(
    address collateral,
    address principal,
    address user,
    uint256 principalAmount,
    address receiver,
    bytes calldata params
  ) external;

  /**
   * @dev allows smartcontracts to access the liquidity of the pool within one transaction,
   * as long as the amount taken plus a fee is returned. NOTE There are security concerns for developers of flashloan receiver contracts
   * that must be kept into consideration. For further details please visit https://developers.aave.com
   * @param receiver The address of the contract receiving the funds. The receiver should implement the IFlashLoanReceiver interface.
   * @param reserve the address of the principal reserve
   * @param amount the amount requested for this flashloan
   * @param params a bytes array to be sent to the flashloan executor
   * @param referralCode the referral code of the caller
   **/
  function flashLoan(
    address receiver,
    address reserve,
    uint256 amount,
    uint256 debtType,
    bytes calldata params,
    uint16 referralCode
  ) external;

  /**
   * @dev Allows an user to release one of his assets deposited in the protocol, even if it is used as collateral, to swap for another.
   * - It's not possible to release one asset to swap for the same
   * @param receiverAddress The address of the contract receiving the funds. The receiver should implement the ISwapAdapter interface
   * @param fromAsset Asset to swap from
   * @param toAsset Asset to swap to
   * @param params a bytes array to be sent (if needed) to the receiver contract with extra data
   **/
  function swapLiquidity(
    address receiverAddress,
    address fromAsset,
    address toAsset,
    uint256 amountToSwap,
    bytes calldata params
  ) external;

  /**
   * @dev accessory functions to fetch data from the core contract
   **/

  function getReserveConfigurationData(address reserve)
    external
    view
    returns (
      uint256 decimals,
      uint256 ltv,
      uint256 liquidationThreshold,
      uint256 liquidationBonus,
      uint256 reserveFactor,
      address interestRateStrategyAddress,
      bool usageAsCollateralEnabled,
      bool borrowingEnabled,
      bool stableBorrowRateEnabled,
      bool isActive,
      bool isFreezed
    );

  function getReserveTokensAddresses(address reserve)
    external
    view
    returns (
      address aTokenAddress,
      address stableDebtTokenAddress,
      address variableDebtTokenAddress
    );

  function getReserveData(address reserve)
    external
    view
    returns (
      uint256 availableLiquidity,
      uint256 totalStableDebt,
      uint256 totalVariableDebt,
      uint256 liquidityRate,
      uint256 variableBorrowRate,
      uint256 stableBorrowRate,
      uint256 averageStableBorrowRate,
      uint256 liquidityIndex,
      uint256 variableBorrowIndex,
      uint40 lastUpdateTimestamp
    );

  function getUserAccountData(address user)
    external
    view
    returns (
      uint256 totalCollateralETH,
      uint256 totalBorrowsETH,
      uint256 availableBorrowsETH,
      uint256 currentLiquidationThreshold,
      uint256 ltv,
      uint256 healthFactor
    );

  function getUserReserveData(address reserve, address user)
    external
    view
    returns (
      uint256 currentATokenBalance,
      uint256 currentStableDebt,
      uint256 currentVariableDebt,
      uint256 principalStableDebt,
      uint256 scaledVariableDebt,
      uint256 stableBorrowRate,
      uint256 liquidityRate,
      uint40 stableRateLastUpdated,
      bool usageAsCollateralEnabled
    );

  /**
   * @dev initializes a reserve
   * @param reserve the address of the reserve
   * @param aTokenAddress the address of the overlying aToken contract
   * @param interestRateStrategyAddress the address of the interest rate strategy contract
   **/
  function initReserve(
    address reserve,
    address aTokenAddress,
    address stableDebtAddress,
    address variableDebtAddress,
    address interestRateStrategyAddress
  ) external;

  /**
   * @dev updates the address of the interest rate strategy contract
   * @param reserve the address of the reserve
   * @param rateStrategyAddress the address of the interest rate strategy contract
   **/

  function setReserveInterestRateStrategyAddress(address reserve, address rateStrategyAddress)
    external;

  function setConfiguration(address reserve, uint256 configuration) external;

  function getConfiguration(address reserve)
    external
    view
    returns (ReserveConfiguration.Map memory);

  function getReserveNormalizedIncome(address reserve) external view returns (uint256);

  function getReserveNormalizedVariableDebt(address reserve) external view returns (uint256);

  function balanceDecreaseAllowed(
    address reserve,
    address user,
    uint256 amount
  ) external view returns (bool);

  function getReserves() external view returns (address[] memory);

  /**
   * @dev Set the _pause state
   * @param val the boolean value to set the current pause state of LendingPool
   */
  function setPause(bool val) external;

  /**
   * @dev Returns if the LendingPool is paused
   */
  function paused() external view returns (bool);
}








/*
 * @dev Provides information about the current execution context, including the
 * sender of the transaction and its data. While these are generally available
 * via msg.sender and msg.data, they should not be accessed in such a direct
 * manner, since when dealing with GSN meta-transactions the account sending and
 * paying for execution may not be the actual sender (as far as an application
 * is concerned).
 *
 * This contract is only required for intermediate, library-like contracts.
 */
/* Duplicate abstract contract Context removed */                                                                                                                                                                                                                                                                                                                 







interface IERC20Detailed is IERC20 {
  function name() external view returns (string memory);

  function symbol() external view returns (string memory);

  function decimals() external view returns (uint8);
}




pragma experimental ABIEncoderV2;

interface IAaveIncentivesController {
  function handleAction(
    address user,
    uint256 userBalance,
    uint256 totalSupply
  ) external;
}


/**
 * @title ERC20
 * @notice Basic ERC20 implementation
 * @author Aave, inspired by the Openzeppelin ERC20 implementation
 **/
contract IncentivizedERC20 is Context, IERC20, IERC20Detailed {
  using SafeMath for uint256;

  IAaveIncentivesController internal immutable _incentivesController;

  mapping(address => uint256) internal _balances;

  mapping(address => mapping(address => uint256)) private _allowances;
  uint256 internal _totalSupply;
  string private _name;
  string private _symbol;
  uint8 private _decimals;

  constructor(
    string memory name,
    string memory symbol,
    uint8 decimals,
    address incentivesController
  ) public {
    _name = name;
    _symbol = symbol;
    _decimals = decimals;
    _incentivesController = IAaveIncentivesController(incentivesController);
  }

  /**
   * @return the name of the token
   **/
  function name() public override view returns (string memory) {
    return _name;
  }

  /**
   * @return the symbol of the token
   **/
  function symbol() public override view returns (string memory) {
    return _symbol;
  }

  /**
   * @return the decimals of the token
   **/
  function decimals() public override view returns (uint8) {
    return _decimals;
  }

  /**
   * @return the total supply of the token
   **/
  function totalSupply() public virtual override view returns (uint256) {
    return _totalSupply;
  }

  /**
   * @return the balance of the token
   **/
  function balanceOf(address account) public virtual override view returns (uint256) {
    return _balances[account];
  }

  /**
   * @dev executes a transfer of tokens from msg.sender to recipient
   * @param recipient the recipient of the tokens
   * @param amount the amount of tokens being transferred
   * @return true if the transfer succeeds, false otherwise
   **/
  function transfer(address recipient, uint256 amount) public virtual override returns (bool) {
    _transfer(_msgSender(), recipient, amount);
    emit Transfer(msg.sender, recipient, amount);
    return true;
  }

  /**
   * @dev returns the allowance of spender on the tokens owned by owner
   * @param owner the owner of the tokens
   * @param spender the user allowed to spend the owner's tokens
   * @return the amount of owner's tokens spender is allowed to spend
   **/
  function allowance(address owner, address spender)
    public
    virtual
    override
    view
    returns (uint256)
  {
    return _allowances[owner][spender];
  }

  /**
   * @dev allows spender to spend the tokens owned by msg.sender
   * @param spender the user allowed to spend msg.sender tokens
   * @return true
   **/
  function approve(address spender, uint256 amount) public virtual override returns (bool) {
    _approve(_msgSender(), spender, amount);
    return true;
  }

  /**
   * @dev executes a transfer of token from sender to recipient, if msg.sender is allowed to do so
   * @param sender the owner of the tokens
   * @param recipient the recipient of the tokens
   * @param amount the amount of tokens being transferred
   * @return true if the transfer succeeds, false otherwise
   **/
  function transferFrom(
    address sender,
    address recipient,
    uint256 amount
  ) public virtual override returns (bool) {
    _transfer(sender, recipient, amount);
    _approve(
      sender,
      _msgSender(),
      _allowances[sender][_msgSender()].sub(amount, 'ERC20: transfer amount exceeds allowance')
    );
    emit Transfer(sender, recipient, amount);
    return true;
  }

  /**
   * @dev increases the allowance of spender to spend msg.sender tokens
   * @param spender the user allowed to spend on behalf of msg.sender
   * @param addedValue the amount being added to the allowance
   * @return true
   **/
  function increaseAllowance(address spender, uint256 addedValue) public virtual returns (bool) {
    _approve(_msgSender(), spender, _allowances[_msgSender()][spender].add(addedValue));
    return true;
  }

  /**
   * @dev decreases the allowance of spender to spend msg.sender tokens
   * @param spender the user allowed to spend on behalf of msg.sender
   * @param subtractedValue the amount being subtracted to the allowance
   * @return true
   **/
  function decreaseAllowance(address spender, uint256 subtractedValue)
    public
    virtual
    returns (bool)
  {
    _approve(
      _msgSender(),
      spender,
      _allowances[_msgSender()][spender].sub(
        subtractedValue,
        'ERC20: decreased allowance below zero'
      )
    );
    return true;
  }

  function _transfer(
    address sender,
    address recipient,
    uint256 amount
  ) internal virtual {
    require(sender != address(0), 'ERC20: transfer from the zero address');
    require(recipient != address(0), 'ERC20: transfer to the zero address');

    _beforeTokenTransfer(sender, recipient, amount);

    uint256 oldSenderBalance = _balances[sender];
    _balances[sender] = oldSenderBalance.sub(amount, 'ERC20: transfer amount exceeds balance');
    uint256 oldRecipientBalance = _balances[recipient];
    _balances[recipient] = _balances[recipient].add(amount);

    if (address(_incentivesController) != address(0)) {
      uint256 totalSupply = _totalSupply;
      _incentivesController.handleAction(sender, totalSupply, oldSenderBalance);
      if (sender != recipient) {
        _incentivesController.handleAction(recipient, totalSupply, oldRecipientBalance);
      }
    }
  }

  function _mint(address account, uint256 amount) internal virtual {
    require(account != address(0), 'ERC20: mint to the zero address');

    _beforeTokenTransfer(address(0), account, amount);

    uint256 oldTotalSupply = _totalSupply;
    _totalSupply = oldTotalSupply.add(amount);

    uint256 oldAccountBalance = _balances[account];
    _balances[account] = oldAccountBalance.add(amount);

    if (address(_incentivesController) != address(0)) {
      _incentivesController.handleAction(account, oldTotalSupply, oldAccountBalance);
    }
  }

  function _burn(address account, uint256 amount) internal virtual {
    require(account != address(0), 'ERC20: burn from the zero address');

    _beforeTokenTransfer(account, address(0), amount);

    uint256 oldTotalSupply = _totalSupply;
    _totalSupply = oldTotalSupply.sub(amount);

    uint256 oldAccountBalance = _balances[account];
    _balances[account] = oldAccountBalance.sub(amount, 'ERC20: burn amount exceeds balance');

    if (address(_incentivesController) != address(0)) {
      _incentivesController.handleAction(account, oldTotalSupply, oldAccountBalance);
    }
  }

  function _approve(
    address owner,
    address spender,
    uint256 amount
  ) internal virtual {
    require(owner != address(0), 'ERC20: approve from the zero address');
    require(spender != address(0), 'ERC20: approve to the zero address');

    _allowances[owner][spender] = amount;
    emit Approval(owner, spender, amount);
  }

  function _setName(string memory newName) internal {
    _name = newName;
  }

  function _setSymbol(string memory newSymbol) internal {
    _symbol = newSymbol;
  }

  function _setDecimals(uint8 newDecimals) internal {
    _decimals = newDecimals;
  }

  function _beforeTokenTransfer(
    address from,
    address to,
    uint256 amount
  ) internal virtual {}
}



/**
 * @title DebtTokenBase
 * @notice Base contract for different types of debt tokens, like StableDebtToken or VariableDebtToken
 * @author Aave
 */

abstract contract DebtTokenBase is IncentivizedERC20, VersionedInitializable {
  address internal immutable UNDERLYING_ASSET;
  ILendingPool internal immutable POOL;
  mapping(address => uint256) internal _usersData;

  /**
   * @dev Only lending pool can call functions marked by this modifier
   **/
  modifier onlyLendingPool {
    require(msg.sender == address(POOL), Errors.CALLER_MUST_BE_LENDING_POOL);
    _;
  }

  /**
   * @dev The metadata of the token will be set on the proxy, that the reason of
   * passing "NULL" and 0 as metadata
   */
  constructor(
    address pool,
    address underlyingAssetAddress,
    string memory name,
    string memory symbol,
    address incentivesController
  ) public IncentivizedERC20(name, symbol, 18, incentivesController) {
    POOL = ILendingPool(pool);
    UNDERLYING_ASSET = underlyingAssetAddress;
  }

  /**
   * @dev Initializes the debt token.
   * @param name The name of the token
   * @param symbol The symbol of the token
   * @param decimals The decimals of the token
   */
  function initialize(
    uint8 decimals,
    string memory name,
    string memory symbol
  ) public initializer {
    _setName(name);
    _setSymbol(symbol);
    _setDecimals(decimals);
  }

  function underlyingAssetAddress() public view returns (address) {
    return UNDERLYING_ASSET;
  }

  /**
   * @dev Being non transferrable, the debt token does not implement any of the
   * standard ERC20 functions for transfer and allowance.
   **/
  function transfer(address recipient, uint256 amount) public virtual override returns (bool) {
    recipient;
    amount;
    revert('TRANSFER_NOT_SUPPORTED');
  }

  function allowance(address owner, address spender)
    public
    virtual
    override
    view
    returns (uint256)
  {
    owner;
    spender;
    revert('ALLOWANCE_NOT_SUPPORTED');
  }

  function approve(address spender, uint256 amount) public virtual override returns (bool) {
    spender;
    amount;
    revert('APPROVAL_NOT_SUPPORTED');
  }

  function transferFrom(
    address sender,
    address recipient,
    uint256 amount
  ) public virtual override returns (bool) {
    sender;
    recipient;
    amount;
    revert('TRANSFER_NOT_SUPPORTED');
  }

  function increaseAllowance(address spender, uint256 addedValue)
    public
    virtual
    override
    returns (bool)
  {
    spender;
    addedValue;
    revert('ALLOWANCE_NOT_SUPPORTED');
  }

  function decreaseAllowance(address spender, uint256 subtractedValue)
    public
    virtual
    override
    returns (bool)
  {
    spender;
    subtractedValue;
    revert('ALLOWANCE_NOT_SUPPORTED');
  }
}



/**
 * @title Helpers library
 * @author Aave
 * @notice Implements calculation helpers.
 */
library Helpers {
  /**
   * @dev fetches the user current stable and variable debt balances
   * @param user the user
   * @param reserve the reserve object
   * @return the stable and variable debt balance
   **/
  function getUserCurrentDebt(address user, ReserveLogic.ReserveData storage reserve)
    internal
    view
    returns (uint256, uint256)
  {
    return (
      DebtTokenBase(reserve.stableDebtTokenAddress).balanceOf(user),
      DebtTokenBase(reserve.variableDebtTokenAddress).balanceOf(user)
    );
  }
}







pragma experimental ABIEncoderV2;












/**
 * @title UserConfiguration library
 * @author Aave
 * @notice Implements the bitmap logic to handle the user configuration
 */
library UserConfiguration {
  uint256 internal constant BORROWING_MASK = 0x5555555555555555555555555555555555555555555555555555555555555555;

  struct Map {
    uint256 data;
  }

  /**
   * @dev sets if the user is borrowing the reserve identified by reserveIndex
   * @param self the configuration object
   * @param reserveIndex the index of the reserve in the bitmap
   * @param borrowing true if the user is borrowing the reserve, false otherwise
   **/
  function setBorrowing(
    UserConfiguration.Map storage self,
    uint256 reserveIndex,
    bool borrowing
  ) internal {
    self.data =
      (self.data & ~(1 << (reserveIndex * 2))) |
      (uint256(borrowing ? 1 : 0) << (reserveIndex * 2));
  }

  /**
   * @dev sets if the user is using as collateral the reserve identified by reserveIndex
   * @param self the configuration object
   * @param reserveIndex the index of the reserve in the bitmap
   * @param _usingAsCollateral true if the user is usin the reserve as collateral, false otherwise
   **/
  function setUsingAsCollateral(
    UserConfiguration.Map storage self,
    uint256 reserveIndex,
    bool _usingAsCollateral
  ) internal {
    self.data =
      (self.data & ~(1 << (reserveIndex * 2 + 1))) |
      (uint256(_usingAsCollateral ? 1 : 0) << (reserveIndex * 2 + 1));
  }

  /**
   * @dev used to validate if a user has been using the reserve for borrowing or as collateral
   * @param self the configuration object
   * @param reserveIndex the index of the reserve in the bitmap
   * @return true if the user has been using a reserve for borrowing or as collateral, false otherwise
   **/
  function isUsingAsCollateralOrBorrowing(UserConfiguration.Map memory self, uint256 reserveIndex)
    internal
    pure
    returns (bool)
  {
    return (self.data >> (reserveIndex * 2)) & 3 != 0;
  }

  /**
   * @dev used to validate if a user has been using the reserve for borrowing
   * @param self the configuration object
   * @param reserveIndex the index of the reserve in the bitmap
   * @return true if the user has been using a reserve for borrowing, false otherwise
   **/
  function isBorrowing(UserConfiguration.Map memory self, uint256 reserveIndex)
    internal
    pure
    returns (bool)
  {
    return (self.data >> (reserveIndex * 2)) & 1 != 0;
  }

  /**
   * @dev used to validate if a user has been using the reserve as collateral
   * @param self the configuration object
   * @param reserveIndex the index of the reserve in the bitmap
   * @return true if the user has been using a reserve as collateral, false otherwise
   **/
  function isUsingAsCollateral(UserConfiguration.Map memory self, uint256 reserveIndex)
    internal
    pure
    returns (bool)
  {
    return (self.data >> (reserveIndex * 2 + 1)) & 1 != 0;
  }

  /**
   * @dev used to validate if a user has been borrowing from any reserve
   * @param self the configuration object
   * @return true if the user has been borrowing any reserve, false otherwise
   **/
  function isBorrowingAny(UserConfiguration.Map memory self) internal pure returns (bool) {
    return self.data & BORROWING_MASK != 0;
  }

  /**
   * @dev used to validate if a user has not been using any reserve
   * @param self the configuration object
   * @return true if the user has been borrowing any reserve, false otherwise
   **/
  function isEmpty(UserConfiguration.Map memory self) internal pure returns (bool) {
    return self.data == 0;
  }
}





/**
 * @title GenericLogic library
 * @author Aave
 * @title Implements protocol-level logic to check the status of the user across all the reserves
 */
library GenericLogic {
  using ReserveLogic for ReserveLogic.ReserveData;
  using SafeMath for uint256;
  using WadRayMath for uint256;
  using PercentageMath for uint256;
  using ReserveConfiguration for ReserveConfiguration.Map;
  using UserConfiguration for UserConfiguration.Map;

  uint256 public constant HEALTH_FACTOR_LIQUIDATION_THRESHOLD = 1 ether;
  uint256 public constant HEALTH_FACTOR_CRITICAL_THRESHOLD = 0.98 ether;

  struct balanceDecreaseAllowedLocalVars {
    uint256 decimals;
    uint256 ltv;
    uint256 collateralBalanceETH;
    uint256 borrowBalanceETH;
    uint256 currentLiquidationThreshold;
    uint256 reserveLiquidationThreshold;
    uint256 amountToDecreaseETH;
    uint256 collateralBalancefterDecrease;
    uint256 liquidationThresholdAfterDecrease;
    uint256 healthFactorAfterDecrease;
    bool reserveUsageAsCollateralEnabled;
  }

  /**
   * @dev check if a specific balance decrease is allowed
   * (i.e. doesn't bring the user borrow position health factor under HEALTH_FACTOR_LIQUIDATION_THRESHOLD)
   * @param asset the address of the reserve
   * @param user the address of the user
   * @param amount the amount to decrease
   * @param reservesData the data of all the reserves
   * @param userConfig the user configuration
   * @param reserves the list of all the active reserves
   * @param oracle the address of the oracle contract
   * @return true if the decrease of the balance is allowed
   **/
  function balanceDecreaseAllowed(
    address asset,
    address user,
    uint256 amount,
    mapping(address => ReserveLogic.ReserveData) storage reservesData,
    UserConfiguration.Map calldata userConfig,
    address[] calldata reserves,
    address oracle
  ) external view returns (bool) {
    if (
      !userConfig.isBorrowingAny() ||
      !userConfig.isUsingAsCollateral(reservesData[asset].id)
    ) {
      return true;
    }

    balanceDecreaseAllowedLocalVars memory vars;

    (vars.ltv, , , vars.decimals) = reservesData[asset].configuration.getParams();

    if (vars.ltv == 0) {
      return true; //if reserve is not used as collateral, no reasons to block the transfer
    }

    (
      vars.collateralBalanceETH,
      vars.borrowBalanceETH,
      ,
      vars.currentLiquidationThreshold,

    ) = calculateUserAccountData(user, reservesData, userConfig, reserves, oracle);

    if (vars.borrowBalanceETH == 0) {
      return true; //no borrows - no reasons to block the transfer
    }

    vars.amountToDecreaseETH = IPriceOracleGetter(oracle).getAssetPrice(asset).mul(amount).div(
      10**vars.decimals
    );

    vars.collateralBalancefterDecrease = vars.collateralBalanceETH.sub(vars.amountToDecreaseETH);

    //if there is a borrow, there can't be 0 collateral
    if (vars.collateralBalancefterDecrease == 0) {
      return false;
    }

    vars.liquidationThresholdAfterDecrease = vars
      .collateralBalanceETH
      .mul(vars.currentLiquidationThreshold)
      .sub(vars.amountToDecreaseETH.mul(vars.reserveLiquidationThreshold))
      .div(vars.collateralBalancefterDecrease);

    uint256 healthFactorAfterDecrease = calculateHealthFactorFromBalances(
      vars.collateralBalancefterDecrease,
      vars.borrowBalanceETH,
      vars.liquidationThresholdAfterDecrease
    );

    return healthFactorAfterDecrease > GenericLogic.HEALTH_FACTOR_LIQUIDATION_THRESHOLD;
  }

  struct CalculateUserAccountDataVars {
    uint256 reserveUnitPrice;
    uint256 tokenUnit;
    uint256 compoundedLiquidityBalance;
    uint256 compoundedBorrowBalance;
    uint256 decimals;
    uint256 ltv;
    uint256 liquidationThreshold;
    uint256 i;
    uint256 healthFactor;
    uint256 totalCollateralBalanceETH;
    uint256 totalBorrowBalanceETH;
    uint256 totalFeesETH;
    uint256 avgLtv;
    uint256 avgLiquidationThreshold;
    uint256 reservesLength;
    bool healthFactorBelowThreshold;
    address currentReserveAddress;
    bool usageAsCollateralEnabled;
    bool userUsesReserveAsCollateral;
  }

  /**
   * @dev calculates the user data across the reserves.
   * this includes the total liquidity/collateral/borrow balances in ETH,
   * the average Loan To Value, the average Liquidation Ratio, and the Health factor.
   * @param user the address of the user
   * @param reservesData data of all the reserves
   * @param userConfig the configuration of the user
   * @param reserves the list of the available reserves
   * @param oracle the price oracle address
   * @return the total collateral and total borrow balance of the user in ETH, the avg ltv and liquidation threshold and the HF
   * also the average Ltv, liquidation threshold, and the health factor
   **/
  function calculateUserAccountData(
    address user,
    mapping(address => ReserveLogic.ReserveData) storage reservesData,
    UserConfiguration.Map memory userConfig,
    address[] memory reserves,
    address oracle
  )
    internal
    view
    returns (
      uint256,
      uint256,
      uint256,
      uint256,
      uint256
    )
  {
    CalculateUserAccountDataVars memory vars;

    if (userConfig.isEmpty()) {
      return (0, 0, 0, 0, uint256(-1));
    }
    for (vars.i = 0; vars.i < reserves.length; vars.i++) {
      if (!userConfig.isUsingAsCollateralOrBorrowing(vars.i)) {
        continue;
      }

      vars.currentReserveAddress = reserves[vars.i];
      ReserveLogic.ReserveData storage currentReserve = reservesData[vars.currentReserveAddress];

      (vars.ltv, vars.liquidationThreshold, , vars.decimals) = currentReserve
        .configuration
        .getParams();

      vars.tokenUnit = 10**vars.decimals;
      vars.reserveUnitPrice = IPriceOracleGetter(oracle).getAssetPrice(vars.currentReserveAddress);

      if (vars.ltv != 0 && userConfig.isUsingAsCollateral(vars.i)) {
        vars.compoundedLiquidityBalance = IERC20(currentReserve.aTokenAddress).balanceOf(user);

        uint256 liquidityBalanceETH = vars
          .reserveUnitPrice
          .mul(vars.compoundedLiquidityBalance)
          .div(vars.tokenUnit);

        vars.totalCollateralBalanceETH = vars.totalCollateralBalanceETH.add(liquidityBalanceETH);

        vars.avgLtv = vars.avgLtv.add(liquidityBalanceETH.mul(vars.ltv));
        vars.avgLiquidationThreshold = vars.avgLiquidationThreshold.add(
          liquidityBalanceETH.mul(vars.liquidationThreshold)
        );
      }

      if (userConfig.isBorrowing(vars.i)) {
        vars.compoundedBorrowBalance = IERC20(currentReserve.stableDebtTokenAddress).balanceOf(
          user
        );
        vars.compoundedBorrowBalance = vars.compoundedBorrowBalance.add(
          IERC20(currentReserve.variableDebtTokenAddress).balanceOf(user)
        );

        vars.totalBorrowBalanceETH = vars.totalBorrowBalanceETH.add(
          vars.reserveUnitPrice.mul(vars.compoundedBorrowBalance).div(vars.tokenUnit)
        );
      }
    }

    vars.avgLtv = vars.totalCollateralBalanceETH > 0
      ? vars.avgLtv.div(vars.totalCollateralBalanceETH)
      : 0;
    vars.avgLiquidationThreshold = vars.totalCollateralBalanceETH > 0
      ? vars.avgLiquidationThreshold.div(vars.totalCollateralBalanceETH)
      : 0;

    vars.healthFactor = calculateHealthFactorFromBalances(
      vars.totalCollateralBalanceETH,
      vars.totalBorrowBalanceETH,
      vars.avgLiquidationThreshold
    );
    return (
      vars.totalCollateralBalanceETH,
      vars.totalBorrowBalanceETH,
      vars.avgLtv,
      vars.avgLiquidationThreshold,
      vars.healthFactor
    );
  }

  /**
   * @dev calculates the health factor from the corresponding balances
   * @param collateralBalanceETH the total collateral balance in ETH
   * @param borrowBalanceETH the total borrow balance in ETH
   * @param liquidationThreshold the avg liquidation threshold
   * @return the health factor calculated from the balances provided
   **/
  function calculateHealthFactorFromBalances(
    uint256 collateralBalanceETH,
    uint256 borrowBalanceETH,
    uint256 liquidationThreshold
  ) internal pure returns (uint256) {
    if (borrowBalanceETH == 0) return uint256(-1);

    return (collateralBalanceETH.percentMul(liquidationThreshold)).wadDiv(borrowBalanceETH);
  }

    /**
   * @dev calculates the equivalent amount in ETH that an user can borrow, depending on the available collateral and the
   * average Loan To Value.
   * @param collateralBalanceETH the total collateral balance
   * @param borrowBalanceETH the total borrow balance
   * @param ltv the average loan to value
   * @return the amount available to borrow in ETH for the user
   **/

  function calculateAvailableBorrowsETH(
    uint256 collateralBalanceETH,
    uint256 borrowBalanceETH,
    uint256 ltv
  ) internal pure returns (uint256) {
    uint256 availableBorrowsETH = collateralBalanceETH.percentMul(ltv); //ltv is in percentage

    if (availableBorrowsETH < borrowBalanceETH) {
      return 0;
    }

    availableBorrowsETH = availableBorrowsETH.sub(borrowBalanceETH);
    return availableBorrowsETH;
  }
}



pragma experimental ABIEncoderV2;














/**
 * @title ReserveLogic library
 * @author Aave
 * @notice Implements functions to validate specific action on the protocol.
 */
library ValidationLogic {
  using ReserveLogic for ReserveLogic.ReserveData;
  using SafeMath for uint256;
  using WadRayMath for uint256;
  using PercentageMath for uint256;
  using SafeERC20 for IERC20;
  using ReserveConfiguration for ReserveConfiguration.Map;
  using UserConfiguration for UserConfiguration.Map;

  /**
   * @dev validates a deposit.
   * @param reserve the reserve state on which the user is depositing
   * @param amount the amount to be deposited
   */
  function validateDeposit(ReserveLogic.ReserveData storage reserve, uint256 amount) external view {
    (bool isActive, bool isFreezed, , ) = reserve.configuration.getFlags();

    require(amount > 0, Errors.AMOUNT_NOT_GREATER_THAN_0);
    require(isActive, Errors.NO_ACTIVE_RESERVE);
    require(!isFreezed, Errors.NO_UNFREEZED_RESERVE);
  }

  /**
   * @dev validates a withdraw action.
   * @param reserveAddress the address of the reserve
   * @param amount the amount to be withdrawn
   * @param userBalance the balance of the user
   */
  function validateWithdraw(
    address reserveAddress,
    uint256 amount,
    uint256 userBalance,
    mapping(address => ReserveLogic.ReserveData) storage reservesData,
    UserConfiguration.Map storage userConfig,
    address[] calldata reserves,
    address oracle
  ) external view {
    require(amount > 0, Errors.AMOUNT_NOT_GREATER_THAN_0);

    require(amount <= userBalance, Errors.NOT_ENOUGH_AVAILABLE_USER_BALANCE);

    require(
      GenericLogic.balanceDecreaseAllowed(
        reserveAddress,
        msg.sender,
        userBalance,
        reservesData,
        userConfig,
        reserves,
        oracle
      ),
      Errors.TRANSFER_NOT_ALLOWED
    );
  }

  struct ValidateBorrowLocalVars {
    uint256 principalBorrowBalance;
    uint256 currentLtv;
    uint256 currentLiquidationThreshold;
    uint256 requestedBorrowAmountETH;
    uint256 amountOfCollateralNeededETH;
    uint256 userCollateralBalanceETH;
    uint256 userBorrowBalanceETH;
    uint256 borrowBalanceIncrease;
    uint256 currentReserveStableRate;
    uint256 availableLiquidity;
    uint256 finalUserBorrowRate;
    uint256 healthFactor;
    ReserveLogic.InterestRateMode rateMode;
    bool healthFactorBelowThreshold;
    bool isActive;
    bool isFreezed;
    bool borrowingEnabled;
    bool stableRateBorrowingEnabled;
  }

  /**
   * @dev validates a borrow.
   * @param reserve the reserve state from which the user is borrowing
   * @param userAddress the address of the user
   * @param amount the amount to be borrowed
   * @param amountInETH the amount to be borrowed, in ETH
   * @param interestRateMode the interest rate mode at which the user is borrowing
   * @param maxStableLoanPercent the max amount of the liquidity that can be borrowed at stable rate, in percentage
   * @param reservesData the state of all the reserves
   * @param userConfig the state of the user for the specific reserve
   * @param reserves the addresses of all the active reserves
   * @param oracle the price oracle
   */

  function validateBorrow(
    ReserveLogic.ReserveData storage reserve,
    address userAddress,
    uint256 amount,
    uint256 amountInETH,
    uint256 interestRateMode,
    uint256 maxStableLoanPercent,
    mapping(address => ReserveLogic.ReserveData) storage reservesData,
    UserConfiguration.Map storage userConfig,
    address[] calldata reserves,
    address oracle
  ) external view {
    ValidateBorrowLocalVars memory vars;

    (
      vars.isActive,
      vars.isFreezed,
      vars.borrowingEnabled,
      vars.stableRateBorrowingEnabled
    ) = reserve.configuration.getFlags();

    require(vars.isActive, Errors.NO_ACTIVE_RESERVE);
    require(!vars.isFreezed, Errors.NO_UNFREEZED_RESERVE);

    require(vars.borrowingEnabled, Errors.BORROWING_NOT_ENABLED);

    //validate interest rate mode
    require(
      uint256(ReserveLogic.InterestRateMode.VARIABLE) == interestRateMode ||
        uint256(ReserveLogic.InterestRateMode.STABLE) == interestRateMode,
      Errors.INVALID_INTEREST_RATE_MODE_SELECTED
    );

    (
      vars.userCollateralBalanceETH,
      vars.userBorrowBalanceETH,
      vars.currentLtv,
      vars.currentLiquidationThreshold,
      vars.healthFactor
    ) = GenericLogic.calculateUserAccountData(
      userAddress,
      reservesData,
      userConfig,
      reserves,
      oracle
    );

    require(vars.userCollateralBalanceETH > 0, Errors.COLLATERAL_BALANCE_IS_0);

    require(
      vars.healthFactor > GenericLogic.HEALTH_FACTOR_LIQUIDATION_THRESHOLD,
      Errors.HEALTH_FACTOR_LOWER_THAN_LIQUIDATION_THRESHOLD
    );

    //add the current already borrowed amount to the amount requested to calculate the total collateral needed.
    vars.amountOfCollateralNeededETH = vars.userBorrowBalanceETH.add(amountInETH).percentDiv(
      vars.currentLtv
    ); //LTV is calculated in percentage

    require(
      vars.amountOfCollateralNeededETH <= vars.userCollateralBalanceETH,
      Errors.COLLATERAL_CANNOT_COVER_NEW_BORROW
    );

    /**
     * Following conditions need to be met if the user is borrowing at a stable rate:
     * 1. Reserve must be enabled for stable rate borrowing
     * 2. Users cannot borrow from the reserve if their collateral is (mostly) the same currency
     *    they are borrowing, to prevent abuses.
     * 3. Users will be able to borrow only a relatively small, configurable amount of the total
     *    liquidity
     **/

    if (vars.rateMode == ReserveLogic.InterestRateMode.STABLE) {
      //check if the borrow mode is stable and if stable rate borrowing is enabled on this reserve

      require(vars.stableRateBorrowingEnabled, Errors.STABLE_BORROWING_NOT_ENABLED);

      require(
        !userConfig.isUsingAsCollateral(reserve.id) ||
          reserve.configuration.getLtv() == 0 ||
          amount > IERC20(reserve.aTokenAddress).balanceOf(userAddress),
        Errors.CALLATERAL_SAME_AS_BORROWING_CURRENCY
      );

      //calculate the max available loan size in stable rate mode as a percentage of the
      //available liquidity
      uint256 maxLoanSizeStable = vars.availableLiquidity.percentMul(maxStableLoanPercent);

      require(amount <= maxLoanSizeStable, Errors.AMOUNT_BIGGER_THAN_MAX_LOAN_SIZE_STABLE);
    }
  }

  /**
   * @dev validates a repay.
   * @param reserve the reserve state from which the user is repaying
   * @param amountSent the amount sent for the repayment. Can be an actual value or uint(-1)
   * @param onBehalfOf the address of the user msg.sender is repaying for
   * @param stableDebt the borrow balance of the user
   * @param variableDebt the borrow balance of the user
   */
  function validateRepay(
    ReserveLogic.ReserveData storage reserve,
    uint256 amountSent,
    ReserveLogic.InterestRateMode rateMode,
    address onBehalfOf,
    uint256 stableDebt,
    uint256 variableDebt
  ) external view {
    bool isActive = reserve.configuration.getActive();

    require(isActive, Errors.NO_ACTIVE_RESERVE);

    require(amountSent > 0, Errors.AMOUNT_NOT_GREATER_THAN_0);

    require(
      (stableDebt > 0 &&
        ReserveLogic.InterestRateMode(rateMode) == ReserveLogic.InterestRateMode.STABLE) ||
        (variableDebt > 0 &&
          ReserveLogic.InterestRateMode(rateMode) == ReserveLogic.InterestRateMode.VARIABLE),
      Errors.NO_DEBT_OF_SELECTED_TYPE
    );

    require(
      amountSent != uint256(-1) || msg.sender == onBehalfOf,
      Errors.NO_EXPLICIT_AMOUNT_TO_REPAY_ON_BEHALF
    );
  }

  /**
   * @dev validates a swap of borrow rate mode.
   * @param reserve the reserve state on which the user is swapping the rate
   * @param userConfig the user reserves configuration
   * @param stableBorrowBalance the stable borrow balance of the user
   * @param variableBorrowBalance the stable borrow balance of the user
   * @param currentRateMode the rate mode of the borrow
   */
  function validateSwapRateMode(
    ReserveLogic.ReserveData storage reserve,
    UserConfiguration.Map storage userConfig,
    uint256 stableBorrowBalance,
    uint256 variableBorrowBalance,
    ReserveLogic.InterestRateMode currentRateMode
  ) external view {
    (bool isActive, bool isFreezed, , bool stableRateEnabled) = reserve.configuration.getFlags();

    require(isActive, Errors.NO_ACTIVE_RESERVE);
    require(!isFreezed, Errors.NO_UNFREEZED_RESERVE);

    if (currentRateMode == ReserveLogic.InterestRateMode.STABLE) {
      require(stableBorrowBalance > 0, Errors.NO_STABLE_RATE_LOAN_IN_RESERVE);
    } else if (currentRateMode == ReserveLogic.InterestRateMode.VARIABLE) {
      require(variableBorrowBalance > 0, Errors.NO_VARIABLE_RATE_LOAN_IN_RESERVE);
      /**
       * user wants to swap to stable, before swapping we need to ensure that
       * 1. stable borrow rate is enabled on the reserve
       * 2. user is not trying to abuse the reserve by depositing
       * more collateral than he is borrowing, artificially lowering
       * the interest rate, borrowing at variable, and switching to stable
       **/
      require(stableRateEnabled, Errors.STABLE_BORROWING_NOT_ENABLED);

      require(
        !userConfig.isUsingAsCollateral(reserve.id) ||
          reserve.configuration.getLtv() == 0 ||
          stableBorrowBalance.add(variableBorrowBalance) >
          IERC20(reserve.aTokenAddress).balanceOf(msg.sender),
        Errors.CALLATERAL_SAME_AS_BORROWING_CURRENCY
      );
    } else {
      revert(Errors.INVALID_INTEREST_RATE_MODE_SELECTED);
    }
  }

  /**
   * @dev validates the choice of a user of setting (or not) an asset as collateral
   * @param reserve the state of the reserve that the user is enabling or disabling as collateral
   * @param reserveAddress the address of the reserve
   * @param reservesData the data of all the reserves
   * @param userConfig the state of the user for the specific reserve
   * @param reserves the addresses of all the active reserves
   * @param oracle the price oracle
   */
  function validateSetUseReserveAsCollateral(
    ReserveLogic.ReserveData storage reserve,
    address reserveAddress,
    mapping(address => ReserveLogic.ReserveData) storage reservesData,
    UserConfiguration.Map storage userConfig,
    address[] calldata reserves,
    address oracle
  ) external view {
    uint256 underlyingBalance = IERC20(reserve.aTokenAddress).balanceOf(msg.sender);

    require(underlyingBalance > 0, Errors.UNDERLYING_BALANCE_NOT_GREATER_THAN_0);

    require(
      GenericLogic.balanceDecreaseAllowed(
        reserveAddress,
        msg.sender,
        underlyingBalance,
        reservesData,
        userConfig,
        reserves,
        oracle
      ),
      Errors.DEPOSIT_ALREADY_IN_USE
    );
  }

  /**
   * @dev validates a flashloan action
   * @param mode the flashloan mode (0 = classic flashloan, 1 = open a stable rate loan, 2 = open a variable rate loan)
   * @param premium the premium paid on the flashloan
   **/
  function validateFlashloan(uint256 mode, uint256 premium) internal pure {
    require(premium > 0, Errors.REQUESTED_AMOUNT_TOO_SMALL);
    require(mode <= uint256(ReserveLogic.InterestRateMode.VARIABLE), Errors.INVALID_FLASHLOAN_MODE);
  }

  /**
   * @dev Validates the liquidationCall() action
   * @param collateralReserve The reserve data of the collateral
   * @param principalReserve The reserve data of the principal
   * @param userConfig The user configuration
   * @param userHealthFactor The user's health factor
   * @param userStableDebt Total stable debt balance of the user
   * @param userVariableDebt Total variable debt balance of the user
   **/
  function validateLiquidationCall(
    ReserveLogic.ReserveData storage collateralReserve,
    ReserveLogic.ReserveData storage principalReserve,
    UserConfiguration.Map storage userConfig,
    uint256 userHealthFactor,
    uint256 userStableDebt,
    uint256 userVariableDebt
  ) internal view returns (uint256, string memory) {
    if (
      !collateralReserve.configuration.getActive() || !principalReserve.configuration.getActive()
    ) {
      return (uint256(Errors.CollateralManagerErrors.NO_ACTIVE_RESERVE), Errors.NO_ACTIVE_RESERVE);
    }

    if (userHealthFactor >= GenericLogic.HEALTH_FACTOR_LIQUIDATION_THRESHOLD) {
      return (
        uint256(Errors.CollateralManagerErrors.HEALTH_FACTOR_ABOVE_THRESHOLD),
        Errors.HEALTH_FACTOR_NOT_BELOW_THRESHOLD
      );
    }

    bool isCollateralEnabled = collateralReserve.configuration.getLiquidationThreshold() > 0 &&
      userConfig.isUsingAsCollateral(collateralReserve.id);

    //if collateral isn't enabled as collateral by user, it cannot be liquidated
    if (!isCollateralEnabled) {
      return (
        uint256(Errors.CollateralManagerErrors.COLLATERAL_CANNOT_BE_LIQUIDATED),
        Errors.COLLATERAL_CANNOT_BE_LIQUIDATED
      );
    }

    if (userStableDebt == 0 && userVariableDebt == 0) {
      return (
        uint256(Errors.CollateralManagerErrors.CURRRENCY_NOT_BORROWED),
        Errors.SPECIFIED_CURRENCY_NOT_BORROWED_BY_USER
      );
    }

    return (uint256(Errors.CollateralManagerErrors.NO_ERROR), Errors.NO_ERRORS);
  }

  /**
   * @dev Validates the repayWithCollateral() action
   * @param collateralReserve The reserve data of the collateral
   * @param principalReserve The reserve data of the principal
   * @param userConfig The user configuration
   * @param user The address of the user
   * @param userHealthFactor The user's health factor
   * @param userStableDebt Total stable debt balance of the user
   * @param userVariableDebt Total variable debt balance of the user
   **/
  function validateRepayWithCollateral(
    ReserveLogic.ReserveData storage collateralReserve,
    ReserveLogic.ReserveData storage principalReserve,
    UserConfiguration.Map storage userConfig,
    address user,
    uint256 userHealthFactor,
    uint256 userStableDebt,
    uint256 userVariableDebt
  ) internal view returns (uint256, string memory) {
    if (
      !collateralReserve.configuration.getActive() || !principalReserve.configuration.getActive()
    ) {
      return (uint256(Errors.CollateralManagerErrors.NO_ACTIVE_RESERVE), Errors.NO_ACTIVE_RESERVE);
    }

    if (
      msg.sender != user && userHealthFactor >= GenericLogic.HEALTH_FACTOR_LIQUIDATION_THRESHOLD
    ) {
      return (
        uint256(Errors.CollateralManagerErrors.HEALTH_FACTOR_ABOVE_THRESHOLD),
        Errors.HEALTH_FACTOR_NOT_BELOW_THRESHOLD
      );
    }

    if (msg.sender != user) {
      bool isCollateralEnabled = collateralReserve.configuration.getLiquidationThreshold() > 0 &&
        userConfig.isUsingAsCollateral(collateralReserve.id);

      //if collateral isn't enabled as collateral by user, it cannot be liquidated
      if (!isCollateralEnabled) {
        return (
          uint256(Errors.CollateralManagerErrors.COLLATERAL_CANNOT_BE_LIQUIDATED),
          Errors.COLLATERAL_CANNOT_BE_LIQUIDATED
        );
      }
    }

    if (userStableDebt == 0 && userVariableDebt == 0) {
      return (
        uint256(Errors.CollateralManagerErrors.CURRRENCY_NOT_BORROWED),
        Errors.SPECIFIED_CURRENCY_NOT_BORROWED_BY_USER
      );
    }

    return (uint256(Errors.CollateralManagerErrors.NO_ERROR), Errors.NO_ERRORS);
  }

  /**
   * @dev Validates the swapLiquidity() action
   * @param fromReserve The reserve data of the asset to swap from
   * @param toReserve The reserve data of the asset to swap to
   * @param fromAsset Address of the asset to swap from
   * @param toAsset Address of the asset to swap to
   **/
  function validateSwapLiquidity(
    ReserveLogic.ReserveData storage fromReserve,
    ReserveLogic.ReserveData storage toReserve,
    address fromAsset,
    address toAsset
  ) internal view returns (uint256, string memory) {
    if (fromAsset == toAsset) {
      return (
        uint256(Errors.CollateralManagerErrors.INVALID_EQUAL_ASSETS_TO_SWAP),
        Errors.INVALID_EQUAL_ASSETS_TO_SWAP
      );
    }

    (bool isToActive, bool isToFreezed, , ) = toReserve.configuration.getFlags();
    if (!fromReserve.configuration.getActive() || !isToActive) {
      return (uint256(Errors.CollateralManagerErrors.NO_ACTIVE_RESERVE), Errors.NO_ACTIVE_RESERVE);
    }
    if (isToFreezed) {
      return (
        uint256(Errors.CollateralManagerErrors.NO_UNFREEZED_RESERVE),
        Errors.NO_UNFREEZED_RESERVE
      );
    }

    return (uint256(Errors.CollateralManagerErrors.NO_ERROR), Errors.NO_ERRORS);
  }
}









/**
 * @title IFlashLoanReceiver interface
 * @notice Interface for the Aave fee IFlashLoanReceiver.
 * @author Aave
 * @dev implement this interface to develop a flashloan-compatible flashLoanReceiver contract
 **/
interface IFlashLoanReceiver {
  function executeOperation(
    address reserve,
    uint256 amount,
    uint256 fee,
    bytes calldata params
  ) external;
}




interface ISwapAdapter {
  /**
   * @dev Swaps an `amountToSwap` of an asset to another, approving a `fundsDestination` to pull the funds
   * @param assetToSwapFrom Origin asset
   * @param assetToSwapTo Destination asset
   * @param amountToSwap How much `assetToSwapFrom` needs to be swapped
   * @param fundsDestination Address that will be pulling the swapped funds
   * @param params Additional variadic field to include extra params
   */
  function executeOperation(
    address assetToSwapFrom,
    address assetToSwapTo,
    uint256 amountToSwap,
    address fundsDestination,
    bytes calldata params
  ) external;
}






























contract LendingPoolStorage {
  using ReserveLogic for ReserveLogic.ReserveData;
  using ReserveConfiguration for ReserveConfiguration.Map;
  using UserConfiguration for UserConfiguration.Map;

  ILendingPoolAddressesProvider internal _addressesProvider;

  mapping(address => ReserveLogic.ReserveData) internal _reserves;
  mapping(address => UserConfiguration.Map) internal _usersConfig;
  // debt token address => user who gives allowance => user who receives allowance => amount
  mapping(address => mapping(address => mapping(address => uint256))) internal _borrowAllowance;

  address[] internal _reservesList;

  bool internal _flashLiquidationLocked;
  bool internal _paused;

  /**
   * @dev returns the list of the initialized reserves
   **/
  function getReservesList() external view returns (address[] memory) {
    return _reservesList;
  }

  /**
   * @dev returns the addresses provider
   **/
  function getAddressesProvider() external view returns (ILendingPoolAddressesProvider) {
    return _addressesProvider;
  }
}


/**
 * @title LendingPoolCollateralManager contract
 * @author Aave
 * @notice Implements actions involving management of collateral in the protocol.
 * @notice this contract will be ran always through delegatecall
 * @dev LendingPoolCollateralManager inherits VersionedInitializable from OpenZeppelin to have the same storage layout as LendingPool
 **/
contract LendingPoolCollateralManager is VersionedInitializable, LendingPoolStorage {
  using SafeERC20 for IERC20;
  using SafeMath for uint256;
  using WadRayMath for uint256;
  using PercentageMath for uint256;

  // IMPORTANT The storage layout of the LendingPool is reproduced here because this contract
  // is gonna be used through DELEGATECALL

  uint256 internal constant LIQUIDATION_CLOSE_FACTOR_PERCENT = 5000;

  /**
   * @dev emitted when a borrower is liquidated
   * @param collateral the address of the collateral being liquidated
   * @param principal the address of the reserve
   * @param user the address of the user being liquidated
   * @param purchaseAmount the total amount liquidated
   * @param liquidatedCollateralAmount the amount of collateral being liquidated
   * @param liquidator the address of the liquidator
   * @param receiveAToken true if the liquidator wants to receive aTokens, false otherwise
   **/
  event LiquidationCall(
    address indexed collateral,
    address indexed principal,
    address indexed user,
    uint256 purchaseAmount,
    uint256 liquidatedCollateralAmount,
    address liquidator,
    bool receiveAToken
  );

  /**
    @dev emitted when a borrower/liquidator repays with the borrower's collateral
    @param collateral the address of the collateral being swapped to repay
    @param principal the address of the reserve of the debt
    @param user the borrower's address
    @param liquidator the address of the liquidator, same as the one of the borrower on self-repayment
    @param principalAmount the amount of the debt finally covered
    @param swappedCollateralAmount the amount of collateral finally swapped
  */
  event RepaidWithCollateral(
    address indexed collateral,
    address indexed principal,
    address indexed user,
    address liquidator,
    uint256 principalAmount,
    uint256 swappedCollateralAmount
  );

  struct LiquidationCallLocalVars {
    uint256 userCollateralBalance;
    uint256 userStableDebt;
    uint256 userVariableDebt;
    uint256 maxPrincipalAmountToLiquidate;
    uint256 actualAmountToLiquidate;
    uint256 liquidationRatio;
    uint256 maxAmountCollateralToLiquidate;
    ReserveLogic.InterestRateMode borrowRateMode;
    uint256 userStableRate;
    uint256 maxCollateralToLiquidate;
    uint256 principalAmountNeeded;
    uint256 healthFactor;
    IAToken collateralAtoken;
    bool isCollateralEnabled;
    address principalAToken;
    uint256 errorCode;
    string errorMsg;
  }

  struct SwapLiquidityLocalVars {
    uint256 healthFactor;
    uint256 amountToReceive;
    uint256 userBalanceBefore;
    IAToken fromReserveAToken;
    IAToken toReserveAToken;
    uint256 errorCode;
    string errorMsg;
  }

  struct AvailableCollateralToLiquidateLocalVars {
    uint256 userCompoundedBorrowBalance;
    uint256 liquidationBonus;
    uint256 collateralPrice;
    uint256 principalCurrencyPrice;
    uint256 maxAmountCollateralToLiquidate;
    uint256 principalDecimals;
    uint256 collateralDecimals;
  }

  /**
   * @dev as the contract extends the VersionedInitializable contract to match the state
   * of the LendingPool contract, the getRevision() function is needed.
   */
  function getRevision() internal override pure returns (uint256) {
    return 0;
  }

  /**
   * @dev users can invoke this function to liquidate an undercollateralized position.
   * @param collateral the address of the collateral to liquidated
   * @param principal the address of the principal reserve
   * @param user the address of the borrower
   * @param purchaseAmount the amount of principal that the liquidator wants to repay
   * @param receiveAToken true if the liquidators wants to receive the aTokens, false if
   * he wants to receive the underlying asset directly
   **/
  function liquidationCall(
    address collateral,
    address principal,
    address user,
    uint256 purchaseAmount,
    bool receiveAToken
  ) external returns (uint256, string memory) {
    ReserveLogic.ReserveData storage collateralReserve = _reserves[collateral];
    ReserveLogic.ReserveData storage principalReserve = _reserves[principal];
    UserConfiguration.Map storage userConfig = _usersConfig[user];

    LiquidationCallLocalVars memory vars;

    (, , , , vars.healthFactor) = GenericLogic.calculateUserAccountData(
      user,
      _reserves,
      _usersConfig[user],
      _reservesList,
      _addressesProvider.getPriceOracle()
    );

    //if the user hasn't borrowed the specific currency defined by asset, it cannot be liquidated
    (vars.userStableDebt, vars.userVariableDebt) = Helpers.getUserCurrentDebt(
      user,
      principalReserve
    );

    (vars.errorCode, vars.errorMsg) = ValidationLogic.validateLiquidationCall(
      collateralReserve,
      principalReserve,
      userConfig,
      vars.healthFactor,
      vars.userStableDebt,
      vars.userVariableDebt
    );

    if (Errors.CollateralManagerErrors(vars.errorCode) != Errors.CollateralManagerErrors.NO_ERROR) {
      return (vars.errorCode, vars.errorMsg);
    }

    vars.collateralAtoken = IAToken(collateralReserve.aTokenAddress);

    vars.userCollateralBalance = vars.collateralAtoken.balanceOf(user);

    vars.maxPrincipalAmountToLiquidate = vars.userStableDebt.add(vars.userVariableDebt).percentMul(
      LIQUIDATION_CLOSE_FACTOR_PERCENT
    );

    vars.actualAmountToLiquidate = purchaseAmount > vars.maxPrincipalAmountToLiquidate
      ? vars.maxPrincipalAmountToLiquidate
      : purchaseAmount;

    (
      vars.maxCollateralToLiquidate,
      vars.principalAmountNeeded
    ) = calculateAvailableCollateralToLiquidate(
      collateralReserve,
      principalReserve,
      collateral,
      principal,
      vars.actualAmountToLiquidate,
      vars.userCollateralBalance
    );

    //if principalAmountNeeded < vars.ActualAmountToLiquidate, there isn't enough
    //of collateral to cover the actual amount that is being liquidated, hence we liquidate
    //a smaller amount

    if (vars.principalAmountNeeded < vars.actualAmountToLiquidate) {
      vars.actualAmountToLiquidate = vars.principalAmountNeeded;
    }

    //if liquidator reclaims the underlying asset, we make sure there is enough available collateral in the reserve
    if (!receiveAToken) {
      uint256 currentAvailableCollateral = IERC20(collateral).balanceOf(
        address(vars.collateralAtoken)
      );
      if (currentAvailableCollateral < vars.maxCollateralToLiquidate) {
        return (
          uint256(Errors.CollateralManagerErrors.NOT_ENOUGH_LIQUIDITY),
          Errors.NOT_ENOUGH_LIQUIDITY_TO_LIQUIDATE
        );
      }
    }

    //update the principal reserve
    principalReserve.updateState();

    principalReserve.updateInterestRates(
      principal,
      principalReserve.aTokenAddress,
      vars.actualAmountToLiquidate,
      0
    );

    if (vars.userVariableDebt >= vars.actualAmountToLiquidate) {
      IVariableDebtToken(principalReserve.variableDebtTokenAddress).burn(
        user,
        vars.actualAmountToLiquidate,
        principalReserve.variableBorrowIndex
      );
    } else {
      IVariableDebtToken(principalReserve.variableDebtTokenAddress).burn(
        user,
        vars.userVariableDebt,
        principalReserve.variableBorrowIndex
      );

      IStableDebtToken(principalReserve.stableDebtTokenAddress).burn(
        user,
        vars.actualAmountToLiquidate.sub(vars.userVariableDebt)
      );
    }

    //if liquidator reclaims the aToken, he receives the equivalent atoken amount
    if (receiveAToken) {
      vars.collateralAtoken.transferOnLiquidation(user, msg.sender, vars.maxCollateralToLiquidate);
    } else {
      //otherwise receives the underlying asset

      //updating collateral reserve
      collateralReserve.updateState();
      collateralReserve.updateInterestRates(
        collateral,
        address(vars.collateralAtoken),
        0,
        vars.maxCollateralToLiquidate
      );

      //burn the equivalent amount of atoken
      vars.collateralAtoken.burn(
        user,
        msg.sender,
        vars.maxCollateralToLiquidate,
        collateralReserve.liquidityIndex
      );
    }

    //transfers the principal currency to the aToken
    IERC20(principal).safeTransferFrom(
      msg.sender,
      principalReserve.aTokenAddress,
      vars.actualAmountToLiquidate
    );

    emit LiquidationCall(
      collateral,
      principal,
      user,
      vars.actualAmountToLiquidate,
      vars.maxCollateralToLiquidate,
      msg.sender,
      receiveAToken
    );

    return (uint256(Errors.CollateralManagerErrors.NO_ERROR), Errors.NO_ERRORS);
  }

  /**
   * @dev flashes the underlying collateral on an user to swap for the owed asset and repay
   * - Both the owner of the position and other liquidators can execute it.
   * - The owner can repay with his collateral at any point, no matter the health factor.
   * - Other liquidators can only use this function below 1 HF. To liquidate 50% of the debt > HF 0.98 or the whole below.
   * @param collateral The address of the collateral asset.
   * @param principal The address of the owed asset.
   * @param user Address of the borrower.
   * @param principalAmount Amount of the debt to repay.
   * @param receiver Address of the contract receiving the collateral to swap.
   * @param params Variadic bytes param to pass with extra information to the receiver
   **/
  function repayWithCollateral(
    address collateral,
    address principal,
    address user,
    uint256 principalAmount,
    address receiver,
    bytes calldata params
  ) external returns (uint256, string memory) {
    ReserveLogic.ReserveData storage collateralReserve = _reserves[collateral];
    ReserveLogic.ReserveData storage debtReserve = _reserves[principal];
    UserConfiguration.Map storage userConfig = _usersConfig[user];

    LiquidationCallLocalVars memory vars;

    (, , , , vars.healthFactor) = GenericLogic.calculateUserAccountData(
      user,
      _reserves,
      _usersConfig[user],
      _reservesList,
      _addressesProvider.getPriceOracle()
    );

    (vars.userStableDebt, vars.userVariableDebt) = Helpers.getUserCurrentDebt(user, debtReserve);

    (vars.errorCode, vars.errorMsg) = ValidationLogic.validateRepayWithCollateral(
      collateralReserve,
      debtReserve,
      userConfig,
      user,
      vars.healthFactor,
      vars.userStableDebt,
      vars.userVariableDebt
    );

    if (Errors.CollateralManagerErrors(vars.errorCode) != Errors.CollateralManagerErrors.NO_ERROR) {
      return (vars.errorCode, vars.errorMsg);
    }

    vars.maxPrincipalAmountToLiquidate = vars.userStableDebt.add(vars.userVariableDebt);

    vars.actualAmountToLiquidate = principalAmount > vars.maxPrincipalAmountToLiquidate
      ? vars.maxPrincipalAmountToLiquidate
      : principalAmount;

    vars.collateralAtoken = IAToken(collateralReserve.aTokenAddress);
    vars.userCollateralBalance = vars.collateralAtoken.balanceOf(user);

    (
      vars.maxCollateralToLiquidate,
      vars.principalAmountNeeded
    ) = calculateAvailableCollateralToLiquidate(
      collateralReserve,
      debtReserve,
      collateral,
      principal,
      vars.actualAmountToLiquidate,
      vars.userCollateralBalance
    );

    //if principalAmountNeeded < vars.ActualAmountToLiquidate, there isn't enough
    //of collateral to cover the actual amount that is being liquidated, hence we liquidate
    //a smaller amount
    if (vars.principalAmountNeeded < vars.actualAmountToLiquidate) {
      vars.actualAmountToLiquidate = vars.principalAmountNeeded;
    }
    //updating collateral reserve indexes
    collateralReserve.updateState();

    vars.collateralAtoken.burn(
      user,
      receiver,
      vars.maxCollateralToLiquidate,
      collateralReserve.liquidityIndex
    );

    if (vars.userCollateralBalance == vars.maxCollateralToLiquidate) {
      _usersConfig[user].setUsingAsCollateral(collateralReserve.id, false);
    }

    vars.principalAToken = debtReserve.aTokenAddress;

    // Notifies the receiver to proceed, sending as param the underlying already transferred
    ISwapAdapter(receiver).executeOperation(
      collateral,
      principal,
      vars.maxCollateralToLiquidate,
      address(this),
      params
    );

    //updating debt reserve
    debtReserve.updateState();
    debtReserve.updateInterestRates(
      principal,
      vars.principalAToken,
      vars.actualAmountToLiquidate,
      0
    );
    IERC20(principal).transferFrom(receiver, vars.principalAToken, vars.actualAmountToLiquidate);

    if (vars.userVariableDebt >= vars.actualAmountToLiquidate) {
      IVariableDebtToken(debtReserve.variableDebtTokenAddress).burn(
        user,
        vars.actualAmountToLiquidate,
        debtReserve.variableBorrowIndex
      );
    } else {
      IVariableDebtToken(debtReserve.variableDebtTokenAddress).burn(
        user,
        vars.userVariableDebt,
        debtReserve.variableBorrowIndex
      );
      IStableDebtToken(debtReserve.stableDebtTokenAddress).burn(
        user,
        vars.actualAmountToLiquidate.sub(vars.userVariableDebt)
      );
    }

    //updating collateral reserve
    collateralReserve.updateInterestRates(
      collateral,
      address(vars.collateralAtoken),
      0,
      vars.maxCollateralToLiquidate
    );

    emit RepaidWithCollateral(
      collateral,
      principal,
      user,
      msg.sender,
      vars.actualAmountToLiquidate,
      vars.maxCollateralToLiquidate
    );

    return (uint256(Errors.CollateralManagerErrors.NO_ERROR), Errors.NO_ERRORS);
  }

  /**
   * @dev Allows an user to release one of his assets deposited in the protocol, even if it is used as collateral, to swap for another.
   * - It's not possible to release one asset to swap for the same
   * @param receiverAddress The address of the contract receiving the funds. The receiver should implement the ISwapAdapter interface
   * @param fromAsset Asset to swap from
   * @param toAsset Asset to swap to
   * @param params a bytes array to be sent (if needed) to the receiver contract with extra data
   **/
  function swapLiquidity(
    address receiverAddress,
    address fromAsset,
    address toAsset,
    uint256 amountToSwap,
    bytes calldata params
  ) external returns (uint256, string memory) {
    ReserveLogic.ReserveData storage fromReserve = _reserves[fromAsset];
    ReserveLogic.ReserveData storage toReserve = _reserves[toAsset];

    SwapLiquidityLocalVars memory vars;

    (vars.errorCode, vars.errorMsg) = ValidationLogic.validateSwapLiquidity(
      fromReserve,
      toReserve,
      fromAsset,
      toAsset
    );

    if (Errors.CollateralManagerErrors(vars.errorCode) != Errors.CollateralManagerErrors.NO_ERROR) {
      return (vars.errorCode, vars.errorMsg);
    }

    vars.fromReserveAToken = IAToken(fromReserve.aTokenAddress);
    vars.toReserveAToken = IAToken(toReserve.aTokenAddress);

    fromReserve.updateState();
    toReserve.updateState();

    if (vars.fromReserveAToken.balanceOf(msg.sender) == amountToSwap) {
      _usersConfig[msg.sender].setUsingAsCollateral(fromReserve.id, false);
    }

    fromReserve.updateInterestRates(fromAsset, address(vars.fromReserveAToken), 0, amountToSwap);
    // SWC-105-Unprotected Ether Withdrawal: L490-517
    vars.fromReserveAToken.burn(
      msg.sender,
      receiverAddress,
      amountToSwap,
      fromReserve.liquidityIndex
    );
    // Notifies the receiver to proceed, sending as param the underlying already transferred
    ISwapAdapter(receiverAddress).executeOperation(
      fromAsset,
      toAsset,
      amountToSwap,
      address(this),
      params
    );

    vars.amountToReceive = IERC20(toAsset).balanceOf(receiverAddress);
    if (vars.amountToReceive != 0) {
      IERC20(toAsset).transferFrom(
        receiverAddress,
        address(vars.toReserveAToken),
        vars.amountToReceive
      );

      if (vars.toReserveAToken.balanceOf(msg.sender) == 0) {
        _usersConfig[msg.sender].setUsingAsCollateral(toReserve.id, true);
      }

      vars.toReserveAToken.mint(msg.sender, vars.amountToReceive, toReserve.liquidityIndex);
      toReserve.updateInterestRates(
        toAsset,
        address(vars.toReserveAToken),
        vars.amountToReceive,
        0
      );
    }

    (, , , , vars.healthFactor) = GenericLogic.calculateUserAccountData(
      msg.sender,
      _reserves,
      _usersConfig[msg.sender],
      _reservesList,
      _addressesProvider.getPriceOracle()
    );

    if (vars.healthFactor < GenericLogic.HEALTH_FACTOR_LIQUIDATION_THRESHOLD) {
      return (
        uint256(Errors.CollateralManagerErrors.HEALTH_FACTOR_LOWER_THAN_LIQUIDATION_THRESHOLD),
        Errors.HEALTH_FACTOR_LOWER_THAN_LIQUIDATION_THRESHOLD
      );
    }

    return (uint256(Errors.CollateralManagerErrors.NO_ERROR), Errors.NO_ERRORS);
  }

  /**
   * @dev calculates how much of a specific collateral can be liquidated, given
   * a certain amount of principal currency. This function needs to be called after
   * all the checks to validate the liquidation have been performed, otherwise it might fail.
   * @param collateralAddress the collateral to be liquidated
   * @param principalAddress the principal currency to be liquidated
   * @param purchaseAmount the amount of principal being liquidated
   * @param userCollateralBalance the collatera balance for the specific collateral asset of the user being liquidated
   * @return collateralAmount the maximum amount that is possible to liquidated given all the liquidation constraints (user balance, close factor)
   * @return principalAmountNeeded the purchase amount
   **/
  function calculateAvailableCollateralToLiquidate(
    ReserveLogic.ReserveData storage collateralReserve,
    ReserveLogic.ReserveData storage principalReserve,
    address collateralAddress,
    address principalAddress,
    uint256 purchaseAmount,
    uint256 userCollateralBalance
  ) internal view returns (uint256, uint256) {
    uint256 collateralAmount = 0;
    uint256 principalAmountNeeded = 0;
    IPriceOracleGetter oracle = IPriceOracleGetter(_addressesProvider.getPriceOracle());

    AvailableCollateralToLiquidateLocalVars memory vars;

    vars.collateralPrice = oracle.getAssetPrice(collateralAddress);
    vars.principalCurrencyPrice = oracle.getAssetPrice(principalAddress);

    (, , vars.liquidationBonus, vars.collateralDecimals) = collateralReserve
      .configuration
      .getParams();
    vars.principalDecimals = principalReserve.configuration.getDecimals();

    //this is the maximum possible amount of the selected collateral that can be liquidated, given the
    //max amount of principal currency that is available for liquidation.
    vars.maxAmountCollateralToLiquidate = vars
      .principalCurrencyPrice
      .mul(purchaseAmount)
      .mul(10**vars.collateralDecimals)
      .div(vars.collateralPrice.mul(10**vars.principalDecimals))
      .percentMul(vars.liquidationBonus);

    if (vars.maxAmountCollateralToLiquidate > userCollateralBalance) {
      collateralAmount = userCollateralBalance;
      principalAmountNeeded = vars
        .collateralPrice
        .mul(collateralAmount)
        .mul(10**vars.principalDecimals)
        .div(vars.principalCurrencyPrice.mul(10**vars.collateralDecimals))
        .percentDiv(vars.liquidationBonus);
    } else {
      collateralAmount = vars.maxAmountCollateralToLiquidate;
      principalAmountNeeded = purchaseAmount;
    }
    return (collateralAmount, principalAmountNeeded);
  }
}






/**
 * @title LendingPool contract
 * @notice Implements the actions of the LendingPool, and exposes accessory methods to fetch the users and reserve data
 * @author Aave
 **/
contract LendingPool is VersionedInitializable, ILendingPool, LendingPoolStorage {
  using SafeMath for uint256;
  using WadRayMath for uint256;
  using PercentageMath for uint256;
  using SafeERC20 for IERC20;

  //main configuration parameters
  uint256 public constant REBALANCE_UP_LIQUIDITY_RATE_THRESHOLD = 4000;
  uint256 public constant REBALANCE_UP_USAGE_RATIO_THRESHOLD = 0.95 * 1e27; //usage ratio of 95%
  uint256 public constant MAX_STABLE_RATE_BORROW_SIZE_PERCENT = 2500;
  uint256 public constant FLASHLOAN_PREMIUM_TOTAL = 9;
  uint256 public constant MAX_NUMBER_RESERVES = 128;
  uint256 public constant LENDINGPOOL_REVISION = 0x2;

  /**
   * @dev only lending pools configurator can use functions affected by this modifier
   **/
  function _onlyLendingPoolConfigurator() internal view {
    require(
      _addressesProvider.getLendingPoolConfigurator() == msg.sender,
      Errors.CALLER_NOT_LENDING_POOL_CONFIGURATOR
    );
  }
  /**
   * @dev Function to make a function callable only when the contract is not paused.
   *
   * Requirements:
   *
   * - The contract must not be paused.
   */
  function _whenNotPaused() internal view {
    require(!_paused, Errors.IS_PAUSED);
  }

  function getRevision() internal override pure returns (uint256) {
    return LENDINGPOOL_REVISION;
  }

  /**
   * @dev this function is invoked by the proxy contract when the LendingPool contract is added to the
   * AddressesProvider.
   * @param provider the address of the LendingPoolAddressesProvider registry
   **/
  function initialize(ILendingPoolAddressesProvider provider) public initializer {
    _addressesProvider = provider;
  }

  /**
   * @dev deposits The underlying asset into the reserve. A corresponding amount of the overlying asset (aTokens)
   * is minted.
   * @param asset the address of the reserve
   * @param amount the amount to be deposited
   * @param referralCode integrators are assigned a referral code and can potentially receive rewards.
   **/
   // SWC-107-Reentrancy: L92-119
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

  /**
   * @dev withdraws the _reserves of user.
   * @param asset the address of the reserve
   * @param amount the underlying amount to be redeemed
   **/
  function withdraw(address asset, uint256 amount) external override {
    _whenNotPaused();
    ReserveLogic.ReserveData storage reserve = _reserves[asset];

    address aToken = reserve.aTokenAddress;

    uint256 userBalance = IAToken(aToken).balanceOf(msg.sender);

    uint256 amountToWithdraw = amount;

    //if amount is equal to uint(-1), the user wants to redeem everything
    if (amount == type(uint256).max) {
      amountToWithdraw = userBalance;
    }

    ValidationLogic.validateWithdraw(
      asset,
      amountToWithdraw,
      userBalance,
      _reserves,
      _usersConfig[msg.sender],
      _reservesList,
      _addressesProvider.getPriceOracle()
    );

    reserve.updateState();

    reserve.updateInterestRates(asset, aToken, 0, amountToWithdraw);

    if (amountToWithdraw == userBalance) {
      _usersConfig[msg.sender].setUsingAsCollateral(reserve.id, false);
    }

    IAToken(aToken).burn(msg.sender, msg.sender, amountToWithdraw, reserve.liquidityIndex);

    emit Withdraw(asset, msg.sender, amount);
  }

  /**
   * @dev returns the borrow allowance of the user
   * @param asset The underlying asset of the debt token
   * @param fromUser The user to giving allowance
   * @param toUser The user to give allowance to
   * @param interestRateMode Type of debt: 1 for stable, 2 for variable
   * @return the current allowance of toUser
   **/
  function getBorrowAllowance(
    address fromUser,
    address toUser,
    address asset,
    uint256 interestRateMode
  ) external override view returns (uint256) {
    return
      _borrowAllowance[_reserves[asset].getDebtTokenAddress(interestRateMode)][fromUser][toUser];
  }

  /**
   * @dev Sets allowance to borrow on a certain type of debt asset for a certain user address
   * @param asset The underlying asset of the debt token
   * @param user The user to give allowance to
   * @param interestRateMode Type of debt: 1 for stable, 2 for variable
   * @param amount Allowance amount to borrow
   **/
  function delegateBorrowAllowance(
    address asset,
    address user,
    uint256 interestRateMode,
    uint256 amount
  ) external override {
    _whenNotPaused();
    address debtToken = _reserves[asset].getDebtTokenAddress(interestRateMode);

    _borrowAllowance[debtToken][msg.sender][user] = amount;
    emit BorrowAllowanceDelegated(asset, msg.sender, user, interestRateMode, amount);
  }

  /**
   * @dev Allows users to borrow a specific amount of the reserve currency, provided that the borrower
   * already deposited enough collateral.
   * @param asset the address of the reserve
   * @param amount the amount to be borrowed
   * @param interestRateMode the interest rate mode at which the user wants to borrow. Can be 0 (STABLE) or 1 (VARIABLE)
   * @param referralCode a referral code for integrators
   * @param onBehalfOf address of the user who will receive the debt
   **/
  function borrow(
    address asset,
    uint256 amount,
    uint256 interestRateMode,
    uint16 referralCode,
    address onBehalfOf
  ) external override {
    _whenNotPaused();
    ReserveLogic.ReserveData storage reserve = _reserves[asset];

    if (onBehalfOf != msg.sender) {
      address debtToken = reserve.getDebtTokenAddress(interestRateMode);

      _borrowAllowance[debtToken][onBehalfOf][msg
        .sender] = _borrowAllowance[debtToken][onBehalfOf][msg.sender].sub(
        amount,
        Errors.BORROW_ALLOWANCE_ARE_NOT_ENOUGH
      );
    }
    _executeBorrow(
      ExecuteBorrowParams(
        asset,
        msg.sender,
        onBehalfOf,
        amount,
        interestRateMode,
        reserve.aTokenAddress,
        referralCode,
        true
      )
    );
  }

  /**
   * @notice repays a borrow on the specific reserve, for the specified amount (or for the whole amount, if uint256(-1) is specified).
   * @dev the target user is defined by onBehalfOf. If there is no repayment on behalf of another account,
   * onBehalfOf must be equal to msg.sender.
   * @param asset the address of the reserve on which the user borrowed
   * @param amount the amount to repay, or uint256(-1) if the user wants to repay everything
   * @param onBehalfOf the address for which msg.sender is repaying.
   **/
  function repay(
    address asset,
    uint256 amount,
    uint256 rateMode,
    address onBehalfOf
  ) external override {
    _whenNotPaused();

    ReserveLogic.ReserveData storage reserve = _reserves[asset];

    (uint256 stableDebt, uint256 variableDebt) = Helpers.getUserCurrentDebt(onBehalfOf, reserve);

    ReserveLogic.InterestRateMode interestRateMode = ReserveLogic.InterestRateMode(rateMode);

    //default to max amount
    uint256 paybackAmount = interestRateMode == ReserveLogic.InterestRateMode.STABLE
      ? stableDebt
      : variableDebt;

    if (amount != type(uint256).max && amount < paybackAmount) {
      paybackAmount = amount;
    }

    ValidationLogic.validateRepay(
      reserve,
      amount,
      interestRateMode,
      onBehalfOf,
      stableDebt,
      variableDebt
    );

    reserve.updateState();

    //burns an equivalent amount of debt tokens
    if (interestRateMode == ReserveLogic.InterestRateMode.STABLE) {
      IStableDebtToken(reserve.stableDebtTokenAddress).burn(onBehalfOf, paybackAmount);
    } else {
      IVariableDebtToken(reserve.variableDebtTokenAddress).burn(
        onBehalfOf,
        paybackAmount,
        reserve.variableBorrowIndex
      );
    }

    address aToken = reserve.aTokenAddress;
    reserve.updateInterestRates(asset, aToken, paybackAmount, 0);

    if (stableDebt.add(variableDebt).sub(paybackAmount) == 0) {
      _usersConfig[onBehalfOf].setBorrowing(reserve.id, false);
    }

    IERC20(asset).safeTransferFrom(msg.sender, aToken, paybackAmount);

    emit Repay(asset, onBehalfOf, msg.sender, paybackAmount);
  }

  /**
   * @dev borrowers can user this function to swap between stable and variable borrow rate modes.
   * @param asset the address of the reserve on which the user borrowed
   * @param rateMode the rate mode that the user wants to swap
   **/
  function swapBorrowRateMode(address asset, uint256 rateMode) external override {
    _whenNotPaused();
    ReserveLogic.ReserveData storage reserve = _reserves[asset];

    (uint256 stableDebt, uint256 variableDebt) = Helpers.getUserCurrentDebt(msg.sender, reserve);

    ReserveLogic.InterestRateMode interestRateMode = ReserveLogic.InterestRateMode(rateMode);

    ValidationLogic.validateSwapRateMode(
      reserve,
      _usersConfig[msg.sender],
      stableDebt,
      variableDebt,
      interestRateMode
    );

    reserve.updateState();

    if (interestRateMode == ReserveLogic.InterestRateMode.STABLE) {
      //burn stable rate tokens, mint variable rate tokens
      IStableDebtToken(reserve.stableDebtTokenAddress).burn(msg.sender, stableDebt);
      IVariableDebtToken(reserve.variableDebtTokenAddress).mint(
        msg.sender,
        stableDebt,
        reserve.variableBorrowIndex
      );
    } else {
      //do the opposite
      IVariableDebtToken(reserve.variableDebtTokenAddress).burn(
        msg.sender,
        variableDebt,
        reserve.variableBorrowIndex
      );
      IStableDebtToken(reserve.stableDebtTokenAddress).mint(
        msg.sender,
        variableDebt,
        reserve.currentStableBorrowRate
      );
    }

    reserve.updateInterestRates(asset, reserve.aTokenAddress, 0, 0);

    emit Swap(asset, msg.sender);
  }

  /**
   * @dev rebalances the stable interest rate of a user if current liquidity rate > user stable rate.
   * this is regulated by Aave to ensure that the protocol is not abused, and the user is paying a fair
   * rate. Anyone can call this function.
   * @param asset the address of the reserve
   * @param user the address of the user to be rebalanced
   **/
  function rebalanceStableBorrowRate(address asset, address user) external override {
    
    _whenNotPaused();
    
    ReserveLogic.ReserveData storage reserve = _reserves[asset];

    IERC20 stableDebtToken = IERC20(reserve.stableDebtTokenAddress);
    IERC20 variableDebtToken = IERC20(reserve.variableDebtTokenAddress);
    address aTokenAddress = reserve.aTokenAddress;

    uint256 stableBorrowBalance = IERC20(stableDebtToken).balanceOf(user);

    //if the utilization rate is below 95%, no rebalances are needed
    uint256 totalBorrows = stableDebtToken.totalSupply().add(variableDebtToken.totalSupply()).wadToRay();
    uint256 availableLiquidity = IERC20(asset).balanceOf(aTokenAddress).wadToRay();
    uint256 usageRatio = totalBorrows == 0
      ? 0
      : totalBorrows.rayDiv(availableLiquidity.add(totalBorrows));

    //if the liquidity rate is below REBALANCE_UP_THRESHOLD of the max variable APR at 95% usage,
    //then we allow rebalancing of the stable rate positions.

    uint256 currentLiquidityRate = reserve.currentLiquidityRate;
    uint256 maxVariableBorrowRate = IReserveInterestRateStrategy(
      reserve
        .interestRateStrategyAddress
    )
      .getMaxVariableBorrowRate();

    require(
      usageRatio >= REBALANCE_UP_USAGE_RATIO_THRESHOLD &&
      currentLiquidityRate <=
        maxVariableBorrowRate.percentMul(REBALANCE_UP_LIQUIDITY_RATE_THRESHOLD),
      Errors.INTEREST_RATE_REBALANCE_CONDITIONS_NOT_MET
    );

    reserve.updateState();

    IStableDebtToken(address(stableDebtToken)).burn(user, stableBorrowBalance);
    IStableDebtToken(address(stableDebtToken)).mint(user, stableBorrowBalance, reserve.currentStableBorrowRate);

    reserve.updateInterestRates(asset, aTokenAddress, 0, 0);

    emit RebalanceStableBorrowRate(asset, user);

  }

  /**
   * @dev allows depositors to enable or disable a specific deposit as collateral.
   * @param asset the address of the reserve
   * @param useAsCollateral true if the user wants to user the deposit as collateral, false otherwise.
   **/
  function setUserUseReserveAsCollateral(address asset, bool useAsCollateral) external override {
    _whenNotPaused();
    ReserveLogic.ReserveData storage reserve = _reserves[asset];

    ValidationLogic.validateSetUseReserveAsCollateral(
      reserve,
      asset,
      _reserves,
      _usersConfig[msg.sender],
      _reservesList,
      _addressesProvider.getPriceOracle()
    );

    _usersConfig[msg.sender].setUsingAsCollateral(reserve.id, useAsCollateral);

    if (useAsCollateral) {
      emit ReserveUsedAsCollateralEnabled(asset, msg.sender);
    } else {
      emit ReserveUsedAsCollateralDisabled(asset, msg.sender);
    }
  }

  /**
   * @dev users can invoke this function to liquidate an undercollateralized position.
   * @param asset the address of the collateral to liquidated
   * @param asset the address of the principal reserve
   * @param user the address of the borrower
   * @param purchaseAmount the amount of principal that the liquidator wants to repay
   * @param receiveAToken true if the liquidators wants to receive the aTokens, false if
   * he wants to receive the underlying asset directly
   **/
  function liquidationCall(
    address collateral,
    address asset,
    address user,
    uint256 purchaseAmount,
    bool receiveAToken
  ) external override {
    _whenNotPaused();
    address collateralManager = _addressesProvider.getLendingPoolCollateralManager();

    //solium-disable-next-line
    (bool success, bytes memory result) = collateralManager.delegatecall(
      abi.encodeWithSignature(
        'liquidationCall(address,address,address,uint256,bool)',
        collateral,
        asset,
        user,
        purchaseAmount,
        receiveAToken
      )
    );
    require(success, Errors.LIQUIDATION_CALL_FAILED);

    (uint256 returnCode, string memory returnMessage) = abi.decode(result, (uint256, string));

    if (returnCode != 0) {
      //error found
      revert(string(abi.encodePacked(returnMessage)));
    }
  }

  /**
   * @dev flashes the underlying collateral on an user to swap for the owed asset and repay
   * - Both the owner of the position and other liquidators can execute it
   * - The owner can repay with his collateral at any point, no matter the health factor
   * - Other liquidators can only use this function below 1 HF. To liquidate 50% of the debt > HF 0.98 or the whole below
   * @param collateral The address of the collateral asset
   * @param principal The address of the owed asset
   * @param user Address of the borrower
   * @param principalAmount Amount of the debt to repay. type(uint256).max to repay the maximum possible
   * @param receiver Address of the contract receiving the collateral to swap
   * @param params Variadic bytes param to pass with extra information to the receiver
   **/
  function repayWithCollateral(
    address collateral,
    address principal,
    address user,
    uint256 principalAmount,
    address receiver,
    bytes calldata params
  ) external override {
    _whenNotPaused();
    require(!_flashLiquidationLocked, Errors.REENTRANCY_NOT_ALLOWED);
    _flashLiquidationLocked = true;

    address collateralManager = _addressesProvider.getLendingPoolCollateralManager();

    //solium-disable-next-line
    (bool success, bytes memory result) = collateralManager.delegatecall(
      abi.encodeWithSignature(
        'repayWithCollateral(address,address,address,uint256,address,bytes)',
        collateral,
        principal,
        user,
        principalAmount,
        receiver,
        params
      )
    );
    require(success, Errors.FAILED_REPAY_WITH_COLLATERAL);

    (uint256 returnCode, string memory returnMessage) = abi.decode(result, (uint256, string));

    if (returnCode != 0) {
      revert(string(abi.encodePacked(returnMessage)));
    }

    _flashLiquidationLocked = false;
  }

  struct FlashLoanLocalVars {
    uint256 premium;
    uint256 amountPlusPremium;
    IFlashLoanReceiver receiver;
    address aTokenAddress;
    address oracle;
  }

  /**
   * @dev allows smartcontracts to access the liquidity of the pool within one transaction,
   * as long as the amount taken plus a fee is returned. NOTE There are security concerns for developers of flashloan receiver contracts
   * that must be kept into consideration. For further details please visit https://developers.aave.com
   * @param receiverAddress The address of the contract receiving the funds. The receiver should implement the IFlashLoanReceiver interface.
   * @param asset The address of the principal reserve
   * @param amount The amount requested for this flashloan
   * @param mode Type of the debt to open if the flash loan is not returned. 0 -> Don't open any debt, just revert, 1 -> stable, 2 -> variable
   * @param params Variadic packed params to pass to the receiver as extra information
   * @param referralCode Referral code of the flash loan
   **/
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

  /**
   * @dev Allows an user to release one of his assets deposited in the protocol, even if it is used as collateral, to swap for another.
   * - It's not possible to release one asset to swap for the same
   * @param receiverAddress The address of the contract receiving the funds. The receiver should implement the ISwapAdapter interface
   * @param fromAsset Asset to swap from
   * @param toAsset Asset to swap to
   * @param params a bytes array to be sent (if needed) to the receiver contract with extra data
   **/
  function swapLiquidity(
    address receiverAddress,
    address fromAsset,
    address toAsset,
    uint256 amountToSwap,
    bytes calldata params
  ) external override {
    _whenNotPaused();
    address collateralManager = _addressesProvider.getLendingPoolCollateralManager();

    //solium-disable-next-line
    (bool success, bytes memory result) = collateralManager.delegatecall(
      abi.encodeWithSignature(
        'swapLiquidity(address,address,address,uint256,bytes)',
        receiverAddress,
        fromAsset,
        toAsset,
        amountToSwap,
        params
      )
    );
    require(success, Errors.FAILED_COLLATERAL_SWAP);

    (uint256 returnCode, string memory returnMessage) = abi.decode(result, (uint256, string));

    if (returnCode != 0) {
      revert(string(abi.encodePacked(returnMessage)));
    }
  }

  /**
   * @dev accessory functions to fetch data from the core contract
   **/

  function getReserveConfigurationData(address asset)
    external
    override
    view
    returns (
      uint256 decimals,
      uint256 ltv,
      uint256 liquidationThreshold,
      uint256 liquidationBonus,
      uint256 reserveFactor,
      address interestRateStrategyAddress,
      bool usageAsCollateralEnabled,
      bool borrowingEnabled,
      bool stableBorrowRateEnabled,
      bool isActive,
      bool isFreezed
    )
  {
    ReserveLogic.ReserveData storage reserve = _reserves[asset];

    return (
      reserve.configuration.getDecimals(),
      reserve.configuration.getLtv(),
      reserve.configuration.getLiquidationThreshold(),
      reserve.configuration.getLiquidationBonus(),
      reserve.configuration.getReserveFactor(),
      reserve.interestRateStrategyAddress,
      reserve.configuration.getLtv() != 0,
      reserve.configuration.getBorrowingEnabled(),
      reserve.configuration.getStableRateBorrowingEnabled(),
      reserve.configuration.getActive(),
      reserve.configuration.getFrozen()
    );
  }

  function getReserveTokensAddresses(address asset)
    external
    override
    view
    returns (
      address aTokenAddress,
      address stableDebtTokenAddress,
      address variableDebtTokenAddress
    )
  {
    ReserveLogic.ReserveData storage reserve = _reserves[asset];

    return (
      reserve.aTokenAddress,
      reserve.stableDebtTokenAddress,
      reserve.variableDebtTokenAddress
    );
  }

  function getReserveData(address asset)
    external
    override
    view
    returns (
      uint256 availableLiquidity,
      uint256 totalStableDebt,
      uint256 totalVariableDebt,
      uint256 liquidityRate,
      uint256 variableBorrowRate,
      uint256 stableBorrowRate,
      uint256 averageStableBorrowRate,
      uint256 liquidityIndex,
      uint256 variableBorrowIndex,
      uint40 lastUpdateTimestamp
    )
  {
    ReserveLogic.ReserveData memory reserve = _reserves[asset];

    return (
      IERC20(asset).balanceOf(reserve.aTokenAddress),
      IERC20(reserve.stableDebtTokenAddress).totalSupply(),
      IERC20(reserve.variableDebtTokenAddress).totalSupply(),
      reserve.currentLiquidityRate,
      reserve.currentVariableBorrowRate,
      reserve.currentStableBorrowRate,
      IStableDebtToken(reserve.stableDebtTokenAddress).getAverageStableRate(),
      reserve.liquidityIndex,
      reserve.variableBorrowIndex,
      reserve.lastUpdateTimestamp
    );
  }

  function getUserAccountData(address user)
    external
    override
    view
    returns (
      uint256 totalCollateralETH,
      uint256 totalBorrowsETH,
      uint256 availableBorrowsETH,
      uint256 currentLiquidationThreshold,
      uint256 ltv,
      uint256 healthFactor
    )
  {
    (
      totalCollateralETH,
      totalBorrowsETH,
      ltv,
      currentLiquidationThreshold,
      healthFactor
    ) = GenericLogic.calculateUserAccountData(
      user,
      _reserves,
      _usersConfig[user],
      _reservesList,
      _addressesProvider.getPriceOracle()
    );
    
    availableBorrowsETH = GenericLogic.calculateAvailableBorrowsETH(
      totalCollateralETH,
      totalBorrowsETH,
      ltv
    );
  }

  function getUserReserveData(address asset, address user)
    external
    override
    view
    returns (
      uint256 currentATokenBalance,
      uint256 currentStableDebt,
      uint256 currentVariableDebt,
      uint256 principalStableDebt,
      uint256 scaledVariableDebt,
      uint256 stableBorrowRate,
      uint256 liquidityRate,
      uint40 stableRateLastUpdated,
      bool usageAsCollateralEnabled
    )
  {
    ReserveLogic.ReserveData storage reserve = _reserves[asset];

    currentATokenBalance = IERC20(reserve.aTokenAddress).balanceOf(user);
    (currentStableDebt, currentVariableDebt) = Helpers.getUserCurrentDebt(user, reserve);
    principalStableDebt = IStableDebtToken(reserve.stableDebtTokenAddress).principalBalanceOf(user);
    scaledVariableDebt = IVariableDebtToken(reserve.variableDebtTokenAddress).scaledBalanceOf(user);
    liquidityRate = reserve.currentLiquidityRate;
    stableBorrowRate = IStableDebtToken(reserve.stableDebtTokenAddress).getUserStableRate(user);
    stableRateLastUpdated = IStableDebtToken(reserve.stableDebtTokenAddress).getUserLastUpdated(
      user
    );
    usageAsCollateralEnabled = _usersConfig[user].isUsingAsCollateral(reserve.id);
  }

  function getReserves() external override view returns (address[] memory) {
    return _reservesList;
  }

  receive() external payable {
    revert();
  }

  /**
   * @dev initializes a reserve
   * @param asset the address of the reserve
   * @param aTokenAddress the address of the overlying aToken contract
   * @param interestRateStrategyAddress the address of the interest rate strategy contract
   **/
  function initReserve(
    address asset,
    address aTokenAddress,
    address stableDebtAddress,
    address variableDebtAddress,
    address interestRateStrategyAddress
  ) external override {
    _onlyLendingPoolConfigurator();
    _reserves[asset].init(
      aTokenAddress,
      stableDebtAddress,
      variableDebtAddress,
      interestRateStrategyAddress
    );
    _addReserveToList(asset);
  }

  /**
   * @dev updates the address of the interest rate strategy contract
   * @param asset the address of the reserve
   * @param rateStrategyAddress the address of the interest rate strategy contract
   **/

  function setReserveInterestRateStrategyAddress(address asset, address rateStrategyAddress)
    external
    override
  {
    _onlyLendingPoolConfigurator();
    _reserves[asset].interestRateStrategyAddress = rateStrategyAddress;
  }

  function setConfiguration(address asset, uint256 configuration) external override {
    _onlyLendingPoolConfigurator();
    _reserves[asset].configuration.data = configuration;
  }

  function getConfiguration(address asset)
    external
    override
    view
    returns (ReserveConfiguration.Map memory)
  {
    return _reserves[asset].configuration;
  }

  // internal functions

  struct ExecuteBorrowParams {
    address asset;
    address user;
    address onBehalfOf;
    uint256 amount;
    uint256 interestRateMode;
    address aTokenAddress;
    uint16 referralCode;
    bool releaseUnderlying;
  }

  /**
   * @dev Internal function to execute a borrowing action, allowing to transfer or not the underlying
   * @param vars Input struct for the borrowing action, in order to avoid STD errors
   **/
  function _executeBorrow(ExecuteBorrowParams memory vars) internal {
    ReserveLogic.ReserveData storage reserve = _reserves[vars.asset];
    UserConfiguration.Map storage userConfig = _usersConfig[vars.onBehalfOf];

    address oracle = _addressesProvider.getPriceOracle();

    uint256 amountInETH = IPriceOracleGetter(oracle).getAssetPrice(vars.asset).mul(vars.amount).div(
      10**reserve.configuration.getDecimals()
    );

    ValidationLogic.validateBorrow(
      reserve,
      vars.onBehalfOf,
      vars.amount,
      amountInETH,
      vars.interestRateMode,
      MAX_STABLE_RATE_BORROW_SIZE_PERCENT,
      _reserves,
      userConfig,
      _reservesList,
      oracle
    );

    uint256 reserveId = reserve.id;
    if (!userConfig.isBorrowing(reserveId)) {
      userConfig.setBorrowing(reserveId, true);
    }

    reserve.updateState();

    //caching the current stable borrow rate
    uint256 currentStableRate = 0;

    if (
      ReserveLogic.InterestRateMode(vars.interestRateMode) == ReserveLogic.InterestRateMode.STABLE
    ) {
      currentStableRate = reserve.currentStableBorrowRate;

      IStableDebtToken(reserve.stableDebtTokenAddress).mint(
        vars.onBehalfOf,
        vars.amount,
        currentStableRate
      );
    } else {
      IVariableDebtToken(reserve.variableDebtTokenAddress).mint(
        vars.onBehalfOf,
        vars.amount,
        reserve.variableBorrowIndex
      );
    }

    reserve.updateInterestRates(
      vars.asset,
      vars.aTokenAddress,
      0,
      vars.releaseUnderlying ? vars.amount : 0
    );

    if (vars.releaseUnderlying) {
      IAToken(vars.aTokenAddress).transferUnderlyingTo(vars.user, vars.amount);
    }

    emit Borrow(
      vars.asset,
      vars.user,
      vars.onBehalfOf,
      vars.amount,
      vars.interestRateMode,
      ReserveLogic.InterestRateMode(vars.interestRateMode) == ReserveLogic.InterestRateMode.STABLE
        ? currentStableRate
        : reserve.currentVariableBorrowRate,
      vars.referralCode
    );
  }

  /**
   * @dev adds a reserve to the array of the _reserves address
   **/
  function _addReserveToList(address asset) internal {
    bool reserveAlreadyAdded = false;
    require(_reservesList.length < MAX_NUMBER_RESERVES, Errors.NO_MORE_RESERVES_ALLOWED);
    for (uint256 i = 0; i < _reservesList.length; i++)
      if (_reservesList[i] == asset) {
        reserveAlreadyAdded = true;
      }
    if (!reserveAlreadyAdded) {
      _reserves[asset].id = uint8(_reservesList.length);
      _reservesList.push(asset);
    }
  }

  /**
   * @dev returns the normalized income per unit of asset
   * @param asset the address of the reserve
   * @return the reserve normalized income
   */
  function getReserveNormalizedIncome(address asset) external override view returns (uint256) {
    return _reserves[asset].getNormalizedIncome();
  }

  /**
   * @dev returns the normalized variable debt per unit of asset
   * @param asset the address of the reserve
   * @return the reserve normalized debt
   */
  function getReserveNormalizedVariableDebt(address asset)
    external
    override
    view
    returns (uint256)
  {
    return _reserves[asset].getNormalizedDebt();
  }

  /**
   * @dev validate if a balance decrease for an asset is allowed
   * @param asset the address of the reserve
   * @param user the user related to the balance decrease
   * @param amount the amount being transferred/redeemed
   * @return true if the balance decrease can be allowed, false otherwise
   */
  function balanceDecreaseAllowed(
    address asset,
    address user,
    uint256 amount
  ) external override view returns (bool) {
    _whenNotPaused();
    return
      GenericLogic.balanceDecreaseAllowed(
        asset,
        user,
        amount,
        _reserves,
        _usersConfig[user],
        _reservesList,
        _addressesProvider.getPriceOracle()
      );
  }

  /**
   * @dev Set the _pause state
   * @param val the boolean value to set the current pause state of LendingPool
   */
  function setPause(bool val) external override {
    _onlyLendingPoolConfigurator();

    _paused = val;
    if (_paused) {
      emit Paused();
    } else {
      emit Unpaused();
    }
  }

  /**
   * @dev Returns if the LendingPool is paused
   */
  function paused() external override view returns (bool) {
    return _paused;
  }
}
