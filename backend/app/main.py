from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import settings
from .database import init_db
from .api import auth_router, users_router, history_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Événements de cycle de vie de l'application
    """
    # Startup
    print(f"🚀 Démarrage de {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    print("✅ Base de données initialisée")
    
    yield
    
    # Shutdown
    print("🛑 Arrêt de l'application")


# Créer l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API pour l'authentification et la gestion des comptes utilisateurs de Shroomleur",
    lifespan=lifespan,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routes
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(history_router)


@app.get("/", tags=["health"])
def read_root():
    """
    Endpoint de vérification de santé de l'application
    """
    return {
        "message": f"Bienvenue sur {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health", tags=["health"])
def health_check():
    """
    Endpoint pour vérifier que l'application est en bonne santé
    """
    return {"status": "ok", "message": "Application en bonne santé"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
