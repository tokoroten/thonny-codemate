# GGUF変換ガイド

## 概要

このガイドでは、Hugging Faceからダウンロードした通常のモデルをGGUF形式に変換する方法を説明します。

## 必要なツール

### 1. llama.cpp のインストール

```bash
# リポジトリをクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド（Linux/macOS）
make

# ビルド（Windows）
# Visual Studio または MinGW が必要
cmake -B build
cmake --build build --config Release
```

### 2. Python依存関係のインストール

```bash
pip install -r requirements.txt
```

## 変換手順

### ステップ1: モデルのダウンロード

```bash
# Hugging Face CLIを使用
pip install huggingface-hub

# モデルをダウンロード
huggingface-cli download future-architect/Llama-3.1-Future-Code-Ja-8B \
  --local-dir ./models/Llama-3.1-Future-Code-Ja-8B
```

### ステップ2: GGUF形式への変換

```bash
# llama.cppディレクトリに移動
cd llama.cpp

# 変換スクリプトを実行
python convert_hf_to_gguf.py \
  ../models/Llama-3.1-Future-Code-Ja-8B \
  --outfile ../models/Llama-3.1-Future-Code-Ja-8B-f16.gguf \
  --outtype f16
```

### ステップ3: 量子化（オプション）

より小さいファイルサイズにするため、量子化を行います：

```bash
# Q4_K_M量子化（推奨：品質とサイズのバランスが良い）
./llama-quantize \
  ../models/Llama-3.1-Future-Code-Ja-8B-f16.gguf \
  ../models/Llama-3.1-Future-Code-Ja-8B-Q4_K_M.gguf \
  Q4_K_M

# その他の量子化オプション
# Q2_K    - 最小サイズ（品質低下）
# Q3_K_S  - 小サイズ
# Q3_K_M  - 小サイズ（より良い品質）
# Q3_K_L  - 小サイズ（最高品質）
# Q4_0    - 古い形式
# Q4_K_S  - 中サイズ
# Q4_K_M  - 中サイズ（推奨）
# Q5_0    - 古い形式
# Q5_K_S  - 大サイズ
# Q5_K_M  - 大サイズ（より良い品質）
# Q6_K    - 大サイズ（最高品質）
# Q8_0    - ほぼ元のサイズ
```

## 自動変換スクリプト

以下は変換を自動化するPythonスクリプトです：

```python
#!/usr/bin/env python3
"""
GGUF変換ヘルパースクリプト
"""
import subprocess
import sys
from pathlib import Path

def convert_to_gguf(model_path: str, output_path: str, quantization: str = "Q4_K_M"):
    """モデルをGGUF形式に変換"""
    
    model_path = Path(model_path)
    output_path = Path(output_path)
    
    # llama.cppのパスを確認
    llama_cpp_path = Path("llama.cpp")
    if not llama_cpp_path.exists():
        print("Error: llama.cpp not found. Please clone it first:")
        print("git clone https://github.com/ggerganov/llama.cpp")
        sys.exit(1)
    
    # 一時的なf16ファイル
    temp_f16 = output_path.parent / f"{output_path.stem}-f16.gguf"
    
    # Step 1: HFからGGUF（f16）への変換
    print("Converting to GGUF format...")
    cmd = [
        sys.executable,
        str(llama_cpp_path / "convert_hf_to_gguf.py"),
        str(model_path),
        "--outfile", str(temp_f16),
        "--outtype", "f16"
    ]
    subprocess.run(cmd, check=True)
    
    # Step 2: 量子化
    print(f"Quantizing to {quantization}...")
    quantize_exe = llama_cpp_path / "llama-quantize"
    if sys.platform == "win32":
        quantize_exe = quantize_exe.with_suffix(".exe")
    
    cmd = [
        str(quantize_exe),
        str(temp_f16),
        str(output_path),
        quantization
    ]
    subprocess.run(cmd, check=True)
    
    # 一時ファイルを削除
    temp_f16.unlink()
    
    print(f"Conversion complete: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_to_gguf.py <model_path> <output_path> [quantization]")
        print("Example: python convert_to_gguf.py ./models/Llama-3.1-Future-Code-Ja-8B ./models/Llama-3.1-Future-Code-Ja-8B-Q4_K_M.gguf Q4_K_M")
        sys.exit(1)
    
    model_path = sys.argv[1]
    output_path = sys.argv[2]
    quantization = sys.argv[3] if len(sys.argv) > 3 else "Q4_K_M"
    
    convert_to_gguf(model_path, output_path, quantization)
```

## トラブルシューティング

### メモリ不足エラー

大きなモデルの変換にはかなりのRAMが必要です。以下の対策を試してください：

1. スワップファイルを増やす
2. より小さい量子化レベルを使用（Q2_K、Q3_K_S）
3. クラウドサービスまたは高スペックマシンを使用

### 変換エラー

- モデルの形式がサポートされていない場合があります
- llama.cppを最新版にアップデート：`git pull && make clean && make`
- Python依存関係を再インストール：`pip install -r requirements.txt --upgrade`

## 推奨事項

1. **ディスク容量**: 元のモデルの3倍以上の空き容量を確保
2. **RAM**: 最低16GB、推奨32GB以上
3. **時間**: 8Bモデルの変換には30分〜1時間程度かかる場合があります

## 参考リンク

- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [GGUF形式の詳細](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)
- [量子化の比較](https://github.com/ggerganov/llama.cpp/discussions/2094)