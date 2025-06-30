# Build Instructions for PyPI

## 1. Preparation Steps

### Install required tools
```bash
# In your virtual environment
pip install --upgrade build twine
```

### Clean previous builds
```bash
rm -rf dist/ build/ *.egg-info/
```

## 2. Build the Package

```bash
python -m build
```

This will create:
- `dist/thonny_codemate-0.1.0-py3-none-any.whl`
- `dist/thonny_codemate-0.1.0.tar.gz`

## 3. Check the Package

```bash
# Check package contents
tar -tvf dist/thonny_codemate-0.1.0.tar.gz

# Check for issues
python -m twine check dist/*
```

## 4. Test Installation Locally

```bash
# Create a test virtual environment
python -m venv test_env
test_env\Scripts\activate  # Windows
# or
source test_env/bin/activate  # Linux/macOS

# Install from local wheel
pip install dist/thonny_codemate-0.1.0-py3-none-any.whl

# Test import
python -c "import thonnycontrib.thonny_codemate; print('Success!')"
```

## 5. Upload to PyPI

### First time: Create PyPI account and API token
1. Go to https://pypi.org/account/register/
2. Create account
3. Go to https://pypi.org/manage/account/token/
4. Create API token with scope "Entire account"
5. Save token securely

### Upload to TestPyPI first (recommended)
```bash
python -m twine upload --repository testpypi dist/*
```

### Upload to PyPI
```bash
python -m twine upload dist/*
```

Username: `__token__`
Password: Your PyPI API token (starts with `pypi-`)

## 6. Verify Installation

```bash
pip install thonny-local-ollama
```

## Important Notes

- The package name on PyPI is `thonny-local-ollama`
- Make sure version in pyproject.toml is updated before building
- Test thoroughly before uploading to PyPI (uploads cannot be deleted)
- Consider using TestPyPI first for testing