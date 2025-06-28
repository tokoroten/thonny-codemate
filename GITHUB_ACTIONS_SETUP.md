# GitHub Actions Setup for Automatic PyPI Publishing

## Overview

This repository uses GitHub Actions to automatically publish the package to PyPI when a new release is created.

## Setup Steps

### 1. Get PyPI API Tokens

#### For PyPI (Production):
1. Go to https://pypi.org/manage/account/token/
2. Create a new API token with scope "Entire account" or project-specific
3. Copy the token (starts with `pypi-`)

#### For TestPyPI:
1. Go to https://test.pypi.org/manage/account/token/
2. Create a new API token
3. Copy the token

### 2. Add Secrets to GitHub Repository

1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add the following secrets:
   - Name: `PYPI_API_TOKEN`
     Value: Your PyPI API token
   - Name: `TEST_PYPI_API_TOKEN`
     Value: Your TestPyPI API token

### 3. How It Works

#### Automatic Testing (`test.yml`):
- Runs on every push and pull request
- Tests on multiple Python versions (3.8-3.12)
- Tests on multiple OS (Ubuntu, Windows, macOS)

#### Automatic Publishing (`publish.yml`):
- **Pre-release**: Publishes to TestPyPI
- **Release**: Publishes to PyPI
- Can also be triggered manually via GitHub Actions UI

### 4. Creating a Release

#### For Testing (Pre-release):
```bash
# Create and push a tag
git tag -a v0.1.0-beta.1 -m "Beta release for testing"
git push origin v0.1.0-beta.1
```

Then on GitHub:
1. Go to Releases → Create a new release
2. Choose the tag you created
3. Check "Set as a pre-release"
4. Publish release

This will publish to TestPyPI.

#### For Production:
```bash
# Create and push a tag
git tag -a v0.1.0 -m "First release"
git push origin v0.1.0
```

Then on GitHub:
1. Go to Releases → Create a new release
2. Choose the tag you created
3. Write release notes
4. Publish release (NOT as pre-release)

This will publish to PyPI.

### 5. Manual Trigger

You can also manually trigger the workflow:
1. Go to Actions tab
2. Select "Publish to PyPI" workflow
3. Click "Run workflow"
4. Choose branch and run

### 6. Version Management

Before creating a release:
1. Update version in `pyproject.toml`
2. Commit the change
3. Create tag matching the version

Example:
```bash
# Update pyproject.toml version to 0.2.0
git add pyproject.toml
git commit -m "Bump version to 0.2.0"
git push

# Create release tag
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

## Troubleshooting

### If publishing fails:
1. Check the Actions tab for error logs
2. Verify API tokens are correct
3. Ensure version number is unique (can't republish same version)
4. Check that all tests pass

### Test installation from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ thonny-local-ollama
```