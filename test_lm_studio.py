#!/usr/bin/env python3
"""
Test script for LM Studio connection
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_lm_studio_direct():
    """Test LM Studio connection directly with OpenAI library"""
    try:
        from openai import OpenAI
    except ImportError:
        print("OpenAI library not installed. Run: pip install openai")
        return
    
    print("Testing LM Studio connection with OpenAI library...")
    print("-" * 50)
    
    # LM Studio default configuration
    client = OpenAI(
        api_key="lm-studio",  # LM Studio doesn't need a real API key
        base_url="http://localhost:1234/v1"
    )
    
    try:
        # Test 1: List models
        print("\n1. Testing /v1/models endpoint:")
        models = client.models.list()
        print(f"   Available models: {[m.id for m in models.data]}")
        
        # Test 2: Chat completion
        print("\n2. Testing chat completion:")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello LM Studio' in 5 words or less."}
        ]
        
        # Get the first available model or use a default
        model_id = models.data[0].id if models.data else "local-model"
        print(f"   Using model: {model_id}")
        
        # Non-streaming test
        print("\n   Non-streaming response:")
        response = client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0.7,
            max_tokens=50
        )
        print(f"   Response: {response.choices[0].message.content}")
        
        # Streaming test
        print("\n   Streaming response:")
        stream = client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0.7,
            max_tokens=50,
            stream=True
        )
        
        print("   Response: ", end="")
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print()
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "-" * 50)

def test_with_provider():
    """Test using our OllamaProvider"""
    from thonnycontrib.thonny_codemate.external_providers import OllamaProvider
    
    print("\n\nTesting with OllamaProvider...")
    print("-" * 50)
    
    try:
        # Get available models first
        from openai import OpenAI
        client = OpenAI(api_key="lm-studio", base_url="http://localhost:1234/v1")
        models = client.models.list()
        model_id = models.data[0].id if models.data else "local-model"
        print(f"Using model: {model_id}")
        
        # Test with our provider
        provider = OllamaProvider(
            base_url="http://localhost:1234",  # Provider will add /v1
            model=model_id
        )
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2 + 2?"}
        ]
        
        print("\nGenerating response...")
        for token in provider.generate_stream("", messages=messages):
            print(token, end="", flush=True)
        print("\n\n✅ Provider test passed!")
        
    except Exception as e:
        print(f"\n❌ Provider test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lm_studio_direct()
    test_with_provider()