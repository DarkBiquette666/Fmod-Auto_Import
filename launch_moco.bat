@echo off
setlocal
set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%"
start "" pythonw "%SCRIPT_DIR%moco_auto_import.py"
popd
