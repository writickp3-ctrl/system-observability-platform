import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from src.db import fetch_logs
from src.logger import get_logger

logger = get_logger(__name__)

# Error keywords weighted in feature extraction
_ERROR_KEYWORDS = ['error', 'fail', 'crash', 'timeout', 'critical',
                   'exception', 'killed', 'oom', 'refused', 'denied']


def _extract_features(df: pd.DataFrame) -> np.ndarray:
    """
    Feature vector per log entry:
      - message length
      - error keyword count
      - level severity score (INFO=0, WARN=1, ERROR=2)
    """
    level_score = {'INFO': 0, 'WARN': 1, 'ERROR': 2}

    df = df.copy()
    df['msg_len']   = df['message'].str.len()
    df['kw_count']  = df['message'].str.lower().apply(
        lambda m: sum(kw in m for kw in _ERROR_KEYWORDS)
    )
    df['lvl_score'] = df['level'].map(level_score).fillna(1)

    return df[['msg_len', 'kw_count', 'lvl_score']].values


def detect_anomalies(contamination: float = 0.2) -> list[dict]:
    """
    Run Isolation Forest on all stored logs.
    Returns list of anomalous log entries with scores.
    """
    rows = fetch_logs()
    if not rows:
        logger.warning("No logs in DB — anomaly detection skipped")
        return []

    df = pd.DataFrame(rows, columns=['id', 'timestamp', 'level', 'message'])

    if len(df) < 3:
        logger.warning("Too few logs for anomaly detection (need >= 3)")
        return []

    X = _extract_features(df)

    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100
    )
    df['anomaly_label'] = model.fit_predict(X)
    df['anomaly_score'] = model.score_samples(X)   # more negative = more anomalous

    anomalies = df[df['anomaly_label'] == -1].copy()
    anomalies['anomaly_score'] = anomalies['anomaly_score'].round(4)

    logger.info(
        "Anomaly detection complete — %d/%d entries flagged",
        len(anomalies), len(df)
    )
    return anomalies[['id', 'timestamp', 'level', 'message', 'anomaly_score']].to_dict(orient='records')


def detect_single(message: str, level: str = 'ERROR') -> dict:
    """
    Lightweight anomaly check for a single incoming log message.
    Uses heuristics since we can't fit a model on one point.
    """
    msg_lower = message.lower()
    kw_hits   = [kw for kw in _ERROR_KEYWORDS if kw in msg_lower]
    lvl_score = {'INFO': 0, 'WARN': 1, 'ERROR': 2}.get(level.upper(), 1)

    # Heuristic score: high keyword hits + ERROR level => anomaly
    score = len(kw_hits) * 0.4 + lvl_score * 0.3 + (len(message) / 500) * 0.3
    is_anomaly = score > 0.5 or level.upper() == 'ERROR'

    return {
        'is_anomaly': bool(is_anomaly),
        'heuristic_score': round(score, 3),
        'matched_keywords': kw_hits
    }
