# 2. Installation

## Prérequis

- **Python 3.10+** (le projet est testé avec 3.12)
- **make** (facultatif mais recommandé)
- **Docker** (facultatif, seulement pour `make docker-up`)

## Installation automatique (recommandé)

```bash
make setup
```

Cette commande :
1. crée un environnement virtuel `.venv/` ;
2. met à jour `pip` ;
3. installe le paquet en mode éditable avec toutes les options :
   `pip install -e ".[dev,app,monitoring]"`.

## Installation manuelle

```bash
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -e ".[dev,app,monitoring]"
```

### Les « extras » disponibles

Le fichier `pyproject.toml` définit des groupes de dépendances optionnels :

| Extra | Contenu | Utilité |
|-------|---------|---------|
| (base) | numpy, pandas, scikit-learn, xgboost, fastapi, uvicorn, pandera… | API + pipeline |
| `app` | streamlit, httpx | Application Streamlit (C10) |
| `monitoring` | evidently | Rapport de dérive HTML (C11) |
| `dev` | pytest, ruff, pre-commit, dvc | Tests, qualité, MLOps (C12/C13) |

Exemple pour installer uniquement de quoi servir l'API :

```bash
./.venv/bin/pip install -e .
```

## Vérifier l'installation

```bash
./.venv/bin/python -c "import air_quality; print('OK')"
make test-fast      # lance la suite de tests rapide
```

## Activer le venv (optionnel)

La plupart des commandes `make` utilisent directement `./.venv/bin/python`, donc
activer le venv n'est pas nécessaire. Si vous voulez l'activer malgré tout :

```bash
source .venv/bin/activate     # zsh / bash
```

> ⚠️ **Note DVC** : `dvc repro` lance `python` depuis le `PATH`. Si un Python
> conda/système masque le venv, les étapes échouent. Utilisez `make dvc-repro`
> (qui force le venv en tête du `PATH`) ou activez le venv au préalable.
