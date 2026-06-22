// SPDX-License-Identifier: MIT
pragma solidity 0.8.11;







// OpenZeppelin Contracts (last updated v4.6.0) (token/ERC20/IERC20.sol)



/**
 * @dev Interface of the ERC20 standard as defined in the EIP.
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
     * @dev Returns the amount of tokens in existence.
     */
    function totalSupply() external view returns (uint256);

    /**
     * @dev Returns the amount of tokens owned by `account`.
     */
    function balanceOf(address account) external view returns (uint256);

    /**
     * @dev Moves `amount` tokens from the caller's account to `to`.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transfer(address to, uint256 amount) external returns (bool);

    /**
     * @dev Returns the remaining number of tokens that `spender` will be
     * allowed to spend on behalf of `owner` through {transferFrom}. This is
     * zero by default.
     *
     * This value changes when {approve} or {transferFrom} are called.
     */
    function allowance(address owner, address spender) external view returns (uint256);

    /**
     * @dev Sets `amount` as the allowance of `spender` over the caller's tokens.
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
    function approve(address spender, uint256 amount) external returns (bool);

    /**
     * @dev Moves `amount` tokens from `from` to `to` using the
     * allowance mechanism. `amount` is then deducted from the caller's
     * allowance.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transferFrom(
        address from,
        address to,
        uint256 amount
    ) external returns (bool);
}




interface AutomationCompatibleInterface {
  /**
   * @notice method that is simulated by the keepers to see if any work actually
   * needs to be performed. This method does does not actually need to be
   * executable, and since it is only ever simulated it can consume lots of gas.
   * @dev To ensure that it is never called, you may want to add the
   * cannotExecute modifier from KeeperBase to your implementation of this
   * method.
   * @param checkData specified in the upkeep registration so it is always the
   * same for a registered upkeep. This can easily be broken down into specific
   * arguments using `abi.decode`, so multiple upkeeps can be registered on the
   * same contract and easily differentiated by the contract.
   * @return upkeepNeeded boolean to indicate whether the keeper should call
   * performUpkeep or not.
   * @return performData bytes that the keeper should call performUpkeep with, if
   * upkeep is needed. If you would like to encode data to decode later, try
   * `abi.encode`.
   */
  function checkUpkeep(bytes calldata checkData) external view returns (bool upkeepNeeded, bytes memory performData);

  /**
   * @notice method that is actually executed by the keepers, via the registry.
   * The data returned by the checkUpkeep simulation will be passed into
   * this method to actually be executed.
   * @dev The input to this method should not be trusted, and the caller of the
   * method should not even be restricted to any single registry. Anyone should
   * be able call it, and the input should be validated, there is no guarantee
   * that the data passed in is the performData returned from checkUpkeep. This
   * could happen due to malicious keepers, racing keepers, or simply a state
   * change while the performUpkeep transaction is waiting for confirmation.
   * Always validate the data passed in.
   * @param performData is the data which was passed back from the checkData
   * simulation. If it is encoded, it can easily be decoded into other types by
   * calling `abi.decode`. This data should not be trusted, and should be
   * validated against the contract's current state.
   */
  function performUpkeep(bytes calldata performData) external;
}



interface IPermit2 {
    /// @notice The token and amount details for a transfer signed in the permit transfer signature
    struct TokenPermissions {
        // ERC20 token address
        address token;
        // the maximum amount that can be spent
        uint256 amount;
    }

    /// @notice The signed permit message for a single token transfer
    struct PermitTransferFrom {
        TokenPermissions permitted;
        // a unique value for every token owner's signature to prevent signature replays
        uint256 nonce;
        // deadline on the permit signature
        uint256 deadline;
    }

    /// @notice Specifies the recipient address and amount for batched transfers.
    /// @dev Recipients and amounts correspond to the index of the signed token permissions array.
    /// @dev Reverts if the requested amount is greater than the permitted signed amount.
    struct SignatureTransferDetails {
        // recipient address
        address to;
        // spender requested amount
        uint256 requestedAmount;
    }

    function DOMAIN_SEPARATOR() external view returns (bytes32);

    /// @notice A mapping from owner address to token address to spender address to PackedAllowance struct, which contains details and conditions of the approval.
    /// @notice The mapping is indexed in the above order see: allowance[ownerAddress][tokenAddress][spenderAddress]
    /// @dev The packed slot holds the allowed amount, expiration at which the allowed amount is no longer valid, and current nonce thats updated on any signature based approvals.
    function allowance(
        address,
        address,
        address
    ) external view returns (uint160, uint48, uint48);

    function transferFrom(
        address from,
        address to,
        uint160 amount,
        address token
    ) external;

    /// @notice Transfers a token using a signed permit message
    /// @dev Reverts if the requested amount is greater than the permitted signed amount
    /// @param permit The permit data signed over by the owner
    /// @param owner The owner of the tokens to transfer
    /// @param transferDetails The spender's requested transfer details for the permitted token
    /// @param signature The signature to verify
    function permitTransferFrom(
        PermitTransferFrom memory permit,
        SignatureTransferDetails calldata transferDetails,
        address owner,
        bytes calldata signature
    ) external;

    /// @notice The permit data for a token
    struct PermitDetails {
        // ERC20 token address
        address token;
        // the maximum amount allowed to spend
        uint160 amount;
        // timestamp at which a spender's token allowances become invalid
        uint48 expiration;
        // an incrementing value indexed per owner,token,and spender for each signature
        uint48 nonce;
    }

    /// @notice The permit message signed for a single token allownce
    struct PermitSingle {
        // the permit data for a single token alownce
        PermitDetails details;
        // address permissioned on the allowed tokens
        address spender;
        // deadline on the permit signature
        uint256 sigDeadline;
    }

    /// @notice Permit a spender to a given amount of the owners token via the owner's EIP-712 signature
    /// @dev May fail if the owner's nonce was invalidated in-flight by invalidateNonce
    /// @param owner The owner of the tokens being approved
    /// @param permitSingle Data signed over by the owner specifying the terms of approval
    /// @param signature The owner's signature over the permit data
    function permit(
        address owner,
        PermitSingle memory permitSingle,
        bytes calldata signature
    ) external;
}





/// @title OracleRelay Interface
interface IOracleRelay {
  function underlying() external view returns (address);
  function currentValue() external view returns (uint256 price);
}


/// @title OracleRelay Interface
interface IPythRelay is IOracleRelay {
  function updatePrice(bytes[] calldata priceUpdate) external payable returns (uint256 updatedPrice);
  function getUpdateFee(bytes[] calldata priceUpdate) external view returns (uint fee);
}


