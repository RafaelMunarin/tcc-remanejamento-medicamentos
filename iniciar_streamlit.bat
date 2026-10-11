@echo off
setlocal
cd /d "%~dp0"
set "VENV_DIR=%LOCALAPPDATA%\tcc-remanejamento-medicamentos\.venv"
if exist "%VENV_DIR%\Scripts\python.exe" goto dependencias
if not exist "%LOCALAPPDATA%\tcc-remanejamento-medicamentos" mkdir "%LOCALAPPDATA%\tcc-remanejamento-medicamentos"
python -m venv "%VENV_DIR%"
if errorlevel 1 goto erro_python
:dependencias
if exist "%VENV_DIR%\bibliotecas_instaladas.txt" goto executar
"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro_instalacao
echo OK > "%VENV_DIR%\bibliotecas_instaladas.txt"
:executar
"%VENV_DIR%\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto erro_execucao
exit /b 0
:erro_python
echo Nao foi possivel criar o ambiente virtual. Confira a mensagem acima.
echo No CMD, execute python --version e confirme que aparece Python 3.12.
echo Tambem confira se o Windows nao bloqueou a pasta: %VENV_DIR%
pause
exit /b 1
:erro_instalacao
echo A instalacao nao terminou. Confira a conexao e execute:
echo "%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
pause
exit /b 1
:erro_execucao
echo Confira a mensagem acima. Para instalar as bibliotecas, execute:
echo "%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
pause
exit /b 1
