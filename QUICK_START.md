# 🚀 Quick Start - Shroomleur API

## Démarrage le plus rapide possible (5 minutes)

### 1. Préparation initiale
```bash
# Cloner et entrer dans le répertoire
git clone https://github.com/ShrooML-Team/Shroomleur.git
cd Shroomleur

# Créer le fichier de configuration
cp .env.example .env
```

### 2. Lancer avec Docker (Recommandé)
```bash
docker-compose up
```

**Voilà ! L'API devrait être accessible à http://localhost:8000**

---

## Vérification

### Health Check
```bash
curl http://localhost:8000/health
# Réponse: {"status":"ok","message":"Application en bonne santé"}
```

### Accès à la documentation
- **Swagger UI (Interactive)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Premier Test d'API

### 1. S'inscrire
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "identifiant": "champignon_lover",
    "email": "user@example.com",
    "mot_de_passe": "SecurePassword123!",
    "champignon_prefere": "Boletus edulis"
  }'
```

**Réponse attendue:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "identifiant": "champignon_lover",
    "email": "user@example.com",
    "scoring": 0.0,
    "streak": 0,
    "niveau": 1,
    ...
  }
}
```

### 2. Enregistrer une identification (nécessite le token)
```bash
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST "http://localhost:8000/users/me/history" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "champignon": "Amanita muscaria",
    "score": 85.5,
    "heure": "14:30:00",
    "localisation": "Forêt de Fontainebleau",
    "latitude": 48.4,
    "longitude": 2.65
  }'
```

### 3. Consulter les statistiques
```bash
curl -X GET "http://localhost:8000/users/me/history/stats" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

## Environnement Local (Sans Docker)

### Prérequis
- Python 3.11+
- PostgreSQL 15+

### Installation
```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -e .

# Configurer .env avec votre BD locale
# DATABASE_URL=postgresql://user:password@localhost:5432/shroomleur

# Lancer le serveur
uvicorn app.main:app --reload
```

---

## Configuration Google OAuth (Optionnel)

Pour activer la connexion par Google:

1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un projet → APIs & Services → Credentials
3. Créer un "OAuth 2.0 Client ID" (type: Web application)
4. Autoriser les URIs:
   - `http://localhost:8000/auth/google/callback`
5. Copier Client ID et Secret dans `.env`:
```env
GOOGLE_CLIENT_ID=123456789-abcdefghijk.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxx
```

---

## Arrêter les services

### Avec Docker
```bash
docker-compose down
```

### Pour nettoyer aussi la BD
```bash
docker-compose down -v
```

---

## Dépannage

### "Cannot connect to Docker daemon"
→ Vérifier que Docker Desktop est lancé

### "Port 5432 already in use"
→ Le port PostgreSQL est occupé. Changez dans `.env`:
```env
DB_PORT=5433
```

### "ModuleNotFoundError: No module named 'app'"
→ Vous êtes dans le mauvais répertoire. Lancez depuis la racine du projet.

### Les tables ne sont pas créées
→ Vérifier que PostgreSQL est accessible et que `DATABASE_URL` est correcte

---

## Fichiers importants

| Fichier | Rôle |
|---------|------|
| `docker-compose.yml` | Orchestration des services |
| `Dockerfile` | Image de conteneur FastAPI |
| `.env` | Variables de configuration locale |
| `pyproject.toml` | Dépendances Python |
| `backend/app/main.py` | Application FastAPI |
| `backend/app/models/` | Modèles de BD |
| `backend/app/api/routes/` | Endpoints de l'API |

---

## Prochaines étapes

1. ✅ L'API fonctionne
2. ⏭️ [Lire la doc complète](README.md)
3. ⏭️ [Configurer Google Login](README.md#configuration-google-oauth)
4. ⏭️ [Développer votre frontend](README.md)

---

**Besoin d'aide ?** 
- 📖 Swagger: http://localhost:8000/docs
- 💬 Issues: https://github.com/ShrooML-Team/Shroomleur/issues
- 📧 Email: support@shroomleur.dev
