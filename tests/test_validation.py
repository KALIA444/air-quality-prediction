"""Tests des règles de validation du jeu de données (C12 : jeux de données)."""
from __future__ import annotations

import pandas as pd
import pytest
from pandera.errors import SchemaError, SchemaErrors

from air_quality import config
from air_quality.validation import validate_raw


def test_raw_schema_accepts_real_data():
    df = pd.read_csv(config.RAW_CSV)
    validate_raw(df)  # ne doit pas lever d'exception


def test_raw_schema_rejects_negative_pollutant():
    df = pd.read_csv(config.RAW_CSV).copy()
    df.loc[0, "PM2.5"] = -5.0  # concentration impossible
    with pytest.raises((SchemaError, SchemaErrors)):
        validate_raw(df)


def test_raw_schema_rejects_out_of_range_humidity():
    df = pd.read_csv(config.RAW_CSV).copy()
    df.loc[0, "Humidity"] = 150.0  # > 100 %
    with pytest.raises((SchemaError, SchemaErrors)):
        validate_raw(df)
