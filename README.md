# Shroomleur API

API d'authentification et gestion des comptes utilisateurs pour l'application Shroomleur.

## Caractéristiques

✨ **Authentification complète**
- Authentification locale (identifiant + mot de passe)
- Authentification via Google OAuth 2.0
- JWT tokens pour les sessions utilisateur

👤 **Gestion des profils**
- Profils utilisateurs complets
- Système de scoring et de streaks
- Niveaux de joueur dynamiques
- Inventaire d'items personnalisés

🍄 **Historique d'identifications**
- Enregistrement des identifications
- Localisation (coordonnées GPS ou texte)
- Horodatage complet (date, heure)
- Statistiques d'identification

🐳 **Infrastructure**
- Dockerisé avec PostgreSQL
- docker-compose pour démarrage facile
- Environment variables pour configuration

## Prérequis

- Docker & Docker Compose
- ou Python 3.11+, PostgreSQL 15+

## Installation & Démarrage

### Avec Docker Compose (Recommandé)

1. **Cloner le repository**
```bash
git clone https://github.com/ShrooML-Team/Shroomleur.git
cd Shroomleur
```

2. **Configurer les variables d'environnement**
```bash
cp .env.example .env
# Éditer .env et remplir les valeurs (surtout GOOGLE_CLIENT_ID et SECRET)
```

3. **Lancer les services**
```bash
docker-compose up
```

L'API sera accessible à `http://localhost:8000`

### Sans Docker (Développement local)

1. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Installer les dépendances**
```bash
pip install -e .
```

3. **Configurer la base de données**
- Créer une base de données PostgreSQL
- Mettre à jour DATABASE_URL dans .env

4. **Initialiser la BD**
```bash
python -c "from app.database import init_db; init_db()"
```

5. **Lancer le serveur**
```bash
uvicorn app.main:app --reload
```

## Documentation de l'API

Une fois le serveur lancé, accédez à la documentation interactive:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Structure du Projet

```
Shroomleur/
├── backend/
│   └── app/
│       ├── core/              # Configuration & sécurité
│       │   ├── config.py
│       │   └── security.py
│       ├── models/            # Modèles SQLAlchemy
│       │   ├── user.py
│       │   └── identification_history.py
│       ├── schemas/           # Schémas Pydantic
│       │   ├── user.py
│       │   └── identification_history.py
│       ├── api/routes/        # Endpoints
│       │   ├── auth.py
│       │   ├── users.py
│       │   └── history.py
│       ├── database.py        # Configuration SQLAlchemy
│       ├── dependencies.py    # Dépendances FastAPI
│       └── main.py            # Application FastAPI
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

## Endpoints Principaux

### Authentification (POST /auth)
- `POST /auth/register` - Inscription locale
- `POST /auth/login` - Connexion locale
- `POST /auth/google` - Login Google OAuth
- `POST /auth/refresh` - Rafraîchir le JWT token

### Utilisateurs (GET/PUT /users)
- `GET /users/me` - Profil personnel
- `PUT /users/me` - Modifier le profil
- `GET /users/{user_id}` - Profil public d'un utilisateur
- `GET /users/me/items` - Inventaire personnel

### Historique (GET/POST /users/me/history)
- `POST /users/me/history` - Enregistrer une identification
- `GET /users/me/history` - Historique paginé
- `GET /users/me/history/stats` - Statistiques de l'utilisateur
- `DELETE /users/me/history/{history_id}` - Supprimer une entrée

## Configuration Google OAuth

1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un nouveau projet
3. Activer l'API Google+ et l'API OAuth 2.0
4. Créer des credentials (OAuth 2.0 Client ID)
5. Ajouter les URIs autorisés:
   - `http://localhost:8000/auth/google/callback` (développement)
   - `https://yourdomain.com/auth/google/callback` (production)
6. Copier CLIENT_ID et CLIENT_SECRET dans .env

## Variables d'Environnement

Voir `.env.example` pour la liste complète. Les variables critiques:

```env
# Base de données
DATABASE_URL=postgresql://user:password@host:port/dbname

# JWT
SECRET_KEY=your-secret-key-minimum-32-chars

# Google OAuth (optionnel mais recommandé)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

## Développement

### Lancer les tests
```bash
pytest
```

### Formater le code
```bash
ruff check backend/
ruff format backend/
```

### Type checking
```bash
mypy backend/app
```

## Modèle de Données

### User
- `id` (PK)
- `identifiant` (unique)
- `email` (unique)
- `mot_de_passe` (hash bcrypt)
- `photo_profil`
- `description`
- `champignon_prefere`
- `scoring` (float)
- `streak` (int)
- `niveau` (int)
- `google_id` (OAuth)
- `is_active` (softdelete)
- `created_at`, `updated_at`

### IdentificationHistory
- `id` (PK)
- `user_id` (FK → User)
- `champignon` (name)
- `score` (0-100)
- `date`, `heure`
- `localisation`, `latitude`, `longitude`
- `notes`
- `created_at`

### UserItem
- `id` (PK)
- `user_id` (FK → User)
- `item_name`
- `quantity`
- `acquired_at`

## Sécurité

- ✅ Mots de passe hashés avec bcrypt
- ✅ JWT tokens avec expiration
- ✅ CORS configurable
- ✅ Authentification par Bearer token
- ✅ Validation Pydantic de toutes les entrées
- ✅ Database connection pooling

## Déploiement

### Production avec docker-compose

1. Copier `.env.example` en `.env`
2. Remplir toutes les variables d'environnement
3. Générer un SECRET_KEY sécurisé: `openssl rand -hex 32`
4. `docker-compose up -d`
5. Vérifier: `curl http://localhost:8000/health`

### Avec Kubernetes

À venir (voir `.github/workflows/` pour CI/CD)

## Support & Contribution

- 🐛 Issues: https://github.com/ShrooML-Team/Shroomleur/issues
- 💬 Discussions: https://github.com/ShrooML-Team/Shroomleur/discussions
- 🤝 Pull Requests: Bienvenues!

## Licences

MIT License - Voir [LICENSE](LICENSE)

---

**Maintenu par**: ShrooML Team
**Version**: 0.1.0
**Dernière mise à jour**: 2 mars 2026
