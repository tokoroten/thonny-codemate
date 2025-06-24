# TODO List for Thonny Local LLM Plugin

## Completed Tasks ✅

### High Priority
- [x] Create basic project structure with pyproject.toml
- [x] Implement thonnycontrib package structure with __init__.py
- [x] Create llm_client.py for llama-cpp-python integration
- [x] Implement basic load_plugin() function
- [x] Create chat panel UI on the right side (like GitHub Copilot)
- [x] Implement context menu for 'Code Explanation'
- [x] Add model download manager with recommended models

### Medium Priority
- [x] Add configuration management (config.py)
- [x] Implement lazy model loading (load on first use)
- [x] Add error fixing assistance feature
- [x] Create tests directory and basic unit tests
- [x] Implement code generation from comments
- [x] Add customizable system prompts

### Low Priority
- [x] Add user skill level selection feature
- [x] Implement multi-file context understanding
- [x] Add support for external APIs (ChatGPT/Ollama/OpenRouter)

## Pending Tasks 📝

### Low Priority
- [ ] Implement inline code completion (cursor position)
  - Need to detect cursor position in editor
  - Show suggestions based on current context
  - Handle tab/enter key for accepting suggestions

- [ ] Create USB portable deployment configuration
  - Bundle Thonny + plugin + models
  - Create portable launcher script
  - Test on different systems

- [ ] Prepare PyPI package and publish
  - Finalize package metadata
  - Create proper versioning
  - Write deployment documentation
  - Submit to PyPI

## Future Enhancements 🚀

- [ ] Add support for more model formats (GPTQ, AWQ)
- [ ] Implement code refactoring suggestions
- [ ] Add support for other programming languages
- [ ] Create model fine-tuning interface
- [ ] Add telemetry and usage analytics (optional)
- [ ] Implement collaborative features
- [ ] Add voice input/output support

## Known Issues 🐛

- [ ] Large models may cause memory issues on low-end systems
- [ ] Streaming responses can sometimes get cut off
- [ ] Context window limitations with very large projects

## Notes 📌

- All core features have been implemented
- External API support includes ChatGPT, Ollama, and OpenRouter
- Model download manager supports automatic download of recommended models
- System prompts can be customized for different use cases
- The plugin is feature-complete for initial release