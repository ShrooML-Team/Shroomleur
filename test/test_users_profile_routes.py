#!/usr/bin/env python3
"""Tests unitaires des routes profil utilisateur."""

from pathlib import Path
import sys

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.routes.users import router as users_router
from app.database import Base, get_db
from app.dependencies import get_current_user
from app.models.user import User


def _build_client(tmp_path):
    db_path = tmp_path / "test_users_profile.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    with testing_session_local() as session:
        current_user = User(
            identifiant="current_user",
            email="current@example.com",
            mot_de_passe="hash",
            scoring=100.0,
            niveau=2,
            is_active=True,
        )
        other_user = User(
            identifiant="other_user",
            email="other@example.com",
            mot_de_passe="hash",
            scoring=500.0,
            niveau=3,
            is_active=True,
        )
        session.add_all([current_user, other_user])
        session.commit()

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    def override_get_current_user(db: Session = Depends(get_db)):
        return db.query(User).filter(User.identifiant == "current_user").first()

    app = FastAPI()
    app.include_router(users_router)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    return TestClient(app), testing_session_local, engine


def test_put_me_updates_description_index(tmp_path):
    client, session_factory, engine = _build_client(tmp_path)

    response = client.put("/users/me", json={"description_index": 7})

    assert response.status_code == 200
    body = response.json()
    assert body["description_index"] == 7

    with session_factory() as session:
        user = session.query(User).filter(User.identifiant == "current_user").first()
        assert user.description_index == 7

    Base.metadata.drop_all(bind=engine)


def test_put_me_rejects_duplicate_email(tmp_path):
    client, _session_factory, engine = _build_client(tmp_path)

    response = client.put("/users/me", json={"email": "other@example.com"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Email déjà utilisé"

    Base.metadata.drop_all(bind=engine)


def test_put_me_clamps_negative_score_and_recomputes_level(tmp_path):
    client, session_factory, engine = _build_client(tmp_path)

    response = client.put("/users/me", json={"scoring": -50})

    assert response.status_code == 200
    body = response.json()
    assert body["scoring"] == 0
    assert body["niveau"] == 1

    with session_factory() as session:
        user = session.query(User).filter(User.identifiant == "current_user").first()
        assert user.scoring == 0
        assert user.niveau == 1

    Base.metadata.drop_all(bind=engine)


def test_get_me_returns_rank_based_on_higher_scores(tmp_path):
    client, _session_factory, engine = _build_client(tmp_path)

    response = client.get("/users/me")

    assert response.status_code == 200
    body = response.json()
    assert body["identifiant"] == "current_user"
    assert body["rang"] == 2

    Base.metadata.drop_all(bind=engine)
