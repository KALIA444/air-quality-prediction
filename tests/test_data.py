"""Tests de la construction du jeu de données (C12 : étape de préparation des données)."""
from __future__ import annotations

import pandas as pd

from air_quality import config


def test_target_added_and_noise_dropped(processed_df):
    assert config.TARGET in processed_df.columns
    assert config.ORIGINAL_TARGET not in processed_df.columns  # bruit retiré


def test_datetime_index_sorted(processed_df):
    assert isinstance(processed_df.index, pd.DatetimeIndex)
    assert processed_df.index.is_monotonic_increasing


def test_aqi_in_valid_range(processed_df):
    aqi = processed_df[config.TARGET]
    assert aqi.between(0, 500).all()


def test_dominant_pollutant_is_known(processed_df):
    known = set(config.AQI_POLLUTANT_COLUMNS)
    assert set(processed_df["DominantPollutant"].unique()).issubset(known)
