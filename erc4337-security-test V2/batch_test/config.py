from pathlib import Path

# Base directory: .../erc4337-security-test V2/batch_test
BASE_DIR = Path(__file__).resolve().parent

# Test root directory: .../erc4337-security-test V2
TEST_ROOT = BASE_DIR.parent

# Shared deployment output from deploy script
DEPLOYMENTS_PATH = TEST_ROOT / "data" / "deployments.json"

# Reports output directory
REPORTS_DIR = TEST_ROOT / "data" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Hardhat local RPC
RPC_URL = "http://127.0.0.1:8545"

# Default gas knobs for PackedUserOperation (V2)
DEFAULT_VERIFICATION_GAS_LIMIT = 200_000
DEFAULT_CALL_GAS_LIMIT = 300_000
DEFAULT_PRE_VERIFICATION_GAS = 50_000
DEFAULT_SUBMIT_TX_GAS = 1_500_000
