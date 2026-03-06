@echo off
REM Script de configuration et démarrage du projet Shroomleur

echo.
echo ===================================
echo  Shroomleur API - Configuration
echo ===================================
echo.

REM Vérifier si .env existe
if not exist .env (
    echo [INFO] Création du fichier .env à partir de .env.example...
    copy .env.example .env
    echo [OK] Fichier .env créé. Veuillez le configurer avant de continuer.
    echo.
    echo Important: Configurer les variables suivantes dans .env:
    echo  - GOOGLE_CLIENT_ID
    echo  - GOOGLE_CLIENT_SECRET
    echo  - SECRET_KEY
    echo.
    pause
)

REM Vérifier Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Docker n'est pas installé ou n'est pas dans le PATH.
    echo Veuillez installer Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [OK] Docker trouvé
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Docker Compose n'est pas disponible.
    pause
    exit /b 1
)

echo [OK] Docker Compose trouvé
echo.

echo [INFO] Démarrage des services...
docker-compose up

pause
