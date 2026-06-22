// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.11;

// Copyright (c) 2025 Steakhouse Financial



// OpenZeppelin Contracts (last updated v5.5.0) (interfaces/IERC4626.sol)




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
 * @dev Interface of the ERC-4626 "Tokenized Vault Standard", as defined in
 * https://eips.ethereum.org/EIPS/eip-4626[ERC-4626].
 */
interface IERC4626 is IERC20, IERC20Metadata {
    event Deposit(address indexed sender, address indexed owner, uint256 assets, uint256 shares);

    event Withdraw(
        address indexed sender,
        address indexed receiver,
        address indexed owner,
        uint256 assets,
        uint256 shares
    );

    /**
     * @dev Returns the address of the underlying token used for the Vault for accounting, depositing, and withdrawing.
     *
     * - MUST be an ERC-20 token contract.
     * - MUST NOT revert.
     */
    function asset() external view returns (address assetTokenAddress);

    /**
     * @dev Returns the total amount of the underlying asset that is “managed” by Vault.
     *
     * - SHOULD include any compounding that occurs from yield.
     * - MUST be inclusive of any fees that are charged against assets in the Vault.
     * - MUST NOT revert.
     */
    function totalAssets() external view returns (uint256 totalManagedAssets);

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
     * @dev Deposit `assets` underlying tokens and send the corresponding number of vault shares (`shares`) to `receiver`.
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
     * @dev Mints exactly `shares` vault shares to `receiver` in exchange for `assets` underlying tokens.
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
     * @dev Allows an on-chain or off-chain user to simulate the effects of their redemption at the current block,
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


// OpenZeppelin Contracts (last updated v5.5.0) (token/ERC20/ERC20.sol)






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


// OpenZeppelin Contracts (last updated v5.5.0) (interfaces/draft-IERC6093.sol)



/**
 * @dev Standard ERC-20 Errors
 * Interface of the https://eips.ethereum.org/EIPS/eip-6093[ERC-6093] custom errors for ERC-20 tokens.
 */
interface IERC20Errors {
    /**
     * @dev Indicates an error related to the current `balance` of a `sender`. Used in transfers.
     * @param sender Address whose tokens are being transferred.
     * @param balance Current balance for the interacting account.
     * @param needed Minimum amount required to perform a transfer.
     */
    error ERC20InsufficientBalance(address sender, uint256 balance, uint256 needed);

    /**
     * @dev Indicates a failure with the token `sender`. Used in transfers.
     * @param sender Address whose tokens are being transferred.
     */
    error ERC20InvalidSender(address sender);

    /**
     * @dev Indicates a failure with the token `receiver`. Used in transfers.
     * @param receiver Address to which tokens are being transferred.
     */
    error ERC20InvalidReceiver(address receiver);

    /**
     * @dev Indicates a failure with the `spender`’s `allowance`. Used in transfers.
     * @param spender Address that may be allowed to operate on tokens without being their owner.
     * @param allowance Amount of tokens a `spender` is allowed to operate with.
     * @param needed Minimum amount required to perform a transfer.
     */
    error ERC20InsufficientAllowance(address spender, uint256 allowance, uint256 needed);

    /**
     * @dev Indicates a failure with the `approver` of a token to be approved. Used in approvals.
     * @param approver Address initiating an approval operation.
     */
    error ERC20InvalidApprover(address approver);

    /**
     * @dev Indicates a failure with the `spender` to be approved. Used in approvals.
     * @param spender Address that may be allowed to operate on tokens without being their owner.
     */
    error ERC20InvalidSpender(address spender);
}

/**
 * @dev Standard ERC-721 Errors
 * Interface of the https://eips.ethereum.org/EIPS/eip-6093[ERC-6093] custom errors for ERC-721 tokens.
 */
interface IERC721Errors {
    /**
     * @dev Indicates that an address can't be an owner. For example, `address(0)` is a forbidden owner in ERC-721.
     * Used in balance queries.
     * @param owner Address of the current owner of a token.
     */
    error ERC721InvalidOwner(address owner);

    /**
     * @dev Indicates a `tokenId` whose `owner` is the zero address.
     * @param tokenId Identifier number of a token.
     */
    error ERC721NonexistentToken(uint256 tokenId);

    /**
     * @dev Indicates an error related to the ownership over a particular token. Used in transfers.
     * @param sender Address whose tokens are being transferred.
     * @param tokenId Identifier number of a token.
     * @param owner Address of the current owner of a token.
     */
    error ERC721IncorrectOwner(address sender, uint256 tokenId, address owner);

    /**
     * @dev Indicates a failure with the token `sender`. Used in transfers.
     * @param sender Address whose tokens are being transferred.
     */
    error ERC721InvalidSender(address sender);

    /**
     * @dev Indicates a failure with the token `receiver`. Used in transfers.
     * @param receiver Address to which tokens are being transferred.
     */
    error ERC721InvalidReceiver(address receiver);

    /**
     * @dev Indicates a failure with the `operator`’s approval. Used in transfers.
     * @param operator Address that may be allowed to operate on tokens without being their owner.
     * @param tokenId Identifier number of a token.
     */
    error ERC721InsufficientApproval(address operator, uint256 tokenId);

    /**
     * @dev Indicates a failure with the `approver` of a token to be approved. Used in approvals.
     * @param approver Address initiating an approval operation.
     */
    error ERC721InvalidApprover(address approver);

    /**
     * @dev Indicates a failure with the `operator` to be approved. Used in approvals.
     * @param operator Address that may be allowed to operate on tokens without being their owner.
     */
    error ERC721InvalidOperator(address operator);
}

/**
 * @dev Standard ERC-1155 Errors
 * Interface of the https://eips.ethereum.org/EIPS/eip-6093[ERC-6093] custom errors for ERC-1155 tokens.
 */
interface IERC1155Errors {
    /**
     * @dev Indicates an error related to the current `balance` of a `sender`. Used in transfers.
     * @param sender Address whose tokens are being transferred.
     * @param balance Current balance for the interacting account.
     * @param needed Minimum amount required to perform a transfer.
     * @param tokenId Identifier number of a token.
     */
    error ERC1155InsufficientBalance(address sender, uint256 balance, uint256 needed, uint256 tokenId);

    /**
     * @dev Indicates a failure with the token `sender`. Used in transfers.
     * @param sender Address whose tokens are being transferred.
     */
    error ERC1155InvalidSender(address sender);

    /**
     * @dev Indicates a failure with the token `receiver`. Used in transfers.
     * @param receiver Address to which tokens are being transferred.
     */
    error ERC1155InvalidReceiver(address receiver);

    /**
     * @dev Indicates a failure with the `operator`’s approval. Used in transfers.
     * @param operator Address that may be allowed to operate on tokens without being their owner.
     * @param owner Address of the current owner of a token.
     */
    error ERC1155MissingApprovalForAll(address operator, address owner);

    /**
     * @dev Indicates a failure with the `approver` of a token to be approved. Used in approvals.
     * @param approver Address initiating an approval operation.
     */
    error ERC1155InvalidApprover(address approver);

    /**
     * @dev Indicates a failure with the `operator` to be approved. Used in approvals.
     * @param operator Address that may be allowed to operate on tokens without being their owner.
     */
    error ERC1155InvalidOperator(address operator);

