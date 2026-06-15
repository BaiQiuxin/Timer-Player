@echo off
chcp 65001 > nul
title Timer & Player

cd /d "%~dp0"

set CONDA_EXE=E:\anaconda\Scripts\conda.exe
set CONDA_ENV=E:\anaconda_envs\envs\player
set PYTHON_CMD=%CONDA_EXE% run -p %CONDA_ENV% --no-capture-output python

echo 正在初始化配置...
%PYTHON_CMD% initialize.py

echo 正在启动程序...
%PYTHON_CMD% player.py

pause