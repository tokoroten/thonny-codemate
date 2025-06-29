# Troubleshooting Guide

This guide helps you resolve common issues with the Thonny Local LLM Plugin.

## Common Issues

### 1. Model Loading Issues

#### Problem: "Failed to load model" error
**Symptoms:**
- Red error message in the chat view
- Model status shows "Load failed"

**Solutions:**
1. **Check model file existence:**
   ```bash
   # Verify the model file exists and is readable
   ls -la /path/to/your/model.gguf
   ```

2. **Verify model format:**
   - Ensure the file is a valid GGUF format
   - Try downloading a known-good model from the built-in manager

3. **Check available memory:**
   - Large models require significant RAM
   - Close other applications to free memory
   - Consider using a smaller model (1B-3B parameters)

4. **Check llama-cpp-python installation:**
   ```bash
   python -c "import llama_cpp; print('OK')"
   ```

#### Problem: "Model file not found"
**Solutions:**
- Use the built-in model download manager (Settings → Download Models)
- Verify the path in Settings → Model Path
- Ensure proper file permissions

### 2. Connection Issues

#### Problem: "Failed to connect to Ollama/LM Studio"
**Symptoms:**
- Cannot fetch model list from external providers
- Connection timeout errors

**Solutions:**
1. **Check server status:**
   - Ollama: `ollama list` in terminal
   - LM Studio: Verify server is running on correct port

2. **Verify host/port settings:**
   - Ollama default: `localhost:11434`
   - LM Studio default: `localhost:1234`
   - Use preset buttons for quick setup

3. **Test network connectivity:**
   ```bash
   # For Ollama
   curl http://localhost:11434/api/tags
   
   # For LM Studio
   curl http://localhost:1234/v1/models
   ```

4. **Check firewall settings:**
   - Ensure ports are not blocked
   - Temporarily disable firewall for testing

### 3. Performance Issues

#### Problem: Slow response times
**Solutions:**
1. **Use GPU acceleration:**
   - Install CUDA version of llama-cpp-python for NVIDIA GPUs
   - See [INSTALL_GPU.md](INSTALL_GPU.md) for details

2. **Optimize model settings:**
   - Reduce context size (Settings → Context Size)
   - Use smaller models (3B vs 8B parameters)
   - Lower temperature for faster generation

3. **Close unnecessary applications:**
   - Free up RAM and CPU resources
   - Monitor system resources during generation

#### Problem: UI becomes unresponsive
**Solutions:**
1. **Update to latest version:**
   ```bash
   pip install --upgrade thonny-local-ollama
   ```

2. **Clear conversation history:**
   - Use "Clear" button in chat view
   - Restart Thonny if needed

3. **Check for infinite loops:**
   - Look for repeated animation warnings in logs
   - Restart the plugin if animations get stuck

### 4. Installation Issues

#### Problem: "tkinterweb not found" for Markdown rendering
**Solutions:**
```bash
# Install tkinterweb for enhanced UI
pip install tkinterweb

# If installation fails, use text-only mode
# The plugin will work without tkinterweb
```

#### Problem: llama-cpp-python installation fails
**Solutions:**
1. **For CPU-only systems:**
   ```bash
   pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
   ```

2. **For NVIDIA GPU systems:**
   ```bash
   pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
   ```

3. **For Apple Silicon Macs:**
   ```bash
   CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-binary llama-cpp-python
   ```

### 5. Memory Issues

#### Problem: "Out of memory" errors
**Solutions:**
1. **Use smaller models:**
   - Llama-3.2-1B instead of Llama-3.1-8B
   - Q4_K_M quantization instead of F16

2. **Reduce context size:**
   - Lower context size in settings (e.g., 2048 instead of 4096)
   - Clear conversation history regularly

3. **Enable GPU offloading:**
   - Move model layers to GPU memory
   - Configure GPU layers in advanced settings

### 6. Language and Localization Issues

#### Problem: Mixed language interface
**Solutions:**
1. **Set Thonny language:**
   - Tools → Options → General → Language
   - Restart Thonny after changing

2. **Check output language setting:**
   - Plugin Settings → Output Language
   - Use "Auto" to follow Thonny's language

## Debug Information

### Collecting Logs
1. **Enable debug logging:**
   - Add debug output to Thonny's System Shell
   - Look for LLM-related error messages

2. **Check conversation history:**
   - Located in Thonny's configuration directory
   - Path: `~/.config/thonny/llm_assistant/chat_history.json`

3. **System information to include:**
   - Operating system and version
   - Python version
   - Thonny version
   - llama-cpp-python version
   - Available RAM and GPU

### Performance Monitoring
The plugin includes built-in performance monitoring:
- Slow operations (>1 second) are logged as warnings
- Use the statistics to identify bottlenecks
- Large message counts may trigger virtualization

## Getting Help

### Before Reporting Issues
1. **Update to latest version:**
   ```bash
   pip install --upgrade thonny-local-ollama
   ```

2. **Try with a fresh model:**
   - Download a known-good model from the manager
   - Test with Llama-3.2-1B (smallest, fastest)

3. **Test with external providers:**
   - Try Ollama or LM Studio as alternative
   - Rules out local model issues

### Reporting Bugs
When reporting issues, please include:
- Complete error messages
- Steps to reproduce the problem
- System information (OS, Python version, etc.)
- Model being used
- Plugin settings (without API keys)

### Community Support
- GitHub Issues: [Report bugs and request features](https://github.com/tokoroten/thonny_local_ollama/issues)
- Discussions: Share usage tips and ask questions

## Advanced Troubleshooting

### Custom Installation Paths
If using custom installation paths:
1. **Set environment variables:**
   ```bash
   export LLAMA_CPP_PYTHON_PATH=/custom/path
   ```

2. **Verify import path:**
   ```python
   import sys
   print(sys.path)
   ```

### Network Configuration
For corporate networks:
1. **Configure proxy settings:**
   ```bash
   pip install --proxy http://proxy:port thonny-local-ollama
   ```

2. **Certificate issues:**
   ```bash
   pip install --trusted-host pypi.org --trusted-host pypi.python.org thonny-local-ollama
   ```

### Development and Testing
For developers and advanced users:
1. **Clone repository:**
   ```bash
   git clone https://github.com/tokoroten/thonny_local_ollama.git
   cd thonny_local_ollama
   pip install -e .
   ```

2. **Run tests:**
   ```bash
   pytest tests/
   ```

3. **Enable debug mode:**
   ```python
   import logging
   logging.getLogger('thonnycontrib.thonny_local_ollama').setLevel(logging.DEBUG)
   ```