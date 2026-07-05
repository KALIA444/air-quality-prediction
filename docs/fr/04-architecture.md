# 5. Architecture

## Arborescence

```
Mari-E3/
├── AirQualityData.csv            # données brutes (4000 lignes)
├── params.yaml                   # hyperparamètres (suivis par DVC)
├── pyproject.toml                # paquet + dépendances + config pytest/ruff
├── dvc.yaml                      # pipeline reproductible (C13)
├── Dockerfile, docker-compose.yml
├── Makefile                      # raccourcis de commandes
│
├── src/air_quality/              # le paquet Python
│   ├── config.py                 # chemins, colonnes, lecture de params.yaml
│   ├── aqi.py                    # calcul de l'AQI EPA (formule officielle)
│   ├── data.py                   # chargement + validation + cible AQI
│   ├── features.py               # ingénierie des variables
│   ├── modeling.py               # entraînement / comparaison des modèles
│   ├── evaluate.py               # métriques + graphiques
│   ├── validation.py             # règles pandera (C12)
│   ├── inference.py              # featurisation partagée API + app
│   ├── monitoring.py             # détection de dérive + alerte (C11)
│   ├── logging_config.py         # journaux JSON + journal des prédictions
│   ├── cli.py                    # ligne de commande
│   └── api/                      # service FastAPI (C9)
│       ├── main.py               # routes + métriques Prometheus
│       ├── schemas.py            # modèles Pydantic (validation des entrées)
│       └── security.py           # clé API, CORS, limitation de débit
│
├── app/streamlit_app.py          # application cliente (C10)
├── tests/                        # suite pytest (C12)
├── scripts/run.py                # point d'entrée CLI
├── docs/                         # api_spec.md + docs/fr/
└── .github/workflows/            # ci.yml, cd.yml (C13)
```

## Flux de données (pipeline d'entraînement)

```
AirQualityData.csv
   │  data.load_raw()  ── validation pandera (validation.py)
   ▼
calcul de l'AQI EPA  (aqi.compute_aqi)  ── on supprime la colonne bruitée
   │  data.build_dataset()
   ▼
ingénierie des variables  (features.add_features)
   │  modeling.prepare_splits()  ── découpage train/test (random_state=42)
   ▼
entraînement LR / RF / XGBoost dans un Pipeline([StandardScaler, modèle])
   │  modeling.train_and_evaluate()  ── sélection par R² test
   ▼
models/best_model.joblib  +  reports/metrics.json
   │  evaluate.run()
   ▼
graphiques  reports/figures/*.png
```

## Flux d'inférence (API et application)

```
Requête (mesures + horodatage)
   │  api/schemas.py  ── validation Pydantic (plages de valeurs)
   ▼
inference.featurize_request()
   │  reconstruit EXACTEMENT les variables attendues (ordre de reports/metrics.json)
   │  réutilise features.add_features()
   ▼
modèle.predict()  →  inference.predict_one()
   ▼
Réponse : { aqi, category, dominant_pollutant }
   │  + métriques Prometheus, + journal des prédictions
```

## Principes de conception importants

- **Un seul chemin d'inférence** : l'API et l'application appellent toutes deux
  `inference.predict_one`. La featurisation ne peut donc pas diverger entre les
  deux.
- **Pas de fuite de données** (data leakage) : la normalisation (`StandardScaler`)
  est dans le `Pipeline` scikit-learn — elle est apprise sur le pli
  d'entraînement uniquement, jamais sur tout le jeu de données.
- **Déterminisme** : `config.RANDOM_STATE` (42) est l'unique source du découpage,
  donc `train` et `evaluate` voient le même jeu de test entre deux exécutions.
- **L'ordre des variables est un contrat** : l'API aligne les entrées sur la
  liste `features` de `reports/metrics.json`. Il faut **réentraîner** dès que
  l'ensemble des variables change, sinon `/predict` mélangerait les colonnes.
- **Les hyperparamètres vivent dans `params.yaml`** (suivis par DVC), pas dans le
  code ; `config.py` les lit avec des valeurs par défaut de repli.

## Hypothèses sur le calcul de l'AQI

Pour chaque polluant, la concentration est convertie en sous-indice via la table
de seuils EPA (interpolation linéaire) ; l'AQI global est le **maximum** des
sous-indices (polluant dominant). PM2.5/PM10 sont utilisés directement en µg/m³ ;
les gaz sont supposés en CO→ppm et O3/NO2/SO2→ppb. NOx n'est pas un polluant AQI
officiel : il reste une variable explicative. Détails dans `src/air_quality/aqi.py`.
