"""Sécurité de l'API : authentification par clé, CORS et limitation de débit.

La clé est lue depuis la variable d'environnement ``API_KEY`` (avec repli sur une
valeur par défaut de développement) afin que les secrets ne soient jamais dans le
code. ``require_api_key`` est attachée comme dépendance FastAPI sur chaque route
protégée.
"""
from __future__ import annotations

import os

from fastapi import Header, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from .. import config

API_KEY = os.getenv("API_KEY", config.DEFAULT_API_KEY)

# Origines CORS autorisées (variable d'env séparée par des virgules ; "*" pour le dev local).
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Limiteur de débit partagé (par IP cliente).
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


async def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Rejette les requêtes sans en-tête ``X-API-Key`` valide (HTTP 401).

    L'en-tête est déclaré optionnel afin qu'une clé *manquante* produise notre 401
    plutôt que le 422 générique de FastAPI pour un en-tête requis manquant.
    """
    if x_api_key is None or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante.",
        )
    return x_api_key
