# OpenAI Context Test

This test script verifies that conversation context is properly passed to the OpenAI provider.

## Running the Test

1. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. Run the test:
   ```bash
   python test_openai_context.py
   ```

## What it Tests

1. **Simple generation** - Basic API call without context
2. **Generation with history** - Verifies that conversation history is passed correctly
3. **Streaming with history** - Tests streaming responses with context
4. **LLMClient integration** - Tests the full integration through LLMClient

## Expected Result

The test should show that the AI remembers information from previous messages in the conversation (like a name or favorite color).