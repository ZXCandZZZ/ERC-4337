import random
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class AttackVector:
    """Standardized attack vector for V2 PackedUserOperation tests."""

    name: str
    description: str
    attack_type: str

    # Explicit signature bytes. If None, runner may build a fallback signature.
    signature: Optional[bytes] = None

    # Nonce delta relative to current getNonce(sender, 0)
    nonce_offset: int = 0

    # Gas multipliers to stress account/pipeline behavior
    call_gas_limit_factor: float = 1.0
    verification_gas_limit_factor: float = 1.0

    # Optional override callData; if None runner builds account.execute(attacker,0,"")
    call_data: Optional[bytes] = None

    # Security expectation for this vector
    should_be_blocked: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FixedCaseGenerator:
    """Deterministic and reproducible baseline cases (fixed priority)."""

    def generate_batch(self) -> List[AttackVector]:
        return [
            AttackVector(
                name="SIG_ZERO_65",
                description="All-zero 65-byte signature should be rejected",
                attack_type="signature_forgery",
                signature=b"\x00" * 65,
                should_be_blocked=True,
            ),
            AttackVector(
                name="SIG_EMPTY",
                description="Empty signature should be rejected",
                attack_type="signature_forgery",
                signature=b"",
                should_be_blocked=True,
            ),
            AttackVector(
                name="SIG_SHORT_64",
                description="64-byte non-EIP2098 raw signature payload should be rejected",
                attack_type="signature_forgery",
                signature=b"\x01" * 64,
                should_be_blocked=True,
            ),
            AttackVector(
                name="SIG_LONG_66",
                description="66-byte malformed signature should be rejected",
                attack_type="signature_forgery",
                signature=b"\x01" * 66,
                should_be_blocked=True,
            ),
            AttackVector(
                name="SIG_INVALID_V_0",
                description="65-byte signature with invalid v=0 should be rejected",
                attack_type="signature_forgery",
                signature=(b"\x11" * 64) + bytes([0]),
                should_be_blocked=True,
            ),
            AttackVector(
                name="SIG_INVALID_V_1",
                description="65-byte signature with invalid v=1 should be rejected",
                attack_type="signature_forgery",
                signature=(b"\x22" * 64) + bytes([1]),
                should_be_blocked=True,
            ),
            AttackVector(
                name="SIG_INVALID_V_29",
                description="65-byte signature with invalid v=29 should be rejected",
                attack_type="signature_forgery",
                signature=(b"\x33" * 64) + bytes([29]),
                should_be_blocked=True,
            ),
            AttackVector(
                name="SIG_INVALID_V_255",
                description="65-byte signature with invalid v=255 should be rejected",
                attack_type="signature_forgery",
                signature=(b"\x44" * 64) + bytes([255]),
                should_be_blocked=True,
            ),
            AttackVector(
                name="REPLAY_PREV_NONCE",
                description="Replay-style nonce offset -1 should be blocked",
                attack_type="replay",
                nonce_offset=-1,
                signature=b"\x00" * 65,
                should_be_blocked=True,
            ),
            AttackVector(
                name="GAS_OVERSTRETCH_10X",
                description="Excessive gas factor with invalid signature should still be blocked",
                attack_type="gas_exhaustion",
                signature=b"\x00" * 65,
                call_gas_limit_factor=10.0,
                verification_gas_limit_factor=10.0,
                should_be_blocked=True,
            ),
        ]


class MockGenerator:
    """Small random extension cases (used after fixed cases)."""

    def generate_batch(self, count: int = 10) -> List[AttackVector]:
        attacks: List[AttackVector] = []
        for i in range(max(0, count)):
            attack_type = random.choices(
                ["signature_forgery", "replay", "gas_exhaustion"],
                weights=[0.7, 0.2, 0.1],
                k=1,
            )[0]

            if attack_type == "signature_forgery":
                attacks.append(self._generate_signature_attack(i))
            elif attack_type == "replay":
                attacks.append(self._generate_replay_attack(i))
            else:
                attacks.append(self._generate_gas_attack(i))

        return attacks

    def _generate_signature_attack(self, index: int) -> AttackVector:
        subtype = random.choice(["zero", "short", "empty", "invalid_v"])

        if subtype == "zero":
            sig = b"\x00" * 65
            desc = "Random: all-zero signature"
        elif subtype == "short":
            length = random.randint(1, 64)
            sig = b"\x01" * length
            desc = f"Random: short signature {length} bytes"
        elif subtype == "empty":
            sig = b""
            desc = "Random: empty signature"
        else:
            sig = b"\xaa" * 64 + bytes([random.choice([0, 1, 26, 29, 255])])
            desc = "Random: invalid-v signature"

        return AttackVector(
            name=f"R_SIG_{index}_{subtype}",
            description=desc,
            attack_type="signature_forgery",
            signature=sig,
            should_be_blocked=True,
        )

    def _generate_replay_attack(self, index: int) -> AttackVector:
        return AttackVector(
            name=f"R_REPLAY_{index}",
            description="Random: nonce offset -1 replay-style attempt",
            attack_type="replay",
            nonce_offset=-1,
            signature=b"\x00" * 65,
            should_be_blocked=True,
        )

    def _generate_gas_attack(self, index: int) -> AttackVector:
        factor = random.choice([0.1, 0.5, 2.0, 5.0, 10.0])
        return AttackVector(
            name=f"R_GAS_{index}_{factor}",
            description=f"Random: gas factor {factor}",
            attack_type="gas_exhaustion",
            signature=b"\x00" * 65,
            call_gas_limit_factor=factor,
            verification_gas_limit_factor=factor,
            should_be_blocked=True,
        )
