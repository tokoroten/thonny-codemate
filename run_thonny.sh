#!/bin/bash
# uvを使ってThonnyを起動する簡易スクリプト

# プロジェクトルートをPYTHONPATHに追加
export PYTHONPATH="$(pwd):$PYTHONPATH"

# uvでThonnyを実行
uv run thonny