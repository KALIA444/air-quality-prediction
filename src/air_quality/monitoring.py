"""Surveillance de la dérive des données avec alertes et rapports (C11).

La détection de dérive pour l'*alerte* utilise un test de Kolmogorov–Smirnov à
deux échantillons par colonne numérique (via scipy) — un signal stable et
indépendant de la version. Evidently est utilisé par-dessus pour générer un
rapport HTML riche ; si son API en évolution rapide casse, l'alerte centrale
fonctionne toujours (l'étape HTML est enveloppée de façon défensive).

Une colonne est « dérivée » lorsque la p-value KS < 0.05. Si la part des
colonnes dérivées dépasse ``config.DRIFT_SHARE_THRESHOLD``, un JSON d'alerte est
écrit et l'appelant (CLI) sort avec un code non nul afin qu'une tâche cron/CI
puisse réagir.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import pandas as pd
from scipy.stats import ks_2samp

from . import config
from .data import build_dataset

logger = logging.getLogger("air_quality.monitoring")

# Colonnes surveillées pour la dérive (features numériques + cible).
_DROP = {"DominantPollutant"}


def _numeric_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[c for c in _DROP if c in df.columns]).select_dtypes("number")


def _perturb(df: pd.DataFrame) -> pd.DataFrame:
    """Injecte une dérive synthétique large sur les capteurs pour tester le chemin d'alerte."""
    out = df.copy()
    multipliers = {"PM2.5": 1.6, "PM10": 1.5, "O3(GT)": 1.4,
                   "NO2(GT)": 1.5, "NOx(GT)": 1.4, "CO(GT)": 1.5, "SO2(GT)": 1.6,
                   "CO_MA3": 1.5, "NO2_MA3": 1.5, "O3_MA3": 1.4}
    for col, factor in multipliers.items():
        if col in out:
            out[col] = out[col] * factor
    out["Temperature"] = out["Temperature"] + 12
    out["Humidity"] = (out["Humidity"] * 0.6).clip(0, 100)
    return out


def compute_drift(reference: pd.DataFrame, current: pd.DataFrame,
                  p_threshold: float = 0.05) -> dict:
    """Dérive KS par colonne ; renvoie la part dérivée et les p-values par colonne."""
    ref_num = _numeric_frame(reference)
    cur_num = _numeric_frame(current)
    columns = [c for c in ref_num.columns if c in cur_num.columns]

    per_column = {}
    drifted = 0
    for col in columns:
        stat, pvalue = ks_2samp(ref_num[col].dropna(), cur_num[col].dropna())
        is_drift = bool(pvalue < p_threshold)
        drifted += int(is_drift)
        per_column[col] = {"p_value": float(pvalue), "drifted": is_drift}

    share = drifted / len(columns) if columns else 0.0
    return {"drift_share": share, "n_drifted": drifted,
            "n_columns": len(columns), "columns": per_column}


def _save_html_report(reference: pd.DataFrame, current: pd.DataFrame, path) -> bool:
    """Rapport HTML de dérive Evidently au mieux. Renvoie True en cas de succès."""
    try:
        from evidently import Report
        from evidently.presets import DataDriftPreset

        report = Report([DataDriftPreset()])
        snapshot = report.run(
            current_data=_numeric_frame(current).reset_index(drop=True),
            reference_data=_numeric_frame(reference).reset_index(drop=True),
        )
        snapshot.save_html(str(path))
        return True
    except Exception as exc:  # ne jamais laisser le rapport casser l'alerte
        logger.warning("Rapport HTML Evidently ignoré : %s", exc)
        return False


def run_drift_report(current_csv=None, perturb: bool = False) -> dict:
    """Compare les données de référence (entraînement) à un lot courant ; alerte sur la dérive.

    ``current_csv`` pointe vers un CSV de nouvelles observations ; s'il est omis,
    les données de référence sont réutilisées (éventuellement perturbées via
    ``perturb`` pour démontrer une alerte).
    """
    reference = build_dataset()
    if current_csv:
        current = build_dataset(path=current_csv)
    else:
        current = _perturb(reference) if perturb else reference.copy()

    drift = compute_drift(reference, current)
    alert = drift["drift_share"] > config.DRIFT_SHARE_THRESHOLD

    config.DRIFT_DIR.mkdir(parents=True, exist_ok=True)
    config.ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    html_path = config.DRIFT_DIR / "drift_report.html"
    json_path = config.DRIFT_DIR / "drift_summary.json"

    html_ok = _save_html_report(reference, current, html_path)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "drift_share": drift["drift_share"],
        "threshold": config.DRIFT_SHARE_THRESHOLD,
        "n_drifted": drift["n_drifted"],
        "n_columns": drift["n_columns"],
        "alert": alert,
        "columns": drift["columns"],
        "html_path": str(html_path) if html_ok else None,
        "json_path": str(json_path),
        "alert_path": None,
    }

    if alert:
        alert_path = config.ALERTS_DIR / "drift_alert.json"
        with open(alert_path, "w") as fh:
            json.dump({k: summary[k] for k in
                       ("generated_at", "drift_share", "threshold", "n_drifted")}, fh, indent=2)
        summary["alert_path"] = str(alert_path)
        logger.warning("ALERTE DE DÉRIVE DES DONNÉES : part dérivée %.2f (> %.2f)",
                       drift["drift_share"], config.DRIFT_SHARE_THRESHOLD)

    with open(json_path, "w") as fh:
        json.dump(summary, fh, indent=2)
    return summary
