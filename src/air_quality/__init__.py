"""Pipeline ML de qualité de l'air.

Le CSV fournit une colonne ``AirQualityIndex`` statistiquement indépendante de
chaque variable (|r de Pearson| < 0.04 pour toutes les colonnes), elle est donc
inapprenable. Ce package ignore cette colonne et dérive à la place un véritable
AQI de type EPA à partir des concentrations de polluants (voir
:mod:`air_quality.aqi`) et modélise CETTE cible.
"""

__all__ = ["config", "aqi", "data", "features", "modeling", "evaluate"]
