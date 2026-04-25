import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from src.db import fetch_logs
from src.logger import get_logger

logger = get_logger(__name__)

_SEVERITY_MAP = {'INFO': 'LOW', 'WARN': 'MEDIUM', 'ERROR': 'HIGH'}

_CRITICAL_KEYWORDS = ['oom', 'killed', 'segfault', 'panic', 'crash',
                      'out of memory', 'disk full', 'connection refused']
_HIGH_KEYWORDS     = ['error', 'fail', 'timeout', 'exception', 'denied']
_MEDIUM_KEYWORDS   = ['warn', 'high', 'slow', 'retry', 'degraded']


def classify_single(message: str, level: str = 'INFO') -> dict:
    """
    Rule-based severity classification for a single message.
    Returns severity label + confidence.
    """
    msg_lower = message.lower()

    if any(kw in msg_lower for kw in _CRITICAL_KEYWORDS):
        severity, confidence = 'CRITICAL', 0.95
    elif level.upper() == 'ERROR' or any(kw in msg_lower for kw in _HIGH_KEYWORDS):
        severity, confidence = 'HIGH', 0.85
    elif level.upper() == 'WARN' or any(kw in msg_lower for kw in _MEDIUM_KEYWORDS):
        severity, confidence = 'MEDIUM', 0.75
    else:
        severity, confidence = 'LOW', 0.90

    return {'severity': severity, 'confidence': confidence}


def classify_all() -> list[dict]:
    """
    ML-backed severity classification across all stored logs.
    Uses Logistic Regression trained on message features.
    """
    rows = fetch_logs()
    if not rows:
        return []

    df = pd.DataFrame(rows, columns=['id', 'timestamp', 'level', 'message'])

    df['msg_len']  = df['message'].str.len()
    df['kw_score'] = df['message'].str.lower().apply(
        lambda m: sum(kw in m for kw in _CRITICAL_KEYWORDS) * 2
                + sum(kw in m for kw in _HIGH_KEYWORDS)
    )
    df['label'] = df['level'].map({'INFO': 0, 'WARN': 1, 'ERROR': 2}).fillna(1).astype(int)

    X = df[['msg_len', 'kw_score']].values
    y = df['label'].values

    if len(set(y)) < 2:
        # All same class — fall back to rule-based
        df['predicted_severity'] = df['level'].map(_SEVERITY_MAP).fillna('MEDIUM')
    else:
        model = LogisticRegression(max_iter=500, random_state=42)
        model.fit(X, y)
        preds = model.predict(X)
        label_names = {0: 'LOW', 1: 'MEDIUM', 2: 'HIGH'}
        df['predicted_severity'] = [label_names.get(p, 'MEDIUM') for p in preds]

    logger.info("Severity classification complete for %d logs", len(df))
    return df[['id', 'timestamp', 'level', 'message', 'predicted_severity']].to_dict(orient='records')
