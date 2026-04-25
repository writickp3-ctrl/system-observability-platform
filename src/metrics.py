import os
import pandas as pd
from src.db import fetch_logs, fetch_log_count
from src.logger import get_logger

logger = get_logger(__name__)

METRICS_DIR = os.environ.get('METRICS_DIR', 'metrics')
os.makedirs(METRICS_DIR, exist_ok=True)


def generate_metrics() -> dict:
    """
    Generate operational metrics from stored logs.
    Writes metrics.csv and returns a summary dict.
    """
    rows = fetch_logs()
    total = fetch_log_count()

    if not rows:
        return {
            'total_logs': 0,
            'by_level': {},
            'error_rate_pct': 0.0,
            'warn_rate_pct': 0.0
        }

    df = pd.DataFrame(rows, columns=['id', 'timestamp', 'level', 'message'])
    level_counts = df['level'].value_counts().to_dict()

    error_count = level_counts.get('ERROR', 0)
    warn_count  = level_counts.get('WARN', 0)

    summary = {
        'total_logs':      total,
        'by_level':        level_counts,
        'error_rate_pct':  round(error_count / total * 100, 2) if total else 0.0,
        'warn_rate_pct':   round(warn_count  / total * 100, 2) if total else 0.0,
    }

    # Persist to CSV
    out_path = os.path.join(METRICS_DIR, 'metrics.csv')
    df['level'].value_counts().reset_index().rename(
        columns={'index': 'level', 'level': 'count'}
    ).to_csv(out_path, index=False)

    logger.info("Metrics generated — total=%d error_rate=%.1f%%",
                total, summary['error_rate_pct'])
    return summary
