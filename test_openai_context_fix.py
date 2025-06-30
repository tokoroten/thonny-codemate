#!/usr/bin/env python3
"""
Test script to verify OpenAI context handling after fix
"""

import sys
import os
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup
from thonnycontrib.thonny_codemate.llm_client import LLMClient
from thonnycontrib.thonny_codemate.external_providers import ChatGPTProvider

def test_openai_context():
    """Test that OpenAI provider correctly handles conversation context"""
    
    # Create a mock provider with debug output
    class DebugChatGPTProvider(ChatGPTProvider):
        def generate_stream(self, prompt: str, **kwargs):
            messages = kwargs.get("messages", [])
            print(f"\n=== DEBUG: ChatGPT Provider ===")
            print(f"Prompt parameter: '{prompt}'")
            print(f"Messages parameter ({len(messages)} messages):")
            for i, msg in enumerate(messages):
                print(f"  [{i}] {msg['role']}: {msg['content'][:100]}...")
            print("===========================\n")
            
            # Call parent method
            yield from super().generate_stream(prompt, **kwargs)
    
    # Initialize client
    client = LLMClient()
    
    # Set up mock external provider
    api_key = os.environ.get("OPENAI_API_KEY", "test-key")
    client._external_provider = DebugChatGPTProvider(api_key)
    
    # Test conversation
    conversation_history = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "My name is Alice"},
        {"role": "assistant", "content": "Nice to meet you, Alice!"},
        {"role": "user", "content": "What's my name?"}
    ]
    
    print("Testing OpenAI context handling...")
    print(f"Conversation history has {len(conversation_history)} messages")
    
    # This should only pass the messages, not duplicate the prompt
    response_tokens = []
    for token in client.generate_stream("What's my name?", messages=conversation_history[:-1]):
        response_tokens.append(token)
        print(token, end='', flush=True)
    
    print("\n\nTest complete!")
    
    # Check if response mentions Alice
    full_response = ''.join(response_tokens).lower()
    if 'alice' in full_response:
        print("✅ SUCCESS: The AI remembered the name from context!")
    else:
        print("❌ FAILURE: The AI did not remember the name from context")
        print(f"Response: {full_response}")

if __name__ == "__main__":
    test_openai_context()