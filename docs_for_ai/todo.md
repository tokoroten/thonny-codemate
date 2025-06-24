# TODO List for Thonny Local LLM Plugin

このファイルは、プロジェクトのタスク管理のためのTODOリストです。
AIはこのファイルを参照して作業を進め、完了したタスクは適宜更新してください。

## High Priority Tasks

- [ ] Create basic project structure with pyproject.toml
- [ ] Implement thonnycontrib package structure with __init__.py
- [ ] Create llm_client.py for llama-cpp-python integration
- [ ] Implement basic load_plugin() function
- [ ] Create chat panel UI on the right side (like GitHub Copilot)
- [ ] Implement context menu for 'Code Explanation'

## Medium Priority Tasks

- [ ] Add configuration management (config.py)
- [ ] Implement lazy model loading (load on first use, not at startup)
- [ ] Add error fixing assistance feature
- [ ] Create tests directory and basic unit tests

## Low Priority Tasks

- [ ] Add user skill level selection feature
- [ ] Implement multi-file context understanding
- [ ] Add support for external APIs (ChatGPT/Ollama/OpenRouter)
- [ ] Implement inline code completion (cursor position)
- [ ] Create USB portable deployment configuration
- [ ] Prepare PyPI package and publish

## Notes

- タスクを開始する際は、該当項目を `- [ ]` から `- [x]` に変更してください
- 新しいタスクが発生した場合は、適切な優先度のセクションに追加してください
- 完了したタスクには完了日を記載すると良いでしょう（例：`- [x] タスク内容 (2024-01-24完了)`）