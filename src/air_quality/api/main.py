"""Application FastAPI exposant le modèle AQI (C9) avec des hooks de surveillance (C11).

Routes
------
GET  /health        vivacité + indicateur de modèle chargé
GET  /model/info    nom du modèle, liste des features, métriques d'entraînement
POST /predict       prédiction unitaire (authentification requise)
POST /predict/batch prédiction par lot (authentification requise)
GET  /metrics       exposition Prometheus (ajoutée par l'instrumentator)

La documentation OpenAPI interactive est servie automatiquement sur /docs et
/redoc — c'est la documentation technique de l'API (utilisée par le client C10).
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import joblib
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .. import config
from ..inference import load_feature_names, predict_one
from ..logging_config import configure_logging, log_prediction
from .schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictionRequest,
    PredictionResponse,
)
from .security import CORS_ORIGINS, limiter, require_api_key

logger = logging.getLogger("air_quality.api")

# --- Métriques Prometheus personnalisées (C11) -----------------------------
PREDICTIONS = Counter(
    "aqi_predictions_total", "Nombre total de prédictions servies", ["category"])
PREDICTION_AQI = Histogram(
    "aqi_prediction_value", "Distribution des valeurs AQI prédites",
    buckets=[25, 50, 100, 150, 200, 300, 400, 500])
PREDICTION_ERRORS = Counter(
    "aqi_prediction_errors_total", "Erreurs du gestionnaire de prédiction")

# Chargé une fois au démarrage, partagé entre les requêtes.
STATE: dict = {"model": None, "feature_names": None, "metrics": None}


def _load_artifacts() -> None:
    import json

    STATE["model"] = joblib.load(config.MODELS_DIR / "best_model.joblib")
    STATE["feature_names"] = load_feature_names()
    with open(config.REPORTS_DIR / "metrics.json") as fh:
        STATE["metrics"] = json.load(fh)
    logger.info("Artefacts du modèle chargés", extra={"best_model": STATE["metrics"]["best_model"]})


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    _load_artifacts()
    yield


app = FastAPI(
    title="API AQI de qualité de l'air",
    description="Prédire l'indice de qualité de l'air EPA à partir des mesures de polluants et météo.",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Expose les métriques HTTP par défaut + les nôtres personnalisées sur /metrics.
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


def _to_payload(req: PredictionRequest) -> dict:
    p = req.model_dump()
    p["timestamp"] = (req.timestamp or datetime.now(timezone.utc)).isoformat()
    return p


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health():
    return HealthResponse(status="ok", model_loaded=STATE["model"] is not None)


@app.get("/model/info", response_model=ModelInfoResponse, tags=["meta"])
async def model_info():
    m = STATE["metrics"]
    return ModelInfoResponse(
        best_model=m["best_model"],
        n_features=len(m["features"]),
        features=m["features"],
        metrics=m["results"][m["best_model"]],
    )


@app.post("/predict", response_model=PredictionResponse, tags=["inference"])
@limiter.limit("60/minute")
async def predict(request: Request, body: PredictionRequest,
                  _: str = Depends(require_api_key)):
    payload = _to_payload(body)
    try:
        result = predict_one(STATE["model"], payload, STATE["feature_names"])
    except Exception:
        PREDICTION_ERRORS.inc()
        logger.exception("Échec de la prédiction")
        raise
    PREDICTIONS.labels(category=result["category"]).inc()
    PREDICTION_AQI.observe(result["aqi"])
    log_prediction(payload, result)
    return PredictionResponse(**result)


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["inference"])
@limiter.limit("20/minute")
async def predict_batch(request: Request, body: BatchPredictionRequest,
                        _: str = Depends(require_api_key)):
    out = []
    for item in body.items:
        payload = _to_payload(item)
        result = predict_one(STATE["model"], payload, STATE["feature_names"])
        PREDICTIONS.labels(category=result["category"]).inc()
        PREDICTION_AQI.observe(result["aqi"])
        log_prediction(payload, result)
        out.append(PredictionResponse(**result))
    return BatchPredictionResponse(predictions=out)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    logger.exception("Erreur non gérée")
    return JSONResponse(status_code=500, content={"detail": "Erreur interne du serveur."})
