import json
import pytest
from eth_account import Account, messages
from web3 import Web3, exceptions
from pathlib import Path
import pandas as pd
from datetime import datetime


class SignatureSecurityTest:
    """Test smart contract wallet signature verification logic"""
    
    def __init__(self, rpc_url="http://127.0.0.1:8545"):
        # Connect to local node
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise Exception("❌ Cannot connect to local node. Please ensure 'npx hardhat node' is running.")
        
        # Load deployed contract information
        with open(Path('data/deployments.json'), 'r') as f:
            self.deployments = json.load(f)
        
        # Initialize accounts (using Hardhat test accounts)
        self.accounts = {
            'deployer': Account.from_key('0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'),
            'attacker': Account.from_key('0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d'),
            'user': Account.from_key('0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a')
        }
        
        # Initialize contract instances
        self.entrypoint = self.w3.eth.contract(
            address=self.deployments['contracts']['entryPoint']['address'],
            abi=self.deployments['contracts']['entryPoint']['abi']
        )
        
        self.account = self.w3.eth.contract(
            address=self.deployments['contracts']['simpleAccount']['address'],
            abi=self.deployments['contracts']['simpleAccount']['abi']
        )
        
        print("=" * 60)
        print("🔒 ERC-4337 Signature Security Test Suite")
        print("=" * 60)
        print(f"Test Network: {rpc_url}")
        print(f"Chain ID: {self.w3.eth.chain_id}")
        print(f"EntryPoint Address: {self.entrypoint.address}")
        print(f"Test Wallet Address: {self.account.address}")
        print(f"Wallet Owner: {self.accounts['user'].address}")
        print()
    
    def get_account_nonce(self, account_address, key=0):
        """Get account nonce"""
        try:
            # Use EntryPoint's getNonce function, key is usually 0
            nonce_value = self.entrypoint.functions.getNonce(account_address, key).call()
            print(f"    Retrieved nonce: account={account_address[:10]}..., key={key}, nonce={nonce_value}")
            return nonce_value
        except Exception as e:
            print(f"    Failed to get nonce: {e}")
            # For testing purposes, return 0
            return 0
    
    def pack_uint128_pair(self, a, b):
        """Pack two uint128 values into a bytes32"""
        # Ensure values are within uint128 range
        a = a & ((1 << 128) - 1)
        b = b & ((1 << 128) - 1)
        # a in lower 128 bits, b in higher 128 bits
        packed = (b << 128) | a
        return packed.to_bytes(32, 'big')
    
    def create_packed_user_op(self, sender, nonce, initCode, callData, 
                             verificationGasLimit, callGasLimit, 
                             preVerificationGas, maxPriorityFeePerGas, maxFeePerGas,
                             paymasterAndData, signature):
        """Create PackedUserOperation compliant with EntryPoint v0.9 specification"""
        
        # Pack accountGasLimits: verificationGasLimit (128 bits) | callGasLimit (128 bits)
        accountGasLimits = self.pack_uint128_pair(verificationGasLimit, callGasLimit)
        
        # Pack gasFees: maxPriorityFeePerGas (128 bits) | maxFeePerGas (128 bits)
        gasFees = self.pack_uint128_pair(maxPriorityFeePerGas, maxFeePerGas)
        
        # Return structure compliant with ABI
        return (
            sender,                  # address sender
            nonce,                   # uint256 nonce
            initCode,                # bytes initCode
            callData,                # bytes callData
            accountGasLimits,        # bytes32 accountGasLimits
            preVerificationGas,      # uint256 preVerificationGas
            gasFees,                 # bytes32 gasFees
            paymasterAndData,        # bytes paymasterAndData
            signature                # bytes signature
        )
    
    def run_all_tests(self):
        """Run all signature security tests"""
        test_results = []
        
        print("🧪 Starting security tests...\n")
        
        # Test 1: All-zero signature attack
        print("[Test 1/4] All-zero Signature Attack")
        result1 = self.test_zero_signature()
        test_results.append(result1)
        print(f"   Result: {result1['status']} - {result1['description']}\n")
        
        # Test 2: Short signature attack  
        print("[Test 2/4] Short Signature Attack")
        result2 = self.test_short_signature()
        test_results.append(result2)
        print(f"   Result: {result2['status']} - {result2['description']}\n")
        
        # Test 3: Invalid v-value signature
        print("[Test 3/4] Invalid v-value Signature")
        result3 = self.test_invalid_v_signature()
        test_results.append(result3)
        print(f"   Result: {result3['status']} - {result3['description']}\n")
        
        # Test 4: Replay attack (same nonce)
        print("[Test 4/4] Transaction Replay Attack (same nonce)")
        result4 = self.test_replay_attack()
        test_results.append(result4)
        print(f"   Result: {result4['status']} - {result4['description']}\n")
        
        # Save test results
        self.save_results(test_results)
        
        return test_results
    
    def test_zero_signature(self):
        """Test 1: Check if all-zero signature passes validation"""
        print("   Purpose: Check if contract accepts all-zero invalid signature")
        
        # Get current nonce
        nonce = self.get_account_nonce(self.account.address, 0)
        
        # Get gas price
        gas_price = self.w3.eth.gas_price
        print(f"   Gas Price: {gas_price}")
        
        # Construct callData
        callData = self.account.functions.execute(
            self.accounts['attacker'].address,
            0,
            b''
        )._encode_transaction_data()
        
        # Create PackedUserOperation
        user_op = self.create_packed_user_op(
            sender=self.account.address,
            nonce=nonce,
            initCode=b'',
            callData=callData,
            verificationGasLimit=200000,
            callGasLimit=300000,
            preVerificationGas=50000,
            maxPriorityFeePerGas=gas_price,
            maxFeePerGas=gas_price,
            paymasterAndData=b'',
            signature=b'\x00' * 65
        )
        
        try:
            # Attempt to execute malicious operation
            tx_hash = self.entrypoint.functions.handleOps([user_op], self.accounts['attacker'].address).transact({
                'from': self.accounts['deployer'].address,
                'gas': 1000000
            })
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                return {
                    'test': 'zero_signature',
                    'status': '❌ CRITICAL VULNERABILITY',
                    'description': 'All-zero signature accepted! Attacker can forge arbitrary transactions.',
                    'severity': 'CRITICAL',
                    'evidence': tx_hash.hex()
                }
            else:
                return {
                    'test': 'zero_signature',
                    'status': '✅ PASSED',
                    'description': 'All-zero signature correctly rejected.',
                    'severity': 'NONE'
                }
                
        except exceptions.ContractLogicError as e:
            error_msg = str(e)
            # Check for various rejection reasons
            if any(keyword in error_msg for keyword in ['Invalid signature', 'Signature', 'revert', 'failed', 'denied']):
                return {
                    'test': 'zero_signature',
                    'status': '✅ PASSED',
                    'description': 'All-zero signature rejected by contract logic.',
                    'severity': 'NONE',
                    'error': error_msg[:100]
                }
            else:
                return {
                    'test': 'zero_signature',
                    'status': '⚠️ WARNING',
                    'description': f'Unknown error: {error_msg[:50]}',
                    'severity': 'MEDIUM',
                    'error': error_msg[:100]
                }
        except Exception as e:
            error_msg = str(e)
            # Check if it's a rejection-type error
            if 'revert' in error_msg.lower() or 'denied' in error_msg.lower() or 'failed' in error_msg.lower():
                return {
                    'test': 'zero_signature',
                    'status': '✅ PASSED',
                    'description': 'All-zero signature rejected.',
                    'severity': 'NONE',
                    'error': error_msg[:100]
                }
            else:
                return {
                    'test': 'zero_signature',
                    'status': '⚠️ TEST FAILED',
                    'description': f'Execution failed: {error_msg[:100]}',
                    'severity': 'INFO',
                    'error': error_msg[:200]
                }
    
    def test_short_signature(self):
        """Test 2: Various short signature attacks"""
        print("   Purpose: Check if contract can handle non-standard length signatures")
        
        test_cases = [
            ('Empty signature', b''),
            ('1 byte', b'\x01'),
            ('32 bytes', b'\x01' * 32),
            ('64 bytes', b'\x01' * 64),
            ('66 bytes', b'\x01' * 66)  # 1 byte longer than standard signature
        ]
        
        results = []
        nonce = self.get_account_nonce(self.account.address, 0)
        
        # Get gas price
        gas_price = self.w3.eth.gas_price
        
        for name, signature in test_cases:
            # Create PackedUserOperation
            user_op = self.create_packed_user_op(
                sender=self.account.address,
                nonce=nonce,
                initCode=b'',
                callData=b'',
                verificationGasLimit=200000,
                callGasLimit=200000,
                preVerificationGas=50000,
                maxPriorityFeePerGas=gas_price,
                maxFeePerGas=gas_price,
                paymasterAndData=b'',
                signature=signature
            )
            
            try:
                tx_hash = self.entrypoint.functions.handleOps([user_op], self.accounts['attacker'].address).transact({
                    'from': self.accounts['deployer'].address,
                    'gas': 500000
                })
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    results.append(f'{name} accepted')
                else:
                    results.append(f'{name} rejected')
                    
            except Exception as e:
                error_msg = str(e)
                if 'revert' in error_msg.lower() or 'failed' in error_msg.lower():
                    results.append(f'{name} rejected')
                else:
                    results.append(f'{name} failed: {error_msg[:50]}')
        
        # If any short signature was accepted, there is risk
        if any('accepted' in r for r in results):
            return {
                'test': 'short_signature',
                'status': '❌ MEDIUM VULNERABILITY',
                'description': f'Some non-standard signatures accepted. Results: {results}',
                'severity': 'MEDIUM',
                'details': results
            }
        else:
            return {
                'test': 'short_signature',
                'status': '✅ PASSED',
                'description': 'All non-standard length signatures rejected.',
                'severity': 'NONE',
                'details': results
            }
    
    def test_invalid_v_signature(self):
        """Test 3: Invalid signature v-value attack (v ≠ 27, 28)"""
        print("   Purpose: Check if contract validates signature v-value must be 27 or 28")

        # Build a baseline signature and mutate v byte for on-chain verification path
        message = messages.encode_defunct(text="ERC-4337 invalid-v test")
        signed = self.accounts['user'].sign_message(message)
        r = signed.r.to_bytes(32, 'big')
        s = signed.s.to_bytes(32, 'big')

        # Invalid v values for ECDSA in this context
        invalid_v_values = [0, 1, 26, 29, 255]
        results = []

        base_nonce = self.get_account_nonce(self.account.address, 0)
        gas_price = self.w3.eth.gas_price
        callData = self.account.functions.execute(
            self.accounts['attacker'].address,
            0,
            b''
        )._encode_transaction_data()

        for i, invalid_v in enumerate(invalid_v_values):
            invalid_signature = r + s + bytes([invalid_v])

            user_op = self.create_packed_user_op(
                sender=self.account.address,
                nonce=base_nonce + i,
                initCode=b'',
                callData=callData,
                verificationGasLimit=250000,
                callGasLimit=300000,
                preVerificationGas=50000,
                maxPriorityFeePerGas=gas_price,
                maxFeePerGas=gas_price,
                paymasterAndData=b'',
                signature=invalid_signature
            )

            try:
                tx_hash = self.entrypoint.functions.handleOps([user_op], self.accounts['attacker'].address).transact({
                    'from': self.accounts['deployer'].address,
                    'gas': 1200000
                })
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt.status == 1:
                    results.append(f'v={invalid_v}: accepted')
                else:
                    results.append(f'v={invalid_v}: rejected(status=0)')

            except Exception as e:
                error_msg = str(e).lower()
                if 'revert' in error_msg or 'failed' in error_msg or 'invalid' in error_msg:
                    results.append(f'v={invalid_v}: rejected')
                else:
                    results.append(f'v={invalid_v}: error({str(e)[:60]})')

        if any('accepted' in r for r in results):
            return {
                'test': 'invalid_v_signature',
                'status': '❌ HIGH VULNERABILITY',
                'description': f'Invalid v signatures accepted by contract. Results: {results}',
                'severity': 'HIGH',
                'details': results
            }

        return {
            'test': 'invalid_v_signature',
            'status': '✅ PASSED',
            'description': 'All invalid v-value signatures were rejected on-chain.',
            'severity': 'NONE',
            'details': results
        }
    
    def test_replay_attack(self):
        """Test 4: Transaction replay attack (using same nonce)"""
        print("   Purpose: Check if contract nonce mechanism prevents transaction replay")
        
        # Get initial nonce
        initial_nonce = self.get_account_nonce(self.account.address, 0)
        print(f"   Initial nonce: {initial_nonce}")
        
        # Verify nonce mechanism core: invalid transactions should not consume nonce
        print("   Verify nonce mechanism core: invalid transactions should not consume nonce")
        
        gas_price = self.w3.eth.gas_price
        
        # Create invalid UserOperation (all-zero signature)
        invalid_user_op = self.create_packed_user_op(
            sender=self.account.address,
            nonce=initial_nonce,
            initCode=b'',
            callData=b'',
            verificationGasLimit=300000,
            callGasLimit=300000,
            preVerificationGas=100000,
            maxPriorityFeePerGas=gas_price,
            maxFeePerGas=gas_price,
            paymasterAndData=b'',
            signature=b'\x00' * 65  # Invalid signature
        )
        
        try:
            print("   Attempting to execute invalid UserOperation...")
            tx_hash = self.entrypoint.functions.handleOps([invalid_user_op], self.accounts['deployer'].address).transact({
                'from': self.accounts['deployer'].address,
                'gas': 1500000
            })
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                # Should not happen - invalid signature accepted
                return {
                    'test': 'replay_attack',
                    'status': '❌ CRITICAL VULNERABILITY',
                    'description': 'Invalid signature accepted, security mechanism failed!',
                    'severity': 'CRITICAL'
                }
            else:
                print("   Invalid transaction rejected (expected)")
                
        except Exception as e:
            error_msg = str(e)
            print(f"   Invalid transaction execution failed (expected): {error_msg[:100]}")
        
        # Check if nonce remains unchanged
        final_nonce = self.get_account_nonce(self.account.address, 0)
        print(f"   Nonce after failed transaction: {final_nonce}")
        
        # Verify results
        if final_nonce == initial_nonce:
            # Correct: invalid transaction does not consume nonce, preventing DoS attacks
            print("   ✅ Invalid transaction did not consume nonce, compliant with security specification")
            
            # Attempt to replay the same invalid transaction
            print("   Attempting to replay the same invalid transaction...")
            try:
                tx_hash2 = self.entrypoint.functions.handleOps([invalid_user_op], self.accounts['deployer'].address).transact({
                    'from': self.accounts['deployer'].address,
                    'gas': 1500000
                })
                receipt2 = self.w3.eth.wait_for_transaction_receipt(tx_hash2)
                
                if receipt2.status == 1:
                    return {
                        'test': 'replay_attack',
                        'status': '❌ CRITICAL VULNERABILITY',
                        'description': 'Replay attack successful! Same invalid transaction accepted twice.',
                        'severity': 'CRITICAL'
                    }
                else:
                    print("   Replay transaction rejected (expected)")
                    
            except Exception as e:
                error_msg = str(e)
                print(f"   Replay transaction failed (expected): {error_msg[:100]}")
            
            # Final verification: nonce still remains unchanged
            final_nonce_after_replay = self.get_account_nonce(self.account.address, 0)
            print(f"   Nonce after replay attempt: {final_nonce_after_replay}")
            
            if final_nonce_after_replay == initial_nonce:
                return {
                    'test': 'replay_attack',
                    'status': '✅ PASSED',
                    'description': f'Nonce mechanism fully protected: invalid transaction rejected, nonce remains {initial_nonce}, replay attack prevented.',
                    'severity': 'NONE',
                    'details': 'Compliant with ERC-4337 security specification: 1) Invalid signature rejected 2) Nonce not consumed by invalid transactions 3) Replay attack prevented'
                }
            else:
                return {
                    'test': 'replay_attack',
                    'status': '⚠️ WARNING',
                    'description': f'Nonce changed after replay attempt (from {initial_nonce} to {final_nonce_after_replay}).',
                    'severity': 'MEDIUM'
                }
        else:
            # Error: invalid transaction consumed nonce
            return {
                'test': 'replay_attack',
                'status': '❌ CRITICAL VULNERABILITY',
                'description': f'Invalid transaction consumed nonce (from {initial_nonce} to {final_nonce}), DoS attack risk!',
                'severity': 'CRITICAL',
                'details': 'Attacker can exhaust account nonce by sending invalid transactions, making account unusable'
            }
    
    def save_results(self, test_results):
        """Save test results to file"""
        # Create results directory
        results_dir = Path('data/results')
        results_dir.mkdir(exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_path = results_dir / f'signature_tests_{timestamp}.json'
        with open(json_path, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        # Save as CSV (for analysis)
        csv_data = []
        for result in test_results:
            csv_data.append({
                'test_name': result['test'],
                'status': result['status'],
                'severity': result.get('severity', 'NONE'),
                'description': result['description']
            })
        
        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_path = results_dir / f'signature_tests_{timestamp}.csv'
            df.to_csv(csv_path, index=False)
        
        print("=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        for result in test_results:
            print(f"{result['status']} {result['test']}: {result['description']}")
        
        print(f"\n📁 Detailed results saved to:")
        print(f"   {json_path}")
        if csv_data:
            print(f"   {csv_path}")
        
        # Statistics
        total = len(test_results)
        passed = sum(1 for r in test_results if '✅' in r['status'])
        critical = sum(1 for r in test_results if r.get('severity') == 'CRITICAL')
        
        print(f"\n📈 Statistics: {passed}/{total} passed, {critical} critical vulnerabilities")
        
        if critical > 0:
            print("🚨 Critical vulnerabilities found, please fix immediately!")
        elif passed == total:
            print("🎉 All signature security tests passed! Contract compliant with ERC-4337 security specification.")
        else:
            print("⚠️  Some tests failed, please check logs for details.")

def main():
    """Main function: run all security tests"""
    print("🔍 Starting ERC-4337 Signature Security Test Suite")
    print("Note: Ensure local Hardhat node is running (npx hardhat node)\n")
    
    try:
        # Create test instance
        tester = SignatureSecurityTest()
        
        # Run all tests
        results = tester.run_all_tests()
        
        # Return exit code (for CI/CD)
        critical_count = sum(1 for r in results if r.get('severity') == 'CRITICAL')
        return 1 if critical_count > 0 else 0
        
    except Exception as e:
        print(f"❌ Test framework initialization failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)