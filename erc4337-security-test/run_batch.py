import argparse
import sys
from pathlib import Path

# Add project root to python path to allow imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from batch_test.ai_generator import MockGenerator
from batch_test.batch_runner import BatchRunner
from batch_test.visualizer import Visualizer

def main():
    """
    Main entry point for the AI-Driven Batch Security Test Framework.
    
    Usage:
        python run_batch.py --count 50
        
    This script orchestrates the entire testing pipeline:
    1. Generates attack vectors (using MockGenerator or future AI integration).
    2. Executes attacks against the local Hardhat node.
    3. Analyzes results and generates visualization reports.
    """
    parser = argparse.ArgumentParser(description='ERC-4337 AI-Driven Batch Security Test')
    parser.add_argument('--count', type=int, default=50, help='Number of attack vectors to generate')
    parser.add_argument('--mock', action='store_true', default=True, help='Use mock generator (fuzzing) instead of real AI API')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🤖 ERC-4337 AI-Driven Batch Security Test Framework")
    print("="*60)
    
    try:
        # 1. Generate Attacks
        print(f"\n[Phase 1] Generating {args.count} attack vectors...")
        if args.mock:
            generator = MockGenerator()
            attacks = generator.generate_batch(args.count)
        else:
            # [TODO] Future Integration Point:
            # Instantiate AIGenerator here when API keys are available.
            # e.g., generator = AIGenerator(api_key=...)
            print("Real AI integration not yet configured. Falling back to mock.")
            generator = MockGenerator()
            attacks = generator.generate_batch(args.count)
            
        print(f"✅ Generated {len(attacks)} vectors.")
        
        # 2. Execute Attacks
        print(f"\n[Phase 2] Executing attacks against local node...")
        runner = BatchRunner()
        results = runner.execute_batch(attacks)
        
        # 3. Visualize Results
        print(f"\n[Phase 3] Analyzing and visualizing results...")
        viz = Visualizer(results)
        viz.generate_report()
        
        # Summary
        vuln_count = sum(1 for r in results if r['status'] == 'VULNERABLE')
        print("\n" + "="*60)
        print(f"🏁 Test Complete. Found {vuln_count} potential vulnerabilities.")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
