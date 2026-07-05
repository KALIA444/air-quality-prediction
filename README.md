# Qualité de l'air — Prédiction de l'AQI

Projet Python qui prédit l'**indice de qualité de l'air (AQI)** à partir de
mesures horaires de polluants et de météo (`AirQualityData.csv`, 4000 lignes,
[source Kaggle](https://www.kaggle.com/datasets/khushikyad001/air-quality-data/data)).

Le projet va plus loin qu'un simple modèle : il fournit aussi une **API REST**,
une **application web**, du **monitoring**, des **tests** et une chaîne
**MLOps** (compétences C9 à C13).

> 📚 **Documentation complète en français** : dossier [`docs/fr/`](docs/fr/README.md).
> Débutant ? Lisez d'abord la [vue d'ensemble](docs/fr/00-vue-ensemble.md) puis le
> [glossaire des outils](docs/fr/05-glossaire-outils.md).

---

## Pour les pressés (3 commandes)

```bash
make setup        # 1) crée l'environnement et installe tout
make all          # 2) prépare la cible AQI, entraîne et évalue le modèle
make api          # 3) lance l'API -> http://localhost:8000/docs
```

> Sans `make` ? Remplacez par l'interpréteur du projet :
> `./.venv/bin/python scripts/run.py all`.

---

## La découverte importante sur les données

La colonne `AirQualityIndex` fournie dans le CSV est **du bruit aléatoire** :
elle n'a aucun lien avec les autres colonnes (corrélation < 0,04 partout). Aucun
modèle ne peut l'apprendre — on obtient un **R² négatif** (pire que prédire la
moyenne).

**Solution :** on ignore cette colonne et on **recalcule un vrai AQI** avec la
formule officielle de l'EPA à partir des polluants (`src/air_quality/aqi.py`).
Sur cette cible, les modèles atteignent **R² ≈ 0,999**.

| Modèle | R² (colonne d'origine, bruitée) | R² (AQI recalculé) |
|--------|---------------------------------|--------------------|
| Régression linéaire | −0,01 | 0,74 |
| Random Forest | −0,03 | **0,999** |
| XGBoost | −0,23 | 0,999 |

---

## Installation

```bash
make setup
```

Cette commande crée un environnement virtuel `.venv/` et installe toutes les
dépendances. Détails et installation manuelle : [`docs/fr/01-installation.md`](docs/fr/01-installation.md).

---

## Utiliser le pipeline (ligne de commande)

⚠️ **Lancez UNE commande à la fois.** La barre `|` dans l'aide signifie
« au choix », ce n'est pas à taper.

```bash
python scripts/run.py build-target   # calcule l'AQI EPA -> data/air_quality_with_aqi.csv
python scripts/run.py train          # entraîne LR/RF/XGB, garde le meilleur modèle
python scripts/run.py evaluate       # tableau de métriques + graphiques
python scripts/run.py monitor        # rapport de dérive des données + alerte

# Tout enchaîner (train puis evaluate) :
python scripts/run.py all
```

Fichiers produits : `models/best_model.joblib` (le modèle), `reports/metrics.json`
(les métriques), `reports/figures/*.png` (les graphiques).

---

## Les services (API, application, monitoring, tests, MLOps)

| Domaine | Quoi | Lancer |
|---------|------|--------|
| **API REST** (C9) | FastAPI : `/predict`, `/predict/batch`, `/health`, `/model/info`, `/metrics`. Validation des entrées, clé API, documentation auto sur `/docs`. | `make api` → http://localhost:8000/docs |
| **Application** (C10) | Application Streamlit qui interroge l'API (saisie unique + lot CSV). | `make app` → http://localhost:8501 |
| **Monitoring** (C11) | Métriques Prometheus, journaux, détection de dérive avec alerte. | `make monitor` |
| **Tests** (C12) | pytest : calcul AQI, validation des données, API, seuil de qualité du modèle. | `make test` |
| **MLOps** (C13) | Pipeline DVC, Docker + compose, GitHub Actions, pre-commit, déploiement cloud Render. | `make dvc-repro`, `make docker-up` |

Guide pas à pas de chaque service : [`docs/fr/02-demarrage-services.md`](docs/fr/02-demarrage-services.md).

### Exemple d'appel à l'API

```bash
make api  # puis, dans un autre terminal :
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: dev-local-key" -H "Content-Type: application/json" \
  -d '{"co":3.8,"nox":172,"no2":144.3,"o3":118.1,"so2":1.2,"pm25":147.3,
       "pm10":208.8,"temperature":28.5,"humidity":45,"pressure":1013.2,
       "wind_speed":6,"wind_direction":210}'
# {"aqi":213.98,"category":"Très mauvais","dominant_pollutant":"O3(GT)"}
```

---

## Comment l'AQI est calculé

Pour chaque polluant, la concentration est convertie en sous-indice via la table
de seuils de l'EPA (interpolation linéaire) ; l'AQI global est le **maximum** des
sous-indices (le polluant dominant). PM2.5/PM10 sont en µg/m³ ; les gaz sont
supposés en CO→ppm et O3/NO2/SO2→ppb. NOx n'est pas un polluant AQI officiel : il
reste une simple variable explicative. Détails dans `src/air_quality/aqi.py`.

> Accessibilité : Streamlit a des limites RGAA/WCAG. L'application associe couleur
> **+ texte + icône** (jamais la couleur seule) et documente les limites
> restantes ; la même route `/predict` pourrait alimenter une page HTML
> strictement accessible si besoin.

---

## Organisation du projet

```
src/air_quality/   aqi · data · features · modeling · evaluate · config
                   inference · validation · monitoring · logging_config · cli
src/air_quality/api/   service FastAPI : main · schemas · security
app/streamlit_app.py   application Streamlit (C10)
tests/             suite pytest, dont validation des données + seuil modèle (C12)
scripts/run.py     ligne de commande : build-target | train | evaluate | all | monitor
dvc.yaml params.yaml   pipeline reproductible (C13)
Dockerfile docker-compose.yml   conteneurs (C13)
Dockerfile.render render.yaml   déploiement Render (C13)
.github/workflows/     ci.yml · cd.yml (C13)
docs/api_spec.md       spécification de l'API (C9)
docs/deployment_render.md   guide de déploiement Render (C13)
docs/fr/               documentation en français
data/ models/ reports/   fichiers générés : données, modèle, métriques, graphiques
```

## Déploiement cloud (Render)

L'API et l'application Streamlit se déploient sur [Render](https://render.com)
via le **Blueprint** `render.yaml` (deux services web Docker).

```
Dashboard Render → New → Blueprint → sélectionner ce dépôt
```

Render lit `render.yaml`, construit `Dockerfile.render` (qui **régénère le
modèle au build** — les artefacts ne sont pas versionnés dans git) et crée
`air-quality-api` + `air-quality-app`. La clé `API_KEY` est générée pour l'API
et partagée avec Streamlit ; il reste **une** variable à renseigner à la main
après le premier déploiement : `API_URL` (l'URL publique de l'API) sur le
service Streamlit. Détails complets, variables d'environnement et déclenchement
depuis la CI : **[docs/deployment_render.md](docs/deployment_render.md)**.
