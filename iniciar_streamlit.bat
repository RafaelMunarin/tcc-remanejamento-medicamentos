@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto dependencias
python -m venv .venv
if errorlevel 1 goto erro_python
:dependencias
if exist ".venv\bibliotecas_instaladas.txt" goto executar
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro_instalacao
echo OK > ".venv\bibliotecas_instaladas.txt"
:executar
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto erro_execucao
exit /b 0
:erro_python
echo Nao foi possivel criar o ambiente virtual. Confira a mensagem acima.
echo No CMD, execute python --version e confirme que aparece Python 3.12.
pause
exit /b 1
:erro_instalacao
echo A instalacao nao terminou. Confira a conexao e execute:
echo .venv\Scripts\python.exe -m pip install -r requirements.txt
pause
exit /b 1
:erro_execucao
echo Confira a mensagem acima. Para instalar as bibliotecas, execute:
echo .venv\Scripts\python.exe -m pip install -r requirements.txt
pause
exit /b 1
