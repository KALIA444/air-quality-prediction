# Build multi-etapes pour l'API AQI (C13 : packaging).
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Installer d'abord le package (meilleure mise en cache des couches).
COPY pyproject.toml README.md ./
COPY src ./src
# Installer avec l'extra [app] pour que la meme image serve l'API ou Streamlit.
RUN pip install --upgrade pip && pip install ".[app]"

# Copier le reste (scripts, modele entraine, params, squelette des rapports).
COPY params.yaml ./
COPY scripts ./scripts
COPY models ./models
COPY reports ./reports
COPY AirQualityData.csv ./

EXPOSE 8000

# Utilisateur non-root pour la securite.
RUN useradd -m appuser && chown -R appuser /app
USER appuser

CMD ["uvicorn", "air_quality.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