    /**
     * @dev Indicates an array length mismatch between ids and values in a safeBatchTransferFrom operation.
     * Used in batch transfers.
     * @param idsLength Length of the array of token identifiers
     * @param valuesLength Length of the array of token amounts
     */
    error ERC1155InvalidArrayLength(uint256 idsLength, uint256 valuesLength);
}


/**
 * @dev Implementation of the {IERC20} interface.
 *
 * This implementation is agnostic to the way tokens are created. This means
 * that a supply mechanism has to be added in a derived contract using {_mint}.
 *
 * TIP: For a detailed writeup see our guide
 * https://forum.openzeppelin.com/t/how-to-implement-erc20-supply-mechanisms/226[How
 * to implement supply mechanisms].
 *
 * The default value of {decimals} is 18. To change this, you should override
 * this function so it returns a different value.
 *
 * We have followed general OpenZeppelin Contracts guidelines: functions revert
 * instead returning `false` on failure. This behavior is nonetheless
 * conventional and does not conflict with the expectations of ERC-20
 * applications.
 */
abstract contract ERC20 is Context, IERC20, IERC20Metadata, IERC20Errors {
    mapping(address account => uint256) private _balances;

    mapping(address account => mapping(address spender => uint256)) private _allowances;

    uint256 private _totalSupply;

    string private _name;
    string private _symbol;

    /**
     * @dev Sets the values for {name} and {symbol}.
     *
     * Both values are immutable: they can only be set once during construction.
     */
    constructor(string memory name_, string memory symbol_) {
        _name = name_;
        _symbol = symbol_;
    }

    /**
     * @dev Returns the name of the token.
     */
    function name() public view virtual returns (string memory) {
        return _name;
    }

    /**
     * @dev Returns the symbol of the token, usually a shorter version of the
     * name.
     */
    function symbol() public view virtual returns (string memory) {
        return _symbol;
    }

    /**
     * @dev Returns the number of decimals used to get its user representation.
     * For example, if `decimals` equals `2`, a balance of `505` tokens should
     * be displayed to a user as `5.05` (`505 / 10 ** 2`).
     *
     * Tokens usually opt for a value of 18, imitating the relationship between
     * Ether and Wei. This is the default value returned by this function, unless
     * it's overridden.
     *
     * NOTE: This information is only used for _display_ purposes: it in
     * no way affects any of the arithmetic of the contract, including
     * {IERC20-balanceOf} and {IERC20-transfer}.
     */
    function decimals() public view virtual returns (uint8) {
        return 18;
    }

    /// @inheritdoc IERC20
    function totalSupply() public view virtual returns (uint256) {
        return _totalSupply;
    }

    /// @inheritdoc IERC20
    function balanceOf(address account) public view virtual returns (uint256) {
        return _balances[account];
    }

    /**
     * @dev See {IERC20-transfer}.
     *
     * Requirements:
     *
     * - `to` cannot be the zero address.
     * - the caller must have a balance of at least `value`.
     */
    function transfer(address to, uint256 value) public virtual returns (bool) {
        address owner = _msgSender();
        _transfer(owner, to, value);
        return true;
    }

    /// @inheritdoc IERC20
    function allowance(address owner, address spender) public view virtual returns (uint256) {
        return _allowances[owner][spender];
    }

    /**
     * @dev See {IERC20-approve}.
     *
     * NOTE: If `value` is the maximum `uint256`, the allowance is not updated on
     * `transferFrom`. This is semantically equivalent to an infinite approval.
     *
     * Requirements:
     *
     * - `spender` cannot be the zero address.
     */
    function approve(address spender, uint256 value) public virtual returns (bool) {
        address owner = _msgSender();
        _approve(owner, spender, value);
        return true;
    }

    /**
     * @dev See {IERC20-transferFrom}.
     *
     * Skips emitting an {Approval} event indicating an allowance update. This is not
     * required by the ERC. See {xref-ERC20-_approve-address-address-uint256-bool-}[_approve].
     *
     * NOTE: Does not update the allowance if the current allowance
     * is the maximum `uint256`.
     *
     * Requirements:
     *
     * - `from` and `to` cannot be the zero address.
     * - `from` must have a balance of at least `value`.
     * - the caller must have allowance for ``from``'s tokens of at least
     * `value`.
     */
    function transferFrom(address from, address to, uint256 value) public virtual returns (bool) {
        address spender = _msgSender();
        _spendAllowance(from, spender, value);
        _transfer(from, to, value);
        return true;
    }

    /**
     * @dev Moves a `value` amount of tokens from `from` to `to`.
     *
     * This internal function is equivalent to {transfer}, and can be used to
     * e.g. implement automatic token fees, slashing mechanisms, etc.
     *
     * Emits a {Transfer} event.
     *
     * NOTE: This function is not virtual, {_update} should be overridden instead.
     */
    function _transfer(address from, address to, uint256 value) internal {
        if (from == address(0)) {
            revert ERC20InvalidSender(address(0));
        }
        if (to == address(0)) {
            revert ERC20InvalidReceiver(address(0));
        }
        _update(from, to, value);
    }

    /**
     * @dev Transfers a `value` amount of tokens from `from` to `to`, or alternatively mints (or burns) if `from`
     * (or `to`) is the zero address. All customizations to transfers, mints, and burns should be done by overriding
     * this function.
     *
     * Emits a {Transfer} event.
     */
    function _update(address from, address to, uint256 value) internal virtual {
        if (from == address(0)) {
            // Overflow check required: The rest of the code assumes that totalSupply never overflows
            _totalSupply += value;
        } else {
            uint256 fromBalance = _balances[from];
            if (fromBalance < value) {
                revert ERC20InsufficientBalance(from, fromBalance, value);
            }
            unchecked {
                // Overflow not possible: value <= fromBalance <= totalSupply.
                _balances[from] = fromBalance - value;
            }
        }

        if (to == address(0)) {
            unchecked {
                // Overflow not possible: value <= totalSupply or value <= fromBalance <= totalSupply.
                _totalSupply -= value;
            }
        } else {
            unchecked {
                // Overflow not possible: balance + value is at most totalSupply, which we know fits into a uint256.
                _balances[to] += value;
            }
        }

        emit Transfer(from, to, value);
    }

    /**
     * @dev Creates a `value` amount of tokens and assigns them to `account`, by transferring it from address(0).
     * Relies on the `_update` mechanism
     *
     * Emits a {Transfer} event with `from` set to the zero address.
     *
     * NOTE: This function is not virtual, {_update} should be overridden instead.
     */
    function _mint(address account, uint256 value) internal {
        if (account == address(0)) {
            revert ERC20InvalidReceiver(address(0));
        }
        _update(address(0), account, value);
    }

    /**
     * @dev Destroys a `value` amount of tokens from `account`, lowering the total supply.
     * Relies on the `_update` mechanism.
     *
     * Emits a {Transfer} event with `to` set to the zero address.
     *
     * NOTE: This function is not virtual, {_update} should be overridden instead
     */
    function _burn(address account, uint256 value) internal {
        if (account == address(0)) {
            revert ERC20InvalidSender(address(0));
        }
        _update(account, address(0), value);
    }

    /**
     * @dev Sets `value` as the allowance of `spender` over the `owner`'s tokens.
     *
     * This internal function is equivalent to `approve`, and can be used to
     * e.g. set automatic allowances for certain subsystems, etc.
     *
     * Emits an {Approval} event.
     *
     * Requirements:
     *
     * - `owner` cannot be the zero address.
     * - `spender` cannot be the zero address.
     *
     * Overrides to this logic should be done to the variant with an additional `bool emitEvent` argument.
     */
    function _approve(address owner, address spender, uint256 value) internal {
        _approve(owner, spender, value, true);
    }

    /**
     * @dev Variant of {_approve} with an optional flag to enable or disable the {Approval} event.
     *
     * By default (when calling {_approve}) the flag is set to true. On the other hand, approval changes made by
     * `_spendAllowance` during the `transferFrom` operation sets the flag to false. This saves gas by not emitting any
     * `Approval` event during `transferFrom` operations.
     *
     * Anyone who wishes to continue emitting `Approval` events on the `transferFrom` operation can force the flag to
     * true using the following override:
     *
     * ```solidity
     * function _approve(address owner, address spender, uint256 value, bool) internal virtual override {
     *     super._approve(owner, spender, value, true);
     * }
     * ```
     *
     * Requirements are the same as {_approve}.
     */
    function _approve(address owner, address spender, uint256 value, bool emitEvent) internal virtual {
        if (owner == address(0)) {
            revert ERC20InvalidApprover(address(0));
        }
        if (spender == address(0)) {
            revert ERC20InvalidSpender(address(0));
        }
        _allowances[owner][spender] = value;
        if (emitEvent) {
            emit Approval(owner, spender, value);
        }
    }

    /**
     * @dev Updates `owner`'s allowance for `spender` based on spent `value`.
     *
     * Does not update the allowance value in case of infinite allowance.
     * Revert if not enough allowance is available.
     *
     * Does not emit an {Approval} event.
     */
    function _spendAllowance(address owner, address spender, uint256 value) internal virtual {
        uint256 currentAllowance = allowance(owner, spender);
        if (currentAllowance < type(uint256).max) {
            if (currentAllowance < value) {
                revert ERC20InsufficientAllowance(spender, currentAllowance, value);
            }
            unchecked {
                _approve(owner, spender, currentAllowance - value, false);
            }
        }
    }
}




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


// Copyright (c) 2025 Steakhouse





// Copyright (c) 2025 Steakhouse






/// @notice Oracle interface to get a token price with 36 decimals of precision
interface IOracle {
    function price() external view returns (uint256);
}


interface IOracleCallback {
    /// @dev RIs considered to have a price of ORACLE_PRECISION
    function asset() external view returns (address);

    /// @dev Returns an oracle for tokens that are not the asset
    function oracles(IERC20 token) external view returns (IOracle);
}

/**
 * @notice Interface for a funding module
 * @notice `nav` should never revert
 */
interface IFunding {
    // ========== ADMIN ==========
    function addFacility(bytes calldata facilityData) external;
    function removeFacility(bytes calldata facilityData) external;
    function isFacility(bytes calldata facilityData) external view returns (bool);
    function facilities(uint256 index) external view returns (bytes memory);
    function facilitiesLength() external view returns (uint256);

    function addCollateralToken(IERC20 collateralToken) external;
    function removeCollateralToken(IERC20 collateralToken) external;
    function isCollateralToken(IERC20 collateralToken) external view returns (bool);
    function collateralTokens(uint256 index) external view returns (IERC20);
    function collateralTokensLength() external view returns (uint256);

    function addDebtToken(IERC20 debtToken) external;
    function removeDebtToken(IERC20 debtToken) external;
    function isDebtToken(IERC20 debtToken) external view returns (bool);
    function debtTokens(uint256 index) external view returns (IERC20);
    function debtTokensLength() external view returns (uint256);

    // ========== ACTIONS ==========
    function skim(IERC20 token) external;
    function pledge(bytes calldata facilityData, IERC20 collateralToken, uint256 collateralAmount) external;
    function depledge(bytes calldata facilityData, IERC20 collateralToken, uint256 collateralAmount) external;
    function borrow(bytes calldata facilityData, IERC20 debtToken, uint256 borrowAmount) external;
    function repay(bytes calldata facilityData, IERC20 debtToken, uint256 repayAmount) external;

    // ========== POSITION ==========
    function ltv(bytes calldata facilityData) external view returns (uint256);
    function debtBalance(bytes calldata facilityData, IERC20 debtToken) external view returns (uint256);
    function collateralBalance(bytes calldata facilityData, IERC20 collateralToken) external view returns (uint256);
    function debtBalance(IERC20 debtToken) external view returns (uint256);
    function collateralBalance(IERC20 collateralToken) external view returns (uint256);
    function nav(IOracleCallback oraclesProvider) external view returns (uint256);
}







interface ISwapper {
    /// @dev Sells `amountIn` of `input` tokens for `output` tokens.
    /// @param input The address of the input token.
    /// @param output The address of the output token.
    /// @param amountIn The amount of input tokens to sell.
    /// @param data Additional data to pass to the swapper.
    function sell(IERC20 input, IERC20 output, uint256 amountIn, bytes calldata data) external;
}


/// @notice Callback interface for Box flash loans
interface IBoxFlashCallback {
    function onBoxFlash(IERC20 token, uint256 amount, bytes calldata data) external;
}

interface IBox is IERC4626, IOracleCallback {
    /* FUNCTIONS */

    // ========== STATE FUNCTIONS ==========
    function asset() external view override(IERC4626, IOracleCallback) returns (address);
    function slippageEpochDuration() external view returns (uint256);
    function shutdownSlippageDuration() external view returns (uint256);
    function shutdownWarmup() external view returns (uint256);
    function owner() external view returns (address);
    function curator() external view returns (address);
    function guardian() external view returns (address);
    function shutdownTime() external view returns (uint256);
    function skimRecipient() external view returns (address);
    function isAllocator(address account) external view returns (bool);
    function isFeeder(address account) external view returns (bool);
    function tokens(uint256 index) external view returns (IERC20);
    function oracles(IERC20 token) external view returns (IOracle);
    function maxSlippage() external view returns (uint256);
    function accumulatedSlippage() external view returns (uint256);
    function slippageEpochStart() external view returns (uint256);
    function executableAt(bytes calldata data) external view returns (uint256);

    // ========== INVESTMENT MANAGEMENT ==========
    function skim(IERC20 token) external;
    function skimFunding(IFunding fundingModule, IERC20 token) external;
    function allocate(
        IERC20 token,
        uint256 assetsAmount,
        ISwapper swapper,
        bytes calldata data
    ) external returns (uint256 expected, uint256 received);
    function deallocate(
        IERC20 token,
        uint256 tokensAmount,
        ISwapper swapper,
        bytes calldata data
    ) external returns (uint256 expected, uint256 received);
    function reallocate(
        IERC20 from,
        IERC20 to,
        uint256 tokensAmount,
        ISwapper swapper,
        bytes calldata data
    ) external returns (uint256 expected, uint256 received);

