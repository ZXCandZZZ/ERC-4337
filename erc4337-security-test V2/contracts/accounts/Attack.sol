// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "../core/BaseAccount.sol";
import "../core/EntryPoint.sol";

/**
 * @title Attack
 * @dev Malicious account contract used to test ERC-4337 vulnerability.
 *      Insert your malicious logic at the "Attack code placeholder" in the validateUserOp function.
 */
contract Attack is BaseAccount {
    IEntryPoint private immutable _entryPoint;
    address public owner;
    bool public attackPerformed;

    event AttackTriggered(address sender, bytes32 userOpHash);

    constructor(IEntryPoint entryPoint_) {
        _entryPoint = entryPoint_;
        owner = msg.sender; // Attacker themselves as owner
    }

    /// @inheritdoc BaseAccount
    function entryPoint() public view override returns (IEntryPoint) {
        return _entryPoint;
    }

    /**
     * @dev Function called during the validation phase. Insert your malicious logic here.
     */
    function validateUserOp(
        PackedUserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 missingAccountFunds
    ) external override returns (uint256 validationData) {
        // Only trigger if attack has not been performed yet
        if (!attackPerformed) {
            // === Insert your attack code here ===
            // For example: attempt to re-enter EntryPoint, or drain user deposits
            // Note: directly calling entryPoint.handleOps will be blocked by nonReentrant
            // You could try calling other functions of entryPoint, or use delegatecall
            // Below is an example: emit event and mark attack as performed
            emit AttackTriggered(msg.sender, userOpHash);
            attackPerformed = true;
            // =====================================
        }

        // Verify signature (must be correct, otherwise attacker's own transaction will fail)
        validationData = _validateSignature(userOp, userOpHash);
        if (validationData != 0) {
            return validationData;
        }

        // Pay prefund (required by EntryPoint)
        _payPrefund(missingAccountFunds);
        return 0;
    }

    /**
     * @dev Implementation of BaseAccount's abstract function: signature validation.
     */
    function _validateSignature(
        PackedUserOperation calldata userOp,
        bytes32 userOpHash
    ) internal override returns (uint256 validationData) {
        if (owner != ECDSA.recover(userOpHash, userOp.signature)) {
            return SIG_VALIDATION_FAILED;
        }
        return SIG_VALIDATION_SUCCESS;
    }

    /**
     * @dev Function called during the execution phase (if the UserOperation's callData includes an executeUserOp call).
     *      Malicious logic can also be inserted here (optional).
     */
    function executeUserOp(
        PackedUserOperation calldata userOp,
        bytes32 userOpHash
    ) external {
        require(msg.sender == address(entryPoint()), "only entrypoint");
        // Attack code in execution phase (optional)
    }

    receive() external payable {}
}