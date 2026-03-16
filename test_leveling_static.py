#!/usr/bin/env python3
"""Tests statiques de la logique de niveau (sans Docker / API distante)."""

from pathlib import Path
import sys

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.routes.users import router as users_router
from app.core.leveling import calculate_level_from_score
from app.database import Base, get_db
from app.dependencies import get_current_user
from app.models.user import User


def _build_client(tmp_path):
    db_path = tmp_path / "test_leveling.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as session:
        user = User(
            identifiant="level_user",
            email="level@test.local",
            mot_de_passe="hash",
            scoring=0,
            niveau=1,
            is_active=True,
        )
        session.add(user)
        session.commit()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_get_current_user(db: Session = Depends(override_get_db)):
        return db.query(User).filter(User.identifiant == "level_user").first()

    app = FastAPI()
    app.include_router(users_router)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    return TestClient(app), TestingSessionLocal, engine


def test_calculate_level_progressive_thresholds():
    assert calculate_level_from_score(0) == 1
    assert calculate_level_from_score(99) == 1
    assert calculate_level_from_score(100) == 2
    assert calculate_level_from_score(249) == 2
    assert calculate_level_from_score(250) == 3
    assert calculate_level_from_score(449) == 3
    assert calculate_level_from_score(450) == 4


def test_put_scoring_recomputes_level(tmp_path):
    client, session_factory, engine = _build_client(tmp_path)

    response = client.put("/users/me", json={"scoring": 250})

    assert response.status_code == 200
    body = response.json()
    assert body["scoring"] == 250
    assert body["niveau"] == 3

    with session_factory() as session:
        user = session.query(User).filter(User.identifiant == "level_user").first()
        assert user.niveau == 3

    Base.metadata.drop_all(bind=engine)
