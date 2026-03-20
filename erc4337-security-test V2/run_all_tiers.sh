#!/bin/bash
# =============================================================================
# Three-Tier Testing Script for ERC-4337 Security Testing Framework
# Owner: Role C (Test Execution & Data Analyst)
# M3 Deliverable: Run 100/500/1000+ operation tests
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="${SCRIPT_DIR}/logs"
OUTPUT_DIR="${SCRIPT_DIR}/analysis_outputs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "${LOGS_DIR}"
mkdir -p "${OUTPUT_DIR}"

SEED=${SEED:-42}
API_KEY=${DEEPSEEK_API_KEY:-""}

if [ -z "$API_KEY" ]; then
    echo "Error: DEEPSEEK_API_KEY environment variable not set"
    exit 1
fi

echo "========================================"
echo "ERC-4337 Three-Tier Testing"
echo "========================================"
echo "Timestamp: ${TIMESTAMP}"
echo "Random Seed: ${SEED}"
echo "Logs Directory: ${LOGS_DIR}"
echo "========================================"
echo ""

run_tier() {
    local tier=$1
    local count=$2
    local log_file="${LOGS_DIR}/tier_${tier}_${TIMESTAMP}.log"
    
    echo "----------------------------------------"
    echo "Running Tier ${tier} (${count} operations)"
    echo "Log file: ${log_file}"
    echo "Started at: $(date)"
    echo "----------------------------------------"
    
    python3 "${SCRIPT_DIR}/ai-attack-generator/attack_generator.py" \
        --mode batch \
        --count ${count} \
        --output "${OUTPUT_DIR}/attacks_tier_${tier}.json" \
        2>&1 | tee "${log_file}"
    
    echo "Tier ${tier} completed at: $(date)"
    echo ""
}

compute_metrics() {
    local input_file=$1
    local output_csv="${OUTPUT_DIR}/metrics_summary_${TIMESTAMP}.csv"
    
    echo "Computing metrics..."
    
    python3 -c "
import json
import csv
from datetime import datetime
from pathlib import Path

input_file = '${input_file}'
output_csv = '${output_csv}'

with open(input_file) as f:
    data = json.load(f)

attacks = data.get('attacks', [])
total = len(attacks)

blocked = sum(1 for a in attacks if a.get('should_be_blocked', True))
passed = total - blocked

legit = [a for a in attacks if a.get('attack_type') == 'legitimate']
total_legit = len(legit)
blocked_legit = sum(1 for a in legit if a.get('blocked', False))
passed_legit = total_legit - blocked_legit if total_legit > 0 else 0

tp = blocked
tn = passed_legit
fp = blocked_legit
fn = passed - passed_legit

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

metrics = [
    ('timestamp', datetime.now().isoformat()),
    ('total_tests', total),
    ('total_attacks', total - total_legit),
    ('total_legitimate', total_legit),
    ('true_positive', tp),
    ('false_negative', fn),
    ('true_negative', tn),
    ('false_positive', fp),
    ('tp_rate', round(tp / total if total > 0 else 0, 4)),
    ('fn_rate', round(fn / total if total > 0 else 0, 4)),
    ('fp_rate', round(fp / total_legit if total_legit > 0 else 0, 4)),
    ('precision', round(precision, 4)),
    ('recall', round(recall, 4)),
    ('f1_score', round(f1, 4)),
]

with open(output_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['metric', 'value'])
    writer.writerows(metrics)

print(f'Metrics saved to {output_csv}')
for m, v in metrics:
    print(f'  {m}: {v}')
"
}

echo "Starting Three-Tier Test Execution"
echo ""

# Tier 1: Smoke Test (100 operations)
run_tier "100" 100

# Tier 2: Medium Test (500 operations)
run_tier "500" 500

# Tier 3: Large Test (1000 operations)
run_tier "1000" 1000

# Compute metrics for the largest test
echo "========================================"
echo "Computing Final Metrics"
echo "========================================"
compute_metrics "${OUTPUT_DIR}/attacks_tier_1000.json"

echo ""
echo "========================================"
echo "Three-Tier Testing Complete!"
echo "========================================"
echo "Logs saved to: ${LOGS_DIR}"
echo "Metrics saved to: ${OUTPUT_DIR}"
echo "========================================"