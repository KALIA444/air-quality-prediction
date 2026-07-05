"""Tests du feature engineering (C12 : étape de préparation des données)."""
from __future__ import annotations

from air_quality import config
from air_quality.features import add_features, split_X_y

EXPECTED_ENGINEERED = {
    "Month", "Season", "Hour_sin", "Hour_cos", "Month_sin", "Month_cos",
    "Wind_sin", "Wind_cos", "PM2.5_Temperature", "O3_Humidity",
}


def test_add_features_creates_expected_columns(processed_df):
    eng = add_features(processed_df)
    assert EXPECTED_ENGINEERED.issubset(eng.columns)


def test_cyclical_encodings_in_unit_range(processed_df):
    eng = add_features(processed_df)
    for col in ["Hour_sin", "Hour_cos", "Month_sin", "Month_cos", "Wind_sin", "Wind_cos"]:
        assert eng[col].between(-1, 1).all()


def test_no_nans_introduced(processed_df):
    eng = add_features(processed_df)
    assert not eng[list(EXPECTED_ENGINEERED)].isna().any().any()


def test_split_X_y_excludes_non_features(processed_df):
    X, y = split_X_y(add_features(processed_df))
    assert config.TARGET not in X.columns
    assert "DominantPollutant" not in X.columns
    assert y.name == config.TARGET
    assert len(X) == len(y)
