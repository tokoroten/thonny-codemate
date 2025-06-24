# Thonny ローカルLLMプラグイン

Thonny IDEにローカルLLM機能を統合するプラグインです。llama-cpp-pythonを使用してGitHub Copilotのような機能を外部APIサービスなしで提供します。

## 機能

- 🤖 **ローカルLLM統合**: llama-cpp-pythonを使用してGGUFモデルを直接読み込み（Ollamaサーバー不要）
- 🚀 **オンデマンドモデル読み込み**: 起動時の遅延を避けるため、モデルは初回使用時に読み込まれます
- 📝 **コード生成**: 自然言語の指示に基づいてコードを生成
- 💡 **コード解説**: コードを選択してコンテキストメニューからAIによる解説を取得
- 🎯 **コンテキスト認識**: 複数のファイルとプロジェクトのコンテキストを理解
- 🎚️ **スキルレベル適応**: ユーザーのプログラミングスキルレベルに応じて回答を調整
- 🔌 **外部API対応（オプション）**: ChatGPT、Ollamaサーバー、OpenRouterを代替として使用可能
- 💾 **USBポータブル**: Thonnyとモデルをバンドルしてポータブル使用が可能

## インストール

### PyPIから（準備中）
```bash
pip install thonny-ollama
```

### 開発環境でのインストール
```bash
# リポジトリをクローン
git clone https://github.com/yourusername/thonny_local_ollama.git
cd thonny_local_ollama

# 仮想環境を作成
python -m venv .venv
.venv\Scripts\activate  # Windows
# または
source .venv/bin/activate  # macOS/Linux

# 依存関係をインストール
pip install -e .
```

### llama-cpp-pythonのインストール

CPU版：
```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

CUDA版：
```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
```

## モデルのセットアップ

### GGUFモデルのダウンロード
```bash
# Hugging Face CLIをインストール
pip install -U "huggingface_hub[cli]"

# モデルをダウンロード（例）
huggingface-cli download TheBloke/Llama-3-8B-GGUF llama3-8b.Q4_K_M.gguf --local-dir ./models
```

## 使い方

1. **Thonnyを起動** - プラグインが自動的に読み込まれます
2. **モデルの読み込み** - 設定されたGGUFモデルが初回使用時に読み込まれます（遅延読み込み）
3. **コード解説**：
   - エディタでコードを選択
   - 右クリックして「コード解説」を選択
4. **コード生成**：
   - AIアシスタントパネルを開く
   - 自然言語でリクエストを入力
   - AIが指示に基づいてコードを生成

## 開発

### プロジェクト構造
```
thonny_local_ollama/
├── thonnycontrib/
│   └── thonny_local_ollama/
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

- モデルのパスと選択
- ユーザーのスキルレベル（初心者/中級者/上級者）
- 外部サービス用のオプションAPIエンドポイント
- コンテキストウィンドウサイズ
- 生成パラメータ（temperature、最大トークン数など）

## 必要要件

- Python 3.8以上
- Thonny 4.0以上
- llama-cpp-python
- 4GB以上のRAM（モデルサイズによる）
- 5-10GBのディスク容量（モデル用）

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

## ステータス

🚧 **開発中** - このプラグインは現在、初期開発段階にあります。

## ロードマップ

- [x] 初期プロジェクトセットアップ
- [ ] 基本的なプラグイン構造
- [ ] llama-cpp-pythonとのLLM統合
- [ ] コード解説用コンテキストメニュー
- [ ] コード生成インターフェース
- [ ] 複数ファイルのコンテキストサポート
- [ ] 設定UI
- [ ] USBポータブルパッケージング
- [ ] PyPIリリース

## プロジェクトのゴール

このプロジェクトの詳細な目標：

1. **モデル読み込みの最適化**
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