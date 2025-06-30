# PyPI Publishing Guide

This guide describes how to publish the thonny-codemate package to PyPI.

## Prerequisites

1. Install build tools:
```bash
pip install --upgrade build twine
```

2. Create PyPI account:
- Register at https://pypi.org/account/register/
- Create an API token at https://pypi.org/manage/account/token/
- Save the token securely

## Building the Package

1. Clean previous builds:
```bash
rm -rf dist/ build/ *.egg-info/
```

2. Build the package:
```bash
python -m build
```

This creates:
- `dist/thonny_codemate-0.1.0-py3-none-any.whl` (wheel file)
- `dist/thonny_codemate-0.1.0.tar.gz` (source distribution)

## Testing with TestPyPI (Recommended)

1. Upload to TestPyPI first:
```bash
python -m twine upload --repository testpypi dist/*
```

2. Test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ thonny-codemate
```

## Publishing to PyPI

1. Upload to PyPI:
```bash
python -m twine upload dist/*
```

Enter your PyPI username and API token when prompted.

2. Verify installation:
```bash
pip install thonny-codemate
```

## Using .pypirc for Authentication

Create `~/.pypirc` file:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TEST-API-TOKEN-HERE
```

## Version Management

Before each release:
1. Update version in `pyproject.toml`
2. Create a git tag: `git tag v0.1.0`
3. Push tag: `git push origin v0.1.0`

## Post-Publishing

1. Test installation on different systems
2. Update README with installation instructions
3. Create GitHub release with changelog