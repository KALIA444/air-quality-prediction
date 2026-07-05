# 1. Vue d'ensemble

## Le projet

À partir du jeu de données `AirQualityData.csv` (4000 mesures horaires de
polluants et de météo), l'objectif est de **prédire l'indice de qualité de l'air
(AQI)** puis d'exposer ce modèle via une API, une application, du monitoring, des
tests et une chaîne MLOps.

## La découverte importante sur les données

La colonne `AirQualityIndex` fournie dans le CSV est **du bruit aléatoire** : sa
corrélation avec **toutes** les autres colonnes est inférieure à |0,04|. Aucun
modèle ne peut l'apprendre — le notebook de référence
(`air-quality-prediction.ipynb`) obtient d'ailleurs un **R² négatif** avec la
régression linéaire, Random Forest et XGBoost (RMSE ≈ écart-type de la cible,
c'est-à-dire pas mieux que prédire la moyenne).

**Solution retenue :** on ignore cette colonne et on **recalcule un vrai AQI**
selon la méthode officielle de l'EPA (US Environmental Protection Agency) à
partir des concentrations de polluants (`src/air_quality/aqi.py`). Sur cette
cible réellement apprenable, les mêmes modèles atteignent **R² ≈ 0,999**.

| Modèle | R² (cible bruitée d'origine) | R² (AQI recalculé) |
|--------|------------------------------|--------------------|
| Régression linéaire | −0,01 | 0,74 |
| Random Forest | −0,03 | **0,999** |
| XGBoost | −0,23 | 0,999 |

Les variables les plus importantes (O3, PM2.5, PM10) sont exactement les
polluants qui pilotent la formule EPA : c'est la preuve que le modèle apprend une
structure réelle.

## Ce qui a été construit

Au départ, le dépôt n'était qu'un pipeline de laboratoire (entraînement en ligne
de commande). Il a été transformé en projet déployable couvrant 5 compétences :

| Compétence | Réalisation | Comment lancer |
|------------|-------------|----------------|
| **C9** — API REST | FastAPI : `/predict`, `/predict/batch`, `/health`, `/model/info`, `/metrics`. Validation Pydantic, authentification par clé, CORS, limitation de débit, documentation OpenAPI. | `make api` |
| **C10** — Application | Application Streamlit qui consomme l'API (prédiction unitaire + lot CSV), affichage accessible de la catégorie. | `make app` |
| **C11** — Monitoring | Métriques Prometheus, journaux JSON, journal des prédictions, détection de dérive (drift) avec alerte. | `make monitor` |
| **C12** — Tests automatisés | pytest : calcul AQI, préparation des données, règles de validation (pandera), API, et **seuil de qualité du modèle (R² > 0,9)**. | `make test` |
| **C13** — CI/CD & MLOps | Pipeline DVC, Docker + docker-compose, GitHub Actions (CI/CD), pre-commit. | `make dvc-repro`, `make docker-up` |

La suite de cette documentation explique l'installation puis le démarrage de
chaque service en détail.
