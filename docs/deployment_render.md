# Déploiement sur Render (C13)

Ce guide décrit le déploiement de l'API AQI et du client Streamlit sur
[Render](https://render.com) à partir du **Blueprint** `render.yaml`.

## Ce qui est fourni

| Fichier | Rôle |
|---|---|
| `render.yaml` | Blueprint Render : deux services web Docker (`air-quality-api`, `air-quality-app`). |
| `Dockerfile.render` | Image autonome qui **régénère le modèle au build** puis sert l'API ou Streamlit. |
| `.github/workflows/cd.yml` | Étape « Déployer sur Render » qui appelle un *Deploy Hook* (optionnelle). |

### Pourquoi un Dockerfile dédié ?

Le `Dockerfile` principal fait `COPY models ./models` : il embarque un modèle
**pré-entraîné présent sur le disque local**. Mais ces artefacts ne sont pas
versionnés dans git :

- `models/best_model.joblib` → gitignoré (`models/*.joblib`) ;
- `reports/metrics.json` → non suivi.

Un build Render part d'un clone git *propre* : ces fichiers seraient absents et
l'API échouerait au démarrage (elle charge le modèle et `metrics.json` dans son
`lifespan`). `Dockerfile.render` résout ça en exécutant, pendant le build :

```dockerfile
RUN python scripts/run.py build-target && python scripts/run.py train
```

Le modèle et `metrics.json` sont donc reconstruits *dans l'image*, de façon
déterministe (`RANDOM_STATE=42`, params dans `params.yaml`). L'image reste
auto-suffisante — aucun stockage DVC distant requis.

Il honore aussi `$PORT` (injecté par Render) via une commande shell, et copie
`app/` pour pouvoir servir Streamlit depuis la même image.

## Déploiement en Blueprint (recommandé)

1. Poussez le dépôt sur GitHub/GitLab (avec `render.yaml` et `Dockerfile.render`).
2. Sur [dashboard.render.com](https://dashboard.render.com) → **New** →
   **Blueprint** → sélectionnez le dépôt.
3. Render détecte `render.yaml` et propose de créer les deux services. Validez.
4. Premier build : ~5–10 min (installation des deps + entraînement du modèle).

### Variables d'environnement

Elles sont déclarées dans `render.yaml` ; voici ce que fait Render et ce qui
vous reste à faire :

| Service | Variable | Source | Action |
|---|---|---|---|
| `air-quality-api` | `API_KEY` | `generateValue: true` | Générée automatiquement (secret). |
| `air-quality-api` | `CORS_ORIGINS` | `sync: false` | À renseigner : URL du service Streamlit, ou `*` pour un test. |
| `air-quality-app` | `API_KEY` | `fromService` | Copiée automatiquement depuis l'API (même clé). |
| `air-quality-app` | `API_URL` | `sync: false` | **À renseigner après le 1er déploiement** (voir ci-dessous). |

### L'unique étape manuelle : `API_URL`

Render ne connaît l'URL publique de l'API qu'après le premier déploiement. Une
fois l'API en ligne :

1. Copiez son URL (ex. `https://air-quality-api.onrender.com`).
2. Service `air-quality-app` → **Environment** → `API_URL` = cette URL.
3. **Manual Deploy** du service Streamlit pour prendre en compte la variable.

> Streamlit appelle l'API via `httpx` avec `base_url=API_URL` : l'URL doit
> inclure le schéma `https://` (un simple nom d'hôte échouerait).

## Vérification

```bash
# Santé (public, sans clé) :
curl https://air-quality-api.onrender.com/health
# -> {"status":"ok","model_loaded":true}

# Documentation interactive :
open https://air-quality-api.onrender.com/docs

# Prédiction (clé requise — récupérez API_KEY dans le dashboard de l'API) :
curl -X POST https://air-quality-api.onrender.com/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <API_KEY>" \
  -d '{"CO_GT":2.1,"NOx_GT":180,"NO2_GT":110,"C6H6_GT":8.4,"PT08_S1_CO":1200,"PT08_S2_NMHC":900,"PT08_S3_NOx":800,"PT08_S4_NO2":1500,"PT08_S5_O3":1100,"T":18.2,"RH":48.0,"AH":0.9}'
```

L'application Streamlit est servie sur l'URL du service `air-quality-app`.

## Déploiement continu depuis GitHub Actions (optionnel)

`cd.yml` contient une étape « Déployer sur Render » qui déclenche un
redéploiement via un **Deploy Hook** :

1. Service `air-quality-api` → **Settings** → **Deploy Hook** → copiez l'URL.
2. Dépôt GitHub → **Settings** → **Secrets and variables** → **Actions** →
   nouveau secret `RENDER_DEPLOY_HOOK_URL` = cette URL.
3. À chaque tag `v*` (ou lancement manuel du workflow CD), l'étape appelle le
   hook et Render redéploie. Sans le secret, l'étape est ignorée.

> Alternative : laissez `autoDeploy: true` (déjà dans `render.yaml`). Render
> redéploie automatiquement à chaque push sur la branche suivie — dans ce cas le
> Deploy Hook est redondant.

## Notes et limites

- **Plan `free`** : les services s'endorment après ~15 min d'inactivité ; la
  première requête après réveil est lente (cold start). Le build réentraîne le
  modèle à chaque déploiement — acceptable ici (dataset de 4000 lignes).
- **Région** : `frankfurt` par défaut dans `render.yaml` ; changez `region`
  selon vos besoins (gardez la même pour les deux services).
- **Persistance** : `reports/predictions_log.jsonl` (journal des prédictions)
  est éphémère sur Render (système de fichiers non persistant). Pour le
  conserver, montez un disque Render ou exportez les métriques `/metrics`
  (Prometheus) vers un collecteur externe.
- **`CORS_ORIGINS`** : en production, restreignez-le à l'URL Streamlit plutôt
  que `*`.
