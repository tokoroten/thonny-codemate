# Thonnyプラグイン実装に必要な要素技術

## 1. エディタの操作とロック機能

### エディタへのアクセス方法
```python
from thonny import get_workbench

# 現在のエディタを取得
workbench = get_workbench()
editor = workbench.get_editor_notebook().get_current_editor()
if editor:
    text_widget = editor.get_text_widget()  # tkinter Textウィジェット
```

### エディタのロック/アンロック
```python
# エディタをロック（編集を禁止）
text_widget.config(state=tk.DISABLED)  # または state="disabled"

# エディタをアンロック（編集を許可）
text_widget.config(state=tk.NORMAL)    # または state="normal"
```

### プログラムによるコード書き換え
```python
# ロックされている場合は一時的にアンロック
text_widget.config(state=tk.NORMAL)

# テキストの取得
current_content = text_widget.get("1.0", tk.END)

# テキストの挿入
text_widget.insert("1.0", "# AI generated code\n")  # 先頭に挿入
text_widget.insert(tk.END, "\n# End of code")       # 末尾に追加

# テキストの削除と置換
text_widget.delete("1.0", tk.END)  # 全削除
text_widget.insert("1.0", new_content)  # 新しい内容を挿入

# 再度ロック
text_widget.config(state=tk.DISABLED)
```

## 2. コンテキストメニューの実装

### 選択テキストの検出
```python
def _has_selection(widget):
    """Textウィジェットがテキスト選択を持っているかチェック"""
    if not isinstance(widget, tk.Text):
        return False
    try:
        return bool(widget.tag_ranges("sel"))
    except:
        return False
```

### 選択テキストの取得
```python
if widget.tag_ranges("sel"):
    selected_text = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
```

### コンテキストメニューの追加方法

#### 方法1: 独自のコンテキストメニュー
```python
from tkinter import Menu

# メニューを作成
context_menu = Menu(text_widget, tearoff=0)
context_menu.add_command(label="コード解説", command=explain_handler)

# 右クリックイベントをバインド
if sys.platform == "darwin":  # macOS
    text_widget.bind("<Button-2>", show_context_menu, add='+')
    text_widget.bind("<Control-Button-1>", show_context_menu, add='+')
else:  # Windows/Linux
    text_widget.bind("<Button-3>", show_context_menu, add='+')

def show_context_menu(event):
    context_menu.tk_popup(event.x_root, event.y_root)
```

#### 方法2: Thonnyのメニューに統合
```python
workbench.add_command(
    command_id="explain_selection",
    menu_name="edit",
    command_label="コード解説 (AI)",
    handler=explain_handler,
    group=80  # メニュー内の位置
)
```

#### 方法3: モンキーパッチング（高度）
```python
# 既存のShellMenuクラスを拡張
import thonny.shell

OriginalShellMenu = thonny.shell.ShellMenu

class CustomShellMenu(OriginalShellMenu):
    def add_extra_items(self):
        super().add_extra_items()
        self.add_separator()
        self.add_command(
            label="🤖コード解説",
            command=self.explain_selection
        )

# パッチを適用
thonny.shell.ShellMenu = CustomShellMenu
```

## 3. プラグイン構造の基本

### 必須ディレクトリ構造
```
thonnycontrib/
└── plugin_name/
    └── __init__.py  # load_plugin()関数が必須
```

### load_plugin()の実装
```python
def load_plugin():
    """Thonnyが呼び出すエントリポイント"""
    from thonny import get_workbench
    
    try:
        workbench = get_workbench()
        
        # ビューを登録
        from .views import AssistantView
        workbench.add_view(
            AssistantView,
            "AI Assistant",
            "se",  # 位置: south-east
            view_id="AIAssistantView"
        )
        
        # コマンドを登録
        workbench.add_command(
            command_id="show_ai_assistant",
            menu_name="tools",
            command_label="AI Assistant",
            handler=show_assistant_handler
        )
        
    except Exception as e:
        import logging
        logging.error(f"Failed to load plugin: {e}")
```

## 4. 非同期処理とスレッディング

### モデル読み込みの非同期化
```python
import threading
import queue

class LLMClient:
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.loading_queue = queue.Queue()
    
    def load_model_async(self):
        """バックグラウンドでモデルを読み込む"""
        thread = threading.Thread(target=self._load_model)
        thread.daemon = True
        thread.start()
    
    def _load_model(self):
        try:
            from llama_cpp import Llama
            self.model = Llama(
                model_path="path/to/model.gguf",
                n_ctx=4096,
                n_gpu_layers=0  # CPU only
            )
            self.model_loaded = True
            self.loading_queue.put(("success", None))
        except Exception as e:
            self.loading_queue.put(("error", str(e)))
```

