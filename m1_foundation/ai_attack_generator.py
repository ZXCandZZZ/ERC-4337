"""
AI-Driven Attack Generator for ERC-4337 Smart Wallet Testing
Member B: AI Attack Designer
Milestone 1: API Integration and Initial Prompt Design

This script demonstrates the integration with DeepSeek API
to generate malformed UserOperation data for fuzzing ERC-4337 smart wallets.
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
import requests


class AIAttackGenerator:
    """
    Core class for generating attack vectors using AI.
    Currently supports DeepSeek API (OpenAI-compatible).
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com"):
        """
        Initialize the AI attack generator with DeepSeek API.
        
        Args:
            api_key: DeepSeek API key (defaults to env var DEEPSEEK_API_KEY)
            base_url: DeepSeek API base URL
        """
        self.api_key = api_key or os.getenv("sk-85f96e1bfc48422fa3755f8b7721892d")
        
        if not self.api_key:
            raise ValueError(
                "API key not found. Set DEEPSEEK_API_KEY environment variable "
                "or pass it directly."
            )
        
        self.base_url = base_url
        self.model = "deepseek-chat"
    
    def get_system_prompt_v1(self) -> str:
        """
        System Prompt v1: Initial prompt design for generating malformed UserOperations.
        
        Design decisions:
        - Focus on ERC-4337 UserOperation structure
        - Emphasize boundary conditions and edge cases
        - Target common vulnerability patterns
        - Output format: strict JSON
        """
        return """You are an expert Ethereum security researcher specializing in ERC-4337 Account Abstraction vulnerabilities.

Your task is to generate malformed or malicious UserOperation objects that could potentially exploit vulnerabilities in smart wallet implementations.

A valid ERC-4337 UserOperation has the following structure:
{
  "sender": "0x... (address, 20 bytes)",
  "nonce": "uint256",
  "initCode": "0x... (bytes, optional)",
  "callData": "0x... (bytes)",
  "callGasLimit": "uint256",
  "verificationGasLimit": "uint256",
  "preVerificationGas": "uint256",
  "maxFeePerGas": "uint256",
  "maxPriorityFeePerGas": "uint256",
  "paymasterAndData": "0x... (bytes, optional)",
  "signature": "0x... (bytes)"
}

Generate UserOperations that test the following vulnerability categories:
1. **Integer overflow/underflow** in gas fields
2. **Invalid addresses** (zero address, non-existent contracts, EOAs)
3. **Malformed callData** (wrong function selectors, corrupted parameters)
4. **Signature forgery attempts** (empty, wrong length, invalid values)
5. **Nonce manipulation** (replay attacks, future nonces)
6. **Gas limit attacks** (extremely high/low values, inconsistent limits)

Output ONLY valid JSON containing a single UserOperation object. Do not include explanations or markdown formatting."""

    def _call_deepseek_api(self, system_prompt: str, user_message: str) -> str:
        """
        Call DeepSeek API using OpenAI-compatible interface.
        
        Args:
            system_prompt: System prompt for the model
            user_message: User message/query
            
        Returns:
            Model response text
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def generate_attack_userop(self, attack_type: Optional[str] = None) -> Dict:
        """
        Generate a single malformed UserOperation using AI.
        
        Args:
            attack_type: Optional specification of attack category
            
        Returns:
            Dictionary containing the generated UserOperation
        """
        system_prompt = self.get_system_prompt_v1()
        
        user_message = "Generate a malformed UserOperation that attempts an integer overflow in gas fields."
        if attack_type:
            user_message = f"Generate a malformed UserOperation that targets: {attack_type}"
        
        try:
            response_text = self._call_deepseek_api(system_prompt, user_message)
            
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```"):
                lines = cleaned_text.split('\n')
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or (not line.strip().startswith("```")):
                        json_lines.append(line)
                cleaned_text = '\n'.join(json_lines).strip()
            
            try:
                userop = json.loads(cleaned_text)
                return userop
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse JSON",
                    "raw_response": response_text,
                    "cleaned_attempt": cleaned_text,
                    "attack_type": attack_type or "integer_overflow_gas"
                }
        except Exception as e:
            return {
                "error": str(e),
                "attack_type": attack_type or "integer_overflow_gas"
            }
    
    def save_response(self, data: Dict, filename: str = "ai_response_v0.1.json"):
        """
        Save AI response to file for evidence documentation.
        
        Args:
            data: Response data to save
            filename: Output filename
        """
        output = {
            "timestamp": datetime.now().isoformat(),
            "provider": "deepseek",
            "model": self.model,
            "prompt_version": "v1",
            "response": data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Response saved to {filename}")
        return filename


def main():
    """
    Demonstration of AI API integration for Milestone 1 evidence.
    """
    print("=" * 60)
    print("AI Attack Generator - Milestone 1 Demo")
    print("Member B: AI Attack Designer")
    print("Provider: DeepSeek API")
    print("=" * 60)
    
    # Initialize generator
    print("\n[1] Initializing DeepSeek API client...")
    try:
        # Use hardcoded API key for demo
        api_key = "sk-85f96e1bfc48422fa3755f8b7721892d"
        generator = AIAttackGenerator(api_key=api_key)
        print("✓ DeepSeek API client initialized")
        print(f"✓ Model: {generator.model}")
    except ValueError as e:
        print(f"✗ Error: {e}")
        print("\nTo run this demo, set your API key:")
        print("  export DEEPSEEK_API_KEY='your-key-here'")
        return
    
    # Generate first attack
    print("\n[2] Generating first UserOperation attack...")
    print(f"Using System Prompt v1")
    
    userop = generator.generate_attack_userop()
    
    print("\n[3] Raw AI Response:")
    print(json.dumps(userop, indent=2, ensure_ascii=False))
    
    # Save for evidence
    print("\n[4] Saving response for evidence pack...")
    filename = generator.save_response(userop)
    
    print("\n" + "=" * 60)
    print("Milestone 1 Demo Complete!")
    print(f"Evidence file: {filename}")
    print("=" * 60)


if __name__ == "__main__":
    main()
