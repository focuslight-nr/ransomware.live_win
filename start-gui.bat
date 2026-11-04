@echo off
:: Ransomware.live GUI launcher (Windows)
cd /d "%~dp0"

if exist ".venv-py314\Scripts\python.exe" (
    set PYTHON=.venv-py314\Scripts\python.exe
) else if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else (
    set PYTHON=python
)

%PYTHON% gui.py %*
