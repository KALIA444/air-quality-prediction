"""Fixtures pytest partagées."""
from __future__ import annotations

import pandas as pd
import pytest

from air_quality.data import build_dataset


@pytest.fixture(scope="session")
def processed_df() -> pd.DataFrame:
    """Le jeu de données traité complet avec la cible AQI calculée."""
    return build_dataset()


@pytest.fixture
def sample_payload() -> dict:
    """Une charge utile de prédiction unique et valide."""
    return {
        "timestamp": "2024-07-15T14:00:00",
        "co": 3.8, "nox": 172.0, "no2": 144.3, "o3": 118.1, "so2": 1.2,
        "pm25": 147.3, "pm10": 208.8, "temperature": 28.5,
        "humidity": 45.0, "pressure": 1013.2,
        "wind_speed": 6.0, "wind_direction": 210.0,
    }
