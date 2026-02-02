import json
import os
from solcx import compile_source, set_solc_version
from web3 import Web3
from eth_account import Account
from pathlib import Path

# Set Solidity version (must match version in contracts)
set_solc_version('0.8.19')

class ERC4337Deployer:
    def __init__(self, rpc_url="http://127.0.0.1:8545"):
        # Connect to local Hardhat node
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise Exception("❌ Failed to connect to local node. Make sure 'npx hardhat node' is running")
        
        # Use first Hardhat test account as deployer
        self.deployer = Account.from_key(
            '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'
        )
        
        # Second account as regular user
        self.user = Account.from_key(
            '0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d'
        )
        
        print("=" * 60)
        print("ERC-4337 Contract Deployer")
        print("=" * 60)
        print(f"Network: {'Connected' if self.w3.is_connected() else 'Disconnected'}")
        print(f"Chain ID: {self.w3.eth.chain_id}")
        print(f"Deployer: {self.deployer.address}")
        print(f"User: {self.user.address}")
        print(f"Current Block: {self.w3.eth.block_number}")
        
    def compile_contract(self, contract_name):
        """Compile Solidity contract file"""
        contract_path = Path(f"contracts/{contract_name}.sol")
        if not contract_path.exists():
            raise FileNotFoundError(f"Contract file not found: {contract_path}")
        
        with open(contract_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        print(f"\nCompiling contract: {contract_name}")
        compiled = compile_source(source_code, solc_version='0.8.19')
        contract_id, contract_interface = compiled.popitem()
        
        return contract_interface['abi'], contract_interface['bin']
    
    def deploy_contract(self, contract_name, abi, bytecode, args=(), value=0):
        """Deploy contract to blockchain"""
        print(f"Deploying contract: {contract_name}")
        
        # Create contract object
        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        
        # Build deployment transaction
        transaction = contract.constructor(*args).build_transaction({
            'from': self.deployer.address,
            'nonce': self.w3.eth.get_transaction_count(self.deployer.address),
            'gas': 4000000,
            'gasPrice': self.w3.eth.gas_price,
            'value': value,
            'chainId': 31337  # Hardhat local network chain ID
        })
        
        # Sign and send transaction
        signed_txn = self.deployer.sign_transaction(transaction)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # Wait for deployment to complete
        print(f"  Transaction Hash: {tx_hash.hex()}")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            contract_address = receipt.contractAddress
            print(f"  ✅ Deployment successful!")
            print(f"     Address: {contract_address}")
            print(f"     Gas Used: {receipt.gasUsed}")
            
            # Return contract instance
            return self.w3.eth.contract(address=contract_address, abi=abi), contract_address
        else:
            raise Exception(f"Deployment failed, transaction hash: {tx_hash.hex()}")
    
    def deploy_all(self):
        """Deploy all ERC-4337 core contracts"""
        deployments = {}
        
        try:
            # 1. Deploy EntryPoint contract
            print("\n" + "=" * 60)
            print("1. Deploying SimpleEntryPoint Contract")
            print("=" * 60)
            
            entrypoint_abi, entrypoint_bytecode = self.compile_contract("SimpleEntryPoint")
            entrypoint_contract, entrypoint_address = self.deploy_contract(
                "SimpleEntryPoint", 
                entrypoint_abi, 
                entrypoint_bytecode
            )
            
            deployments['entryPoint'] = {
                'address': entrypoint_address,
                'abi': entrypoint_abi
            }
            
            # 2. Deploy SimpleAccount contract
            print("\n" + "=" * 60)
            print("2. Deploying SimpleAccount Contract")
            print("=" * 60)
            
            account_abi, account_bytecode = self.compile_contract("SimpleAccount")
            account_contract, account_address = self.deploy_contract(
                "SimpleAccount",
                account_abi,
                account_bytecode,
                args=(self.user.address, entrypoint_address)  # Set owner and EntryPoint address
            )
            
            deployments['simpleAccount'] = {
                'address': account_address,
                'abi': account_abi
            }
            
            # 3. Transfer test ETH to smart contract wallet
            print("\n" + "=" * 60)
            print("3. Transferring Test ETH to Smart Contract Wallet")
            print("=" * 60)
            
            transfer_tx = {
                'from': self.deployer.address,
                'to': account_address,
                'value': self.w3.to_wei(1, 'ether'),
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.deployer.address),
                'chainId': 31337
            }
            
            signed_transfer = self.deployer.sign_transaction(transfer_tx)
            transfer_hash = self.w3.eth.send_raw_transaction(signed_transfer.raw_transaction)
            transfer_receipt = self.w3.eth.wait_for_transaction_receipt(transfer_hash)
            
            if transfer_receipt.status == 1:
                balance = self.w3.eth.get_balance(account_address)
                print(f"  ✅ Transfer successful!")
                print(f"     Contract wallet balance: {self.w3.from_wei(balance, 'ether')} ETH")
                print(f"     Transaction hash: {transfer_hash.hex()}")
            else:
                print("  ⚠️ Transfer failed, but contract deployment succeeded")
            
            # 4. Verify contract functionality
            print("\n" + "=" * 60)
            print("4. Verifying Contract Functionality")
            print("=" * 60)
            
            # Verify SimpleAccount owner
            actual_owner = account_contract.functions.owner().call()
            print(f"  Contract wallet owner: {actual_owner}")
            print(f"  Expected owner: {self.user.address}")
            print(f"  ✅ Owner verification: {'Passed' if actual_owner == self.user.address else 'Failed'}")
            
            # Verify EntryPoint link
            actual_entrypoint = account_contract.functions.entryPoint().call()
            print(f"  Linked EntryPoint: {actual_entrypoint}")
            print(f"  Actual EntryPoint: {entrypoint_address}")
            print(f"  ✅ EntryPoint link verification: {'Passed' if actual_entrypoint == entrypoint_address else 'Failed'}")
            
            # 5. Save deployment information
            print("\n" + "=" * 60)
            print("5. Saving Deployment Information")
            print("=" * 60)
            
            # Ensure data directory exists
            data_dir = Path('data')
            data_dir.mkdir(exist_ok=True)
            
            # Save deployment info to JSON file
            deployment_info = {
                'network': {
                    'chainId': self.w3.eth.chain_id,
                    'rpcUrl': 'http://127.0.0.1:8545'
                },
                'accounts': {
                    'deployer': self.deployer.address,
                    'user': self.user.address
                },
                'contracts': deployments,
                'timestamp': self.w3.eth.get_block('latest')['timestamp']
            }
            
            with open(data_dir / 'deployments.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            print(f"  ✅ Deployment info saved to: {data_dir / 'deployments.json'}")
            
            # 6. Update .env file
            with open('.env', 'a') as f:
                f.write(f'\n# ERC-4337 Contract Addresses\n')
                f.write(f'ENTRY_POINT_ADDRESS={entrypoint_address}\n')
                f.write(f'SIMPLE_ACCOUNT_ADDRESS={account_address}\n')
            
            print(f"  ✅ Environment variables updated")
            
            return deployment_info
            
        except Exception as e:
            print(f"\n❌ Error during deployment: {e}")
            import traceback
            traceback.print_exc()
            return None
            

def main():
    print("🚀 Starting ERC-4337 smart contract deployment...")
    
    # Create deployer instance
    deployer = ERC4337Deployer()
    
    # Execute deployment
    result = deployer.deploy_all()
    
    if result:
        print("\n" + "=" * 60)
        print("✅ Deployment completed!")
        print("=" * 60)
        print(f"EntryPoint address: {result['contracts']['entryPoint']['address']}")
        print(f"SimpleAccount address: {result['contracts']['simpleAccount']['address']}")
        print(f"User address: {result['accounts']['user']}")
        print(f"\nDeployment details available at: data/deployments.json")
        print("\nNext steps: Run security tests or interact with contracts")

if __name__ == "__main__":
    main()