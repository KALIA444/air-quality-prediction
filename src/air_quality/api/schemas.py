"""Schémas Pydantic v2 de requête/réponse — le contrat d'entrée fonctionnel de l'API.

Les contraintes de plage par champ (`Field(ge=..., le=...)`) constituent la
spécification technique *et* une première couche de sécurité : les charges utiles
malformées ou hors plage sont rejetées avec un HTTP 422 avant d'atteindre le modèle.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    """Une observation horaire des polluants + météorologie."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2024-07-15T14:00:00",
                "co": 3.8, "nox": 172.0, "no2": 144.3, "o3": 118.1, "so2": 1.2,
                "pm25": 147.3, "pm10": 208.8, "temperature": 28.5,
                "humidity": 45.0, "pressure": 1013.2,
                "wind_speed": 6.0, "wind_direction": 210.0,
            }
        }
    )

    timestamp: datetime | None = Field(
        default=None, description="Heure de l'observation (ISO-8601). Par défaut : maintenant.")
    co: float = Field(ge=0, le=100, description="Concentration de CO (ppm).")
    nox: float = Field(ge=0, le=1000, description="Concentration de NOx.")
    no2: float = Field(ge=0, le=1000, description="Concentration de NO2 (ppb).")
    o3: float = Field(ge=0, le=1000, description="Concentration d'O3 (ppb).")
    so2: float = Field(ge=0, le=1000, description="Concentration de SO2 (ppb).")
    pm25: float = Field(ge=0, le=1000, description="PM2.5 (µg/m³).")
    pm10: float = Field(ge=0, le=1000, description="PM10 (µg/m³).")
    temperature: float = Field(ge=-50, le=60, description="Température de l'air (°C).")
    humidity: float = Field(ge=0, le=100, description="Humidité relative (%).")
    pressure: float = Field(ge=870, le=1085, description="Pression (hPa).")
    wind_speed: float = Field(ge=0, le=200, description="Vitesse du vent.")
    wind_direction: float = Field(ge=0, le=360, description="Direction du vent (deg).")


class PredictionResponse(BaseModel):
    aqi: float = Field(description="Indice de qualité de l'air EPA prédit (0–500).")
    category: str = Field(description="Libellé de catégorie EPA pour l'AQI prédit.")
    dominant_pollutant: str = Field(description="Polluant déterminant l'AQI.")


class BatchPredictionRequest(BaseModel):
    items: list[PredictionRequest] = Field(min_length=1, max_length=1000)


class BatchPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class ModelInfoResponse(BaseModel):
    best_model: str
    n_features: int
    features: list[str]
    metrics: dict


class ErrorResponse(BaseModel):
    detail: str
