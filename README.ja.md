# Thonny CodeMateプラグイン

Thonny IDEにローカルLLM機能を統合するプラグインです。llama-cpp-pythonを使用してGitHub Copilotのような機能を外部APIサービスなしで提供します。

## 機能

- 🤖 **ローカルLLM統合**: llama-cpp-pythonを使用してGGUFモデルを直接読み込み（Ollamaサーバー不要）
- 🚀 **オンデマンドモデル読み込み**: 起動時の遅延を避けるため、モデルは初回使用時に読み込まれます
- 📝 **コード生成**: 自然言語の指示に基づいてコードを生成
- 💡 **コード解説**: コードを選択してコンテキストメニューからAIによる解説を取得
- 🎯 **コンテキスト認識**: 複数のファイルとプロジェクトのコンテキストを理解
- 💬 **会話履歴の保持**: LLMに会話履歴を送信し、文脈を保った対話が可能
- 🎚️ **スキルレベル適応**: ユーザーのプログラミングスキルレベルに応じて回答を調整
- 🔌 **外部API対応**: ChatGPT、Ollamaサーバー、OpenRouterをオプションで使用可能
- 📥 **モデルダウンロードマネージャー**: 推奨モデルの組み込みダウンロードマネージャー
- 🎨 **カスタマイズ可能なシステムプロンプト**: カスタムシステムプロンプトでAIの動作を調整
- 📋 **インタラクティブなコードブロック**: ネイティブUIでコードのコピーと挿入が可能（JavaScript不要）
- 🎨 **Markdownレンダリング**: tkinterwebによるオプションのリッチテキスト表示
- 💾 **USBポータブル**: Thonnyとモデルをバンドルしてポータブル使用が可能

## インストール

### PyPIから
```bash
# 標準インストール（CPU版のllama-cpp-pythonを含む）
pip install thonny-codemate
```

**GPUサポートについては**、[INSTALL_GPU.md](INSTALL_GPU.md)を参照してください：
- NVIDIA GPU (CUDA)
- Apple Silicon (Metal)
- 自動GPU検出

### 開発環境でのインストール

#### uvを使った簡単セットアップ（推奨）
```bash
# リポジトリをクローン
git clone https://github.com/tokoroten/thonny-codemate.git
cd thonny-codemate

# uvをインストール（未インストールの場合）
# Windows (PowerShell):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 全ての依存関係をインストール（llama-cpp-python含む）
uv sync --all-extras

# または開発用依存関係のみインストール
uv sync --extra dev

# （オプション）Markdownレンダリングサポートをインストール
# 基本的なMarkdownレンダリング：
uv sync --extra markdown
# インタラクティブ機能のための完全なJavaScriptサポート：
uv sync --extra markdown-full

# 仮想環境をアクティベート
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

#### セットアップスクリプトを使用
```bash
# ガイド付きインストール
python setup_dev.py
```

### GPUサポートでのインストール

デフォルトでは、llama-cpp-pythonはCPUサポートでインストールされます。GPU高速化の場合：

**CUDA版**：
```bash
# CUDA対応のllama-cpp-pythonを再インストール
uv pip uninstall llama-cpp-python
uv pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
```

**Metal版（macOS）**：
```bash
# Metalサポートで再ビルド
uv pip uninstall llama-cpp-python
CMAKE_ARGS="-DLLAMA_METAL=on" uv pip install llama-cpp-python --no-cache-dir
```

## モデルのセットアップ

### GGUFモデルのダウンロード

推奨モデル：
- **Qwen2.5-Coder-14B** - プログラミングに特化した最新の高性能モデル（8.8GB）
- **Llama-3.2-1B/3B** - 軽量で高速なモデル（0.8GB/2.0GB）
- **Llama-3-ELYZA-JP-8B** - 日本語特化モデル（4.9GB）

```bash
# Hugging Face CLIをインストール
pip install -U "huggingface_hub[cli]"

# Qwen2.5 Coder（プログラミング特化、推奨）
huggingface-cli download bartowski/Qwen2.5-Coder-14B-Instruct-GGUF Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf --local-dir ./models

