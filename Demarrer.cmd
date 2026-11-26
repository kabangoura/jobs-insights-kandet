@echo off
rem Double-clic : lance le serveur local (serveur.py) et ouvre la page des offres.
rem Option --sans-navigateur : ne pas ouvrir le navigateur (pour les essais).
chcp 65001 >nul
setlocal
cd /d "%~dp0\03-amelioration-preuve-de-concept"
set "ADRESSE=http://127.0.0.1:8000"

where python >nul 2>nul
if errorlevel 1 (
    echo Python est introuvable. Installez Python 3.12 ou plus recent depuis https://www.python.org/downloads/
    echo puis cochez "Add python.exe to PATH" pendant l'installation.
    pause
    exit /b 1
)

rem Le serveur tourne deja ? On ouvre seulement la page.
call :serveur_pret
if not errorlevel 1 goto ouvrir

if not exist offres.html (
    echo Premiere utilisation : la page n'existe pas encore.
    echo Lancez une premiere collecte avec : python main.py   (environ 17 minutes)
    echo.
)
echo Demarrage du serveur. Pour l'arreter, fermez la fenetre « Offres TI - serveur ».
start "Offres TI - serveur" /min python serveur.py

rem Attendre que le serveur reponde (au plus 15 secondes).
for /l %%i in (1,1,15) do (
    call :serveur_pret
    if not errorlevel 1 goto ouvrir
    timeout /t 1 /nobreak >nul
)
echo Le serveur ne repond pas. Lancez « python serveur.py » dans le dossier 03-amelioration-preuve-de-concept pour voir l'erreur.
pause
exit /b 1

:ouvrir
echo Page : %ADRESSE%
if /i not "%~1"=="--sans-navigateur" start "" "%ADRESSE%"
exit /b 0

:serveur_pret
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing '%ADRESSE%/api/etat' -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
exit /b %errorlevel%
