"""Tests d'entraînement/évaluation incluant la barrière de qualité du modèle (C12)."""
from __future__ import annotations

import pytest

from air_quality.modeling import prepare_splits, train_and_evaluate


def test_prepare_splits_shapes():
    X_train, X_test, y_train, y_test, features = prepare_splits()
    assert len(X_train) > len(X_test)              # 80/20
    assert list(X_train.columns) == features
    assert len(X_train) == len(y_train)
    assert len(X_test) == len(y_test)


@pytest.mark.slow
def test_model_quality_gate():
    """Étape de validation : le meilleur modèle doit bien expliquer l'AQI calculé."""
    results, best = train_and_evaluate()
    assert results[best]["test_r2"] > 0.9, f"best {best} R²={results[best]['test_r2']:.3f}"
    # Contrôle : le RMSE doit représenter une petite fraction de l'échelle AQI (0–500).
    assert results[best]["test_rmse"] < 25
