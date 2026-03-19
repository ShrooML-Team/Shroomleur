#!/usr/bin/env python3
"""
Script pour créer des utilisateurs fictifs avec des scores variés
pour tester le système de rangs
"""

import os
import random
import string
import argparse
from urllib.parse import urlsplit, urlunsplit
from datetime import datetime

import bcrypt
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()


def load_env_file(env_path: str) -> dict:
    """Charge un fichier .env simple (KEY=VALUE) sans dépendance externe."""
    values = {}
    if not os.path.exists(env_path):
        return values

    with open(env_path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def resolve_database_url(target_env: str) -> str:
    """Résout DATABASE_URL selon l'environnement demandé."""
    project_root = os.path.dirname(__file__)
    env_values = load_env_file(os.path.join(project_root, ".env"))

    if target_env == "prod":
        database_url = (
            os.getenv("PROD_DATABASE_URL")
            or env_values.get("PROD_DATABASE_URL")
            or os.getenv("DATABASE_URL")
            or env_values.get("DATABASE_URL")
        )
    elif target_env == "staging":
        database_url = (
            os.getenv("STAGING_DATABASE_URL")
            or env_values.get("STAGING_DATABASE_URL")
            or os.getenv("DATABASE_URL")
            or env_values.get("DATABASE_URL")
        )
    else:
        database_url = (
            os.getenv("DATABASE_URL")
            or env_values.get("DATABASE_URL")
            or "postgresql://shroomleur:shroomleur@localhost:5432/shroomleur"
        )

    if not database_url:
        raise RuntimeError("DATABASE_URL introuvable. Définit DATABASE_URL (ou PROD/STAGING_DATABASE_URL).")

    # Hors docker-compose, l'hôte "db" n'est pas résolu depuis WSL/host.
    if "@db:" in database_url and not os.path.exists("/.dockerenv"):
        database_url = database_url.replace("@db:", "@localhost:")

    return database_url


def mask_database_url(database_url: str) -> str:
    """Masque le mot de passe pour l'affichage console."""
    parsed = urlsplit(database_url)
    if parsed.password is None:
        return database_url

    username = parsed.username or ""
    hostname = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{username}:***@{hostname}{port}" if username else f"***@{hostname}{port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def ensure_prod_confirmation(target_env: str, confirm_prod: bool) -> None:
    if target_env == "prod" and not confirm_prod:
        raise RuntimeError(
            "Mode production bloqué: ajoute --confirm-prod pour autoriser l'écriture."
        )


def calculate_level_from_score(score: float) -> int:
    """Calculer le niveau en fonction du score."""
    import math
    if score < 0:
        return 1
    return max(1, int(math.sqrt(score / 100)) + 1)


class User(Base):
    """Modèle utilisateur"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    identifiant = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    mot_de_passe = Column(String(255), nullable=True)
    photo_profil = Column(String(500), nullable=True)
    champignon_prefere = Column(String(255), nullable=True)
    description_index = Column(Integer, default=0, nullable=True)
    
    scoring = Column(Float, default=0.0)
    streak = Column(Integer, default=0)
    niveau = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True)
    
    google_id = Column(String(255), unique=True, nullable=True, index=True)


def build_engine_and_session(database_url: str):
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, session_local


def hash_password(password: str) -> str:
    """Hasher un mot de passe avec bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def generate_random_username(length=8, prefix="user_"):
    """Générer un nom d'utilisateur aléatoire"""
    return prefix + ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_email(prefix="user_"):
    """Générer un email fictif aléatoire"""
    username = generate_random_username(6, prefix=prefix)
    return f"{username}@test.local"


def create_fake_users(session_local, count=50, prefix="user_", dry_run=False):
    """
    Créer des utilisateurs fictifs avec des scores variés
    """
    db = session_local()
    
    try:
        print(f"Creation de {count} utilisateurs fictifs (prefix={prefix}, dry_run={dry_run})...")
        
        fake_users = []
        
        for _ in range(count):
            score = random.randint(0, 10000)
            
            user = User(
                identifiant=generate_random_username(prefix=prefix),
                email=generate_random_email(prefix=prefix),
                mot_de_passe=hash_password("password123"),
                photo_profil=None,
                champignon_prefere=None,
                description_index=random.randint(0, 14),
                scoring=float(score),
                streak=random.randint(0, 100),
                niveau=calculate_level_from_score(float(score)),
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            fake_users.append(user)

        if dry_run:
            print("Dry-run: aucun utilisateur n'est insere.")
            preview_count = min(5, len(fake_users))
            for idx in range(preview_count):
                user = fake_users[idx]
                print(f"  preview[{idx+1}] {user.identifiant} | score={user.scoring} | niveau={user.niveau}")
            return
        
        db.add_all(fake_users)
        db.commit()
        
        print(f"OK: {count} utilisateurs crees avec succes")
        
        print("\nStatistiques:")
        all_users = db.query(User).all()
        print(f"   Total d'utilisateurs: {len(all_users)}")
        
        by_level = {}
        for user in all_users:
            level = user.niveau
            by_level[level] = by_level.get(level, 0) + 1
        
        print("   Répartition par niveau:")
        for level in sorted(by_level.keys()):
            print(f"      Niveau {level}: {by_level[level]} utilisateurs")
        
        top_10 = db.query(User).order_by(User.scoring.desc()).limit(10).all()
        print("\nTop 10:")
        for rank, user in enumerate(top_10, 1):
            print(f"   {rank}. {user.identifiant} - {user.scoring} points (Niveau {user.niveau})")
        
    except Exception as e:
        print(f"Erreur: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def clear_fake_users(session_local, prefix="user_", dry_run=False):
    """Supprimer les utilisateurs fictifs selon le prefix."""
    db = session_local()
    
    try:
        query = db.query(User).filter(User.identifiant.like(f"{prefix}%"))

        if dry_run:
            fake_user_count = query.count()
            print(f"Dry-run: {fake_user_count} utilisateurs seraient supprimes (prefix={prefix})")
            return

        fake_user_count = query.delete(synchronize_session=False)
        db.commit()
        
        print(f"OK: {fake_user_count} utilisateurs fictifs supprimes (prefix={prefix})")
        
    except Exception as e:
        print(f"Erreur: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def print_stats(session_local):
    db = session_local()
    try:
        all_users = db.query(User).all()
        print(f"Total users: {len(all_users)}")
        top_10 = db.query(User).order_by(User.scoring.desc()).limit(10).all()
        print("Top 10:")
        for rank, user in enumerate(top_10, 1):
            print(f"  {rank}. {user.identifiant} - {user.scoring} (niveau {user.niveau})")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gérer les utilisateurs fictifs pour tester les rangs"
    )
    parser.add_argument(
        "action",
        choices=["create", "clear", "stats"],
        help="Action à effectuer"
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=50,
        help="Nombre d'utilisateurs à créer (défaut: 50)"
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="user_",
        help="Préfixe des comptes fictifs (défaut: user_)"
    )
    parser.add_argument(
        "--env",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Environnement cible"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simule l'opération sans écrire en base"
    )
    parser.add_argument(
        "--confirm-prod",
        action="store_true",
        help="Obligatoire pour autoriser l'écriture en production"
    )
    parser.add_argument(
        "--max-count",
        type=int,
        default=200,
        help="Garde-fou max pour --count (défaut: 200)"
    )
    
    args = parser.parse_args()

    if args.count < 0:
        raise SystemExit("--count doit etre positif")
    if args.count > args.max_count:
        raise SystemExit(f"--count={args.count} depasse --max-count={args.max_count}")

    ensure_prod_confirmation(args.env, args.confirm_prod)
    DATABASE_URL = resolve_database_url(args.env)
    print(f"Environnement: {args.env}")
    print(f"Database URL: {mask_database_url(DATABASE_URL)}")

    engine, SessionLocal = build_engine_and_session(DATABASE_URL)
    Base.metadata.bind = engine
    
    if args.action == "create":
        create_fake_users(SessionLocal, args.count, prefix=args.prefix, dry_run=args.dry_run)
    elif args.action == "clear":
        clear_fake_users(SessionLocal, prefix=args.prefix, dry_run=args.dry_run)
    elif args.action == "stats":
        print_stats(SessionLocal)
