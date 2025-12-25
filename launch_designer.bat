@echo off
call C:\Users\georg\miniconda3\Scripts\activate.bat watermark-ui
set "PATH=%CONDA_PREFIX%\Library\bin;%CONDA_PREFIX%\Library\lib\qt6\bin;%PATH%"
start "" "%CONDA_PREFIX%\Library\lib\qt6\bin\designer.exe"
