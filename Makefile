.PHONY: setup install build-target train evaluate all monitor \
        lint test test-fast api app docker-build docker-up dvc-repro clean

PY := ./.venv/bin/python
PIP := ./.venv/bin/pip

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
