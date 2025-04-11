#!/usr/bin/env python
import argparse
import logging
from datetime import datetime

from app.services.database import Base, engine, get_db
from app.models import User
from app.config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Initialize database tables if they don't exist"""
    try:
        logger.info("Initializing database tables...")
        Base.metadata.create_all(engine)
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise

def seed_user(identifier):
    """
    Create or update a user with the specified identifier
    
    Args:
        identifier: User email or other unique identifier
    """
    db = next(get_db())

    try:
        # Check if user exists
        user = db.query(User).filter(User.identifier == identifier).first()

        # Set user metadata
        metadata = {
            "name": "Default User",
            "role": "admin",
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
            "preferences": {
                "theme": "light",
                "language": "en"
            }
        }

        if user:
            logger.info(f"Updating existing user '{identifier}'")
            user.metadata_ = metadata
        else:
            logger.info(f"Creating new user '{identifier}'")
            user = User(
                identifier=identifier,
                metadata_=metadata,
                createdAt=datetime.now().isoformat()
            )
            db.add(user)

        # Commit changes
        db.commit()
        logger.info(f"User '{identifier}' configuration completed")

        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error during user '{identifier}' creation/update: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Run database seed operations')
    parser.add_argument('--email', default=config.DEFAULT_ADMIN_EMAIL, 
                        help='User email address')
    parser.add_argument('--password', default=config.DEFAULT_ADMIN_PASSWORD,
                        help='User password (not stored, used for authentication only)')

    args = parser.parse_args()

    # Initialize database
    setup_database()

    # Create default user
    seed_user(args.email)

    logger.info("Seed operations completed")

if __name__ == "__main__":
    main()