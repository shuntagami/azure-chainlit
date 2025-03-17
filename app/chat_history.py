import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from database import Thread, Step, User

class ChatHistoryManager:
    """Manager for chat history operations"""

    @staticmethod
    def create_thread(db: Session, user: User, name: Optional[str] = None) -> Thread:
        """Create a new chat thread for a user"""
        thread = Thread(
            id=uuid.uuid4(),
            name=name or f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            userId=user.id,
            userIdentifier=user.identifier,
            createdAt=datetime.utcnow().isoformat()
        )
        db.add(thread)
        db.commit()
        db.refresh(thread)
        return thread

    @staticmethod
    def get_user_threads(db: Session, user_id: uuid.UUID) -> List[Thread]:
        """Get all threads for a user"""
        return db.query(Thread).filter(Thread.userId == user_id).order_by(Thread.createdAt.desc()).all()

    @staticmethod
    def get_thread(db: Session, thread_id: uuid.UUID) -> Optional[Thread]:
        """Get a specific thread by ID"""
        return db.query(Thread).filter(Thread.id == thread_id).first()

    @staticmethod
    def add_message(
        db: Session,
        thread_id: uuid.UUID,
        message_type: str,
        content: str,
        name: str = "message",
        metadata: Dict[str, Any] = None
    ) -> Step:
        """Add a message to a thread"""
        step = Step(
            id=uuid.uuid4(),
            threadId=thread_id,
            type=message_type,
            name=name,
            streaming=False,
            input=content if message_type == "user" else None,
            output=content if message_type == "assistant" else None,
            createdAt=datetime.utcnow().isoformat(),
            start=datetime.utcnow().isoformat(),
            end=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step

    @staticmethod
    def get_thread_messages(db: Session, thread_id: uuid.UUID) -> List[Step]:
        """Get all messages in a thread"""
        return db.query(Step).filter(Step.threadId == thread_id).order_by(Step.createdAt).all()

    @staticmethod
    def format_messages_for_openai(steps: List[Step]) -> List[Dict[str, str]]:
        """Format thread messages for OpenAI API"""
        messages = []

        for step in steps:
            if step.type == "user" and step.input:
                messages.append({"role": "user", "content": step.input})
            elif step.type == "assistant" and step.output:
                messages.append({"role": "assistant", "content": step.output})
            elif step.type == "system" and step.input:
                messages.append({"role": "system", "content": step.input})

        return messages
