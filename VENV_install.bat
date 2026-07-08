@echo off
setlocal

echo ============================================
echo   Clean install VENV
echo ============================================
echo.

cd /d "%~dp0"

if exist venv (
    echo Suppression de l'ancien venv...
    rmdir /s /q venv
)

py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python 3.11 introuvable via "py -3.11".
    echo Installe Python 3.11 depuis python.org, puis relance ce script.
    pause
    exit /b 1
)

echo Creating the new virtual environment...
py -3.11 -m venv venv

echo Activating venv...
call venv\Scripts\activate

echo Updating pip . . .
python -m pip install --upgrade pip

if exist requirements.txt (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
) else (
    echo WARNING: requirements.txt not found in this folder.
    echo No dependencies automatically installed.
)

echo.
echo ============================================
echo   Installation complete!
echo ============================================
echo Quick OpenCV verification:
python -c "import cv2; print('OpenCV version:', cv2.__version__); print('groupRectangles disponible:', hasattr(cv2, 'groupRectangles'))"

echo.
pause
