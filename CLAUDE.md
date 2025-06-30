# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Thonny IDE plugin that integrates local LLM capabilities using llama-cpp-python (not Ollama server) to provide GitHub Copilot-like features. The plugin will:
- Load GGUF models directly using llama-cpp-python when Thonny starts
- Provide code generation and explanation based on user instructions
- Support context-aware coding with multiple file understanding
- Include a portable USB deployment option

## AI向けドキュメント

`docs_for_ai/*.md` はAI向けのドキュメントです。AIがこのプロジェクトを理解しやすくするために、プロジェクトの目的・ゴールの情報が含まれています。

また、AIは作業を開始する前に`docs_for_ai/todo.md` を参照し、タスクを確認してください。
新たなタスクが発生した場合は、このファイルに追加してください。
タスクが完了したら、 `docs_for_ai/todo.md` の該当箇所を完了のステータスにしてください。i had

`README.md` を更新した場合は `README.ja.md` も日本語で更新してください。

## Project Goals

1. **Core Functionality**
   - Direct GGUF model loading via llama-cpp-python (no Ollama server)
   - Automatic model loading on Thonny startup
   - Agentic coding with multi-file context understanding
   - Code generation based on user instructions

2. **User Features**
   - Text selection in editor → context-aware Q&A with LLM
   - "Code Explanation" context menu for selected text
   - User skill level selection for appropriate responses
   - Optional support for ChatGPT/Ollama/OpenRouter servers

3. **Distribution**
   - PyPI package: `pip install thonny-codemate`
   - USB portable version with Thonny + plugin + models bundled

## Project Structure

```
thonny-codemate/
├── docs_for_ai/
│   └── project_goal.md    # Detailed project requirements
├── pyproject.toml         # Package configuration
├── README.md
├── thonnycontrib/
│   └── thonny_codemate/
│       ├── __init__.py    # load_plugin() implementation
│       ├── llm_client.py  # llama-cpp-python wrapper
│       ├── ui_widgets.py  # Thonny UI components
│       └── config.py      # Configuration management
├── models/                # GGUF model storage
├── tests/                 # Unit tests
└── CLAUDE.md             # This file
```

## Development Setup

### Virtual Environment Setup
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -U pip
```

### Install Dependencies
```bash
# Install llama-cpp-python (CPU version)
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# For CUDA support:
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# Install Thonny for development
git clone https://github.com/thonny/thonny.git
pip install -e ./thonny

# Install plugin in editable mode
pip install -e .
```

### Download GGUF Models
```bash
pip install -U "huggingface_hub[cli]"
huggingface-cli download TheBloke/Llama-3-8B-GGUF llama3-8b.Q4_K_M.gguf --local-dir ./models
```

## Common Commands

```bash
# Run Thonny with plugin
python -m thonny

# Debug mode with debugpy
python -m debugpy --listen 5678 --wait-for-client -m thonny

# Run tests
pytest -v

# Build package
python -m build

# Quick restart workflow
# Ctrl+Q → Enter → ↑ → Enter
```

## Architecture

### Core Components

1. **LLM Client Module** (`llm_client.py`)
   - Wraps llama-cpp-python for GGUF model loading
   - Manages model lifecycle and memory
   - Handles chat formatting and context management

2. **UI Integration** (`ui_widgets.py`)
   - Context menu for "Code Explanation"
   - Assistant panel for interactive Q&A
   - Progress indicators for model loading

3. **Configuration** (`config.py`)
   - Model path and selection
   - User skill level settings
   - Optional API endpoints for external services

### Key Implementation Details

```python
# Plugin entry point in __init__.py
def load_plugin():
    from thonny import get_workbench
    from .llm_client import LLMClient
    from .ui_widgets import AssistantView
    
    # Initialize LLM on startup
    client = LLMClient()
    client.load_model_async()
    
    # Add UI components
    get_workbench().add_view(AssistantView, "Assistant", "se")
```

## Development Notes

### Debugging Tips
- Use `logging` module - output goes to System Shell
- Check `thonny.log` in Thonny data folder for detailed logs
- VS Code/PyCharm remote debugging via debugpy is most efficient

### Performance Considerations
- Load models asynchronously to avoid blocking UI
- Use threading for LLM inference
- Cache model in memory between sessions if possible

### Testing Strategy
- Mock `thonny.get_workbench()` for unit tests
- Test model loading separately from UI
- Include integration tests with small GGUF models

### Portability Requirements
- Bundle all dependencies for USB deployment
- Use relative paths for model files
- Include platform-specific llama-cpp-python wheels