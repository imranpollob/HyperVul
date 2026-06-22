// SPDX-License-Identifier: MIT
pragma solidity 0.8.11;




// Failed to resolve import: import {AccessControlUpgradeable} from "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
// Failed to resolve import: import {PausableUpgradeable} from "@openzeppelin/contracts-upgradeable/security/PausableUpgradeable.sol";





interface IL1MessageQueueV2 {
    /**********
     * Events *
     **********/

    /// @notice Emitted when a new L1 => L2 transaction is appended to the queue.
    /// @param sender The address of the sender account on L2.
    /// @param target The address of the target account on L2.
    /// @param value The ETH value transferred to the target account on L2.
    /// @param queueIndex The index of this transaction in the message queue.
    /// @param gasLimit The gas limit used on L2.
    /// @param data The calldata passed to the target account on L2.
    event QueueTransaction(
        address indexed sender,
        address indexed target,
        uint256 value,
        uint64 queueIndex,
        uint256 gasLimit,
        bytes data
    );

    /// @notice Emitted when some L1 => L2 transactions are finalized on L1.
    /// @param finalizedIndex The index of the last message finalized.
    event FinalizedDequeuedTransaction(uint256 finalizedIndex);

    /*************************
     * Public View Functions *
     *************************/

    /// @notice Return the start index of all messages in this contract.
    function firstCrossDomainMessageIndex() external view returns (uint256);

    /// @notice Return the start index of all unfinalized messages.
    function nextUnfinalizedQueueIndex() external view returns (uint256);

    /// @notice Return the index to be used for the next message.
    /// @dev Also the total number of appended messages, including messages in `L1MessageQueueV1`.
    function nextCrossDomainMessageIndex() external view returns (uint256);

    /// @notice Return the message rolling hash of `queueIndex`.
    /// @param queueIndex The index to query.
    function getMessageRollingHash(uint256 queueIndex) external view returns (bytes32);

    /// @notice Return the message enqueue timestamp of `queueIndex`.
    /// @param queueIndex The index to query.
    function getMessageEnqueueTimestamp(uint256 queueIndex) external view returns (uint256);

    /// @notice Return the first unfinalized message enqueue timestamp.
    function getFirstUnfinalizedMessageEnqueueTime() external view returns (uint256);

    /// @notice Return the amount of ETH that should be paid for a cross-domain message.
    /// @param gasLimit The gas limit required to complete the message relay on L2.
    function estimateCrossDomainMessageFee(uint256 gasLimit) external view returns (uint256);

    /// @notice Return the estimated base fee on L2.
    function estimateL2BaseFee() external view returns (uint256);

    /// @notice Return the intrinsic gas required by the provided cross-domain message.
    /// @param data The calldata of the cross-domain message.
    function calculateIntrinsicGasFee(bytes calldata data) external view returns (uint256);

    /// @notice Compute the transaction hash of an L1 message.
    /// @param sender The address of the sender account.
    /// @param queueIndex The index of this transaction in the message queue.
    /// @param value The ETH value transferred to the target account.
    /// @param target The address of the target account.
    /// @param gasLimit The gas limit provided.
    /// @param data The calldata passed to the target account.
    function computeTransactionHash(
        address sender,
        uint256 queueIndex,
        uint256 value,
        address target,
        uint256 gasLimit,
        bytes calldata data
    ) external view returns (bytes32);

    /*****************************
     * Public Mutating Functions *
     *****************************/

    /// @notice Append a L1 => L2 cross-domain message to the message queue.
    /// @param target The address of the target account on L2.
    /// @param gasLimit The gas limit used on L2.
    /// @param data The calldata passed to the target account on L2.
    /// @dev This function can only be called by `L1ScrollMessenger`.
    function appendCrossDomainMessage(
        address target,
        uint256 gasLimit,
        bytes calldata data
    ) external;

