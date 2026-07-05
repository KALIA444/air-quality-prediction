"""Calcule un véritable indice de qualité de l'air de type EPA à partir des concentrations de polluants.

Raison d'être
-------------
La colonne ``AirQualityIndex`` du CSV est un bruit uniforme (non corrélé à
chaque feature), donc aucun modèle ne peut la prédire. Ici nous construisons une
cible *apprenable* : l'AQI de l'US EPA, qui est une fonction déterministe et
linéaire par morceaux des concentrations de polluants. Un modèle alimenté avec
les colonnes de polluants peut la retrouver avec un R² élevé.

Méthode (EPA 454/B-18-007)
--------------------------
Pour chaque polluant p de concentration C, trouver l'intervalle de seuils
[BP_lo, BP_hi] contenant C et interpoler linéairement l'indice :

    I_p = (I_hi - I_lo) / (BP_hi - BP_lo) * (C - BP_lo) + I_lo

L'AQI global est le sous-indice maximal parmi les polluants (le polluant
« dominant » détermine l'AQI).

Hypothèses d'unités pour ce jeu de données synthétique
------------------------------------------------------
PM2.5 / PM10 sont déjà dans des plages plausibles en µg/m³ et utilisées
directement. Les colonnes gazeuses sont traitées ainsi : CO → ppm, O3/NO2/SO2 →
ppb (O3 est converti en ppm pour la table sur 8 heures). NOx n'est *pas* un
polluant de l'AQI EPA et est volontairement exclu — il reste uniquement une
feature. Ces hypothèses sont documentées afin que la cible dérivée soit
reproductible, et non présentée comme une vérité terrain.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Chaque tuple : (C_lo, C_hi, I_lo, I_hi). Concentrations dans l'unité indiquée.
# Catégories : Bon 0-50, Modéré 51-100, USG 101-150, Mauvais 151-200,
# Très mauvais 201-300, Dangereux 301-500.
BREAKPOINTS: dict[str, list[tuple[float, float, int, int]]] = {
    # PM2.5, 24 h, µg/m³ (table EPA d'avant 2024)
    "pm25": [
        (0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400), (350.5, 500.4, 401, 500),
    ],
    # PM10, 24 h, µg/m³
    "pm10": [
        (0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
        (255, 354, 151, 200), (355, 424, 201, 300),
        (425, 504, 301, 400), (505, 604, 401, 500),
    ],
    # O3, 8 h, ppm
    "o3_8h": [
        (0.000, 0.054, 0, 50), (0.055, 0.070, 51, 100), (0.071, 0.085, 101, 150),
        (0.086, 0.105, 151, 200), (0.106, 0.200, 201, 300),
    ],
    # CO, 8 h, ppm
    "co_8h": [
        (0.0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150),
        (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300),
        (30.5, 40.4, 301, 400), (40.5, 50.4, 401, 500),
    ],
    # SO2, 1 h, ppb
    "so2_1h": [
        (0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150),
        (186, 304, 151, 200), (305, 604, 201, 300),
        (605, 804, 301, 400), (805, 1004, 401, 500),
    ],
    # NO2, 1 h, ppb
    "no2_1h": [
        (0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150),
        (361, 649, 151, 200), (650, 1249, 201, 300),
        (1250, 1649, 301, 400), (1650, 2049, 401, 500),
    ],
}

# Troncature des concentrations (décimales) selon l'EPA avant consultation de la table.
_TRUNCATE = {"pm25": 1, "pm10": 0, "o3_8h": 3, "co_8h": 1, "so2_1h": 0, "no2_1h": 0}

# Conversion appliquée à la colonne CSV brute avant son entrée dans la table.
# La colonne O3 est supposée en ppb -> convertie en ppm pour la table sur 8 heures.
_SCALE = {"o3_8h": 1e-3}


def _truncate(values: np.ndarray, decimals: int) -> np.ndarray:
    factor = 10.0**decimals
    return np.floor(values * factor) / factor


def sub_index(concentration: np.ndarray, pollutant: str) -> np.ndarray:
    """Sous-indice EPA vectorisé pour un seul polluant.

    Les concentrations au-dessus du seuil le plus élevé de la table sont
    plafonnées à l'indice maximal (500) ; les concentrations négatives/NaN
    donnent NaN.
    """
    table = BREAKPOINTS[pollutant]
    c = np.asarray(concentration, dtype=float) * _SCALE.get(pollutant, 1.0)
    c = _truncate(c, _TRUNCATE[pollutant])

    out = np.full(c.shape, np.nan, dtype=float)
    top_index = table[-1][3]
    top_conc = table[-1][1]

    for c_lo, c_hi, i_lo, i_hi in table:
        mask = (c >= c_lo) & (c <= c_hi)
        out[mask] = (i_hi - i_lo) / (c_hi - c_lo) * (c[mask] - c_lo) + i_lo

    # Au-dessus du seuil le plus élevé -> plafonner à l'indice maximal.
    out[c > top_conc] = top_index
    return np.round(out)


# Plages de catégories de l'AQI EPA : (borne_supérieure_incluse, label).
_CATEGORY_BANDS = [
    (50, "Bon"),
    (100, "Modéré"),
    (150, "Mauvais pour groupes sensibles"),
    (200, "Mauvais"),
    (300, "Très mauvais"),
    (500, "Dangereux"),
]


def aqi_category(value: float) -> str:
    """Associe une valeur d'AQI à son label de catégorie EPA."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "Inconnu"
    for upper, label in _CATEGORY_BANDS:
        if value <= upper:
            return label
    return "Dangereux"


def compute_aqi(df: pd.DataFrame, pollutant_columns: dict[str, str]) -> pd.DataFrame:
    """Renvoie les sous-indices par polluant, l'AQI global et le polluant dominant.

    Paramètres
    ----------
    df : DataFrame source contenant les colonnes brutes de polluants.
    pollutant_columns : associe le nom de colonne brute -> clé de la table de seuils.

    Renvoie un DataFrame avec les colonnes ``AQI_<raw>`` pour chaque polluant,
    ``AQI`` (maximum par ligne) et ``DominantPollutant``.
    """
    sub = pd.DataFrame(index=df.index)
    for raw_col, table_key in pollutant_columns.items():
        sub[f"AQI_{raw_col}"] = sub_index(df[raw_col].to_numpy(), table_key)

    aqi = sub.max(axis=1)
    dominant = sub.idxmax(axis=1).str.replace("AQI_", "", regex=False)

    result = sub.copy()
    result["AQI"] = aqi
    result["DominantPollutant"] = dominant
    return result