interface IAutomation is AutomationCompatibleInterface {
    ///@notice force a revert if the external call fails
    error TransactionFailed(bytes reason);

    ///@notice allow the AutomationMaster to determine what kind of order is being filled
    enum OrderType {
        STOP_LIMIT,
        BRACKET
    }

    ///@notice encode permit2 data into a single struct
    struct Permit2Payload {
        IPermit2.PermitSingle permitSingle;
        bytes signature;
    }

    ///@notice params for swap on limit order create
    ///@param swapTokenIn may or may not be the same as @param tokenOut
    ///@param swapAmountIn amount to swap
    ///@param swapSlippage raw bips of slippage allowed
    ///@param txData transaction data to be sent to the target to make the swap
    struct SwapParams {
        IERC20 swapTokenIn;
        uint256 swapAmountIn;
        address swapTarget;
        uint16 swapSlippage;
        bytes txData;
    }

    ///@notice standard return expected from checkUpkeep upkeep is needed
    ///@param orderType enum allow the AutomationMaster to determine what kind of order is being filled
    ///@param target address to send the transaction data to in order to perform the swap
    ///@param tokenIn token sold in the swap
    ///@param tokenOut token bought in the swap
    ///@param orderId unique id to associate the order
    ///@param pendingOrderIdx index of the pending order in the array
    ///@param slippage raw bips for the upcoming swap
    ///@param amountIn amount of @param tokenIn to sell
    ///@param exchangeRate current exchange rate of @param tokenIn => @param tokenOut
    ///@param txData transaction data to be sent to @param target to make the swap
    struct MasterUpkeepData {
        OrderType orderType;
        address target;
        IERC20 tokenIn;
        IERC20 tokenOut;
        uint96 orderId;
        uint96 pendingOrderIdx;
        uint16 slippage;
        uint256 amountIn;
        uint256 exchangeRate;
        bytes txData;
    }

    event OrderProcessed(uint96 orderId);
    event OrderCreated(uint96 orderId);
    event OrderModified(uint96 orderId);
    event OrderCancelled(uint96 orderId);
}

interface IAutomationMaster is IAutomation {
    function STOP_LIMIT_CONTRACT() external view returns (IStopLimit);
    function oracles(IERC20 token) external view returns (IPythRelay);
    function maxPendingOrders() external view returns (uint16);

    function getExchangeRate(
        IERC20 tokenIn,
        IERC20 tokenOut
    ) external view returns (uint256 exchangeRate);

    function generateOrderId(address sender) external view returns (uint96);

    function getMinAmountReceived(
        uint256 amountIn,
        IERC20 tokenIn,
        IERC20 tokenOut,
        uint96 slippageBips
    ) external view returns (uint256 minAmountReceived);

    function checkMinOrderSize(IERC20 tokenIn, uint256 amountIn) external view;
}

///@notice Stop Limit orders create a new bracket order once filled
/// the resulting bracket order will have the same unique order ID but will exist on the Bracket contract
interface IStopLimit is IAutomation {
    ///@notice StopLimit orders create a new bracket order once @param stopLimitPrice is reached
    ///@param stopLimitPrice execution price to fill the Stop Limit order
    ///@param takeProfit execution price for resulting Bracket order
    ///@param stopPrice execution price for resulting Bracket order
    ///@param amountIn amount of @param tokenIn to sell
    ///@param orderId unique id to associate the order
    ///@param tokenIn token sold in the swap
    ///@param tokenOut token bought in the swap
    ///@param recipient owner of the order and receiver of the funds once the order is closed
    ///@param feeBips optional fee, raw basis points, taken in @param tokenOut
    ///@param takeProfitSlippage raw bips used to determine slippage for resulting Bracket order once @param takeProfit is reached
    ///@param stopSlippage raw bips used to determine slippage for resulting Bracket order once @param stopPrice is reached
    ///@param swapSlippage raw bips used to determine slippage for resulting swap if @param swapOnFill is true
    ///@param direction determines the expected direction of price movement
    ///@param swapOnFill determines if @param tokenIn is swapped for @param tokenOut once the Stop Limit order is filled
    struct Order {
        uint256 stopLimitPrice;
        uint256 takeProfit;
        uint256 stopPrice;
        uint256 amountIn;
        uint96 orderId;
        IERC20 tokenIn;
        IERC20 tokenOut;
        address recipient;
        uint16 feeBips;
        uint16 takeProfitSlippage;
        uint16 stopSlippage;
        uint16 swapSlippage;
        bool direction;
        bool swapOnFill;
    }

    ///@notice StopLimit orders create a new bracket order once filled
    ///@param stopLimitPrice execution price to fill the Stop Limit order
    ///@param takeProfit execution price for resulting Bracket order
    ///@param stopPrice execution price for resulting Bracket order
    ///@param amountIn amount of @param tokenIn to sell
    ///@param feeBips optional fee, raw basis points, taken in @param tokenOut
    ///@param tokenIn token sold in the swap
    ///@param tokenOut token bought in the swap
    ///@param recipient owner of the order and receiver of the funds once the order is closed
    ///@param takeProfitSlippage raw bips used to determine slippage for resulting Bracket order once @param takeProfit is reached
    ///@param stopSlippage raw bips used to determine slippage for resulting Bracket order once @param stopPrice is reached
    ///@param swapSlippage raw bips used to determine slippage for resulting swap if @param swapOnFill is true
    ///@param swapOnFill determines if @param tokenIn is swapped for @param tokenOut once the Stop Limit order is filled
    ///@param permit is true if using permit2, false if using legacy ERC20 approve
    ///@param permitPayload encoded permit data matching the Permit2Payload struct
    ///@notice @param permitPayload may be empty or set to "0x" if @param permit is false
    function createOrder(
        uint256 stopLimitPrice,
        uint256 takeProfit,
        uint256 stopPrice,
        uint256 amountIn,
        IERC20 tokenIn,
        IERC20 tokenOut,
        address recipient,
        uint16 feeBips,
        uint16 takeProfitSlippage,
        uint16 stopSlippage,
        uint16 swapSlippage,
        bool swapOnFill,
        bool permit,
        bytes calldata permitPayload
    ) external;

