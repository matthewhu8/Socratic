"""Process-wide singleton service instances shared across routers."""
import os

from .services.conversation_service import ConversationService

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
convo_service = ConversationService(redis_url=REDIS_URL)
