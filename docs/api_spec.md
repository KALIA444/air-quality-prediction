# Air Quality AQI API — Specification (C9)

REST service exposing the trained AQI regression model. Built with FastAPI;
interactive OpenAPI docs are auto-generated at `/docs` (Swagger) and `/redoc`.

## Run

```bash
uvicorn air_quality.api.main:app --host 0.0.0.0 --port 8000
# or: make api
```

## Authentication

All inference endpoints require an `X-API-Key` header. The key is read from the
`API_KEY` environment variable (default `dev-local-key` for local dev).
Missing/invalid key → `401`.

## Security & quality controls

- **Input validation:** Pydantic v2 schemas with per-field range constraints
  (`co`, `pm25`, `humidity`, …). Out-of-range or malformed bodies → `422`.
- **Rate limiting:** `slowapi`, 60/min on `/predict`, 20/min on `/predict/batch`.
- **CORS:** configurable via `CORS_ORIGINS` (comma-separated; `*` for dev).
- **Observability:** Prometheus metrics at `/metrics`; each prediction logged as
  JSON and appended to `reports/predictions_log.jsonl`.

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | no | Liveness + `model_loaded` flag |
| GET | `/model/info` | no | Best model name, feature list, training metrics |
| POST | `/predict` | yes | Single prediction |
| POST | `/predict/batch` | yes | Up to 1000 predictions |
| GET | `/metrics` | no | Prometheus exposition |
| GET | `/docs`, `/redoc` | no | Interactive API documentation |

### `POST /predict`

Request body:

```json
{
  "timestamp": "2024-07-15T14:00:00",
  "co": 3.8, "nox": 172.0, "no2": 144.3, "o3": 118.1, "so2": 1.2,
  "pm25": 147.3, "pm10": 208.8, "temperature": 28.5,
  "humidity": 45.0, "pressure": 1013.2,
  "wind_speed": 6.0, "wind_direction": 210.0
}
```

`timestamp` is optional (defaults to now). Field ranges are documented in
`/docs`.

Response `200`:

```json
{ "aqi": 213.98, "category": "Très mauvais", "dominant_pollutant": "O3(GT)" }
```

### `POST /predict/batch`

```json
{ "items": [ { /* PredictionRequest */ }, { /* ... */ } ] }
```

Response: `{ "predictions": [ { "aqi": ..., "category": ..., "dominant_pollutant": ... } ] }`

## Status codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Missing/invalid API key |
| 422 | Validation error (range / type) |
| 429 | Rate limit exceeded |
| 500 | Internal error |

## Example

```bash
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: dev-local-key" -H "Content-Type: application/json" \
  -d '{"co":3.8,"nox":172,"no2":144.3,"o3":118.1,"so2":1.2,"pm25":147.3,
       "pm10":208.8,"temperature":28.5,"humidity":45,"pressure":1013.2,
       "wind_speed":6,"wind_direction":210}'
```