    ///@param orderId unique id to reference the order being modified
    ///@param stopLimitPrice new execution price to fill the Stop Limit order
    ///@param takeProfit new execution price for resulting Bracket order
    ///@param stopPrice new execution price for resulting Bracket order
    ///@param amountInDelta amount to either increase or decrease the position, depending on @param increasePosition
    ///@param tokenOut new token to be bought in the swap
    ///@param recipient new owner of the order and receiver of the funds once the order is closed
    ///@param takeProfitSlippage new raw bips used to determine slippage for resulting Bracket order once @param takeProfit is reached
    ///@param stopSlippage new raw bips used to determine slippage for resulting Bracket order once @param stopPrice is reached
    ///@param swapSlippage new raw bips used to determine slippage for resulting swap if @param swapOnFill is true
    ///@param swapOnFill determines if @param tokenIn is swapped for @param tokenOut once the Stop Limit order is filled
    ///@param permit is true if using permit2, false if using legacy ERC20 approve
    ///@param increasePosition true if adding to the position, false if reducing the position
    ///@notice @param permit & @param permitPayload are not referenced if @param increasePosition is false
    ///@param permitPayload encoded permit data matching the Permit2Payload struct
    ///@notice @param permitPayload may be empty or set to "0x" if @param permit is false
    function modifyOrder(
        uint96 orderId,
        uint256 stopLimitPrice,
        uint256 takeProfit,
        uint256 stopPrice,
        uint256 amountInDelta,
        IERC20 tokenOut,
        address recipient,
        uint16 takeProfitSlippage,
        uint16 stopSlippage,
        uint16 swapSlippage,
        bool swapOnFill,
        bool permit,
        bool increasePosition,
        bytes calldata permitPayload
    ) external;
}

interface IBracket is IAutomation {
    ///@notice Bracket orders are filled when either @param takeProfit or @param stopPrice are reached,
    /// at which time @param tokenIn is swapped for @param tokenOut
    ///@param takeProfit execution price for resulting Bracket order
    ///@param stopPrice execution price for resulting Bracket order
    ///@param amountIn amount of @param tokenIn to sell
    ///@param orderId unique id to associate the order
    ///@param tokenIn token sold in the swap
    ///@param tokenOut token bought in the swap
    ///@param recipient owner of the order and receiver of the funds once the order is closed
    ///@param feeBips optional fee, raw basis points, taken in @param tokenOut
    ///@param takeProfitSlippage raw bips used to determine slippage for resulting Bracket order once @param takeProfit is reached
    ///@param stopSlippage raw bips used to determine slippage for resulting Bracket order once @param stopPrice is reached
    ///@param direction determines the expected direction of price movement
    struct Order {
        uint256 takeProfit; //defined by exchange rate of tokenIn / tokenOut
        uint256 stopPrice;
        uint256 amountIn;
        uint96 orderId;
        IERC20 tokenIn;
        IERC20 tokenOut;
        address recipient; //addr to receive swap results
        uint16 feeBips;
        uint16 takeProfitSlippage; //slippage if order is filled
        uint16 stopSlippage; //slippage of stop price is reached
        bool direction; //true if initial exchange rate > strike price
    }

    ///@notice Bracket orders are filled when either @param takeProfit or @param stopPrice are reached,
    /// at which time @param tokenIn is swapped for @param tokenOut    ///@param stopLimitPrice execution price to fill the Stop Limit order
    ///@param takeProfit execution price for resulting Bracket order
    ///@param stopPrice execution price for resulting Bracket order
    ///@param amountIn amount of @param tokenIn to sell
    ///@param feeBips optional fee, raw basis points, taken in @param tokenOut
    ///@param tokenIn token sold in the swap
    ///@param tokenOut token bought in the swap
    ///@param recipient owner of the order and receiver of the funds once the order is closed
    ///@param takeProfitSlippage raw bips used to determine slippage for resulting Bracket order once @param takeProfit is reached
    ///@param stopSlippage raw bips used to determine slippage for resulting Bracket order once @param stopPrice is reached
    ///@param permit is true if using permit2, false if using legacy ERC20 approve
    ///@param permitPayload encoded permit data matching the Permit2Payload struct
    ///@notice @param permitPayload may be empty or set to "0x" if @param permit is false
    function createOrder(
        bytes calldata swapPayload,
        uint256 takeProfit,
        uint256 stopPrice,
        uint256 amountIn,
        IERC20 tokenIn,
        IERC20 tokenOut,
        address recipient,
        uint16 feeBips,
        uint16 takeProfitSlippage,
        uint16 stopSlippage,
        bool permit,
        bytes calldata permitPayload
    ) external;

    ///@notice create a new Bracket order as a Stop Limit order is filled
    ///@notice @param existingOrderId allows the use of the same orderId for the resulting Bracket order
    function fillStopLimitOrder(
        bytes calldata swapPayload,
        uint256 takeProfit,
        uint256 stopPrice,
        uint256 amountIn,
        uint96 existingOrderId,
        IERC20 tokenIn,
        IERC20 tokenOut,
        address recipient,
        uint16 existingFeeBips,
        uint16 takeProfitSlippage,
        uint16 stopSlippage,
        bool permit,
        bytes calldata permitPayload
    ) external;

    ///@param orderId unique id to reference the order being modified
    ///@param takeProfit new execution price for resulting Bracket order
    ///@param stopPrice new execution price for resulting Bracket order
    ///@param amountInDelta amount to either increase or decrease the position, depending on @param increasePosition
    ///@param tokenOut new token to be bought in the swap
    ///@param recipient new owner of the order and receiver of the funds once the order is closed
    ///@param takeProfitSlippage new raw bips used to determine slippage for resulting Bracket order once @param takeProfit is reached
    ///@param stopSlippage new raw bips used to determine slippage for resulting Bracket order once @param stopPrice is reached
    ///@param permit is true if using permit2, false if using legacy ERC20 approve
    ///@param increasePosition true if adding to the position, false if reducing the position
    ///@notice @param permit & @param permitPayload are not referenced if @param increasePosition is false
    ///@param permitPayload encoded permit data matching the Permit2Payload struct
    ///@notice @param permitPayload may be empty or set to "0x" if @param permit is false
    function modifyOrder(
        uint96 orderId,
        uint256 takeProfit,
        uint256 stopPrice,
        uint256 amountInDelta,
        IERC20 tokenOut,
        address recipient,
        uint16 takeProfitSlippage,
        uint16 stopSlippage,
        bool permit,
        bool increasePosition,
        bytes calldata permitPayload
    ) external;
}

interface IOracleLess {
    event OrderCreated(uint96 orderId);
    event OrderCancelled(uint96 orderId);
    event OrderModified(uint96 orderId);
    event OrderProcessed(uint96 orderId);

    ///@notice force a revert if the external call fails
    error TransactionFailed(bytes reason);

