@echo off
REM Batch wrapper for build_pypi.ps1
REM This allows easier invocation from cmd.exe

echo.
echo ========================================
echo Building fabricla-connector Package
echo ========================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_pypi.ps1"
exit /b %errorlevel%
