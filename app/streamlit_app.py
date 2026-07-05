"""Client Streamlit pour l'API AQI (C10).

Consomme les routes FastAPI ``/predict`` et ``/predict/batch`` via httpx, en
utilisant le contrat OpenAPI documenté sur le ``/docs`` de l'API.

Mesures d'accessibilité (RGAA/WCAG) dans les limites de Streamlit :
* chaque contrôle a un label descriptif et un texte ``help`` ;
* la catégorie d'AQI est transmise par **texte + icône + couleur ensemble** —
  jamais par la couleur seule (WCAG 1.4.1) ;
* un badge à fort contraste et une hiérarchie de titres claire.
Les lacunes résiduelles (contrôle de l'ordre de focus, ARIA complet) sont
signalées dans l'expander « Accessibilité » de l'application ; une version
strictement RGAA servirait une page HTML accessible équivalente depuis la même
route ``/predict``.
"""
from __future__ import annotations

import os
from datetime import datetime

import httpx
import pandas as pd
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "dev-local-key")

# Catégorie EPA -> (couleur de fond, couleur du texte, icône). La couleur est
# associée au label et à une icône pour que le sens ne dépende jamais de la
# couleur seule.
CATEGORY_STYLE = {
    "Bon": ("#00897B", "#FFFFFF", "✅"),
    "Modéré": ("#F9A825", "#000000", "🟡"),
    "Mauvais pour groupes sensibles": ("#EF6C00", "#FFFFFF", "🟠"),
    "Mauvais": ("#C62828", "#FFFFFF", "🔴"),
    "Très mauvais": ("#6A1B9A", "#FFFFFF", "🟣"),
    "Dangereux": ("#4E342E", "#FFFFFF", "⚫"),
    "Inconnu": ("#546E7A", "#FFFFFF", "❔"),
}

FIELDS = [
    ("co", "CO (ppm)", 0.0, 100.0, 3.8),
    ("nox", "NOx", 0.0, 1000.0, 172.0),
    ("no2", "NO2 (ppb)", 0.0, 1000.0, 144.3),
    ("o3", "O3 (ppb)", 0.0, 1000.0, 118.1),
    ("so2", "SO2 (ppb)", 0.0, 1000.0, 1.2),
    ("pm25", "PM2.5 (µg/m³)", 0.0, 1000.0, 147.3),
    ("pm10", "PM10 (µg/m³)", 0.0, 1000.0, 208.8),
    ("temperature", "Température (°C)", -50.0, 60.0, 28.5),
    ("humidity", "Humidité (%)", 0.0, 100.0, 45.0),
    ("pressure", "Pression (hPa)", 870.0, 1085.0, 1013.2),
    ("wind_speed", "Vitesse du vent", 0.0, 200.0, 6.0),
    ("wind_direction", "Direction du vent (°)", 0.0, 360.0, 210.0),
]


def _client() -> httpx.Client:
    return httpx.Client(base_url=API_URL, headers={"X-API-Key": API_KEY}, timeout=15)


def render_result(result: dict) -> None:
    cat = result["category"]
    bg, fg, icon = CATEGORY_STYLE.get(cat, CATEGORY_STYLE["Inconnu"])
    col1, col2 = st.columns([1, 2])
    col1.metric(label="AQI prédit", value=f"{result['aqi']:.0f}")
    col2.markdown(
        f"<div role='status' aria-label='Catégorie de qualité de l'air : {cat}' "
        f"style='background:{bg};color:{fg};padding:0.8rem 1rem;border-radius:8px;"
        f"font-size:1.1rem;font-weight:600;'>{icon} {cat}</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Polluant dominant : **{result['dominant_pollutant']}**")


def single_prediction_tab() -> None:
    st.subheader("Prédiction unique")
    with st.form("predict_form"):
        when = st.text_input("Horodatage (ISO-8601)", value=datetime.now().isoformat(timespec="minutes"),
                             help="Heure d'observation ; influence les features calendaires.")
        cols = st.columns(3)
        values = {}
        for i, (key, label, lo, hi, default) in enumerate(FIELDS):
            values[key] = cols[i % 3].number_input(
                label, min_value=lo, max_value=hi, value=default,
                help=f"Plage autorisée {lo}–{hi}.")
        submitted = st.form_submit_button("Prédire l'AQI")

    if submitted:
        payload = {"timestamp": when, **values}
        try:
            with _client() as c:
                resp = c.post("/predict", json=payload)
            if resp.status_code == 200:
                render_result(resp.json())
            else:
                st.error(f"Erreur de l'API {resp.status_code} : {resp.text}")
        except httpx.HTTPError as exc:
            st.error(f"Impossible de joindre l'API sur {API_URL} : {exc}")


def batch_tab() -> None:
    st.subheader("Prédiction par lots")
    st.write("Téléversez un CSV dont les colonnes correspondent aux champs de la "
             "prédiction unique "
             "(`co, nox, no2, o3, so2, pm25, pm10, temperature, humidity, "
             "pressure, wind_speed, wind_direction`), `timestamp` optionnel.")
    file = st.file_uploader("Fichier CSV", type="csv", help="Une observation par ligne.")
    if file is None:
        return
    df = pd.read_csv(file)
    items = df.to_dict(orient="records")
    try:
        with _client() as c:
            resp = c.post("/predict/batch", json={"items": items})
    except httpx.HTTPError as exc:
        st.error(f"Impossible de joindre l'API : {exc}")
        return
    if resp.status_code != 200:
        st.error(f"Erreur de l'API {resp.status_code} : {resp.text}")
        return
    preds = pd.DataFrame(resp.json()["predictions"])
    out = pd.concat([df.reset_index(drop=True), preds], axis=1)
    st.dataframe(out, use_container_width=True)
    st.download_button("Télécharger les prédictions", out.to_csv(index=False),
                       file_name="aqi_predictions.csv", mime="text/csv")


def main() -> None:
    st.set_page_config(page_title="Prédicteur d'AQI de qualité de l'air", page_icon="🌫️",
                       layout="centered")
    st.title("🌫️ Prédicteur d'AQI de qualité de l'air")
    st.write("Estimez l'indice de qualité de l'air EPA à partir des relevés de "
             "polluants et de météo. "
             f"Appuyé par l'API AQI sur `{API_URL}`.")

    with st.sidebar:
        st.header("Connexion")
        st.write(f"URL de l'API : `{API_URL}`")
        st.write("Définissez les variables d'environnement `API_URL` / `API_KEY` "
                 "pour pointer ailleurs.")
        with st.expander("Notes d'accessibilité"):
            st.write("La catégorie utilise texte + icône + couleur (pas la couleur "
                     "seule). Streamlit limite le contrôle de l'ordre de focus et "
                     "d'ARIA ; une interface HTML strictement RGAA peut utiliser la "
                     "même route `/predict`.")

    tab1, tab2 = st.tabs(["Unique", "Par lots"])
    with tab1:
        single_prediction_tab()
    with tab2:
        batch_tab()


if __name__ == "__main__":
    main()
