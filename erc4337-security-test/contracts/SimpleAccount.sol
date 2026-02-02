// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.19;

interface IEntryPoint {
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
    
    function getUserOpHash(UserOperation calldata op) external pure returns (bytes32);
}

contract SimpleAccount {
    address public owner;
    IEntryPoint public entryPoint;
    
    // 部署时设置所有者和EntryPoint地址
    constructor(address _owner, address _entryPoint) {
        owner = _owner;
        entryPoint = IEntryPoint(_entryPoint);
    }
    
    // 验证UserOperation（简化版签名验证）
    function validateUserOp(
        bytes calldata userOp,
        bytes32 userOpHash,
        uint256 missingAccountFunds
    ) external returns (uint256 validationData) {
        require(msg.sender == address(entryPoint), "Only entry point");
        
        // 从userOp末尾提取签名（简化：假设签名在最后65字节）
        require(userOp.length >= 65, "Invalid userOp");
        bytes memory signature = userOp[userOp.length-65:];
        
        // 恢复签名者地址
        address recovered = recoverSigner(userOpHash, signature);
        
        if (recovered == owner) {
            return 0; // 验证成功
        } else {
            return 1; // 验证失败
        }
    }
    
    // 执行调用（只有EntryPoint可以调用）
    function execute(address dest, uint256 value, bytes calldata func) external {
        require(msg.sender == address(entryPoint), "Only entry point");
        (bool success, ) = dest.call{value: value}(func);
        require(success, "Execution failed");
    }
    
    // 从签名恢复地址
    function recoverSigner(bytes32 messageHash, bytes memory signature) internal pure returns (address) {
        require(signature.length == 65, "Invalid signature length");
        
        bytes32 r;
        bytes32 s;
        uint8 v;
        
        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }
        
        if (v < 27) v += 27;
        require(v == 27 || v == 28, "Invalid signature");
        
        return ecrecover(messageHash, v, r, s);
    }
    
    // 接收以太币
    receive() external payable {}
}