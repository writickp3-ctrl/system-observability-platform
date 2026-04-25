"""
init_db.py — Database bootstrap script
Run this once before starting the app for the first time.

Usage:
    python init_db.py
    python init_db.py --with-sample-data
"""

import sys
import os

# Make sure src/ is importable
sys.path.insert(0, os.path.dirname(__file__))

from src.db import init_db
from src.log_parser import parse_and_store
from src.logger import get_logger

logger = get_logger(__name__)


def main():
    print("=" * 50)
    print("  System Observability Platform — DB Init")
    print("=" * 50)

    # Step 1: Initialise database
    print("\n[1/2] Initialising SQLite database...")
    init_db()
    print("      ✓ logs.db created")

    # Step 2: Optionally load sample data
    load_samples = "--with-sample-data" in sys.argv
    if load_samples:
        sample_path = os.path.join("sample_logs", "syslog.txt")
        if os.path.exists(sample_path):
            print("\n[2/2] Loading sample log data...")
            count = parse_and_store(sample_path)
            print(f"      ✓ {count} sample entries loaded from {sample_path}")
        else:
            print(f"\n[2/2] Sample file not found: {sample_path} — skipping")
    else:
        print("\n[2/2] Skipping sample data (use --with-sample-data to load)")

    print("\n✓ Database ready. You can now run:")
    print("    python app.py")
    print("    or")
    print("    docker-compose up\n")


if __name__ == "__main__":
    main()
