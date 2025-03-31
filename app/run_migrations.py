#!/usr/bin/env python
import os
import sys
import logging
import time
from alembic import command
from alembic.config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run database migrations"""
    try:
        # Get alembic.ini file path (Docker container's /app directory)
        alembic_ini_path = "alembic.ini"  # Working directory is already /app

        if not os.path.exists(alembic_ini_path):
            logger.error(f"alembic.ini file not found: {alembic_ini_path}")
            return False

        # Create Alembic Config object
        alembic_cfg = Config(alembic_ini_path)

        # Display current migration state
        logger.info("Checking current migration status...")
        try:
            command.current(alembic_cfg)
        except Exception as e:
            logger.error(f"Exception during migration status check: {e}")
            logger.error(f"Exception details: {str(e.__class__.__name__)}: {str(e)}")
            raise

        # Run migrations
        logger.info("Running migrations...")
        command.upgrade(alembic_cfg, "head")

        logger.info("Migrations completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error during migration execution: {e}")
        return False

if __name__ == "__main__":
    # Wait a bit for the DB to start
    retry_count = 0
    max_retries = 5

    while retry_count < max_retries:
        logger.info(f"Attempting migration execution... ({retry_count + 1}/{max_retries})")
        if run_migrations():
            sys.exit(0)

        retry_count += 1
        logger.info(f"Waiting 10 seconds before retry...")
        time.sleep(10)

    logger.error("Migration execution failed. Maximum retry attempts reached.")
    sys.exit(1)