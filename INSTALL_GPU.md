# GPU Support Installation Guide

## Overview

By default, `thonny-local-ollama` installs with CPU support. To enable GPU acceleration, you need to reinstall `llama-cpp-python` with the appropriate build for your hardware.

## Automatic GPU Detection

When you run the plugin, it will automatically detect available GPUs and use them if the correct version of llama-cpp-python is installed.

## NVIDIA GPU (CUDA)

### Windows/Linux with NVIDIA GPU:

```bash
# First, install the plugin
pip install thonny-local-ollama

# Then reinstall llama-cpp-python with CUDA support
pip uninstall llama-cpp-python
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
```

### Verify CUDA Installation:

```bash
python -c "from llama_cpp import llama_cpp; print('CUDA Support:', hasattr(llama_cpp, 'GGML_USE_CUBLAS') and llama_cpp.GGML_USE_CUBLAS)"
```

## Apple Silicon (Metal)

### macOS with M1/M2/M3:

```bash
# First, install the plugin
pip install thonny-local-ollama

# Then rebuild llama-cpp-python with Metal support
pip uninstall llama-cpp-python
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-cache-dir
```

### Verify Metal Installation:

```bash
python -c "from llama_cpp import llama_cpp; print('Metal Support:', hasattr(llama_cpp, 'GGML_USE_METAL') and llama_cpp.GGML_USE_METAL)"
```

## Troubleshooting

### CUDA Version Mismatch

If you encounter CUDA errors, ensure your CUDA toolkit version matches the llama-cpp-python build:

- `cu124` = CUDA 12.4
- `cu121` = CUDA 12.1
- `cu118` = CUDA 11.8

Check your CUDA version:
```bash
nvidia-smi
```

### Metal Performance

For optimal Metal performance on macOS:

1. Ensure you have the latest macOS version
2. Close other GPU-intensive applications
3. The plugin will automatically use all available GPU memory

### Fallback to CPU

If GPU initialization fails, the plugin will automatically fall back to CPU mode. Check the logs in Thonny's Shell for diagnostic information.

## Development Installation with GPU

For development with `uv`:

```bash
# CUDA support
uv pip uninstall llama-cpp-python
uv pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# Metal support
uv pip uninstall llama-cpp-python
CMAKE_ARGS="-DLLAMA_METAL=on" uv pip install llama-cpp-python --no-cache-dir
```