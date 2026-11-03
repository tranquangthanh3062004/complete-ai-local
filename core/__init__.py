"""
COMPLETE AI — Core Package
Shared constants, enums, exceptions, and schemas.
"""
from core.constants import APP_NAME, APP_VERSION
from core.enums import OperationMode, LLMEngine, EmbeddingEngine, IntentType, TopicType

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "OperationMode",
    "LLMEngine",
    "EmbeddingEngine",
    "IntentType",
    "TopicType",
]
