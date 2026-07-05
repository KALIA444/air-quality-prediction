"""Évalue le meilleur modèle sauvegardé : table de métriques, graphiques, importance des variables.

Re-dérive le même split train/test (RANDOM_STATE identique) et charge le
``best_model.joblib`` persisté afin que l'évaluation corresponde à ce que
l'entraînement a sauvegardé.
"""
from __future__ import annotations

import json

import joblib
import matplotlib

matplotlib.use("Agg")  # sans affichage : écrit des PNG, n'ouvre jamais de fenêtre
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config
from .modeling import prepare_splits


def _load_metrics() -> dict:
    with open(config.REPORTS_DIR / "metrics.json") as fh:
        return json.load(fh)


def _feature_importance(model, feature_names) -> pd.Series | None:
    est = model.named_steps["model"]
    if hasattr(est, "feature_importances_"):
        imp = est.feature_importances_
    elif hasattr(est, "coef_"):
        imp = np.abs(est.coef_)
    else:
        return None
    return pd.Series(imp, index=feature_names).sort_values(ascending=False)


def run():
    metrics = _load_metrics()
    X_train, X_test, y_train, y_test, feature_names = prepare_splits()
    model = joblib.load(config.MODELS_DIR / "best_model.joblib")
    y_pred = model.predict(X_test)

    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Prédit vs réel.
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(y_test, y_pred, s=8, alpha=0.4)
    lims = [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())]
    ax.plot(lims, lims, "r--", lw=1)
    ax.set_xlabel("AQI réel")
    ax.set_ylabel("AQI prédit")
    ax.set_title(f"Prédit vs Réel — {metrics['best_model']}")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "pred_vs_actual.png", dpi=120)
    plt.close(fig)

    # 2. Résidus.
    residuals = y_test - y_pred
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter(y_pred, residuals, s=8, alpha=0.4)
    ax.axhline(0, color="r", lw=1)
    ax.set_xlabel("AQI prédit")
    ax.set_ylabel("Résidu (réel - prédit)")
    ax.set_title("Résidus")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "residuals.png", dpi=120)
    plt.close(fig)

    # 3. Importance des variables.
    imp = _feature_importance(model, feature_names)
    if imp is not None:
        top = imp.head(15)[::-1]
        fig, ax = plt.subplots(figsize=(7, 6))
        ax.barh(top.index, top.values)
        ax.set_title(f"Top des importances de variables — {metrics['best_model']}")
        fig.tight_layout()
        fig.savefig(config.FIGURES_DIR / "feature_importance.png", dpi=120)
        plt.close(fig)

    # Résumé console.
    print("\n=== Comparaison des modèles (cible : AQI EPA calculé) ===")
    header = f"{'model':18s} {'cv_r2':>8s} {'test_r2':>8s} {'test_rmse':>10s} {'test_mae':>9s}"
    print(header)
    print("-" * len(header))
    for name, m in metrics["results"].items():
        marker = "  <-- meilleur" if name == metrics["best_model"] else ""
        print(f"{name:18s} {m['cv_r2_mean']:8.4f} {m['test_r2']:8.4f} "
              f"{m['test_rmse']:10.3f} {m['test_mae']:9.3f}{marker}")

    if imp is not None:
        print("\nTop 8 des variables :")
        for feat, val in imp.head(8).items():
            print(f"  {feat:22s} {val:.4f}")

    print(f"\nFigures écrites dans {config.FIGURES_DIR}")
    return metrics
