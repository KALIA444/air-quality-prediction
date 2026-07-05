"""Chemins centraux et définitions de colonnes pour le pipeline.

Tout ce sur quoi un autre module pourrait devoir s'accorder (où vivent les
fichiers, ce que signifient les colonnes) est défini une seule fois ici. Les
hyperparamètres sont chargés depuis ``params.yaml`` (suivi par DVC), avec les
littéraux ci-dessous comme valeurs par défaut de repli.
"""
from __future__ import annotations

from pathlib import Path

import yaml

# --- Chemins ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = ROOT / "AirQualityData.csv"
DATA_DIR = ROOT / "data"
PROCESSED_CSV = DATA_DIR / "air_quality_with_aqi.csv"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
DRIFT_DIR = REPORTS_DIR / "drift"
ALERTS_DIR = REPORTS_DIR / "alerts"
PREDICTIONS_LOG = REPORTS_DIR / "predictions_log.jsonl"
PARAMS_FILE = ROOT / "params.yaml"


def _load_params() -> dict:
    """Lit params.yaml s'il existe ; retourne {} pour que les appelants utilisent les valeurs par défaut."""
    if PARAMS_FILE.exists():
        with open(PARAMS_FILE) as fh:
            return yaml.safe_load(fh) or {}
    return {}


PARAMS = _load_params()

# --- Colonnes --------------------------------------------------------------
DATE_COL = "Date"
TIME_COL = "Time"

# La cible d'origine. Bruit aléatoire — exclue des variables, jamais modélisée.
ORIGINAL_TARGET = "AirQualityIndex"

# La cible que ce pipeline prédit réellement (calculée dans aqi.py).
TARGET = "AQI"

# Colonnes de polluants qui alimentent le calcul de l'AQI EPA. Associe la colonne
# brute du CSV à la clé de la table des seuils EPA définie dans aqi.py.
AQI_POLLUTANT_COLUMNS = {
    "PM2.5": "pm25",
    "PM10": "pm10",
    "O3(GT)": "o3_8h",
    "CO(GT)": "co_8h",
    "SO2(GT)": "so2_1h",
    "NO2(GT)": "no2_1h",
}

# --- Hyperparamètres (params.yaml surcharge ces valeurs par défaut) --------
_split = PARAMS.get("split", {})
RANDOM_STATE = _split.get("random_state", 42)
TEST_SIZE = _split.get("test_size", 0.2)
CV_FOLDS = _split.get("cv_folds", 5)

# Hyperparamètres par modèle consommés dans modeling.get_models().
MODEL_PARAMS = PARAMS.get("models", {})

# Seuils de monitoring consommés dans monitoring.py.
DRIFT_SHARE_THRESHOLD = PARAMS.get("monitoring", {}).get("drift_share_threshold", 0.5)

# Clé API pour le service REST (surchargeable via env dans security.py).
DEFAULT_API_KEY = "dev-local-key"
