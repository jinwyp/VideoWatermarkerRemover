@echo off
IF NOT EXIST venv (
    python -m venv venv
) ELSE (
    echo venv folder already exists, skipping creation...
)
call .\venv\Scripts\activate.bat

@REM pyinstaller --noconfirm --onedir --windowed --add-data "j:\ai\watermarkremover\venv\lib\site-packages/customtkinter;customtkinter/"  "./gui.py"


auto-py-to-exe -c ./autopytoexe.json -o ./dist gui.py
