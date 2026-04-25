# System Observability Platform

> **Author:** Writick Parui | M.E. CSE, TIET Patiala | GATE 2025 Qualified | Ex-Intern TCS iON Kolkata

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit%20Site-00e87a?style=flat-square)](https://writickp3-ctrl.github.io/system-observability-platform/)
[![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?style=flat-square)](https://flask.palletsprojects.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square)](https://docker.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-orange?style=flat-square)](https://scikit-learn.org)

A production-style backend observability platform that ingests system logs via REST APIs, detects anomalies using Isolation Forest, classifies severity using Logistic Regression, and exposes operational metrics — fully containerized with Docker.

---

## Live Demo

**[→ Open Live Demo](https://writickp3-ctrl.github.io/system-observability-platform/)**

Paste any system log and get real-time anomaly detection + severity classification powered by the ML pipeline.

---

## Problem Statement

Modern Linux-based systems generate thousands of log events per hour. Manually inspecting these is inefficient and error-prone — critical anomalies get missed and severity is inconsistently assessed.

This platform solves that by:
- Centralising log ingestion via REST APIs
- Persisting events reliably in SQLite
- Detecting anomalies automatically using Isolation Forest (ML)
- Classifying severity using Logistic Regression + rule-based engine
- Exposing operational metrics for real-time debugging and monitoring

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.10, Flask 3.0 |
| ML — Anomaly Detection | scikit-learn (Isolation Forest) |
| ML — Severity Classification | scikit-learn (Logistic Regression) |
| Data Processing | Pandas, NumPy |
| Storage | SQLite |
| Containerization | Docker, Gunicorn |
| Logging | Python logging (structured, file + stdout) |
| Runtime | Linux |

---

## Project Structure

```
system-observability-platform/
│
├── app.py                    # Flask application — all REST endpoints
├── init_db.py                # One-time DB bootstrap script
├── Dockerfile                # Production container (Gunicorn)
├── docker-compose.yml        # One-command startup
├── requirements.txt          # Pinned dependencies
├── index.html                # Live demo portfolio site
├── system_log_monitor.ipynb  # Original development notebook
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── db.py                 # SQLite layer (init, insert, fetch, clear)
│   ├── log_parser.py         # Regex syslog parser
│   ├── anomaly.py            # Isolation Forest (batch + single inference)
│   ├── severity.py           # Logistic Regression (batch + rule-based)
│   ├── metrics.py            # Operational metrics + CSV export
│   └── logger.py             # Structured logging (file + stdout)
│
├── sample_logs/
│   └── syslog.txt            # 15 sample syslog entries for testing
│
├── logs/                     # Runtime application logs (auto-generated)
└── metrics/                  # metrics.csv output (auto-generated)
```

---

## Quickstart

### Option 1 — Docker (Recommended)

```bash
# 1. Clone the repo
git clone https://github.com/writickp3-ctrl/system-observability-platform.git
cd system-observability-platform

# 2. Start with docker-compose
docker-compose up
```

Service live at: `http://localhost:5000`

---

### Option 2 — Run Locally (Without Docker)

```bash
# 1. Clone the repo
git clone https://github.com/writickp3-ctrl/system-observability-platform.git
cd system-observability-platform

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialise the database
python init_db.py

# 5. (Optional) Load sample data
python init_db.py --with-sample-data

# 6. Start the server
python app.py
```

Service live at: `http://localhost:5000`

---

### Option 3 — Production Server

```bash
gunicorn --workers=2 --bind=0.0.0.0:5000 --timeout=60 app:app
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check + service info |
| POST | `/log` | Ingest log → store → instant ML prediction |
| POST | `/predict` | ML inference only (no storage) |
| POST | `/upload` | Bulk upload a syslog file |
| GET | `/logs` | Fetch all logs (filter: `?level=ERROR&limit=50`) |
| GET | `/anomalies` | Isolation Forest on all stored logs |
| GET | `/severity` | Logistic Regression on all stored logs |
| GET | `/metrics` | Error rate, warn rate, level breakdown |
| DELETE | `/logs` | Clear all stored logs |

---

## Sample API Usage

### Ingest a single log

```bash
curl -X POST http://localhost:5000/log \
  -H "Content-Type: application/json" \
  -d '{"message": "Out of memory: Kill process 4821 (java)", "level": "ERROR"}'
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "stored": true,
    "level": "ERROR",
    "anomaly": {
      "is_anomaly": true,
      "heuristic_score": 0.83,
      "matched_keywords": ["killed", "oom"]
    },
    "severity": {
      "severity": "CRITICAL",
      "confidence": 0.95
    }
  }
}
```

### Predict without storing

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"message": "CPU spike detected: 94.2% for 180s", "level": "WARN"}'
```

### Bulk upload a log file

```bash
curl -X POST http://localhost:5000/upload \
  -F "file=@sample_logs/syslog.txt"
```

### Get operational metrics

```bash
curl http://localhost:5000/metrics
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "total_logs": 15,
    "by_level": {"ERROR": 6, "INFO": 6, "WARN": 3},
    "error_rate_pct": 40.0,
    "warn_rate_pct": 20.0
  }
}
```

### Filter logs by level

```bash
curl "http://localhost:5000/logs?level=ERROR&limit=10"
```

---

## High-Level Architecture

```
Log Producer / Client
        |
        v
  Flask REST API (app.py)
        |
   +----+----+
   v         v
SQLite     Processing Layer
Store          |
           +---+----+
           v         v
       ML Engine   Logger
     (Isolation    (Structured
      Forest +      Logging)
      LogReg)
           |
           v
     Metrics & Monitoring
```

---

## ML Pipeline

### Anomaly Detection — Isolation Forest

**Batch mode (`GET /anomalies`):**
- Loads all stored logs from SQLite
- Extracts 3 features per log: message length, error keyword count, level severity score
- Fits Isolation Forest (`contamination=0.2`, `n_estimators=100`, `random_state=42`)
- Returns flagged entries with anomaly scores (more negative = more anomalous)

**Single inference (`POST /log`, `POST /predict`):**
- Heuristic scoring for zero-latency real-time response
- Weighted combination: keyword matches + level severity + message length

**Error keywords monitored:**
`error`, `fail`, `crash`, `timeout`, `critical`, `exception`, `killed`, `oom`, `refused`, `denied`

---

### Severity Classification — Logistic Regression

**Batch mode (`GET /severity`):**
- Trains Logistic Regression on stored logs using extracted features
- Outputs `LOW / MEDIUM / HIGH` per log entry
- Falls back to rule-based when class diversity is insufficient

**Single inference — Rule-based tiers:**

| Severity | Trigger Keywords |
|----------|-----------------|
| CRITICAL | oom, killed, segfault, panic, crash, out of memory, disk full |
| HIGH | error, fail, timeout, exception, denied |
| MEDIUM | warn, high, slow, retry, degraded |
| LOW | all others |

---

## Engineering Highlights

- **Modular service design** — DB, parsing, ML, metrics, and logging each isolated in `src/`
- **Dual inference modes** — fast heuristic for real-time single requests, full ML for batch historical analysis
- **Centralised exception handling** — all routes wrapped with try/except, errors structured as JSON
- **Structured logging** — dual output to `logs/app.log` and stdout with timestamp, level, and module
- **Production containerisation** — Gunicorn multi-worker deployment via Docker
- **Environment-configurable** — DB path, port, metrics directory via environment variables
- **Clean bootstrap** — `init_db.py` handles first-run DB setup with optional sample data

---

## Performance & Reliability

- SQLite for lightweight, zero-config local persistence
- Gunicorn multi-worker handles concurrent requests
- Modular architecture supports horizontal scaling of individual services
- Docker ensures environment parity across dev, staging, and prod
- Structured logs simplify debugging and tracing

---

## Future Enhancements

- [ ] Replace SQLite with PostgreSQL for production scale
- [ ] Add Prometheus metrics exporter (`/metrics/prometheus`)
- [ ] Implement distributed tracing (OpenTelemetry)
- [ ] Async log ingestion via Celery + Redis message queue
- [ ] Add JWT authentication and rate limiting middleware
- [ ] Real-time alerting via webhooks on CRITICAL events
- [ ] Deploy on Kubernetes with horizontal pod autoscaling

---

## Development Notes

The original prototype was developed in `system_log_monitor.ipynb` covering:
- SQLite schema design and CRUD operations
- Syslog regex parsing and structured storage
- Isolation Forest anomaly detection on message features
- Logistic Regression severity classification
- Operational metrics generation and CSV export
- Flask API design and Docker containerisation

The production codebase in `src/` refactors all notebook logic into a clean, modular, deployable backend.

---

## License

MIT License — free to use, modify, and distribute.
