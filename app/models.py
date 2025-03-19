from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, DateTime, Integer, String, TEXT, UniqueConstraint
from sqlalchemy.orm import validates
from settings import Base
import bcrypt
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(30), nullable=False)
    password_hash = Column(TEXT, nullable=True)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(ZoneInfo("Asia/Tokyo")))
    updatedAt = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(ZoneInfo("Asia/Tokyo")))

    @validates('email')
    def validate_email(self, key, value):
        if not value:
            raise ValueError('メールアドレスは必須です')
        elif '@' not in value:
            raise ValueError('有効なメールアドレスを入力してください')
        elif len(value) > 30:
            raise ValueError('メールアドレスは30文字以内である必要があります')
        return value

    @validates('password_hash')
    def validate_password_hash(self, key, value):
        if not value:
            raise ValueError('パスワードは必須です')
        elif len(value) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        return value

    __table_args__ = (
        UniqueConstraint('email', name='uq_user_email'),
    )

    def set_password(self, password):
        """パスワードをハッシュ化してデータベースに保存する"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def check_password(self, password):
        """パスワードが正しいかを検証する"""
        if not self.password_hash:
            return False
        password_bytes = password.encode('utf-8')
        stored_hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, stored_hash_bytes)
