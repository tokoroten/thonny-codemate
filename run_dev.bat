@echo off
REM Windows用開発環境起動スクリプト

echo ========================================
echo Thonny Local LLM Plugin - Dev Runner
echo ========================================

REM 仮想環境をアクティベート（存在する場合）
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Pythonスクリプトを実行
python run_dev.py %*

REM エラーレベルをチェック
if errorlevel 1 (
    echo.
    echo Error occurred. Press any key to exit...
    pause > nul
)