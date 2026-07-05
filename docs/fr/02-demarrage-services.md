# 3. Démarrage des services

Ce guide détaille comment lancer **chaque service**, dans l'ordre logique.
Toutes les commandes se lancent depuis la racine du projet.

---

## Étape 0 — Préparer le modèle (obligatoire la première fois)

L'API et l'application ont besoin d'un modèle entraîné
(`models/best_model.joblib`) et de ses métriques (`reports/metrics.json`).

```bash
make all
```

Équivalent détaillé :

```bash
./.venv/bin/python scripts/run.py build-target   # calcule l'AQI EPA -> data/
./.venv/bin/python scripts/run.py train          # entraîne LR/RF/XGB, garde le meilleur
./.venv/bin/python scripts/run.py evaluate        # graphiques + tableau de métriques
```

Artefacts produits :
- `data/air_quality_with_aqi.csv` — jeu de données avec la cible AQI
- `models/best_model.joblib` — meilleur modèle (pipeline scikit-learn)
- `reports/metrics.json` — métriques + liste ordonnée des variables
- `reports/figures/*.png` — graphiques

---

## Service 1 — API REST (C9)

```bash
make api
```

Équivalent :

```bash
./.venv/bin/python -m uvicorn air_quality.api.main:app --reload --port 8000
```

- **URL** : http://localhost:8000
- **Documentation interactive (Swagger)** : http://localhost:8000/docs
- **Documentation alternative (ReDoc)** : http://localhost:8000/redoc
- **Arrêt** : `Ctrl+C`

### Authentification

Les routes de prédiction exigent l'en-tête `X-API-Key`. La clé est lue dans la
variable d'environnement `API_KEY` (valeur par défaut en local : `dev-local-key`).

```bash
export API_KEY="ma-cle-secrete"   # avant de lancer make api, en production
```

### Exemple d'appel

```bash
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: dev-local-key" -H "Content-Type: application/json" \
  -d '{"co":3.8,"nox":172,"no2":144.3,"o3":118.1,"so2":1.2,"pm25":147.3,
       "pm10":208.8,"temperature":28.5,"humidity":45,"pressure":1013.2,
       "wind_speed":6,"wind_direction":210}'
# Réponse : {"aqi":213.98,"category":"Very Unhealthy","dominant_pollutant":"O3(GT)"}
```

### Principales routes

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/health` | non | État du service + modèle chargé |
| GET | `/model/info` | non | Modèle retenu, variables, métriques |
| POST | `/predict` | oui | Prédiction unitaire |
| POST | `/predict/batch` | oui | Jusqu'à 1000 prédictions |
| GET | `/metrics` | non | Métriques Prometheus |
| GET | `/docs` | non | Documentation OpenAPI |

Spécification complète : [`docs/api_spec.md`](../api_spec.md).

---

## Service 2 — Application Streamlit (C10)

> ⚠️ L'API (Service 1) doit tourner pour que l'application fonctionne.

Dans un **second terminal** :

```bash
make app
```

Équivalent :

```bash
./.venv/bin/python -m streamlit run app/streamlit_app.py
```

- **URL** : http://localhost:8501
- **Arrêt** : `Ctrl+C`

### Configuration

L'application lit deux variables d'environnement :

```bash
export API_URL="http://localhost:8000"   # où joindre l'API
export API_KEY="dev-local-key"           # clé envoyée à l'API
```

### Fonctionnalités

- **Onglet « Single »** : formulaire de saisie d'une mesure → AQI prédit +
  catégorie (texte + icône + couleur) + polluant dominant.
- **Onglet « Batch »** : import d'un CSV → tableau de prédictions téléchargeable.

> Accessibilité : Streamlit offre un contrôle limité sur les normes RGAA/WCAG.
> La catégorie est signalée par **texte + icône + couleur** (jamais la couleur
> seule). Les limites résiduelles sont indiquées dans l'application.

---

## Service 3 — Monitoring / dérive des données (C11)

```bash
make monitor
```

Équivalent :

```bash
./.venv/bin/python scripts/run.py monitor
```

Compare le jeu de données de référence (entraînement) à un lot courant et :
- écrit un rapport HTML : `reports/drift/drift_report.html`
- écrit un résumé JSON : `reports/drift/drift_summary.json`
- si la part de colonnes en dérive dépasse le seuil
  (`drift_share_threshold` dans `params.yaml`), écrit une alerte
  `reports/alerts/drift_alert.json` et **sort avec le code 1**.

### Tester l'alerte (dérive simulée)

```bash
./.venv/bin/python scripts/run.py monitor --perturb
echo "code de sortie : $?"    # 1 = alerte déclenchée
```

### Métriques temps réel

Quand l'API tourne, les métriques Prometheus sont exposées :

```bash
# http://localhost:8000/metrics
# Exemples de métriques personnalisées :
#   aqi_predictions_total{category="..."}   nombre de prédictions par catégorie
#   aqi_prediction_value                     distribution des AQI prédits
#   aqi_prediction_errors_total              erreurs de prédiction
```

Chaque prédiction servie est aussi journalisée (JSON) dans
`reports/predictions_log.jsonl`.

---

## Service 4 — Tests automatisés (C12)

```bash
make test          # suite rapide PUIS seuil de qualité du modèle (lent)
make test-fast     # uniquement la suite rapide
```

Équivalents :

```bash
./.venv/bin/python -m pytest -m "not slow"     # rapide
./.venv/bin/python -m pytest -m slow            # seuil de qualité du modèle (R² > 0,9)
./.venv/bin/python -m pytest tests/test_api.py  # un seul fichier
./.venv/bin/python -m pytest tests/test_api.py::test_health   # un seul test
```

Qualité du code :

```bash
make lint          # ruff
```

---

## Service 5 — Pipeline reproductible DVC (C13)

```bash
make dvc-repro
```

Rejoue les étapes `build-target → train → evaluate` en ne recalculant que ce qui
a changé (données ou `params.yaml`). Produit/actualise `dvc.lock`.

> ⚠️ Utilisez bien `make dvc-repro` (et non `dvc repro` directement) pour éviter
> le conflit d'interpréteur Python décrit dans l'installation.

---

## Service 6 — Conteneurs Docker (C13)

Lance l'API **et** l'application ensemble :

```bash
make docker-up
```

Équivalent :

```bash
docker compose up --build
```

- API : http://localhost:8000
- Application : http://localhost:8501
- **Arrêt** : `Ctrl+C`, puis `docker compose down`

Construire uniquement l'image de l'API :

```bash
make docker-build
# ou : docker build -t air-quality-api:latest .
```

---

## Récapitulatif des ports

| Service | Port | URL |
|---------|------|-----|
| API REST | 8000 | http://localhost:8000/docs |
| Application Streamlit | 8501 | http://localhost:8501 |

## Récapitulatif des variables d'environnement

| Variable | Défaut | Utilisée par |
|----------|--------|--------------|
| `API_KEY` | `dev-local-key` | API (auth) + application |
| `API_URL` | `http://localhost:8000` | application |
| `CORS_ORIGINS` | `*` | API (CORS) |