    /// @notice Append an enforced transaction to the message queue.
    /// @param sender The address of the sender account on L2.
    /// @param target The address of the target account on L2.
    /// @param value The ETH value transferred to the target account on L2.
    /// @param gasLimit The gas limit used on L2.
    /// @param data The calldata passed to the target account on L2.
    /// @dev This function can only be called by `EnforcedTxGateway`.
    function appendEnforcedTransaction(
        address sender,
        address target,
        uint256 value,
        uint256 gasLimit,
        bytes calldata data
    ) external;

    /// @notice Mark cross-domain messages as finalized.
    /// @param nextUnfinalizedQueueIndex The index of the first unfinalized message after this call.
    /// @dev This function can only be called by `ScrollChain`.
    function finalizePoppedCrossDomainMessage(uint256 nextUnfinalizedQueueIndex) external;
}





/// @title IRollupVerifier
/// @notice The interface for rollup verifier.
interface IRollupVerifier {
    /// @notice Verify aggregate zk proof.
    /// @param batchIndex The batch index to verify.
    /// @param aggrProof The aggregated proof.
    /// @param publicInputHash The public input hash.
    function verifyAggregateProof(
        uint256 batchIndex,
        bytes calldata aggrProof,
        bytes32 publicInputHash
    ) external view;

    /// @notice Verify aggregate zk proof.
    /// @param version The version of verifier to use.
    /// @param batchIndex The batch index to verify.
    /// @param aggrProof The aggregated proof.
    /// @param publicInputHash The public input hash.
    function verifyAggregateProof(
        uint256 version,
        uint256 batchIndex,
        bytes calldata aggrProof,
        bytes32 publicInputHash
    ) external view;

    /// @notice Verify bundle zk proof.
    /// @param version The version of verifier to use.
    /// @param batchIndex The batch index used to select verifier.
    /// @param bundleProof The aggregated proof.
    /// @param publicInput The public input.
    function verifyBundleProof(
        uint256 version,
        uint256 batchIndex,
        bytes calldata bundleProof,
        bytes calldata publicInput
    ) external view;
}





interface IScrollChainValidium {
    /**********
     * Events *
     **********/

    /// @notice Emitted when a new batch is committed.
    /// @param batchIndex The index of the batch.
    /// @param batchHash The hash of the batch.
    event CommitBatch(uint256 indexed batchIndex, bytes32 indexed batchHash);

    /// @notice revert a range of batches.
    /// @param startBatchIndex The start batch index of the range (inclusive).
    /// @param finishBatchIndex The finish batch index of the range (inclusive).
    event RevertBatch(uint256 indexed startBatchIndex, uint256 indexed finishBatchIndex);

    /// @notice Emitted when a batch is finalized.
    /// @param batchIndex The index of the batch.
    /// @param batchHash The hash of the batch
    /// @param stateRoot The state root on layer 2 after this batch.
    /// @param withdrawRoot The merkle root on layer2 after this batch.
    event FinalizeBatch(uint256 indexed batchIndex, bytes32 indexed batchHash, bytes32 stateRoot, bytes32 withdrawRoot);

    /// @notice Emitted when a new encryption key is added.
    /// @param keyId The incremental index of the key.
    /// @param msgIndex The message queue index at the time of key rotation.
    /// @param key The encryption key.
    event NewEncryptionKey(uint256 indexed keyId, uint256 msgIndex, bytes key);

    /*************************
     * Public View Functions *
     *************************/

    /// @return The latest finalized batch index.
    function lastFinalizedBatchIndex() external view returns (uint256);

    /// @return The latest committed batch index.
    function lastCommittedBatchIndex() external view returns (uint256);

    /// @param batchIndex The index of the batch.
    /// @return The batch hash of a committed batch.
    function committedBatches(uint256 batchIndex) external view returns (bytes32);

    /// @param batchIndex The index of the batch.
    /// @return The state root of a committed batch.
    function stateRoots(uint256 batchIndex) external view returns (bytes32);

    /// @param batchIndex The index of the batch.
    /// @return The message root of a committed batch.
    function withdrawRoots(uint256 batchIndex) external view returns (bytes32);

