# TODO List for Thonny Local LLM Plugin

このファイルは、プロジェクトのタスク管理のためのTODOリストです。
AIはこのファイルを参照して作業を進め、完了したタスクは適宜更新してください。

## High Priority Tasks

- [x] Create basic project structure with pyproject.toml (2025-06-24完了)
- [x] Implement thonnycontrib package structure with __init__.py (2025-06-24完了)
- [x] Create llm_client.py for llama-cpp-python integration (2025-06-24完了)
- [x] Implement basic load_plugin() function (2025-06-24完了)
- [x] Create chat panel UI on the right side (like GitHub Copilot) (2025-06-24完了)
- [x] Implement context menu for 'Code Explanation' (2025-06-24完了)
- [x] Add model download manager with recommended models (2025-06-25完了)
- [x] Fix streaming output duplicate labels (2025-06-25完了)
- [x] Add stop generation functionality (button and ESC key) (2025-06-25完了)
- [x] Fix context inclusion to use current editor file (2025-06-25完了)
- [x] Fix logging errors in Thonny environment (2025-06-25完了)
- [x] Implement Markdown rendering for LLM output using tkinterweb (2025-06-26完了)

## Medium Priority Tasks

- [x] Add configuration management (settings_dialog.py) (2025-06-24完了)
- [x] Implement lazy model loading (load on first use, not at startup) (2025-06-24完了)
- [x] Add error fixing assistance feature (2025-06-25完了)
- [x] Create tests directory and basic unit tests (2025-06-24完了)
- [x] Implement code generation from comments (2025-06-25完了)
- [x] Add customizable system prompts (2025-06-25完了)
- [x] Improve button sizes for better text display (2025-06-25完了)
- [x] Implement key binding changes and UI adjustments (2025-06-25完了)
- [x] Add Copy and Insert buttons for code blocks (2025-06-26完了)
- [x] Implement virtual DOM system to reduce flickering in HTML chat view (2025-06-26完了)
- [x] Fix Copy/Insert buttons not clickable during message streaming (2025-06-26完了)

## Low Priority Tasks

- [x] Add user skill level selection feature (2025-06-24完了)
- [x] Implement multi-file context understanding (2025-06-25完了)
- [x] Add support for external APIs (ChatGPT/Ollama/OpenRouter) (2025-06-25完了)
- [x] Prepare PyPI package and publish (2025-06-30完了) - v0.1.3 released to PyPI
- [ ] Implement inline code completion (cursor position)
- [ ] Create USB portable deployment configuration

## Recent Updates (2025-06-30)

### Repository Renaming and Package Updates
- Renamed package from `thonny_local_ollama` to `thonny-codemate`
- Updated all references in code, documentation, and configuration files
- Updated GitHub repository URL to https://github.com/tokoroten/thonny-codemate
- Added acknowledgment that 99% of code was created by Claude Code

### Python Version Requirements Update
- Updated minimum Python version from 3.8 to 3.10 to match Thonny requirements
- Updated all CI/CD workflows to test only Python 3.10, 3.11, and 3.12
- Updated pyproject.toml and tool configurations accordingly

### Test Suite Optimization
- Removed heavy integration tests that require Thonny environment
- Removed performance monitoring and message virtualization tests
- Fixed all module import errors and deprecated assertions
- All tests now pass in GitHub Actions CI

### Error Handling Consolidation
- Created unified error handling utilities in utils/unified_error_handler.py
- Consolidated duplicate error handling code across the codebase
- Improved user-friendly error messages with proper localization

### GitHub Actions Setup
- Created automated release workflow for PyPI publishing
- Configured support for both TestPyPI and production PyPI
- Set up proper test workflow with matrix strategy for multiple OS and Python versions

## Recent Updates (2025-06-26)

### Button Click Fix During Message Streaming
- Fixed issue where Copy/Insert buttons couldn't be clicked during message streaming
- Replaced full HTML reload with partial DOM updates using JavaScript
- Added `_update_last_message_js()` method for incremental updates
- Reduced update interval from 500ms to 100ms for smoother streaming
- Buttons now remain functional throughout the entire message generation process

### Virtual DOM Implementation for Flicker-Free Updates
- Created `virtual_dom.py` to track DOM changes and generate minimal patches
- Implemented `incremental_markdown_renderer.py` for rendering individual messages
- Created `chat_view_html_vdom.py` with virtual DOM support
- Reduced flickering during message streaming by updating only changed parts
- Improved performance with rate-limited updates and smooth scrolling

### Markdown Rendering Implementation
- Created `markdown_renderer.py` for converting markdown to HTML with syntax highlighting
- Implemented `chat_view_html.py` using tkinterweb for rich text display
- Added interactive Copy/Insert buttons for code blocks
- Made HTML view optional with fallback to text-only view
- Added setting in preferences to toggle between HTML and text views

### Features Added
- **Virtual DOM**: Incremental updates to reduce flickering during streaming
- **Markdown Rendering**: Full markdown support with syntax highlighting using Pygments
- **Code Block Buttons**: 
  - Copy button: Copies code to clipboard with fallback support
  - Insert button: Inserts code at cursor position in editor
- **Graceful Fallback**: If tkinterweb is not installed, falls back to text view
- **User Choice**: Setting to choose between HTML (Markdown) and text views

### Technical Details
- Virtual DOM system generates JavaScript patches for incremental updates
- Message caching to avoid re-rendering unchanged content
- JavaScript update queue for smooth, non-blocking updates
- Uses `tkinterweb` for HTML rendering in Tkinter
- Uses `markdown` library for Markdown to HTML conversion
- Uses `pygments` for syntax highlighting with friendly theme
- JavaScript interface for communication between HTML and Python
- Responsive design with proper styling for chat interface

## Notes

- タスクを開始する際は、該当項目を `- [ ]` から `- [x]` に変更してください
- 新しいタスクが発生した場合は、適切な優先度のセクションに追加してください
- 完了したタスクには完了日を記載すると良いでしょう（例：`- [x] タスク内容 (2024-01-24完了)`）