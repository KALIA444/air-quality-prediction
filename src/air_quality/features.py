"""Ingénierie des variables : encodages temporels et termes d'interaction.

Opère sur le DataFrame retourné par :func:`air_quality.data.build_dataset`.
Toutes les transformations sont sans état et calculées à partir de colonnes
présentes au moment de l'inférence, de sorte que la même fonction s'applique en
toute sécurité aux lignes d'entraînement et de test indépendamment (pas de fuite
fit/transform).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

# Colonnes non-variables qui ne doivent jamais entrer dans la matrice du modèle.
NON_FEATURES = [config.TARGET, "DominantPollutant"]


def _season(month: pd.Series) -> pd.Series:
    # 1 Hiver, 2 Printemps, 3 Été, 4 Automne
    return ((month % 12) // 3 + 1).astype(int)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne une copie de ``df`` avec les colonnes issues de l'ingénierie ajoutées."""
    out = df.copy()

    # Variables calendaires à partir de l'index datetime.
    out["Month"] = out.index.month
    out["Season"] = _season(out["Month"])

    # Encodages cycliques pour que le modèle voie la continuité (23h ~ 0h, déc ~ jan).
    out["Hour_sin"] = np.sin(2 * np.pi * out["Hour"] / 24)
    out["Hour_cos"] = np.cos(2 * np.pi * out["Hour"] / 24)
    out["Month_sin"] = np.sin(2 * np.pi * out["Month"] / 12)
    out["Month_cos"] = np.cos(2 * np.pi * out["Month"] / 12)
    out["Wind_sin"] = np.sin(np.deg2rad(out["WindDirection"]))
    out["Wind_cos"] = np.cos(np.deg2rad(out["WindDirection"]))

    # Interactions motivées physiquement (polluant x météorologie).
    out["PM2.5_Temperature"] = out["PM2.5"] * out["Temperature"]
    out["O3_Humidity"] = out["O3(GT)"] * out["Humidity"]

    return out


def split_X_y(df: pd.DataFrame):
    """Sépare un DataFrame transformé en matrice de variables X et cible y (AQI)."""
    y = df[config.TARGET]
    X = df.drop(columns=[c for c in NON_FEATURES if c in df.columns])
    return X, y
