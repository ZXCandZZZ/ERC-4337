import random
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

@dataclass
class AttackVector:
    """
    Standardized data structure for an attack vector.
    This schema is designed to be compatible with AI-generated JSON outputs.
    """
    name: str
    description: str
    attack_type: str  # e.g., 'signature_forgery', 'replay', 'gas_exhaustion'
    
    # --- Parameters to override in UserOperation ---
    # If None, the default valid value will be used.
    
    # Malicious signature payload (bytes)
    signature: Optional[bytes] = None
    
    # Offset from the current valid nonce. 
    # 0 = valid nonce, -1 = replay attack (previous nonce), 1 = future nonce (gap)
    nonce_offset: int = 0
    
    # Multipliers for gas limits to simulate exhaustion or griefing attacks
    call_gas_limit_factor: float = 1.0
    verification_gas_limit_factor: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# ==============================================================================
# [TODO] AI Integration Guide for Future Developers
# ==============================================================================
# This SYSTEM_PROMPT is designed for LLMs (e.g., DeepSeek, GPT-4).
# To implement the real AI generator:
# 1. Create a new class `AIGenerator` that inherits from a base generator interface.
# 2. Use an API client (openai/anthropic) to send this prompt + current contract ABI.
# 3. Parse the JSON response into a list of `AttackVector` objects.
# ==============================================================================
SYSTEM_PROMPT = """
You are a smart contract security auditor specializing in ERC-4337.
Your task is to generate malicious UserOperation parameters to test the robustness of a SimpleAccount wallet.
Focus on the following vulnerabilities:
1. Signature Forgery (e.g., zero signature, short signature, invalid v/r/s)
2. Replay Attacks (reusing nonces)
3. Gas Exhaustion (manipulating gas limits)
4. Malformed Calldata

Output format: JSON list of attack vectors matching the AttackVector schema.
"""

class MockGenerator:
    """
    [Fuzzing Module]
    Generates deterministic fuzzing data to simulate AI-generated attacks.
    
    Use this class to:
    1. Test the batch execution framework without consuming API credits.
    2. Establish a baseline for vulnerability detection (known bad inputs).
    3. Verify that the reporting and visualization pipeline works correctly.
    """
    
    def generate_batch(self, count: int = 10) -> List[AttackVector]:
        """
        Generates a batch of random attack vectors.
        
        Args:
            count: Number of attack vectors to generate.
            
        Returns:
            List[AttackVector]: A list of malicious inputs ready for execution.
        """
        attacks = []
        for i in range(count):
            # Weighted random choice to focus on signature attacks (most critical for M1)
            attack_type = random.choices(
                ['signature_forgery', 'replay', 'gas_exhaustion'],
                weights=[0.6, 0.2, 0.2],
                k=1
            )[0]
            
            if attack_type == 'signature_forgery':
                attacks.append(self._generate_signature_attack(i))
            elif attack_type == 'replay':
                attacks.append(self._generate_replay_attack(i))
            elif attack_type == 'gas_exhaustion':
                attacks.append(self._generate_gas_attack(i))
                
        return attacks

    def _generate_signature_attack(self, index: int) -> AttackVector:
        subtype = random.choice(['zero', 'short', 'empty', 'invalid_v'])
        
        if subtype == 'zero':
            sig = b'\x00' * 65
            desc = "All-zero signature (65 bytes) - Testing ecrecover(0) vulnerability"
        elif subtype == 'short':
            length = random.randint(1, 64)
            sig = b'\x01' * length
            desc = f"Short signature ({length} bytes) - Testing length validation"
        elif subtype == 'empty':
            sig = b''
            desc = "Empty signature (0 bytes) - Testing missing check"
        else: # invalid_v
            # Construct a signature with invalid v (not 27 or 28)
            # Standard signature is 65 bytes: r(32) + s(32) + v(1)
            sig = b'\x01' * 64 + bytes([random.choice([0, 1, 26, 29, 255])])
            desc = "Signature with invalid v value - Testing ECDSA recovery logic"
            
        return AttackVector(
            name=f"SigAttack_{index}_{subtype}",
            description=desc,
            attack_type="signature_forgery",
            signature=sig
        )

    def _generate_replay_attack(self, index: int) -> AttackVector:
        return AttackVector(
            name=f"ReplayAttack_{index}",
            description="Attempting to use an already used nonce (current - 1)",
            attack_type="replay",
            nonce_offset=-1 
        )

    def _generate_gas_attack(self, index: int) -> AttackVector:
        factor = random.choice([0.1, 0.5, 2.0, 10.0])
        return AttackVector(
            name=f"GasAttack_{index}",
            description=f"Modified gas limits by factor {factor}",
            attack_type="gas_exhaustion",
            call_gas_limit_factor=factor,
            verification_gas_limit_factor=factor
        )
