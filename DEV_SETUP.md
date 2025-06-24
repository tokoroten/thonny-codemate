# 開発環境セットアップガイド

## クイックスタート

### 1. uvのインストール
```bash
# Windows (PowerShell):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 依存関係のインストール
```bash
# uvで仮想環境を作成
uv venv

# アクティベート
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 依存関係をインストール
uv pip install thonny
uv pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

または、`run_dev.py`を実行すると自動的にuvで環境をセットアップします：
```bash
python run_dev.py --check-only
```

### 2. 開発モードでThonnyを起動

#### Windows
```cmd
run_dev.bat
```

#### Linux/macOS
```bash
./run_dev.sh
```

#### Python直接実行
```bash
python run_dev.py
```

## 起動オプション

### 通常起動
```bash
python run_dev.py
```
プラグインを読み込んでThonnyを起動します。

### デバッグモード
```bash
python run_dev.py --debug
```
debugpyでポート5678で待機します。VS CodeやPyCharmからアタッチできます。

### 依存関係チェックのみ
```bash
python run_dev.py --check-only
```
必要なパッケージがインストールされているか確認します。

## VS Codeでのデバッグ

`.vscode/launch.json`に3つの設定を用意しています：

1. **Debug Thonny Plugin** - Thonnyを直接デバッグ起動
2. **Attach to Thonny** - `run_dev.py --debug`で起動したThonnyにアタッチ
3. **Run Tests** - pytestでテストを実行

### デバッグ手順

#### 方法1: 直接デバッグ
1. VS Codeで「Debug Thonny Plugin」を選択
2. F5キーでデバッグ開始
3. ブレークポイントが効きます

#### 方法2: アタッチデバッグ
1. ターミナルで`python run_dev.py --debug`を実行
2. VS Codeで「Attach to Thonny」を選択
3. F5キーでアタッチ
4. より安定したデバッグが可能

## プラグイン開発のワークフロー

### 1. コード編集
プラグインコードを編集：
```
thonnycontrib/thonny_local_ollama/
├── __init__.py    # load_plugin()
├── llm_client.py  # LLM統合
├── ui_widgets.py  # UIコンポーネント
└── config.py      # 設定管理
```

### 2. Thonnyで確認
1. 実行中のThonnyを閉じる（Ctrl+Q）
2. `run_dev.py`で再起動
3. 変更を確認

### 3. ログの確認
- **System Shell**: Thonny内のSystem Shellでprint出力を確認
- **ログファイル**: Tools → Open Thonny data folder → thonny.log

### 4. 高速な開発サイクル
```bash
# エイリアスを設定しておくと便利
alias tdev="python run_dev.py"
alias tdebug="python run_dev.py --debug"
```

## トラブルシューティング

### プラグインが読み込まれない
1. `thonnycontrib/thonny_local_ollama/__init__.py`が存在するか確認
2. `load_plugin()`関数が定義されているか確認
3. PYTHONPATHが正しく設定されているか確認

### インポートエラー
```python
# __init__.pyの最小構成
def load_plugin():
    import logging
    logging.info("Plugin loaded!")
```

### デバッグ出力の確認方法
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Debug message")  # System Shellに表示
```

## 便利なコマンド

### プラグインの再読み込み
Thonnyの再起動が最も確実ですが、開発中は以下のショートカットが便利：
- **Ctrl+Q** → **Enter**: Thonnyを終了
- **↑** → **Enter**: 前のコマンドを再実行

### モデルのテスト
```python
# Thonnyのシェルで実行
from thonnycontrib.thonny_local_ollama.llm_client import LLMClient
client = LLMClient()
client.test_connection()
```

## 推奨される開発環境

- **エディタ**: VS Code（launch.json設定済み）
- **Python**: 3.8以上
- **Thonny**: 4.0以上
- **デバッガ**: debugpy（VS Code統合）

このセットアップにより、効率的にプラグインを開発できます。