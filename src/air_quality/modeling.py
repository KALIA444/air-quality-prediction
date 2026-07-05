"""Entraîne et compare des modèles sur la cible AQI calculée.

Chaque modèle est encapsulé dans un ``Pipeline`` avec un ``StandardScaler`` afin
que la mise à l'échelle soit ajustée uniquement sur le pli d'entraînement — cela
évite la fuite train/test qui résulte d'une mise à l'échelle de l'ensemble du
jeu de données en amont. Les arbres ignorent le scaler sans dommage, ce qui
maintient un chemin de code unique pour tous les estimateurs.
"""
from __future__ import annotations

import json

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from . import config
from .data import build_dataset, save_processed
from .features import add_features, split_X_y


def get_models() -> dict[str, object]:
    """Construit les modèles candidats, en tirant les hyperparamètres de params.yaml.

    Les valeurs par défaut correspondent aux littéraux d'origine, de sorte que le
    comportement reste inchangé lorsque params.yaml est absent.
    """
    rf = config.MODEL_PARAMS.get("random_forest", {})
    xgb = config.MODEL_PARAMS.get("xgboost", {})
    return {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(
            n_estimators=rf.get("n_estimators", 300),
            random_state=config.RANDOM_STATE, n_jobs=-1,
        ),
        "xgboost": XGBRegressor(
            n_estimators=xgb.get("n_estimators", 400),
            learning_rate=xgb.get("learning_rate", 0.05),
            max_depth=xgb.get("max_depth", 6),
            subsample=xgb.get("subsample", 0.9),
            colsample_bytree=xgb.get("colsample_bytree", 0.9),
            random_state=config.RANDOM_STATE, n_jobs=-1,
        ),
    }


def _pipeline(estimator) -> Pipeline:
    return Pipeline([("scaler", StandardScaler()), ("model", estimator)])


def prepare_splits():
    """Construit le jeu de données, crée les variables, retourne les splits train/test + noms de variables."""
    df = build_dataset()
    save_processed(df)
    engineered = add_features(df)
    X, y = split_X_y(engineered)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE
    )
    return X_train, X_test, y_train, y_test, list(X.columns)


def train_and_evaluate():
    """Entraîne tous les modèles, valide en croisé, choisit le meilleur par R² test, sauvegarde les artefacts.

    Retourne un tuple (results, best_name) où results associe le nom du modèle à
    son dictionnaire de métriques.
    """
    X_train, X_test, y_train, y_test, feature_names = prepare_splits()

    results: dict[str, dict] = {}
    fitted: dict[str, Pipeline] = {}

    for name, estimator in get_models().items():
        pipe = _pipeline(estimator)
        cv_r2 = cross_val_score(
            pipe, X_train, y_train, scoring="r2", cv=config.CV_FOLDS, n_jobs=-1
        )
        cv_rmse = -cross_val_score(
            pipe, X_train, y_train,
            scoring="neg_root_mean_squared_error", cv=config.CV_FOLDS, n_jobs=-1,
        )

        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)

        results[name] = {
            "cv_r2_mean": float(cv_r2.mean()),
            "cv_r2_std": float(cv_r2.std()),
            "cv_rmse_mean": float(cv_rmse.mean()),
            "test_r2": float(r2_score(y_test, y_pred)),
            "test_rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "test_mae": float(mean_absolute_error(y_test, y_pred)),
        }
        fitted[name] = pipe

    best_name = max(results, key=lambda n: results[n]["test_r2"])

    # Persiste les artefacts.
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(fitted[best_name], config.MODELS_DIR / "best_model.joblib")

    payload = {
        "target": config.TARGET,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "features": feature_names,
        "best_model": best_name,
        "results": results,
    }
    with open(config.REPORTS_DIR / "metrics.json", "w") as fh:
        json.dump(payload, fh, indent=2)

    return results, best_name