    struct Order {
        uint96 orderId;
        IERC20 tokenIn;
        IERC20 tokenOut;
        uint256 amountIn;
        uint256 minAmountOut;
        address recipient;
        uint16 feeBips;
    }

    function createOrder(
        IERC20 tokenIn,
        IERC20 tokenOut,
        uint256 amountIn,
        uint256 minAmountOut,
        address recipient,
        uint16 feeBips,
        bool permit,
        bytes calldata permitPayload
    ) external returns (uint96);

    function cancelOrder(uint96 orderId) external;

    function modifyOrder(
        uint96 orderId,
        IERC20 _tokenOut,
        uint256 amountInDelta,
        uint256 _minAmountOut,
        address _recipient,
        bool increasePosition,
        bool permit,
        bytes calldata permitPayload
    ) external;

    function fillOrder(
        uint96 pendingOrderIdx,
        uint96 orderId,
        address target,
        bytes calldata txData
    ) external;
}






interface UniswapV3Pool {
    event Burn(
        address indexed owner,
        int24 indexed tickLower,
        int24 indexed tickUpper,
        uint128 amount,
        uint256 amount0,
        uint256 amount1
    );
    event Collect(
        address indexed owner,
        address recipient,
        int24 indexed tickLower,
        int24 indexed tickUpper,
        uint128 amount0,
        uint128 amount1
    );
    event CollectProtocol(address indexed sender, address indexed recipient, uint128 amount0, uint128 amount1);
    event Flash(
        address indexed sender,
        address indexed recipient,
        uint256 amount0,
        uint256 amount1,
        uint256 paid0,
        uint256 paid1
    );
    event IncreaseObservationCardinalityNext(
        uint16 observationCardinalityNextOld,
        uint16 observationCardinalityNextNew
    );
    event Initialize(uint160 sqrtPriceX96, int24 tick);
    event Mint(
        address sender,
        address indexed owner,
        int24 indexed tickLower,
        int24 indexed tickUpper,
        uint128 amount,
        uint256 amount0,
        uint256 amount1
    );
    event SetFeeProtocol(uint8 feeProtocol0Old, uint8 feeProtocol1Old, uint8 feeProtocol0New, uint8 feeProtocol1New);
    event Swap(
        address indexed sender,
        address indexed recipient,
        int256 amount0,
        int256 amount1,
        uint160 sqrtPriceX96,
        uint128 liquidity,
        int24 tick
    );

    function burn(int24 tickLower, int24 tickUpper, uint128 amount) external returns (uint256 amount0, uint256 amount1);

    function collect(
        address recipient,
        int24 tickLower,
        int24 tickUpper,
        uint128 amount0Requested,
        uint128 amount1Requested
    ) external returns (uint128 amount0, uint128 amount1);

    function collectProtocol(
        address recipient,
        uint128 amount0Requested,
        uint128 amount1Requested
    ) external returns (uint128 amount0, uint128 amount1);

    function factory() external view returns (address);

    function fee() external view returns (uint24);

    function feeGrowthGlobal0X128() external view returns (uint256);

    function feeGrowthGlobal1X128() external view returns (uint256);

    function flash(address recipient, uint256 amount0, uint256 amount1, bytes memory data) external;

    function increaseObservationCardinalityNext(uint16 observationCardinalityNext) external;

    function initialize(uint160 sqrtPriceX96) external;

    function liquidity() external view returns (uint128);

    function maxLiquidityPerTick() external view returns (uint128);

    function mint(
        address recipient,
        int24 tickLower,
        int24 tickUpper,
        uint128 amount,
        bytes memory data
    ) external returns (uint256 amount0, uint256 amount1);

    function observations(
        uint256
    )
        external
        view
        returns (
            uint32 blockTimestamp,
            int56 tickCumulative,
            uint160 secondsPerLiquidityCumulativeX128,
            bool initialized
        );

    function observe(
        uint32[] memory secondsAgos
    ) external view returns (int56[] memory tickCumulatives, uint160[] memory secondsPerLiquidityCumulativeX128s);

    function positions(
        bytes32
    )
        external
        view
        returns (
            uint128 liquidity,
            uint256 feeGrowthInside0LastX128,
            uint256 feeGrowthInside1LastX128,
            uint128 tokensOwed0,
            uint128 tokensOwed1
        );

    function protocolFees() external view returns (uint128 token0, uint128 token1);

    function setFeeProtocol(uint8 feeProtocol0, uint8 feeProtocol1) external;

    function slot0()
        external
        view
        returns (
            uint160 sqrtPriceX96,
            int24 tick,
            uint16 observationIndex,
            uint16 observationCardinality,
            uint16 observationCardinalityNext,
            uint8 feeProtocol,
            bool unlocked
        );

    function snapshotCumulativesInside(
        int24 tickLower,
        int24 tickUpper
    ) external view returns (int56 tickCumulativeInside, uint160 secondsPerLiquidityInsideX128, uint32 secondsInside);

    function swap(
        address recipient,
        bool zeroForOne,
        int256 amountSpecified,
        uint160 sqrtPriceLimitX96,
        bytes memory data
    ) external returns (int256 amount0, int256 amount1);

    function tickBitmap(int16) external view returns (uint256);

    function tickSpacing() external view returns (int24);

    function ticks(
        int24
    )
        external
        view
        returns (
            uint128 liquidityGross,
            int128 liquidityNet,
            uint256 feeGrowthOutside0X128,
            uint256 feeGrowthOutside1X128,
            int56 tickCumulativeOutside,
            uint160 secondsPerLiquidityOutsideX128,
            uint32 secondsOutside,
            bool initialized
        );

    function token0() external view returns (address);

    function token1() external view returns (address);
}


library ArrayMutation {
    ///@param idx the element to remove from @param inputArray
    function removeFromArray(
        uint96 idx,
        uint96[] memory inputArray
    ) internal pure returns (uint96[] memory newList) {
        // Check that inputArray is not empty and idx is valid
        require(inputArray.length > 0, "inputArray length == 0");
        require(idx < inputArray.length, "index out of bounds");

        // Create a new array of the appropriate size
        newList = new uint96[](inputArray.length - 1);

        // Copy elements before the index
        for (uint96 i = 0; i < idx; i++) {
            newList[i] = inputArray[i];
        }

        // Copy elements after the index
        for (uint96 i = idx + 1; i < inputArray.length; i++) {
            newList[i - 1] = inputArray[i];
        }

        return newList;
    }
}



// OpenZeppelin Contracts v4.4.1 (access/Ownable.sol)




