import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, Integer, ForeignKey, ARRAY, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from settings import Base

# Database connection
# Models
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier = Column(String, unique=True, nullable=False)
    createdAt = Column(String, default=lambda: datetime.utcnow().isoformat())
    updatedAt = Column(String, default=lambda: datetime.utcnow().isoformat())

    def __repr__(self):
        return "<User('identifier={}', metadata={}, createdAt={})>".format(
            self.identifier,
            self.createdAt,
            self.updatedAt,
        )

# Get database session
