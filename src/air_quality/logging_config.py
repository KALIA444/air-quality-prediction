"""Journalisation structurée en JSON + journal d'audit par prédiction (C11).

``configure_logging`` configure le logger racine pour émettre du JSON sur une
seule ligne vers stdout (compatible 12-factor, facile à parser pour les
collecteurs de logs). ``log_prediction`` ajoute chaque prédiction servie à
``reports/predictions_log.jsonl`` afin que la tâche de surveillance puisse
calculer la dérive sur le trafic réel.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

try:  # module déplacé dans les versions récentes de python-json-logger
    from pythonjsonlogger.json import JsonFormatter
except ImportError:  # pragma: no cover
    from pythonjsonlogger.jsonlogger import JsonFormatter

from . import config

_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(
        JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    _CONFIGURED = True


def log_prediction(payload: dict, result: dict) -> None:
    """Ajoute un enregistrement de prédiction (entrées + sorties) au journal d'audit JSONL."""
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "inputs": {k: v for k, v in payload.items() if k != "timestamp"},
        "prediction": result,
    }
    with open(config.PREDICTIONS_LOG, "a") as fh:
        fh.write(json.dumps(record, default=str) + "\n")
