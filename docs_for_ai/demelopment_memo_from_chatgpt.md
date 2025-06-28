
# ChatGPTから得た開発メモ

## PythonからOllama/llama.cppを使う方法まとめ

### 1. Ollamaサーバを使う方法

- [Ollama公式](https://github.com/ollama/ollama)のサーバ（`ollama serve`）を起動し、[ollama-python](https://github.com/ollama/ollama-python)クライアントでアクセス
- サーバが未起動なら `subprocess.Popen(["ollama", "serve"])` で裏で立ち上げることも可能

#### サンプルコード

```python
from ollama import chat

resp = chat(
    model='llama3',
    messages=[{'role':'user', 'content':'日本語で自己紹介して'}]
)
print(resp.message.content)
```

- **メリット**: Ollamaの全機能（ストリーミング、埋め込み、モデル管理）が利用可能
- **デメリット**: バイナリ同梱が必要、別プロセス通信のオーバーヘッドあり

---

### 2. llama-cpp-pythonでGGUFを直接ロード（バイナリ不要）

- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)を使い、GGUFファイルを直接ロード
- 完全な純粋Pythonは不可。C/C++ビルドは必要

#### モデル（.gguf）の準備

- Ollamaでpull済みなら `~/.ollama/models/blobs/` 以下に`.gguf`がある
- ない場合は [Hugging Face](https://huggingface.co/) などからダウンロード

#### パッケージのインストール

- CPU版（公式Wheel）:  
  ```powershell
  pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
  ```
  [公式リリースノート](https://github.com/abetlen/llama-cpp-python/releases)

- CUDA版（公式Wheel）:  
  ```powershell
  pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
  ```
  [CUDA対応Wheel一覧](https://abetlen.github.io/llama-cpp-python/whl/)

- CUDA版（コミュニティWheel）:  
  ```powershell
  python -m pip install llama-cpp-python --prefer-binary --extra-index-url=https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu117
  ```
  [jllllll/llama-cpp-python-cuBLAS-wheels](https://github.com/jllllll/llama-cpp-python-cuBLAS-wheels)

#### 推論サンプル

```python
from llama_cpp import Llama

llm = Llama(
    model_path="path/to/llama3.Q4_K_M.gguf",
    n_ctx=4096,           # 上限トークン長
    n_gpu_layers=50       # GPUオフロード層数（CPUのみなら0）
)

print(llm("こんにちは。自己紹介してください。", max_tokens=128))
```

- チャット履歴のフォーマットやRAG用の埋め込み生成は自前実装が必要

---

### 3. GGUFモデルをHugging Faceからダウンロードする方法

#### CLIでダウンロード

- [huggingface_hub CLI](https://huggingface.co/docs/huggingface_hub/quick-start#download-files-with-the-cli)をインストール
  ```powershell
  pip install -U "huggingface_hub[cli]"
  huggingface-cli login  # 必要ならトークン入力
  ```
- 単一ファイル取得例
  ```powershell
  huggingface-cli download TheBloke/Llama-3-8B-GGUF llama3-8b.Q4_K_M.gguf --local-dir ./models --local-dir-use-symlinks False
  ```
- 複数ファイルをパターンでまとめて
  ```powershell
  huggingface-cli download TheBloke/Llama-3-8B-GGUF --include "*Q4_*gguf" --local-dir ./models
  ```

#### Pythonスクリプトでダウンロード

- [huggingface_hub](https://github.com/huggingface/huggingface_hub)を利用

```python
from huggingface_hub import hf_hub_download, snapshot_download

# 単一ファイル
def download_single():
    path = hf_hub_download(
        repo_id="TheBloke/Llama-3-8B-GGUF",
        filename="llama3-8b.Q4_K_M.gguf",
        local_dir="models"
    )
    print(path)

# パターンでまとめて
def download_pattern():
    snapshot_download(
        repo_id="TheBloke/Llama-3-8B-GGUF",
        allow_patterns="*Q4_*gguf",
        local_dir="models"
    )
```

#### 高速化オプション

- [hf_transfer](https://github.com/huggingface/hf_transfer)を使うと高速化可能
  ```powershell
  pip install "huggingface_hub[hf_transfer]"
  set HF_HUB_ENABLE_HF_TRANSFER=1
  ```

---

## Thonnyプラグイン開発のおすすめ開発体制・デバッグ手法

### 結論（最速手順）
- 仮想環境を1つ作り、Thonny本体もプラグインもeditable（`pip install -e`）でインストール
- Thonnyをその仮想環境から `python -m thonny` で起動
- 普段の開発はVS CodeやPyCharmなど外部IDEで行い、`debugpy`を使ってThonnyプロセスにアタッチしてブレークポイントを張る
- print/loggingの出力は「Tools → Open Thonny data folder…」配下の`thonny.log`と「System Shell」ウインドウで即座に確認
- UI変更を試すときはThonnyを再起動（Ctrl+Q→Enter）するのが最速

### 1. ディレクトリ構成例

```
my_thonny_plugin/
├── pyproject.toml         # build backendはhatchling/poetryなどで可
├── README.md
└── thonnycontrib/
    └── myplugin/
        ├── __init__.py    # load_plugin() を実装
        └── widgets.py ...
```
- Thonnyのプラグインは`thonnycontrib`名前空間に置き、起動時に呼ばれる`load_plugin()`を用意するだけで認識される
- editableインストールしておけばファイルを保存→Thonny再起動だけで反映される

#### セットアップ例
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -U pip
# Thonny本体も最新版を開発用に
git clone https://github.com/thonny/thonny.git
pip install -e ./thonny            # Thonnyを開発モードで
pip install -e ./my_thonny_plugin  # 作成中のプラグイン
```
- ThonnyはPYTHONPATHにプロジェクトを入れるだけでも可（公式wikiより）
- ただしeditableの方がIDEから補完が効きやすいのでおすすめ

### 2. Thonnyをデバッグ起動するワンライナー

```bash
python -m debugpy --listen 5678 --wait-for-client -m thonny
```
- 先にVS Code/PyCharmでポート5678にアタッチする設定を作り、BreakPointを置けばプラグインのコードでも普通に停止してステップ実行できる
- デバッガ待受を外したいときは`thonny`だけで起動し、内蔵デバッガ（Ctrl+F5＝nicer / Shift+F5＝faster）を使う
- 2種類のモードは[公式ブログ](https://thonny.org/blog/)で解説あり

### 3. ログと標準出力

```python
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```
- loggingはそのままSystem shellに流れるので動的情報の確認が高速
- さらに詳細な起動ログはTools→Open Thonny data folder…内の`thonny.log`を見る
- Gitでコミットするときに`.log*`を無視すれば汚れない

### 4. 再起動を最小コストにするテクニック

| 操作 | キー | メモ |
|------|-----|------|
| Thonnyを閉じる | Ctrl+Q | ダイアログが出るのでEnterで即終了 |
| 直前と同じコマンドで再起動 | ↑（履歴） | zsh/fishなら`!!`でも可 |
| バックエンドのみ再起動 | Ctrl+F2 | マイコン接続時の固まり解消にも便利 |

- 再起動1〜2秒＋editable反映だけなら、ホットリロード機構を自作するより早いことが多い

### 5. 単体テストも忘れずに
- UI以外のロジックはpytestで普通にテスト可能

```bash
pip install pytest
pytest -q
```
- プラグイン部分はモックで`thonny.get_workbench()`を差し替えておけばCI上でも安全に動作

---

#### まとめ
- 仮想環境＋editableで同じPythonをThonnyと共有
- 外部IDEのリモートデバッガattachが一番ストレスが少ない
- System shell & logファイルでprint/ログ確認
- Thonny再起動をショートカット化してUI変更をすばやく試す

これだけで「コード編集→再起動→動作確認」のループが5秒以内に収まるようになります。
プラグイン開発、楽しんでください！