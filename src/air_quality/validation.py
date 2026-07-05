"""Schémas pandera — les règles de validation du jeu de données (C12).

Ils encodent le contrat que les données doivent satisfaire avant toute
préparation, entraînement ou mise en service. ``data.build_dataset`` appelle
:func:`validate_raw` et :func:`validate_processed` ; la suite de tests réutilise
les mêmes schémas pour vérifier que les données valides passent et que les
données corrompues sont rejetées.

Les bornes sont délibérément un peu plus larges que les plages observées : elles
attrapent les corruptions grossières (concentrations négatives, humidité
impossible) sans rejeter les valeurs extrêmes légitimes.
"""
from __future__ import annotations

from pandera.pandas import Check, Column, DataFrameSchema

# Bornes physiquement significatives par colonne brute.
_NONNEG = Check.ge(0)

RAW_SCHEMA = DataFrameSchema(
    {
        "Date": Column(str),
        "Time": Column(str),
        "CO(GT)": Column(float, _NONNEG),
        "NOx(GT)": Column(float, _NONNEG),
        "NO2(GT)": Column(float, _NONNEG),
        "O3(GT)": Column(float, _NONNEG),
        "SO2(GT)": Column(float, _NONNEG),
        "PM2.5": Column(float, _NONNEG),
        "PM10": Column(float, _NONNEG),
        "Temperature": Column(float, [Check.ge(-50), Check.le(60)]),
        "Humidity": Column(float, [Check.ge(0), Check.le(100)]),
        "Pressure": Column(float, [Check.ge(870), Check.le(1085)]),
        "WindSpeed": Column(float, _NONNEG),
        "WindDirection": Column(float, [Check.ge(0), Check.le(360)]),
        "CO_NOx_Ratio": Column(float, _NONNEG),
        "NOx_NO2_Ratio": Column(float, _NONNEG),
        "Temp_Humidity_Index": Column(float),
        "AirQualityIndex": Column(float, [Check.ge(0), Check.le(500)]),
        "CO_MA3": Column(float, _NONNEG),
        "NO2_MA3": Column(float, _NONNEG),
        "O3_MA3": Column(float, _NONNEG),
        "DayOfWeek": Column(int, [Check.ge(0), Check.le(6)]),
        "Hour": Column(int, [Check.ge(0), Check.le(23)]),
    },
    coerce=True,
    strict=False,  # tolère les colonnes supplémentaires
)

# DataFrame traité : index Datetime, cible bruit d'origine supprimée, AQI ajouté.
PROCESSED_SCHEMA = DataFrameSchema(
    {
        "AQI": Column(float, [Check.ge(0), Check.le(500)]),
        "DominantPollutant": Column(
            str, Check.isin(["PM2.5", "PM10", "O3(GT)", "CO(GT)", "SO2(GT)", "NO2(GT)"])
        ),
    },
    coerce=True,
    strict=False,
)


def validate_raw(df):
    """Valide un DataFrame CSV brut ; lève ``pandera.errors.SchemaError`` en cas d'échec."""
    return RAW_SCHEMA.validate(df, lazy=True)


def validate_processed(df):
    """Valide un DataFrame traité portant la cible AQI calculée."""
    return PROCESSED_SCHEMA.validate(df, lazy=True)