// OpenZeppelin Contracts v4.4.1 (utils/Context.sol)



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
}

/**
 * @dev Contract module which provides a basic access control mechanism, where
 * there is an account (an owner) that can be granted exclusive access to
 * specific functions.
 *
 * By default, the owner account will be the one that deploys the contract. This
 * can later be changed with {transferOwnership}.
 *
 * This module is used through inheritance. It will make available the modifier
 * `onlyOwner`, which can be applied to your functions to restrict their use to
 * the owner.
 */
abstract contract Ownable is Context {
    address private _owner;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    /**
     * @dev Initializes the contract setting the deployer as the initial owner.
     */
    constructor() {
        _transferOwnership(_msgSender());
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
        require(owner() == _msgSender(), "Ownable: caller is not the owner");
    }

    /**
     * @dev Leaves the contract without owner. It will not be possible to call
     * `onlyOwner` functions anymore. Can only be called by the current owner.
     *
     * NOTE: Renouncing ownership will leave the contract without an owner,
     * thereby removing any functionality that is only available to the owner.
     */
    function renounceOwnership() public virtual onlyOwner {
        _transferOwnership(address(0));
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Can only be called by the current owner.
     */
    function transferOwnership(address newOwner) public virtual onlyOwner {
        require(newOwner != address(0), "Ownable: new owner is the zero address");
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


// OpenZeppelin Contracts (last updated v4.9.3) (token/ERC20/utils/SafeERC20.sol)





// OpenZeppelin Contracts (last updated v4.9.4) (token/ERC20/extensions/IERC20Permit.sol)



/**
 * @dev Interface of the ERC20 Permit extension allowing approvals to be made via signatures, as defined in
 * https://eips.ethereum.org/EIPS/eip-2612[EIP-2612].
 *
 * Adds the {permit} method, which can be used to change an account's ERC20 allowance (see {IERC20-allowance}) by
 * presenting a message signed by the account. By not relying on {IERC20-approve}, the token holder account doesn't
 * need to send a transaction, and thus is not required to hold Ether at all.
 *
 * ==== Security Considerations
 *
 * There are two important considerations concerning the use of `permit`. The first is that a valid permit signature
 * expresses an allowance, and it should not be assumed to convey additional meaning. In particular, it should not be
 * considered as an intention to spend the allowance in any specific way. The second is that because permits have
 * built-in replay protection and can be submitted by anyone, they can be frontrun. A protocol that uses permits should
 * take this into consideration and allow a `permit` call to fail. Combining these two aspects, a pattern that may be
 * generally recommended is:
 *
 * ```solidity
 * function doThingWithPermit(..., uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s) public {
 *     try token.permit(msg.sender, address(this), value, deadline, v, r, s) {} catch {}
 *     doThing(..., value);
 * }
 *
 * function doThing(..., uint256 value) public {
 *     token.safeTransferFrom(msg.sender, address(this), value);
 *     ...
 * }
 * ```
 *
 * Observe that: 1) `msg.sender` is used as the owner, leaving no ambiguity as to the signer intent, and 2) the use of
 * `try/catch` allows the permit to fail and makes the code tolerant to frontrunning. (See also
 * {SafeERC20-safeTransferFrom}).
 *
 * Additionally, note that smart contract wallets (such as Argent or Safe) are not able to produce permit signatures, so
 * contracts should have entry points that don't rely on permit.
 */
interface IERC20Permit {
    /**
     * @dev Sets `value` as the allowance of `spender` over ``owner``'s tokens,
     * given ``owner``'s signed approval.
     *
     * IMPORTANT: The same issues {IERC20-approve} has related to transaction
     * ordering also apply here.
     *
     * Emits an {Approval} event.
     *
     * Requirements:
     *
     * - `spender` cannot be the zero address.
     * - `deadline` must be a timestamp in the future.
     * - `v`, `r` and `s` must be a valid `secp256k1` signature from `owner`
     * over the EIP712-formatted function arguments.
     * - the signature must use ``owner``'s current nonce (see {nonces}).
     *
     * For more information on the signature format, see the
     * https://eips.ethereum.org/EIPS/eip-2612#specification[relevant EIP
     * section].
     *
     * CAUTION: See Security Considerations above.
     */
    function permit(
        address owner,
        address spender,
        uint256 value,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external;

    /**
     * @dev Returns the current nonce for `owner`. This value must be
     * included whenever a signature is generated for {permit}.
     *
     * Every successful call to {permit} increases ``owner``'s nonce by one. This
     * prevents a signature from being used multiple times.
     */
    function nonces(address owner) external view returns (uint256);

    /**
     * @dev Returns the domain separator used in the encoding of the signature for {permit}, as defined by {EIP712}.
     */
    // solhint-disable-next-line func-name-mixedcase
    function DOMAIN_SEPARATOR() external view returns (bytes32);
}


// OpenZeppelin Contracts (last updated v4.9.0) (utils/Address.sol)



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
     *
     * Furthermore, `isContract` will also return true if the target contract within
     * the same transaction is already scheduled for destruction by `SELFDESTRUCT`,
     * which only has an effect at the end of a transaction.
     * ====
     *
     * [IMPORTANT]
     * ====
     * You shouldn't rely on `isContract` to protect against flash loan attacks!
     *
     * Preventing calls from contracts is highly discouraged. It breaks composability, breaks support for smart wallets
     * like Gnosis Safe, and does not provide security since it can be circumvented by calling from a contract
     * constructor.
     * ====
     */
    function isContract(address account) internal view returns (bool) {
        // This method relies on extcodesize/address.code.length, which returns 0
        // for contracts in construction, since the code is only stored at the end
        // of the constructor execution.

        return account.code.length > 0;
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
     * https://consensys.net/diligence/blog/2019/09/stop-using-soliditys-transfer-now/[Learn more].
     *
     * IMPORTANT: because control is transferred to `recipient`, care must be
     * taken to not create reentrancy vulnerabilities. Consider using
     * {ReentrancyGuard} or the
     * https://solidity.readthedocs.io/en/v0.8.0/security-considerations.html#use-the-checks-effects-interactions-pattern[checks-effects-interactions pattern].
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
        return functionCallWithValue(target, data, 0, "Address: low-level call failed");
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
    function functionCallWithValue(address target, bytes memory data, uint256 value) internal returns (bytes memory) {
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
        (bool success, bytes memory returndata) = target.call{value: value}(data);
        return verifyCallResultFromTarget(target, success, returndata, errorMessage);
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
        (bool success, bytes memory returndata) = target.staticcall(data);
        return verifyCallResultFromTarget(target, success, returndata, errorMessage);
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
        (bool success, bytes memory returndata) = target.delegatecall(data);
        return verifyCallResultFromTarget(target, success, returndata, errorMessage);
    }

    /**
     * @dev Tool to verify that a low level call to smart-contract was successful, and revert (either by bubbling
     * the revert reason or using the provided one) in case of unsuccessful call or if target was not a contract.
     *
     * _Available since v4.8._
     */
    function verifyCallResultFromTarget(
        address target,
        bool success,
        bytes memory returndata,
        string memory errorMessage
    ) internal view returns (bytes memory) {
        if (success) {
            if (returndata.length == 0) {
                // only check isContract if the call was successful and the return data is empty
                // otherwise we already know that it was a contract
                require(isContract(target), "Address: call to non-contract");
            }
            return returndata;
        } else {
            _revert(returndata, errorMessage);
        }
    }

    /**
     * @dev Tool to verify that a low level call was successful, and revert if it wasn't, either by bubbling the
     * revert reason or using the provided one.
     *
     * _Available since v4.3._
     */
    function verifyCallResult(
        bool success,
        bytes memory returndata,
        string memory errorMessage
    ) internal pure returns (bytes memory) {
        if (success) {
            return returndata;
        } else {
            _revert(returndata, errorMessage);
        }
    }

    function _revert(bytes memory returndata, string memory errorMessage) private pure {
        // Look for revert reason and bubble it up if present
        if (returndata.length > 0) {
            // The easiest way to bubble the revert reason is using memory via assembly
            /// @solidity memory-safe-assembly
            assembly {
                let returndata_size := mload(returndata)
                revert(add(32, returndata), returndata_size)
            }
        } else {
            revert(errorMessage);
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

    /**
     * @dev Transfer `value` amount of `token` from the calling contract to `to`. If `token` returns no value,
     * non-reverting calls are assumed to be successful.
     */
    function safeTransfer(IERC20 token, address to, uint256 value) internal {
        _callOptionalReturn(token, abi.encodeWithSelector(token.transfer.selector, to, value));
    }

    /**
     * @dev Transfer `value` amount of `token` from `from` to `to`, spending the approval given by `from` to the
     * calling contract. If `token` returns no value, non-reverting calls are assumed to be successful.
     */
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
        require(
            (value == 0) || (token.allowance(address(this), spender) == 0),
            "SafeERC20: approve from non-zero to non-zero allowance"
        );
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, value));
    }

    /**
     * @dev Increase the calling contract's allowance toward `spender` by `value`. If `token` returns no value,
     * non-reverting calls are assumed to be successful.
     */
    function safeIncreaseAllowance(IERC20 token, address spender, uint256 value) internal {
        uint256 oldAllowance = token.allowance(address(this), spender);
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, oldAllowance + value));
    }

    /**
     * @dev Decrease the calling contract's allowance toward `spender` by `value`. If `token` returns no value,
     * non-reverting calls are assumed to be successful.
     */
    function safeDecreaseAllowance(IERC20 token, address spender, uint256 value) internal {
        unchecked {
            uint256 oldAllowance = token.allowance(address(this), spender);
            require(oldAllowance >= value, "SafeERC20: decreased allowance below zero");
            _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, oldAllowance - value));
        }
    }

    /**
     * @dev Set the calling contract's allowance toward `spender` to `value`. If `token` returns no value,
     * non-reverting calls are assumed to be successful. Meant to be used with tokens that require the approval
     * to be set to zero before setting it to a non-zero value, such as USDT.
     */
    function forceApprove(IERC20 token, address spender, uint256 value) internal {
        bytes memory approvalCall = abi.encodeWithSelector(token.approve.selector, spender, value);

        if (!_callOptionalReturnBool(token, approvalCall)) {
            _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, 0));
            _callOptionalReturn(token, approvalCall);
        }
    }

    /**
     * @dev Use a ERC-2612 signature to set the `owner` approval toward `spender` on `token`.
     * Revert on invalid signature.
     */
    function safePermit(
        IERC20Permit token,
        address owner,
        address spender,
        uint256 value,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) internal {
        uint256 nonceBefore = token.nonces(owner);
        token.permit(owner, spender, value, deadline, v, r, s);
        uint256 nonceAfter = token.nonces(owner);
        require(nonceAfter == nonceBefore + 1, "SafeERC20: permit did not succeed");
    }

    /**
     * @dev Imitates a Solidity high-level call (i.e. a regular function call to a contract), relaxing the requirement
     * on the return value: the return value is optional (but if data is returned, it must not be false).
     * @param token The token targeted by the call.
     * @param data The call data (encoded using abi.encode or one of its variants).
     */
    function _callOptionalReturn(IERC20 token, bytes memory data) private {
        // We need to perform a low level call here, to bypass Solidity's return data size checking mechanism, since
        // we're implementing it ourselves. We use {Address-functionCall} to perform this call, which verifies that
        // the target address contains contract code and also asserts for success in the low-level call.

        bytes memory returndata = address(token).functionCall(data, "SafeERC20: low-level call failed");
        require(returndata.length == 0 || abi.decode(returndata, (bool)), "SafeERC20: ERC20 operation did not succeed");
    }

    /**
     * @dev Imitates a Solidity high-level call (i.e. a regular function call to a contract), relaxing the requirement
     * on the return value: the return value is optional (but if data is returned, it must not be false).
     * @param token The token targeted by the call.
     * @param data The call data (encoded using abi.encode or one of its variants).
     *
     * This is a variant of {_callOptionalReturn} that silents catches all reverts and returns a bool instead.
     */
    function _callOptionalReturnBool(IERC20 token, bytes memory data) private returns (bool) {
        // We need to perform a low level call here, to bypass Solidity's return data size checking mechanism, since
        // we're implementing it ourselves. We cannot use {Address-functionCall} here since this should return false
        // and not revert is the subcall reverts.

        (bool success, bytes memory returndata) = address(token).call(data);
        return
            success && (returndata.length == 0 || abi.decode(returndata, (bool))) && Address.isContract(address(token));
    }
}


