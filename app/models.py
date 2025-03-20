from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from settings import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(ZoneInfo("Asia/Tokyo")))
    updatedAt = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(ZoneInfo("Asia/Tokyo")))

    def __repr__(self):
        return "<User(createdAt={}, updatedAt={})>".format(self.createdAt, self.updatedAt)
