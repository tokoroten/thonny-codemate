#!/usr/bin/env python3
"""
開発用Thonny起動スクリプト
開発中のプラグインを自動的に読み込んでThonnyを起動します
"""
import os
import sys
import subprocess
from pathlib import Path

# プロジェクトルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.absolute()
PLUGIN_DIR = PROJECT_ROOT / "thonnycontrib"

def setup_development_environment():
    """開発環境をセットアップ"""
    # プロジェクトルートをPYTHONPATHに追加
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    
    # 環境変数を設定
    env = os.environ.copy()
    
    # PYTHONPATHにプロジェクトルートを追加
    pythonpath = env.get('PYTHONPATH', '')
    if pythonpath:
        env['PYTHONPATH'] = f"{PROJECT_ROOT}{os.pathsep}{pythonpath}"
    else:
        env['PYTHONPATH'] = str(PROJECT_ROOT)
    
    # デバッグモードを有効化（オプション）
    env['THONNY_DEBUG'] = '1'
    
    return env

def check_uv():
    """uvがインストールされているかチェック"""
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_with_uv():
    """uvを使用して依存関係をインストール"""
    if not check_uv():
        print("✗ uv not found. Please install uv first:")
        print("  Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
        print("  Linux/macOS: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False
    
    print("Installing dependencies with uv...")
    
    # uvで仮想環境を作成（存在しない場合）
    if not Path(".venv").exists():
        subprocess.run(["uv", "venv"], check=True)
    
    # 依存関係をインストール
    subprocess.run(["uv", "pip", "install", "thonny"], check=True)
    
    # llama-cpp-pythonをインストール
    subprocess.run([
        "uv", "pip", "install", "llama-cpp-python",
        "--extra-index-url", "https://abetlen.github.io/llama-cpp-python/whl/cpu"
    ], check=True)
    
    return True

def check_dependencies():
    """必要な依存関係をチェック"""
    # uvが利用可能な場合は優先的に使用
    if check_uv() and not Path(".venv").exists():
        print("Creating virtual environment with uv...")
        install_with_uv()
    
    try:
        import thonny
        print(f"✓ Thonny {thonny.get_version()} found")
    except ImportError:
        print("✗ Thonny not found. Installing...")
        if check_uv():
            subprocess.check_call(["uv", "pip", "install", "thonny"])
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "thonny"])
    
    try:
        import llama_cpp
        print("✓ llama-cpp-python found")
    except ImportError:
        print("✗ llama-cpp-python not found")
        print("  To install CPU version:")
        if check_uv():
            print("  uv pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu")
        else:
            print("  pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu")

def run_thonny(debug_mode=False):
    """Thonnyを起動"""
    env = setup_development_environment()
    
    if debug_mode:
        # デバッグモードで起動（VS Codeなどからアタッチ可能）
        cmd = [
            sys.executable,
            "-m", "debugpy",
            "--listen", "5678",
            "--wait-for-client",
            "-m", "thonny"
        ]
        print("Starting Thonny in debug mode (waiting for debugger on port 5678)...")
    else:
        # 通常モードで起動
        cmd = [sys.executable, "-m", "thonny"]
        print("Starting Thonny in development mode...")
    
    print(f"PYTHONPATH: {env['PYTHONPATH']}")
    print(f"Working directory: {os.getcwd()}")
    
    # Thonnyを起動
    subprocess.run(cmd, env=env)

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="開発用Thonny起動スクリプト")
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="デバッグモードで起動（debugpyを使用）"
    )
    parser.add_argument(
        "--check-only", "-c",
        action="store_true",
        help="依存関係のチェックのみ実行"
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("Thonny Local LLM Plugin - Development Runner")
    print("=" * 50)
    
    # 依存関係をチェック
    check_dependencies()
    
    if args.check_only:
        return
    
    # プラグインディレクトリの存在確認
    if not PLUGIN_DIR.exists():
        print(f"\n⚠️  Plugin directory not found: {PLUGIN_DIR}")
        print("Creating plugin structure...")
        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        (PLUGIN_DIR / "thonny_local_ollama").mkdir(exist_ok=True)
        init_file = PLUGIN_DIR / "thonny_local_ollama" / "__init__.py"
        if not init_file.exists():
            init_file.write_text('''"""Thonny Local LLM Plugin"""

def load_plugin():
    """Thonnyが呼び出すプラグインエントリポイント"""
    import logging
    logging.info("Thonny Local LLM Plugin loaded!")
    # TODO: Implement plugin initialization
''')
            print(f"Created: {init_file}")
    
    print("\n")
    
    # Thonnyを起動
    try:
        run_thonny(debug_mode=args.debug)
    except KeyboardInterrupt:
        print("\nThonny terminated by user")
    except Exception as e:
        print(f"\nError running Thonny: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())