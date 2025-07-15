#!/usr/bin/env python3
"""
GGUF変換ヘルパースクリプト
Future-Code-Ja-8Bなど、GGUF形式で提供されていないモデルを変換するためのツール
"""
import subprocess
import sys
import os
from pathlib import Path
import shutil
import tempfile

def check_llama_cpp():
    """llama.cppがインストールされているか確認"""
    llama_cpp_path = Path("llama.cpp")
    if not llama_cpp_path.exists():
        print("❌ llama.cppが見つかりません。")
        print("\n以下のコマンドでインストールしてください:")
        print("git clone https://github.com/ggerganov/llama.cpp")
        print("cd llama.cpp")
        print("make  # Linux/macOS")
        print("# または")
        print("cmake -B build && cmake --build build --config Release  # Windows")
        return False
    return True

def download_model(model_id: str, output_dir: Path):
    """Hugging Faceからモデルをダウンロード"""
    print(f"📥 モデルをダウンロード中: {model_id}")
    
    # huggingface-hubがインストールされているか確認
    try:
        import huggingface_hub
    except ImportError:
        print("❌ huggingface-hubがインストールされていません。")
        print("pip install huggingface-hub")
        return None
    
    try:
        # スナップショットダウンロード
        from huggingface_hub import snapshot_download
        local_dir = output_dir / model_id.replace("/", "_")
        
        snapshot_download(
            repo_id=model_id,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False
        )
        
        print(f"✅ ダウンロード完了: {local_dir}")
        return local_dir
    except Exception as e:
        print(f"❌ ダウンロードエラー: {e}")
        return None

def convert_to_gguf(model_path: Path, output_path: Path, quantization: str = "Q4_K_M"):
    """モデルをGGUF形式に変換"""
    
    llama_cpp_path = Path("llama.cpp")
    
    # 一時的なf16ファイル
    temp_f16 = output_path.parent / f"{output_path.stem}-f16.gguf"
    
    try:
        # Step 1: HFからGGUF（f16）への変換
        print(f"\n🔄 GGUF形式に変換中...")
        convert_script = llama_cpp_path / "convert_hf_to_gguf.py"
        
        if not convert_script.exists():
            # 新しいバージョンのllama.cppでは名前が変わっている可能性
            convert_script = llama_cpp_path / "convert.py"
        
        cmd = [
            sys.executable,
            str(convert_script),
            str(model_path),
            "--outfile", str(temp_f16),
            "--outtype", "f16"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ 変換エラー: {result.stderr}")
            return False
        
        # Step 2: 量子化
        print(f"\n🔄 量子化中 ({quantization})...")
        quantize_exe = llama_cpp_path / "llama-quantize"
        if sys.platform == "win32":
            quantize_exe = quantize_exe.with_suffix(".exe")
        
        if not quantize_exe.exists():
            # ビルドされていない可能性
            print(f"❌ {quantize_exe} が見つかりません。llama.cppをビルドしてください。")
            return False
        
        cmd = [
            str(quantize_exe),
            str(temp_f16),
            str(output_path),
            quantization
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ 量子化エラー: {result.stderr}")
            return False
        
        print(f"✅ 変換完了: {output_path}")
        return True
        
    finally:
        # 一時ファイルを削除
        if temp_f16.exists():
            temp_f16.unlink()

def convert_future_code_ja():
    """Future-Code-Ja-8Bモデルを変換"""
    print("🚀 Llama-3.1-Future-Code-Ja-8B GGUF変換ツール")
    print("=" * 50)
    
    # llama.cppの確認
    if not check_llama_cpp():
        return
    
    # 出力ディレクトリ
    output_dir = Path("models")
    output_dir.mkdir(exist_ok=True)
    
    # モデルIDとファイル名
    model_id = "future-architect/Llama-3.1-Future-Code-Ja-8B"
    output_filename = "Llama-3.1-Future-Code-Ja-8B-Q4_K_M.gguf"
    output_path = output_dir / output_filename
    
    # 既に変換済みか確認
    if output_path.exists():
        print(f"✅ 既に変換済みです: {output_path}")
        response = input("再変換しますか？ (y/N): ")
        if response.lower() != 'y':
            return
    
    # モデルをダウンロード
    model_path = download_model(model_id, Path("temp_models"))
    if not model_path:
        return
    
    # 変換実行
    print("\n" + "=" * 50)
    print("変換を開始します。これには時間がかかる場合があります...")
    print("必要なRAM: 約16GB以上")
    print("必要なディスク容量: 約20GB以上")
    print("=" * 50)
    
    success = convert_to_gguf(model_path, output_path)
    
    # 一時ファイルを削除
    if model_path.parent.name == "temp_models":
        shutil.rmtree(model_path.parent, ignore_errors=True)
    
    if success:
        print(f"\n🎉 変換が完了しました！")
        print(f"📁 出力ファイル: {output_path}")
        print(f"📏 ファイルサイズ: {output_path.stat().st_size / (1024**3):.2f} GB")
        print(f"\nThonny Codemateで使用できます。")
    else:
        print(f"\n❌ 変換に失敗しました。")

def main():
    """メイン処理"""
    if len(sys.argv) > 1:
        # カスタムモデルの変換
        if len(sys.argv) < 3:
            print("使用方法: python convert_to_gguf.py <model_path> <output_path> [quantization]")
            print("例: python convert_to_gguf.py ./models/my-model ./models/my-model-Q4_K_M.gguf Q4_K_M")
            sys.exit(1)
        
        model_path = Path(sys.argv[1])
        output_path = Path(sys.argv[2])
        quantization = sys.argv[3] if len(sys.argv) > 3 else "Q4_K_M"
        
        if not check_llama_cpp():
            sys.exit(1)
        
        success = convert_to_gguf(model_path, output_path, quantization)
        sys.exit(0 if success else 1)
    else:
        # デフォルト: Future-Code-Ja-8Bを変換
        convert_future_code_ja()

if __name__ == "__main__":
    main()