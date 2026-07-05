"""Charge le CSV brut et y attache la cible AQI calculée."""
from __future__ import annotations

import pandas as pd

from . import config
from .aqi import compute_aqi
from .validation import validate_processed, validate_raw


def load_raw(path=None, validate: bool = True) -> pd.DataFrame:
    """Charge le CSV avec un index ``Datetime`` analysé, Date/Time supprimées.

    Lorsque ``validate`` est vrai, le DataFrame brut est vérifié par rapport à
    :data:`validation.RAW_SCHEMA` avant toute transformation, afin que les
    données invalides échouent rapidement au début du pipeline.
    """
    path = path or config.RAW_CSV
    df = pd.read_csv(path)
    if validate:
        validate_raw(df)
    df["Datetime"] = pd.to_datetime(df[config.DATE_COL] + " " + df[config.TIME_COL])
    df = df.set_index("Datetime").sort_index()
    df = df.drop(columns=[config.DATE_COL, config.TIME_COL])
    return df


def build_dataset(path=None) -> pd.DataFrame:
    """Charge les données brutes, calcule la cible AQI EPA, supprime la cible bruit.

    Le DataFrame retourné conserve toutes les variables d'origine plus une colonne
    ``AQI`` et une étiquette ``DominantPollutant``. La colonne aléatoire d'origine
    ``AirQualityIndex`` est supprimée afin qu'elle ne puisse pas fuiter dans les
    variables.
    """
    df = load_raw(path)
    aqi = compute_aqi(df, config.AQI_POLLUTANT_COLUMNS)
    df[config.TARGET] = aqi[config.TARGET]
    df["DominantPollutant"] = aqi["DominantPollutant"]
    df = df.drop(columns=[config.ORIGINAL_TARGET])
    validate_processed(df)
    return df


def save_processed(df: pd.DataFrame, path=None) -> None:
    path = path or config.PROCESSED_CSV
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