    /// @param batchIndex The index of the batch.
    /// @return Whether the batch is finalized by batch index.
    function isBatchFinalized(uint256 batchIndex) external view returns (bool);

    /// @return The key-id of the latest encryption key.
    /// @return The latest encryption key.
    function getLatestEncryptionKey() external view returns (uint256, bytes memory);

    /// @param keyId The incremental index for the encryption key.
    /// @return The encryption key with the given key-id.
    function getEncryptionKey(uint256 keyId) external view returns (bytes memory);

    /*****************************
     * Public Mutating Functions *
     *****************************/

    /// @notice Commit a pending batch.
    /// @param version The version of this batch.
    /// @param parentBatchHash The hash of parent batch.
    /// @param stateRoot The state root after this batch.
    /// @param withdrawRoot The withdraw trie root after this batch.
    /// @param commitment The data commitment.
    function commitBatch(
        uint8 version,
        bytes32 parentBatchHash,
        bytes32 stateRoot,
        bytes32 withdrawRoot,
        bytes calldata commitment
    ) external;

    /// @notice Revert pending batches.
    /// @dev one can only revert unfinalized batches.
    /// @param batchHeader The header of the first batch we want to revert.
    function revertBatch(bytes calldata batchHeader) external;

    /// @notice Finalize a list of committed batches (i.e. bundle) on layer 1.
    /// @param batchHeader The header of the last batch in this bundle.
    /// @param totalL1MessagesPoppedOverall The number of messages processed after this bundle.
    /// @param aggrProof The aggregation proof for current bundle.
    function finalizeBundle(
        bytes calldata batchHeader,
        uint256 totalL1MessagesPoppedOverall,
        bytes calldata aggrProof
    ) external;
}






// solhint-disable no-inline-assembly

