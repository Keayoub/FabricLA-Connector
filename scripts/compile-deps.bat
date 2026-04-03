@echo off
REM Recompile requirements.txt from requirements.in using uv (fast Rust-based resolver)
REM Usage: scripts\compile-deps.bat
REM
REM uv is ~100x faster than pip-compile and produces identical output format.
REM Install uv: pip install uv  OR  winget install astral-sh.uv

echo Compiling requirements.txt from requirements.in...
uv pip compile requirements.in ^
    --generate-hashes ^
    --output-file requirements.txt ^
    --annotation-style line ^
    --python-version 3.11

if %ERRORLEVEL% EQU 0 (
    echo Done! requirements.txt updated.
) else (
    echo ERROR: uv pip compile failed. Make sure uv is installed: pip install uv
    exit /b 1
)