    // ========== SIMPLE FUNDING OPERATIONS ==========
    function pledge(IFunding fundingModule, bytes calldata facilityData, IERC20 collateralToken, uint256 collateralAmount) external;
    function depledge(IFunding fundingModule, bytes calldata facilityData, IERC20 collateralToken, uint256 collateralAmount) external;
    function borrow(IFunding fundingModule, bytes calldata facilityData, IERC20 debtToken, uint256 borrowAmount) external;
    function repay(IFunding fundingModule, bytes calldata facilityData, IERC20 debtToken, uint256 repayAmount) external;

    // ========== COMPLEX FUNDING OPERATIONS WITH FLASHLOAN AND SWAPPER ==========
    function flash(IERC20 flashToken, uint256 flashAmount, bytes calldata data) external;

    // ========== BATCHING ==========
    function multicall(bytes[] calldata data) external;

    // ========== EMERGENCY ==========
    function shutdown() external;
    function recover() external;

    // ========== ADMIN FUNCTIONS ==========
    function setSkimRecipient(address newSkimRecipient) external;
    function transferOwnership(address newOwner) external;
    function setCurator(address newCurator) external;
    function setGuardian(address newGuardian) external;
    function setIsAllocator(address account, bool newIsAllocator) external;

    // ========== TIMELOCK GOVERNANCE ==========
    function submit(bytes calldata data) external;
    function timelock(bytes4 selector) external view returns (uint256);
    function revoke(bytes calldata data) external;
    function increaseTimelock(bytes4 selector, uint256 newDuration) external;
    function decreaseTimelock(bytes4 selector, uint256 newDuration) external;
    function abdicateTimelock(bytes4 selector) external;

    // ========== TIMELOCKED FUNCTIONS ==========
    function setIsFeeder(address account, bool newIsFeeder) external;
    function setMaxSlippage(uint256 newMaxSlippage) external;
    function addToken(IERC20 token, IOracle oracle) external;
    function removeToken(IERC20 token) external;
    function changeTokenOracle(IERC20 token, IOracle oracle) external;

    // ========== VIEW FUNCTIONS ==========
    function isToken(IERC20 token) external view returns (bool);
    function isTokenOrAsset(IERC20 token) external view returns (bool);
    function tokensLength() external view returns (uint256);
    function isShutdown() external view returns (bool);
    function isWinddown() external view returns (bool);

    // ========== FUNDING ADMIN FUNCTIONS ==========
    function addFunding(IFunding fundingModule) external;
    function addFundingFacility(IFunding fundingModule, bytes calldata facilityData) external;
    function addFundingCollateral(IFunding fundingModule, IERC20 collateralToken) external;
    function addFundingDebt(IFunding fundingModule, IERC20 debtToken) external;
    function removeFunding(IFunding fundingModule) external;
    function removeFundingFacility(IFunding fundingModule, bytes calldata facilityData) external;
    function removeFundingCollateral(IFunding fundingModule, IERC20 collateralToken) external;
    function removeFundingDebt(IFunding fundingModule, IERC20 debtToken) external;

