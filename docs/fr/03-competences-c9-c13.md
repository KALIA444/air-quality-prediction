# 4. Correspondance avec les compétences C9–C13

Ce document fait le lien entre chaque compétence visée et sa réalisation concrète
dans le code (utile pour la soutenance / certification).

---

## C9 — Développer une API REST exposant un modèle d'IA

> *« …en respectant ses spécifications fonctionnelles et techniques et les
> standards de qualité et de sécurité du marché… »*

**Réalisation** — Service FastAPI dans `src/air_quality/api/`.

| Exigence | Où |
|----------|----|
| Spécifications fonctionnelles/techniques | `docs/api_spec.md` + schémas Pydantic (`api/schemas.py`) |
| Documentation technique de l'API | OpenAPI auto-générée sur `/docs` et `/redoc` |
| Qualité (validation des entrées) | `Field(ge=…, le=…)` Pydantic → erreur `422` si hors plage |
| Sécurité — authentification | En-tête `X-API-Key` (`api/security.py`) → `401` si absente/invalide |
| Sécurité — CORS, limitation de débit | `CORSMiddleware` + `slowapi` (60/min sur `/predict`) |
| Interaction avec les autres composants | `/predict`, `/predict/batch`, `/model/info`, `/health` |

**Lancer** : `make api` → http://localhost:8000/docs

---

## C10 — Intégrer l'API dans une application (avec normes d'accessibilité)

> *« …à l'aide de la documentation technique de l'API… »*

**Réalisation** — Application Streamlit `app/streamlit_app.py`.

| Exigence | Où |
|----------|----|
| Intégration de l'API | Appels httpx vers `/predict` et `/predict/batch` |
| Usage de la doc technique | Contrat OpenAPI de l'API (`/docs`) |
| Fonctionnalité d'IA | Prédiction d'AQI unitaire + traitement par lot (CSV) |
| Accessibilité | Catégorie signalée par **texte + icône + couleur** (jamais la couleur seule), libellés et aides sur chaque champ, hiérarchie de titres |

**Limite assumée** : Streamlit contrôle mal certains aspects RGAA (ordre de
focus, ARIA complet). Ces limites sont documentées dans l'application ; une page
HTML stricte-RGAA pourrait réutiliser le même endpoint `/predict`.

**Lancer** : `make app` → http://localhost:8501

---

## C11 — Monitorer un modèle d'IA

> *« …en intégrant les outils de collecte, d'alerte et de restitution… »*

**Réalisation** — `src/air_quality/monitoring.py` + instrumentation de l'API.

| Exigence | Où |
|----------|----|
| Collecte (métriques) | Endpoint Prometheus `/metrics` + compteurs personnalisés (`api/main.py`) |
| Collecte (journaux) | Journaux JSON + `reports/predictions_log.jsonl` (`logging_config.py`) |
| Alerte | Dérive (test KS) > seuil → `reports/alerts/` + code de sortie 1 |
| Restitution | Rapport HTML Evidently `reports/drift/drift_report.html` + résumé JSON |
| Amélioration itérative | Le journal des prédictions permet de calculer la dérive sur le trafic réel |

**Lancer** : `make monitor` (ou `... monitor --perturb` pour tester l'alerte)

---

## C12 — Programmer les tests automatisés d'un modèle d'IA

> *« …règles de validation des jeux de données, des étapes de préparation,
> d'entraînement, d'évaluation et de validation du modèle… »*

**Réalisation** — Dossier `tests/` (pytest) + `src/air_quality/validation.py`.

| Étape testée | Fichier |
|--------------|---------|
| Règles de validation des données (pandera) | `validation.py`, `tests/test_validation.py` |
| Préparation — calcul AQI | `tests/test_aqi.py` |
| Préparation — données / features | `tests/test_data.py`, `tests/test_features.py` |
| Entraînement / découpage | `tests/test_modeling.py` |
| **Validation du modèle (seuil R² > 0,9)** | `tests/test_modeling.py` (marqueur `slow`) |
| API (intégration) | `tests/test_api.py` |

Les règles de validation des données sont **aussi appliquées dans le pipeline**
(`data.build_dataset` appelle `validate_raw`/`validate_processed`).

**Lancer** : `make test` (33 tests). Intégration continue : la suite est rejouée
par GitHub Actions.

---

## C13 — Créer une chaîne de livraison continue (approche MLOps)

> *« …automatiser les étapes de validation, de test, de packaging et de
> déploiement du modèle. »*

**Réalisation** — DVC + Docker + GitHub Actions.

| Exigence | Où |
|----------|----|
| Pipeline reproductible | `dvc.yaml` (build_target → train → evaluate) + `params.yaml` |
| Versionnement données/modèle | DVC (`dvc.lock`, cache `.dvc/`) |
| Validation + test (CI) | `.github/workflows/ci.yml` : lint → train → tests → build image |
| Packaging | `Dockerfile` (image API) + `docker-compose.yml` (API + app) |
| Déploiement (CD) | `.github/workflows/cd.yml` : `dvc repro` → publication image GHCR → artefact modèle |
| Qualité avant commit | `.pre-commit-config.yaml` (ruff, hooks) |

**Lancer** : `make dvc-repro` (pipeline), `make docker-up` (conteneurs).

> Hors périmètre : la cible de déploiement cloud n'est pas fixée — la CD s'arrête
> à la publication de l'image et de l'artefact modèle ; l'étape de déploiement est
> un emplacement à compléter selon l'hébergeur.
