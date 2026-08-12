@echo off
REM Double-click launcher for build-exe.py -> builds dist\pc45years.exe
REM (all the real work / fixes live in build-exe.py; this just runs it)
python "%~dp0build-exe.py" %*
pause
