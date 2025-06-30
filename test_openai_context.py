#!/usr/bin/env python3
"""
Test script to verify OpenAI context is working properly.
This script tests the conversation history functionality.
"""

import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from thonnycontrib.thonny_codemate.llm_client import LLMClient
from thonnycontrib.thonny_codemate.external_providers import ChatGPTProvider


def test_openai_context():
    """Test OpenAI provider with conversation history"""
    
    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Create provider
    provider = ChatGPTProvider(api_key=api_key, model="gpt-3.5-turbo")
    
    # Test 1: Simple generation without history
    print("=== Test 1: Simple generation ===")
    response = provider.generate("Hello, please remember that my favorite color is blue.")
    print(f"Response: {response}\n")
    
    # Test 2: Generation with conversation history
    print("=== Test 2: With conversation history ===")
    messages = [
        {"role": "user", "content": "Hello, please remember that my favorite color is blue."},
        {"role": "assistant", "content": "I'll remember that your favorite color is blue. Is there anything else you'd like me to know?"},
        {"role": "user", "content": "What is my favorite color?"}
    ]
    
    response = provider.generate(
        prompt="What is my favorite color?",
        messages=messages
    )
    print(f"Response: {response}\n")
    
    # Test 3: Streaming with conversation history
    print("=== Test 3: Streaming with history ===")
    print("Response: ", end="", flush=True)
    for token in provider.generate_stream(
        prompt="Can you tell me again what my favorite color is?",
        messages=messages
    ):
        print(token, end="", flush=True)
    print("\n")


def test_llm_client_integration():
    """Test LLMClient integration with external provider"""
    print("\n=== Test 4: LLMClient Integration ===")
    
    # Mock workbench for testing
    class MockWorkbench:
        def __init__(self):
            self.options = {
                "llm.provider": "chatgpt",
                "llm.chatgpt_api_key": os.environ.get("OPENAI_API_KEY", ""),
                "llm.external_model": "gpt-3.5-turbo",
                "llm.temperature": 0.7,
                "llm.max_tokens": 200
            }
        
        def get_option(self, key, default=None):
            return self.options.get(key, default)
    
    # Monkey patch get_workbench
    import thonnycontrib.thonny_codemate.llm_client
    original_get_workbench = None
    if hasattr(thonnycontrib.thonny_codemate.llm_client, 'get_workbench'):
        original_get_workbench = thonnycontrib.thonny_codemate.llm_client.get_workbench
    
    thonnycontrib.thonny_codemate.llm_client.get_workbench = MockWorkbench
    
    try:
        # Create LLM client
        client = LLMClient()
        
        # Test with conversation history
        messages = [
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Nice to meet you, Alice! How can I help you today?"}
        ]
        
        print("Testing with conversation history...")
        response = ""
        for token in client.generate_stream("What is my name?", messages=messages):
            response += token
            print(token, end="", flush=True)
        print("\n")
        
        # Check if the response mentions "Alice"
        if "Alice" in response:
            print("✓ Context is working! The assistant remembered the name.")
        else:
            print("✗ Context is NOT working. The assistant didn't remember the name.")
            
    finally:
        # Restore original get_workbench
        if original_get_workbench:
            thonnycontrib.thonny_codemate.llm_client.get_workbench = original_get_workbench


if __name__ == "__main__":
    print("Testing OpenAI Context Functionality\n")
    
    # Run tests
    test_openai_context()
    test_llm_client_integration()
    
    print("\nTests completed!")