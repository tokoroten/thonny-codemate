# Version 0.1.7

## 🚀 New Features

### Dynamic Model Fetching for OpenRouter
- Added automatic model list fetching from OpenRouter API
- New "Refresh" button to update available models
- "Free only" checkbox to filter free models
- Support for 55+ free models available on OpenRouter

### Manual Model Entry for All Providers
- ChatGPT, OpenRouter, and Ollama now support manual model name entry
- Use new models immediately without waiting for plugin updates
- Combo boxes allow both selection and manual input

### Unified Provider Implementation
- Refactored Ollama and LM Studio to use OpenAI-compatible API
- Simplified codebase with consistent error handling
- Better compatibility with various LLM servers

## 🐛 Bug Fixes

### Edit Mode Improvements
- Fixed code block extraction for multiline strings containing ```
- Prevent LLM from adding explanations after code blocks
- Auto-scroll to bottom for system messages

### Provider Fixes
- Fixed OpenRouter model availability (removed non-existent models)
- Fixed LM Studio connection issues at localhost:1234
- Fixed context handling for OpenAI provider in Chat mode

## 🔧 Technical Improvements

- All external providers now use OpenAI library for consistency
- Removed provider-specific detection logic
- Updated default model lists with currently available models
- Improved test coverage and mocking

## 📝 Updated Models

### OpenRouter Default Free Models
- meta-llama/llama-3.2-1b-instruct:free
- meta-llama/llama-3.1-8b-instruct:free
- google/gemini-2.0-flash-exp:free
- mistralai/mistral-7b-instruct:free
- qwen/qwen-2.5-72b-instruct:free