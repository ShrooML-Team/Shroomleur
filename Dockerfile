FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY pyproject.toml .

# Installer les dépendances Python
RUN pip install --no-cache-dir -e .

# Copier le code source
COPY backend/ .
COPY create_fake_users.py /app/create_fake_users.py

# Préparer le répertoire d'uploads
RUN mkdir -p /app/uploads/profiles
RUN chmod +x /app/create_fake_users.py

# Créer un utilisateur non-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
