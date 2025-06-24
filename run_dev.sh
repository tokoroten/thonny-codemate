#!/bin/bash
# Linux/macOS用開発環境起動スクリプト

echo "========================================"
echo "Thonny Local LLM Plugin - Dev Runner"
echo "========================================"

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 仮想環境をアクティベート（存在する場合）
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Pythonスクリプトを実行
python3 run_dev.py "$@"