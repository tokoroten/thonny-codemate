#!/usr/bin/env python3
"""
開発環境セットアップスクリプト
uvを使用して仮想環境と依存関係をセットアップします
"""
import subprocess
import sys
import platform
from pathlib import Path


def check_uv():
    """uvがインストールされているかチェック"""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, check=True, text=True)
        print(f"✓ {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_uv():
    """uvをインストール"""
    print("Installing uv...")
    
    if platform.system() == "Windows":
        print("\nPlease run this command in PowerShell as Administrator:")
        print('powershell -c "irm https://astral.sh/uv/install.ps1 | iex"')
        print("\nThen run this script again.")
        return False
    else:
        # Linux/macOS
        try:
            subprocess.run(
                "curl -LsSf https://astral.sh/uv/install.sh | sh",
                shell=True,
                check=True
            )
            print("✓ uv installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install uv")
            return False


def setup_virtual_env():
    """uvで仮想環境をセットアップ"""
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print("✓ Virtual environment already exists")
    else:
        print("Creating virtual environment with uv...")
        subprocess.run(["uv", "venv"], check=True)
        print("✓ Virtual environment created")


def install_dependencies():
    """依存関係をインストール"""
    print("\nInstalling dependencies with uv sync...")
    
    # uv syncで全ての依存関係をインストール（開発用エクストラを含む）
    subprocess.run(["uv", "sync", "--extra", "dev"], check=True)
    
    print("\n✓ All dependencies installed (including llama-cpp-python)")


def create_project_structure():
    """プロジェクト構造を作成"""
    print("\nCreating project structure...")
    
    # 必要なディレクトリを作成
    directories = [
        "thonnycontrib/thonny_codemate",
        "tests",
        "models",
        "docs_for_ai",
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # __init__.pyファイルを作成
    init_files = [
        "thonnycontrib/__init__.py",
        "thonnycontrib/thonny_codemate/__init__.py",
        "tests/__init__.py",
    ]
    
    for init_file in init_files:
        path = Path(init_file)
        if not path.exists():
            path.touch()
            print(f"Created: {init_file}")
    
    # 基本的なプラグインコードを作成
    plugin_init = Path("thonnycontrib/thonny_codemate/__init__.py")
    if plugin_init.stat().st_size == 0:  # ファイルが空の場合
        plugin_init.write_text('''"""Thonny Local LLM Plugin"""

def load_plugin():
    """Thonnyが呼び出すプラグインエントリポイント"""
    from thonny import get_workbench
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Thonny Local LLM Plugin loading...")
    
    try:
        # TODO: プラグインの初期化を実装
        logger.info("Thonny Local LLM Plugin loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load plugin: {e}")
''')
        print("Created basic plugin structure")


def show_next_steps():
    """次のステップを表示"""
    print("\n" + "="*50)
    print("✅ Setup completed!")
    print("="*50)
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    if platform.system() == "Windows":
        print("   .venv\\Scripts\\activate")
    else:
        print("   source .venv/bin/activate")
    print("\n2. Run Thonny in development mode:")
    print("   python run_dev.py")
    print("\n3. Run Thonny with debugging:")
    print("   python run_dev.py --debug")
    print("\n4. Check the DEV_SETUP.md for more details")


def main():
    """メイン処理"""
    print("="*50)
    print("Thonny Local LLM Plugin - Development Setup")
    print("="*50)
    
    # uvのチェックとインストール
    if not check_uv():
        print("✗ uv not found")
        if not install_uv():
            sys.exit(1)
        # uvがインストールされたら再度チェック
        if not check_uv():
            print("\nuv is not in PATH. Please restart your terminal and run this script again.")
            sys.exit(1)
    
    # 仮想環境のセットアップ
    setup_virtual_env()
    
    # 依存関係のインストール
    install_dependencies()
    
    # プロジェクト構造の作成
    create_project_structure()
    
    # 次のステップを表示
    show_next_steps()


if __name__ == "__main__":
    main()