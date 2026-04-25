import re
from datetime import datetime
from src.db import insert_log
from src.logger import get_logger

logger = get_logger(__name__)

# Matches: "Jan 10 10:12:33 INFO Some message here"
_PATTERN = re.compile(
    r'(\w{3}\s+\d{1,2}\s[\d:]+)\s+(INFO|WARN|WARNING|ERROR|CRITICAL|DEBUG)\s+(.*)',
    re.IGNORECASE
)

# Normalise non-standard level names
_LEVEL_MAP = {
    'WARNING': 'WARN',
    'CRITICAL': 'ERROR',
    'DEBUG': 'INFO',
}


def parse_line(line: str) -> dict | None:
    """Parse a single syslog-style line. Returns dict or None if no match."""
    match = _PATTERN.search(line.strip())
    if not match:
        return None
    ts_raw, level, message = match.groups()
    level = _LEVEL_MAP.get(level.upper(), level.upper())
    # Normalise timestamp
    try:
        year = datetime.now().year
        ts = datetime.strptime(f"{year} {ts_raw}", "%Y %b %d %H:%M:%S").isoformat()
    except ValueError:
        ts = ts_raw
    return {'timestamp': ts, 'level': level, 'message': message.strip()}


def parse_and_store(file_path: str) -> int:
    """
    Parse a log file and persist every matched entry to SQLite.
    Returns the number of entries inserted.
    """
    inserted = 0
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as fh:
            for line in fh:
                entry = parse_line(line)
                if entry:
                    insert_log(entry['timestamp'], entry['level'], entry['message'])
                    inserted += 1
        logger.info("Parsed %d entries from %s", inserted, file_path)
    except FileNotFoundError:
        logger.error("File not found: %s", file_path)
    except Exception as exc:
        logger.error("Parser error: %s", exc)
    return inserted
