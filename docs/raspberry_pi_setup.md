# Raspberry Pi Setup Guide

## 推奨構成

### ハードウェア要件
- **最小**: Raspberry Pi 4 (4GB RAM)
- **推奨**: Raspberry Pi 4/5 (8GB RAM)
- **ストレージ**: 32GB以上のSDカード

### インストール方法

#### 1. 外部APIのみを使用する場合（推奨）

Raspberry Piのリソース制限により、ローカルLLMではなく外部APIの使用を推奨します：

```bash
# 基本インストール（外部APIのみ）
pip install thonny-codemate --no-deps
pip install thonny>=4.0.0 tkinterweb markdown pygments openai

# または external-only オプション
pip install thonny-codemate[external-only]
```

#### 2. ローカルLLMを使用する場合（非推奨）

```bash
# ARM用にllama-cpp-pythonをビルド
CMAKE_ARGS="-DLLAMA_NATIVE=off -DLLAMA_BLAS=off" pip install llama-cpp-python

# その後、プラグインをインストール
pip install thonny-codemate
```

### 設定推奨

1. **プロバイダー選択**
   - ChatGPT、OpenRouter、Ollamaサーバー（別マシン）を推奨
   - ローカルLLMは避ける

2. **Ollamaサーバーの外部化**
   ```python
   # 別のマシンでOllamaを実行
   # Raspberry Piからは以下のように接続
   Host: 192.168.1.100  # Ollamaサーバーのアドレス
   Port: 11434
   ```

3. **軽量モデルの選択**（外部APIを使用する場合）
   - OpenRouter: `mistralai/mistral-7b-instruct:free`
   - ChatGPT: `gpt-4o-mini`

### パフォーマンス最適化

1. **不要な依存関係を除外**
   ```bash
   # pythonmonkeyとllama-cpp-pythonを除外してインストール
   pip install thonny>=4.0.0 huggingface-hub markdown pygments openai
   ```

2. **メモリ使用量の削減**
   - Max Tokensを小さく設定（512-1024）
   - Context Sizeを小さく設定（2048）

### トラブルシューティング

#### pythonmonkey のインストールエラー
```bash
# 代替として、JavaScriptなしでインストール
pip install tkinterweb --no-deps
pip install tkinterweb
```

#### メモリ不足エラー
- スワップファイルを増やす
- 他のプロセスを停止
- 外部APIを使用

### 制限事項

1. **ローカルLLM実行は非現実的**
   - 推論速度が極めて遅い（分単位）
   - メモリ不足でクラッシュの可能性

2. **UI応答性の低下**
   - tkinterwebのレンダリングが遅い可能性
   - 簡易表示モードの使用を推奨

## 代替案

### 1. Raspberry PiをクライアントとしてIを使用
- 別のPCでOllamaサーバーを実行
- Raspberry Piから接続

### 2. 軽量版の開発
- tkinterwebを使わないシンプルなUI
- 外部API専用モード

### 3. SSH + リモート開発
- Raspberry PiでThonnyを実行
- 開発はSSH経由で別PCから