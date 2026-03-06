#!/bin/bash
# Script de configuration et démarrage du projet Shroomleur

echo ""
echo "==================================="
echo "  Shroomleur API - Configuration"
echo "==================================="
echo ""

# Vérifier si .env existe
if [ ! -f .env ]; then
    echo "[INFO] Création du fichier .env à partir de .env.example..."
    cp .env.example .env
    echo "[OK] Fichier .env créé. Veuillez le configurer avant de continuer."
    echo ""
    echo "Important: Configurer les variables suivantes dans .env:"
    echo "  - GOOGLE_CLIENT_ID"
    echo "  - GOOGLE_CLIENT_SECRET"
    echo "  - SECRET_KEY"
    echo ""
    read -p "Appuyez sur ENTRÉE pour continuer..."
fi

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "[ERREUR] Docker n'est pas installé ou n'est pas dans le PATH."
    echo "Veuillez installer Docker: https://www.docker.com/"
    exit 1
fi

echo "[OK] Docker trouvé"

if ! command -v docker-compose &> /dev/null; then
    echo "[ERREUR] Docker Compose n'est pas disponible."
    exit 1
fi

echo "[OK] Docker Compose trouvé"
echo ""

echo "[INFO] Démarrage des services..."
docker-compose up

