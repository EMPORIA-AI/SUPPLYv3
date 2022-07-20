@echo off
:main
cls
q server.py g\*.py routes\*.py common\*.py
rem python -m cProfile -s ncalls server.py | list /s
rem hypercorn server.py
pause
if errorlevel 1 goto end
goto main
:end
