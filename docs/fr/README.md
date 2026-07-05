# Documentation (français)

Projet **Mari-E3** — prédiction de l'indice de qualité de l'air (AQI) avec une
chaîne complète : modèle, API REST, application, monitoring, tests et MLOps.

Cette documentation explique ce qui a été fait et comment lancer chaque service.

## Sommaire

1. [Vue d'ensemble](00-vue-ensemble.md) — le projet, la découverte sur les données, ce qui a été construit.
2. [Installation](01-installation.md) — environnement Python et dépendances.
3. [Démarrage des services](02-demarrage-services.md) — comment lancer l'API, l'application, le monitoring, les tests, DVC et Docker.
4. [Compétences C9–C13](03-competences-c9-c13.md) — correspondance entre chaque compétence et le code.
5. [Architecture](04-architecture.md) — organisation du code et flux de données.
6. [Les outils expliqués (débutant)](05-glossaire-outils.md) — à quoi sert chaque outil (Streamlit, DVC, FastAPI, Docker…), avec des images simples.

> 📄 **Rapport de projet (Word)** : [`RAPPORT_C9-C13.docx`](RAPPORT_C9-C13.docx),
> présentation des compétences C9 à C13 avec captures d'écran des résultats.
> Régénérable via `./.venv/bin/python scripts/generate_report.py`.

> 🖥️ **Présentation de soutenance (PowerPoint)** : [`PRESENTATION.pptx`](PRESENTATION.pptx),
> diaporama 16:9 moderne et épuré. Régénérable via `./.venv/bin/python scripts/generate_slides.py`.

> 🆕 Débutant ? Commencez par [la vue d'ensemble](00-vue-ensemble.md) puis
> [le glossaire des outils](05-glossaire-outils.md) avant de lancer les services.

## Démarrage ultra-rapide

```bash
make setup        # crée le venv et installe tout
make all          # calcule la cible AQI, entraîne et évalue le modèle
make api          # lance l'API REST   -> http://localhost:8000/docs
make app          # lance l'application -> http://localhost:8501
```

> Toutes les commandes utilisent l'interpréteur du venv. Sans `make`, préfixez par
> `./.venv/bin/python` (ex. `./.venv/bin/python scripts/run.py train`).
