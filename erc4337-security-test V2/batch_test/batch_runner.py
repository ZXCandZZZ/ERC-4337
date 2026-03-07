import json
import time
from typing import Any, Dict, List, Optional

from eth_account import Account
from web3 import Web3, exceptions

from .ai_generator import AttackVector
from .config import (
    DEFAULT_CALL_GAS_LIMIT,
    DEFAULT_PRE_VERIFICATION_GAS,
    DEFAULT_SUBMIT_TX_GAS,
    DEFAULT_VERIFICATION_GAS_LIMIT,
    DEPLOYMENTS_PATH,
    RPC_URL,
)


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
        with open(DEPLOYMENTS_PATH, "r", encoding="utf-8") as f:
            self.deployments = json.load(f)

    def _init_contracts(self):
        self.entrypoint = self.w3.eth.contract(
            address=self.deployments["contracts"]["entryPoint"]["address"],
            abi=self.deployments["contracts"]["entryPoint"]["abi"],
        )
        self.account = self.w3.eth.contract(
            address=self.deployments["contracts"]["simpleAccount"]["address"],
            abi=self.deployments["contracts"]["simpleAccount"]["abi"],
        )

    def _init_accounts(self):
        # Hardhat default keys
        self.deployer = Account.from_key(
            "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        )
        self.attacker = Account.from_key(
            "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
        )
        self.user = Account.from_key(
            "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"
        )

    @staticmethod
    def _pack_uint128_pair(lower_128: int, upper_128: int) -> bytes:
        lower_128 = lower_128 & ((1 << 128) - 1)
        upper_128 = upper_128 & ((1 << 128) - 1)
        packed = (upper_128 << 128) | lower_128
        return packed.to_bytes(32, "big")

    def _get_nonce(self, sender: str, key: int = 0) -> int:
        return int(self.entrypoint.functions.getNonce(sender, key).call())

    def _build_call_data(self, attack: AttackVector) -> bytes:
        if attack.call_data is not None:
            return attack.call_data
        return self.account.functions.execute(
            self.attacker.address,
            0,
            b"",
        )._encode_transaction_data()

    def _construct_user_op(self, attack: AttackVector):
        current_nonce = self._get_nonce(self.account.address, 0)
        nonce = max(0, current_nonce + int(attack.nonce_offset))

        gas_price = self.w3.eth.gas_price
        verification_gas = int(DEFAULT_VERIFICATION_GAS_LIMIT * attack.verification_gas_limit_factor)
        call_gas = int(DEFAULT_CALL_GAS_LIMIT * attack.call_gas_limit_factor)

        account_gas_limits = self._pack_uint128_pair(verification_gas, call_gas)
        gas_fees = self._pack_uint128_pair(gas_price, gas_price)

        signature = attack.signature if attack.signature is not None else b""
        call_data = self._build_call_data(attack)

        # V2 PackedUserOperation layout
        return (
            self.account.address,  # sender
            nonce,  # nonce
            b"",  # initCode
            call_data,  # callData
            account_gas_limits,  # bytes32 accountGasLimits
            DEFAULT_PRE_VERIFICATION_GAS,  # preVerificationGas
            gas_fees,  # bytes32 gasFees
            b"",  # paymasterAndData
            signature,  # signature
        )

    @staticmethod
    def _extract_exception_info(e: Exception) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "exception_type": type(e).__name__,
            "message": str(e),
            "args": list(e.args) if hasattr(e, "args") else [],
            "code": None,
            "data": None,
            "raw": None,
        }

        first_arg = e.args[0] if hasattr(e, "args") and len(e.args) > 0 else None
        if isinstance(first_arg, dict):
            payload["raw"] = first_arg
            payload["code"] = first_arg.get("code")
            payload["data"] = first_arg.get("data")
            if "message" in first_arg and isinstance(first_arg["message"], str):
                payload["message"] = first_arg["message"]
        elif isinstance(first_arg, str):
            payload["raw"] = first_arg
            # web3 sometimes stores dict-like payload as a string
            if "'code': -32603" in first_arg or '"code": -32603' in first_arg:
                payload["code"] = -32603

        return payload

    @staticmethod
    def _is_revert_like_exception(exc_info: Dict[str, Any]) -> bool:
        code = exc_info.get("code")
        message = str(exc_info.get("message") or "").lower()
        data_text = str(exc_info.get("data") or "").lower()
        raw_text = str(exc_info.get("raw") or "").lower()

        text_blob = " | ".join([message, data_text, raw_text])
        has_revert_signal = any(
            key in text_blob
            for key in [
                "revert",
                "reverted",
                "vm exception",
                "execution reverted",
                "aa23",
                "failedop",
                "custom error",
            ]
        )

        return bool(has_revert_signal or code == -32603)

    def _run_single(self, attack: AttackVector) -> Dict[str, Any]:
        tx_hash_hex: Optional[str] = None

        try:
            op = self._construct_user_op(attack)
            tx_hash = self.entrypoint.functions.handleOps(
                [op],
                self.attacker.address,
            ).transact(
                {
                    "from": self.deployer.address,
                    "gas": DEFAULT_SUBMIT_TX_GAS,
                }
            )
            tx_hash_hex = tx_hash.hex()
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            blocked = receipt.status == 0
            status = "BLOCKED" if blocked else "VULNERABLE"
            expected = "BLOCKED" if attack.should_be_blocked else "ALLOWED"
            verdict = "PASS" if ((blocked and attack.should_be_blocked) or (not blocked and not attack.should_be_blocked)) else "FAIL"

            return {
                "name": attack.name,
                "type": attack.attack_type,
                "description": attack.description,
                "expected": expected,
                "status": status,
                "verdict": verdict,
                "tx_hash": tx_hash_hex,
                "error": None if not blocked else "Transaction reverted with status=0",
            }

        except exceptions.ContractLogicError as e:
            # ContractLogicError is an explicit on-chain rejection.
            blocked = True
            status = "BLOCKED"
            expected = "BLOCKED" if attack.should_be_blocked else "ALLOWED"
            verdict = "PASS" if attack.should_be_blocked else "FAIL"
            return {
                "name": attack.name,
                "type": attack.attack_type,
                "description": attack.description,
                "expected": expected,
                "status": status,
                "verdict": verdict,
                "tx_hash": tx_hash_hex,
                "error": str(e),
            }
        except Exception as e:
            exc_info = self._extract_exception_info(e)
            expected = "BLOCKED" if attack.should_be_blocked else "ALLOWED"

            # Revert-like RPC errors (e.g. Web3RPCError code=-32603) mean on-chain rejection,
            # so classify as BLOCKED, not framework ERROR.
            if self._is_revert_like_exception(exc_info):
                verdict = "PASS" if attack.should_be_blocked else "FAIL"
                return {
                    "name": attack.name,
                    "type": attack.attack_type,
                    "description": attack.description,
                    "expected": expected,
                    "status": "BLOCKED",
                    "verdict": verdict,
                    "tx_hash": tx_hash_hex,
                    "error": str(e),
                }

            # Non-revert exceptions are true runner/runtime errors.
            return {
                "name": attack.name,
                "type": attack.attack_type,
                "description": attack.description,
                "expected": expected,
                "status": "ERROR",
                "verdict": "FAIL",
                "tx_hash": tx_hash_hex,
                "error": str(e),
            }

    def execute_batch(self, attacks: List[AttackVector]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        print(f"🚀 Starting V2 batch execution of {len(attacks)} attacks...")

        for i, attack in enumerate(attacks, start=1):
            print(f"[{i}/{len(attacks)}] {attack.name} - {attack.description}")
            result = self._run_single(attack)
            results.append(result)
            time.sleep(0.08)

        return results
