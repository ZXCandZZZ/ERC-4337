# ERC-4337 AI Fuzzing Attack Generator

AI-driven fuzzing framework for ERC-4337 smart wallet security testing. Uses DeepSeek API to generate malformed UserOperation attacks.

## Setup

```bash
pip install -r requirements.txt
```

Set your DeepSeek API key:

```bash
export DEEPSEEK_API_KEY=your_api_key_here
```

---

## attack_generator.py

Generates malformed ERC-4337 UserOperations to test smart wallet vulnerabilities.

### Modes

#### Single — generate one attack (quick test)

```bash
python attack_generator.py --mode single
```

Target a specific attack category:

```bash
python attack_generator.py --mode single --attack-type nonce_manipulation
```

Available attack types:
- `integer_overflow_gas`
- `invalid_address`
- `malformed_calldata`
- `signature_forgery`
- `nonce_manipulation`
- `gas_limit_attack`

#### Batch — generate 50+ attacks in parallel

```bash
python attack_generator.py --mode batch --count 50 --output attacks.json
```

#### Validate — check an existing dataset against ERC-4337 schema

```bash
python attack_generator.py --mode validate --input attacks.json
```

Add `--no-strict` to allow unknown fields:

```bash
python attack_generator.py --mode validate --input attacks.json --no-strict
```

### All Options

| Flag | Default | Description |
|---|---|---|
| `--mode` | `single` | `single` / `batch` / `validate` |
| `--api-key` | env var | DeepSeek API key |
| `--attack-type` | — | Attack category (single mode) |
| `--count` | `50` | Number of attacks (batch mode) |
| `--output` | `attacks_dataset.json` | Output file |
| `--input` | — | Input file (validate mode) |
| `--no-strict` | off | Allow unknown fields in validation |

---

## analyze_results.py

Analyzes a generated dataset and produces charts and a markdown report.

```bash
python analyze_results.py --input attacks.json --output-dir ./analysis_outputs
```

Outputs (saved to `--output-dir`):
- `attack_distribution_pie.png` — attack type breakdown
- `success_failure_bar.png` — success vs failure counts
- `analysis_summary_report.md` — full markdown report

### All Options

| Flag | Default | Description |
|---|---|---|
| `--input` | `attacks_dataset_50plus.json` | Dataset JSON file |
| `--output-dir` | `./analysis_outputs` | Directory for outputs |

---

## Typical Workflow

```bash
# 1. Generate a batch of attacks
python attack_generator.py --mode batch --count 50 --output attacks.json

# 2. Validate the dataset
python attack_generator.py --mode validate --input attacks.json

# 3. Analyze and visualize results
python analyze_results.py --input attacks.json --output-dir ./analysis_outputs
```
