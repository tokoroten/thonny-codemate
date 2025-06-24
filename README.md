# Thonny Local LLM Plugin

A Thonny IDE plugin that integrates local LLM capabilities using llama-cpp-python to provide GitHub Copilot-like features without requiring external API services.

## Features

- 🤖 **Local LLM Integration**: Uses llama-cpp-python to load GGUF models directly (no Ollama server required)
- 🚀 **On-Demand Model Loading**: Models are loaded on first use (not at startup) to avoid slow startup times
- 📝 **Code Generation**: Generate code based on natural language instructions
- 💡 **Code Explanation**: Select code and get AI-powered explanations via context menu
- 🎯 **Context-Aware**: Understands multiple files and project context
- 🎚️ **Skill Level Adaptation**: Adjusts responses based on user's programming skill level
- 🔌 **Optional External APIs**: Support for ChatGPT, Ollama server, and OpenRouter as alternatives
- 💾 **USB Portable**: Can be bundled with Thonny and models for portable use

## Installation

### From PyPI (Coming Soon)
```bash
pip install thonny-ollama
```

### Development Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/thonny_local_ollama.git
cd thonny_local_ollama

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -e .
```

### Installing llama-cpp-python

For CPU support:
```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

For CUDA support:
```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
```

## Model Setup

### Download GGUF Models
```bash
# Install Hugging Face CLI
pip install -U "huggingface_hub[cli]"

# Download a model (example)
huggingface-cli download TheBloke/Llama-3-8B-GGUF llama3-8b.Q4_K_M.gguf --local-dir ./models
```

## Usage

1. **Start Thonny** - The plugin will load automatically
2. **Model Loading** - The configured GGUF model loads on first use (lazy loading)
3. **Code Explanation**:
   - Select code in the editor
   - Right-click and choose "Code Explanation"
4. **Code Generation**:
   - Open the AI Assistant panel
   - Type your request in natural language
   - The AI will generate code based on your instructions

## Development

### Project Structure
```
thonny_local_ollama/
├── thonnycontrib/
│   └── thonny_local_ollama/
│       ├── __init__.py       # Plugin entry point
│       ├── llm_client.py     # LLM integration
│       ├── ui_widgets.py     # UI components
│       └── config.py         # Configuration
├── models/                   # GGUF model storage
├── tests/                    # Unit tests
├── docs_for_ai/             # AI documentation
└── README.md
```

### Running Tests
```bash
pytest -v
```

### Debugging
```bash
# Run Thonny with debugpy support
python -m debugpy --listen 5678 --wait-for-client -m thonny
```

## Configuration

The plugin stores its configuration in Thonny's settings system. You can configure:

- Model path and selection
- User skill level (beginner/intermediate/advanced)
- Optional API endpoints for external services
- Context window size
- Generation parameters (temperature, max tokens, etc.)

## Requirements

- Python 3.8+
- Thonny 4.0+
- llama-cpp-python
- 4GB+ RAM (depending on model size)
- 5-10GB disk space for models

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by GitHub Copilot's functionality
- Built on top of [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- Designed for [Thonny IDE](https://thonny.org/)

## Status

🚧 **Under Development** - This plugin is currently in early development stage.

## Roadmap

- [x] Initial project setup
- [ ] Basic plugin structure
- [ ] LLM integration with llama-cpp-python
- [ ] Context menu for code explanation
- [ ] Code generation interface
- [ ] Multi-file context support
- [ ] Configuration UI
- [ ] USB portable packaging
- [ ] PyPI release

## Links

- [Thonny IDE](https://thonny.org/)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [Project Documentation](docs_for_ai/)