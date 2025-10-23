@echo off
REM Batch wrapper for release.ps1
REM This allows easier invocation from cmd.exe

if "%1"=="" (
    echo Error: Version number required
    echo Usage: release.bat VERSION [/push] [/build] [/force]
    echo Example: release.bat 1.0.1 /push /build
    exit /b 1
)

set PS_ARGS=-NewVersion %1
if /i "%2"=="/push" set PS_ARGS=%PS_ARGS% -Push
if /i "%3"=="/push" set PS_ARGS=%PS_ARGS% -Push
if /i "%4"=="/push" set PS_ARGS=%PS_ARGS% -Push
if /i "%2"=="/build" set PS_ARGS=%PS_ARGS% -Build
if /i "%3"=="/build" set PS_ARGS=%PS_ARGS% -Build
if /i "%4"=="/build" set PS_ARGS=%PS_ARGS% -Build
if /i "%2"=="/force" set PS_ARGS=%PS_ARGS% -Force
if /i "%3"=="/force" set PS_ARGS=%PS_ARGS% -Force
if /i "%4"=="/force" set PS_ARGS=%PS_ARGS% -Force

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0release.ps1" %PS_ARGS%
exit /b %errorlevel%