    // ========== FUNDING VIEW FUNCTIONS ==========
    function fundings(uint256 index) external view returns (IFunding);
    function fundingsLength() external view returns (uint256);
    function isFunding(IFunding fundingModule) external view returns (bool);
}






// Copyright (c) 2025 Steakhouse


// Precision for percentage calculations
uint256 constant PRECISION = 1 ether;
// Maximum timelock duration (4 weeks)
uint256 constant TIMELOCK_CAP = 4 weeks;
// Timelock duration for disabled selectors
uint256 constant TIMELOCK_DISABLED = type(uint256).max;
// Maximum allowed slippage percentage (1%)
uint256 constant MAX_SLIPPAGE_LIMIT = 0.01 ether;
// Delay from start of a shutdown to possible liquidations
uint256 constant MAX_SHUTDOWN_WARMUP = 4 weeks;
// Precision for oracle prices
uint256 constant ORACLE_PRECISION = 1e36;
// Maximum number of tokens allowed in a box
uint256 constant MAX_TOKENS = 20;

import {ErrorsLib} from "./libraries/ErrorsLib.sol";








library EventsLib {
    // ========== FACTORIES ==========
    event BoxCreated(
        address indexed box,
        address indexed asset,
        address indexed owner,
        address curator,
        string name,
        string symbol,
        uint256 maxSlippage,
        uint256 slippageEpochDuration,
        uint256 shutdownSlippageDuration,
        uint256 shutdownWarmup
    );

    // ========== ACCESS CONTROL ==========
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event CuratorUpdated(address indexed previousCurator, address indexed newCurator);
    event GuardianUpdated(address indexed previousGuardian, address indexed newGuardian);
    event AllocatorUpdated(address indexed account, bool isAllocator);
    event FeederUpdated(address indexed account, bool isFeeder);

    // ========== INVESTMENT MANAGEMENT ==========
    event Allocation(
        IERC20 indexed token,
        uint256 assets,
        uint256 expectedTokens,
        uint256 actualTokens,
        int256 slippagePct,
        ISwapper indexed swapper,
        bytes data
    );
    event Deallocation(
        IERC20 indexed token,
        uint256 tokens,
        uint256 expectedAssets,
        uint256 actualAssets,
        int256 slippagePct,
        ISwapper indexed swapper,
        bytes data
    );
    event Reallocation(
        IERC20 indexed fromToken,
        IERC20 indexed toToken,
        uint256 tokensFrom,
        uint256 expectedTokensTo,
        uint256 actualTokensTo,
        int256 slippagePct,
        ISwapper indexed swapper,
        bytes data
    );
    event Pledge(IFunding indexed fundingModule, bytes facilityData, IERC20 collateralToken, uint256 collateralAmount);
    event Depledge(IFunding indexed fundingModule, bytes facilityData, IERC20 collateralToken, uint256 collateralAmount);
    event Borrow(IFunding indexed fundingModule, bytes facilityData, IERC20 debtToken, uint256 borrowAmount);
    event Repay(IFunding indexed fundingModule, bytes facilityData, IERC20 debtToken, uint256 repayAmount);
    event Flash(address indexed caller, IERC20 indexed token, uint256 amount);

    // ========== MISC ==========
    event SlippageAccumulated(uint256 amount, uint256 total);
    event SlippageEpochReset(uint256 newEpochStart);
    event MaxSlippageUpdated(uint256 previousMaxSlippage, uint256 newMaxSlippage);
    event Skim(IERC20 indexed token, address indexed recipient, uint256 amount);

    // ========== CONFIGURATION ==========
    event TokenAdded(IERC20 indexed token, IOracle indexed oracle);
    event TokenRemoved(IERC20 indexed token);
    event TokenOracleChanged(IERC20 indexed token, IOracle indexed oracle);
    event FundingModuleAdded(IFunding indexed fundingModule);
    event FundingFacilityAdded(IFunding indexed fundingModule, bytes facilityData);
    event FundingCollateralAdded(IFunding indexed fundingModule, IERC20 collateralToken);
    event FundingDebtAdded(IFunding indexed fundingModule, IERC20 debtToken);
    event FundingModuleRemoved(IFunding indexed fundingModule);
    event FundingFacilityRemoved(IFunding indexed fundingModule, bytes facilityData);
    event FundingCollateralRemoved(IFunding indexed fundingModule, IERC20 collateralToken);
    event FundingDebtRemoved(IFunding indexed fundingModule, IERC20 debtToken);
    event SkimRecipientUpdated(address indexed previousRecipient, address indexed newRecipient);
    event Shutdown(address indexed guardian);
    event Recover(address indexed guardian);

    // ========== TIMELOCK ==========
    event TimelockSubmitted(bytes4 indexed selector, bytes data, uint256 executableAt, address who);
    event TimelockRevoked(bytes4 indexed selector, bytes data, address who);
    event TimelockIncreased(bytes4 indexed selector, uint256 newDuration, address who);
    event TimelockDecreased(bytes4 indexed selector, uint256 newDuration, address who);
    event TimelockExecuted(bytes4 indexed selector, bytes data, address who);
}


/**
 * @title Box
 * @notice An ERC4626 vault that holds a base asset, invest in other ERC20 tokens and can borrow/lend via funding modules.
 * @dev Features role-based access control, timelocked governance, and slippage protection
 * @dev Box is not inflation or donation resistant as deposits are strictly controlled via the isFeeder role.
 * @dev Should deposit happen in an automated way (liquidity on a Vault V2) and from multiple feeders, it should be seeded first.
 * @dev Oracles can be manipulated to give an unfair price
 * @dev It is recommanded to create resiliency by using the BoxAdapterCached
 * @dev and/or by using a Vault V2 as a parent vault, which can have a reported price a but lower the NAV price and a setMaxRate()
 * @dev During flash operations there is no totalAssets() calculation possible to avoid NAV based attacks
 * @dev There is no protection against ERC4626 inflation attacks, as deposits are controlled via the isFeeder role.
 * @dev Users shouldn't be able to deposited directly or indirectly to a Box.
 * @dev The Box uses forceApprove with 0 value, making it incompatible with the BNB ERC-20 token (reverts on zero-value approvals)
 * @dev Token removal can be stopped by sending dust amount of tokens. Can be fixed by deallocating then removing the token atomically
 * @dev The epoch-based slippage protection is relative to Box total assets, but a bad allocator can deposit all parent Vault V2
 * @dev fund into one Box to temporarily inflate its total asset and extract more value than expected.
 */
contract Box is IBox, ERC20, ReentrancyGuard {
    using SafeERC20 for IERC20;
    using Math for uint256;
    using SafeCast for uint256;
    using SafeCast for int256;

    // ========== IMMUTABLE STATE ==========

    /// @notice Base currency token (e.g., USDC)
    address public immutable override asset;

    /// @notice Number of decimals for the vault shares (normalized to 18 for assets with fewer decimals)
    uint8 private immutable _decimals;

    /// @notice Virtual shares used for inflation attack protection
    uint256 public immutable virtualShares;

    /// @notice Duration of slippage tracking epochs
    uint256 public immutable slippageEpochDuration;

    /// @notice Duration over which shutdown slippage tolerance increases
    uint256 public immutable shutdownSlippageDuration;

    /// @notice Duration between shutdown and wind-down phase
    uint256 public immutable shutdownWarmup;

    // ========== MUTABLE STATE ==========

    /// @notice Contract owner with administrative privileges
    address public owner;

    /// @notice Curator who manages tokens and funding modules
    address public curator;

    /// @notice Guardian who can trigger shutdowns and revoke timelocked actions
    address public guardian;

    /// @notice Timestamp when shutdown was triggered, no shutdown if type(uint256).max
    uint256 public shutdownTime;

    /// @notice Recipient of skimmed tokens that aren't part of the vault's strategy
    address public skimRecipient;

    /// @notice Tracks which addresses can execute allocation strategies
    mapping(address => bool) public isAllocator;

    /// @notice Tracks which addresses can deposit into the vault
    mapping(address => bool) public isFeeder;

    /// @notice List of whitelisted investment tokens
    IERC20[] public tokens;

    /// @notice Maps each token to its price oracle
    mapping(IERC20 => IOracle) public oracles;

    /// @notice Maximum allowed slippage per operation and per epoch (scaled by PRECISION = 1e18)
    uint256 public maxSlippage;

    /// @notice Accumulated slippage within current epoch (scaled by PRECISION = 1e18)
    uint256 public accumulatedSlippage;

    /// @notice Timestamp when the current slippage tracking epoch started
    uint256 public slippageEpochStart;

    /// @notice Delay duration for each function selector (in seconds)
    mapping(bytes4 => uint256) public timelock;

    /// @notice Timestamp when specific calldata becomes executable
    mapping(bytes => uint256) public executableAt;

    /// @notice List of whitelisted funding modules for borrowing/lending
    IFunding[] public fundings;

    /// @notice Quick lookup to check if a funding module is whitelisted
    mapping(IFunding => bool) internal fundingMap;

    /// @notice Depth counter for nested NAV-caching operations (flash and swaps)
    uint8 private transient _cachedNavDepth;

    /// @notice Cached NAV value during flash and swap operations to prevent manipulation
    uint256 private transient _cachedNav;

    // ========== CONSTRUCTOR ==========

    /**
     * @notice Allows the contract to receive native currency
     * @dev Required for skimming native currency from funding modules
     */
    receive() external payable {}

    /**
     * @notice Fallback function to receive native currency
     * @dev Required for skimming native currency from funding modules
     */
    fallback() external payable {}

    /**
     * @notice Initializes the Box vault
     * @param _asset Base currency token (e.g., USDC)
     * @param _owner Initial owner address
     * @param _curator Initial curator address
     * @param _name ERC20 token name
     * @param _symbol ERC20 token symbol
     * @param _maxSlippage Max allowed slippage for a swap or aggregated over `_slippageEpochDuration`
     * @param _slippageEpochDuration Duration for which slippage is measured
     * @param _shutdownSlippageDuration When shutdown duration for slippage allowance to widen
     * @param _shutdownWarmup Duration between shutdown and wind-down phase
     * @dev To mitigate donation attacks, make an initial "dead" deposit after deployment
     *      (e.g., deposit a small amount and transfer the shares to address(0xdead)).
     */
    constructor(
        address _asset,
        address _owner,
        address _curator,
        string memory _name,
        string memory _symbol,
        uint256 _maxSlippage,
        uint256 _slippageEpochDuration,
        uint256 _shutdownSlippageDuration,
        uint256 _shutdownWarmup
    ) ERC20(_name, _symbol) {
        _requireNonZeroAddress(_asset);
        _requireNonZeroAddress(_owner);
        _requireNonZeroAddress(_curator);
        require(_maxSlippage <= MAX_SLIPPAGE_LIMIT, ErrorsLib.SlippageTooHigh());
        _requireNotEqual(_slippageEpochDuration, 0);
        _requireNotEqual(_shutdownSlippageDuration, 0);
        require(_shutdownWarmup <= MAX_SHUTDOWN_WARMUP, ErrorsLib.InvalidValue());

        asset = _asset;
        owner = _owner;
        curator = _curator;
        maxSlippage = _maxSlippage;
        slippageEpochDuration = _slippageEpochDuration;
        shutdownSlippageDuration = _shutdownSlippageDuration;
        shutdownWarmup = _shutdownWarmup;
        slippageEpochStart = block.timestamp;
        shutdownTime = type(uint256).max; // No shutdown initially

        // Set up decimals following VaultV2 pattern
        uint256 assetDecimals = IERC20Metadata(asset).decimals();
        uint256 decimalOffset = uint256(18) > assetDecimals ? uint256(18) - assetDecimals : 0;
        _decimals = uint8(assetDecimals + decimalOffset);
        virtualShares = 10 ** decimalOffset;

        emit EventsLib.BoxCreated(
            address(this),
            asset,
            owner,
            curator,
            _name,
            _symbol,
            maxSlippage,
            slippageEpochDuration,
            shutdownSlippageDuration,
            shutdownWarmup
        );
        emit EventsLib.OwnershipTransferred(address(0), _owner);
        emit EventsLib.CuratorUpdated(address(0), _curator);
    }

    // ========== ERC4626 IMPLEMENTATION ==========

    /// @notice Returns the number of decimals for the vault shares
    /// @dev Overrides ERC20.decimals() to support assets with different decimal values
    function decimals() public view override(ERC20, IERC20Metadata) returns (uint8) {
        return _decimals;
    }

    /// @inheritdoc IERC4626
    /// @notice Returns the total value of assets managed by the vault
    /// @dev Returns cached NAV during flash and swap operations to prevent manipulation
    function totalAssets() public view returns (uint256) {
        return _cachedNavDepth > 0 ? _cachedNav : _nav();
    }

    /// @inheritdoc IERC4626
    /// @notice Calculates shares received for a given asset amount
    function convertToShares(uint256 assets) public view returns (uint256) {
        uint256 supply = totalSupply();
        return assets.mulDiv(supply + virtualShares, totalAssets() + 1, Math.Rounding.Floor);
    }

    /// @inheritdoc IERC4626
    /// @notice Calculates assets received for redeeming shares
    function convertToAssets(uint256 shares) public view returns (uint256) {
        uint256 supply = totalSupply();
        return shares.mulDiv(totalAssets() + 1, supply + virtualShares, Math.Rounding.Floor);
    }

    /// @inheritdoc IERC4626
    /// @notice Maximum assets that can be deposited
    function maxDeposit(address) external view returns (uint256) {
        return (isShutdown()) ? 0 : type(uint256).max;
    }

    /// @inheritdoc IERC4626
    /// @notice Simulates share minting for a deposit
    function previewDeposit(uint256 assets) public view returns (uint256) {
        return convertToShares(assets);
    }

    /// @inheritdoc IERC4626
    /// @notice Deposits base asset and mints shares to receiver
    /// @dev Only authorized feeders can deposit
    function deposit(uint256 assets, address receiver) public nonReentrant returns (uint256 shares) {
        shares = previewDeposit(assets);
        _depositMint(assets, shares, receiver);
    }

    /// @inheritdoc IERC4626
    /// @notice Maximum shares that can be minted
    function maxMint(address) external view returns (uint256) {
        return (isShutdown()) ? 0 : type(uint256).max;
    }

    /// @inheritdoc IERC4626
    /// @notice Simulates assets needed to mint shares
    function previewMint(uint256 shares) public view returns (uint256) {
        uint256 supply = totalSupply();
        return shares.mulDiv(totalAssets() + 1, supply + virtualShares, Math.Rounding.Ceil);
    }

    /// @inheritdoc IERC4626
    /// @notice Mints exact shares by depositing necessary base asset
    /// @dev Only authorized feeders can mint
    function mint(uint256 shares, address receiver) external nonReentrant returns (uint256 assets) {
        assets = previewMint(shares);
        _depositMint(assets, shares, receiver);
    }

    /// @dev Internal helper for deposit and mint to reduce bytecode duplication
    function _depositMint(uint256 assets, uint256 shares, address receiver) internal {
        require(_cachedNavDepth == 0, ErrorsLib.ReentryNotAllowed());
        _onlyFeeder();
        _requireNotShutdown();
        _requireNonZeroAddress(receiver);

        IERC20(asset).safeTransferFrom(msg.sender, address(this), assets);
        _mint(receiver, shares);

        emit Deposit(msg.sender, receiver, assets, shares);
    }

    /// @inheritdoc IERC4626
    /// @notice Maximum assets owner can withdraw
    function maxWithdraw(address owner_) external view returns (uint256) {
        uint256 ownerAssets = convertToAssets(balanceOf(owner_));
        uint256 availableLiquidity = IERC20(asset).balanceOf(address(this));
        return ownerAssets < availableLiquidity ? ownerAssets : availableLiquidity;
    }

    /// @inheritdoc IERC4626
    /// @notice Simulates shares burned for withdrawing assets
    function previewWithdraw(uint256 assets) public view returns (uint256) {
        uint256 supply = totalSupply();
        return assets.mulDiv(supply + virtualShares, totalAssets() + 1, Math.Rounding.Ceil);
    }

    /// @inheritdoc IERC4626
    /// @notice Withdraws base asset by burning owner's shares
    /// @dev Requires sufficient shares and vault liquidity
    function withdraw(uint256 assets, address receiver, address owner_) public nonReentrant returns (uint256 shares) {
        shares = previewWithdraw(assets);
        _withdrawRedeem(assets, shares, receiver, owner_);
    }

    /// @inheritdoc IERC4626
    /// @notice Maximum shares owner can redeem
    function maxRedeem(address owner_) external view returns (uint256) {
        uint256 ownerShares = balanceOf(owner_);
        uint256 availableLiquidity = IERC20(asset).balanceOf(address(this));
        uint256 liquidityShares = convertToShares(availableLiquidity);
        return ownerShares < liquidityShares ? ownerShares : liquidityShares;
    }

    /// @inheritdoc IERC4626
    /// @notice Simulates assets received for redeeming shares
    function previewRedeem(uint256 shares) public view returns (uint256) {
        return convertToAssets(shares);
    }

    /// @inheritdoc IERC4626
    /// @notice Redeems shares for underlying base asset
    /// @dev Burns shares and transfers base asset to receiver
    function redeem(uint256 shares, address receiver, address owner_) external nonReentrant returns (uint256 assets) {
        assets = previewRedeem(shares);
        _withdrawRedeem(assets, shares, receiver, owner_);
    }

    /// @dev Internal helper for withdraw and redeem to reduce bytecode duplication
    function _withdrawRedeem(uint256 assets, uint256 shares, address receiver, address owner_) internal {
        require(_cachedNavDepth == 0, ErrorsLib.ReentryNotAllowed());
        _requireNonZeroAddress(receiver);

        if (msg.sender != owner_) {
            uint256 allowed = allowance(owner_, msg.sender);
            if (allowed < shares) revert ErrorsLib.InsufficientAllowance();
            if (allowed != type(uint256).max) {
                _approve(owner_, msg.sender, allowed - shares);
            }
        }

        if (balanceOf(owner_) < shares) revert ErrorsLib.InsufficientShares();
        if (IERC20(asset).balanceOf(address(this)) < assets) revert ErrorsLib.InsufficientLiquidity();

        _burn(owner_, shares);
        IERC20(asset).safeTransfer(receiver, assets);

        emit Withdraw(msg.sender, receiver, owner_, assets, shares);
    }

    // ========== SWAP FUNCTIONS ==========

    /**
     * @notice Transfers accidentally sent tokens to the skim recipient
     * @param token Token to skim from the contract
     * @dev Cannot skim the base asset or whitelisted investment tokens
     */
    function skim(IERC20 token) external nonReentrant {
        require(msg.sender == skimRecipient, ErrorsLib.OnlySkimRecipient());
        _requireNotEqualAddress(address(token), asset);
        require(!isToken(token), ErrorsLib.CannotSkimToken());

        uint256 balance;

        if (address(token) != address(0)) {
            // ERC-20 tokens
            balance = token.balanceOf(address(this));
            require(balance > 0, ErrorsLib.CannotSkimZero());
            token.safeTransfer(skimRecipient, balance);
        } else {
            // ETH
            balance = address(this).balance;
            require(balance > 0, ErrorsLib.CannotSkimZero());
            (bool ok, ) = skimRecipient.call{value: balance}("");
            require(ok, ErrorsLib.TransferFailed());
        }

        emit EventsLib.Skim(token, skimRecipient, balance);
    }

    /**
     * @notice Swaps base asset for investment tokens
     * @param token Target token to acquire
     * @param assetsAmount Maximum amount of base asset to spend
     * @param swapper Contract that will execute the swap
     * @param data Custom data for the swapper implementation
     * @return expected Expected amount of target token based on oracle price
     * @return received Actual amount of target token received from the allocation
     * @dev Enforces slippage protection based on oracle prices
     * @dev During wind-down, slippage tolerance increases over time
     */
    function allocate(
        IERC20 token,
        uint256 assetsAmount,
        ISwapper swapper,
        bytes calldata data
    ) public nonReentrant returns (uint256 expected, uint256 received) {
        _startNavCache();

        bool winddown = isWinddown();
        require((isAllocator[msg.sender] && !winddown) || (winddown && _debtBalance(token) > 0), ErrorsLib.OnlyAllocatorsOrWinddown());
        _requireIsToken(token);

        uint256 oraclePrice = oracles[token].price();
        uint256 slippageTolerance = winddown ? _winddownSlippageTolerance() : maxSlippage;

        if (winddown) {
            // Limit allocation to debt shortfall adjusted for slippage tolerance
            uint256 debtAmount = _debtBalance(token);
            uint256 existingBalance = token.balanceOf(address(this));
            uint256 neededTokens = debtAmount > existingBalance ? debtAmount - existingBalance : 0;
            uint256 neededValue = neededTokens.mulDiv(oraclePrice, ORACLE_PRECISION, Math.Rounding.Ceil);
            uint256 maxAllocation = neededValue.mulDiv(PRECISION, PRECISION - slippageTolerance, Math.Rounding.Ceil);
            require(assetsAmount <= maxAllocation, ErrorsLib.InvalidAmount());
        }

        // Execute swap
        (uint256 assetsSpent, uint256 tokensReceived) = _executeSwap(IERC20(asset), token, assetsAmount, swapper, data);

        // Calculate and validate slippage
        uint256 expectedTokens = assetsAmount.mulDiv(ORACLE_PRECISION, oraclePrice, Math.Rounding.Ceil);
        uint256 minTokens = _calculateMinAmount(expectedTokens, slippageTolerance);
        require(tokensReceived >= minTokens, ErrorsLib.AllocationTooExpensive());

        int256 slippagePct = _calculateSlippagePct(expectedTokens, tokensReceived);

        // Track slippage if we are not in winddown and have positive slippage
        if (!winddown && tokensReceived < expectedTokens) {
            uint256 slippageValue = (expectedTokens - tokensReceived).mulDiv(oraclePrice, ORACLE_PRECISION, Math.Rounding.Ceil);
            _increaseSlippage(slippageValue.mulDiv(PRECISION, totalAssets(), Math.Rounding.Ceil));
        }

        emit EventsLib.Allocation(token, assetsSpent, expectedTokens, tokensReceived, slippagePct, swapper, data);

        _endNavCache();
        return (expectedTokens, tokensReceived);
    }

    /**
     * @notice Swaps investment tokens back to base asset
     * @param token Token to sell
     * @param tokensAmount Maximum amount of tokens to sell
     * @param swapper Contract that will execute the swap
     * @param data Custom data for the swapper implementation
     * @return expected Expected amount of base asset based on oracle price
     * @return received Actual amount of base asset received from the deallocation
     * @dev Enforces slippage protection based on oracle prices
     * @dev During wind-down, anyone can deallocate tokens with no outstanding debt
     */
    function deallocate(
        IERC20 token,
        uint256 tokensAmount,
        ISwapper swapper,
        bytes calldata data
    ) external nonReentrant returns (uint256 expected, uint256 received) {
        _startNavCache();

        bool winddown = isWinddown();
        require((isAllocator[msg.sender] && !winddown) || (winddown && _debtBalance(token) == 0), ErrorsLib.OnlyAllocatorsOrWinddown());
        _requireIsToken(token);

        uint256 oraclePrice = oracles[token].price();
        uint256 slippageTolerance = winddown ? _winddownSlippageTolerance() : maxSlippage;

        // Execute swap
        (uint256 tokensSpent, uint256 assetsReceived) = _executeSwap(token, IERC20(asset), tokensAmount, swapper, data);

        // Calculate and validate slippage
        uint256 expectedAssets = tokensAmount.mulDiv(oraclePrice, ORACLE_PRECISION, Math.Rounding.Ceil);
        uint256 minAssets = _calculateMinAmount(expectedAssets, slippageTolerance);
        require(assetsReceived >= minAssets, ErrorsLib.TokenSaleNotGeneratingEnoughAssets());

        int256 slippagePct = _calculateSlippagePct(expectedAssets, assetsReceived);

        // Track slippage if not in winddown and we have positive slippage
        if (!winddown && assetsReceived < expectedAssets) {
            // slippage is already in asset units
            uint256 slippageValue = expectedAssets - assetsReceived;
            _increaseSlippage(slippageValue.mulDiv(PRECISION, totalAssets(), Math.Rounding.Ceil));
        }

        emit EventsLib.Deallocation(token, tokensSpent, expectedAssets, assetsReceived, slippagePct, swapper, data);

        _endNavCache();
        return (expectedAssets, assetsReceived);
    }

    /**
     * @notice Swaps between two investment tokens directly
     * @param from Source token to sell
     * @param to Target token to buy
     * @param tokensAmount Maximum amount of source token to sell
     * @param swapper Contract that will execute the swap
     * @param data Custom data for the swapper implementation
     * @return expected Expected amount of target token based on oracle prices
     * @return received Actual amount of target token received from the reallocation
     * @dev More gas efficient than separate deallocate + allocate
     */
    function reallocate(
        IERC20 from,
        IERC20 to,
        uint256 tokensAmount,
        ISwapper swapper,
        bytes calldata data
    ) external nonReentrant returns (uint256 expected, uint256 received) {
        _startNavCache();

        _onlyAllocator();
        _requireNotWinddown();
        _requireIsToken(from);
        _requireIsToken(to);

        uint256 fromOraclePrice = oracles[from].price();
        uint256 toOraclePrice = oracles[to].price();

        // Execute swap
        (uint256 fromSpent, uint256 toReceived) = _executeSwap(from, to, tokensAmount, swapper, data);

        // Calculate expected amounts and validate slippage
        uint256 fromValue = tokensAmount.mulDiv(fromOraclePrice, ORACLE_PRECISION, Math.Rounding.Ceil);
        uint256 expectedToTokens = fromValue.mulDiv(ORACLE_PRECISION, toOraclePrice, Math.Rounding.Ceil);
        uint256 minToTokens = _calculateMinAmount(expectedToTokens, maxSlippage);
        require(toReceived >= minToTokens, ErrorsLib.ReallocationSlippageTooHigh());

        int256 slippagePct = _calculateSlippagePct(expectedToTokens, toReceived);

        // Track slippage if we have positive slippage
        // Note: No winddown check needed as reallocate cannot be called during winddown
        if (toReceived < expectedToTokens) {
            uint256 slippageValue = (expectedToTokens - toReceived).mulDiv(toOraclePrice, ORACLE_PRECISION, Math.Rounding.Ceil);
            _increaseSlippage(slippageValue.mulDiv(PRECISION, totalAssets(), Math.Rounding.Ceil));
        }

        emit EventsLib.Reallocation(from, to, fromSpent, expectedToTokens, toReceived, slippagePct, swapper, data);

        _endNavCache();
        return (expectedToTokens, toReceived);
    }

    // ========== FUNDING FUNCTIONS ==========

    /**
     * @notice Posts collateral to a lending facility
     * @param fundingModule Module managing the facility
     * @param facilityData Encoded facility identifier
     * @param collateralToken Token to pledge as collateral
     * @param collateralAmount Amount to pledge
     * @dev Transfers tokens to module and updates collateral position
     */
    function pledge(
        IFunding fundingModule,
        bytes calldata facilityData,
        IERC20 collateralToken,
        uint256 collateralAmount
    ) external nonReentrant {
        _onlyAllocatorNotWinddown();
        _requireIsFunding(fundingModule);

        collateralToken.safeTransfer(address(fundingModule), collateralAmount);
        fundingModule.pledge(facilityData, collateralToken, collateralAmount);

        emit EventsLib.Pledge(fundingModule, facilityData, collateralToken, collateralAmount);
    }

    /**
     * @notice Withdraws collateral from a lending facility
     * @param fundingModule Module managing the facility
     * @param facilityData Encoded facility identifier
     * @param collateralToken Token to withdraw
     * @param collateralAmount Amount to withdraw (max uint256 = all)
     * @dev Returns tokens to vault, must maintain required collateral ratios
     */
    function depledge(
        IFunding fundingModule,
        bytes calldata facilityData,
        IERC20 collateralToken,
        uint256 collateralAmount
    ) external nonReentrant {
        _onlyAllocatorOrWinddown();
        _requireIsFunding(fundingModule);

        uint256 pledgeAmount = fundingModule.collateralBalance(facilityData, collateralToken);

        if (collateralAmount == type(uint256).max) {
            collateralAmount = pledgeAmount;
        }

        fundingModule.depledge(facilityData, collateralToken, collateralAmount);

        emit EventsLib.Depledge(fundingModule, facilityData, collateralToken, collateralAmount);
    }

    /**
     * @notice Takes out a loan from a lending facility
     * @param fundingModule Module managing the facility
     * @param facilityData Encoded facility identifier
     * @param debtToken Token to borrow
     * @param borrowAmount Amount to borrow
     * @dev Requires sufficient collateral, borrowed tokens sent to vault
     */
    function borrow(IFunding fundingModule, bytes calldata facilityData, IERC20 debtToken, uint256 borrowAmount) external nonReentrant {
        _onlyAllocatorNotWinddown();
        _requireIsFunding(fundingModule);

        fundingModule.borrow(facilityData, debtToken, borrowAmount);

        emit EventsLib.Borrow(fundingModule, facilityData, debtToken, borrowAmount);
    }

    /**
     * @notice Repays borrowed tokens to a lending facility
     * @param fundingModule Module managing the facility
     * @param facilityData Encoded facility identifier
     * @param debtToken Token to repay
     * @param repayAmount Amount to repay (max uint256 = full debt)
     * @dev Transfers tokens from vault to module, reduces debt position
     */
    function repay(IFunding fundingModule, bytes calldata facilityData, IERC20 debtToken, uint256 repayAmount) external nonReentrant {
        _onlyAllocatorOrWinddown();
        _requireIsFunding(fundingModule);

        uint256 debtAmount = fundingModule.debtBalance(facilityData, debtToken);

        if (repayAmount > debtAmount) {
            repayAmount = debtAmount;
        }

        debtToken.safeTransfer(address(fundingModule), repayAmount);
        fundingModule.repay(facilityData, debtToken, repayAmount);

        emit EventsLib.Repay(fundingModule, facilityData, debtToken, repayAmount);
    }

    /**
     * @notice Recovers non-position tokens from a funding module
     * @param fundingModule Module to skim from
     * @param token Token to recover
     * @dev NAV must remain unchanged to prevent skimming tokenized positions
     */
    function skimFunding(IFunding fundingModule, IERC20 token) external nonReentrant {
        _onlyAllocatorOrWinddown();
        _requireIsFunding(fundingModule);

        fundingModule.skim(token);
    }

    /**
     * @notice Provides temporary liquidity for complex operations
     * @param flashToken Token to flash loan
     * @param flashAmount Amount to provide temporarily
     * @param data Custom data passed to the callback
     * @dev Caller must implement IBoxFlashCallback; the Box returns the tokens within the same transaction
     * @dev NAV is cached during flash to prevent manipulation
     */
    function flash(IERC20 flashToken, uint256 flashAmount, bytes calldata data) external {
        _onlyAllocatorOrWinddown();
        _requireNonZeroAddress(address(flashToken));
        _requireIsTokenOrAsset(flashToken);
        // Prevent re-entrancy. Can't use nonReentrant modifier because of conflict with allocate/deallocate/reallocate
        require(_cachedNavDepth == 0, ErrorsLib.ReentryNotAllowed());

        // Cache NAV before starting flash operation for slippage calculations
        _startNavCache();

        // Transfer flash amount FROM caller TO this contract
        flashToken.safeTransferFrom(msg.sender, address(this), flashAmount);

        // Call the callback function on the caller
        IBoxFlashCallback(msg.sender).onBoxFlash(flashToken, flashAmount, data);

        // Repay the flash loan by transferring back TO caller
        flashToken.safeTransfer(msg.sender, flashAmount);

        _endNavCache();

        emit EventsLib.Flash(msg.sender, flashToken, flashAmount);
    }

    /**
     * @notice Executes multiple calls in a single transaction
     * @param data Array of encoded function calls
     * @dev Allows EOAs to execute multiple operations atomically
     */
    function multicall(bytes[] calldata data) external {
        uint256 length = data.length;
        for (uint256 i = 0; i < length; i++) {
            (bool success, bytes memory returnData) = address(this).delegatecall(data[i]);
            if (!success) {
                assembly ("memory-safe") {
                    revert(add(32, returnData), mload(returnData))
                }
            }
        }
    }

    // ========== ADMIN FUNCTIONS ==========

    /**
     * @notice Sets the address that receives skimmed tokens
     * @param newSkimRecipient New recipient address for skimmed tokens
     * @dev Only owner can call this function
     */
    function setSkimRecipient(address newSkimRecipient) external {
        _onlyOwner();
        _requireNonZeroAddress(newSkimRecipient);
        address oldRecipient = skimRecipient;
        _requireNotEqualAddress(newSkimRecipient, oldRecipient);

        skimRecipient = newSkimRecipient;

        emit EventsLib.SkimRecipientUpdated(oldRecipient, newSkimRecipient);
    }

    /**
     * @notice Transfers ownership of the contract
     * @param newOwner Address that will become the new owner
     * @dev Immediately transfers all owner privileges
     */
    function transferOwnership(address newOwner) external {
        _requireNonZeroAddress(newOwner);
        address oldOwner = owner;
        _onlyOwner();
        _requireNotEqualAddress(newOwner, oldOwner);

        owner = newOwner;

        emit EventsLib.OwnershipTransferred(oldOwner, newOwner);
    }

    /**
     * @notice Sets a new curator for the vault
     * @param newCurator Address that will manage tokens and funding
     * @dev Only owner can update the curator
     */
    function setCurator(address newCurator) external {
        _onlyOwner();
        _requireNonZeroAddress(newCurator);
        _requireNotEqualAddress(newCurator, curator);

        address oldCurator = curator;
        curator = newCurator;

        emit EventsLib.CuratorUpdated(oldCurator, newCurator);
    }

    /**
     * @notice Sets a new guardian with emergency powers
     * @param newGuardian Address that can trigger shutdowns and revoke actions
     * @dev Requires timelock, only curator can execute
     */
    function setGuardian(address newGuardian) external {
        _requireNotWinddown();
        timelocked();
        _onlyCurator();
        _requireNonZeroAddress(newGuardian);
        _requireNotEqualAddress(newGuardian, guardian);

        address oldGuardian = guardian;
        guardian = newGuardian;

        emit EventsLib.GuardianUpdated(oldGuardian, newGuardian);
    }

    /**
     * @notice Grants or revokes allocator privileges
     * @param account Address to modify permissions for
     * @param newIsAllocator True to grant allocator role, false to revoke
     * @dev Allocators can execute investment strategies
     */
    function setIsAllocator(address account, bool newIsAllocator) external {
        _onlyCurator();
        _requireNonZeroAddress(account);
        require(isAllocator[account] != newIsAllocator, ErrorsLib.InvalidValue());

        isAllocator[account] = newIsAllocator;

        emit EventsLib.AllocatorUpdated(account, newIsAllocator);
    }

    /**
     * @notice Initiates emergency shutdown of the vault
     * @dev Stops deposits and starts the wind-down process after warmup period
     * @dev Guardian or curator can trigger shutdown
     */
    function shutdown() external {
        require(msg.sender == guardian || msg.sender == curator, ErrorsLib.OnlyGuardianOrCuratorCanShutdown());
        require(!isShutdown(), ErrorsLib.AlreadyShutdown());

        shutdownTime = block.timestamp;

        emit EventsLib.Shutdown(msg.sender);
    }

    /**
     * @notice Cancels shutdown and returns vault to normal operation
     * @dev Only guardian can recover, must be before wind-down phase starts
     */
    function recover() external {
        require(msg.sender == guardian, ErrorsLib.OnlyGuardianCanRecover());
        require(isShutdown(), ErrorsLib.NotShutdown());
        require(!isWinddown(), ErrorsLib.CannotRecoverAfterWinddown());

        shutdownTime = type(uint256).max;

        emit EventsLib.Recover(msg.sender);
    }

    // ========== TIMELOCK GOVERNANCE ==========

    /**
     * @notice Submits a function call to the timelock queue
     * @param data Encoded function call to be executed after delay
     * @dev Delay duration depends on the function selector
     * @dev WARNING: Timelock periods are 0 by default. Users and the box owner should ensure that
     *      sufficiently long timelock periods are set for all critical functions (especially setGuardian)
     *      to allow the guardian time to react if the curator is compromised.
     */
    function submit(bytes calldata data) external {
        _onlyCurator();
        require(executableAt[data] == 0, ErrorsLib.DataAlreadyTimelocked());
        require(data.length >= 4, ErrorsLib.InvalidAmount());

        bytes4 selector = bytes4(data);
        uint256 delay = selector == IBox.decreaseTimelock.selector ? timelock[bytes4(data[4:8])] : timelock[selector];
        require(delay != TIMELOCK_DISABLED, ErrorsLib.FunctionDisabled());
        executableAt[data] = block.timestamp + delay;

        emit EventsLib.TimelockSubmitted(selector, data, executableAt[data], msg.sender);
    }

    /**
     * @dev Validates and consumes a timelocked transaction
     * @dev Checks if current calldata is timelocked and ready for execution
     */
    function timelocked() internal {
        require(executableAt[msg.data] > 0, ErrorsLib.DataNotTimelocked());
        require(block.timestamp >= executableAt[msg.data], ErrorsLib.TimelockNotExpired());

        executableAt[msg.data] = 0;

        emit EventsLib.TimelockExecuted(bytes4(msg.data), msg.data, msg.sender);
    }

    /**
     * @notice Cancels a pending timelocked transaction
     * @param data Encoded function call to cancel
     * @dev Guardian or curator can revoke pending transactions
     */
    function revoke(bytes calldata data) external {
        require(msg.sender == curator || msg.sender == guardian, ErrorsLib.OnlyCuratorOrGuardian());
        require(executableAt[data] > 0, ErrorsLib.DataNotTimelocked());

        executableAt[data] = 0;

        emit EventsLib.TimelockRevoked(bytes4(data), data, msg.sender);
    }

    /**
     * @notice Extends the timelock delay for a function
     * @param selector Function signature to modify
     * @param newDuration New delay in seconds (must be longer than current)
     * @dev No timelock required to increase delays
     */
    function increaseTimelock(bytes4 selector, uint256 newDuration) external {
        _onlyCurator();
        require(newDuration <= TIMELOCK_CAP, ErrorsLib.InvalidTimelock());
        require(newDuration > timelock[selector], ErrorsLib.TimelockNotIncreasing());

        timelock[selector] = newDuration;

        emit EventsLib.TimelockIncreased(selector, newDuration, msg.sender);
    }

    /**
     * @notice Reduces the timelock delay for a function
     * @param selector Function signature to modify
     * @param newDuration New delay in seconds (must be shorter than current)
     * @dev Requires timelock to prevent governance attacks
     */
    function decreaseTimelock(bytes4 selector, uint256 newDuration) external {
        timelocked();
        _onlyCurator();
        uint256 currentTimelock = timelock[selector];
        require(currentTimelock != TIMELOCK_DISABLED, ErrorsLib.InvalidTimelock());
        require(newDuration < currentTimelock, ErrorsLib.TimelockNotDecreasing());

        timelock[selector] = newDuration;

        emit EventsLib.TimelockDecreased(selector, newDuration, msg.sender);
    }

    /**
     * @notice Permanently disables a function by setting infinite timelock
     * @param selector Function signature to disable
     * @dev Irreversible - function becomes permanently inaccessible
     * @dev Does not impact previsously queued changes
     */
    function abdicateTimelock(bytes4 selector) external {
        _onlyCurator();

        timelock[selector] = TIMELOCK_DISABLED;

        emit EventsLib.TimelockIncreased(selector, TIMELOCK_DISABLED, msg.sender);
    }

    // ========== TIMELOCKED FUNCTIONS ==========

    /**
     * @notice Grants or revokes deposit privileges
     * @param account Address to modify permissions for
     * @param newIsFeeder True to allow deposits, false to revoke
     * @dev Requires timelock to add feeders
     */
    function setIsFeeder(address account, bool newIsFeeder) external {
        timelocked();
        _requireNonZeroAddress(account);
        require(isFeeder[account] != newIsFeeder, ErrorsLib.InvalidValue());

        isFeeder[account] = newIsFeeder;

        emit EventsLib.FeederUpdated(account, newIsFeeder);
    }

    /**
     * @notice Sets the maximum tolerated slippage for swaps
     * @param newMaxSlippage New limit scaled by PRECISION (e.g., 0.01e18 = 1%)
     * @dev Requires timelock, applies per-swap and per-epoch
     */
    function setMaxSlippage(uint256 newMaxSlippage) external {
        timelocked();
        require(newMaxSlippage <= MAX_SLIPPAGE_LIMIT, ErrorsLib.SlippageTooHigh());
        _requireNotEqual(newMaxSlippage, maxSlippage);

        uint256 oldMaxSlippage = maxSlippage;
        maxSlippage = newMaxSlippage;

        emit EventsLib.MaxSlippageUpdated(oldMaxSlippage, newMaxSlippage);
    }

    /**
     * @notice Whitelists a new investment token
     * @param token Token contract to add
     * @param oracle Price feed for the token
     * @dev Requires timelock, oracle must return prices in base asset terms
     */
    function addToken(IERC20 token, IOracle oracle) external {
        timelocked();
        _requireNonZeroAddress(address(token));
        _requireNotEqualAddress(address(token), asset);
        require(address(oracle) != address(0), ErrorsLib.OracleRequired());
        require(!isToken(token), ErrorsLib.TokenAlreadyWhitelisted());
        require(tokens.length < MAX_TOKENS, ErrorsLib.TooManyTokens());

        tokens.push(token);
        oracles[token] = oracle;

        emit EventsLib.TokenAdded(token, oracle);
    }

    /**
     * @notice Removes a token from the whitelist
     * @param token Token to delist
     * @dev Token balance must be zero and not used in any funding module
     */
    function removeToken(IERC20 token) external {
        _onlyCurator();
        _requireIsToken(token);
        require(token.balanceOf(address(this)) == 0, ErrorsLib.TokenBalanceMustBeZero());
        require(!_isTokenUsedInFunding(token), ErrorsLib.CannotRemove());

        uint256 length = tokens.length;
        for (uint256 i; i < length; i++) {
            if (tokens[i] == token) {
                tokens[i] = tokens[length - 1];
                tokens.pop();
                break;
            }
        }

        delete oracles[token];

        emit EventsLib.TokenRemoved(token);
    }

    /**
     * @notice Updates the price oracle for a whitelisted token
     * @param token Token to update oracle for
     * @param oracle New price feed contract
     * @dev Requires timelock in normal operation, guardian can update during final wind-down
     */
    function changeTokenOracle(IERC20 token, IOracle oracle) external {
        if (isWinddown()) {
            require(block.timestamp >= shutdownTime + shutdownWarmup + shutdownSlippageDuration, ErrorsLib.NotAllowed());
            _onlyGuardian();
        } else {
            _onlyCurator();
            timelocked();
        }
        _requireNonZeroAddress(address(oracle));
        _requireIsToken(token);
        _requireNotEqualAddress(address(oracles[token]), address(oracle));

        oracles[token] = oracle;

        emit EventsLib.TokenOracleChanged(token, oracle);
    }

    /**
     * @notice Adds a new funding module for borrowing/lending
     * @param fundingModule Module contract to whitelist
     * @dev Module must be empty with no facilities, collateral, or debt
     */
    function addFunding(IFunding fundingModule) external {
        timelocked();
        require(!fundingMap[fundingModule], ErrorsLib.AlreadyWhitelisted());
        _requireNonZeroAddress(address(fundingModule));
        // Check that Box is the owner of the funding module
        (bool success, bytes memory data) = address(fundingModule).staticcall(abi.encodeWithSignature("owner()"));
        require(success && data.length == 32, ErrorsLib.InvalidValue());
        address fundingOwner = abi.decode(data, (address));
        require(fundingOwner == address(this), ErrorsLib.InvalidValue());
        require(fundingModule.facilitiesLength() == 0, ErrorsLib.NotClean());
        require(fundingModule.collateralTokensLength() == 0, ErrorsLib.NotClean());
        require(fundingModule.debtTokensLength() == 0, ErrorsLib.NotClean());

        fundingMap[fundingModule] = true;
        fundings.push(fundingModule);

        emit EventsLib.FundingModuleAdded(fundingModule);
    }

    /**
     * @notice Registers a lending facility within a funding module
     * @param fundingModule Module to add facility to
     * @param facilityData Encoded facility parameters
     * @dev Requires timelock, facility specifics depend on module implementation
     */
    function addFundingFacility(IFunding fundingModule, bytes calldata facilityData) external {
        timelocked();
        _requireIsFunding(fundingModule);

        fundingModule.addFacility(facilityData);

        emit EventsLib.FundingFacilityAdded(fundingModule, facilityData);
    }

    /**
     * @notice Enables a token as collateral in a funding module
     * @param fundingModule Module to configure
     * @param collateralToken Token to use as collateral
     * @dev Token must be whitelisted in the vault first
     */
    function addFundingCollateral(IFunding fundingModule, IERC20 collateralToken) external {
        timelocked();
        _requireIsFunding(fundingModule);
        _requireIsTokenOrAsset(collateralToken);

        fundingModule.addCollateralToken(collateralToken);

        emit EventsLib.FundingCollateralAdded(fundingModule, collateralToken);
    }

    /**
     * @notice Enables a token for borrowing in a funding module
     * @param fundingModule Module to configure
     * @param debtToken Token that can be borrowed
     * @dev Token must be whitelisted in the vault first
     */
    function addFundingDebt(IFunding fundingModule, IERC20 debtToken) external {
        timelocked();
        _requireIsFunding(fundingModule);
        _requireIsTokenOrAsset(debtToken);

        fundingModule.addDebtToken(debtToken);

        emit EventsLib.FundingDebtAdded(fundingModule, debtToken);
    }

    /**
     * @notice Removes a funding module from the vault
     * @param fundingModule Module to remove
     * @dev Module must be empty with no active facilities, collateral, or debt
     */
    function removeFunding(IFunding fundingModule) external {
        _onlyCurator();
        _requireIsFunding(fundingModule);

        require(fundingModule.facilitiesLength() == 0, ErrorsLib.CannotRemove());
        require(fundingModule.collateralTokensLength() == 0, ErrorsLib.CannotRemove());
        require(fundingModule.debtTokensLength() == 0, ErrorsLib.CannotRemove());

        fundingMap[fundingModule] = false;
        uint256 index = _findFundingIndex(fundingModule);
        fundings[index] = fundings[fundings.length - 1];
        fundings.pop();

        emit EventsLib.FundingModuleRemoved(fundingModule);
    }

    /**
     * @notice Deregisters a lending facility from a funding module
     * @param fundingModule Module containing the facility
     * @param facilityData Encoded facility identifier
     * @dev Facility must have no outstanding positions
     */
    function removeFundingFacility(IFunding fundingModule, bytes calldata facilityData) external {
        _onlyCurator();
        _requireIsFunding(fundingModule);

        fundingModule.removeFacility(facilityData);

        emit EventsLib.FundingFacilityRemoved(fundingModule, facilityData);
    }

    /**
     * @notice Disables a token as collateral in a funding module
     * @param fundingModule Module to update
     * @param collateralToken Token to remove from collateral list
     * @dev Token must not be actively used as collateral
     */
    function removeFundingCollateral(IFunding fundingModule, IERC20 collateralToken) external {
        _onlyCurator();
        _requireIsFunding(fundingModule);

        fundingModule.removeCollateralToken(collateralToken);

        emit EventsLib.FundingCollateralRemoved(fundingModule, collateralToken);
    }

    /**
     * @notice Disables borrowing of a token in a funding module
     * @param fundingModule Module to update
     * @param debtToken Token to remove from debt list
     * @dev No outstanding debt must exist for this token
     */
    function removeFundingDebt(IFunding fundingModule, IERC20 debtToken) external {
        _onlyCurator();
        _requireIsFunding(fundingModule);

        fundingModule.removeDebtToken(debtToken);

        emit EventsLib.FundingDebtRemoved(fundingModule, debtToken);
    }

    // ========== VIEW FUNCTIONS ==========
    /**
     * @notice Checks if a token is whitelisted for investment
     * @param token Token to check
     * @return True if the token has an associated oracle
     */
    function isToken(IERC20 token) public view returns (bool) {
        return address(oracles[token]) != address(0);
    }

    /**
     * @notice Checks if a token is the base asset or a whitelisted token
     * @param token Token to check
     * @return True if it's the base asset or has an oracle
     */
    function isTokenOrAsset(IERC20 token) public view returns (bool) {
        return address(token) == asset || address(oracles[token]) != address(0);
    }

    /**
     * @notice Gets the count of whitelisted tokens
     * @return Number of tokens in the investment list
     */
    function tokensLength() external view returns (uint256) {
        return tokens.length;
    }

    /**
     * @notice Checks if a funding module is authorized
     * @param fundingModule Module to verify
     * @return True if the module can be used for borrowing/lending
     */
    function isFunding(IFunding fundingModule) public view returns (bool) {
        return fundingMap[fundingModule];
    }

    /**
     * @notice Gets the count of active funding modules
     * @return Number of modules available for borrowing/lending
     */
    function fundingsLength() external view override returns (uint256) {
        return fundings.length;
    }

    /**
     * @notice Checks if the vault is in shutdown mode
     * @return True if shutdown has been triggered
     */
    function isShutdown() public view returns (bool) {
        return shutdownTime != type(uint256).max;
    }

    /**
     * @notice Checks if the vault has entered wind-down phase
     * @return True if past the warmup period after shutdown
     */
    function isWinddown() public view returns (bool) {
        return shutdownTime != type(uint256).max && block.timestamp >= shutdownTime + shutdownWarmup;
    }

    // ========== INTERNAL FUNCTIONS ==========

    /**
     * @dev Checks if msg.sender is the owner
     */
    function _onlyOwner() internal view {
        require(msg.sender == owner, ErrorsLib.OnlyOwner());
    }

    /**
     * @dev Checks if msg.sender is the curator
     */
    function _onlyCurator() internal view {
        require(msg.sender == curator, ErrorsLib.OnlyCurator());
    }

    /**
     * @dev Checks that an address is not zero
     */
    function _requireNonZeroAddress(address addr) internal pure {
        require(addr != address(0), ErrorsLib.InvalidAddress());
    }

    /**
     * @dev Checks if a token is whitelisted
     */
    function _requireIsToken(IERC20 token) internal view {
        require(isToken(token), ErrorsLib.TokenNotWhitelisted());
    }

    /**
     * @dev Checks if a funding module is whitelisted
     */
    function _requireIsFunding(IFunding fundingModule) internal view {
        require(isFunding(fundingModule), ErrorsLib.NotWhitelisted());
    }

    /**
     * @dev Checks that vault is not in winddown
     */
    function _requireNotWinddown() internal view {
        require(!isWinddown(), ErrorsLib.CannotDuringWinddown());
    }

    /**
     * @dev Checks if msg.sender is allocator and not in winddown
     */
    function _onlyAllocatorNotWinddown() internal view {
        require(isAllocator[msg.sender] && !isWinddown(), ErrorsLib.OnlyAllocators());
    }

    /**
     * @dev Checks if msg.sender is allocator or in winddown
     */
    function _onlyAllocatorOrWinddown() internal view {
        require(isAllocator[msg.sender] || isWinddown(), ErrorsLib.OnlyAllocatorsOrWinddown());
    }

    /**
     * @dev Checks that two values are not equal
     */
    function _requireNotEqual(uint256 a, uint256 b) internal pure {
        require(a != b, ErrorsLib.InvalidValue());
    }

    /**
     * @dev Checks that two addresses are not equal
     */
    function _requireNotEqualAddress(address a, address b) internal pure {
        require(a != b, ErrorsLib.InvalidValue());
    }

    /**
     * @dev Checks if msg.sender is the guardian
     */
    function _onlyGuardian() internal view {
        require(msg.sender == guardian, ErrorsLib.OnlyGuardian());
    }

    /**
     * @dev Checks if msg.sender is allocator
     */
    function _onlyAllocator() internal view {
        require(isAllocator[msg.sender], ErrorsLib.OnlyAllocators());
    }

    /**
     * @dev Checks if msg.sender is feeder
     */
    function _onlyFeeder() internal view {
        require(isFeeder[msg.sender], ErrorsLib.OnlyFeeders());
    }

    /**
     * @dev Checks that vault is not shutdown
     */
    function _requireNotShutdown() internal view {
        require(!isShutdown(), ErrorsLib.CannotDuringShutdown());
    }

    /**
     * @dev Checks if token is whitelisted or is the base asset
     */
    function _requireIsTokenOrAsset(IERC20 token) internal view {
        require(isTokenOrAsset(token), ErrorsLib.TokenNotWhitelisted());
    }

    /**
     * @dev Starts NAV caching for the current operation
     * @dev Caches NAV on first call (depth 0 -> 1), increments depth on nested calls
     * @dev Properly handles nesting when swaps are called from flash callbacks
     */
    function _startNavCache() internal {
        if (_cachedNavDepth == 0) {
            _cachedNav = _nav();
        }
        _cachedNavDepth++;
    }

    /**
     * @dev Ends NAV caching for the current operation
     * @dev Decrements the depth counter
     */
    function _endNavCache() internal {
        _cachedNavDepth--;
    }

    /**
     * @dev Executes a swap through a swapper contract with approval management
     * @param fromToken Token to sell
     * @param toToken Token to buy
     * @param maxAmount Maximum amount of fromToken to sell
     * @param swapper Swapper contract to execute the trade
     * @param data Custom data for the swapper
     * @return spent Actual amount of fromToken spent
     * @return received Amount of toToken received
     */
    function _executeSwap(
        IERC20 fromToken,
        IERC20 toToken,
        uint256 maxAmount,
        ISwapper swapper,
        bytes calldata data
    ) internal returns (uint256 spent, uint256 received) {
        uint256 fromBefore = fromToken.balanceOf(address(this));
        uint256 toBefore = toToken.balanceOf(address(this));

        fromToken.forceApprove(address(swapper), maxAmount);
        swapper.sell(fromToken, toToken, maxAmount, data);
        fromToken.forceApprove(address(swapper), 0);

        spent = fromBefore - fromToken.balanceOf(address(this));
        received = toToken.balanceOf(address(this)) - toBefore;

        require(spent <= maxAmount, ErrorsLib.SwapperDidSpendTooMuch());
    }

    /**
     * @dev Calculates slippage percentage from expected vs actual amounts
     * @param expectedAmount Expected amount based on oracle price
     * @param actualAmount Actual amount received/spent
     * @return slippagePct Slippage as a percentage scaled by PRECISION
     */
    function _calculateSlippagePct(uint256 expectedAmount, uint256 actualAmount) internal pure returns (int256 slippagePct) {
        if (expectedAmount == 0) return 0;

        int256 slippage = expectedAmount.toInt256() - actualAmount.toInt256();
        // Round up when calculating slippage to be conservative
        if (slippage >= 0) {
            // Positive slippage (loss): round up
            slippagePct = int256(uint256(slippage).mulDiv(PRECISION, expectedAmount, Math.Rounding.Ceil));
        } else {
            // Negative slippage (gain): round down (more conservative)
            slippagePct = -int256(uint256(-slippage).mulDiv(PRECISION, expectedAmount, Math.Rounding.Floor));
        }
    }

    /**
     * @dev Calculates minimum acceptable amount based on slippage tolerance
     * @param expectedAmount Expected amount based on oracle price
     * @param tolerance Maximum allowed slippage scaled by PRECISION
     * @return minAmount Minimum acceptable amount after slippage
     */
    function _calculateMinAmount(uint256 expectedAmount, uint256 tolerance) internal pure returns (uint256 minAmount) {
        minAmount = expectedAmount.mulDiv(PRECISION - tolerance, PRECISION, Math.Rounding.Ceil);
    }

    /**
     * @dev Tracks slippage within current epoch and enforces limits
     * @param slippagePct Slippage to add scaled by PRECISION
     * @dev Resets epoch if duration has passed
     */
    function _increaseSlippage(uint256 slippagePct) internal {
        // Reset epoch if expired
        if (block.timestamp >= slippageEpochStart + slippageEpochDuration) {
            slippageEpochStart = block.timestamp;
            accumulatedSlippage = slippagePct;
            emit EventsLib.SlippageEpochReset(block.timestamp);
        } else {
            accumulatedSlippage += slippagePct;
        }

        require(accumulatedSlippage < maxSlippage, ErrorsLib.TooMuchAccumulatedSlippage());

        emit EventsLib.SlippageAccumulated(slippagePct, accumulatedSlippage);
    }

    /**
     * @dev Calculates total vault value across all positions
     * @return nav Sum of base asset, token values, and funding positions
     * @dev Negative funding NAV is floored to zero
     * @dev Reverts if called during NAV-cached operations (swaps or flash) to prevent read-only reentrancy
     */
    function _nav() internal view returns (uint256 nav) {
        require(_cachedNavDepth == 0, ErrorsLib.NoNavDuringCache());
        nav = IERC20(asset).balanceOf(address(this));

        // Add value of all tokens
        uint256 length = tokens.length;
        for (uint256 i; i < length; i++) {
            IERC20 token = tokens[i];
            IOracle oracle = oracles[token];
            uint256 tokenBalance = token.balanceOf(address(this));
            if (tokenBalance > 0) {
                nav += tokenBalance.mulDiv(oracle.price(), ORACLE_PRECISION);
            }
        }
        // Loop over funding sources
        length = fundings.length;
        for (uint256 i; i < length; i++) {
            IFunding funding = fundings[i];
            nav += funding.nav(IOracleCallback(address(this)));
        }
    }

    /**
     * @dev Calculates dynamic slippage tolerance during wind-down
     * @return Slippage limit that increases linearly over shutdown duration
     * @dev Returns up to 1% slippage after full duration
     */
    function _winddownSlippageTolerance() internal view returns (uint256) {
        uint256 timeElapsed = block.timestamp - shutdownWarmup - shutdownTime;
        return
            (timeElapsed < shutdownSlippageDuration)
                ? timeElapsed.mulDiv(MAX_SLIPPAGE_LIMIT, shutdownSlippageDuration)
                : MAX_SLIPPAGE_LIMIT;
    }

    /**
     * @dev Locates a funding module's position in the array
     * @param fundingModule Module to find
     * @return Index in the fundings array
     * @dev Reverts if module is not whitelisted
     */
    function _findFundingIndex(IFunding fundingModule) internal view returns (uint256) {
        uint256 length = fundings.length;
        for (uint256 i = 0; i < length; i++) {
            if (fundings[i] == fundingModule) {
                return i;
            }
        }
        revert ErrorsLib.NotWhitelisted();
    }

    /**
     * @dev Checks if a token is used in any funding module
     * @param token Token to check
     * @return True if token is used as collateral or debt anywhere
     */
    function _isTokenUsedInFunding(IERC20 token) internal view returns (bool) {
        uint256 length = fundings.length;
        for (uint256 i; i < length; i++) {
            IFunding funding = fundings[i];
            if (funding.isCollateralToken(token) || funding.isDebtToken(token)) {
                return true;
            }
        }
        return false;
    }

    /**
     * @dev Sums outstanding debt for a token across all modules
     * @param debtToken Token to check debt for
     * @return totalDebt Combined debt balance from all facilities
     */
    function _debtBalance(IERC20 debtToken) internal view returns (uint256 totalDebt) {
        uint256 length = fundings.length;
        for (uint256 i; i < length; i++) {
            IFunding funding = fundings[i];
            totalDebt += funding.debtBalance(debtToken);
        }
    }
}
