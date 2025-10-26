@echo off
REM Wrapper to invoke the cross-platform convert.py helper using the current Python interpreter
python "%~dp0convert.py" %*