# Llama 3.2 1B（軽量版）
huggingface-cli download bartowski/Llama-3.2-1B-Instruct-GGUF Llama-3.2-1B-Instruct-Q4_K_M.gguf --local-dir ./models
```

## 使い方

1. **Thonnyを起動** - プラグインが自動的に読み込まれます
2. **モデルの設定**：
   - 設定 → LLMアシスタント設定を開く
   - ローカルモデルまたは外部APIを選択
   - ローカルモデルの場合：GGUFファイルを選択するか推奨モデルをダウンロード
   - 外部APIの場合：APIキーとモデル名を入力
3. **コード解説**：
   - エディタでコードを選択
   - 右クリックして「選択範囲を説明」を選択
   - AIがスキルレベルに応じてコードを解説
4. **コード生成**：
   - 実装したい内容をコメントで記述
   - 右クリックして「コメントから生成」を選択
   - またはAIアシスタントパネルでインタラクティブにチャット
5. **エラー修正**：
   - エラーが発生したら、アシスタントパネルの「エラーを説明」をクリック
   - AIがエラーを分析して修正案を提示

### 外部APIの設定

#### ChatGPT
1. [OpenAI](https://platform.openai.com/)からAPIキーを取得
2. 設定で「chatgpt」をプロバイダーとして選択
3. APIキーを入力
4. モデルを選択（例：gpt-3.5-turbo、gpt-4）

#### Ollama
1. [Ollama](https://ollama.ai/)をインストールして実行
2. 設定で「ollama」をプロバイダーとして選択
3. ベースURLを設定（デフォルト：http://localhost:11434）
4. インストール済みモデルを選択（例：llama3、mistral）

#### OpenRouter
1. [OpenRouter](https://openrouter.ai/)からAPIキーを取得
2. 設定で「openrouter」をプロバイダーとして選択
3. APIキーを入力
4. モデルを選択（無料モデルも利用可能）

## 開発

### プロジェクト構造
```
thonny-codemate/
├── thonnycontrib/
│   └── thonny_codemate/
│       ├── __init__.py       # プラグインエントリポイント
│       ├── llm_client.py     # LLM統合
│       ├── ui_widgets.py     # UIコンポーネント
│       └── config.py         # 設定管理
├── models/                   # GGUFモデル格納
├── tests/                    # ユニットテスト
├── docs_for_ai/             # AI向けドキュメント
└── README.ja.md
```

### テストの実行
```bash
pytest -v
```

### デバッグ
```bash
# debugpyサポート付きでThonnyを実行
python -m debugpy --listen 5678 --wait-for-client -m thonny
```

## 設定

プラグインはThonnyの設定システムに設定を保存します。以下の項目を設定できます：

- **プロバイダー選択**: ローカルモデルまたは外部API（ChatGPT、Ollama、OpenRouter）
- **モデル設定**: モデルパス、コンテキストサイズ、生成パラメータ
- **ユーザー設定**: スキルレベル（初心者/中級者/上級者）
- **システムプロンプト**: コーディング重視、解説重視、またはカスタムプロンプトから選択
- **生成パラメータ**: temperature、最大トークン数など

## 必要要件

- Python 3.8以上
- Thonny 4.0以上
- llama-cpp-python（自動的にインストールされます）
- 4GB以上のRAM（モデルサイズによる）
- 5-10GBのディスク容量（モデル用）
- uv（開発用）
- tkinterweb（JavaScriptサポート付き、Markdownレンダリングとインタラクティブ機能用）
  - プラグインと一緒に自動的にインストールされます
  - JavaScript-Python通信のためのPythonMonkeyを含みます
  - Copy/InsertボタンがPythonと直接統合されます

## 貢献

貢献を歓迎します！プルリクエストをお気軽に送信してください。

1. リポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュ (`git push origin feature/AmazingFeature`)
5. プルリクエストを開く

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細はLICENSEファイルを参照してください。

## 謝辞

- GitHub Copilotの機能にインスパイアされました
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)を基盤として構築
- [Thonny IDE](https://thonny.org/)向けに設計
- **このプロジェクトのコードの99%は[Claude Code](https://claude.ai/code)によって生成されました** - AI支援開発の可能性を示すプロジェクトです

## ステータス

🚧 **開発中** - このプラグインは現在、初期開発段階にあります。

## ロードマップ

- [x] 初期プロジェクトセットアップ
- [x] uvを使用した開発環境
- [x] 基本的なプラグイン構造
- [x] llama-cpp-pythonとのLLM統合
- [x] チャットパネルUI（右側）
- [x] コード解説用コンテキストメニュー
- [x] コメントからのコード生成
- [x] エラー修正支援
- [x] 設定UI
- [x] 複数ファイルのコンテキストサポート
- [x] モデルダウンロードマネージャー
- [x] 外部API対応（ChatGPT、Ollama、OpenRouter）
- [x] カスタマイズ可能なシステムプロンプト
- [ ] インラインコード補完
- [ ] USBポータブルパッケージング
- [ ] PyPIリリース

## プロジェクトのゴール

このプロジェクトの詳細な目標：

1. **効率的なモデル読み込み**
   - 初回使用時にLLMモデルを読み込む（起動時ではなく）
   - 数GBのモデルでも起動時間に影響しない
   - バックグラウンドでの非同期読み込みによりUIをブロックしない

2. **エージェント型コーディング支援**
   - ユーザーの指示を理解し、適切なコードを生成
   - プロジェクト全体のコンテキストを考慮した提案

3. **教育的配慮**
   - 初心者から上級者まで、スキルレベルに応じた説明
   - プログラミング学習をサポートする機能

4. **ポータビリティ**
   - USBメモリから直接実行可能
   - インストール不要で使用できる配布形態

## リンク

- [Thonny IDE](https://thonny.org/)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [プロジェクトドキュメント](docs_for_ai/)