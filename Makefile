.PHONY: setup install build-target train evaluate all monitor \
        lint test test-fast api app docker-build docker-up dvc-repro clean demo

PY := ./.venv/bin/python
PIP := ./.venv/bin/pip

# --- Demo (one-shot) ------------------------------------------------------
# `make demo` : tout depuis zero, sans rien preparer.
# Cree le venv si absent, installe, calcule la cible, entraine le modele si
# besoin, lance l'API (fond) + Streamlit (premier plan). Ctrl-C arrete tout.
demo:
	@command -v python3 >/dev/null 2>&1 || { echo "python3 introuvable"; exit 1; }
	@test -x $(PY) || { echo ">> venv absent : creation..."; python3 -m venv .venv; }
	@echo ">> Installation des dependances..."
	@$(PIP) install --quiet --upgrade pip
	@$(PIP) install --quiet -e ".[dev,app,monitoring]"
	@echo ">> Calcul de la cible EPA AQI..."
	@$(PY) scripts/run.py build-target
	@test -f models/best_model.joblib || { echo ">> Entrainement du modele..."; $(PY) scripts/run.py train; }
	@echo ">> Liberation des ports 8010 / 8510 si occupes..."
	@-lsof -ti tcp:8010 -sTCP:LISTEN | xargs kill 2>/dev/null || true
	@-lsof -ti tcp:8510 -sTCP:LISTEN | xargs kill 2>/dev/null || true
	@echo ""
	@echo ">> Demo prete. Ouvrez :"
	@echo "     Application : http://localhost:8510"
	@echo "     API (docs)  : http://localhost:8010/docs"
	@echo "   Ctrl-C pour tout arreter."
	@echo ""
	@trap 'kill 0' EXIT INT TERM; \
	  $(PY) -m uvicorn air_quality.api.main:app --port 8010 & \
	  API_URL=http://localhost:8010 $(PY) -m streamlit run app/streamlit_app.py \
	    --server.port 8510 --server.headless true & \
	  wait

setup:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev,app,monitoring]"

install:
	$(PIP) install -e ".[dev,app,monitoring]"

# --- Pipeline -------------------------------------------------------------
build-target:
	$(PY) scripts/run.py build-target

train:
	$(PY) scripts/run.py train

evaluate:
	$(PY) scripts/run.py evaluate

all:
	$(PY) scripts/run.py all

monitor:
	$(PY) scripts/run.py monitor

# --- Qualite --------------------------------------------------------------
lint:
	$(PY) -m ruff check src scripts app tests

test-fast:
	$(PY) -m pytest -m "not slow"

test:
	$(PY) -m pytest -m "not slow" && $(PY) -m pytest -m slow

# --- Service --------------------------------------------------------------
api:
	$(PY) -m uvicorn air_quality.api.main:app --reload --port 8000

app:
	$(PY) -m streamlit run app/streamlit_app.py

# --- MLOps ----------------------------------------------------------------
dvc-repro:
	PATH="$(CURDIR)/.venv/bin:$$PATH" $(PY) -m dvc repro

docker-build:
	docker build -t air-quality-api:latest .

docker-up:
	docker compose up --build

clean:
	rm -rf models/*.joblib reports/metrics.json reports/figures/*.png \
	       reports/drift/* reports/alerts/* reports/predictions_log.jsonl data/*.csv