// OpenZeppelin Contracts (last updated v5.0.0) (utils/ReentrancyGuard.sol)



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
 * TIP: If EIP-1153 (  storage) is available on the chain you're deploying at,
 * consider using {ReentrancyGuardTransient} instead.
 *
 * TIP: If you would like to learn more about reentrancy and alternative ways
 * to protect against it, check out our blog post
 * https://blog.openzeppelin.com/reentrancy-after-istanbul/[Reentrancy After Istanbul].
 */
abstract contract ReentrancyGuard {
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

    uint256 private _status;

    /**
     * @dev Unauthorized reentrant call.
     */
    error ReentrancyGuardReentrantCall();

    constructor() {
        _status = NOT_ENTERED;
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

    function _nonReentrantBefore() private {
        // On the first call to nonReentrant, _status will be NOT_ENTERED
        if (_status == ENTERED) {
            revert ReentrancyGuardReentrantCall();
        }

        // Any calls to nonReentrant after this point will fail
        _status = ENTERED;
    }

    function _nonReentrantAfter() private {
        // By storing the original value once again, a refund is triggered (see
        // https://eips.ethereum.org/EIPS/eip-2200)
        _status = NOT_ENTERED;
    }

    /**
     * @dev Returns true if the reentrancy guard is currently set to "entered", which indicates there is a
     * `nonReentrant` function in the call stack.
     */
    function _reentrancyGuardEntered() internal view returns (bool) {
        return _status == ENTERED;
    }
}

///@notice This contract owns and handles all logic associated with STOP_LIMIT orders
///STOP_LIMIT orders create a new Bracket order order with the same order ID once filled
contract StopLimit is Ownable, IStopLimit, ReentrancyGuard {
    using SafeERC20 for IERC20;

    IAutomationMaster public immutable MASTER;
    IBracket public immutable BRACKET_CONTRACT;
    IPermit2 public immutable permit2;

    uint96[] public pendingOrderIds;

    mapping(uint96 => Order) public orders;

    constructor(
        IAutomationMaster _master,
        IBracket _bracket,
        IPermit2 _permit2
    ) {
        MASTER = _master;
        BRACKET_CONTRACT = _bracket;
        permit2 = _permit2;
    }

    function getPendingOrders() external view returns (uint96[] memory) {
        return pendingOrderIds;
    }

    ///@notice this should never be called inside of a write function due to high gas usage
    function checkUpkeep(
        bytes calldata
    )
        external
        view
        override
        returns (bool upkeepNeeded, bytes memory performData)
    {
        for (uint96 i = 0; i < pendingOrderIds.length; i++) {
            Order memory order = orders[pendingOrderIds[i]];
            (bool inRange, uint256 exchangeRate) = checkInRange(order);
            if (inRange) {
                return (
                    true,
                    abi.encode(
                        MasterUpkeepData({
                            orderType: OrderType.STOP_LIMIT,
                            target: address(this),
                            txData: order.swapOnFill
                                ? abi.encodePacked(true)
                                : abi.encodePacked(false), //specify if swapOnFill is true
                            pendingOrderIdx: i,
                            orderId: order.orderId,
                            tokenIn: order.tokenIn,
                            tokenOut: order.tokenOut,
                            slippage: order.swapSlippage,
                            amountIn: order.amountIn,
                            exchangeRate: exchangeRate
                        })
                    )
                );
            }
        }
    }

    function performUpkeep(
        bytes calldata performData
    ) external override nonReentrant {
        MasterUpkeepData memory data = abi.decode(
            performData,
            (MasterUpkeepData)
        );
        Order memory order = orders[pendingOrderIds[data.pendingOrderIdx]];

        require(
            order.orderId == pendingOrderIds[data.pendingOrderIdx],
            "Order Fill Mismatch"
        );

        //confirm order is in range to prevent improper fill
        (bool inRange, ) = checkInRange(order);
        require(inRange, "order ! in range");

        //remove from pending array
        pendingOrderIds = ArrayMutation.removeFromArray(
            data.pendingOrderIdx,
            pendingOrderIds
        );

        //approve
        updateApproval(
            address(BRACKET_CONTRACT),
            order.tokenIn,
            order.amountIn
        );

        bytes memory swapPayload;
        IERC20 tokenIn = order.tokenIn;
        IERC20 tokenOut = order.tokenOut;
        if (order.swapOnFill) {
            //for swap on fill, we expect to be paid out in the same asset we provided
            //so the resulting order tokenIn and tokenOut are inverted relative to our original swap limit order
            SwapParams memory params = SwapParams({
                swapTokenIn: order.tokenIn, //asset provided
                swapAmountIn: order.amountIn,
                swapTarget: data.target,
                swapSlippage: order.swapSlippage,
                txData: data.txData
            });
            swapPayload = abi.encode(params);

            tokenIn = order.tokenOut;
            tokenOut = order.tokenIn;
        }

        //create bracket order
        BRACKET_CONTRACT.fillStopLimitOrder(
            swapPayload,
            order.takeProfit,
            order.stopPrice,
            order.amountIn,
            order.orderId,
            tokenIn,
            tokenOut,
            order.recipient,
            order.feeBips,
            order.takeProfitSlippage,
            order.stopSlippage,
            false, //permit
            "0x" //permitPayload
        );

        emit OrderProcessed(order.orderId);
    }

    ///@notice see @IStopLimit
    function createOrder(
        uint256 stopLimitPrice,
        uint256 takeProfit,
        uint256 stopPrice,
        uint256 amountIn,
        IERC20 tokenIn,
        IERC20 tokenOut,
        address recipient,
        uint16 feeBips,
        uint16 takeProfitSlippage,
        uint16 stopSlippage,
        uint16 swapSlippage,
        bool swapOnFill,
        bool permit,
        bytes calldata permitPayload
    ) external override nonReentrant {
        if (permit) {
            handlePermit(
                recipient,
                permitPayload,
                uint160(amountIn),
                address(tokenIn)
            );
        } else {
            //take asset, assume prior approval
            tokenIn.safeTransferFrom(recipient, address(this), amountIn);
        }

        _createOrder(
            stopLimitPrice,
            takeProfit,
            stopPrice,
            amountIn,
            tokenIn,
            tokenOut,
            recipient,
            feeBips,
            takeProfitSlippage,
            stopSlippage,
            swapSlippage,
            swapOnFill
        );
    }

    ///@notice see @IStopLimit
    function modifyOrder(
        uint96 orderId,
        uint256 _stopLimitPrice,
        uint256 _takeProfit,
        uint256 _stopPrice,
        uint256 _amountInDelta,
        IERC20 _tokenOut,
        address _recipient,
        uint16 _takeProfitSlippage,
        uint16 _stopSlippage,
        uint16 _swapSlippage,
        bool _swapOnFill,
        bool permit,
        bool increasePosition,
        bytes calldata permitPayload
    ) external override nonReentrant {
        //get existing order
        Order memory order = orders[orderId];
        //only order owner
        require(msg.sender == order.recipient, "only order owner");
        //deduce any amountIn changes
        uint256 newAmountIn = order.amountIn;
        if (_amountInDelta != 0) {
            if (increasePosition) {
                newAmountIn += _amountInDelta;
                //take funds via permit2
                if (permit) {
                    handlePermit(
                        order.recipient,
                        permitPayload,
                        uint160(_amountInDelta),
                        address(order.tokenIn)
                    );
                } else {
                    //legacy transfer, assume prior approval
                    order.tokenIn.safeTransferFrom(
                        order.recipient,
                        address(this),
                        _amountInDelta
                    );
                }
            } else {
                //ensure delta is valid
                require(_amountInDelta < order.amountIn, "invalid delta");

                //set new amountIn for accounting
                newAmountIn -= _amountInDelta;

                //check min order size for new amount
                MASTER.checkMinOrderSize(order.tokenIn, newAmountIn);

                //refund position partially
                order.tokenIn.safeTransfer(order.recipient, _amountInDelta);

                //check slippage
                require(
                    _takeProfitSlippage <= 10000 &&
                        _stopSlippage <= 10000 &&
                        _swapSlippage <= 10000,
                    "BIPS > 10k"
                );
            }
        }

        //check for oracles
        if (_tokenOut != order.tokenOut) {
            require(
                address(MASTER.oracles(_tokenOut)) != address(0x0),
                "Oracle !exist"
            );
        }

        //construct order
        Order memory newOrder = Order({
            orderId: orderId,
            stopLimitPrice: _stopLimitPrice,
            takeProfit: _takeProfit,
            stopPrice: _stopPrice,
            amountIn: newAmountIn,
            tokenIn: order.tokenIn,
            tokenOut: _tokenOut,
            feeBips: order.feeBips,
            takeProfitSlippage: _takeProfitSlippage,
            stopSlippage: _stopSlippage,
            swapSlippage: _swapSlippage,
            recipient: _recipient,
            direction: MASTER.getExchangeRate(order.tokenIn, _tokenOut) >
                _stopLimitPrice,
            swapOnFill: _swapOnFill
        });

        //store new order
        orders[orderId] = newOrder;
    }

    ///@notice contract owner can cancel any order
    ///@notice cancelled orders refund the order recipient
    function adminCancelOrder(uint96 orderId) external onlyOwner {
        _cancelOrder(orderId);
    }

    ///@notice only the order recipient can cancel their order
    ///@notice only pending orders can be cancelled
    function cancelOrder(uint96 orderId) external {
        Order memory order = orders[orderId];
        require(msg.sender == order.recipient, "Only Order Owner");
        require(_cancelOrder(orderId), "Order not active");
    }

    function _createOrder(
        uint256 stopLimitPrice,
        uint256 takeProfit,
        uint256 stopPrice,
        uint256 amountIn,
        IERC20 tokenIn,
        IERC20 tokenOut,
        address recipient,
        uint16 feeBips,
        uint16 takeProfitSlippage,
        uint16 stopSlippage,
        uint16 swapSlippage,
        bool swapOnFill
    ) internal {
        //verify both oracles exist, as we need both to calc the exchange rate
        require(
            address(MASTER.oracles(tokenIn)) != address(0x0) &&
                address(MASTER.oracles(tokenOut)) != address(0x0),
            "Oracle !exist"
        );
        require(
            pendingOrderIds.length < MASTER.maxPendingOrders(),
            "Max Order Count Reached"
        );
        require(
            takeProfitSlippage <= 10000 &&
                stopSlippage <= 10000 &&
                swapSlippage <= 10000 &&
                feeBips <= 10000,
            "BIPS > 10k"
        );

        MASTER.checkMinOrderSize(tokenIn, amountIn);

        uint96 orderId = MASTER.generateOrderId(msg.sender);

        orders[orderId] = Order({
            orderId: orderId,
            stopLimitPrice: stopLimitPrice,
            stopPrice: stopPrice,
            takeProfit: takeProfit,
            amountIn: amountIn,
            tokenIn: tokenIn,
            tokenOut: tokenOut,
            takeProfitSlippage: takeProfitSlippage,
            feeBips: feeBips,
            stopSlippage: stopSlippage,
            swapSlippage: swapSlippage,
            recipient: recipient,
            direction: MASTER.getExchangeRate(tokenIn, tokenOut) >
                stopLimitPrice, //compare to stop price for this order's direction
            swapOnFill: swapOnFill
        });
        pendingOrderIds.push(uint96(orderId));
        //emit
        emit OrderCreated(orderId);
    }

    function _cancelOrder(uint96 orderId) internal returns (bool) {
        Order memory order = orders[orderId];
        for (uint96 i = 0; i < pendingOrderIds.length; i++) {
            if (pendingOrderIds[i] == orderId) {
                //remove from pending array
                pendingOrderIds = ArrayMutation.removeFromArray(
                    i,
                    pendingOrderIds
                );
                order.tokenIn.safeTransfer(order.recipient, order.amountIn);

                //emit event
                emit OrderCancelled(orderId);

                //short circuit loop
                return true;
            }
        }
        return false;
    }

    ///@notice handle signature and acquisition of asset with permit2
    function handlePermit(
        address owner,
        bytes calldata permitPayload,
        uint160 amount,
        address token
    ) internal {
        Permit2Payload memory payload = abi.decode(
            permitPayload,
            (Permit2Payload)
        );

        permit2.permit(owner, payload.permitSingle, payload.signature);
        permit2.transferFrom(owner, address(this), amount, token);
    }

    ///@notice if current approval is insufficient, approve max
    ///@notice oz safeIncreaseAllowance controls for tokens that require allowance to be reset to 0 before increasing again
    function updateApproval(
        address spender,
        IERC20 token,
        uint256 amount
    ) internal {
        // get current allowance
        uint256 currentAllowance = token.allowance(address(this), spender);
        if (currentAllowance < amount) {
            // amount is a delta, so need to pass max - current to avoid overflow
            token.safeIncreaseAllowance(
                spender,
                type(uint256).max - currentAllowance
            );
        }
    }

    ///@notice check if the order is fillable
    function checkInRange(
        Order memory order
    ) internal view returns (bool inRange, uint256 exchangeRate) {
        exchangeRate = MASTER.getExchangeRate(order.tokenIn, order.tokenOut);
        if (order.direction) {
            if (exchangeRate <= order.stopLimitPrice) {
                inRange = true;
            }
        } else {
            if (exchangeRate >= order.stopLimitPrice) {
                inRange = true;
            }
        }
    }
}
