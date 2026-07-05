# 6. Les outils expliqués simplement (pour débutant)

Ce projet utilise plusieurs outils. Voici **à quoi sert chacun**, avec une image
simple et le rôle qu'il joue **ici**. Pas besoin de tout connaître pour
commencer.

---

## 🧠 Le cœur : entraîner le modèle

### scikit-learn
- **C'est quoi ?** La boîte à outils de référence du machine learning en Python.
  Elle fournit des modèles tout faits (régression, forêts aléatoires…) et des
  outils pour préparer les données.
- **Image** : une caisse à outils standard pour construire un modèle prédictif.
- **Ici** : la régression linéaire et le Random Forest, plus le `StandardScaler`
  (mise à l'échelle des données) et le découpage entraînement/test.

### XGBoost
- **C'est quoi ?** Un modèle très performant qui combine des centaines de petits
  « arbres de décision » pour faire de meilleures prédictions.
- **Image** : au lieu d'un seul expert, on demande son avis à des centaines
  d'experts et on combine intelligemment leurs réponses.
- **Ici** : un des 3 modèles comparés. On garde automatiquement le meilleur.

### pandas / NumPy
- **C'est quoi ?** pandas manipule des tableaux de données (comme un Excel en
  code) ; NumPy fait les calculs numériques rapides.
- **Image** : pandas = le tableur, NumPy = la calculatrice scientifique.
- **Ici** : lire le CSV, calculer l'AQI, préparer les variables.

### joblib
- **C'est quoi ?** Sert à **sauvegarder** un modèle entraîné dans un fichier et à
  le **recharger** plus tard.
- **Image** : « enregistrer sous… » pour un modèle.
- **Ici** : `models/best_model.joblib` est le modèle sauvegardé que l'API
  recharge.

---

## 🌐 Exposer le modèle : l'API (C9)

### FastAPI
- **C'est quoi ?** Un outil pour créer une **API REST** : un programme qui répond
  à des requêtes envoyées par Internet (ex. « voici des mesures, donne-moi
  l'AQI »).
- **Image** : un **guichet** ou un **serveur de restaurant** : on passe une
  commande (la requête), il revient avec le plat (la réponse).
- **Pourquoi ?** Pour que d'autres programmes (site web, application…) puissent
  utiliser le modèle sans connaître son fonctionnement interne.
- **Bonus** : FastAPI génère **tout seul** une page de documentation interactive
  sur `/docs`.

### uvicorn
- **C'est quoi ?** Le **serveur** qui fait réellement tourner l'application
  FastAPI et écoute les requêtes sur un port (ici 8000).
- **Image** : le moteur sous le capot ; FastAPI écrit la logique, uvicorn la fait
  tourner.
- **Ici** : `uvicorn air_quality.api.main:app --port 8000`.

### Pydantic
- **C'est quoi ?** Vérifie que les données reçues ont **le bon format** et sont
  dans les **bonnes plages** (ex. humidité entre 0 et 100).
- **Image** : un **videur** à l'entrée : si la requête est mal formée, elle est
  refusée (erreur 422) avant d'atteindre le modèle.
- **Ici** : `api/schemas.py` décrit chaque champ attendu.

### Clé d'API (X-API-Key)
- **C'est quoi ?** Un **mot de passe** envoyé dans l'en-tête de la requête pour
  prouver qu'on a le droit d'utiliser l'API.
- **Image** : un **badge d'accès**. Sans badge → porte fermée (erreur 401).
- **Ici** : géré dans `api/security.py`.

---

## 🖥️ L'application pour l'utilisateur (C10)

### Streamlit
- **C'est quoi ?** Un outil pour créer une **application web** (avec formulaires,
  boutons, graphiques) **uniquement en Python**, sans écrire de HTML/JavaScript.
- **Image** : un **kit de montage rapide** d'interface : on décrit les champs, il
  fabrique la page web.
- **Pourquoi ?** Pour offrir une interface simple où l'on saisit des mesures et
  où l'on voit l'AQI prédit, sans toucher à l'API directement.
- **Ici** : `app/streamlit_app.py` — l'application appelle l'API en coulisses.

### httpx
- **C'est quoi ?** Une bibliothèque pour **envoyer des requêtes** à une API depuis
  du code Python.
- **Image** : le **téléphone** que l'application utilise pour « appeler » l'API.
- **Ici** : l'application Streamlit s'en sert pour joindre `/predict`.

---

## 📊 Surveiller le modèle : monitoring (C11)

### Prometheus (via prometheus-client)
- **C'est quoi ?** Un standard pour **collecter des métriques** (combien de
  prédictions, temps de réponse, erreurs…). L'API expose ces chiffres sur
  `/metrics`.
- **Image** : le **tableau de bord** d'une voiture (vitesse, température…), mais
  pour le service.
- **Ici** : compteurs comme `aqi_predictions_total`.

