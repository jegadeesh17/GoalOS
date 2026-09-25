"""Authentic demo environment loader for GoalOS (zero PII, zero synthetic jargon).

Loads the authentic sanitized dataset (121 daily logs, 8 active life goals, 262 human
memories and lessons from daily journaling, 94 daily scores, 46 APM traces)
with demo persona 'Alex Chen' and zero personally identifiable information.
"""

from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from configs.settings import settings
except ImportError:
    from config.settings import settings
from database.connection import get_db
from database.repositories.log_repository import LogRepository

logger = logging.getLogger(__name__)

DEMO_DB_PATH = ROOT / "data" / "demo_goalos.db"
DEMO_CHROMA_PATH = ROOT / "data" / "demo_chroma_db"



def seed_demo_environment() -> dict[str, int]:
    """Initialize environment with authentic, sanitized dataset if unpopulated."""
    results = {
        "logs_loaded": 0,
        "goals_loaded": 0,
        "memories_loaded": 0,
        "scores_loaded": 0,
    }

    target_db = Path(settings.DB_PATH)
    target_chroma = Path(settings.CHROMA_PATH)

    log_repo = LogRepository()

    # 1. Populate SQLite database from authentic sanitized dataset if empty
    if DEMO_DB_PATH.exists() and (not target_db.exists() or log_repo.count() == 0):
        target_db.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DEMO_DB_PATH, target_db)
        logger.info("Loaded authentic sanitized database from %s to %s", DEMO_DB_PATH, target_db)

    # 2. Populate ChromaDB from authentic sanitized vector store if missing
    if DEMO_CHROMA_PATH.exists() and not target_chroma.exists():
        target_chroma.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(DEMO_CHROMA_PATH, target_chroma)
        logger.info("Loaded authentic sanitized ChromaDB from %s to %s", DEMO_CHROMA_PATH, target_chroma)

    with get_db() as conn:
        results["logs_loaded"] = conn.execute("SELECT count(*) FROM daily_logs").fetchone()[0]
        results["goals_loaded"] = conn.execute("SELECT count(*) FROM goals").fetchone()[0]
        results["memories_loaded"] = conn.execute("SELECT count(*) FROM memories").fetchone()[0]
        results["scores_loaded"] = conn.execute("SELECT count(*) FROM scores").fetchone()[0]


    logger.info("Authentic demo environment ready: %s", results)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(seed_demo_environment())
