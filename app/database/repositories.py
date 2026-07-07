# app/database/repositories.py
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.database import models
from app.chat.conversation import Conversation, Message
from typing import List, Optional
from datetime import datetime
from contextlib import contextmanager

@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ConversationRepository:
    def __init__(self, db: Session = None):
        self._db = db

    def _get_db(self):
        if self._db is not None:
            @contextmanager
            def external_session():
                yield self._db
            return external_session()
        else:
            return get_session()

    def create(self, conversation: Conversation) -> Conversation:
        with self._get_db() as db:
            db_conv = models.Conversation(
                title=conversation.title,
                model=conversation.model
            )
            db.add(db_conv)
            db.commit()
            db.refresh(db_conv)
            conversation.id = db_conv.id
            return conversation

    def get(self, conv_id: int) -> Optional[Conversation]:
        with self._get_db() as db:
            db_conv = db.query(models.Conversation).filter(models.Conversation.id == conv_id).first()
            if not db_conv:
                return None
            return self._to_pydantic(db_conv)

    def list(self) -> List[Conversation]:
        with self._get_db() as db:
            db_convs = db.query(models.Conversation).order_by(models.Conversation.updated_at.desc()).all()
            return [self._to_pydantic(c) for c in db_convs]

    def update_title(self, conv_id: int, title: str):
        with self._get_db() as db:
            db_conv = db.query(models.Conversation).filter(models.Conversation.id == conv_id).first()
            if db_conv:
                db_conv.title = title
                db_conv.updated_at = datetime.utcnow()
                db.commit()

    def delete(self, conv_id: int):
        with self._get_db() as db:
            db_conv = db.query(models.Conversation).filter(models.Conversation.id == conv_id).first()
            if db_conv:
                db.delete(db_conv)
                db.commit()

    def _to_pydantic(self, db_conv: models.Conversation) -> Conversation:
        return Conversation(
            id=db_conv.id,
            title=db_conv.title,
            model=db_conv.model,
            created_at=db_conv.created_at,
            updated_at=db_conv.updated_at,
            messages=[]
        )

class MessageRepository:
    def __init__(self, db: Session = None):
        self._db = db

    def _get_db(self):
        if self._db is not None:
            @contextmanager
            def external_session():
                yield self._db
            return external_session()
        else:
            return get_session()

    def create(self, conversation_id: int, role: str, content: str) -> Message:
        with self._get_db() as db:
            db_msg = models.Message(
                conversation_id=conversation_id,
                role=role,
                content=content
            )
            db.add(db_msg)
            db.commit()
            db.refresh(db_msg)
            
            # Update conversation updated_at
            conv = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
            if conv:
                conv.updated_at = datetime.utcnow()
                db.commit()
                
            return Message(
                id=db_msg.id,
                conversation_id=db_msg.conversation_id,
                role=db_msg.role,
                content=db_msg.content,
                created_at=db_msg.created_at
            )

    # FIXED: get_messages now returns most recent messages in chronological order
    def get_messages(self, conversation_id: int, limit: Optional[int] = None) -> List[Message]:
        with self._get_db() as db:
            # Get newest messages first (so LIMIT gives the most recent)
            query = db.query(models.Message).filter(
                models.Message.conversation_id == conversation_id
            ).order_by(models.Message.created_at.desc())
            if limit:
                query = query.limit(limit)
            msgs = query.all()
            # Reverse to chronological order (oldest first) for the LLM
            msgs = reversed(msgs)
            return [Message(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                created_at=m.created_at
            ) for m in msgs]