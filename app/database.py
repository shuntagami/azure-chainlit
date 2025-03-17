import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, Integer, ForeignKey, ARRAY, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database connection
DB_HOST = os.getenv("APP_DATABASE_HOST", "db")
DB_USERNAME = os.getenv("APP_DATABASE_USERNAME", "postgres")
DB_PASSWORD = os.getenv("APP_DATABASE_PASSWORD", "postgres")
DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:5432/chainlit"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier = Column(String, unique=True, nullable=False)
    metadata = Column(JSONB, nullable=False, default={})
    createdAt = Column(String, default=lambda: datetime.utcnow().isoformat())

    threads = relationship("Thread", back_populates="user", cascade="all, delete-orphan")

class Thread(Base):
    __tablename__ = "threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    createdAt = Column(String, default=lambda: datetime.utcnow().isoformat())
    name = Column(String)
    userId = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    userIdentifier = Column(String)
    tags = Column(ARRAY(String), default=[])
    metadata = Column(JSONB, default={})

    user = relationship("User", back_populates="threads")
    steps = relationship("Step", back_populates="thread", cascade="all, delete-orphan")
    elements = relationship("Element", back_populates="thread", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="thread", cascade="all, delete-orphan")

class Step(Base):
    __tablename__ = "steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    threadId = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False)
    parentId = Column(UUID(as_uuid=True), nullable=True)
    streaming = Column(Boolean, nullable=False)
    waitForAnswer = Column(Boolean)
    isError = Column(Boolean)
    metadata = Column(JSONB)
    tags = Column(ARRAY(String), default=[])
    input = Column(Text)
    output = Column(Text)
    createdAt = Column(String, default=lambda: datetime.utcnow().isoformat())
    start = Column(String)
    end = Column(String)
    generation = Column(JSONB)
    showInput = Column(String)
    language = Column(String)
    indent = Column(Integer)

    thread = relationship("Thread", back_populates="steps")
    feedbacks = relationship("Feedback", back_populates="step", cascade="all, delete-orphan")

class Element(Base):
    __tablename__ = "elements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    threadId = Column(UUID(as_uuid=True), ForeignKey("threads.id"))
    type = Column(String)
    url = Column(String)
    chainlitKey = Column(String)
    name = Column(String, nullable=False)
    display = Column(String)
    objectKey = Column(String)
    size = Column(String)
    page = Column(Integer)
    autoPlay = Column(Boolean)
    playerConfig = Column(JSONB)
    language = Column(String)
    forId = Column(UUID(as_uuid=True))
    mime = Column(String)

    thread = relationship("Thread", back_populates="elements")

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forId = Column(UUID(as_uuid=True), ForeignKey("steps.id"), nullable=False)
    threadId = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False)
    value = Column(Integer, nullable=False)
    comment = Column(Text)

    thread = relationship("Thread", back_populates="feedbacks")
    step = relationship("Step", back_populates="feedbacks")

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
