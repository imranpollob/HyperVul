# HyperVul — Node Feature Extraction Specification

This document defines the exact feature extraction scheme to be used uniformly across all splits (train, validation, test, and the eval-only OpenZeppelin dataset) to prevent feature dimension and distribution mismatches.

---

## 1. Model Checkpoint
* **Model Class**: `transformers.RobertaModel`
* **Tokenizer Class**: `transformers.RobertaTokenizer`
* **Checkpoint Name**: `web3se/SmartBERT-v3` (hosted on Hugging Face / cached locally)
* **Output Dimension**: 768-dimensional float vectors

---

## 2. Pooling Strategy
* **Method**: **CLS Token Activation**
* **Implementation Details**: The model output is processed by extracting the hidden state of the first token (index `0`) of the last layer:
  ```python
  outputs = encoder(**inputs)
  cls_embeddings = outputs.last_hidden_state[:, 0, :]
  ```
  *Mean pooling is NOT used.*

---

## 3. Node Type Specific Inputs

Each hyperedge node is mapped to a text span and encoded using the tokenizer settings detailed below:

### A. Calling Function Nodes
* **Input Text**: The full raw Solidity source code of the calling function (including signature, attributes, and body).
* **Max Token Length**: 256 tokens.
* **Truncation**: `truncation=True` (truncates the function body at the tail if exceeding 256 tokens).
* **Padding**: `padding="max_length"`.

### B. State Variable Nodes
* **Input Text**: A space-separated declaration string formatted as `f"{var_type} {var_name}"` (e.g., `mapping(address => uint256) balances`). 
  * If the type cannot be resolved from the contract AST (or its inherited base contracts), the var name itself is used.
* **Max Token Length**: 256 tokens.
* **Truncation**: `truncation=True`.
* **Padding**: `padding="max_length"`.

### C. Call Site (External Call) Nodes
* **Input Text**: The exact call expression source code snippet (e.g. `IERC20(token).transfer(recipient, amount)`).
* **Max Token Length**: 64 tokens.
* **Truncation**: `truncation=True`.
* **Padding**: `padding="max_length"`.

---

## 4. OPCode and Dimension Decisions
* **Node Dimension**: Uniformly **768-d** across all three node types.
* **OPCode Flag Encoding**: The 6-dimensional external call opcode flags (representing call type, transfer methods, etc.) are **omitted** from the call site node embeddings themselves. They are deferred to the downstream G-HAN graph neural network architecture classification/data loading phase to preserve uniform embedding dimensions at the node level.
