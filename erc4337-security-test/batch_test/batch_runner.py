import json
import time
from typing import List, Dict, Any
from web3 import Web3, exceptions
from eth_account import Account, messages
from .config import RPC_URL, DEPLOYMENTS_PATH
from .ai_generator import AttackVector

class BatchRunner:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to Hardhat node at {RPC_URL}")
            
        self._load_deployments()
        self._init_contracts()
        self._init_accounts()
        
    def _load_deployments(self):
        if not DEPLOYMENTS_PATH.exists():
            raise FileNotFoundError(f"Deployments file not found at {DEPLOYMENTS_PATH}")
        with open(DEPLOYMENTS_PATH, 'r') as f:
            self.deployments = json.load(f)
            
    def _init_contracts(self):
        self.entrypoint = self.w3.eth.contract(
            address=self.deployments['contracts']['entryPoint']['address'],
            abi=self.deployments['contracts']['entryPoint']['abi']
        )
        self.account = self.w3.eth.contract(
            address=self.deployments['contracts']['simpleAccount']['address'],
            abi=self.deployments['contracts']['simpleAccount']['abi']
        )
        
    def _init_accounts(self):
        # Hardhat default accounts
        self.deployer = Account.from_key('0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80')
        self.attacker = Account.from_key('0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d')
        self.user = Account.from_key('0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a')

    def execute_batch(self, attacks: List[AttackVector]) -> List[Dict[str, Any]]:
        results = []
        print(f"🚀 Starting batch execution of {len(attacks)} attacks...")
        
        for i, attack in enumerate(attacks):
            print(f"[{i+1}/{len(attacks)}] Executing {attack.name}: {attack.description}")
            result = self._execute_single_attack(attack)
            results.append(result)
            # Small delay to prevent nonce race conditions if we were sending valid txs rapidly
            # (though for attacks we expect reverts)
            time.sleep(0.1)
            
        return results

    def _execute_single_attack(self, attack: AttackVector) -> Dict[str, Any]:
        try:
            # 1. Prepare UserOperation
            op = self._construct_user_op(attack)
            
            # 2. Send Transaction
            # We call handleOps from the attacker's address
            tx_hash = self.entrypoint.functions.handleOps([op], self.attacker.address).transact({
                'from': self.deployer.address, # Using deployer to pay for gas to submit the tx
                'gas': 5000000
            })
            
            # 3. Wait for Receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # 4. Analyze Result
            if receipt.status == 1:
                return {
                    'name': attack.name,
                    'type': attack.attack_type,
                    'status': 'VULNERABLE', # Transaction succeeded -> Attack worked -> Vulnerability exists
                    'description': attack.description,
                    'tx_hash': tx_hash.hex(),
                    'error': None
                }
            else:
                return {
                    'name': attack.name,
                    'type': attack.attack_type,
                    'status': 'BLOCKED', # Transaction failed -> Attack blocked -> Secure
                    'description': attack.description,
                    'tx_hash': tx_hash.hex(),
                    'error': 'Transaction reverted (status 0)'
                }
                
        except exceptions.ContractLogicError as e:
            # This is the most common outcome for a blocked attack (revert with reason)
            return {
                'name': attack.name,
                'type': attack.attack_type,
                'status': 'BLOCKED',
                'description': attack.description,
                'tx_hash': None,
                'error': str(e)
            }
        except Exception as e:
            return {
                'name': attack.name,
                'type': attack.attack_type,
                'status': 'ERROR', # Test execution error
                'description': attack.description,
                'tx_hash': None,
                'error': str(e)
            }

    def _construct_user_op(self, attack: AttackVector):
        # Get current nonce
        current_nonce = self.entrypoint.functions.nonces(self.account.address).call()
        
        # Apply nonce offset (for replay attacks)
        nonce = current_nonce + attack.nonce_offset
        
        # Default gas values
        call_gas = int(200000 * attack.call_gas_limit_factor)
        verification_gas = int(100000 * attack.verification_gas_limit_factor)
        
        # Construct CallData (execute function)
        call_data = self.account.functions.execute(
            self.attacker.address,
            0,
            b''
        )._encode_transaction_data()
        
        # Determine signature
        if attack.signature is not None:
            signature = attack.signature
        else:
            # Valid signature for baseline
            msg_hash = self.entrypoint.functions.getUserOpHash((
                self.account.address, nonce, b'', call_data,
                call_gas, verification_gas, 21000,
                self.w3.eth.gas_price, self.w3.eth.gas_price,
                b'', b'' # Empty signature for hash calculation
            )).call()
            # This is a simplification; normally we'd sign the hash. 
            # But for fuzzing, we usually provide explicit signatures in the attack vector.
            # If no signature provided, we default to empty (which is an attack in itself)
            signature = b''

        return (
            self.account.address,
            nonce,
            b'',          # initCode
            call_data,
            call_gas,
            verification_gas,
            21000,        # preVerificationGas
            self.w3.eth.gas_price,
            self.w3.eth.gas_price,
            b'',          # paymasterAndData
            signature
        )
