"""
System Observability Platform — Flask Backend
Author: Writick Parui | TIET Patiala | 2024
"""

import os
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response

from src.logger import get_logger
from src.db import init_db, insert_log, fetch_logs, fetch_log_count, clear_logs
from src.log_parser import parse_and_store
from src.anomaly import detect_anomalies, detect_single
from src.severity import classify_single, classify_all
from src.metrics import generate_metrics

# ── App setup ──────────────────────────────────────────────────────────────
app = Flask(__name__)
logger = get_logger(__name__)

# Initialise DB on startup
with app.app_context():
    init_db()


# ── Helpers ─────────────────────────────────────────────────────────────────
def _ok(data: dict | list, status: int = 200) -> Response:
    return jsonify({'status': 'ok', 'data': data}), status


def _err(message: str, status: int = 400) -> Response:
    return jsonify({'status': 'error', 'message': message}), status


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def health():
    """Health check endpoint."""
    return _ok({
        'service': 'System Observability Platform',
        'version': '2.0.0',
        'author':  'Writick Parui',
        'uptime':  'ok',
        'total_logs_stored': fetch_log_count()
    })


# ── Log Ingestion ─────────────────────────────────────────────────────────

@app.route('/log', methods=['POST'])
def ingest_log():
    """
    Ingest a single log entry.

    Body (JSON):
      {
        "message": "CPU spike detected on node-01",
        "level":   "ERROR"          # optional, default INFO
      }

    Response:
      {
        "status":   "ok",
        "data": {
          "stored":   true,
          "anomaly":  { "is_anomaly": true, "heuristic_score": 0.83, ... },
          "severity": { "severity": "HIGH", "confidence": 0.85 }
        }
      }
    """
    body = request.get_json(silent=True)
    if not body or 'message' not in body:
        return _err("Request body must be JSON with a 'message' field")

    message = str(body['message']).strip()
    level   = str(body.get('level', 'INFO')).upper()
    ts      = body.get('timestamp', _now())

    if level not in ('INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL', 'DEBUG'):
        level = 'INFO'

    try:
        insert_log(ts, level, message)
        anomaly_result  = detect_single(message, level)
        severity_result = classify_single(message, level)

        logger.info(
            "Ingested | level=%s | anomaly=%s | severity=%s | msg=%.60s",
            level, anomaly_result['is_anomaly'],
            severity_result['severity'], message
        )

        return _ok({
            'stored':   True,
            'timestamp': ts,
            'level':    level,
            'anomaly':  anomaly_result,
            'severity': severity_result
        }, 201)

    except Exception as exc:
        logger.error("Ingest failed: %s", exc)
        return _err("Internal error during log ingestion", 500)


@app.route('/upload', methods=['POST'])
def upload_log_file():
    """
    Upload a syslog-format text file for bulk ingestion.

    Form-data: file=<log_file.txt>
    """
    if 'file' not in request.files:
        return _err("No file part in request. Use form-data key 'file'")

    f = request.files['file']
    if f.filename == '':
        return _err("Empty filename")

    save_path = os.path.join('/tmp', f.filename)
    f.save(save_path)

    count = parse_and_store(save_path)
    logger.info("Uploaded file '%s' — %d entries parsed", f.filename, count)

    return _ok({'file': f.filename, 'entries_parsed': count}, 201)


# ── Query ────────────────────────────────────────────────────────────────

@app.route('/logs', methods=['GET'])
def get_logs():
    """
    Return all stored log entries.

    Query params:
      ?level=ERROR    — filter by level
      ?limit=50       — max results (default 100)
    """
    level = request.args.get('level', '').upper()
    limit = min(int(request.args.get('limit', 100)), 1000)

    rows = fetch_logs()
    data = [
        {'id': r[0], 'timestamp': r[1], 'level': r[2], 'message': r[3]}
        for r in rows
    ]
    if level:
        data = [d for d in data if d['level'] == level]

    return _ok(data[:limit])


# ── ML Endpoints ─────────────────────────────────────────────────────────

@app.route('/anomalies', methods=['GET'])
def get_anomalies():
    """
    Run Isolation Forest anomaly detection on all stored logs.
    Returns flagged entries with anomaly scores.
    """
    try:
        result = detect_anomalies()
        return _ok({'count': len(result), 'anomalies': result})
    except Exception as exc:
        logger.error("Anomaly detection error: %s", exc)
        return _err("Anomaly detection failed", 500)


@app.route('/severity', methods=['GET'])
def get_severity():
    """
    Run Logistic Regression severity classification across all stored logs.
    """
    try:
        result = classify_all()
        return _ok({'count': len(result), 'classifications': result})
    except Exception as exc:
        logger.error("Severity classification error: %s", exc)
        return _err("Severity classification failed", 500)


@app.route('/predict', methods=['POST'])
def predict():
    """
    Run anomaly detection + severity classification on a single message
    WITHOUT storing it in the DB. Useful for live inference.

    Body (JSON):
      { "message": "...", "level": "ERROR" }
    """
    body = request.get_json(silent=True)
    if not body or 'message' not in body:
        return _err("Request body must be JSON with a 'message' field")

    message = str(body['message']).strip()
    level   = str(body.get('level', 'INFO')).upper()

    anomaly  = detect_single(message, level)
    severity = classify_single(message, level)

    return _ok({
        'message':  message,
        'level':    level,
        'anomaly':  anomaly,
        'severity': severity
    })


# ── Metrics ───────────────────────────────────────────────────────────────

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Return operational metrics summary."""
    try:
        return _ok(generate_metrics())
    except Exception as exc:
        logger.error("Metrics error: %s", exc)
        return _err("Metrics generation failed", 500)


# ── Admin ─────────────────────────────────────────────────────────────────

@app.route('/logs', methods=['DELETE'])
def delete_logs():
    """Clear all stored logs. Use with caution."""
    clear_logs()
    return _ok({'message': 'All logs cleared'})


# ── Error Handlers ────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(_):
    return _err("Endpoint not found", 404)


@app.errorhandler(405)
def method_not_allowed(_):
    return _err("Method not allowed", 405)


@app.errorhandler(500)
def server_error(_):
    return _err("Internal server error", 500)


# ── Entry Point ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    logger.info("Starting System Observability Platform on port %d", port)
    app.run(host='0.0.0.0', port=port, debug=debug)
