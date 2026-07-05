"""Inférence partagée : transforme un payload de mesure brut en une prédiction du modèle.

L'API REST (:mod:`air_quality.api`) et l'application Streamlit appellent toutes
deux :func:`predict_one`, de sorte que la logique de construction des variables
vit en un seul et même endroit et ne peut pas diverger entre elles.
``featurize_request`` reconstruit le vecteur de variables exact sur lequel le
modèle a été entraîné (en réutilisant :func:`features.add_features` pour les
colonnes calendaires / cycliques / d'interaction), puis aligne l'ordre des
colonnes sur les ``feature_names`` persistés au moment de l'entraînement.

Hypothèses pour une observation unique (documentées car elles n'ont pas d'historique) :
* les ratios de polluants sont recalculés à partir de leurs composants ;
* les moyennes mobiles à 3 pas (``*_MA3``) prennent par défaut la valeur courante ;
* ``Temp_Humidity_Index`` utilise l'indice d'inconfort de Thom (approximation Celsius).
Ces variables ont toutes une importance quasi nulle, donc les approximations sont sûres.
"""
from __future__ import annotations

import json

import pandas as pd

from . import config
from .aqi import aqi_category, compute_aqi
from .features import add_features

# Associe le champ du payload API -> nom de colonne brute du CSV.
PAYLOAD_TO_COLUMN = {
    "co": "CO(GT)",
    "nox": "NOx(GT)",
    "no2": "NO2(GT)",
    "o3": "O3(GT)",
    "so2": "SO2(GT)",
    "pm25": "PM2.5",
    "pm10": "PM10",
    "temperature": "Temperature",
    "humidity": "Humidity",
    "pressure": "Pressure",
    "wind_speed": "WindSpeed",
    "wind_direction": "WindDirection",
}


def load_feature_names(path=None) -> list[str]:
    """Lit l'ordre des variables du modèle entraîné depuis reports/metrics.json."""
    path = path or (config.REPORTS_DIR / "metrics.json")
    with open(path) as fh:
        return json.load(fh)["features"]


def _thom_index(temp_c: float, humidity_pct: float) -> float:
    """Indice Température-Humidité (d'inconfort) de Thom, approximation Celsius."""
    return temp_c - (0.55 - 0.0055 * humidity_pct) * (temp_c - 14.5)


def _base_row(payload: dict) -> dict:
    """Assemble les colonnes brutes du CSV à partir d'un payload de mesure + timestamp."""
    row = {col: float(payload[key]) for key, col in PAYLOAD_TO_COLUMN.items()}

    # Colonnes dérivées que le jeu de données fournit précalculées.
    row["CO_NOx_Ratio"] = row["CO(GT)"] / row["NOx(GT)"] if row["NOx(GT)"] else 0.0
    row["NOx_NO2_Ratio"] = row["NOx(GT)"] / row["NO2(GT)"] if row["NO2(GT)"] else 0.0
    row["Temp_Humidity_Index"] = _thom_index(row["Temperature"], row["Humidity"])
    # Pas d'historique au moment de l'inférence -> MA3 retombe sur la valeur courante.
    row["CO_MA3"] = row["CO(GT)"]
    row["NO2_MA3"] = row["NO2(GT)"]
    row["O3_MA3"] = row["O3(GT)"]
    return row


def featurize_request(payload: dict) -> pd.DataFrame:
    """Construit un DataFrame de variables d'une seule ligne à partir d'un payload de mesure.

    ``payload`` doit porter chaque clé de :data:`PAYLOAD_TO_COLUMN` plus
    ``timestamp`` (chaîne ISO-8601 ou datetime).
    """
    ts = pd.to_datetime(payload["timestamp"])
    row = _base_row(payload)
    row["DayOfWeek"] = ts.weekday()
    row["Hour"] = ts.hour

    df = pd.DataFrame([row], index=pd.DatetimeIndex([ts], name="Datetime"))
    return add_features(df)


def predict_one(model, payload: dict, feature_names: list[str]) -> dict:
    """Prédit l'AQI pour un payload unique ; retourne aqi, catégorie, polluant dominant."""
    engineered = featurize_request(payload)
    X = engineered[feature_names]
    aqi_value = float(model.predict(X)[0])

    dominant = compute_aqi(
        engineered, config.AQI_POLLUTANT_COLUMNS
    )["DominantPollutant"].iloc[0]

    return {
        "aqi": round(aqi_value, 2),
        "category": aqi_category(aqi_value),
        "dominant_pollutant": dominant,
    }


def predict_batch(model, payloads: list[dict], feature_names: list[str]) -> list[dict]:
    """Wrapper pratique vectorisé au-dessus de :func:`predict_one`."""
    return [predict_one(model, p, feature_names) for p in payloads]
