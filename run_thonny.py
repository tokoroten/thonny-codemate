#!/usr/bin/env python3
"""
Thonnyを起動するシンプルなスクリプト
uv run run_thonny.py で実行可能
"""
import sys
import subprocess

if __name__ == "__main__":
    # Thonnyを起動
    subprocess.run([sys.executable, "-m", "thonny"] + sys.argv[1:])