/// @dev Below is the encoding for `BatchHeaderValidium` V0, total 105 + dynamic bytes.
/// ```text
///   * Field                   Bytes       Type        Index   Comments
///   * version                 1           uint8       0       The batch version.
///   * batchIndex              8           uint64      1       The index of the batch.
///   * parentBatchHash         32          bytes32     9       The parent batch hash.
///   * postStateRoot           32          bytes32     41      The state root after this batch.
///   * withdrawRoot            32          bytes32     73      The withdraw root after this batch.
///   * commitment              dynamic     bytes       105     A dynamic data commitment.
/// ```
library BatchHeaderValidiumV0Codec {
    /// @dev Thrown when the length of batch header is smaller than 105
    error ErrorBatchHeaderV0LengthTooSmall();

    /// @dev The length of fixed parts of the batch header.
    uint256 internal constant BATCH_HEADER_FIXED_LENGTH = 105;

    /// @notice Load batch header in calldata to memory.
    /// @param _batchHeader The encoded batch header bytes in calldata.
    /// @return batchPtr The start memory offset of the batch header in memory.
    /// @return length The length in bytes of the batch header.
    function loadAndValidate(bytes calldata _batchHeader) internal pure returns (uint256 batchPtr, uint256 length) {
        length = _batchHeader.length;
        if (length < BATCH_HEADER_FIXED_LENGTH) revert ErrorBatchHeaderV0LengthTooSmall();

        // copy batch header to memory.
        assembly {
            batchPtr := mload(0x40)
            calldatacopy(batchPtr, _batchHeader.offset, length)
            mstore(0x40, add(batchPtr, length))
        }
    }

    /// @notice Get the version of the batch header.
    /// @param batchPtr The start memory offset of the batch header in memory.
    /// @return _version The version of the batch header.
    function getVersion(uint256 batchPtr) internal pure returns (uint256 _version) {
        assembly {
            _version := shr(248, mload(batchPtr))
        }
    }

    /// @notice Get the batch index of the batch.
    /// @param batchPtr The start memory offset of the batch header in memory.
    /// @return _batchIndex The batch index of the batch.
    function getBatchIndex(uint256 batchPtr) internal pure returns (uint256 _batchIndex) {
        assembly {
            _batchIndex := shr(192, mload(add(batchPtr, 1)))
        }
    }

    /// @notice Get the parent batch hash of the batch.
    /// @param batchPtr The start memory offset of the batch header in memory.
    /// @return _parentBatchHash The parent batch hash.
    function getParentBatchHash(uint256 batchPtr) internal pure returns (bytes32 _parentBatchHash) {
        assembly {
            _parentBatchHash := mload(add(batchPtr, 9))
        }
    }

    /// @notice Get the batch index of the batch.
    /// @param batchPtr The start memory offset of the batch header in memory.
    /// @return _postStateRoot The state root after of the batch.
    function getPostStateRoot(uint256 batchPtr) internal pure returns (bytes32 _postStateRoot) {
        assembly {
            _postStateRoot := mload(add(batchPtr, 41))
        }
    }

    /// @notice Get the withdraw root of the batch.
    /// @param batchPtr The start memory offset of the batch header in memory.
    /// @return _withdrawRoot The withdraw root of the batch.
    function getWithdrawRoot(uint256 batchPtr) internal pure returns (bytes32 _withdrawRoot) {
        assembly {
            _withdrawRoot := mload(add(batchPtr, 73))
        }
    }

    /// @notice Encode necessary fields to batch header bytes.
    ///
    /// @param version The batch version
    /// @param batchIndex The index of the batch
    /// @param parentBatchHash The parent batch hash
    /// @param postStateRoot The state root after this batch.
    /// @param withdrawRoot The withdraw root after this batch.
    /// @param commitment A dynamic data commitment.
    function encode(
        uint8 version,
        uint64 batchIndex,
        bytes32 parentBatchHash,
        bytes32 postStateRoot,
        bytes32 withdrawRoot,
        bytes memory commitment
    ) internal pure returns (bytes memory) {
        return abi.encodePacked(version, batchIndex, parentBatchHash, postStateRoot, withdrawRoot, commitment);
    }

    /// @notice Compute the batch hash.
    /// @dev Caller should make sure that the encoded batch header is correct.
    ///
    /// @param header The bytes of batch header in memory.
    /// @return batchHash The hash of the corresponding batch.
    function computeBatchHash(bytes memory header) internal pure returns (bytes32 batchHash) {
        uint256 dataPtr;
        uint256 length;
        // in the current version, the hash is: keccak(BatchHeader without timestamp)
        assembly {
            dataPtr := header
            length := mload(dataPtr)
        }
        batchHash = computeBatchHash(dataPtr + 32, length);
    }

    /// @notice Compute the batch hash.
    /// @dev Caller should make sure that the encoded batch header is correct.
    ///
    /// @param batchPtr The start memory offset of the batch header in memory.
    /// @param length The length of the batch.
    /// @return batchHash The hash of the corresponding batch.
    function computeBatchHash(uint256 batchPtr, uint256 length) internal pure returns (bytes32 batchHash) {
        // in the current version, the hash is: keccak(BatchHeader without timestamp)
        assembly {
            batchHash := keccak256(batchPtr, length)
        }
    }
}


// solhint-disable no-inline-assembly
// solhint-disable reason-string

