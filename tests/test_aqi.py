"""Tests unitaires du calcul de l'AQI EPA face à des points de référence connus."""
from __future__ import annotations

import numpy as np
import pytest

from air_quality.aqi import aqi_category, compute_aqi, sub_index


@pytest.mark.parametrize(
    "conc,pollutant,expected",
    [
        (12.0, "pm25", 50),    # haut de « Bon »
        (35.4, "pm25", 100),   # haut de « Modéré »
        (0.0, "pm25", 0),      # plancher
        (54, "pm10", 50),
        (4.4, "co_8h", 50),
    ],
)
def test_sub_index_breakpoint_endpoints(conc, pollutant, expected):
    got = sub_index(np.array([conc]), pollutant)[0]
    assert got == pytest.approx(expected, abs=1)


def test_sub_index_caps_above_table():
    # PM2.5 très au-dessus du seuil le plus élevé est plafonné à 500.
    assert sub_index(np.array([10_000.0]), "pm25")[0] == 500


def test_sub_index_nan_for_negative():
    assert np.isnan(sub_index(np.array([-1.0]), "pm25")[0])


def test_compute_aqi_is_rowwise_max():
    import pandas as pd

    df = pd.DataFrame({"PM2.5": [12.0], "O3(GT)": [200.0]})  # O3 200 ppb -> 0.2 ppm
    out = compute_aqi(df, {"PM2.5": "pm25", "O3(GT)": "o3_8h"})
    # Le sous-indice O3 (haut de la table, AQI 300) doit dominer PM2.5 (AQI 50).
    assert out["AQI"].iloc[0] == max(out["AQI_PM2.5"].iloc[0], out["AQI_O3(GT)"].iloc[0])
    assert out["DominantPollutant"].iloc[0] == "O3(GT)"


@pytest.mark.parametrize(
    "value,label",
    [(25, "Bon"), (75, "Modéré"), (125, "Mauvais pour groupes sensibles"),
     (175, "Mauvais"), (250, "Très mauvais"), (450, "Dangereux")],
)
def test_aqi_category_bands(value, label):
    assert aqi_category(value) == label