### Evidently
- **C'est quoi ?** Un outil qui détecte la **dérive des données** (« data
  drift ») : quand les nouvelles données ne ressemblent plus à celles de
  l'entraînement, signe que le modèle pourrait se dégrader.
- **Image** : une **alarme** qui prévient quand le monde a changé et qu'il faut
  peut-être réentraîner.
- **Ici** : génère le rapport HTML `reports/drift/drift_report.html`.

### Journaux JSON (logs)
- **C'est quoi ?** Un **carnet de bord** : chaque prédiction est enregistrée
  ligne par ligne dans un fichier.
- **Image** : le **livre de comptes** du service.
- **Ici** : `reports/predictions_log.jsonl`.

---

## ✅ Vérifier que tout marche : tests (C12)

### pytest
- **C'est quoi ?** L'outil qui lance des **tests automatiques** : de petits
  programmes qui vérifient que le code donne les bons résultats.
- **Image** : un **contrôle qualité** en usine : chaque pièce est vérifiée
  automatiquement.
- **Ici** : 33 tests dans `tests/` (calcul AQI, API, qualité du modèle…).

### pandera
- **C'est quoi ?** Vérifie que les **données** respectent des règles (types,
  plages de valeurs) — ex. une concentration ne peut pas être négative.
- **Image** : une **checklist** appliquée au jeu de données avant de l'utiliser.
- **Ici** : `validation.py`, utilisé dans le pipeline ET dans les tests.

### ruff
- **C'est quoi ?** Un **linter** : il relit le code et signale erreurs et
  mauvaises habitudes de style, très rapidement.
- **Image** : le **correcteur orthographique** du code.
- **Ici** : `make lint`.

---

## 🚀 Automatiser et livrer : MLOps (C13)

> **MLOps** = appliquer au machine learning les bonnes pratiques de l'industrie
> logicielle (automatisation, reproductibilité, déploiement). Les outils
> ci-dessous servent à cela.

### DVC (Data Version Control)
- **C'est quoi ?** Comme « Git pour les données et les modèles ». Il **versionne**
  les gros fichiers (données, modèle) et décrit le **pipeline** d'étapes
  (préparer → entraîner → évaluer) pour le **rejouer** automatiquement.
- **Image** : une **recette de cuisine** enregistrée : on relance `dvc repro` et
  il refait seulement les étapes nécessaires si un ingrédient a changé.
- **Ici** : `dvc.yaml` décrit les 3 étapes ; `params.yaml` contient les réglages.

### Docker
- **C'est quoi ?** Met l'application et **tout ce dont elle a besoin** (Python,
  bibliothèques…) dans une **« boîte »** (un conteneur) qui tourne pareil sur
  n'importe quelle machine.
- **Image** : un **carton de déménagement** standardisé : « ça marche chez moi »
  devient « ça marche partout ».
- **Ici** : `Dockerfile` (l'image de l'API) + `docker-compose.yml` (lance l'API
  et l'application ensemble).

### GitHub Actions
- **C'est quoi ?** Un service qui **exécute automatiquement** des tâches quand on
  pousse du code : lancer les tests, construire l'image Docker, publier le
  modèle… C'est la **CI/CD**.
  - **CI** (intégration continue) = vérifier automatiquement à chaque changement.
  - **CD** (livraison continue) = packager et publier automatiquement.
- **Image** : un **assistant** qui, à chaque modification, refait tous les
  contrôles et prépare la livraison à votre place.
- **Ici** : `.github/workflows/ci.yml` (tests) et `cd.yml` (publication).

### pre-commit
- **C'est quoi ?** Lance des vérifications **juste avant chaque commit** Git
  (formatage, linter…), pour ne pas envoyer de code fautif.
- **Image** : un **dernier coup d'œil** automatique avant d'envoyer.
- **Ici** : `.pre-commit-config.yaml`.

---

## 🧰 Le « ciment » du projet

### Make (Makefile)
- **C'est quoi ?** Permet de créer des **raccourcis** de commandes longues. Au
  lieu de taper une commande complète, on tape `make api`.
- **Image** : des **boutons de raccourci**.
- **Ici** : `make setup`, `make api`, `make app`, `make test`…

### pyproject.toml
- **C'est quoi ?** La **fiche d'identité** du projet Python : son nom, ses
  dépendances, la configuration des outils.
- **Image** : la **liste de courses** + la **carte d'identité** du projet.

### Environnement virtuel (.venv)
- **C'est quoi ?** Un dossier isolé qui contient **sa propre** version de Python
  et des bibliothèques, pour ne pas mélanger avec le reste de l'ordinateur.
- **Image** : un **bac à sable** propre, dédié à ce projet.
- **Ici** : créé par `make setup`.

---

## En une phrase

> On **entraîne** un modèle (scikit-learn / XGBoost), on l'**expose** via une API
> (FastAPI/uvicorn), on l'**utilise** dans une application (Streamlit), on le
> **surveille** (Prometheus/Evidently), on le **teste** (pytest/pandera) et on
> **automatise** tout le cycle (DVC/Docker/GitHub Actions).
