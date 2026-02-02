// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.19;

// 简化的UserOperation结构
struct UserOperation {
    address sender;
    uint256 nonce;
    bytes initCode;
    bytes callData;
    uint256 callGasLimit;
    uint256 verificationGasLimit;
    uint256 preVerificationGas;
    uint256 maxFeePerGas;
    uint256 maxPriorityFeePerGas;
    bytes paymasterAndData;
    bytes signature;
}

contract SimpleEntryPoint {
    // 存储每个发送者的nonce，防止重放攻击
    mapping(address => uint256) public nonces;
    
    event UserOperationHandled(address indexed sender, uint256 nonce, bool success);
    
    // 处理UserOperations（简化版，省略了签名验证和支付逻辑）
    function handleOps(UserOperation[] calldata ops, address payable beneficiary) external {
        for (uint256 i = 0; i < ops.length; i++) {
            UserOperation calldata op = ops[i];
            
            // 验证nonce
            require(nonces[op.sender] == op.nonce, "Invalid nonce");
            nonces[op.sender]++;
            
            // 这里应该是：调用 sender 账户合约的 validateUserOp 进行验证
            // 为了简化，我们假设所有签名都有效
            
            // 执行调用
            (bool success, ) = op.sender.call(op.callData);
            
            emit UserOperationHandled(op.sender, op.nonce, success);
            require(success, "Execution failed");
        }
    }
    
    // 获取UserOperation的哈希（用于后续签名验证）
    function getUserOpHash(UserOperation calldata op) public pure returns (bytes32) {
        return keccak256(abi.encode(
            op.sender,
            op.nonce,
            keccak256(op.initCode),
            keccak256(op.callData),
            op.callGasLimit,
            op.verificationGasLimit,
            op.preVerificationGas,
            op.maxFeePerGas,
            op.maxPriorityFeePerGas,
            keccak256(op.paymasterAndData)
        ));
    }
}