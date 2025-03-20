import uuid
from sqlalchemy import Column, String, ForeignKey, Boolean, Integer, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from settings import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier = Column(String, nullable=False, unique=True)
    metadata_ = Column("metadata", JSONB, nullable=False)
    createdAt = Column(String)

    def __repr__(self):
        return f"<User(id={self.id}, identifier={self.identifier})>"

class Thread(Base):
    __tablename__ = "threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    createdAt = Column(String)
    name = Column(String)
    userId = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    userIdentifier = Column(String)
    tags = Column(ARRAY(String))
    metadata_ = Column("metadata", JSONB)

    def __repr__(self):
        return f"<Thread(id={self.id}, name={self.name})>"

class Step(Base):
    __tablename__ = "steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    threadId = Column(UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    parentId = Column(UUID(as_uuid=True))
    streaming = Column(Boolean, nullable=False)
    waitForAnswer = Column(Boolean)
    isError = Column(Boolean)
    metadata_ = Column("metadata", JSONB)
    tags = Column(ARRAY(String))
    input = Column(Text)
    output = Column(Text)
    createdAt = Column(String)
    start = Column(String)
    end = Column(String)
    generation = Column(JSONB)
    showInput = Column(String)
    language = Column(String)
    indent = Column(Integer)

    def __repr__(self):
        return f"<Step(id={self.id}, name={self.name}, type={self.type})>"

class Element(Base):
    __tablename__ = "elements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    threadId = Column(UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"))
    type = Column(String)
    url = Column(String)
    chainlitKey = Column(String)
    name = Column(String, nullable=False)
    display = Column(String)
    objectKey = Column(String)
    size = Column(String)
    page = Column(Integer)
    language = Column(String)
    forId = Column(UUID(as_uuid=True))
    mime = Column(String)
    props = Column(Text)

    def __repr__(self):
        return f"<Element(id={self.id}, name={self.name}, type={self.type})>"

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forId = Column(UUID(as_uuid=True), nullable=False)
    threadId = Column(UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    value = Column(Integer, nullable=False)
    comment = Column(Text)

    def __repr__(self):
        return f"<Feedback(id={self.id}, value={self.value})>"
