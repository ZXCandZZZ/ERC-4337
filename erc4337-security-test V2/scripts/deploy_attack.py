import json
from pathlib import Path
from web3 import Web3
from eth_account import Account
from solcx import compile_files, set_solc_version, install_solc

# ========== Configuration ==========
RPC_URL = "http://127.0.0.1:8545"
DEPLOYMENTS_FILE = "data/deployments.json"
ATTACKER_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

# ========== Initialization ==========
w3 = Web3(Web3.HTTPProvider(RPC_URL))
assert w3.is_connected(), "Unable to connect to Hardhat node"

install_solc('0.8.28')
set_solc_version('0.8.28')

with open(DEPLOYMENTS_FILE) as f:
    deployments = json.load(f)
entrypoint_addr = deployments['contracts']['entryPoint']['address']

attacker_acct = Account.from_key(ATTACKER_PRIVATE_KEY)

print("=" * 60)
print("Deploying Attack Contract")
print("=" * 60)
print(f"Attacker address: {attacker_acct.address}")
print(f"EntryPoint address: {entrypoint_addr}")

# Compile Attack.sol
compiled = compile_files(
    ['contracts/accounts/Attack.sol'],
    solc_version='0.8.28',
    output_values=['abi', 'bin'],
    import_remappings=['@openzeppelin/=node_modules/@openzeppelin/'],
    allow_paths=['.', './contracts', './node_modules']
)

# Find Attack contract
attack_contract_key = next(key for key in compiled if 'Attack' in key)
abi = compiled[attack_contract_key]['abi']
bytecode = compiled[attack_contract_key]['bin']

Attack = w3.eth.contract(abi=abi, bytecode=bytecode)

# Deploy
nonce = w3.eth.get_transaction_count(attacker_acct.address)
tx = Attack.constructor(entrypoint_addr).build_transaction({
    'from': attacker_acct.address,
    'nonce': nonce,
    'gas': 3_000_000,
    'gasPrice': w3.eth.gas_price,
    'chainId': w3.eth.chain_id
})
signed = attacker_acct.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

attack_addr = receipt.contractAddress
print(f"Attack contract deployed successfully! Address: {attack_addr}")

# Deposit ETH into attack contract (to cover prefund)
deposit_amount = w3.to_wei(0.1, 'ether')
tx = {
    'from': attacker_acct.address,
    'to': attack_addr,
    'value': deposit_amount,
    'gas': 100_000,
    'gasPrice': w3.eth.gas_price,
    'nonce': w3.eth.get_transaction_count(attacker_acct.address),
    'chainId': w3.eth.chain_id
}
signed = attacker_acct.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Deposited {w3.from_wei(deposit_amount, 'ether')} ETH to attack contract")

# Save attack contract info
attack_info = {
    'address': attack_addr,
    'abi': abi,
    'deployedBy': attacker_acct.address
}
Path('data').mkdir(exist_ok=True)
with open('data/attack.json', 'w') as f:
    json.dump(attack_info, f, indent=2)
print("Attack contract info saved to data/attack.json")