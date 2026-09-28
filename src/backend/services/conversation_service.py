from typing import Any

from cache import RedisCache
from models import Conversations, Messages, db


class ConversationService:
    """Handles CRUD operations and cache invalidation for conversations and messages."""

    def __init__(self, cache: RedisCache | None = None) -> None:
        """Initializes ConversationService.

        Args:
            cache: RedisCache wrapper instance for caching queries.
        """
        self.cache = cache

    def invalidate_cache(self, user_id: int, conversation_id: int | None = None) -> None:
        """Clears Redis caches related to a user and conversation."""
        if not self.cache:
            return
        if conversation_id is not None:
            self.cache.delete(f"conversation:{conversation_id}")
            self.cache.delete(f"messages:conversation:{conversation_id}:user:{user_id}")
        self.cache.delete(f"conversations:user:{user_id}")

    def get_or_create_conversation(
        self, user_id: int, problem_id: int | None = None, conversation_id: int | None = None
    ) -> Conversations:
        """Retrieves an existing conversation or creates a new one."""
        convo = None
        if conversation_id:
            convo = Conversations.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not convo:
            convo = Conversations(user_id=user_id, problem_id=problem_id)
            db.session.add(convo)
            db.session.flush()

        return convo

    def add_message(
        self, conversation_id: int, user_id: int, role: str, content: str
    ) -> Messages:
        """Adds a message to an active conversation and persists it."""
        msg = Messages(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
        )
        db.session.add(msg)
        return msg

    def get_user_conversations(self, user_id: int) -> list[dict[str, Any]]:
        """Returns all conversations belonging to a user."""
        cache_key = f"conversations:user:{user_id}"
        if self.cache:
            cached = self.cache.get_json(cache_key)
            if cached is not None:
                return cached

        convos = Conversations.query.filter_by(user_id=user_id).all()
        result = [
            {
                "id": c.id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "user_id": c.user_id,
                "problem_id": c.problem_id,
            }
            for c in convos
        ]
        if self.cache:
            self.cache.set_json(cache_key, result, ttl=600)
        return result

    def get_conversation_messages(self, conversation_id: int, user_id: int) -> list[dict[str, Any]]:
        """Returns ordered messages for a conversation."""
        cache_key = f"messages:conversation:{conversation_id}:user:{user_id}"
        if self.cache:
            cached = self.cache.get_json(cache_key)
            if cached is not None:
                return cached

        messages = (
            Messages.query.filter_by(conversation_id=conversation_id, user_id=user_id)
            .order_by(Messages.created_at)
            .all()
        )
        payload = [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat() if m.created_at else None}
            for m in messages
        ]
        if self.cache:
            self.cache.set_json(cache_key, payload, ttl=600)
        return payload

    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """Deletes a conversation and invalidates its cache."""
        convo = Conversations.query.filter_by(id=conversation_id, user_id=user_id).first()
        if not convo:
            return False

        db.session.delete(convo)
        db.session.commit()
        self.invalidate_cache(user_id=user_id, conversation_id=conversation_id)
        return True
