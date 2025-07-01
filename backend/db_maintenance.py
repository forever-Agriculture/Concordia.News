# backend/db_maintenance.py
"""
Database maintenance scheduler for optimizing the SQLite database.

This module uses the `schedule` library to periodically run a VACUUM operation on `news_analysis.db`
to reclaim space and improve performance, scheduled weekly on Sundays at midnight UTC. It ensures
cost efficiency (no additional costs beyond minimal CPU/disk), reliability with error logging, and
no fabricated data, printing progress with emojis (e.g., 🚀, 🛠️). Logs INFO messages to
`logs/db_maintenance.log`.

Dependencies:
    - schedule: For task scheduling.
    - src.news_utils: For the vacuum_database function.
    - logging: For tracking operations.

Usage:
    >>> python db_maintenance.py
    🚀 Starting database maintenance scheduler...
    🛠️ Successfully vacuumed database at 2025-02-24 03:00:00
    # Runs continuously, vacuuming weekly, stopping with Ctrl+C (⏹️ Database maintenance scheduler stopped by user)
"""

import schedule
import time
import logging
import sqlite3
from backend.src.news_utils import vacuum_database
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, filename="logs/db_maintenance.log")
logger = logging.getLogger(__name__)


def quick_optimize_database(db_path: str = "news_analysis.db"):
    """Perform quick database optimization without full vacuum."""
    try:
        logger.info("Starting quick database optimization...")
        print("🔄 Starting quick database optimization...")
        
        with sqlite3.connect(db_path) as conn:
            # Use incremental vacuum instead of full vacuum
            print("🧹 Running incremental vacuum...")
            conn.execute("PRAGMA incremental_vacuum")
            
            # Analyze the database to update statistics for the query planner
            print("🔍 Running ANALYZE...")
            conn.execute("ANALYZE")
            
            # Run SQLite's built-in optimizer
            print("⚙️ Running PRAGMA optimize...")
            conn.execute("PRAGMA optimize")
            
            # Ensure WAL is checkpointed (synced to main database file)
            print("💾 Running WAL checkpoint...")
            conn.execute("PRAGMA wal_checkpoint(FULL)")
        
        success_message = f"✅ Quick database optimization completed at {datetime.now()}"
        logger.info(success_message)
        print(success_message)
    except Exception as e:
        error_message = f"❌ Database optimization failed: {str(e)}"
        logger.error(error_message)
        print(error_message)


if __name__ == "__main__":
    # Just run the optimization directly and exit
    quick_optimize_database()
    
    # Or set up a schedule for regular optimization
    schedule.every().day.at("03:30").do(quick_optimize_database)
    
    print("🚀 Starting database maintenance scheduler...")
    logger.info("🚀 Starting database maintenance scheduler")

    # Run the scheduler continuously, checking every 60 seconds
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        stop_message = "⏹️ Database maintenance scheduler stopped by user"
        logger.info(stop_message)
        print(stop_message)