/// @title ScrollChainValidium
contract ScrollChainValidium is AccessControlUpgradeable, PausableUpgradeable, IScrollChainValidium {
    /**********
     * Errors *
     **********/

    /// @dev Thrown when the given genesis batch is invalid.
    error ErrorInvalidGenesisBatch();

    /// @dev Thrown when finalizing a verified batch.
    error ErrorBatchIsAlreadyVerified();

    /// @dev Thrown when importing genesis batch twice.
    error ErrorGenesisBatchImported();

    /// @dev Thrown when the batch hash is incorrect.
    error ErrorIncorrectBatchHash();

    /// @dev Thrown when reverting a finalized batch.
    error ErrorRevertFinalizedBatch();

    /// @dev Thrown when the given state root is zero.
    error ErrorStateRootIsZero();

    /// @dev Thrown when given batch is not committed before.
    error ErrorBatchNotCommitted();

    /// @dev Error thrown when encryption key length is invalid.
    error ErrorInvalidEncryptionKeyLength();

    /// @dev Error thrown the user attempts to use an encryption key that is unknown.
    error ErrorUnknownEncryptionKey();

    /// @dev Error thrown the user attempts to use an encryption key that is deprecated.
    error ErrorDeprecatedEncryptionKey();

    /*************
     * Constants *
     *************/

    /// @notice The role for import genesis batch.
    bytes32 public constant GENESIS_IMPORTER_ROLE = keccak256("GENESIS_IMPORTER_ROLE");

    /// @notice The role for sequencer who can commit batch.
    bytes32 public constant SEQUENCER_ROLE = keccak256("SEQUENCER_ROLE");

    /// @notice The role for prover who can finalize batch.
    bytes32 public constant PROVER_ROLE = keccak256("PROVER_ROLE");

    /// @notice The role that can rotate encryption keys.
    bytes32 public constant KEY_MANAGER_ROLE = keccak256("KEY_MANAGER_ROLE");

    /***********************
     * Immutable Variables *
     ***********************/

    /// @notice The chain id of the corresponding layer 2 chain.
    uint64 public immutable layer2ChainId;

    /// @notice The address of `L1MessageQueueV2`.
    address public immutable messageQueueV2;

    /// @notice The address of `MultipleVersionRollupVerifier`.
    address public immutable verifier;

    /***********
     * Structs *
     ***********/

    struct EncryptionKey {
        // The on-chain message index when the key was set.
        uint256 msgIndex;
        // The 33-bytes compressed public key, i.e. encryption key.
        bytes key;
    }

    /*********************
     * Storage Variables *
     *********************/

    /// @inheritdoc IScrollChainValidium
    uint256 public override lastFinalizedBatchIndex;

    /// @inheritdoc IScrollChainValidium
    uint256 public override lastCommittedBatchIndex;

    /// @dev Mapping from batch index to batch hash.
    mapping(uint256 => bytes32) public override committedBatches;

    /// @dev Mapping from batch index to corresponding state root in Validium L3.
    mapping(uint256 => bytes32) public override stateRoots;

    /// @dev Mapping from batch index to corresponding withdraw root in Validium L3.
    mapping(uint256 => bytes32) public override withdrawRoots;

    /// @dev An array of encryption keys.
    EncryptionKey[] public encryptionKeys;

    /// @dev The storage slots reserved for future usage.
    uint256[50] private __gap;

    /***************
     * Constructor *
     ***************/

    /// @notice Constructor for `ScrollChainValidium` implementation contract.
    ///
    /// @param _chainId The chain id of L2.
    /// @param _messageQueueV2 The address of `L1MessageQueueV2`.
    /// @param _verifier The address of `MultipleVersionRollupVerifier`.
    constructor(
        uint64 _chainId,
        address _messageQueueV2,
        address _verifier
    ) {
        _disableInitializers();

        layer2ChainId = _chainId;
        messageQueueV2 = _messageQueueV2;
        verifier = _verifier;
    }

    /// @notice Initialize the storage of ScrollChainValidium.
    /// @param _admin The address of the admin.
    function initialize(address _admin) external initializer {
        __Context_init();
        __ERC165_init();
        __AccessControl_init();
        __Pausable_init();

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
    }

    /*************************
     * Public View Functions *
     *************************/

    /// @inheritdoc IScrollChainValidium
    function isBatchFinalized(uint256 _batchIndex) external view override returns (bool) {
        return _batchIndex <= lastFinalizedBatchIndex;
    }

    /// @inheritdoc IScrollChainValidium
    function getLatestEncryptionKey() external view override returns (uint256, bytes memory) {
        uint256 _numKeys = encryptionKeys.length;
        if (_numKeys == 0) revert ErrorUnknownEncryptionKey();
        return (_numKeys - 1, encryptionKeys[_numKeys - 1].key);
    }

    /// @inheritdoc IScrollChainValidium
    function getEncryptionKey(uint256 _keyId) external view override returns (bytes memory) {
        uint256 _numKeys = encryptionKeys.length;
        if (_numKeys == 0) revert ErrorUnknownEncryptionKey();
        if (_keyId >= _numKeys) revert ErrorUnknownEncryptionKey();
        if (_keyId < _numKeys - 1) revert ErrorDeprecatedEncryptionKey();
        return encryptionKeys[_numKeys - 1].key;
    }

    /*****************************
     * Public Mutating Functions *
     *****************************/

    /// @notice Import layer 2 genesis block
    /// @param _batchHeader The header of the genesis batch.
    function importGenesisBatch(bytes calldata _batchHeader) external onlyRole(GENESIS_IMPORTER_ROLE) {
        (uint256 batchPtr, uint256 _length) = BatchHeaderValidiumV0Codec.loadAndValidate(_batchHeader);
        // batch index should be 0 for genesis batch
        if (BatchHeaderValidiumV0Codec.getBatchIndex(batchPtr) != 0) {
            revert ErrorInvalidGenesisBatch();
        }
        // parant batch hash should be 0 for genesis batch
        if (BatchHeaderValidiumV0Codec.getParentBatchHash(batchPtr) != bytes32(0)) {
            revert ErrorInvalidGenesisBatch();
        }
        // withdraw root should be 0 for genesis batch
        if (BatchHeaderValidiumV0Codec.getWithdrawRoot(batchPtr) != bytes32(0)) {
            revert ErrorInvalidGenesisBatch();
        }

        bytes32 _postStateRoot = BatchHeaderValidiumV0Codec.getPostStateRoot(batchPtr);

        // check state root
        if (_postStateRoot == bytes32(0)) revert ErrorStateRootIsZero();

        // check whether the genesis batch is imported
        if (stateRoots[0] != bytes32(0)) revert ErrorGenesisBatchImported();

        bytes32 _batchHash = BatchHeaderValidiumV0Codec.computeBatchHash(batchPtr, _length);

        committedBatches[0] = _batchHash;
        stateRoots[0] = _postStateRoot;

        emit CommitBatch(0, _batchHash);
        emit FinalizeBatch(0, _batchHash, _postStateRoot, bytes32(0));
    }

    /// @inheritdoc IScrollChainValidium
    function commitBatch(
        uint8 version,
        bytes32 parentBatchHash,
        bytes32 postStateRoot,
        bytes32 withdrawRoot,
        bytes calldata commitment
    ) external onlyRole(SEQUENCER_ROLE) whenNotPaused {
        if (postStateRoot == bytes32(0)) revert ErrorStateRootIsZero();

        uint256 cachedLastCommittedBatchIndex = lastCommittedBatchIndex;
        if (parentBatchHash != committedBatches[cachedLastCommittedBatchIndex]) {
            revert ErrorIncorrectBatchHash();
        }

        cachedLastCommittedBatchIndex += 1;
        bytes memory batchHeader = BatchHeaderValidiumV0Codec.encode(
            version,
            uint64(cachedLastCommittedBatchIndex),
            parentBatchHash,
            postStateRoot,
            withdrawRoot,
            commitment
        );
        bytes32 batchHash = BatchHeaderValidiumV0Codec.computeBatchHash(batchHeader);

        lastCommittedBatchIndex = cachedLastCommittedBatchIndex;
        committedBatches[cachedLastCommittedBatchIndex] = batchHash;
        stateRoots[cachedLastCommittedBatchIndex] = postStateRoot;
        withdrawRoots[cachedLastCommittedBatchIndex] = withdrawRoot;

        emit CommitBatch(cachedLastCommittedBatchIndex, batchHash);
    }

    /// @inheritdoc IScrollChainValidium
    function revertBatch(bytes calldata batchHeader) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 lastBatchIndex = lastCommittedBatchIndex;
        (, , uint256 startBatchIndex) = _loadBatchHeader(batchHeader, lastBatchIndex);

        // check finalization
        if (startBatchIndex <= lastFinalizedBatchIndex) revert ErrorRevertFinalizedBatch();

        // actual revert
        for (uint256 i = lastBatchIndex; i >= startBatchIndex; --i) {
            delete committedBatches[i];
            delete stateRoots[i];
            delete withdrawRoots[i];
        }
        emit RevertBatch(startBatchIndex, lastBatchIndex);

        // update `lastCommittedBatchIndex`
        lastCommittedBatchIndex = startBatchIndex - 1;
    }

    /// @inheritdoc IScrollChainValidium
    function finalizeBundle(
        bytes calldata batchHeader,
        uint256 totalL1MessagesPoppedOverall,
        bytes calldata aggrProof
    ) external override onlyRole(PROVER_ROLE) whenNotPaused {
        _finalizeBundle(batchHeader, totalL1MessagesPoppedOverall, aggrProof);
    }

    /************************
     * Restricted Functions *
     ************************/

    function registerNewEncryptionKey(bytes memory _key) external onlyRole(KEY_MANAGER_ROLE) {
        if (_key.length != 33) revert ErrorInvalidEncryptionKeyLength();
        uint256 _keyId = encryptionKeys.length;

        // The message from `nextCrossDomainMessageIndex` will utilise the newly registered encryption key.
        uint256 _msgIndex = IL1MessageQueueV2(messageQueueV2).nextCrossDomainMessageIndex();
        encryptionKeys.push(EncryptionKey(_msgIndex, _key));

        emit NewEncryptionKey(_keyId, _msgIndex, _key);
    }

    /// @notice Pause the contract
    /// @param _status The pause status to update.
    function setPause(bool _status) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (_status) {
            _pause();
        } else {
            _unpause();
        }
    }

    /**********************
     * Internal Functions *
     **********************/

    /// @dev Internal function to do common actions before actual batch finalization.
    function _beforeFinalizeBatch(bytes calldata batchHeader)
        internal
        view
        returns (
            uint256 version,
            bytes32 batchHash,
            uint256 batchIndex,
            uint256 prevBatchIndex
        )
    {
        uint256 batchPtr;
        // compute pending batch hash and verify
        (batchPtr, batchHash, batchIndex) = _loadBatchHeader(batchHeader, lastCommittedBatchIndex);

        // make sure don't finalize batch multiple times
        prevBatchIndex = lastFinalizedBatchIndex;
        if (batchIndex <= prevBatchIndex) revert ErrorBatchIsAlreadyVerified();

        version = BatchHeaderValidiumV0Codec.getVersion(batchPtr);
    }

    /// @dev Internal function to do common actions after actual batch finalization.
    function _afterFinalizeBatch(
        uint256 batchIndex,
        bytes32 batchHash,
        uint256 totalL1MessagesPoppedOverall,
        bytes32 postStateRoot,
        bytes32 withdrawRoot
    ) internal {
        lastFinalizedBatchIndex = batchIndex;

        if (totalL1MessagesPoppedOverall > 0) {
            IL1MessageQueueV2(messageQueueV2).finalizePoppedCrossDomainMessage(totalL1MessagesPoppedOverall);
        }

        emit FinalizeBatch(batchIndex, batchHash, postStateRoot, withdrawRoot);
    }

    /// @dev Internal function to finalize a bundle.
    /// @param batchHeader The header of the last batch in this bundle.
    /// @param totalL1MessagesPoppedOverall The number of messages processed after this bundle.
    /// @param aggrProof The bundle proof for this bundle.
    function _finalizeBundle(
        bytes calldata batchHeader,
        uint256 totalL1MessagesPoppedOverall,
        bytes calldata aggrProof
    ) internal virtual {
        // actions before verification
        (uint256 version, bytes32 batchHash, uint256 batchIndex, uint256 prevBatchIndex) = _beforeFinalizeBatch(
            batchHeader
        );

        // L1 message hashes are chained,
        // this hash commits to the whole queue up to and including `totalL1MessagesPoppedOverall-1`
        bytes32 messageQueueHash = totalL1MessagesPoppedOverall == 0
            ? bytes32(0)
            : IL1MessageQueueV2(messageQueueV2).getMessageRollingHash(totalL1MessagesPoppedOverall - 1);

        bytes32 postStateRoot = stateRoots[batchIndex];
        bytes32 withdrawRoot = withdrawRoots[batchIndex];

        // Get the encryption key at the time of on-chain message queue index.
        bytes memory encryptionKey = totalL1MessagesPoppedOverall == 0
            ? _getEncryptionKey(0)
            : _getEncryptionKey(totalL1MessagesPoppedOverall - 1);

        bytes memory publicInputs = abi.encodePacked(
            layer2ChainId,
            messageQueueHash,
            uint32(batchIndex - prevBatchIndex), // numBatches
            stateRoots[prevBatchIndex], // _prevStateRoot
            committedBatches[prevBatchIndex], // _prevBatchHash
            postStateRoot,
            batchHash,
            withdrawRoot,
            encryptionKey
        );

        // verify bundle, choose the correct verifier based on the last batch
        // our off-chain service will make sure all unfinalized batches have the same batch version.
        IRollupVerifier(verifier).verifyBundleProof(version, batchIndex, aggrProof, publicInputs);

        // actions after verification
        _afterFinalizeBatch(batchIndex, batchHash, totalL1MessagesPoppedOverall, postStateRoot, withdrawRoot);
    }

    /// @dev Internal function to load batch header from calldata to memory.
    /// @param _batchHeader The batch header in calldata.
    /// @param _lastCommittedBatchIndex The index of the last committed batch.
    /// @return batchPtr The start memory offset of loaded batch header.
    /// @return _batchHash The hash of the loaded batch header.
    /// @return _batchIndex The index of this batch.
    /// @dev This function only works with batches whose hashes are stored in `committedBatches`.
    function _loadBatchHeader(bytes calldata _batchHeader, uint256 _lastCommittedBatchIndex)
        internal
        view
        virtual
        returns (
            uint256 batchPtr,
            bytes32 _batchHash,
            uint256 _batchIndex
        )
    {
        // load version from batch header, it is always the first byte.
        uint256 version;
        assembly {
            version := shr(248, calldataload(_batchHeader.offset))
        }

        uint256 length;
        (batchPtr, length) = BatchHeaderValidiumV0Codec.loadAndValidate(_batchHeader);

        _batchIndex = BatchHeaderValidiumV0Codec.getBatchIndex(batchPtr);

        if (_batchIndex > _lastCommittedBatchIndex) revert ErrorBatchNotCommitted();

        // check against local storage
        _batchHash = BatchHeaderValidiumV0Codec.computeBatchHash(batchPtr, length);
        if (committedBatches[_batchIndex] != _batchHash) {
            revert ErrorIncorrectBatchHash();
        }
    }

    /// @dev Internal function to get the relevant encryption key that was used to encrypt messages up to the provided message index.
    /// @param _msgIndex The on-chain message queue index being finalised.
    /// @return The encryption key used at the time of the provided on-chain message queue index.
    function _getEncryptionKey(uint256 _msgIndex) internal view returns (bytes memory) {
        // Start from the "latest" key and continue fetching keys until we find the key
        // that was rotated before the message index we have been provided.
        uint256 _numKeys = encryptionKeys.length;
        if (_numKeys == 0) revert ErrorUnknownEncryptionKey();
        EncryptionKey memory _encryptionKey = encryptionKeys[--_numKeys];

        while (_encryptionKey.msgIndex > _msgIndex) {
            if (_numKeys == 0) revert ErrorUnknownEncryptionKey();
            _encryptionKey = encryptionKeys[--_numKeys];
        }

        return _encryptionKey.key;
    }
}