### UI更新の非同期処理
```python
def update_ui_from_thread():
    """スレッドからUIを安全に更新"""
    workbench.get_root().after(0, lambda: ui_update_function())
```

## 5. 設定管理

### Thonnyの設定システムを使用
```python
from thonny import get_workbench

# 設定を保存
workbench = get_workbench()
workbench.set_option("thonny_local_ollama.model_path", "/path/to/model.gguf")
workbench.set_option("thonny_local_ollama.skill_level", "beginner")

# 設定を読み込み
model_path = workbench.get_option("thonny_local_ollama.model_path", default="")
skill_level = workbench.get_option("thonny_local_ollama.skill_level", default="beginner")
```

### カスタムJSON設定ファイル
```python
import json
import os
from pathlib import Path

class Config:
    def __init__(self):
        self.config_path = Path.home() / ".thonny_local_ollama" / "config.json"
        self.load()
    
    def load(self):
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = self.get_defaults()
    
    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.data, f, indent=2)
```

## 6. UIコンポーネントの実装

### 基本的なビュークラス
```python
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

class AssistantView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.init_ui()
    
    def init_ui(self):
        # チャット表示エリア
        self.chat_display = ScrolledText(self, wrap=tk.WORD)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # 入力エリア
        self.input_frame = ttk.Frame(self)
        self.input_frame.pack(fill=tk.X)
        
        self.input_text = tk.Text(self.input_frame, height=3)
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.send_button = ttk.Button(
            self.input_frame,
            text="送信",
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT)
```

## 7. ストリーミング応答の実装

```python
import queue
import threading

class StreamingHandler:
    def __init__(self, display_widget):
        self.display_widget = display_widget
        self.response_queue = queue.Queue()
        self.streaming = False
    
    def stream_response(self, prompt):
        """ストリーミング応答を開始"""
        self.streaming = True
        thread = threading.Thread(
            target=self._generate_stream,
            args=(prompt,)
        )
        thread.daemon = True
        thread.start()
        
        # UIを定期的に更新
        self._update_display()
    
    def _generate_stream(self, prompt):
        """バックグラウンドでトークンを生成"""
        for token in self.model.generate_tokens(prompt):
            if not self.streaming:
                break
            self.response_queue.put(token)
        self.response_queue.put(None)  # 終了シグナル
    
    def _update_display(self):
        """キューからトークンを取得してUIを更新"""
        try:
            while True:
                token = self.response_queue.get_nowait()
                if token is None:
                    self.streaming = False
                    break
                self.display_widget.insert(tk.END, token)
        except queue.Empty:
            pass
        
        if self.streaming:
            self.display_widget.after(50, self._update_display)
```

## 8. エラー処理とロギング

```python
import logging

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Thonnyのロギングシステムに統合
from thonny import get_workbench
workbench = get_workbench()
# ログはSystem Shellとthonny.logに出力される

# エラー処理の例
try:
    # 危険な操作
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    # ユーザーへの通知
    from tkinter import messagebox
    messagebox.showerror(
        "エラー",
        f"操作が失敗しました: {str(e)}"
    )
```

## 9. プラットフォーム対応

```python
import sys
import platform

def get_platform_specific_path():
    if sys.platform == "win32":
        return Path.home() / "AppData" / "Local" / "thonny_local_ollama"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "thonny_local_ollama"
    else:  # Linux
        return Path.home() / ".config" / "thonny_local_ollama"

# マウスボタンのプラットフォーム対応
def bind_context_menu(widget):
    if platform.system() == "Darwin":  # macOS
        widget.bind("<Button-2>", show_menu)
        widget.bind("<Control-Button-1>", show_menu)
    else:  # Windows/Linux
        widget.bind("<Button-3>", show_menu)
```

## 10. 遅延読み込み（Lazy Loading）の実装

```python
class LLMClient:
    def __init__(self):
        self._model = None
        self._loading = False
        self._load_lock = threading.Lock()
    
    @property
    def model(self):
        """モデルへの最初のアクセス時に読み込む"""
        if self._model is None and not self._loading:
            with self._load_lock:
                if self._model is None and not self._loading:
                    self._loading = True
                    self._load_model()
        return self._model
    
    def _load_model(self):
        """実際のモデル読み込み処理"""
        try:
            from llama_cpp import Llama
            self._model = Llama(
                model_path=self.get_model_path(),
                n_ctx=4096
            )
        finally:
            self._loading = False
```

これらの要素技術を組み合わせることで、Thonny用のローカルLLMプラグインを実装できます。