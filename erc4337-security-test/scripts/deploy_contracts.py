import json
import os
from solcx import compile_source, set_solc_version
from web3 import Web3
from eth_account import Account
from pathlib import Path

# 设置Solidity版本（必须与合约中的版本匹配）
set_solc_version('0.8.19')

class ERC4337Deployer:
    def __init__(self, rpc_url="http://127.0.0.1:8545"):
        # 连接到本地Hardhat节点
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise Exception("❌ 无法连接到本地节点。请确保已运行 'npx hardhat node'")
        
        # 使用Hardhat提供的第一个测试账户作为部署者
        self.deployer = Account.from_key(
            '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'
        )
        
        # 第二个账户作为普通用户
        self.user = Account.from_key(
            '0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d'
        )
        
        print("=" * 60)
        print("ERC-4337 合约部署器")
        print("=" * 60)
        print(f"网络: {'已连接' if self.w3.is_connected() else '未连接'}")
        print(f"链ID: {self.w3.eth.chain_id}")
        print(f"部署者: {self.deployer.address}")
        print(f"用户: {self.user.address}")
        print(f"当前区块: {self.w3.eth.block_number}")
        
    def compile_contract(self, contract_name):
        """编译Solidity合约文件"""
        contract_path = Path(f"contracts/{contract_name}.sol")
        if not contract_path.exists():
            raise FileNotFoundError(f"找不到合约文件: {contract_path}")
        
        with open(contract_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        print(f"\n编译合约: {contract_name}")
        compiled = compile_source(source_code, solc_version='0.8.19')
        contract_id, contract_interface = compiled.popitem()
        
        return contract_interface['abi'], contract_interface['bin']
    
    def deploy_contract(self, contract_name, abi, bytecode, args=(), value=0):
        """部署合约到区块链"""
        print(f"部署合约: {contract_name}")
        
        # 创建合约对象
        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        
        # 构建部署交易
        transaction = contract.constructor(*args).build_transaction({
            'from': self.deployer.address,
            'nonce': self.w3.eth.get_transaction_count(self.deployer.address),
            'gas': 4000000,
            'gasPrice': self.w3.eth.gas_price,
            'value': value,
            'chainId': 31337  # Hardhat本地网络链ID
        })
        
        # 签名并发送交易
        signed_txn = self.deployer.sign_transaction(transaction)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # 等待部署完成
        print(f"  交易哈希: {tx_hash.hex()}")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            contract_address = receipt.contractAddress
            print(f"  ✅ 部署成功!")
            print(f"     地址: {contract_address}")
            print(f"     Gas消耗: {receipt.gasUsed}")
            
            # 返回合约实例
            return self.w3.eth.contract(address=contract_address, abi=abi), contract_address
        else:
            raise Exception(f"部署失败，交易哈希: {tx_hash.hex()}")
    
    def deploy_all(self):
        """部署所有ERC-4337核心合约"""
        deployments = {}
        
        try:
            # 1. 部署EntryPoint合约
            print("\n" + "=" * 60)
            print("1. 部署 SimpleEntryPoint 合约")
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
            
            # 2. 部署SimpleAccount合约
            print("\n" + "=" * 60)
            print("2. 部署 SimpleAccount 合约")
            print("=" * 60)
            
            account_abi, account_bytecode = self.compile_contract("SimpleAccount")
            account_contract, account_address = self.deploy_contract(
                "SimpleAccount",
                account_abi,
                account_bytecode,
                args=(self.user.address, entrypoint_address)  # 设置所有者和EntryPoint地址
            )
            
            deployments['simpleAccount'] = {
                'address': account_address,
                'abi': account_abi
            }
            
            # 3. 给智能合约钱包转账测试ETH
            print("\n" + "=" * 60)
            print("3. 向智能合约钱包转账测试ETH")
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
                print(f"  ✅ 转账成功!")
                print(f"     合约钱包余额: {self.w3.from_wei(balance, 'ether')} ETH")
                print(f"     交易哈希: {transfer_hash.hex()}")
            else:
                print("  ⚠️  转账失败，但合约部署成功")
            
            # 4. 验证合约功能
            print("\n" + "=" * 60)
            print("4. 验证合约功能")
            print("=" * 60)
            
            # 验证SimpleAccount的所有者
            actual_owner = account_contract.functions.owner().call()
            print(f"  合约钱包所有者: {actual_owner}")
            print(f"  预期所有者: {self.user.address}")
            print(f"  ✅ 所有者验证: {'通过' if actual_owner == self.user.address else '失败'}")
            
            # 验证EntryPoint链接
            actual_entrypoint = account_contract.functions.entryPoint().call()
            print(f"  链接的EntryPoint: {actual_entrypoint}")
            print(f"  实际EntryPoint: {entrypoint_address}")
            print(f"  ✅ EntryPoint链接验证: {'通过' if actual_entrypoint == entrypoint_address else '失败'}")
            
            # 5. 保存部署信息
            print("\n" + "=" * 60)
            print("5. 保存部署信息")
            print("=" * 60)
            
            # 确保data目录存在
            data_dir = Path('data')
            data_dir.mkdir(exist_ok=True)
            
            # 保存部署信息到JSON文件
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
            
            print(f"  ✅ 部署信息已保存到: {data_dir / 'deployments.json'}")
            
            # 6. 更新.env文件
            with open('.env', 'a') as f:
                f.write(f'\n# ERC-4337合约地址\n')
                f.write(f'ENTRY_POINT_ADDRESS={entrypoint_address}\n')
                f.write(f'SIMPLE_ACCOUNT_ADDRESS={account_address}\n')
            
            print(f"  ✅ 环境变量已更新")
            
            return deployment_info
            
        except Exception as e:
            print(f"\n❌ 部署过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
            return None
            

def main():
    print("🚀 开始部署ERC-4337智能合约...")
    
    # 创建部署器实例
    deployer = ERC4337Deployer()
    
    # 执行部署
    result = deployer.deploy_all()
    
    if result:
        print("\n" + "=" * 60)
        print("✅ 部署完成!")
        print("=" * 60)
        print(f"EntryPoint地址: {result['contracts']['entryPoint']['address']}")
        print(f"SimpleAccount地址: {result['contracts']['simpleAccount']['address']}")
        print(f"用户地址: {result['accounts']['user']}")
        print(f"\n部署详情请查看: data/deployments.json")
        print("\n下一步：运行安全测试或与合约交互")

if __name__ == "__main__":
    main()