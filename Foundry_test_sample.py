curl -L https://foundry.paradigm.xyz | bash
foundryup

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/EntryPoint.sol";
import "../src/Wallet.sol";
import "../src/Paymaster.sol";

contract TestSetup is Test {
    EntryPoint public entryPoint;
    Wallet public wallet;
    Paymaster public paymaster;
    address public user = address(0x123);
    uint256 public userKey = 0x123; // Only used for simulated signature. Actually applying should use vm.addr

    function setUp() public virtual {
        entryPoint = new EntryPoint();
        wallet = new Wallet(address(entryPoint));
        paymaster = new Paymaster();

        // Deposit some ETH into the wallet for paying the gas fee (if the wallet is a contract account, it needs to be deployed first)
        vm.deal(address(wallet), 10 ether);
        entryPoint.depositTo{value: 5 ether}(address(wallet));
    }

    function _signUserOp(UserOperation memory op, uint256 privateKey) internal returns (bytes memory) {）
        bytes32 hash = entryPoint.getUserOpHash(op);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(privateKey, hash);
        return abi.encodePacked(r, s, v);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Setup.sol";

contract SignatureInvariantTest is TestSetup {
    // Fuzz testing: Attempt to invoke handleOps using randomly invalid signatures
    function testFuzz_InvalidSignatureReverts(bytes memory maliciousSig) public {
        // Construct a valid UserOperation (excluding the signature)
        UserOperation memory op = _createBaseUserOp();
        op.signature = maliciousSig; // random signatures

        UserOperation[] memory ops = new UserOperation[](1);
        ops[0] = op;

        vm.expectRevert(abi.encodeWithSignature("FailedOp(uint256,string)", 0, "AA24 signature error"));
        entryPoint.handleOps(ops, payable(user));
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Setup.sol";

contract NonceInvariantTest is TestSetup {
    function test_NonceMonotonicallyIncreasing() public {
        address sender = address(wallet);
        uint256 nonceBefore = entryPoint.getNonce(sender, 0);

        // Submit a legal operation
        UserOperation memory op = _createBaseUserOp();
        op.nonce = nonceBefore;
        op.signature = _signUserOp(op, userKey);

        UserOperation[] memory ops = new UserOperation[](1);
        ops[0] = op;

        entryPoint.handleOps(ops, payable(user));

        uint256 nonceAfter = entryPoint.getNonce(sender, 0);
        assertEq(nonceAfter, nonceBefore + 1, "Nonce should increase by 1");
    }

    function testFail_ReplaySameNonce() public {
        // Submit twice using the same nonce.
        address sender = address(wallet);
        uint256 nonce = entryPoint.getNonce(sender, 0);

        UserOperation memory op = _createBaseUserOp();
        op.nonce = nonce;
        op.signature = _signUserOp(op, userKey);

        UserOperation[] memory ops = new UserOperation[](1);
        ops[0] = op;

        entryPoint.handleOps(ops, payable(user)); // 第一次成功

        //  The second submission should fail.
        entryPoint.handleOps(ops, payable(user)); // If revert, test passes.
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Setup.sol";

contract BalanceInvariantTest is TestSetup {
    function invariant_senderDepositNeverNegative() public {
        uint256 balance = entryPoint.balanceOf(address(wallet));
        assertGe(balance, 0, "Deposit balance should never be negative");
    }

    function test_CannotSpendMoreThanDeposit() public {
        // Empty the deposit
        entryPoint.withdrawTo(payable(user), entryPoint.balanceOf(address(wallet)));

        // Attempt to perform an operation that requires gas.
        UserOperation memory op = _createBaseUserOp();
        op.signature = _signUserOp(op, userKey);

        UserOperation[] memory ops = new UserOperation[](1);
        ops[0] = op;

        //  Expect revert dut to 0 balance in account
        vm.expectRevert(abi.encodeWithSignature("FailedOp(uint256,string)", 0, "AA21 didn't pay prefund"));
        entryPoint.handleOps(ops, payable(user));
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Setup.sol";

contract MaliciousWallet {
    EntryPoint public entryPoint;

    constructor(address _entryPoint) {
        entryPoint = EntryPoint(_entryPoint);
    }

    function validateUserOp(UserOperation calldata, bytes32, uint256) external returns (uint256 validationData) {
        // Malicious: Callback to EntryPoint during verification stage
        entryPoint.getUserOpHash(UserOperation({...})); // Attampt to re-enter
        return 0;
    }
}

contract ReentrancyTest is TestSetup {
    function test_NoReentrancyInValidation() public {
        MaliciousWallet badWallet = new MaliciousWallet(address(entryPoint));
        vm.deal(address(badWallet), 1 ether);

        UserOperation memory op = _createBaseUserOp();
        op.sender = address(badWallet);
        op.signature = ""; // No signature, cause validateUserOp return 0（Malicious logic）

        UserOperation[] memory ops = new UserOperation[](1);
        ops[0] = op;

        // Expect revert or no changing in state
        vm.expectRevert("Reentrancy detected");
        entryPoint.handleOps(ops, payable(user));
    }
}